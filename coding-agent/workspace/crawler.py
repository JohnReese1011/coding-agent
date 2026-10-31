import requests
from bs4 import BeautifulSoup
import csv
import time
import random

# 配置参数
TARGET_URL = 'https://www.qq.com'
OUTPUT_FILE = 'output.csv'

try:
    # 发送HTTP请求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Safari/537.36'
    }
    response = requests.get(TARGET_URL, headers=headers, timeout=10)
    response.raise_for_status()

    # 解析HTML内容
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 提取目标数据（示例：提取所有段落文本）
    data = [{'text': p.get_text(strip=True)} for p in soup.find_all('p')]
    
    # 写入CSV文件
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'text'])
        writer.writeheader()
        for item in data:
            writer.writerow({'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'), 'text': item['text']})
    
    print(f'成功抓取 {len(data)} 条数据，已保存至 {OUTPUT_FILE}')

except requests.exceptions.RequestException as e:
    print(f'网络请求失败: {str(e)}')
except Exception as e:
    print(f'发生异常: {str(e)}')
