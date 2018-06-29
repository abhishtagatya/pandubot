import json

msg = "token RAFFLESHILLS"
inp_token = msg.split()[1]
print(inp_token)

travel_point = 10

with open('data/token.json', 'r') as token_file:
    token_list = json.load(token_file)

status = False

for provider in token_list['token_list']:
    if (inp_token == provider['token']):
        status = True
        travel_point += provider['value']
        break

if status:
    print(travel_point)
