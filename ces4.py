import requests


def get_eastmoney_data(stock_code: str, market: str) -> dict:
    """
    从东方财富获取个股数据，自动拼接secid
    :param stock_code: 股票代码（如 600000 / 000001）
    :param market: 市场类型（sh=上证, sz=深证）
    :return: 接口返回的JSON数据
    """
    # 1. 拼接secid：上证=1.代码，深证=0.代码
    secid_prefix = "1." if market == "sh" else "0."
    secid = secid_prefix + stock_code

    # 2. 封装所有请求参数到params字典（对应URL中的参数）
    params = {
        "cb": "jQuery35105592216436984774_1767074640945",  # 回调函数名（可固定或动态生成）
        "secid": secid,  # 核心参数：市场+代码
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

    try:
        response = requests.get(url, params=params, headers=headers)
        # 处理JSONP格式数据：去掉回调函数包裹，提取JSON内容
        json_str = response.text.split("(", 1)[1].rsplit(")", 1)[0]
        return eval(json_str)  # 转换为字典（或用json.loads，需确保字符串合法）
    except Exception as e:
        print(f"请求失败：{e}")
        return {}


# ------------------- 调用示例 -------------------
# 示例1：上证股票 600000（浦发银行）
sh_data = get_eastmoney_data(stock_code="600000", market="sh")
print("上证600000数据：", sh_data)

# 示例2：深证股票 000001（平安银行）
sz_data = get_eastmoney_data(stock_code="000001", market="sz")
print("深证000001数据：", sz_data)