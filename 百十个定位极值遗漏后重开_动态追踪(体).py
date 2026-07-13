#没问题，这个需求很具体。要统计“突破历史极值后，还要等多久才开”的数据，我们需要先理清逻辑：
#定义“极值”：对于每一期，我们需要知道截止到上一期为止，该位置数字的历史最大遗漏值是多少。
#捕捉“突破”：当某期开奖后，如果某个数字的当前遗漏值超过了它当时的“历史极值”，就标记为一次突破事件。
#`计算“等待期”：从突破的那一刻开始，往后数期数，直到该数字再次开出，这个间隔就是你要的“距离重开出现的遗漏值”。

import pandas as pd
import sys

def analyze_p3_breakthrough(file_path):
    try:
        # 1. 读取 CSV，自动处理编码
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='gbk')

        print(f"✅ 文件读取成功，共 {len(df)} 期数据。")
        
        # 2. 智能识别列名
        cols = list(df.columns)
        issue_col = None
        code_col = None
        
        for c in cols:
            lower_c = str(c).lower()
            if '期' in str(c) or 'issue' in lower_c:
                issue_col = c
            if '号' in str(c) or 'code' in lower_c or 'result' in lower_c:
                code_col = c
                
        if not issue_col or not code_col:
            print(f"❌ 无法识别列名。检测到的列: {cols}")
            return

        # 确保按期号排序（防止数据乱序导致统计错误）
        # 尝试将期号转为字符串进行排序，避免数字排序导致的 10 < 2 问题
        df[issue_col] = df[issue_col].astype(str)
        df = df.sort_values(by=issue_col).reset_index(drop=True)

        # 3. 数据预处理：拆分“开奖号码”为 百、十、个 位
        # 假设号码是字符串 "358" 或数字 358
        df['code_str'] = df[code_col].astype(str).str.zfill(3) # 补齐3位，防止如 "58" 被误读
        
        try:
            df['hundred'] = df['code_str'].str[0].astype(int)
            df['ten']     = df['code_str'].str[1].astype(int)
            df['unit']    = df['code_str'].str[2].astype(int)
        except Exception as e:
            print(f"❌ 号码拆分失败，请检查开奖号码列格式是否标准(如: 3,5,8 或 358)。错误: {e}")
            return

        # 4. 核心统计算法
        # 结构: stats[position][digit] = {'max_ever': 历史极值, 'current_streak': 当前连续未出期数, 'breakthrough_records': []}
        positions = {'hundred': '百位', 'ten': '十位', 'unit': '个位'}
        stats = {}
        
        for pos_key in positions:
            stats[pos_key] = {}
            for d in range(10):
                stats[pos_key][d] = {
                    'max_ever': 0,          # 截止当前的历史最大遗漏
                    'current_streak': 0,    # 当前遗漏值
                    'records': []           # 记录突破后的回补期数
                }

        # 遍历每一行数据（模拟时间轴）
        total_rows = len(df)
        for i in range(total_rows):
            row = df.iloc[i]
            
            for pos_key, pos_name in positions.items():
                current_num = row[pos_key]
                
                # 对 0-9 每个数字进行检查
                for d in range(10):
                    data = stats[pos_key][d]
                    
                    # A. 如果当前行开出了这个数字 d
                    if current_num == d:
                        # 检查在开出之前，是否处于“突破历史极值”的状态
                        # 只有当遗漏值 > 0 (说明之前没出) 且 大于之前的历史极值
                        if data['current_streak'] > data['max_ever']:
                            # 记录这次突破后的回补期数 (即当前的 streak)
                            data['records'].append(data['current_streak'])
                        
                        # 更新历史极值 (如果当前遗漏比历史极值大，更新它)
                        if data['current_streak'] > data['max_ever']:
                            data['max_ever'] = data['current_streak']
                            
                        # 重置当前遗漏为 0
                        data['current_streak'] = 0
                    
                    # B. 如果当前行没开出这个数字 d
                    else:
                        data['current_streak'] += 1

        # 5. 输出统计结果
        print("\n" + "="*60)
        print("📊 排列三【突破历史极值后】的回补期数统计")
        print("="*60)
        
        for pos_key, pos_name in positions.items():
            print(f"\n📍 【{pos_name}】分析结果:")
            print(f"{'数字':<6} | {'发生次数':<10} | {'平均回补期数':<12} | {'最大回补期数':<12} | {'具体数据(前10次)'}")
            print("-" * 90)
            
            for d in range(10):
                records = stats[pos_key][d]['records']
                count = len(records)
                
                if count > 0:
                    avg_wait = sum(records) / count
                    max_wait = max(records)
                    # 格式化显示前10次数据，太长则截断
                    sample_data = str(records[:10])
                    if len(records) > 10:
                        sample_data = sample_data[:-1] + ", ...]"
                        
                    print(f"{d:<6} | {count:<10} | {avg_wait:<12.2f} | {max_wait:<12} | {sample_data}")
                else:
                    print(f"{d:<6} | 0 (从未突破极值或未回补)")

        print("\n💡 结论解读：")
        print("如果某数字‘平均回补期数’很大，说明一旦它打破了历史最长遗漏纪录，往往还会继续冷很长一段时间（即‘破极值后更冷’）。")
        print("如果‘平均回补期数’较小（接近1），说明一旦打破纪录，很快就会回补（即‘物极必反’）。")

    except FileNotFoundError:
        print(f"❌ 找不到文件: {file_path}")
    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        import traceback
        traceback.print_exc()

# --- 主程序入口 ---
if __name__ == "__main__":
    # 这里填入你的CSV文件名，或者使用 input 输入
    file_name = "allpaisan.csv" 
    print(f"正在分析文件: {file_name} ...")
    analyze_p3_breakthrough(file_name)