import requests
from qcloud_cos import CosConfig, CosS3Client
import os

url = "https://misub-d0t.pages.dev/profiles/dafd961f-bcb2-4c0b-9dbd-2fe3ca591923?clash"

headers = {
    "User-Agent": "Clash/Windows"
}

secret_id = os.environ["SECRET_ID"]
secret_key = os.environ["SECRET_KEY"]
region = os.environ["REGION"]
bucket = os.environ["BUCKET"]

try:
    response = requests.get(url, headers=headers, timeout=200)
    response.raise_for_status()
    file_content = response.content

    text = file_content.decode('utf-8', errors='replace')
    print("Fetched content (first 300 chars):")
    print(text[:300])

    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
    cos_client = CosS3Client(config)

    upload_response = cos_client.put_object(
        Bucket=bucket,
        Body=file_content,
        Key='1',
    )

    upload_str = str(upload_response)
    print("Upload response (first 300 chars):")
    print(upload_str[:300])

    print("clash 文件更新及日志输出完成！")
except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
except Exception as e:
    print(f"上传失败: {e}")
