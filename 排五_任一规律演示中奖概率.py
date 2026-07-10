import pandas as pd
import os
from datetime import datetime  # ✅ 修复：添加此行

def load_and_validate_data(file_path='paiwu.csv'):
    """加载并验证CSV数据"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ 文件 '{file_path}' 不存在，请确认文件名和路径")
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')  # 兼容带BOM的UTF-8
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file_path, encoding='gbk')
        except Exception as e:
            raise ValueError(f"❌ 编码解析失败，请确保文件为UTF-8或GBK编码: {e}")
    
    # 智能列名校正
    col_map = {}
    for col in df.columns:
        clean = col.strip().replace(' ', '').replace('号码', '').replace('开奖', '').replace('期', '').lower()
        if '期' in col or 'draw' in clean or 'issue' in clean:
            col_map[col] = '期号'
        elif '开' in col or 'number' in clean or 'code' in clean or 'result' in clean:
            col_map[col] = '开奖号码'
    df = df.rename(columns=col_map)
    
    required_cols = ['期号', '开奖号码']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"❌ CSV必须包含列：'期号' 和 '开奖号码'（当前列: {list(df.columns)}）")
    
    # 清洗数据
    df = df.dropna(subset=required_cols)
    df['开奖号码'] = df['开奖号码'].astype(str).str.strip()
    df = df[df['开奖号码'].str.match(r'^\d{5}$')]  # 仅保留5位纯数字
    
    if len(df) < 3:
        raise ValueError(f"❌ 有效数据不足3期（当前{len(df)}期），无法执行策略回测")
    
    # 按期号排序（字符串排序适用于2017001格式）
    df = df.sort_values('期号').reset_index(drop=True)
    print(f"✅ 成功加载 {len(df)} 期有效数据 | 起始期: {df['期号'].iloc[0]} | 结束期: {df['期号'].iloc[-1]}")
    return df

def test_pailie5_strategy_from_csv(file_path='paiwu.csv', start_issue='2017001'):
    """
    主执行函数：读取CSV → 策略回测 → 输出明细与统计
    策略规则：
      - 万/千位：上上期+上期未出现的数字（0-9中缺失值）
      - 百位：上期开奖号的十位+个位（去重）
      - 十/个位：全包0-9
    """
    # =============== 数据加载 ===============
    df = load_and_validate_data(file_path)
    
    # 定位起始期（支持跳过早期数据）
    if start_issue in df['期号'].values:
        start_idx = df[df['期号'] == start_issue].index[0]
        if start_idx < 2:
            print(f"⚠️ 起始期 {start_issue} 过早，将从第3期（索引2）开始回测")
            start_idx = 2
        df = df.iloc[start_idx:].reset_index(drop=True)
    else:
        print(f"⚠️ 指定起始期 {start_issue} 不存在，将从数据第3期开始回测")
    
    if len(df) < 3:
        raise ValueError("❌ 起始期后数据不足3期，无法回测")
    
    # =============== 回测初始化 ===============
    results = []
    total_tested = 0
    total_wins = 0
    skipped = []
    start_time = datetime.now()  # ✅ 使用datetime.now()
    
    print("\n" + "="*80)
    print(f"🎰 排列五定位复式策略回测 | 起始期: {df['期号'].iloc[0]} | 策略规则:")
    print("   • 万位/千位 = 前两期（上上期+上期）未出现的数字")
    print("   • 百位 = 上期开奖号的十位 + 个位（去重）")
    print("   • 十位/个位 = 全包(0-9)")
    print("="*80 + "\n")
    
    # =============== 逐期回测 ===============
    for i in range(2, len(df)):
        curr = df.iloc[i]
        prev1 = df.iloc[i-1]  # 上期
        prev2 = df.iloc[i-2]  # 上上期
        
        # 1. 万/千位候选：前两期未出现的数字
        prev_digits = set(prev1['开奖号码'] + prev2['开奖号码'])
        missing = [d for d in map(str, range(10)) if d not in prev_digits]
        
        # 2. 百位候选：上期十位+个位（去重）
        last_ten = prev1['开奖号码'][3]
        last_one = prev1['开奖号码'][4]
        hundred_cands = list({last_ten, last_one})
        
        # 3. 计算注数与金额
        bets = len(missing) * len(missing) * len(hundred_cands) * 10 * 10
        cost = bets * 2
        
        # 跳过无效投注
        if bets == 0:
            skipped.append(curr['期号'])
            continue
        
        total_tested += 1
        
        # 4. 中奖判定（十/个位全包，只需验证前三位）
        num = curr['开奖号码']
        is_win = (num[0] in missing) and (num[1] in missing) and (num[2] in hundred_cands)
        if is_win:
            total_wins += 1
            win_flag = "✅【中奖】"
        else:
            win_flag = "❌ 未中奖"
        
        # 5. 记录结果
        results.append({
            '期号': curr['期号'],
            '万位候选': ','.join(missing) if missing else '无',
            '千位候选': ','.join(missing) if missing else '无',
            '百位候选': ','.join(hundred_cands),
            '十位候选': '0-9',
            '个位候选': '0-9',
            '注数': bets,
            '金额': cost,
            '开奖号码': num,
            '中奖': is_win
        })
        
        # 6. 实时输出（每100期摘要+中奖期高亮）
        if is_win or (i - 2) % 100 == 0 or i == len(df)-1:
            print(f"【{curr['期号']}】{win_flag} | 开奖: {num}")
            if is_win:
                print(f"  🎯 中奖组合匹配: 万({num[0]})∈[{','.join(missing)}], 千({num[1]})∈[{','.join(missing)}], 百({num[2]})∈[{','.join(hundred_cands)}]")
            print(f"  💰 投注: {bets:,}注 | ¥{cost:,} | 候选: 万/千=[{','.join(missing)}], 百=[{','.join(hundred_cands)}]")
            print("-" * 80)
    
    # =============== 生成统计报告 ===============
    end_time = datetime.now()  # ✅ 使用datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("📊 策略回测统计报告")
    print(f"⏱️  执行时间: {duration:.2f}秒 | 数据范围: {df['期号'].iloc[0]} → {df['期号'].iloc[-1]}")
    print(f"• 总处理期数: {len(df)-2}期（从{df['期号'].iloc[2]}开始）")
    print(f"• 有效投注期数: {total_tested}期")
    print(f"• 跳过期数: {len(skipped)}期（万/千位无候选，示例: {', '.join(skipped[:3])}{'...' if len(skipped)>3 else ''})")
    if total_tested > 0:
        win_rate = total_wins / total_tested
        theoretical = 0.00001  # 1/100000
        efficiency = win_rate / theoretical if theoretical > 0 else float('inf')
        print(f"• 中奖期数: {total_wins}期 | 实际中奖概率: {win_rate:.4%} ({total_wins}/{total_tested})")
        print(f"• 理论随机概率: {theoretical:.5%} | 策略效率: {efficiency:.1f}倍")
        # 保存详细结果到CSV
        results_df = pd.DataFrame(results)
        output_file = f"pailie5_strategy_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"• 详细结果已保存至: {output_file}")
        # 保存中奖期明细
        if total_wins > 0:
            win_df = results_df[results_df['中奖']]
            win_file = f"pailie5_wins_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            win_df.to_csv(win_file, index=False, encoding='utf-8-sig')
            print(f"• 中奖期明细已保存至: {win_file}")
    else:
        print("• 无有效投注期，无法计算中奖概率")
    print("="*80)
    
    return {
        '总处理期数': len(df)-2,
        '有效投注期数': total_tested,
        '中奖期数': total_wins,
        '中奖概率': f"{total_wins/total_tested:.4%}" if total_tested else "N/A",
        '跳过期数': len(skipped),
        '执行耗时(秒)': round(duration, 2)
    }

# ================== 执行入口 ==================
if __name__ == "__main__":
    try:
        print("🚀 启动排列五策略回测系统...")
        print("📌 要求: paiwu.csv 需包含 '期号' 和 '开奖号码' 两列（5位数字）")
        report = test_pailie5_strategy_from_csv(
            file_path='paiwu.csv',
            start_issue='25001'  # 可按需修改起始期
        )
        print("\n✅ 回测完成！报告摘要:")
        for k, v in report.items():
            print(f"  • {k}: {v}")
    except Exception as e:
        print(f"\n❌ 执行出错: {type(e).__name__}: {str(e)}")
        print("💡 建议检查:")
        print("   1. paiwu.csv 是否在当前目录")
        print("   2. CSV列名是否含'期号'/'开奖号码'（支持模糊匹配）")
        print("   3. 开奖号码是否为5位纯数字")
        print("   4. 是否安装pandas: pip install pandas")