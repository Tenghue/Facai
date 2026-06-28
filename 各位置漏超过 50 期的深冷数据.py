import pandas as pd
import os

def analyze_deep_cold_omission_fixed(file_path):
    # 1. 读取与清洗数据
    if not os.path.exists(file_path):
        print(f"❌ 错误：找不到文件 {file_path}")
        return

    # 自动识别编码
    df = None
    for enc in ['utf-8', 'gbk', 'gb2312']:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except: continue
    
    if df is None:
        print("❌ 无法读取文件")
        return

    # --- 修改点：优先寻找期号列 ---
    issue_col = None
    cols_lower = [str(c).lower() for c in df.columns]
    # 常见的期号列名
    for kw in ['issue', '期号', '期', 'date', 'time', 'no']:
        for i, c in enumerate(cols_lower):
            if kw in c:
                issue_col = df.columns[i]
                break
        if issue_col: break
    
    # 如果没找到期号列，默认使用第一列
    if not issue_col:
        issue_col = df.columns[0]
        print(f"⚠️ 未找到明确的期号列，默认使用第一列: {issue_col}")
    else:
        print(f"✅ 识别到期号列: {issue_col}")

    # 识别号码列
    target_col = None
    for kw in ['num', 'code', 'kaijiang', '号码', 'result']:
        for i, c in enumerate(cols_lower):
            if kw in c:
                target_col = df.columns[i]
                break
        if target_col: break
    if not target_col: target_col = df.columns[-1] # 默认取最后一列作为号码列

    # 清洗并拆分号码
    def split_num(x):
        try: 
            s = str(int(float(x))).zfill(3)
            return int(s[0]), int(s[1]), int(s[2]) # 百, 十, 个
        except: 
            return 0, 0, 0
            
    df[['b', 's', 'g']] = df[target_col].apply(lambda x: pd.Series(split_num(x)))
    
    # 提取位置数据
    positions = {
        '百位': df['b'].tolist(),
        '十位': df['s'].tolist(),
        '个位': df['g'].tolist()
    }
    
    # 提取期号列表
    issue_list = df[issue_col].tolist()
    
    print(f"🚀 正在统计遗漏超过 50 期的深冷数据...")

    # 2. 核心统计逻辑
    # 存储结果：{位置: [(期号, 数字, 遗漏值)]}
    cold_records = {pos: [] for pos in positions}
    # 统计每个数字的遗漏详情
    digit_stats = {pos: {i: {'max_omission': 0, 'count': 0} for i in range(10)} for pos in positions}
    
    for pos_name, pos_data in positions.items():
        total_periods = len(pos_data)
        # 记录每个数字当前的遗漏值
        current_omission = {i: 0 for i in range(10)}
        
        for i in range(total_periods):
            current_digit = pos_data[i]
            current_issue = issue_list[i] # 获取当前真实的期号
            
            # 更新其他未出现数字的遗漏值
            for d in range(10):
                if d != current_digit:
                    current_omission[d] += 1
                else:
                    # 当前数字出现了，检查它之前的遗漏是否超过50
                    if current_omission[d] > 50:
                        # 记录：真实期号, 数字, 遗漏值
                        cold_records[pos_name].append((current_issue, d, current_omission[d]))
                        digit_stats[pos_name][d]['count'] += 1
                        if current_omission[d] > digit_stats[pos_name][d]['max_omission']:
                            digit_stats[pos_name][d]['max_omission'] = current_omission[d]
                    
                    # 重置当前数字的遗漏
                    current_omission[d] = 0

    # 3. 输出结果
    print("-" * 80)
    print(f"📊 位置遗漏超过 50 期统计报告")
    print("-" * 80)
    
    total_cold_events = 0
    
    for pos_name, records in cold_records.items():
        if not records:
            print(f"【{pos_name}】: 无遗漏超过50期的数据")
            continue
            
        print(f"【{pos_name}】共发现 {len(records)} 次深冷遗漏事件")
        print(f"{'期号':<15} {'号码':<10} {'遗漏值':<10}")
        print("-" * 40)
        for issue, digit, omission in records:
            print(f"{str(issue):<15} {digit:<10} {omission:<10}")
        print("-" * 80)
        
        total_cold_events += len(records)

    # 4. 汇总统计
    print(f"🔥 深冷号码汇总统计 (遗漏>50期)")
    print("-" * 80)
    print(f"{'位置':<10} {'号码':<10} {'出现次数':<10} {'最大遗漏'}")
    print("-" * 80)
    
    for pos_name, stats in digit_stats.items():
        for digit in range(10):
            if stats[digit]['count'] > 0:
                print(f"{pos_name:<10} {digit:<10} {stats[digit]['count']:<10} {stats[digit]['max_omission']}")
                
    print("-" * 80)
    print(f"💡 结论:")
    print(f"   历史数据中，遗漏超过50期属于极端情况。")
    print(f"   如果某位置号码遗漏接近50期，建议开始关注其回补机会。")

# --- 运行 ---
if __name__ == "__main__":
    analyze_deep_cold_omission_fixed('allpaisan.csv')
    input("\n按回车键退出...")