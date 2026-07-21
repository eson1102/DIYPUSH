import requests
import json

token_str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2MjkiLCJlbWFpbCI6ImR1bmNhbnl1MTEwMkBnbWFpbC5jb20iLCJleHAiOjE3ODUyMjA4MTl9.sA5JQg0OwDQ3CiP7Xi2K3h387Yf7nd_O7x536XEEMhQ"

headers = {
    "Authorization": f"Bearer {token_str}",
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "origin": "https://layercraft.com.cn",
    "referer": "https://layercraft.com.cn/app.html"
}

# ===================== 配置你的企微机器人webhook =====================
WECOM_WEBHOOK = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e75ac7b2-f7e7-45a5-a7b8-0f92390ab020"
# ===================================================================

# 封装企微消息推送函数
def send_wechat_msg(content):
    try:
        post_data = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        resp = requests.post(
            WECOM_WEBHOOK,
            data=json.dumps(post_data),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print("企业微信推送返回：", resp.text)
    except Exception as e:
        print(f"企业微信推送失败，仅本地输出：{str(e)}")

try:
    # 1、校验账号
    res_user = requests.get("https://layercraft.com.cn/api/auth/me", headers=headers, timeout=15)
    print("状态码：", res_user.status_code)

    if res_user.status_code != 200:
        err_msg = f"❌ 账号校验失败，HTTP状态码：{res_user.status_code}"
        print(err_msg)
        send_wechat_msg(err_msg)
    else:
        user_info = res_user.json()
        print("用户信息：", user_info)

        # 提取关键信息组装推送文案
        email = user_info.get("email", "无")
        balance = user_info.get("points_balance", 0)
        daily_login = user_info.get("daily_login", {})
        granted = daily_login.get("granted", -1)
        daily_total_points = daily_login.get("points_balance", 0)

        if granted == 0:
            sign_tip = "今日尚未领取登录4积分"
        elif granted == 1:
            sign_tip = "今日已完成签到，积分已到账"
        else:
            sign_tip = f"签到状态未知，granted={granted}"

        push_text = (
            "【LayerCraft账号状态报告】\n"
            f"绑定邮箱：{email}\n"
            f"当前可用消费积分：{balance}\n"
            f"累计签到积分总额：{daily_total_points}\n"
            f"签到状态：{sign_tip}"
        )
        send_wechat_msg(push_text)

except Exception as e:
    crash_msg = f"❌ 脚本执行异常：{str(e)}"
    print(crash_msg)
    send_wechat_msg(crash_msg)
