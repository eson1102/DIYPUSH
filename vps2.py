import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

bot_token=os.environ["BOT_TOKEN"]
chat_id=os.environ["CHAT_ID"]

# 定义多个账号的信息
accounts = {
    'account1': {'name': 'duncanyu1102@gmail.com', 'cookie': 'codrpWmCzHjBTYo%252bG79kPQ%253d%253d%257cJim6153%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f4769447162%252f4769447162_28637.png_wiki-template-global%257c4423811951%257ca90a7db32d8c6f1833b9e43cac38c93f'},
    'account2': {'name': 'vgfvxixz@idrrate.com', 'cookie': '6OqTtw%252bzch7fL2BJvNgHLQ%253d%253d%257cFX3565537695%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5860011989%257c1716000c3d7ab46bf88309f2e7d77bc0'},
    'account3': {'name': 'magiceson@vip.qq.com', 'cookie': 'l4D9tnpeGd4CnDxzLmP8Bw%253d%253d%257c%25e9%25a1%25be%25e5%25b0%258f%25e9%2593%25ad%2B%25e8%25b4%25a4%25e5%2595%2586%25e8%258d%259f%25c2%25ae%25e4%25bc%2597%25e5%2588%259b%25e7%25a9%25ba%25e9%2597%25b4%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f3731259258%252f3731259258_24995.png_wiki-template-global%257c5564136319%257c3d9ca3c1bba06fd062851c81850d6b58'},
    'account4': {'name': '156627504@qq.com', 'cookie': '3XZ26INfMzKMKGrK8hCLVQ%253d%253d%257csolar%2540%25e5%25a5%2589%25e8%25b4%25a4%25e7%2594%259f%25e6%25b4%25bb%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f2516564746%252f2516564746_62872.png_wiki-template-global%257c0755990470%257c115781ff272d1564850a880b17a02de5'},
    'account5': {'name': 'nsjbodelxs@iubridge.com', 'cookie': 'hgD6SmDwqMWP7bAy4gmH2A%253d%253d%257ctom2220%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4437224218%257c62d8210130a7dc86ea197189b35e9ab0'},
    'account6': {'name': 'wyrgahvqzn@iubridge.com', 'cookie': 'xNvz6XMM1mseSUsercMZTg%253d%253d%257cjjj8729%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4437224251%257cb3db081376e4ec0c50b0b2dd9e028293'},
    # 添加更多账号信息
}

url = 'https://vps.wikifx.com/zh-cn/jyzh'

# 遍历多个账号
for index, (account, info) in enumerate(accounts.items(), start=1):
    cookies = {'DJkdikKMG': info['cookie']}
    message = f"\n帐号 {index}: {info['name']}\n"

    try:
        r = requests.get(url, cookies=cookies)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, 'html.parser')
        information_items = soup.find_all('div', class_='information-list-item')

        current_date = datetime.now()

        key_labels = ["VPS IP", "到期日期", "近1月实盘交易数量"]

        for item in information_items:
            label = item.find('div', class_='information-list-item-left').text.strip()
            value = item.find('div', class_='information-list-item-right').text.strip()

            if label in key_labels:
                if label == "到期日期":
                    expiry_date = datetime.strptime(value, '%Y-%m-%d')
                    days_remaining = (expiry_date - current_date).days
                    if days_remaining < 5:
                        message += f"{label}: {value} (即将到期！剩余时间小于5天，还剩 {days_remaining} 天)\n"
                        
                    else:
                        message += f"{label}: {value} (还剩 {days_remaining} 天)\n"
                       
                else:
                    message += f"{label}: {value}\n"
                    
        r = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": message})

    except requests.RequestException as e:
        print(f"Error during request for account {account}: {e}")
