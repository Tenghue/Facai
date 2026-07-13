from PIL import Image, ImageDraw, ImageFont
import csv

# 1. 定义模板和字体路径
TEMPLATE_PATH = "template.png"
FONT_PATH = "arial.ttf"  # 确保有支持中文的字体，如 simhei.ttf
OUTPUT_DIR = "output_images/"

def generate_images_from_csv(csv_path):
    # 2. 加载自定义字体
    font = ImageFont.truetype(FONT_PATH, size=40) 
    
    # 3. 读取CSV数据并循环生成
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # 打开模板（每次都要重新打开，避免上一次修改的残留）
            img = Image.open(TEMPLATE_PATH)
            draw = ImageDraw.Draw(img)
            
            # 4. 在指定坐标写入信息 (x, y, text, color, font)
            draw.text((100, 200), row['name'], font=font, fill="black")
            draw.text((100, 300), row['number'], font=font, fill="red")
            
            # 5. 保存生成的图片
            output_path = f"{OUTPUT_DIR}{row['name']}_card.png"
            img.save(output_path)
            print(f"成功生成: {output_path}")

# 运行生成函数
# generate_images_from_csv("data.csv")