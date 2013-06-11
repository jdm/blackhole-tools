from __future__ import absolute_import

import poplib
import re
import os
import datetime
import email
import ConfigParser
from email.parser import Parser

config = ConfigParser.ConfigParser()
config.read('config')

BUGMAIL_HOST = config.get('blackhole', 'host')
BUGMAIL_USER = config.get('blackhole', 'user')
BUGMAIL_PASS = config.get('blackhole', 'password')
BUG_ID_RE = re.compile(r'\[Bug (\d+)\]')
BUG_SUMMARY_RE = re.compile(r'\[Bug (?:\d+)\](?: New:)? (.+)$', re.MULTILINE)
COMMENT_RE = re.compile(r'--- Comment #(\d+)')
REVIEW_RE = re.compile(r'Review of attachment (\d+):')
FEEDBACK_RE = re.compile(r'\|feedback[+-]')
NEEDINFO_RE = re.compile(r'\|needinfo[+-]')
# 'admin' also comes through but is for account creation.
BUGZILLA_TYPES = (
    'new',
    'changed',
)

FIELD_NAME_TO_HEADER = {
    'resolution': 'x-bugzilla-resolution',
    'bug_status': 'x-bugzilla-status',
    'assigned_to': 'x-bugzilla-assigned-to',
    'severity': 'x-bugzilla-severity',
    'version': 'x-bugzilla-version',
    'op_sys': 'x-bugzilla-os',
    'priority': 'x-bugzilla-priority',
    'target_milestone': 'x-bugzilla-target-milestone'
}

FIELD_NAME_TO_HEADER_ARRAY = {
    'keywords': 'x-bugzilla-keywords',
    'flagtypes.name': 'x-bugzilla-flags'
}


def get_messages(delete=True, max_get=1):
    """
    Return a list of `email.message.Message` objects from the POP3 server.
    :return: list
    """
    messages = []
    if BUGMAIL_HOST:
        conn = poplib.POP3_SSL(BUGMAIL_HOST)
        conn.user(BUGMAIL_USER)
        conn.pass_(BUGMAIL_PASS)
        num_messages = len(conn.list()[1])
        num_get = min(num_messages, max_get)
        print 'Getting %d bugmails' % num_get
        for msgid in range(1, num_get + 1):
            msg_str = '\n'.join(conn.retr(msgid)[1])
            msg = Parser().parsestr(msg_str)
            if is_bugmail(msg):
                if is_interesting(msg):
                    yield msg
                if delete:
                    conn.dele(msgid)
        conn.quit()


def is_interesting(msg):
    """
    Return true if the bug is of a product and component about which we care.
    :param msg: email.message.Message object
    :return: bool
    """
    prod = msg['x-bugzilla-product']
    comp = msg['x-bugzilla-component']
    print 'Bugmail found with product=%s and component=%s' % (prod, comp)
    return True


def is_bugmail(msg):
    """
    Return true if the Message is from Bugzilla.
    :param msg: email.message.Message object
    :return: bool
    """
    return msg.get('x-bugzilla-type', None) in BUGZILLA_TYPES


def get_bug_id(msg):
    """
    Return the id of the bug the message is about.
    :param msg: email.message.Message object
    :return: int
    """
    if 'x-bugzilla-id' in msg:
        return int(msg['x-bugzilla-id'])
    m = BUG_ID_RE.search(msg['subject'])
    if m:
        return int(m.group(1))
    return None


def extract_bug_info(msg):
    """
    Extract the useful info from the bugmail message and return it.
    :param msg: message
    :return: dict
    """
    #date_str = msg.get('date')
    #date_tuple = email.utils.parsedate_tz(date_str)
    #date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))

    info = {'changed_by': msg.get('x-bugzilla-who'),
            'changed_at': msg.get('date')}

    def sanitize(s):
        return s.replace('.', '_').replace('-', '_')

    # Array of uniquely-named modified field names 
    fields = msg.get('x-bugzilla-changed-field-names')
    if fields:
        fields = map(sanitize, fields.split())
    info['fields'] = fields
    
    values = {}
    for field in fields:
        sanitized = sanitize(field)
        if field in FIELD_NAME_TO_HEADER:
            values[sanitized] = msg.get(FIELD_NAME_TO_HEADER[field])
        elif field in FIELD_NAME_TO_HEADER_ARRAY:
            values[sanitized] = map(sanitize, msg.get(FIELD_NAME_TO_HEADER_ARRAY[field]).split())
    info['values'] = values

    info['id'] = get_bug_id(msg)

    info['product'] = msg.get('x-bugzilla-product')

    info['component'] = msg.get('x-bugzilla-component')

    if msg.get('x-bugzilla-type') == 'new':
        info['new'] = True

    if msg.get('x-bugzilla-firstpatch'):
        info['firstpatch'] = True

    body = msg.get_payload(decode=True)
    if COMMENT_RE.search(body):
        info['comment'] = True

    if REVIEW_RE.search(body):
        info['review'] = True

    if FEEDBACK_RE.search(body):
        info['feedback'] = True

    if NEEDINFO_RE.search(body):
        info['needinfo'] = True

    return info

