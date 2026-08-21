import os
import requests
import json
import hashlib
from datetime import datetime

class MindVideoAutoCheckin:
    def __init__(self):
        # 从环境变量读取账号密码
        self.email = os.environ.get('EMAIL')
        self.password = os.environ.get('PASSWORD')  # 明文密码
        self.webhook_url = os.environ.get('WECOM_WEBHOOK')  # 企业微信机器人webhook
        
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
        self.checkin_result = {
            "success": False,
            "message": "",
            "points": 0,
            "continuity": 0,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    def md5_encrypt(self, text):
        """MD5加密"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def send_wecom_message(self, title, content, is_success=True):
        """发送企业微信机器人消息（Text格式）"""
        if not self.webhook_url:
            print("⚠️ 未设置企业微信Webhook，跳过通知")
            return False
        
        try:
            # 构建纯文本消息
            if is_success:
                status_emoji = "✅"
            else:
                status_emoji = "❌"
            
            # 构建完整的文本内容
            full_text = f"""【{status_emoji} {title}】
━━━━━━━━━━━━━━━━━━━━
📅 时间：{self.checkin_result['timestamp']}
📧 账号：{self.email}
📊 状态：{'成功 ✅' if is_success else '失败 ❌'}
{content}
━━━━━━━━━━━━━━━━━━━━
🤖 MindVideo 自动签到系统"""
            
            # 企业微信机器人Text消息格式
            message = {
                "msgtype": "text",
                "text": {
                    "content": full_text
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    print("✅ 企业微信通知发送成功")
                    return True
                else:
                    print(f"⚠️ 企业微信通知发送失败: {result}")
                    return False
            else:
                print(f"⚠️ 企业微信通知发送失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ 发送企业微信通知异常: {e}")
            return False
    
    def login(self):
        """自动登录获取Token"""
        if not self.email or not self.password:
            error_msg = "❌ 错误：未设置账号密码环境变量"
            print(error_msg)
            self.checkin_result["message"] = error_msg
            return False
            
        print(f"🔄 正在登录账号: {self.email}")
        
        # 加密密码（MD5）
        encrypted_password = self.md5_encrypt(self.password)
        
        # 登录请求体
        login_data = {
            "email": self.email,
            "password": encrypted_password
        }
        
        try:
            response = requests.post(
                self.login_url, 
                json=login_data, 
                headers=self.base_headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # 提取Token
                token = None
                if 'data' in result and result['data']:
                    token = result['data'].get('token')
                if not token:
                    token = result.get('token')
                
                if token:
                    if not token.startswith('Bearer '):
                        self.token = f'Bearer {token}'
                    else:
                        self.token = token
                    
                    print(f"✅ 登录成功！")
                    return True
                else:
                    error_msg = f"登录响应中未找到Token"
                    print(f"⚠️ {error_msg}")
                    self.checkin_result["message"] = error_msg
                    return False
            else:
                error_msg = f"登录失败，状态码: {response.status_code}"
                print(f"❌ {error_msg}")
                self.checkin_result["message"] = error_msg
                return False
                
        except Exception as e:
            error_msg = f"登录异常: {str(e)}"
            print(f"❌ {error_msg}")
            self.checkin_result["message"] = error_msg
            return False
    
    def checkin(self):
        """执行签到"""
        if not self.token:
            error_msg = "未获取到Token，请先登录"
            print(f"❌ {error_msg}")
            self.checkin_result["message"] = error_msg
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
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 签到成功！")
                print(f"📊 返回数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                # 解析返回的数据
                self.checkin_result["success"] = True
                
                if 'data' in result and result['data']:
                    data = result['data']
                    self.checkin_result["points"] = data.get('points', 0)
                    self.checkin_result["continuity"] = data.get('continuity', 0)
                    
                    # 构建成功消息
                    msg_parts = []
                    if 'points' in data:
                        msg_parts.append(f"💎 当前积分：{data['points']}")
                    if 'continuity' in data:
                        msg_parts.append(f"📅 连续签到：{data['continuity']}天")
                    if 'message' in data:
                        msg_parts.append(f"📝 消息：{data['message']}")
                    
                    self.checkin_result["message"] = "\n".join(msg_parts) if msg_parts else "签到成功"
                elif 'message' in result:
                    self.checkin_result["message"] = result['message']
                else:
                    self.checkin_result["message"] = "签到成功"
                
                return True
            else:
                error_msg = f"签到失败，状态码: {response.status_code}"
                print(f"❌ {error_msg}")
                self.checkin_result["message"] = error_msg
                
                if response.status_code == 401:
                    self.checkin_result["message"] = "Token已过期，需要重新登录"
                    print("⚠️ Token已过期")
                
                return False
                
        except Exception as e:
            error_msg = f"签到异常: {str(e)}"
            print(f"❌ {error_msg}")
            self.checkin_result["message"] = error_msg
            return False
    
    def send_notification(self):
        """发送通知（根据签到结果）"""
        if self.checkin_result["success"]:
            title = "MindVideo 签到成功 🎉"
            content = f"""
{self.checkin_result['message']}

💎 积分：{self.checkin_result.get('points', 'N/A')}
📅 连续签到：{self.checkin_result.get('continuity', 'N/A')}天"""
            return self.send_wecom_message(title, content, is_success=True)
        else:
            title = "MindVideo 签到失败 ⚠️"
            content = f"""
❌ 错误信息：{self.checkin_result['message']}

💡 建议检查：
  • 账号密码是否正确
  • 网络是否正常
  • Token是否过期"""
            return self.send_wecom_message(title, content, is_success=False)
    
    def run(self):
        """主流程"""
        print("=" * 60)
        print(f"🚀 MindVideo自动签到系统启动")
        print(f"⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 登录获取Token
        if not self.login():
            print("❌ 登录失败，签到流程终止")
            self.send_notification()  # 发送失败通知
            return False
        
        print("-" * 60)
        
        # 2. 执行签到
        if self.checkin():
            print("🎉 签到流程完成！")
            self.send_notification()  # 发送成功通知
            return True
        else:
            print("❌ 签到流程失败")
            self.send_notification()  # 发送失败通知
            return False

if __name__ == "__main__":
    checker = MindVideoAutoCheckin()
    success = checker.run()
    
    # 退出码用于GitHub Actions判断
    exit(0 if success else 1)
