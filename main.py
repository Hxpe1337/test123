from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
import asyncio
import datetime

api_id = '22453502'
api_hash = '0719fac747ce39c31d3f73216f6dd8fd'
bot_token = '6888167196:AAErMiDXultcjRZhs6ztfi-iBLs-OALyY9A'
group_id = -1001912349765

client = TelegramClient('sesja', api_id, api_hash)

async def forward_message():
    channel_id = -1001912349765
    message_id = 359
    total_sent = 0
    total_failed = 0

    while True:
        message = await client.get_messages(channel_id, ids=message_id)
        groups = await client.get_dialogs(limit=25)
        sent_count = 0

        for group in groups:
            if group.is_group and group.id != group_id and sent_count < 25:
                try:
                    forward_message = await client.forward_messages(group.id, message)
                    sent_count += 1
                    total_sent += 1
                    status = "⛔️ **Status**: Wysłana"
                    forward_link = f"https://t.me/c/{forward_message.to_id.channel_id}/{forward_message.id}"
                    await client.send_message(group_id, f"💎 **WarsawFinest - Bot 24/7**\n\n{status}\n**🟢 Grupa**: [{group.name}]({forward_link})\n🔄 Wysłano: {total_sent}", link_preview=False)
                    await asyncio.sleep(2)
                except FloodWaitError as e:
                    total_failed += 1
                    await client.send_message(group_id, f"💎 **WarsawFinest - Bot 24/7**\n\n⛔️ **Status**: Niewysłana\n**🔴 Grupa**: {group.name}\n**🔴 Powód**: Tryb spowolnienia aktywny, czekam {e.seconds} sekund.", link_preview=False)
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    total_failed += 1
                    await client.send_message(group_id, f"💎 **WarsawFinest - Bot 24/7**\n\n⛔️ **Status**: Niewysłana\n**🔴 Grupa**: {group.name}\n**🔴 Powód**: {str(e)}", link_preview=False)

        await client.send_message(group_id, f"💎 **WarsawFinest - Bot 24/7**\n\n⛔️ **Status**: Podsumowanie\n**🟢 Wysłano**: {total_sent}\n**🔴 Nieudane**: {total_failed}", link_preview=False)
        await asyncio.sleep(10)


with client:
    client.loop.run_until_complete(forward_message())
