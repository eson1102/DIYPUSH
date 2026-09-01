#!/usr/bin/env python3
"""
单独获取Bybit RWA产品ID的脚本
用法: python get_product_id.py [产品名称]
如果不指定产品名称，则列出所有产品
"""

import sys
from pybit.unified_trading import HTTP

# 初始化 HTTP 会话
session = HTTP(testnet=False)

def get_product_list(coin='USDC'):
    """
    获取RWA产品列表
    :param coin: 结算币种筛选
    :return: 产品列表
    """
    try:
        params = {"coin": coin}
        response = session.get_rwa_product(params)
        
        if response.get('retCode') == 0:
            products = response.get('result', {}).get('list', [])
            return products
        else:
            print(f"获取产品列表失败: {response.get('retMsg')}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def list_all_products(coin='USDC'):
    """列出所有产品"""
    products = get_product_list(coin)
    if not products:
        return
    
    print(f"\n{'='*100}")
    print(f"{'ID':<6} {'产品名称':<35} {'管理者':<20} {'币种':<8} {'NAV':<12} {'年化利率':<10}")
    print(f"{'='*100}")
    
    for p in products:
        product_id = p.get('productId')
        asset = p.get('assetSymbol', '')[:33]
        manager = p.get('manager', '')[:18]
        coin = p.get('coin', '')
        nav = p.get('nav', '')
        base_apr = float(p.get('baseApr', '0')) * 100
        bonus_apr = float(p.get('bonusApr', '0')) * 100 if p.get('bonusApr') else 0
        total_apr = base_apr + bonus_apr
        
        print(f"{product_id:<6} {asset:<35} {manager:<20} {coin:<8} {nav:<12} {total_apr:.2f}%")
    
    print(f"{'='*100}")
    print(f"总计: {len(products)} 个产品\n")

def find_product_by_name(product_name, coin='USDC'):
    """
    根据产品名称查找产品ID
    :param product_name: 产品名称（支持部分匹配）
    :param coin: 结算币种
    :return: 产品信息字典
    """
    products = get_product_list(coin)
    if not products:
        return None
    
    # 先尝试精确匹配
    for p in products:
        if p.get('assetSymbol', '') == product_name:
            return p
    
    # 再尝试模糊匹配（不区分大小写）
    matches = []
    for p in products:
        if product_name.lower() in p.get('assetSymbol', '').lower():
            matches.append(p)
    
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"\n找到多个匹配的产品:")
        for p in matches:
            print(f"  ID: {p.get('productId')}, 名称: {p.get('assetSymbol')}")
        print(f"\n请指定更精确的产品名称")
        return None
    
    print(f"未找到包含 '{product_name}' 的产品")
    return None

def print_product_info(product):
    """打印产品详细信息"""
    if not product:
        return
    
    print(f"\n{'='*60}")
    print(f"产品ID:     {product.get('productId')}")
    print(f"产品名称:   {product.get('assetSymbol')}")
    print(f"管理者:     {product.get('manager')}")
    print(f"结算币种:   {product.get('coin')}")
    print(f"最新NAV:    {product.get('nav')}")
    
    base_apr = float(product.get('baseApr', '0')) * 100
    bonus_apr = float(product.get('bonusApr', '0')) * 100 if product.get('bonusApr') else 0
    print(f"基础年化:   {base_apr:.2f}%")
    if bonus_apr > 0:
        print(f"奖励年化:   +{bonus_apr:.2f}%")
    print(f"总年化:     {base_apr + bonus_apr:.2f}%")
    
    print(f"产品类型:   {product.get('savingType', 'N/A')}")
    print(f"锁仓天数:   {product.get('duration', 0)}")
    print(f"最低认购:   {product.get('minStakeAmount')} {product.get('coin')}")
    print(f"详情链接:   {product.get('extLink', 'N/A')}")
    print(f"{'='*60}\n")

def main():
    # 解析命令行参数
    if len(sys.argv) > 1:
        # 如果有参数，按产品名称查找
        product_name = ' '.join(sys.argv[1:])
        print(f"正在查找产品: {product_name}")
        
        product = find_product_by_name(product_name)
        if product:
            print_product_info(product)
        else:
            # 未找到时列出所有产品供参考
            print("\n所有可用产品:")
            list_all_products()
    else:
        # 无参数时列出所有产品
        list_all_products()

if __name__ == "__main__":
    main()
