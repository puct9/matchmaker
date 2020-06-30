import random
from itertools import combinations, permutations
from math import log

from .base import Matcher


class RoleMatcher(Matcher):

    NAME = 'role'

    @staticmethod
    def get_query(room_info, response_id):
        return ('How confident are you in each role?',
                'Answer as a value from 0 to 10. '
                'Invalid or blank answers will default to 0.',
                [
                    ('top', 'Top lane', 'number'),
                    ('jg', 'Jungle', 'number'),
                    ('mid', 'Mid lane', 'number'),
                    ('adc', 'AD Carry', 'number'),
                    ('sup', 'Support', 'number')
                ])

    @staticmethod
    def read_response(response):
        roles = ['top', 'jg', 'mid', 'adc', 'sup']
        return [min(max(response.get(role, 0), 0), 10) for role in roles]

    def __init__(self, epsilon=1e-5, strategy='fair'):
        super().__init__()
        self.epsilon = epsilon
        self.strategy = strategy

    def generate_teams(self, prefs):
        strategy_fn = {
            'fair': self.fair_logsum_strategy
        }[self.strategy]
        best_happiness = float('-inf')
        # we start with a random assortment of the two teams
        team1 = random.sample([i for i in range(10)], k=5)
        team2 = list({i for i in range(10)} - set(team1))
        random.shuffle(team2)
        # then we make changes to the teams and see
        # if some changes result in improvements to the teams
        happiness_1 = [prefs[p][i] for i, p in enumerate(team1)]
        happiness_2 = [prefs[p][i] for i, p in enumerate(team2)]
        best_score = strategy_fn(happiness_1, happiness_2)
        best_teams = (team1, team2)
        suggestions = self.dfs_greedy_search(team1, team2,
            best_score, strategy_fn, prefs, max_search=20
        )
        for suggest_t1, suggest_t2, score in suggestions:
            if score <= best_score:
                continue
            best_score = score
            best_teams = (suggest_t1, suggest_t2)
        print(best_teams)
        return best_teams, best_happiness

    def team_transpose(self, t1, t2, move):
        t_new = t1 + t2
        t_new[move[0]], t_new[move[1]] = t_new[move[1]], t_new[move[0]]
        return t_new[:5], t_new[5:]

    def dfs_greedy_search(self, t1, t2, current_score, strategy_fn, prefs,
                          searched=None, max_search=5000, moves=None):
        searched = searched or [0]
        searched[0] += 1
        if searched[0] > max_search:
            return
        moves = moves or list(combinations([i for i in range(10)], 2))
        move_scores = []
        for move in moves:
            t1_, t2_ = self.team_transpose(t1, t2, move)
            h1 = [prefs[p][i] for i, p in enumerate(t1_)]
            h2 = [prefs[p][i] for i, p in enumerate(t2_)]
            move_scores.append((move, strategy_fn(h1, h2)))
        move_scores.sort(key=lambda x: x[1], reverse=True)
        for move, new_score in move_scores:
            if new_score < current_score:
                break
            t1_new, t2_new = self.team_transpose(t1, t2, move)
            yield from self.dfs_greedy_search(t1_new, t2_new, new_score,
                                              strategy_fn, prefs,
                                              searched=searched,
                                              max_search=max_search,
                                              moves=moves)
        yield t1, t2, current_score

    def fair_logsum_strategy(self, happiness_1, happiness_2):
        # adjust for team fairness
        t1_score = sum(log(max(h, self.epsilon)) for h in happiness_1)
        t2_score = sum(log(max(h, self.epsilon)) for h in happiness_2)
        # lowest possible score now is log(epsilon) * 5
        t1_score += -log(self.epsilon) * 5 + self.epsilon
        t2_score += -log(self.epsilon) * 5 + self.epsilon
        # adjust for role fairness
        # system is penalised for making a difference in mirroring roles
        diff_penalty = sum(abs(log(a + 1) - log(b + 1))
                           for a, b in zip(happiness_1, happiness_2)) / 50
        return (log(t1_score) + log(t2_score) - diff_penalty +
                random.random() / 100)
