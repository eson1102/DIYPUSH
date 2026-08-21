#!/usr/bin/env python3
"""
LayerCraft 自动签到脚本
支持每日自动登录并领取签到积分，推送结果到企业微信群
包含详细的 Debug 日志
"""

import requests
import json
import logging
import os
import sys
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
        if DEBUG:
            logger.debug(f"初始化企业微信通知器: webhook_url={webhook_url[:30]}...")
    
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
            
            if DEBUG:
                logger.debug(f"发送企业微信消息: {content[:100]}...")
                logger.debug(f"请求 payload: {json.dumps(payload, ensure_ascii=False)[:200]}...")
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if DEBUG:
                logger.debug(f"企业微信响应状态码: {response.status_code}")
                logger.debug(f"企业微信响应内容: {response.text[:200]}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info("✅ 企业微信消息推送成功")
                    if DEBUG:
                        logger.debug(f"企业微信完整响应: {result}")
                    return True
                else:
                    logger.error(f"❌ 企业微信推送失败: {result}")
                    return False
            else:
                logger.error(f"❌ 企业微信推送请求失败: {response.status_code}")
                if DEBUG:
                    logger.debug(f"响应内容: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 企业微信推送异常: {e}")
            if DEBUG:
                logger.debug(f"异常详情: {e.__class__.__name__}: {str(e)}")
            return False


class LayerCraftCheckin:
    """LayerCraft 签到客户端"""
    
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
            'Content-Type': 'application/json',
            'Origin': 'https://layercraft.com.cn',
            'Referer': 'https://layercraft.com.cn/app.html',
        })
        self.user_data = None
        
        if DEBUG:
            logger.debug(f"初始化 LayerCraft 客户端")
            logger.debug(f"邮箱: {email[:3]}***{email[-10:] if len(email) > 10 else ''}")
            logger.debug(f"请求头: {json.dumps(dict(self.session.headers), indent=2)}")
        
    def login(self) -> bool:
        """用户登录"""
        try:
            login_url = f"{self.BASE_URL}/auth/login"
            payload = {
                "email": self.email,
                "password": self.password
            }
            
            if DEBUG:
                logger.debug(f"登录请求 URL: {login_url}")
                logger.debug(f"登录请求数据: email={self.email}, password={'*' * len(self.password)}")
                logger.debug(f"请求头: {json.dumps(dict(self.session.headers), indent=2)}")
            
            logger.info(f"正在登录: {self.email}")
            response = self.session.post(login_url, json=payload, timeout=30)
            
            if DEBUG:
                logger.debug(f"登录响应状态码: {response.status_code}")
                logger.debug(f"登录响应头: {dict(response.headers)}")
                logger.debug(f"登录响应内容: {response.text[:500]}")
            
            if response.status_code == 200:
                self.user_data = response.json()
                if DEBUG:
                    logger.debug(f"登录返回数据: {json.dumps(self.user_data, indent=2, ensure_ascii=False)}")
                    # 打印关键信息
                    membership = self.user_data.get('membership', {})
                    points = membership.get('points_balance', 0)
                    daily_login = self.user_data.get('daily_login', {})
                    granted = daily_login.get('granted', 0)
                    logger.debug(f"当前积分: {points}, 今日已签到: {granted == 1}")
                
                logger.info("✅ 登录成功")
                return True
            else:
                logger.error(f"❌ 登录失败: {response.status_code}")
                if DEBUG:
                    logger.debug(f"登录失败响应: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 登录请求异常: {e}")
            if DEBUG:
                logger.debug(f"异常详情: {e.__class__.__name__}: {str(e)}")
                if hasattr(e, 'response') and e.response:
                    logger.debug(f"异常响应: {e.response.text}")
            return False
    
    def get_user_info(self) -> Optional[Dict]:
        """获取用户信息 - 使用登录返回的数据"""
        if self.user_data:
            logger.info("✅ 使用登录返回的用户数据")
            if DEBUG:
                logger.debug(f"用户数据: {json.dumps(self.user_data, indent=2, ensure_ascii=False)[:500]}...")
            return self.user_data
        
        logger.warning("⚠️ 未找到用户数据")
        return None
    
    def daily_checkin(self) -> Dict:
        """执行每日签到"""
        try:
            # 获取用户信息（从登录数据中获取）
            user_info = self.get_user_info()
            
            if user_info:
                # 检查是否已签到
                daily_login = user_info.get('daily_login', {})
                membership = user_info.get('membership', {})
                current_points = membership.get('points_balance', 0)
                
                if DEBUG:
                    logger.debug(f"daily_login 数据: {json.dumps(daily_login, indent=2)}")
                    logger.debug(f"membership 数据: {json.dumps(membership, indent=2)}")
                    logger.debug(f"当前积分: {current_points}")
                
                # 判断是否已签到
                if daily_login.get('granted', 0) == 1:
                    logger.info("ℹ️ 今日已签到")
                    if DEBUG:
                        logger.debug("granted=1，今日已签到，无需重复签到")
                    return {
                        'success': True,
                        'already_checked': True,
                        'points': current_points,
                        'message': '今日已签到'
                    }
                
                if DEBUG:
                    logger.debug(f"granted={daily_login.get('granted', 0)}，今日未签到，执行签到")
                
                # 执行签到
                logger.info("正在执行签到...")
                checkin_url = f"{self.BASE_URL}/user/daily-checkin"
                
                if DEBUG:
                    logger.debug(f"签到请求 URL: {checkin_url}")
                    logger.debug(f"签到请求头: {json.dumps(dict(self.session.headers), indent=2)}")
                
                response = self.session.post(checkin_url, timeout=30)
                
                if DEBUG:
                    logger.debug(f"签到响应状态码: {response.status_code}")
                    logger.debug(f"签到响应内容: {response.text[:500]}")
                
                if response.status_code == 200:
                    result = response.json()
                    if DEBUG:
                        logger.debug(f"签到返回数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
                    
                    new_points = result.get('points_balance', current_points + self.DAILY_POINTS)
                    logger.info(f"✅ 签到成功！获得 +{self.DAILY_POINTS} 积分")
                    logger.info(f"💰 当前总积分: {new_points}")
                    
                    return {
                        'success': True,
                        'already_checked': False,
                        'points': new_points,
                        'daily_points': self.DAILY_POINTS,
                        'message': '签到成功',
                        'raw_response': result if DEBUG else None
                    }
                else:
                    logger.error(f"❌ 签到失败: {response.status_code}")
                    if DEBUG:
                        logger.debug(f"签到失败响应: {response.text}")
                    
                    # 尝试使用 GET 请求签到
                    logger.info("尝试使用 GET 请求签到...")
                    checkin_get_url = f"{self.BASE_URL}/user/checkin"
                    
                    if DEBUG:
                        logger.debug(f"GET 签到请求 URL: {checkin_get_url}")
                    
                    get_response = self.session.get(checkin_get_url, timeout=30)
                    
                    if DEBUG:
                        logger.debug(f"GET 签到响应状态码: {get_response.status_code}")
                        logger.debug(f"GET 签到响应内容: {get_response.text[:500]}")
                    
                    if get_response.status_code == 200:
                        logger.info("✅ GET 请求签到成功")
                        result = get_response.json()
                        if DEBUG:
                            logger.debug(f"GET 签到返回数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return {
                            'success': True,
                            'already_checked': False,
                            'points': current_points + self.DAILY_POINTS,
                            'daily_points': self.DAILY_POINTS,
                            'message': '签到成功 (GET)',
                            'raw_response': result if DEBUG else None
                        }
                    
                    return {
                        'success': False,
                        'already_checked': False,
                        'points': current_points,
                        'message': f'签到失败: {response.status_code}'
                    }
            else:
                # 没有用户数据
                logger.error("❌ 未获取到用户数据")
                if DEBUG:
                    logger.debug("user_data 为空，无法获取用户信息")
                return {
                    'success': False,
                    'already_checked': False,
                    'points': 0,
                    'message': '未获取到用户数据'
                }
                
        except Exception as e:
            logger.error(f"❌ 签到异常: {e}")
            if DEBUG:
                import traceback
                logger.debug(f"异常堆栈: {traceback.format_exc()}")
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
        
        # 尝试推送错误消息
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
    
    # 登录
    if not client.login():
        logger.error("❌ 登录失败，签到终止")
        
        # 推送失败通知
        if notifier:
            now = datetime.now(BEIJING_TZ)
            content = f"""==================================================
❌ LayerCraft 签到失败
==================================================
签到时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}
用户账号: {email}

失败原因: 登录失败，请检查账号密码

--------------------------------------------------
推送时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}
=================================================="""
            notifier.send_text(content)
        return
    
    # 执行签到
    result = client.daily_checkin()
    
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
    
    if DEBUG:
        msg_lines.append(f"[Debug] 结果数据: {json.dumps(result, ensure_ascii=False)}")
        msg_lines.append("")
    
    if result.get('success', False):
        if result.get('already_checked', False):
            msg_lines.append("签到状态: ✅ 今日已签到")
            msg_lines.append(f"当前积分: {result.get('points', 0)} 分")
        else:
            msg_lines.append("签到状态: ✅ 签到成功")
            msg_lines.append(f"获得积分: +{result.get('daily_points', 4)} 分")
            msg_lines.append(f"当前总积分: {result.get('points', 0)} 分")
    else:
        msg_lines.append("签到状态: ❌ 签到失败")
        msg_lines.append(f"失败原因: {result.get('message', '未知错误')}")
    
    msg_lines.append("")
    msg_lines.append("-" * 50)
    msg_lines.append(f"推送时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}")
    
    if DEBUG:
        msg_lines.append(f"Debug 模式: 已启用")
        msg_lines.append(f"Email: {email}")
        msg_lines.append(f"结果: {json.dumps(result, ensure_ascii=False)}")
    
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
        # 如果是 Debug 模式，发送更详细的消息
        if DEBUG:
            # Debug 模式发送完整信息
            debug_msg = final_message
            notifier.send_text(debug_msg)
        else:
            # 普通模式发送正常消息
            normal_msg = "\n".join(msg_lines[:-3] if DEBUG else msg_lines)  # 移除 debug 信息
            notifier.send_text(final_message)


if __name__ == "__main__":
    main()
