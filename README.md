# uberspace_mail_pw_reset_flask

A small flask project to securely allow resetting passwords of uberspace mailboxes without having access to the account itself.

## Translations

Before executing the application or doing any translation work, make sure the translation files are up to date:

	sh update_translations.sh

Ensure `pybabel` is either in `PATH` or in a venv so we find it in `bin/`

To start translating to a new language, run

	pybabel init -i strings.pot -d translations -l de

and substitute `de` for your language code.
