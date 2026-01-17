#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List
import os
import sys

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
    data: Dict = None

def extract_by_label(soup, label):
    for item in soup.select(".information-list-item"):
        left = item.select_one(".information-list-item-left")
        if left and label in left.text:
            right = item.select_one(".information-list-item-right")
            return right.text.strip()
    return ""

def check_single_vps(cfg: Dict) -> VPSResult:
    account = cfg["remark"]
    try:
        r = requests.get(
            VPS_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            cookies={"DJkdikKMG": cfg["DJkdikKMG"]},
            timeout=TIMEOUT
        )

        soup = BeautifulSoup(r.text, "html.parser")
        root = soup.find("div", class_="information")
        if not root:
            return VPSResult(account, False, "页面不包含VPS信息")

        data = {
            "ip": extract_by_label(soup, "VPS IP"),
            "location": extract_by_label(soup, "服务器地址"),
            "expire": extract_by_label(soup, "到期日期"),
            "trade": extract_by_label(soup, "近1月实盘交易数量"),
        }

        data["type"] = soup.select_one(".condition-left").text.strip()
        data["status"] = soup.select_one(".condition-right").text.strip()

        nums = soup.select(".information-num-item")
        if len(nums) >= 4:
            data["asset"] = nums[0].select_one("p.color1").text.strip()
            data["profit"] = nums[3].select_one("p").text.strip()

        return VPSResult(account, True, data=data)

    except Exception:
        return VPSResult(account, False, "页面不包含VPS信息")

def format_message(results: List[VPSResult]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = [r for r in results if r.success]
    bad = [r for r in results if not r.success]

    lines = [
        f"🚀 VPS状态检查报告 ({now})\n",
        f"📊 状态: {len(ok)}正常 {len(bad)}异常\n"
    ]

    if ok:
        lines.append("✅ 正常账号:")
        for r in ok:
            d = r.data
            lines += [
                f"  • {r.account}",
                f"    - IP: {d.get('ip')}",
                f"    - 地区: {d.get('location')}",
                f"    - 状态: {d.get('type')} · {d.get('status')}",
                f"    - 到期: {d.get('expire')}",
                f"    - 近1月交易: {d.get('trade')}",
                ""
            ]

    if bad:
        lines.append("❌ 异常账号:")
        for r in bad:
            lines.append(f"  • {r.account}: {r.error}")
        lines.append("")

    lines.append("📅 检查完成")
    if "GITHUB_ACTIONS" in os.environ:
        lines.append(f"🔗 详情: GitHub Actions #{os.getenv('GITHUB_RUN_NUMBER')}")

    return "\n".join(lines)

def main():
    results = []
    with ThreadPoolExecutor(MAX_THREADS) as pool:
        for f in as_completed([pool.submit(check_single_vps, c) for c in COOKIES_CONFIG]):
            results.append(f.result())

    msg = format_message(results)
    if WEBHOOK_URL:
        requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": msg}})
    else:
        print(msg)

if __name__ == "__main__":
    sys.exit(main())
