from .friendmatcher import FriendMatcher

MATCHERS = [
    FriendMatcher
]

MAPPING = {
    matcher.NAME: matcher for matcher in MATCHERS
}


def str2matcher(matcher_id):
    return MAPPING[matcher_id]
