import json
import datetime
from telethon import TelegramClient, events
from telethon.tl.custom import Button
import math

from collections import defaultdict

# API credentials and bot token
api_id = "23871558"
api_hash = "80bfa6f40cec8c438dcb6f5a96ac3778"
bot_token = "7062746636:AAGZPknLiptkdymOG84bOf_iDcZ6Q89Ca18"

# List of allowed user IDs
allowed_user_ids = ["6551761715", "987654321"]

# Initialize Telethon client
client = TelegramClient("bot_session", api_id, api_hash).start(bot_token=bot_token)

# Path to JSON database file
database_path = "database.json"

# --- Database Functions ---
def load_database():
    try:
        with open(database_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_database(data):
    with open(database_path, "w") as file:
        json.dump(data, file)


database = load_database()


def is_allowed_user(user_id):
    return str(user_id) in allowed_user_ids


# --- Menu Functions ---
def create_main_menu():
    buttons = [
        [
            Button.inline("👤 Sprzedawcy", b"sellers"),
            Button.inline("✨ Dodaj", b"one_time_sales"),
        ],
        [Button.inline("📈 Statystyki", b"stats")],
        [Button.inline("⚙️ Admin", b"admin")]
    ]
    return buttons


def create_admin_menu():
    buttons = [
        [Button.inline("💰 Zmień Saldo", b"change_balance")],  
        [Button.inline("🔙 Wróć", b"back")]
    ]
    return buttons

@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    user_id = event.sender_id
    user_name = event.sender.username if event.sender.username else "Nieznajomy"  # Use "Nieznajomy" if no username
    saldo = database.get("saldo", 0)
    
    message = f"""
👋 Witaj, {user_name}!

💰 **Aktualne saldo:** {saldo} zł

__Wersja 0.1__
    """  # Multiline string with emojis and Markdown formatting

    await event.respond(message, buttons=create_main_menu(), parse_mode="markdown") 



@client.on(events.CallbackQuery(data=b"stats"))
async def show_stats(event):
    weekly_stats_message = generate_weekly_stats()
    daily_stats_message = generate_daily_stats()
    await event.edit(
        f"{weekly_stats_message}\n{daily_stats_message}",
        buttons=[Button.inline("Wróć", b"back")],
        parse_mode="markdown",
    )


def generate_weekly_stats(week_start=None):
    if week_start is None:
        week_start = datetime.datetime.now() - datetime.timedelta(days=7)

    week_sales = defaultdict(lambda: {"amount": 0, "sales": 0})

    for seller_name, seller_data in database.get("sellerzy", {}).items():
        for day_str, day_data in seller_data.items():
            try:
                day = datetime.datetime.strptime(day_str, "%Y-%m-%d")
                if week_start <= day <= week_start + datetime.timedelta(days=6):
                    week_sales[seller_name]["amount"] += day_data["amount"]
                    week_sales[seller_name]["sales"] += day_data["sales"]
            except ValueError:  # Ignore non-date keys
                pass

    stats_message = "**Statystyki sprzedaży tygodniowe:**\n\n"
    for seller_name, data in week_sales.items():
        stats_message += (
            f"- **{seller_name}:** {data['amount']} zł ({data['sales']} sprzedaży)\n"
        )
    return stats_message


def generate_daily_stats():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    daily_sales = defaultdict(lambda: {"amount": 0, "sales": 0})

    for seller_name, seller_data in database.get("sellerzy", {}).items():
        if today in seller_data:
            daily_sales[seller_name] = seller_data[today]

    stats_message = "**Statystyki sprzedaży z dzisiaj:**\n\n"
    for seller_name, data in daily_sales.items():
        stats_message += (
            f"- **{seller_name}:** {data['amount']} zł ({data['sales']} sprzedaży)\n"
        )
    return stats_message


@client.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()

    if data == "sellers":
        await show_sellers(event, page=1)

    elif data.startswith("seller_page_"):
        page = int(data.split("_")[-1])
        await show_sellers(event, page=page)

    elif data.startswith("seller_"):
        seller_name = data[7:]  # Extract seller_name without encoding/decoding
        await show_seller_info(event, seller_name)
    elif data == "admin":
        await event.edit("Panel administratora:", buttons=create_admin_menu())

    elif data == "change_balance":
        async with client.conversation(event.sender_id) as conv:
            await conv.send_message("Podaj nowe saldo (w zł):")
            new_balance_msg = await conv.get_response()
            try:
                new_balance = int(new_balance_msg.text)
            except ValueError:
                await conv.send_message("Nieprawidłowa kwota.")
                return

            buttons = [
                [Button.inline("✅ Tak", b"confirm_balance_change_" + str(new_balance).encode())],
                [Button.inline("❌ Nie", b"back")]
            ]
            await conv.send_message(f"Czy na pewno chcesz zmienić saldo na {new_balance} zł?", buttons=buttons)

    elif data.startswith("confirm_balance_change_"):
        new_balance_str = data[22:].lstrip("_")  # Remove any leading underscores
        try:
            new_balance = int(new_balance_str)
            database["saldo"] = new_balance
            save_database(database)
            await event.edit(f"Saldo zmienione na {new_balance} zł", buttons=create_main_menu())
        except ValueError:  # Handle the case where new_balance_str is not an integer
            await event.edit("Nieprawidłowa kwota. Spróbuj ponownie.", buttons=create_main_menu())

    elif data.startswith("confirm_balance_change_"):
        new_balance = int(data[22:])
        database["saldo"] = new_balance
        save_database(database)
        await event.edit(f"Saldo zmienione na {new_balance} zł", buttons=create_main_menu())

    elif data.startswith("delete_seller_confirm_"):
        seller_name = data[22:]
        if seller_name.startswith("_"):  # Remove leading underscore if present
            seller_name = seller_name[1:]

        if seller_name in database["sellerzy"]:
            del database["sellerzy"][seller_name]
            save_database(database)
            await event.edit(
                f"❌ Sprzedawca '{seller_name}' usunięty.", buttons=create_main_menu()
            )
        else:
            await event.edit(
                f"Sprzedawca '{seller_name}' nie istnieje.", buttons=create_main_menu()
            )

    elif data.startswith("delete_seller_"):
        seller_name = data[13:]
        if seller_name.startswith("_"):  # Remove leading underscore if present
            seller_name = seller_name[1:]

        buttons = [
            [
                Button.inline(
                    "✅ Tak, usuń", b"delete_seller_confirm_" + seller_name.encode()
                ),
                Button.inline("🔙 Nie, wróć", b"sellers"),
            ]
        ]
        await event.edit(
            f"Czy na pewno chcesz usunąć sprzedawcę '{seller_name}'?", buttons=buttons
        )

  
    elif data.startswith("add_sale_"):
        amount, seller_name = data[9:].split("_", 1)
        amount = int(amount)

        seller_data = database["sellerzy"][seller_name]
        seller_data[f"sprzedane_{amount}"] = (
            seller_data.get(f"sprzedane_{amount}", 0) + 1
        )
        seller_data["sprzedane"] = seller_data.get("sprzedane", 0) + amount

        # Combined total quantity for notification check
        total_quantity = (
            seller_data.get("sprzedane_60", 0)
            + seller_data.get("sprzedane_70", 0)
            + seller_data.get("sprzedane_36", 0)
            + seller_data.get("sprzedane_inne", 0)
        )

        day_str = datetime.datetime.now().strftime("%Y-%m-%d")
        seller_data = database["sellerzy"][seller_name]
        if day_str not in seller_data:
            seller_data[day_str] = {"amount": 0, "sales": 0}
        seller_data[day_str]["amount"] += amount
        seller_data[day_str]["sales"] += 1

        if total_quantity > 0 and total_quantity % 5 == 0:
            notification_number = total_quantity // 5
            await send_notification(event.sender_id, notification_number, seller_name)

        # Update overall balance
        database["saldo"] += amount
        save_database(database)
        await event.edit(
            f"Dodano sprzedaż {amount} zł dla {seller_name}", buttons=create_main_menu()
        )

    elif data.startswith("dismiss_notification_"):
        seller_name = data[21:]
        seller_data = database["sellerzy"][seller_name]

        # Reset notifications and acknowledged counters
        seller_data["acknowledged"] = 0
        total_quantity = (
            seller_data.get("sprzedane_60", 0)
            + seller_data.get("sprzedane_70", 0)
            + seller_data.get("sprzedane_inne", 0)
        )
        seller_data["notifications"] = total_quantity // 5

        save_database(database)
        await event.delete()
        # Refresh the seller info to reflect the changes
        await show_seller_info(event, seller_name)

    elif data == "back":


        user_id = event.sender_id
        user_name = event.sender.username if event.sender.username else "Nieznajomy"  # Use "Nieznajomy" if no username
        saldo = database.get("saldo", 0)
        
        message = f"""
👋 Witaj, {user_name}!

💰 **Aktualne saldo:** {saldo} zł

__Wersja 0.1__
        """  # Multiline string with emojis and Markdown formatting
        await event.edit(
            message, buttons=create_main_menu()
        )  # Display the welcome message and menu

    elif data == "one_time_sales":
        await handle_one_time_sale(event)


# --- Notification Function ---
async def send_notification(user_id, notification_number, seller_name):
    timestamp = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
    message = f"""**5 nowych zamówień u sprzedawcy {seller_name}** Wiadomość: `#{notification_number} - 5 zamówień | {timestamp} | {seller_name}`"""
    await client.send_message(
        user_id,
        message,
        buttons=[
            Button.inline("Odnotuj", b"dismiss_notification_" + seller_name.encode())
        ],
    )


async def handle_one_time_sale(event):
    buttons = [
        [Button.inline("70 zł", b"add_one_time_sale_70")],
        [Button.inline("50 zł", b"add_one_time_sale_50")],
        [Button.inline("36 zł", b"add_one_time_sale_36")],
        [Button.inline("Inne", b"add_one_time_sale_other")],
        [Button.inline("Wróć", b"back")],
    ]
    await event.edit("Wybierz kwotę jednorazowej sprzedaży:", buttons=buttons)


@client.on(
    events.CallbackQuery(data=lambda data: data.startswith(b"add_one_time_sale_"))
)
async def handle_add_one_time_sale_choice(event):
    data = event.data.decode()
    if data == "add_one_time_sale_other":
        async with client.conversation(event.sender_id) as conv:
            await conv.send_message("Podaj kwotę jednorazowej sprzedaży:")
            amount_msg = await conv.get_response()
            try:
                amount = int(amount_msg.text)  # Poprawne pobranie kwoty
            except ValueError:
                await conv.send_message("Nieprawidłowa kwota.")
                return
    else:
        amount = int(
            data.split("_")[-1]
        )  # Extract last part of data after underscores ('70', '50', or '36')

    database["saldo"] += amount
    save_database(database)

    # Odświeżenie salda w wiadomości
    user_name = event.sender.username if event.sender.username else "Unknown"
    message = f"Witaj, {user_name}!\n\nSaldo: {database.get('saldo', 0)} zł"

    await event.edit(message, buttons=create_main_menu())


async def show_seller_info(event, seller_name):
    seller_data = database.get("sellerzy", {}).get(seller_name, {})
    total_sold_60 = seller_data.get("sprzedane_60", 0) * 60
    total_sold_70 = seller_data.get("sprzedane_70", 0) * 70
    total_sold_36 = seller_data.get("sprzedane_36", 0) * 36  # Calculate total for 36 zł
    total_sold_other = seller_data.get("sprzedane_inne", 0)
    total_sold = total_sold_60 + total_sold_70 + total_sold_36 + total_sold_other
    total_quantity = (
        seller_data.get("sprzedane_60", 0)
        + seller_data.get("sprzedane_70", 0)
        + seller_data.get("sprzedane_36", 0)
        + seller_data.get("sprzedane_inne", 0)
    )

    # Calculate notifications (reset when acknowledged)
    notifications = seller_data.get("notifications", total_quantity // 5)

    # If all notifications are acknowledged, reset the counter
    if notifications == seller_data.get("acknowledged", 0):
        seller_data["notifications"] = total_quantity // 5
        seller_data["acknowledged"] = 0
        save_database(database)

    acknowledged = seller_data.get("acknowledged", 0)

    message = (
        f"**Panel sprzedawcy:** `{seller_name}`\n\n"
        f"**Łącznie sprzedane:** `{total_quantity}` (`{total_sold} zł`)\n"
        f'- `60 zł:` {seller_data.get("sprzedane_60", 0)} szt. (`{total_sold_60} zł`)\n'
        f'- `70 zł:` {seller_data.get("sprzedane_70", 0)} szt. (`{total_sold_70} zł`)\n'
        f'- `36 zł:` {seller_data.get("sprzedane_36", 0)} szt. (`{total_sold_36} zł`)\n'  # Added line for 36 zł
        f'- `Inne:` {seller_data.get("sprzedane_inne", 0)} szt. (`{total_sold_other} zł`)\n\n'
        f"**Odnotowano:** {notifications}\n"
    )

    buttons = [
        [
            Button.inline(
                "Dodaj sprzedaż: 70 zł", b"add_sale_70_" + seller_name.encode()
            )
        ],
        [
            Button.inline(
                "Dodaj sprzedaż: 60 zł", b"add_sale_60_" + seller_name.encode()
            )
        ],
        [
            Button.inline(
                "Dodaj sprzedaż: 36 zł", b"add_sale_36_" + seller_name.encode()
            )
        ],
        [
            Button.inline("💰 Inne", b"add_other_sale_" + seller_name.encode())
        ],  # "Inne" button
        [
            Button.inline(
                "🗑️ Usuń sprzedawcę", b"delete_seller_" + seller_name.encode()
            )
        ],  # Delete button
        [Button.inline("🔙 Wróć", b"sellers")],
    ]

    await event.edit(message, buttons=buttons, parse_mode="markdown")


@client.on(events.CallbackQuery(data=b"add_seller"))
async def handle_add_seller(event):
    async with client.conversation(event.sender_id) as conv:
        await conv.send_message("Podaj nazwę nowego sprzedawcy:")
        seller_name_msg = await conv.get_response()
        seller_name = seller_name_msg.text.strip()

        if not seller_name:
            await conv.send_message("Nazwa sprzedawcy nie może być pusta.")
            return

        if seller_name in database["sellerzy"]:
            await conv.send_message(
                f"Sprzedawca o nazwie '{seller_name}' już istnieje."
            )
            return

        # Inicjalizacja danych nowego sprzedawcy
        database["sellerzy"][seller_name] = {
            "sprzedane": 0,
            "sprzedane_60": 0,
            "sprzedane_70": 0,
            "sprzedane_36": 0,
            "sprzedane_inne": 0,
            "notifications": 0,
            "acknowledged": 0,
        }
        save_database(database)

        await conv.send_message(
            f"Dodano nowego sprzedawcę: '{seller_name}'", buttons=create_main_menu()
        )


@client.on(events.CallbackQuery(data=lambda data: data.startswith(b"add_other_sale_")))
async def handle_add_other_sale(event):
    seller_name = event.data.decode()[14:]

    if seller_name.startswith("_"):
        seller_name = seller_name[1:]

    async with client.conversation(event.sender_id) as conv:
        await conv.send_message("Podaj kwotę sprzedaży:")
        amount_msg = await conv.get_response()
        try:
            amount = int(amount_msg.text)
        except ValueError:
            await conv.send_message("Nieprawidłowa kwota.")
            return

        seller_data = database["sellerzy"].get(seller_name)
        if seller_data:
            seller_data["sprzedane_inne"] += amount
            seller_data["sprzedane"] += amount

            # Update daily stats
            day_str = datetime.datetime.now().strftime("%Y-%m-%d")
            if day_str not in seller_data:
                seller_data[day_str] = {"amount": 0, "sales": 0}
            seller_data[day_str]["amount"] += amount
            seller_data[day_str]["sales"] += 1

            # Update overall balance
            database["saldo"] += amount

            save_database(database)
            await conv.send_message(
                f"Dodano sprzedaż {amount} zł dla {seller_name}",
                buttons=create_main_menu(),
            )
        else:
            await conv.send_message("Sprzedawca nie znaleziony.")


# Function to display sellers list
async def show_sellers(event, page=1):
    sellers = list(database.get("sellerzy", {}).keys())
    sellers_per_page = 5

    total_pages = math.ceil(len(sellers) / sellers_per_page)
    if page > total_pages:
        page = total_pages
    if page < 1:
        page = 1

    start_index = (page - 1) * sellers_per_page
    end_index = start_index + sellers_per_page

    buttons = []
    for seller in sellers[start_index:end_index]:
        buttons.append([Button.inline(seller, b"seller_" + seller.encode())])

    buttons.append(
        [
            Button.inline("➕ Dodaj sprzedawcę", b"add_seller"),
            Button.inline("🔙 Wróć", b"back"),
        ]
    )

    # Pagination buttons
    if total_pages > 1:
        pagination_buttons = []
        if page > 1:
            pagination_buttons.append(
                Button.inline("⬅️ Poprzednia", b"seller_page_" + str(page - 1).encode())
            )
        if page < total_pages:
            pagination_buttons.append(
                Button.inline("➡️ Następna", b"seller_page_" + str(page + 1).encode())
            )
        buttons.append(pagination_buttons)

    await event.edit(
        "Wybierz sprzedawcę (Strona {}/{}):".format(page, total_pages), buttons=buttons
    )




# Run the client
client.run_until_disconnected()
