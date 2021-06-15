from app import create_app, models
import logging


def __setup_logging():
    logging.basicConfig(format="[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S %z", level=logging.INFO)

def shutdown():
    logging.info("Stopped uberspace_mail_pw_reset_flask.")

def startup():
    logging.info("Started uberspace_mail_pw_reset_flask.")

__setup_logging()
app = create_app()
