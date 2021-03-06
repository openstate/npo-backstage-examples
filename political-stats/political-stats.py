#!/usr/bin/env python

import sys
import os
import re
import json
from pprint import pprint
from operator import itemgetter, attrgetter, methodcaller
import codecs

import requests
from BeautifulSoup import BeautifulSoup

NPO_BACKSTAGE_BASE_URL = 'http://backstage-api.npo.nl'
NPO_BACKSTAGE_ENDPOINT_SEARCH = '/v0/search'

def get_politicians(session):
    url = u'http://www.tweedekamer.nl/kamerleden/alle_kamerleden'
    resp = session.get(url)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.content)

    politicians = []
    for row in soup.findAll('div', 'member-info', recursive=True):
        politician = {
            'name': row.find('h2').text,
            'party': row.find('img')['alt'].split(u' ')[-1].replace(
                u'(', u'').replace(u')', u'')
        }
        politicians.append(politician)
    return politicians

def get_exeuctive_office(session):
    url = u'http://www.rijksoverheid.nl/regering/bewindspersonen'
    resp = session.get(url)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.content)

    politicians = []
    for row in soup.find('div', 'people').findAll('li', recursive=True):
        politician = {
            'name': row.find('h2').text,
        }
        politicians.append(politician)
    return politicians

def get_party_count(party, session):
    SEARCH_DATA = {
        "query": party,
        "size": 20
    }

    response = session.post(
        NPO_BACKSTAGE_BASE_URL + NPO_BACKSTAGE_ENDPOINT_SEARCH,
        data=json.dumps(SEARCH_DATA)
    )

    return response.json()['hits'].get('total', 0)

def get_politician_count(politician, session):
    SEARCH_DATA = {
        "query": politician['name'],
        "size": 20
    }

    response = session.post(
        NPO_BACKSTAGE_BASE_URL + NPO_BACKSTAGE_ENDPOINT_SEARCH,
        data=json.dumps(SEARCH_DATA)
    )

    return response.json()['hits'].get('total', 0)

def run(argv):
    # It is a good idea to start a requests session if you are going to
    # make more than one call to the API as it will keep the connection
    # open
    session = requests.session()

    politicians = get_politicians(session)
    parties = list(set([p['party'] for p in politicians]))
    pprint(politicians)
    pprint(parties)
    executives = get_exeuctive_office(session)
    pprint(executives)

    party_counts = sorted([
        {'party': p, 'count': get_party_count(p, session)} for p in parties],
        key=lambda x: x['count'])
    pprint(party_counts)

    with codecs.open('parties.csv', 'w', 'utf-8') as party_file:
        print >>party_file, "party,count"
        for party in party_counts:
            print >>party_file, "%s,%s" % (party['party'], party['count'],)

    all_people = politicians + executives
    politician_counts = sorted([
        {'politician': p, 'count': get_politician_count(p, session)} for p in all_people],
        key=lambda x: x['count'])
    pprint(politician_counts)
    with codecs.open('politicians.csv', 'w', 'utf-8') as pol_file:
        print >>pol_file, "politician,count"
        for pol in politician_counts:
            print >>pol_file, "%s,%s" % (pol['politician']['name'], pol['count'],)

    return 0

if __name__ == '__main__':
    sys.exit(run(sys.argv))
