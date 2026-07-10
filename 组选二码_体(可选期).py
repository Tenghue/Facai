import pandas as pd
import numpy as np
from itertools import combinations
import re
from datetime import datetime

def safe_sort_key(s):
    """智能提取期号数字部分用于排序"""
    nums = re.sub(r'\D', '', str(s))
    return int(nums) if nums else 0

def load_data():
    """加载并预处理CSV数据"""
    file_path = 'allpaisan.csv'
    try:
        # 尝试多种编码
        encodings = ['utf-8', 'gbk', 'utf-8-sig']
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(file_path, encoding=enc, dtype=str)
                break
            except UnicodeDecodeError:
                continue
        if df is None:
            raise ValueError("无法使用常见编码读取文件")
        
        # 自动识别列名
        issue_col = None
        number_col = None
        for col in df.columns:
            if any(keyword in col.lower() for keyword in ['期号', '期', 'issue', 'id']):
                issue_col = col
            if any(keyword in col.lower() for keyword in ['号码', 'code', 'number', '开奖']):
                number_col = col
        
        if not issue_col or not number_col:
            print(f"列名检测结果: {list(df.columns)}")
            raise ValueError("未找到期号或开奖号码列")
        
        # 数据清洗
        df = df[[issue_col, number_col]].copy()
        df = df.dropna()
        df[issue_col] = df[issue_col].astype(str).str.strip()
        df[number_col] = df[number_col].astype(str).str.strip()
        
        # 确保开奖号码是3位数字
        df = df[df[number_col].str.match(r'^\d{3}$')]
        
        # 按期号排序
        df['sort_key'] = df[issue_col].apply(safe_sort_key)
        df = df.sort_values('sort_key').drop('sort_key', axis=1).reset_index(drop=True)
        
        print(f"✅ 成功加载数据: 共 {len(df)} 期，期号范围 {df[issue_col].iloc[0]} - {df[issue_col].iloc[-1]}")
        return df, issue_col, number_col
        
    except FileNotFoundError:
        print(f"❌ 文件 {file_path} 不存在")
        # 生成示例数据用于演示
        print("💡 使用示例数据进行演示...")
        periods = [f"2023{i:03d}" for i in range(1, 101)]
        codes = []
        np.random.seed(42)
        for _ in range(100):
            # 生成示例开奖号码
            r = np.random.random()
            if r < 0.7:  # 70%组六
                digits = np.random.choice(10, 3, replace=False)
                code = ''.join(map(str, sorted(digits)))
            elif r < 0.9:  # 20%组三
                same_digit = np.random.randint(0, 10)
                other_digit = np.random.randint(0, 10)
                while other_digit == same_digit:
                    other_digit = np.random.randint(0, 10)
                positions = np.random.permutation([same_digit, same_digit, other_digit])
                code = ''.join(map(str, positions))
            else:  # 10%豹子
                digit = np.random.randint(0, 10)
                code = f"{digit}{digit}{digit}"
            codes.append(code)
        
        df = pd.DataFrame({
            '期号': periods,
            '开奖号码': codes
        })
        return df, '期号', '开奖号码'

def filter_data_by_end_period(df, issue_col, target_period):
    """根据目标期号过滤数据"""
    available_periods = df[issue_col].tolist()
    
    # 精确匹配
    if target_period in available_periods:
        end_idx = df[df[issue_col] == target_period].index[0]
        return df.iloc[:end_idx + 1].reset_index(drop=True)
    
    # 找到最接近的期号
    target_key = safe_sort_key(target_period)
    closest_period = None
    closest_idx = -1
    
    for i, period in enumerate(available_periods):
        if safe_sort_key(period) <= target_key:
            closest_period = period
            closest_idx = i
        else:
            break
    
    if closest_period is None:
        raise ValueError(f"期号 {target_period} 太小，最小期号为 {available_periods[0] if available_periods else 'N/A'}")
    
    print(f"⚠️ 期号 {target_period} 不存在，使用最接近的期号 {closest_period}")
    return df.iloc[:closest_idx + 1].reset_index(drop=True)

def analyze_two_digit_miss(df, number_col):
    """分析所有组选二码的遗漏情况"""
    # 获取所有可能的二码组合
    all_pairs = list(combinations(range(10), 2))
    
    results = []
    
    # 获取开奖号码列表
    codes = df[number_col].tolist()
    n = len(codes)
    
    for d1, d2 in all_pairs:
        target_pair = {d1, d2}
        
        # 标记每期是否包含该二码
        hit_flags = []
        for code in codes:
            code_digits = set(int(d) for d in code)
            hit = target_pair.issubset(code_digits)
            hit_flags.append(hit)
        
        # 准确计算遗漏值
        current_miss = 0
        max_miss = 0
        all_misses = []
        temp_miss = 0
        
        # 从前向后遍历，计算所有遗漏段
        for hit in hit_flags:
            if hit:
                if temp_miss > 0:
                    all_misses.append(temp_miss)
                    max_miss = max(max_miss, temp_miss)
                    temp_miss = 0
            else:
                temp_miss += 1
        
        # 处理最后一个未结束的遗漏段（即当前遗漏）
        if temp_miss > 0:
            current_miss = temp_miss
            max_miss = max(max_miss, temp_miss)
        else:
            current_miss = 0
        
        # 计算超过最大遗漏值的次数
        exceed_max_count = sum(1 for miss in all_misses if miss > max_miss)
        
        # 找到上次较大遗漏的期数和遗漏值
        last_large_miss_value = 0
        last_large_miss_period = "N/A"
        
        if all_misses:
            # 按遗漏值降序排列
            sorted_misses = sorted(all_misses, reverse=True)
            if len(sorted_misses) > 1:
                # 取第二大的遗漏值
                unique_sorted = sorted(set(sorted_misses), reverse=True)
                if len(unique_sorted) > 1:
                    second_max = unique_sorted[1]
                    # 找到最后一次出现第二大遗漏的位置
                    for i in range(len(all_misses)-1, -1, -1):
                        if all_misses[i] == second_max:
                            # 计算对应的期数
                            # 由于all_misses按时间顺序排列，需要找到具体期数
                            # 计算到这个遗漏段结束的期数索引
                            pos = 0
                            for j, miss_val in enumerate(all_misses):
                                if j == i:
                                    # 找到这个遗漏段结束的期数
                                    # 从前往后累计期数
                                    total_count_before = sum(all_misses[:j])
                                    # 找到遗漏段开始的期数（不中奖的开始）
                                    start_pos = total_count_before
                                    # 结束期数（中奖的期数）
                                    end_pos = total_count_before + miss_val
                                    if end_pos < len(df):
                                        start_period = df.iloc[start_pos]['期号'] if '期号' in df.columns else str(start_pos)
                                        end_period = df.iloc[end_pos]['期号'] if '期号' in df.columns else str(end_pos)
                                        last_large_miss_period = f"{start_period}至{end_period}"
                                    break
                            
                            last_large_miss_value = second_max
                            break
                else:
                    # 如果只有一种遗漏值，就用最大的那个
                    largest_val = unique_sorted[0]
                    for i in range(len(all_misses)-1, -1, -1):
                        if all_misses[i] == largest_val:
                            # 计算到这个遗漏段结束的期数索引
                            total_count_before = sum(all_misses[:i])
                            start_pos = total_count_before
                            end_pos = total_count_before + largest_val
                            if end_pos < len(df):
                                start_period = df.iloc[start_pos]['期号'] if '期号' in df.columns else str(start_pos)
                                end_period = df.iloc[end_pos]['期号'] if '期号' in df.columns else str(end_pos)
                                last_large_miss_period = f"{start_period}至{end_period}"
                            last_large_miss_value = largest_val
                            break
            elif sorted_misses:
                # 只有一个遗漏值
                largest_val = sorted_misses[0]
                for i in range(len(all_misses)-1, -1, -1):
                    if all_misses[i] == largest_val:
                        # 计算到这个遗漏段结束的期数索引
                        total_count_before = sum(all_misses[:i])
                        start_pos = total_count_before
                        end_pos = total_count_before + largest_val
                        if end_pos < len(df):
                            start_period = df.iloc[start_pos]['期号'] if '期号' in df.columns else str(start_pos)
                            end_period = df.iloc[end_pos]['期号'] if '期号' in df.columns else str(end_pos)
                            last_large_miss_period = f"{start_period}至{end_period}"
                        last_large_miss_value = largest_val
                        break
        
        # 计算超过当前遗漏值的次数
        exceed_current_count = sum(1 for miss in all_misses if miss > current_miss)
        
        results.append({
            '二码': f"{d1}{d2}",
            '历史最大遗漏值': max_miss,
            '当前遗漏值': current_miss,
            '超过当前遗漏次数': exceed_current_count,
            '超过最大遗漏次数': exceed_max_count,
            '上次较大遗漏期数和值': f"{last_large_miss_period}({last_large_miss_value}期)" if last_large_miss_period != "N/A" else "N/A",
            '出现次数': sum(hit_flags),
            '遗漏序列': all_misses
        })
    
    return results

def main():
    print("🧠 开始分析排列三组选二码遗漏情况...")
    
    try:
        # 加载数据
        df, issue_col, number_col = load_data()
        print(f"📊 数据期号范围: {df[issue_col].iloc[0]} → {df[issue_col].iloc[-1]}")
        
        # 获取截止期号
        target_period = input("请输入截止期号 (例如: 2023100): ").strip()
        
        if not target_period:
            target_period = df[issue_col].iloc[-1]
            print(f"✅ 使用最新期号: {target_period}")
        
        # 过滤数据
        filtered_df = filter_data_by_end_period(df, issue_col, target_period)
        print(f"✅ 过滤后数据: {len(filtered_df)} 期，范围 {filtered_df[issue_col].iloc[0]} → {filtered_df[issue_col].iloc[-1]}")
        
        # 分析二码遗漏
        print(f"🔄 正在分析45个组选二码的遗漏情况...")
        results = analyze_two_digit_miss(filtered_df, number_col)
        
        # 按历史最大遗漏值排序
        results.sort(key=lambda x: (-x['历史最大遗漏值'], -x['当前遗漏值']))
        
        # 输出结果
        print("\n" + "="*120)
        print(f"📊 组选二码遗漏统计报告 (截止期号: {target_period})")
        print(f"📈 共分析 {len(filtered_df)} 期数据")
        print("="*120)
        print(f"{'二码':<6} {'最大遗漏':<8} {'当前遗漏':<8} {'超当前次数':<10} {'超最大次数':<10} {'上次大遗漏':<25} {'出现次数':<8}")
        print("-"*120)
        
        for r in results:
            last_miss_info = r['上次较大遗漏期数和值']
            if len(last_miss_info) > 23:
                last_miss_info = last_miss_info[:23] + ".."
            print(f"{r['二码']:<6} {r['历史最大遗漏值']:<8} {r['当前遗漏值']:<8} {r['超过当前遗漏次数']:<10} {r['超过最大遗漏次数']:<10} {last_miss_info:<25} {r['出现次数']:<8}")
        
        # 保存结果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'组选二码遗漏统计_{target_period}_{timestamp}.csv'
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print("-"*120)
        print(f"✅ 分析完成！结果已保存至: {output_file}")
        print(f"💡 提示: 当前遗漏值高的二码组合可能值得关注")
        print(f"💡 '超当前次数': 历史上有多少次该二码的遗漏值超过了当前遗漏值")
        
    except Exception as e:
        import traceback
        print(f"❌ 执行出错: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()