import random
import string
from copy import deepcopy

CHARSET = string.ascii_uppercase + string.digits


class MMDB:

    def __init__(self):
        pass

    def reset(self):
        pass

    def create_room(self, players):
        # for now the mode is set only for player-player preferences
        # returns new room id
        pass

    def get_room_info(self, room_id):
        # returns {player: response, ...}, mode
        pass

    def room_exists(self, room_id):
        pass

    def set_response(self, response_id, prefs):
        # the response_id is mapped to a room
        pass

    def response_exists(self, response_id):
        pass

    def response_id_to_room(self, response_id):
        pass

    def response_id_to_player(self, response_id):
        pass


class SimpleDB(MMDB):

    def __init__(self):
        super().__init__()
        self.rooms = {}
        self.reverse_mapping = {}

    def reset(self):
        self.rooms.clear()
        self.reverse_mapping.clear()

    def create_room(self, players, mode='friend'):
        room_id = None
        # avoid collisions
        while room_id is None or room_id in self.rooms:
            room_id = ''.join(random.choices(CHARSET, k=6))
        self.rooms[room_id] = {
            'mode': mode,
            'players': [p for p in players],
            'player_info': {p: None for p in players},
            'response_ids': {}
        }
        # create some response ids
        for player in players:
            response_id = None
            # avoid collisions
            while response_id is None or response_id in self.reverse_mapping:
                response_id = ''.join(random.choices(CHARSET, k=7))
            self.rooms[room_id]['response_ids'][response_id] = player
            self.reverse_mapping[response_id] = room_id
        return room_id

    def get_room_info(self, room_id):
        return deepcopy(self.rooms.get(room_id))

    def room_exists(self, room_id):
        return self.rooms.get(room_id) is not None

    def set_response(self, response_id, prefs):
        room_id = self.reverse_mapping.get(response_id)
        if room_id is None:
            return
        player = self.rooms[room_id]['response_ids'][response_id]
        self.rooms[room_id]['player_info'][player] = prefs

    def response_exists(self, response_id):
        return self.reverse_mapping.get(response_id) is not None

    def response_id_to_room(self, response_id):
        return self.reverse_mapping.get(response_id)

    def response_id_to_player(self, response_id):
        if self.response_exists(response_id):
            return self.rooms[self.reverse_mapping[response_id]
                              ]['response_ids'][response_id]
