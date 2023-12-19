from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
import asyncio
import datetime
import requests
import json

api_id = '28557501'
api_hash = '0719fac747ce39c31d3241307c2569b916cf5b27720e257da79f73216f6dd8fd'
webhook_url = "https://discord.com/api/webhooks/1186461345302970378/jPkV4JVpiQZ1QNBXUHnVgxZal83aMbbqvzhjkqwqXrTZajh3RB7K04VXpLKpqWjqzzkV"
group_to_track = -1001871713516

client = TelegramClient('sesja', api_id, api_hash)

def send_to_discord(title, description, footer):
    embed = json.dumps({
        "embeds": [{
            "title": title,
            "description": description,
            "footer": {"text": footer}
        }]
    })
    headers = {"Content-Type": "application/json"}
    response = requests.post(webhook_url, data=embed, headers=headers)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(f"ServiceHeaven - Błąd wysyłania do Discord: {err}")

async def forward_message():
    channel_id = -1002037820955
    message_id = 7
    total_sent = 0
    total_failed = 0

    while True:
        message = await client.get_messages(channel_id, ids=message_id)
        groups = await client.get_dialogs(limit=25)
        sent_count = 0

        for group in groups:
            if group.is_group and sent_count < 25:
                try:
                    await client.forward_messages(group.id, message)
                    sent_count += 1
                    total_sent += 1
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    send_to_discord("ServiceHeaven - Informacja o wysyłaniu wiadomości", f"[{current_time}] Pomyślnie wysłano wiadomość na '{group.name}'", "Made by Hype")
                    await asyncio.sleep(2)
                except FloodWaitError as e:
                    total_failed += 1
                    send_to_discord("ServiceHeaven - Błąd FloodWait", f"Tryb spowolnienia aktywny, czekam {e.seconds} sekund.", "Made by Hype")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    total_failed += 1
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    send_to_discord("ServiceHeaven - Błąd wysyłania", f"[{current_time}] Nie udało się wysłać wiadomości na '{group.name}': {e}", "Made by Hype")

        send_to_discord("ServiceHeaven - Podsumowanie statystyk", f"Wysłano: {total_sent}, Nieudane: {total_failed}", "Made by Hype")
        await asyncio.sleep(10)


with client:
    client.loop.run_until_complete(forward_message())
