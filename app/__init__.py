from app.config import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET_TOKEN

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/LINEUser.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


from app import routes
