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

    def __init__(self, token, mailbox):
        self.token = token
        self.mailbox = mailbox

    def __repr__(self):
        return "<Token {}>".format(self.token)
