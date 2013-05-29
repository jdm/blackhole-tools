import sys
import re
import email
import datetime
from pymongo import MongoClient
from email.parser import Parser

f = open(sys.argv[1], "rb")
contents = f.read()
f.close()

data = []

matches = re.finditer("Date: (.*)\nSubject: \[Contribute\] Inquiry about Mozilla (.*)\nMessage-ID: (.*)\s+Email: (.*)", contents)
for match in matches:
    date_tuple = email.utils.parsedate_tz(match.groups()[0])
    date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
    email_str = match.groups()[3].replace(' at ', '@')
    interest = match.groups()[1].lower()
    data.append({'date': date, 'email': email_str, 'interest': interest})

client = MongoClient()
db = client.test_database
entrypoints = db.entrypoints

for datum in data:
    entrypoints.insert({'email': datum['email'],
                        'source': 'contributelist',
                        'datetime': datum['date'],
                        'extra': {'interest': datum['interest']}})
