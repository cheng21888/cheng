import requests
import pandas as pd
import json
from datetime import datetime, timedelta
import pytz
# 设置时区
tz = pytz.timezone('Asia/Shanghai')

def get_hot_themes():
    """获取各大网站热点题材"""
    themes = []

    # 东方财富热门概念板块
    try:
        url = "http://push2.eastmoney.com/api/qt/clist/get"
        params = {
            'fid': 'f3', 'po': '1', 'pz': '20', 'pn': '1', 'np': '1',
            'fltt': '2', 'invt': '2',
            'fs': 'm:90+t:2',
            'fields': 'f12,f14,f3,f62,f136'
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        print(data)

        if data['data'] and data['data']['diff']:
            for item in data['data']['diff']:
                themes.append({
                    'source': '东方财富',
                    'theme_name': item['f14'],
                    'theme_code': item['f12'],
                    'change_pct': round(item['f3'], 2),
                    'leading_stock': item.get('f136', ''),
                    'type': '概念板块',
                    'timestamp': datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                })
    except Exception as e:
        print(f"获取东方财富热点题材失败: {str(e)}")

print(get_hot_themes())
hot_themes = get_hot_themes()
print(f"获取到 {len(hot_themes)} 个热点题材")