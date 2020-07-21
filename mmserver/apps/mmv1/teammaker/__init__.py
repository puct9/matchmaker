from .friendmatcher import FriendMatcher
from .rolematcher import RoleMatcher, RoleMatcherV2

MATCHERS = [
    FriendMatcher,
    RoleMatcher,
    RoleMatcherV2
]

MAPPING = {
    matcher.NAME: matcher for matcher in MATCHERS
}


def str2matcher(matcher_id):
    return MAPPING[matcher_id]
