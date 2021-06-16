from app import create_app_context_only
import logging
import sys

logging.basicConfig(format="[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S %z", level=logging.INFO)

app = create_app_context_only()

from app.public.views import initial_use_mail

with app.app_context():
    initial_use_mail(sys.argv[1], sys.argv[2])
