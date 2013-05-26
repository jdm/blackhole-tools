from utils import get_bugmails, extract_bug_info
from pymongo import MongoClient

msgs = get_bugmails()
if msgs:
    client = MongoClient()
    db = client.test_database
    contributions = db.contributions

    for msg in msgs:
        bug_data = extract_bug_info(msg)
        contributions.insert(bug_data)
    print 'Synced %d bug(s) from email' % len(msgs)

# What we want:
# - email
# - contribution source
# - date/time

# For Bugzilla in particular:
# - product
# - component
# - new/changed
# - bug id
# - fields changed (array)
# - value of changed fields?
# - first patch status?
# - [X] type of new attachment
# - [X] flag being changed
