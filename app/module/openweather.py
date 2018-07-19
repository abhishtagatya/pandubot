import os
import sys
import json
import requests

from instance.config import WEATHER_MAP_API

# Mapping to the Weather ID
weather_code_range = [
    (range(200,233), 'thunderstorm'),
    (range(300, 332), 'rain'),
    (range(500, 532), 'shower rain'),
    (range(600, 622), 'snow'),
    (range(701,782), 'mist'),
    ([800], 'clear sky'),
    ([801], 'few clouds'),
    ([802], 'scattered clouds'),
    ([803,804], 'broken clouds')
]

class OpenWeatherAPI(object):

    def __init__(self, key=WEATHER_MAP_API, headers=None, debug_mode=False, *args,**kwargs):
        self.key = key
        self.debug = debug_mode
        self.args = args
        self.kwargs = kwargs

        self.baseurl = 'https://api.openweathermap.org/data/2.5/'

        if (headers != None):
            self.headers = headers
        else :
            self.headers = {
                "User-agent": "curl/7.43.0",
                "Content-type": "application/json",
                "User-key": self.key
            }

    def current_weather(self, **option):
        """ Get current weather data by city name """

        option['appid'] = self.key

        if 'coordinate' in option:
            if type(option['coordinate']) is str:
                lat, lon = option['coordinate'].split()
            else :
                lat, lon = option['coordinate']

            option['lat'] = lat
            option['lon'] = lon
            del option['coordinate']

        weather_url = self.baseurl + 'weather'
        response = requests.get(url=weather_url, params=option, headers=self.headers)
        if (self.debug):
            print(response.url)

        return response.json()
