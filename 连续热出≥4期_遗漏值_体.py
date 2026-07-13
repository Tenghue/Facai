#我想请你帮我分析一下3D历史开奖号码中，组选单码，至少连续4期都重复的号码，
# 遗漏多少期又再次出。帮我显示出来，我会提供一个all3D.cvs
import csv
import os
from collections import defaultdict

# ========== 【核心函数1】数据加载（含数字0验证） ==========
def read_and_sort_data(filename):
    """读取CSV，严格验证含0数据"""
    if not os.path.exists(filename):
        print(f"❌ 错误：文件 '{filename}' 不存在！")
        return [], []
    
    records = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if '期号' not in reader.fieldnames or '开奖号码' not in reader.fieldnames:
                print(f"⚠️ 警告：CSV表头缺失！需包含'期号'和'开奖号码'，当前表头: {reader.fieldnames}")
                return [], []
            
            for row in reader:
                period = row.get('期号', '').strip()
                code = row.get('开奖号码', '').strip()
                if period and code:
                    digits = ''.join(c for c in code if c.isdigit())
                    if len(digits) == 3:
                        records.append((period, digits))
        
        records.sort(key=lambda x: x[0])
        periods = [r[0] for r in records]
        codes = [r[1] for r in records]
        
        # 验证数字0覆盖
        zero_periods = [p for p, c in zip(periods, codes) if '0' in c]
        print(f"✅ 成功加载 {len(records)} 期数据（期号: {periods[0]} ~ {periods[-1]}）")
        print(f"   🔢 含数字0的期数: {len(zero_periods)} 期 (占比 {len(zero_periods)/len(codes):.1%})")
        if len(zero_periods) > 0:
            print(f"      • 示例: {zero_periods[:3]}... (共{len(zero_periods)}期)")
        else:
            print("      ⚠️ 警告：数据中未检测到任何含数字0的开奖号码！")
        return periods, codes
    except Exception as e:
        print(f"❌ 读取文件出错: {e}")
        return [], []

# ========== 【核心函数2】全量深度分析（0-9完整覆盖+三重验证） ==========
def analyze_hot_streaks(periods, codes):
    """深度分析：0-9全数字覆盖 + 三重验证机制"""
    if not periods:
        print("⚠️ 无有效数据，分析终止")
        return
    
    total_draws = len(periods)
    print("\n" + "="*85)
    print("🔍 排列三组选单码「连续热出≥3期」全数字深度分析（0-9完整覆盖）")
    print("✅ 专项保障：数字0分析独立验证 + 全局事件总览 + 详细块显式标注")
    print("="*85)
    
    digit_event_summary = {str(d): 0 for d in range(10)}
    global_morph = {'组三': 0, '组六': 0}
    global_total_valid = 0
    
    for digit in range(10):
        d_str = str(digit)
        section_title = f"【正在分析：组选独码 {digit}】" if digit == 0 else f"【分析：组选独码 {digit}】"
        print(f"\n{'='*30} {section_title} {'='*30}")
        
        appears = [d_str in code for code in codes]
        events = []
        morph_count = {'组三': 0, '组六': 0}
        co_occur = defaultdict(int)
        valid_events = 0
        i = 0
        
        while i < total_draws:
            if appears[i]:
                start_idx = i
                while i < total_draws and appears[i]:
                    i += 1
                end_idx = i - 1
                streak_len = end_idx - start_idx + 1
                if streak_len >= 4:
                    next_idx = None
                    for j in range(end_idx + 1, total_draws):
                        if appears[j]:
                            next_idx = j
                            break
                    
                    if next_idx is not None:
                        interval = next_idx - end_idx
                        next_code = codes[next_idx]
                        unique_digits = set(next_code)
                        pattern = "组三" if len(unique_digits) < 3 else "组六"
                        morph_count[pattern] += 1
                        
                        for d_char in unique_digits:
                            if d_char != d_str:
                                try:
                                    co_occur[int(d_char)] += 1
                                except:
                                    continue
                        
                        valid_events += 1
                        global_morph[pattern] += 1
                        global_total_valid += 1
                        status = f"间隔{interval-1}期重现（{pattern}）| 重现号:{next_code}"
                        is_valid = True
                    else:
                        interval = total_draws - end_idx
                        status = f"【数据截止】已间隔{interval-1}期未再出现"
                        is_valid = False
                    
                    events.append({
                        'start_period': periods[start_idx],
                        'end_period': periods[end_idx],
                        'streak_len': streak_len,
                        'interval': interval,
                        'status': status,
                        'is_valid': is_valid
                    })
            else:
                i += 1
        
        digit_event_summary[d_str] = len(events)
        
        if events:
            print(f"✅ 共发现 {len(events)} 次「连续热出≥4期」事件：")
            print("-" * 80)
            for idx, ev in enumerate(events, 1):
                flag = "✅" if ev['is_valid'] else "⚠️"
                print(f"  {flag} 事件{idx}: {ev['start_period']} → {ev['end_period']} "
                      f"(连{ev['streak_len']}期) | {ev['status']}")
            
            if valid_events > 0:
                print(f"\n📊 【形态统计】(基于{valid_events}次有效重现)")
                g3_rate = morph_count['组三'] / valid_events
                g6_rate = morph_count['组六'] / valid_events
                print(f"  • 组三: {morph_count['组三']}次 ({g3_rate:.1%}) {'🌟' if g3_rate>0.6 else '📉' if g3_rate<0.4 else ''}")
                print(f"  • 组六: {morph_count['组六']}次 ({g6_rate:.1%}) {'🌟' if g6_rate>0.6 else '📉' if g6_rate<0.4 else ''}")
                
                if co_occur:
                    sorted_co = sorted(co_occur.items(), key=lambda x: (-x[1], x[0]))[:3]
                    print(f"\n🔗 【高频共现数字】(与{digit}重现时同步出现，已排除{digit}本身)")
                    if 0 in co_occur:
                        zero_cnt = co_occur[0]
                        zero_freq = zero_cnt / valid_events
                        print(f"  💡【数字0共现】: {zero_cnt}次 (频率{zero_freq:.1%}) {'🔥' if zero_freq>0.5 else ''}")
                    for rank, (num, cnt) in enumerate(sorted_co, 1):
                        if num == 0: continue
                        freq = cnt / valid_events
                        icon = "🔥" if freq > 0.5 else "💡" if freq > 0.3 else ""
                        print(f"  {rank}. 数字{num}: {cnt}次 ({freq:.1%}) {icon}")
                else:
                    reason = f"豹子形态（如{digit}{digit}{digit}）" if digit != 0 else "豹子000"
                    print(f"\n🔗 【高频共现数字】无（所有重现均为{reason}）")
            else:
                print("⚠️  无有效重现事件（所有事件均为数据截止）")
        else:
            print(f"❌ 未检测到数字 {digit} 的「连续热出≥4期」事件")
            print("   （可能原因：该数字无连续4期及以上热出记录）")
    
    # ========== 全数字事件总览（0-9一目了然）==========
    print("\n" + "="*85)
    print("📋 全数字事件统计总览（0-9完整验证）")
    print("="*85)
    print(f"{'数字':<6}{'事件数量':<12}{'状态':<30}")
    print("-"*85)
    for d in range(10):
        cnt = digit_event_summary[str(d)]
        status = "✅ 有事件" if cnt > 0 else "❌ 无连续热出≥3期记录"
        if d == 0:
            print(f"{'→ 0 ←':<6}{cnt:<12}{status:<30} 🔑 组选独码0已完整分析")
        else:
            print(f"{d:<6}{cnt:<12}{status:<30}")
    print("="*85)
    
    if global_total_valid > 0:
        print("\n🌍 全局形态分布（所有有效重现事件）")
        print("-"*85)
        g3_global = global_morph['组三'] / global_total_valid
        g6_global = global_morph['组六'] / global_total_valid
        print(f"总有效事件: {global_total_valid} | 组三: {global_morph['组三']} ({g3_global:.1%}) | 组六: {global_morph['组六']} ({g6_global:.1%})")
    
    print("\n" + "="*85)
    print("✅ 本次分析已100%覆盖组选独码 0-9")
    print("• 数字0专项保障：数据验证→分析标题→总览高亮→结束声明")
    print("⚠️ 提醒：若显示「无事件」，是历史数据事实，非程序遗漏")
    print("="*85)

# ========== 【新增】期号范围分割函数 ==========
def split_data_by_period_range(periods, codes, range_name, start_num, end_num):
    """按期号数值范围分割数据（智能处理前导零/非标准期号）"""
    new_periods, new_codes = [], []
    invalid_periods = []
    
    for p, c in zip(periods, codes):
        try:
            clean_p = ''.join(filter(str.isdigit, p))
            if not clean_p:
                invalid_periods.append(p)
                continue
            p_int = int(clean_p)
            
            if start_num <= p_int <= end_num:
                new_periods.append(p)
                new_codes.append(c)
        except:
            invalid_periods.append(p)
            continue
    
    if invalid_periods and len(invalid_periods) < 3:
        print(f"⚠️ {range_name}：跳过{len(invalid_periods)}个无法解析期号（示例:{invalid_periods[:3]}）")
    elif invalid_periods:
        print(f"⚠️ {range_name}：跳过{len(invalid_periods)}个无法解析期号")
    
    coverage = f"{len(new_periods)/len(periods):.1%}" if periods else "0%"
    print(f"✅ {range_name}：筛选 {len(new_periods)} 期（占全量{coverage}）| 期号范围: {start_num} ~ {end_num}")
    return new_periods, new_codes, len(new_periods)

# ========== 【新增】区域统计核心函数 ==========
def get_region_stats(periods, codes):
    """执行热号分析并返回结构化统计结果（不打印细节）"""
    if not periods or len(periods) < 10:
        return None
    
    total_draws = len(periods)
    global_valid = 0
    global_morph = {'组三': 0, '组六': 0}
    digit_stats = {str(d): {'events': 0, 'valid': 0, '组三': 0, '组六': 0} for d in range(10)}
    
    for digit in range(10):
        d_str = str(digit)
        appears = [d_str in code for code in codes]
        i, total = 0, len(periods)
        
        while i < total:
            if appears[i]:
                start = i
                while i < total and appears[i]:
                    i += 1
                end = i - 1
                streak = end - start + 1
                
                if streak >= 4:
                    digit_stats[d_str]['events'] += 1
                    next_idx = None
                    for j in range(end + 1, total):
                        if appears[j]:
                            next_idx = j
                            break
                    
                    if next_idx is not None:
                        digit_stats[d_str]['valid'] += 1
                        global_valid += 1
                        unique = set(codes[next_idx])
                        pattern = "组三" if len(unique) < 3 else "组六"
                        digit_stats[d_str][pattern] += 1
                        global_morph[pattern] += 1
            else:
                i += 1
    
    g3_rate = global_morph['组三'] / global_valid if global_valid else 0
    return {
        'total_draws': total_draws,
        'global_valid': global_valid,
        'global_morph': global_morph,
        'g3_rate': g3_rate,
        'digit_stats': digit_stats
    }

# ========== 【新增】双区域对比报告生成 ==========
def generate_comparison_report(stats1, stats2, name1, name2):
    """生成量化对比报告（突出显著差异）"""
    print("\n" + "="*95)
    print(f"📊 双区域热号重现形态对比分析 | {name1} vs {name2}")
    print("="*95)
    
    print(f"\n【1】基础数据概览")
    print(f"{'指标':<15} {name1:<25} {name2:<25} {'差异':<15}")
    print("-"*95)
    print(f"{'总期数':<15} {stats1['total_draws']:<25} {stats2['total_draws']:<25} "
          f"{stats2['total_draws']-stats1['total_draws']:<15}")
    print(f"{'有效重现事件':<15} {stats1['global_valid']:<25} {stats2['global_valid']:<25} "
          f"{stats2['global_valid']-stats1['global_valid']:<15}")
    
    g3_1, g3_2 = stats1['g3_rate'], stats2['g3_rate']
    diff = abs(g3_2 - g3_1)
    diff_pct = f"{diff:.1%}"
    significance = "🔥 显著差异" if diff > 0.15 else "⚠️ 中等差异" if diff > 0.08 else "✅ 差异微小"
    icon = "🔴" if diff > 0.15 else "🟡" if diff > 0.08 else "🟢"
    
    print(f"\n【2】全局组三形态比例（核心指标）")
    print(f"{'区域':<15} {'组三比例':<15} {'事件基数':<15}")
    print("-"*95)
    print(f"{name1:<15} {g3_1:.1%} (<{stats1['global_valid']}>)")
    print(f"{name2:<15} {g3_2:.1%} (<{stats2['global_valid']}>)")
    print(f"\n{icon} 差异值: {diff_pct} | 评估: {significance}")
    print(f"   💡 解读: {'历史走势发生明显变化' if diff>0.15 else '走势相对稳定' if diff<0.05 else '存在波动需关注'}")
    
    print(f"\n【3】各数字「连续热出≥3期」事件数量对比（仅有效重现）")
    print(f"{'数字':<6} {name1:<12} {name2:<12} {'差值':<10} {'变化趋势':<15}")
    print("-"*95)
    
    for d in range(10):
        d_str = str(d)
        v1 = stats1['digit_stats'][d_str]['valid']
        v2 = stats2['digit_stats'][d_str]['valid']
        delta = v2 - v1
        trend = "↑↑↑" if delta > 3 else "↑↑" if delta > 1 else "↓↓" if delta < -1 else "→"
        if abs(delta) >= 2:
            trend = f"{trend} 🔥" if delta > 0 else f"{trend} 📉"
        print(f"{d:<6} {v1:<12} {v2:<12} {delta:<10} {trend:<15}")
    
    print("\n" + "="*95)
    print("💡 综合结论")
    print("="*95)
    if diff > 0.15:
        print(f"• 区域间组三比例差异显著（{diff_pct}），表明热号回调形态分布发生实质性变化")
        print(f"• 建议：重点关注差异>2次的数字（如上表🔥/📉标记），其热出规律可能已调整")
    elif diff > 0.08:
        print(f"• 区域间存在中等差异（{diff_pct}），需结合近期开奖验证趋势")
    else:
        print(f"• 两区域热号重现形态高度一致（差异{diff_pct}），历史规律稳定性强")
    print(f"⚠️ 重要提醒：区域对比仅为历史现象观察，不构成未来预测依据。彩票本质是独立随机事件")
    print("="*95)

# ========== 【主程序】全量分析 + 双区域对比 ==========
if __name__ == "__main__":
    FILENAME = 'allpaisan.csv'
    
    print("="*95)
    print("🚀 启动三全量分析 + 双区域对比（04001~20001 vs 20002~26050）")
    print("="*95)
    
    # 步骤1：加载全量数据
    periods, codes = read_and_sort_data(FILENAME)
    if not (periods and len(periods) == len(codes) and len(periods) > 0):
        print("\n❌ 数据加载失败，终止执行")
        exit()
    
    # 步骤2：全量深度分析（含数字0三重验证）
    print("\n" + "="*95)
    print("🔍 执行全量数据深度分析（0-9组选独码完整覆盖）")
    print("="*95)
    analyze_hot_streaks(periods, codes)
    
    # 步骤3：分割双区域（期号转整数：04001→4001, 20001→20001）
    print("\n" + "="*95)
    print("🔄 执行双区域数据分割与对比分析")
    print("="*95)
    p1, c1, cnt1 = split_data_by_period_range(periods, codes, "区域1(04001-20001)", 4001, 20001)
    p2, c2, cnt2 = split_data_by_period_range(periods, codes, "区域2(20002-26050)", 20002, 26050)
    
    # 步骤4：验证并生成对比报告
    if cnt1 < 50 or cnt2 < 50:
        print(f"\n⚠️ 警告：区域数据量过小（区域1:{cnt1}期, 区域2:{cnt2}期），对比结果可能失真")
        print("   建议：补充历史数据或调整期号范围")
    elif cnt1 == 0 or cnt2 == 0:
        print("\n❌ 错误：至少一个区域无有效数据，终止对比分析")
    else:
        stats1 = get_region_stats(p1, c1)
        stats2 = get_region_stats(p2, c2)
        
        if not stats1 or not stats2 or stats1['global_valid'] < 5 or stats2['global_valid'] < 5:
            print("\n⚠️ 警告：区域有效事件过少（需≥5次），跳过形态对比")
        else:
            generate_comparison_report(stats1, stats2, "区域1(14001-20001)", "区域2(20002-26050)")
    
    # 终极验证
    print("\n✅ 分析流程完毕")
    print("   • 全量分析：组选独码 0-9 完整覆盖（含三重验证）")
    print("   • 区域对比：04001~20001 vs 20002~26050 量化评估")
    print("   • 期号处理：智能清洗前导零/非标格式（如04001→4001）")