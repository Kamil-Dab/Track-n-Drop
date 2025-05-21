# Track-n-Drop: Price Tracker Bot

This project is a Python-based script to track product prices on various online platforms (starting with OLX) and send notifications via Telegram when a product's price drops below a specified target.

## Features

-   Track prices for multiple products.
-   Initial support for OLX.pl.
-   Telegram notifications for price alerts.
-   Configurable product list and target prices.
-   Avoids re-notifying for already alerted items within a session/day (by storing notified URLs).

## Setup

1.  **Configure the application:**
    *   Copy `config.py.example` to `config.py`:
        ```bash
        cp config.py.example config.py
        ```
    *   Edit `config.py` and fill in your details:
        *   `TELEGRAM_BOT_TOKEN`: Your Telegram Bot's API token. You can get this from BotFather on Telegram.
        *   `TELEGRAM_CHAT_ID`: Your Telegram Chat ID where notifications will be sent. You can get this by sending a message to your bot and checking the updates URL (`https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`), or by messaging `@userinfobot` on Telegram.
        *   `PRODUCTS_TO_TRACK`: A list of products you want to monitor. Each product entry should include:
            *   `name`: The search query for the product (e.g., "iphone 15 pro").
            *   `platform`: Currently "olx".
            *   `target_price`: The maximum price. Notifications are sent if the price is at or below this.
            *   `min_price` (optional): The minimum price to consider, to filter out irrelevant listings.
        *   `CHECK_INTERVAL_SECONDS` (optional): How often the script checks for prices (default is 3600 seconds / 1 hour).
        *   `NOTIFIED_ITEMS_FILE` (optional): Path to store notified item URLs (default is `notified_items.json`).

2.  **Set up a Telegram Bot:**
    *   Open Telegram and search for "BotFather".
    *   Send `/newbot` command to BotFather and follow the instructions to create your bot and get the API token.

## Running the Tracker

Once configured, you can run the main script directly or use Docker.

This project includes a `Dockerfile` and `docker-compose.yml` for easy containerization.

1.  **Ensure `config.py` is present and configured** in the root of the project directory. The Docker setup mounts this file into the container.
2.  **Build and run the container (in detached mode):**
    ```bash
    docker-compose up --build -d
    ```
3.  **Check logs:**
    ```bash
    docker-compose logs -f price-tracker
    ```
4.  **Stop the container:**
    ```bash
    docker-compose down
    ```
    To stop the container and remove the `notified_data` volume (which stores `notified_items.json`):
    ```bash
    docker-compose down -v
    ```

The script will periodically check the prices of the configured products and send a Telegram notification if a product is found at or below your target price.

## How OLX Fetching Works

The `olx_fetcher.py` script uses OLX's internal GraphQL API to search for listings.
-   It sends a POST request with a GraphQL query and variables (including your product search term).
-   The query is designed to retrieve essential details like title, price, currency, and URL of the listings.
-   The response is parsed to extract these details for further processing.

**Note on OLX API:**
The OLX GraphQL endpoint and its structure might change without notice, which could break the script. The `user-agent` and `referer` headers are included to mimic a browser request, which can be important for some sites. Cookie management (`PHPSESSID`) might be necessary if OLX tightens its API access, but is currently omitted for simplicity.

## Future Enhancements

-   Support for more platforms (e.g., Allegro, Amazon).
-   More robust error handling and logging.
-   Storing historical price data.
-   Web interface or dashboard.
-   More sophisticated duplicate detection.
-   Allowing users to manage tracked products via Telegram commands.
