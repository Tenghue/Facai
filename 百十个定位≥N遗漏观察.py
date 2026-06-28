import pandas as pd
import os

def analyze_cross_position_phenomenon(file_path, threshold=56):
    # 1. 读取与预处理数据
    if not os.path.exists(file_path):
        print(f"错误：找不到文件 '{file_path}'")
        return

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"读取CSV失败: {e}")
        return

    if '期号' not in df.columns or '开奖号码' not in df.columns:
        print("错误：CSV必须包含 '期号' 和 '开奖号码' 两列")
        return

    # 拆分数字
    def split_digits(code_str):
        code_str = str(code_str).strip()
        digits = [c for c in code_str if c.isdigit()]
        if len(digits) >= 3:
            return int(digits[0]), int(digits[1]), int(digits[2])
        return None, None, None

    splits = df['开奖号码'].apply(split_digits)
    df['百位'] = splits.apply(lambda x: x[0])
    df['十位'] = splits.apply(lambda x: x[1])
    df['个位'] = splits.apply(lambda x: x[2])

    df.dropna(subset=['百位', '十位', '个位'], inplace=True)
    df[['百位', '十位', '个位']] = df[['百位', '十位', '个位']].astype(int)

    print(f"数据加载完成，共 {len(df)} 期有效数据。")
    print(f"分析目标：当某位置数字遗漏 > {threshold} 期时，该数字在其他位置的跨位现象。\n")

    # 2. 初始化统计容器
    # 结构: {数字0-9: {百位: {trigger: 0, hit: 0}, 十位: {...}, 个位: {...}}}
    stats = {d: {pos: {'trigger': 0, 'hit': 0} for pos in ['百位', '十位', '个位']} for d in range(10)}
    
    # 记录当前遗漏值：{位置: {数字: 当前遗漏期数}}
    current_omission = {pos: {d: 0 for d in range(10)} for pos in ['百位', '十位', '个位']}
    
    other_positions_map = {
        '百位': ['十位', '个位'],
        '十位': ['百位', '个位'],
        '个位': ['百位', '十位']
    }

    # 3. 逐行遍历统计
    for index, row in df.iterrows():
        cur_nums = {'百位': row['百位'], '十位': row['十位'], '个位': row['个位']}

        # 检查每个位置
        for pos in ['百位', '十位', '个位']:
            digit = cur_nums[pos]

            # A. 判断是否触发大遗漏
            if current_omission[pos][digit] > threshold:
                stats[digit][pos]['trigger'] += 1

                # B. 检查其他位置是否出现了该数字
                for other_pos in other_positions_map[pos]:
                    if cur_nums[other_pos] == digit:
                        stats[digit][pos]['hit'] += 1
                        break  # 只要其他位置有一个出了就算命中，不重复计数

            # C. 更新遗漏状态
            for d in range(10):
                if d == digit:
                    current_omission[pos][d] = 0
                else:
                    current_omission[pos][d] += 1

    # 4. 打印详细现象报告
    print("="*70)
    print("【跨位现象详细报告】（遗漏 > {} 期）".format(threshold))
    print("="*70)
    
    total_trigger = 0
    total_hit = 0
    
    for d in range(10):
        print(f"\n🔢 针对数字 [{d}] 的跨位表现：")
        print("-" * 40)
        for pos in ['百位', '十位', '个位']:
            t = stats[d][pos]['trigger']
            h = stats[d][pos]['hit']
            rate = (h / t * 100) if t > 0 else 0
            
            total_trigger += t
            total_hit += h
            
            if t > 0:
                print(f"  当 [{pos}] 遗漏>{threshold}期时: 触发 {t} 次, 跨位命中 {h} 次, 频率: {rate:.2f}%")
            else:
                print(f"  当 [{pos}] 遗漏>{threshold}期时: 历史未触发")
                
    print("\n" + "="*70)
    print("【全局综合现象】")
    overall_rate = (total_hit / total_trigger * 100) if total_trigger > 0 else 0
    print(f"  总触发次数: {total_trigger} 次")
    print(f"  总跨位命中次数: {total_hit} 次")
    print(f"  综合跨位频率: {overall_rate:.2f}% （理论随机期望值约为 20.00%）")
    print("="*70)

if __name__ == "__main__":
    # 修改阈值只需改这里的数字，比如改成 56
    analyze_cross_position_phenomenon("allpaisan.csv", threshold=56)