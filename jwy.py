import json, datetime, os, requests

# 从 GitHub Secrets 获取环境变量
WEBHOOK_URL = os.environ.get("WECHAT_WEBHOOK_URL")
CF_WORKER_URL = os.environ.get("CF_WORKER_URL") # 你的 Worker 地址

def main():
    if not os.path.exists('data.json'): return
    with open('data.json', 'r', encoding='utf-8') as f:
        subs = json.load(f)
    
    today = datetime.date.today()
    for item in subs:
        due_date = datetime.datetime.strptime(item['due_date'], '%Y-%m-%d').date()
        delta = (due_date - today).days
        
        if 0 <= delta <= item['reminder_days']:
            # 构造点击即触发的链接
            confirm_url = f"{CF_WORKER_URL}?name={item['name']}"
            
            content = (
                f"### 📅 VPS 到期提醒\n"
                f"> **项目**：{item['name']}\n"
                f"> **金额**：{item['price']}\n"
                f"> **到期日期**：{item['due_date']} (剩 {delta} 天)\n\n"
                f"✅ [已续费，点此一键更新日期]({confirm_url})"
            )
            
            requests.post(WEBHOOK_URL, json={
                "msgtype": "markdown",
                "markdown": {"content": content}
            })

if __name__ == "__main__":
    main()
