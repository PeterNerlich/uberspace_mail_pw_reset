from flask import render_template, redirect, request, escape, flash, url_for
from flask_babel import lazy_gettext as _l
from . import public
from .. import babel, db
from ..models import Token
import logging

import os, subprocess
import datetime, time
import urllib.parse

from do_the_pw_thing import generate_pw, ensure_ascii, tmp_pass
from do_the_mail_thing import send_token_mail, send_genuine_mail

#
# Locale Initialization
#

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(os.getenv('LANGUAGES').split(','))

#
# Static Functions
#

#
# Routes
#

@public.route("/", methods=["GET","POST"])
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

@public.route("/request", methods=["GET","POST"])
def req():
    if 'request_btn' in request.form and 'mailbox' in request.form and request.form['mailbox'] != '' and request.form['mailbox'] not in os.getenv('BLACKLISTED_MAILBOXES').split(','):
        # create token, set start ts
        token = Token(token=ensure_ascii(generate_pw(random_delimiters=False, numwords=4)), mailbox=request.form['mailbox'])
        db.session.add(token)
        db.session.commit()

        # deposit mail for user if mailbox exists, but don't tell
        if send_token_mail(token.mailbox,
                f=os.getenv('MAIL_SENDER'),
                t='{}@{}'.format(token.mailbox, os.getenv('MAIL_RECEIVER_DOMAIN')),
                s=_l('Password reset token'),
                p=render_template("/mail_reset_token.j2",
                    url=url_for('public.index', t=token.token, _external=True))):
            print('Sent token mail to {}'.format(token.mailbox))
        else:
            print('Failed to send token mail to {}'.format(token.mailbox))

        return render_template("/public/requested.html")

    else:
        flash(_l("Invalid request: Please try again."))
        return render_template("/public/index.html")

def initial_use_mail(mailbox: str, receiver: str):
    token = Token(token=ensure_ascii(generate_pw(random_delimiters=False, numwords=6)), mailbox=mailbox, initial_use=True)
    db.session.add(token)
    db.session.commit()

    def fake_tr(s, *args, **kwargs):
        return s

    tmp_pass = ensure_ascii(generate_pw(numwords=8))
    print('### SETTING NEW TMP PASS FOR {}'.format(mailbox))
    proc = subprocess.run(["uberspace", "mail", "user", "password", "-p", tmp_pass, mailbox], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    send_genuine_mail(
        f='{}@{}'.format(mailbox, os.getenv('MAIL_RECEIVER_DOMAIN')),
        t=receiver.split(','),
        s='[{}] {}'.format(mailbox, 'Password reset token'),
        p=render_template("mail_initial_use.j2",
            url=url_for('public.index', t=token.token, _external=True),
            l=fake_tr),
        tmp_pass=tmp_pass)


@public.route("/reset", methods=["GET","POST"])
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

@public.route("/access", methods=["GET","POST"])
def access():
    return render_template("/public/access.html",
        hostname=os.getenv('MAIL_HOSTNAME'))
