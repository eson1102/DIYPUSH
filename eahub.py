import requests
import random
import time
from datetime import datetime
from urllib.parse import urljoin

def visit_eahub_random_pages():
    # 基础URL
    base_url = "https://www.eahub.cn/"
    target_url = urljoin(base_url, "forum-41-1.html")
    
    # 你提供的cookies
    cookies = {
        'Hm_lvt_bb18f408ae1aff391c9ec42813571ad9': '1745053672',
        'HMACCOUNT': 'AA7C9B444AE3055C',
        'Hm_lpvt_bb18f408ae1aff3919ec42813571ad9': '1745053675',
        '64rF_2132_pc_size_c': '0',
        '64rF_2132_saltkey': 'fzj0Ju0G',
        '64rF_2132_lastvisit': '1745062094',
        '64rF_2132_auth': '9d84eWlfKK1tZ6ya2%2Br5ZB3tLp4xRIjl3VR1q9uSOZ%2FNtH%2BkmJlOUMPmtfskTzVW00hJjdah9hX3rBBBU8DfeOQ',
        '64rF_2132_zqlj_userlog': '7fe089465007cdb400ee88c9e0ce9fd4',
        '64rF_2132_smile': '4D1',
        '64rF_2132_visitedfid': '41D40',
        'vClickLastTime': 'a%3A3%3A%7Bi%3A0%3Bi%3A1744992000%3Bi%3A1%3Bi%3A1744992000%3Bi%3A142942%3Bi%3A1744992000%3B%7D',
        '64rF_2132_st_p': '610%7C1745067237%7C75154a61bdef495a238cfcd97bd0c031',
        '64rF_2132_viewid': 'tid_144085',
        '64rF_2132_noticeTitle': '1',
        '64rF_2132_sid': 're5uKk',
        '64rF_2132_lip': '101.228.119.208%2C1745067237',
        '64rF_2132_st_t': '610%7C1745111694%7C612b01e2ad662932f90a7433f07eeffb',
        '64rF_2132_forum_lastvisit': 'D_41_1745111694',
        '64rF_2132_ulastactivity': 'a9b1wpLWT49khNlCirCRMbOZsPyU%2B16d0CcII3tY%2BXqWf%2B2x%2BRLs',
        '64rF_2132_lastcheckfeed': '610%7C1745111695',
        '64rF_2132_lastact': '1745112136%09forum.php%09viewthread',
        '64rF_2132_nomultiple': '8d18b9852e2908312b5d19ba47d1c0f4'
    }
    
    # 设置请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': base_url,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Connection': 'keep-alive'
    }
    
    try:
        # 创建会话
        session = requests.Session()
        session.headers.update(headers)
        session.cookies.update(cookies)
        
        # 1. 首先访问目标页面
        print(f"[{datetime.now()}] 正在访问目标页面: {target_url}")
        response = session.get(target_url)
        print(f"目标页面状态码: {response.status_code}")
        
        if response.status_code != 200:
            print("目标页面访问失败，终止操作")
            return
        
        # 2. 随机选择3个其他页面访问
        # 常见Discuz论坛URL模式
        possible_pages = [
            "forum-42-1.html",  # 其他板块
            "forum-43-1.html",
            "forum-44-1.html",
            "forum.php?mod=forumdisplay&fid=45",
            "forum.php?mod=viewthread&tid=144086",  # 随机帖子
            "forum.php?mod=viewthread&tid=144087",
            "forum.php?mod=guide&view=newthread",  # 新帖
            "forum.php?mod=guide&view=hot",  # 热门
            "home.php?mod=space&uid=1",  # 用户空间
            "portal.php",  # 门户首页
        ]
        
        # 随机选择3个不重复的页面
        random_pages = random.sample(possible_pages, min(3, len(possible_pages)))
        
        for i, page in enumerate(random_pages, 1):
            page_url = urljoin(base_url, page)
            
            # 添加随机延迟(1-5秒)模拟人类浏览
            delay = random.uniform(1, 5)
            print(f"[{datetime.now()}] 等待 {delay:.1f} 秒后访问第 {i} 个随机页面...")
            time.sleep(delay)
            
            print(f"[{datetime.now()}] 正在访问随机页面 {i}: {page_url}")
            page_response = session.get(page_url)
            print(f"页面 {i} 状态码: {page_response.status_code}")
            
            # 简单的访问验证
            if page_response.status_code == 200:
                print(f"成功访问: {page_url}")
            else:
                print(f"访问失败: {page_url}")
        
        print(f"[{datetime.now()}] 所有页面访问完成")
        
    except requests.exceptions.RequestException as e:
        print(f"网络请求出错: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")

if __name__ == "__main__":
    visit_eahub_random_pages()
