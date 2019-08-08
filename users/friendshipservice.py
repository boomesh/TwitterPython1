"""
Aids with managing friends of a user
"""
import os
import time
import requests
from static.constants import TRENDS_URL, FRIENDS_URL, FOLLOWERS_URL
from static.constants import USER_SEARCH_URL, FRIENDSHIP_CREATE_URL
from static.constants import FRIENDSHIP_DESTROY_URL, TWEET_SEARCH_URL
from static.logger import logging
from static.logger import res_err
import static.env

SCREEN_NAME = os.getenv("auth_user_screen_name")


class FriendshipService:
    """
    Long running service that will create friends or remove friends
    (in order to get more followers)
    """

    def __init__(self, session: requests.Session):
        self.session = session

    def create(self):
        """
        add friends based on the latest trends
        """
        # fetch the most popular trends on twitter (Canada)
        # file = open("mock/trends_ottawa.json", "r")
        # trends = json.load(file)[0]["trends"]
        # file.close()
        trends_res = self.session.get(f'{TRENDS_URL}?id=23424775')
        res_err(trends_res, "fetching trends")
        if trends_res.status_code < 200 or trends_res.status_code > 299:
            return
        trends = trends_res.json()[0]["trends"]

        # perform a user lookup based on the top trends
        # (memcache those users?)
        top_trends = trends[0:3]
        logging.info(f'top trends are: {top_trends}')

        # look for users who have hardcoded trend information in their profile
        # user_ids = []
        # for trend in top_trends:
        #     query = trend["query"]
        #     users = self.__fetch_users(query=query)
        #     # file = open("mock/users_search_summer_fun.json", "r")
        #     # users = json.load(file)
        #     # file.close()
        #     if not users:
        #         continue
        #     ids = map(lambda user: user["id"], users)
        #     user_ids.extend(ids)

        # look for unique users related to the trends
        trend_query = "%20OR%20".join(
            map(lambda trend: trend["query"], top_trends))
        tweets = self.__search_tweets(query=trend_query)
        user_ids = set()
        for tweet in tweets:
            user_ids.add(tweet["user"]["id"])
        logging.info(f'adding {len(user_ids)} friends')
        # follow all those memcached users
        for user_id in user_ids:
            self.__follow(user_id)
            # follow once a minute
            time.sleep(60)
        logging.info("friendship create complete")

    def purge(self):
        """
        remove friends that have not followed back
        """
        # fetch friends
        # https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-friendships-list
        r_friends = self.session.get(
            f'{FRIENDS_URL}?count=200&screen_name={SCREEN_NAME}')
        res_err(r_friends, "fetching people user is following")
        if r_friends.status_code < 200 or r_friends.status_code > 299:
            return

        # fetch followers
        # https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-followers-list
        r_followers = self.session.get(
            f'{FOLLOWERS_URL}?count=200&screen_name={SCREEN_NAME}')
        res_err(r_followers, "fetching user's followers")
        if r_followers.status_code < 200 or r_followers.status_code > 299:
            return

        friends = r_friends.json()['users']
        followers = r_followers.json()['users']

        # friends_file = open('mock/friends1.json', 'r')
        # followers_file = open('mock/followers1.json', 'r')
        # friends_json = json.load(friends_file)
        # followers_json = json.load(followers_file)
        # friends_file.close()
        # followers_file.close()
        # friends = friends_json['users']
        # followers = followers_json['users']

        # identify those who are not "followed_by"
        friend_ids = set(map(lambda user: user['id'], friends))
        follower_ids = set(map(lambda user: user['id'], followers))
        users_to_unfollow = friend_ids - follower_ids

        logging.info(f'{len(friend_ids)} friends')
        logging.info(f'{len(follower_ids)} followers')

        logging.info(f'removing {len(users_to_unfollow)} friends')
        # unfollow all those users
        for user_id in users_to_unfollow:
            self.__unfollow(user_id)
            # unfollow once a minute
            time.sleep(60)
        logging.info(f'purge completed')

    def __fetch_users(self, query):
        """
        https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-users-search
        """
        search_res = self.session.get(f'{USER_SEARCH_URL}?q={query}')
        res_err(search_res, f'searching users with query: {query}')
        if search_res.status_code < 200 or search_res.status_code > 299:
            return None
        json = search_res.json()
        logging.info(f'users search with {query} returned {len(json)} results')
        return json

    def __search_tweets(self, query):
        url = f'{TWEET_SEARCH_URL}?q={query}&count=60'
        tweets_res = self.session.get(url)
        res_err(tweets_res, f'searching tweets with query: {query}')
        if tweets_res.status_code < 200 or tweets_res.status_code > 299:
            return None
        tweets = tweets_res.json()["statuses"]

        # file = open("mock/tweets_hello_100.json", "r")
        # tweets = json.load(file)["statuses"]
        # file.close()
        logging.info(
            f'tweet search with {query} returned {len(tweets)} results')
        return tweets

    def __follow(self, user_id):
        """
        https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/post-friendships-create
        """
        create_res = self.session.post(
            f'{FRIENDSHIP_CREATE_URL}?user_id={user_id}')
        res_err(create_res, f'following user: {user_id}')

    def __unfollow(self, user_id):
        """
        https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/post-friendships-destroy
        """
        destroy_res = self.session.post(
            f'{FRIENDSHIP_DESTROY_URL}?user_id={user_id}')
        res_err(destroy_res, f'unfollowing user: {user_id}')
