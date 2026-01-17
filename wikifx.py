import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import os
import sys
import json

# 从环境变量或secrets获取配置
WEBHOOK_URL = os.getenv('WECHAT_WEBHOOK_URL111', '')

# Cookies配置
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


def log_message(message, level="INFO"):
    """简单的日志函数"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level_icon = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "SUCCESS": "✅"
    }.get(level, "")
    
    log_line = f"[{timestamp}] {level_icon} {message}"
    
    # 根据级别输出到不同的流
    if level == "ERROR":
        print(log_line, file=sys.stderr)
    elif level == "WARNING":
        print(log_line, file=sys.stderr)
    else:
        print(log_line, file=sys.stdout)


def send_wechat_message(webhook_url, content, is_markdown=True):
    """发送消息到企业微信群机器人"""
    if not webhook_url:
        log_message("未配置Webhook URL，跳过发送", "WARNING")
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
        response = requests.post(webhook_url, json=data, headers=headers, timeout=10)
        result = response.json()
        
        if result.get("errcode") == 0:
            log_message("消息发送成功", "SUCCESS")
            return True
        else:
            log_message(f"消息发送失败: {result.get('errmsg')}", "ERROR")
            return False
            
    except Exception as e:
        log_message(f"发送消息时发生错误: {str(e)}", "ERROR")
        return False


def format_vps_info(vps_list):
    """格式化VPS信息"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 分类统计
    total = len(vps_list)
    normal = sum(1 for vps in vps_list if vps.get('success', False))
    error = total - normal
    
    # 创建Markdown格式内容
    content = f"## 📊 VPS状态检查报告 ({current_time})\n\n"
    content += f"**统计:** 共 {total} 个账号 | ✅ 正常: {normal} 个 | ❌ 异常: {error} 个\n\n"
    
    # 处理异常状态的VPS
    if error > 0:
        content += "### ❌ 异常账号\n"
        for vps in vps_list:
            if not vps.get('success', False):
                error_msg = vps.get('error', '未知错误')
                content += f"- **{vps['account']}**: {error_msg}\n"
        content += "\n"
    
    # 处理正常状态的VPS
    normal_vps = [vps for vps in vps_list if vps.get('success', False)]
    
    if normal_vps:
        # 按剩余天数排序
        normal_vps.sort(key=lambda x: x.get('days_left', 9999))
        
        content += "### ✅ 正常账号\n"
        
        for vps in normal_vps:
            # 添加到期警告
            warnings = []
            days_left = vps.get('days_left')
            
            if days_left is not None:
                if days_left <= 3:
                    warnings.append("⚠️ **即将到期**")
                elif days_left <= 7:
                    warnings.append("⚠️ 7天内到期")
                elif days_left <= 30:
                    warnings.append("⏳ 30天内到期")
            
            warning_text = " ".join(warnings)
            if warning_text:
                warning_text = f" {warning_text}"
            
            content += f"#### {vps['account']}{warning_text}\n"
            content += f"- **IP:** `{vps.get('ip', 'N/A')}`\n"
            content += f"- **地区:** {vps.get('location', 'N/A')}\n"
            content += f"- **近1月交易:** {vps.get('transactions', 0)} 笔\n"
            
            if vps.get('expire_date'):
                content += f"- **到期日:** {vps['expire_date']} "
                if days_left is not None:
                    if days_left < 0:
                        content += f"(已过期 {-days_left}天) ❌"
                    else:
                        content += f"(剩余 {days_left}天)"
                content += "\n"
            
            content += "\n"
    
    # 添加摘要信息
    content += "---\n"
    content += f"**检查时间:** {current_time}\n"
    content += "**触发方式:** GitHub Actions\n"
    content += f"**成功率:** {normal}/{total} ({normal/total*100:.1f}%)"
    
    return content


def parse_vps_info(soup):
    """解析VPS信息页面"""
    info_div = soup.find('div', class_='information-right')
    if not info_div:
        return None
    
    info_items = {}
    for item in info_div.find_all('div', class_='information-list-item'):
        left = item.find('div', class_='information-list-item-left')
        right = item.find('div', class_='information-list-item-right')
        if left and right:
            key = left.get_text(strip=True)
            value = right.get_text(strip=True)
            info_items[key] = value
    
    return info_items


def check_single_vps(account_data, today):
    """检查单个VPS账号的状态"""
    account_email = account_data['remark']
    cookies = {'DJkdikKMG': account_data['DJkdikKMG']}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    for attempt in range(RETRY_COUNT + 1):
        try:
            # 随机延迟，避免请求过于频繁
            if attempt > 0:
                delay = 2 ** attempt + random.uniform(0, 1)
                time.sleep(delay)
            
            response = requests.get(
                VPS_URL,
                cookies=cookies,
                headers=headers,
                allow_redirects=False,
                timeout=TIMEOUT
            )
            
            # 处理重定向或访问限制
            if response.status_code in (302, 403):
                return {
                    'account': account_email,
                    'success': False,
                    'error': f"访问受限({response.status_code})，可能Cookie失效"
                }
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                info_items = parse_vps_info(soup)
                
                if not info_items:
                    return {
                        'account': account_email,
                        'success': False,
                        'error': "未找到VPS信息"
                    }
                
                # 提取关键信息
                transactions = int(info_items.get('近1月实盘交易数量', '0'))
                location = info_items.get('服务器地址', 'N/A')
                expire_date_str = info_items.get('到期日期', '')
                vps_ip = info_items.get('VPS IP', 'N/A')
                
                # 计算剩余天数
                days_left = None
                if expire_date_str:
                    try:
                        expire_date = datetime.strptime(expire_date_str, "%Y-%m-%d").date()
                        days_left = (expire_date - today).days
                    except ValueError:
                        expire_date_str = '格式错误'
                
                return {
                    'account': account_email,
                    'success': True,
                    'ip': vps_ip,
                    'location': location,
                    'transactions': transactions,
                    'expire_date': expire_date_str,
                    'days_left': days_left
                }
            else:
                return {
                    'account': account_email,
                    'success': False,
                    'error': f"HTTP错误({response.status_code})"
                }
                
        except requests.exceptions.Timeout:
            error_msg = f"请求超时(尝试{attempt+1}/{RETRY_COUNT+1})"
            if attempt == RETRY_COUNT:
                return {
                    'account': account_email,
                    'success': False,
                    'error': error_msg
                }
        except requests.exceptions.RequestException as e:
            error_msg = f"网络错误: {str(e)}"
            if attempt == RETRY_COUNT:
                return {
                    'account': account_email,
                    'success': False,
                    'error': error_msg
                }
        except Exception as e:
            error_msg = f"解析错误: {str(e)}"
            if attempt == RETRY_COUNT:
                return {
                    'account': account_email,
                    'success': False,
                    'error': error_msg
                }
    
    return {
        'account': account_email,
        'success': False,
        'error': "检查失败"
    }


def check_all_vps():
    """检查所有VPS状态"""
    today = datetime.now().date()
    results = []
    
    log_message(f"开始检查 {len(COOKIES_CONFIG)} 个VPS账号...", "INFO")
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # 提交所有任务
        future_to_account = {
            executor.submit(check_single_vps, account_data, today): 
            account_data['remark'] for account_data in COOKIES_CONFIG
        }
        
        # 收集结果
        for future in as_completed(future_to_account):
            account_name = future_to_account[future]
            try:
                result = future.result()
                results.append(result)
                if result['success']:
                    days_left = result.get('days_left', '?')
                    transactions = result.get('transactions', 0)
                    log_message(f"{account_name}: IP={result.get('ip', 'N/A')}, 交易={transactions}, 剩余{days_left}天", "SUCCESS")
                else:
                    log_message(f"{account_name}: {result.get('error', '未知错误')}", "ERROR")
            except Exception as e:
                log_message(f"{account_name}: 处理异常 - {str(e)}", "ERROR")
                results.append({
                    'account': account_name,
                    'success': False,
                    'error': f"处理异常: {str(e)}"
                })
    
    # 按原始顺序排序结果
    account_order = {data['remark']: i for i, data in enumerate(COOKIES_CONFIG)}
    results.sort(key=lambda x: account_order.get(x['account'], 999))
    
    return results


def print_summary_table(vps_results):
    """打印漂亮的汇总表格"""
    from prettytable import PrettyTable
    
    table = PrettyTable()
    table.field_names = ["账号", "状态", "IP地址", "交易量", "剩余天数", "备注"]
    table.align["账号"] = "l"
    table.align["备注"] = "l"
    
    for result in vps_results:
        if result['success']:
            status = "✅ 正常"
            ip = result.get('ip', 'N/A')
            transactions = str(result.get('transactions', 0))
            days_left = str(result.get('days_left', '?'))
            
            # 添加到期警告
            remark = ""
            days = result.get('days_left')
            if days is not None:
                if days <= 3:
                    remark = "⚠️ 即将到期"
                elif days <= 7:
                    remark = "⚠️ 7天内到期"
                elif days <= 30:
                    remark = "⏳ 30天内到期"
        else:
            status = "❌ 异常"
            ip = "-"
            transactions = "-"
            days_left = "-"
            remark = result.get('error', '检查失败')
        
        table.add_row([
            result['account'],
            status,
            ip,
            transactions,
            days_left,
            remark
        ])
    
    print("\n" + "="*80)
    print("VPS状态检查汇总")
    print("="*80)
    print(table)
    
    # 统计信息
    total = len(vps_results)
    normal = sum(1 for vps in vps_results if vps.get('success', False))
    error = total - normal
    
    print(f"\n📊 统计: 共 {total} 个账号 | ✅ 正常: {normal} 个 | ❌ 异常: {error} 个")
    
    if error > 0:
        print(f"⚠️  发现 {error} 个异常账号，请检查Cookie是否失效")
    
    return error


def main():
    """主函数"""
    log_message("VPS监控脚本开始运行", "INFO")
    start_time = time.time()
    
    try:
        # 检查所有VPS
        vps_results = check_all_vps()
        
        # 打印汇总表格
        error_count = print_summary_table(vps_results)
        
        # 生成报告
        report_content = format_vps_info(vps_results)
        
        # 发送到企业微信
        if WEBHOOK_URL:
            log_message("准备发送通知到企业微信...", "INFO")
            send_success = send_wechat_message(WEBHOOK_URL, report_content, is_markdown=True)
            
            if send_success:
                log_message("通知发送成功", "SUCCESS")
            else:
                log_message("通知发送失败，但检查已完成", "WARNING")
        else:
            log_message("未配置Webhook URL，跳过发送通知", "WARNING")
            # 在本地运行时就打印报告内容
            print("\n" + "="*80)
            print("企业微信报告内容预览:")
            print("="*80)
            print(report_content)
        
        # 输出执行时间
        elapsed_time = time.time() - start_time
        log_message(f"脚本执行完成，耗时 {elapsed_time:.2f} 秒", "SUCCESS")
        
        # 只在完全失败时返回非零退出码
        # 对于GitHub Actions，即使有部分错误也返回0，避免任务被标记为失败
        success_count = sum(1 for result in vps_results if result.get('success', False))
        
        if success_count == 0:
            log_message("所有账号检查都失败，脚本执行失败", "ERROR")
            return 1  # 所有都失败才返回1
        else:
            log_message(f"脚本执行成功（{success_count}/{len(vps_results)} 成功）", "SUCCESS")
            return 0  # 只要有一个成功就返回0
        
    except KeyboardInterrupt:
        log_message("用户中断执行", "WARNING")
        return 130
    except Exception as e:
        log_message(f"脚本执行出错: {str(e)}", "ERROR")
        return 1


if __name__ == "__main__":
    # 设置编码
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # 尝试导入prettytable，如果没有安装则跳过
    try:
        from prettytable import PrettyTable
        HAS_PRETTYTABLE = True
    except ImportError:
        HAS_PRETTYTABLE = False
        log_message("未安装prettytable，将使用简单格式输出", "WARNING")
    
    # 运行主函数
    exit_code = main()
    sys.exit(exit_code)
