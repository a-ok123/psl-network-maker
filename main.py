import argparse
import asyncio
import sys
import logging
from enum import Enum
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.executors.asyncio import AsyncIOExecutor

from pastel_gateway_sdk.rest import ApiException
from pastel_gateway_sdk import GatewayApiClientAsync

TICKET_INTERVAL = 3
CHECK_INTERVAL = 300


class TicketType(Enum):
    CASCADE = "cascade"
    SENSE = "sense"
    NFT = "nft"


Files2Use = {
    TicketType.CASCADE: [
        ["C:\\Users\\alexe\\OneDrive\\Pictures\\Screenshots\\Screenshot 2024-01-15 185056.png"]
    ],
    TicketType.SENSE: [
        ["C:\\Users\\alexe\\OneDrive\\Pictures\\Screenshots\\Screenshot 2024-01-15 185056.png"]
    ],
    TicketType.NFT: [
        ["C:\\Users\\alexe\\OneDrive\\Pictures\\Screenshots\\Screenshot 2024-01-15 185056.png"]
    ]
}


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
        self.scheduler = None
        self.client = None

    async def run(self):
        try:
            self.client = GatewayApiClientAsync(network=self.network)
            self.client.set_auth_api_key(self.api_key)
            await self.create_ticket()

            self.scheduler = AsyncIOScheduler(executors={"default": AsyncIOExecutor()})
            self.scheduler.add_job(self.create_ticket, 'interval', seconds=TICKET_INTERVAL)
            self.scheduler.add_job(self.check_statuses, 'interval', seconds=CHECK_INTERVAL)
            self.scheduler.start()

            logging.info("Scheduler started")

            # to keep the script running
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            await self.shutdown(None, None)
        except Exception as error:
            logging.exception(error)
            pass
        finally:
            await self.shutdown(None, None)

    async def shutdown(self, _signal, _frame):
        if self.scheduler.running:
            logging.info('Shutting down...')
            self.scheduler.shutdown()
            sys.exit(0)

    async def create_ticket(self):
        selected_type: TicketType = random.choice(list(TicketType))
        logging.info(f"Create {selected_type.name} ticket on {self.network} network")

        # get random file list from Files dict
        files2use_by_type = Files2Use[selected_type]
        if not files2use_by_type:
            logging.info(f"No files for {selected_type.name} ticket")
            return
        file_list = random.choice(files2use_by_type)

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
            return

        # remove file from list
        files2use_by_type.remove(file_list)
        logging.info(f"File '{file_list}' removed from list")

    async def check_statuses(self):
        logging.info(f"Check ticket registration statuses on {self.network} network")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Pastel Network Maker')
    parser.add_argument('-n', '--network', type=str, required=True, help='Network to use - mainnet or testnet')
    parser.add_argument('-k', '--api-key', type=str, required=True, help='API Key to use')
    parser.add_argument('-l', '--logfile', type=str, required=False, help='Log file')
    args = parser.parse_args()

    setup_logging(args.logfile)

    maker = NetworkMaker(args.network, args.api_key)
    asyncio.run(maker.run())
