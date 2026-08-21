#!/usr/bin/env python3
"""
LayerCraft 自动签到脚本 - 最终修复版
通过模拟页面加载触发签到
"""

import requests
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Any

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
                else:
                    logger.error(f"❌ 企业微信推送失败: {result}")
            else:
                logger.error(f"❌ 企业微信推送请求失败: {response.status_code}")
            return False
                
        except Exception as e:
            logger.error(f"❌ 企业微信推送异常: {e}")
            return False


class LayerCraftCheckin:
    """LayerCraft 签到客户端 - 最终修复版"""
    
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
                if DEBUG:
                    logger.debug(f"登录失败响应: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 登录异常: {e}")
            if DEBUG:
                import traceback
                logger.debug(traceback.format_exc())
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
    
    def get_point_transactions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近的积分交易记录"""
        try:
            url = f"{self.BASE_URL}/account/point-transactions?limit={limit}"
            response = self.session.get(url, timeout=30)
            
            if DEBUG:
                logger.debug(f"积分记录响应状态码: {response.status_code}")
                logger.debug(f"积分记录响应内容前200字符: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                
                # 处理不同的数据格式
                if isinstance(data, list):
                    if DEBUG:
                        logger.debug(f"获取到 {len(data)} 条积分记录 (列表格式)")
                    return data
                elif isinstance(data, dict):
                    # 有些 API 返回 {data: [...]} 格式
                    if 'data' in data and isinstance(data['data'], list):
                        if DEBUG:
                            logger.debug(f"获取到 {len(data['data'])} 条积分记录 (data字段)")
                        return data['data']
                    elif 'items' in data and isinstance(data['items'], list):
                        if DEBUG:
                            logger.debug(f"获取到 {len(data['items'])} 条积分记录 (items字段)")
                        return data['items']
                    else:
                        # 可能是单个对象
                        if DEBUG:
                            logger.debug(f"返回的是字典格式，尝试作为列表处理")
                        return [data] if data else []
                else:
                    logger.warning(f"⚠️ 未知的数据格式: {type(data)}")
                    return []
            else:
                logger.warning(f"⚠️ 获取积分记录失败: {response.status_code}")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析失败: {e}")
            if DEBUG:
                logger.debug(f"原始响应: {response.text[:500]}")
            return []
        except Exception as e:
            logger.error(f"❌ 获取积分记录异常: {e}")
            if DEBUG:
                import traceback
                logger.debug(traceback.format_exc())
            return []
    
    def check_today_checkin(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检查今天是否已签到"""
        today = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d')
        
        if DEBUG:
            logger.debug(f"检查今日签到: {today}")
            logger.debug(f"交易记录数: {len(transactions)}")
        
        for tx in transactions:
            if not isinstance(tx, dict):
                if DEBUG:
                    logger.debug(f"跳过非字典项: {tx}")
                continue
                
            reason = tx.get('reason', '')
            if reason == 'daily_login_bonus':
                ref_id = tx.get('reference_id', '')
                if ref_id == today:
                    if DEBUG:
                        logger.debug(f"找到今日签到记录: {json.dumps(tx, ensure_ascii=False)}")
                    return {
                        'checked': True,
                        'points': tx.get('balance_after', 0),
                        'amount': tx.get('amount', 0),
                        'time': tx.get('created_at', '')
                    }
        
        if DEBUG:
            logger.debug("未找到今日签到记录")
        return {'checked': False}
    
    def daily_checkin(self) -> Dict[str, Any]:
        """执行每日签到"""
        try:
            # 1. 先获取当前积分记录，检查今日是否已签到
            logger.info("检查今日签到状态...")
            transactions = self.get_point_transactions(10)
            
            if not transactions:
                logger.warning("⚠️ 未获取到积分记录，可能是接口返回空数据")
                # 继续尝试签到
            
            check_result = self.check_today_checkin(transactions)
            if check_result.get('checked'):
                logger.info(f"ℹ️ 今日已签到，获得 +{check_result.get('amount', 0)} 积分")
                logger.info(f"💰 当前积分: {check_result.get('points', 0)}")
                return {
                    'success': True,
                    'already_checked': True,
                    'points': check_result.get('points', 0),
                    'message': f"今日已签到 (+{check_result.get('amount', 0)})"
                }
            
            # 2. 未签到，尝试多种方式触发签到
            logger.info("今日未签到，正在触发签到...")
            
            # 方式1: 加载应用页面
            self.load_app_page()
            time.sleep(2)
            
            # 方式2: 尝试调用签到 API
            logger.info("尝试调用签到 API...")
            checkin_apis = [
                ("POST", "/user/daily-checkin"),
                ("POST", "/daily-checkin"),
                ("GET", "/user/daily-checkin"),
                ("GET", "/daily-checkin"),
            ]
            
            for method, endpoint in checkin_apis:
                try:
                    url = f"{self.BASE_URL}{endpoint}"
                    if method == "POST":
                        response = self.session.post(url, json={}, timeout=10)
                    else:
                        response = self.session.get(url, timeout=10)
                    
                    if DEBUG:
                        logger.debug(f"{method} {endpoint} - 状态码: {response.status_code}")
                    
                    if response.status_code == 200:
                        logger.info(f"✅ API 签到请求成功: {method} {endpoint}")
                        break
                except Exception as e:
                    if DEBUG:
                        logger.debug(f"{method} {endpoint} 失败: {e}")
                    continue
            
            # 3. 重新获取积分记录，确认签到是否成功
            time.sleep(1)
            logger.info("验证签到结果...")
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
            else:
                # 如果还是没有签到记录，尝试使用登录返回的数据
                if self.user_data:
                    daily_login = self.user_data.get('daily_login', {})
                    points = daily_login.get('points_balance', 0)
                    if daily_login.get('granted', 0) == 1:
                        return {
                            'success': True,
                            'already_checked': True,
                            'points': points,
                            'message': "通过登录数据确认已签到"
                        }
                
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
        logger.debug("启动 LayerCraft 自动签到 (最终修复版)")
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
