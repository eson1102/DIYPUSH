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

# 自定义词
custom_word = "【备用速度慢】"  # 替换为您的自定义词

# 使用请求库获取ini文件的内容
response = requests.get("https://ipdb.api.030101.xyz/?type=bestproxy&country=true", timeout=20)
file_content = response.text

# 处理文件内容，在每行的 '#' 后面添加自定义词
processed_content = ""
for line in file_content.splitlines():
    if '#' in line:
        line_parts = line.split('#')
        line_parts[1] = custom_word + line_parts[1]  # 添加自定义词
        processed_content += '#'.join(line_parts) + '\n'
    else:
        processed_content += line + '\n'

# 腾讯云COS的配置和客户端初始化
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
cos_client = CosS3Client(config)

# 上传文件：注意'addressesapi.txt'是文件的名称，你可以根据需要改变
cos_client.put_object(
    Bucket=bucket,
    Body=processed_content.encode('utf-8'),
    Key='addressesapi.txt',
)

print("文件更新成功！")
#r = requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage', json={"chat_id": telegram_chat_id, "text": "文件更新成功！"})
