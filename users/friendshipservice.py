"""
Aids with managing friends of a user
"""
import os
import time
import requests
from static.constants import TRENDS_URL, FRIENDS_URL, FOLLOWERS_URL
from static.constants import USER_SEARCH_URL, FRIENDSHIP_CREATE_URL
from static.constants import FRIENDSHIP_DESTROY_URL, TWEET_SEARCH_URL
from static.constants import TWEET_LIKE_URL, TWEET_UNLIKE_URL
from static.constants import RETWEET_URL, REMOVE_RETWEET_URL
from static.constants import FAVOURITED_TWEETS_URL
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
        user_tweet_map = {}
        for tweet in tweets:
            user_tweet_map[tweet["user"]["id"]] = tweet
        logging.info(f'adding {len(user_tweet_map)} friends')
        logging.info(f'liking {len(user_tweet_map)} tweets')
        # follow all those memcached users
        for user_id, tweet in user_tweet_map.items():
            self.__follow(user_id)
            self.__like(tweet)
            # once every ten seconds
            time.sleep(10)

    def purge(self):
        """
        remove friends, unlike tweets of friends that have not followed back
        """
        # fetch all the user's friends
        friends = []
        next_cursor = -1
        while next_cursor != 0:
            pair = self.__fetch_friends(cursor=next_cursor)
            if pair is None:
                return
            next_cursor = pair[0]
            friends.extend(pair[1])
            time.sleep(5)

        # fetch all the user's followers
        followers = []
        next_cursor = -1
        while next_cursor != 0:
            pair = self.__fetch_followers(cursor=next_cursor)
            if pair is None:
                return
            next_cursor = pair[0]
            followers.extend(pair[1])
            time.sleep(5)

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
            # unfollow once every five seconds
            time.sleep(5)

        # unfavourite all tweets
        favourites = self.__favourited_tweets()
        logging.info(f'unliking {len(favourites)} tweets')
        # unlike all favourited tweets
        for tweet in favourites:
            self.__unlike(tweet)
            # unlike once every five seconds
            time.sleep(5)
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
        url = f'{TWEET_SEARCH_URL}?q={query}&count=100'
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

    def __fetch_friends(self, cursor=-1):
        # fetch friends
        # https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-friendships-list
        friends = []
        url = (f'{FRIENDS_URL}'
               "?count=200"
               f'&cursor={cursor}'
               f'&screen_name={SCREEN_NAME}')
        r_friends = self.session.get(url)
        res_err(r_friends, "fetching people user is following")
        if r_friends.status_code < 200 or r_friends.status_code > 299:
            return None
        res = r_friends.json()
        next_cursor = res["next_cursor"]
        friends = res["users"]
        return (next_cursor, friends)

    def __fetch_followers(self, cursor=-1):
        # fetch followers
        # https://developer.twitter.com/en/docs/accounts-and-users/follow-search-get-users/api-reference/get-followers-list
        followers = []
        next_cursor = -1
        url = (f'{FOLLOWERS_URL}'
               "?count=200"
               f'&cursor={cursor}'
               f'&screen_name={SCREEN_NAME}')
        r_followers = self.session.get(url)
        res_err(r_followers, "fetching user's followers")
        if r_followers.status_code < 200 or r_followers.status_code > 299:
            return None
        res = r_followers.json()
        followers = res["users"]
        next_cursor = res["next_cursor"]
        return (next_cursor, followers)

    def __favourited_tweets(self):
        """
        https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/get-favorites-list
        """
        response = self.session.get(
            f'{FAVOURITED_TWEETS_URL}?count=200&screen_name={SCREEN_NAME}')
        res_err(response, f'fetching favourite tweets')
        if response.status_code < 200 or response.status_code > 299:
            return None
        tweets = response.json()
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

    def __like(self, tweet):
        """
        https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/post-favorites-create.html
        """
        response = self.session.post(
            f'{TWEET_LIKE_URL}?id={tweet["id"]}')
        res_err(response, f'liking tweet: {tweet}')

    def __unlike(self, tweet):
        """
        https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/post-favorites-destroy
        """
        response = self.session.post(
            f'{TWEET_UNLIKE_URL}?id={tweet["id"]}')
        res_err(response, f'unliking tweet: {tweet}')

    def __retweet(self, tweet):
        """
        https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/post-statuses-retweet-id
        """
        response = self.session.post(
            RETWEET_URL.format(tweet_id=tweet["id"]))
        res_err(response, f'retweeting: {tweet}')

    def __unretweet(self, tweet):
        """
        https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/post-statuses-unretweet-id
        """
        response = self.session.post(
            REMOVE_RETWEET_URL.format(tweet_id=tweet["id"]))
        res_err(response, f'removing retweet: {tweet}')
