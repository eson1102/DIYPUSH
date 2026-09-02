import os
import json
import requests
from datetime import datetime, timedelta
import time

# --- 配置 ---
TARGET_PRODUCT_NAME = "BlackOpal LiquidStone II"  # 要监控的产品名称
WEWORK_WEBHOOK = os.environ.get("WEWORK_WEBHOOK")
DATA_FILE = "nav_data.json"
BASE_URL = "https://api.bybit.com"

def _get_headers(referer=None):
    """获取通用请求头，模拟真实浏览器"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.bybit.com",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }
    if referer:
        headers["Referer"] = referer
    return headers

def get_product_list(coin='USDC'):
    """获取RWA产品列表"""
    url = f"{BASE_URL}/v5/earn/rwa/product"
    headers = _get_headers("https://www.bybit.com/en/earn/rwa")
    params = {"coin": coin} if coin else {}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('retCode') == 0:
            return data.get('result', {}).get('list', [])
        else:
            print(f"获取产品列表失败: {data.get('retMsg')}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def find_product_by_name(product_name, coin='USDC'):
    """根据产品名称查找产品"""
    products = get_product_list(coin)
    if not products:
        return None
    
    # 精确匹配
    for p in products:
        if p.get('assetSymbol', '') == product_name:
            return p
    
    # 模糊匹配
    for p in products:
        if product_name.lower() in p.get('assetSymbol', '').lower():
            return p
    
    print(f"未找到产品: {product_name}")
    return None

def get_nav_data(product_id, start_time=None, end_time=None):
    """获取NAV历史数据"""
    url = f"{BASE_URL}/v5/earn/rwa/nav-chart"
    headers = _get_headers(f"https://www.bybit.com/en/earn/rwa/detail/?id={product_id}")
    
    params = {"productId": product_id}
    if start_time:
        params["startTime"] = int(start_time)
    if end_time:
        params["endTime"] = int(end_time)
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('retCode') == 0:
            return data.get('result', {}).get('list', [])
        else:
            print(f"获取NAV数据失败: {data.get('retMsg')}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def get_current_and_yesterday_nav(product_id):
    """获取今日和昨日的NAV值"""
    # 获取今日NAV
    current_list = get_nav_data(product_id)
    if not current_list:
        print("无法获取当前NAV数据")
        return None, None, None, None
    
    today_data = current_list[-1]
    current_nav = today_data.get('nav')
    current_date = today_data.get('date')
    
    if not current_nav:
        print("NAV数据格式异常")
        return None, None, None, None
    
    print(f"今日 ({current_date}) NAV: {current_nav}")
    
    # 获取昨日NAV
    today_zero = int(time.mktime(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timetuple()))
    yesterday_list = get_nav_data(product_id, end_time=today_zero)
    
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

def list_all_products(coin='USDC'):
    """列出所有产品"""
    products = get_product_list(coin)
    if not products:
        return None
    
    print(f"\n{'='*100}")
    print(f"{'ID':<6} {'产品名称':<35} {'管理者':<20} {'币种':<8} {'NAV':<12} {'年化利率':<10}")
    print(f"{'='*100}")
    
    for p in products:
        product_id = p.get('productId')
        asset = p.get('assetSymbol', '')[:33]
        manager = p.get('manager', '')[:18]
        coin = p.get('coin', '')
        nav = p.get('nav', '')
        base_apr = float(p.get('baseApr', '0')) * 100
        bonus_apr = float(p.get('bonusApr', '0')) * 100 if p.get('bonusApr') else 0
        total_apr = base_apr + bonus_apr
        
        marker = " ← 目标" if TARGET_PRODUCT_NAME.lower() in p.get('assetSymbol', '').lower() else ""
        print(f"{product_id:<6} {asset:<35} {manager:<20} {coin:<8} {nav:<12} {total_apr:.2f}%{marker}")
    
    print(f"{'='*100}")
    print(f"总计: {len(products)} 个产品\n")
    return products

def load_previous_nav():
    """从本地文件加载存储的NAV值"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                return data.get('nav'), data.get('date'), data.get('product_id')
        except:
            return None, None, None
    return None, None, None

def save_current_nav(nav, date, product_id):
    """保存当前NAV到本地文件"""
    with open(DATA_FILE, 'w') as f:
        json.dump({
            'product_id': product_id,
            'nav': nav,
            'date': date,
            'updated': datetime.now().isoformat()
        }, f)

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
            "mentioned_list": []
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
    
    # 1. 获取产品列表，找到目标产品的ID
    print(f"\n正在查找目标产品: {TARGET_PRODUCT_NAME}")
    
    products = list_all_products('USDC')
    if not products:
        print("无法获取产品列表，流程终止")
        return
    
    target_product = find_product_by_name(TARGET_PRODUCT_NAME, 'USDC')
    if not target_product:
        print(f"\n未找到产品: {TARGET_PRODUCT_NAME}")
        print("请检查产品名称是否正确，或修改 TARGET_PRODUCT_NAME 变量")
        return
    
    product_id = target_product.get('productId')
    product_name = target_product.get('assetSymbol')
    manager = target_product.get('manager')
    
    print(f"\n✅ 找到目标产品:")
    print(f"   ID: {product_id}")
    print(f"   名称: {product_name}")
    print(f"   管理者: {manager}")
    print(f"   当前NAV: {target_product.get('nav')}")
    
    # 2. 获取今日和昨日NAV
    print(f"\n正在获取产品 {product_id} 的NAV历史数据...")
    current_nav, current_date, previous_nav, previous_date = get_current_and_yesterday_nav(product_id)
    
    if not current_nav:
        print("无法获取当前NAV，流程终止")
        return
    
    # 如果API没有返回昨日数据，尝试从本地文件读取
    if not previous_nav:
        cached_nav, cached_date, cached_product_id = load_previous_nav()
        if cached_nav and cached_product_id == product_id:
            previous_nav = cached_nav
            previous_date = cached_date
            print(f"从本地缓存读取昨日数据: {previous_nav} ({previous_date})")
    
    # 3. 构造对比消息
    message = f"📊 Bybit RWA NAV 监控\n"
    message += f"⏰ {beijing_time}\n"
    message += f"━━━━━━━━━━━━━━━━\n"
    message += f"🏷️ {product_name}\n"
    message += f"👤 {manager}\n"
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
    message += f"🔗 [查看完整详情](https://www.bybit.com/en/earn/rwa/detail/?id={product_id})"
    
    # 4. 发送到企业微信
    print("\n准备发送消息:")
    print("-" * 30)
    print(message)
    print("-" * 30)
    
    send_to_wework(message)
    
    # 5. 保存当前NAV供下次使用
    if current_nav:
        save_current_nav(current_nav, current_date, product_id)
    
    print("\n任务完成")

if __name__ == "__main__":
    main()
