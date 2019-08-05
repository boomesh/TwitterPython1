"""
Setup for the logging mechanism.
Helper methods for logging mechanism go here too.
"""
import logging

logging.basicConfig(
    filename='output.log',
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')


def res_err(response, msg):
    """
    helper method to log response information from the requests library
    ONLY if the response code is not 2xx.
    """
    if response.status_code < 200 or response.status_code > 299:
        logging.error('RESPONSE CODE: %s', response.status_code)
        logging.error(msg)
        logging.error(response.text)
