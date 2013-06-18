import email
import datetime
from email.parser import Parser
from utils import get_messages, extract_bug_info
from mongotools import MongoConnection

with MongoConnection() as conn:
    count = 0
    for msg in get_messages():
        all_data = extract_bug_info(msg)

        who = all_data['changed_by']
        all_data.pop('changed_by')
        when_str = all_data['changed_at']
        when_tuple = email.utils.parsedate_tz(when_str)
        when = datetime.datetime.fromtimestamp(email.utils.mktime_tz(when_tuple))
        all_data.pop('changed_at')
        source = 'bugzilla'
        comment = ('#c' + str(all_data['comment'])) if 'comment' in all_data else ''
        canonical = 'https://bugzilla.mozilla.org/show_bug.cgi?id=%s%s' % (all_data['id'],
                                                                           comment)
        conn.add_contribution(who, when, source, canonical, all_data)

        count += 1
    print 'Synced %d bug(s) from email' % count
