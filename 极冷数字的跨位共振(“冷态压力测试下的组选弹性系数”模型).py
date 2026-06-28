import pandas as pd
import numpy as np
import unicodedata

# ==================== 显示对齐工具函数 ====================
def get_display_width(text):
    """精确计算字符串在控制台中的实际显示宽度（兼容中文/Emoji/全角符号）"""
    width = 0
    for char in str(text):
        if unicodedata.east_asian_width(char) in ('W', 'F'):
            width += 2
        else:
            width += 1
    return width

def pad_to_width(text, target_width, align='center'):
    """根据实际显示宽度进行精准空格填充"""
    text = str(text)
    current_width = get_display_width(text)
    padding = max(0, target_width - current_width)
    
    if align == 'left':
        return text + ' ' * padding
    elif align == 'right':
        return ' ' * padding + text
    else:  # center
        left_pad = padding // 2
        right_pad = padding - left_pad
        return ' ' * left_pad + text + ' ' * right_pad

# ==================== 核心分析函数 ====================
def analyze_dual_window_elasticity(file_path, base_threshold=55, post_window=8):
    """双窗口弹性分析法（含完美对齐输出）"""
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ 读取CSV失败: {e}")
        return

    if '开奖号码' not in df.columns:
        print("❌ 错误：CSV中未找到 '开奖号码' 列")
        return

    # 1. 数据预处理
    def parse_digits(x):
        s = str(x).strip()
        digits = [int(i) for i in s if i.isdigit()]
        return pd.Series(digits[:3])

    df[['百位', '十位', '个位']] = df['开奖号码'].apply(parse_digits)
    df.dropna(subset=['百位', '十位', '个位'], inplace=True)
    df[['百位', '十位', '个位']] = df[['百位', '十位', '个位']].astype(int)
    df.reset_index(drop=True, inplace=True)

    positions = ['百位', '十位', '个位']
    THEORETICAL_GROUP_RATE = 1 - (0.9 ** 3)
    total_rows = len(df)

    # 2. 预计算矩阵
    print("⏳ 正在预计算遗漏矩阵与组选命中标记...")
    current_miss = {f"{d}_{p}": 0 for d in range(10) for p in positions}
    miss_records, group_hit_records = [], []
    
    for idx, row in df.iterrows():
        hit_row = {}
        for d in range(10):
            hit_row[d] = (row['百位'] == d) or (row['十位'] == d) or (row['个位'] == d)
            for p in positions:
                key = f"{d}_{p}"
                current_miss[key] = 0 if row[p] == d else current_miss[key] + 1
        miss_records.append(current_miss.copy())
        group_hit_records.append(hit_row)
        
    direct_miss_df = pd.DataFrame(miss_records)
    group_hit_df = pd.DataFrame(group_hit_records)
    print("✅ 预计算完成，开始双窗口扫描...")

    # 3. 双窗口扫描
    results = []
    for d in range(10):
        for p in positions:
            col_name = f"{d}_{p}"
            trigger_indices = direct_miss_df.index[direct_miss_df[col_name] == base_threshold + 1].tolist()
            
            for t_idx in trigger_indices:
                post_end = t_idx + post_window
                if post_end > total_rows:
                    continue
                
                pre_start = max(0, t_idx - base_threshold)
                pre_hits = group_hit_df.iloc[pre_start:t_idx][d].sum()
                pre_periods = t_idx - pre_start
                pre_rate = pre_hits / pre_periods if pre_periods > 0 else 0
                
                post_hits = group_hit_df.iloc[t_idx:post_end][d].sum()
                post_rate = post_hits / post_window
                
                if pre_rate > 0:
                    elasticity = post_rate / pre_rate
                elif post_rate > 0:
                    elasticity = float('inf')
                else:
                    elasticity = 0.0
                
                if elasticity == float('inf'):
                    tag = "🚀 触底反弹"
                elif elasticity >= 1.5:
                    tag = "🔥 加速回补"
                elif elasticity <= 0.5:
                    tag = "❄️ 加速冰封"
                elif post_rate >= THEORETICAL_GROUP_RATE * 1.3:
                    tag = "➖ 高位维持"
                elif post_rate <= THEORETICAL_GROUP_RATE * 0.7:
                    tag = "➖ 低位维持"
                else:
                    tag = "➖ 常态波动"

                results.append({
                    '触发期号': str(df.at[t_idx, '期号']) if '期号' in df.columns else str(t_idx),
                    '数字': str(d),
                    '位置': p,
                    '前55期组选率': f"{pre_rate:.2%}",
                    f'后{post_window}期组选率': f"{post_rate:.2%}",
                    '弹性系数': "∞" if elasticity == float('inf') else f"{elasticity:.2f}",
                    '演化特征': tag
                })

    # 4. 完美对齐输出
    print("\n" + "=" * 90)
    if not results:
        print(f"⚠️ 未找到符合条件的双窗口完整样本。")
    else:
        res_df = pd.DataFrame(results)
        print(f"📊 双窗口弹性分析完成！共捕获 {len(res_df)} 个有效样本")
        print("-" * 90)
        
        # 定义列配置：(列名, 目标显示宽度, 对齐方式)
        columns_config = [
            ('触发期号', 12, 'center'),
            ('数字',     6, 'center'),
            ('位置',     6, 'center'),
            ('前55期组选率', 14, 'right'),
            (f'后{post_window}期组选率', 14, 'right'),
            ('弹性系数', 10, 'right'),
            ('演化特征', 16, 'left')
        ]
        
        # 打印表头
        header_line = "".join([pad_to_width(name, width, align) for name, width, align in columns_config])
        print(header_line)
        print("-" * 90)
        
        # 打印数据行
        for _, row in res_df.iterrows():
            data_line = "".join([
                pad_to_width(row[col], width, align) 
                for col, width, align in columns_config
            ])
            print(data_line)
        
        # 汇总统计
        print("\n" + "=" * 90)
        print("📈 【演化特征分布汇总】")
        tag_counts = res_df['演化特征'].value_counts()
        for tag, cnt in tag_counts.items():
            print(f"   {tag}: {cnt} 次 ({cnt/len(res_df):.1%})")
            
        valid_elasticity = res_df[res_df['弹性系数'] != "∞"]['弹性系数'].astype(float)
        if not valid_elasticity.empty:
            print(f"\n   🎯 平均弹性系数: {valid_elasticity.mean():.2f} (>1代表极冷后组选变活跃, <1代表变沉寂)")
        print("=" * 90)


# === ✅ 执行入口 ===
if __name__ == "__main__":
    file_path = "allpaisan.csv"
    analyze_dual_window_elasticity(file_path, base_threshold=62, post_window=20)