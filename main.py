import re
import os
import whois
import time
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup
from telebot import types
from datetime import datetime, timedelta
from telethon import TelegramClient, events, sync
from telethon.errors import FileMigrateError
from markdownv2 import *
from config import *


async def extract_data(text):
    try:
        data = {
            'token_full_name': None,
            'token_symbol': None,
            'token_contract': None,
            'token_type': None,
            'token_total_supply': None,
            'token_tax': None,
            'deployer_link': None,
            'deployer_address': None,
            'contract_age': None,
            'contract_balance': None,
            'deployed_from': None,
            'deployed_from_link': None,
            'total_txs': None,
            'contract_description': None,
            'mint_link': None,
            'signature_link': None,
        }

        patterns = {
            'token_full_name': r"Token Details:\s*\n\n(.+?) \(",
            'token_symbol': r"\((.+?)\)",
            'token_contract': r"`([A-Za-z0-9]+)`",
            'token_type': r"Type: (.+?) \(",
            'token_total_supply': r"Supply: ([\d,]+)",
            'token_tax': r"Tax: ([\d%]+)",
            'deployer_link': r"\[Deployer\]\((https?://[^\s]+)\)",
            'deployer_address': r"\n`([A-Za-z0-9]+)`",
            'contract_age': r"Age: (.+?)\n",
            'contract_balance': r"Balance: ([\d.]+) SOL",
            'total_txs': r"Txs: (\d+)",
            'contract_description': r"Description:\n\n([\s\S]+?)(?=\n🍌 Token Details|$)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.DOTALL)
            if match:
                data[key] = match.group(1).strip()

        mint_match = re.search(r"\(Mint \((https?://[^\s]+)\)", text)
        if mint_match:
            data['mint_link'] = mint_match.group(1)

        signature_link_pattern = r"https://solscan\.io/tx/[A-Za-z0-9_-]+"
        matches = re.findall(signature_link_pattern, text)
        for match in matches:
            data['signature_link'] = match

        deployed_from_match = re.search(r"💰 From: (.+?) \((https?://[^\s]+)\)", text)
        if deployed_from_match:
            data['deployed_from'] = deployed_from_match.group(1)
            data['deployed_from_link'] = deployed_from_match.group(2)
        else:
            deployed_from_match = re.search(r"💰 From: (.+)", text)
            if deployed_from_match:
                data['deployed_from'] = deployed_from_match.group(1)

        return data
    except Exception as error:
        print(error)


async def safe_download_media(client, message, filename):
    file_path = path_to_photo + filename
    try:
        await client.download_media(message.photo, file=file_path)
    except FileMigrateError as e:
        new_client = await client.migrate_to(e.new_dc)
        await new_client.download_media(message.photo, file=file_path)
        print("migration to new media server")


async def last_msg_id(client):
    channel = await client.get_entity(channel_id)
    last_msg = []
    async for message in client.iter_messages(channel, reverse=False):
        if len(last_msg) == 0:
            # timestamp = int(time.time())
            # filename = f"{timestamp}"
            await asyncio.sleep(10)

            last_msg.append((message.id, message.text))

            data = await extract_data(last_msg[0][1])
            filename = data["token_symbol"]

            file_path = path_to_photo + f"{filename}.jpg"
            if os.path.exists(file_path):
                pass
            else:
                try:
                    post_id = await client.get_messages(channel_id, ids=message.id)
                    await safe_download_media(client, message, f'{filename}.jpg')
                except Exception as error:
                    print(error)
                    print("Photo didnt downloaded")

            return last_msg[0], filename


async def check_last_msg():
    try:
        async with TelegramClient(session, api_id, api_hash) as client:
            last_m, img_name = await last_msg_id(client)

        while True:
            async with TelegramClient(session, api_id, api_hash) as client:
                new_m, img_name = await last_msg_id(client)
                file_path = path_to_photo + f'{img_name}.jpg'
                if new_m[0] > last_m[0]:
                    print(new_m[0])
                    data = await extract_data(new_m[1])

                    if data["contract_description"] != None:
                        msg_free = ('🧟‍♂️ New Token Launched on SOLANA:\n\n'
                                    f'Token Name: **{data["token_full_name"]}**\n'
                                    f'Token Symbol: {data["token_symbol"]}\n\n'
                                    'Contract ID:\n'
                                    f'`{data["token_contract"]}`\n\n'
                                    f'🧟‍♂️ Type: **{data["token_type"]}**\n'
                                    f'[Mint View](https://solscan.io/token/{data["token_contract"]}) **|** [Signature View]({data["signature_link"]})\n\n'
                                    f'🧟‍♂️ Supply: **{data["token_total_supply"]}**\n'
                                    f'🚕 Tax: **{data["token_tax"]}**\n\n'
                                    f'[📖 Deployer address:]({data["deployer_link"]})\n'
                                    f'`{data["deployer_address"]}`\n'
                                    f'  💰 Age: **{data["contract_age"]}**\n'
                                    f'  💰 Balance: **{data["contract_balance"]} SOL**\n'
                                    f'  💰 From: **{data["deployed_from"]}**\n'
                                    f'  💰 Txs: **{data["total_txs"]}**\n\n'
                                    '📝 Description:\n\n'
                                    f'{data["contract_description"]}')
                    else:
                        msg_free = ('🧟‍♂️ New Token Launched on SOLANA:\n\n'
                                    f'Token Name: **{data["token_full_name"]}**\n'
                                    f'Token Symbol: {data["token_symbol"]}\n\n'
                                    'Contract ID:\n'
                                    f'`{data["token_contract"]}`\n\n'
                                    f'🧟‍♂️ Type: **{data["token_type"]}**\n'
                                    f'[Mint View](https://solscan.io/token/{data["token_contract"]}) **|** [Signature View]({data["signature_link"]})\n\n'
                                    f'🧟‍♂️ Supply: **{data["token_total_supply"]}**\n'
                                    f'🚕 Tax: **{data["token_tax"]}**\n\n'
                                    f'[📖 Deployer address:]({data["deployer_link"]})\n'
                                    f'`{data["deployer_address"]}`\n'
                                    f'  💰 Age: **{data["contract_age"]}**\n'
                                    f'  💰 Balance: **{data["contract_balance"]} SOL**\n'
                                    f'  💰 From: **{data["deployed_from"]}**\n'
                                    f'  💰 Txs: **{data["total_txs"]}**\n')

                    button_list1 = [
                        types.InlineKeyboardButton("🧟‍♂️ Snipe the token Launch - ZOMBYGUN 🧟‍♂️", url="https://t.me/zombygun_bot"),
                    ]
                    reply_markup = types.InlineKeyboardMarkup([button_list1])

                    msg_free = escape(msg_free, flag=0)

                    signature_free = "\n\n⚡️ [NewDeploy Solana](https://t.me/NewDeploy_solana) ⚡️"
                    signature_paid = "\n\n⚡️ [NewDeployAI Solana](https://t.me/NewDeployAI_solana) ⚡️"

                    bot = AsyncTeleBot(token)

                    try:
                        if os.path.exists(file_path):
                            with open(file_path, 'rb') as photo:
                                await bot.send_photo(chat_id=post_free_channel_id, photo=photo, caption=msg_free + signature_free, reply_markup=reply_markup, parse_mode='MarkdownV2')
                        else:
                            await bot.send_message(chat_id=post_free_channel_id, text=msg_free + signature_free, reply_markup=reply_markup, parse_mode='MarkdownV2', disable_web_page_preview=True)
                    except Exception as error:
                        print(error)
                        break
                    # try:
                    #     website_links_pattern = r"https?://(?!t\.me|twitter\.com|x\.com|bit\.ly|dexscreener\.com|dexcheck\.com|solscan\.io|solscan\.io)[\w.-]+"
                    #     website_links = re.findall(website_links_pattern, data["contract_description"])
                    #     unique_website_links = list(set(website_links))
                    #     if len(unique_website_links) > 0:
                    #
                    #
                    #         w = whois.whois(unique_website_links[0])
                    #         creation_domain_date = w.creation_date
                    #
                    #
                    #         current_date = datetime.now()
                    #         creation_date = datetime.strptime(creation_domain_date, "%Y-%m-%d")
                    #         difference = current_date - creation_date
                    #         if difference.days > 15:
                    #             if os.path.exists(file_path):
                    #                 with open(file_path, 'rb') as photo:
                    #                     bot.send_photo(chat_id=post_paid_channel_id, photo=photo, caption=msg_free + signature_paid, reply_markup=reply_markup, parse_mode='MarkdownV2')
                    #             else:
                    #                 bot.send_message(chat_id=post_paid_channel_id, text=msg_free + signature_paid, reply_markup=reply_markup, parse_mode='MarkdownV2', disable_web_page_preview=True)
                    # except:
                    #     pass
                break
    except Exception as error:
        print(error)



while True:
    try:
        asyncio.run(check_last_msg())
    except KeyboardInterrupt:
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
