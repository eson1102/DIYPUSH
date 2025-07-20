import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
import os

chat_id = os.environ.get("CHAT_ID", "未设置")  # 可选使用
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e75ac7b2-f7e7-45a5-a7b8-0f92390ab020"
url = "https://vps.wikifx.com/zh-cn/jyzh"

LOCATION_EMOJIS = {
    "香港": "🇭🇰", "新加坡": "🇸🇬", "美国": "🇺🇸", "日本": "🇯🇵",
    "英国": "🇬🇧", "德国": "🇩🇪", "澳大利亚": "🇦🇺", "加拿大": "🇨🇦",
    "韩国": "🇰🇷", "台湾": "🇹🇼", "澳门": "🇲🇴", "马来西亚": "🇲🇾",
    "俄罗斯": "🇷🇺", "巴西": "🇧🇷", "印度": "🇮🇳"
}

# 你的cookies列表
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
        'DJkdikKMG': 'l4D9tnpeGd4CnDxzLmP8Bw%253d%253d%257c%25e9%25a1%25be%25e5%25b0%258f%25e9%2593%25ad%2B%25e8%25b4%25a4%25e5%2595%2586%25e8%258d%259f%25c2%25ae%25e4%25bc%2597%25e5%2588%259b%25e7%25a9%25ba%25e9%2597%25b4%257chttps%253a%252f%252fimg.fx696.com%252f%252fthirdparty%252f3731259258%252f3731259258_24995.png_wiki200%257c5684213809%257c4e1b12aecd84921870a82460de102e02',
        'remark': 'magiceson@vip.qq.com'
    },
    {
        'DJkdikKMG': 
'hgD6SmDwqMWP7bAy4gmH2A%253d%253d%257ctom2220%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4557438868%257c2dc336931d74210f917b12f7e3d7201b',
        'remark': 'nsjbodelxs@iubridge.com'
    },
    {
        'DJkdikKMG': 
'ncK4Do%252fFX08LfUpcy2Vuog%253d%253d%257cbh91%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c9558792639%257c9902dc74056508234edfe3e68fef9c14',
        'remark': 'iijoidpfdc@iubridge.com'
    },
    {
        'DJkdikKMG': 
'fj96MZf3%252bStvSnUf%252bUVSyQ%253d%253d%257chh5848%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5685545944%257cb10eccbe4f8f269cf4e6e351b0c0d387',
        'remark': 'hwqeecfkzd@iubridge.com'
    },
    {
        'DJkdikKMG': 
'xNvz6XMM1mseSUsercMZTg%253d%253d%257cjjj8729%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4553966332%257ce3524da70aa8e09a9fce9e1df950b93e',
        'remark': 'wyrgahvqzn@iubridge.com'
    },
    {
        'DJkdikKMG': 
'PPgySUq%252bC8tOjdWsbRettQ%253d%253d%257ctom8726%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c0871730611%257c8f8fb7b0f75f8861ddfeaf70faed0555',
        'remark': 'bjtuunopmv@iubridge.com'
    },
    {
        'DJkdikKMG': 
'nZ%2fREPYCNY4jChEq2TyhJQ%3d%3d%7cttt2655%7chttps%3a%2f%2fimg.fx696.com%2fWikiEnterprise%2fsign%2fpersonph.png_wiki-template-global%7c4874607030%7c38ffe74365d16319e350687690da2640',
        'remark': 'pyjangubwq@iubridge.com'
    },
        {
        'DJkdikKMG': 
'bAmJqy7fF8ar2mW4Zpm7CQ%3d%3d%7chj1810%7chttps%3a%2f%2fimg.fx696.com%2fWikiEnterprise%2fsign%2fpersonph.png_wiki-template-global%7c4537459372%7c4fd335a3c568bc551872525f717282be',
        'remark': 'zdznfwehez@iubridge.com'
    },
    # 添加更多账号的cookies和备注
]


def send_wechat_notification(message):
    max_length = 1800
    segments = [message[i:i+max_length] for i in range(0, len(message), max_length)]
    for i, segment in enumerate(segments):
        if len(segments) > 1:
            segment = f"【分段 {i+1}/{len(segments)}】\n{segment}"
        payload = {"msgtype": "text", "text": {"content": segment}}
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code != 200:
            print(f"⚠️ 消息发送失败: {response.text}")
        time.sleep(1)

def check_vps_status():
    stats = {
        'total_accounts': len(cookies_list),
        'active_vps': 0,
        'inactive_accounts': 0,
        'invalid_cookies': 0,
        'no_vps_info': 0,
        'invalid_cookies_list': [],
        'no_vps_info_list': [],
        'locations': {},
        'expired': 0,
        'expiring_urgent': 0,
        'expiring_soon': 0,
        'no_transactions': 0,
        'low_transactions': 0,
        'normal_transactions': 0,
        'critical_vps': [],
        'all_vps_details': []  # ✅ 所有账号信息
    }

    today = datetime.now().date()

    for account_data in cookies_list:
        account_email = account_data['remark']
        cookies = {'DJkdikKMG': account_data['DJkdikKMG']}
        try:
            response = requests.get(url, cookies=cookies, allow_redirects=False)
            if response.status_code == 302:
                stats['no_vps_info'] += 1
                stats['no_vps_info_list'].append(account_email)
                continue
            if response.status_code == 403:
                stats['invalid_cookies'] += 1
                stats['invalid_cookies_list'].append(account_email)
                continue
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                info_div = soup.find('div', class_='information-right')
                if info_div:
                    info_items = {}
                    for item in info_div.find_all('div', class_='information-list-item'):
                        key = item.find('div', class_='information-list-item-left').get_text(strip=True)
                        value = item.find('div', class_='information-list-item-right').get_text(strip=True)
                        info_items[key] = value
                    transactions = int(info_items.get('近1月实盘交易数量', '0'))
                    location = info_items.get('服务器地址', 'N/A')
                    expire_date_str = info_items.get('到期日期', 'N/A')
                    vps_ip = info_items.get('VPS IP', 'N/A')
                    emoji = LOCATION_EMOJIS.get(location, "")
                    if emoji:
                        location = f"{emoji} {location}"
                    stats['active_vps'] += 1
                    transaction_status = ""
                    if transactions == 0:
                        stats['no_transactions'] += 1
                        transaction_status = "❌无交易"
                    elif transactions < 10:
                        stats['low_transactions'] += 1
                        transaction_status = "⚠️低交易"
                    else:
                        stats['normal_transactions'] += 1
                        transaction_status = "✅正常"
                    stats['locations'][location] = stats['locations'].get(location, 0) + 1
                    expire_status = ""
                    days_left = None
                    if expire_date_str != 'N/A':
                        try:
                            expire_date = datetime.strptime(expire_date_str, "%Y-%m-%d").date()
                            days_left = (expire_date - today).days
                            if days_left < 0:
                                stats['expired'] += 1
                                expire_status = "❗❗已过期"
                            elif days_left <= 3:
                                stats['expiring_urgent'] += 1
                                expire_status = "❗❗急需续费"
                            elif days_left <= 7:
                                stats['expiring_soon'] += 1
                                expire_status = "❗需续费"
                            else:
                                expire_status = "✅正常"
                        except ValueError:
                            expire_status = "⏹️日期错误"
                    problems = []
                    if transaction_status != "✅正常":
                        problems.append(f"交易: {transaction_status}({transactions})")
                    if expire_status != "✅正常":
                        problems.append(f"到期: {expire_status}")
                        if days_left is not None:
                            problems.append(f"剩余天数: {days_left}")
                    if problems:
                        stats['critical_vps'].append({
                            'account': account_email,
                            'ip': vps_ip,
                            'location': location,
                            'problems': problems
                        })
                    # ✅ 记录所有账号详情
                    stats['all_vps_details'].append({
                        'account': account_email,
                        'ip': vps_ip,
                        'location': location,
                        'transactions': transactions,
                        'expire_date': expire_date_str,
                        'days_left': days_left,
                        'transaction_status': transaction_status,
                        'expire_status': expire_status
                    })
                else:
                    stats['inactive_accounts'] += 1
            else:
                stats['inactive_accounts'] += 1
        except Exception as e:
            stats['inactive_accounts'] += 1
        time.sleep(2)

    today_str = today.strftime('%Y-%m-%d')
    wechat_msg = f"""⏰ 天眼云VPS健康状态报告 {today_str}

📊 基础统计
总账号: {stats['total_accounts']}
有效VPS: {stats['active_vps']}
无效账号: {stats['inactive_accounts']}
🚫 Cookies失效(403): {stats['invalid_cookies']}
⚠️ 无法获取VPS信息(302): {stats['no_vps_info']}"""

    if stats['invalid_cookies_list']:
        wechat_msg += "\n\n🔴 Cookies失效账号列表(403):"
        for account in stats['invalid_cookies_list']:
            wechat_msg += f"\n• {account}"

    wechat_msg += f"""

🔢 交易量问题统计
❌ 无交易: {stats['no_transactions']}
⚠️ 低交易(0<x<10): {stats['low_transactions']}

⏳ 到期问题统计
急需续费(≤3天): {stats['expiring_urgent']}
需续费(≤7天): {stats['expiring_soon']}

🌍 地区分布
""" + "\n".join([f"{loc}: {count}" for loc, count in stats['locations'].items()])

    if stats['critical_vps']:
        critical_report = "\n\n🚨 问题VPS列表\n"
        for vps in stats['critical_vps']:
            critical_report += f"""
账号: {vps['account']}
IP: {vps['ip']}
地区: {vps['location']}"""
            for problem in vps['problems']:
                critical_report += f"\n{problem}"
            critical_report += "\n"
        wechat_msg += critical_report

    # ✅ 添加所有账号信息
    vps_details_text = "\n\n📄 所有账号VPS明细"
    for vps in stats['all_vps_details']:
        vps_details_text += f"""
账号: {vps['account']}
IP: {vps['ip']}
地区: {vps['location']}
交易状态: {vps['transaction_status']} ({vps['transactions']})
到期状态: {vps['expire_status']} | 到期日: {vps['expire_date']}"""
        if vps['days_left'] is not None:
            vps_details_text += f" | 剩余: {vps['days_left']}天"
        vps_details_text += "\n"
    wechat_msg += vps_details_text

    wechat_msg += f"\n\n⏱️ 统计时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return wechat_msg

if __name__ == "__main__":
    try:
        print("开始检查VPS状态...")
        report = check_vps_status()
        print("生成报告成功，正在发送企业微信通知...")
        send_wechat_notification(report)
        print("通知发送完成！")
    except Exception as e:
        error_msg = f"❌ VPS状态检查失败: {str(e)}"
        print(error_msg)
        send_wechat_notification(error_msg)
