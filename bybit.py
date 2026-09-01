import os
import json
import requests
from datetime import datetime, timedelta
import time

# --- 配置 ---
PRODUCT_ID = 3  # Bybit RWA产品ID
BYBIT_PAGE_URL = "https://www.bybit.com/en/earn/rwa/detail/?id=3"
WEWORK_WEBHOOK = os.environ.get("WEWORK_WEBHOOK")
DATA_FILE = "nav_data.json"

def get_nav_data(product_id, end_time=None):
    """
    通过Bybit官方API获取NAV数据
    :param product_id: 产品ID
    :param end_time: 结束时间（Unix时间戳，秒），不传则默认为当前时间
    :return: NAV数据列表
    """
    url = "https://api.bybit.com/v5/earn/rwa/nav-chart"
    
    # 完整的请求头，模拟真实浏览器访问
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.bybit.com",
        "Referer": "https://www.bybit.com/en/earn/rwa/detail/?id=3",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    params = {
        "productId": product_id
    }
    if end_time:
        params["endTime"] = int(end_time)
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('retCode') == 0:
            nav_list = data.get('result', {}).get('list', [])
            if nav_list:
                return nav_list
            else:
                print("API返回空数据")
                return None
        else:
            print(f"API业务错误: {data.get('retMsg')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

def get_current_and_yesterday_nav():
    """
    获取今日和昨日的NAV值
    :return: (今日NAV, 今日日期, 昨日NAV, 昨日日期)
    """
    # 1. 获取今日NAV（默认返回最近7天数据）
    current_list = get_nav_data(PRODUCT_ID)
    if not current_list:
        print("无法获取当前NAV数据")
        return None, None, None, None
    
    # 最新的一条数据就是今日NAV
    today_data = current_list[-1]
    current_nav = today_data.get('nav')
    current_date = today_data.get('date')
    
    if not current_nav:
        print("NAV数据格式异常")
        return None, None, None, None
    
    print(f"今日 ({current_date}) NAV: {current_nav}")
    
    # 2. 获取昨日NAV（将结束时间设为今天0点）
    today_zero = int(time.mktime(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timetuple()))
    yesterday_list = get_nav_data(PRODUCT_ID, end_time=today_zero)
    
    previous_nav = None
    previous_date = None
    
    if yesterday_list and len(yesterday_list) > 0:
        yesterday_data = yesterday_list[-1]
        previous_nav = yesterday_data.get('nav')
        previous_date = yesterday_data.get('date')
        print(f"昨日 ({previous_date}) NAV: {previous_nav}")
    else:
        print("无法获取昨日NAV数据（可能是首次运行）")
    
    return current_nav, current_date, previous_nav, previous_date

def load_previous_nav():
    """从本地文件加载存储的NAV值和日期（作为备用）"""
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
        return False
    
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "text",
        "text": {
            "content": message,
            "mentioned_list": []  # 不@任何人
        }
    }
    
    try:
        response = requests.post(WEWORK_WEBHOOK, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        print("消息发送成功")
        return True
    except Exception as e:
        print(f"发送消息失败: {e}")
        return False

def get_beijing_time():
    """获取当前北京时间"""
    beijing_time = datetime.utcnow() + timedelta(hours=8)
    return beijing_time.strftime("%Y-%m-%d %H:%M")

def main():
    beijing_time = get_beijing_time()
    print(f"开始执行监控任务 - 北京时间 {beijing_time}")
    print("=" * 50)
    
    # 1. 通过API获取今日和昨日NAV
    current_nav, current_date, previous_nav, previous_date = get_current_and_yesterday_nav()
    
    if not current_nav:
        print("无法获取当前NAV，流程终止")
        return
    
    # 如果API没有返回昨日数据，尝试从本地文件读取
    if not previous_nav:
        previous_nav, previous_date = load_previous_nav()
        if previous_nav:
            print(f"从本地缓存读取昨日数据: {previous_nav} ({previous_date})")
    
    # 2. 构造对比消息
    message = f"📊 Bybit RWA NAV 监控\n"
    message += f"⏰ {beijing_time}\n"
    message += f"━━━━━━━━━━━━━━━━\n"
    message += f"💰 当前 NAV ({current_date} UTC)\n"
    message += f"   `{current_nav} USDC`\n\n"
    
    if previous_nav and previous_nav != current_nav:
        try:
            cur = float(current_nav)
            prev = float(previous_nav)
            change = cur - prev
            change_percent = (change / prev) * 100 if prev != 0 else 0
            
            if change > 0:
                change_symbol = "📈 上涨"
            elif change < 0:
                change_symbol = "📉 下跌"
            else:
                change_symbol = "➖ 持平"
            
            message += f"📊 对比昨日 ({previous_date or '历史'} UTC)\n"
            message += f"   `{previous_nav} USDC`\n\n"
            message += f"📈 变动: {change_symbol}\n"
            message += f"   `{change:+.4f}` USDC  (`{change_percent:+.2f}%`)\n"
            
            if abs(change_percent) > 0.5:
                message += f"\n⚠️ 单日变动超过 0.5%，请关注！\n"
                
        except ValueError:
            message += f"📊 昨日 NAV: `{previous_nav} USDC`\n"
            message += f"   (无法计算数值变化)\n"
    elif previous_nav and previous_nav == current_nav:
        message += f"📊 对比昨日: 持平\n"
        message += f"   `{previous_nav} USDC`\n"
    else:
        message += f"📊 历史数据: 无\n"
        message += f"   (首次运行，已记录当前值)\n"
    
    message += f"\n━━━━━━━━━━━━━━━━\n"
    message += f"🔗 [查看完整详情]({BYBIT_PAGE_URL})"
    
    # 3. 发送到企业微信
    print("\n准备发送消息:")
    print("-" * 30)
    print(message)
    print("-" * 30)
    
    send_to_wework(message)
    
    # 4. 保存当前NAV供下次使用（作为备用）
    if current_nav:
        save_current_nav(current_nav, current_date)
    
    print("\n任务完成")

if __name__ == "__main__":
    main()
