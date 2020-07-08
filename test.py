from teammaker import RoleMatcher


if __name__ == '__main__':
    prefs = [
        # 0 mason
        [10, 7, 6, 0, 3],
        # 1 luke l
        [9, 7, 6, 6, 7],
        # 2 luke y
        [6, 4, 9, 8, 7],
        # 3 corey
        [4, 4, 4, 7, 4],
        # 4 david
        [5, 1, 0, 0, 2],
        # 5 alastiar
        [4, 4, 2, 6, 3],
        # 6 Dennis
        [3, 3, 4, 4, 9],
        # 7 Andy
        [10, 7, 8, 8, 6],
        # 8 Seong
        [2, 4, 2, 1, 1],
        # 9 Derick
        [2, 1, 2, 0, 1]
    ]
    matcher = RoleMatcher()
    teams = matcher.generate_teams(prefs)
    print(teams)
