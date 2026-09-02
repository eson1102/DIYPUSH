import requests
import json

def get_rwa_products(coin=None):
    """
    获取Bybit RWA产品列表
    
    Args:
        coin: 结算币种筛选，如'USDC'，不填则返回所有
    
    Returns:
        dict: API响应结果
    """
    url = "https://api.bybit.com/v5/earn/rwa/product"
    
    # 构建请求参数
    params = {}
    if coin:
        params['coin'] = coin.upper()
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None

# 使用示例
if __name__ == "__main__":
    # 获取所有RWA产品
    result = get_rwa_products()
    if result and result['retCode'] == 0:
        print("所有产品列表:")
        for product in result['result']['list']:
            print(f"产品ID: {product['productId']}")
            print(f"资产: {product['assetSymbol']}")
            print(f"管理方: {product['manager']}")
            print(f"币种: {product['coin']}")
            print(f"类型: {product['savingType']}")
            print(f"基础年化: {float(product['baseApr']) * 100:.2f}%")
            if product['bonusApr']:
                print(f"奖励年化: {float(product['bonusApr']) * 100:.2f}%")
            print(f"NAV: {product['nav']}")
            print("-" * 50)
    
    # 获取USDC产品
    print("\nUSDC产品:")
    usdc_products = get_rwa_products('USDC')
    if usdc_products and usdc_products['retCode'] == 0:
        for product in usdc_products['result']['list']:
            print(json.dumps(product, indent=2))
