# consumer.py

import asyncio
import os
import pika
import logging
import json
import time
from dotenv import load_dotenv
from aiohttp import ClientSession
from utils import fetch_links
from colorlog import ColoredFormatter

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
logging.getLogger("pika").setLevel(logging.WARNING)

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "urls")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
TIMEOUT = int(os.getenv("TIMEOUT", 10))

async def process_message(channel, body, delivery_tag, session):
    try:
        data = json.loads(body)
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
            channel.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=json.dumps(link),
                properties=pika.BasicProperties(
                    delivery_mode=1,
                ))
    except json.JSONDecodeError:
        logging.error("PAGE: Received invalid JSON")
    except Exception as e:
        logging.error(f"PAGE: Error processing message: {e}")
    finally:
        channel.basic_ack(delivery_tag=delivery_tag)

async def consume():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE)

    async with ClientSession() as session:
        last_message_time = time.time()

        while True:
            method_frame, properties, body = channel.basic_get(RABBITMQ_QUEUE, auto_ack=False)
            if method_frame:
                await process_message(channel, body, method_frame.delivery_tag, session)
                last_message_time = time.time()
            else:
                if time.time() - last_message_time > TIMEOUT:
                    logging.info(f"No messages received in the last {TIMEOUT} seconds. Exiting.")
                    break
                await asyncio.sleep(1)

    connection.close()

def main():
    try:
        asyncio.run(consume())
    except KeyboardInterrupt:
        logging.info("Stopping consumer...")

if __name__ == "__main__":
    main()
