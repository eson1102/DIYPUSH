#!/usr/bin/env python3
"""
LayerCraft 自动签到脚本 - 最终版
通过模拟页面加载触发签到
"""

import requests
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

# 设置调试模式
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
        if not self.webhook_url:
            return False
        
        try:
            payload = {
                "msgtype": "text",
                "text": {"content": content}
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
            return False
                
        except Exception as e:
            logger.error(f"❌ 企业微信推送异常: {e}")
            return False


class LayerCraftCheckin:
    """LayerCraft 签到客户端 - 最终版"""
    
    BASE_URL = "https://layercraft.com.cn/api"
    APP_URL = "https://layercraft.com.cn/app.html"
    DAILY_POINTS = 4
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': 'https://layercraft.com.cn',
            'Referer': 'https://layercraft.com.cn/app.html',
        })
        self.user_data = None
        self.token = None
        
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
                self.user_data = response.json()
                self.token = self.user_data.get('token')
                if self.token:
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.token}'
                    })
                
                if DEBUG:
                    logger.debug(f"登录成功，Token: {self.token[:20]}...")
                    logger.debug(f"登录返回: {json.dumps(self.user_data, indent=2, ensure_ascii=False)}")
                
                logger.info("✅ 登录成功")
                return True
            else:
                logger.error(f"❌ 登录失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 登录异常: {e}")
            return False
    
    def load_app_page(self) -> bool:
        """加载应用页面 - 触发签到"""
        try:
            logger.info("正在加载应用页面...")
            
            # 访问 app.html 页面，这会触发前端加载和签到
            response = self.session.get(self.APP_URL, timeout=30)
            
            if DEBUG:
                logger.debug(f"页面加载状态码: {response.status_code}")
                logger.debug(f"页面内容长度: {len(response.text)}")
            
            if response.status_code == 200:
                logger.info("✅ 应用页面加载成功")
                return True
            else:
                logger.warning(f"⚠️ 应用页面加载失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 加载页面异常: {e}")
            return False
    
    def get_point_transactions(self, limit: int = 5) -> list:
        """获取最近的积分交易记录"""
        try:
            url = f"{self.BASE_URL}/account/point-transactions?limit={limit}"
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if DEBUG:
                    logger.debug(f"获取到 {len(data)} 条积分记录")
                return data
            return []
        except Exception as e:
            logger.error(f"❌ 获取积分记录异常: {e}")
            return []
    
    def check_today_checkin(self, transactions: list) -> Dict:
        """检查今天是否已签到"""
        today = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        
        for tx in transactions:
            if tx.get('reason') == 'daily_login_bonus':
                ref_id = tx.get('reference_id', '')
                if ref_id == today:
                    return {
                        'checked': True,
                        'points': tx.get('balance_after', 0),
                        'amount': tx.get('amount', 0),
                        'time': tx.get('created_at', '')
                    }
        
        return {'checked': False}
    
    def daily_checkin(self) -> Dict:
        """执行每日签到"""
        try:
            # 1. 先获取当前积分记录，检查今日是否已签到
            logger.info("检查今日签到状态...")
            transactions = self.get_point_transactions(5)
            
            check_result = self.check_today_checkin(transactions)
            if check_result.get('checked'):
                logger.info(f"ℹ️ 今日已签到，获得 {check_result.get('amount', 0)} 积分")
                logger.info(f"💰 当前积分: {check_result.get('points', 0)}")
                return {
                    'success': True,
                    'already_checked': True,
                    'points': check_result.get('points', 0),
                    'message': f"今日已签到 (+{check_result.get('amount', 0)})"
                }
            
            # 2. 未签到，加载应用页面触发签到
            logger.info("今日未签到，正在触发签到...")
            
            # 访问应用页面
            self.load_app_page()
            
            # 等待一下，让前端完成签到请求
            import time
            time.sleep(2)
            
            # 3. 重新获取积分记录，确认签到是否成功
            logger.info("验证签到结果...")
            transactions = self.get_point_transactions(5)
            check_result = self.check_today_checkin(transactions)
            
            if check_result.get('checked'):
                logger.info(f"✅ 签到成功！获得 +{check_result.get('amount', 0)} 积分")
                logger.info(f"💰 当前积分: {check_result.get('points', 0)}")
                return {
                    'success': True,
                    'already_checked': False,
                    'points': check_result.get('points', 0),
                    'daily_points': check_result.get('amount', self.DAILY_POINTS),
                    'message': f"签到成功 (+{check_result.get('amount', self.DAILY_POINTS)})"
                }
            else:
                # 4. 尝试获取更多记录，可能签到记录在更后面
                transactions = self.get_point_transactions(10)
                check_result = self.check_today_checkin(transactions)
                
                if check_result.get('checked'):
                    logger.info(f"✅ 签到成功！获得 +{check_result.get('amount', 0)} 积分")
                    logger.info(f"💰 当前积分: {check_result.get('points', 0)}")
                    return {
                        'success': True,
                        'already_checked': False,
                        'points': check_result.get('points', 0),
                        'daily_points': check_result.get('amount', self.DAILY_POINTS),
                        'message': f"签到成功 (+{check_result.get('amount', self.DAILY_POINTS)})"
                    }
                
                # 5. 尝试通过前端 API 触发签到
                logger.info("尝试通过 API 触发签到...")
                checkin_url = f"{self.BASE_URL}/user/daily-checkin"
                try:
                    response = self.session.post(checkin_url, json={}, timeout=30)
                    if response.status_code == 200:
                        logger.info("✅ API 签到请求成功")
                        # 重新获取记录
                        transactions = self.get_point_transactions(5)
                        check_result = self.check_today_checkin(transactions)
                        if check_result.get('checked'):
                            return {
                                'success': True,
                                'already_checked': False,
                                'points': check_result.get('points', 0),
                                'daily_points': check_result.get('amount', self.DAILY_POINTS),
                                'message': f"API 签到成功 (+{check_result.get('amount', self.DAILY_POINTS)})"
                            }
                except Exception as e:
                    logger.debug(f"API 签到尝试失败: {e}")
                
                return {
                    'success': False,
                    'already_checked': False,
                    'points': 0,
                    'message': '签到触发失败，请检查网络或接口'
                }
                
        except Exception as e:
            logger.error(f"❌ 签到异常: {e}")
            if DEBUG:
                import traceback
                logger.debug(traceback.format_exc())
            return {
                'success': False,
                'already_checked': False,
                'points': 0,
                'message': str(e)
            }


def main():
    """主函数"""
    email = os.getenv('LAYERCRAFT_EMAIL')
    password = os.getenv('LAYERCRAFT_PASSWORD')
    webhook_url = os.getenv('WECOM_WEBHOOK')
    
    if DEBUG:
        logger.debug("=" * 60)
        logger.debug("启动 LayerCraft 自动签到 (最终版)")
        logger.debug(f"LAYERCRAFT_EMAIL={'已设置' if email else '未设置'}")
        logger.debug(f"LAYERCRAFT_PASSWORD={'已设置' if password else '未设置'}")
        logger.debug("=" * 60)
    
    if not email or not password:
        error_msg = "请设置环境变量 LAYERCRAFT_EMAIL 和 LAYERCRAFT_PASSWORD"
        logger.error(f"❌ {error_msg}")
        return
    
    notifier = WeComNotifier(webhook_url) if webhook_url else None
    client = LayerCraftCheckin(email, password)
    
    if not client.login():
        logger.error("❌ 登录失败")
        if notifier:
            now = datetime.now(BEIJING_TZ)
            content = f"""==================================================
❌ LayerCraft 签到失败
==================================================
时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}
账号: {email}
原因: 登录失败
=================================================="""
            notifier.send_text(content)
        return
    
    result = client.daily_checkin()
    
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
    msg_lines.append("=" * 50)
    
    final_message = "\n".join(msg_lines)
    print(final_message)
    
    if notifier:
        notifier.send_text(final_message)


if __name__ == "__main__":
    main()
