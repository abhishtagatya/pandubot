import json
import random

keyword = {
    "food:makan" : ["makan", "minum", "laper"],
    "bioskop" : ["sinema", "bioskop", "film"]
}

text = "hi pandu"

with open('data/keyword.json', 'r') as keyword:
    query = json.load(keyword)

with open('data/speech.json', 'r') as speechwords:
    speech = json.load(speechwords)

places_list = [
    "Hello",
    "World"
]

for count, places in enumerate(places_list):
    print(count, places)
