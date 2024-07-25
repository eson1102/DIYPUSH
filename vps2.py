import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define multiple account information
accounts = {
    'account1': {'name': 'duncanyu1102@gmail.com', 'cookie': 'codrpWmCzHjBTYo%252bG79kPQ%253d%253d%257cJim6153%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f4769447162%252f4769447162_28637.png_wiki-template-global%257c4423811951%257ca90a7db32d8c6f1833b9e43cac38c93f'},
    'account2': {'name': 'vgfvxixz@idrrate.com', 'cookie': '6OqTtw%252bzch7fL2BJvNgHLQ%253d%253d%257cFX3565537695%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5860011989%257c1716000c3d7ab46bf88309f2e7d77bc0'},
    'account3': {'name': 'magiceson@vip.qq.com', 'cookie': 'l4D9tnpeGd4CnDxzLmP8Bw%253d%253d%257c%25e9%25a1%25be%25e5%25b0%258f%25e9%2593%25ad%2B%25e8%25b4%25a4%25e5%2595%2586%25e8%258d%259f%25c2%25ae%25e4%25bc%2597%25e5%2588%259b%25e7%25a9%25ba%25e9%2597%25b4%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f3731259258%252f3731259258_24995.png_wiki-template-global%257c5564136319%257c3d9ca3c1bba06fd062851c81850d6b58'},
    'account4': {'name': '156627504@qq.com', 'cookie': '3XZ26INfMzKMKGrK8hCLVQ%253d%253d%257csolar%2540%25e5%25a5%2589%25e8%25b4%25a4%25e7%2594%259f%25e6%25b4%25bb%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f2516564746%252f2516564746_62872.png_wiki-template-global%257c0755990470%257c115781ff272d1564850a880b17a02de5'},
    'account5': {'name': 'tmifmahoge@iubridge.com', 'cookie': 'TPrf8cfx2MgVm3OJR9nQ0A%253d%253d%257chhhh723%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c3213176112%257c538a37f6a60199da2c299ee8c8cff6a5'},
    'account6': {'name': 'gkvcciymld@iubridge.com', 'cookie': 'dIaXUzSBBYnFfAfiS3kNsA%253d%253d%257cggg5352%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4433028554%257c845f9e87bd9fc26ca63e0e960b2f0c7a'},
    'account7': {'name': 'hudoaanjnd@iubridge.com', 'cookie': 'UK4QLy%252biJ7fUKEx4c2c5yA%253d%253d%257chh2440%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c9687315565%257c7af7b43640e6db1a2ee8ad4e650c0cd9'},
    'account8': {'name': 'hwqeecfkzd@iubridge.com', 'cookie': 'fj96MZf3%252bStvSnUf%252bUVSyQ%253d%253d%257chh5848%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5561623261%257c9e12b8331368e6de79a4436f0b6e3c8e'},
}

url = 'https://vps.wikifx.com/zh-cn/jyzh'
bot_token = os.environ["BOT_TOKEN"]
chat_id = os.environ["CHAT_ID"]

def fetch_account_data(account, info):
    cookies = {'DJkdikKMG': info['cookie']}
    try:
        with requests.Session() as session:
            response = session.get(url, cookies=cookies)
            response.raise_for_status()
            return response.text
    except requests.RequestException as e:
        logging.error(f"Error during request for account {account}: {e}")
        return None

def parse_account_data(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    information_items = soup.find_all('div', class_='information-list-item')
    
    current_date = datetime.now()
    account_info = []

    key_labels = ["VPS IP", "到期日期", "近1月实盘交易数量", "服务器地址"]

    for item in information_items:
        label = item.find('div', class_='information-list-item-left').text.strip()
        value = item.find('div', class_='information-list-item-right').text.strip()

        if label in key_labels:
            if label == "到期日期":
                expiry_date = datetime.strptime(value, '%Y-%m-%d')
                days_remaining = (expiry_date - current_date).days
                if days_remaining < 5:
                    account_info.append(f"{label}: {value} (即将到期！剩余时间小于5天，还剩 {days_remaining} 天)")
                else:
                    account_info.append(f"{label}: {value} (还剩 {days_remaining} 天)")
            else:
                account_info.append(f"{label}: {value}")

    return "\n".join(account_info)

def send_telegram_message(message):
    try:
        requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": message})
    except requests.RequestException as e:
        logging.error(f"Error sending message: {e}")

def main():
    combined_message = ""
    for index, (account, info) in enumerate(accounts.items(), start=1):
        html_text = fetch_account_data(account, info)
        if html_text:
            account_info = parse_account_data(html_text)
            combined_message += f"\n帐号 {index}: {info['name']}\n{account_info}\n"
    
    if combined_message:
        send_telegram_message(combined_message)

if __name__ == "__main__":
    main()
