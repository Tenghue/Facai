import csv
import os
from collections import defaultdict

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

def analyze_win_intervals_and_misses(periods, win_records, start_idx):
    """分析中奖间隔和遗漏值"""
    if not win_records:
        print(f"\n📊 中奖间隔与遗漏统计: 无中奖记录")
        return
    
    # 提取中奖期号的索引
    win_indices = []
    for record in win_records:
        for i, period in enumerate(periods):
            if period == record['期号']:
                win_indices.append(i)
                break
    
    # 计算中奖间隔
    intervals = []
    for i in range(1, len(win_indices)):
        interval = win_indices[i] - win_indices[i-1] - 1  # 间隔期数
        intervals.append(interval)
    
    # 计算遗漏值（从起始期到首次中奖的间隔）
    first_win_interval = None
    if win_indices:
        first_win_interval = win_indices[0] - start_idx  # 从起始期到首次中奖的期数
    
    # 计算当前遗漏值（最后一次中奖到当前期的间隔）
    current_miss = None
    if win_indices:
        current_miss = len(periods) - 1 - win_indices[-1]  # 从最后中奖期到当前期的间隔
    
    print(f"\n📊 中奖间隔与遗漏统计:")
    print("-" * 50)
    
    if intervals:
        print(f"中奖间隔记录 ({len(intervals)} 次间隔):")
        for i, interval in enumerate(intervals, 1):
            win_period_1 = periods[win_indices[i-1]]
            win_period_2 = periods[win_indices[i]]
            print(f"   间隔{i}: {win_period_1} → {win_period_2} = {interval}期")
        
        max_interval = max(intervals)
        min_interval = min(intervals)
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        print(f"\n📈 间隔统计:")
        print(f"   最大间隔: {max_interval} 期")
        print(f"   最小间隔: {min_interval} 期") 
        print(f"   平均间隔: {avg_interval:.2f} 期")
    else:
        print("   仅有一期中奖或无间隔数据")
    
    if first_win_interval is not None:
        print(f"\n🎯 首次中奖: 第{first_win_interval}期中奖 (期号: {win_records[0]['期号']})")
    
    if current_miss is not None:
        print(f"🔍 当前遗漏: {current_miss} 期 (自{win_records[-1]['期号']}后未中奖)")

def backtest_strategy_v2_with_analysis(periods, hundreds, tens, units, start_period):
    """回测策略版本2 - 个位也使用前两期未出现的数字，并添加详细分析"""
    print(f"\n🎯 排列三定位复式策略回测 V2 | 起始期: {start_period} | 策略规则:")
    print("   • 百位 = 前两期排五（上上期+上期）未出现的数字")
    print("   • 十位 = 前两期排五（上上期+上期）未出现的数字") 
    print("   • 个位 = 前两期排五（上上期+上期）未出现的数字")
    print("="*80)
    
    # 找到起始期的索引
    start_idx = -1
    for i, period in enumerate(periods):
        if period.endswith(start_period) or period == start_period:
            start_idx = i
            break
    
    if start_idx == -1:
        print(f"❌ 未找到起始期号: {start_period}")
        return
    
    print(f"✅ 开始回测，从第 {start_idx} 期 ({periods[start_idx]}) 开始")
    
    total_bets = 0
    total_wins = 0
    win_records = []
    win_periods = []  # 存储中奖期号的索引
    
    # 从起始期开始，逐期计算
    for current_idx in range(start_idx, len(periods)):
        if current_idx < 2:  # 需要至少前两期数据
            continue
            
        # 获取前两期的数据（上期和上上期）
        prev_prev_idx = current_idx - 2  # 上上期
        prev_idx = current_idx - 1       # 上期
        
        # 获取前两期的所有数字
        prev_prev_digits = set([hundreds[prev_prev_idx], tens[prev_prev_idx], units[prev_prev_idx]])
        prev_digits = set([hundreds[prev_idx], tens[prev_idx], units[prev_idx]])
        
        # 合并前两期的所有数字
        all_prev_digits = prev_prev_digits.union(prev_digits)
        
        # 百位、十位、个位候选数字 = 前两期未出现的数字
        hundred_candidates = [str(i) for i in range(10) if str(i) not in all_prev_digits]
        ten_candidates = [str(i) for i in range(10) if str(i) not in all_prev_digits]
        unit_candidates = [str(i) for i in range(10) if str(i) not in all_prev_digits]
        
        # 生成投注组合
        bet_combinations = []
        for h in hundred_candidates:
            for t in ten_candidates:
                for u in unit_candidates:
                    bet_combinations.append(h + t + u)
        
        total_bets += len(bet_combinations)
        
        # 当前期的实际开奖号码
        actual_number = hundreds[current_idx] + tens[current_idx] + units[current_idx]
        
        # 检查是否中奖
        hit = actual_number in bet_combinations
        if hit:
            total_wins += 1
            win_record = {
                '期号': periods[current_idx],
                '开奖号码': actual_number,
                '投注组合数': len(bet_combinations),
                '百位候选': ','.join(hundred_candidates),
                '十位候选': ','.join(ten_candidates),
                '个位候选': ','.join(unit_candidates),
                '期索引': current_idx
            }
            win_records.append(win_record)
            win_periods.append(current_idx)  # 记录中奖期的索引
        
        # 输出当期分析
        print(f"\n📊 第 {current_idx - start_idx + 1} 期: {periods[current_idx]}")
        print(f"   上上期: {periods[prev_prev_idx]} = {hundreds[prev_prev_idx]}{tens[prev_prev_idx]}{units[prev_prev_idx]}")
        print(f"   上期:  {periods[prev_idx]} = {hundreds[prev_idx]}{tens[prev_idx]}{units[prev_idx]}")
        print(f"   前两期数字集合: {sorted(all_prev_digits)}")
        print(f"   百位候选: {hundred_candidates if hundred_candidates else '无'}")
        print(f"   十位候选: {ten_candidates if ten_candidates else '无'}")
        print(f"   个位候选: {unit_candidates if unit_candidates else '无'}")
        print(f"   投注组合数: {len(bet_combinations)}")
        print(f"   实际开奖: {actual_number}")
        print(f"   🏆 中奖!" if hit else f"   ❌ 未中奖")
    
    # 输出汇总结果
    print("\n" + "="*80)
    print("🏆 回测结果汇总:")
    print("="*80)
    print(f"总投注期数: {len(periods) - start_idx}")
    print(f"总投注次数: {total_bets}")
    print(f"中奖次数: {total_wins}")
    if total_bets > 0:
        win_rate = (total_wins / (len(periods) - start_idx)) * 100
        hit_rate = (total_wins / max(1, total_wins)) * 100 if total_wins > 0 else 0
        avg_bets_per_period = total_bets / (len(periods) - start_idx)
        print(f"中奖率: {win_rate:.2f}% ({total_wins}/{len(periods) - start_idx})")
        print(f"命中率: {hit_rate:.2f}%")
        print(f"平均每期投注数: {avg_bets_per_period:.1f}")
    
    # 输出中奖记录
    if win_records:
        print(f"\n🎉 中奖记录 ({len(win_records)} 次):")
        print("-"*80)
        for record in win_records:
            print(f"期号: {record['期号']} | 开奖: {record['开奖号码']} | 百位候选: [{record['百位候选']}] | 十位候选: [{record['十位候选']}] | 个位候选: [{record['个位候选']}] | 投注数: {record['投注组合数']}")
        
        # 分析中奖间隔和遗漏值
        analyze_win_intervals_and_misses(periods, win_records, start_idx)
    else:
        print(f"\n😔 无中奖记录")
    
    return win_records

def compare_strategies(periods, hundreds, tens, units, start_period):
    """比较原策略和新策略"""
    print(f"\n🎯 策略对比分析 | 起始期: {start_period}")
    print("="*100)
    
    # 找到起始期的索引
    start_idx = -1
    for i, period in enumerate(periods):
        if period.endswith(start_period) or period == start_period:
            start_idx = i
            break
    
    if start_idx == -1:
        print(f"❌ 未找到起始期号: {start_period}")
        return
    
    print(f"✅ 开始对比分析，从第 {start_idx} 期 ({periods[start_idx]}) 开始")
    
    # 统计两种策略的投注数
    old_total_bets = 0  # 原策略：个位全包
    new_total_bets = 0  # 新策略：个位也排五
    total_periods = 0
    
    for current_idx in range(start_idx, len(periods)):
        if current_idx < 2:  # 需要至少前两期数据
            continue
            
        # 获取前两期的数据
        prev_prev_idx = current_idx - 2  # 上上期
        prev_idx = current_idx - 1       # 上期
        
        # 获取前两期的所有数字
        prev_prev_digits = set([hundreds[prev_prev_idx], tens[prev_prev_idx], units[prev_prev_idx]])
        prev_digits = set([hundreds[prev_idx], tens[prev_idx], units[prev_idx]])
        
        # 合并前两期的所有数字
        all_prev_digits = prev_prev_digits.union(prev_digits)
        
        # 百位、十位候选数字 = 前两期未出现的数字
        hundred_candidates = [str(i) for i in range(10) if str(i) not in all_prev_digits]
        ten_candidates = [str(i) for i in range(10) if str(i) not in all_prev_digits]
        unit_candidates_new = [str(i) for i in range(10) if str(i) not in all_prev_digits]
        
        # 原策略：个位全包
        unit_candidates_old = [str(i) for i in range(10)]
        
        # 计算投注数
        old_bets = len(hundred_candidates) * len(ten_candidates) * len(unit_candidates_old)
        new_bets = len(hundred_candidates) * len(ten_candidates) * len(unit_candidates_new)
        
        old_total_bets += old_bets
        new_total_bets += new_bets
        total_periods += 1
    
    print(f"\n📊 策略对比结果:")
    print(f"   原策略（个位全包）:")
    print(f"     总投注数: {old_total_bets}")
    print(f"     平均每期: {old_total_bets / total_periods:.1f}")
    print(f"   新策略（个位排五）:")
    print(f"     总投注数: {new_total_bets}")
    print(f"     平均每期: {new_total_bets / total_periods:.1f}")
    print(f"   投注缩减比例: {(1 - new_total_bets / old_total_bets) * 100:.1f}%")
    print(f"   平均每期节省: {old_total_bets / total_periods - new_total_bets / total_periods:.1f} 注")

def main():
    try:
        periods, hundreds, tens, units = load_positional_data()
        
        # 获取起始期号
        start_period = input("\n请输入起始期号 (例如: 4001): ").strip()
        if not start_period:
            start_period = "4001"  # 默认值
        
        # 执行新策略回测
        win_records = backtest_strategy_v2_with_analysis(periods, hundreds, tens, units, start_period)
        
        # 执行策略对比分析
        compare_strategies(periods, hundreds, tens, units, start_period)
        
    except Exception as e:
        import traceback
        print(f"\n❌ 执行出错: {type(e).__name__}: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()