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

def get_user_summary(User_Data, SortedSearchSubs):
    # Calculate most active subs
    SubTotals = {}
    CatTotals = {}
    UserTotal = 0
    UserCount = 0

    for sreddit, stype in SortedSearchSubs:
        if sreddit not in User_Data: 
            continue

        if not stype in CatTotals: CatTotals[stype] = 0
        if not sreddit in SubTotals: SubTotals[sreddit] = 0

        if 'c_karma' in User_Data[sreddit]:
            SubKarma = User_Data[sreddit]['c_karma'] + User_Data[sreddit]['s_karma']
        else:
            continue
    
        if 'c_count' in User_Data[sreddit]:
            SubCount = User_Data[sreddit]['c_count'] + User_Data[sreddit]['s_count']
        else:
            continue

        # counts weight 1x  karma
        SubValue = SubKarma
        SubTotals[sreddit] += SubValue

        if SubValue > 0:
            CatTotals[stype] += SubValue
            UserTotal += SubValue

        UserCount += SubCount
        

    if UserCount < 20:
        #return "Sorry, not enough user activity on political subs for analysis, this user probably has a life"
        return "This user does not have enough activity in political subs for analysis or has no clear leanings, they might be one of those weirdo moderate types. I don't trust them."
    
    Sorted_SubTotals = {k: v for k, v in sorted(SubTotals.items(), key=lambda x: x[1])}
    Sorted_CatTotals = {k: v for k, v in sorted(CatTotals.items(), key=lambda x: x[1])}

    if len(list(Sorted_CatTotals.keys())) >= 1:
        TopCat = list(Sorted_CatTotals.keys())[-1]
        if UserTotal > 0:
            TopCat_pct = truediv(Sorted_CatTotals[TopCat], UserTotal) * 100
        else:
            TopCat_pct = 0
    else:
        TopCat = ""
        TopCat_pct = 0

    if len(list(Sorted_SubTotals.keys())) >= 1:
        TopSub = list(Sorted_SubTotals.keys())[-1]
        if SubTotals[TopSub] < 25:
            TopSub = ""
    else:
        TopSub = ""

    if len(list(Sorted_SubTotals.keys())) >= 2:
        SecondSub = list(Sorted_SubTotals.keys())[-2]
        if SubTotals[SecondSub] < 25:
            SecondSub = ""
    else:
        SecondSub= ""

    print("Top Cat: %s pct=%s TopSub: %s SecondSub:%s" % (TopCat, TopCat_pct, TopSub, SecondSub))

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
    donald_words=   [ ', and most likely has a closet full of MAGA hats' , ', and is probably a graduate of Trump University' ]
    anarchy_words=  [ ', and they attend antifa protests whenever their mom will give them a ride', ', and they keep their protest gear in their moms minivan' ]
    conservative_words= [ ', and is likely also conservative so when you agree with them, say mega dittos', ', and might be conservative so they are probably arguing with you while having one hand tied behind their back just to make it fair', ', and is probably a conservative who thinks their talent is on loan from god', ', and probably joined Paul Ryan\'s gym to hang out with him', ', and enjoys tea parties with Ann Coulter', ', and tunes into turning point USA and Prager U to learn the real truth' ]
    liberal_words = [ ', and they are also a /politics fan, so they probably have MSNBC on in the room right now', ', and they might believe that AOC is the greatest thinker in more than 100 years', ', and still has a Hillary2016 sticker on their Prius' ]
    libertarian_words = [ ', and believes gay married couples should be able to protect ther Marijuana plants with fully automatic weapons', ', and wants to take over the world so they can leave you the hell alone', 'Voted for Gary Johnson while complaining that Gary Johnson isn\'t actually a libertarian', 'Would happily wash Ron Paul\'s car for free', 'Wouldn\'t dream of a aggressing upon you unless you aggressed upon them first', 'Just wants you to admit that taxation IS theft'. '' , '', '']

    if "communis" in TopSub.lower() or "communis" in SecondSub.lower():
        withword=random.choice(communism_words)
    elif "chapo" in TopSub.lower() or "chapo" in SecondSub.lower():
        withword=random.choice(communism_words)
    elif "socialism" in TopSub.lower() or "socialism" in SecondSub.lower():
        withword=random.choice(socialism_words)
    elif "the_donald" == TopSub.lower() or "the_donald" == SecondSub.lower():
        withword=random.choice(donald_words)
    elif "anarchis" in TopSub.lower() or "anarchis" in SecondSub.lower():
        withword=random.choice(communism_words)
    elif "anarchy" in TopSub.lower() or "anarchy" in SecondSub.lower():
        withword=random.choice(anarchy_words)
    elif "conservative" in TopSub.lower() or "conservative" in SecondSub.lower():
        withword=random.choice(conservative_words)
    elif "politics" == TopSub.lower() or "politics" == SecondSub.lower():
        withword=random.choice(liberal_words)
    elif TopCat_pct > 75 and TopCat == 'libertarian':
        withword=random.choice(libertarian_words)
    else:
        withword=""

    usersummary += withword

    return usersummary
