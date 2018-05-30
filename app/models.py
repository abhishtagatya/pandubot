from datetime import datetime
from app import db

class Users(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(20))
    location = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    def __init__(self, id, name, location, latitude, longitude):
        self.id = id
        self.name = name
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
