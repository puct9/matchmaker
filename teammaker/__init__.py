from .friendmatcher import FriendMatcher
from .rolematcher import RoleMatcher

MATCHERS = [
    FriendMatcher,
    RoleMatcher
]

MAPPING = {
    matcher.NAME: matcher for matcher in MATCHERS
}


def str2matcher(matcher_id):
    return MAPPING[matcher_id]
