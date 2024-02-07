from aiohttp import web
import jinja2
import aiohttp_jinja2

import argparse
import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
import logging
import random
import signal
import sys

from pastel_gateway_sdk import GatewayApiClientAsync, RequestResult, ResultRegistrationResult
from pastel_gateway_sdk.rest import ApiException

from config import settings, biased_random, get_random_genre
from db_manager import SQLiteDB
from image_generator import SDImageGenerator
from prompt_generator import LlamaPromptGenerator
from tools import execution_timer


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class TicketType(Enum):
    CASCADE = "cascade"
    SENSE = "sense"
    NFT = "nft"
    COLLECTION = "collection"


# Setup logging
def setup_logging(logfile=None):
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format, handlers=[
        logging.StreamHandler(sys.stdout),
        *([] if logfile is None else [logging.FileHandler(logfile)])
    ])


class NetworkMaker:
    def __init__(self, network: str, api_key: str):
        self.network = network
        self.api_key = api_key
        self.client = None
        self.loop = asyncio.get_event_loop()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.db = SQLiteDB(settings.DB_NAME)
        self.img_generator = SDImageGenerator()
        self.prompt_generator = LlamaPromptGenerator()
        self.client = GatewayApiClientAsync(network=self.network)
        self.client.set_auth_api_key(self.api_key)

        self.statistics = {}

    @execution_timer
    async def generate_images(self):
        if not settings.ENABLE_GENERATE_IMAGES:
            logging.info("generate_images: Disabled")
            return
        logging.info(f"generate_images: Starting task...")
        while True:
            try:
                prompt, file_name, file_path = await self.loop.run_in_executor(self.executor, self._generate_image)
                logging.info(f"generate_images: Inserting new   image info into DB...")
                tags = prompt.get("Tags", "")
                keywords = ', '.join(tags)
                await self.db.add_image(description=prompt["Description"], name=prompt.get("Title", file_name),
                                        file_path=file_path, keywords=keywords,
                                        series_name=prompt.get("SeriesName", ""))

                logging.info(f"generate_images: DONE")
            except Exception as error:
                logging.exception(error)
            await asyncio.sleep(settings.GENERATE_IMAGE_INTERVAL)

    def _generate_image(self) -> (dict | None, str | None, str | None):
        logging.info(f"_generate_image: Starting thread...")
        genre = get_random_genre()
        prompt: dict = self.prompt_generator.generate_prompt(genre)
        logging.info(f"Prompt: {prompt}")
        if (prompt is None
                or "Description" not in prompt
                or not prompt["Description"]
                or not isinstance(prompt["Description"], str)
                or len(prompt["Description"]) == 0):
            logging.info("Prompt generation failed, wait for next iteration")
            return None, None, None
        if "FileName" not in prompt:
            logging.info("No file names in prompt, generating random file name")
            file_name: str = f"{random.randint(100000, 999999)}.jpg"
        else:
            file_name = prompt['FileName']
            name, extension = os.path.splitext(file_name)
            if not extension or extension != ".jpg" or extension != ".jpeg" or extension != ".png":
                file_name = f"{file_name}.jpg"
        file_path: str = os.path.join(settings.BASE_IMG_PATH, file_name)
        file_path = self._check_image_path(file_path)
        logging.info(f"Generate image {file_path}")
        self.img_generator.generate(prompt["Description"], file_path)
        logging.info(f"generate_images: DONE - {file_name} generated")
        return prompt, file_name, file_path

    @staticmethod
    def _check_image_path(filepath):
        base = os.path.splitext(filepath)[0]
        ext = os.path.splitext(filepath)[1]
        while True:
            rand_num = random.randint(0, 9999)
            new_filename = f"{base}_{rand_num}{ext}"
            if not os.path.exists(new_filename):
                return new_filename

    async def create_ticket(self):
        if not settings.ENABLE_CREATE_TICKETS:
            logging.info("create_ticket: Disabled")
            return
        logging.info(f"create_ticket: Starting task...")
        while True:
            selected_type: TicketType = random.choice(list(TicketType))
            logging.info(f"create_ticket: Create {selected_type.name} ticket on {self.network} network")
            try:
                ok = False
                if selected_type == TicketType.CASCADE:
                    ok = await self._register_cascade_ticket()
                elif selected_type == TicketType.SENSE:
                    ok = await self._register_sense_ticket()
                elif selected_type == TicketType.NFT:
                    ok = await self._register_cascade_ticket()              ### !!!! TEMPORARY
                    # ok = await self._register_nft_ticket()
                elif selected_type == TicketType.COLLECTION:
                    ok = await self._register_sense_ticket()                ### !!!! TEMPORARY
                    # ok = await self._register_collection_ticket()

                if ok:
                    logging.info(f"create_ticket: DONE")
                else:
                    logging.info(f"create_ticket: FAILED, wait for next iteration")
            except ApiException as error:
                logging.exception(error)
            except Exception as error:
                logging.exception(error)
            await asyncio.sleep(settings.CREATE_TICKET_INTERVAL)

    async def _register_cascade_ticket(self) -> bool:
        image_rec = await self.db.find_image_for_cascade()
        if not image_rec:
            logging.info("No images to process for Cascade, wait for next iteration")
            return False
        make_publicly_accessible = random.choice([True, False])
        file_list, image_rec_id = [image_rec['file_path']], image_rec['id']
        output: RequestResult = await self.client.cascade_api.cascade_process_request(file_list,
                                                                                      make_publicly_accessible)
        res_id = reg_txid = act_txid = res_status = ""
        if output:
            if output.results and len(output.results) > 0:
                result: ResultRegistrationResult = output.results[0]
                res_id, res_status = result.result_id, result.result_status.value
                reg_txid, act_txid = result.registration_ticket_txid, result.activation_ticket_txid
            await self.db.add_cascade(image_rec_id, res_status, output.request_id, res_id, reg_txid, act_txid,
                                      make_publicly_accessible)
            logging.info(f"Cascade ticket registration started. Request ID {output.request_id}. "
                         f"Request status: {output.request_status}")
            return True
        else:
            logging.info(f"Failed to register Cascade ticket")
            return False

    async def _register_sense_ticket(self) -> bool:
        image_rec = await self.db.find_image_for_sense_or_nft()
        if not image_rec:
            logging.info("No images to process for Sense, wait for next iteration")
            return False
        collection_act_txid, open_api_group_id = "", ""
        file_list, image_rec_id = [image_rec['file_path']], image_rec['id']
        output: RequestResult = await self.client.sense_api.sense_submit_request(file_list,
                                                                                 collection_act_txid, open_api_group_id)
        res_id = reg_txid = act_txid = res_status = ""
        if output:
            if output.results and len(output.results) > 0:
                result: ResultRegistrationResult = output.results[0]
                res_id, res_status = result.result_id, result.result_status.value
                reg_txid, act_txid = result.registration_ticket_txid, result.activation_ticket_txid
            await self.db.add_sense(image_rec_id, res_status, output.request_id, res_id, reg_txid, act_txid,
                                    collection_act_txid, open_api_group_id)
            logging.info(f"Sense ticket registration started. Request ID {output.request_id}. "
                         f"Request status: {output.request_status}")
            return True
        else:
            logging.info(f"Failed to register Sense ticket")
            return False

    async def _register_nft_ticket(self) -> bool:
        image_rec = await self.db.find_image_for_sense_or_nft()
        if not image_rec:
            logging.info("No images to process for NFT, wait for next iteration")
            return False
        nft_details_payload = {
            "description": image_rec['description'],
            "name": image_rec['name'],
            "creator_name": image_rec['creator_name'],
            "keywords": image_rec['keywords'],
            "series_name": image_rec['series_name'],
            "issued_copies": biased_random(),
            "green": random.choice([True, False]),
            "royalty": random.uniform(0.1, 10.0)
        }
        nft_details_payload_str = json.dumps(nft_details_payload)
        collection_act_txid, open_api_group_id = "", ""
        make_publicly_accessible = random.choice([True, False])
        file_list, image_rec_id = [image_rec['file_path']], image_rec['id']
        output: RequestResult = await self.client.nft_api.nft_process_request(file_list, nft_details_payload_str,
                                                                              make_publicly_accessible,
                                                                              collection_act_txid, open_api_group_id)

        res_id = reg_txid = act_txid = res_status = ""
        if output:
            if output.results and len(output.results) > 0:
                result: ResultRegistrationResult = output.results[0]
                res_id, res_status = result.result_id, result.result_status.value
                reg_txid, act_txid = result.registration_ticket_txid, result.activation_ticket_txid
            await self.db.add_nft(image_rec_id, res_status, output.request_id, res_id, reg_txid, act_txid,
                                  issued_copies=nft_details_payload["issued_copies"],
                                  green=nft_details_payload["green"], royalty=nft_details_payload["royalty"],
                                  collection_act_txid=collection_act_txid, open_api_group_id=open_api_group_id,
                                  make_publicly_accessible=make_publicly_accessible)
            logging.info(f"NFT ticket registration started. Request ID {output.request_id}. "
                         f"Request status: {output.request_status}")
            return True
        else:
            logging.info(f"Failed to register NFT ticket")
            return False

    async def _register_collection_ticket(self) -> bool:
        return True

    async def check_statuses(self):
        if not settings.ENABLE_CHECK_STATUSES:
            logging.info("check_statuses: Disabled")
            return
        logging.info(f"check_statuses: Starting task...")
        while True:
            logging.info(f"check_statuses: Check ticket registration statuses")
            try:
                await self.update_statuses()

                await self.collect_stats()

                logging.info(f"check_statuses: DONE")
            except Exception as error:
                logging.exception(error)
            await asyncio.sleep(settings.CHECK_INTERVAL)

    async def update_statuses(self):
        await self._check_ticket_status(self.db.get_cascade_pending,
                                        self.client.cascade_api.cascade_get_result,
                                        self.db.update_cascade_status)
        await self._check_ticket_status(self.db.get_sense_pending,
                                        self.client.sense_api.sense_get_result_by_id,
                                        self.db.update_sense_status)
        await self._check_ticket_status(self.db.get_nft_pending,
                                        self.client.nft_api.nft_get_result_by_result_id,
                                        self.db.update_nft_status)
        # await self._check_ticket_status(self.db.get_collections_pending,
        #                                 self.client.collection_api.collection_get_result,
        #                                 self.db.update_collection_status)

    async def collect_stats(self):
        all_tickets = await self.db.read_all_images()
        logging.info("check_statuses: Total images: {}".format(len(all_tickets)))
        self.statistics['Total images'] = len(all_tickets)
        await self.log_ticket_counts(self.db.get_cascade_counts, "Cascade")
        await self.log_ticket_counts(self.db.get_sense_counts, "Sense")
        await self.log_ticket_counts(self.db.get_nft_counts, "NFT")
        await self.log_ticket_counts(self.db.get_collections_counts, "Collections")

    async def log_ticket_counts(self, get_counts_function, ticket_type):
        nums = await get_counts_function()
        total = sum(count for status, count in nums)
        msg = f"\t{ticket_type} tickets: {total};"
        stats = {'total': total}
        for status, count in nums:
            msg += f" {status}: {count}"
            stats[status] = count
        logging.info(msg)
        self.statistics[ticket_type] = stats

    @staticmethod
    async def _check_ticket_status(func_get_pending, func_get_result, func_update_status):
        pending = await func_get_pending()
        if not pending:
            return
        for ticket in pending:
            try:
                res_id = ticket['res_id']
                result = await func_get_result(res_id)
                if result:
                    res_status = result.result_status.value
                    if res_status != ticket['status']:
                        reg_txid = result.registration_ticket_txid
                        act_txid = result.activation_ticket_txid
                        await func_update_status(ticket['id'], res_status, reg_txid, act_txid)
                        logging.info(f"Cascade ticket status checked. Result ID {res_id}. "
                                     f"Request status: {res_status}")
                else:
                    logging.info(f"Failed to get Cascade ticket status. Result ID {res_id}.")
            except ApiException as error:
                logging.exception(error)
            except Exception as error:
                logging.exception(error)

    async def run(self):
        await self.db.initialize_db()
        app = web.Application()
        aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader(os.path.join(BASE_DIR, 'web')))
        app.add_routes([web.get('/', self.show_statistics)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, port=8080)
        await site.start()

        # threading.Thread(target=web.run_app, args=(app,), kwargs={'port': 8080}, daemon=True).start()
        await asyncio.gather(
            self.generate_images(),
            self.create_ticket(),
            self.check_statuses()
        )
        await self.client.close()
        logging.info("Exiting...")

    async def show_statistics(self, request):
        # await self.collect_stats()
        await self.update_statuses()
        response = aiohttp_jinja2.render_template('statistics.html', request,
                                                  {'statistics': self.statistics, 'network': self.network})
        return response


async def shutdown_tasks_and_cleanup(loop):
    tasks = [t for t in asyncio.all_tasks(loop) if t is not
             asyncio.current_task()]
    [task.cancel() for task in tasks]

    await asyncio.gather(*tasks, return_exceptions=True)
    await loop.shutdown_asyncgens()
    loop.stop()


def graceful_shutdown(signal, loop):
    logging.info("Shutting down gracefully...")
    asyncio.ensure_future(shutdown_tasks_and_cleanup(loop), loop=loop)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pastel Network Maker')
    parser.add_argument('-n', '--network', type=str, required=True, help='Network to use - mainnet or testnet')
    parser.add_argument('-k', '--api-key', type=str, required=True, help='API Key to use')
    parser.add_argument('-l', '--logfile', type=str, required=False, help='Log file')
    args = parser.parse_args()

    setup_logging(args.logfile)

    maker = NetworkMaker(args.network, args.api_key)
    loop = asyncio.get_event_loop()
    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(s, lambda sig=s: graceful_shutdown(sig, loop))

    try:
        loop.create_task(maker.run())
        loop.run_forever()
    except asyncio.CancelledError:
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
