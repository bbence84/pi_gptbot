import os
from dotenv import load_dotenv
import json
import yfinance as yf
import requests
load_dotenv()

from visionservice import VisionService


class AITools:
    def __init__(self, default_language="English", default_internet_market="hu-HU"):
        self.default_language = default_language
        self.default_internet_market = default_internet_market
        self.vision_service = VisionService(default_language=default_language)
        pass

    def call_tool(self, tool_name, function_args):

        print("CALLING FUNCTION: " + tool_name)

        if tool_name == "get_current_weather":
            func_arg = function_args.get("city_name")
            func_result = self.tool_get_current_weather(func_arg)
        elif tool_name == "search_internet":
            func_arg = function_args.get("query")
            func_result =  self.tool_search_internet(func_arg)
        elif tool_name == "get_stock_price":
            func_arg = function_args.get("symbol")
            func_result =  self.tool_get_stock_price(func_arg)
        elif tool_name == "get_whats_visible_on_camera":
            func_arg = {}
            func_result = self.vision_service.get_whats_visible_on_camera()
        else:
            return "Unknown tool"
        
        print("FUNCTION CALL RESULTS: " + tool_name + "(" + str(func_arg) + ")" + " -> " + str(func_result))
        return func_result        

    def get_tools_list(self):
        enable_stock_tool = True
        tools = [ ]
        if (enable_stock_tool):
            tools.append({
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "description": "Get the stock price for a given symbol",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {
                                "type": "string",
                                "description": "The stock symbol, e.g. AAPL",
                            }
                        },
                        "required": ["symbol"],
                    },
                },
            });
        if (os.environ.get('AZURE_OPENAI_GPT4V_API_KEY')):
            tools.append({
                "type": "function",
                "function": {
                    "name": "get_whats_visible_on_camera",
                    "description": "Get what is visible around you. Also can be used to describe what the bot can see in case it's requested or implied that vision skills is required.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                },
            });
        if (os.environ.get('OPENWEATHERMAP_API_KEY')):
            tools.append({
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "city_name": {
                                "type": "string",
                                "description": "The city name, e.g. New York",
                            }
                        },
                        "required": ["city_name"],
                    },
                },
            });
        if (os.environ.get('BING_SEARCH_API_KEY')):
            tools.append({
                "type": "function",
                "function": {
                    "name": "search_internet",
                    "description": "Searches on the internet for a current event, or something that might require up to date internet access",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "What to search for on the internet",
                            }
                        },
                        "required": ["query"],
                    },
                },
            });
        return tools
    
    def tool_search_internet(self, query):
        subscription_key = os.environ.get('BING_SEARCH_API_KEY')
        response = requests.get("https://api.bing.microsoft.com/v7.0/search", headers={ 'Ocp-Apim-Subscription-Key': subscription_key }, params={ 'q': query, 'mkt': self.default_internet_market,"count":3 })
        webpage_results = ''
        for webpage in response.json()['webPages']['value']:
            webpage_results += webpage['name'] + " | " + webpage['snippet'] + "\n "
        return webpage_results
            
    def tool_get_stock_price(self, symbol):
        stock_info = yf.Ticker(symbol)
        price = stock_info.info['currentPrice']
        return str(price)

    def tool_get_current_weather(self, city_name):
        open_weather_api_key = os.environ.get('OPENWEATHERMAP_API_KEY')
        complete_url = "http://api.openweathermap.org/data/2.5/weather?" + "appid=" + open_weather_api_key + "&units=metric&q=" + city_name
        response_json = requests.get(complete_url).json()
        return json.dumps({"city": city_name, "temperature": response_json["main"]["temp"], "description": response_json["weather"][0]["description"]})    