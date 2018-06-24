import json

keyword = {
    "food:makan" : ["makan", "minum", "laper"],
    "bioskop" : ["sinema", "bioskop", "film"]
}

print(list(keyword.values()))

text = "laper nih"

with open('data/keyword.json', 'r') as keyword:
    query = json.load(keyword)

    print(query['search'].items())

for key, value in query['search'].items():
    for word in value:
        if word in text:
            print(key)
