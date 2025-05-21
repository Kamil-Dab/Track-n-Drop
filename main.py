import time
import json
import os
from datetime import datetime

# Attempt to import config, if not found, guide user.
try:
    import config
except ImportError:
    print("Error: Configuration file 'config.py' not found.")
    print("Please copy 'config.py.example' to 'config.py' and fill in your details.")
    exit(1)

from service.olx_fetcher import fetch_olx_data, parse_olx_items
from service.telegram_sender import send_telegram_message

NOTIFIED_ITEMS_FILE = getattr(config, 'NOTIFIED_ITEMS_FILE', 'notified_items.json')

def load_notified_items():
    """Loads the set of notified item URLs from a file."""
    if os.path.exists(NOTIFIED_ITEMS_FILE):
        try:
            with open(NOTIFIED_ITEMS_FILE, 'r') as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            print(f"Warning: Could not decode JSON from {NOTIFIED_ITEMS_FILE}. Starting with an empty set.")
            return set()
    return set()

def save_notified_items(notified_urls):
    """Saves the set of notified item URLs to a file."""
    with open(NOTIFIED_ITEMS_FILE, 'w') as f:
        json.dump(list(notified_urls), f)

def check_prices():
    """
    Main function to check prices for all configured products.
    """
    if not hasattr(config, 'PRODUCTS_TO_TRACK') or not config.PRODUCTS_TO_TRACK:
        print("No products configured in 'config.py'. Please add products to PRODUCTS_TO_TRACK.")
        return

    if not hasattr(config, 'TELEGRAM_BOT_TOKEN') or config.TELEGRAM_BOT_TOKEN == "YOUR_ACTUAL_TELEGRAM_BOT_TOKEN" or \
       not hasattr(config, 'TELEGRAM_CHAT_ID') or config.TELEGRAM_CHAT_ID == "YOUR_ACTUAL_TELEGRAM_CHAT_ID":
        print("Telegram Bot Token or Chat ID is not configured correctly in 'config.py'.")
        print("Please update these values to enable notifications.")
        return
        
    notified_items_today = load_notified_items()
    newly_notified_items_session = set()

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting price check...")

    for product_config in config.PRODUCTS_TO_TRACK:
        product_name = product_config.get("name")
        platform = product_config.get("platform")
        target_price = product_config.get("target_price")
        min_price = product_config.get("min_price", 0) # Default min_price to 0 if not specified

        if not all([product_name, platform, target_price is not None]):
            print(f"Skipping invalid product configuration: {product_config}")
            continue

        print(f"Checking '{product_name}' on '{platform}' (Target price: {target_price}, Min price: {min_price})...")

        items_found = []
        if platform.lower() == "olx":
            raw_data = fetch_olx_data(product_name)
            if raw_data:
                items_found = parse_olx_items(raw_data)
        else:
            print(f"Platform '{platform}' is not yet supported.")
            continue

        if not items_found:
            print(f"No items found for '{product_name}' on '{platform}'.")
            continue
        
        print(f"Found {len(items_found)} items for '{product_name}'. Analyzing prices...")
        for item in items_found:
            item_url = item.get('url')
            # Unique identifier for the item to avoid re-notification for the same listing
            # OLX URLs can sometimes have parameters, so we might want to normalize them if needed
            # For now, the full URL is used.
            if item_url in notified_items_today:
                # print(f"Already notified for: {item['title']} ({item_url})")
                continue

            current_price = item.get("price")
            if current_price is not None:
                if min_price <= current_price <= target_price:
                    message = (
                        f"🎉 Price Alert for *{product_name}*! 🎉\\n\\n"
                        f"Item: *{item['title']}*\\n"
                        f"Price: *{item['price']:.2f} {item.get('currency', '')}* (Target: {target_price:.2f})\\n"
                        f"Platform: {platform.upper()}\\n"
                        f"URL: {item['url']}"
                    )
                    print(f"Found matching item: {item['title']} at {item['price']}")
                    send_telegram_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, message)
                    newly_notified_items_session.add(item_url)
                # else:
                #     print(f"Item '{item['title']}' price {current_price} is not within target range [{min_price} - {target_price}].")

    if newly_notified_items_session:
        all_notified_items = notified_items_today.union(newly_notified_items_session)
        save_notified_items(all_notified_items)
        print(f"Updated notified items file: {NOTIFIED_ITEMS_FILE}")
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Price check finished.")


if __name__ == "__main__":
    interval = getattr(config, 'CHECK_INTERVAL_SECONDS', 3600)
    print(f"Price checker started. Will check prices every {interval} seconds.")
    print(f"Press Ctrl+C to stop.")
    
    try:
        while True:
            check_prices()
            print(f"Next check in {interval} seconds...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Price checker stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred in the main loop: {e}")
        # Optionally send a Telegram message about the error
        error_message = f"Price tracker encountered an error: {e}"
        if hasattr(config, 'TELEGRAM_BOT_TOKEN') and hasattr(config, 'TELEGRAM_CHAT_ID'):
             send_telegram_message(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID, error_message)
