import pandas as pd
from collections import defaultdict
import os


def get_zuxuan_duizi_digit(code):
    """
    从组选角度提取对子号中的"对子数字"
    例如: '122','212','221' -> 返回 '2' (组选122的对子数字)
         '005','050','500' -> 返回 '0' (组选005的对子数字)
         '123'(组六), '111'(豹子) -> 返回 None
    """
    digits = sorted(code)
    if digits[0] == digits[1] and digits[1] != digits[2]:
        return digits[0]  # AAB型，A是对子数字
    elif digits[1] == digits[2] and digits[0] != digits[1]:
        return digits[2]  # BAA型，A是对子数字
    return None  


def calc_duizi_miss(csv_file='all3D.csv'):
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"找不到文件: {csv_file}，请将CSV文件放在脚本同级目录")

    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    code_col = next((c for c in df.columns if any(k in c for k in ['开奖号码', '号码', 'Number'])), None)
    if not code_col:
        raise ValueError("未找到开奖号码列，请检查CSV表头是否包含'开奖号码/号码/Number'")

    # 解析所有有效3位号码（按期号正序）
    codes = []
    for _, row in df.iterrows():
        clean = ''.join(c for c in str(row[code_col]) if c.isdigit())
        padded = clean.zfill(3)[:3] if len(clean) <= 3 else clean[:3]
        if len(padded) == 3:
            codes.append(padded)

    if not codes:
        raise ValueError("CSV中未解析到有效的3位开奖号码")

    total_periods = len(codes)
    # 记录每个数字(0-9)作为对子数字最近一次出现的期号索引(0-based)
    last_appear = {str(d): -1 for d in range(10)}
    miss_values = {}

    # 遍历所有历史开奖，更新每个对子数字的最后出现位置
    for idx, code in enumerate(codes):
        duizi_digit = get_zuxuan_duizi_digit(code)
        if duizi_digit is not None:
            last_appear[duizi_digit] = idx

    # 计算遗漏值：当前总期数 - 最后出现期号 - 1
    # 若某数字从未以对子形式出现，则遗漏值=总期数
    print(f"📊 历史总期数: {total_periods}")
    print("=" * 40)
    print(f"{'数字':<6}{'对子遗漏期数':<15}{'备注'}")
    print("-" * 40)
    for digit in range(10):
        d = str(digit)
        last_idx = last_appear[d]
        if last_idx == -1:
            miss = total_periods
            remark = "从未以对子形式出现"
        else:
            miss = total_periods - last_idx - 1
            remark = f"上次出现在第{last_idx + 1}期"
        miss_values[d] = miss
        print(f"{d:<6}{miss:<15}{remark}")
    print("=" * 40)

    return miss_values


if __name__ == "__main__":
    try:
        calc_duizi_miss('all3D.csv')
    except Exception as e:
        import traceback
        print(f"❌ 错误: {e}")
        traceback.print_exc()