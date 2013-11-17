from __future__ import absolute_import

import poplib
import re
import os
import datetime
import email
import ConfigParser
from email.parser import Parser
from email.header import decode_header
from BeautifulSoup import BeautifulSoup

config = ConfigParser.ConfigParser()
config.read('config')

BUGMAIL_HOST = config.get('blackhole', 'host')
BUGMAIL_USER = config.get('blackhole', 'user')
BUGMAIL_PASS = config.get('blackhole', 'password')
BUG_ID_RE = re.compile(r'\[Bug (\d+)\]')
BUG_SUMMARY_RE = re.compile(r'\[Bug (?:\d+)\](?: New:)?\s+(.+)', re.DOTALL)
COMMENT_RE = re.compile(r'Comment # (\d+)')
ATTACHMENT_FLAG_RE = re.compile(r'Attachment #(\d+) Flags')
ATTACHMENT_CREATE_RE = re.compile(r'Created attachment (\d+) \[details\]( \[diff\] \[review\])?')
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
    'bug_severity': 'x-bugzilla-severity',
    'version': 'x-bugzilla-version',
    'op_sys': 'x-bugzilla-os',
    'priority': 'x-bugzilla-priority',
    'target_milestone': 'x-bugzilla-target-milestone'
}

FIELD_NAME_TO_HEADER_ARRAY = {
    'keywords': 'x-bugzilla-keywords',
#    'flagtypes.name': 'x-bugzilla-flags'
}


def get_messages(delete=True, max_get=1000):
    """
    Return a list of `email.message.Message` objects from the POP3 server.
    :return: list
    """
    messages = []
    if BUGMAIL_HOST:
        conn = poplib.POP3_SSL(BUGMAIL_HOST)
        conn.user(BUGMAIL_USER)
        conn.pass_(BUGMAIL_PASS)
        (num_messages, total_size) = conn.stat()
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

    values = {}

    # Array of uniquely-named modified field names 
    fields = msg.get('x-bugzilla-changed-field-names')
    if fields:
        fields = fields.split()
        info['fields'] = map(sanitize, fields)
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

    info['assignee'] = msg.get('x-bugzilla-assigned-to')

    if msg.get('x-bugzilla-type') == 'new':
        info['new'] = True

    if msg.get('x-bugzilla-firstpatch'):
        info['firstpatch'] = True

    body = msg.get_payload(decode=(not msg.is_multipart()))
    if isinstance(body, list):
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                body = part.get_payload(decode=True)
                break

    document = BeautifulSoup(body, convertEntities=BeautifulSoup.HTML_ENTITIES)

    diffs = document.find('div', {'class':'diffs'})
    if diffs:
        all_diffs = diffs.table.findAll('tr')[1:]
        for diff in all_diffs:
            entries = diff.findAll('td')
            kind = entries[0].string
            removed = entries[1].string.strip()
            added = entries[2].string.strip()

            if added and (ATTACHMENT_FLAG_RE.match(kind) or kind == 'Flags'):
                if 'flagtypes_name' not in info['values']:
                    info['values']['flagtypes_name'] = []
                info['values']['flagtypes_name'] += [added]

            elif kind == 'Whiteboard':
                if added.find('mentor=') != -1:
                    info['mentored'] = True
                info['values']['status_whiteboard'] = added

            else:
                bug_flags = ['status-', 'blocking-', 'tracking-']
                present_flags = filter(lambda x: kind.find(x) != -1, bug_flags)
                if present_flags:
                    info['values']['cf_' + sanitize(kind)] = added
            #print '%s: %s' % (kind, added)

    header_value = msg['subject']

    # see http://stackoverflow.com/questions/7331351/python-email-header-decoding-utf-8
    if not BUG_SUMMARY_RE.search(header_value):
        default_charset = 'ASCII'
        header_value = re.sub(r"(=\?.*\?=)(?!$)", r"\1 ", header_value)
        dh = decode_header(header_value)
        header_value = ' '.join([ unicode(t[0], t[1] or default_charset) for t in dh ])
        #print header_value

    summary = BUG_SUMMARY_RE.search(header_value).groups()[-1].replace('\r\n', '')
    info['summary'] = summary

    comments = document.find(id='comments')
    if comments:
        # get the comment number and author name
        if 'new' not in info:
            info['comment'] = int(COMMENT_RE.search(comments.find('a').string).group(1))

        # check for new attachments
        content = ''.join(comments.div.pre.findAll(text=True))
        attachment = ATTACHMENT_CREATE_RE.search(content)
        if attachment:
            # new patch ([diff] present)?
            if attachment.group(2):
                info['patch'] = True
            info['attachment'] = True
            info['values']['attachment_created'] = attachment.group(1)
        #print content

    if 'new' in info:
        fields = document.findAll('td', {'class': 'c1'})
        for field in fields:
            attachment = ATTACHMENT_FLAG_RE.search(field.b.string)
            if attachment:
                info['values']['attachment_created'] = attachment.group(1)
                sibling = field.parent.find('td', {'class':'c2'})
                info['values']['flagtypes_name'] = [sibling.string.strip()]

    author = document.find('span', {'class': 'vcard'})
    if author:
        author_info = author.find('span', {'class': 'fn'})
        if author_info:
            info['author_name'] = author_info.string
        else:
            #print author
            pass
    
    return info

