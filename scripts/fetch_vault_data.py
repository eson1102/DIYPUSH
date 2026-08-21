#!/usr/bin/env python3
"""
Plume Vault 净值数据抓取脚本
从 https://app.plume.org/vaults/nest-opal-vault 获取净值数据
并发送企业微信通知
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import requests
from bs4 import BeautifulSoup
import re
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlumeVaultTracker:
    """Plume Vault 数据跟踪器"""
    
    def __init__(self):
        self.url = "https://app.plume.org/vaults/nest-opal-vault"
        self.data_dir = "data"
        self.today_file = os.path.join(self.data_dir, "today.json")
        self.history_file = os.path.join(self.data_dir, "history.json")
        self.daily_summary_file = os.path.join(self.data_dir, "daily_summary.json")
        
        # 企业微信机器人 Webhook（从环境变量读取）
        self.wecom_webhook = os.environ.get('WECOM_WEBHOOK', '')
        
        # 确保数据目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        
    def fetch_data(self) -> Optional[Dict]:
        """
        从页面获取数据
        返回: {
            'price': float,
            'price_change': float,
            'price_change_percent': float,
            'apy': float,
            'timestamp': str,
            'date': str
        }
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            logger.info(f"正在请求: {self.url}")
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {
                'price': 0.0,
                'price_change': 0.0,
                'price_change_percent': 0.0,
                'apy': 0.0,
                'timestamp': datetime.utcnow().isoformat(),
                'date': datetime.utcnow().strftime('%Y-%m-%d')
            }
            
            # 方法1: 通过CSS类查找价格
            price_element = soup.find('p', class_=re.compile(r'css-1cz2y6m'))
            if price_element:
                text = price_element.get_text(strip=True)
                price = self._extract_price(text)
                if price:
                    data['price'] = price
                    logger.info(f"找到价格: ${price}")
            
            # 方法2: 查找包含$符号的文本
            if data['price'] == 0.0:
                all_text = soup.get_text()
                price_pattern = r'\$(\d+\.\d{4})'
                matches = re.findall(price_pattern, all_text)
                if matches:
                    data['price'] = float(matches[0])
                    logger.info(f"通过正则找到价格: ${data['price']}")
            
            # 提取价格变化和APY
            change_element = soup.find('span', class_=re.compile(r'css-lbly53'))
            if change_element:
                text = change_element.get_text(strip=True)
                logger.info(f"变化文本: {text}")
                
                # 提取价格变化: +$0.056329
                change_match = re.search(r'([\+\-])\$([\d.]+)', text)
                if change_match:
                    sign = change_match.group(1)
                    value = float(change_match.group(2))
                    data['price_change'] = value if sign == '+' else -value
                    logger.info(f"提取价格变化: {data['price_change']}")
                
                # 提取涨跌幅
                percent_match = re.search(r'\(([\d.]+)%', text)
                if percent_match:
                    data['price_change_percent'] = float(percent_match.group(1))
                    logger.info(f"提取涨跌幅: {data['price_change_percent']}%")
                
                # 提取APY
                apy_match = re.search(r'([\d.]+)%\s*APY', text)
                if apy_match:
                    data['apy'] = float(apy_match.group(1))
                    logger.info(f"提取APY: {data['apy']}%")
                
                # 如果上面的没匹配到，尝试其他格式
                if data['apy'] == 0.0:
                    apy_match2 = re.search(r'([\d.]+)%APY', text)
                    if apy_match2:
                        data['apy'] = float(apy_match2.group(1))
                        logger.info(f"提取APY(备用): {data['apy']}%")
            
            # 方法3: 从Vault APY区域获取数据
            if data['apy'] == 0.0:
                apy_elements = soup.find_all('span', class_=re.compile(r'css-hukq4b'))
                for el in apy_elements:
                    text = el.get_text(strip=True)
                    if '%' in text:
                        apy_match = re.search(r'([\d.]+)%', text)
                        if apy_match:
                            data['apy'] = float(apy_match.group(1))
                            logger.info(f"从Vault APY找到APY: {data['apy']}%")
                            break
            
            # 检查是否获取到有效数据
            if data['price'] == 0.0:
                logger.error("未能获取到价格数据")
                return None
            
            logger.info(f"成功获取数据: {json.dumps(data, indent=2)}")
            return data
            
        except requests.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"数据解析失败: {e}")
            return None
    
    def _extract_price(self, text: str) -> Optional[float]:
        """从文本中提取价格"""
        if not text:
            return None
        
        match = re.search(r'\$(\d+\.\d+)', text)
        if match:
            return float(match.group(1))
        return None
    
    def save_today_data(self, data: Dict) -> bool:
        """保存今天的数据"""
        if not data:
            return False
        
        try:
            with open(self.today_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"已保存今天的数据到 {self.today_file}")
            return True
        except Exception as e:
            logger.error(f"保存今天数据失败: {e}")
            return False
    
    def load_history(self) -> List[Dict]:
        """加载历史数据"""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            return []
    
    def save_history(self, history: List[Dict]):
        """保存历史数据"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"保存历史数据失败: {e}")
    
    def update_history(self, data: Dict):
        """更新历史数据"""
        history = self.load_history()
        
        today_date = data['date']
        existing_index = None
        for i, record in enumerate(history):
            if record.get('date') == today_date:
                existing_index = i
                break
        
        if existing_index is not None:
            history[existing_index] = data
            logger.info(f"更新了 {today_date} 的记录")
        else:
            history.append(data)
            logger.info(f"添加了 {today_date} 的新记录")
        
        history.sort(key=lambda x: x.get('date', ''))
        self.save_history(history)
    
    def get_previous_day_data(self, current_date: str) -> Optional[Dict]:
        """获取前一天的数据"""
        history = self.load_history()
        
        current_dt = datetime.strptime(current_date, '%Y-%m-%d')
        previous_dt = current_dt - timedelta(days=1)
        previous_date = previous_dt.strftime('%Y-%m-%d')
        
        for record in history:
            if record.get('date') == previous_date:
                return record
        
        return None
    
    def send_wecom_notification(self, data: Dict):
        """发送企业微信通知"""
        if not self.wecom_webhook:
            logger.warning("未配置企业微信 Webhook，跳过通知")
            return
        
        try:
            # 获取前一天数据用于对比
            yesterday_data = self.get_previous_day_data(data['date'])
            
            # 计算24小时变化
            price_change_24h = 0.0
            price_change_percent_24h = 0.0
            apy_change = 0.0
            
            if yesterday_data:
                yesterday_price = yesterday_data.get('price', 0)
                if yesterday_price > 0:
                    price_change_24h = data['price'] - yesterday_price
                    price_change_percent_24h = (price_change_24h / yesterday_price) * 100
                
                yesterday_apy = yesterday_data.get('apy', 0)
                if yesterday_apy > 0:
                    apy_change = data['apy'] - yesterday_apy
            
            # 判断趋势
            if price_change_percent_24h > 0:
                trend = "上涨 📈"
            elif price_change_percent_24h == 0:
                trend = "持平 ➡️"
            else:
                trend = "下跌 📉"
            
            # 构建消息（使用 f-string 正确格式化）
            message = f"""【Plume Vault 净值更新】

更新日期: {data['date']}

当前净值: ${data['price']:.4f}
当前 APY: {data['apy']:.2f}%

价格变化: {trend}
  24小时变化: ${price_change_24h:+.6f}
  24小时涨跌幅: {price_change_percent_24h:+.2f}%

更新时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
查看详情: https://github.com/eson1102/DIYPUSH/actions"""
            
            # 发送到企业微信
            payload = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }
            
            response = requests.post(
                self.wecom_webhook,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ 企业微信通知发送成功")
            else:
                logger.error(f"企业微信通知发送失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"发送企业微信通知异常: {e}")

def main():
    """主函数"""
    tracker = PlumeVaultTracker()
    
    logger.info("开始获取Plume Vault数据...")
    data = tracker.fetch_data()
    
    if not data:
        logger.error("获取数据失败")
        exit(1)
    
    # 保存数据
    tracker.save_today_data(data)
    tracker.update_history(data)
    
    # 发送企业微信通知
    tracker.send_wecom_notification(data)
    
    logger.info("数据获取完成！")

if __name__ == "__main__":
    main()
