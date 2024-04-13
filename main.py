import time
import traceback
from pprint import pprint
import pickledb

import requests
from decouple import config
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler

BSCSCAN_KEY = config("BSCSCAN_KEY")
APP_URL = config("APP_URL")
TOKEN = config("TOKEN")

watch_db = pickledb.load("watch.db", True)


def get_bnb_price() -> float:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return data["binancecoin"]["usd"]
    else:
        return 0.0


# Class to store addresses, previous balances and the Telegram chatID
class WatchEntry:
    def __init__(self, chat_id, eth_address, current_balance, added_time):
        self.chat_id = chat_id
        self.eth_address = eth_address
        self.current_balance = current_balance
        self.added_time = added_time

    def __dict__(self):
        return {
            "chat_id": self.chat_id,
            "eth_address": self.eth_address,
            "current_balance": self.current_balance,
            "added_time": self.added_time,
        }


# Array to store WatchEntry objects
# watch_db = []

# *********************************
# Helper functions
# *********************************


# Function to check if an address is a valid ETH address
def is_address(address):
    address = address.lower()
    if not address.startswith("0x") or len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False


# *********************************
# Telegram bot event listeners
# *********************************


# Telegram error handling
def error_handler(update, context):
    trace = traceback.format_exc()
    pprint(trace)

    print(f"\nError: {context.error}")


# Telegram /start command
def start_command(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(
        chat_id=chat_id,
        text="""🔥🔥🔥🔥🔥\n
Hey there! I am a Telegram bot by @Nimak86.

I am here to watch BNB Smart Chain addresses. I will ping you if there's a change in balance. 
This is useful if you've just sent a transaction and want to be notified when it arrives.
Due to API limitations, I can watch an address for no more than 24 hours.
<b>Commands</b>
    * <code>/watch (address)</code> - start watching an address.
    * <code>/forget (address)</code> - stop watching an address.
    * <a>/list</a> - list the addresses you are watching.
Have fun! 💫💫💫""",
        parse_mode=ParseMode.HTML,
    )


# Telegram /watch command
def watch_command(update, context):
    chat_id = update.effective_chat.id
    eth_address = " ".join(context.args)
    if is_address(eth_address):
        response = requests.get(
            f"https://api.bscscan.com/api?module=account&action=balance&address={eth_address}&tag=latest&apikey={BSCSCAN_KEY}"
        )
        balance_data = response.json()
        current_balance = balance_data["result"]
        timestamp = int(time.time())
        new_entry = WatchEntry(chat_id, eth_address, current_balance, timestamp)
        if not watch_db.exists(f"{chat_id}_{eth_address}"):
            watch_db.set(f"{chat_id}_{eth_address}", new_entry.__dict__())
        balance_to_display = int(current_balance) / 1e18
        balance_to_display = "{:.4f}".format(balance_to_display)
        context.bot.send_message(
            chat_id=chat_id,
            text=f"Started watching the address {eth_address}\nIt currently has {balance_to_display} BNB.",
        )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text="""
            This is not a valid BSC address.
            Type /watch followed by a valid BSC address like this:
            <code>/watch 0xB91986a9854be250aC681f6737836945D7afF6Fa</code>
            """,
            parse_mode=ParseMode.HTML,
        )


# Telegram /forget command
def forget_command(update, context):
    chat_id = update.effective_chat.id
    eth_address = " ".join(context.args)
    if is_address(eth_address):
        # Remove the entry from the watch_db if it exists
        watch_entries = [
            entry
            for entry in watch_db.getall().values()
            if entry.eth_address == eth_address and entry.chat_id == chat_id
        ]
        if len(watch_entries) > 0:
            watch_db.rem(watch_entries[0])
            context.bot.send_message(
                chat_id=chat_id, text=f"Stopped watching the address {eth_address}"
            )
        else:
            context.bot.send_message(
                chat_id=chat_id, text="You are not watching this address."
            )
    else:
        context.bot.send_message(
            chat_id=chat_id,
            text="This is not a valid BSC address.\nType /forget followed by a valid BSC address like this:\n<code>/forget 0xB91986a9854be250aC681f6737836945D7afF6Fa</code>",
            parse_mode=ParseMode.HTML,
        )


# Telegram /list command
def list_command(update, context):
    chat_id = update.effective_chat.id
    watch_entries = []
    # check_balances(context)
    for entry in list(watch_db.getall()):
        if str(entry).startswith(str(chat_id)):
            watch_entries.append(watch_db.get(entry))

    if len(watch_entries) > 0:
        message = "⤵️<b>Addresses you are watching:</b>\n"
        for entry in watch_entries:
            balance_to_display = int(entry["current_balance"]) / 1e18
            balance_to_display = "{:.4f}".format(balance_to_display)
            message += f"\n-<code>{entry['eth_address']}</code> \n\t💰(Balance: {balance_to_display} BNB)\n"
        context.bot.send_message(
            chat_id=chat_id, text=message, parse_mode=ParseMode.HTML
        )
    else:
        context.bot.send_message(
            chat_id=chat_id, text="You are not watching any addresses."
        )


# Function to check for changes in balances
def check_balances(context):
    for en in watch_db.getall():
        entry = watch_db.get(en)
        eth_address = entry["eth_address"]
        chat_id = entry["chat_id"]
        response = requests.get(
            f"https://api.bscscan.com/api?module=account&action=balance&address={eth_address}&tag=latest"
            f"&apikey={BSCSCAN_KEY}"
        )
        balance_data = response.json()
        current_balance = balance_data["result"]
        if current_balance != entry["current_balance"]:
            balance_to_display = int(current_balance) / 1e18
            balance_to_display = "{:.4f}".format(balance_to_display)
            bnb_price = get_bnb_price()
            usd_balance = float(balance_to_display) * bnb_price

            context.bot.send_message(
                chat_id=chat_id,
                text=f"""
The balance of address 🔗{eth_address} has changed.
It is now {balance_to_display} BNB.
The balance in USD is approximately 💰 ${usd_balance:.2f}. """,
            )
            entry["current_balance"] = current_balance
            watch_db.set(f"{chat_id}_{eth_address}", entry)


# *********************************
# Main function
# *********************************


def main():
    # Create the Telegram bot
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the event listeners
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("watch", watch_command))
    dispatcher.add_handler(CommandHandler("forget", forget_command))
    dispatcher.add_handler(CommandHandler("list", list_command))
    dispatcher.add_error_handler(error_handler)

    # Start the bot
    updater.start_polling()

    # Schedule the balance check every 5 minutes
    job_queue = updater.job_queue
    job_queue.run_repeating(check_balances, interval=60, first=0)

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()


if __name__ == "__main__":
    main()
