import requests
import json
import time

# 1. 设置签到地址和你的Token
url = "https://api-app.mindvideo.ai/api/checkin"
token = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FwaS1hcHAubWluZHZpZGVvLmFpL2FwaS9yZWZyZXNoIiwiaWF0IjoxNzg2OTMwODE1LCJleHAiOjE3ODcxMDkwMTYsIm5iZiI6MTc4NzEwMTgxNiwianRpIjoiSFUwVk9aRVpicGdkOUZ4ZyIsInN1YiI6IjIzMTkxNDIiLCJwcnYiOiIyM2JkNWM4OTQ5ZjYwMGFkYjM5ZTcwMWM0MDA4NzJkYjdhNTk3NmY3IiwidWlkIjoyMzE5MTQyLCJlbWFpbCI6ImR1bmNhbnl1MTEwMkBnbWFpbC5jb20iLCJpc05ldyI6ZmFsc2V9.YSyrxhmvv4PBUSeX20JEP8XaPRQckXpRPz7aZ9zsJuI"  # 请复制上面那一长串，包括前面的 "Bearer "

# 2. 设置请求头（模拟浏览器行为）
headers = {
    "authorization": token,
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "accept": "application/json, text/plain, */*",
    "origin": "https://www.mindvideo.ai",
    "referer": "https://www.mindvideo.ai/"
}

# 3. 发送签到请求
try:
    response = requests.post(url, headers=headers)
    
    # 4. 检查结果
    if response.status_code == 200:
        result = response.json()
        # 假设返回的数据中有 'code' 或 'message' 字段，根据你的需求调整
        print(f"签到成功！服务器返回: {result}")
    else:
        print(f"签到失败，状态码: {response.status_code}, 返回内容: {response.text}")
except Exception as e:
    print(f"发生错误: {e}")
