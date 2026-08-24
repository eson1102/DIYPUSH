import os
import requests
import json
import hashlib
from datetime import datetime
import pytz  # 添加时区库

class MindVideoAutoCheckin:
    def __init__(self):
        # 从环境变量读取账号密码
        self.email = os.environ.get('EMAIL')
        self.password = os.environ.get('PASSWORD')
        self.webhook_url = os.environ.get('WECOM_WEBHOOK')
        
        # API地址
        self.login_url = "https://api-app.mindvideo.ai/api/login"
        self.checkin_url = "https://api-app.mindvideo.ai/api/checkin"
        self.credits_url = "https://api-app.mindvideo.ai/api/user/credits/stats"
        
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
            "total_credits": 0,
            "used_credits": 0,
            "remaining_credits": 0,
            "subscription_type": "Free",
            "timestamp": self.get_beijing_time()  # 使用北京时间
        }
    
    def get_beijing_time(self):
        """获取北京时间 (UTC+8)"""
        try:
            # 尝试使用pytz
            beijing_tz = pytz.timezone('Asia/Shanghai')
            beijing_time = datetime.now(beijing_tz)
            return beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        except:
            # 如果pytz未安装，手动加8小时
            utc_now = datetime.utcnow()
            beijing_time = utc_now + timedelta(hours=8)
            return beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        
    def md5_encrypt(self, text):
        """MD5加密"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def send_wecom_message(self, title, content, is_success=True):
        """发送企业微信机器人消息（Text格式）"""
        if not self.webhook_url:
            print("⚠️ 未设置企业微信Webhook，跳过通知")
            return False
        
        try:
            if is_success:
                status_emoji = "✅"
            else:
                status_emoji = "❌"
            
            # 更新时间为北京时间
            current_time = self.get_beijing_time()
            
            full_text = f"""【{status_emoji} {title}】
━━━━━━━━━━━━━━━━━━━━
📅 时间：{current_time}
📧 账号：{self.email}
📊 状态：{'成功 ✅' if is_success else '失败 ❌'}
{content}
━━━━━━━━━━━━━━━━━━━━
🤖 MindVideo 自动签到系统"""
            
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
                
                # 从 data.access_token 提取Token
                if result.get('code') == 0 and 'data' in result:
                    token = result['data'].get('access_token')
                    if token:
                        if not token.startswith('Bearer '):
                            self.token = f'Bearer {token}'
                        else:
                            self.token = token
                        
                        print(f"✅ 登录成功！")
                        return True
                
                error_msg = f"登录响应异常: {json.dumps(result, ensure_ascii=False)}"
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
    
    def get_credits_stats(self):
        """获取积分统计信息"""
        if not self.token:
            print("❌ 未获取到Token，无法查询积分")
            return False
        
        print("🔄 正在查询积分信息...")
        
        headers = self.base_headers.copy()
        headers["authorization"] = self.token
        
        try:
            response = requests.get(
                self.credits_url,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('code') == 0 and 'data' in result:
                    data = result['data']
                    
                    # 提取总积分信息
                    total_info = data.get('total', {})
                    self.checkin_result["total_credits"] = int(total_info.get('total_credits', 0))
                    self.checkin_result["used_credits"] = int(total_info.get('used_credits', 0))
                    self.checkin_result["remaining_credits"] = int(total_info.get('remaining_credits', 0))
                    
                    # 提取订阅类型
                    self.checkin_result["subscription_type"] = data.get('subscription_type', 'Free')
                    
                    print(f"✅ 积分查询成功")
                    print(f"📊 总积分: {self.checkin_result['total_credits']}")
                    print(f"📊 已用积分: {self.checkin_result['used_credits']}")
                    print(f"📊 剩余积分: {self.checkin_result['remaining_credits']}")
                    print(f"📊 订阅类型: {self.checkin_result['subscription_type']}")
                    
                    return True
                else:
                    print(f"⚠️ 积分查询响应异常: {json.dumps(result, ensure_ascii=False)}")
                    return False
            else:
                print(f"⚠️ 积分查询失败，状态码: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"⚠️ 积分查询异常: {e}")
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
                
                # 判断签到结果
                code = result.get('code')
                message = result.get('message', '')
                
                if code == 0:
                    # 签到成功
                    self.checkin_result["success"] = True
                    print(f"✅ 签到成功！")
                    
                    if 'data' in result and result['data']:
                        data = result['data']
                        self.checkin_result["points"] = data.get('points', 0)
                        self.checkin_result["continuity"] = data.get('continuity', 0)
                        
                        msg_parts = []
                        if 'points' in data:
                            msg_parts.append(f"💎 本次获得积分：+{data['points']}")
                        if 'continuity' in data:
                            msg_parts.append(f"📅 连续签到：{data['continuity']}天")
                        if 'message' in data:
                            msg_parts.append(f"📝 消息：{data['message']}")
                        
                        self.checkin_result["message"] = "\n".join(msg_parts) if msg_parts else "签到成功"
                    else:
                        self.checkin_result["message"] = message or "签到成功"
                    
                    return True
                    
                elif code == 70001:
                    # 今天已签到
                    self.checkin_result["success"] = True
                    print(f"ℹ️ {message}")
                    self.checkin_result["message"] = f"{message}（今日已签到）"
                    return True
                    
                else:
                    # 其他错误
                    error_msg = f"签到失败: {message} (code: {code})"
                    print(f"❌ {error_msg}")
                    self.checkin_result["message"] = error_msg
                    return False
                    
            else:
                error_msg = f"签到请求失败，状态码: {response.status_code}"
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
            
            # 构建积分信息
            credit_info = ""
            if self.checkin_result["total_credits"] > 0:
                credit_info = f"""
💳 积分详情：
  • 总积分：{self.checkin_result['total_credits']}
  • 已用积分：{self.checkin_result['used_credits']}
  • 剩余积分：{self.checkin_result['remaining_credits']}
  • 订阅类型：{self.checkin_result['subscription_type']}"""
            
            content = f"""
{self.checkin_result['message']}
{credit_info}"""
            
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
        current_time = self.get_beijing_time()
        print("=" * 20)
        print(f"🚀 MindVideo自动签到系统启动")
        print(f"⏰ 当前时间: {current_time} (北京时间)")
        print("=" * 20)
        
        # 1. 登录获取Token
        if not self.login():
            print("❌ 登录失败，签到流程终止")
            self.send_notification()
            return False
        
        print("-" * 20)
        
        # 2. 执行签到
        if not self.checkin():
            print("❌ 签到流程失败")
            self.send_notification()
            return False
        
        print("-" * 20)
        
        # 3. 查询积分信息
        self.get_credits_stats()
        
        print("-" * 20)
        
        # 4. 发送通知
        print("📤 发送通知...")
        self.send_notification()
        
        print("🎉 签到流程完成！")
        return True

if __name__ == "__main__":
    checker = MindVideoAutoCheckin()
    success = checker.run()
    exit(0 if success else 1)
