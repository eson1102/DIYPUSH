import os
import requests
import json
import hashlib
import time
from datetime import datetime

class MindVideoAutoCheckin:
    def __init__(self):
        # 从环境变量读取账号密码
        self.email = os.environ.get('EMAIL')
        self.password = os.environ.get('PASSWORD')  # 明文密码
        
        # API地址
        self.login_url = "https://api-app.mindvideo.ai/api/login"
        self.checkin_url = "https://api-app.mindvideo.ai/api/checkin"
        
        # 基础请求头
        self.base_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "application/json, text/plain, */*",
            "origin": "https://www.mindvideo.ai",
            "referer": "https://www.mindvideo.ai/",
            "content-type": "application/json",
            "i-lang": "zh-CN",
            "i-version": "1.0.8"
        }
        
        self.token = None
        
    def md5_encrypt(self, text):
        """MD5加密"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def login(self):
        """自动登录获取Token"""
        if not self.email or not self.password:
            print("❌ 错误：未设置账号密码环境变量")
            print("请在GitHub Secrets中设置 EMAIL 和 PASSWORD")
            return False
            
        print(f"🔄 正在登录账号: {self.email}")
        
        # 加密密码（MD5）
        encrypted_password = self.md5_encrypt(self.password)
        
        # 登录请求体
        login_data = {
            "email": self.email,
            "password": encrypted_password
        }
        
        # 复制基础headers并添加特定headers
        headers = self.base_headers.copy()
        # 注意：i-sign 可能每次都需要从服务器获取，这里先尝试不使用
        # 如果登录失败，可能需要额外处理 i-sign
        
        try:
            print(f"📤 发送登录请求...")
            response = requests.post(
                self.login_url, 
                json=login_data, 
                headers=headers, 
                timeout=30
            )
            
            print(f"📥 登录响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📊 登录响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 根据实际响应提取Token
                # 尝试多种可能的字段路径
                token = None
                if 'data' in result and result['data']:
                    if 'token' in result['data']:
                        token = result['data']['token']
                    elif 'access_token' in result['data']:
                        token = result['data']['access_token']
                elif 'token' in result:
                    token = result['token']
                elif 'access_token' in result:
                    token = result['access_token']
                
                if token:
                    # 确保Token格式正确
                    if not token.startswith('Bearer '):
                        self.token = f'Bearer {token}'
                    else:
                        self.token = token
                    
                    print(f"✅ 登录成功！Token已获取")
                    print(f"🔑 Token预览: {self.token[:50]}...")
                    return True
                else:
                    print("⚠️ 未找到Token字段")
                    print(f"响应中的字段: {list(result.keys())}")
                    return False
            else:
                print(f"❌ 登录失败，状态码: {response.status_code}")
                print(f"返回内容: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 登录异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def checkin(self):
        """执行签到"""
        if not self.token:
            print("❌ 未获取到Token，请先登录")
            return False
        
        print("🔄 正在执行签到...")
        
        headers = self.base_headers.copy()
        headers["authorization"] = self.token
        
        try:
            response = requests.post(
                self.checkin_url, 
                headers=headers, 
                timeout=30
            )
            
            print(f"📥 签到响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 签到成功！")
                print(f"📊 返回数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 解析返回的数据
                if 'data' in result and result['data']:
                    data = result['data']
                    if 'points' in data:
                        print(f"💎 当前积分: {data['points']}")
                    if 'continuity' in data:
                        print(f"📅 连续签到: {data['continuity']}天")
                    if 'message' in data:
                        print(f"📝 消息: {data['message']}")
                elif 'message' in result:
                    print(f"📝 消息: {result['message']}")
                
                return True
            else:
                print(f"❌ 签到失败，状态码: {response.status_code}")
                print(f"返回内容: {response.text}")
                
                # 如果返回401，说明Token过期
                if response.status_code == 401:
                    print("⚠️ Token已过期，需要重新登录")
                    return False
                return False
                
        except Exception as e:
            print(f"❌ 签到异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run(self):
        """主流程"""
        print("=" * 60)
        print(f"🚀 MindVideo自动签到系统启动")
        print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 登录获取Token
        if not self.login():
            print("❌ 登录失败，签到流程终止")
            return False
        
        print("-" * 60)
        
        # 2. 执行签到
        if self.checkin():
            print("🎉 签到流程完成！")
            return True
        else:
            print("❌ 签到流程失败")
            return False

if __name__ == "__main__":
    checker = MindVideoAutoCheckin()
    success = checker.run()
    
    # 退出码用于GitHub Actions判断
    exit(0 if success else 1)
