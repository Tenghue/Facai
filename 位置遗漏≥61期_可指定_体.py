import csv
import os
from datetime import datetime

def load_data(filename='allpaisan.csv'):
    """加载并验证数据（严格按时间升序）"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"❌ 数据文件 '{filename}' 不存在！请确认文件在当前目录")
    
    periods, hundreds, tens, units = [], [], [], []
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'期号', '开奖号码'}
        if not required.issubset(reader.fieldnames):
            raise ValueError(f"❌ 表头错误！需含{required}，当前: {reader.fieldnames}")
        
        for row in reader:
            period = row['期号'].strip()
            num = ''.join(filter(str.isdigit, row['开奖号码'].strip()))
            if period and len(num) == 3:
                periods.append(period)
                hundreds.append(num[0])
                tens.append(num[1])
                units.append(num[2])
    
    # 按期号数字排序（处理"2026001"类格式）
    combined = list(zip(periods, hundreds, tens, units))
    try:
        combined.sort(key=lambda x: int(''.join(filter(str.isdigit, x[0]))))
    except:
        print("⚠️ 期号含非数字字符，按字符串排序")
        combined.sort(key=lambda x: x[0])
    
    periods, hundreds, tens, units = zip(*combined) if combined else ([],[],[],[])
    print(f"✅ 已加载 {len(periods)} 期数据 | 期号范围: {periods[0]} → {periods[-1]}")
    print(f"🔍 样本（前3期）: {periods[0]}:{hundreds[0]}{tens[0]}{units[0]}, "
          f"{periods[1]}:{hundreds[1]}{tens[1]}{units[1]}, {periods[2]}:{hundreds[2]}{tens[2]}{units[2]}")
    return list(periods), list(hundreds), list(tens), list(units)

def find_long_missings(periods, digit_list, target_digit, position_name):
    """
    核心算法：统计指定位置+指定号码遗漏≥61期的所有段
    • 遗漏定义：连续未出现的期数（如上期出现→本期出现，中间间隔61期=遗漏61期）
    • 严格包含：历史已结束段 + 当前进行中段
    """
    target_digit = str(target_digit).strip()
    if target_digit not in '0123456789':
        raise ValueError("❌ 指定号码必须是0-9的数字")
    
    segments = []  # 存储所有遗漏≥61期的段
    last_occurrence_idx = -1  # 上次出现的索引
    total_periods = len(periods)
    
    # 遍历每期，记录出现位置
    for idx in range(total_periods):
        if digit_list[idx] == target_digit:
            if last_occurrence_idx == -1:
                # 首次出现：检查开头遗漏
                gap = idx  # 从第0期到当前期前，共idx期未出现
                if gap >= 61:
                    segments.append({
                        'start_period': periods[0],
                        'end_period': periods[idx-1],
                        'missing_length': gap,
                        'recovery_period': periods[idx],
                        'status': '已结束'
                    })
            else:
                # 两次出现之间
                gap = idx - last_occurrence_idx - 1
                if gap >= 61:
                    segments.append({
                        'start_period': periods[last_occurrence_idx + 1],
                        'end_period': periods[idx - 1],
                        'missing_length': gap,
                        'recovery_period': periods[idx],
                        'status': '已结束'
                    })
            last_occurrence_idx = idx
    
    # 处理末尾进行中遗漏
    if last_occurrence_idx == -1:
        # 从未出现
        if total_periods >= 50:
            segments.append({
                'start_period': periods[0],
                'end_period': periods[-1],
                'missing_length': total_periods,
                'recovery_period': '从未出现',
                'status': '进行中（未回补）'
            })
    else:
        # 最后一次出现后到数据末尾
        gap = total_periods - 1 - last_occurrence_idx
        if gap >= 61:
            segments.append({
                'start_period': periods[last_occurrence_idx + 1],
                'end_period': periods[-1],
                'missing_length': gap,
                'recovery_period': '进行中（未回补）',
                'status': '进行中'
            })
    
    # 统计摘要
    total_occurrences = digit_list.count(target_digit)
    return segments, total_occurrences, total_periods

def main():
    print("="*85)
    print("🎯 排列三指定位+指定号码遗漏≥61期精准统计（严格防未来数据污染）")
    print("💡 用法: 指定位置(百/十/个) + 指定号码(0-9) → 输出所有遗漏≥61期的具体段")
    print("="*85)
    
    try:
        # 1. 加载数据
        periods, hundreds, tens, units = load_data('allpaisan.csv')
        if len(periods) < 50:
            print(f"❌ 历史数据仅{len(periods)}期，不足61期，无法统计遗漏≥61期")
            return
        
        # 2. 用户输入
        print("\n📌 请输入分析参数:")
        pos_map = {'百': hundreds, '十': tens, '个': units, 
                   '百位': hundreds, '十位': tens, '个位': units,
                   '1': hundreds, '2': tens, '3': units}
        
        while True:
            pos_input = input("   • 位置（百/十/个 或 1/2/3）: ").strip()
            if pos_input in pos_map:
                digit_list = pos_map[pos_input]
                pos_name = {'百': '百位', '十': '十位', '个': '个位'}.get(pos_input[:1], pos_input)
                break
            print("❌ 无效位置！请输入: 百/十/个 或 1/2/3")
        
        while True:
            num_input = input("   • 号码（0-9）: ").strip()
            if num_input.isdigit() and 0 <= int(num_input) <= 9:
                target_digit = num_input
                break
            print("❌ 无效号码！请输入0-9的数字")
        
        # 3. 执行统计
        print(f"\n🔍 正在分析: 【{pos_name}】位置数字 【{target_digit}】")
        segments, total_occ, total_periods = find_long_missings(
            periods, digit_list, target_digit, pos_name
        )
        
        # 4. 输出结果
        print("\n" + "="*85)
        print(f"📊 统计摘要 | 位置: {pos_name} | 号码: {target_digit}")
        print(f"   • 历史总期数: {total_periods} | 该号码总出现: {total_occ}次 | 出现频率: {total_occ/total_periods*100:.2f}%")
        print(f"   • 遗漏≥61期的段数: {len(segments)}")
        print("="*85)
        
        if not segments:
            print(f"\n✅ 恭喜！在全部{total_periods}期历史数据中，【{pos_name}】{target_digit} 无任何遗漏≥61期的记录")
            print("   （最大遗漏可能<61期，如需查看最大遗漏值可扩展功能）")
        else:
            # 表格输出
            print(f"\n{'序号':<6}{'遗漏长度':<12}{'开始期号':<15}{'结束期号':<15}{'回补期号/状态':<25}{'状态'}")
            print("-"*85)
            for i, seg in enumerate(segments, 1):
                recov = seg['recovery_period']
                status = '🟢 已回补' if seg['status'] == '已结束' else '🔴 进行中'
                print(f"{i:<6}{seg['missing_length']:<12}{seg['start_period']:<15}{seg['end_period']:<15}"
                      f"{recov:<25}{status}")
            
            # 洞察
            max_miss = max(seg['missing_length'] for seg in segments)
            ongoing = [s for s in segments if '进行中' in s['status']]
            print("\n💡 洞察:")
            print(f"   • 历史最大遗漏: {max_miss}期")
            if ongoing:
                curr = ongoing[0]
                print(f"   • ⚠️ 当前进行中遗漏: {curr['missing_length']}期（{curr['start_period']} 至 {curr['end_period']}）")
                print(f"      → 已超过60期！需重点关注回补信号")
            else:
                print(f"   • ✅ 当前无进行中遗漏≥61期")
        
        # 5. 导出选项
        if segments:
            export = input("\n💾 导出详细数据到CSV? (y/n): ").strip().lower()
            if export in ('y', 'yes'):
                filename = f"遗漏_{pos_name}{target_digit}_{datetime.now().strftime('%Y%m%d%H%M')}.csv"
                with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['序号', '遗漏长度(期)', '开始期号', '结束期号', '回补期号', '状态', '分析时间'])
                    for i, seg in enumerate(segments, 1):
                        writer.writerow([
                            i,
                            seg['missing_length'],
                            seg['start_period'],
                            seg['end_period'],
                            seg['recovery_period'],
                            seg['status'],
                            datetime.now().strftime('%Y-%m-%d %H:%M')
                        ])
                print(f"✅ 已导出: {filename} | 共{len(segments)}条记录")
                print("   • 字段说明: '回补期号'为'进行中（未回补）'表示当前仍在遗漏中")
        
        print("\n" + "="*85)
        print("✅ 分析完成 | 数据纯净度: 100%（仅使用历史数据，无未来信息）")
        print("💡 应用建议:")
        print("   • 进行中遗漏≥61期：该位置该号码长期未出，回补概率显著提升")
        print("   • 历史最大遗漏参考：对比当前遗漏与历史最大值，评估回补紧迫性")
        print("="*85)
    
    except Exception as e:
        print(f"\n❌ 执行出错: {type(e).__name__} - {str(e)}")
        print("\n🔍 调试建议:")
        print("   1. 检查allpaisan.csv是否存在且含'期号,开奖号码'列")
        print("   2. 确认输入位置为: 百/十/个 或 1/2/3")
        print("   3. 确认输入号码为0-9单个数字")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()