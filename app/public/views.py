from flask import render_template, redirect, request, escape, flash, url_for
from flask_babel import lazy_gettext as _l
from . import public
from .. import babel, db
from ..models import Token
import logging

from xkcdpass import xkcd_password as xp
import random, os, subprocess
import datetime
import urllib.parse, re
from string import ascii_letters, digits
import mailbox

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

def send_token_mail(box, token):
    #url = '{}{}'.format(os.getenv('URL_BASE'), url_for('public.index', t=token))
    url = url_for('public.index', t=token, _external=True)

    try:
        mb = mailbox.Maildir("~/users/{}".format(box), create=False)
    except mailbox.NoSuchMailboxError as e:
        print(e)
        return False

    mb.lock()

    try:
        msg = mailbox.MaildirMessage()
        msg.set_subdir('new')
        msg.set_date(datetime.datetime.utcnow())
        msg.add_flag('F')   # mark as important
        msg['From'] = os.getenv('MAIL_SENDER')
        msg['To'] = '{}@{}'.format(box, os.getenv('MAIL_RECEIVER_DOMAIN'))
        msg['Subject'] = _l('Password reset token')
        msg.set_payload("test test: {}".format(url))

        mb.add(msg)
        mb.flush()

        return True
    except Exception as e:
        print(e)
        return False
    finally:
        mb.unlock()

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
        if send_token_mail(token.mailbox, token.token):
            print('Sent token mail to {}'.format(token.mailbox))
        else:
            print('Failed to send token mail to {}'.format(token.mailbox))

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

            for i in range(2):
                # generate new pw
                password = ensure_ascii(generate_pw())
                # change mailbox pw
                print('### SETTING NEW PASSWORD FOR {}"'.format(token_query.mailbox))
                proc = subprocess.run(["uberspace", "mail", "user", "password", "-p", password, token_query.mailbox], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                if proc.returncode == 0:
                    break

            if proc.returncode == 0:
                token_query.successful = True
                db.session.commit()

                return render_template("/public/success.html",
                    password=password)
            else:
                return render_template("/public/error.html",
                    stderr=proc.stderr)
    else:
        flash(_l("Invalid request: No token. Please try again."))

    return render_template("/public/index.html")
