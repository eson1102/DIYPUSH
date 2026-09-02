import requests
import json
import time
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class BybitRWA:
    def __init__(self):
        self.base_url = "https://api.bybit.com"
        self.endpoint = "/v5/earn/rwa/product"
        
        # 创建带重试机制的session
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Referer': 'https://www.bybit.com/',
            'Origin': 'https://www.bybit.com'
        }
    
    def get_products(self, coin=None, timeout=10):
        """
        获取RWA产品列表
        
        Args:
            coin: 结算币种筛选，如'USDC'，不填则返回所有
            timeout: 请求超时时间（秒）
        
        Returns:
            dict: API响应结果，失败返回None
        """
        url = f"{self.base_url}{self.endpoint}"
        params = {'coin': coin.upper()} if coin else {}
        
        try:
            print(f"正在请求: {url}")
            if params:
                print(f"参数: {params}")
            
            response = self.session.get(
                url, 
                headers=self.headers, 
                params=params, 
                timeout=timeout
            )
            
            print(f"响应状态码: {response.status_code}")
            print(f"响应头: {dict(response.headers)}")
            
            response.raise_for_status()
            
            # 尝试解析JSON
            try:
                return response.json()
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print(f"响应内容: {response.text[:500]}...")
                return None
                
        except requests.exceptions.HTTPError as e:
            print(f"HTTP错误: {e}")
            if hasattr(e.response, 'text'):
                print(f"错误响应内容: {e.response.text}")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"连接错误: {e}")
            return None
        except requests.exceptions.Timeout as e:
            print(f"请求超时: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            return None
    
    def parse_products(self, response):
        """解析并格式化产品数据"""
        if not response:
            return []
            
        if response.get('retCode') != 0:
            print(f"API返回错误: {response.get('retMsg')}")
            print(f"完整响应: {json.dumps(response, indent=2)}")
            return []
        
        products = response.get('result', {}).get('list', [])
        
        if not products:
            print("没有找到产品")
            return []
        
        # 处理数据
        for product in products:
            try:
                # 转换利率为百分比
                product['baseAprPercent'] = float(product['baseApr']) * 100 if product['baseApr'] else 0
                product['bonusAprPercent'] = float(product['bonusApr']) * 100 if product['bonusApr'] else 0
                product['totalAprPercent'] = product['baseAprPercent'] + product['bonusAprPercent']
                
                # 转换金额
                product['minStakeAmountFloat'] = float(product['minStakeAmount']) if product['minStakeAmount'] else 0
                product['navFloat'] = float(product['nav']) if product['nav'] else 0
                
                # 添加产品类型描述
                saving_type = product.get('savingType', '')
                duration = product.get('duration', 0)
                if saving_type == 'Flexible':
                    product['savingTypeDesc'] = '活期'
                elif saving_type == 'Fixed':
                    product['savingTypeDesc'] = f'定期{duration}天'
                else:
                    product['savingTypeDesc'] = '未知类型'
                    
            except (ValueError, TypeError) as e:
                print(f"处理产品 {product.get('productId', 'unknown')} 时出错: {e}")
                continue
        
        return products
    
    def print_products(self, coin=None):
        """打印产品信息"""
        print(f"\n{'='*80}")
        print(f"Bybit RWA产品列表")
        print(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if coin:
            print(f"筛选币种: {coin}")
        print(f"{'='*80}\n")
        
        # 获取产品
        response = self.get_products(coin)
        products = self.parse_products(response)
        
        if not products:
            print("未获取到产品数据")
            print("\n调试信息：")
            print(f"完整响应: {json.dumps(response, indent=2) if response else 'None'}")
            return
        
        print(f"共找到 {len(products)} 个产品\n")
        
        for idx, product in enumerate(products, 1):
            print(f"【产品 {idx}】")
            print(f"  产品ID: {product.get('productId', 'N/A')}")
            print(f"  资产名称: {product.get('assetSymbol', 'N/A')}")
            print(f"  管理方: {product.get('manager', 'N/A')}")
            print(f"  结算币种: {product.get('coin', 'N/A')}")
            print(f"  产品类型: {product.get('savingTypeDesc', 'N/A')}")
            print(f"  最新NAV: {product.get('nav', 'N/A')}")
            print(f"  基础年化: {product.get('baseAprPercent', 0):.2f}%")
            if product.get('bonusApr'):
                print(f"  奖励年化: {product.get('bonusAprPercent', 0):.2f}%")
            print(f"  总年化: {product.get('totalAprPercent', 0):.2f}%")
            print(f"  最低认购: {product.get('minStakeAmount', 'N/A')} {product.get('coin', '')}")
            if product.get('maxStakeAmount'):
                print(f"  最高认购: {product.get('maxStakeAmount')} {product.get('coin', '')}")
            if product.get('userMaxAmount'):
                print(f"  用户最大持有: {product.get('userMaxAmount')} {product.get('coin', '')}")
            if product.get('userQuota'):
                print(f"  用户剩余额度: {product.get('userQuota')} {product.get('coin', '')}")
            print(f"  赎回费率: {float(product.get('redeemFeeRate', 0)) * 100:.2f}%")
            print(f"  认购费率: {float(product.get('subscriptionFee', 0)) * 100:.2f}%")
            if product.get('extLink'):
                print(f"  详情链接: {product.get('extLink')}")
            print("-" * 60)

def main():
    """主函数"""
    bybit = BybitRWA()
    
    # 测试1: 获取所有产品
    print("=== 测试1: 获取所有RWA产品 ===")
    bybit.print_products()
    
    # 等待1秒避免频率限制
    time.sleep(1)
    
    # 测试2: 获取USDC产品
    print("\n\n=== 测试2: 获取USDC产品 ===")
    bybit.print_products('USDC')
    
    # 测试3: 直接获取原始数据（用于调试）
    print("\n\n=== 测试3: 获取原始JSON数据 ===")
    response = bybit.get_products('USDC')
    if response:
        print(f"返回码: {response.get('retCode')}")
        print(f"返回消息: {response.get('retMsg')}")
        if response.get('result'):
            product_count = len(response['result'].get('list', []))
            print(f"产品数量: {product_count}")
            if product_count > 0:
                print("\n第一个产品原始数据:")
                print(json.dumps(response['result']['list'][0], indent=2))

if __name__ == "__main__":
    main()
