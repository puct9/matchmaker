from itertools import combinations
from math import log

from .base import Matcher


class FriendMatcher(Matcher):

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
                log(max(happiness_2, self.epsilon)))

    def utilitarian_strategy(self, happiness_1, happiness_2):
        return happiness_1 + happiness_2
