import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from collections import Counter

# ================== 配置区域 ==================
FILE_PATH = 'allpaisan.csv'   # 您的数据文件名
TARGET_CODE = [0, 5]          # 【重点】这里可以填对子，如 [1, 1], [0, 0]；也可以是普通二码 [1, 5]
MAX_SHOW_PERIODS = None       # 图表只显示最近多少期 (设为 None 则显示全部历史)
# ==============================================

def load_and_clean_csv(file_path):
    """
    智能读取CSV文件，解决编码、特殊字符和列名不匹配的问题
    """
    if not os.path.exists(file_path):
        print(f"❌ 错误：找不到文件 {file_path}")
        return None

    df = None
    # 尝试多种编码读取，防止乱码
    for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if df is None:
        print("❌ 无法读取文件，请检查文件是否损坏或格式异常。")
        return None

    # --- 清洗表头 (去除空格、#号等干扰字符) ---
    original_cols = list(df.columns)
    clean_cols = []
    for col in original_cols:
        c = str(col).strip().replace('#', '').replace(' ', '')
        clean_cols.append(c)
    df.columns = clean_cols

    # --- 识别关键列 ---
    period_col = None
    code_col = None

    for col in df.columns:
        lower_col = col.lower()
        # 识别期号
        if any(k in lower_col for k in ['期', 'issue', 'period', 'no']):
            period_col = col
        # 识别开奖号
        elif any(k in lower_col for k in ['号', 'code', 'result', 'num']):
            code_col = col

    if not period_col or not code_col:
        print(f"⚠️ 无法自动识别列名。当前识别到的列: {list(df.columns)}")
        return None

    print(f"✅ 成功加载数据: {len(df)} 期 | 期号列: [{period_col}] | 号码列: [{code_col}]")

    # --- 拆分号码为列表 (保留重复数字，这对对子判断至关重要) ---
    def split_code(code_str):
        try:
            s = str(int(code_str)).zfill(3)
            return [int(s[0]), int(s[1]), int(s[2])]
        except:
            return [0, 0, 0]

    df['digits'] = df[code_col].apply(split_code)
    return df, period_col

def check_hit(draw_digits, target_list):
    """
    核心算法：检查开奖号是否包含目标二码（支持对子）
    原理：统计频次。只有当 开奖号中某数字的数量 >= 目标中该数字的数量 时，才算满足条件。
    """
    draw_counts = Counter(draw_digits)
    target_counts = Counter(target_list)

    # 遍历目标二码中的每一个数字及其需要的数量
    for num, needed_count in target_counts.items():
        if draw_counts.get(num, 0) < needed_count:
            return False
    return True

def calculate_group_omission(df, period_col, target_code):
    """
    计算遗漏值
    """
    omission_list = []
    current_omission = 0
    results = []

    print(f"\n🔍 正在计算组选 {'对子' if target_code[0]==target_code[1] else '二码'} [{target_code}] 的遗漏...")

    for idx, row in df.iterrows():
        draw_nums = row['digits']

        # 使用新的核心算法判断
        if check_hit(draw_nums, target_code):
            # 命中
            results.append({
                'period': row[period_col],
                'omission': current_omission,
                'hit': True
            })
            current_omission = 0
        else:
            # 未命中
            current_omission += 1

    res_df = pd.DataFrame(results)

    # 统计数据
    if len(res_df) > 0:
        avg_omission = res_df['omission'].mean()
        max_omission = res_df['omission'].max()
    else:
        avg_omission = 0
        max_omission = 0

    print(f"📊 统计结果:")
    print(f"   历史出现次数: {len(res_df)}")
    print(f"   平均遗漏: {avg_omission:.2f} 期")
    print(f"   最大遗漏: {max_omission} 期")
    print(f"   当前遗漏: {current_omission} 期 (截至数据末尾)")

    return res_df, avg_omission, max_omission, current_omission

def plot_omission_chart(data_df, avg_om, max_om, current_om, target_code):
    """
    绘制带期号的遗漏走势图
    """
    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    # 截取最近 N 期数据
    display_data = data_df.tail(MAX_SHOW_PERIODS).copy() if MAX_SHOW_PERIODS else data_df.copy()

    if display_data.empty:
        print("没有足够的数据绘图。")
        return

    # 动态调整画布宽度，保证期号不拥挤
    width = max(14, len(display_data) * 0.6)
    plt.figure(figsize=(width, 7))

    # 判断是否为对子，决定柱子颜色
    is_pair = (target_code[0] == target_code[1])
    bar_color = '#FF9F43' if is_pair else '#54A0FF' # 对子用橙色，普通用蓝色
    title_prefix = "组选对子" if is_pair else "组选二码"

    # 绘制柱状图
    x_pos = range(len(display_data))
    plt.bar(x_pos, display_data['omission'], color=bar_color, alpha=0.8, label='遗漏值')

    # 绘制参考线
    plt.axhline(y=avg_om, color='green', linestyle='--', linewidth=1.5, label=f'平均遗漏 ({avg_om:.1f})')
    plt.axhline(y=max_om, color='red', linestyle='--', linewidth=1.5, label=f'历史最大遗漏 ({max_om})')

    # 标注最高点
    if not display_data.empty:
        max_idx = display_data['omission'].idxmax()
        # 注意：这里的 max_idx 是 display_data 的索引，需要转换为相对位置
        relative_max_idx = display_data.index.get_loc(max_idx)
        max_val = display_data.loc[max_idx, 'omission']
        plt.text(relative_max_idx, max_val + 1, f"{int(max_val)}",
                 ha='center', va='bottom', color='red', fontweight='bold')

    # === 关键修改：X轴显示所有期号 ===
    plt.xticks(ticks=x_pos, labels=display_data['period'], rotation=90, fontsize=8)

    plt.title(f'{title_prefix} [{target_code[0]}, {target_code[1]}] 遗漏走势 (近{len(display_data)}期)', fontsize=16)
    plt.xlabel('开奖期号', fontsize=12)
    plt.ylabel('遗漏期数', fontsize=12)
    plt.grid(axis='y', linestyle=':', alpha=0.5)
    plt.legend()

    # 添加文本注释框
    textstr = f'当前遗漏: {current_om}\n平均: {avg_om:.1f}\n极值: {max_om}'
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    plt.text(0.02, 0.95, textstr, transform=plt.gca().transAxes, fontsize=12,
             verticalalignment='top', bbox=props)

    plt.tight_layout()
    plt.show()

# ================== 主程序执行 ==================
if __name__ == "__main__":
    # 1. 读取数据
    result = load_and_clean_csv(FILE_PATH)
    if result is None:
        exit()
    df, period_col = result

    # 2. 计算遗漏
    result_df, avg_o, max_o, curr_o = calculate_group_omission(df, period_col, TARGET_CODE)

    # 3. 绘图
    if not result_df.empty:
        plot_omission_chart(result_df, avg_o, max_o, curr_o, TARGET_CODE)
    else:
        print("未找到任何匹配记录，无法绘图。")