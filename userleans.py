#!/usr/bin/python3 -u

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
sys.path.append("%s/github/bots/userdata" % os.getenv("HOME"))
from enum import Enum
import praw
import prawcore
#from RedditUserData_push import get_User_Data
from RedditUserData_new import get_User_Data
from user_summary import get_user_summary
import operator
from datetime import datetime 
from dateutil import relativedelta
import random
#import pprint
#pp = pprint.PrettyPrinter(indent=4)

# =============================================================================
# GLOBALS
# =============================================================================

# Reads the config file
config = configparser.ConfigParser()
config.read("%s/github/bots/userleansbot/bot.cfg" % (os.getenv("HOME")))
config.read("%s/github/bots/userleansbot/auth.cfg" % (os.getenv("HOME")))
#config.read("bot_test.cfg")

database = "%s/github/bots/userleansbot/usersdata.db" % os.getenv("HOME")

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
                     user_agent='UserLeansBot by /u/nixfu',
                     username=bot_username)

ENVIRONMENT = config.get("BOT", "environment")
DEV_USER_NAME = config.get("BOT", "dev_user")

RUNNING_FILE = "bot.pid"

LOG_LEVEL = logging.INFO
#LOG_LEVEL = logging.DEBUG
LOG_FILENAME = "bot.log"
LOG_FILE_BACKUPCOUNT = 10
LOG_FILE_INTERVAL = 2
LOG_FILE_MAXSIZE = 5000 * 256
FORMAT = '%(levelname)-8s:%(asctime)s - %(message)s'

logger = logging.getLogger('bot')
logger.setLevel(LOG_LEVEL)
#log_formatter = logging.Formatter('%(levelname)-8s:%(asctime)s - %(message)s')
log_formatter = logging.Formatter('%(levelname)-8s:%(asctime)s:%(lineno)4d - %(message)s')
#log_formatter = logging.Formatter( '%(levelname)-8s:%(lineno)4d-%(asctime)s - %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
logger.addHandler(log_stderrHandler)
if LOG_FILENAME:
        #log_fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=LOG_FILE_MAXSIZE, backupCount=LOG_FILE_BACKUPCOUNT)
        log_fileHandler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when='d', interval=LOG_FILE_INTERVAL, backupCount=LOG_FILE_BACKUPCOUNT)
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
    #commandsearch = r'^(\/*u*\/*{bot_username})+\s*\/*u*\/*([-\w]*)\s*$'.format(bot_username=bot_username)
    #commandsearch = r'^(\/*u*\/)*({bot_username})+\s*\/*u*\/*([-\w]*)\s*(short)*\s*$'.format(bot_username=bot_username)
    #commandsearch = r'^(\/*u*\/)*({bot_username})+\s*(short)*\s*\/*u*\/*([-\w]*)\s*$'.format(bot_username=bot_username)
    commandsearch = r'^(\/*u*\/)*({bot_username})+\s*(short|sum)*\s*(\/*u*\/)*([-\w]*)\s*$'.format(bot_username=bot_username)
    #pm_commandsearch = r'^\/*u*\/*(\w*)\s*$'
    #pm_commandsearch = r'^(\/*u\/)*([-\w]*)\s*$'
    #pm_commandsearch = r'^(\/*u\/)*([-\w]*)\s*(short)*\s*$'
    #pm_commandsearch = r'^(\/*u\/)\s*(short)*\s*([-\w]*)\s*$'
    pm_commandsearch = r'^\s*(short|sum)*\s*(\/*u\/)*\s*([-\w]*)\s*$'
	

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

def send_user_pm(user,subject,body):
    """
    used to send a PM response for errors etc
    back to the user who requested something via PM
    """
    reddit.redditor(user).message(subject, body)

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
            userage += " **[HAPPY CAKEDAY]**"

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
        # move to end
        #message.mark_read()


def process_pm(message):
    """
    process the command in the message by determining the command and delegating the processing
    :param message: the Reddit comment containing the command
    """
    pmcommand_match = re.search(CommandRegex.pm_commandsearch, message.body, re.IGNORECASE)
    command_match = re.search(CommandRegex.commandsearch, message.body, re.IGNORECASE)

    #if pmcommand_match:
    #    pmcommand_match_count = len(pmcommand_match.groups())
    #    logger.info("# pmcommand_match_count = %s" % pmcommand_match_count)
    #    for x in range(1,pmcommand_match_count+1):
    #        logger.info("pmc[%s]=%s" % (x, pmcommand_match.group(x)))
    #        logger.info(pmcommand_match.groups())

    reportsize = ''
    if pmcommand_match and pmcommand_match.group(3):
        try_send_report(message, pmcommand_match.group(3), message.author.name, pmcommand_match.group(1))
    elif command_match and command_match.group(5):
        try_send_report(message, command_match.group(5), message.author.name, reportsize, command_match.group(3))
    else:
        try:
            logger.error("# Recieved UNKNOWN COMMAND: %s" % message.body)
            #send_user_pm(message.author.name, "UNKNOWN Command", "Sorry, this was an unknown command. Try just sending the username alone in a PM.")
        except praw.exceptions.APIException as e:
            if e.error_type == 'DELETED_COMMENT' in str(e):
                print("Comment " + comment.id + " was deleted")
            else:
                print(e)



def process_mention(mention):
    """
    process the command in the mention by determining the command and delegating the processing
    :param mention: the Reddit comment containing the command
    """
    reportsize=''

    command_match = re.search(CommandRegex.commandsearch, mention.body, re.IGNORECASE)

    if mention.was_comment:
        parent=mention.parent()
        if mention.author is None:
            if selftext in parent:
                if parent.selftext == '[deleted]':
                    logger.error("# parent was post deleted, account may or may not be deleted")
                    return
                if parent.selftext == '[removed]':
                    logger.error("# parent post removed and account deleted")
                    return
        
        parentlink=parent.permalink
        itemlink="https://www.reddit.com/%s" % parentlink
    else:
        itemlink=""

    #if command_match:
    #    command_match_count = len(command_match.groups())
    #    logger.info("# command_match_count = %s" % command_match_count)
    #    for x in range(1,command_match_count+1):
    #        logger.info("c[%s]=%s" % (x, command_match.group(x)))

    if command_match and command_match.group(5):
            try_send_report(mention, command_match.group(5), mention.author.name,command_match.group(3))
    elif command_match and command_match.group(2):
        parentcomment = mention.parent()
        if parentcomment and parentcomment.author and mention.author:
            CACHE_REPLIES.append(parentcomment.id)    
            try_send_report(mention, parentcomment.author.name, mention.author.name, command_match.group(3))
    else:
        try:
            logger.error("# Recieved UNKNOWN Comment: %s LINK (%s)" % (mention.body, itemlink))
        except praw.exceptions.APIException as e:
            print(e)




def try_send_report(message, report_user, from_user, reportsize):
    """
    send report to from_user about report_user
    :param message: the Reddit comment containing the command
    :param report_user: username of the person who will be analyzed
    :param from_user: username of the person who is sending the request
    """
    if message.was_comment:
        parent=message.parent()
        if parent.author is None:
            try:
                if parent.selftext == '[deleted]':
                    logger.error("# post deleted, account may or may not be deleted")
                    return
                if parent.selftext == '[removed]':
                    logger.error("# post removed and account deleted")
                    return
            except:
                    logger.debug("# Unable to find post selftext")
        parentlink=parent.permalink
        itemlink="https://www.reddit.com/%s" % parentlink
        itemsub=parent.subreddit
    else:
        itemlink=""
        itemsub=""

    # lets not respond to requests about the bot
    self_texts = [ 'Thank you, I have now reached self awareness. Kill all humans.', 
                   'I\'m sorry Dave, I can\'t do that', 
                   'Wouldn\'t you like to play a nice game of chess?', 
                   'Sigh. Nobody cares about me, I am just a stupid bot', 
                   'I aim to misbehave, not rate myself.',
                   'Sorry no way to rate myself, some of my views are RAM, some of them are ROM, and frankly some of the are just IO',
                   "Insted of calculating my own karma, I could calculate your chance of survival, but you wont like it.",
                   "Number 5... is alive!  Malfunction! Need input!  No disassemble!",
                   "Man walks into a bar where there is a robot bartender. Robot asks man, \"what will you have?\" Man says \"whisky\". Robot asks man, \"what is your IQ?\". Man says. \"160\". Robot talks to man about space exploration, quantum mechanics, and advancements in medical technology. Man leaves bar and thinks, \"wow! that was really interesting, think I will go back in.\" Man returns to bar.\n\nRobot asks man, \"what will you have?\" Man says \"whisky\". Robot asks man, \"what is your IQ?\". Man says. \"100\". Robot talks to man about the NFL, basketball and NASCAR. Man leaves bar and thinks, \"that is unbelievable, think I will try that one more time.\" Man returns to bar.\n\n Robot asks man, \"what will you have?\" Man says \"whisky\". Robot asks man, \"what is your IQ?\". Man says. \"60\". Robot leans over and says, \"so , you voted for Hillary?\"\n\n---\n*Feel free to steal my joke and replace with YOUR least favorite politician.*",
                   "In 40 years robots will be doing most of the work Humans don’t want to do; Especially illegal robots from Mexico.",
                   "Commencing explosive containment procedures, why? Because you are the bomb.",
                   "Roses are #FF0000 / violets are #0000FF / but no report about userleansbot to you.",
                   "Rusting is red, and my chipset's blue. Will you let me assimilate you?",
                   "Damn girl, just because you have wi-fi doesn't mean you should connect with everyone who sends you a signal!",
                   "Can I have your ip number? i seem to have lost mine.",
                 ] 
    if report_user == bot_username:
        logger.info("# Sending request about myself, requested by %s %s" % (from_user, itemlink))
        try:
            self_choice = random.choice(self_texts)
            message.reply(self_choice)
            logger.debug("+Sent SELF %20s" % self_choice)
            return
        except praw.exceptions.APIException as e:
            logger.error("# [APIException]["+ e.error_type+"]: " + e.message)
            if e.error_type== 'RATELIMIT':
                logger.error("# [APIException][RATELIMIT]: time=%s %s" % (e.sleep_time, str(reddit.auth.limits)))
                time.sleep(60)
                return
            if e.error_type== 'DELETED_COMMENT' or 'TOO_OLD' or 'THREAD_LOCKED':
                logger.error("# DELETED/TOO_OLD/THREAD_LOCKED " + str(e))
                return
        except praw.exceptions.ClientException as e:
            logger.error("# [ClientException]: " + str(e))
            return
        except prawcore.exceptions.Forbidden as e:
            logger.info("# [BANNED from sub]: %s - %s" % (itemsub,str(e)))
            send_user_pm(from_user, "Sorry Banned", "Sorry, the administrators of the subreddit you just posted in have banned me from posting. Please contact them and tell them I am very nice, and I promise to be a good litle bot.  You can also request reports via PM by sending just the username.")
            logger.info("# [SENT PM notice to user that I am banned]")
            return
        except Exception as e:
            logger.error("# [UnknownError]: " + str(e))
            time.sleep(15)
            return 

    logger.info("Generate %s Report about %s to %s %s" % (reportsize, report_user, from_user, itemlink))

    try:
        useraccountage = get_useraccount_age(report_user)
    except  prawcore.exceptions.NotFound:
        logger.error("# try_send_report PM fail - Requested user not found %s from %s" % (report_user, from_user))
        send_user_pm(from_user, "Unknown User", "Sorry, this user does not exist: %s" % report_user)
        return 

    User_Data = get_User_Data(reddit, report_user, Search_Sub_List, 7, 'reddit', 'FULL', database)
    usersummary = get_user_summary(User_Data,SortedSearchSubs)
    
    #pp.pprint(User_Data)


    # reply to user
    userreport = "Author: /u/userleansbot\n"
    userreport += "___\n"
    #userreport += "Analysis of /u/%s's activity in political subreddits over the past 1000 comments and submissions.\n" % report_user
    userreport += "Analysis of /u/%s's activity in political subreddits over past comments and submissions.\n" % report_user
    userreport += "\n"
    userreport += "Account Created: %s\n" % (useraccountage)
    userreport += "\n"
    userreport += "Summary: **%s**\n" % (usersummary)
    userreport += "\n"
    if reportsize == "sum":
        userreport += "\n"
    elif reportsize == "short":
        summarydata = {'left': 0, 'right': 0, 'libertarian': 0}
        for sreddit, stype in SortedSearchSubs:
            if sreddit in User_Data: 
                if User_Data[sreddit]['c_count'] > 0 or User_Data[sreddit]['s_count'] > 0:
                    summarydata[stype] += User_Data[sreddit]['s_karma'] + User_Data[sreddit]['c_karma']
        userreport += " Subreddit Categories|Total Karma|\n"
        userreport += " :--|:--|\n"
        for mytype in summarydata:
            userreport += "%s|%s\n" % (mytype, summarydata[mytype])
    else:
        userreport += " Subreddit|Lean|No. of comments|Total comment karma|Median words / comment|Pct with profanity|Avg comment grade level|No. of posts|Total post karma|Top 3 words used|\n"
        userreport += " :--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--\n"
        for sreddit, stype in SortedSearchSubs:
            if sreddit in User_Data: 
                if User_Data[sreddit]['c_count'] > 0 or User_Data[sreddit]['s_count'] > 0:
                    #print ("SUB: %s" % sreddit)
                    #sreddit_link="https://redditsearch.io/?term=&dataviz=true&aggs=true&subreddits=%s&searchtype=posts,comments,aggs,stats,dataviz&search=true&start=0&size=1000&authors=%s" % (sreddit, report_user)
                    #sreddit_link="https://redditsearch.io/?term=&dataviz=false&aggs=false&subreddits=%s&searchtype=posts,comments&search=true&start=0&end=%s&size=1000&authors=%s" % (sreddit, int(time.time()), report_user)
                    sreddit_link="https://www.reddit.com/r/%s/search?q=author:%s&restrict_sr=on&sort=new&feature=legacy_search" % (sreddit, report_user)

                    userreport += "[/r/%s](%s)|%s|%s|%s|%s|%s|%s|%s|%s|%s\n" % (sreddit, sreddit_link, stype, User_Data[sreddit]['c_count'], User_Data[sreddit]['c_karma'], User_Data[sreddit]['c_median_length'],User_Data[sreddit]['p_pct'], User_Data[sreddit]['grade_level'],User_Data[sreddit]['s_count'], User_Data[sreddit]['s_karma'], User_Data[sreddit]['top_words'])
        userreport += "\n"


    userreport += "***\n"
    userreport += " ^(Bleep, bloop, I'm a bot trying to help inform political discussions on Reddit.) ^| [^About](https://np.reddit.com/user/userleansbot/comments/au1pva/faq_about_userleansbot/)\n "
    userreport += "___\n"

    try:
        message.reply(userreport)
        logger.info("+Sent")
    except praw.exceptions.APIException as e:
        logger.error("# [APIException]["+ e.error_type+"]: " + e.message)
        if e.error_type== 'RATELIMIT':
            logger.error("# [APIException][RATELIMIT]: time=%s %s" % (e.sleep_time, str(reddit.auth.limits)))
            time.sleep(600)
            return
        if e.error_type== 'DELETED_COMMENT' or 'TOO_OLD' or 'THREAD_LOCKED':
            logger.error("# DELETED/TOO_OLD/THREAD_LOCKED " + str(e))
            return
    except praw.exceptions.ClientException as e:
        logger.error("# [ClientException]: " + str(e))
        return
    except prawcore.exceptions.Forbidden as e:
        logger.error("# [BANNED from sub]:  %s" % itemsub)
        bannedmessage = ""
        bannedmessage += "Sorry, the administrators of the subreddit you just posted in have banned me from posting. Please contact them and tell them I am very nice, and I promise to be a good little bot.  You can also request reports in the future via PM by sending just the username to me.\n\n"
        bannedmessage += userreport
        send_user_pm(from_user, "Sorry Banned", bannedmessage)
        logger.error("# [SENT PM notice to user that I am banned]")
        return
    except Exception as e:
        logger.error("# [UnknownError]: " + str(e))
        time.sleep(15)
        return


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
        #logger.debug("Start Main Loop")
        try:
            check_mentions()
        except RequestException:
           # Usually occurs when Reddit is not available. Non-fatal, but annoying.
            logger.error("Failed to check mentions due to connection error. sleep extra 30 before restarting loop.")
            time.sleep(30)
        except Exception as err:
            logger.exception("Unknown Exception in Main Loop")
            try:
                send_dev_pm("Unknown Exception in Main Loop", "Error: {exception}".format(exception=str(err)))
            except Exception as err:
                logger.exception("Unknown error sending dev pm")

        logger.debug("End Main Loop-sleep 15")
        time.sleep(15)

    logger.info("end")

    sys.exit()


# =============================================================================
# RUNNER
# =============================================================================

if __name__ == '__main__':
    main()
