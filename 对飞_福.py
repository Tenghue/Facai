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
    file_path = 'all3D.csv'
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ 文件 '{file_path}' 不存在！")
    
    for enc in ['utf-8-sig', 'gbk', 'utf-8']:
        try:
            # 关键：强制以字符串读取期号和开奖号码，防止前导0丢失
            df = pd.read_csv(file_path, encoding=enc, dtype={'期号': str, '开奖号码': str})
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

def find_long_miss_periods(intervals, indices, df, threshold):
    """
    查找超过指定阈值的遗漏间隔所对应的期号
    Args:
        intervals: 间隔列表
        indices: 出现期的索引列表
        df: 原始数据框
        threshold: 阈值
    Returns:
        期号列表
    """
    periods = []
    for i in range(1, len(indices)):
        gap = intervals[i-1]  # intervals[i-1] 对应 indices[i-1] -> indices[i] 的间隔
        if gap >= threshold:
            start_period = df.iloc[indices[i-1]]['期号']
            end_period = df.iloc[indices[i]]['期号']
            periods.append(f"{start_period}-{end_period}({gap}期)")
    return periods

def analyze_group_three_digits(df):
    """
    分析0-9每个数字在"组三形态"中的遗漏情况
    - 定义：数字d在组三形态中出现≥2次（d d X / d X d / X d d，且X≠d）
    - 注意：豹子（ddd）不计入，只统计真正的组三
    """
    results = []
    total = len(df)
    
    for d in map(str, range(10)):  # 包含 '0'
        indices = []  # 存储该数字在组三中出现的期索引
        
        for idx, row in df.iterrows():
            code = row['开奖号码']
            if is_group_three(code) and code.count(d) >= 2:  # 是组三 且 d出现≥2次
                indices.append(idx)
        
        # 当前遗漏
        if indices:
            last_idx = indices[-1]
            current_miss = (total - 1) - last_idx
            last_code = df.loc[last_idx, '开奖号码']
        else:
            current_miss = total
            last_code = "—"
        
        # 历史最大遗漏（已完成间隔的最大值）
        intervals = []
        for i in range(1, len(indices)):
            gap = indices[i] - indices[i-1] - 1
            intervals.append(gap)
        
        max_miss = max(intervals) if intervals else (0 if indices else total)

        # 计算历史遗漏分布及对应期数
        hist_5 = sum(1 for gap in intervals if gap >= 5)
        hist_10 = sum(1 for gap in intervals if gap >= 10)
        hist_15 = sum(1 for gap in intervals if gap >= 15)
        hist_20 = sum(1 for gap in intervals if gap >= 20)
        hist_50 = sum(1 for gap in intervals if gap >= 50)
        hist_100 = sum(1 for gap in intervals if gap >= 100)
        hist_130 = sum(1 for gap in intervals if gap >= 130)
        hist_150 = sum(1 for gap in intervals if gap >= 150)

        # 获取≥150期遗漏的具体期数
        long_miss_periods_150 = find_long_miss_periods(intervals, indices, df, 150)

        results.append({
            '数字': d,
            '当前遗漏值': current_miss,
            '历史最大遗漏值': max_miss,
            '出现次数': len(indices),
            '最近出现号码': last_code,
            '历史≥5期遗漏': hist_5,
            '历史≥10期遗漏': hist_10,
            '历史≥15期遗漏': hist_15,
            '历史≥20期遗漏': hist_20,
            '历史≥50期遗漏': hist_50,
            '历史≥100期遗漏': hist_100,
            '历史≥130期遗漏': hist_130,
            '历史≥150期遗漏': hist_150,
            '≥150期遗漏详情': long_miss_periods_150,
        })
    
    return results

def generate_report_and_save(stats, df):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    lines = []
    
    lines.append("=" * 180)
    lines.append("📊 排列三组三形态0-9数字遗漏精细化分析报告")  # 修正：去掉中文引号
    lines.append(f"📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"🔍 数据范围: {df['期号'].iloc[0]} → {df['期号'].iloc[-1]} | 总期数: {len(df)}")
    lines.append("💡 核心定义:")
    lines.append("   • 组三形态 = 开奖号码中恰好有2个数字相同（AAB/ABA/BAA），不含豹子（AAA）")
    lines.append("   • 数字d在组三中出现 = d在开奖号码中出现≥2次 且 该期为组三形态")
    lines.append("=" * 180)
    
    # 主要结果：数字遗漏分布
    lines.append(f"\n🏆 0-9数字在组三形态中的遗漏分布（按当前遗漏值降序）")
    lines.append("-" * 180)
    header = (
        f"{'数字':<4} {'当前遗漏':<8} {'历史最大':<8} {'出现次数':<8} {'最近号码':<10} "
        f"{'≥5':<6} {'≥10':<6} {'≥15':<6} {'≥20':<6} {'≥50':<6} {'≥100':<7} {'≥130':<7} {'≥150':<7}"
    )
    lines.append(header)
    lines.append("-" * 180)
    
    # 修正排序：按当前遗漏降序，数字升序（0在前）
    sorted_stats = sorted(stats, key=lambda x: (-x['当前遗漏值'], int(x['数字'])))
    for r in sorted_stats:
        line = (
            f"{r['数字']:<4} {r['当前遗漏值']:<8} {r['历史最大遗漏值']:<8} {r['出现次数']:<8} {r['最近出现号码']:<10} "
            f"{r['历史≥5期遗漏']:<6} {r['历史≥10期遗漏']:<6} {r['历史≥15期遗漏']:<6} {r['历史≥20期遗漏']:<6} {r['历史≥50期遗漏']:<6} {r['历史≥100期遗漏']:<7} {r['历史≥130期遗漏']:<7} {r['历史≥150期遗漏']:<7}"
        )
        lines.append(line)

    # 新增部分：≥150期遗漏详情
    lines.append("\n" + "=" * 180)
    lines.append("📋 ≥150期遗漏详情 (起始期-结束期(遗漏期数))")
    lines.append("-" * 180)
    for r in sorted_stats:
        num = r['数字']
        details = r['≥150期遗漏详情']
        if details:
            lines.append(f"数字 {num}: {', '.join(details)}")
        else:
            lines.append(f"数字 {num}: 无")

    # 保存报告
    report = "\n".join(lines)
    txt_file = f'GroupThree_DigitMiss_Report_{timestamp}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 保存明细到CSV
    detail_df = pd.DataFrame(sorted_stats)
    csv_file = f'GroupThree_DigitMiss_Details_{timestamp}.csv'
    detail_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    
    # 控制台输出摘要
    print("\n".join(lines[:25]))
    print(f"\n✅ 分析完成！")
    print(f"   📄 完整报告: {txt_file}")
    print(f"   📊 数字遗漏明细: {csv_file}")

def main():
    print("🧠 正在分析排列三组三形态0-9数字遗漏情况...")
    
    try:
        df = load_data()
        if len(df) < 30:
            raise ValueError(f"❌ 数据量过少（需≥30期），当前仅{len(df)}期")
        
        stats = analyze_group_three_digits(df)
        generate_report_and_save(stats, df)
        
    except Exception as e:
        import traceback
        print(f"\n❌ 执行出错: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()