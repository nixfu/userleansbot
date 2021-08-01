#!/usr/bin/python3 -u

import re
import logging
import time
import os
import sys
sys.path.append("%s/github/bots/userdata" % os.getenv("HOME"))
from enum import Enum
import praw
from RedditUserData_push import get_User_Data
from user_summary import get_user_summary

import operator
import configparser
import pprint
pp = pprint.PrettyPrinter(indent=4)

#LOG_LEVEL = logging.INFO
LOG_LEVEL = logging.DEBUG
logger = logging.getLogger('bot')
logger.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter('%(levelname)-8s:%(asctime)s - %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
logger.addHandler(log_stderrHandler)

# Reads the config file
config = configparser.ConfigParser()
config.read("%s/github/bots/userleansbot/bot.cfg" % os.getenv("HOME"))
config.read("%s/github/bots/userleansbot/auth.cfg" % os.getenv("HOME"))

bot_username = config.get("Reddit", "username")
bot_password = config.get("Reddit", "password")
client_id = config.get("Reddit", "client_id")
client_secret = config.get("Reddit", "client_secret")

SortedSearchSubs = sorted(config['SearchSubs'].items(), key=operator.itemgetter(1))
SubCategories = []
for x,y in SortedSearchSubs:
        if y not in SubCategories: SubCategories.append(y)
        Search_Sub_List = list(config['SearchSubs'].keys())


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
User_Karma = get_User_Data(reddit,user,Search_Sub_List)

User_Summary = get_user_summary(User_Karma,SortedSearchSubs)
pp.pprint(User_Karma)

print ("------------------------------")
pp.pprint(User_Summary)
