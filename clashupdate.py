import requests
from qcloud_cos import CosConfig, CosS3Client
import os
import json

url = "https://misub-d0t.pages.dev/profiles/dafd961f-bcb2-4c0b-9dbd-2fe3ca591923?clash"

headers = {
    "User-Agent": "Clash/Windows"
}

# ============ 公共 COS 配置（同地区、同用户） ============
secret_id = os.environ["SECRET_ID"]
secret_key = os.environ["SECRET_KEY"]
region = os.environ["REGION"]

wecom_webhook = os.environ.get("WECOM_WEBHOOK", "")

# ============ 需要上传的多个文件（同一 bucket，不同 Key） ============
# 格式：(bucket, key)
COS_TARGETS = [
    (os.environ["BUCKET"], "1"),
    (os.environ["BUCKET"], "1.yaml"),
    (os.environ["BUCKET"], "2"),
    # 如果文件名/目录不同，直接改 key，例如 "clash/config.yaml"
]
# =============================================================


def send_wecom_message(msg):
    if not wecom_webhook:
        return
    try:
        data = {
            "msgtype": "text",
            "text": {
                "content": msg
            }
        }
        response = requests.post(wecom_webhook, json=data, timeout=10)
        print(f"企业微信通知发送结果: {response.status_code}")
    except Exception as e:
        print(f"发送企业微信通知失败: {e}")


def is_valid_clash_config(content):
    text = content.decode('utf-8', errors='replace')
    valid_keywords = ["proxies:", "mixed-port:", "mode:", "dns:", "external-controller:", "allow-lan:"]
    found_count = sum(1 for kw in valid_keywords if kw in text)
    return found_count >= 3


try:
    response = requests.get(url, headers=headers, timeout=200)
    response.raise_for_status()
    file_content = response.content

    text = file_content.decode('utf-8', errors='replace')
    print("获取到的内容（前 300 字符）:")
    print(text[:300])

    if not is_valid_clash_config(file_content):
        error_msg = "⚠️ Clash 配置内容校验失败！获取到的内容可能不是有效的配置文件，跳过上传。"
        print(error_msg)
        send_wecom_message(error_msg)
        exit(1)

    # 公共 COS 客户端（同地区、同用户，只需初始化一次）
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    cos_client = CosS3Client(config)

    # 循环上传到多个 Key
    success_list = []
    fail_list = []
    for bucket, key in COS_TARGETS:
        try:
            upload_response = cos_client.put_object(
                Bucket=bucket,
                Body=file_content,
                Key=key,
            )
            upload_str = str(upload_response)
            print(f"[{bucket}/{key}] 上传响应（前 300 字符）:")
            print(upload_str[:300])
            success_list.append(f"{bucket}/{key}")
        except Exception as e:
            fail_list.append(f"{bucket}/{key}: {e}")
            print(f"[{bucket}/{key}] 上传失败: {e}")

    if fail_list:
        summary = "⚠️ Clash 配置部分上传结果：\n"
        if success_list:
            summary += "✅ 成功:\n" + "\n".join(success_list) + "\n"
        summary += "❌ 失败:\n" + "\n".join(fail_list)
        print(summary)
        send_wecom_message(summary)
        exit(1)
    else:
        success_msg = "✅ Clash 配置更新成功！已上传到:\n" + "\n".join(success_list)
        print(success_msg)
        send_wecom_message(success_msg)

except requests.exceptions.RequestException as e:
    error_msg = f"❌ 请求失败: {e}"
    print(error_msg)
    send_wecom_message(error_msg)
    exit(1)
except Exception as e:
    error_msg = f"❌ 上传失败: {e}"
    print(error_msg)
    send_wecom_message(error_msg)
    exit(1)
