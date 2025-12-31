import requests
import pandas as pd
import json
import akshare as ak
import streamlit as st
from datetime import date, datetime
import pandas as pd
from log import logger
import pytz
import time
import json
import re


def get_top_n_popular_stocks(n):
    """
    获取成交额前 N 的股票详细信息和统计数据。

    参数:
        n (int): 获取前 N 只股票的信息

    返回:
        df: 包含前 N 只股票的详细信息和统计数据的 DataFrame。
    """
    try:
        # 获取 A 股实时行情数据
        df = ak.stock_zh_a_spot_em()
        # 按成交额降序排序
        df_sorted = df.sort_values("成交额", ascending=False)
        # 获取前 N 只股票
        top_n_stocks = df_sorted.head(n).copy()
        # 选择需要的列并重命名
        result_df = top_n_stocks[
            ["代码", "名称", "最新价", "涨跌幅", "成交额", "总市值", "换手率"]
        ].copy()
        # 格式化数值
        result_df["涨跌幅"] = result_df["涨跌幅"].apply(lambda x: f"{x:.2f}%")
        result_df["换手率"] = result_df["换手率"].apply(lambda x: f"{x:.2f}%")
        result_df["成交额"] = (result_df["成交额"] / 1e8).apply(lambda x: f"{int(x)}亿")
        result_df["总市值"] = (result_df["总市值"] / 1e8).apply(lambda x: f"{int(x)}亿")
        result_df["最新价"] = result_df["最新价"].apply(lambda x: f"{x:.2f}")
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

def top_n_stock_avg_price_change(n):
    """
    计算前 n% 成交金额的股票的平均涨幅。

    该函数获取A股的实时交易数据，将股票按成交金额降序排序，并计算总成交金额。
    然后确定构成前 n% 成交金额的股票数量，并计算这些股票的平均涨幅。

    参数:
        n (float): 要计算的股票百分比。

    返回:
        float: 前 n% 成交金额的股票的平均涨幅。如果数据为空，则返回0。
    """
    # 获取 A 股实时行情数据
    # 序号	代码	名称	最新价	涨跌幅	涨跌额	成交量	成交额	振幅	最高	...	量比	换手率	市盈率-动态	市净率	总市值	流通市值	涨速	5分钟涨跌	60日涨跌幅	年初至今涨跌幅
    df = ak.stock_zh_a_spot_em()
    # 按成交金额降序排序
    df_sorted = df.sort_values("成交额", ascending=False)
    # 计算前 n% 的股票数量
    num_stocks = len(df)
    top_n_percent = int(num_stocks * (n / 100))
    # 计算前 n% 股票的加权平均涨幅
    top_n_weighted_avg_price_change = (
        df_sorted["涨跌幅"].head(top_n_percent)
        * df_sorted["总市值"].head(top_n_percent)
    ).sum() / df_sorted["总市值"].head(top_n_percent).sum()
    # 计算前 n% 股票的算数平均涨幅，去除涨幅超过31%的股票
    top_n_avg_price_change = (
        df_sorted[df_sorted["涨跌幅"] < 31]["涨跌幅"].head(top_n_percent).mean()
    )
    logger.info(f"前 {n}% 成交金额的股票的平均涨幅为: {top_n_avg_price_change:.2f}%")
    return top_n_weighted_avg_price_change, top_n_avg_price_change


def generate_stock_url():
    """
    生成指定股票代码的东方财富网接口URL
    :return: 拼接好市场标识的完整URL对应的DataFrame
    """
    # 1. 获取多股票代码（元组类型）
    stock_codes = get_top_n_popular_stocks(n=2)
    # 确保股票代码是可迭代对象（兼容元组/列表）
    if not isinstance(stock_codes, (list, tuple)):
        stock_codes = [stock_codes]

    # 存储最终结果的列表
    all_result_df = []

    # 2. 遍历每个股票代码，逐个处理（解决多股票代码问题）
    for stock_code in stock_codes:
        # 验证股票代码是字符串类型（避免非字符串报错）
        if not isinstance(stock_code, str):
            stock_code = str(stock_code)

        # 3. 判断股票市场类型，生成secid_value
        try:
            if stock_code.startswith(('600', '601', '603', '605', '688')):
                # 上证股票：以600/601/603/605/688开头，前面拼接1
                secid_value = f"1.{stock_code}"
            elif stock_code.startswith(('000', '001', '002', '003', '004', '300', '301', '302')):
                # 深圳股票：以000/001/002/003/004/300/301/302开头，前面拼接0
                secid_value = f"0.{stock_code}"
            else:
                raise ValueError(f"暂不支持该股票代码：{stock_code}，请确认是上证或深证股票")
        except Exception as e:
            print(f"处理股票代码 {stock_code} 时出错：{e}，跳过该股票")
            continue

        # 4. 封装请求参数
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
            "_": "1767074640946"
        }

        # 5. 发送GET请求（添加异常处理，避免请求失败导致程序中断）
        url = "https://push2.eastmoney.com/api/qt/slist/get"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            # 发送请求，设置超时时间避免无限等待
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()  # 抛出HTTP请求异常（如404/500）
            a1 = response.text
        except requests.exceptions.RequestException as e:
            print(f"请求股票 {stock_code} 对应的接口失败：{e}，跳过该股票")
            continue

        # 6. 处理JSONP格式数据（添加异常处理，避免匹配不到数据报错）
        try:
            json_match = re.search(r'\((.*)\);$', a1)
            if not json_match:
                print(f"股票 {stock_code} 未匹配到JSONP数据，跳过该股票")
                continue
            json_str = json_match.group(1)
        except Exception as e:
            print(f"解析股票 {stock_code} 的JSONP数据失败：{e}，跳过该股票")
            continue

        # 7. 解析JSON数据（添加异常处理）
        try:
            data_dict = json.loads(json_str)
            # 验证数据结构是否存在，避免键不存在报错
            if 'data' not in data_dict or 'diff' not in data_dict['data']:
                print(f"股票 {stock_code} 对应的返回数据无diff列表，跳过该股票")
                continue
            diff_list = data_dict['data']['diff']
            if not diff_list:  # 空列表直接跳过
                print(f"股票 {stock_code} 对应的diff列表为空，跳过该股票")
                continue
        except Exception as e:
            print(f"解析股票 {stock_code} 的JSON数据失败：{e}，跳过该股票")
            continue

        # 8. 构建结果并转换为DataFrame
        try:
            result_list = [{'f12': item['f12']} for item in diff_list]
            df = pd.DataFrame(result_list)
            # 可选：添加当前股票代码列，方便区分
            df['stock_code'] = stock_code
            all_result_df.append(df)
        except Exception as e:
            print(f"构建股票 {stock_code} 的DataFrame失败：{e}，跳过该股票")
            continue

    # 9. 合并所有股票的DataFrame（如果有数据）
    if all_result_df:
        final_df = pd.concat(all_result_df, ignore_index=True)
    else:
        # 无有效数据时返回空DataFrame，避免返回None报错
        final_df = pd.DataFrame(columns=['f12', 'stock_code'])

    return final_df

def a1():
    url="https://simqry2.eastmoney.com/qry_tzzh_v2?type=spo_rank_hot&plat=2&ver=web20&utToken=&ctToken=&rankType=40002&recIdx=1&recCnt=15&cb=jQuery112305533330907282918_1766982360609&_=1766982360610"
    headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    a1=requests.get(url,headers=headers).text
    #print(a1)
    json_str = a1.split('(', 1)[1].rsplit(')', 1)[0]
    # 解析为Python字典
    raw_data = json.loads(json_str)
    # 后续步骤同上（提取data + 转换DataFrame）
    target_data = raw_data["data"]
    df = pd.DataFrame(target_data)
    print(df)
    return df

def xiangt():
    f1=generate_stock_url()
    f2=a1()
    plate_code_list = f2['plateCode'].tolist()
    f12_list = f1['f12'].tolist()
    #print(plate_code_list)
    # 遍历查找相同代码
    same_codes_basic = []
    for code in plate_code_list:
        if code in f12_list:
            same_codes_basic.append(code)
    return same_codes_basic

def bankcfg():
    """
    爬取东方财富网板块数据，自动分页直到data为空

    Args:
        plate_codes: 板块代码列表，例如 ["bk0481", "bk0482"]
        pz: 每页数据条数，默认20条
    Returns:
        所有板块的所有分页数据列表
    """
    plate_codes=xiangt()
    try:
        # 基础URL（移除cb参数，避免JSONP格式，直接获取JSON）
        base_url = "https://push2.eastmoney.com/api/qt/clist/get"
        # 公共请求参数（固定不变的部分）
        common_params = {
            "np": "1",
            "fltt": "1",
            "invt": "2",
            "fs": "",  # 动态填充板块代码
            "fields": "f12,f13,f14,f1,f2,f4,f3,f152,f5,f6,f7,f15,f18,f16,f17,f10,f8,f9,f23",
            "fid": "f3",
            "pn": 1,  # 初始页码
            "pz": "50",
            "po": "1",
            "dect": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "wbp2u": "|0|0|0|web",
            "_": int(time.time() * 1000)  # 时间戳参数，防止缓存
        }
        all_data = []  # 存储所有爬取到的数据

        for plate_code in plate_codes:
            print(f"===== 开始爬取板块 {plate_code} 的数据 =====")
            page_num = 1  # 每个板块从第1页开始
            while True:
                try:
                    # 动态拼接fs参数：格式为 b:板块代码 + f:!50
                    common_params["fs"] = f"b:{plate_code}+f:!50"
                    common_params["pn"] = page_num  # 更新页码
                    common_params["_"] = int(time.time() * 1000)  # 更新时间戳
                    # 发送GET请求
                    response = requests.get(base_url, params=common_params, timeout=10)
                    response.raise_for_status()  # 抛出HTTP错误（如404、500）
                    # 解析JSON数据
                    result = response.json()
                    # 获取当前页数据列表
                    page_data = result.get("data", {}).get("diff", [])

                    if not page_data:
                        # data为空，终止当前板块的分页请求
                        print(f"板块 {plate_code} 第 {page_num} 页无数据，停止爬取该板块")
                        break
                    # 数据非空，添加到总列表
                    all_data.extend(page_data)
                    print(f"板块 {plate_code} 第 {page_num} 页爬取成功，共 {len(page_data)} 条数据")
                    # 页码自增，准备下一页请求
                    page_num += 1
                    # 加延迟，避免请求过快被封IP
                    time.sleep(0.5)
                except Exception as e:
                    print(f"爬取板块 {plate_code} 第 {page_num} 页时出错: {str(e)}")
                    break  # 出错时终止当前板块的爬取
        return all_data
    except Exception as e:
        return None

def chenfl():
    stock_data=bankcfg()
    extracted_data = []
    for item in stock_data:
        # 提取每个字典中的f12（股票代码）和f14（股票名称）
        stock_code = item['f12']
        stock_name = item['f14']
        # 将提取的键值对添加到新列表中，可自定义列名（此处用“股票代码”和“股票名称”更直观）
        extracted_data.append({'股票代码': stock_code, '股票名称': stock_name})

    # 4. 生成Pandas DataFrame
    df = pd.DataFrame(extracted_data)
    return df

if __name__ == "__main__":
    n=10
    b1=get_top_n_popular_stocks(n)
    print(b1)
    #b2=top_n_stock_avg_price_change(n)
    a3=(xiangt())
    a4=chenfl()
    print(a4)
