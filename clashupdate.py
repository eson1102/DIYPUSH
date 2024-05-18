import requests
from qcloud_cos import CosConfig, CosS3Client
import os

# 腾讯云信息
secret_id = os.environ["SECRET_ID"]      # 替换为您的 SecretId
secret_key = os.environ["SECRET_KEY"]    # 替换为您的 SecretKey
region = os.environ["REGION"]            # 替换为桶的所在地域
bucket = os.environ["BUCKET"]       # 替换为您的桶名称
telegram_token = os.environ["BOT_TOKEN"]
telegram_chat_id = os.environ["CHAT_ID"]

# 使用请求库获取ini文件的内容
response = requests.get("https://api.tsutsu.one/sub?target=clash&url=https://music.easygourl.xyz/link/McmsZz3oJKPy4b9TdWKO78216LAgj4DQ?config=all|https://gateway.51tu.lol/gateway/sb?token=416913abef74f0f74959f31c4599f91f|https://subscribe.xsus.net.co/api/v1/client/subscribe?token=0ae03574013e75ca024d91c336ae02a2|https://sub.xf.edu.kg/api/v1/client/subscribe?token=ea16d8b2c8a3d1a4a1182edc19d19571&insert=false&config=https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/config/ACL4SSR_Online_Full_NoAuto.ini&emoji=true&list=false&xudp=false&udp=false&tfo=false&expand=true&scv=false&fdn=false&new_name=true",timeout=20)
file_content = response.content

# 腾讯云COS的配置和客户端初始化
config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
cos_client = CosS3Client(config)

# 上传文件：注意'ACL4SSR_Online_Full_NoAuto.ini'是文件的名称，你可以根据需要改变
cos_client.put_object(
    Bucket=bucket,
    Body=file_content,
    Key='1.yaml',
)

print("clash文件更新成功！")
r = requests.post(f'https://api.telegram.org/bot{telegram_token}/sendMessage', json={"chat_id": telegram_chat_id, "text": f"clash文件更新成功！"})
