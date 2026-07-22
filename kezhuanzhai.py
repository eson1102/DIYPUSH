import akshare as ak
import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta

# ==================== 配置区 ====================
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
FUTURE_DAYS = 7

# ==================== 核心函数 ====================

def get_calendar_data():
    """获取可转债申购和上市数据"""
    try:
        print("📊 从 bond_zh_cov 获取可转债数据...")
        bond_df = ak.bond_zh_cov()
        
        print(f"📋 原始数据列：{bond_df.columns.tolist()}")
        print(f"📊 总数据量：{len(bond_df)} 条")
        
        # 日期相关的列名映射
        date_col_mappings = {
            '申购日期': '申购日',
            '上市时间': '上市日', 
            '上市日期': '上市日',
            '发行日期': '发行日',
            'list_date': '上市日',
            'apply_date': '申购日'
        }
        
        actual_date_cols = {}
        for col in bond_df.columns:
            if col in date_col_mappings:
                actual_date_cols[col] = date_col_mappings[col]
        
        if not actual_date_cols:
            print("❌ 未找到日期相关列，打印所有列名：")
            print(bond_df.columns.tolist())
            return pd.DataFrame()
        
        print(f"✅ 找到日期列：{actual_date_cols}")
        
        today = datetime.now().date()
        future = today + timedelta(days=FUTURE_DAYS)
        
        result_dfs = []
        
        for orig_col, new_col in actual_date_cols.items():
            temp_df = bond_df.copy()
            temp_df[orig_col] = pd.to_datetime(temp_df[orig_col], errors='coerce')
            
            mask = (temp_df[orig_col].dt.date >= today) & (temp_df[orig_col].dt.date <= future)
            filtered = temp_df[mask].copy()
            
            if not filtered.empty:
                filtered.rename(columns={orig_col: '日期'}, inplace=True)
                
                if '申购' in orig_col:
                    filtered['类型'] = '申购'
                elif '上市' in orig_col or 'list' in orig_col.lower():
                    filtered['类型'] = '上市'
                else:
                    filtered['类型'] = '其他'
                
                # 保留关键列
                keep_cols = []
                for col in filtered.columns:
                    if '代码' in col or 'code' in col.lower():
                        keep_cols.append(col)
                    elif '名称' in col or '简称' in col or 'name' in col.lower():
                        keep_cols.append(col)
                    elif col == '日期' or col == '类型':
                        keep_cols.append(col)
                
                final_cols = list(dict.fromkeys(keep_cols))
                if '日期' not in final_cols:
                    final_cols.append('日期')
                if '类型' not in final_cols:
                    final_cols.append('类型')
                
                filtered = filtered[final_cols]
                result_dfs.append(filtered)
        
        if result_dfs:
            result_df = pd.concat(result_dfs, ignore_index=True)
            result_df = result_df.sort_values('日期')
            print(f"✅ 筛选出 {len(result_df)} 条未来 {FUTURE_DAYS} 天内的数据")
            return result_df
        else:
            print("ℹ️ 未来 7 天内没有可转债动态")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"❌ 获取数据出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def format_text_message(df):
    """格式化纯文本消息"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
        df = df.sort_values('日期')
    
    type_counts = df['类型'].value_counts()
    
    msg = f"【可转债日历】{today}\n"
    msg += "-" * 40 + "\n"
    msg += f"未来 {FUTURE_DAYS} 天内共有 {len(df)} 只可转债有动态\n"
    
    stat_parts = []
    for t in ['申购', '上市']:
        if t in type_counts:
            stat_parts.append(f"{t} {type_counts[t]} 只")
    if stat_parts:
        msg += "（" + "，".join(stat_parts) + "）\n"
    msg += "\n"
    
    for event_type in ['申购', '上市', '其他']:
        type_df = df[df['类型'] == event_type]
        if not type_df.empty:
            emoji = "🎯" if event_type == '申购' else "📈" if event_type == '上市' else "📋"
            msg += f"{emoji} {event_type}：\n"
            for _, row in type_df.iterrows():
                code = 'N/A'
                name = 'N/A'
                
                for col in row.index:
                    if '代码' in col or 'code' in col.lower():
                        code = row[col]
                    elif '名称' in col or 'name' in col.lower() or '简称' in col:
                        name = row[col]
                
                date = row.get('日期', 'N/A')
                msg += f"  {name}（{code}）{date}\n"
            msg += "\n"
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_events = df[df['日期'] == today_str]
    if not today_events.empty:
        msg += "🔔 今日提醒：\n"
        for _, row in today_events.iterrows():
            name = 'N/A'
            for col in row.index:
                if '名称' in col or 'name' in col.lower() or '简称' in col:
                    name = row[col]
            event_type = row.get('类型', '')
            msg += f"  ⚠️ {name} 今日 {event_type}！\n"
        msg += "\n"
    
    msg += "-" * 40 + "\n"
    msg += "数据来源：东方财富 | 仅供参考，投资需谨慎"
    
    return msg


def send_to_wechat(message):
    """发送消息到企业微信机器人"""
    if not WEBHOOK_URL:
        print("❌ 未设置 WEBHOOK_URL 环境变量")
        return False
    
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": message
        }
    }
    
    try:
        response = requests.post(WEBHOOK_URL, headers=headers, json=data, timeout=30)
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
    
    # ========== 没有数据就不推送 ==========
    if df.empty:
        print("ℹ️ 未来 7 天内没有可转债动态，跳过推送")
        print("✅ 任务结束（无数据，不发送消息）")
        return True
    
    print("\n📋 筛选结果：")
    print(df.to_string())
    
    message = format_text_message(df)
    
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
