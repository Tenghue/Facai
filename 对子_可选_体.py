import pandas as pd
import os
from collections import Counter

def analyze_group3_followers(file_path, input_digit):
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

    # 识别期号列
    issue_col = None
    cols_lower = [str(c).lower() for c in df.columns]
    for kw in ['issue', '期号', '期', 'date', 'time', 'no']:
        for i, c in enumerate(cols_lower):
            if kw in c:
                issue_col = df.columns[i]
                break
        if issue_col: break
    if not issue_col: issue_col = df.columns[0]

    # 识别号码列
    target_col = None
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
    
    # 提取期号和号码列表
    issue_list = df[issue_col].tolist()
    numbers = df['clean_num'].tolist()
    total_draws = len(numbers)
    
    print(f"🚀 正在分析独码【{input_digit}】的组三(AA)形态后3期走势...")

    # 2. 核心统计逻辑
    # 检查是否为组三且包含输入独码
    def is_group3_with_digit(num_str, digit):
        digits = [int(d) for d in num_str]
        # 判断是否为组三（有两个数字相同）
        if digits[0] == digits[1] or digits[1] == digits[2] or digits[0] == digits[2]:
            # 判断是否包含指定独码
            if int(digit) in digits:
                return True
        return False

    follower_counter = Counter()
    trigger_count = 0
    
    # 遍历每一期（留出3期作为观察窗口）
    for i in range(total_draws - 3):
        current_num = numbers[i]
        
        # 判断当前期是否为 AA 形态且包含输入独码
        if is_group3_with_digit(current_num, input_digit):
            trigger_count += 1
            
            # 获取后3期的数字
            next_3_digits = set()
            for j in range(1, 4): # 后1期，后2期，后3期
                next_num = numbers[i+j]
                next_3_digits.update(int(d) for d in next_num)
            
            # 统计跟随关系
            follower_counter.update(next_3_digits)

    # 3. 输出结果
    print("-" * 70)
    print(f"📊 组三(AA)后3期高频跟随统计报告")
    print("-" * 70)
    print(f"输入独码: {input_digit}")
    print(f"触发条件: 开出包含 {input_digit} 的组三号码 (如 {input_digit}{input_digit}X)")
    print(f"触发次数: {trigger_count} 次")
    print("-" * 70)
    
    if trigger_count == 0:
        print("⚠️ 历史数据中该形态出现次数太少或没有，无法统计。")
        return

    print(f"{'排名':<6} {'跟随独码':<10} {'出现次数':<10} {'概率(相对触发次数)'}")
    print("-" * 70)
    
    top_10 = follower_counter.most_common(10)
    for rank, (digit, count) in enumerate(top_10, 1):
        # 概率计算：该数字在后3期出现的总次数 / 触发次数
        prob = (count / trigger_count) * 100
        print(f"{rank:<6} {digit:<10} {count:<10} {prob:.2f}%")
        
    print("-" * 70)
    print(f"💡 结论:")
    if top_10:
        print(f"   当开出包含 {input_digit} 的组三形态后，后3期内数字【 {top_10[0][0]} 】出现频率最高。")
        print(f"   建议重点关注：{', '.join([str(x[0]) for x in top_10[:3]])}")
    print("-" * 70)

# --- 运行入口 ---
if __name__ == "__main__":
    user_digit = input("请输入要查询的独码 (0-9): ").strip()
    if user_digit not in [str(i) for i in range(10)]:
        print("❌ 请输入0-9之间的数字。")
    else:
        analyze_group3_followers('allpaisan.csv', user_digit)
    
    input("\n按回车键退出...")