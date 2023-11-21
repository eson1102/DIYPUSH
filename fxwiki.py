import pandas as pd
from datetime import datetime
import requests
import os

bot_token=os.environ["BOT_TOKEN"]
chat_id=os.environ["CHAT_ID"]

# 读取Excel表格
file_path = '2.xlsx'  # 将路径替换为你的Excel文件路径
df = pd.read_excel(file_path)

# 获取当前日期
current_date = datetime.now()

# 遍历表格的每一行
for index, row in df.iterrows():
    # 获取“日”列的值
    day_value = row['日']

    # 计算剩余天数
    remaining_days = (current_date.day - day_value)

    # 如果剩余天数在1到5之间，进行提醒
    if -1 < remaining_days > -5:
        # 输出其他列的内容，并用换行分隔
        output_str = (
            f"剩余天数: {remaining_days}\n"
            f"到期日: {day_value}\n"
            f"===================\n"
            f"序号: {row['序号']}\n"
            f"ip: {row['ip尾号']}\n"
            f"邮箱: {row['邮箱']}\n"
            f"地区: {row['地区']}\n"
            # 添加其他列信息...
        )
                # 通过Telegram bot发送通知消息
        message = output_str  # 通知消息的内容
        r = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": message})
        print('Telegram通知消息已发送')
        print("-" * 30)  # 添加分隔线

    # 如果不需要提醒，可以省略这一部分
    # else:
    #     print(f"剩余天数: {remaining_days}，日期日: {day_value}")
