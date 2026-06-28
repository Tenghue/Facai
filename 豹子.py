# 文件名：pl3_baozi_leakage_advanced.py
import pandas as pd
import numpy as np
import sys
import os

def guess_column_names(df):
    period_candidates = ['period', '期号', 'date', 'time', '期次', '开奖期号']
    number_candidates = ['number', '开奖号码', 'code', 'num', '号码', '三位数']
    period_col = None
    number_col = None
    for col in df.columns:
        col_lower = col.lower()
        if any(cand in col_lower for cand in period_candidates):
            period_col = col
        if any(cand in col_lower for cand in number_candidates):
            number_col = col
    return period_col, number_col

def analyze_all_digits(csv_path, period_col=None, number_col=None):
    """原有全部统计功能"""
    if not os.path.exists(csv_path):
        print(f"❌ 错误：文件不存在！请检查路径：{csv_path}")
        return

    encodings = ['utf-8', 'gbk', 'gb2312']
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(csv_path, dtype=str, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        print("❌ 无法用 utf-8/gbk/gb2312 编码读取文件，请手动指定编码。")
        return

    print(f"✅ 加载 {len(df)} 行数据（编码：{enc}）")

    # 自动猜列名
    if not period_col or not number_col:
        p, n = guess_column_names(df)
        if p and n:
            period_col, number_col = p, n
            print(f"🔍 自动识别：期号='{period_col}'，号码='{number_col}'")
        else:
            print(f"⚠️ 未自动识别列名。当前列：{list(df.columns)}")
            # 尝试默认中文列名
            if '期号' in df.columns and '开奖号码' in df.columns:
                period_col, number_col = '期号', '开奖号码'
            elif 'period' in df.columns and 'number' in df.columns:
                period_col, number_col = 'period', 'number'
            else:
                print("❌ 无法确定列名，请编辑脚本设置 DEFAULT_PERIOD/DEFAULT_NUMBER")
                return

    # 验证列
    if period_col not in df.columns:
        print(f"❌ 列 '{period_col}' 不存在！可用列：{list(df.columns)}")
        return
    if number_col not in df.columns:
        print(f"❌ 列 '{number_col}' 不存在！可用列：{list(df.columns)}")
        return

    # 清洗号码：只保留3位纯数字
    df = df.copy()
    df[number_col] = df[number_col].astype(str).str.strip()
    df = df[df[number_col].str.match(r'^\d{3}$')]
    if len(df) == 0:
        print("❌ 无有效3位号码数据。")
        return

    # 排序：按期号数值或字符串升序
    try:
        df[period_col] = pd.to_numeric(df[period_col], errors='coerce')
        df = df.dropna(subset=[period_col]).sort_values(period_col).reset_index(drop=True)
    except:
        df = df.sort_values(period_col).reset_index(drop=True)

    # 找豹子号
    baozi_mask = df[number_col].apply(lambda x: len(set(x)) == 1)
    baozi_df = df[baozi_mask].copy()
    baozi_df['digit'] = baozi_df[number_col].str[0].astype(int)

    if len(baozi_df) == 0:
        print("⚠️ 无豹子号记录。")
        return

    stats = {i: {'gaps': [], 'periods': []} for i in range(10)}

    # 遍历每个豹子号
    for _, row in baozi_df.iterrows():
        # 找到该期在原始df中的索引位置
        idx_list = df[df[period_col] == row[period_col]].index.tolist()
        if not idx_list:
            continue
        baozi_idx = idx_list[0]
        digit = row['digit']
        baozi_period = row[period_col]

        # 向后查找该数字再次出现
        for j in range(baozi_idx + 1, len(df)):
            num_str = df.iloc[j][number_col]
            if str(digit) in num_str:
                gap = j - baozi_idx - 1  # 遗漏值
                stats[digit]['gaps'].append(gap)
                stats[digit]['periods'].append(df.iloc[j][period_col]) # 记录再次出现的期号
                break

    # 输出结果
    print("\n" + "="*120)
    print("📊 排列三豹子号后该数字再次出现的遗漏值统计")
    print("="*120)
    print(f"{'数字':<6} {'最大遗漏':<10} {'平均遗漏':<12} {'最频遗漏':<12} {'再出现次数':<12} {'总豹子数':<10} {'最频遗漏次数':<12}")
    print("-"*120)

    for d in range(10):
        gaps = stats[d]['gaps']
        total_baozi = (baozi_df['digit'] == d).sum()
        if not gaps:
            print(f"{d:<6} N/A        N/A          N/A          0             {total_baozi:<10} N/A         ")
            continue
        max_g = max(gaps)
        avg_g = round(np.mean(gaps), 2)
        uniq, cnts = np.unique(gaps, return_counts=True)
        mode_idx = np.argmax(cnts)
        mode_val = uniq[mode_idx]
        mode_count = cnts[mode_idx]
        print(f"{d:<6} {max_g:<10} {avg_g:<12.2f} {mode_val:<12} {len(gaps):<12} {total_baozi:<10} {mode_count:<12}")

    print("="*120)

def analyze_single_digit(digit, csv_path, period_col=None, number_col=None):
    """
    新增功能：统计指定数字的所有豹子号后，再次出现为独码的遗漏值列表
    """
    if digit < 0 or digit > 9:
        print("❌ 输入错误：数字必须是 0-9 之间的整数！")
        return

    if not os.path.exists(csv_path):
        print(f"❌ 错误：文件不存在！请检查路径：{csv_path}")
        return

    encodings = ['utf-8', 'gbk', 'gb2312']
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(csv_path, dtype=str, encoding=enc)
            break
        except UnicodeDecodeError:
            continue
    if df is None:
        print("❌ 无法用 utf-8/gbk/gb2312 编码读取文件，请手动指定编码。")
        return

    # 自动猜列名
    if not period_col or not number_col:
        p, n = guess_column_names(df)
        if p and n:
            period_col, number_col = p, n
        else:
            # 尝试默认中文列名
            if '期号' in df.columns and '开奖号码' in df.columns:
                period_col, number_col = '期号', '开奖号码'
            elif 'period' in df.columns and 'number' in df.columns:
                period_col, number_col = 'period', 'number'
            else:
                print("❌ 无法确定列名，请编辑脚本设置 DEFAULT_PERIOD/DEFAULT_NUMBER")
                return

    # 验证列
    if period_col not in df.columns:
        print(f"❌ 列 '{period_col}' 不存在！可用列：{list(df.columns)}")
        return
    if number_col not in df.columns:
        print(f"❌ 列 '{number_col}' 不存在！可用列：{list(df.columns)}")
        return

    # 清洗号码
    df = df.copy()
    df[number_col] = df[number_col].astype(str).str.strip()
    df = df[df[number_col].str.match(r'^\d{3}$')]
    if len(df) == 0:
        print("❌ 无有效3位号码数据。")
        return

    # 排序
    try:
        df[period_col] = pd.to_numeric(df[period_col], errors='coerce')
        df = df.dropna(subset=[period_col]).sort_values(period_col).reset_index(drop=True)
    except:
        df = df.sort_values(period_col).reset_index(drop=True)

    # 找该数字的所有豹子号
    baozi_mask = (df[number_col].apply(lambda x: len(set(x)) == 1)) & (df[number_col].str[0].astype(int) == digit)
    baozi_df = df[baozi_mask].copy()
    baozi_df['digit'] = baozi_df[number_col].str[0].astype(int)

    if len(baozi_df) == 0:
        print(f"⚠️  数字 {digit} 在数据中从未开出豹子号（{digit}{digit}{digit}）。")
        return

    print(f"\n🔍 查询数字：{digit}")
    print(f"📊 发现该数字共开出 {len(baozi_df)} 次豹子号。")
    print("-" * 80)
    print(f"{'豹子号期号':<12} {'再次出现期号':<15} {'遗漏值':<8} {'再次出现号码':<12}")
    print("-" * 80)

    gaps_list = []
    periods_list = []

    for _, row in baozi_df.iterrows():
        baozi_idx = df[df[period_col] == row[period_col]].index[0]
        baozi_period = row[period_col]

        found = False
        for j in range(baozi_idx + 1, len(df)):
            num_str = df.iloc[j][number_col]
            if str(digit) in num_str:
                gap = j - baozi_idx - 1
                reappear_period = df.iloc[j][period_col]
                reappear_code = df.iloc[j][number_col]
                
                print(f"{baozi_period:<12} {reappear_period:<15} {gap:<8} {reappear_code:<12}")
                
                gaps_list.append(gap)
                periods_list.append(reappear_period)
                found = True
                break
        
        if not found:
            print(f"{baozi_period:<12} {'未再出现':<15} {'N/A':<8} {'N/A':<12}")
            # 不计入统计列表，因为没有再次出现

    if not gaps_list:
        print(f"⚠️  数字 {digit} 的所有豹子号后，该数字均未再次出现。")
        return

    # 计算并显示统计摘要
    max_gap = max(gaps_list)
    avg_gap = round(np.mean(gaps_list), 2)
    uniq, cnts = np.unique(gaps_list, return_counts=True)
    mode_idx = np.argmax(cnts)
    mode_val = uniq[mode_idx]
    mode_count = cnts[mode_idx]
    
    print("-" * 80)
    print("📈 统计摘要：")
    print(f"  - 遗漏值列表: {gaps_list}")
    print(f"  - 最大遗漏值: {max_gap}")
    print(f"  - 平均遗漏值: {avg_gap:.2f}")
    print(f"  - 最频遗漏值: {mode_val} (出现了 {mode_count} 次)")
    print(f"  - 总统计次数: {len(gaps_list)} (从 {len(baozi_df)} 次豹子号中)")

# ======================
# 🔥 主程序入口：交互式菜单
# ======================
if __name__ == "__main__":
    DEFAULT_CSV = "allpaisan.csv"
    
    print("🎯 排列三豹子号遗漏分析工具")
    print("📁 默认读取文件:", DEFAULT_CSV)
    
    if not os.path.exists(DEFAULT_CSV):
        print(f"❌ 默认文件 {DEFAULT_CSV} 不存在！请将CSV文件重命名为 'allpaisan.csv' 并放在同目录下，或编辑脚本修改 'DEFAULT_CSV'。")
        sys.exit(1)
    
    while True:
        print("\n" + "="*50)
        print("请选择功能：")
        print("1. 统计所有数字（0-9）的豹子号遗漏情况")
        print("2. 查询指定数字的豹子号遗漏详情")
        print("3. 退出")
        print("="*50)
        
        choice = input("请输入选项 (1/2/3): ").strip()
        
        if choice == '1':
            analyze_all_digits(DEFAULT_CSV)
        elif choice == '2':
            try:
                digit_input = input("请输入要查询的数字 (0-9): ").strip()
                digit = int(digit_input)
                analyze_single_digit(digit, DEFAULT_CSV)
            except ValueError:
                print("❌ 输入错误，请输入一个 0-9 之间的数字！")
        elif choice == '3':
            print("👋 感谢使用，再见！")
            break
        else:
            print("❌ 无效选项，请重新输入！")