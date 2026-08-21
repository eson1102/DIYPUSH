#!/usr/bin/env python3
"""
LayerCraft 自动签到脚本
支持每日自动登录并领取签到积分，推送结果到企业微信群
"""

import requests
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置北京时间 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


class WeComNotifier:
    """企业微信通知器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_message(self, content: str, msg_type: str = "text") -> bool:
        """
        发送消息到企业微信群
        
        Args:
            content: 消息内容
            msg_type: 消息类型 (text/markdown)
        """
        if not self.webhook_url:
            logger.warning("⚠️ 企业微信 Webhook URL 未配置，跳过推送")
            return False
        
        try:
            if msg_type == "markdown":
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": content
                    }
                }
            else:
                payload = {
                    "msgtype": "text",
                    "text": {
                        "content": content
                    }
                }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info("✅ 企业微信消息推送成功")
                    return True
                else:
                    logger.error(f"❌ 企业微信推送失败: {result}")
                    return False
            else:
                logger.error(f"❌ 企业微信推送请求失败: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 企业微信推送异常: {e}")
            return False
    
    def send_checkin_result(self, success: bool, email: str, points: int, 
                            daily_points: int = 4, message: str = ""):
        """发送签到结果通知"""
        
        # 获取北京时间
        now = datetime.now(BEIJING_TZ)
        date_str = now.strftime('%Y年%m月%d日 %H:%M:%S')
        
        if success:
            # 成功消息 - 使用 Markdown 格式更美观
            content = f"""## 🎉 LayerCraft 签到成功

**签到时间：** {date_str}
**用户账号：** {email}
**获得积分：** +{daily_points} 分
**当前总积分：** {points} 分

---
> 签到状态：✅ 成功
> 签到方式：自动签到
> 推送时间：{date_str}"""
        else:
            # 失败消息
            error_msg = message or "未知错误，请检查日志"
            content = f"""## ❌ LayerCraft 签到失败

**签到时间：** {date_str}
**用户账号：** {email}
**失败原因：** {error_msg}

---
> 签到状态：❌ 失败
> 请检查账号配置或网络连接
> 推送时间：{date_str}"""
        
        # 发送 Markdown 消息
        return self.send_message(content, msg_type="markdown")


class LayerCraftCheckin:
    """LayerCraft 签到客户端"""
    
    BASE_URL = "https://layercraft.com.cn/api"
    DAILY_POINTS = 4  # 每日签到积分
    
    def __init__(self, email: str, password: str, webhook_url: Optional[str] = None):
        self.email = email
        self.password = password
        self.webhook_url = webhook_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': 'https://layercraft.com.cn',
            'Referer': 'https://layercraft.com.cn/app.html',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        
    def login(self) -> bool:
        """用户登录"""
        try:
            login_url = f"{self.BASE_URL}/auth/login"
            payload = {
                "email": self.email,
                "password": self.password
            }
            
            logger.info(f"正在登录: {self.email}")
            response = self.session.post(login_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # 提取并保存 token（如果有）
                if 'token' in data:
                    self.session.headers.update({
                        'Authorization': f'Bearer {data["token"]}'
                    })
                logger.info("✅ 登录成功")
                return True
            else:
                logger.error(f"❌ 登录失败: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 登录请求异常: {e}")
            return False
    
    def daily_checkin(self) -> Optional[Dict]:
        """执行每日签到"""
        try:
            # 获取用户信息
            user_info_url = f"{self.BASE_URL}/user/profile"
            response = self.session.get(user_info_url, timeout=30)
            
            if response.status_code == 200:
                user_data = response.json()
                daily_login = user_data.get('daily_login', {})
                membership = user_data.get('membership', {})
                current_points = membership.get('points_balance', 0)
                
                # 检查是否已签到
                if daily_login.get('granted', 0) == 1:
                    logger.info("ℹ️ 今日已签到，无需重复签到")
                    return {
                        'success': True,
                        'already_checked': True,
                        'points': current_points,
                        'message': '今日已签到'
                    }
                
                # 执行签到（通过访问签到接口）
                checkin_url = f"{self.BASE_URL}/user/daily-checkin"
                checkin_response = self.session.post(checkin_url, timeout=30)
                
                if checkin_response.status_code == 200:
                    result = checkin_response.json()
                    new_points = result.get('points_balance', current_points + self.DAILY_POINTS)
                    logger.info(f"✅ 签到成功！当前积分: {new_points}")
                    
                    # 记录签到日志
                    self._log_checkin_result(True, new_points)
                    
                    return {
                        'success': True,
                        'already_checked': False,
                        'points': new_points,
                        'daily_points': self.DAILY_POINTS,
                        'message': '签到成功'
                    }
                else:
                    error_msg = f"签到接口返回 {checkin_response.status_code}"
                    logger.error(f"❌ 签到失败: {error_msg}")
                    self._log_checkin_result(False, current_points)
                    return {
                        'success': False,
                        'already_checked': False,
                        'points': current_points,
                        'message': error_msg
                    }
            else:
                error_msg = f"获取用户信息失败: {response.status_code}"
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'already_checked': False,
                    'points': 0,
                    'message': error_msg
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"签到请求异常: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'already_checked': False,
                'points': 0,
                'message': error_msg
            }
    
    def get_user_info(self) -> Optional[Dict]:
        """获取用户信息"""
        try:
            url = f"{self.BASE_URL}/user/profile"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取用户信息失败: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            return None
    
    def _log_checkin_result(self, success: bool, points: int):
        """记录签到结果到文件"""
        log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'checkin.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # 使用北京时间
        now = datetime.now(BEIJING_TZ)
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        status = '✅ 成功' if success else '❌ 失败'
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f'{timestamp} - {status} - 积分: {points} - 用户: {self.email}\n')


def main():
    """主函数"""
    # 从环境变量读取配置
    email = os.getenv('LAYERCRAFT_EMAIL')
    password = os.getenv('LAYERCRAFT_PASSWORD')
    webhook_url = os.getenv('WECOM_WEBHOOK')
    
    if not email or not password:
        error_msg = "请设置环境变量 LAYERCRAFT_EMAIL 和 LAYERCRAFT_PASSWORD"
        logger.error(f"❌ {error_msg}")
        # 尝试推送错误消息
        if webhook_url:
            notifier = WeComNotifier(webhook_url)
            now = datetime.now(BEIJING_TZ)
            content = f"""## ⚠️ LayerCraft 签到配置错误

**错误时间：** {now.strftime('%Y年%m月%d日 %H:%M:%S')}
**错误原因：** {error_msg}

---
> 请检查 GitHub Secrets 配置
> 确保已设置 LAYERCRAFT_EMAIL 和 LAYERCRAFT_PASSWORD"""
            notifier.send_message(content, msg_type="markdown")
        return
    
    # 创建签到客户端
    client = LayerCraftCheckin(email, password, webhook_url)
    notifier = WeComNotifier(webhook_url) if webhook_url else None
    
    # 登录
    if not client.login():
        error_msg = "登录失败，签到终止"
        logger.error(f"❌ {error_msg}")
        
        # 推送失败通知
        if notifier:
            now = datetime.now(BEIJING_TZ)
            content = f"""## ❌ LayerCraft 签到失败

**签到时间：** {now.strftime('%Y年%m月%d日 %H:%M:%S')}
**用户账号：** {email}
**失败原因：** {error_msg}

---
> 请检查账号密码是否正确
> 推送时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}"""
            notifier.send_message(content, msg_type="markdown")
        return
    
    # 执行签到
    result = client.daily_checkin()
    
    if result:
        logger.info("🎉 签到流程完成")
        
        # 获取最新用户信息（用于确认积分）
        user_info = client.get_user_info()
        if user_info:
            points = user_info.get('membership', {}).get('points_balance', 0)
            logger.info(f"💰 当前总积分: {points}")
        else:
            points = result.get('points', 0)
        
        # 推送签到结果
        if notifier:
            notifier.send_checkin_result(
                success=result.get('success', False),
                email=email,
                points=points,
                daily_points=client.DAILY_POINTS,
                message=result.get('message', '')
            )
    else:
        error_msg = "签到流程异常"
        logger.error(f"❌ {error_msg}")
        
        # 推送异常通知
        if notifier:
            now = datetime.now(BEIJING_TZ)
            content = f"""## ⚠️ LayerCraft 签到异常

**签到时间：** {now.strftime('%Y年%m月%d日 %H:%M:%S')}
**用户账号：** {email}
**异常信息：** {error_msg}

---
> 请检查系统日志了解详情
> 推送时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}"""
            notifier.send_message(content, msg_type="markdown")


if __name__ == "__main__":
    main()
