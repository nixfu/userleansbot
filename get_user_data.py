#!/usr/bin/env python

import re
import configparser
import logging
import time
import os
import sys
from enum import Enum
import praw
from user_karma import get_user_karma, get_user_summary
import operator
from bot import get_useraccount_age


# Reads the config file
config = configparser.ConfigParser()
config.read("bot.cfg")

bot_username = config.get("Reddit", "username")
bot_password = config.get("Reddit", "password")
client_id = config.get("Reddit", "client_id")
client_secret = config.get("Reddit", "client_secret")

SortedSearchSubs = sorted(config['SearchSubs'].items(), key=operator.itemgetter(1))

SubCategories = []
for x,y in SortedSearchSubs:
    if y not in SubCategories: SubCategories.append(y)
Search_Sub_List = config['SearchSubs'].keys()

# Reddit info
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     password=bot_password,
                     user_agent='User Leans Bot',
                     username=bot_username)

ENVIRONMENT = config.get("BOT", "environment")
DEV_USER_NAME = config.get("BOT", "dev_user")

user=sys.argv[1]

print ("Checking User=%s" % user)

# TEST FUNCTION
User_Karma = {}
User_Karma = get_user_karma(user,Search_Sub_List)

usersummary = get_user_summary(User_Karma, SortedSearchSubs)
useraccountage = get_useraccount_age(user)

print (User_Karma)
print (usersummary)

print (useraccountage)
