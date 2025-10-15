import requests
from bs4 import BeautifulSoup
import json
import os

# ========== 配置部分（同原代码，需确保WEBHOOK_URL正确） ==========
AUTHOR_URL = "https://www.mql5.com/zh/signals/author/wanbaolu"
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=5efc99e5-42a6-4da8-abe9-80158d9b38cf"  # 替换为你的Webhook key
DATA_FILE = "mql5_subscribers.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# ========== 企业微信推送（同原代码） ==========
def send_wechat_message(content):
    data = {"msgtype": "text", "text": {"content": content}}
    try:
        resp = requests.post(WEBHOOK_URL, json=data, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ 推送失败: {resp.status_code}, {resp.text}")
    except Exception as e:
        print(f"❌ 推送异常: {e}")

# ========== 抓取信号信息（同原代码） ==========
def fetch_signals():
    headers = {"User-Agent": USER_AGENT}
    html = requests.get(AUTHOR_URL, headers=headers, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")

    signals = {}
    rows = soup.select("div.row.signal")

    for row in rows:
        name_tag = row.select_one(".signal .name a")
        subs_tag = row.select_one(".col-subscribers")
        if name_tag and subs_tag:
            name = name_tag.text.strip()
            url = "https://www.mql5.com" + name_tag.get("href")
            subs = subs_tag.text.strip().replace(",", "")
            try:
                subscribers = int(subs)
            except ValueError:
                subscribers = 0
            signals[name] = {"subs": subscribers, "url": url}

    return signals

# ========== 读取与保存本地状态（同原代码） ==========
def load_last_state():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========== 主逻辑（同原代码） ==========
def main():
    print("🔍 正在检查 MQL5 订阅者变化...")
    current_data = fetch_signals()
    last_data = load_last_state()

    if not last_data:
        print("首次运行，保存初始数据。")
        save_state(current_data)
        return

    changes = []
    for name, info in current_data.items():
        subs = info["subs"]
        url = info["url"]
        old_info = last_data.get(name)
        if not old_info:
            changes.append(f"🆕 新增信号《{name}》\n📍订阅者：{subs} 人\n🔗 {url}")
        else:
            old_subs = old_info["subs"]
            if subs != old_subs:
                diff = subs - old_subs
                arrow = "📈 增加" if diff > 0 else "📉 减少"
                changes.append(f"《{name}》{arrow} {abs(diff)} 人 → 当前 {subs} 人\n🔗 {url}")

    if changes:
        summary = f"📢 MQL5 订阅者变动提醒\n\n本次检测共有 {len(changes)} 个信号发生变化。\n\n—— 详细变动如下 ——\n\n"
        msg = summary + "\n\n".join(changes)
        print(msg)
        send_wechat_message(msg)
    else:
        print("✅ 无变化")

    save_state(current_data)

# ========== 单次运行（删除while循环，直接执行main） ==========
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❗ 执行错误: {e}")
