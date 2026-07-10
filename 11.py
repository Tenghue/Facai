import os
import csv
from collections import defaultdict
from itertools import combinations

# ================= 1. 数据加载与预处理 =================
def load_positional_data(filename='allpaisan.csv'):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"❌ 数据文件 '{filename}' 不存在！")
    
    periods, hundreds, tens, units = [], [], [], []
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
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
                    
    combined = list(zip(periods, hundreds, tens, units))
    combined.sort(key=lambda x: int(''.join(filter(str.isdigit, x[0]))) if ''.join(filter(str.isdigit, x[0])) else 0)
    periods, hundreds, tens, units = zip(*combined) if combined else ([], [], [], [])
    return list(periods), list(hundreds), list(tens), list(units)

# ================= 2. 核心关联分析引擎 =================
def analyze_position_vs_combo_correlation(filename='allpaisan.csv', high_miss_ratio=2.0):
    """
    分析单位置高遗漏与组选二码遗漏的关联
    :param high_miss_ratio: 高遗漏触发倍数 (当前遗漏 >= 平均遗漏 * high_miss_ratio)
    """
    print("🔄 正在加载数据并计算基础统计...")
    periods, hundreds, tens, units = load_positional_data(filename)
    total_periods = len(periods)
    
    # 1. 计算各位置的基准平均遗漏
    pos_data = {'百位': hundreds, '十位': tens, '个位': units}
    avg_miss_map = {}
    for pos_name, data in pos_data.items():
        occ = defaultdict(list)
        for idx, d in enumerate(data): occ[d].append(idx)
        intervals = []
        for d in [str(i) for i in range(10)]:
            if occ[d]:
                for i in range(1, len(occ[d])):
                    intervals.append(occ[d][i] - occ[d][i-1] - 1)
        avg_miss_map[pos_name] = sum(intervals) / len(intervals) if intervals else 10

    # 2. 预计算每一期所有组选二码的当前遗漏值
    print("🔄 正在预计算每期组选二码遗漏值（耗时较长，请稍候）...")
    all_combos = [f"{i}{j}" for i, j in combinations(range(10), 2)]
    combo_last_seen = {combo: -1 for combo in all_combos}
    
    # combo_miss_timeline[idx] = {combo: miss_value}
    combo_miss_timeline = []
    for idx in range(total_periods):
        digits = sorted(set([hundreds[idx], tens[idx], units[idx]]))
        current_combos = set()
        if len(digits) >= 2:
            for a, b in combinations(digits, 2):
                current_combos.add(f"{a}{b}")
                
        period_miss = {}
        for combo in all_combos:
            if combo in current_combos:
                combo_last_seen[combo] = idx
                period_miss[combo] = 0
            else:
                period_miss[combo] = idx - combo_last_seen[combo] - 1 if combo_last_seen[combo] != -1 else idx + 1
        combo_miss_timeline.append(period_miss)

    # 3. 遍历时间轴，捕捉单位置高遗漏事件，并提取对应的二码遗漏
    print("🔍 正在扫描单位置高遗漏事件并提取二码关联...")
    correlation_stats = {
        '百位': defaultdict(list), 
        '十位': defaultdict(list), 
        '个位': defaultdict(list)
    }
    
    for idx in range(total_periods):
        for pos_name, data in pos_data.items():
            digit = data[idx]
            # 计算该位置该数字的当前遗漏
            current_miss = 0
            for back_idx in range(idx - 1, -1, -1):
                if data[back_idx] == digit:
                    current_miss = idx - back_idx - 1
                    break
            else:
                current_miss = idx  # 历史从未出现
                
            avg = avg_miss_map[pos_name]
            # 触发高遗漏条件
            if current_miss >= avg * high_miss_ratio:
                # 提取当前期所有二码的遗漏值
                current_combo_miss = combo_miss_timeline[idx]
                for combo, miss in current_combo_miss.items():
                    correlation_stats[pos_name][combo].append(miss)

    # 4. 汇总与输出报告
    print("\n" + "="*90)
    print(f"📊 【单位置高遗漏 vs 组选二码遗漏】关联分析报告")
    print(f"🎯 触发条件: 单位置当前遗漏 >= 平均遗漏 × {high_miss_ratio}")
    print("="*90)
    
    for pos_name, combos in correlation_stats.items():
        print(f"\n📍 {pos_name} (基准平均遗漏: {avg_miss_map[pos_name]:.1f}期)")
        print("-"*90)
        
        if not combos:
            print("   ⚠️ 未检测到符合条件的高遗漏事件。")
            continue
            
        # 计算每个二码组合在单位置高遗漏时的【平均遗漏值】和【触发次数】
        combo_avg_miss_during_high = {}
        for combo, miss_list in combos.items():
            combo_avg_miss_during_high[combo] = {
                '触发次数': len(miss_list),
                '二码平均遗漏': round(sum(miss_list) / len(miss_list), 1)
            }
            
        # 按触发次数降序排列，找出最容易与单位置高遗漏产生共振的二码
        sorted_combos = sorted(combo_avg_miss_during_high.items(), key=lambda x: x[1]['触发次数'], reverse=True)
        
        print(f"{'组选二码':<10}{'触发次数':<10}{'二码平均遗漏':<15}{'关联解读'}")
        print("-"*90)
        for combo, stats in sorted_combos[:15]:  # 展示Top 15
            trigger = stats['触发次数']
            miss = stats['二码平均遗漏']
            
            # 智能解读
            if trigger > 20 and miss > 30:
                tag = "🔥 强共振 (高频且极冷)"
            elif trigger > 20:
                tag = "⚡ 高频伴生 (极易受单位置拖累)"
            elif miss > 40:
                tag = "🧊 隐性极冷 (低频但一旦触发极冷)"
            else:
                tag = "⏳ 弱关联"
                
            print(f"{combo:<10}{trigger:<10}{miss:<15}{tag}")
            
    print("\n" + "="*90)

# --- 运行分析 ---
if __name__ == "__main__":
    # high_miss_ratio=2.0 表示当遗漏达到平均遗漏的2倍时视为高遗漏
    analyze_position_vs_combo_correlation(high_miss_ratio=2.0)