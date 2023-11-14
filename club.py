import requests
from bs4 import BeautifulSoup
import time


bot_token='6676903379:AAGjF8oK3uUd03rqhwQM1xwO151Emv74zuM'
chat_id='507265893'
qywechat='fc52ec93-b058-4e96-9991-598f6cdf803b'

url = 'https://clubbingbuy.net/threads/nesco-mt5.11471/'

r = requests.get(url, timeout=10)

soup = BeautifulSoup(r.text, 'html.parser')

h1 = soup.find('h1')
span = h1.find('span')
value = span.text

# 设置定时任务，这里以3秒为例
time.sleep(3)

# 通过Telegram bot发送通知消息
message = "帖子状态为:" + value  # 通知消息的内容
r = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": message})
print('Telegram通知消息已发送')

# 通过WeChat bot发送通知消息
wechat_response = requests.post(
    "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key="+qywechat,
    json={
        "msgtype": "text",
        "text": {
            "content": message
        }
    }
)
print('WeChat通知消息已发送')
