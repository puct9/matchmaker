# Base class for all matching algorithms


class Matcher:

    NAME = ''

    @staticmethod
    def get_query(room_info, response_id):
        pass

    @staticmethod
    def read_response(response):
        pass

    def __init__(self):
        pass

    def generate_teams(self, prefs):
        pass
