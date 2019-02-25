#!/usr/bin/env python3

# =============================================================================
# IMPORTS
# =============================================================================
import re
import configparser
import logging
import logging.handlers
import time
import os
import sys
from enum import Enum
import praw
from user_karma import get_user_karma, get_user_summary
import operator
from datetime import datetime 
from dateutil import relativedelta


# =============================================================================
# GLOBALS
# =============================================================================

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
Search_Sub_List = list(config['SearchSubs'].keys())

# Reddit info
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     password=bot_password,
                     user_agent='User Leans Bot by /u/nixfu',
                     username=bot_username)

ENVIRONMENT = config.get("BOT", "environment")
DEV_USER_NAME = config.get("BOT", "dev_user")

RUNNING_FILE = "bot.running"

LOG_LEVEL = logging.INFO
#LOG_LEVEL = logging.DEBUG
LOG_FILENAME = "bot.log"
LOG_FILE_BACKUPCOUNT = 5
LOG_FILE_MAXSIZE = 1024 * 256
FORMAT = '%(levelname)-8s:%(asctime)s - %(message)s'

logger = logging.getLogger('bot')
logger.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter('%(levelname)-8s:%(asctime)s - %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
logger.addHandler(log_stderrHandler)
if LOG_FILENAME:
        log_fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=LOG_FILE_MAXSIZE, backupCount=LOG_FILE_BACKUPCOUNT)
        log_fileHandler.setFormatter(log_formatter)
        logger.addHandler(log_fileHandler)

documentation_link = "https://github.com/userleansbot"

CACHE_REPLIES = []


# =============================================================================
# CLASSES
# =============================================================================
class ParseMessageStatus(Enum):
    SUCCESS = 1
    SYNTAX_ERROR = 2

class CommandType(Enum):
    REPORT_DIRECT = 1
    REPORT_PARENT = 2
    UNKNOWN = 3

class CommandRegex:
    commandsearch = r'^(\/*u*\/*{bot_username})+\s*\/*u*\/*(\w*)\s*$'.format(bot_username=bot_username)
    pm_commandsearch = r'^\/*u*\/*(\w*)\s*$'

# =============================================================================
# FUNCTIONS
# =============================================================================

def send_dev_pm(subject, body):
    """
    sends a PM to the dev's Reddit account
    :param subject: subject of the PM
    :param body: body of the PM
    """
    reddit.redditor(DEV_USER_NAME).message(subject, body)

def get_useraccount_age(user):
    """
    gets the user account age
    """
    userage = "unknown"
    if user:
        created_utc = int(reddit.redditor(user).created_utc)
        created = datetime.fromtimestamp(created_utc)
        now = datetime.now()
        difference = relativedelta.relativedelta(now, created)
        years = difference.years
        months = difference.months
        days = difference.days
        if years > 0:
            userage = "%s years, %s months, %s days ago" % (years, months, days)
        elif months > 0:
            userage = "%s months, %s days ago" % (months, days)
        else:
            userage = "%s days ago" % (days)

        # detect birthday
        if now.month == created.month and now.day == created.day:
            userage += " **TODAY IS CAKEDAY**"

    return userage

def check_mentions():
    """
    go through the comments mentioning the bot process them
    """
    for message in reddit.inbox.unread(limit=None):
        # Mark Read first in case there is an error we don't want to keep trying to process it
        message.mark_read()
        if message.was_comment:
            parent=message.parent()
            if parent.id in CACHE_REPLIES: 
                logger.info("* possible dupe parentid=%s" % parent.id)
            process_mention(message)
        else:
            process_pm(message)


def process_pm(message):
    """
    process the command in the message by determining the command and delegating the processing
    :param message: the Reddit comment containing the command
    """
    pmcommand_match = re.search(CommandRegex.pm_commandsearch, message.body, re.IGNORECASE)

    if pmcommand_match and pmcommand_match.group(1):
        try_send_report(message, pmcommand_match.group(1), message.author.name)
    else:
        logger.info("Sending UNKNOWN COMMAND message to %s" % message.author.name)
        message.reply('UNKNOWN COMMAND!')


def process_mention(mention):
    """
    process the command in the mention by determining the command and delegating the processing
    :param mention: the Reddit comment containing the command
    """
    command_match = re.search(CommandRegex.commandsearch, mention.body, re.IGNORECASE)

    if mention.was_comment:
        parent=mention.parent()
        parentlink=parent.permalink
        itemlink="https://www.reddit.com/%s" % parentlink
    else:
        itemlink=""

    if command_match and command_match.group(2):
        try_send_report(mention, command_match.group(2), mention.author.name)
    elif command_match and command_match.group(1):
        parentcomment = mention.parent()
        if parentcomment and parentcomment.author and mention.author:
            CACHE_REPLIES.append(parentcomment.id)    
            try_send_report(mention, parentcomment.author.name, mention.author.name)

def try_send_report(message, report_user, from_user):
    """
    send report to from_user about report_user
    :param message: the Reddit comment containing the command
    :param report_user: username of the person who will be analyzed
    :param from_user: username of the person who is sending the request
    """


    if message.was_comment:
        parent=message.parent()
        parentlink=parent.permalink
        itemlink="https://www.reddit.com/%s" % parentlink
    else:
        itemlink=""

    # lets not respond to requests about the bot
    if report_user == bot_user:
        logger.info("# Not sending report about myself, requested by %s %s" % (from_user, itemlink))
        return

    logger.info("Sending Report about %s to %s %s" % (report_user, from_user, itemlink))

    User_Karma = get_user_karma(report_user, Search_Sub_List)
    usersummary = get_user_summary(User_Karma,SortedSearchSubs)
    useraccountage = get_useraccount_age(report_user)

    # reply to user
    userreport = "Author: /u/userleansbot\n"
    userreport += "___\n"
    userreport += "Analysis of /u/%s's activity in political subreddits over the past 1000 comments and submissions.\n" % report_user
    userreport += "\n"
    userreport += "Account Created: %s\n" % (useraccountage)
    userreport += "\n"
    userreport += "Summary: **%s**\n" % (usersummary)
    userreport += "\n"
    userreport += " Subreddit|Lean|No. of comments|Total comment karma|No. of posts|Total post karma\n"
    userreport += " :--|:--|:--|:--|:--|:--|:--|:--\n"
    for sreddit, stype in SortedSearchSubs:
        if sreddit in User_Karma: 
            if User_Karma[sreddit]['c_count'] > 0 or User_Karma[sreddit]['s_count'] > 0:
                userreport += "/r/%s|%s|%s|%s|%s|%s\n" % (sreddit, stype, User_Karma[sreddit]['c_count'], User_Karma[sreddit]['c_karma'], User_Karma[sreddit]['s_count'], User_Karma[sreddit]['s_karma'])
    userreport += "\n"

    userreport += "***\n"
    userreport += " ^(Bleep, bloop, I'm a bot trying to help inform political discussions on Reddit.) ^| [^About](https://www.reddit.com/user/userleansbot/comments/au1pva/faq_about_userleansbot/)\n "
    userreport += "___\n"

    message.reply(userreport)
    logger.info("+Sent")


def create_running_file():
    """
    creates a file that exists while the process is running
    """
    running_file = open(RUNNING_FILE, "w")
    running_file.write(str(os.getpid()))
    running_file.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    start_process = False
    logger.info("start")

    if ENVIRONMENT == "DEV" and os.path.isfile(RUNNING_FILE):
        os.remove(RUNNING_FILE)
        logger.info("running file removed")

    if not os.path.isfile(RUNNING_FILE):
        create_running_file()
        start_process = True
    else:
        logger.error("bot already running! Will not start.")

    while start_process and os.path.isfile(RUNNING_FILE):
        logger.debug("Start Main Loop")
        try:
            check_mentions()
            logger.debug("End Main Loop")
        except Exception as err:
            logger.exception("Unknown Exception in Main Loop")
            try:
                send_dev_pm("Unknown Exception in Main Loop", "Error: {exception}".format(exception=str(err)))
            except Exception as err:
                logger.exception("Unknown error sending dev pm")
        time.sleep(10)

    logger.info("end")

    sys.exit()


# =============================================================================
# RUNNER
# =============================================================================

if __name__ == '__main__':
    main()
