#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VPS 状态监控脚本（WikiFX）
企业微信文本通知版
消息模板严格按指定格式输出
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
from dataclasses import dataclass
from typing import List, Dict

# ==================== 基本配置 ====================

VPS_URL = "https://vps.wikifx.com/zh-cn/jyzh"
TIMEOUT = 15
MAX_THREADS = 3

WEBHOOK_URL = os.getenv("WECHAT_WEBHOOK_URL111", "")

# ==================== Cookies（按你要求写死在脚本里） ====================

COOKIES_CONFIG = [
    {
        'DJkdikKMG': '6OqTtw%2bzch7fL2BJvNgHLQ%3d%3d%7cFX3565537695%7chttps%3a%2f%2fimg.zy223.com%2fWikiEnterprise%2fsign%2fpersonph.png_wiki-template-global%7c5922814844%7c7cebf35dbf59a8100b6b52a74293a4e5',
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

# ==================== 数据结构 ====================

@dataclass
class VPSResult:
    account: str
    success: bool
    error: str = ""

# ==================== 核心检查 ====================

def check_single_vps(account_data: Dict) -> VPSResult:
    account = account_data["remark"]
    cookie = account_data["DJkdikKMG"]

    headers = {
        "User-Agent": "Mozilla/5.0 Chrome/120",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }

    try:
        r = requests.get(
            VPS_URL,
            headers=headers,
            cookies={"DJkdikKMG": cookie},
            timeout=TIMEOUT,
            allow_redirects=True
        )

        if r.status_code != 200:
            return VPSResult(account, False, "页面不包含VPS信息")

        soup = BeautifulSoup(r.text, "html.parser")

        # 只认这一层结构
        if not soup.find("div", class_="information"):
            return VPSResult(account, False, "页面不包含VPS信息")

        return VPSResult(account, True)

    except Exception:
        return VPSResult(account, False, "页面不包含VPS信息")

# ==================== 并发执行 ====================

def check_all_vps() -> List[VPSResult]:
    results = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as pool:
        futures = [pool.submit(check_single_vps, a) for a in COOKIES_CONFIG]
        for f in as_completed(futures):
            results.append(f.result())
    return results

# ==================== 企业微信模板（严格对齐） ====================

def format_wechat_message(results: List[VPSResult]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total = len(results)
    success_count = sum(1 for r in results if r.success)
    error_count = total - success_count

    lines = []
    lines.append(f"🚀 VPS状态检查报告 ({now})\n")
    lines.append(f"📊 状态: {success_count}正常 {error_count}异常\n")

    if error_count > 0:
        lines.append("❌ 异常账号:")
        for r in results:
            if not r.success:
                lines.append(f"  • {r.account}: {r.error}")
        lines.append("")

    lines.append("📅 检查完成")

    if "GITHUB_ACTIONS" in os.environ:
        run_number = os.getenv("GITHUB_RUN_NUMBER", "")
        lines.append(f"🔗 详情: GitHub Actions #{run_number}")

    return "\n".join(lines)

# ==================== 企业微信发送 ====================

def send_wechat(content: str):
    if not WEBHOOK_URL:
        print(content)
        return

    requests.post(
        WEBHOOK_URL,
        json={
            "msgtype": "text",
            "text": {"content": content}
        },
        timeout=10
    )

# ==================== 主入口 ====================

def main():
    results = check_all_vps()
    message = format_wechat_message(results)
    send_wechat(message)

    # 只要有一个成功，就返回 0
    return 0 if any(r.success for r in results) else 1

if __name__ == "__main__":
    sys.exit(main())
