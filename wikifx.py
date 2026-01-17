#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys
from dataclasses import dataclass
from typing import List, Dict

VPS_URL = "https://vps.wikifx.com/zh-cn/jyzh"
TIMEOUT = 15
MAX_THREADS = 3

WEBHOOK_URL = os.getenv("WECHAT_WEBHOOK_URL111", "")

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

@dataclass
class VPSResult:
    account: str
    success: bool
    error: str = ""
    info: str = ""

def check_single_vps(account_data: Dict) -> VPSResult:
    account = account_data["remark"]
    cookie = account_data["DJkdikKMG"]

    try:
        r = requests.get(
            VPS_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            cookies={"DJkdikKMG": cookie},
            timeout=TIMEOUT
        )

        if r.status_code != 200:
            return VPSResult(account, False, "页面不包含VPS信息")

        soup = BeautifulSoup(r.text, "html.parser")

        if not soup.find("div", class_="information"):
            return VPSResult(account, False, "页面不包含VPS信息")

        return VPSResult(account, True, info="VPS页面正常")

    except Exception:
        return VPSResult(account, False, "页面不包含VPS信息")

def check_all_vps() -> List[VPSResult]:
    results = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as pool:
        futures = [pool.submit(check_single_vps, a) for a in COOKIES_CONFIG]
        for f in as_completed(futures):
            results.append(f.result())
    return results

def format_wechat_message(results: List[VPSResult]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    success_list = [r for r in results if r.success]
    error_list = [r for r in results if not r.success]

    lines = []
    lines.append(f"🚀 VPS状态检查报告 ({now})\n")
    lines.append(f"📊 状态: {len(success_list)}正常 {len(error_list)}异常\n")

    if success_list:
        lines.append("✅ 正常账号:")
        for r in success_list:
            lines.append(f"  • {r.account}: {r.info}")
        lines.append("")

    if error_list:
        lines.append("❌ 异常账号:")
        for r in error_list:
            lines.append(f"  • {r.account}: {r.error}")
        lines.append("")

    lines.append("📅 检查完成")

    if "GITHUB_ACTIONS" in os.environ:
        lines.append(f"🔗 详情: GitHub Actions #{os.getenv('GITHUB_RUN_NUMBER')}")

    return "\n".join(lines)

def send_wechat(content: str):
    if not WEBHOOK_URL:
        print(content)
        return
    requests.post(
        WEBHOOK_URL,
        json={"msgtype": "text", "text": {"content": content}},
        timeout=10
    )

def main():
    results = check_all_vps()
    message = format_wechat_message(results)
    send_wechat(message)
    return 0 if results else 1

if __name__ == "__main__":
    sys.exit(main())
