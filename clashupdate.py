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
response = requests.get("https://url.v1.mk/sub?target=clash&url=https%3A%2F%2Fgateway.51tu.lol%2Fgateway%2Ftaoqitu%3Ftoken%3D416913abef74f0f74959f31c4599f91f%7Chttps%3A%2F%2Fmusic.easygourl.xyz%2Flink%2FMcmsZz3oJKPy4b9TdWKO78216LAgj4DQ%3Fconfig%3Dall%7Chttps%3A%2F%2Fsub.xf.edu.kg%2Fapi%2Fv1%2Fclient%2Fsubscribe%3Ftoken%3Dea16d8b2c8a3d1a4a1182edc19d19571%7C&insert=false&config=https://github.com/eson1102/rules/blob/main/Mini_MultiCountry.ini&emoji=true&list=false&xudp=false&udp=false&tfo=false&expand=true&scv=false&fdn=false&new_name=true",timeout=20)
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
