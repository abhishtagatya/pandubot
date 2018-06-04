import os
import sys
import json

from instance.config import GOOGLE_MAPS_API_KEY

import requests
import googlemaps

class GoogleMapsAPI:

    def __init__(self, key=GOOGLE_MAPS_API_KEY):
        self.gmaps = googlemaps.Client(key=key)

    def geocode(self, location):
        location = self.gmaps.geocode(location)
        return location

    def places(self, query, location, radius=10, open_now=True):
        places = self.gmaps.places(query=query, location=location, radius=radius, open_now=open_now)
        return places

    def place(self, id):
        place = self.gmaps.place(id)
        return place
