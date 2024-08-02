import requests
from bs4 import BeautifulSoup
import threading
import os

# 目标网页URL
url = 'https://vps.wikifx.com/zh-cn/jyzh'

# Telegram bot token和chat ID
bot_token = os.environ["BOT_TOKEN"]
chat_id = os.environ["CHAT_ID"]

# 多个账号的cookies字典，每个账号添加一个备注
cookies_list = [
    {
        'DJkdikKMG': '6OqTtw%252bzch7fL2BJvNgHLQ%253d%253d%257cFX3565537695%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5860011989%257c1716000c3d7ab46bf88309f2e7d77bc0',
        'remark': 'vgfvxixz@idrrate.com'
    },
    {
        'DJkdikKMG': 'codrpWmCzHjBTYo%252bG79kPQ%253d%253d%257cJim6153%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f4769447162%252f4769447162_28637.png_wiki-template-global%257c4423811951%257ca90a7db32d8c6f1833b9e43cac38c93f',
        'remark': 'duncanyu1102@gmail.com'
    },
    # 添加更多账号的cookies和备注
]

def fetch_data(cookies):
    try:
        # 发送GET请求
        response = requests.get(url, cookies=cookies)
        
        # 检查请求是否成功
        if response.status_code == 200:
            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
            
            # 定位到包含所需信息的div元素
            information_div = soup.find('div', class_='information-list')
            
            # 提取并打印信息
            if information_div:
                message = f'{cookies["remark"]}:\n'
                for item in information_div.find_all('div', class_='information-list-item'):
                    left = item.find('div', class_='information-list-item-left').text.strip()
                    right = item.find('div', class_='information-list-item-right').text.strip()
                    if left in ['VPS IP', '服务器地址', '到期日期', '近1月实盘交易数量']:
                        message += f'  {left}: {right}\n'
                # 发送消息到Telegram
                requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": message})
            else:
                message = f'{cookies["remark"]}: 没有找到包含信息的div元素。'
                requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": message})
        else:
            message = f'{cookies["remark"]}: 请求失败，状态码：{response.status_code}'
            requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": message})
    except Exception as e:
        message = f'{cookies["remark"]}: 请求发生错误：{e}'
        requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": message})

# 创建并启动线程
threads = []
for cookies in cookies_list:
    thread = threading.Thread(target=fetch_data, args=(cookies,))
    threads.append(thread)
    thread.start()

# 等待所有线程完成
for thread in threads:
    thread.join()
