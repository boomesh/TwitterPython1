"""
A long running service pertaining to posting a tweet
"""
import json
import os
import requests
from static.constants import MEDIA_UPLOAD_URL, STATUS_UPDATE_URL
from static.logger import logging
from static.logger import res_err

TWEETS = "cached/tweets/tweets.json"
TWEETED = "cached/tweets/tweeted.json"


class TweetService:  # pylint: disable=too-few-public-methods
    """
    the this is a long running service which will post tweets
    from the cached/tweets/tweets.json map.
    """

    def __init__(self, session: requests.Session):
        self.session = session
        self.tweeted = []
        self.tweets = []

    def tweet(self):
        """
        fetch from local json
        post the first tweet in the list
        then record that the tweet was tweeted
        """
        self.__refresh_local_tweets()

        if not self.tweets:
            return

        tweet_obj = self.tweets[0]

        # upload picture
        media_id = self.__upload_media(tweet_obj["img"])

        # tweet with text, and image
        if not media_id:
            return
        self.__post_status(tweet_obj["text"], media_id)

        self.tweets.remove(tweet_obj)
        self.tweeted.append(tweet_obj)
        self.__update_local_tweets()

    def __refresh_local_tweets(self):
        """
        fetch latest tweets saved from json
        """
        f_tweets = open(f'{TWEETS}', 'r')
        f_tweeted = open(f'{TWEETED}', 'r')

        try:
            self.tweets = json.load(f_tweets)
            self.tweeted = json.load(f_tweeted)
        finally:
            f_tweets.close()
            f_tweeted.close()

    def __update_local_tweets(self):
        """
        record the modified tweet/tweeted structures on disk
        """
        f_tweets = open(f'{TWEETS}', 'w')
        f_tweeted = open(f'{TWEETED}', 'w')
        try:
            f_tweets.write(json.dumps(self.tweets, sort_keys=True, indent=4))
            f_tweeted.write(json.dumps(self.tweeted, sort_keys=True, indent=4))
        finally:
            f_tweets.close()
            f_tweeted.close()

    def __post_status(self, text, media_id):
        """
        post the tweet with a media and text
        """
        params = {
            "status": text,
            "media_ids": ",".join(map(str, [media_id]))
        }
        response = self.session.post(STATUS_UPDATE_URL, data=params)
        res_err(response, "POSTING THE TWEET AFTER MEDIA UPLOAD")
        logging.info(f'posted {text}')

    def __upload_media(self, file_name):
        """
        Using https://github.com/twitterdev/large-video-upload-python/blob/master/async-upload.py
        as a resource
        """
        file_path = f'resources/pictures/{file_name}'
        file_size = os.path.getsize(file_path)

        # INIT
        params = {
            "command": "INIT",
            "media_type": "image/jpeg",
            "total_bytes": file_size
        }
        init_response = self.session.post(MEDIA_UPLOAD_URL, data=params)
        res_err(init_response, "MEDIA UPLOAD INIT")
        if init_response.status_code < 200 or init_response.status_code > 299:
            return None
        logging.info(f'{file_name} INIT succeeded')
        media_id = init_response.json()['media_id']

        # APPEND CHUNKED
        segment_id = 0
        bytes_sent = 0
        media_file = open(file_path, 'rb')
        try:
            while bytes_sent < file_size:
                # read 4MB at a time
                chunk = media_file.read(4*1024*1024)
                params = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_id
                }

                files = {
                    "media": chunk
                }
                chunk_res = self.session.post(
                    MEDIA_UPLOAD_URL, data=params, files=files)
                res_err(chunk_res, "MEDIA UPLOAD APPEND")
                res_err(chunk_res, f'({bytes_sent}/{file_size}) {file_path}')
                if chunk_res.status_code < 200 or chunk_res.status_code > 299:
                    return None

                segment_id = segment_id + 1
                bytes_sent = media_file.tell()
        finally:
            media_file.close()
        logging.info(f'{file_name} CHUNK succeeded')
        # FINALIZE
        params = {
            "command": "FINALIZE",
            "media_id": media_id,
        }
        fin_res = self.session.post(MEDIA_UPLOAD_URL, data=params)
        res_err(fin_res, "MEDIA UPLOAD FINALIZE")
        if fin_res.status_code < 200 or fin_res.status_code > 299:
            return None
        logging.info(f'{file_name} {media_id} FINALIZE succeeded')
        # RETURN MEDIA_ID
        return media_id
