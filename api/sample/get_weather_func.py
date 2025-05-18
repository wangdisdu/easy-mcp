def get_weather_func(city, apiKey):
    """
    通过高德开发天气api获取天气

    city: 查询城市
    """
    import httpx

    try:
        # 验证参数
        if not city:
            return "缺少必要参数: city"

        if not apiKey:
            return "缺少API密钥,请在配置中设置apiKey"

        # 构建API URL
        url = f"https://restapi.amap.com/v3/weather/weatherInfo"
        params = {
            "city": city,
            "key": apiKey,
            "extensions": "base",  # 获取实时天气
        }

        # 发送请求
        print(f"正在获取城市 {city} 的天气信息")
        response = httpx.get(url, params=params)

        # 检查响应状态
        response.raise_for_status()

        # 解析响应数据
        data = response.json()

        # 检查API响应状态
        if data.get("status") != "1":
            error_msg = data.get("info", "未知错误")
            print(f"高德天气API返回错误: {error_msg}")
            return f"API错误: {error_msg}"

        # 提取天气数据
        lives = data.get("lives", [])
        if not lives:
            return "未找到天气数据"

        weather_info = lives[0]

        # 格式化结果
        result = {
            "城市": weather_info.get("city"),
            "天气": weather_info.get("weather"),
            "温度": f"{weather_info.get('temperature')}°C",
            "风向": weather_info.get("winddirection"),
            "风力": f"{weather_info.get('windpower')}级",
            "湿度": f"{weather_info.get('humidity')}%",
            "发布时间": weather_info.get("reporttime"),
        }

        return result

    except httpx.HTTPStatusError as e:
        print(f"HTTP错误: {str(e)}")
        return f"HTTP请求错误: {e.response.status_code}"
    except httpx.RequestError as e:
        print(f"请求错误: {str(e)}")
        return f"网络请求错误: {str(e)}"
    except Exception as e:
        print(f"获取天气信息时发生错误: {str(e)}")
        return f"获取天气信息时发生错误: {str(e)}"
