import akshare as ak
import pandas as pd
import requests
import os
from datetime import datetime, timedelta, timezone

# ==================== 配置区 ====================
WECOM_WEBHOOK = os.environ.get('WECOM_WEBHOOK', '')

# 强制使用北京时间，避免 GitHub Actions 默认 UTC 导致日期筛选错误
BJT = timezone(timedelta(hours=8))


def get_apply_data():
    """获取今明两日可申购的可转债（北京时间基准）"""
    try:
        print("📊 从 bond_zh_cov 获取可转债数据...")
        bond_df = ak.bond_zh_cov()

        # 接口固定返回“申购日期”列，直接使用即可[citation:1]
        if '申购日期' not in bond_df.columns:
            print(f"❌ 未找到申购日期列，现有列：{bond_df.columns.tolist()}")
            return pd.DataFrame()

        # 统一处理日期
        bond_df['申购日期'] = pd.to_datetime(bond_df['申购日期'], errors='coerce')

        today = datetime.now(BJT).date()
        tomorrow = today + timedelta(days=1)

        # 筛选今明两日
        mask = bond_df['申购日期'].dt.date.isin([today, tomorrow])
        filtered = bond_df[mask].copy()

        if filtered.empty:
            print("ℹ️ 今明两日没有可申购的可转债")
            return pd.DataFrame()

        # 标记标签
        filtered['日期标签'] = filtered['申购日期'].dt.date.apply(
            lambda x: '🔥 今日申购' if x == today else '📅 明日申购'
        )

        # 只保留需要的列（接口列名固定，无需模糊匹配）
        result = filtered[['债券代码', '债券简称', '申购日期', '日期标签']].copy()
        result.rename(columns={'申购日期': '日期'}, inplace=True)
        result = result.sort_values('日期')

        print(f"✅ 找到 {len(result)} 只今明两日可申购的可转债")
        return result

    except Exception as e:
        print(f"❌ 获取数据出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def format_text_message(df):
    """格式化纯文本消息"""
    now = datetime.now(BJT)
    now_str = now.strftime('%Y-%m-%d %H:%M')
    today = now.date()
    tomorrow = today + timedelta(days=1)

    # 统一转换为 date 比较，避免 str/date 混用
    df['日期'] = pd.to_datetime(df['日期']).dt.date
    today_count = len(df[df['日期'] == today])
    tomorrow_count = len(df[df['日期'] == tomorrow])

    msg = f"【可转债申购提醒】{now_str}\n"
    msg += "-" * 40 + "\n"

    stat_parts = []
    if today_count > 0:
        stat_parts.append(f"今日 {today_count} 只")
    if tomorrow_count > 0:
        stat_parts.append(f"明日 {tomorrow_count} 只")
    msg += "今明两日共有 " + "，".join(stat_parts) + " 可转债开放申购\n\n"

    for date_label in ['🔥 今日申购', '📅 明日申购']:
        type_df = df[df['日期标签'] == date_label]
        if not type_df.empty:
            msg += f"{date_label}：\n"
            for _, row in type_df.iterrows():
                # 接口固定列名：债券代码、债券简称
                msg += f"  {row['债券简称']}（{row['债券代码']}）{row['日期']}\n"
            msg += "\n"

    msg += "-" * 40 + "\n"
    msg += "💡 记得在交易时间内申购\n"
    msg += "📊 数据来源：东方财富 | 仅供参考"
    return msg


def send_to_wechat(message):
    """发送消息到企业微信机器人"""
    if not WECOM_WEBHOOK:
        print("❌ 未设置 WECOM_WEBHOOK 环境变量")
        return False

    headers = {'Content-Type': 'application/json'}
    data = {"msgtype": "text", "text": {"content": message}}

    try:
        response = requests.post(WECOM_WEBHOOK, headers=headers, json=data, timeout=30)
        if response.status_code == 200 and response.json().get('errcode') == 0:
            print("✅ 消息发送成功")
            return True
        print(f"❌ 发送失败: {response.status_code} {response.text}")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def main():
    print(f"🚀 开始运行可转债申购提醒任务...")
    print(f"⏰ 当前北京时间：{datetime.now(BJT).strftime('%Y-%m-%d %H:%M:%S')}")

    df = get_apply_data()

    if df.empty:
        print("ℹ️ 今明两日没有可申购的可转债，跳过推送")
        return True

    print("\n📋 筛选结果：")
    print(df.to_string())

    message = format_text_message(df)
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50 + "\n")

    success = send_to_wechat(message)
    print("🎉 任务完成！" if success else "⚠️ 任务部分失败，请检查日志")
    return success


if __name__ == "__main__":
    main()
