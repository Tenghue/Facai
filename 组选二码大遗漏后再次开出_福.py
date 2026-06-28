import csv
import os
import pandas as pd
from collections import defaultdict

def load_data(filename='all3D.csv'):
    """
    加载排列三历史开奖数据
    期望格式：期号,开奖号码（或其他包含这两列的CSV）
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"找不到文件: {filename}")
    
    periods = []
    codes = []
    
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        headers = next(reader)  # 读取表头
        
        # 查找期号和开奖号码列的位置
        period_idx = None
        code_idx = None
        
        for i, header in enumerate(headers):
            if '期号' in header or '期' in header:
                period_idx = i
            if '开奖号码' in header or '开奖' in header or '号码' in header:
                code_idx = i
        
        if period_idx is None or code_idx is None:
            raise ValueError(f"CSV文件必须包含'期号'和'开奖号码'列，当前表头: {headers}")
        
        for row in reader:
            if len(row) > max(period_idx, code_idx):
                period = row[period_idx].strip()
                code = ''.join(c for c in row[code_idx].strip() if c.isdigit())
                
                if len(code) >= 3:  # 至少3位数字
                    code = code[:3]  # 取前3位
                    periods.append(period)
                    codes.append(code)
    
    print(f"✅ 成功加载 {len(periods)} 期数据，期号范围: {periods[0]} → {periods[-1]}")
    return periods, codes

def generate_all_two_digit_combinations():
    """生成所有45个组选二码组合 (00, 01, 02, ..., 89, 99)"""
    combinations = []
    for i in range(10):
        for j in range(i, 10):
            combinations.append(f"{i}{j}")
    return combinations

def extract_two_digit_combinations(code):
    """从三位号码中提取所有组选二码组合"""
    if len(code) != 3:
        return []
    
    digits = list(code)
    combinations = set()
    
    # 提取所有两位数组合并排序
    for i in range(3):
        for j in range(i + 1, 3):
            a, b = sorted([digits[i], digits[j]])
            combinations.add(f"{a}{b}")
    
    return list(combinations)

def analyze_miss_values(periods, codes):
    """分析每个组选二码的遗漏值"""
    all_combos = generate_all_two_digit_combinations()
    results = {}
    
    for combo in all_combos:
        # 记录该组合在哪些期出现
        appearance_periods = []
        
        for idx, code in enumerate(codes):
            two_digits = extract_two_digit_combinations(code)
            if combo in two_digits:
                appearance_periods.append(idx)
        
        # 计算遗漏值
        miss_values = []
        if appearance_periods:
            # 第一次出现前的遗漏
            miss_values.append(appearance_periods[0])
            
            # 各次出现之间的遗漏
            for i in range(1, len(appearance_periods)):
                gap = appearance_periods[i] - appearance_periods[i-1] - 1
                miss_values.append(gap)
        
        # 当前遗漏（从最后一次出现到现在）
        current_miss = len(codes) - 1 - appearance_periods[-1] if appearance_periods else len(codes)
        
        # 找出最大的5个遗漏值及其出现位置
        miss_with_info = []
        for i, miss_val in enumerate(miss_values):
            # 找到对应的期号
            occ_idx = appearance_periods[i] if i < len(appearance_periods) else -1
            period = periods[occ_idx] if 0 <= occ_idx < len(periods) else "N/A"
            
            miss_with_info.append({
                'miss_value': miss_val,
                'period_index': i,
                'period_number': period,
                'after_miss_value': miss_values[i+1] if i+1 < len(miss_values) else "最后一次出现",
                'occurrence_index': occ_idx
            })
        
        # 按遗漏值降序排序，取前5
        top_5_misses = sorted(miss_with_info, key=lambda x: x['miss_value'], reverse=True)[:5]
        
        results[combo] = {
            'total_appearances': len(appearance_periods),
            'miss_values': miss_values,
            'top_5_max_misses': top_5_misses,
            'current_miss': current_miss,
            'appearance_periods': appearance_periods,
            'max_miss': max(miss_values) if miss_values else 0,
            'avg_miss': sum(miss_values) / len(miss_values) if miss_values else 0
        }
    
    return results

def display_results(results, periods, codes):
    """显示分析结果"""
    print("\n" + "="*120)
    print("📊 排列三45个组选二码遗漏值分析报告")
    print("="*120)
    
    # 汇总表
    summary_data = []
    for combo, data in results.items():
        summary_data.append({
            '组选二码': combo,
            '总出现次数': data['total_appearances'],
            '最大遗漏值': data['max_miss'],
            '平均遗漏值': round(data['avg_miss'], 2),
            '当前遗漏值': data['current_miss']
        })
    
    # 按最大遗漏值排序
    df_summary = pd.DataFrame(summary_data)
    df_summary = df_summary.sort_values('最大遗漏值', ascending=False)
    
    print("\n📋 按最大遗漏值排序的汇总表（前20名）:")
    print(df_summary.head(20).to_string(index=False))
    
    print("\n" + "="*120)
    print("🔍 各组选二码TOP5最大遗漏详情及后续遗漏值")
    print("="*120)
    
    # 显示每个组合的详细分析
    for combo, data in results.items():
        if data['top_5_max_misses']:
            print(f"\n🔢 组选二码 {combo} (共出现 {data['total_appearances']} 次, 最大遗漏 {data['max_miss']} 期):")
            
            for i, miss_info in enumerate(data['top_5_max_misses'], 1):
                after_miss = miss_info['after_miss_value']
                if isinstance(after_miss, str):
                    print(f"   {i}. 遗漏 {miss_info['miss_value']} 期后出现 ({miss_info['period_number']}) -> {after_miss}")
                else:
                    print(f"   {i}. 遗漏 {miss_info['miss_value']} 期后出现 ({miss_info['period_number']}) -> 后续遗漏 {after_miss} 期")
    
    # 统计分析
    print("\n" + "="*120)
    print("📈 综合统计分析")
    print("="*120)
    
    all_max_misses = [data['max_miss'] for data in results.values()]
    print(f"• 所有组合最大遗漏值范围: {min(all_max_misses)} - {max(all_max_misses)} 期")
    print(f"• 平均最大遗漏值: {round(sum(all_max_misses)/len(all_max_misses), 2)} 期")
    
    # 找出最大遗漏值最高的10个组合
    top_miss_combos = sorted(
        [(combo, data['max_miss']) for combo, data in results.items()],
        key=lambda x: x[1], reverse=True
    )[:10]
    
    print(f"\n🎯 最大遗漏值TOP10组合:")
    for i, (combo, max_miss) in enumerate(top_miss_combos, 1):
        data = results[combo]
        print(f"   {i:2d}. {combo} : 最大遗漏 {max_miss} 期 (当前遗漏 {data['current_miss']} 期)")
    
    # 后续遗漏值统计
    all_after_misses = []
    for data in results.values():
        for miss_info in data['top_5_max_misses']:
            after_miss = miss_info['after_miss_value']
            if isinstance(after_miss, int):
                all_after_misses.append(after_miss)
    
    if all_after_misses:
        print(f"\n🔄 大遗漏后再次出现的遗漏值统计:")
        print(f"   - 范围: {min(all_after_misses)} - {max(all_after_misses)} 期")
        print(f"   - 平均值: {round(sum(all_after_misses)/len(all_after_misses), 2)} 期")
        
        from collections import Counter
        counter = Counter(all_after_misses)
        most_common = counter.most_common(5)
        print(f"   - 最常见遗漏值 (前5): {most_common}")
def main():
    print("="*120)
    print("🔍 排列三组选二码遗漏值深度分析系统")
    print("📊 分析45个组选二码的最大遗漏TOP5及后续遗漏模式")
    print("="*120)
    
    try:
        # 加载数据
        periods, codes = load_data('all3D.csv')
        
        if not periods:
            print("❌ 未找到有效数据")
            return
        
        print(f"\n📊 开始分析 {len(periods)} 期数据中的45个组选二码组合...")
        
        # 分析遗漏值
        results = analyze_miss_values(periods, codes)
        
        # 显示结果
        display_results(results, periods, codes)
        
        print(f"\n✅ 分析完成！共分析45个组选二码组合。")
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
        print("   请确保 'all3D.csv' 文件存在于当前目录中")
    except ValueError as e:
        print(f"❌ 数据格式错误: {e}")
    except Exception as e:
        import traceback
        print(f"❌ 程序执行错误: {e}")
        traceback.print_exc()
if __name__ == "__main__":
    main()