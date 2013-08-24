from collections import defaultdict
import ConfigParser
import json

def sanitize(s):
    return s.replace(u"\u201c", '"').replace(u"\u201d", '"').replace(u"\u2018", "'").replace(u"\u2019", "'")

DEFAULT_CONFIG = "config"
config = ConfigParser.RawConfigParser()
config.read(DEFAULT_CONFIG)

employees = None
emails = None
names = None

def classify_volunteer(author):
    global employees, emails, names
    if not employees:
        with open(config.get('employee_data', 'filename')) as f:
            employees = json.load(f)[u'Report_Entry']
            employees = filter(lambda x: u'primaryWorkEmail' in x, employees)
            emails = map(lambda x: x[u'primaryWorkEmail'], employees)
            names = map(lambda x: (sanitize(x[u'Preferred_Name_-_First_Name']),
                              sanitize(x[u'Preferred_Name_-_Last_Name'])),
                        employees)

            with open(config.get('employee_data', 'extra_emails')) as f:
                lines = f.readlines()
                if not lines[-1].split():
                    lines.pop()
                emails += map(lambda x: x.split()[0], lines)

    for (first, last) in names:
        if last in author:
            # Really dumb stemming - if the provided first name matches part of
            # a "word" in the full author's line, claim it's a match (eg. Josh in Joshua)
            if first in author or filter(lambda x: x in first, author.split()):
                return False
    else:
        for email in emails:
            if email in author:
                return False
        # Last ditch. I feel bad.
        return '@mozilla.org' not in author and '@mozilla.com' not in author
