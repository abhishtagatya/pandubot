keyword = {
    "food" : ["makan", "minum", "laper"],
    "bioskop" : ["sinema", "bioskop", "film"]
}

print(list(keyword.values()))

text = "laper nih"

for key, value in keyword.items():
    for word in value:
        if word in text:
            print(key)
