import logging

def setup_logging():
    logging.basicConfig(
        filename='logs/app.log',
        filemode='a',
        format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
        level=logging.INFO
    )
