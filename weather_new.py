"""
key:04c40f323b556a631ae8a877aea9241e

"""
import requests
import json


def weather(city):
    """
    :param city: 用户输入的城市
    :return: 返回实时天气数据/近7天的天气数据
    """

    # 天气预报数据请求地址
    url = "http://apis.juhe.cn/simpleWeather/query"

    # 这次的请求接口是POST请求，需要传参数；参数如下
    params_dict = {
        "city": city,
        "key": "04c40f323b556a631ae8a877aea9241e"
    }

    # 请求接口 获取数据
    result = requests.post(url, params_dict).text

    # 得到的数据是字符串（str）类型,不容易提取数据。将字符串类型转换为json类型，使用 json.loads()
    print("获取到的数据是什么数据类型？：", type(result))
    jsonRes = json.loads(result)
    print("转换后之后的数据类型：", type(jsonRes))

    print("数据：", jsonRes)

    # 如果请求成功 在数据末有判断数据是否请求成果的字段 error_code ， 如果 error_code 的值为 0 那么代表数据获取成功。仅此接口是通过error_code来判断的。
    """
        dict的获取方法
        例如：
            dict = {
                "key" : "value"            
            }

        value = dict["key"]

        因为该数据是嵌套dict，所以要一层一层的获取，如下：

    """
    if jsonRes["error_code"] == 0:
        # 温度
        temperature = jsonRes['result']['realtime']['temperature']
        # 湿度
        humidity = jsonRes['result']['realtime']['humidity']
        # 天气
        info = jsonRes['result']['realtime']['info']
        # 天气标识
        wid = jsonRes['result']['realtime']['wid']
        # 风向
        direct = jsonRes['result']['realtime']['direct']
        # 风力
        power = jsonRes['result']['realtime']['power']
        # 空气
        aqi = jsonRes['result']['realtime']['aqi']

        # 字符串拼接输出
        print(
            "实时数据如下：\n 温度：" + temperature + "℃\n 湿度：" + humidity + "\n 天气：" + info + "\n 天气标识：" + wid + "\n 风向：" + direct + "\n 风力：" + power + "\n 空气：" + aqi)

        # 格式化输出
        # print("温度：%s\n湿度：%s\n天气：%s\n天气标识：%s\n风向：%s\n风力：%s\n空气质量：%s" % (temperature, humidity, info, wid, direct, power, aqi))


if __name__ == '__main__':
    try:
        city = input("请输入要查询的城市名称（中文）：")
        weather(city)
    except Exception as e:
        print(e)
