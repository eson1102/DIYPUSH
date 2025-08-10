import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

LOCATION_EMOJIS = {
    "香港": "🇭🇰", "新加坡": "🇸🇬", "美国": "🇺🇸", "日本": "🇯🇵",
    "英国": "🇬🇧", "德国": "🇩🇪", "澳大利亚": "🇦🇺", "加拿大": "🇨🇦",
    "韩国": "🇰🇷", "台湾": "🇹🇼", "澳门": "🇲🇴", "马来西亚": "🇲🇾",
    "俄罗斯": "🇷🇺", "巴西": "🇧🇷", "印度": "🇮🇳"
}

# 企业微信机器人Webhook地址（群机器人）
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e75ac7b2-f7e7-45a5-a7b8-0f92390ab020"
# VPS检查页面
url = "https://vps.wikifx.com/zh-cn/jyzh"

# 配置参数
MAX_THREADS = 3
TIMEOUT = 15
RETRY_COUNT = 2
# 消息类型: "text" 或 "markdown"
MESSAGE_TYPE = "text"  # 可切换为"markdown"使用富文本格式

cookies_list = [
    {
        'DJkdikKMG': '6OqTtw%252bzch7fL2BJvNgHLQ%253d%253d%257cFX3565537695%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5860011989%257c1716000c3d7ab46bf88309f2e7d77bc0',
        'remark': 'vgfvxixz@idrrate.com'
    },
    {
        'DJkdikKMG': 'codrpWmCzHjBTYo%252bG79kPQ%253d%253d%257cJim6153%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f4769447162%252f4769447162_28637.png_wiki-template-global%257c4423811951%257ca90a7db32d8c6f1833b9e43cac38c93f',
        'remark': 'duncanyu1102@gmail.com'
    },
    {
        'DJkdikKMG': '3XZ26INfMzKMKGrK8hCLVQ%253d%253d%257csolar%2540%25e5%25a5%2589%25e8%25b4%25a4%25e7%2594%259f%25e6%25b4%25bb%257chttps%253a%252f%252fimg.fx696.com%252f%252fthirdparty%252f2516564746%252f2516564746_62872.png_wiki200%257c0875342355%257c4a3e2e1c2959ea12792eb2497a3641ab',
        'remark': '156627504@qq.com'
    },
    {
        'DJkdikKMG': 'ncK4Do%2fFX08LfUpcy2Vuog%3d%3d%7cbh91%7chttps%3a%2f%2fimg.fx696.com%2fWikiEnterprise%2fsign%2fpersonph.png_wiki-template-global%7c9575322624%7cddb7515da1b345f9e4c3f14192cbb265',
        'remark': 'iijoidpfdc@iubridge.com'
    }
    # 添加更多账号的cookies和备注
]


def send_wechat_text_message(webhook_url, content):
    """发送文本消息到企业微信群机器人"""
    if not webhook_url or "key=" not in webhook_url:
        print("无效的Webhook地址，必须包含key参数")
        return False
        
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    try:
        response = requests.post(webhook_url, json=data, headers=headers, timeout=10)
        result = response.json()
        
        if result.get("errcode") == 0:
            print("文本消息发送成功")
            return True
        else:
            print(f"文本消息发送失败: {result.get('errmsg')}")
            return False
            
    except Exception as e:
        print(f"发送文本消息时发生错误: {str(e)}")
        return False


def send_wechat_markdown_message(webhook_url, content):
    """发送Markdown消息到企业微信群机器人"""
    if not webhook_url or "key=" not in webhook_url:
        print("企业微信群机器人Webhook地址配置不正确")
        return False
        
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": content
        }
    }
    
    try:
        response = requests.post(webhook_url, json=data, headers=headers, timeout=10)
        result = response.json()
        if result.get("errcode") == 0:
            print("Markdown消息发送成功")
            return True
        else:
            print(f"Markdown消息发送失败: {result.get('errmsg')}")
            return False
    except Exception as e:
        print(f"发送Markdown消息时发生错误: {str(e)}")
        return False


def format_vps_info_text(vps_list):
    """格式化VPS信息为文本格式"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"VPS状态检查报告 ({current_time})\n\n"
    
    # 分类统计
    total = len(vps_list)
    normal = sum(1 for vps in vps_list if 'status' not in vps)
    error = total - normal
    
    content += f"统计: 共 {total} 个账号 | 正常: {normal} 个 | 异常: {error} 个\n\n"
    
    # 处理异常状态的VPS
    if error > 0:
        content += "异常账号:\n"
        for vps in vps_list:
            if 'status' in vps:
                content += f"- {vps['account']}: {vps['status']}\n"
        content += "\n"
    
    # 处理正常状态的VPS
    normal_vps = [vps for vps in vps_list if 'status' not in vps]
    normal_vps.sort(key=lambda x: x['days_left'] if x['days_left'] is not None else float('inf'))
    
    if normal_vps:
        content += "正常账号:\n"
        for vps in normal_vps:
            expire_tag = ""
            if vps['days_left'] is not None:
                if vps['days_left'] <= 3:
                    expire_tag = " ⚠️ 即将到期"
                elif vps['days_left'] <= 7:
                    expire_tag = " ⚠️ 7天内到期"
            
            content += f"- {vps['account']}\n"
            content += f"  IP: {vps['ip']}\n"
            content += f"  地区: {vps['location']}\n"
            content += f"  近1月交易: {vps['transactions']} 笔\n"
            content += f"  到期日: {vps['expire_date']} ({vps['days_left']}天){expire_tag}\n\n"
    
    return content


def format_vps_info_markdown(vps_list):
    """格式化VPS信息为Markdown格式"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = f"### VPS状态检查报告 ({current_time})\n\n"
    
    # 分类统计
    total = len(vps_list)
    normal = sum(1 for vps in vps_list if 'status' not in vps)
    error = total - normal
    
    content += f"📊 统计: 共 {total} 个账号 | 正常: {normal} 个 | 异常: {error} 个\n\n"
    
    # 处理异常状态的VPS
    if error > 0:
        content += "❌ **异常账号**\n"
        for vps in vps_list:
            if 'status' in vps:
                content += f"- {vps['account']}: {vps['status']}\n"
        content += "\n"
    
    # 处理正常状态的VPS
    normal_vps = [vps for vps in vps_list if 'status' not in vps]
    normal_vps.sort(key=lambda x: x['days_left'] if x['days_left'] is not None else float('inf'))
    
    if normal_vps:
        content += "✅ **正常账号**\n"
        for vps in normal_vps:
            expire_tag = ""
            if vps['days_left'] is not None:
                if vps['days_left'] <= 3:
                    expire_tag = " ⚠️ 即将到期"
                elif vps['days_left'] <= 7:
                    expire_tag = " ⚠️ 7天内到期"
            
            content += f"- {vps['account']}\n"
            content += f"  - IP: {vps['ip']}\n"
            content += f"  - 地区: {vps['location']}\n"
            content += f"  - 近1月交易: {vps['transactions']} 笔\n"
            content += f"  - 到期日: {vps['expire_date']} ({vps['days_left']}天){expire_tag}\n\n"
    
    return content


def check_single_vps_with_retry(account_data, today):
    """带重试机制的单个VPS检查"""
    for attempt in range(RETRY_COUNT + 1):
        try:
            return check_single_vps(account_data, today, attempt)
        except Exception as e:
            if attempt < RETRY_COUNT:
                print(f"检查 {account_data['remark']} 失败，正在重试 ({attempt + 1}/{RETRY_COUNT})...")
                time.sleep(2** attempt)  # 指数退避
            else:
                return {
                    'account': account_data['remark'],
                    'status': f"多次尝试后失败: {str(e)}"
                }


def check_single_vps(account_data, today, attempt=0):
    """检查单个VPS账号的状态"""
    account_email = account_data['remark']
    cookies = {'DJkdikKMG': account_data['DJkdikKMG']}

    try:
        # 随机延迟
        delay = 1 + random.uniform(0, 2)
        time.sleep(delay)
        
        # 模拟浏览器请求头
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2'
        }
        
        response = requests.get(
            url, 
            cookies=cookies, 
            headers=headers,
            allow_redirects=False, 
            timeout=TIMEOUT
        )

        if response.status_code in (302, 403):
            return {
                'account': account_email,
                'status': f"访问失败({response.status_code})，可能是Cookie失效"
            }

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            info_div = soup.find('div', class_='information-right')
            if not info_div:
                return {
                    'account': account_email,
                    'status': "未找到 VPS 信息"
                }

            info_items = {}
            for item in info_div.find_all('div', class_='information-list-item'):
                left = item.find('div', class_='information-list-item-left')
                right = item.find('div', class_='information-list-item-right')
                if left and right:
                    key = left.get_text(strip=True)
                    value = right.get_text(strip=True)
                    info_items[key] = value

            transactions = int(info_items.get('近1月实盘交易数量', '0'))
            location = info_items.get('服务器地址', 'N/A')
            expire_date_str = info_items.get('到期日期', 'N/A')
            vps_ip = info_items.get('VPS IP', 'N/A')

            emoji = LOCATION_EMOJIS.get(location, "")
            if emoji:
                location = f"{emoji} {location}"

            days_left = None
            if expire_date_str != 'N/A':
                try:
                    expire_date = datetime.strptime(expire_date_str, "%Y-%m-%d").date()
                    days_left = (expire_date - today).days
                except ValueError:
                    pass

            return {
                'account': account_email,
                'ip': vps_ip,
                'location': location,
                'transactions': transactions,
                'expire_date': expire_date_str,
                'days_left': days_left
            }
        else:
            return {
                'account': account_email,
                'status': f"HTTP错误({response.status_code})"
            }

    except Exception as e:
        raise Exception(f"HTTPS连接错误: {str(e)}")


def check_vps_status():
    """多线程检查所有VPS状态"""
    today = datetime.now().date()
    all_vps_details = []
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {
            executor.submit(check_single_vps_with_retry, account_data, today): 
            account_data for account_data in cookies_list
        }
        
        for future in as_completed(futures):
            account_data = futures[future]
            try:
                result = future.result()
                all_vps_details.append(result)
                print(f"已完成检查: {account_data['remark']}")
            except Exception as e:
                print(f"处理 {account_data['remark']} 时发生错误: {str(e)}")
    
    return all_vps_details


if __name__ == "__main__":
    print("开始检查 VPS 状态...")
    start_time = time.time()
    
    vps_list = check_vps_status()
    
    end_time = time.time()
    print(f"检查完成，耗时: {end_time - start_time:.2f}秒，结果如下：")

    # 打印控制台输出
    for vps in vps_list:
        if 'status' in vps:
            print(f"[{vps['account']}] {vps['status']}")
        else:
            print(f"[{vps['account']}] IP: {vps['ip']} | 地区: {vps['location']} | 交易量: {vps['transactions']} | 到期: {vps['expire_date']} | 剩余: {vps['days_left']}天")
    
    # 发送到企业微信群机器人
    print("\n准备发送到企业微信群...")
    if MESSAGE_TYPE == "text":
        wechat_content = format_vps_info_text(vps_list)
        send_wechat_text_message(WEBHOOK_URL, wechat_content)
    else:
        wechat_content = format_vps_info_markdown(vps_list)
        send_wechat_markdown_message(WEBHOOK_URL, wechat_content)
    
