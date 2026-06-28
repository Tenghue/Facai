import pandas as pd
import numpy as np
import os

def analyze_cold_number_companions(file_path='allpaisan.csv', target_num=8, window=100):
    """
    从组选角度分析：当目标数字在近N期表现低迷时，其他数字的表现特征。
    """
    # 1. 读取数据
    if not os.path.exists(file_path):
        print(f"错误：找不到文件 {file_path}")
        return

    try:
        df = pd.read_csv(file_path)
        print(f"成功读取 {len(df)} 期数据。")
    except Exception as e:
        print(f"读取失败: {e}")
        return

    # 2. 数据预处理：将 '开奖号码' 拆解为三个独立的数字列
    # 假设 '开奖号码' 是整数(358)或字符串("358")
    try:
        # 统一转为字符串，不足3位的补0（虽然排列三通常是3位）
        codes = df['开奖号码'].astype(str).str.zfill(3)

        # 提取百、十、个位（组选分析其实不需要严格区分位置，但为了统计方便我们拆开）
        df['d1'] = codes.str[0].astype(int)
        df['d2'] = codes.str[1].astype(int)
        df['d3'] = codes.str[2].astype(int)

        # 标记当期是否包含目标数字（组选视角：只要有一个位置是8就算出现）
        df['has_target'] = ((df['d1'] == target_num) |
                            (df['d2'] == target_num) |
                            (df['d3'] == target_num)).astype(int)

        # 标记当期是否为组三（有重复数字）
        df['is_group3'] = ((df['d1'] == df['d2']) | (df['d1'] == df['d3']) | (df['d2'] == df['d3'])).astype(int)

    except Exception as e:
        print(f"数据处理出错，请检查CSV中'开奖号码'列格式是否正确: {e}")
        return

    # 3. 计算滚动频次（判断是否低迷）
    # rolling(window) 计算过去 window 期的总和
    df['rolling_count'] = df['has_target'].rolling(window=window).sum()

    # 设定低迷阈值：比如近100期，理论上8号应该出现约 27次 (1-(9/10)^3 * 100)。
    # 如果实际出现次数 < 15次 (约一半)，视为极度低迷。你可以调整这个系数。
    low_freq_threshold = window * 0.15

    # 筛选出所有处于“低迷状态”的行（忽略前 window-1 行因为数据不足）
    cold_mask = df['rolling_count'] < low_freq_threshold
    # 排除掉刚开始数据不够的情况
    cold_mask.iloc[:window] = False

    cold_periods = df[cold_mask]

    if len(cold_periods) == 0:
        print(f"\n未检测到近 {window} 期内 {target_num} 号有明显低迷现象（出现次数均 >= {low_freq_threshold}）。")
        return

    print(f"\n>>> 分析结果：在 {target_num} 号低迷的 {len(cold_periods)} 期中 <<<")

    # --- 分析 1：谁是高频替代者？ ---
    # 统计这 periods 里，0-9 每个数字出现的总次数（不分位置，直接统计 d1,d2,d3 三列的总和）
    all_nums_in_cold = pd.concat([cold_periods['d1'], cold_periods['d2'], cold_periods['d3']])
    freq_stats = all_nums_in_cold.value_counts().sort_index()

    # 找出除了 target_num 之外出现最多的数字
    other_nums_freq = freq_stats.drop(target_num, errors='ignore')
    hot_partner = other_nums_freq.idxmax()
    hot_count = other_nums_freq.max()

    print(f"1. 【高频替代者】：当 {target_num} 缺失时，数字 [{hot_partner}] 表现最活跃，共出现 {hot_count} 次。")

    # --- 分析 2：谁是连坐受害者（跟着一起冷）？ ---
    cold_partner = other_nums_freq.idxmin()
    cold_count = other_nums_freq.min()
    print(f"2. 【连坐受害者】：当 {target_num} 缺失时，数字 [{cold_partner}] 也极少出现，仅出现 {cold_count} 次。")

    # --- 分析 3：组三（对子）倾向 ---
    group3_ratio = cold_periods['is_group3'].mean()
    print(f"3. 【形态倾向】：在 {target_num} 低迷期间，开出【组三】（对子）的比例为 {group3_ratio:.2%}。")
    if group3_ratio > 0.30:
        print("   -> 提示：该比例高于理论值(27%)，说明冷号期间容易出对子防守。")
    else:
        print("   -> 提示：该比例正常或偏低，组六形态为主。")

    # --- 分析 4：具体哪两个位置最爱出热号？（可选补充） ---
    # 虽然你是组选思维，但看看热号喜欢落在哪个位置也有参考价值
    pos_stats = {
        '百位': cold_periods['d1'].value_counts(),
        '十位': cold_periods['d2'].value_counts(),
        '个位': cold_periods['d3'].value_counts()
    }
    print(f"\n4. 【热号分布细节】：热号 [{hot_partner}] 在这期间的分布：")
    for pos_name, stats in pos_stats.items():
        count = stats.get(hot_partner, 0)
        print(f"   - {pos位}: {count} 次")

if __name__ == "__main__":
    # 配置区
    FILE_PATH = 'allpaisan.csv'  # 确保文件名一致
    TARGET_NUM = 8               # 你想分析的数字
    WINDOW_SIZE = 100            # 观察窗口大小

    analyze_cold_number_companions(FILE_PATH, TARGET_NUM, WINDOW_SIZE)