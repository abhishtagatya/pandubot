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

for key, value in query['interaction'].items():
    for word in value:
        if word in text:
            print(random.choice(speech['speech'][key]['answer']).format(
                name = 'Name',
                baseball = 'baseball'
            ))
            break
