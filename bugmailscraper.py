import email
import datetime
from email.parser import Parser
from utils import get_messages, extract_bug_info
from mongotools import MongoConnection
from tools import classify_volunteer

with MongoConnection() as conn:
    count = 0
    for msg in get_messages():
        try:
            all_data = extract_bug_info(msg)
        except:
            continue

        who = all_data['changed_by']
        all_data.pop('changed_by')

        author_info = who
        if 'author_name' in all_data:
            author_info += " " + all_data['author_name']
            all_data.pop('author_name')
        volunteer = classify_volunteer(author_info)

        all_data['volunteer_assignee'] = classify_volunteer(all_data['assignee'])

        when_str = all_data['changed_at']
        when_tuple = email.utils.parsedate_tz(when_str)
        when = datetime.datetime.fromtimestamp(email.utils.mktime_tz(when_tuple))
        all_data.pop('changed_at')
        source = 'bugzilla'
        comment = ('#c' + str(all_data['comment'])) if 'comment' in all_data else ''
        canonical = 'https://bugzilla.mozilla.org/show_bug.cgi?id=%s%s' % (all_data['id'],
                                                                           comment)
        conn.add_contribution(who, when, source, canonical, volunteer, all_data)

        count += 1
    print 'Synced %d bug(s) from email' % count
