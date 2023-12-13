from telethon import TelegramClient, events
from telethon.errors import FloodWaitError
import asyncio
import datetime

api_id = '22453502'
api_hash = '0719fac747ce39c31d3f73216f6dd8fd'

client = TelegramClient('sesja', api_id, api_hash)

async def forward_message():
    channel_id = -1002037820955  # Dla kanału; użyj -2037820955 dla grupy
    message_id = 3

    while True:
        # Pobranie wiadomości
        message = await client.get_messages(channel_id, ids=message_id)

        # Pobranie aktywnych grup
        groups = await client.get_dialogs(limit=20)
        sent_count = 0

        # Przekazywanie wiadomości do grup
        for group in groups:
            if group.is_group and sent_count < 20:  # ograniczenie do 20 grup
                try:
                    await client.forward_messages(group.id, message)
                    sent_count += 1
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"[{current_time}] Pomyślnie wysłano wiadomość na '{group.name}'")
                    await asyncio.sleep(2)  # krótsze opóźnienie
                except FloodWaitError as e:
                    print(f"Tryb spowolnienia aktywny, czekam {e.seconds} sekund.")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"[{current_time}] Nie udało się wysłać wiadomości na '{group.name}': {e}")

        print("Przerwa 1 minuta przed kolejną rundą wysyłania wiadomości.")
        await asyncio.sleep(60)  # krótsza przerwa

with client:
    client.loop.run_until_complete(forward_message())
