#!/usr/bin/env python3
"""
LayerCraft 自动签到脚本
每日登录即自动签到，推送结果到企业微信群
"""

import requests
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

# 设置调试模式（通过环境变量控制）
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# 配置日志
log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# 设置北京时间 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))


class WeComNotifier:
    """企业微信通知器"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_text(self, content: str) -> bool:
        """发送纯文本消息到企业微信群"""
        if not self.webhook_url:
            logger.warning("⚠️ 企业微信 Webhook URL 未配置，跳过推送")
            return False
        
        try:
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


class LayerCraftCheckin:
    """LayerCraft 签到客户端 - 登录即签到"""
    
    BASE_URL = "https://layercraft.com.cn/api"
    DAILY_POINTS = 4  # 每日签到积分
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': 'https://layercraft.com.cn',
            'Referer': 'https://layercraft.com.cn/app.html',
        })
        self.user_data = None
        self.token = None
        
    def login_and_checkin(self) -> Dict:
        """
        登录并自动签到
        登录成功后，系统会自动记录每日登录并发放积分
        """
        try:
            login_url = f"{self.BASE_URL}/auth/login"
            payload = {
                "email": self.email,
                "password": self.password
            }
            
            logger.info(f"正在登录: {self.email}")
            response = self.session.post(login_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                self.user_data = response.json()
                
                # 保存 token
                self.token = self.user_data.get('token')
                if self.token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.token}'
                    })
                
                if DEBUG:
                    logger.debug(f"登录返回数据: {json.dumps(self.user_data, indent=2, ensure_ascii=False)}")
                
                # 检查签到状态（登录后系统自动签到）
                daily_login = self.user_data.get('daily_login', {})
                granted = daily_login.get('granted', 0)
                points = daily_login.get('points_balance', 0)
                
                logger.info("✅ 登录成功")
                
                # 判断签到状态
                if granted == 1:
                    logger.info(f"✅ 今日签到成功！获得 +{self.DAILY_POINTS} 积分")
                    logger.info(f"💰 当前总积分: {points}")
                    return {
                        'success': True,
                        'already_checked': False,  # 刚签到的，不是之前签到的
                        'points': points,
                        'daily_points': self.DAILY_POINTS,
                        'message': '登录签到成功'
                    }
                else:
                    # 理论上登录后 granted 应该变为 1，如果没有变，说明可能有问题
                    logger.warning(f"⚠️ 登录后 granted={granted}，可能签到未触发")
                    return {
                        'success': False,
                        'already_checked': False,
                        'points': points,
                        'message': f'登录成功但签到未触发 (granted={granted})'
                    }
            else:
                logger.error(f"❌ 登录失败: {response.status_code}")
                if DEBUG:
                    logger.debug(f"登录失败响应: {response.text}")
                return {
                    'success': False,
                    'already_checked': False,
                    'points': 0,
                    'message': f'登录失败: {response.status_code}'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 登录请求异常: {e}")
            return {
                'success': False,
                'already_checked': False,
                'points': 0,
                'message': str(e)
            }


def main():
    """主函数"""
    # 从环境变量读取配置
    email = os.getenv('LAYERCRAFT_EMAIL')
    password = os.getenv('LAYERCRAFT_PASSWORD')
    webhook_url = os.getenv('WECOM_WEBHOOK')
    
    if DEBUG:
        logger.debug("=" * 60)
        logger.debug("启动 Debug 模式")
        logger.debug(f"环境变量: DEBUG={DEBUG}")
        logger.debug(f"LAYERCRAFT_EMAIL={'已设置' if email else '未设置'}")
        logger.debug(f"LAYERCRAFT_PASSWORD={'已设置' if password else '未设置'}")
        logger.debug(f"WECOM_WEBHOOK={'已设置' if webhook_url else '未设置'}")
        logger.debug("=" * 60)
    
    if not email or not password:
        error_msg = "请设置环境变量 LAYERCRAFT_EMAIL 和 LAYERCRAFT_PASSWORD"
        logger.error(f"❌ {error_msg}")
        
        if webhook_url:
            notifier = WeComNotifier(webhook_url)
            now = datetime.now(BEIJING_TZ)
            content = f"""==================================================
⚠️ LayerCraft 签到配置错误
==================================================
错误时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}
错误原因: {error_msg}

请检查 GitHub Secrets 配置:
- LAYERCRAFT_EMAIL
- LAYERCRAFT_PASSWORD
=================================================="""
            notifier.send_text(content)
        return
    
    # 初始化企业微信通知器
    notifier = WeComNotifier(webhook_url) if webhook_url else None
    
    # 创建签到客户端
    client = LayerCraftCheckin(email, password)
    
    # 登录并签到
    result = client.login_and_checkin()
    
    if DEBUG:
        logger.debug(f"签到结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 构建推送消息
    now = datetime.now(BEIJING_TZ)
    msg_lines = []
    msg_lines.append("=" * 50)
    msg_lines.append("🎮 LayerCraft 签到结果")
    msg_lines.append("=" * 50)
    msg_lines.append(f"签到时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}")
    msg_lines.append(f"用户账号: {email}")
    msg_lines.append("")
    
    if result.get('success', False):
        msg_lines.append("签到状态: ✅ 签到成功")
        msg_lines.append(f"获得积分: +{result.get('daily_points', 4)} 分")
        msg_lines.append(f"当前总积分: {result.get('points', 0)} 分")
    else:
        msg_lines.append("签到状态: ❌ 签到失败")
        msg_lines.append(f"失败原因: {result.get('message', '未知错误')}")
    
    msg_lines.append("")
    msg_lines.append("-" * 50)
    msg_lines.append(f"推送时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}")
    msg_lines.append("=" * 50)
    
    final_message = "\n".join(msg_lines)
    
    # 打印到控制台
    print("\n" + "=" * 60)
    print("签到结果")
    print("=" * 60)
    print(final_message)
    print("=" * 60 + "\n")
    
    logger.info("🎉 签到流程完成")
    
    # 推送到企业微信
    if notifier:
        notifier.send_text(final_message)


if __name__ == "__main__":
    main()
