# -*- coding: UTF-8 -*-

#  ..#######.########.#######.##....#..######..######.########....###...########.#######.########..######.
#  .##.....#.##.....#.##......###...#.##....#.##....#.##.....#...##.##..##.....#.##......##.....#.##....##
#  .##.....#.##.....#.##......####..#.##......##......##.....#..##...##.##.....#.##......##.....#.##......
#  .##.....#.########.######..##.##.#..######.##......########.##.....#.########.######..########..######.
#  .##.....#.##.......##......##..###.......#.##......##...##..########.##.......##......##...##........##
#  .##.....#.##.......##......##...##.##....#.##....#.##....##.##.....#.##.......##......##....##.##....##
#  ..#######.##.......#######.##....#..######..######.##.....#.##.....#.##.......#######.##.....#..######.

'''
    gowatchseries scraper for Exodus forks.
    Nov 9 2018 - Checked

    Updated and refactored by someone.
    Originally created by others.
'''
import json
import re
import urllib
import urlparse

from exoscrapers.modules import cfscrape
from exoscrapers.modules import cleantitle
from exoscrapers.modules import client
from exoscrapers.modules import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['gowatchseries.io', 'gowatchseries.co']
        self.base_link = 'https://ww5.gowatchseries.co'
        self.search_link = '/ajax-search.html?keyword=%s&id=-1'
        self.search_link2 = '/search.html?keyword=%s'
        self.scraper = cfscrape.create_scraper()

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url == None: return

            url = urlparse.parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
            url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
            url = urllib.urlencode(url)
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []

            if url == None: return sources

            if not str(url).startswith('http'):

                data = urlparse.parse_qs(url)
                data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

                title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
                if 'season' in data: season = data['season']
                if 'episode' in data: episode = data['episode']
                year = data['year']

                query = urlparse.urljoin(self.base_link,
                                         self.search_link % urllib.quote_plus(cleantitle.getsearch(title)))
                r = self.scraper.get(query).content
                r = json.loads(r)['content']
                r = zip(client.parseDOM(r, 'a', ret='href'), client.parseDOM(r, 'a'))

                if 'tvshowtitle' in data:
                    cltitle = cleantitle.get(title + 'season' + season)
                    cltitle2 = cleantitle.get(title + 'season%02d' % int(season))
                    r = [i for i in r if cltitle == cleantitle.get(i[1]) or cltitle2 == cleantitle.get(i[1])]
                    vurl = '%s%s-episode-%s' % (self.base_link, str(r[0][0]).replace('/info', ''), episode)
                    vurl2 = None
                else:
                    cltitle = cleantitle.getsearch(title)
                    cltitle2 = cleantitle.getsearch('%s (%s)' % (title, year))
                    r = [i for i in r if
                         cltitle2 == cleantitle.getsearch(i[1]) or cltitle == cleantitle.getsearch(i[1])]
                    vurl = '%s%s-episode-0' % (self.base_link, str(r[0][0]).replace('/info', ''))
                    vurl2 = '%s%s-episode-1' % (self.base_link, str(r[0][0]).replace('/info', ''))

                r = self.scraper.get(vurl).content

                slinks = client.parseDOM(r, 'div', attrs={'class': 'anime_muti_link'})
                slinks = client.parseDOM(slinks, 'li', ret='data-video')
                if len(slinks) == 0 and not vurl2 is None:
                    r = self.scraper.get(vurl2).content
                    slinks = client.parseDOM(r, 'div', attrs={'class': 'anime_muti_link'})
                    slinks = client.parseDOM(slinks, 'li', ret='data-video')

                for slink in slinks:
                    try:
                        if 'vidnode.net/streaming.php' in slink:
                            r = self.scraper.get('https:%s' % slink)
                            clinks = re.findall(r'sources:\[(.*?)\]', r)[0]
                            clinks = re.findall(r'file:\s*\'(http[^\']+)\',label:\s*\'(\d+)', clinks)
                            for clink in clinks:
                                q = source_utils.label_to_quality(clink[1])
                                sources.append(
                                    {'source': 'cdn', 'quality': q, 'language': 'en', 'url': clink[0], 'direct': True,
                                     'debridonly': False})
                        else:
                            valid, hoster = source_utils.is_host_valid(slink, hostDict)
                            if valid:
                                sources.append(
                                    {'source': hoster, 'quality': 'SD', 'language': 'en', 'url': slink, 'direct': False,
                                     'debridonly': False})
                    except:
                        pass

            return sources
        except:
            return sources

    def resolve(self, url):
        return url
