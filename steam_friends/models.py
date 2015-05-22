import functools
import logging

import steam.api

from steam_friends import ext


log = logging.getLogger(__name__)


@functools.total_ordering
class SteamApp(object):

    image_url = "http://media.steampowered.com/steamcommunity/public/images/apps/{appid}/{hash}.jpg"

    def __init__(self, **kwargs):
        self.appid = kwargs['appid']
        self.name = kwargs['name'].encode('ascii', 'ignore')  # todo: what should we do here?

        self._img_logo_url = kwargs['img_logo_url']
        self._img_icon_url = kwargs['img_icon_url']

        # there are more attributes than this, but we don't need them

    def __eq__(self, other):
        try:
            return self.appid == other.appid
        except AttributeError:
            return False

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(self.appid)

    def __repr__(self):
        return "{cls}(appid={appid}, name={name})".format(
            cls=self.__class__.__name__,
            appid=self.appid,
            name=self.name,
        )

    def __str__(self):
        return self.name

    @property
    def img_icon_url(self):
        return self.image_url.format(
            appid=self.appid,
            hash=self._img_icon_url,
        )

    @property
    def img_logo_url(self):
        return self.image_url.format(
            appid=self.appid,
            hash=self._img_logo_url,
        )

    def to_dict(self):
        return {
            'appid': self.appid,
            'name': self.name,
            'img_logo_url': self._img_logo_url,
            'img_icon_url': self._img_icon_url,
        }

    # todo: crawl steam's store page and expose a bunch of things


@functools.total_ordering
class SteamUser(object):

    def __init__(self, **kwargs):
        self.avatar = kwargs['avatar']
        self.avatarmedium = kwargs['avatarmedium']
        self.avatarfull = kwargs['avatarfull']
        self.steamid = kwargs['steamid']
        self.personaname = kwargs['personaname']
        self.personastate = kwargs['personastate']

    def __eq__(self, other):
        try:
            return self.steamid == other.steamid
        except AttributeError:
            return False

    def __lt__(self, other):
        try:
            return self.personaname < other.personaname
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.steamid)

    def __str__(self):
        return self.personaname

    def __repr__(self):
        return "{cls}(steamid='{steamid}', personaname='{personaname}')".format(
            cls=self.__class__.__name__,
            steamid=self.steamid,
            personaname=self.personaname,
        )

    @property
    @ext.cache.memoize(3600)
    def friends(self, relationship='friend'):
        f = []

        # todo: only lookup friends that aren't in our cache
        log.info("Checking friends of %r", self)
        friends_response = steam.api.interface('ISteamUser').GetFriendList(
            steamid=self.steamid,
            relationship=relationship,
        )
        try:
            for friends_data in friends_response['friendslist']['friends']:
                f.append(friends_data['steamid'])
        except steam.api.HTTPError:
            log.warning("Failed fetching friends for %s", self)
        return self.get_users(f)

    @property
    @ext.cache.memoize(3600)
    def games(self, include_appinfo=1, include_played_free_games=1):
        g = []

        log.info("Checking games of %r", self)
        games_response = steam.api.interface('IPlayerService').GetOwnedGames(
            steamid=self.steamid,
            include_appinfo=include_appinfo,
            include_played_free_games=include_played_free_games,
        )
        if games_response['response'] == {}:
            log.warning("Failed fetching games for %s", self)
        else:
            for game_data in games_response['response']['games']:
                g.append(SteamApp(**game_data))
        return g

    def to_dict(self, with_friends=True, with_games=True):
        result = {
            'avatar': self.avatar,
            'avatarfull': self.avatarfull,
            'avatarmedium': self.avatarmedium,
            'personaname': self.personaname,
            'personastate': self.personastate,
            'steamid': self.steamid,
        }
        if with_friends:
            result['friends'] = [f.to_dict(with_friends=False, with_games=False) for f in self.friends]
        if with_games:
            result['games'] = [g.to_dict() for g in self.games]
        return result

    @classmethod
    def get_user(cls, steamid64):
        users = cls.get_users(steamid64)

        if not users:
            return None
        if len(users) > 1:
            raise Exception("More than one user found with steamid64 %s", steamid64)
        return users[0]

    @classmethod
    def get_users(cls, steamid64s):
        users = []

        # fetch any users in the cache
        cached_users = ext.cache.cache.get_dict(*steamid64s)
        for cached_id, cached_data in cached_users.iteritems():
            if not cached_data:
                # this shouldn't ever happen
                continue

            u = cls(**cached_data)
            steamid64s.remove(cached_id)
            users.append(u)

        # fetch any users not in the cache
        users_response = steam.api.interface('ISteamUser').GetPlayerSummaries(
            steamids=steamid64s,
            version=2,
        )
        for user_data in users_response['response']['players']:
            if not user_data:
                # this shouldn't ever happen
                continue
            u = cls(**user_data)
            ext.cache.cache.set(u.steamid, user_data)
            users.append(u)

        return users

    @classmethod
    @ext.cache.memoize(3600)
    def id_from_openid(cls, claim_id):
        if not claim_id.startswith('http://steamcommunity.com/openid/id/'):
            raise ValueError("claim_id not from steamcommunity.com")
        return claim_id[len('http://steamcommunity.com/openid/id/'):]

    @classmethod
    @ext.cache.memoize(3600)
    def id_to_id64(cls, steamid):
        # todo: cache this
        log.info("Checking for steam64id of %s", steamid)
        r = steam.api.interface('ISteamUser').ResolveVanityURL(vanityurl=steamid)
        try:
            return r['response']['steamid']
        except (KeyError, steam.api.HTTPError):
            return None
