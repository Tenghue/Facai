import pandas as pd
from collections import Counter

def analyze_3d_top10_miss_per_digit(csv_path: str):
    """
    针对 all3D.csv (列: ['期号','开奖号码']) 
    输出0-9每个数字历史遗漏值排名前10的完整分布
    """
    # ================= 1. 数据加载与清洗 =================
    try:
        df = pd.read_csv(csv_path, encoding='utf-8', dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='gbk', dtype=str)

    if not {'期号', '开奖号码'}.issubset(df.columns):
        raise ValueError(f"CSV必须包含'期号'和'开奖号码'列，当前列: {list(df.columns)}")

    df = df.dropna(subset=['期号', '开奖号码']).copy()
    df['期号'] = df['期号'].astype(str).str.strip()
    df['开奖号码'] = df['开奖号码'].astype(str).str.strip().str.zfill(3)
    
    # 过滤非法行
    valid_mask = df['开奖号码'].str.match(r'^\d{3}$')
    if (~valid_mask).any():
        print(f"⚠️ 跳过 {(~valid_mask).sum()} 行非3位数字的异常数据")
        df = df[valid_mask].reset_index(drop=True)

    print(f"✅ 加载完成: {len(df)} 期 ({df['期号'].iloc[0]} ~ {df['期号'].iloc[-1]})")

    # ================= 2. 核心计算：每个数字的TOP10遗漏 =================
    all_results = []
    issues = df['期号'].values
    # 预计算每期数字集合，避免循环内重复转换
    digits_sets = [set(num) for num in df['开奖号码'].values]

    for digit in map(str, range(10)):
        miss_records = []  # 存储该数字所有遗漏段
        
        current_miss = 0
        miss_start_idx = -1
        miss_other_digits = []

        for i, d_set in enumerate(digits_sets):
            if digit in d_set:
                # 命中：记录当前遗漏段
                if current_miss > 0 and miss_start_idx >= 0:
                    counter = Counter(miss_other_digits)
                    high_freq = ','.join([n for n, _ in counter.most_common(3)]) or '-'
                    miss_records.append({
                        '遗漏值': current_miss,
                        '起始期号': issues[miss_start_idx],
                        '结束期号': issues[i - 1],
                        '高频数字': high_freq
                    })
                # 重置
                current_miss = 0
                miss_other_digits = []
                miss_start_idx = i + 1
            else:
                current_miss += 1
                if miss_start_idx >= 0:
                    miss_other_digits.extend([d for d in d_set if d != digit])

        # 处理尾部未命中段
        if current_miss > 0 and miss_start_idx < len(df):
            counter = Counter(miss_other_digits)
            high_freq = ','.join([n for n, _ in counter.most_common(3)]) or '-'
            miss_records.append({
                '遗漏值': current_miss,
                '起始期号': issues[miss_start_idx],
                '结束期号': issues[-1],
                '高频数字': high_freq
            })

        # 按遗漏值降序取TOP10
        top10 = sorted(miss_records, key=lambda x: x['遗漏值'], reverse=True)[:10]
        for rank, rec in enumerate(top10, 1):
            rec['数字'] = digit
            rec['排名'] = rank
            all_results.append(rec)

    # ================= 3. 格式化输出 =================
    result_df = pd.DataFrame(all_results)[['数字', '排名', '遗漏值', '起始期号', '结束期号', '高频数字']]
    result_df = result_df.sort_values(['数字', '排名']).reset_index(drop=True)

    print("\n📊 福彩3D组选独码 各数字遗漏TOP10分布（共100条）")
    print("=" * 80)
    # 按数字分组打印，便于阅读
    for digit in map(str, range(10)):
        sub = result_df[result_df['数字'] == digit]
        print(f"\n🔢 数字 [{digit}] 遗漏TOP10:")
        print(sub[['排名', '遗漏值', '起始期号', '结束期号', '高频数字']].to_string(index=False))
    print("=" * 80)

    # 导出完整结果
    out_path = csv_path.replace('.csv', '_各数字遗漏TOP10.csv')
    result_df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 完整100条结果已保存: {out_path}")


if __name__ == '__main__':
    analyze_3d_top10_miss_per_digit('all3D.csv')