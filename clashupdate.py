import requests
from qcloud_cos import CosConfig, CosS3Client
import os

# 腾讯云信息
secret_id = os.environ["SECRET_ID"]      # 替换为您的 SecretId
secret_key = os.environ["SECRET_KEY"]    # 替换为您的 SecretKey
region = os.environ["REGION"]            # 替换为桶的所在地域
bucket = os.environ["BUCKET"]            # 替换为您的桶名称
telegram_token = os.environ["BOT_TOKEN"]
telegram_chat_id = os.environ["CHAT_ID"]

# 使用请求库获取 ini 文件的内容
response = requests.get(
    "https://cfdingyue-4lu.pages.dev/a5ce27a6-76df-48da-be62-493fbda9a3af/?clash",
    timeout=200
)

# 原始二进制内容
file_content = response.content

# 尝试以 utf-8 解码，解码失败则替换掉错误字符
try:
    text = file_content.decode('utf-8', errors='replace')
except Exception:
    text = repr(file_content)

# 只输出前 300 字符
print("Fetched content (first 300 chars):")
print(text[:300])

# 腾讯云 COS 的配置和客户端初始化
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
cos_client = CosS3Client(config)

# 上传文件：'1' 是对象键（Key），根据需求可改
upload_response = cos_client.put_object(
    Bucket=bucket,
    Body=file_content,
    Key='1',
)

# 将上传响应转换为字符串并截断
upload_str = str(upload_response)
print("Upload response (first 300 chars):")
print(upload_str[:300])

print("clash 文件更新及日志输出完成！")

# 如果仍要通过 Telegram 通知，可取消下面注释：
# telegram_msg = f"Fetched: {text[:100]}...\nUploaded response: {upload_str[:100]}..."
# requests.post(
#     f'https://api.telegram.org/bot{telegram_token}/sendMessage',
#     json={"chat_id": telegram_chat_id, "text": telegram_msg}
# )
