#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS状态监控脚本 - 适配GitHub Actions
检查多个VPS账号状态并通过企业微信机器人发送通知
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import os
import sys
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import re

# ==================== 配置区域 ====================
# 从环境变量获取Webhook URL
WEBHOOK_URL = os.getenv('WECHAT_WEBHOOK_URL111', '')

# VPS账号配置 - 可以放在环境变量或secrets中
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
DELAY_BETWEEN_REQUESTS = 1  # 基础延迟秒数

# ==================== 数据类 ====================
@dataclass
class VPSResult:
    """VPS检查结果数据类"""
    account: str
    success: bool
    ip: str = "N/A"
    location: str = "N/A"
    transactions: int = 0
    expire_date: str = ""
    days_left: Optional[int] = None
    error: str = ""
    check_time: str = ""

# ==================== 日志函数 ====================
def log_message(message: str, level: str = "INFO"):
    """统一的日志函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    icons = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "SUCCESS": "✅",
        "DEBUG": "🐛"
    }
    
    icon = icons.get(level, "")
    log_line = f"[{timestamp}] {icon} {message}"
    
    # GitHub Actions 特殊格式
    if level == "ERROR":
        print(f"::error::{message}")
    elif level == "WARNING":
        print(f"::warning::{message}")
    elif level == "INFO":
        print(log_line)
    else:
        print(log_line)

# ==================== 企业微信通知 ====================
def send_wechat_message(content: str, is_markdown: bool = True) -> bool:
    """发送消息到企业微信机器人"""
    if not WEBHOOK_URL:
        log_message("未配置企业微信Webhook URL，跳过发送通知", "WARNING")
        return False
    
    headers = {"Content-Type": "application/json"}
    
    if is_markdown:
        data = {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
    else:
        data = {
            "msgtype": "text",
            "text": {"content": content}
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

# ==================== 格式化函数 ====================
def format_duration(seconds: float) -> str:
    """格式化时间间隔"""
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        return f"{seconds/60:.1f}分钟"
    else:
        return f"{seconds/3600:.1f}小时"

def format_vps_report(results: List[VPSResult]) -> str:
    """格式化VPS检查报告为Markdown格式"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 统计信息
    total = len(results)
    success_count = sum(1 for r in results if r.success)
    error_count = total - success_count
    success_rate = (success_count / total * 100) if total > 0 else 0
    
    # 构建报告
    report = [
        f"## 📊 VPS状态监控报告",
        f"",
        f"**检查时间:** {current_time}",
        f"**检查账号:** {total} 个",
        f"**成功检查:** {success_count} 个",
        f"**失败检查:** {error_count} 个",
        f"**成功率:** {success_rate:.1f}%",
        f""
    ]
    
    # 失败账号列表
    if error_count > 0:
        report.append("### ❌ 检查失败的账号")
        for result in results:
            if not result.success:
                report.append(f"- **{result.account}**: {result.error}")
        report.append("")
    
    # 成功账号详情
    if success_count > 0:
        report.append("### ✅ 正常运行的VPS")
        
        # 按剩余天数排序
        successful_results = [r for r in results if r.success]
        successful_results.sort(key=lambda x: x.days_left if x.days_left is not None else 9999)
        
        for result in successful_results:
            # 添加状态标识
            status_icon = "🟢"
            status_note = ""
            
            if result.days_left is not None:
                if result.days_left < 0:
                    status_icon = "🔴"
                    status_note = f"（已过期 {-result.days_left}天）"
                elif result.days_left <= 3:
                    status_icon = "🟠"
                    status_note = "（即将到期）"
                elif result.days_left <= 7:
                    status_icon = "🟡"
                    status_note = "（7天内到期）"
                elif result.days_left <= 30:
                    status_note = "（30天内到期）"
            
            report.append(f"#### {status_icon} {result.account}{status_note}")
            report.append(f"- **IP地址:** `{result.ip}`")
            report.append(f"- **服务器地区:** {result.location}")
            report.append(f"- **近1月交易量:** {result.transactions:,} 笔")
            
            if result.expire_date:
                days_info = f"剩余 {result.days_left} 天" if result.days_left is not None else ""
                report.append(f"- **到期时间:** {result.expire_date} {days_info}")
            
            report.append(f"- **检查时间:** {result.check_time}")
            report.append("")
    
    # GitHub Actions 信息
    if "GITHUB_ACTIONS" in os.environ:
        run_id = os.getenv("GITHUB_RUN_ID", "")
        run_number = os.getenv("GITHUB_RUN_NUMBER", "")
        if run_id:
            run_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY', '')}/actions/runs/{run_id}"
            report.append(f"**工作流运行:** [#{run_number}]({run_url})")
    
    report.append("---")
    report.append("*本报告由GitHub Actions自动生成*")
    
    return "\n".join(report)

def print_simple_table(results: List[VPSResult]):
    """打印简单的表格输出"""
    print("\n" + "="*90)
    print("VPS状态检查汇总".center(90))
    print("="*90)
    
    # 表头
    print(f"{'账号':<30} {'状态':<10} {'IP地址':<20} {'交易量':<8} {'剩余天数':<10} {'备注':<20}")
    print("-" * 90)
    
    for result in results:
        account = result.account
        status = "✅ 正常" if result.success else "❌ 异常"
        ip = result.ip if result.success else "-"
        transactions = str(result.transactions) if result.success else "-"
        
        if result.success and result.days_left is not None:
            if result.days_left < 0:
                days_left = f"过期{-result.days_left}"
                remark = "已过期"
            elif result.days_left <= 3:
                days_left = str(result.days_left)
                remark = "⚠️即将到期"
            elif result.days_left <= 7:
                days_left = str(result.days_left)
                remark = "7天内到期"
            elif result.days_left <= 30:
                days_left = str(result.days_left)
                remark = "30天内到期"
            else:
                days_left = str(result.days_left)
                remark = ""
        else:
            days_left = "-"
            remark = result.error if not result.success else ""
        
        print(f"{account:<30} {status:<10} {ip:<20} {transactions:<8} {days_left:<10} {remark:<20}")
    
    print("-" * 90)
    
    # 统计信息
    total = len(results)
    success_count = sum(1 for r in results if r.success)
    error_count = total - success_count
    
    print(f"📊 统计: 共检查 {total} 个账号 | ✅ 正常: {success_count} 个 | ❌ 异常: {error_count} 个")
    
    if error_count > 0:
        print(f"⚠️  注意: 有 {error_count} 个账号检查失败，可能是Cookie已失效")
    
    print("=" * 90)

# ==================== 核心检查函数 ====================
def parse_vps_page(html: str) -> Optional[Dict]:
    """解析VPS信息页面"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        info_div = soup.find('div', class_='information-right')
        
        if not info_div:
            return None
        
        info_items = {}
        for item in info_div.find_all('div', class_='information-list-item'):
            left = item.find('div', class_='information-list-item-left')
            right = item.find('div', class_='information-list-item-right')
            
            if left and right:
                key = left.get_text(strip=True).replace(' ', '')
                value = right.get_text(strip=True)
                info_items[key] = value
        
        return info_items
    except Exception as e:
        log_message(f"解析页面时出错: {str(e)}", "ERROR")
        return None

def check_single_vps(account_data: Dict, today: datetime.date) -> VPSResult:
    """检查单个VPS账号状态"""
    account = account_data['remark']
    cookie_value = account_data['DJkdikKMG']
    check_time = datetime.now().strftime("%H:%M:%S")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    cookies = {'DJkdikKMG': cookie_value}
    
    for attempt in range(RETRY_COUNT + 1):
        try:
            # 请求延迟
            if attempt > 0:
                delay = DELAY_BETWEEN_REQUESTS * (attempt + 1) + random.uniform(0, 1)
                log_message(f"{account}: 第{attempt+1}次重试，等待{delay:.1f}秒", "DEBUG")
                time.sleep(delay)
            
            # 发送请求
            response = requests.get(
                VPS_URL,
                cookies=cookies,
                headers=headers,
                allow_redirects=False,
                timeout=TIMEOUT
            )
            
            # 检查响应状态
            if response.status_code in [302, 403]:
                error_msg = f"访问被拒绝(HTTP {response.status_code})，Cookie可能已失效"
                if attempt == RETRY_COUNT:
                    return VPSResult(
                        account=account,
                        success=False,
                        error=error_msg,
                        check_time=check_time
                    )
                continue
            
            if response.status_code != 200:
                error_msg = f"HTTP错误 {response.status_code}"
                if attempt == RETRY_COUNT:
                    return VPSResult(
                        account=account,
                        success=False,
                        error=error_msg,
                        check_time=check_time
                    )
                continue
            
            # 解析页面
            info_items = parse_vps_page(response.text)
            if not info_items:
                error_msg = "未找到VPS信息"
                if attempt == RETRY_COUNT:
                    return VPSResult(
                        account=account,
                        success=False,
                        error=error_msg,
                        check_time=check_time
                    )
                continue
            
            # 提取信息
            ip = info_items.get('VPSIP', 'N/A')
            location = info_items.get('服务器地址', 'N/A')
            
            # 清理交易量数据
            transactions_str = info_items.get('近1月实盘交易数量', '0')
            transactions = int(re.sub(r'[^\d]', '', transactions_str) or '0')
            
            expire_date = info_items.get('到期日期', '')
            days_left = None
            
            if expire_date:
                try:
                    expire_date_obj = datetime.strptime(expire_date, "%Y-%m-%d").date()
                    days_left = (expire_date_obj - today).days
                except ValueError:
                    expire_date = "日期格式错误"
            
            return VPSResult(
                account=account,
                success=True,
                ip=ip,
                location=location,
                transactions=transactions,
                expire_date=expire_date,
                days_left=days_left,
                check_time=check_time
            )
            
        except requests.exceptions.Timeout:
            error_msg = f"请求超时(第{attempt+1}次尝试)"
            if attempt == RETRY_COUNT:
                return VPSResult(
                    account=account,
                    success=False,
                    error=error_msg,
                    check_time=check_time
                )
        except requests.exceptions.RequestException as e:
            error_msg = f"网络错误: {str(e)}"
            if attempt == RETRY_COUNT:
                return VPSResult(
                    account=account,
                    success=False,
                    error=error_msg,
                    check_time=check_time
                )
        except Exception as e:
            error_msg = f"未知错误: {str(e)}"
            if attempt == RETRY_COUNT:
                return VPSResult(
                    account=account,
                    success=False,
                    error=error_msg,
                    check_time=check_time
                )
    
    return VPSResult(
        account=account,
        success=False,
        error="所有重试都失败",
        check_time=check_time
    )

def check_all_vps() -> List[VPSResult]:
    """并发检查所有VPS账号"""
    today = datetime.now().date()
    results = []
    
    log_message(f"开始检查 {len(COOKIES_CONFIG)} 个VPS账号...", "INFO")
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # 提交任务
        future_to_account = {}
        for account_data in COOKIES_CONFIG:
            future = executor.submit(check_single_vps, account_data, today)
            future_to_account[future] = account_data['remark']
        
        # 处理结果
        for future in as_completed(future_to_account):
            account = future_to_account[future]
            try:
                result = future.result(timeout=TIMEOUT + 5)
                results.append(result)
                
                if result.success:
                    log_message(f"{account}: 检查成功 - IP: {result.ip}, 交易量: {result.transactions:,}, 剩余天数: {result.days_left or 'N/A'}", "SUCCESS")
                else:
                    log_message(f"{account}: 检查失败 - {result.error}", "ERROR")
                    
            except Exception as e:
                error_result = VPSResult(
                    account=account,
                    success=False,
                    error=f"处理异常: {str(e)}",
                    check_time=datetime.now().strftime("%H:%M:%S")
                )
                results.append(error_result)
                log_message(f"{account}: 处理异常 - {str(e)}", "ERROR")
    
    # 按原始顺序排序
    account_order = {data['remark']: i for i, data in enumerate(COOKIES_CONFIG)}
    results.sort(key=lambda x: account_order.get(x.account, 999))
    
    return results

# ==================== 主函数 ====================
def main() -> int:
    """主函数"""
    start_time = time.time()
    log_message("VPS监控脚本开始运行", "INFO")
    
    try:
        # 检查环境
        if "GITHUB_ACTIONS" in os.environ:
            log_message("运行环境: GitHub Actions", "INFO")
            log_message(f"工作流: {os.getenv('GITHUB_WORKFLOW', '未知')}", "INFO")
            log_message(f"触发事件: {os.getenv('GITHUB_EVENT_NAME', '未知')}", "INFO")
        
        # 执行检查
        results = check_all_vps()
        
        # 打印汇总
        print_simple_table(results)
        
        # 生成报告
        report = format_vps_report(results)
        
        # 发送通知
        if WEBHOOK_URL:
            log_message("正在发送企业微信通知...", "INFO")
            send_success = send_wechat_message(report)
            
            if not send_success:
                log_message("企业微信通知发送失败，但检查已完成", "WARNING")
        else:
            log_message("未配置企业微信Webhook，跳过通知发送", "WARNING")
            
            # 在本地运行或GitHub Actions中打印报告
            print("\n" + "="*90)
            print("Markdown报告预览:".center(90))
            print("="*90)
            print(report)
        
        # 统计信息
        elapsed_time = time.time() - start_time
        success_count = sum(1 for r in results if r.success)
        total_count = len(results)
        
        log_message(f"检查完成！耗时: {format_duration(elapsed_time)}", "INFO")
        log_message(f"检查结果: {success_count}/{total_count} 个账号成功", 
                   "SUCCESS" if success_count > 0 else "ERROR")
        
        # 返回退出码
        if success_count == 0:
            log_message("所有账号检查都失败，请检查配置", "ERROR")
            return 1
        else:
            return 0
            
    except KeyboardInterrupt:
        log_message("用户中断脚本执行", "WARNING")
        return 130
    except Exception as e:
        log_message(f"脚本执行出错: {str(e)}", "ERROR")
        return 1

# ==================== 入口点 ====================
if __name__ == "__main__":
    # 设置编码和缓冲
    if sys.platform != "win32":
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    sys.stderr.reconfigure(encoding='utf-8') if hasattr(sys.stderr, 'reconfigure') else None
    
    # 运行主函数
    exit_code = main()
    sys.exit(exit_code)
