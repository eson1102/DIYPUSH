import requests
from datetime import datetime, timedelta, timezone
import pytz
from concurrent.futures import ThreadPoolExecutor
import os

# Send message to Telegram
def send_telegram_message(message, bot_token, chat_id):
    requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', data={
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    })

# Send message to WeChat Work
def send_wechat_message(message, webhook_url):
    requests.post(webhook_url, json={"msgtype": "text", "text": {"content": message}})

# Toggle for push notifications
push_notifications_enabled = True

# Configurations
telegram_bot_token = os.getenv("telegram_bot_token")
telegram_chat_id = os.getenv("telegram_chat_id")
wechat_webhook_url1 = os.getenv("wechat_webhook_url1")
wechat_webhook_url2 = os.getenv("wechat_webhook_url2")


# Get today's date in YYYY-MM-DD
today = datetime.now()
year, month, day = today.strftime('%Y'), today.strftime('%m'), today.strftime('%d')

# Fetch economic data
url = f'https://cdn-rili.jin10.com/web_data/{year}/daily/{month}/{day}/economics.json'
data = requests.get(url).json()

# Timezone
beijing_tz = pytz.timezone('Asia/Shanghai')

# Prepare a single message to merge all the information
merged_message = "5 星新闻提醒" + "\n" + "="*20 + "\n"

# Flag to check if there are any 5-star news
has_5_star_news = False

# Process data
for entry in [e for e in data if e.get('star') == 5]:
    news_name = f"{entry.get('country')} {entry.get('time_period')} {entry.get('name')}"
    consensus = f"{entry.get('consensus')} {entry.get('unit')}"
    previous = f"{entry.get('previous')} {entry.get('unit')}"
    pub_time_beijing = pytz.utc.localize(datetime.strptime(entry.get('pub_time'), '%Y-%m-%dT%H:%M:%S.%fZ')).astimezone(beijing_tz)
    current_time_beijing = datetime.now(timezone.utc).astimezone(beijing_tz)
    
    remaining_time = pub_time_beijing - current_time_beijing
    total_seconds = int(remaining_time.total_seconds())
    
    # Calculate days, hours, and minutes
    days = total_seconds // (3600 * 24)
    remaining_seconds = total_seconds % (3600 * 24)
    hours = remaining_seconds // 3600
    minutes = (remaining_seconds % 3600) // 60

    # Merge the information into one message
    merged_message += f"""
⭐⭐⭐⭐⭐\n
新闻名称: {news_name}
预 测 值: {consensus}
前      值: {previous}
新闻时间: {pub_time_beijing.strftime('%Y-%m-%d %H:%M:%S')}
当前时间: {current_time_beijing.strftime('%Y-%m-%d %H:%M:%S')}\n
🔴距离新闻: {int(days)}天 {int(hours)}小时 {int(minutes)}分钟
    """

    # Set the flag if there is any 5-star news
    has_5_star_news = True

# Check if there is any 5-star news
if has_5_star_news:
    # Ensure no notifications are sent if the time is greater than 2 hours or the news hasn't happened yet
    if any(
        (datetime.strptime(entry.get('pub_time'), '%Y-%m-%dT%H:%M:%S.%fZ').astimezone(beijing_tz) - current_time_beijing <= timedelta(hours=2) or
         datetime.strptime(entry.get('pub_time'), '%Y-%m-%dT%H:%M:%S.%fZ').astimezone(beijing_tz) <= current_time_beijing)
        for entry in [e for e in data if e.get('star') == 5]
    ):
        # Send the notifications if there are relevant 5-star news
        def send_notifications(message):
            if push_notifications_enabled:
                with ThreadPoolExecutor() as executor:
                    # Send messages concurrently to Telegram and WeChat
                    executor.submit(send_telegram_message, message, telegram_bot_token, telegram_chat_id)
                    executor.submit(send_wechat_message, message, wechat_webhook_url1)
                    executor.submit(send_wechat_message, message, wechat_webhook_url2)

        send_notifications(merged_message)
else:
    print("No 5-star news found today. No notifications will be sent.")

# Print the merged message to the console
print(merged_message)
