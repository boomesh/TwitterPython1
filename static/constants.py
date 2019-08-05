"""
Constants to be used throughout this program
stored here.
"""
ROOT_URL = "https://api.twitter.com"
UPLOAD_URL = "https://upload.twitter.com"

REQUEST_TOKEN_URL = f'{ROOT_URL}/oauth/request_token'
AUTHENTICATE_URL = f'{ROOT_URL}/oauth/authenticate'
ACCESS_TOKEN_URL = f'{ROOT_URL}/oauth/access_token'

VERSION = '1.1'

USER_SEARCH_URL = f'{ROOT_URL}/{VERSION}/users/search.json'
FRIENDSHIP_CREATE_URL = f'{ROOT_URL}/{VERSION}/friendships/create.json'
FRIENDSHIP_DESTROY_URL = f'{ROOT_URL}/{VERSION}/friendships/destroy.json'
FRIENDS_URL = f'{ROOT_URL}/{VERSION}/friends/list.json'
FOLLOWERS_URL = f'{ROOT_URL}/{VERSION}/followers/list.json'

STATUS_UPDATE_URL = f'{ROOT_URL}/{VERSION}/statuses/update.json'
MEDIA_UPLOAD_URL = f'{UPLOAD_URL}/{VERSION}/media/upload.json'

TRENDS_URL = f'{ROOT_URL}/{VERSION}/trends/place.json'
