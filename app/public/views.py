from flask import render_template, redirect, request, escape, flash, url_for
from flask_babel import lazy_gettext as _l
from . import public
from .. import babel, db
from ..models import Token
import logging

from xkcdpass import xkcd_password as xp
import random, datetime, os, urllib.parse, re
from string import ascii_letters, digits

#
# Locale Initialization
#

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(os.getenv('LANGUAGES').split(','))

#
# Static Functions
#

special_chars = ".,:-_#+*~=?!$%&/<>"
chars = tuple(set(ascii_letters + digits + special_chars))
rand_gen = random.SystemRandom()

def generate_pw(wordfile="ger-anlx,eff-short", random_delimiters=True, numwords=6):
    wordfile = wordfile or xp.locate_wordfile()
    mywords = xp.generate_wordlist(wordfile=wordfile)

    dl = '-'
    if random_delimiters:
        dl = rand_gen.choice(special_chars)

    return xp.generate_xkcdpassword(mywords, delimiter=dl)

def ensure_ascii(pw):
    replacements = [
        ('ä', 'ae'),
        ('ö', 'oe'),
        ('ü', 'ue'),
        ('Ä', 'AE'),
        ('Ö', 'OE'),
        ('U', 'UE'),
        ('ß', 'ss'),
        ('ẞ', 'SS')
    ]

    for i in replacements:
        pw = pw.replace(i[0], i[1])

    return re.sub('[^{}]+'.format(re.escape(''.join(chars))), '_', pw)

def tmp_pass(length=128):
    return u''.join(rand_gen.choice(chars) for dummy in range(length))

#
# Routes
#

@public.route("/", methods=["GET"])
def index():
    token = request.args.get('t')

    if token in (None, ''):
        return render_template("/public/index.html")
    else:
        # check token validity: in db, no used, not expired
        token_query = Token.query.filter_by(token=token).first()
        now = datetime.datetime.utcnow()

        if token_query is None:
            flash(_l("Invalid token: This token does not exist."))
        elif token_query.used:
            flash(_l("Invalid token: This token was already used."))
        elif now - token_query.requested > datetime.timedelta(seconds=int(os.getenv('TOKEN_SECONDS_VALID'))):
            flash(_l("Invalid token: This token has expired."))
        else:
            token_query.used = now
            token_query.tmp_pass = tmp_pass()
            db.session.commit()

            return render_template("/public/reset.html",
                token=token_query)

        return render_template("/public/reset.html",
            token=None)

@public.route("/request", methods=["POST"])
def req():
    if 'request_btn' in request.form:
        # create token, set start ts
        token = Token(token=ensure_ascii(generate_pw(random_delimiters=False, numwords=4)), mailbox=request.form['mailbox'])
        db.session.add(token)
        db.session.commit()

        # deposit mail for user if mailbox exists, but don't tell
        # TODO
        print('TODO: deposit to {}: {}{}?t={}'.format(token.mailbox, os.getenv('URL_BASE'), url_for('public.index'), urllib.parse.quote(token.token)))

    return render_template("/public/requested.html")

@public.route("/reset", methods=["POST"])
def reset():
    if 'reset_btn' in request.form and 'tmp_pass' in request.form:
        token_query = Token.query.filter_by(tmp_pass=request.form['tmp_pass']).first()
        now = datetime.datetime.utcnow()

        if token_query is None:
            flash(_l("Invalid token: This token does not exist."))
        elif token_query.successful != None:
            flash(_l("Invalid request: Reset was already used."))
        elif now - token_query.used > datetime.timedelta(int(os.getenv('TOKEN_MAX_DELAY_TO_RESET'))):
            flash(_l("Invalid request: Too much time between token usage and actual password reset."))
        elif now - token_query.requested > datetime.timedelta(seconds=int(os.getenv('TOKEN_SECONDS_VALID')) + 10):   # 10 seconds extra
            flash(_l("Invalid token: This token has expired."))
        else:
            token_query.successful = False
            db.session.commit()

            # generate new pw
            password = ensure_ascii(generate_pw())
            # change mailbox pw
            print('TODO: uberspace mail user password -p "{}" "{}"'.format(password, token_query.mailbox))

            token_query.successful = True
            db.session.commit()

            return render_template("/public/success.html",
                password=password)
    else:
        flash(_l("Invalid request: No token. Please try again."))

    return render_template("/public/index.html")