import akshare as ak
import pandas as pd
import requests
import json
import os
from datetime import datetime, timedelta

# ==================== 配置区 ====================
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

# ==================== 核心函数 ====================

def get_apply_data():
    """获取今明两日可申购的可转债"""
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
        tomorrow = today + timedelta(days=1)
        
        result_dfs = []
        
        for orig_col, new_col in actual_date_cols.items():
            # 只处理"申购"相关的列
            if '申购' not in orig_col and 'apply' not in orig_col.lower():
                continue
                
            temp_df = bond_df.copy()
            temp_df[orig_col] = pd.to_datetime(temp_df[orig_col], errors='coerce')
            
            # ========== 关键改动：筛选今天和明天 ==========
            mask = (temp_df[orig_col].dt.date == today) | (temp_df[orig_col].dt.date == tomorrow)
            filtered = temp_df[mask].copy()
            
            if not filtered.empty:
                filtered.rename(columns={orig_col: '日期'}, inplace=True)
                
                # 标记是今天还是明天
                filtered['日期标签'] = filtered['日期'].apply(
                    lambda x: '🔥 今日申购' if x.date() == today else '📅 明日申购'
                )
                
                # 保留关键列
                keep_cols = []
                for col in filtered.columns:
                    if '代码' in col or 'code' in col.lower():
                        keep_cols.append(col)
                    elif '名称' in col or '简称' in col or 'name' in col.lower():
                        keep_cols.append(col)
                    elif col == '日期' or col == '日期标签':
                        keep_cols.append(col)
                
                final_cols = list(dict.fromkeys(keep_cols))
                if '日期' not in final_cols:
                    final_cols.append('日期')
                if '日期标签' not in final_cols:
                    final_cols.append('日期标签')
                
                filtered = filtered[final_cols]
                result_dfs.append(filtered)
        
        if result_dfs:
            result_df = pd.concat(result_dfs, ignore_index=True)
            result_df = result_df.sort_values('日期')
            print(f"✅ 找到 {len(result_df)} 只今明两日可申购的可转债")
            return result_df
        else:
            print("ℹ️ 今明两日没有可申购的可转债")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"❌ 获取数据出错: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()


def format_text_message(df):
    """格式化纯文本消息"""
    today = datetime.now().strftime('%Y-%m-%d')
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    if '日期' in df.columns:
        df['日期'] = pd.to_datetime(df['日期']).dt.strftime('%Y-%m-%d')
    
    # 统计今天和明天的数量
    today_count = len(df[df['日期'] == today])
    tomorrow_count = len(df[df['日期'] == tomorrow])
    
    msg = f"【可转债申购提醒】{today}\n"
    msg += "-" * 40 + "\n"
    
    stat_parts = []
    if today_count > 0:
        stat_parts.append(f"今日 {today_count} 只")
    if tomorrow_count > 0:
        stat_parts.append(f"明日 {tomorrow_count} 只")
    msg += "今明两日共有 " + "，".join(stat_parts) + " 可转债开放申购\n\n"
    
    # 先显示今日，再显示明日
    for date_label in ['🔥 今日申购', '📅 明日申购']:
        type_df = df[df['日期标签'] == date_label]
        if not type_df.empty:
            msg += f"{date_label}：\n"
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
    
    if len(df) == 0:
        msg += "今明两日暂无申购\n\n"
    
    msg += "-" * 40 + "\n"
    msg += "💡 记得在交易时间内申购\n"
    msg += "📊 数据来源：东方财富 | 仅供参考"
    
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
    print(f"🚀 开始运行可转债申购提醒任务...")
    print(f"⏰ 当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    df = get_apply_data()
    
    # 没有数据就不推送
    if df.empty:
        print("ℹ️ 今明两日没有可申购的可转债，跳过推送")
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
