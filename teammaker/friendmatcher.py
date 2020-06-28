import random
from itertools import combinations
from math import log

from .base import Matcher


class FriendMatcher(Matcher):

    NAME = 'friend'

    @staticmethod
    def get_query(room_info, response_id):
        # generate the set of questions for a given response id
        player_n = room_info['players'].index(
            room_info['response_ids'][response_id]
        )
        return ('Put bigger numbers for people you like.',
                'Values will be normalised when they are processed. '
                'Positive integers only. '
                'Invalid inputs are counted as 0.',
                [(str(n), player, 'number')
                 for n, player in enumerate(room_info['players'])
                 if n != player_n])

    @staticmethod
    def read_response(response):
        # we got a response to the query
        res = [0] * 10
        for i in range(10):
            try:
                res[i] = max(0, int(response[str(i)]))
            except (KeyError, ValueError):
                pass
        res = [x / max(1e-5, sum(res)) for x in res]
        return res

    def __init__(self, epsilon=1e-5, strategy='fair'):
        super().__init__()
        self.epsilon = epsilon
        self.strategy = strategy

    def generate_teams(self, prefs):
        strategy_fn = {
            'fair': self.fair_strategy,
            'utilitarian': self.utilitarian_strategy
        }[self.strategy]
        best_happiness = (float('-inf'), float('-inf'))
        optimal_team = None
        for players_t1 in combinations([i for i in range(10)], 5):
            players_t2 = list({i for i in range(10)} - set(players_t1))
            happiness_t1 = 0
            happiness_t2 = 0
            for player in players_t1:
                happiness_t1 += sum(prefs[player][teammate]
                                    for teammate in players_t1)
            for player in players_t2:
                happiness_t2 += sum(prefs[player][teammate]
                                    for teammate in players_t2)
            if (strategy_fn(happiness_t1, happiness_t2) >
                    strategy_fn(*best_happiness)):
                best_happiness = (happiness_t1, happiness_t2)
                optimal_team = (list(players_t1), players_t2)
        return optimal_team, best_happiness

    def fair_strategy(self, happiness_1, happiness_2):
        return (log(max(happiness_1, self.epsilon)) +
                log(max(happiness_2, self.epsilon)) +
                random.random() / 100)

    def utilitarian_strategy(self, happiness_1, happiness_2):
        return happiness_1 + happiness_2 + random.random() / 100
