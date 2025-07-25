import json
import requests
import functools

def post_request_decorator(endpoint):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):  # 明确接收 self（WeatherService 实例）
            try:
                # 调用被装饰的方法（如 getLocationWeather），传入 self 和参数
                data = func(self, *args, **kwargs)
                response = requests.post(
                    endpoint,
                    json=data,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                if response.status_code == 200:
                    resp_data = response.json()
                    if endpoint == 'http://192.168.68.54/weather':
                        print(resp_data)
                        # 从参数中获取要查询的地点（如 Hong Kong Park）
                        place_to_find = args[0] if args else None
                        # 在 post_request_decorator 的 endpoint == 'http://192.168.68.54/weather' 分支中
                        if place_to_find:
                            temps = resp_data.get('temp', [])
                            places = resp_data.get('place', [])
                            found = False
                            # 遍历响应中的地点，与查询地点精确匹配（忽略大小写）
                            for i, place in enumerate(places):
                                # 统一转为小写后比较，避免大小写问题；使用 == 而非 in，确保完全匹配
                                if place.lower() == place_to_find.lower():
                                    self.speak(f"Today Weather in {place} is {temps[i]} degree.")
                                    found = True
                                    break
                            if not found:
                                self.speak(f"Weather data for '{place_to_find}' not found.")
                        else:
                            # 若未指定地点，播报所有地点天气
                            for place, temp in zip(places, temps):
                                self.speak(f"Today Weather in {place} is {temp} degree.")
                    elif endpoint == 'http://192.168.68.54/weatherinformation':
                        # 处理整体天气信息
                        self.speak("Here are today's weather information:")
                        self.speak(f"{resp_data.get('generalSituation', 'N/A')}")
                        self.speak(f"Typhoon info: {resp_data.get('tcInfo', 'No typhoon')}")
                        self.speak(f"Fire danger warning: {resp_data.get('fireDangerWarning', 'None')}")
                        self.speak(f"Forecast period: {resp_data.get('forecastPeriod', 'N/A')}")
                        self.speak(f"Forecast: {resp_data.get('forecastDesc', 'N/A')}")
                        self.speak(f"Outlook: {resp_data.get('outlook', 'N/A')}")
                    return resp_data
                else:
                    self.speak(f"Request failed with status {response.status_code}")
                    return None
            except requests.exceptions.RequestException as e:
                print(f"Network error: {str(e)}")
            except json.JSONDecodeError:
                print("Invalid JSON response")
            return None
        return wrapper
    return decorator

class WeatherService:
    def __init__(self, speak):
        self.speak = speak  # 接收语音播报方法（从 MainAssistant 传入）

    # 移除错误的 lambda 占位符，装饰器会自动使用 self.speak
    @post_request_decorator('http://192.168.68.54/weather')
    def getLocationWeather(self, place):
        # 向接口传递查询的地点（关键：确保参数正确）
        return {"place": place}

    @post_request_decorator('http://192.168.68.54/weatherinformation')
    def getWeatherInformation(self):
        # 无参数，返回空字典
        return {}