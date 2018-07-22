import os
import sys

from instance.config import DATABASE_URI

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_compress import Compress

app = Flask(__name__)
Compress(app)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

from app import bot
from app import web
