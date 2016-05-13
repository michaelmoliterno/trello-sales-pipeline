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

# card = client.get_card('jjU0nqPK')
#
# print card.name
# create_date = datetime.fromtimestamp(int(card.id[:8],16))
# print create_date
#
# markov_moves_list = card.listCardMove_date()
# markov_moves_list.reverse()
#
# prev_move_date = create_date
# for jank in markov_moves_list:
#     move_date = jank[2].replace(tzinfo=None)
#     diff = move_date - prev_move_date
#     print (jank[0],jank[1]), jank[2], diff.days
#     prev_move_date = move_date

def get_moves_list_dict(board):
    cards = board.open_cards()
    moves_list_dict = defaultdict(list)
    now = datetime.now()

    for card in cards:

        # skip cards that are in dummy boards
        # if card.list_id in dsa_config.SALES_LISTS_TO_EXCLUDE:
        #     continue

        create_date = datetime.fromtimestamp(int(card.id[:8],16))

        markov_moves_list = card_move_dates(card)

        print card.name

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

#build_file()
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

# key = ('541c347213f6fb8df8bde205', '541c34b9702db91fe752682f')
# print dict(list_moves)[key]
# print len(dict(list_moves)[key])
#
# listy = dict(list_moves)[key]
# sorted_by_second = sorted(listy, key=lambda tup: tup[1], reverse=True)
# pp.pprint(sorted_by_second)
