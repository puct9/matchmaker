import random
from itertools import combinations, permutations
from math import log, exp

from .base import Matcher


# custom mathematical functions
def sech2(x):
    return 4 * exp(-2 * x) / (exp(-2 * x) + 1) ** 2


class RoleMatcher(Matcher):

    NAME = 'role'

    @staticmethod
    def get_query(room_info, response_id):
        other_players = room_info['players'].copy()
        other_players.remove(room_info['response_ids'][response_id])
        return ('Roughly how many of the other players can you '
                'beat at each role? Assume that your best 3 champions for '
                'each role are banned.',
                'Answer as a value from 0 to 9. Other players are:',
                [
                    ('top', 'Top lane', 'number'),
                    ('jg', 'Jungle', 'number'),
                    ('mid', 'Mid lane', 'number'),
                    ('adc', 'AD Carry', 'number'),
                    ('sup', 'Support', 'number')
                ],
                'respond_page_rm1.html',
                other_players)

    @staticmethod
    def read_response(response):
        roles = ['top', 'jg', 'mid', 'adc', 'sup']
        values = []
        for role in roles:
            try:
                values.append(min(max(int(response.get(role, 0)), 0), 9))
            except (KeyError, ValueError):
                values.append(0)
        return values

    def __init__(self, epsilon=1e-5, strategy='fair'):
        super().__init__()
        self.epsilon = epsilon
        self.strategy = strategy

    def generate_teams(self, prefs):
        strategy_fn = {
            'fair': self.fair_logsum_strategy
        }[self.strategy]
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
            best_score, strategy_fn, prefs, max_search=50
        )
        for suggest_t1, suggest_t2, score in suggestions:
            if score <= best_score:
                continue
            best_score = score
            best_teams = (suggest_t1, suggest_t2)
        bonus_info = []
        strategy_fn(
            [prefs[p][i] for i, p in enumerate(best_teams[0])],
            [prefs[p][i] for i, p in enumerate(best_teams[0])],
            print_fn=bonus_info.append,
            verbose=True
        )
        return best_teams, bonus_info[0]

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

    def fair_logsum_strategy(self, happiness_1, happiness_2, print_fn=None,
                             verbose=False):
        print_fn = print_fn or (print if verbose else None)
        # adjust for team fairness
        t1_score = sum(log(h + self.epsilon) for h in happiness_1)
        t2_score = sum(log(h + self.epsilon) for h in happiness_2)
        fairness_bonus = sech2(t1_score - t2_score) * 5
        # adjust for role fairness
        # system is penalised for making a difference in mirroring roles
        diff_softness = 2
        diff_penalty = sum((log(a + diff_softness) -
                            log(b + diff_softness)) ** 2 * 5
                           for a, b in zip(happiness_1, happiness_2))
        if print_fn is not None:
            diffs = [(log(a + diff_softness) -
                      log(b + diff_softness)) ** 2 * 5
                     for a, b in zip(happiness_1, happiness_2)]
            positives = t1_score + t2_score + fairness_bonus
            print_fn(f'Evaluation metrics:\n=======\nBonuses\n=======\n'
                     f'Team 1 happiness  {happiness_1}\n'
                     f'Team 2 happiness  {happiness_2}\n'
                     f'Team 1 score        {t1_score}\n'
                     f'Team 2 score        {t2_score}\n'
                     f'Fairness bonus    + {fairness_bonus}\n'
                     f'Calculation       = {positives}\n\n'
                     f'=========\nPenalties\n=========\n'
                     f'Differences      {diffs}\n'
                     f'Calculation      {diff_penalty}\n\n'
                     f'=====\nScore\n=====\n{positives - diff_penalty}\n')
        # + random.random() / 100
        return (t1_score + t2_score + fairness_bonus - diff_penalty)


class RoleMatcherV2(RoleMatcher):

    NAME = 'rolev2'

    @staticmethod
    def get_query(room_info, response_id):
        ret = super(RoleMatcherV2, RoleMatcherV2).get_query(room_info,
                                                            response_id)
        ret = list(ret)
        ret[3] = 'respond_page_rm2.html'
        return tuple(ret)

    @staticmethod
    def read_response(response):
        values = super(RoleMatcherV2, RoleMatcherV2).read_response(response)
        # append on judgement of other players named p0->p8
        rating_keys = {
            'worse': 0,
            'unsure': 1,
            'better': 2,
            None: 1
        }
        for i in range(9):
            values.append(rating_keys[response.get(f'rate{i}')])
        return values

    def __init__(self, *args):
        super().__init__(*args)

    def generate_teams(self, prefs):
        strategy_fn = {
            'fair': self.fair_logsum_strategy
        }[self.strategy]
        prefs_ = [x[:5] for x in prefs]
        ratings = [x[5:] for x in prefs]
        for i, rating in enumerate(ratings):
            rating.insert(i, 0)
        for player_num in range(10):
            # get rating of each player based on the responses from peers
            peer_rating = sum(r[player_num] for r in ratings)
            prefs_[player_num].append(peer_rating)
        prefs = prefs_
        # we start with a random assortment of the two teams
        team1 = random.sample([i for i in range(10)], k=5)
        team2 = list({i for i in range(10)} - set(team1))
        random.shuffle(team2)
        # then we make changes to the teams and see
        # if some changes result in improvements to the teams
        happiness_1 = [prefs[p][i] for i, p in enumerate(team1)]
        happiness_2 = [prefs[p][i] for i, p in enumerate(team2)]
        ratings_1 = [prefs[p][5] for p in team1]
        ratings_2 = [prefs[p][5] for p in team2]
        best_score = strategy_fn(happiness_1, happiness_2,
                                 ratings_1, ratings_2)
        best_teams = (team1, team2)
        suggestions = self.dfs_greedy_search(team1, team2,
            best_score, strategy_fn, prefs, max_search=10
        )
        for suggest_t1, suggest_t2, score in suggestions:
            if score <= best_score:
                continue
            best_score = score
            best_teams = (suggest_t1, suggest_t2)
        bonus_info = []
        strategy_fn(
            [prefs[p][i] for i, p in enumerate(best_teams[0])],
            [prefs[p][i] for i, p in enumerate(best_teams[1])],
            [prefs[p][5] for p in best_teams[0]],
            [prefs[p][5] for p in best_teams[1]],
            print_fn=bonus_info.append,
            verbose=True
        )
        return best_teams, bonus_info[0]

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
            p1 = [prefs[p][5] for p in t1_]
            p2 = [prefs[p][5] for p in t2_]
            move_scores.append((move, strategy_fn(h1, h2, p1, p2)))
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

    def fair_logsum_strategy(self, happiness_1, happiness_2,
                             ratings_1, ratings_2, print_fn=None,
                             verbose=False):
        print_fn = print_fn or (print if verbose else None)
        # adjust for team fairness based on lanes
        t1_score = sum(log((h + self.epsilon) ** 2) + h ** 0.75
                       for h in happiness_1) / 3
        t2_score = sum(log((h + self.epsilon) ** 2) + h ** 0.75
                       for h in happiness_2) / 3
        fairness_bonus = sech2(t1_score - t2_score) * 3
        # adjust for team fairness based on peer rated strength
        t1_rating = sum(ratings_1)
        t2_rating = sum(ratings_2)
        rating_fairness = sech2((t1_rating - t2_rating) / 3) ** 0.5 * 4
        # adjust for role fairness
        # system is penalised for making a difference in mirroring roles
        diff_softness = 2
        diff_penalty = sum((log(a + diff_softness) -
                            log(b + diff_softness)) ** 2 * 5 +
                            0.04 * (c - d) ** 2
                           for a, b, c, d in zip(happiness_1, happiness_2,
                                                 ratings_1, ratings_2))
        if print_fn is not None:
            diffs = [(log(a + diff_softness) -
                      log(b + diff_softness)) ** 2 * 5 +
                      0.04 * (c - d) ** 2
                     for a, b, c, d in zip(happiness_1, happiness_2,
                                           ratings_1, ratings_2)]
            positives = t1_score + t2_score + fairness_bonus + rating_fairness
            print_fn(f'Evaluation metrics:\n=======\nBonuses\n=======\n'
                     f'Team 1 skill      {happiness_1} -> '
                     f'{round(t1_score, 2)}\n'
                     f'Team 2 skill      {happiness_2} -> '
                     f'{round(t2_score, 2)}\n'
                     f'Team 1 ratings    {ratings_1} -> {sum(ratings_1)}\n'
                     f'Team 2 ratings    {ratings_2} -> {sum(ratings_2)}\n'
                     f'Fairness bonus      {round(fairness_bonus, 2)}  (/3)\n'
                     f'Rating fairness   + {round(rating_fairness, 2)}  (/4)\n'
                     f'Calculation       = {round(positives, 2)}\n\n'
                     f'=========\nPenalties\n=========\n'
                     f'Differences      {[round(d, 2) for d in diffs]}\n'
                     f'Calculation      {round(diff_penalty, 2)}\n\n'
                     f'=====\nScore\n=====\n'
                     f'{round(positives - diff_penalty, 2)}\n')
        # + random.random() / 100
        return (t1_score + t2_score + fairness_bonus + rating_fairness -
                diff_penalty)
