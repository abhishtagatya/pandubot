from datetime import datetime
from app import db

class Users(db.Model):

    __tablename__ = 'Users'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(50))
    location = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    travel_point = db.Column(db.Integer)

    def __init__(self, id, name, location, latitude, longitude, travel_point):
        self.id = id
        self.name = name
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.travel_point = travel_point

class TravelPointToken(db.Model):

    __tablename__ = 'TravelPointToken'

    token_id = db.Column(db.String(12), primary_key=True)
    token_name = db.Column(db.String(50))
    token_point_value = db.Column(db.Integer)
    token_point_visitor = db.Column(db.Integer)

    def __init__(self, token_id, token_name, token_point_value, token_point_visitor):
        self.token_id = token_id
        self.token_name = token_name
        self.token_point_value = token_point_value
        self.token_point_visitor = token_point_visitor

class TravelPointPromotion(db.Model):

    __tablename__ = 'TravelPointPromotion'

    promotion_id = db.Column(db.String(12), primary_key=True)
    promotion_name = db.Column(db.String(50))
    promotion_description = db.Column(db.String(100))
    promotion_category = db.Column(db.String(20))
    promotion_cost = db.Column(db.Integer)
    promotion_secret = db.Column(db.String(12))

    def __init__(self, promotion_id, promotion_name, promotion_description, promotion_category,
        promotion_cost, promotion_secret):
        self.promotion_id = promotion_id
        self.promotion_name = promotion_name
        self.promotion_description = promotion_description
        self.promotion_category = promotion_category
        self.promotion_cost = promotion_cost
        self.promotion_secret = promotion_secret

'Untuk mengetahui lingkungan Anda, dapatkah Anda membagikan lokasi Anda dengan mengirimkan Send Location?'

class MarketPlaceDatabase(db.Model):

    __tablename__ = 'MarketPlaceDatabase'

    market_id = db.Column(db.String(12), primary_key=True)
    market_name = db.Column(db.String(50))
    # Contact Point
    market_owner = db.Column(db.String(20))
    market_owner_line_id = db.Column(db.String(20))
    market_owner_number = db.Column(db.String(15))
    # Information
    market_description = db.Column(db.String(70))
    market_demand = db.Column(db.String(20))
    market_price = db.Column(db.Integer)
    market_additional = db.Column(db.String(100))

    def __init__(self, market_id, market_name, market_owner, market_owner_line_id,
        market_owner_number, market_description, market_demand, market_price, market_additional):

        self.market_id = market_id
        self.market_name = market_name
        self.market_owner = market_owner
        self.market_owner_line_id = market_owner_line_id
        self.market_owner_number = market_owner_number
        self.market_description = market_description
        self.market_demand = market_demand
        self.market_price = market_price
        self.market_additional = market_additional
