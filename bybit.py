import requests
from datetime import datetime, timedelta
import time

def get_nav_data(product_id, end_time=None):
    """
    获取指定产品的NAV数据
    :param product_id: 产品ID，例如 3
    :param end_time: 结束时间（Unix时间戳，秒），不传则默认为当前时间
    """
    url = "https://api.bybit.com/v5/earn/rwa/nav-chart"
    params = {
        "productId": product_id,
    }
    if end_time:
        params["endTime"] = int(end_time)
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if data['retCode'] == 0:
            return data['result']['list']  # 返回NAV数据列表
        else:
            print(f"API错误: {data['retMsg']}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

# --- 使用示例 ---
PRODUCT_ID = 3  # 假设ID为3

# 1. 获取最新NAV（默认返回最近7天数据）
nav_list = get_nav_data(PRODUCT_ID)
if nav_list:
    today = nav_list[-1]  # 最后一个是最新数据
    print(f"今日 ({today['date']}) NAV: {today['nav']}")

# 2. 获取昨日NAV（将结束时间设为今天0点）
today_zero = int(time.mktime(datetime.now().replace(hour=0, minute=0, second=0).timetuple()))
yesterday_list = get_nav_data(PRODUCT_ID, end_time=today_zero)
if yesterday_list:
    yesterday = yesterday_list[-1]
    print(f"昨日 ({yesterday['date']}) NAV: {yesterday['nav']}")
