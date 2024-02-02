import requests
from datetime import datetime, timedelta
import os

bot_token=os.environ["BOT_TOKEN"]
chat_id=os.environ["CHAT_ID"]

# 获取当前日期的日部分
current_day = datetime.now().day

# 你的字典
expiration_dates = {
    "vgfvxixz@idrrate.com": 28,
    "magiceson@vip.qq.com": 7,
    "duncanyu1102@gmail.com": 10,
    "156627504@qq.com": 27,
    "nsjbodelxs@iubridge.com": 1,
    "wyrgahvqzn@iubridge.com": 1
    }

# 检查到期日期并进行提醒
for key, expiration_day in expiration_dates.items():
    days_until_expiration = expiration_day - current_day

    if days_until_expiration > 0 and days_until_expiration <= 7:
        message=f"{key}将在{days_until_expiration}天后到期，请注意处理！"
        print(message)

        # 通过Telegram bot发送通知消息
        message = message  # 通知消息的内容
        r = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": message})
        print('Telegram通知消息已发送')
