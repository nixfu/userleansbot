#!/usr/bin/env python3

import requests
import time
import os
import sys
import operator
from operator import truediv
import logging
logger = logging.getLogger('bot')

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
        return "not enough data"

    Sorted_SubTotals = {k: v for k, v in sorted(SubTotals.items(), key=lambda x: x[1])}
    Sorted_CatTotals = {k: v for k, v in sorted(CatTotals.items(), key=lambda x: x[1])}

    TopCat = list(Sorted_CatTotals.keys())[-1]
    TopSub = list(Sorted_SubTotals.keys())[-1]
    SecondSub = list(Sorted_SubTotals.keys())[-2]
    TopCat_pct = truediv(Sorted_CatTotals[TopCat], UserTotal) * 100
        

    if TopCat_pct > 75:
        leansword="leans heavy"
    elif TopCat_pct > 60:
        leansword="leans"
    else:
        leansword="leans slightly"
    usersummary = "%s (%2.2f%%) %s" % (leansword, TopCat_pct, TopCat)

    if "communis" in TopSub.lower() or "communis" in SecondSub.lower():
        #withword=" and is probably a communist who calls everyone comrade"
        withword=" and is possibly a communist"
    elif "chapo" in TopSub.lower() or "chapo" in SecondSub.lower():
        withword=" and is possibly a communist"
    elif "socialist" in TopSub.lower() or "socialist" in SecondSub.lower():
        withword=" and is possibly a socialist, and has a Bernie2020 bumper sticker"
    elif "the_donald" in TopSub.lower() or "the_donald" in SecondSub.lower():
        withword=" and probably has a closet full of MAGA hats"
    else:
        withword=""

    usersummary += withword

    return usersummary
