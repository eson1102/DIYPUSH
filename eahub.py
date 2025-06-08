import requests
from bs4 import BeautifulSoup
import time
import random
import re

# 自定义回复列表
REPLY_TEMPLATES = [
    "感谢分享，这个策略看起来很有潜力！",
    "非常实用的EA，下载试试看效果如何。",
    "楼主辛苦了，这个资源对我很有帮助！",
    "看起来不错，请问有实盘数据可以参考吗？",
    "感谢开源，这对我们学习EA开发很有帮助！",
    "这个EA的思路很新颖，期待测试结果。",
    "请问这个EA适合哪个时间周期？",
    "看起来很棒，请问有使用说明文档吗？",
    "感谢分享，已经下载测试了！",
    "这个策略的回测数据看起来很不错！",
    "感谢分享，这个策略值得测试。",
    "EA已下载，准备进行回测验证。",
    "请问该策略的最大回撤是多少？",
    "是否有历史回测报告可供参考？",
    "代码结构清晰，适合进一步优化。",
    "请问支持哪些货币对？",
    "已部署到模拟账户，观察运行情况。",
    "参数设置是否经过优化？",
    "请问是否需要特定经纪商条件？",
    "策略逻辑明确，符合预期。",
    "是否有MT5版本？",
    "请问推荐使用哪个时间框架？",
    "EA运行稳定，无异常报错。",
    "是否支持自动新闻过滤？",
    "请问最低账户资金要求是多少？",
    "已测试EUR/USD，结果符合文档说明。",
    "请问是否支持多品种同时运行？",
    "是否有详细的参数说明？",
    "回测数据显示策略表现稳定。",
    "请问是否支持Tick数据测试？",
    "EA在VPS上运行流畅。",
    "请问是否有动态止损功能？",
    "已收到信号，正在验证准确性。",
    "请问是否支持自定义指标？",
    "策略在震荡行情中表现如何？",
    "是否有实盘账户的跟踪记录？",
    "请问是否支持对冲模式？",
    "EA在M5周期上运行正常。",
    "是否有风险控制模块？",
    "请问是否支持部分平仓功能？",
    "策略在趋势行情中表现良好。",
    "是否有移动端监控方案？",
    "请问滑点控制在多少范围内？",
    "EA在低延迟环境下运行稳定。",
    "是否有自动参数优化功能？",
    "请问是否支持多账户同步？",
    "策略在黄金市场表现如何？",
    "是否有详细的安装指南？",
    "请问是否支持一键平仓？",
    "EA在H1周期上运行正常。",
    "是否有止损追踪功能？",
    "请问是否支持API接入？",
    "策略在美盘时段表现稳定。",
    "是否有云端信号订阅？",
    "请问是否支持自定义资金管理？",
    "EA在D1周期上运行正常。",
    "是否有邮件或短信通知功能？",
    "请问是否支持多时间框架分析？",
    "策略在亚洲盘口表现如何？",
    "是否有完整的日志记录功能？",
]

def parse_discuz_profile(html_content, uid):
    """解析Discuz用户资料页面"""
    soup = BeautifulSoup(html_content, 'html.parser')
    profile = {'uid': str(uid)}
    
    try:
        # 提取基本信息
        username_element = soup.find('h2', class_='mbn')
        if username_element:
            profile['username'] = username_element.get_text(" ", strip=True).split('(UID:')[0].strip()
        
        # 在线状态
        online_icon = soup.find('img', {'alt': 'online'})
        profile['online_status'] = "在线" if online_icon else "离线"
        
        # 活跃概况
        active_info = soup.find('ul', id='pbbs')
        if active_info:
            for li in active_info.find_all('li'):
                text = li.get_text(strip=True)
                if '在线时间' in text:
                    profile['online_time'] = text.split('在线时间')[-1].strip()
                elif '注册时间' in text:
                    profile['register_time'] = text.split('注册时间')[-1].strip()
                elif '注册 IP' in text:
                    profile['register_ip'] = text.split('注册 IP')[-1].strip()
                elif '上次访问 IP' in text:
                    profile['last_ip'] = text.split('上次访问 IP')[-1].strip()
                elif '上次发表时间' in text:
                    profile['last_post_time'] = text.split('上次发表时间')[-1].strip()
                elif '所在时区' in text:
                    profile['timezone'] = text.split('所在时区')[-1].strip()
        
        # 积分信息
        points_info = soup.find('div', id='psts')
        if points_info:
            for li in points_info.find_all('li'):
                text = li.get_text(strip=True)
                if '积分' in text:
                    profile['points'] = text.split('积分')[-1].strip()
                elif 'H币' in text:
                    profile['h_coin'] = text.split('H币')[-1].strip()
                elif '活跃度' in text:
                    profile['activity'] = text.split('活跃度')[-1].strip()
                elif 'U币' in text:
                    profile['u_coin'] = text.split('U币')[-1].strip()
                elif '已用空间' in text:
                    profile['used_space'] = text.split('已用空间')[-1].strip()
        
        # 评级信息
        rating = soup.find('span', class_='xi2')
        if rating:
            profile['rating'] = rating.get_text(strip=True)
            profile['rating_tip'] = rating.get('tip', '')
        
        # 个人资料链接
        profile['profile_url'] = f"https://www.eahub.cn/home.php?mod=space&uid={uid}"
        
    except Exception as e:
        print(f"解析过程中出错: {str(e)}")
    
    return profile

def get_discuz_profile(uid, cookies=None, headers=None):
    """获取Discuz用户资料"""
    url = f'https://www.eahub.cn/home.php?mod=space&uid={uid}'
    
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': f'https://www.eahub.cn/home.php?mod=space&uid={uid}'
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers or default_headers)
        
        if cookies:
            if isinstance(cookies, dict):
                session.cookies.update(cookies)
            else:
                print("警告: cookies参数应为字典格式")
        
        response = session.get(url)
        response.raise_for_status()  # 检查HTTP错误
        
        if '您无权进行当前操作' in response.text:
            print("错误: 没有查看该用户资料的权限")
            return None
        
        return parse_discuz_profile(response.text, uid)
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP错误: {http_err}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"连接错误: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"请求超时: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求异常: {req_err}")
    except Exception as e:
        print(f"获取用户资料时出错: {str(e)}")
    
    return None

def get_latest_posts(cookies=None, headers=None, limit=5):
    """获取论坛最新帖子"""
    url = 'https://www.eahub.cn/forum.php?mod=forumdisplay&fid=41&filter=author&orderby=dateline'
    
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.eahub.cn/'
    }
    
    try:
        session = requests.Session()
        session.headers.update(headers or default_headers)
        
        if cookies:
            if isinstance(cookies, dict):
                session.cookies.update(cookies)
            else:
                print("警告: cookies参数应为字典格式")
        
        response = session.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = []
        
        # 查找所有帖子tbody
        post_tbodies = soup.find_all('tbody', id=lambda x: x and ('normalthread' in x or 'stickthread' in x))
        
        for tbody in post_tbodies[:limit]:
            post = {}
            
            # 获取帖子标题和链接
            title_link = tbody.find('a', class_='tit')
            if title_link:
                post['title'] = title_link.get_text(strip=True)
                post['url'] = title_link['href']
                if not post['url'].startswith('http'):
                    post['url'] = 'https://www.eahub.cn/' + post['url']
                # 提取帖子ID
                match = re.search(r'tid=(\d+)', post['url'])
                if match:
                    post['tid'] = match.group(1)
            
            # 获取作者信息
            author_link = tbody.find('a', class_='userauthor')
            if author_link:
                post['author'] = author_link.get_text(strip=True)
                post['author_url'] = author_link['href']
                if 'space-uid-' in post['author_url']:
                    post['author_uid'] = post['author_url'].split('space-uid-')[-1].split('.')[0]
            
            # 获取浏览数和回复数
            views = tbody.find('em', title=True)
            if views:
                post['views'] = views.get_text(strip=True)
            
            replies = tbody.find('span', class_='replies')
            if replies:
                post['replies'] = replies.get_text(strip=True)
            
            # 获取发布时间
            time_span = tbody.find('span', class_='time')
            if time_span:
                post['post_time'] = time_span.get_text(strip=True)
            
            # 获取分类信息
            categories = []
            cate_links = tbody.find_all('a', href=lambda x: x and ('strategyType_' in x or 'strategyPlatform_' in x or 'strategyFile_' in x))
            for link in cate_links:
                categories.append(link.get_text(strip=True))
            if categories:
                post['categories'] = categories
            
            if post.get('url'):
                # 访问帖子获取更多详情
                post_details = get_post_details(post['url'], cookies, headers)
                if post_details:
                    post.update(post_details)
            
            posts.append(post)
        
        return posts
        
    except Exception as e:
        print(f"获取最新帖子时出错: {str(e)}")
        return None

def get_post_details(post_url, cookies=None, headers=None):
    """获取帖子详情内容"""
    try:
        session = requests.Session()
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.eahub.cn/'
        }
        session.headers.update(headers or default_headers)
        
        if cookies:
            session.cookies.update(cookies)
        
        response = session.get(post_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        details = {}
        
        # 获取帖子内容
        content_div = soup.find('div', class_='t_fsz')
        if content_div:
            details['content'] = content_div.get_text(strip=True)
        
        # 获取附件信息
        attachments = []
        attach_links = soup.find_all('a', href=lambda x: x and 'forum.php?mod=attachment' in x)
        for link in attach_links:
            attachments.append({
                'name': link.get_text(strip=True),
                'url': link['href']
            })
        if attachments:
            details['attachments'] = attachments
        
        # 获取formhash (用于回复)
        formhash_input = soup.find('input', {'name': 'formhash'})
        if formhash_input:
            details['formhash'] = formhash_input['value']
        
        return details
        
    except Exception as e:
        print(f"获取帖子详情时出错: {str(e)}")
        return None

def post_reply(post_url, reply_content, cookies=None, headers=None):
    """在指定帖子中回复"""
    try:
        # 首先获取帖子页面以获取formhash等必要信息
        session = requests.Session()
        default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': post_url
        }
        session.headers.update(headers or default_headers)
        
        if cookies:
            session.cookies.update(cookies)
        
        # 获取帖子信息
        response = session.get(post_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取formhash
        formhash_input = soup.find('input', {'name': 'formhash'})
        if not formhash_input:
            print("错误: 无法获取formhash")
            return False
        formhash = formhash_input['value']
        
        # 提取帖子ID
        match = re.search(r'tid=(\d+)', post_url)
        if not match:
            print("错误: 无法从URL中提取帖子ID")
            return False
        tid = match.group(1)
        
        # 构建回复数据
        reply_url = 'https://www.eahub.cn/forum.php?mod=post&action=reply&tid=' + tid + '&extra=&replysubmit=yes&infloat=yes&handlekey=fastpost&inajax=1'
        
        post_data = {
            'formhash': formhash,
            'message': reply_content,
            'usesig': '1',
            'subject': '',
            'replysubmit': 'true'
        }
        
        # 发送回复
        response = session.post(reply_url, data=post_data)
        response.raise_for_status()
        
        # 检查回复是否成功
        if 'succeed' in response.text:
            print("回复成功!")
            return True
        else:
            print("回复失败:", response.text)
            return False
        
    except Exception as e:
        print(f"回复帖子时出错: {str(e)}")
        return False

# 示例使用
if __name__ == '__main__':
    # 示例cookies（使用你提供的cookies）
    example_cookies = {
        "HMACCOUNT": "AA7C9B444AE3055C",
        "64rF_2132_smile": "4D1",
        "64rF_2132_home_diymode": "1",
        "64rF_2132_clearUserdata": "forum",
        "64rF_2132_saltkey": "lTzFqxj6",
        "64rF_2132_lastvisit": "1748056159",
        "64rF_2132_auth": "44f6QYaX51t%2B2YBfTOANZEhlmVd3s7IjhkYnq7UfLdclP4YmxHX2Zkep%2Bx48pkqKUfGb25qgK7Mx%2F9RGTb1reF8",
        "seaHis": "%5B%22%E9%87%91%E9%94%81%22%5D",
        "64rF_2132_visitedfid": "41",
        "64rF_2132_st_p": "610%7C1749213767%7C831dc835af34172f37ec1f1da27ecab5",
        "64rF_2132_zqlj_userlog": "8d39e191aa6d02f5bb8cee2df4cac047",
        "64rF_2132_pc_size_c": "0",
        "64rF_2132_ulastactivity": "89faq8Ohr9CVMtMNDm8d9V6KQRkW2JVPcxkc1TPooofecoZYANKG",
        "64rF_2132_viewid": "uid_610",
        "Hm_lvt_bb18f408ae1aff391c9ec42813571ad9": "1749364360",
        "Hm_lpvt_bb18f408ae1aff391c9ec42813571ad9": "1749366441",
        "64rF_2132_noticeTitle": "1",
        "64rF_2132_sid": "jI6fEF",
        "64rF_2132_lip": "178.239.123.9%2C1749367788",
        "64rF_2132_st_t": "610%7C1749368614%7C3c181f3fb971dcf05c7fb8bb9fc6eeb3",
        "64rF_2132_forum_lastvisit": "D_41_1749368614",
        "64rF_2132_checkpm": "1",
        "64rF_2132_lastcheckfeed": "610%7C1749368616",
        "64rF_2132_checkfollow": "1",
        "64rF_2132_lastact": "1749368631%09forum.php%09viewthread",
        "64rF_2132_nomultiple": "6aa72e513babbe54cb531ea523aa8811"
        }
    
    # 获取最新5篇帖子
    print("正在获取最新帖子...")
    latest_posts = get_latest_posts(cookies=example_cookies, limit=1)
    
    if latest_posts:
        print("\n" + "="*50)
        print(f"最新5篇帖子信息")
        print("="*50)
        
        for i, post in enumerate(latest_posts, 1):
            print(f"\n帖子 #{i}: {post.get('title', '无标题')}")
            print("-"*50)
            print(f"作者: {post.get('author', '未知')} (UID: {post.get('author_uid', '未知')})")
            print(f"发布时间: {post.get('post_time', '未知')}")
            print(f"分类: {', '.join(post.get('categories', []))}")
            print(f"帖子链接: {post.get('url', '未知')}")

            
            # 随机选择一条回复并发送
            if 'url' in post and 'tid' in post:
                print("\n准备回复帖子...")
                reply_content = random.choice(REPLY_TEMPLATES)
                print(f"回复内容: {reply_content}")
                
                # 实际发送回复
                success = post_reply(post['url'], reply_content, cookies=example_cookies)
                if success:
                    print("回复发送成功!")
                else:
                    print("回复发送失败")
            
            print("-"*50)
            time.sleep(10)  # 礼貌性延迟，避免请求过于频繁
        
        print("\n" + "="*50)
        print("帖子获取和回复完成")
        print("="*50)
    else:
        print("无法获取最新帖子")
