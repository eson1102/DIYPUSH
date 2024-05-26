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
response = requests.get("https://sub.xeton.dev/sub?target=clash&new_name=true&url=https%3A%2F%2Fwww.02er.com%2Fapi%2Fv1%2Fclient%2Fsubscribe%3Ftoken%3D4c872125ce244d4c19f3778ebece5375%26flag%3Dclash%7Chttps%3A%2F%2Fcf.7854128.xyz%2Fapi%2Fv1%2Fclient%2Fsubscribe%3Ftoken%3D84b9da24f9b591ca368608cf8339829b&insert=false&config=https%3A%2F%2Fraw.githubusercontent.com%2FACL4SSR%2FACL4SSR%2Fmaster%2FClash%2Fconfig%2FACL4SSR_Online_Mini_MultiCountry.ini&emoji=true&list=false&tfo=false&scv=false&fdn=false&sort=false",timeout=20)
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
