import pandas as pd

def find_group_miss_after_direct_cold(file_path, direct_threshold=55, group_target=13):
    """
    探寻真实历史案例：当某数字在某位置直选遗漏 > direct_threshold 后，
    其组选遗漏是否曾持续超过 group_target 期。
    
    参数:
        file_path: CSV文件路径
        direct_threshold: 直选遗漏触发阈值（默认55）
        group_target: 组选遗漏目标阈值（默认13）
    """
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ 读取CSV失败: {e}")
        return

    # 1. 数据预处理：拆分百、十、个位
    if '开奖号码' not in df.columns:
        print("❌ 错误：CSV中未找到 '开奖号码' 列")
        return

    def parse_three_digits(x):
        s = str(x).strip()
        digits = [int(i) for i in s if i.isdigit()]
        return pd.Series(digits[:3])

    df[['百位', '十位', '个位']] = df['开奖号码'].apply(parse_three_digits)
    df.dropna(subset=['百位', '十位', '个位'], inplace=True)
    df[['百位', '十位', '个位']] = df[['百位', '十位', '个位']].astype(int)

    positions = ['百位', '十位', '个位']

    # 初始化状态追踪器
    direct_miss = {d: {p: 0 for p in positions} for d in range(10)}  # 直选遗漏
    group_miss = {d: 0 for d in range(10)}                           # 组选遗漏

    # 观察名单：记录哪些数字正处于“直选>55”的极冷观察期
    # 格式: {数字: {'触发位置': pos, '触发时直选遗漏': val, '进入观察时组选遗漏': g}}
    in_watch = {}

    results = []  # 存储所有符合条件的事件

    print(f"\n🔍 开始扫描 {file_path}...")
    print(f"🎯 目标：直选遗漏 > {direct_threshold} 期间，组选遗漏 > {group_target} 的真实案例")
    print("-" * 90)

    # 2. 逐行扫描
    for idx, row in df.iterrows():
        period = row.get('期号', f"P{idx+1}")  # 兼容无期号列
        nums = [row['百位'], row['十位'], row['个位']]
        appeared = set(nums)

        # ===== 第一步：检查观察名单中的数字是否达成组选>target =====
        # 注意：此检查必须在更新本期数据前进行！
        for digit in list(in_watch.keys()):
            if group_miss[digit] > group_target:
                info = in_watch[digit]
                results.append({
                    '期号': period,
                    '数字': digit,
                    '触发位置': info['pos'],
                    '触发时直选遗漏': info['direct_val'],
                    '当前组选遗漏': group_miss[digit],
                    '观察期已持续': group_miss[digit] - info['start_group_miss']
                })

        # ===== 第二步：更新遗漏计数器 =====
        for d in range(10):
            hit_anywhere = False

            # 更新直选遗漏
            for p, val in zip(positions, nums):
                if val == d:
                    direct_miss[d][p] = 0
                    hit_anywhere = True
                else:
                    direct_miss[d][p] += 1

            # 更新组选遗漏
            if hit_anywhere:
                group_miss[d] = 0
                # 关键：如果该数字开出了，且正在观察中，立即移除
                if d in in_watch:
                    del in_watch[d]
            else:
                group_miss[d] += 1

                # 关键：如果尚未在观察中，且直选遗漏刚好突破阈值（即等于 threshold+1），则加入观察
                if d not in in_watch:
                    for p in positions:
                        if direct_miss[d][p] == direct_threshold + 1:
                            in_watch[d] = {
                                'pos': p,
                                'direct_val': direct_miss[d][p],
                                'start_group_miss': group_miss[d]  # 记录进入观察池时的组选遗漏基数
                            }
                            break

    # 3. 输出结果
    print("\n" + "="*90)
    if not results:
        print(f"✅ 未发现任何案例：在直选遗漏 > {direct_threshold} 的期间内，组选遗漏从未超过 {group_target} 期。")
        print("→ 这说明‘单点极冷’并未引发‘全局极冷’（组选>13）。")
    else:
        print(f"🎉 共发现 {len(results)} 个真实案例！以下是按组选遗漏降序排列的 Top 10：")
        res_df = pd.DataFrame(results)
        res_df.sort_values(by='当前组选遗漏', ascending=False, inplace=True)
        print(res_df.head(10).to_string(index=False))

        # 额外提示：最大值
        max_row = res_df.iloc[0]
        print(f"\n📌 极值案例：数字 {max_row['数字']} 在 {max_row['触发位置']} 位置直选遗漏 {max_row['触发时直选遗漏']} 期后，")
        print(f"   组选遗漏最高达到 {max_row['当前组选遗漏']} 期，持续了 {max_row['观察期已持续']} 期！")

    print("="*90)

# === ✅ 正确的执行入口 ===
if __name__ == "__main__":
    # 请确保 allpaisan.csv 与本脚本在同一目录下
    file_path = "allpaisan.csv"
    find_group_miss_after_direct_cold(file_path, direct_threshold=55, group_target=13)