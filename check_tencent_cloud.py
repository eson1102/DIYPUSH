# -*- coding: utf-8 -*-
import os
import json
import requests
import logging
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.lighthouse.v20200324 import lighthouse_client, models

# 日志配置
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# ================= 配置区 =================
# 从 GitHub Secrets 读取
ACCOUNTS = json.loads(os.environ.get('ACCOUNT_CONFIG', '[]'))
WECOM_WEBHOOK = os.environ.get('WECOM_WEBHOOK', '')

# 地域列表
REGIONS = ["ap-shanghai", "ap-guangzhou", "ap-beijing", "ap-hongkong", "ap-singapore"]
# 预警阈值
THRESHOLD_DAYS = 150
# 并发线程数
MAX_WORKERS = 10 
# ==========================================

def send_wecom_notification(content):
    if not WECOM_WEBHOOK:
        logging.error("未配置 WECOM_WEBHOOK")
        return
    payload = {"msgtype": "text", "text": {"content": content}}
    try:
        res = requests.post(WECOM_WEBHOOK, json=payload, timeout=15)
        logging.info(f"推送响应: {res.text}")
    except Exception as e:
        logging.error(f"推送失败: {e}")

def fetch_region_instances(acc, region):
    results = []
    try:
        cred = credential.Credential(acc['sid'], acc['skey'])
        client = lighthouse_client.LighthouseClient(cred, region)
        req = models.DescribeInstancesRequest()
        req.Limit = 100
        
        resp = client.DescribeInstances(req)
        for ins in resp.InstanceSet:
            # 解析过期时间并计算剩余天数
            expired_dt = datetime.strptime(ins.ExpiredTime, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            remaining_days = (expired_dt - datetime.now(timezone.utc)).days
            
            results.append({
                "name": ins.InstanceName,
                "account": acc['name'],
                "region": region,
                "ip": ins.PublicAddresses[0] if ins.PublicAddresses else "内网",
                "expiry": ins.ExpiredTime[:10],
                "days": remaining_days
            })
    except TencentCloudSDKException as e:
        if "AuthFailure" not in str(e):
            logging.error(f"查询出错 [{acc['name']}-{region}]: {e.code}")
    except Exception as e:
        logging.error(f"未知错误 [{acc['name']}-{region}]: {e}")
    return results

def main():
    if not ACCOUNTS:
        logging.error("未找到账号配置，请检查 GitHub Secrets 中的 ACCOUNT_CONFIG")
        return

    all_instances = []
    logging.info(f"🚀 开始多线程巡检...")

    # 使用线程池并发查询各账号各地域
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_region_instances, acc, reg) for acc in ACCOUNTS for reg in REGIONS]
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_instances.extend(res)

    # 数据处理：按剩余天数排序
    all_instances.sort(key=lambda x: x['days'])
    warning_list = [i for i in all_instances if i['days'] <= THRESHOLD_DAYS]

    # --- 报告排版 ---
    # 获取北京时间
    tz_bj = timezone(timedelta(hours=8))
    now_str = datetime.now(tz_bj).strftime("%m-%d %H:%M")
    
    report =  f"🔔【腾讯云轻量巡检报告】\n"
    report += f"⏰ 检查时间：{now_str}\n"
    report += f"📊 实例总数：{len(all_instances)} 台\n"
    report += f"====================\n\n"

    if warning_list:
        report += f"🔴【重点预警 ({len(warning_list)})】\n"
        for w in warning_list:
            report += f"⚠️ 账号：{w['account']} \n"
            report += f"   实例：{w['name']} | 剩余：{w['days']}天\n"
            report += f"   到期：{w['expiry']} | IP：{w['ip']}\n\n"
        report += f"====================\n\n"
    else:
        report += f"🟢【预警状态】：一切正常\n\n"

    report += f"📝【全量清单】\n"
    report += f"== 按到期时间排序 ==\n\n"
    for i in all_instances:
        icon = "❗" if i['days'] <= THRESHOLD_DAYS else "🔹"
        report += f"{icon}[{i['days']:3d}天] {i['account']} ({i['name']})\n\n"

    report += f"----------------------------\n"
    report += f"💡 请及时处理即将到期的实例。"

    # 输出到控制台并发送通知
    print(report)
    send_wecom_notification(report)

if __name__ == "__main__":
    main()
