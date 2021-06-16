import datetime
from . import db

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(128), unique=True, nullable=False)
    tmp_pass = db.Column(db.String(128), unique=True, nullable=True)
    mailbox = db.Column(db.String(64), nullable=True)
    requested = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=False)
    used = db.Column(db.DateTime(), nullable=True)
    successful = db.Column(db.Boolean(), nullable=True)
    initial_use = db.Column(db.Boolean(), default=False)

    def __init__(self, token, mailbox, initial_use=False):
        self.token = token
        self.mailbox = mailbox
        self.initial_use = initial_use

    def __repr__(self):
        return "<Token {}>".format(self.token)
