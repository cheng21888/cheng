import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import json
import re
def generate_stock_url(stock_code):
    """
    生成指定股票代码的东方财富网接口URL
    :param stock_code: 股票代码（字符串类型，如"600118"、"000001"）
    :return: 拼接好市场标识的完整URL
    """
    # 判定股票市场，拼接secid对应的值
    if stock_code.startswith(('600', '601', '603', '605', '688')):
        # 上证股票：以600/601/603/605/688开头，前面拼接1
        secid_value = f"1.{stock_code}"
    elif stock_code.startswith(('000', '001', '002', '003', '004', '300', '301', '302')):
        # 深圳股票：以000/001/002/003/004/300/301/302开头，前面拼接0
        secid_value = f"0.{stock_code}"
    else:
        raise ValueError(f"暂不支持该股票代码：{stock_code}，请确认是上证或深证股票")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    # 基础URL模板（secid=后面使用占位符）
    base_url = "https://push2.eastmoney.com/api/qt/slist/get?cb=jQuery35104699993322182152_1767061331967&secid={}&pi=0&po=1&forcect=1&invt=2&spt=3&fid=f3&pz=30&fid0=f4003&fields=f1%2Cf12%2Cf152%2Cf3%2Cf14%2Cf128%2Cf136&np=1&ut=f057cbcbce2a86e2866ab8877db1d059"

    # 替换占位符，生成最终URL
    url = base_url.format(secid_value)
    a1 = requests.get(url, headers=headers).text
    #print(a1)
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

# 测试使用
if __name__ == "__main__":
    # 测试上证股票（600118）
    print(generate_stock_url("002909"))
