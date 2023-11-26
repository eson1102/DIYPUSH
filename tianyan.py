import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import os
import time

def get_page_content(url, cookies):
    try:
        response = requests.get(url, cookies=cookies)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"访问 {url} 时出错：{e}")
        return None

def send_telegram_notification(token, chat_id, message):
    bot = Bot(token=token)
    bot.send_message(chat_id=chat_id, text=message)

def extract_information(soup, left_class, right_class):
    left_elements = soup.find_all('div', class_=left_class)
    right_elements = soup.find_all('div', class_=right_class)

    min_length = min(len(left_elements), len(right_elements))

    information = []
    for i in range(min_length):
        left_text = left_elements[i].text.strip()
        right_text = right_elements[i].text.strip()
        information.append(f"{left_text}: {right_text}")

    return information

def main():
    base_url = "https://vps.wikifx.com/zh-cn/jyzh"
    user_center_url = "https://www.wikifx.com/zh-cn/usercenter/index.html"

    telegram_token = os.environ["BOT_TOKEN"]
    telegram_chat_id = os.environ["CHAT_ID"]

    cookies_list = [
        {
            'account': 'pyjangubwq@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'nZ%252fREPYCNY4jChEq2TyhJQ%253d%253d%257cttt2655%257chttps%253a%252f%252fimg.fx696.com%252fInit%252f900_1.png_wiki-template-global%257c4732690294%257cf538c37f3e058c7e03bb877d5b8582aa',
            }
        },
        {
            'account': 'yushisan@foxmail.com',
            'cookies': {
                'DJkdikKMG': 'JXvND%252fV5YgCaUFRcaZsriw%253d%253d%257cjim%2Bjim%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5559246086%257ca82bb548a16007ab41d5253a0434cb25',
            }
        },
        {
            'account': 'magiceson@vip.qq.com',
            'cookies': {
                'DJkdikKMG': 'l4D9tnpeGd4CnDxzLmP8Bw%253d%253d%257c%25e9%25a1%25be%25e5%25b0%258f%25e9%2593%25ad%2B%25e8%25b4%25a4%25e5%2595%2586%25e8%258d%259f%25c2%25ae%25e4%25bc%2597%25e5%2588%259b%25e7%25a9%25ba%25e9%2597%25b4%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f3731259258%252f3731259258_24995.png_wiki-template-global%257c5559246149%257c7ed770e28fa2a3729a0ff66338cd78ec',
            }
        },
        {
            'account': '13z_w1nz@idrrate.com',
            'cookies': {
                'DJkdikKMG': 'ZHZK2f82lbIJMHHpNdOYYw%253d%253d%257cjhon348%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5559249269%257c4803651ab18841031c2e2f666cf617d9',
            }
        },
        {
            'account': 'vgfvxixz@idrrate.com',
            'cookies': {
                'DJkdikKMG': '6OqTtw%252bzch7fL2BJvNgHLQ%253d%253d%257cFX3565537695%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5855124989%257cc9086a21407d05402e0d222ae1f94d9f',
            }
        },
        {
            'account': 'rfl4vj_j@comparisions.net',
            'cookies': {
                'DJkdikKMG': 'xQVQGxRzXLU2YbNYijqJKA%253d%253d%257cdacid%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c9422479218%257cfc33356f838791e7a9a7ced829bb85a0',
            }
        },
        {
            'account': 'bjtuunopmv@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'PPgySUq%252bC8tOjdWsbRettQ%253d%253d%257ctom8726%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c0740003460%257ccf5dfdd2d179705eb58b3d5caead0820',
            }
        },
        {
            'account': 'unuojabpbw@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'Pe27OdbBhfmKpd8Hz10oKg%253d%253d%257ctomas2335%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4482354603%257c291b3d998ea4faa111eb51453df12011',
            }
        },
        {
            'account': 'vxgihymila@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'WFtQAL24Of9G2YwjYqgu4w%253d%253d%257cdavid1645%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c9676554602%257cba4fa95c4bc9186eae0760f87aeb9ee3',
            }
        },
        {
            'account': 'xjtutwzgwc@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'Od9yoC2SrE1uRkHyF8XUMg%253d%253d%257cdavid185%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4482354790%257c1bb4617aa49eb83ba5f29efb84d334b8',
            }
        },
        {
            'account': 'vdlttzrrbd@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'm%252fMCZMbhiYhM9XDEpQAgMg%253d%253d%257ctom3529%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c9422479425%257c650ad318a93cdf3233695103e924d0cc',
            }
        },
        {
            'account': 'agkreovgoy@iubridge.com',
            'cookies': {
                'DJkdikKMG': '6dBwR5eMHrEIrRX6BA7bRA%253d%253d%257cdavid9748%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4733749961%257c4bb6206248960f6690190e299818203f',
            }
        },
        {
            'account': 'nsjbodelxs@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'hgD6SmDwqMWP7bAy4gmH2A%253d%253d%257ctom2220%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4422337410%257c042f25c849de07273727b518f0129e8b',
            }
        },
        {
            'account': 'dbnywhlbfu@iubridge.com',
            'cookies': {
                'DJkdikKMG': '0s9%252bK%252fBCMPWukDjCNKldTg%253d%253d%257ctom7040%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5559249636%257cd13878820b69ee8221cb04691d2cfbb1',
            }
        },
        {
            'account': 'aoonuvkaiu@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'h8ozj7Vv0n76tQcrlXiEsg%253d%253d%257ctom1124%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c9676554952%257cc24a565960ef2b2139b9d03e945f36f0',
            }
        },
        {
            'account': 'guevbnzsmu@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'XglfddEczxQwdzsui3A4Rw%253d%253d%257ctm9559%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c0740003841%257c1a4810788225b06438e6a30a0b722753',
            }
        },
        {
            'account': 'vhxjcvcwat@iubridge.com',
            'cookies': {
                'DJkdikKMG': '4HA6e4o8bxvVEW65shCXVA%253d%253d%257cuhu8837%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c5559249880%257c1c73f7601be8b41c3d2aaa0361d3ee1a',
            }
        },
        {
            'account': 'jaajfwnilw@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'D3Nq0uDCn1tv9O3uZacgYg%253d%253d%257cto2057%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4422337650%257c8e891a41a3501508dfab8c3ea7f88d87',
            }
        },
        {
            'account': 'zdznfwehez@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'bAmJqy7fF8ar2mW4Zpm7CQ%253d%253d%257chj1810%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4482354181%257c0f1c916bfbb28d939c6b74aba7996668',
            }
        },
        {
            'account': 'ejkriaabdn@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'YhMRwa6raF%252bTC6yg%252fppewg%253d%253d%257cqqq1843%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4422337726%257c64ca379d35f4c34b207cf476f346bcac',
            }
        },
        {
            'account': 'scytxoyqlg@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'L2NTnk%252b3VZM6TokDplYABQ%253d%253d%257cttt563%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c9676554116%257cc52fa09d4e4a4ede53bfc3a6ad3d6449',
            }
        },
        {
            'account': 'wyrgahvqzn@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'xNvz6XMM1mseSUsercMZTg%253d%253d%257cjjj8729%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4422337813%257cb6f97192cad53ac5baa09a8cfca25b38',
            }
        },
        {
            'account': 'bahveatedp@iubridge.com',
            'cookies': {
                'DJkdikKMG': 'sa6KVCy2%252bAn1hzq5rS1jjQ%253d%253d%257caaa344%257chttps%253a%252f%252fimg.fx696.com%252fWikiEnterprise%252fsign%252fpersonph.png_wiki-template-global%257c4422337880%257cb1272cba9980d8df6cd558324c9e5e7e',
            }
        },

        {
            'account': 'duncanyu1102@gmail.com',
            'cookies': {
                'DJkdikKMG': 'codrpWmCzHjBTYo%252bG79kPQ%253d%253d%257cJim6153%257chttps%253a%252f%252fimg.fx696.com%252fthirdparty%252f4769447162%252f4769447162_28637.png_wiki-template-global%257c4421282596%257c8f935b61e24818a96a072b5627e2ae82',
            }
        },
        # ... 添加更多账号及对应的 cookies
    ]

    for i, account_cookies in enumerate(cookies_list, start=1):
        account_name = account_cookies['account']
        cookies = account_cookies['cookies']

        print(f"\n处理第 {i} 个账号: {account_name}")

        user_center_content = get_page_content(user_center_url, cookies)
        if user_center_content:
            user_center_soup = BeautifulSoup(user_center_content, 'html.parser')
            user_email = user_center_soup.find('div', class_='portrait-emit').text.strip()

            print("\n用户信息:")
            print(f"账号: {account_name}")
            print(f"邮箱: {user_email}")
            print("===================")
        else:
            print("无法获取用户中心信息.")
            r = requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage', json={"chat_id": telegram_chat_id, "text": f"无法获取用户中心信息，账号: {account_name}"})

        try:
            vps_content = get_page_content(base_url, cookies)
            if vps_content:
                vps_soup = BeautifulSoup(vps_content, 'html.parser')
                vps_information = extract_information(vps_soup, 'information-list-item-left', 'information-list-item-right')

                print("VPS 信息:")
                
                text = vps_information[3]
                pattern = r'\d{4}-\d{2}-\d{2}'
                match = re.search(pattern, text)

                if match:
                    expiration_date = match.group()
                    print("提取到的日期是:", expiration_date)

                    expiration_datetime = datetime.strptime(expiration_date, "%Y-%m-%d")
                    current_datetime = datetime.now()
                    days_until_expiration = (expiration_datetime - current_datetime).days

                    if 1 < days_until_expiration < 7:
                        reminder_message = (
                            f"提醒：到期时间还有 {days_until_expiration} 天\n"
                            f"===================\n"
                            f"账号 {account_name}\n"
                            f"邮箱 {user_email}\n"
                            f"===================\n"
                            f"VPS信息\n"
                        )
                        for info in vps_information:
                            reminder_message += f"{info}\n"

                        print(reminder_message)
                        r = requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage', json={"chat_id": telegram_chat_id, "text": reminder_message})
                        time.sleep(5)
                else:
                    print("未找到匹配的日期")
                    r = requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage', json={"chat_id": telegram_chat_id, "text": f"未找到匹配的日期，账号: {account_name}"})

            else:
                print("无法获取 VPS 信息.")
                r = requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage', json={"chat_id": telegram_chat_id, "text": f"无法获取 VPS 信息，账号: {account_name}"})

        except Exception as e:
            print(f"在处理账号 {account_name} 时发生错误: {e}")
            r = requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage', json={"chat_id": telegram_chat_id, "text": f"在处理账号 {account_name} 时发生错误,疑似天眼云主机被删除，错误: {e}"})
            continue  # Continue to the next iteration even if an error occurs

if __name__ == "__main__":
    main()
