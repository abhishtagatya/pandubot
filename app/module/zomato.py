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

    def category(self):
        category_url = self.baseurl + 'categories'
        response = requests.get(url=category_url, headers=self.headers).json()

        return response

    def cities(self, query, latitude=None, longitude=None, city_id=None, count=5):
        cities_url = self.baseurl + 'cities?q={q}&lat={lat}&lon={lon}&city_ids={cityid}&count={count}'.format(
            q=query, lat=latitude, lon=longitude,
            cityid=city_id, count=count
        )
        response = requests.get(url=cities_url, headers=self.headers).json()
        return response

    def collections(self, city_id, latitude=None, longitude=None, count=5):
        collections_url = self.baseurl + 'collections?city_id={cityid}&lat={lat}&lon={lon}&count={count}'.format(
            cityid=city_id, count=count,
            lat=latitude, lon=longitude
        )
        response = requests.get(url=collections_url, headers=self.headers).json()
        return response

    def cuisines(self, city_id, latitude=None, longitude=None):
        cuisines_url = self.baseurl + 'cuisines?city_id={cityid}&lat={lat}&lon={lon}'.format(
            lat=latitude, lon=longitude,
            cityid=city_id
        )
        response = requests.get(url=cuisines_url, headers=self.headers).json()
        return response

    def establishments(self, city_id, latitude=None, longitude=None):
        establishments_url = self.baseurl + 'establishments?city_id={cityid}&lat={lat}&lon={lon}'.format(
            lat=latitude, lon=longitude,
            cityid=city_id
        )
        response = requests.get(url=establishments_url, headers=self.headers).json()
        return response


    def geocode(self, latitude, longitude, price_range=None):
        geocode_url = self.baseurl + 'geocode?lat={lat}&lon={lon}'.format(lat=latitude, lon=longitude)
        response = requests.get(url=geocode_url, headers=self.headers).json()
        #response_jsonify = response.json()

        restaurant_list = response['nearby_restaurants']
        return restaurant_list

    def location_details(self, entity_id, entity_type):
        locdetails_url = self.baseurl + 'location_details?entity_id={id}&entity_type={type}'.format(
            id=entity_id, type=entity_type
        )
        response = requests.get(url=locdetails_url, headers=self.headers).json()
        return response

    def locations(self, query, latitude=None, longitude=None, count=5):
        locations_url = self.baseurl + 'locations?q={q}&lat={lat}&lon={lon}&count={count}'.format(
            q=query, lat=latitude,
            lon=longitude, count=count
        )
        response = requests.get(url=locations_url, headers=self.headers).json()
        return response

    def dailymenu(self, res_id):
        dailymenu_url = self.baseurl + 'dailymenu?res_id={id}'.format(
            id=res_id
        )
        response = requests.get(url=dailymenu_url, headers=self.headers).json()
        return response

    def restaurant(self, res_id):
        restaurant_url = self.baseurl + 'restaurant?res_id={id}'.format(
            id=res_id
        )
        response = requests.get(url=restaurant_url, headers=self.headers).json()
        return response

    def reviews(self, res_id, start=None, count=5):
        reviews_url = self.baseurl + 'reviews?res_id={id}&start={start}&count={count}'.format(
            id=res_id, start=start, count=count
        )

        response = requests.get(url=reviews_url, headers=self.headers).json()
        return response

    def search(self, query, entity_id=None, entity_type=None, start=None,
        latitude=None, longitude=None, radius=None, cuisines=None, establishment_type=None,
        collection_id=None, category=None, sort=None, order=None, count=5):

        search_url = self.baseurl + """search?
        entity_id={id}&
        entity_type={type}&
        q={q}&
        start={start}&
        count={count}&
        lat={lat}&
        lon={lon}&
        radius={radius}&
        cuisines={cuisines}&
        establishment_type={est_type}&
        collection_id={col_id}&
        category={category}&
        sort={sort}&
        order={order}""".format(
            id=entity_id, type=entity_type, q=query, start=start, count=count,
            lat=latitude, lon=longitude, radius=radius, cuisines=cuisines,
            est_type=establishment_type ,col_id=collection_id, category=category,
            sort=sort, order=order
        )

        response = requests.get(url=search_url, headers=self.headers).json()
        return response
