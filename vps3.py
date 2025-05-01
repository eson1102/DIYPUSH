import requests
from bs4 import BeautifulSoup
import threading
import os

url = 'https://vps.wikifx.com/zh-cn/jyzh'
bot_token = os.environ["BOT_TOKEN"]
chat_id = os.environ["CHAT_ID"]

# 多个账号的cookies字典，每个账号添加一个备注
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

messages = []  # 用于存储所有账号的消息

def fetch_data(cookies):
    try:
        response = requests.get(url, cookies=cookies)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content.decode('utf-8'), 'html.parser')
            information_div = soup.find('div', class_='information-list')
            if information_div:
                message = f'{cookies["remark"]}:\n'
                for item in information_div.find_all('div', class_='information-list-item'):
                    left = item.find('div', class_='information-list-item-left').text.strip()
                    right = item.find('div', class_='information-list-item-right').text.strip()
                    if left in ['VPS IP', '服务器地址', '到期日期', '近1月实盘交易数量']:
                        message += f'  {left}: {right}\n'
                messages.append(message)
            else:
                messages.append(f'{cookies["remark"]}: 没有找到包含信息的div元素。')
        else:
            messages.append(f'{cookies["remark"]}: 请求失败，状态码：{response.status_code}')
    except Exception as e:
        messages.append(f'{cookies["remark"]}: 请求发生错误：{e}')

threads = []
for cookies in cookies_list:
    thread = threading.Thread(target=fetch_data, args=(cookies,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

# 合成消息并发送
final_message = '\n'.join(messages)
requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={"chat_id": chat_id, "text": final_message})
