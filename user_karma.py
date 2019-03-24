#!/usr/bin/env python3

import requests
import time
import os
import sys
import operator
from operator import truediv
import logging
logger = logging.getLogger('bot')
import random

## Functions to count total comments and comment karma for a user in particular
## subreddit


def get_author_comments(**kwargs):
    r = requests.get("https://api.pushshift.io/reddit/comment/search/",params=kwargs)
    data = r.json()
    return data['data']

def get_author_submissions(**swargs):
    r = requests.get("https://api.pushshift.io/reddit/submission/search/",params=swargs)
    data = r.json()
    return data['data']

def get_user_karma(Search_User,Search_Subs_List):
    User_Karma = {}

    c_count = 0
    comments = get_author_comments(author=Search_User,size=1000,sort='desc',sort_type='created_utc')
    for comment in comments:
        commentsub=comment['subreddit'].lower()
        if commentsub in Search_Subs_List:
            if commentsub not in User_Karma:
                User_Karma[commentsub] = {}
                User_Karma[commentsub]['c_karma'] = 0
                User_Karma[commentsub]['c_count'] = 0
                User_Karma[commentsub]['s_karma'] = 0
                User_Karma[commentsub]['s_count'] = 0
            User_Karma[commentsub]['c_karma'] += comment['score']
            User_Karma[commentsub]['c_count'] += 1

    s_count = 0
    submissions = get_author_submissions(author=Search_User,size=1000,sort='desc',sort_type='created_utc')
    for submit in submissions:
        if 'subreddit' in submit:
            submitsub=submit['subreddit'].lower()
            if submitsub in Search_Subs_List:
                if submitsub not in User_Karma:
                    User_Karma[submitsub] = {}
                    User_Karma[submitsub]['c_karma'] = 0
                    User_Karma[submitsub]['c_count'] = 0
                    User_Karma[submitsub]['s_karma'] = 0
                    User_Karma[submitsub]['s_count'] = 0
                User_Karma[submitsub]['s_karma'] += submit['score']
                User_Karma[submitsub]['s_count'] += 1

    return User_Karma


def get_user_summary(User_Karma, SortedSearchSubs):
    # Calculate most active subs
    SubTotals = {}
    CatTotals = {}
    UserTotal = 0
    UserCount = 0

    for sreddit, stype in SortedSearchSubs:
        if sreddit not in User_Karma: 
            continue
        if not stype in CatTotals: CatTotals[stype] = 0
        if not sreddit in SubTotals: SubTotals[sreddit] = 0

        SubKarma = User_Karma[sreddit]['c_karma'] + User_Karma[sreddit]['s_karma']
        SubCount = User_Karma[sreddit]['c_count'] + User_Karma[sreddit]['s_count']
        SubValue = SubKarma + SubCount

        CatTotals[stype] += SubValue
        SubTotals[sreddit] += SubValue
        UserTotal += SubValue
        UserCount += SubCount
        
    if UserCount < 25:
        #return "Sorry, not enough user activity on political subs for analysis, this user probably has a life"
        return "This user does not have enough activty in political subs for analysis or has no clear leanings, they might be one of those weirdo moderate types. I don't trust them."
    
    Sorted_SubTotals = {k: v for k, v in sorted(SubTotals.items(), key=lambda x: x[1])}
    Sorted_CatTotals = {k: v for k, v in sorted(CatTotals.items(), key=lambda x: x[1])}

    if len(list(Sorted_CatTotals.keys())) >= 1:
        TopCat = list(Sorted_CatTotals.keys())[-1]
        TopCat_pct = truediv(Sorted_CatTotals[TopCat], UserTotal) * 100
    else:
        TopCat = ""
        TopCat_pct = 0

    if len(list(Sorted_SubTotals.keys())) >= 1:
        TopSub = list(Sorted_SubTotals.keys())[-1]
    else:
        TopSub = ""

    if len(list(Sorted_SubTotals.keys())) >= 2:
        SecondSub = list(Sorted_SubTotals.keys())[-2]
    else:
        SecondSub= ""


    if TopCat_pct > 75:
        leansword="leans heavy"
    elif TopCat_pct > 50:
        leansword="leans"
    elif TopCat_pct > 30:
        leansword="leans slightly"
    else:
        leansword="undetermined only"

    if TopCat_pct > 25:
        usersummary = "%s (%2.2f%%) %s" % (leansword, TopCat_pct, TopCat)
    else:
        return "This user has no clear leanings, they might be one of those weirdo moderate types. I don't trust them."

    communism_words= [ ', and is possibly a communist', ', and seems to be a communist, be sure to call them comrade', ', and is likely a communist', ', and probably thinks that real communism has not been tried yet', ', and is secretly plotting the communist revolution from their moms basement' , ', and is probably a communist who wears nothing but plain brown pants and shirts' ]
    socialism_words=[ ', and is probably a socialist', ', and might be a socialist, with a Bernie2020 bumper stick on their Prius', ', and is likely a socialist who does not understand why we can\'t all just not work and be happy' ]
    donald_words=   [ ', and most likely has a closet full of MAGA hats' , ', and is a graduate of Trump University' ]
    anarchy_words=  [ ', and they attend antifa protests whenever their mom will give them a ride', ', and they keep their protest gear in their moms minivan' ]
    conservative_words= [ ', and is also conservative so when you agree with them, say mega dittos', ', and might be conservative so they are probably arguing with you while having one hand tied behind their back just to make it fair', ', and is probably a conservative who thinks their talent is on loan from god' ]
    liberal_words = [ ', and they are also a /politics fan, so they probably have MSNBC on in the room right now', ', and they believe that AOC is the greatest thinker in more than 100 years', ', and still has a Hillary2016 sticker on their Prius' ]
    libertarian_words = [ ', and believes gay married couples should be able to protect ther Marijuana plants with fully automatic weapons', ', and wants to take over the world so they can leave you the hell alone', '' , '', '']


    if "communis" in TopSub.lower() or "communis" in SecondSub.lower():
        withword=random.choice(communism_words)
    elif "chapo" in TopSub.lower() or "chapo" in SecondSub.lower():
        withword=random.choice(communism_words)
    elif "socialism" in TopSub.lower() or "socialism" in SecondSub.lower():
        withword=random.choice(socialism_words)
    elif "the_donald" in TopSub.lower() or "the_donald" in SecondSub.lower():
        withword=random.choice(donald_words)
    elif "anarchis" in TopSub.lower() or "anarchis" in SecondSub.lower():
        withword=random.choice(communism_words)
    elif "anarchy" in TopSub.lower() or "anarchy" in SecondSub.lower():
        withword=random.choice(anarchy_words)
    elif "conservative" in TopSub.lower() or "conservative" in SecondSub.lower():
        withword=random.choice(conservative_words)
    elif "politics" in TopSub.lower() or "politics" in SecondSub.lower():
        withword=random.choice(liberal_words)
    elif TopCat_pct > 75 and TopCat == 'libertarian':
        withword=random.choice(libertarian_words)
    else:
        withword=""

    usersummary += withword

    return usersummary
