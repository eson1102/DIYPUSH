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
response = requests.get("https://url.v1.mk/sub?&url=https%3A%2F%2Fsub.xfltd.cfd%2Fapi%2Fv1%2Fclient%2Fsubscribe%3Ftoken%3D2e9d42c620338cff80d3fd86eca0f31a%7Chttps%3A%2F%2Fdy2.godsky.top%2Fapi%2Fv1%2Fclient%2Fsubscribe%3Ftoken%3D168ab63f0f511e5e244e41aa4db54010%7Chttp%3A%2F%2F101.200.14.80%3A3325%2Fapi%2Fv1%2Fclient%2Fsubscribe%3Ftoken%3Dcdaea491048645724ba1bd9b681ec3ec&target=clash&config=https%3A%2F%2Fraw.githubusercontent.com%2Fcmliu%2FACL4SSR%2Fmain%2FClash%2Fconfig%2FACL4SSR_Online_MultiCountry_CF.ini&emoji=true&append_type=true&append_info=true&scv=true&udp=false&list=false&sort=false&fdn=true&insert=false",timeout=200)
file_content = response.content
print(response)
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
