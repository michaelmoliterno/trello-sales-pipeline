# std libs
import pprint as pp
from datetime import datetime
from collections import defaultdict
import pytz
from dateutil import parser as dateparser
import numpy as np
import pickle
import operator

# py-trello
from trello import TrelloClient, Board, Card

# custom
import dsa_config
import trello_creds

def card_move_dates(card):
    card.fetch_actions('updateCard:idList')
    res = []
    for idx in card.actions:
        date_str = idx['date']
        dateDate = dateparser.parse(date_str)
        strLst = idx['data']['listBefore']['id']
        endLst = idx['data']['listAfter']['id']
        res.append([strLst, endLst, dateDate])
    res.reverse()
    return res

def get_moves_list_dict(board):
    cards = board.open_cards()
    moves_list_dict = defaultdict(list)
    now = datetime.now()

    for card in cards:
        create_date = datetime.fromtimestamp(int(card.id[:8],16))
        markov_moves_list = card_move_dates(card)

        if len(markov_moves_list) == 0:
            move = (card.list_id,None)
            delta = now-create_date
            moves_list_dict[move].append((card.name,delta.days))
        else:
            prev_move_date = create_date
            last = len(markov_moves_list) - 1
            for i, jank in enumerate(markov_moves_list):
                move = (jank[0],jank[1])
                # this is ugly and I hate timezones
                move_date = jank[2].replace(tzinfo=None)
                delta = move_date - prev_move_date
                moves_list_dict[move].append((card.name,delta.days))

                if i == last:
                    move = (jank[1],None)
                    delta = now - move_date
                    moves_list_dict[move].append((card.name,delta.days))

                prev_move_date = move_date

    return dict(moves_list_dict)

def build_file():
    client = TrelloClient(**trello_creds.CREDS)
    sales_board = client.get_board(dsa_config.SALES_BOARD_ID)
    moves_list_dict = get_moves_list_dict(sales_board)
    pickle.dump(moves_list_dict, open("moves_list_dict.p","wb"))
    pp.pprint(moves_list_dict)

def print_summary(sorted_x):
    for x in sorted_x:
        data = x[1]
        start = data[1]
        end = data[2]
        count = data[0]

        if end == None or count <5:
            continue

        print "{}{} --> {} ({}){}".format("*",start,end,count,"*")
        print "* Median Time to Move:",int(data[3])
        print "* Mean Time to Move:",int(data[4])
        print
        print "Longest Moves:"
        for move in data[5][:5]:
            print "{} {}: {}".format("*",move[0],move[1])
        print "Quickest Moves:"
        bottom_five = data[5][-5:]
        bottom_five.reverse()
        for move in bottom_five:
            print "{} {}: {}".format("*",move[0],move[1])
        print
        print

def get_sorted_x():
    list_ids_to_names = dict((v,k) for k,v in dsa_config.SALES_BOARD_LISTS.iteritems())
    moves_list_dict = pickle.load( open( "moves_list_dict.p", "rb" ) )
    for key, val in moves_list_dict.iteritems():

        days = [x[1] for x in val]

        b = key[0]
        e = key[1]

        if e == None:
            e_name = None

        else:
            try:
                b_name = list_ids_to_names[b]
            except KeyError as e:
                b_name = "UNKNOWN START STATE"

            try:
                e_name = list_ids_to_names[e]
            except KeyError as e:
                e_name = "UNKNOWN END STATE"

        mean = np.mean(days)
        median = np.median(days)

        val.sort(key=operator.itemgetter(1), reverse=True)
        moves_list_dict[key] = [len(val),
                                b_name,
                                e_name,
                                mean,
                                median,
                                val
                                ]

    sorted_x = sorted(moves_list_dict.items(), key=operator.itemgetter(1), reverse=True)
    return sorted_x

if __name__ == "__main__":

    #only need to build once
    #build_file()

    sorted_x = get_sorted_x()


    moves = defaultdict(list)

    for x in sorted_x:

        origin_id = x[0][0]

        if origin_id in ['541c34c0319d17548a1a7e32',  # Nope! list
                         '544fd93e4bc071954de3c4ac',  # Finished
                         '56f3583bab9ddc21cdf6d2e5',  # INBOX
                         '541c3a03ba820e017046fa5a']: # UNKNOWN
            continue

        dest_id = x[0][1]

        if dest_id in [None,]: #Current cards
            continue

        data = x[1]
        count = data[0]
        mean = int(data[3])
        median = int(data[4])

        key = data[1]
        val = {"destination":x[0][1],
               "count":count,
               "median":median,
               "mean":mean,
               "origin":data[1],
               "dest":data[2],
               "dest_id":dest_id,
               "origin_id":origin_id
               }

        moves[key].append(val)

    moves = dict(moves)

    for key, val in moves.iteritems():
        counter = 0

        for v in val:
            counter += v['count']

        for i, v in enumerate(val):
            v['p'] = '{0:.3g}'.format(float(v['count'])/counter)
            v['total_count'] = counter
            val[i] = v

        moves[key] = val

    for key, val in moves.iteritems():
        #print "{}{} --> {} ({}){}".format("*",start,end,count,"*")
        print "{}Origin: {} ({} total){}".format("*",key,val[0]["total_count"],"*")
        for v in val:
            print "{} {}: {}".format("*",v["dest"], v["p"])
            print "    {} mean: {} days".format("*",v["mean"])
            print "    {} median: {} days".format("*",v["mean"])
        print








    #print_summary(sorted_x)
