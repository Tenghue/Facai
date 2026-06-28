import pandas as pd
import os
from collections import Counter

def analyze_multi_pair_followers(file_path, pair_list):
    # 1. 读取与清洗数据
    if not os.path.exists(file_path):
        print(f"❌ 错误：找不到文件 {file_path}")
        return

    # 自动识别编码
    df = None
    for enc in ['utf-8', 'gbk', 'gb2312']:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            break
        except: continue
    
    if df is None:
        print("❌ 无法读取文件")
        return

    # 识别号码列
    target_col = None
    cols_lower = [str(c).lower() for c in df.columns]
    for kw in ['num', 'code', 'kaijiang', '号码', 'result']:
        for i, c in enumerate(cols_lower):
            if kw in c:
                target_col = df.columns[i]
                break
        if target_col: break
    if not target_col: target_col = df.columns[-1]

    # 清洗号码
    def clean_num(x):
        try: return str(int(float(x))).zfill(3)
        except: return str(x).zfill(3)
    df['clean_num'] = df[target_col].apply(clean_num)
    numbers = df['clean_num'].tolist()
    total_draws = len(numbers)
    
    print(f"🚀 正在分析 {len(pair_list)} 个二码的后3期跟随关系...")

    # 2. 核心统计逻辑
    # 用于存储每个二码的统计结果
    all_results = {}
    # 用于存储所有二码的汇总数据（共同出现的频率）
    total_counter = Counter()
    total_triggers = 0

    for pair_str in pair_list:
        # 处理输入的二码
        try:
            input_digits = set(int(d) for d in pair_str)
            if len(input_digits) != 2: continue
            
            pair_key = f"{min(input_digits)}{max(input_digits)}"
            follower_counter = Counter()
            trigger_count = 0
            
            # 遍历每一期
            for i in range(total_draws - 3):
                current_num = numbers[i]
                current_digits = set(int(d) for d in current_num)
                
                # 判断当前期是否包含输入的二码
                if input_digits.issubset(current_digits):
                    trigger_count += 1
                    
                    # 获取后3期的数字
                    next_3_digits = set()
                    for j in range(1, 4):
                        next_num = numbers[i+j]
                        next_3_digits.update(int(d) for d in next_num)
                    
                    # 统计跟随关系
                    follower_counter.update(next_3_digits)
                    # 累加到总表
                    total_counter.update(next_3_digits)
                    total_triggers += 1
            
            # 保存该二码的结果
            all_results[pair_key] = {
                'counter': follower_counter,
                'triggers': trigger_count,
                'top_digit': follower_counter.most_common(1)[0] if follower_counter else None
            }
            
        except ValueError:
            continue

    # 3. 输出详细结果
    print("-" * 70)
    print(f"📊 各二码后3期高频跟随统计详情")
    print("-" * 70)
    
    for pair, data in all_results.items():
        if data['triggers'] == 0:
            print(f"二码 {pair}: 历史出现次数太少，无法统计。")
            continue
            
        top_digit, top_count = data['top_digit']
        prob = (top_count / data['triggers']) * 100
        print(f"二码 [{pair}]: 后3期最热独码是【 {top_digit} 】，出现 {top_count} 次 (概率 {prob:.2f}%)")
    
    # 4. 输出汇总结果
    print("-" * 70)
    print(f"🔥 综合汇总报告 (所有输入二码的共振分析)")
    print("-" * 70)
    print(f"总触发次数: {total_triggers} 次")
    print("-" * 70)
    print(f"{'排名':<6} {'跟随独码':<10} {'总出现次数':<12} {'综合概率'}")
    print("-" * 70)
    
    if total_triggers == 0:
        print("无有效数据。")
        return

    # 计算综合概率：该数字在所有触发后的后3期出现的总频率
    top_10 = total_counter.most_common(10)
    for rank, (digit, count) in enumerate(top_10, 1):
        # 综合概率 = 出现次数 / 总触发次数
        prob = (count / total_triggers) * 100
        print(f"{rank:<6} {digit:<10} {count:<12} {prob:.2f}%")
        
    print("-" * 70)
    print(f"💡 结论:")
    if top_10:
        print(f"   综合来看，当输入的三个二码出现时，后3期内数字【 {top_10[0][0]} 】是最强跟随者。")
        print(f"   建议重点关注：{', '.join([str(x[0]) for x in top_10[:3]])}")
    print("-" * 70)

# --- 运行入口 ---
if __name__ == "__main__":
    # 在这里输入您想查询的三个二码
    # 例如：["18", "23", "59"]
    user_pairs_input = input("请输入三个组选二码，用空格分隔 (例如 18 23 59): ").strip()
    user_pairs = user_pairs_input.split()
    
    if len(user_pairs) != 3:
        print("⚠️ 请输入正好三个二码。")
    else:
        analyze_multi_pair_followers('all3D.csv', user_pairs)
    
    input("\n按回车键退出...")