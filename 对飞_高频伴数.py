#分析当特定数字 d 在组三形态中出现（即 d 在开奖号码中出现≥2次）时，与 d 同期开出的另一个不同数字（称为“伴数”）的出现频次
import pandas as pd
import os
import re
from collections import Counter
from datetime import datetime

def safe_sort_key(s):
    """智能提取期号数字部分用于排序"""
    nums = re.sub(r'\D', '', str(s))
    return int(nums) if nums else 0

def load_data():
    """自动加载并智能排序 allpaisan.csv"""
    file_path = 'allpaisan.csv'
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ 文件 '{file_path}' 不存在！")
    
    for enc in ['utf-8-sig', 'gbk', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except Exception as e:
            last_err = e
    else:
        raise ValueError(f"❌ CSV解析失败: {last_err}")
    
    # 列名校正
    col_map = {}
    for col in df.columns:
        clean = col.strip().replace(' ', '').lower()
        if '期' in clean or 'issue' in clean:
            col_map[col] = '期号'
        elif '开' in clean or 'number' in clean or 'code' in clean or '奖' in clean:
            col_map[col] = '开奖号码'
    df = df.rename(columns=col_map)
    
    if not {'期号', '开奖号码'}.issubset(df.columns):
        raise ValueError(f"❌ 缺少必要列！当前列: {list(df.columns)}")
    
    # 清洗
    df = df.dropna(subset=['期号', '开奖号码'])
    df['期号'] = df['期号'].astype(str).str.strip()
    df['开奖号码'] = df['开奖号码'].astype(str).str.strip()
    df = df[df['开奖号码'].str.match(r'^\d{3}$')]
    
    # 按期号数值升序（关键：确保索引0=最早期）
    df['排序键'] = df['期号'].apply(safe_sort_key)
    df = df.sort_values('排序键').drop('排序键', axis=1).reset_index(drop=True)
    
    return df

def is_group_three(code):
    """
    精准判定组三（不含豹子）
    - 组三: 3个数字中有且仅有2个相同 (AAB/ABA/BAA)
    - 豹子: 3个数字全部相同 (AAA)
    - 组六: 3个数字各不相同 (ABC)
    """
    counts = Counter(code)
    return len(counts) == 2 and 2 in counts.values()

def analyze_companion_numbers_for_digit(df, target_digit):
    """
    分析指定数字d在组三中出现时，其伴数的出现频次
    Args:
        df: 开奖数据DataFrame
        target_digit: 目标数字d (str)
    """
    companion_counts = Counter()
    qualifying_codes = [] # 记录符合条件的开奖号码和伴数

    for _, row in df.iterrows():
        code = row['开奖号码']
        # 检查是否为组三形态，且目标数字d出现≥2次
        if is_group_three(code) and code.count(target_digit) >= 2:
            # 找到不同于target_digit的另一个数字
            other_digits = set(code) - {target_digit}
            if len(other_digits) == 1: # 确保是组三形态
                companion_digit = list(other_digits)[0]
                companion_counts[companion_digit] += 1
                qualifying_codes.append((row['期号'], code, companion_digit))

    return companion_counts, qualifying_codes

def generate_companion_report(companion_counts, qualifying_codes, target_digit, df):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    lines = []
    
    lines.append("="*120)
    lines.append(f"📊 排列三数字 '{target_digit}' 在组三形态中的伴数分析报告")
    lines.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"🔍 数据范围: {df['期号'].iloc[0]} → {df['期号'].iloc[-1]}")
    lines.append("💡 分析规则: 仅统计该数字在组三形态中出现≥2次的期次 (如 112, 121, 211 中，1 是主体，2 是伴数)")
    lines.append("="*120)

    total_occurrences = sum(companion_counts.values())
    lines.append(f"\n📈 数字 '{target_digit}' 在组三形态中出现≥2次的总期数: {total_occurrences}")

    if not companion_counts:
        lines.append("\n❌ 在所选数据范围内，未找到数字 '{}' 在组三形态中出现≥2次的记录。")
        report_content = "\n".join(lines)
        print(report_content)
        return

    # 伴数频次统计表
    lines.append("\n🏆 伴数出现频次统计 (按出现次数降序):")
    lines.append("-"*120)
    header = f"{'伴数':<6} {'出现次数':<10} {'占比 (%)':<10}"
    lines.append(header)
    lines.append("-"*120)
    
    sorted_companions = sorted(companion_counts.items(), key=lambda item: (-item[1], item[0]))
    for digit, count in sorted_companions:
        percentage = (count / total_occurrences) * 100 if total_occurrences > 0 else 0
        line = f"{digit:<6} {count:<10} {percentage:.2f}%"
        lines.append(line)

    # 符合条件的开奖记录
    lines.append("\n📋 符合条件的开奖记录:")
    lines.append("-"*120)
    header_log = f"{'期号':<12} {'开奖号码':<10} {'主体数字':<8} {'伴数':<6}"
    lines.append(header_log)
    lines.append("-"*120)
    for period, code, comp in qualifying_codes:
        line_log = f"{period:<12} {code:<10} {target_digit+'(≥2) ':<8} {comp:<6}"
        lines.append(line_log)

    # 保存报告
    report_content = "\n".join(lines)
    txt_file = f'CompanionNumberAnalysis_Digit{target_digit}_Report_{timestamp}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 保存伴数统计到CSV
    if companion_counts:
        summary_df = pd.DataFrame(list(companion_counts.items()), columns=['伴数', '出现次数'])
        summary_df['占比(%)'] = (summary_df['出现次数'] / total_occurrences * 100).round(2)
        summary_df = summary_df.sort_values(by='出现次数', ascending=False)
        summary_csv = f'CompanionNumberSummary_Digit{target_digit}_{timestamp}.csv'
        summary_df.to_csv(summary_csv, index=False, encoding='utf-8-sig')
    else:
        summary_csv = "N/A (无符合条件数据)"

    # 保存详细记录到CSV
    log_df = pd.DataFrame(qualifying_codes, columns=['期号', '开奖号码', '伴数'])
    log_df.insert(2, '主体数字', f'{target_digit}(≥2)')
    log_csv = f'CompanionNumberLog_Digit{target_digit}_{timestamp}.csv'
    log_df.to_csv(log_csv, index=False, encoding='utf-8-sig')
    
    # 控制台输出摘要
    print("\n".join(lines[:15])) # 输出报告头部和统计摘要
    print(f"\n✅ 分析完成！")
    print(f"   📄 完整报告: {txt_file}")
    print(f"   📊 伴数统计: {summary_csv}")
    print(f"   📋 开奖日志: {log_csv}")

def main():
    print("🧠 正在分析排列三数字在组三形态中的伴数规律...")

    try:
        df = load_data()
        if len(df) < 30:
            raise ValueError(f"❌ 数据量过少（需≥30期），当前仅{len(df)}期")

        while True:
            user_input = input("\n请输入您要分析的数字 (0-9)，或输入 'quit' 退出: ").strip()
            if user_input.lower() == 'quit':
                print("程序已退出。")
                break
            
            if not user_input.isdigit() or len(user_input) != 1:
                print("❌ 输入无效，请输入一个数字 (0-9)。")
                continue
            
            target_digit = user_input
            print(f"\n🔍 正在分析数字 '{target_digit}' ...")
            
            companion_counts, qualifying_codes = analyze_companion_numbers_for_digit(df, target_digit)
            generate_companion_report(companion_counts, qualifying_codes, target_digit, df)
            
            print("-" * 60) # 分隔符，方便查看多次分析结果

    except Exception as e:
        import traceback
        print(f"\n❌ 执行出错: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()