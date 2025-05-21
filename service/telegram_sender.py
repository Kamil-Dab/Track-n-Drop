import requests
import urllib.parse

def send_telegram_message(bot_token, chat_id, message):
    parsed_message = urllib.parse.quote_plus(message)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={parsed_message}&parse_mode=Markdown"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(f"Telegram notification sent successfully to chat ID {chat_id}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")
        return None
