#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS状态监控脚本 - 最终修复版
修复: 解析结构混乱、字符串判断、Brotli编码、DEBUG日志
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import os
import sys
import re

# ==================== 配置区域 ====================
# 从环境变量获取Webhook URL
WEBHOOK_URL = os.getenv('WECHAT_WEBHOOK_URL111', '')

# VPS账号配置
COOKIES_CONFIG = [
    {
        'DJkdikKMG': '6OqTtw%2bzch7fL2BJvNgHLQ%3d%3d%7cFX3565537695%7chttps%3a%2f%2fimg.zy223.com%2fWikiEnterprise%2fsign%2fpersonph.png_wiki-template-global%7c5922813873%7cc8020fbb721af53c164569793d0c012f',
        'remark': 'vgfvxixz@idrrate.com'
    },
    {
        'DJkdikKMG': '3XZ26INfMzKMKGrK8hCLVQ%3d%3d%7csolar%40%e5%a5%89%e8%b4%a4%e7%94%9f%e6%b4%bb%7chttps%3a%2f%2fimg.zy223.com%2fthirdparty%2f2516564746%2f2516564746_62872.png_wiki200%7c0817793341%7cb86fd9f3c6b9bffd94e319ee18d59719',
        'remark': '156627504@qq.com'
    },
    {
        'DJkdikKMG': 'nZ%2fREPYCNY4jChEq2TyhJQ%3d%3d%7cttt2655%7chttps%3a%2f%2fimg.zy223.com%2fWikiEnterprise%2fsign%2fpersonph.png_wiki-template-global%7c4800439765%7cea02e589b80d630acdef38cad02375b0',
        'remark': 'pyjangubwq@iubridge.com'
    }
]

# VPS检查页面
VPS_URL = "https://vps.wikifx.com/zh-cn/jyzh"

# 配置参数
MAX_THREADS = 3
TIMEOUT = 15
RETRY_COUNT = 2

# ==================== 日志函数 ====================
def log_message(message: str, level: str = "INFO"):
    """统一的日志函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    icons = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "SUCCESS": "✅"
    }
    
    icon = icons.get(level, "")
    log_line = f"[{timestamp}] {icon} {message}"
    
    if level == "ERROR":
        print(f"::error::{message}")
    elif level == "WARNING":
        print(f"::warning::{message}")
    else:
        print(log_line)

# ==================== 企业微信通知 ====================
def send_wechat_text_message(content: str) -> bool:
    """发送文本消息到企业微信机器人"""
    if not WEBHOOK_URL:
        log_message("未配置企业微信Webhook URL，跳过发送通知", "WARNING")
        return False
    
    headers = {"Content-Type": "application/json"}
    
    data = {
        "msgtype": "text",
        "text": {
            "content": content
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=data, headers=headers, timeout=10)
        result = response.json()
        
        if result.get("errcode") == 0:
            log_message("企业微信通知发送成功", "SUCCESS")
            return True
        else:
            log_message(f"企业微信通知发送失败: {result.get('errmsg')}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"发送企业微信通知时出错: {str(e)}", "ERROR")
        return False

# ==================== 解析函数 - 最终修复版 ====================
def parse_vps_info(html: str) -> dict:
    """解析VPS信息 - 返回统一结构"""
    result = {
        "success": False,
        "error": "",
        "data": {
            "ip": "N/A",
            "location": "N/A",
            "expire_date": "N/A",
            "transactions": 0,
            "status": "unknown"
        }
    }
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 直接查找信息列表容器
        info_list = soup.find('div', class_='information-list')
        if not info_list:
            result["error"] = "未找到VPS信息列表"
            return result
        
        # 查找所有信息项
        info_items = info_list.find_all('div', class_='information-list-item')
        if not info_items:
            result["error"] = "未找到VPS信息项"
            return result
        
        # 遍历信息项并提取数据
        for item in info_items:
            left_div = item.find('div', class_='information-list-item-left')
            right_div = item.find('div', class_='information-list-item-right')
            
            if left_div and right_div:
                key = left_div.get_text(strip=True)
                value = right_div.get_text(strip=True, separator=' ').strip()
                
                # 根据键名提取对应信息
                if 'VPS IP' in key:
                    result["data"]["ip"] = value
                elif '服务器地址' in key:
                    # 处理地区信息
                    location_text = value
                    img = right_div.find('img')
                    if img and img.get('alt'):
                        location_text = img.get('alt')
                    result["data"]["location"] = location_text
                elif '到期日期' in key:
                    result["data"]["expire_date"] = value
                elif '近1月实盘交易数量' in key:
                    # 提取数字
                    num_match = re.search(r'\d+', value)
                    if num_match:
                        result["data"]["transactions"] = int(num_match.group())
        
        # 检查是否获取到必要信息
        if result["data"]["ip"] == "N/A" and result["data"]["expire_date"] == "N/A":
            result["error"] = "未解析到VPS关键信息"
            return result
        
        result["success"] = True
        return result
        
    except Exception as e:
        result["error"] = f"解析异常: {str(e)}"
        return result

# ==================== 检查单个VPS - 修复版 ====================
def check_single_vps(account_data: dict) -> dict:
    """检查单个VPS账号"""
    account = account_data['remark']
    cookie_value = account_data['DJkdikKMG']
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': VPS_URL
        # 注意：移除Accept-Encoding，让requests自动处理，避免Brotli问题
    }
    
    cookies = {'DJkdikKMG': cookie_value}
    
    for attempt in range(RETRY_COUNT + 1):
        try:
            # 添加随机延迟
            if attempt > 0:
                time.sleep(1 + random.random())
            
            # 发送请求
            response = requests.get(
                VPS_URL,
                cookies=cookies,
                headers=headers,
                timeout=TIMEOUT
            )
            
            # 检查HTTP状态码
            if response.status_code != 200:
                return {
                    "account": account,
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                }
            
            # 检查页面内容 - 使用BeautifulSoup而不是字符串判断
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 检查是否有VPS信息
            info_list = soup.find('div', class_='information-list')
            if not info_list:
                # 检查是否被重定向到登录页
                if 'login' in response.url.lower() or 'signin' in response.url.lower():
                    return {
                        "account": account,
                        "success": False,
                        "error": "Cookie失效"
                    }
                return {
                    "account": account,
                    "success": False,
                    "error": "未找到VPS信息"
                }
            
            # 解析VPS信息
            vps_info = parse_vps_info(html_content)
            
            if not vps_info["success"]:
                return {
                    "account": account,
                    "success": False,
                    "error": vps_info["error"]
                }
            
            data = vps_info["data"]
            
            # 计算剩余天数
            days_left = None
            expire_date = data.get("expire_date")
            if expire_date and expire_date != "N/A":
                try:
                    expire_date_obj = datetime.strptime(expire_date, "%Y-%m-%d")
                    today = datetime.now()
                    days_left = (expire_date_obj - today).days
                except:
                    pass
            
            return {
                "account": account,
                "success": True,
                "ip": data.get("ip", "N/A"),
                "location": data.get("location", "N/A"),
                "transactions": data.get("transactions", 0),
                "expire_date": expire_date,
                "days_left": days_left,
                "status": data.get("status", "unknown")
            }
            
        except requests.exceptions.Timeout:
            if attempt == RETRY_COUNT:
                return {
                    "account": account,
                    "success": False,
                    "error": "请求超时"
                }
        except requests.exceptions.RequestException as e:
            if attempt == RETRY_COUNT:
                return {
                    "account": account,
                    "success": False,
                    "error": f"网络错误: {str(e)}"
                }
        except Exception as e:
            if attempt == RETRY_COUNT:
                return {
                    "account": account,
                    "success": False,
                    "error": f"处理错误: {str(e)}"
                }
    
    return {
        "account": account,
        "success": False,
        "error": "检查失败"
    }

# ==================== 批量检查 ====================
def check_all_vps() -> list:
    """检查所有VPS账号"""
    results = []
    
    log_message(f"开始检查 {len(COOKIES_CONFIG)} 个VPS账号...", "INFO")
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # 提交所有任务
        future_to_account = {
            executor.submit(check_single_vps, account_data): 
            account_data['remark'] for account_data in COOKIES_CONFIG
        }
        
        # 收集结果
        for future in as_completed(future_to_account):
            account = future_to_account[future]
            try:
                result = future.result()
                results.append(result)
                
                if result["success"]:
                    log_message(f"{account}: 检查成功", "SUCCESS")
                else:
                    log_message(f"{account}: {result.get('error', '未知错误')}", "ERROR")
                    
            except Exception as e:
                results.append({
                    "account": account,
                    "success": False,
                    "error": f"处理异常: {str(e)}"
                })
                log_message(f"{account}: 处理异常 - {str(e)}", "ERROR")
    
    # 按原始顺序排序
    account_order = {data['remark']: i for i, data in enumerate(COOKIES_CONFIG)}
    results.sort(key=lambda x: account_order.get(x["account"], 999))
    
    return results

# ==================== 格式化报告 ====================
def format_report(results: list) -> str:
    """格式化检查报告"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 统计
    total = len(results)
    success = sum(1 for r in results if r["success"])
    failed = total - success
    
    lines = []
    lines.append(f"🚀 VPS状态检查报告 ({current_time})")
    lines.append("")
    lines.append(f"📊 状态: {success}正常 {failed}异常")
    lines.append("")
    
    # 异常账号
    if failed > 0:
        lines.append("❌ 异常账号:")
        for result in results:
            if not result["success"]:
                error_msg = result.get("error", "未知错误")
                # 简化错误信息
                if "Cookie失效" in error_msg:
                    error_msg = "Cookie失效"
                elif "未找到VPS信息" in error_msg:
                    error_msg = "无法获取VPS信息"
                elif "HTTP 302" in error_msg:
                    error_msg = "访问被拒绝"
                lines.append(f"  • {result['account']}: {error_msg}")
        lines.append("")
    
    # 正常账号
    if success > 0:
        lines.append("✅ 正常账号:")
        for result in results:
            if result["success"]:
                account_line = f"  • {result['account']}"
                
                # 添加到期警告
                days_left = result.get("days_left")
                if days_left is not None:
                    if days_left < 0:
                        account_line += f" 🔴 过期{-days_left}天"
                    elif days_left <= 3:
                        account_line += f" 🟠 {days_left}天到期"
                    elif days_left <= 7:
                        account_line += f" 🟡 {days_left}天到期"
                
                lines.append(account_line)
                lines.append(f"    IP: {result.get('ip', 'N/A')}")
                lines.append(f"    地区: {result.get('location', 'N/A')}")
                lines.append(f"    交易: {result.get('transactions', 0)}笔")
                
                expire_date = result.get("expire_date")
                if expire_date and expire_date != "N/A":
                    lines.append(f"    到期: {expire_date}")
                
                lines.append("")
    
    # 运行信息
    lines.append("📅 检查完成")
    
    if "GITHUB_ACTIONS" in os.environ:
        run_number = os.getenv("GITHUB_RUN_NUMBER", "")
        if run_number:
            lines.append(f"🔗 GitHub Actions Run #{run_number}")
    
    return "\n".join(lines)

def print_table(results: list):
    """打印表格"""
    print("\n" + "="*80)
    print("VPS状态检查汇总".center(80))
    print("="*80)
    
    print(f"{'账号':<25} {'状态':<8} {'IP':<20} {'交易':<6} {'剩余天数':<8} {'备注':<20}")
    print("-" * 80)
    
    for result in results:
        account = result["account"]
        status = "✅" if result["success"] else "❌"
        ip = result.get("ip", "-") if result["success"] else "-"
        transactions = str(result.get("transactions", 0)) if result["success"] else "-"
        
        days_left = result.get("days_left")
        if days_left is not None:
            days_display = str(days_left)
            if days_left < 0:
                days_display = f"过期{-days_left}"
        else:
            days_display = "-"
        
        remark = result.get("error", "") if not result["success"] else ""
        # 简化备注信息
        if len(remark) > 20:
            remark = remark[:17] + "..."
        
        print(f"{account:<25} {status:<8} {ip:<20} {transactions:<6} {days_display:<8} {remark:<20}")
    
    print("-" * 80)
    
    # 统计
    success = sum(1 for r in results if r["success"])
    total = len(results)
    
    if total > 0:
        success_rate = success/total*100
    else:
        success_rate = 0
    
    print(f"📊 统计: {success}/{total} 成功 | 成功率: {success_rate:.1f}%")
    print("=" * 80)

# ==================== 主函数 ====================
def main():
    """主函数"""
    start_time = time.time()
    
    try:
        # 检查VPS状态
        results = check_all_vps()
        
        # 打印表格
        print_table(results)
        
        # 生成报告
        report = format_report(results)
        
        # 发送通知
        if WEBHOOK_URL:
            log_message("发送企业微信通知...", "INFO")
            if send_wechat_text_message(report):
                log_message("通知发送成功", "SUCCESS")
            else:
                log_message("通知发送失败", "WARNING")
        else:
            log_message("未配置Webhook，跳过通知", "WARNING")
            print("\n企业微信报告内容:")
            print("="*60)
            print(report)
            print("="*60)
        
        # 执行时间
        elapsed = time.time() - start_time
        log_message(f"执行完成，耗时 {elapsed:.2f}秒", "INFO")
        
        # 返回状态码 - 只要有成功就返回0
        success_count = sum(1 for r in results if r["success"])
        if success_count == 0:
            log_message("所有账号检查都失败，请检查Cookie配置", "ERROR")
            return 1
        else:
            log_message(f"检查完成，{success_count}个账号成功", "SUCCESS")
            return 0
        
    except Exception as e:
        log_message(f"执行出错: {str(e)}", "ERROR")
        return 1

if __name__ == "__main__":
    # 设置编码
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    
    # 运行
    exit_code = main()
    sys.exit(exit_code)
