import csv
import os
import pandas as pd
from collections import defaultdict, Counter

def load_group_data(filename='allpaisan.csv'):
    """加载组选数据（返回原始未截断数据，供后续按期号截断）"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"❌ 数据文件 '{filename}' 不存在！")
    
    periods, raw_codes = [], []
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not {'期号', '开奖号码'}.issubset(reader.fieldnames):
            raise ValueError(f"⚠️ 表头错误！需含'期号','开奖号码'，当前: {reader.fieldnames}")
        
        for row in reader:
            period = row['期号'].strip()
            code = ''.join(filter(str.isdigit, row['开奖号码'].strip()))
            if period and len(code) == 3:
                periods.append(period)
                raw_codes.append(code)
    
    # 按期号数字部分排序（兼容"2026001"或"第2026001期"等格式）
    def extract_num(s):
        num_str = ''.join(filter(str.isdigit, s))
        return int(num_str) if num_str else 0
    
    combined = sorted(zip(periods, raw_codes), key=lambda x: extract_num(x[0]))
    periods, raw_codes = map(list, zip(*combined)) if combined else ([], [])
    
    print(f"✅ 已加载 {len(periods)} 期组选数据 | 期号范围: {periods[0]} → {periods[-1]}")
    return periods, raw_codes

def preprocess_data(raw_codes):
    """预处理：生成每期数字集合 + 二码组合集合（含重复数字组合）"""
    digit_sets, combo_sets = [], []
    for code in raw_codes:
        digits = list(code)
        digit_sets.append(set(digits))
        
        combos = set()
        for i in range(3):
            for j in range(i+1, 3):
                a, b = sorted([digits[i], digits[j]])
                combos.add(a + b)
        combo_sets.append(combos)
    return digit_sets, combo_sets

def calculate_global_baseline(digit_sets, combo_sets):
    """计算全历史单码/二码组合基准频率（每期出现计1次）"""
    digit_baseline = Counter(d for ds in digit_sets for d in ds)
    combo_baseline = Counter(c for cs in combo_sets for c in cs)
    return digit_baseline, combo_baseline, len(digit_sets)

def find_digit_streak_events(target_digit, digit_sets, min_streak=4):
    """扫描单个数字的连续出现事件（长度≥min_streak）"""
    flags = [1 if target_digit in ds else 0 for ds in digit_sets]
    n, events = len(flags), []
    i = 0
    
    while i < n:
        if flags[i] == 1:
            j = i
            while j < n and flags[j] == 1:
                j += 1
            streak_len = j - i
            if streak_len >= min_streak:
                streak_end = j - 1
                miss_start = j
                miss_end = n - 1
                for k in range(j, n):
                    if flags[k] == 1:
                        miss_end = k - 1
                        break
                if miss_start <= miss_end:
                    events.append({
                        'streak_start_idx': i,
                        'streak_end_idx': streak_end,
                        'streak_length': streak_len,
                        'miss_start_idx': miss_start,
                        'miss_end_idx': miss_end
                    })
            i = j
        else:
            i += 1
    return events

def analyze_miss_period(target_digit, events, digit_sets, combo_sets, periods):
    """统计该数字所有遗漏期间的单码/二码组合频率"""
    digit_counter, combo_counter = Counter(), Counter()
    total_miss_periods, invalid_periods = 0, []
    
    for evt in events:
        for idx in range(evt['miss_start_idx'], evt['miss_end_idx'] + 1):
            if target_digit in digit_sets[idx]:
                invalid_periods.append(periods[idx])
                continue
            for d in digit_sets[idx]:
                digit_counter[d] += 1
            for combo in combo_sets[idx]:
                combo_counter[combo] += 1
            total_miss_periods += 1
    
    if invalid_periods:
        print(f"⚠️ 警告: 数字{target_digit}在{len(invalid_periods)}期遗漏期内意外出现（已跳过）: {', '.join(invalid_periods[:3])}{'...' if len(invalid_periods)>3 else ''}")
    
    return digit_counter, combo_counter, total_miss_periods

def format_status(deviation):
    """智能状态标记"""
    if deviation > 2.0: return "🔥🔥 极热(>200%)"
    if deviation > 1.5: return "🔥 热(>150%)"
    if deviation > 1.2: return "⚠️ 偏热(>120%)"
    if deviation < 0.8: return "❄️ 偏冷(<80%)"
    return "✅ 正常"

def main():
    print("="*85)
    print("🔍 排列三「单数字连续出现后遗漏期」高频单码/二码组合分析系统（纯净历史模式）")
    print("🛡️ 核心保障: 用户指定截止期号 → 自动排除后续数据 → 100%无未来数据污染")
    print("="*85)
    
    try:
        # =============== 1. 加载原始数据 ===============
        periods, raw_codes = load_group_data('allpaisan.csv')
        if not periods:
            print("❌ 无有效数据")
            return
        
        # =============== 2. 用户指定截止期号（关键增强） ===============
        print(f"\n📊 当前完整数据范围: {periods[0]} → {periods[-1]} | 共 {len(periods)} 期")
        target_issue = input("📌 请输入分析截止期号（包含该期，示例: 2026105）: ").strip()
        
        # 智能匹配：支持精确匹配或数字部分匹配（兼容不同期号格式）
        match_idx = None
        target_num = ''.join(filter(str.isdigit, target_issue))
        
        for i, p in enumerate(periods):
            if p == target_issue or (''.join(filter(str.isdigit, p)) == target_num):
                match_idx = i
                break
        
        if match_idx is None:
            print(f"❌ 期号 '{target_issue}' 不存在！请核对（有效范围: {periods[0]} ~ {periods[-1]}）")
            return
        
        # 严格截断：仅保留截止期号及之前数据
        periods = periods[:match_idx+1]
        raw_codes = raw_codes[:match_idx+1]
        print(f"✅ 已截取数据: {periods[0]} → {periods[-1]} | 共 {len(periods)} 期（后续数据已排除）")
        
        # =============== 3. 预处理截断后数据 ===============
        digit_sets, combo_sets = preprocess_data(raw_codes)
        total_periods = len(periods)
        
        # =============== 4. 全历史基准频率（基于截断后数据） ===============
        digit_baseline, combo_baseline, _ = calculate_global_baseline(digit_sets, combo_sets)
        print(f"\n📊 基准统计完成 | 分析基准: {periods[0]} → {periods[-1]} | 总期数: {total_periods}")
        
        # =============== 5. 逐数字分析（逻辑不变，数据已纯净） ===============
        print("\n⏳ 正在分析0-9每个数字的遗漏期高频组合...")
        all_results, summary_rows = {}, []
        
        for digit in [str(d) for d in range(10)]:
            print(f"  分析数字 {digit}...")
            events = find_digit_streak_events(digit, digit_sets, min_streak=4)
            if not events:
                summary_rows.append({
                    '分析数字': digit,
                    '连续事件数': 0,
                    '总遗漏期数': 0,
                    '高频单码': "无事件",
                    '高频二码': "无事件"
                })
                continue
            
            digit_cnt, combo_cnt, total_miss = analyze_miss_period(
                digit, events, digit_sets, combo_sets, periods
            )
            
            if total_miss < 10:
                summary_rows.append({
                    '分析数字': digit,
                    '连续事件数': len(events),
                    '总遗漏期数': total_miss,
                    '高频单码': f"数据不足(<10期)",
                    '高频二码': f"数据不足(<10期)"
                })
                continue
            
            # 单码分析
            digit_results = []
            for d, miss_count in digit_cnt.most_common(10):
                if d == digit: continue
                miss_freq = miss_count / total_miss * 100
                base_freq = digit_baseline.get(d, 0) / total_periods * 100
                deviation = miss_freq / base_freq if base_freq > 0 else 0
                digit_results.append({
                    '单码': d,
                    '遗漏期出现期数': miss_count,
                    '遗漏期频率(%)': round(miss_freq, 2),
                    '全历史频率(%)': round(base_freq, 2),
                    '偏离度(倍)': round(deviation, 2),
                    '状态': format_status(deviation)
                })
            
            # 二码组合分析
            combo_results = []
            for combo, miss_count in combo_cnt.most_common(15):
                if digit in combo: continue
                miss_freq = miss_count / total_miss * 100
                base_freq = combo_baseline.get(combo, 0) / total_periods * 100
                deviation = miss_freq / base_freq if base_freq > 0 else 0
                combo_results.append({
                    '二码组合': combo,
                    '遗漏期出现期数': miss_count,
                    '遗漏期频率(%)': round(miss_freq, 2),
                    '全历史频率(%)': round(base_freq, 2),
                    '偏离度(倍)': round(deviation, 2),
                    '状态': format_status(deviation)
                })
            
            all_results[digit] = {
                'events': events,
                'digit_stats': digit_results[:5],
                'combo_stats': combo_results[:8],
                'total_miss': total_miss,
                'event_count': len(events)
            }
            
            top_digit = digit_results[0] if digit_results else None
            top_combo = combo_results[0] if combo_results else None
            summary_rows.append({
                '分析数字': digit,
                '连续事件数': len(events),
                '总遗漏期数': total_miss,
                '高频单码': f"{top_digit['单码']}({top_digit['偏离度(倍)']}倍)" if top_digit else "无",
                '高频二码': f"{top_combo['二码组合']}({top_combo['偏离度(倍)']}倍)" if top_combo else "无"
            })
        
        # =============== 6. 输出摘要 ===============
        print(f"\n{'='*85}")
        print(f"📊 0-9数字遗漏期高频组合摘要（分析截止: {periods[-1]} | 基于 {total_periods} 期历史）")
        print(f"{'='*85}")
        df_summary = pd.DataFrame(summary_rows)
        print(df_summary.to_string(index=False))
        
        # =============== 7. 输出所有数字的详细分析 ===============
        print(f"\n{'='*100}")
        print(f"📋 所有数字详细分析（分析截止: {periods[-1]}）")
        print(f"{'='*100}")
        
        for digit in [str(d) for d in range(10)]:
            result = all_results.get(digit, {})
            print(f"\n🔢 数字 {digit}:")
            
            if not result:
                print(f"   • 无连续出现事件（连续4期及以上）")
                continue
            
            print(f"   • 连续事件数: {result.get('event_count', 0)} 次")
            print(f"   • 总遗漏期数: {result.get('total_miss', 0)} 期")
            
            if result.get('total_miss', 0) < 10:
                print(f"   • 遗漏期数据不足，无法进行详细分析")
                continue
            
            if result.get('digit_stats'):
                print(f"   • 遗漏期高频单码 TOP5:")
                for i, stat in enumerate(result['digit_stats'], 1):
                    print(f"     {i}. {stat['单码']} - 出现{stat['遗漏期出现期数']}期({stat['遗漏期频率(%)']}%, {stat['偏离度(倍)']}倍, {stat['状态']})")
            
            if result.get('combo_stats'):
                print(f"   • 遗漏期高频二码组合 TOP5:")
                for i, stat in enumerate(result['combo_stats'][:5], 1):
                    print(f"     {i}. {stat['二码组合']} - 出现{stat['遗漏期出现期数']}期({stat['遗漏期频率(%)']}%, {stat['偏离度(倍)']}倍, {stat['状态']})")
        
        print(f"\n✅ 分析完成！已分析所有0-9数字的遗漏期高频组合特征。")
        
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
    except ValueError as e:
        print(f"❌ 数据格式错误: {e}")
    except KeyboardInterrupt:
        print(f"\n⚠️ 用户中断操作")
    except Exception as e:
        import traceback
        print(f"\n❌ 执行出错: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()