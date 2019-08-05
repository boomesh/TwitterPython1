"""
The main module serves as the entry point for the whole twitter user

also contains a helper function to manually fetch the auth tokens (and update
in the .env)
"""
import os
from pprint import pprint
from requests_oauthlib import OAuth1Session
import static.env
from static.constants import REQUEST_TOKEN_URL
from static.constants import AUTHENTICATE_URL
from static.constants import ACCESS_TOKEN_URL
from jobscheduler.actionscheduler import ActionScheduler


def user_context_auth():
    """
    Manually call this function to begin the auth process to refetch the resource
    owner tokens.

    Source:
    https://developer.twitter.com/en/docs/basics/authentication/overview/pin-based-oauth
    """
    session = OAuth1Session(
        os.getenv("oauth_consumer_key"),
        client_secret=os.getenv("oauth_consumer_secret"),
        callback_uri=os.getenv("oauth_callback"))

    session.fetch_request_token(REQUEST_TOKEN_URL)
    auth_url = session.authorization_url(AUTHENTICATE_URL)
    print(auth_url)
    oauth_verifier = input("Visit the above URL, and paste the PIN here: ")
    raw = session.fetch_access_token(ACCESS_TOKEN_URL, verifier=oauth_verifier)
    pprint(raw)


def main():
    """
    The entry point of the program
    - will initialize the process-wide session
    """
    twitter = OAuth1Session(
        os.getenv("oauth_consumer_key"),
        client_secret=os.getenv("oauth_consumer_secret"),
        resource_owner_key=os.getenv("oauth_token"),
        resource_owner_secret=os.getenv("oauth_token_secret"))

    scheduler = ActionScheduler(twitter)
    scheduler.execute()


if __name__ == "__main__":
    # f = FriendshipService(TWITTER)
    # f.create()
    main()
