import csv
import os
import pandas as pd
from collections import defaultdict
from itertools import combinations

def load_positional_data(filename='all3D.csv'):
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
                    '当前历史最大遗漏': e['当前历史最大遗漏'],
                    '分析截止期号': periods[-1]
                })
            df_events = pd.DataFrame(export_data)
            safe_name = ''.join(filter(str.isdigit, periods[-1])) or "full"
            filename = f'组选二码遗漏事件_{safe_name}.csv'
            df_events.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✅ 已导出: {filename} | 含 {len(export_data)} 条事件")
            print("   • 字段说明: '确认出现期号'=冷段结束回补节点（全局时间锚点）")
            print("   • 严格仅含【已结束冷段】，无当前进行中数据污染")
    else:
        print("\n⚠️  未检测到任何符合要求的事件（可能原因）:")
        print("   • 数据量不足（建议≥2000期）")
        print("   • 截止期较早（未积累≥50期冷段）")
        print("   • 当前进行中冷段未被回补确认（不参与事件判定）")
    
    # 当前遗漏极值参考
    print("\n" + "="*120)
    print("📌 附加参考：各组合【当前遗漏】极值（截止分析期末，未被回补确认）")
    print("-"*120)
    sorted_current = sorted(combo_current_miss.items(), key=lambda x: x[1], reverse=True)[:10]
    print(f"{'二码组合':<10}{'当前遗漏':<10}{'状态'}")
    for combo, miss in sorted_current:
        status = "⚠️ 警惕（≥50期）" if miss >= 50 else ("❄️ 冷号（≥30期）" if miss >= 30 else "⏳ 正常")
        print(f"{combo:<10}{miss:<10}{status}")
    print("\n💡 说明: 当前遗漏为【进行中】数据，未被下期回补确认，不参与'首次最大遗漏'事件判定")
    print("="*120)

def main():
    print("="*85)
    print("📊 排列三定位遗漏专业统计系统（含最大遗漏结束期号精准标记）")
    print("🛡️  核心防护: 指定期号截断分析 | 100%杜绝未来数据污染")
    print("💡 使用指南: 输入目标分析截止期号（如2026105），系统自动排除后续所有数据")
    print("="*85)
    
    try:
        # 加载原始数据
        periods, hundreds, tens, units = load_positional_data('all3D.csv')
        total_original = len(periods)
        if total_original == 0:
            print("❌ 无有效数据")
            return
        
        # =============== 【关键】用户指定截止期号（防未来数据污染） ===============
        print(f"\n🔍 完整数据范围: {periods[0]} → {periods[-1]} | 共 {total_original} 期")
        cutoff_input = input("🎯 请输入【分析截止期号】（示例: 2026105，留空=使用全部数据）: ").strip()
        
        # 智能截取逻辑
        if cutoff_input:
            cutoff_clean = ''.join(filter(str.isdigit, cutoff_input))
            if not cutoff_clean:
                print("⚠️  无效期号格式！将使用全部数据（建议输入纯数字期号如2026105）")
                analysis_periods = periods
            else:
                periods_clean = [''.join(filter(str.isdigit, p)) for p in periods]
                if cutoff_clean in periods_clean:
                    cutoff_idx = periods_clean.index(cutoff_clean)
                    analysis_periods = periods[:cutoff_idx+1]
                    hundreds = hundreds[:cutoff_idx+1]
                    tens = tens[:cutoff_idx+1]
                    units = units[:cutoff_idx+1]
                    print(f"✅【防污染生效】已截取至期号: {analysis_periods[-1]} | 分析期数: {len(analysis_periods)} 期")
                    print(f"   🔒 后续 {total_original - len(analysis_periods)} 期数据已自动排除（杜绝未来信息泄露）")
                else:
                    valid_nums = [int(p) for p in periods_clean if p]
                    if valid_nums:
                        closest = min(valid_nums, key=lambda x: abs(x - int(cutoff_clean)))
                        closest_str = str(closest)
                        closest_idx = periods_clean.index(closest_str)
                        print(f"⚠️  期号 '{cutoff_input}' 未精确匹配！")
                        print(f"💡 建议: 最接近的有效期号为 {periods[closest_idx]}（输入此号可精准截断）")
                    print(f"❌ 未找到匹配期号！将使用全部 {total_original} 期数据（存在未来数据污染风险）")
                    analysis_periods = periods
        else:
            analysis_periods = periods
            print(f"✅ 使用全部 {total_original} 期数据（未指定截止期号）")
        
        # 更新分析用变量（关键！后续所有计算基于此）
        periods = analysis_periods
        total = len(periods)
        if total == 0:
            print("❌ 截取后无有效数据！")
            return
        # =============== 截取逻辑结束 ===============
        
        # 定位遗漏分析（基于截取后数据）
        print(f"\n⏳ 正在计算百位、十位、个位遗漏统计（分析截止: {periods[-1]} | 总期数: {total}）...")
        stats_hundred = calculate_position_stats(hundreds, total, periods)
        stats_ten = calculate_position_stats(tens, total, periods)
        stats_unit = calculate_position_stats(units, total, periods)
        
        # 按位置输出
        for pos_name, stats in [("百位", stats_hundred), ("十位", stats_ten), ("个位", stats_unit)]:
            print(f"\n{'='*85}")
            print(f"📍 {pos_name} 遗漏统计（总期数: {total}）")
            print(f"{'数字':<6}{'出现次数':<10}{'最大遗漏':<10}{'平均遗漏':<10}{'当前遗漏':<10}{'欲出几率':<10}{'结束期号':<20}{'状态'}")
            print("-"*85)
            sorted_digits = sorted(stats.items(), key=lambda x: x[1]['当前遗漏'], reverse=True)
            
            for digit, data in sorted_digits:
                status = format_status(
                    data['当前遗漏'], 
                    data['平均遗漏'], 
                    data['最大遗漏']
                )
                end_period = data['最大遗漏结束期号']
                if len(end_period) > 18 and end_period not in [
                    "从未出现", "进行中（当前遗漏）", "进行中（与历史最大持平）", "数据异常"
                ]:
                    end_period = "..." + end_period[-15:]
                print(
                    f"{digit:<6}{data['出现次数']:<10}{data['最大遗漏']:<10}"
                    f"{data['平均遗漏']:<10}{data['当前遗漏']:<10}{data['欲出几率']:<10}"
                    f"{end_period:<20}{status}"
                )
            
            # 位置级洞察
            print(f"\n🔍 {pos_name} 洞察:")
            cold_nums = [d for d, v in stats.items() if v['当前遗漏'] >= v['平均遗漏'] * 2]
            hot_nums = [d for d, v in stats.items() if v['当前遗漏'] == 0]
            if cold_nums:
                print(f"   • 冷号预警(当前遗漏≥2倍平均): {', '.join(cold_nums)}")
            if hot_nums:
                print(f"   • 热号追踪(刚出现): {', '.join(hot_nums)}")
            
            max_miss_val = max(v['最大遗漏'] for v in stats.values())
            max_miss_nums = [d for d, v in stats.items() if v['最大遗漏'] == max_miss_val]
            print(f"   • 历史最大遗漏: {max_miss_val}期 (数字: {', '.join(max_miss_nums)})")
            for num in max_miss_nums:
                end_info = stats[num]['最大遗漏结束期号']
                if "进行中" not in end_info and end_info != "从未出现" and end_info != "数据异常":
                    print(f"      → 该最大遗漏结束于期号: {end_info}（回补节点）")
        
        # 导出定位统计
        print("\n" + "="*85)
        export = input(f"💾 导出完整统计到 '排列三定位遗漏_{periods[-1]}_含结束期号.csv'? (y/n): ").strip().lower()
        if export == 'y':
            export_data = []
            for digit in [str(d) for d in range(10)]:
                for pos_name, stats in [("百位", stats_hundred), ("十位", stats_ten), ("个位", stats_unit)]:
                    data = stats[digit]
                    export_data.append({
                        '位置': pos_name,
                        '数字': digit,
                        '出现次数': data['出现次数'],
                        '最大遗漏': data['最大遗漏'],
                        '平均遗漏': data['平均遗漏'],
                        '当前遗漏': data['当前遗漏'],
                        '欲出几率': data['欲出几率'],
                        '理论周期': data['理论周期'],
                        '最大遗漏结束期号': data['最大遗漏结束期号'],
                        '状态': format_status(data['当前遗漏'], data['平均遗漏'], data['最大遗漏'])
                    })
            
            df = pd.DataFrame(export_data)
            df['排序位置'] = df['位置'].map({'百位':1, '十位':2, '个位':3})
            df = df.sort_values(['排序位置', '当前遗漏'], ascending=[True, False]).drop('排序位置', axis=1)
            safe_cutoff = ''.join(filter(str.isdigit, periods[-1])) or "full"
            output_file = f'排列三定位遗漏_{safe_cutoff}_含结束期号.csv'
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"✅ 已导出！文件: {output_file}")
            print("   • 三位置完整统计（0-9每个数字）")
            print("   • 新增核心字段：最大遗漏结束期号（完整期号，便于溯源）")
            print("   • 智能状态标记 + 按冷热排序")
        
        # 组选二码分析（自动继承截取后数据）
        print("\n" + "="*85)
        two_digit_opt = input("🔍 是否进行组选二码遗漏分析（自动基于上述截止期号）? (y/n): ").strip().lower()
        if two_digit_opt == 'y':
            try:
                analyze_two_digit_combinations(periods, hundreds, tens, units)
            except Exception as e:
                print(f"❌ 组选二码分析出错: {type(e).__name__} - {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 全局洞察
        print("\n" + "="*85)
        print("🎯 全局深度洞察（含结束期号价值解读）")
        print("-"*85)
        
        global_current_max = {}
        for pos, stats in [("百位", stats_hundred), ("十位", stats_ten), ("个位", stats_unit)]:
            max_curr = max(v['当前遗漏'] for v in stats.values())
            nums = [d for d, v in stats.items() if v['当前遗漏'] == max_curr]
            global_current_max[pos] = (max_curr, nums)
        
        print("📌 当前遗漏极值对比:")
        for pos, (val, nums) in global_current_max.items():
            print(f"   • {pos}: {val}期 (数字: {', '.join(nums)})")
        
        all_cold = []
        for pos, stats in [("百位", stats_hundred), ("十位", stats_ten), ("个位", stats_unit)]:
            cold_in_pos = [f"{pos}{d}" for d, v in stats.items() if v['当前遗漏'] >= v['平均遗漏'] * 2]
            all_cold.extend(cold_in_pos)
        if all_cold:
            print(f"\n❄️  全局冷号汇总（当前遗漏≥2倍平均）: {', '.join(all_cold)}")
        
        print("\n" + "="*85)
        print(f"✅ 全部分析完成！基准截止期号: {periods[-1]} | 有效分析期数: {total}")
        print("🛡️  重要提示: 所有统计严格限定在截止期号及之前，无任何未来数据污染")
        print("💡 建议: 回测时务必指定历史期号，避免用开奖结果反推分析逻辑")
        print("="*85)
    
    except Exception as e:
        print(f"\n❌ 程序异常: {type(e).__name__} - {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()