import logging
import asyncio
import os
import re
import uuid
import aiohttp
import requests
from telegram import ForceReply, Update
from telegram.ext import *
from instagrapi import Client

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

tokens = "xxxxxxxxxxxx"

INSTAGRAM_USERNAME = "abc@gmail.com"
INSTAGRAM_PASSWORD = "abc"

RETRY_LIMIT = 3
RETRY_DELAY = 10

# Initialize Instagram client
instagrapi_client = Client()

# Set up logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def login_instagram():
    instagrapi_client.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)

def extract_cdn_url(response_text):
        pattern = r'https://cdn\.downloadgram\.org/[^"\\]+'
        match = re.search(pattern, response_text)
        if match:
            return match.group(0)
        else:
            return None

async def get_video_url(link):
    url = "https://api.downloadgram.org/media"
    headers = {
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://downloadgram.org",
        "referer": "https://downloadgram.org/",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36"
    }
    data = {
        "url": f"{link}"
    }
    response = requests.post(url, headers=headers, data=data)
    url = extract_cdn_url(response.text)
    if url:
        return url
    else:
        return None

async def download_video(video_url):
    file_name = f"video_{uuid.uuid4().hex}.mp4"
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(file_name, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                return file_name

async def upload_video(video_path, caption=""):
    retries = 0
    while retries < RETRY_LIMIT:
        try:
            print(f"Uploading: {video_path}")
            media = instagrapi_client.video_upload(video_path, caption=caption)
            print(f"Video uploaded successfully: {media.pk}")
            return True
        except Exception as e:
            print(f"Upload failed: {e}")
            retries += 1
            print(f"Retrying ({retries}/{RETRY_LIMIT}) in {RETRY_DELAY} seconds...")
            await asyncio.sleep(RETRY_DELAY)
    return False


async def handle_instagram_url(update: Update, context: CallbackContext):
    message = update.message.text
    if "instagram.com" not in message:
        await update.message.reply_text("Please provide a valid Instagram reel URL.")
        return

    await update.message.reply_text("Processing your request...")
    video_url = await get_video_url(message)
    
    if not video_url:
        await update.message.reply_text("Invalid Instagram URL or failed to retrieve the reel.")
        return

    # Download video

    video_path = await download_video(video_url)
    await update.message.reply_text(f"Video downloaded successfully: {video_path}")

    # Upload to Instagram
    await login_instagram()
    craption = """Read More 👇

***** All Airdrop Links in Bio *****

Ten Unknown Facts About #BMW

1. Founding and History: BMW, Bayerische Motoren Werke AG, was founded in 1916 in Munich, Germany, initially producing aircraft engines. The company transitioned to motorcycle production in the 1920s and eventually to automobiles in the 1930s.

2. Iconic Logo: The BMW logo, often referred to as the "roundel," consists of a black ring intersecting with four quadrants of blue and white. It represents the company's origins in aviation, with the blue and white symbolizing a spinning propeller against a clear blue sky.

3. Innovation in Technology: BMW is renowned for its innovations in automotive technology. It introduced the world's first electric car, the BMW i3, in 2013, and has been a leader in developing advanced driving assistance systems (ADAS) and hybrid powertrains.

4. Performance and Motorsport Heritage: BMW has a strong heritage in motorsport, particularly in touring car and Formula 1 racing. The brand's M division produces high-performance variant

The Tesla Cybertruck is an all-elelctric,se Battery-powered light-duty truck unveiled by Tesla, Inc,

Here's a comprehensive overview of its key features and specification:

Tesla Cybertruck Overview

Design in Structure

• Exterior: The cybershrak has a distinctive,
angular stainless steel exoskeleton design for durability and passenger protection. It featured ultra-hard 30X colled-rolled stainless steel and armoured glass.

• Dimensions: approximately 231.7 inches long, 79.8 inches wide. and 75 inches tall, with 6.5-foot cargo bed.

Performance and Variants

• Single Motor RWD:
• 0-60 mph: ~6.5 seconds
• Range: ~250 miles
• Towing Capacity: 7,500 pounds
• Dual Motor AWD:
• 0-60 mph: ~4.5 seconds
• Range: ~300 milesal • Towing Capacity: 10,000 pounds
• Tri-Motor AWD:
• 0-60 mph: ~2.9 seconds
• Range: ~500 miles
• Towing Capacity: 14,000 pounds

#viral #caption #trend #instagram """
    success = await upload_video(video_path, craption)
    
    if success:
        await update.message.reply_text("Reel uploaded to Instagram successfully!")
        if os.path.exists(video_path):
            await asyncio.to_thread(os.remove, video_path)
            await asyncio.to_thread(os.remove, f"{video_path}.jpg")
            await update.message.reply_text("Video file deleted from the system.")
    else:
        await update.message.reply_text("Failed to upload reel after multiple attempts.")

# Start command handler
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Send me an Instagram reel URL and I'll handle the rest!")

def main() -> None:
    application = Application.builder().token(f"{tokens}").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_instagram_url))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
