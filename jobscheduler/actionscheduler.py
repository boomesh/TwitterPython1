"""
encapsulates scheduling related to actions
"""
import time
import schedule

from tweet.tweetservice import TweetService
from users.friendshipservice import FriendshipService


class ActionScheduler:  # pylint: disable=too-few-public-methods
    """
    schedules twitter actions
    """

    def __init__(self, session):
        self.tweetservice = TweetService(session)
        self.friendshipservice = FriendshipService(session)

    def __create(self):
        """
        talks to friendship service to make new friends
        """
        self.friendshipservice.create()

    def __purge(self):
        """
        talks to friendship service to remove friends who have not
        followed back
        """
        self.friendshipservice.purge()

    def __tweet(self):
        """
        talks to tweet service tp issue a brand new tweet
        """
        self.tweetservice.tweet()

    def execute(self):
        """
        starts the scheduler.  Here's the schedule:

        c = create
        p = purge
        t = tweet

        SCHEDULE
        S M T W Th F S
        c p c   c    c
        c   c   c    c
        c p c p c  p c
        t t t t t  t t

        Using this scheduler:
        https://schedule.readthedocs.io/en/stable/
        """
        # schedule the friendships (100 friends max a day, 3 times a day)
        schedule.every().sunday.at("09:00").do(self.__create)
        schedule.every().sunday.at("15:00").do(self.__create)
        schedule.every().sunday.at("21:00").do(self.__create)

        schedule.every().tuesday.at("09:00").do(self.__create)
        schedule.every().tuesday.at("15:00").do(self.__create)
        schedule.every().tuesday.at("21:00").do(self.__create)

        schedule.every().thursday.at("09:00").do(self.__create)
        schedule.every().thursday.at("15:00").do(self.__create)
        schedule.every().thursday.at("21:00").do(self.__create)

        schedule.every().saturday.at("09:00").do(self.__create)
        schedule.every().saturday.at("15:00").do(self.__create)
        schedule.every().saturday.at("21:00").do(self.__create)

        # schedule purge friends (600 removals max, at 10PM)
        schedule.every().monday.at("02:00").do(self.__purge)
        schedule.every().monday.at("22:00").do(self.__purge)
        schedule.every().wednesday.at("22:00").do(self.__purge)
        schedule.every().friday.at("22:00").do(self.__purge)

        # schedule to post a tweet once a day (every day at 1PM)
        schedule.every().day.at("13:00").do(self.__tweet)

        while True:
            schedule.run_pending()
            time.sleep(50)
