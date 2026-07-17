import requests
from qcloud_cos import CosConfig, CosS3Client
import os
import json

url = "https://misub-d0t.pages.dev/profiles/dafd961f-bcb2-4c0b-9dbd-2fe3ca591923?clash"

headers = {
    "User-Agent": "Clash/Windows"
}

secret_id = os.environ["SECRET_ID"]
secret_key = os.environ["SECRET_KEY"]
region = os.environ["REGION"]
bucket = os.environ["BUCKET"]
wecom_webhook = os.environ.get("WECOM_WEBHOOK", "")


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

    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    cos_client = CosS3Client(config)

    upload_response = cos_client.put_object(
        Bucket=bucket,
        Body=file_content,
        Key='1',
    )

    upload_str = str(upload_response)
    print("上传响应（前 300 字符）:")
    print(upload_str[:300])

    success_msg = "✅ Clash 配置更新成功！已上传到腾讯云 COS。"
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
