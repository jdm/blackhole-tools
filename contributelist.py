import sys
import re
import email
import datetime
from mongotools import MongoConnection
from email.parser import Parser

f = open(sys.argv[1], "rb")
contents = f.read()
f.close()

data = []

matches = re.finditer("Date: (.*)\nSubject: \[Contribute\] Inquiry about Mozilla(.*)\nMessage-ID: (.*)\s+E[-]?mail: (.*)", contents)
for match in matches:
    date_tuple = email.utils.parsedate_tz(match.groups()[0])
    date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
    email_str = match.groups()[3].replace(' at ', '@')
    interest = match.groups()[1].lower()
    data.append({'date': date, 'email': email_str, 'interest': interest})
print 'Done matching'

with MongoConnection(configfilename='config') as conn:
    for datum in data:
        print 'Inserting %s... ' % datum['email'],
        conn.add_entrypoint(who=datum['email'],
                            source='contributelist',
                            when=datum['date'],
                            extra={'interest': datum['interest']})
        print 'done'
