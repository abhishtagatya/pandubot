import json

from app import app, db
from app.models import *

from flask import (
    Flask, request, abort, url_for, current_app, render_template, redirect
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/store')
def store():
    row_limit = 5
    col_limit = 4

    query_all_market = MarketPlaceDatabase.query.all()
    chunked_all_market = []
    temp_all_market = []

    for i in range(len(query_all_market)):
        temp_all_market.append(query_all_market[i])
        if (len(temp_all_market) % col_limit == 0):
            chunked_all_market.append(temp_all_market)
            temp_all_market = []

    print(chunked_all_market)
    return render_template('store.html', store_list=chunked_all_market, row_limit=row_limit, col_limit=col_limit)

@app.route('/store/add')
def store_add():
    return render_template('store_adding.html')

@app.route('/store/add', methods=['POST', 'GET'])
def store_form():

    if request.method == 'POST':

        marktetId = request.form['owner-pandu-id']
        marketName = request.form['market-name']
        marketDemand = request.form['market-demand']
        marketPrice = request.form['market-price']
        marketDescription = request.form['market-description']
        marketAdditional = request.form['market-additional']

        ownerName = request.form['owner-name']
        ownerLINE = request.form['owner-line-id']
        ownerNumber = request.form['owner-telephone']

        # Additonal not required
        if (marketAdditional == '' or marketAdditional == None):
            marketAdditional = "{name} tidak menambahkan informasi lebih".format(
                name=ownerName
            )

        # Checking for valid Pandu ID
        valid_id = False
        for users in Users.query.all():
            if (users.id[:12] == marktetId):
                valid_id = True

        findMarket = MarketPlaceDatabase.query.filter_by(market_id=marktetId).first()
        if (findMarket == None and valid_id):
            new_market = MarketPlaceDatabase(
                market_id=marktetId,
                market_name=marketName,
                market_owner=ownerName,
                market_owner_line_id=ownerLINE,
                market_owner_number=ownerNumber,
                market_description=marketDescription,
                market_demand=marketDemand,
                market_price=marketPrice,
                market_additional=marketAdditional
            )
            db.session.add(new_market)
            db.session.commit()
        else :
            print('Error')
    return redirect('store')

@app.route('/greenlight')
def green_light():

    with open('data/envtips.json', 'r') as envtips:
        env_tips = json.load(envtips)

    return render_template('greenlight.html', tips=env_tips)

@app.route('/about')
def about():
    return render_template('about.html')
