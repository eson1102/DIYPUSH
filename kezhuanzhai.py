import akshare as ak
import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta

# ==================== 配置区 ====================
# 从环境变量读取 Webhook URL（更安全）
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
FUTURE_DAYS = 7

# ==================== 核心函数 ====================

def get_calendar_data():
    """获取可转债申购和上市数据"""
    try:
        today_str = datetime.now().strftime('%Y%m%d')
        future_str = (datetime.now() + timedelta(days=FUTURE_DAYS)).strftime('%Y%m%d')
        
        apply_df = None
        list_df = None
        
        # 获取申购日历
        try:
            apply_df = ak.bond_cb_apply(start_date=today_str, end_date=future_str)
            print(f"✅ 获取申购数据成功，共 {len(apply_df)} 条")
        except Exception as e:
            print(f"⚠️ 获取申购数据失败: {e}")
        
        # 获取上市日历
        try:
            list_df = ak.bond_cb_list(start_date=today_str, end_date=future_str)
            print(f"✅ 获取上市数据成功，共 {len(list_df)} 条")
        except Exception as e:
            print(f"⚠️ 获取上市数据失败: {e}")
        
        # 备用方案
        if apply_df is None and list_df is None:
            print("🔄 使用备用方案：从 bond_zh_cov 获取全量数据筛选")
            bond_df = ak.bond_zh_cov()
            
            date_cols = ['申购日期', '上市时间', '发行日期']
            for col in date_cols:
                if col in bond_df.columns:
                    bond_df[col] = pd.to_datetime(bond_df[col], errors='coerce').dt.date
            
            today = datetime.now().date()
            future = today + timedelta(days=FUTURE_DAYS)
            
            mask = pd.Series([False] * len(bond_df))
            for col in date_cols:
                if col in bond_df.columns:
                    mask = mask | ((bond_df[col] >= today) & (bond_df[col] <= future))
            
            future_df = bond_df[mask].copy()
            
            col_map = {
                '申购日期': '申购日',
                '上市时间': '上市日',
                '发行日期': '发行日'
            }
            future_df.rename(columns=col_map, inplace=True)
            
            # 添加类型列
            if '申购日' in future_df.columns:
                future_df['类型'] = future_df['申购日'].apply(lambda x: '申购' if pd.notna(x) else '')
            elif '上市日' in future_df.columns:
                future_df['类型'] = future_df['上市日'].apply(lambda x: '上市' if pd.notna(x) else '')
            
            return future_df
        
        # 合并数据
        result_df = pd.DataFrame()
        
        if apply_df is not None and len(apply_df) > 0:
            apply_df['类型'] = '申购'
            col_map = {}
            for col in apply_df.columns:
                if '代码' in col:
                    col_map[col] = '代码'
                elif '名称' in col or '简称' in col:
                    col_map[col] = '名称'
                elif '日期' in col:
                    col_map[col] = '日期'
            apply_df.rename(columns=col_map, inplace=True)
            result_df = pd.concat([result_df, apply_df], ignore_index=True)
        
        if list_df is not None and len(list_df) > 0:
            list_df['类型'] = '上市'
            col_map = {}
            for col in list_df.columns:
                if '代码' in col:
                    col_map[col] = '代码'
                elif '名称' in col or '简称' in col:
                    col_map[col] = '名称'
                elif '日期' in col:
                    col_map[col] = '日期'
            list_df.rename(columns=col_map, inplace=True)
            result_df = pd.concat([result_df, list_df], ignore_index=True)
        
        return result_df
    
    except Exception as e:
        print(f"❌ 获取数据出错: {e}")
        return pd.DataFrame()


def format_message(df):
    """格式化企业微信消息"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if df.empty:
        return f"""## 📅 可转债日历 ({today})
        
暂无未来 {FUTURE_DAYS} 天内的可转债申购或上市信息。

---
> 📊 数据来源：东方财富"""
    
    if '日期' in df.columns:
        df = df.sort_values('日期')
    
    msg = f"## 📅 可转债日历 ({today})\n"
    msg += f"> 未来 {FUTURE_DAYS} 天内共有 **{len(df)}** 只可转债有动态\n\n"
    
    for event_type in ['申购', '上市']:
        type_df = df[df['类型'] == event_type]
        if not type_df.empty:
            msg += f"### 🎯 {event_type}\n"
            for _, row in type_df.iterrows():
                code = row.get('代码', 'N/A')
                name = row.get('名称', 'N/A')
                date = row.get('日期', 'N/A')
                if hasattr(date, 'strftime'):
                    date = date.strftime('%Y-%m-%d')
                elif isinstance(date, pd.Timestamp):
                    date = date.strftime('%Y-%m-%d')
                msg += f"> • **{name}** ({code}) - {date}\n"
            msg += "\n"
    
    today_str = today
    today_events = df[df['日期'].astype(str).str.contains(today_str)]
    if not today_events.empty:
        msg += "### 🔔 今日提醒\n"
        for _, row in today_events.iterrows():
            msg += f"> ⚠️ **{row.get('名称', '')}** 今日 {row.get('类型', '')}！\n"
        msg += "\n"
    
    msg += "---\n"
    msg += "> 📊 数据来源：东方财富 | 仅供参考，投资需谨慎"
    
    return msg


def send_to_wechat(message):
    """发送消息到企业微信机器人"""
    if not WEBHOOK_URL:
        print("❌ 未设置 WEBHOOK_URL 环境变量")
        return False
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": message
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(data), timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                print("✅ 消息发送成功")
                return True
            else:
                print(f"❌ 发送失败: {result}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def main():
    print(f"🚀 开始运行可转债日历推送任务...")
    print(f"📅 查询范围：未来 {FUTURE_DAYS} 天")
    print(f"⏰ 当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    df = get_calendar_data()
    message = format_message(df)
    
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50 + "\n")
    
    success = send_to_wechat(message)
    
    if success:
        print("🎉 任务完成！")
    else:
        print("⚠️ 任务部分失败，请检查日志")
    
    return success


if __name__ == "__main__":
    main()
