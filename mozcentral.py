import os
import sys
from datetime import tzinfo, timedelta, datetime
from pymongo import MongoClient
from git import *

class FixedOffset(tzinfo):
    def __init__(self, offset):
        self.__offset = timedelta(hours=offset)
        self.__dst = timedelta(hours=offset-1)
        self.__name = ''

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return self.__dst

try:
    f = open('last_commit', 'rb')
    last_commit = f.read()
    f.close()
except:
    last_commit = None

repo = Repo(sys.argv[1])
assert repo.bare == False

data = []
tree = filter(lambda x: x is not '', sys.argv[1].split('/'))[-1]

for commit in repo.iter_commits('master'):
    if last_commit and commit.hexsha in last_commit:
        break
    email = commit.author.email
    commit_date = commit.committed_date
    offset = commit.committer_tz_offset / 3600
    data.append({'email': email,
                 'datetime': datetime.fromtimestamp(commit_date, FixedOffset(offset)),
                 'source': 'hg',
                 'extra': {'tree': tree}})

print 'Parsed repository.'

client = MongoClient()
db = client.test_database
db.contributions.insert(data)

print 'Updated database'

f = open('last_commit', 'wb')
f.write(repo.commit('master').hexsha)
f.close()