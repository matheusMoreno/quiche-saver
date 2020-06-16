"""Main program to the Telegram bot.
For future versions: add a ConversationHandler for the add and remove.
Transform floats into Decimals for better precision."""

import sys
import time
import threading
import logging
import requests

from telegram.ext import CommandHandler, Filters, MessageHandler, Updater
from quichesaver.conf.settings import TELEGRAM_TOKEN
from quichesaver.product import Product


LOGGER = logging.getLogger(__name__)

MAX_ITEMS = 100              # Max number of items per user
MONITOR_INTERVAL = 2 * 60    # Interval between updates, in seconds
ITEM_INTERVAL = 2            # Interval between each individual item check.
                             # Keep it low so that site doesn't block you


def monitor_items(update, context):
    """Monitor the items informed by the user."""
    while True:
        # Since it's possible that we modify the list, we need a lock
        with context.user_data["lock"]:
            matched = [False] * len(context.user_data["products"])

            # Checking the price for each item
            for i in range(len(context.user_data["products"])):
                info_old = context.user_data["products"][i].get_product_info()
                info = {}

                # If there is a problem getting the product, just ignore it
                # It would be best to have a timeout and drop the product
                try:
                    info = context.user_data["products"][i].update_product_info()
                except Exception as exc:
                    LOGGER.error("Error updating product: %s", exc)

                LOGGER.info("Old info: %s; new info: %s", info_old, info)

                # Informing if the product is back in stock
                if not info_old["available"] and info["available"]:
                    message = f"The product {info['name']} is back in stock, "\
                              f"costing R$ {format(info['price'], '.2f')}."\
                              f" {info['url']}"
                    update.message.reply_text(message)

                # Informing if the product is below the max price
                if info["available"] and info["price"] <=\
                   context.user_data["products"][i].max_price:
                    message = f"Hey!! The item {info['name']} is now costing "\
                              f"R$ {format(info['price'], '.2f')}! Go buy it! I "\
                              f"will stop monitoring it. {info['url']}"
                    update.message.reply_text(message)
                    matched[i] = True

                time.sleep(ITEM_INTERVAL)

            # Removing the matched items
            context.user_data["products"] = [elem for i, elem in \
                enumerate(context.user_data["products"]) if not matched[i]]

        # Relase the lock and wait for the next round
        time.sleep(MONITOR_INTERVAL)


def start(update, context):
    """Start the bot."""
    greeting = "Hi! I'll be your price monitor today.\n\nTip: if the product"\
               " link contains spaces, replace them for '%20', so that the"\
               " bot can successfully retrieve the info.\n\n"
    update.message.reply_text(greeting)
    show_help(update, context)

    context.user_data["products"] = []
    context.user_data["lock"] = threading.RLock()
    context.user_data["thread"] = threading.Thread(target=monitor_items,
                                                   args=(update, context))
    context.user_data["thread"].start()
    LOGGER.info("Started thread %s", context.user_data["thread"])


def show_help(update, context):
    """Send basic usage and store list."""
    response = "Available commands:\n"\
               "  - Start monitoring a product: /add <link> <desired price>\n"\
               "  - Stop monitoring a product: /remove <product ID>\n"\
               "  - List products and prices: /status\n"\
               "  - List commands and stores: /help\n\n"\
               "Available stores for monitoring:\n" +\
               '\n'.join([f"  - {s}" for s in Product.stores])
    update.message.reply_text(response)


def add_item(update, context):
    """Usage: /add <link> <desired price>"""
    arguments_str = update.message.text.partition(' ')[2]
    arguments = arguments_str.split(' ')

    LOGGER.info("Recieved arguments: %s", arguments)

    # Validating the arguments passed
    try:
        assert len(arguments) == 2
        url = arguments[0]
        price = float(arguments[1].replace(',', '.'))
    except (AssertionError, ValueError):
        response = "Command usage: /add <link> <desired price>\n"\
                   "Tip: write the price as XXXXXX,XX or XXXXXX.XX, with no"\
                   " currency symbols."
        update.message.reply_text(response)
        return

    # Try to instantiate a new Product object
    try:
        new_prod = Product(url, price)
    except (ValueError, requests.RequestException):
        response = "There was a problem retrieving the product. Please "\
                   "check if the store is accepted by the bot and if the "\
                   "link is not broken."
        update.message.reply_text(response)
        return

    # We need to acquire the lock add a new product to the list
    with context.user_data["lock"]:
        if len(context.user_data["products"]) > MAX_ITEMS:
            response = "You're monitoring too many items! Remove some."
            update.message.reply_text(response)
            return

        context.user_data["products"].append(new_prod)

    response = f"Ok, I am now monitoring the product {new_prod.name} at the "\
               f"store {new_prod.store}. I'll warn you when the price drops "\
               f"to R$ {format(new_prod.max_price, '.2f')} or less."
    update.message.reply_text(response)


def remove_item(update, context):
    """Stop monitoring for a product."""
    index_str = update.message.text.partition(' ')[2]
    item_removed = None

    # Check if the value passed was a valid number (int and in range)
    with context.user_data["lock"]:
        try:
            index = int(index_str) - 1
            item_removed = context.user_data["products"].pop(index)
        except (ValueError, IndexError):
            response = "There was a problem removing the product. Did you "\
                       "pass the right product ID?"
            update.message.reply_text(response)
            return

    # This if is unecessary, but better safe than sorry
    if item_removed:
        response = f"The product {item_removed.name} from the store "\
                   f"{item_removed.store} was successfully removed."
        update.message.reply_text(response)


def status(update, context):
    """Check the status of each product."""
    response = "I'm currently monitoring the following items:\n"
    update.message.reply_text(response)

    with context.user_data["lock"]:
        if not context.user_data["products"]:
            response = "Wow! Nothing!"
            update.message.reply_text(response)

        # List the items
        for i, prod in enumerate(context.user_data["products"]):
            msg_price = f"Current price: R$ {format(prod.price, '.2f')}\n\n" if \
                        prod.available else "Currently unavailable\n\n"
            response = f"[ID {i + 1}] {prod.name} at {prod.store}\n" + msg_price
            update.message.reply_text(response)


def ping(update, context):
    """Ping the bot."""
    response = "Pong!"
    update.message.reply_text(response)


def unknown(update, context):
    """Default answer to random commands."""
    response = "I don't know what you want me to do."
    update.message.reply_text(response)


def main():
    """Main function for the bot."""
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    disp = updater.dispatcher

    # Handle the commands
    disp.add_handler(CommandHandler('start', start))
    disp.add_handler(CommandHandler('ping', ping))
    disp.add_handler(CommandHandler('help', show_help))
    disp.add_handler(CommandHandler('add', add_item))
    disp.add_handler(CommandHandler('remove', remove_item))
    disp.add_handler(CommandHandler('status', status))
    disp.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    file_handler = logging.FileHandler("quichesaver.log")
    stdout_handler = logging.StreamHandler(sys.stdout)

    logging.basicConfig(format="%(asctime)s %(levelname)s    %(message)s",
                        handlers=(file_handler, stdout_handler),
                        level=logging.INFO)

    print("Press Ctrl-C to stop the bot.")
    main()
