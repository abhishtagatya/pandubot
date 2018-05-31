import os
import sys
import json

import requests
from instance.config import ZOMATO_API_KEY

class ZomatoAPI:

    def __init__(self, key=ZOMATO_API_KEY, baseurl='https://developers.zomato.com/api/v2.1/'):
        self.key = key
        self.baseurl = baseurl

        self.headers = {
            "User-agent": "curl/7.43.0",
            "Content-type": "application/json",
            "X-Zomato-API-Key": self.key
        }

    def geocode(self, latitude, longitude):
        geocode_url = self.baseurl + 'geocode?lat={}&lon={}'.format(latitude, longitude)
        response = requests.get(url=geocode_url, headers=self.headers).json()
        #response_jsonify = response.json()

        restaurant_list = response['nearby_restaurants']
        return restaurant_list