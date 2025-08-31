import requests
from bs4 import BeautifulSoup
import re
import json

# URL 和 cookies
url = "https://cp.coocloud.cn/user/admin.php?_menu=orderrenew&id=257730"
cookies = {
    "__cloud_user___ssid": "4303665336836626167356739333835633662636366636262673634693663353",
    "PHPSESSID": "4303665336836626167356739333835633662636366636262673634693663353"
}

# 设置请求头，模拟浏览器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}

# 企业微信群机器人 webhook URL（替换为您的实际 webhook URL）
webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e75ac7b2-f7e7-45a5-a7b8-0f92390ab020"

# 后备内容
fallback_order_id = "257730"
fallback_end_time_content = "2025-09-29 22:54:49 剩余29.41天"

# 初始化变量
order_id = None
end_time_content = None

try:
    # 发送 HTTP 请求
    response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
    
    # 检查请求状态
    if response.status_code == 200:
        # 解析 HTML 内容
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有表格行
        rows = soup.find_all('tr', class_='tbl_row')
        
        # 提取订单编号和服务到期时间
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:  # 确保至少有 2 个 <td> 元素
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if label == "订单编号":
                    order_id = value.replace('<b>', '').replace('</b>', '').strip()
                if label == "服务到期时间":
                    end_time_content = value
        
        # 检查是否成功获取信息
        if not order_id:
            order_id = fallback_order_id
            print("错误：无法从网页获取订单编号，使用后备值")
        if not end_time_content:
            end_time_content = fallback_end_time_content
            print("错误：无法从网页获取服务到期时间，使用后备值")
            
    elif response.status_code in (401, 403):
        print("错误：Cookies 失效或无权限访问（状态码: {}）".format(response.status_code))
        order_id = fallback_order_id
        end_time_content = fallback_end_time_content
    else:
        print(f"错误：无法访问 URL，状态码: {response.status_code}")
        order_id = fallback_order_id
        end_time_content = fallback_end_time_content

except requests.exceptions.Timeout:
    print("错误：请求超时")
    order_id = fallback_order_id
    end_time_content = fallback_end_time_content
except requests.exceptions.ConnectionError:
    print("错误：网络连接失败")
    order_id = fallback_order_id
    end_time_content = fallback_end_time_content
except requests.exceptions.RequestException as e:
    print(f"错误：请求失败 - {e}")
    order_id = fallback_order_id
    end_time_content = fallback_end_time_content
except Exception as e:
    print(f"错误：未知异常 - {e}")
    order_id = fallback_order_id
    end_time_content = fallback_end_time_content

# 输出获取的信息
print("挂机编号:", order_id)
print("服务到期时间:", end_time_content)

# 提取到期时间（日期部分）
date_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', end_time_content)
end_time_date = date_match.group(0) if date_match else "未知到期时间"

# 检查通知条件并合并通知逻辑
notification = None
if "小时" in end_time_content:
    notification = f"挂机通知：订单 {order_id} 的服务将于 {end_time_date} 到期，请注意！"
else:
    # 检查是否包含“剩余x天”，并提取 x
    days_match = re.search(r'剩余([\d.]+)天', end_time_content)
    if days_match:
        remaining_days = float(days_match.group(1))
        if remaining_days < 7:
            notification = f"挂机提醒：订单 {order_id} 的服务将于 {end_time_date} 到期，剩余 {remaining_days} 天，小于 7 天，请尽快处理！"

# 发送企业微信通知（如果有）
if notification:
    try:
        # 构造企业微信消息
        payload = {
            "msgtype": "text",
            "text": {
                "content": notification
            }
        }
        # 发送请求到企业微信 webhook
        response = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200 and response.json().get("errcode") == 0:
            print("企业微信通知发送成功")
        else:
            print(f"企业微信通知发送失败，状态码: {response.status_code}，错误: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"企业微信通知发送失败，错误: {e}")
