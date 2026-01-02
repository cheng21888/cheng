import requests
import akshare as ak
import pandas as pd
import time
import json
import re


headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def qianshi():
    url = "https://push2.eastmoney.com/api/qt/clist/get"

    # 查询参数字典
    params = {
        "np": "1",
        "fltt": "1",
        "invt": "2",
        "cb": "jQuery37106245601911544734_1767072109848",
        "fs": "m:0+t:6+f:!2,m:0+t:80+f:!2,m:1+t:2+f:!2,m:1+t:23+f:!2,m:0+t:81+s:262144+f:!2",
        "fields": "f12,f13,f14,f1,f2,f4,f3,f152,f5,f6,f7,f15,f18,f16,f17,f10,f8,f9,f23",
        "fid": "f6",
        "pn": "1",
        "pz": "20",
        "po": "1",
        "dect": "1",
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "wbp2u": "|0|0|0|web",
        "_": int(time.time() * 1000)  # 时间戳参数，防止缓存
    }
    # 发送请求（GET 方法）
    response = requests.get(url, params=params,headers=headers)
    # 查看拼接后的完整 URL（验证用）
    # print(response.url)
    # 查看响应内容
    raw_data = response.text
    # 方法1：正则表达式匹配（更稳健，适配任意jQuery回调函数名）
    json_pattern = re.compile(r'jQuery\d+_\d+\((.*)\);')
    match_result = json_pattern.search(raw_data)
    json_str = match_result.group(1)  # 步骤2：解析JSON字符串为Python字典
    data_dict = json.loads(json_str)

    # 步骤3：提取diff数组（股票数据列表）
    stock_list = data_dict['data']['diff']

    # 步骤4：构造新的数据集，映射字段名
    processed_data = []
    for stock in stock_list:
        # 提取f12、f3、f6并映射为指定字段名
        stock_info = {
            '代码': stock['f12'],
            '名称': stock['f14'],  # f12 -> code（股票代码）
            '涨跌幅': stock['f3'] / 100,  # f3 -> 涨幅
            '成交额': stock['f6'] / 100000000  # f6 -> 成交额
        }
        processed_data.append(stock_info)
    # 步骤5：转换为DataFrame，并取前十行
    df = pd.DataFrame(processed_data)
    stock_df = df.head(11)  # 取前十行股票数据
    return stock_df

def get_top_n_popular_stocks():
    """
    获取成交额前 N 的股票详细信息和统计数据。

    参数:
        n (int): 获取前 N 只股票的信息

    返回:
        df: 包含前 N 只股票的详细信息和统计数据的 DataFrame。
    """
    try:
        # 获取 A 股实时行情数据
        df = qianshi()
        # 按成交额降序排序
        df_sorted = df.sort_values("成交额", ascending=False)
        # 获取前 N 只股票
        top_n_stocks = df_sorted.head(10).copy()
        # 选择需要的列并重命名
        result_df = top_n_stocks[
            ["代码", "名称","涨跌幅", "成交额"]
        ].copy()
        # 格式化数值
        result_df["涨跌幅"] = result_df["涨跌幅"].apply(lambda x: f"{x:.2f}%")
        result_df["成交额"] = (result_df["成交额"] / 1e8).apply(lambda x: f"{int(x)}亿")
        # 设置索引为名称，但不显示索引名
        result_df.set_index("名称", inplace=True)
        df = pd.DataFrame(result_df)
        df['涨跌幅数值'] = df['涨跌幅'].str.replace('%', '').astype(float)
        top2_gain_idx = df['涨跌幅数值'].nlargest(2).index
        # 2. 通过索引分别获取前两名的股票代码
        max1_code = df.loc[top2_gain_idx[0], '代码']  # 涨跌幅第1名代码
        max2_code = df.loc[top2_gain_idx[1], '代码']  # 涨跌幅第2名代码
        # =================================

        print(f"涨跌幅第1名的股票代码是：{max1_code}")
        print(f"涨跌幅第2名的股票代码是：{max2_code}")
        return (max1_code, max2_code)  # 返回元组包含前两名代码
    except Exception as e:
        print(f"异常信息：{e}")
        return (None, None)


def generate_stock_url(stock_code):
    """
    生成指定股票代码的东方财富网接口URL
    :return: 拼接好市场标识的完整URL对应的DataFrame
    """
        # 判断股票市场类型，拼接secid
    if stock_code.startswith(('600', '601', '603', '605', '688')):
            # 上证股票：以600/601/603/605/688开头，前面拼接1
        secid_value = f"1.{stock_code}"
    elif stock_code.startswith(('000', '001', '002', '003', '004', '300', '301', '302')):
            # 深圳股票：以000/001/002/003/004/300/301/302开头，前面拼接0
        secid_value = f"0.{stock_code}"
        params = {
            "cb": "jQuery35105592216436984774_1767074640945",
            "secid": secid_value,
            "pi": "0",
            "po": "1",
            "forcect": "1",
            "invt": "2",
            "spt": "3",
            "fid": "f3",
            "pz": "30",
            "fid0": "f4003",
            "fields": "f1,f12,f152,f3,f14,f128,f136",
            "np": "1",
            "ut": "f057cbcbce2a86e2866ab8877db1d059",
            "_": int(time.time() * 1000)  # 时间戳参数，防止缓存
        }

        # 5. 发送GET请求（添加异常处理，避免请求失败导致程序中断）
        url = "https://push2.eastmoney.com/api/qt/slist/get"
        # 发送请求，设置超时时间避免无限等待
        response = requests.get(url, params=params, headers=headers, timeout=20)
        response.raise_for_status()  # 抛出HTTP请求异常（如404/500）
        a1 = response.text
        # 6. 处理JSONP格式数据（添加异常处理，避免匹配不到数据报错）
        # 正则说明：匹配 "f12":"任意字符(非双引号)" 并捕获内容，同时匹配对应的 "f14":"任意字符(非双引号)" 并捕获内容
        pattern = r'"f12":"([^"]+)"[^}]*"f14":"([^"]+)"'
        # 查找所有匹配的结果，返回列表，每个元素是(f12值, f14值)的元组
        matches = re.findall(pattern, a1)

        # 2. 将匹配结果转换为DataFrame，并命名列名为“代码”和“板块名称”
        # 先将元组列表转换为字典列表（更直观），也可直接传入DataFrame
        data_list = [{"代码": f12_val, "板块名称": f14_val} for f12_val, f14_val in matches]
        df = pd.DataFrame(data_list)
        return df
def dairu():
    # 1. 获取股票代码元组
    stock_codes = get_top_n_popular_stocks()
    #print(stock_codes)
    # 2. 初始化一个空列表，用于存储每个股票对应的DataFrame
    df_list = []

    # 3. 遍历股票代码元组，逐个生成DataFrame并添加到列表
    for code in stock_codes:
        single_stock_df = generate_stock_url(code)  # 对单个股票代码生成DataFrame
        df_list.append(single_stock_df)  # 将单个DataFrame存入列表

    # 4. 合并列表中所有DataFrame（垂直拼接，忽略原有索引）
    merged_df = pd.concat(df_list, ignore_index=True)

    # 5. 返回合并后的最终DataFrame
    return merged_df
def a1():
    url="https://simqry2.eastmoney.com/qry_tzzh_v2?type=spo_rank_hot&plat=2&ver=web20&utToken=&ctToken=&rankType=40002&recIdx=1&recCnt=15&cb=jQuery112305533330907282918_1766982360609&_=1766982360610"
    a1=requests.get(url,headers=headers).text
    #print(a1)
    pattern = r'"plateCode":"([^"]+)"[^}]*"plateName":"([^"]+)"'
    # 查找所有匹配的结果，返回列表，每个元素是(f12值, f14值)的元组
    matches = re.findall(pattern, a1)

    # 2. 将匹配结果转换为DataFrame，并命名列名为“代码”和“板块名称”
    # 先将元组列表转换为字典列表（更直观），也可直接传入DataFrame
    data_list = [{"代码": plateCode, "板块名称": plateName} for plateCode, plateName in matches]
    df = pd.DataFrame(data_list)
    #print(df)
    return df

def xiangt():
    f1=dairu()
    f2=a1()
    common_df = pd.merge(
        left=f1,
        right=f2,
        on=['代码', '板块名称'],  # 核心：按两列同时匹配
        how='inner'  # 内连接，筛选共同记录（可省略，默认inner）
    )
    return common_df


if __name__ == "__main__":
    # print(qianshi())
    b1=get_top_n_popular_stocks()
    #print(b1)
    b3 = dairu()
    print(b3)
    print(a1())

    a3=print(xiangt())

