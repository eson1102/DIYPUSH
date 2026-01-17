#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VPS 状态监控脚本（WikiFX）
适配 GitHub Actions + 企业微信机器人（文本）
已根据最新 HTML 结构修复解析逻辑
"""

import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import os
import sys
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

# ==================== 配置 ====================

WEBHOOK_URL = (
    os.getenv("WECHAT_WEBHOOK_URL111")
    or os.getenv("WECHAT_WEBHOOK_URL")
    or ""
)

VPS_URL = "https://vps.wikifx.com/zh-cn/jyzh"

MAX_THREADS = 3
TIMEOUT = 15
RETRY_COUNT = 2
DELAY_BETWEEN_REQUESTS = 1

# ⚠️ 建议实际使用 GitHub Secrets
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
    ip: str = ""
    location: str = ""
    transactions: int = 0
    expire_date: str = ""
    days_left: Optional[int] = None
    error: str = ""
    check_time: str = ""

# ==================== 日志 ====================

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    icons = {"INFO":"ℹ️","SUCCESS":"✅","WARNING":"⚠️","ERROR":"❌","DEBUG":"🐛"}
    print(f"[{ts}] {icons.get(level,'')} {msg}")

# ==================== 页面解析（核心） ====================

def parse_vps_page(html: str) -> Optional[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    root = soup.find("div", class_="information")
    if not root:
        return None

    right = root.find("div", class_="information-right")
    if not right:
        return None

    items = right.select(".information-list-item")
    if not items:
        return None

    data = {}
    for item in items:
        k = item.find("div", class_="information-list-item-left")
        v = item.find("div", class_="information-list-item-right")
        if not k or not v:
            continue

        key = k.get_text(strip=True)
        value = v.get_text(strip=True)

        if key == "服务器地址":
            value = value.replace("香港 香港", "香港")

        data[key] = value

    return data if data else None

# ==================== 单账号检查 ====================

def check_single_vps(account_data: Dict) -> VPSResult:
    account = account_data["remark"]
    cookie = account_data["DJkdikKMG"]
    check_time = datetime.now().strftime("%H:%M:%S")

    if not cookie:
        return VPSResult(account, False, error="Cookie 未配置", check_time=check_time)

    headers = {
        "User-Agent": "Mozilla/5.0 Chrome/120",
        "Accept-Language": "zh-CN,zh;q=0.9"
    }

    cookies = {"DJkdikKMG": cookie}

    for attempt in range(RETRY_COUNT + 1):
        try:
            if attempt > 0:
                time.sleep(DELAY_BETWEEN_REQUESTS + random.random())

            r = requests.get(
                VPS_URL,
                headers=headers,
                cookies=cookies,
                timeout=TIMEOUT,
                allow_redirects=True
            )

            if r.status_code != 200:
                raise Exception(f"HTTP {r.status_code}")

            soup = BeautifulSoup(r.text, "html.parser")
            if not soup.find("div", class_="information"):
                raise Exception("未登录或页面结构异常")

            info = parse_vps_page(r.text)
            if not info:
                raise Exception("解析 VPS 信息失败")

            ip = info["VPS IP"]
            location = info["服务器地址"]

            tx = int(info["近1月实盘交易数量"].replace(",", ""))
            expire_date = info["到期日期"]

            expire_obj = datetime.strptime(expire_date, "%Y-%m-%d").date()
            days_left = (expire_obj - datetime.now().date()).days

            return VPSResult(
                account=account,
                success=True,
                ip=ip,
                location=location,
                transactions=tx,
                expire_date=expire_date,
                days_left=days_left,
                check_time=check_time
            )

        except Exception as e:
            if attempt == RETRY_COUNT:
                return VPSResult(
                    account=account,
                    success=False,
                    error=str(e),
                    check_time=check_time
                )

    return VPSResult(account, False, error="未知错误", check_time=check_time)

# ==================== 并发检查 ====================

def check_all_vps() -> List[VPSResult]:
    results = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as pool:
        futures = [pool.submit(check_single_vps, a) for a in COOKIES_CONFIG]
        for f in as_completed(futures):
            results.append(f.result())
    return results

# ==================== 企业微信 ====================

def send_wechat(msg: str):
    if not WEBHOOK_URL:
        return
    requests.post(
        WEBHOOK_URL,
        json={"msgtype":"text","text":{"content":msg}},
        timeout=10
    )

def format_wechat(results: List[VPSResult]) -> str:
    lines = ["🚀 VPS 状态检查结果\n"]
    for r in results:
        if r.success:
            tag = "✅"
            if r.days_left <= 7:
                tag = "🟠"
            elif r.days_left < 0:
                tag = "🔴"
            lines.append(
                f"{tag} {r.account}\n"
                f"IP: {r.ip}\n"
                f"交易: {r.transactions}\n"
                f"到期: {r.expire_date}（{r.days_left}天）\n"
            )
        else:
            lines.append(f"❌ {r.account}：{r.error}\n")
    return "\n".join(lines)

# ==================== 主入口 ====================

def main():
    log("开始 VPS 状态检查")
    results = check_all_vps()

    for r in results:
        if r.success:
            log(f"{r.account} OK | {r.ip} | 剩余 {r.days_left} 天", "SUCCESS")
        else:
            log(f"{r.account} FAIL | {r.error}", "ERROR")

    msg = format_wechat(results)
    send_wechat(msg)

    return 0 if any(r.success for r in results) else 1

if __name__ == "__main__":
    sys.exit(main())
