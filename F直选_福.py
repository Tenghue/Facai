import csv
import os
import pandas as pd
from collections import Counter

def load_data(filename='all3D.csv'):
    """加载并清洗数据，严格按期号升序（时间顺序）"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"❌ 数据文件 '{filename}' 不存在！请确认文件在当前目录")
    
    records = []
    with open(filename, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if '期号' not in reader.fieldnames or '开奖号码' not in reader.fieldnames:
            raise ValueError(f"⚠️ 表头错误！需含'期号','开奖号码'，当前: {reader.fieldnames}")
        
        for row in reader:
            period = row['期号'].strip()
            raw = row['开奖号码'].strip()
            if period and raw:
                clean = ''.join(filter(str.isdigit, raw))
                if len(clean) == 3:
                    # 提取期号数字用于排序
                    pid = ''.join(filter(str.isdigit, period))
                    records.append((period, clean, int(pid) if pid else 0))
    
    # 按期号整数升序排序（确保时间顺序：最早→最新）
    records.sort(key=lambda x: x[2])
    periods = [r[0] for r in records]
    codes = [r[1] for r in records]
    
    print(f"✅ 已加载 {len(records)} 期数据 | 期号范围: {periods[0]} → {periods[-1]}")
    print(f"   🔢 和值范围验证: {min(sum(int(d) for d in c) for c in codes)}~{max(sum(int(d) for d in c) for c in codes)} (理论0~27)")
    return periods, codes

def clean_user_input(user_str):
    """清洗用户输入为标准三位数字字符串"""
    clean = ''.join(filter(str.isdigit, user_str.strip()))
    if len(clean) != 3:
        return None
    return clean.zfill(3)  # 确保三位（如输入"1"→"001"）

def main():
    print("="*70)
    print("🔍 排列三号码轨迹追踪系统 | 输入号码查历史 + 下期数字热力分析")
    print("📌 功能:")
    print("   • 检索指定号码所有历史出现记录")
    print("   • 展示每期：上期 + 本期 + 下两期完整轨迹")
    print("   • 统计「所有下期号码」中0-9数字高频分布（核心！）")
    print("="*70)
    
    try:
        # =============== 1. 加载数据 ===============
        periods, codes = load_data('all3D.csv')
        if not periods:
            print("❌ 无有效开奖数据")
            return
        
        # =============== 2. 用户输入 ===============
        while True:
            user_input = input("\n🔢 请输入要检索的三位数号码（支持 123 / 001 / 1,2,3 格式）: ").strip()
            target = clean_user_input(user_input)
            if target and len(target) == 3:
                break
            print("❌ 输入无效！请确保输入三位数字（如：001, 123, 9,9,9）")
        
        print(f"\n⏳ 正在检索号码 [{target}] 的历史轨迹...")
        
        # =============== 3. 检索匹配记录 ===============
        matches = []
        next_codes_for_stats = []  # 仅收集存在的"下期号码"用于统计
        
        for i in range(len(codes)):
            if codes[i] == target:
                # 上期
                prev_info = {
                    '期号': periods[i-1] if i > 0 else "无",
                    '号码': codes[i-1] if i > 0 else "—"
                }
                # 下期（核心：用于统计）
                if i < len(codes) - 1:
                    next_code = codes[i+1]
                    next_info = {
                        '期号': periods[i+1],
                        '号码': next_code
                    }
                    next_codes_for_stats.append(next_code)  # 收集用于统计
                else:
                    next_info = {'期号': "无（最后一期）", '号码': "—"}
                # 下两期
                if i < len(codes) - 2:
                    next2_info = {'期号': periods[i+2], '号码': codes[i+2]}
                else:
                    next2_info = {'期号': "无", '号码': "—"}
                
                matches.append({
                    '期号': periods[i],
                    '上期': prev_info,
                    '本期': {'期号': periods[i], '号码': target},
                    '下期': next_info,
                    '下两期': next2_info
                })
        
        # =============== 4. 无匹配处理 ===============
        if not matches:
            print(f"\n❌ 未找到号码 [{target}] 的任何历史记录！")
            print("💡 提示: 检查输入格式（如'001'而非'1'），或确认该号码是否在数据范围内")
            return
        
        # =============== 5. 输出匹配详情 ===============
        print(f"\n✅ 共找到 {len(matches)} 次历史记录（号码: {target}）")
        print("="*70)
        for idx, m in enumerate(matches, 1):
            print(f"\n【记录 {idx}/{len(matches)}】")
            print(f"  📍 本期期号: {m['本期']['期号']} | 号码: {m['本期']['号码']}")
            print(f"  ⬅️  上期: {m['上期']['期号']} | 号码: {m['上期']['号码']}")
            print(f"  ➡️  下期: {m['下期']['期号']} | 号码: {m['下期']['号码']}")
            print(f"  ➡️➡️ 下两期: {m['下两期']['期号']} | 号码: {m['下两期']['号码']}")
            print("-"*70)
        
        # =============== 6. 下期数字高频统计（核心功能）===============
        print("\n" + "="*70)
        print(f"📊 「下期号码」数字热力分析（基于 {len(next_codes_for_stats)} 次有效下期记录）")
        print("💡 说明: 统计所有匹配记录的「紧接着下一期」开奖号码中，0-9每位数字出现频率")
        print("="*70)
        
        if next_codes_for_stats:
            # 拆解所有下期号码的每位数字
            all_digits = [d for code in next_codes_for_stats for d in code]
            digit_counter = Counter(all_digits)
            total_digits = len(all_digits)
            
            # 按次数降序，次数相同按数字升序
            sorted_digits = sorted(digit_counter.items(), key=lambda x: (-x[1], x[0]))
            
            # 输出表格
            print(f"\n{'数字':<8}{'出现次数':<12}{'占比':<12}{'热力图'}")
            print("-"*70)
            for digit, count in sorted_digits:
                pct = count / total_digits * 100
                # 动态条形图（按比例）
                bar_len = int(count * 30 / max(digit_counter.values()))
                bar = '█' * bar_len + '░' * (30 - bar_len)
                print(f"{digit:<8}{count:<12}{pct:>6.1f}%     {bar}")
            
            # 高频数字（前3）
            top3 = sorted_digits[:3]
            print("\n🔥 高频数字（下期最常出现）:")
            for i, (digit, count) in enumerate(top3, 1):
                pct = count / total_digits * 100
                print(f"  {i}. 数字 {digit} → {count} 次 ({pct:.1f}%)")
            
            # 附加洞察
            print("\n💡 深度洞察:")
            # 冷数字（出现≤1次）
            cold_digits = [d for d, c in digit_counter.items() if c <= 1]
            if cold_digits:
                print(f"   • 下期冷数字（出现≤1次）: {', '.join(cold_digits)}")
            # 与理论频率对比
            expected = total_digits / 10
            hot_dev = [(d, c, (c-expected)/expected*100) for d, c in sorted_digits if c > expected*1.2]
            if hot_dev:
                print(f"   • 显著偏热（>理论值20%）: " + ", ".join([f"{d}({delta:+.0f}%)" for d, c, delta in hot_dev[:3]]))
            # 最近一次下期号码分析
            if matches and matches[-1]['下期']['号码'] != "—":
                last_next = matches[-1]['下期']['号码']
                last_digits = list(last_next)
                print(f"   • 最近一次下期号码 ({matches[-1]['下期']['期号']}): {last_next} → 含高频数字: {', '.join([d for d in last_digits if int(digit_counter.get(d,0)) >= sorted_digits[2][1]])}")
        else:
            print("⚠️  所有匹配记录均为历史最后一期，无「下期」数据可供统计")
        
        # =============== 7. 导出选项 ===============
        print("\n" + "="*70)
        export = input("💾 导出匹配详情到CSV? (y/n): ").strip().lower()
        if export == 'y':
            export_data = []
            for m in matches:
                export_data.append({
                    '匹配期号': m['本期']['期号'],
                    '上期期号': m['上期']['期号'],
                    '上期号码': m['上期']['号码'],
                    '本期号码': m['本期']['号码'],
                    '下期期号': m['下期']['期号'],
                    '下期号码': m['下期']['号码'],
                    '下两期期号': m['下两期']['期号'],
                    '下两期号码': m['下两期']['号码']
                })
            
            # 添加统计摘要行
            if next_codes_for_stats:
                summary = {
                    '匹配期号': '【统计摘要】',
                    '上期期号': f'共 {len(next_codes_for_stats)} 次有效下期',
                    '上期号码': '',
                    '本期号码': '',
                    '下期期号': '高频数字(前3)',
                    '下期号码': ' | '.join([f"{d}({c}次)" for d, c in sorted_digits[:3]]),
                    '下两期期号': '冷数字(≤1次)',
                    '下两期号码': ', '.join(cold_digits) if cold_digits else '无'
                }
                export_data.append(summary)
            
            df = pd.DataFrame(export_data)
            filename = f"号码_{target}_轨迹分析_{len(matches)}次.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✅ 已导出: {filename}（含轨迹详情+统计摘要）")
        
        print("\n✅ 分析完成！")
        print("💡 使用建议:")
        print("   • 高频数字可作为下期选号参考（但需结合其他指标）")
        print("   • 冷数字若长期未出，可关注回补机会")
        print("   • 轨迹中'上期→本期→下期'模式可辅助形态分析")
        print("="*70)
    
    except Exception as e:
        print(f"\n❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()