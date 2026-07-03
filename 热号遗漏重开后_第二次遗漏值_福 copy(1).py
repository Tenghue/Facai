import csv
import os
from collections import defaultdict
import statistics

def read_and_sort_data(filename):
    """读取CSV文件"""
    if not os.path.exists(filename):
        print(f"❌ 错误：文件 '{filename}' 不存在！")
        return [], []
    
    records = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if '期号' not in reader.fieldnames or '开奖号码' not in reader.fieldnames:
                print(f"⚠️ 警告：CSV表头缺失！需包含'期号'和'开奖号码'")
                return [], []
            
            for row in reader:
                period = row.get('期号', '').strip()
                code = row.get('开奖号码', '').strip()
                if period and code and len(code) == 3:
                    records.append((period, code))
        
        records.sort(key=lambda x: x[0])
        periods = [r[0] for r in records]
        codes = [r[1] for r in records]
        print(f"✅ 成功加载 {len(records)} 期数据")
        return periods, codes
    except Exception as e:
        print(f"❌ 读取文件出错: {e}")
        return [], []

def analyze_hot_streaks(periods, codes):
    """统计0-9每个号码「连续热出≥3期」的事件及「第二次遗漏值」"""
    if not periods:
        print("⚠️ 无有效数据，分析终止")
        return

    total_draws = len(periods)
    print("\n" + "="*60)
    print("🔍 排列三组选单码「连续热出≥3期」事件统计")
    print("="*60)

    # 原有功能：统计「连续热出≥3期」事件
    digit_event_summary = {str(d): [] for d in range(10)}
    for digit in range(10):
        d_str = str(digit)
        print(f"\n--- 分析数字 [{digit}] ---")
        
        appears = [d_str in code for code in codes]
        
        i = 0
        event_count = 0
        while i < total_draws:
            if not appears[i]:
                i += 1
                continue
            
            start_idx = i
            while i < total_draws and appears[i]:
                i += 1
            end_idx = i - 1
            streak_len = end_idx - start_idx + 1
            
            if streak_len >= 3:
                event_count += 1
                start_period = periods[start_idx]
                end_period = periods[end_idx]
                
                event_info = {
                    'start_period': start_period,
                    'end_period': end_period,
                    'streak_len': streak_len
                }
                digit_event_summary[d_str].append(event_info)
                
                print(f"  事件{event_count}: {start_period} → {end_period} (连续{streak_len}期)")

        print(f"  -> 共发现 {event_count} 次符合条件的事件")

    print("\n" + "="*60)
    print("📋 各数字「连续热出≥3期」事件数量总览")
    print("="*60)
    print(f"{'数字':<6}{'事件数量':<12}")
    print("-"*20)
    for d in range(10):
        cnt = len(digit_event_summary[str(d)])
        print(f"{d:<6}{cnt:<12}")
    print("="*60)

    # ========== 新增功能：统计并立即显示每个数字的「第二次遗漏值」 ==========
    print("\n" + "="*60)
    print("🔍 新增功能：「第二次遗漏值」统计与展示")
    print("="*60)
    
    for digit in range(10):
        d_str = str(digit)
        print(f"\n--- 数字 [{digit}] 的「第二次遗漏值」详细统计 ---")
        
        # 创建布尔数组
        appears = [d_str in code for code in codes]
        
        i = 0
        second_miss_values_for_this_digit = []
        trace_details = [] # 用于存储追踪详情，方便调试或展示
        
        while i < total_draws:
            if not appears[i]:
                i += 1
                continue
            
            # 发现连续出现的起点
            start_idx = i
            while i < total_draws and appears[i]:
                i += 1
            end_idx = i - 1
            streak_len = end_idx - start_idx + 1
            
            # 检查是否构成“热号”
            if streak_len >= 3:
                hot_end_index = end_idx # 热号结束的索引

                # 寻找“第一次重开”
                first_reopen_idx = -1
                j = hot_end_index + 1
                while j < total_draws:
                    if appears[j]:
                        first_reopen_idx = j
                        break
                    j += 1
                
                if first_reopen_idx == -1: # 没有第一次重开
                    continue

                # 寻找“第二次重开”
                second_reopen_idx = -1
                k = first_reopen_idx + 1
                while k < total_draws:
                    if appears[k]:
                        second_reopen_idx = k
                        break
                    k += 1
                
                if second_reopen_idx != -1: # 找到了第二次重开
                    second_miss_value = second_reopen_idx - first_reopen_idx - 1
                    second_miss_values_for_this_digit.append(second_miss_value)
                    trace_details.append({
                        '热号结束期': periods[hot_end_index],
                        '第一次重开期': periods[first_reopen_idx],
                        '第二次重开期': periods[second_reopen_idx],
                        '第二次遗漏值': second_miss_value
                    })
        
        # 统计并打印当前数字的「第二次遗漏值」
        count = len(second_miss_values_for_this_digit)
        if count > 0:
            # 打印追踪详情
            print(f"  找到 {count} 个「第二次重开」事件:")
            for detail in trace_details:
                print(f"    从 {detail['热号结束期']} -> {detail['第一次重开期']} -> {detail['第二次重开期']}, 遗漏值: {detail['第二次遗漏值']}")
            
            # 计算并打印统计数据
            avg_val = statistics.mean(second_miss_values_for_this_digit)
            max_val = max(second_miss_values_for_this_digit)
            min_val = min(second_miss_values_for_this_digit)
            print(f"\n  统计结果 -> 事件数: {count}, 平均值: {avg_val:.2f}, 最大值: {max_val}, 最小值: {min_val}")
        else:
            print(f"  未找到「第二次重开」事件，统计结果 -> 事件数: 0, 平均值: -, 最大值: -, 最小值: -")


def main():
    filename = 'all3D.csv'
    periods, codes = read_and_sort_data(filename)
    if periods:
        analyze_hot_streaks(periods, codes)

if __name__ == "__main__":
    main()