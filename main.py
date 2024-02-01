import argparse
import asyncio
import os
import sys
import logging
from enum import Enum
import random
from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger

from pastel_gateway_sdk.rest import ApiException
from pastel_gateway_sdk import GatewayApiClientAsync

from image_generator import SDImageGenerator
from prompt_geenrator import LlamaPromptGenerator
from config import settings


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
        self.file_in_progress = set()
        self.img_generator = SDImageGenerator()
        self.prompt_generator = LlamaPromptGenerator()

    async def run(self):
        try:
            self.client = GatewayApiClientAsync(network=self.network)
            self.client.set_auth_api_key(self.api_key)

            async with AsyncScheduler() as scheduler:
                # scheduler.add_schedule(self.create_ticket, IntervalTrigger(seconds=settings.CREATE_TICKET_INTERVAL))
                # await scheduler.add_schedule(self.check_statuses, IntervalTrigger(seconds=settings.CHECK_INTERVAL))
                await scheduler.add_schedule(self.generate_images, IntervalTrigger(seconds=settings.GENERATE_IMAGE_INTERVAL))

                logging.info("Scheduler started")
                await scheduler.run_until_stopped()

        except (KeyboardInterrupt, SystemExit):
            logging.exception("KeyboardInterrupt or SystemExit")
        except Exception as error:
            logging.exception(error)
        finally:
            await self.client.close()

    async def create_ticket(self):
        selected_type: TicketType = random.choice(list(TicketType))
        logging.info(f"Create {selected_type.name} ticket on {self.network} network")

        file_list = [self.select_random_file(selected_type.name)]

        try:
            if selected_type == TicketType.CASCADE:
                result = await self.client.cascade_api.cascade_process_request(file_list, make_publicly_accessible=True)
                logging.info(f"Cascade ticket registration started. Request status: {result.to_str()}")
            elif selected_type == TicketType.SENSE:
                result = await self.client.sense_api.sense_submit_request(file_list)
                logging.info(f"Sense ticket registration started. Request status: {result.to_str()}")
            elif selected_type == TicketType.NFT:
                result = await self.client.nft_api.nft_process_request(file_list,
                                                                       nft_details_payload={},
                                                                       make_publicly_accessible=True)
                logging.info(f"NFT ticket registration started. Request status: {result.to_str()}")
            else:
                logging.info(f"Unknown ticket type: {selected_type.name}")
                raise Exception(f"Unknown ticket type: {selected_type.name}")

            for file_path in file_list:
                logging.info(f"Deleting file {file_path}")
                os.remove(file_path)

        except ApiException as error:
            logging.exception(error)
        except Exception as error:
            logging.exception(error)

    async def check_statuses(self):
        logging.info(f"Check ticket registration statuses on {self.network} network")
        try:
            print(f"Statuses checked")
        except Exception as error:
            logging.exception(error)

    async def generate_images(self):
        logging.info(f"Generate images on {self.network} network")
        try:
            prompt = self.prompt_generator.generate_prompt()
            print(f"Prompt: {prompt}")
            # file_name = self.prompt_generator.generate_file_name(prompt)
            # file_path = os.path.join(settings.BASE_IMG_PATH, file_name)
            # print(f"Generate image {file_name}")
            # self.img_generator.generate(prompt, file_path)
            # print(f"Image {file_name} generated")
        except Exception as error:
            logging.exception(error)

    def select_random_file(self, file_type) -> str:
        pass
        # image_dir = os.path.join(settings.BASE_IMG_PATH, file_type)
        # files = os.listdir(image_dir)
        # while True:
        #     index = random.randint(0, len(files) - 1)
        #     if files[index] not in self.file_in_progress:
        #         self.file_in_progress.add(files[index])
        #         return os.path.join(image_dir, files[index])
        #     else:
        #         logging.info(f"File {files[index]} already in progress, select another one")
        #         files.pop(index)
        #         if len(files) == 0:
        #             logging.info(f"No more files to select, wait for next iteration")
        #             raise Exception(f"No more files to select, wait for next iteration")


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Pastel Network Maker')
        parser.add_argument('-n', '--network', type=str, required=True, help='Network to use - mainnet or testnet')
        parser.add_argument('-k', '--api-key', type=str, required=True, help='API Key to use')
        parser.add_argument('-l', '--logfile', type=str, required=False, help='Log file')
        args = parser.parse_args()

        setup_logging(args.logfile)

        maker = NetworkMaker(args.network, args.api_key)
        asyncio.run(maker.generate_images())
        # asyncio.run(maker.run())
    except KeyboardInterrupt:
        print('\nProgram interrupted by the user. Exiting...')