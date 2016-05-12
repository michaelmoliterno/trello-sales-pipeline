# std libs
import pprint as pp
from datetime import datetime
from collections import defaultdict
import pytz
from dateutil import parser as dateparser
import numpy as np

# py-trello
from trello import TrelloClient, Board, Card

# custom
import dsa_config
import trello_creds

list_ids_to_names = dict((v,k) for k,v in dsa_config.SALES_BOARD_LISTS.iteritems())

client = TrelloClient(**trello_creds.CREDS)


def listCardMove_dates(card):
    """
        Will return the history of transitions of a card from one list to another
        The lower the index the more resent the historical item

        It returns a list of lists. The sublists are triplates of
        starting list, ending list and when the transition occured.
    """
    card.fetch_actions('updateCard:idList')
    res = []
    for idx in card.actions:
        date_str = idx['date']
        dateDate = dateparser.parse(date_str)
        strLst = idx['data']['listBefore']['id']
        endLst = idx['data']['listAfter']['id']
        res.append([strLst, endLst, dateDate])
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


# this is the Trello sales pipeline, gets all the cards
sales_board = client.get_board(dsa_config.SALES_BOARD_ID)
cards = sales_board.open_cards()

list_moves = defaultdict(list)

now = datetime.now()

for card in cards:

    # skip cards that are in dummy boards
    if card.list_id in dsa_config.SALES_LISTS_TO_EXCLUDE:
        continue

    create_date = datetime.fromtimestamp(int(card.id[:8],16))

    markov_moves_list = listCardMove_dates(card)
    markov_moves_list.reverse()

    if len(markov_moves_list) == 0:
        move = (card.list_id,None)
        delta = now-create_date
        list_moves[move].append(delta.days)
    else:
        print card.name
        prev_move_date = create_date
        for jank in markov_moves_list:
            move = (jank[0],jank[1])

            move_date = jank[2].replace(tzinfo=None)
            diff = move_date - prev_move_date

            list_moves[move].append(diff.days)

            prev_move_date = move_date

key = ('541c347213f6fb8df8bde205', '541c34b9702db91fe752682f')
print dict(list_moves)[key]
print len(dict(list_moves)[key])
print np.median(dict(list_moves)[key])
print np.mean(dict(list_moves)[key])
