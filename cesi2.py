import requests
import time


def crawl_eastmoney_data(plate_codes, pz=20):
    """
    爬取东方财富网板块数据，自动分页直到data为空

    Args:
        plate_codes: 板块代码列表，例如 ["bk0481", "bk0482"]
        pz: 每页数据条数，默认20条
    Returns:
        所有板块的所有分页数据列表
    """
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
            "pz": pz,
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


# ==================== 主程序入口 ====================
if __name__ == "__main__":
    # 配置需要爬取的板块代码列表（可添加多个）
    target_plates = ["bk1145"]
    # 调用爬取函数
    result_data = crawl_eastmoney_data(target_plates)
    # 打印结果统计
    print(f"\n爬取完成，共获取 {len(result_data)} 条数据")
    # 打印前2条数据示例
    if result_data:
        print("前2条数据示例:")
        for i in range(min(2, len(result_data))):
            print(result_data[i])