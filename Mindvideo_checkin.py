import os
import requests
import json
import hashlib
from datetime import datetime, timedelta
import pytz  # 添加时区库


class MindVideoAutoCheckin:
    def __init__(self, email=None, password=None, webhook_url=None, account_index=1):
        # 支持多账号：优先使用传入的参数，否则从环境变量读取
        self.email = email or os.environ.get('EMAIL')
        self.password = password or os.environ.get('PASSWORD')
        self.webhook_url = webhook_url or os.environ.get('WECOM_WEBHOOK')
        self.account_index = account_index

        # API地址
        self.login_url = "https://api-app.mindvideo.ai/api/login"
        self.checkin_url = "https://api-app.mindvideo.ai/api/checkin"
        self.credits_url = "https://api-app.mindvideo.ai/api/user/credits/stats"

        # 基础请求头
        self.base_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept": "application/json, text/plain, */*",
            "origin": "https://www.mindvideo.ai",
            "referer": "https://www.mindvideo.ai/",
            "content-type": "application/json",
            "i-lang": "zh-CN",
            "i-version": "1.0.8"
        }

        self.token = None
        self.checkin_result = {
            "success": False,
            "message": "",
            "points": 0,
            "continuity": 0,
            "total_credits": 0,
            "used_credits": 0,
            "remaining_credits": 0,
            "subscription_type": "Free",
            "timestamp": self.get_beijing_time()
        }

    def get_beijing_time(self):
        """获取北京时间 (UTC+8)"""
        try:
            beijing_tz = pytz.timezone('Asia/Shanghai')
            beijing_time = datetime.now(beijing_tz)
            return beijing_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            utc_now = datetime.utcnow()
            beijing_time = utc_now + timedelta(hours=8)
            return beijing_time.strftime('%Y-%m-%d %H:%M:%S')

    def md5_encrypt(self, text):
        """MD5加密"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def login(self):
        """自动登录获取Token"""
        if not self.email or not self.password:
            error_msg = "❌ 错误：未设置账号密码环境变量"
            print(error_msg)
            self.checkin_result["message"] = error_msg
            return False

        print(f"🔄 正在登录账号: {self.email}")

        encrypted_password = self.md5_encrypt(self.password)

        login_data = {
            "email": self.email,
            "password": encrypted_password
        }

        try:
            response = requests.post(
                self.login_url,
                json=login_data,
                headers=self.base_headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('code') == 0 and 'data' in result:
                    token = result['data'].get('access_token')
                    if token:
                        if not token.startswith('Bearer '):
                            self.token = f'Bearer {token}'
                        else:
                            self.token = token

                        print(f"✅ 登录成功！")
                        return True

                error_msg = f"登录响应异常: {json.dumps(result, ensure_ascii=False)}"
                print(f"⚠️ {error_msg}")
                self.checkin_result["message"] = error_msg
                return False
            else:
                error_msg = f"登录失败，状态码: {response.status_code}"
                print(f"❌ {error_msg}")
                self.checkin_result["message"] = error_msg
                return False

        except Exception as e:
            error_msg = f"登录异常: {str(e)}"
            print(f"❌ {error_msg}")
            self.checkin_result["message"] = error_msg
            return False

    def get_credits_stats(self):
        """获取积分统计信息"""
        if not self.token:
            print("❌ 未获取到Token，无法查询积分")
            return False

        print("🔄 正在查询积分信息...")

        headers = self.base_headers.copy()
        headers["authorization"] = self.token

        try:
            response = requests.get(
                self.credits_url,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('code') == 0 and 'data' in result:
                    data = result['data']

                    total_info = data.get('total', {})
                    self.checkin_result["total_credits"] = int(total_info.get('total_credits', 0))
                    self.checkin_result["used_credits"] = int(total_info.get('used_credits', 0))
                    self.checkin_result["remaining_credits"] = int(total_info.get('remaining_credits', 0))
                    self.checkin_result["subscription_type"] = data.get('subscription_type', 'Free')

                    print(f"✅ 积分查询成功")
                    print(f"📊 总积分: {self.checkin_result['total_credits']}")
                    print(f"📊 已用积分: {self.checkin_result['used_credits']}")
                    print(f"📊 剩余积分: {self.checkin_result['remaining_credits']}")
                    print(f"📊 订阅类型: {self.checkin_result['subscription_type']}")

                    return True
                else:
                    print(f"⚠️ 积分查询响应异常: {json.dumps(result, ensure_ascii=False)}")
                    return False
            else:
                print(f"⚠️ 积分查询失败，状态码: {response.status_code}")
                return False

        except Exception as e:
            print(f"⚠️ 积分查询异常: {e}")
            return False

    def checkin(self):
        """执行签到"""
        if not self.token:
            error_msg = "未获取到Token，请先登录"
            print(f"❌ {error_msg}")
            self.checkin_result["message"] = error_msg
            return False

        print("🔄 正在执行签到...")

        headers = self.base_headers.copy()
        headers["authorization"] = self.token

        try:
            response = requests.post(
                self.checkin_url,
                headers=headers,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()

                code = result.get('code')
                message = result.get('message', '')

                if code == 0:
                    self.checkin_result["success"] = True
                    print(f"✅ 签到成功！")

                    if 'data' in result and result['data']:
                        data = result['data']
                        self.checkin_result["points"] = data.get('points', 0)
                        self.checkin_result["continuity"] = data.get('continuity', 0)

                        msg_parts = []
                        if 'points' in data:
                            msg_parts.append(f"💎 本次获得积分：+{data['points']}")
                        if 'continuity' in data:
                            msg_parts.append(f"📅 连续签到：{data['continuity']}天")
                        if 'message' in data:
                            msg_parts.append(f"📝 消息：{data['message']}")

                        self.checkin_result["message"] = "\n".join(msg_parts) if msg_parts else "签到成功"
                    else:
                        self.checkin_result["message"] = message or "签到成功"

                    return True

                elif code == 70001:
                    self.checkin_result["success"] = True
                    print(f"ℹ️ {message}")
                    self.checkin_result["message"] = f"{message}（今日已签到）"
                    return True

                else:
                    error_msg = f"签到失败: {message} (code: {code})"
                    print(f"❌ {error_msg}")
                    self.checkin_result["message"] = error_msg
                    return False

            else:
                error_msg = f"签到请求失败，状态码: {response.status_code}"
                print(f"❌ {error_msg}")
                self.checkin_result["message"] = error_msg

                if response.status_code == 401:
                    self.checkin_result["message"] = "Token已过期，需要重新登录"
                    print("⚠️ Token已过期")

                return False

        except Exception as e:
            error_msg = f"签到异常: {str(e)}"
            print(f"❌ {error_msg}")
            self.checkin_result["message"] = error_msg
            return False

    def run(self):
        """单个账号的主流程（不发送通知，只返回结果）"""
        current_time = self.get_beijing_time()
        print("=" * 20)
        print(f"🚀 MindVideo自动签到系统启动 - 账号 [{self.account_index}]")
        print(f"⏰ 当前时间: {current_time} (北京时间)")
        print("=" * 20)

        if not self.login():
            print("❌ 登录失败，签到流程终止")
            return False

        print("-" * 20)

        if not self.checkin():
            print("❌ 签到流程失败")
            return False

        print("-" * 20)

        self.get_credits_stats()
        print("🎉 账号签到流程完成！")
        return True


def parse_accounts(env_value):
    """
    解析多账号环境变量，支持以下格式：
    1. 用 & 分隔账号和密码：email1&password1,email2&password2
    2. 用 | 分隔账号和密码：email1|password1,email2|password2
    3. 用 : 分隔账号和密码：email1:password1,email2:password2
    多账号之间用英文逗号 , 或换行分隔
    """
    if not env_value:
        return []

    accounts = []
    entries = []
    for line in env_value.replace('\r\n', '\n').split('\n'):
        entries.extend(line.split(','))

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        for sep in ['&', '|', ':']:
            if sep in entry:
                parts = entry.split(sep, 1)
                if len(parts) == 2 and parts[0].strip() and parts[1].strip():
                    accounts.append((parts[0].strip(), parts[1].strip()))
                    break

    return accounts


def send_merged_wecom_message(webhook_url, results, overall_time):
    """
    把所有账号的结果合并成一条企业微信通知发送
    results: list of dict，每个 dict 包含 account_index/email/success/message/credits 等
    """
    if not webhook_url:
        print("⚠️ 未设置企业微信Webhook，跳过通知")
        return False

    total = len(results)
    success_count = sum(1 for r in results if r["success"])
    fail_count = total - success_count

    # 总体标题
    if fail_count == 0:
        title = f"MindVideo 全部签到成功 🎉 ({success_count}/{total})"
        status_emoji = "✅"
    elif success_count == 0:
        title = f"MindVideo 全部签到失败 ⚠️ (0/{total})"
        status_emoji = "❌"
    else:
        title = f"MindVideo 部分签到成功 ⚠️ ({success_count}/{total})"
        status_emoji = "⚠️"

    # 逐账号拼接详情
    detail_lines = []
    for r in results:
        if r["success"]:
            head = f"✅ [{r['account_index']}] {r['email']}"
        else:
            head = f"❌ [{r['account_index']}] {r['email']}"

        detail_lines.append(head)

        # 签到消息（多行缩进）
        msg = r["message"] or "无"
        for line in msg.split("\n"):
            if line.strip():
                detail_lines.append(f"   {line}")

        # 积分信息
        if r["success"] and r["total_credits"] > 0:
            detail_lines.append(
                f"   💳 总积分:{r['total_credits']} 已用:{r['used_credits']} "
                f"剩余:{r['remaining_credits']} 订阅:{r['subscription_type']}"
            )
        detail_lines.append("")  # 空行分隔各账号

    details = "\n".join(detail_lines).rstrip()

    full_text = f"""【{status_emoji} {title}】

📅 时间：{overall_time}
📊 汇总：成功 {success_count} / 失败 {fail_count} / 总计 {total}

{details}

🤖 MindVideo 自动签到系统"""

    message = {
        "msgtype": "text",
        "text": {
            "content": full_text
        }
    }

    try:
        response = requests.post(
            webhook_url,
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                print("✅ 企业微信合并通知发送成功")
                return True
            else:
                print(f"⚠️ 企业微信通知发送失败: {result}")
                return False
        else:
            print(f"⚠️ 企业微信通知发送失败，状态码: {response.status_code}")
            return False

    except Exception as e:
        print(f"⚠️ 发送企业微信通知异常: {e}")
        return False


if __name__ == "__main__":
    # 优先读取多账号环境变量 ACCOUNTS
    # 格式示例：magiceson@gmail.com&Lulu1110,duncanyu1102@gmail.com&Lulu1110
    accounts_str = os.environ.get('ACCOUNTS', '')
    accounts = parse_accounts(accounts_str)

    # 回退到单账号模式
    if not accounts:
        single_email = os.environ.get('EMAIL')
        single_password = os.environ.get('PASSWORD')
        if single_email and single_password:
            accounts = [(single_email, single_password)]

    if not accounts:
        print("❌ 未找到任何账号配置")
        print("💡 请设置 ACCOUNTS 环境变量，格式：email1&password1,email2&password2")
        print("💡 或设置 EMAIL 和 PASSWORD 环境变量（单账号模式）")
        exit(1)

    webhook_url = os.environ.get('WECOM_WEBHOOK')

    print(f"📋 共发现 {len(accounts)} 个账号")

    all_results = []
    run_time = None

    for idx, (email, password) in enumerate(accounts, start=1):
        print(f"\n{'=' * 60}")
        print(f"处理第 {idx}/{len(accounts)} 个账号")
        print(f"{'=' * 60}")

        checker = MindVideoAutoCheckin(
            email=email,
            password=password,
            account_index=idx
        )

        try:
            checker.run()
        except Exception as e:
            print(f"❌ 账号 [{idx}] 处理异常: {e}")
            checker.checkin_result["success"] = False
            checker.checkin_result["message"] = f"处理异常: {e}"

        if run_time is None:
            run_time = checker.get_beijing_time()

        # 收集每个账号的结果
        all_results.append({
            "account_index": idx,
            "email": email,
            "success": checker.checkin_result["success"],
            "message": checker.checkin_result["message"],
            "points": checker.checkin_result["points"],
            "continuity": checker.checkin_result["continuity"],
            "total_credits": checker.checkin_result["total_credits"],
            "used_credits": checker.checkin_result["used_credits"],
            "remaining_credits": checker.checkin_result["remaining_credits"],
            "subscription_type": checker.checkin_result["subscription_type"],
        })

    success_count = sum(1 for r in all_results if r["success"])
    fail_count = len(all_results) - success_count

    print(f"\n{'=' * 60}")
    print(f"📊 全部完成！成功: {success_count}, 失败: {fail_count}, 总计: {len(all_results)}")
    print(f"{'=' * 60}")

    # 统一发送一条合并通知
    print("📤 发送合并通知...")
    send_merged_wecom_message(webhook_url, all_results, run_time)

    exit(0 if fail_count == 0 else 1)
