'''前三大遗漏值识别：
为每个位置（百位、十位、个位）的每个数字识别前三大遗漏值
显示第一大、第二大、第三大遗漏值
较大遗漏后第二次遗漏值：
仅统计每个较大遗漏重开后，再次遗漏的遗漏值（第二次遗漏值）
格式：较大遗漏值→第二次遗漏值，如 15→8 表示15期较大遗漏后，重开后又遗漏了8期
集成分析：
在每个位置的基础统计后，紧接着显示前三大遗漏后第二次遗漏值分析
提供表格形式和详细分析两种展示方式
import csv
import os
import pandas as pd
from collections import defaultdict
from itertools import combinations'''

import csv
import os
import pandas as pd
from collections import defaultdict, Counter
from itertools import combinations

def load_positional_data(filename='allpaisan.csv'):
    """加载数据并分离百位、十位、个位（严格按时间顺序）"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"❌ 数据文件 '{filename}' 不存在！请确保文件在当前目录")
    
    periods, hundreds, tens, units = [], [], [], []
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not {'期号', '开奖号码'}.issubset(reader.fieldnames):
            raise ValueError(f"⚠️ 表头错误！需含'期号','开奖号码'，当前: {reader.fieldnames}")
        
        for row in reader:
            period = row['期号'].strip()
            raw = row['开奖号码'].strip()
            if period and raw:
                clean = ''.join(filter(str.isdigit, raw))
                if len(clean) == 3:
                    periods.append(period)
                    hundreds.append(clean[0])
                    tens.append(clean[1])
                    units.append(clean[2])
    
    # 按期号数字排序（兼容带横杠格式）
    combined = list(zip(periods, hundreds, tens, units))
    combined.sort(key=lambda x: int(''.join(filter(str.isdigit, x[0]))) if ''.join(filter(str.isdigit, x[0])) else 0)
    periods, hundreds, tens, units = zip(*combined) if combined else ([], [], [], [])
    
    print(f"✅ 已加载 {len(periods)} 期数据 | 期号范围: {periods[0]} → {periods[-1]}")
    print(f"   🔢 百位分布: {min(hundreds)}~{max(hundreds)} | 十位: {min(tens)}~{max(tens)} | 个位: {min(units)}~{max(units)}")
    return list(periods), list(hundreds), list(tens), list(units)

def calculate_position_stats(position_data, total_periods, periods):
    """计算单个位置遗漏统计（含最大遗漏结束期号）"""
    occurrences = defaultdict(list)
    for idx, digit in enumerate(position_data):
        occurrences[digit].append(idx)
    
    stats = {}
    for digit in [str(d) for d in range(10)]:
        occ_list = occurrences.get(digit, [])
        count = len(occ_list)
        
        if count == 0:
            stats[digit] = {
                '出现次数': 0,
                '最大遗漏': total_periods,
                '平均遗漏': total_periods,
                '当前遗漏': total_periods,
                '欲出几率': 1.0,
                '理论周期': round(total_periods / 10, 1),
                '最大遗漏结束期号': "从未出现"
            }
            continue
        
        intervals = []
        end_indices = []
        
        # 首次出现前的遗漏
        intervals.append(occ_list[0])
        end_indices.append(occ_list[0])
        
        # 两次出现之间的遗漏
        for i in range(1, count):
            gap = occ_list[i] - occ_list[i-1] - 1
            intervals.append(gap)
            end_indices.append(occ_list[i])
        
        current_miss = total_periods - 1 - occ_list[-1]
        max_hist_miss = max(intervals) if intervals else 0
        
        # 确定最大遗漏结束期号
        if current_miss > max_hist_miss:
            end_period = "进行中（当前遗漏）"
        elif current_miss == max_hist_miss:
            end_period = "进行中（与历史最大持平）"
        else:
            candidate_ends = [end_indices[i] for i, g in enumerate(intervals) if g == max_hist_miss]
            recent_end_idx = max(candidate_ends) if candidate_ends else None
            if recent_end_idx is not None and 0 <= recent_end_idx < len(periods):
                end_period = periods[recent_end_idx]
            else:
                end_period = "数据异常"
        
        avg_miss = round(sum(intervals) / count, 1) if count > 0 else total_periods
        desire_ratio = round(current_miss / avg_miss, 2) if avg_miss > 0 else 0.0
        
        stats[digit] = {
            '出现次数': count,
            '最大遗漏': max(max_hist_miss, current_miss),
            '平均遗漏': avg_miss,
            '当前遗漏': current_miss,
            '欲出几率': desire_ratio,
            '理论周期': round(total_periods / 10, 1),
            '最大遗漏结束期号': end_period
        }
    return stats

def is_group_three(code):
    """
    判断号码是否为组三形态
    - 组三: 3个数字中有且仅有2个相同 (AAB/ABA/BAA)
    - 组六: 3个数字各不相同 (ABC)
    - 豹子: 3个数字全部相同 (AAA) - 也视为组三
    """
    counts = Counter(code)
    # 组三：有2个相同的数字（包含豹子）
    return len(counts) == 2 or len(counts) == 1

def analyze_digit_miss_after_large_with_form(position_data, periods, all_codes):
    """
    分析每个数字前六大遗漏值
    以及每个遗漏重开后再次遗漏的遗漏值（仅限第二次遗漏值）
    并分析第二次遗漏重出的号码形态和高频数字
    """
    occurrences = defaultdict(list)
    for idx, digit in enumerate(position_data):
        occurrences[digit].append(idx)
    
    results = {}
    for digit in [str(d) for d in range(10)]:
        occ_list = occurrences.get(digit, [])
        if len(occ_list) < 6:  # 至少需要6次出现才能分析前六大遗漏
            results[digit] = {
                '前六大遗漏值': [],
                '较大遗漏后第二次遗漏值': [],
                '形态分析': []
            }
            continue
        
        # 计算所有遗漏间隔
        intervals = []
        for i in range(1, len(occ_list)):
            gap = occ_list[i] - occ_list[i-1] - 1
            intervals.append(gap)
        
        # 创建 (值, 原始索引) 的列表，然后按值降序排序
        indexed_intervals = [(interval, idx) for idx, interval in enumerate(intervals)]
        sorted_indexed = sorted(indexed_intervals, key=lambda x: x[0], reverse=True)
        
        # 获取前六大遗漏值及其位置
        top_six = []
        used_positions = set()  # 防止重复使用同一位置
        
        for value, original_idx in sorted_indexed:
            if len(top_six) >= 6:
                break
            if original_idx not in used_positions:
                label = ['第一大', '第二大', '第三大', '第四大', '第五大', '第六大'][len(top_six)]
                top_six.append((label, value, original_idx))
                used_positions.add(original_idx)
        
        # 获取每个较大遗漏重开后的第二次遗漏值，并分析形态
        second_miss_after_large = []
        form_analysis = []
        
        for label, value, pos in top_six:
            if pos + 2 < len(intervals):  # pos+1是第一次重开遗漏，pos+2是第二次遗漏
                second_miss = intervals[pos + 2]
                second_miss_after_large.append((label, value, second_miss))
                
                # 分析第二次遗漏重出的号码形态和高频数字
                if pos + 2 < len(occ_list):  # 确保有第二次重出期号
                    reopen_idx = occ_list[pos + 2]  # 第二次重出的期号索引
                    reopen_code = all_codes[reopen_idx]  # 第二次重出的号码
                    
                    # 判断形态
                    is_group3 = is_group_three(reopen_code)
                    form_type = "组三" if is_group3 else "组六"
                    
                    # 计算高频数字（出现次数最多的数字）
                    code_counter = Counter(reopen_code)
                    max_count = max(code_counter.values())
                    high_freq_digits = [digit_char for digit_char, count in code_counter.items() if count == max_count]
                    
                    form_analysis.append({
                        'label': label,
                        'large_miss': value,
                        'second_miss': second_miss,
                        'reopen_code': reopen_code,
                        'form_type': form_type,
                        'high_freq_digits': high_freq_digits,
                        'reopen_period': periods[reopen_idx]
                    })
            else:
                # 如果无法找到第二次遗漏，则添加空数据
                second_miss_after_large.append((label, value, "N/A"))
        
        results[digit] = {
            '前六大遗漏值': [(item[0], item[1]) for item in top_six],  # 返回(label, value)格式以便向后兼容
            '较大遗漏后第二次遗漏值': second_miss_after_large,
            '形态分析': form_analysis
        }
    
    return results

def format_status(current_miss, avg_miss, max_miss):
    """智能状态标记"""
    if current_miss >= max_miss * 0.9:
        return "🔥 极冷(接近历史最大)"
    elif current_miss >= avg_miss * 2:
        return "❄️ 冷号(>2倍平均)"
    elif current_miss == 0:
        return "✅ 刚出现"
    elif current_miss <= avg_miss * 0.5:
        return "🔥 热号(<0.5倍平均)"
    else:
        return "⏳ 温号"

def analyze_two_digit_combinations(periods, hundreds, tens, units):
    """组选二码遗漏深度分析（严格基于已截取的历史数据）"""
    print("\n" + "="*120)
    print(f"🎯 组选二码遗漏深度分析（45种组合 | 数据范围: {periods[0]} → {periods[-1]} | 共 {len(periods)} 期）")
    print("💡 核心逻辑:")
    print("   • 首次最大遗漏 = 该组合第一次出现≥50期的【已结束冷段】长度（由下期回补确认）")
    print("   • 刷新事件 = 后续冷段长度 > 当前历史最大遗漏（突破自身记录）")
    print("   • 严格排除：当前进行中冷段（未被回补确认）不参与事件判定")
    print("   • 时间锚点：所有事件按【确认出现期号】（冷段结束回补期）排序")
    print("="*120)
    
    n = len(periods)
    all_codes = [hundreds[i] + tens[i] + units[i] for i in range(n)]  # 生成完整的号码列表
    
    all_combos = [f"{i}{j}" for i, j in combinations(range(10), 2)]
    combo_state = {
        combo: {
            'last_occ_idx': -1,
            'hist_max_miss': 0,
            'event_seq': 0,
            'events': []
        } for combo in all_combos
    }
    combo_events = []
    combo_current_miss = {combo: 0 for combo in all_combos}
    
    print(f"\n🔄 正在追踪 {len(all_combos)} 种组选二码组合的遗漏事件...")
    
    # 按时间顺序遍历每期
    for idx in range(n):
        digits = sorted(set([hundreds[idx], tens[idx], units[idx]]))
        current_combos = set()
        if len(digits) >= 2:
            for a, b in combinations(digits, 2):
                combo_str = f"{a}{b}"
                current_combos.add(combo_str)
        
        for combo in all_combos:
            if combo in current_combos:
                state = combo_state[combo]
                if state['last_occ_idx'] != -1:
                    cold_len = idx - state['last_occ_idx'] - 1
                    
                    if cold_len >= 50:
                        if state['hist_max_miss'] == 0:  # 首次≥50
                            state['event_seq'] = 1
                            event = {
                                '二码组合': combo,
                                '事件类型': '首次最大遗漏',
                                '事件序号': state['event_seq'],
                                '冷段长度': cold_len,
                                '上一次最大遗漏': None,
                                '增幅百分比': None,
                                '冷段开始期号': periods[state['last_occ_idx'] + 1],
                                '冷段结束期号': periods[idx - 1],
                                '确认出现期号': periods[idx],
                                '当前历史最大遗漏': cold_len
                            }
                            state['events'].append(event)
                            combo_events.append(event)
                            state['hist_max_miss'] = cold_len
                            state['event_seq'] += 1
                        elif cold_len > state['hist_max_miss']:  # 刷新事件
                            ratio = (cold_len - state['hist_max_miss']) / state['hist_max_miss']
                            event = {
                                '二码组合': combo,
                                '事件类型': '刷新最大遗漏',
                                '事件序号': state['event_seq'],
                                '冷段长度': cold_len,
                                '上一次最大遗漏': state['hist_max_miss'],
                                '增幅百分比': ratio,
                                '冷段开始期号': periods[state['last_occ_idx'] + 1],
                                '冷段结束期号': periods[idx - 1],
                                '确认出现期号': periods[idx],
                                '当前历史最大遗漏': cold_len
                            }
                            state['events'].append(event)
                            combo_events.append(event)
                            state['hist_max_miss'] = cold_len
                            state['event_seq'] += 1
                
                state['last_occ_idx'] = idx
                combo_current_miss[combo] = 0
            else:
                combo_current_miss[combo] += 1
    
    # 按确认出现期号排序
    combo_events.sort(key=lambda x: x['确认出现期号'])
    
    # 输出全局事件时间线
    if combo_events:
        print(f"\n📅 全局事件时间线（按确认出现期号排序 | 共 {len(combo_events)} 条事件）")
        print("="*120)
        print(f"{'序号':<6}{'二码':<6}{'事件类型':<15}{'冷段长度':<10}{'增幅%':<10}{'冷段区间':<25}{'确认出现期号':<15}")
        print("-"*120)
        for i, e in enumerate(combo_events[:30], 1):
            增幅显示 = f"{e['增幅百分比']:.1%}" if e['增幅百分比'] is not None else "N/A"
            区间显示 = f"{e['冷段开始期号']} → {e['冷段结束期号']}"
            print(f"{i:<6}{e['二码组合']:<6}{e['事件类型']:<15}{e['冷段长度']:<10}{增幅显示:<10}{区间显示:<25}{e['确认出现期号']:<15}")
        
        if len(combo_events) > 30:
            print(f"... 共 {len(combo_events)} 条事件（完整列表见导出文件）")
        
        # 高增幅事件
        high_growth = [e for e in combo_events 
                      if e['事件类型'] == '刷新最大遗漏' 
                      and e['增幅百分比'] is not None 
                      and e['增幅百分比'] >= 0.5]
        if high_growth:
            print(f"\n🔥 增幅≥50%的刷新事件（共 {len(high_growth)} 次 | 按增幅降序）")
            print("-"*120)
            print(f"{'二码':<6}{'事件序号':<10}{'上一次最大':<12}{'本次长度':<10}{'增幅%':<10}{'确认出现期号':<15}")
            print("-"*120)
            for e in sorted(high_growth, key=lambda x: x['增幅百分比'], reverse=True)[:10]:
                print(f"{e['二码组合']:<6}{e['事件序号']:<10}{e['上一次最大遗漏']:<12}{e['冷段长度']:<10}{e['增幅百分比']:.1%}{'':<5}{e['确认出现期号']:<15}")
        
        # 导出选项
        export = input(f"\n💾 导出所有事件到 '组选二码遗漏事件_{periods[-1]}.csv'? (y/n): ").strip().lower()
        if export in ('y', 'yes'):
            export_data = []
            for e in combo_events:
                export_data.append({
                    '二码组合': e['二码组合'],
                    '事件类型': e['事件类型'],
                    '事件序号': e['事件序号'],
                    '冷段长度': e['冷段长度'],
                    '上一次最大遗漏': e['上一次最大遗漏'] if e['上一次最大遗漏'] is not None else '',
                    '增幅百分比': f"{e['增幅百分比']:.2%}" if e['增幅百分比'] is not None else 'N/A',
                    '冷段开始期号': e['冷段开始期号'],
                    '冷段结束期号': e['冷段结束期号'],
                    '确认出现期号': e['确认出现期号'],
                    '当前历史最大遗漏': e['当前历史最大遗漏']
                })
            pd.DataFrame(export_data).to_csv(f'组选二码遗漏事件_{periods[-1]}.csv', index=False, encoding='utf-8-sig')
            print(f"✅ 已导出到 '组选二码遗漏事件_{periods[-1]}.csv'")
    else:
        print(f"\n📊 无≥50期遗漏事件")

def main():
    try:
        periods, hundreds, tens, units = load_positional_data()
        
        # 生成完整的号码列表
        all_codes = [hundreds[i] + tens[i] + units[i] for i in range(len(periods))]
        
        # 获取用户输入的截止期号
        print(f"\n📊 可用期号范围: {periods[0]} → {periods[-1]}")
        cutoff = input("请输入截止期号 (直接回车使用最新期): ").strip()
        
        if cutoff:
            if cutoff in periods:
                end_idx = periods.index(cutoff)
                periods = periods[:end_idx + 1]
                hundreds = hundreds[:end_idx + 1]
                tens = tens[:end_idx + 1]
                units = units[:end_idx + 1]
                all_codes = all_codes[:end_idx + 1]  # 同步截取号码列表
                print(f"✅ 已截取数据至期号: {cutoff} (共 {len(periods)} 期)")
            else:
                print(f"⚠️  期号 {cutoff} 不存在，使用原始数据")
        
        # 分析百位、十位、个位
        for pos_name, pos_data, pos_label in [('百位', hundreds, '百位'), ('十位', tens, '十位'), ('个位', units, '个位')]:
            print(f"\n" + "="*100)
            print(f"🎯 {pos_name}数字遗漏分析 (共 {len(pos_data)} 期)")
            print("="*100)
            
            stats = calculate_position_stats(pos_data, len(pos_data), periods)
            
            # 输出基础统计
            print(f"{'数字':<4}{'出现次数':<8}{'最大遗漏':<8}{'平均遗漏':<10}{'当前遗漏':<10}{'欲出几率':<10}{'状态':<15}")
            print("-"*100)
            
            sorted_stats = sorted(stats.items(), key=lambda x: (-stats[x[0]]['当前遗漏'], int(x[0])))
            for digit, s in sorted_stats:
                status = format_status(s['当前遗漏'], s['平均遗漏'], s['最大遗漏'])
                print(f"{digit:<4}{s['出现次数']:<8}{s['最大遗漏']:<8}{s['平均遗漏']:<10}{s['当前遗漏']:<10}{s['欲出几率']:<10.2f}{status:<15}")
            
            # 新增：前六大遗漏后第二次遗漏值及形态分析
            print(f"\n🔍 {pos_name}前六大遗漏后第二次遗漏值及形态分析:")
            print("-"*120)
            digit_analysis = analyze_digit_miss_after_large_with_form(pos_data, periods, all_codes)
            
            print(f"{'数字':<4} {'前六大遗漏':<25} {'较大遗漏后第二次遗漏值':<30} {'形态分析':<40}")
            print("-"*120)
            
            for digit in [str(d) for d in range(10)]:
                analysis = digit_analysis[digit]
                
                # 格式化前六大遗漏值
                top_six_str = ""
                for label, value in analysis['前六大遗漏值']:
                    if top_six_str:
                        top_six_str += ", "
                    top_six_str += f"{label}({value}期)"
                
                # 格式化较大遗漏后第二次遗漏值
                second_miss_str = ""
                for label, large_miss, second_miss in analysis['较大遗漏后第二次遗漏值']:
                    if second_miss_str:
                        second_miss_str += ", "
                    if isinstance(second_miss, str):  # N/A情况
                        second_miss_str += f"{large_miss}→{second_miss}"
                    else:
                        second_miss_str += f"{large_miss}→{second_miss}"
                
                # 格式化形态分析
                form_str = ""
                for form_info in analysis['形态分析']:
                    if form_str:
                        form_str += ", "
                    freq_digits = ','.join(form_info['high_freq_digits'])
                    form_str += f"{form_info['large_miss']}→{form_info['second_miss']}/{form_info['form_type']}/{freq_digits}({form_info['reopen_code']})"
                
                print(f"{digit:<4} {top_six_str:<25} {second_miss_str:<30} {form_str:<40}")
            
            # 详细分析
            print(f"\n📋 {pos_name}详细分析:")
            print("-"*120)
            for digit in [str(d) for d in range(10)]:
                analysis = digit_analysis[digit]
                print(f"\n数字 {digit}:")
                
                if analysis['前六大遗漏值']:
                    print("  前六大遗漏值:")
                    for label, value in analysis['前六大遗漏值']:
                        print(f"    {label}: {value}期")
                else:
                    print("  无足够遗漏数据")
                
                if analysis['较大遗漏后第二次遗漏值']:
                    print("  较大遗漏后第二次遗漏值:")
                    for label, large_miss, second_miss in analysis['较大遗漏后第二次遗漏值']:
                        if isinstance(second_miss, str):  # N/A情况
                            print(f"    {label}遗漏({large_miss}期) → 第二次遗漏({second_miss})")
                        else:
                            print(f"    {label}遗漏({large_miss}期) → 第二次遗漏({second_miss}期)")
                else:
                    print("  无较大遗漏或无第二次遗漏数据")
                
                if analysis['形态分析']:
                    print("  形态分析:")
                    for form_info in analysis['形态分析']:
                        freq_digits = ','.join(form_info['high_freq_digits'])
                        print(f"    {form_info['label']}遗漏({form_info['large_miss']}期) → 第二次遗漏({form_info['second_miss']}期) → 重出期号: {form_info['reopen_code']} (期号:{form_info['reopen_period']}) → 形态: {form_info['form_type']} → 高频数字: {freq_digits}")
                else:
                    print("  无形态分析数据")
        
        # 组选二码分析
        analyze_two_digit_combinations(periods, hundreds, tens, units)
        
    except Exception as e:
        import traceback
        print(f"\n❌ 执行出错: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()