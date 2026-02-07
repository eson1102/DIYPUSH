import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

# --- 配置区 ---
# 从环境变量获取Webhook URL
WEBHOOK_URL = os.getenv('WECHAT_WEBHOOK_URL111', '')
TARGET_URL = "https://www.jwvps.cn/service?groupid=305"

COOKIES = {
    'ZJMF_E111752CA3D1B055': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyaW5mbyI6eyJpZCI6MjI4NCwidXNlcm5hbWUiOiJkdW5jYW55dTExMDIifSwiaXNzIjoid3d3LmlkY1NtYXJ0LmNvbSIsImF1ZCI6Ind3dy5pZGNTbWFydC5jb20iLCJpcCI6IjIyMy4xNjcuMzMuMjYiLCJpYXQiOjE3NzA0MzQ2NTEsIm5iZiI6MTc3MDQzNDY1MSwiZXhwIjoxNzcwNDQxODUxfQ.iXd5pA0DFP89xXb2dG41Z4pPJzIyvzgBBYCczcbJSGc',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def send_wechat_text(content):
    """
    发送 text 类型消息，并打印企业微信端的实时反馈
    """
    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    print(f"\n[调试] 准备推送到企业微信...")
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        resp_json = res.json()
        if resp_json.get("errcode") == 0:
            print(">>> ✅ 企业微信服务器已成功接收消息！")
        else:
            print(f">>> ❌ 推送被拦截！错误码: {resp_json.get('errcode')}, 原因: {resp_json.get('errmsg')}")
            print("提示：请检查 Webhook 地址是否被删除，或消息内容是否包含违规字符。")
    except Exception as e:
        print(f">>> ❌ 网络通信失败: {e}")

def fetch_and_notify():
    print(f"==========================================")
    print(f"🔍 监控任务启动 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"==========================================")
    
    try:
        # 1. 抓取网页
        print(f"[1/3] 正在请求聚稳云页面...")
        response = requests.get(TARGET_URL, cookies=COOKIES, headers=HEADERS, timeout=15)
        print(f"      - HTTP状态码: {response.status_code}")
        
        if response.status_code != 200:
            send_wechat_text(f"🛑 [告警] 聚稳云访问异常\n状态码: {response.status_code}\n请检查网络或Cookie状态。")
            return

        # 2. 解析数据
        print(f"[2/3] 正在解析 HTML 数据...")
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select("#serviceTbody tr")
        print(f"      - 发现服务行数: {len(rows)}")

        if not rows:
            print(f"      - [警告] 未解析到数据行，可能是登录过期。页面前50字符: {response.text[:50]}")
            send_wechat_text("🛑 [告警] 聚稳云解析失败\n未找到任何服务列表，请手动检查 Cookie。")
            return
        
        today = datetime.now()
        warning_items = []

        print(f"      - 开始遍历机器并筛选 (条件: 距离到期 <= 7天):")
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 8: continue
            
            # 名称处理
            raw_remarks = cols[7].get_text(strip=True).split(' ')[0]
            product_name = cols[1].find('strong').get_text(strip=True)
            display_name = raw_remarks if raw_remarks and raw_remarks != '-' else product_name
            
            # 时间计算
            expiry_str = cols[4].find('p').get_text(strip=True)
            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d')
            days_left = (expiry_date - today).days
            
            # 调试日志：打印每一台机器的现状
            print(f"        > 发现机器: {display_name:<10} | 到期: {expiry_str} | 剩余: {days_left}天")
            
            # 核心判断
            if days_left <= 27:
                icon = "🚫" if days_left < 0 else "⚠️"
                status_text = f"已过期 {abs(days_left)} 天" if days_left < 0 else f"仅剩 {days_left} 天"
                item_info = f"{icon} 机器: {display_name}\n📅 到期: {expiry_str}\n🔔 状态: {status_text}"
                warning_items.append(item_info)
        
        # 3. 推送结果
        print(f"[3/3] 检查推送触发条件...")
        if warning_items:
            print(f"      - 发现 {len(warning_items)} 个到期目标，准备发送通知。")
            header = "🔔 【到期预警】 聚稳云服务监控\n" + "—" * 15 + "\n"
            footer = "\n" + "—" * 15 + f"\n检测时间: {datetime.now().strftime('%m-%d %H:%M')}"
            full_msg = header + "\n\n".join(warning_items) + footer
            send_wechat_text(full_msg)
        else:
            print(f"      - 结果: 所有服务正常 (均大于 7 天)，无需发送通知。")

    except Exception as e:
        err_msg = f"💥 [脚本崩溃] 运行出错\n详细信息: {str(e)}"
        print(f"\n[错误调试] {err_msg}")
        send_wechat_text(err_msg)

if __name__ == "__main__":
    fetch_and_notify()
    print(f"\n监控任务结束。\n==========================================")
