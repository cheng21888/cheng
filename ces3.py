import requests
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import json
import re

def get_eastmoney_data(stock_code):
    """
    从东方财富获取个股数据，自动拼接secid
    :param stock_code: 股票代码（如 600000 / 000001）
    :param market: 市场类型（sh=上证, sz=深证）
    :return: 接口返回的JSON数据
    """
    if stock_code.startswith(('600', '601', '603', '605', '688')):
        # 上证股票：以600/601/603/605/688开头，前面拼接1
        secid_value = f"1.{stock_code}"
    elif stock_code.startswith(('000', '001', '002', '003', '004', '300', '301', '302')):
        # 深圳股票：以000/001/002/003/004/300/301/302开头，前面拼接0
        secid_value = f"0.{stock_code}"
    else:
        raise ValueError(f"暂不支持该股票代码：{stock_code}，请确认是上证或深证股票")
    # 1. 拼接secid：上证=1.代码，深证=0.代码
    # 2. 封装所有请求参数到params字典（对应URL中的参数）
    params = {
        "cb": "jQuery35105592216436984774_1767074640945",  # 回调函数名（可固定或动态生成）
        "secid": secid_value,  # 核心参数：市场+代码
        "pi": "0",  # 页码
        "po": "1",  # 每页条数
        "forcect": "1",  # 强制格式
        "invt": "2",  # 反转参数
        "spt": "3",  # 排序类型
        "fid": "f3",  # 排序字段
        "pz": "30",  # 分页大小
        "fid0": "f4003",  # 辅助排序字段
        "fields": "f1,f12,f152,f3,f14,f128,f136",  # 返回字段
        "np": "1",  # 是否非分页
        "ut": "f057cbcbce2a86e2866ab8877db1d059",  # 加密参数
        "_": "1767074640946"  # 时间戳（可替换为当前时间戳）
    }

    # 3. 发送GET请求（注意：东方财富部分接口需要headers模拟浏览器）
    url = "https://push2.eastmoney.com/api/qt/slist/get"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    a1 = requests.get(url, params=params, headers=headers).text
    # 处理JSONP格式数据：去掉回调函数包裹，提取JSON内容
    # print(a1)
    json_str = re.search(r'\((.*)\);$', a1).group(1)

    # 步骤2：解析JSON为Python字典
    data_dict = json.loads(json_str)

    # 步骤3：获取diff核心列表
    diff_list = data_dict['data']['diff']

    # 步骤4：直接遍历diff列表，提取f12和f14（无if/else判断）
    # 方式1：列表推导式直接构建结果（简洁高效，无if/else）
    result_list = [{'f12': item['f12']} for item in diff_list]
    df = pd.DataFrame(result_list)

    # 4. 可选：打印查看转换后的DataFrame
    return df


if __name__ == "__main__":
    # 测试上证股票（600118）
    print(get_eastmoney_data("002909"))
