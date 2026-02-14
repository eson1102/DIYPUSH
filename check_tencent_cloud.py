# -*- coding: utf-8 -*-
import os
import json
import requests
import logging
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.lighthouse.v20200324 import lighthouse_client, models

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# 从 GitHub Secrets 读取环境变量
ACCOUNTS = json.loads(os.environ.get('ACCOUNT_CONFIG', '[]'))
WECOM_WEBHOOK = os.environ.get('WECOM_WEBHOOK', '')
REGIONS = ["ap-shanghai", "ap-guangzhou", "ap-beijing", "ap-hongkong", "ap-singapore"]
THRESHOLD_DAYS = 150

def send_wecom_notification(content):
    if not WECOM_WEBHOOK:
        logging.error("❌ 错误：环境变量 WECOM_WEBHOOK 为空，请检查 Github Secrets 配置！")
        return
        
    payload = {"msgtype": "text", "text": {"content": content}}
    try:
        res = requests.post(WECOM_WEBHOOK, json=payload, timeout=15)
        # 这一行非常重要，可以告诉你企业微信服务器为什么拒绝你
        logging.info(f"🚀 企业微信返回结果: {res.text}") 
        
        if res.json().get("errcode") != 0:
            logging.error(f"❌ 企业微信报错：{res.json().get('errmsg')}")
    except Exception as e:
        logging.error(f"❌ 网络请求异常: {e}")

def fetch_region_instances(acc, region):
    results = []
    try:
        cred = credential.Credential(acc['sid'], acc['skey'])
        client = lighthouse_client.LighthouseClient(cred, region)
        req = models.DescribeInstancesRequest()
        resp = client.DescribeInstances(req)
        for ins in resp.InstanceSet:
            expired_dt = datetime.strptime(ins.ExpiredTime, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            remaining_days = (expired_dt - datetime.now(timezone.utc)).days
            results.append({
                "name": ins.InstanceName, "account": acc['name'], "region": region,
                "ip": ins.PublicAddresses[0] if ins.PublicAddresses else "内网",
                "expiry": ins.ExpiredTime[:10], "days": remaining_days
            })
    except Exception as e:
        logging.error(f"Error [{acc['name']}-{region}]: {e}")
    return results

if __name__ == "__main__":
    all_instances = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_region_instances, acc, reg) for acc in ACCOUNTS for reg in REGIONS]
        for future in as_completed(futures):
            res = future.result()
            if res: all_instances.extend(res)

    all_instances.sort(key=lambda x: x['days'])
    warning_list = [i for i in all_instances if i['days'] <= THRESHOLD_DAYS]

    now_str = datetime.now().strftime("%m-%d %H:%M")
    report = f"🔔【腾讯云巡检报告】\n⏰ 检查时间：{now_str}\n📊 实例总数：{len(all_instances)} 台\n====================\n\n"
    
    if warning_list:
        report += f"🔴【重点预警 ({len(warning_list)})】\n"
        for w in warning_list:
            report += f"⚠️ {w['account']} | {w['name']}\n   剩余：{w['days']}天 (至{w['expiry']})\n\n"
    
    report += "📝【全量清单】\n"
    for i in all_instances:
        icon = "❗" if i['days'] <= THRESHOLD_DAYS else "🔹"
        report += f"{icon}[{i['days']:3d}天] {i['account']}-{i['name']}\n"

    print(report)
    send_wecom_notification(report)
