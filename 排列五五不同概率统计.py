import csv
import os
from datetime import datetime

def load_paiwu_data(filename='paiwu.csv'):
    """加载排列五数据（严格验证5位数字）"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"❌ 数据文件 '{filename}' 不存在！")
    
    periods, numbers = [], []
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not {'期号', '开奖号码'}.issubset(reader.fieldnames):
            raise ValueError(f"❌ 表头错误！需含'期号','开奖号码'，当前: {reader.fieldnames}")
        
        for row in reader:
            period = row['期号'].strip()
            raw = ''.join(filter(str.isdigit, row['开奖号码'].strip()))
            if period and len(raw) == 5:
                periods.append(period)
                numbers.append(raw)
    
    # 按期号数字升序排序
    combined = list(zip(periods, numbers))
    try:
        combined.sort(key=lambda x: int(''.join(filter(str.isdigit, x[0]))))
    except:
        combined.sort(key=lambda x: x[0])
    periods, numbers = zip(*combined) if combined else ([], [])
    
    print(f"✅ 已加载 {len(periods)} 期排列五数据 | 期号范围: {periods[0]} → {periods[-1]}")
    print(f"🔍 样本验证（前3期）:")
    for i in range(min(3, len(periods))):
        print(f"   {periods[i]}: {numbers[i]} → {'五不同' if len(set(numbers[i]))==5 else '含重复'}")
    return list(periods), list(numbers)

def is_wu_different(num_str):
    """判断是否为五不同（5个数字互不相同）"""
    return len(set(num_str)) == 5

def analyze_wu_different_missing(periods, numbers):
    """
    核心算法：统计"五不同"遗漏段（连续未出现期数）
    • 遗漏定义：连续N期未开出五不同（N=遗漏长度）
    • 严格记录：每段开始/结束期号、回补期号、状态
    """
    segments = []  # 存储所有遗漏段
    current_streak = 0
    last_wu_idx = -1  # 上次五不同的索引
    total_periods = len(periods)
    
    # 遍历每期
    for i in range(total_periods):
        if is_wu_different(numbers[i]):
            if current_streak > 0:  # 遗漏段结束
                start_idx = last_wu_idx + 1 if last_wu_idx != -1 else 0
                segments.append({
                    'start_period': periods[start_idx],
                    'end_period': periods[i-1],
                    'length': current_streak,
                    'recovery_period': periods[i],
                    'status': '已结束'
                })
                current_streak = 0
            last_wu_idx = i
        else:
            current_streak += 1
    
    # 处理末尾进行中遗漏
    if current_streak > 0:
        start_idx = last_wu_idx + 1 if last_wu_idx != -1 else 0
        segments.append({
            'start_period': periods[start_idx],
            'end_period': periods[-1],
            'length': current_streak,
            'recovery_period': '进行中（未回补）',
            'status': '进行中'
        })
    
    # 统计摘要
    wu_count = sum(1 for num in numbers if is_wu_different(num))
    return segments, wu_count, total_periods

def main():
    print("="*85)
    print("🎯 排列五「五不同」最大遗漏精准统计（五个号码全不同）")
    print("💡 定义: 五不同 = 开奖号码5个数字互不相同（如12345✓, 11234✗）")
    print("🔒 严格防污染: 100%基于历史数据，无未来信息")
    print("="*85)
    
    try:
        # 1. 加载数据
        periods, numbers = load_paiwu_data('paiwu.csv')
        if len(periods) < 100:
            print(f"⚠️ 历史数据仅{len(periods)}期，建议≥100期以保证统计有效性")
        
        # 2. 执行分析
        segments, wu_count, total = analyze_wu_different_missing(periods, numbers)
        
        # 3. 输出核心摘要
        print("\n" + "="*85)
        print(f"📊 统计摘要 | 总期数: {total} | 五不同出现: {wu_count}次 | 出现频率: {wu_count/total*100:.2f}%")
        print(f"💡 理论参考: 排列五五不同理论概率 ≈ 30.24%（10×9×8×7×6 / 10^5）")
        print("="*85)
        
        if not segments:
            print("\n✅ 恭喜！历史数据中无任何遗漏段（每期均为五不同，极罕见）")
            return
        
        # 4. 找出最大遗漏段（可能多段同最大值）
        max_len = max(seg['length'] for seg in segments)
        max_segments = [s for s in segments if s['length'] == max_len]
        
        # 5. 输出最大遗漏详情
        print(f"\n🔥【历史最大遗漏】{max_len}期（共{len(max_segments)}段达到此长度）")
        print(f"{'序号':<6}{'开始期号':<15}{'结束期号':<15}{'回补期号/状态':<25}{'状态'}")
        print("-"*85)
        for i, seg in enumerate(max_segments, 1):
            status_icon = '🟢 已回补' if seg['status'] == '已结束' else '🔴 进行中'
            print(f"{i:<6}{seg['start_period']:<15}{seg['end_period']:<15}"
                  f"{seg['recovery_period']:<25}{status_icon}")
        
        # 6. 当前遗漏情况（高亮）
        current_seg = next((s for s in segments if s['status'] == '进行中'), None)
        if current_seg:
            print(f"\n⚠️【当前遗漏】{current_seg['length']}期（{current_seg['start_period']} → {current_seg['end_period']}）")
            if current_seg['length'] >= max_len:
                print(f"   💥 已持平/突破历史最大遗漏！回补概率显著提升")
            elif current_seg['length'] > max_len * 0.8:
                print(f"   ⚡ 接近历史最大遗漏（{max_len}期），需重点关注")
        else:
            print(f"\n✅【当前状态】最新期已开出五不同，无进行中遗漏")
        
        # 7. 补充分析：遗漏分布
        print("\n📈 遗漏分布统计:")
        thresholds = [30, 40, 50, 60, 70, 80, 90, 100]
        for th in thresholds:
            count = sum(1 for s in segments if s['length'] >= th and s['status'] == '已结束')
            if count > 0:
                print(f"   • 遗漏≥{th}期: {count}段")
        
        # 8. 导出选项
        export = input("\n💾 导出完整遗漏段数据到CSV? (y/n): ").strip().lower()
        if export in ('y', 'yes'):
            filename = f"排列五五不同遗漏_{datetime.now().strftime('%Y%m%d')}.csv"
            with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['序号', '遗漏长度(期)', '开始期号', '结束期号', '回补期号', '状态', '分析时间'])
                for i, seg in enumerate(segments, 1):
                    writer.writerow([
                        i,
                        seg['length'],
                        seg['start_period'],
                        seg['end_period'],
                        seg['recovery_period'],
                        seg['status'],
                        datetime.now().strftime('%Y-%m-%d %H:%M')
                    ])
            print(f"✅ 已导出: {filename} | 共{len(segments)}条遗漏段记录")
            print("   • 字段说明: '回补期号'为'进行中（未回补）'表示当前仍在遗漏中")
        
        print("\n" + "="*85)
        print("✅ 分析完成 | 数据纯净度: 100%")
        print("💡 专业解读:")
        print("   • 五不同理论概率30.24%，长期看约3.3期出现1次")
        print("   • 遗漏≥60期属极端冷态（概率<0.1%），历史罕见")
        print("   • 当前遗漏接近历史最大值时，回补预期显著增强")
        print("="*85)
    
    except Exception as e:
        print(f"\n❌ 执行出错: {type(e).__name__} - {str(e)}")
        print("\n🔍 调试建议:")
        print("   1. 确认数据文件为'allpaiwu.csv'且含'期号,开奖号码'列")
        print("   2. 检查开奖号码是否为5位数字（如'12345'）")
        print("   3. 查看上方'样本验证'输出确认数据加载成功")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()