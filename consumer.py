import asyncio
import os
import logging
import json
import time
from dotenv import load_dotenv
from aiohttp import ClientSession
from utils import fetch_links
from colorlog import ColoredFormatter
import aio_pika

log_formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
    },
)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(log_formatter)
logger.addHandler(handler)
logging.getLogger("aio_pika").setLevel(logging.WARNING)

logging.getLogger("aiormq").setLevel(logging.WARNING) 

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "urls")
TIMEOUT = int(os.getenv("TIMEOUT", 10))

async def process_message(channel, message, session):
    try:
        data = json.loads(message.body)
        url = data.get("url")
        title = data.get("title", "No title")

        if not url:
            logging.warning("PAGE: URL not found in message. Skipping.")
            return

        links = await fetch_links(url, session, TIMEOUT)
        if not links:
            logging.info(f"PAGE: No internal links found in '{title}'.")
            return

        for link in links:
            link_title = link.get("title", "No title")
            link_url = link.get("url", "No URL")
            logging.debug(f"LINK: Found '{link_title}' -> {link_url}")
            await channel.default_exchange.publish(
                aio_pika.Message(
                    body=json.dumps(link).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=RABBITMQ_QUEUE
            )
    except json.JSONDecodeError:
        logging.error("PAGE: Received invalid JSON")
    except Exception as e:
        logging.error(f"PAGE: Error processing message: {e}")
    finally:
        await message.ack()

async def consume():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(RABBITMQ_QUEUE)

        async with ClientSession() as session:
            last_message_time = time.time()

            while True:
                message = await queue.get(no_ack=False)
                if message:
                    await process_message(channel, message, session)
                    last_message_time = time.time()
                else:
                    if time.time() - last_message_time > TIMEOUT:
                        logging.info(f"No messages received in the last {TIMEOUT} seconds. Exiting.")
                        break
                    await asyncio.sleep(1)

def main():
    try:
        asyncio.run(consume())
    except KeyboardInterrupt:
        logging.info("Stopping consumer...")

if __name__ == "__main__":
    main()
