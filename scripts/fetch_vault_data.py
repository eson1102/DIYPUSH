#!/usr/bin/env python3
"""
Plume Vault 净值数据抓取脚本
从 https://app.plume.org/vaults/nest-opal-vault 获取净值数据
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
                'price': None,
                'price_change': None,
                'price_change_percent': None,
                'apy': None,
                'timestamp': datetime.utcnow().isoformat(),
                'date': datetime.utcnow().strftime('%Y-%m-%d')
            }
            
            # 方法1: 通过CSS类查找价格
            price_elements = soup.find_all(class_=re.compile(r'css-1cz2y6m'))
            for el in price_elements:
                text = el.get_text(strip=True)
                price = self._extract_price(text)
                if price:
                    data['price'] = price
                    logger.info(f"找到价格: ${price}")
                    break
            
            # 方法2: 查找包含$符号的文本
            if not data['price']:
                all_text = soup.get_text()
                price_pattern = r'\$(\d+\.\d{4})'
                matches = re.findall(price_pattern, all_text)
                if matches:
                    data['price'] = float(matches[0])
                    logger.info(f"通过正则找到价格: ${data['price']}")
            
            # 提取价格变化和APY - 修复正则表达式
            change_elements = soup.find_all(class_=re.compile(r'css-lbly53'))
            for el in change_elements:
                text = el.get_text(strip=True)
                logger.info(f"变化文本: {text}")
                
                # 提取价格变化: +$0.056329
                change_match = re.search(r'([\+\-])\$([\d.]+)', text)
                if change_match:
                    sign = change_match.group(1)
                    value = float(change_match.group(2))
                    data['price_change'] = value if sign == '+' else -value
                
                # 提取涨跌幅: (5.46%) 或 (+5.46%)
                percent_match = re.search(r'\(([\d.]+)%', text)
                if percent_match:
                    data['price_change_percent'] = float(percent_match.group(1))
                
                # 提取APY: 11.38% APY
                apy_match = re.search(r'([\d.]+)%\s*APY', text)
                if apy_match:
                    data['apy'] = float(apy_match.group(1))
                
                # 如果上面的没匹配到，尝试其他格式
                if not data['apy']:
                    apy_match2 = re.search(r'([\d.]+)%APY', text)
                    if apy_match2:
                        data['apy'] = float(apy_match2.group(1))
                
                break
            
            # 如果数据不完整，尝试在script标签中查找
            if not data['price'] or not data['apy']:
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string:
                        text = script.string
                        # 查找价格
                        if not data['price']:
                            price_match = re.search(r'"price"\s*:\s*"?([\d.]+)"?', text)
                            if price_match:
                                data['price'] = float(price_match.group(1))
                        
                        # 查找APY
                        if not data['apy']:
                            apy_match = re.search(r'"apy"\s*:\s*"?([\d.]+)"?', text)
                            if apy_match:
                                data['apy'] = float(apy_match.group(1))
            
            # 检查是否获取到有效数据
            if data['price'] is None:
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
        
        # 匹配 $1.0882 格式
        match = re.search(r'\$(\d+\.\d+)', text)
        if match:
            return float(match.group(1))
        return None
    
    def save_today_data(self, data: Dict) -> bool:
        """保存今天的数据"""
        if not data:
            return False
        
        try:
            # 保存今天的数据
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
        
        # 检查今天是否已有记录
        today_date = data['date']
        existing_index = None
        for i, record in enumerate(history):
            if record.get('date') == today_date:
                existing_index = i
                break
        
        if existing_index is not None:
            # 更新今天的记录
            history[existing_index] = data
            logger.info(f"更新了 {today_date} 的记录")
        else:
            # 添加新记录
            history.append(data)
            logger.info(f"添加了 {today_date} 的新记录")
        
        # 按日期排序
        history.sort(key=lambda x: x.get('date', ''))
        
        self.save_history(history)
    
    def get_previous_day_data(self, current_date: str) -> Optional[Dict]:
        """获取前一天的数据"""
        history = self.load_history()
        
        # 计算前一天的日期
        current_dt = datetime.strptime(current_date, '%Y-%m-%d')
        previous_dt = current_dt - timedelta(days=1)
        previous_date = previous_dt.strftime('%Y-%m-%d')
        
        for record in history:
            if record.get('date') == previous_date:
                return record
        
        return None
    
    def generate_comparison(self, today_data: Dict) -> Optional[Dict]:
        """生成今天和昨天的对比"""
        if not today_data:
            return None
        
        yesterday_data = self.get_previous_day_data(today_data['date'])
        
        comparison = {
            'today': today_data,
            'yesterday': yesterday_data,
            'comparison': {
                'price_change_24h': None,
                'price_change_percent_24h': None,
                'apy_change': None,
                'apy_change_percent': None
            }
        }
        
        if yesterday_data:
            today_price = today_data.get('price', 0)
            yesterday_price = yesterday_data.get('price', 0)
            
            if yesterday_price > 0:
                price_diff = today_price - yesterday_price
                comparison['comparison']['price_change_24h'] = round(price_diff, 6)
                comparison['comparison']['price_change_percent_24h'] = round(
                    (price_diff / yesterday_price) * 100, 2
                )
            
            today_apy = today_data.get('apy', 0)
            yesterday_apy = yesterday_data.get('apy', 0)
            if yesterday_apy > 0:
                comparison['comparison']['apy_change'] = round(today_apy - yesterday_apy, 2)
                comparison['comparison']['apy_change_percent'] = round(
                    ((today_apy - yesterday_apy) / yesterday_apy) * 100, 2
                )
        
        # 保存对比报告
        summary = {
            'date': today_data['date'],
            'timestamp': datetime.utcnow().isoformat(),
            'comparison': comparison['comparison'],
            'today': {
                'price': today_data.get('price'),
                'apy': today_data.get('apy'),
                'price_change': today_data.get('price_change'),
                'price_change_percent': today_data.get('price_change_percent')
            },
            'yesterday': {
                'price': yesterday_data.get('price') if yesterday_data else None,
                'apy': yesterday_data.get('apy') if yesterday_data else None
            }
        }
        
        # 保存每日摘要
        try:
            # 加载现有摘要
            daily_summaries = []
            if os.path.exists(self.daily_summary_file):
                with open(self.daily_summary_file, 'r') as f:
                    daily_summaries = json.load(f)
            
            # 更新或添加
            existing_index = None
            for i, s in enumerate(daily_summaries):
                if s.get('date') == today_data['date']:
                    existing_index = i
                    break
            
            if existing_index is not None:
                daily_summaries[existing_index] = summary
            else:
                daily_summaries.append(summary)
            
            daily_summaries.sort(key=lambda x: x.get('date', ''))
            
            with open(self.daily_summary_file, 'w') as f:
                json.dump(daily_summaries, f, indent=2)
                
        except Exception as e:
            logger.error(f"保存每日摘要失败: {e}")
        
        return comparison
    
    def print_comparison(self, comparison: Dict):
        """打印对比结果"""
        if not comparison:
            print("\n❌ 无对比数据")
            return
        
        today = comparison.get('today', {})
        yesterday = comparison.get('yesterday')
        comp = comparison.get('comparison', {})
        
        print("\n" + "="*60)
        print(f"📊 Plume Vault 净值对比 - {today.get('date', 'Unknown')}")
        print("="*60)
        
        print(f"\n💰 当前净值: ${today.get('price', 0):.4f}")
        if yesterday:
            print(f"📉 昨日净值: ${yesterday.get('price', 0):.4f}")
            print(f"📈 24小时变化: ${comp.get('price_change_24h', 0):+.6f}")
            print(f"📊 24小时涨跌幅: {comp.get('price_change_percent_24h', 0):+.2f}%")
        else:
            print("📉 昨日数据: 暂无")
        
        print(f"\n🏦 当前 APY: {today.get('apy', 0):.2f}%")
        if yesterday and yesterday.get('apy'):
            print(f"📉 昨日 APY: {yesterday.get('apy', 0):.2f}%")
            print(f"📊 APY 变化: {comp.get('apy_change', 0):+.2f}%")
        
        print("\n" + "="*60)
        
        # 保存到markdown文件
        self.save_markdown_report(comparison)
    
    def save_markdown_report(self, comparison: Dict):
        """保存Markdown格式的报告"""
        today = comparison.get('today', {})
        yesterday = comparison.get('yesterday')
        comp = comparison.get('comparison', {})
        date = today.get('date', 'unknown')
        
        # 安全获取yesterday数据
        yesterday_price = yesterday.get('price', 0) if yesterday else 0
        yesterday_apy = yesterday.get('apy', 0) if yesterday else 0
        
        # 格式化变化值
        price_change = comp.get('price_change_24h', 0)
        price_change_percent = comp.get('price_change_percent_24h', 0)
        apy_change = comp.get('apy_change', 0)
        
        lines = [
            f"# Plume Vault 净值报告 - {date}",
            "",
            "## 📊 数据概览",
            "",
            "| 指标 | 今日 | 昨日 | 变化 |",
            "|------|------|------|------|",
            f"| 净值 | ${today.get('price', 0):.4f} | ${yesterday_price:.4f} | ${price_change:+.6f} ({price_change_percent:+.2f}%) |",
            f"| APY | {today.get('apy', 0):.2f}% | {yesterday_apy:.2f}% | {apy_change:+.2f}% |",
            "",
            f"📅 更新时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "---",
            "*数据来源: https://app.plume.org/vaults/nest-opal-vault*"
        ]
        
        markdown_file = os.path.join(self.data_dir, f"report_{date}.md")
        try:
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            logger.info(f"已保存Markdown报告: {markdown_file}")
        except Exception as e:
            logger.error(f"保存Markdown报告失败: {e}")

def main():
    """主函数"""
    tracker = PlumeVaultTracker()
    
    # 获取数据
    logger.info("开始获取Plume Vault数据...")
    data = tracker.fetch_data()
    
    if not data:
        logger.error("获取数据失败")
        exit(1)
    
    # 保存今天的数据
    tracker.save_today_data(data)
    
    # 更新历史记录
    tracker.update_history(data)
    
    # 生成对比
    comparison = tracker.generate_comparison(data)
    
    # 打印对比
    if comparison:
        tracker.print_comparison(comparison)
    else:
        logger.warning("无法生成对比数据")
    
    logger.info("数据获取完成！")

if __name__ == "__main__":
    main()
