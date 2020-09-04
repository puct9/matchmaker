import json
import json.decoder
import os
import random
import string
from base64 import b64encode
from copy import deepcopy

CHARSET = string.ascii_uppercase + string.digits


class DraftDB:

    def __init__(self):
        pass

    def all_rooms(self):
        pass

    def reset(self):
        pass

    def create_room(self):
        pass

    def get_room_info(self):
        pass

    def room_exists(self, room_id):
        pass

    def add_guest(self, room_id, name):
        pass

    def advance_stage(self, room_id):
        pass

    def set_payment(self, room_id, payment, accept, team):
        pass

    def secret_to_room_id(self, secret):
        pass

    def secret_to_name(self, secret):
        pass

    def kick_user(self, secret):
        pass

    def make_captain(self, secret):
        pass


class SimpleFsDB(DraftDB):

    def __init__(self, fname='dump_draftv1.json'):
        super().__init__()
        self.fname = fname
        self.rooms = {}
        self.secrets = {}
        try:
            self.rooms, self.secrets = json.load(open(fname))
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            pass

    def write_info(self):
        json.dump([self.rooms, self.secrets], open(self.fname, 'w'), indent=4)

    def all_rooms(self):
        return deepcopy(self.rooms)

    def reset(self):
        self.rooms = {}
        self.write_info()

    def create_room(self):
        room_id = None
        # avoid collisions
        while room_id is None or room_id in self.rooms:
            room_id = ''.join(random.choices(CHARSET, k=6))
        self.rooms[room_id] = {
            'order': [],
            'guests': {},
            'captains': [],
            'stage': 0,
            'teams': [[], []],
            'intents': [[[None, None], [None, None]] for _ in range(8)]
        }
        self.write_info()
        return room_id

    def get_room_info(self, room_id):
        return deepcopy(self.rooms.get(room_id))

    def room_exists(self, room_id):
        return room_id in self.rooms

    def add_guest(self, room_id, name):
        room = self.rooms.get(room_id)
        if room is None:
            return False, 'Room does not exist'
        if room['stage']:
            return False, 'Drafting has already started'
        if len(name) < 3:
            return False, 'Name must be at least 3 characters'
        guests = room['guests']
        if any(name.lower() == n.lower() for n in guests):
            return False, 'Name taken'
        if len(guests) == 10:
            return False, 'Room is full'
        guests[name] = {'owner': False, 'coins': 100, 'captain': 0}
        if len(guests) == 1:
            guests[name]['owner'] = True
        # generate the secret for the guest
        secret = None
        while secret is None or secret in self.secrets:
            secret = b64encode(os.urandom(32)).decode()
        self.secrets[secret] = [room_id, name]
        guests[name]['secret'] = secret
        room['order'].append(name)
        self.write_info()
        return True, secret

    def advance_stage(self, room_id):
        room = self.rooms.get(room_id)
        if room is None:
            return
        room['stage'] = 1
        room['draft_order'] = room['order'].copy()
        room['draft_order'].remove(room['captains'][0])
        room['draft_order'].remove(room['captains'][1])
        random.shuffle(room['draft_order'])
        room['teams'][0].append(room['captains'][0])
        room['teams'][1].append(room['captains'][1])
        self.write_info()

    def set_payment(self, room_id, payment, accept, team):
        room = self.rooms.get(room_id)
        if room is None:
            return
        player = room['stage'] - 1
        intents = room['intents'][player]
        intents[team] = [payment, accept]
        # check if both players have made an offer
        full = None
        if intents[1 - team][0] is not None:
            # decide player
            winner = (0 if intents[0][0] > intents[1][0]
                      else 1 if intents[0][0] < intents[1][0]
                      else random.randint(0, 1))
            #       winner  0   1
            # action
            # 0             1   0   <-- resultant team
            # 1             0   1
            to_team = intents[winner][1] == winner
            room['teams'][to_team].append(room['draft_order'][player])
            room['stage'] += 1
            room['guests'][room['captains'][winner]]['coins'] -= intents[winner
                                                                         ][0]
            # check if a team is full
            full = (0 if len(room['teams'][0]) == 5
                    else 1 if len(room['teams'][1]) == 5
                    else None)
            if full is not None:
                for p in range(player + 1, 8):
                    room['teams'][1 - full].append(room['draft_order'][p])
                    room['stage'] += 1
        self.write_info()
        # return whether we are done with the drafting process
        return full is not None

    def secret_to_room_id(self, secret):
        if not self.secrets.get(secret):
            return None
        return self.secrets.get(secret)[0]

    def secret_to_name(self, secret):
        if not self.secrets.get(secret):
            return None
        return self.secrets.get(secret)[1]

    def kick_user(self, secret):
        info = self.secrets.get(secret)
        if info is None:
            return
        room_id, name = info
        if self.rooms[room_id]['stage']:
            return
        self.rooms[room_id]['order'].remove(name)
        del self.rooms[room_id]['guests'][name]
        del self.secrets[secret]
        # might be a captain
        try:
            self.rooms[room_id]['captains'].remove(name)
            for guest in self.rooms[room_id]['guests']:
                self.rooms[room_id]['guests'][guest]['captain'] = 0
            for i, capt in enumerate(self.rooms[room_id]['captains'], 1):
                self.rooms[room_id]['guests'][capt]['captain'] = i
        except ValueError:
            pass
        if self.rooms[room_id]['order']:
            # make sure the oldest member is owner
            self.rooms[room_id]['guests'][self.rooms[room_id]['order'][0]
                                          ]['owner'] = True
        self.write_info()

    def set_captain(self, secret):
        info = self.secrets.get(secret)
        if info is None:
            return
        room_id, name = info
        current = self.rooms[room_id]['captains']
        if name not in current or (len(current) == 2 and name != current[-1]):
            current.append(name)
            if len(current) > 2:
                current.pop(0)
            for guest in self.rooms[room_id]['guests']:
                self.rooms[room_id]['guests'][guest]['captain'] = 0
            for i, capt in enumerate(current, 1):
                self.rooms[room_id]['guests'][capt]['captain'] = i
            self.write_info()


class HotSwapDB(SimpleFsDB):

    def __init__(self, fname='dump_draftv1.json'):
        super().__init__()
        self.fname = fname
        self.rooms = {}
        self.secrets = {}
        try:
            self.rooms, self.secrets = json.load(open(fname))
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            pass

    def load_info(self):
        try:
            self.rooms, self.secrets = json.load(open(self.fname))
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            pass

    def all_rooms(self):
        self.load_info()
        return super().all_rooms()

    def create_room(self):
        self.load_info()
        return super().create_room()

    def get_room_info(self, room_id):
        self.load_info()
        return super().get_room_info(room_id)

    def room_exists(self, room_id):
        self.load_info()
        return super().room_exists(room_id)

    def add_guest(self, room_id, name):
        self.load_info()
        return super().add_guest(room_id, name)

    def advance_stage(self, room_id):
        self.load_info()
        return super().advance_stage(room_id)

    def set_payment(self, room_id, payment, accept, team):
        self.load_info()
        return super().set_payment(room_id, payment, accept, team)

    def secret_to_room_id(self, secret):
        self.load_info()
        return super().secret_to_room_id(secret)

    def secret_to_name(self, secret):
        self.load_info()
        return super().secret_to_name(secret)

    def kick_user(self, secret):
        self.load_info()
        return super().kick_user(secret)

    def make_captain(self, secret):
        self.load_info()
        return super().make_captain(secret)
