# producer.py

import asyncio
import os
import pika
import logging
import json
from dotenv import load_dotenv
import argparse
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

def parse_args():
    parser = argparse.ArgumentParser(description="Process a URL and enqueue internal links.")
    parser.add_argument("url", help="The HTTP(S) URL to process")
    return parser.parse_args()

async def main():
    args = parse_args()
    url = args.url
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    )
    channel = connection.channel()
    channel.queue_declare(queue=RABBITMQ_QUEUE)

    async with ClientSession() as session:
        links = await fetch_links(url, session, TIMEOUT)
        if not links:
            logging.info("PAGE: No links found. Exiting.")
            connection.close()
            return

        for message in links:
            link_title = message.get("title", "No title")
            link_url = message.get("url", "No URL")
            logging.debug(f"LINK: Found '{link_title}' -> {link_url}")
            channel.basic_publish(
                exchange='',
                routing_key=RABBITMQ_QUEUE,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=1,
                ))
    connection.close()

if __name__ == "__main__":
    asyncio.run(main())
