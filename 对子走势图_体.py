import pandas as pd
import numpy as np
from collections import Counter
import json
import os

def load_3d_data(csv_path: str):
    """加载并清洗all3D.csv数据"""
    try:
        df = pd.read_csv(csv_path, encoding='utf-8', dtype=str)
    except UnicodeDecodeError:
        df = pd.read_csv(csv_path, encoding='gbk', dtype=str)
        
    if not {'期号', '开奖号码'}.issubset(df.columns):
        raise ValueError(f"CSV必须包含'期号'和'开奖号码'列，当前列: {list(df.columns)}")
        
    df = df.dropna(subset=['期号', '开奖号码']).copy()
    df['期号'] = df['期号'].astype(str).str.strip()
    df['开奖号码'] = df['开奖号码'].astype(str).str.strip().str.zfill(3)
    
    valid_mask = df['开奖号码'].str.match(r'^\d{3}$')
    invalid_count = (~valid_mask).sum()
    if invalid_count > 0:
        print(f"⚠️ 跳过 {invalid_count} 行非3位数字的异常数据")
    df = df[valid_mask].reset_index(drop=True)
    return df

def get_pair_trajectory(df: pd.DataFrame, digit: str):
    """计算指定数字的对子轨迹 (aab/baa/aba)"""
    is_pair = []
    hit_issues = []
    hit_nums = []
    
    for _, row in df.iterrows():
        num_str = row['开奖号码']
        cnt = Counter(num_str)
        # 严格判定：该数字恰好出现2次（排除豹子）
        if cnt.get(digit, 0) == 2:
            is_pair.append(True)
            hit_issues.append(row['期号'])
            hit_nums.append(num_str)
        else:
            is_pair.append(False)
            
    return np.array(is_pair), hit_issues, hit_nums

def print_terminal_chart(is_pair: np.ndarray, digit: str, width: int = 80):
    """终端ASCII轨迹图预览"""
    total = len(is_pair)
    hits = int(is_pair.sum())
    print(f"\n📊 数字 [{digit}] 对子轨迹概览 (共{total}期, 命中{hits}次)")
    print("-" * width)
    
    chunk_size = max(1, total // width)
    chart_line = ""
    for i in range(0, total, chunk_size):
        chunk = is_pair[i:i+chunk_size]
        chart_line += "★" if chunk.any() else "─"
        
    for i in range(0, len(chart_line), width):
        print(chart_line[i:i+width])
    print("-" * width)
    print("★ = 对子命中   ─ = 未命中\n")

def generate_html_chart(df: pd.DataFrame, is_pair: np.ndarray, digit: str):
    """生成修复版交互式HTML轨迹图"""
    issues = df['期号'].tolist()
    nums = df['开奖号码'].tolist()
    pair_list = is_pair.tolist()
    
    # 安全序列化数据，避免JS语法错误
    data_json = json.dumps({
        "issues": issues,
        "nums": nums,
        "isPair": pair_list,
        "digit": digit
    }, ensure_ascii=False)
    
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>福彩3D [{digit}对子] 出现轨迹图</title>
<style>
  body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f7fa; color: #333; }}
  h2 {{ margin-bottom: 10px; }}
  .stats {{ padding: 12px 16px; background: #e3f2fd; border-radius: 8px; margin-bottom: 15px; font-size: 14px; line-height: 1.8; }}
  .chart-wrapper {{ 
    width: 100%; height: 320px; overflow-x: auto; overflow-y: hidden;
    border: 1px solid #dce1e8; border-radius: 8px; background: #fff; position: relative;
  }}
  canvas {{ display: block; cursor: crosshair; }}
  .tooltip {{ 
    position: fixed; background: rgba(30,30,30,0.9); color: #fff; 
    padding: 8px 12px; border-radius: 6px; font-size: 12px; pointer-events: none; 
    display: none; z-index: 999; white-space: nowrap; line-height: 1.6;
  }}
  .error-msg {{ color: #d32f2f; padding: 40px; text-align: center; font-size: 16px; }}
</style>
</head>
<body>
<h2>🎯 福彩3D 数字 [{digit}] 对子(aab/baa/aba) 出现轨迹图</h2>
<div class="stats" id="stats"></div>
<div class="chart-wrapper" id="chartWrapper">
  <canvas id="chart"></canvas>
</div>
<div class="tooltip" id="tooltip"></div>

<script>
try {{
  const DATA = {data_json};
  const {{ issues, nums, isPair, digit }} = DATA;
  
  if (!issues || issues.length === 0) {{
    document.getElementById('chartWrapper').innerHTML = '<div class="error-msg">❌ 无有效数据，请检查CSV文件</div>';
    throw new Error('Empty data');
  }}

  // 统计信息
  const totalHits = isPair.filter(Boolean).length;
  const totalPeriods = isPair.length;
  document.getElementById('stats').innerHTML = 
    `📈 总期数: <b>${{totalPeriods}}</b> &nbsp;|&nbsp; 🎯 命中次数: <b>${{totalHits}}</b> &nbsp;|&nbsp; 📊 出现概率: <b>${{(totalHits/totalPeriods*100).toFixed(2)}}%</b>`;

  // Canvas 初始化 —— 关键修复：动态计算真实宽度
  const canvas = document.getElementById('chart');
  const wrapper = document.getElementById('chartWrapper');
  const ctx = canvas.getContext('2d');
  const tooltip = document.getElementById('tooltip');

  const POINT_GAP = 6;       // 每个数据点占用的像素宽度
  const PADDING = {{ top: 30, bottom: 50, left: 20, right: 20 }};
  const CHART_H = 300;
  
  // 强制画布宽度 = 数据量 × 间距，最小为容器宽度
  const realWidth = Math.max(wrapper.clientWidth, totalPeriods * POINT_GAP + PADDING.left + PADDING.right);
  canvas.width = realWidth;
  canvas.height = CHART_H;

  const drawAreaH = CHART_H - PADDING.top - PADDING.bottom;
  const hitY = PADDING.top + 15;          // 命中点的Y坐标
  const missY = CHART_H - PADDING.bottom - 15; // 未命中点的Y坐标

  // 预计算所有点位坐标
  const points = [];
  for (let i = 0; i < totalPeriods; i++) {{
    points.push({{
      x: PADDING.left + i * POINT_GAP + POINT_GAP / 2,
      y: isPair[i] ? hitY : missY,
      issue: issues[i],
      num: nums[i],
      hit: isPair[i]
    }});
  }}

  // 绘制背景网格线
  ctx.strokeStyle = '#f0f0f0';
  ctx.lineWidth = 1;
  const labelStep = Math.max(1, Math.floor(totalPeriods / 30));
  ctx.font = '10px Arial';
  ctx.fillStyle = '#aaa';
  for (let i = 0; i < totalPeriods; i += labelStep) {{
    const x = points[i].x;
    ctx.beginPath(); ctx.moveTo(x, PADDING.top); ctx.lineTo(x, CHART_H - PADDING.bottom); ctx.stroke();
    ctx.save();
    ctx.translate(x, CHART_H - 8);
    ctx.rotate(-Math.PI / 4);
    ctx.textAlign = 'right';
    ctx.fillText(issues[i], 0, 0);
    ctx.restore();
  }}

  // 绘制轨迹连线（使用Path2D提升大数据渲染性能）
  const path = new Path2D();
  points.forEach((p, i) => {{
    if (i === 0) path.moveTo(p.x, p.y);
    else path.lineTo(p.x, p.y);
  }});
  ctx.strokeStyle = '#90caf9';
  ctx.lineWidth = 1;
  ctx.stroke(path);

  // 绘制数据点
  points.forEach(p => {{
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.hit ? 4 : 1.5, 0, Math.PI * 2);
    ctx.fillStyle = p.hit ? '#e53935' : '#ddd';
    ctx.fill();
  }});

  // 鼠标悬停交互
  canvas.addEventListener('mousemove', e => {{
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const mx = (e.clientX - rect.left) * scaleX;
    
    // 二分查找最近的点（O(logN)替代O(N)遍历）
    let lo = 0, hi = points.length - 1, best = -1;
    while (lo <= hi) {{
      const mid = (lo + hi) >> 1;
      if (points[mid].x <= mx) {{ best = mid; lo = mid + 1; }}
      else hi = mid - 1;
    }}
    // 检查相邻点取最近
    if (best >= 0 && best < points.length - 1) {{
      if (Math.abs(points[best+1].x - mx) < Math.abs(points[best].x - mx)) best++;
    }}
    
    const p = points[best];
    if (p && Math.abs(mx - p.x) < POINT_GAP) {{
      tooltip.style.display = 'block';
      tooltip.style.left = (e.clientX + 15) + 'px';
      tooltip.style.top = (e.clientY - 40) + 'px';
      tooltip.innerHTML = `<b>期号:</b> ${{p.issue}}<br><b>开奖:</b> ${{p.num}}<br>${{p.hit ? '✅ ' + digit + '对子命中' : '❌ 未命中'}}`;
    }} else {{
      tooltip.style.display = 'none';
    }}
  }});
  
  canvas.addEventListener('mouseleave', () => tooltip.style.display = 'none');
  
  console.log(`✅ 图表渲染成功: ${{totalPeriods}}期, 画布宽度${{realWidth}}px`);
}} catch(err) {{
  console.error('图表渲染失败:', err);
  document.getElementById('chartWrapper').innerHTML = 
    '<div class="error-msg">❌ 图表渲染失败: ' + err.message + '<br>请检查浏览器控制台(F12)</div>';
}}
</script>
</body>
</html>"""
    
    out_path = f"3D_pair_trajectory_{digit}.html"
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    return out_path


def main():
    csv_path = 'allpaisan.csv'
    if not os.path.exists(csv_path):
        print(f"❌ 未找到 {csv_path}，请确保文件在当前目录下")
        return
        
    print("⏳ 正在加载数据...")
    df = load_3d_data(csv_path)
    print(f"✅ 加载完成: {len(df)} 期 ({df['期号'].iloc[0]} ~ {df['期号'].iloc[-1]})")
    
    while True:
        digit = input("\n请输入要查询的数字(0-9)，输入q退出: ").strip()
        if digit.lower() == 'q':
            print("👋 已退出")
            break
        if digit not in [str(i) for i in range(10)]:
            print("⚠️ 请输入0-9之间的单个数字")
            continue
            
        is_pair, hit_issues, hit_nums = get_pair_trajectory(df, digit)
        print_terminal_chart(is_pair, digit)
        
        if hit_issues:
            print(f"📋 最近10次 [{digit}对子] 命中明细:")
            for iss, num in zip(hit_issues[-10:], hit_nums[-10:]):
                print(f"   期号: {iss}  开奖: {num}")
        else:
            print(f"⚠️ 历史数据中未找到 [{digit}对子]")
            
        html_path = generate_html_chart(df, is_pair, digit)
        print(f"🌐 交互式轨迹图已生成: {html_path}")
        print(f"   👉 请用浏览器打开该文件查看（双击即可）")


if __name__ == '__main__':
    main()