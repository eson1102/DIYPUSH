import os
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# --- 配置 ---
BYBIT_URL = "https://www.bybit.com/en/earn/rwa/detail/?id=3"
WEWORK_WEBHOOK = os.environ.get("WEWORK_WEBHOOK")
DATA_FILE = "nav_data.json"

def fetch_nav_from_bybit():
    """基于确切的HTML结构提取NAV值"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        response = requests.get(BYBIT_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 方法1: 通过类名直接定位NAV值
        nav_element = soup.find('span', class_='DetailHero_navValue__FGGHP')
        if nav_element:
            raw_text = nav_element.get_text(strip=True)
            # 提取数字部分，去除 "USDC"
            nav_match = re.search(r'(\d+\.\d+)', raw_text)
            if nav_match:
                return nav_match.group(1)
        
        # 方法2: 通过包含"NAV"的标签定位（备用）
        nav_label = soup.find('span', string=lambda t: t and 'NAV' in t)
        if nav_label:
            parent_div = nav_label.find_parent('div', class_='DetailHero_dataItem__fsWIv')
            if parent_div:
                nav_value_span = parent_div.find('span', class_=lambda c: c and 'navValue' in c)
                if nav_value_span:
                    raw_text = nav_value_span.get_text(strip=True)
                    nav_match = re.search(r'(\d+\.\d+)', raw_text)
                    if nav_match:
                        return nav_match.group(1)
        
        print("未找到NAV值，页面结构可能已变化。")
        return None
        
    except Exception as e:
        print(f"获取NAV失败: {e}")
        return None

def get_nav_date_from_page():
    """从页面提取NAV的日期信息"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(BYBIT_URL, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找包含"NAV"和日期格式的文本
        nav_label = soup.find('span', string=lambda t: t and 'NAV' in t)
        if nav_label:
            text = nav_label.get_text(strip=True)
            # 提取日期，格式如 "NAV (09-01 UTC)"
            date_match = re.search(r'NAV\s*\((\d{2}-\d{2})\s*UTC\)', text)
            if date_match:
                return date_match.group(1)
        return None
    except:
        return None

def load_previous_nav():
    """从本地文件加载昨日NAV值和日期"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                return data.get('nav'), data.get('date')
        except:
            return None, None
    return None, None

def save_current_nav(nav, date):
    """保存当前NAV到本地文件"""
    with open(DATA_FILE, 'w') as f:
        json.dump({'nav': nav, 'date': date, 'updated': datetime.now().isoformat()}, f)

def send_to_wework(message):
    """发送消息到企业微信群机器人"""
    if not WEWORK_WEBHOOK:
        print("错误：未设置企业微信机器人Webhook环境变量 WEWORK_WEBHOOK")
        return
    
    headers = {"Content-Type": "application/json"}
    # 企业微信文本消息类型
    data = {
        "msgtype": "text",
        "text": {
            "content": message,
            "mentioned_list": []  # 不@任何人
        }
    }
    
    # 如果希望@所有人，可以添加 "mentioned_list": ["@all"]
    
    try:
        response = requests.post(WEWORK_WEBHOOK, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        print("消息发送成功")
    except Exception as e:
        print(f"发送消息失败: {e}")

def main():
    print(f"开始执行监控任务 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 获取当前NAV和日期
    current_nav = fetch_nav_from_bybit()
    if not current_nav:
        print("无法获取当前NAV，流程终止")
        return
    
    nav_date = get_nav_date_from_page()
    if not nav_date:
        nav_date = datetime.now().strftime("%m-%d")  # 如果获取失败，使用今天日期
    
    print(f"当前NAV: {current_nav}, 日期: {nav_date}")
    
    # 2. 获取昨日数据
    previous_nav, previous_date = load_previous_nav()
    
    # 3. 构造对比消息
    today_str = datetime.now().strftime("%Y-%m-%d")
    message = f"📊 **BlackOpal LiquidStone II NAV监控**\n"
    message += f"📅 日期: {today_str}\n"
    message += f"💰 当前NAV ({nav_date} UTC): `{current_nav} USDC`\n"
    
    if previous_nav and previous_nav != current_nav:
        # 对比并计算变化
        try:
            cur = float(current_nav)
            prev = float(previous_nav)
            change = cur - prev
            change_percent = (change / prev) * 100 if prev != 0 else 0
            
            if change > 0:
                change_symbol = "📈 ↗"
            elif change < 0:
                change_symbol = "📉 ↘"
            else:
                change_symbol = "➖"
            
            message += f"📊 昨日NAV ({previous_date or '未知'} UTC): `{previous_nav} USDC`\n"
            message += f"📈 变动: {change_symbol} `{change:+.4f}` USDC (`{change_percent:+.2f}%`)\n"
            
            # 添加趋势指示
            if abs(change_percent) > 1:
                message += f"⚠️ 注意：单日变动超过1%，请关注！\n"
                
        except ValueError:
            message += f"📊 昨日NAV: `{previous_nav} USDC` (无法计算数值变化)\n"
    elif previous_nav and previous_nav == current_nav:
        message += f"📊 昨日NAV: `{previous_nav} USDC` (与今日持平)\n"
    else:
        message += f"📊 昨日NAV: 无历史数据 (首次运行)\n"
    
    # 添加产品信息
    message += "\n---\n"
    message += f"🔗 [查看详情]({BYBIT_URL})"
    
    # 4. 发送到企业微信
    print(f"准备发送消息:\n{message}")
    send_to_wework(message)
    
    # 5. 保存当前NAV供下次使用
    save_current_nav(current_nav, nav_date)
    print("任务完成")

if __name__ == "__main__":
    main()
