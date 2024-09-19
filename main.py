import logging
from email_processor import process_emails
from utils import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting the intelligent email automation system.")
    process_emails()
    logger.info("Email processing completed.")

if __name__ == '__main__':
    main()
