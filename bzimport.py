#!/usr/bin/python
import MySQLdb
import MySQLdb.cursors
import itertools

db = MySQLdb.connect(host="localhost",
                     db="bmo",
                     cursorclass=MySQLdb.cursors.DictCursor)

cur = db.cursor() 

cur.execute("SELECT * FROM bugs ORDER BY creation_ts DESC LIMIT 1000")

def get_customizable(db, name, field, id):
    cur = db.cursor()
    cur.execute('SELECT %s FROM %s WHERE id = %d' % (field, name, id))
    return cur.fetchone()[field]

def get_product(db, id):
    return get_customizable(db, 'products', 'name', id)

def get_component(db, id):
    return get_customizable(db, 'components', 'name', id)

def get_field(db, id):
    return get_customizable(db, 'fielddefs', 'name', id)

def get_user(db, id):
    return get_customizable(db, 'profiles', 'login_name', id)

for bug_entry in cur:
    bug = {'bug_id': bug_entry[0],
           'product': get_product(db, bug_entry['product_id']),
           'component' get_component(db, bug_entry['component_id']),
           'short_desc': bug_entry['short_desc'],
           'version': bug_entry['version'],
           'rep_platform': bug_entry['rep_platform'],
           'op_sys': bug_entry['op_sys'],
           'bug_status': bug_entry['bug_status'],
           'bug_severity': bug_entry['bug_severity'],
           'priority': bug_entry['priority'],
           'assigned_to': get_user(db, bug_entry['assigned_to']),
           'resolution': bug_entry['resolution']
           'reporter': get_user(db, bug_entry['reporter'])}

    #FIXME: needs attachment data as well

    cur2 = db.cursor()
    cur2.execute("SELECT * FROM sanitized_bugs_activity WHERE bug_id = %d ORDER BY bug_when DESC" % bug[0])
    for (key, group) in itertools.groupby(cur2, lambda x: (x['who'], x['bug_when'])):
        change = {}
        orig = {}
        for activity in group:
            field = get_field(db, activity['fieldid']) 
            change[field] = activity['added']
            orig[field] = activity['removed']
        # add entry:
        # - who: get_user(db, key[0])
        # - datetime: group[1],
        # - source: 'bugzilla',
        # - canonical: 'https://bugzilla.mozilla.org/show_bug.cgi?id=%d' % bug['bug_id'],
        # - extra: {
        #     'fields': changes.keys(),
        #     'values': changes,
        #     'id': bug['bug_id'],
        #     'product': bug['product'],
        #     'component': bug['component'],
        #     'volunteer_assignee': ... (classify bug['assigned_to']) ...
        #   }

        for (key, value) in orig:
            bug[key] = value

        # add entry:
        # - who: bug['reporter'],
        # - datetime: group[1],
        # - source: 'bugzilla',
        # - canonical: 'https://bugzilla.mozilla.org/show_bug.cgi?id=%d' % bug['bug_id'],
        # - extra: {
        #     'fields': changes.keys(),
        #     'values': changes,
        #     'id': bug['bug_id'],
        #     'product': bug['product'],
        #     'component': bug['component'],
        #     'volunteer_assignee': ... (classify bug['assigned_to']) ...
        #     'new': True
        #   }
    raw_input()
