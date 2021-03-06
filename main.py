from utils import get_messages, extract_bug_info
from bugzillaproducer import publish_message, BugzillaPublisher

# Default RabbitMQ host settings are as defined in the accompanying
# vagrant puppet files.
DEFAULT_RABBIT_HOST = '192.168.33.10'
DEFAULT_RABBIT_PORT = 5672
DEFAULT_RABBIT_VHOST = 'pulse'
DEFAULT_RABBIT_USER = 'pulse'
DEFAULT_RABBIT_PASSWORD = 'pulse'

# Global pulse configuration.
pulse_cfg = {}

def main(pulse_opts):
    global pulse_cfg
    pulse_cfg.update(pulse_opts)
    publisher = BugzillaPublisher(**pulse_cfg)

    count = 0
    for msg in get_messages():
        bug_data = extract_bug_info(msg)
        publish_message(publisher, bug_data, 'org.mozilla.bugzilla.exchange')
        count += 1
    print 'Synced %d bug(s) from email' % count


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--host', action='store', dest='host',
                      default=DEFAULT_RABBIT_HOST,
                      help='host running RabbitMQ; defaults to %s' %
                      DEFAULT_RABBIT_HOST)
    parser.add_option('--port', action='store', type='int', dest='port',
                      default=DEFAULT_RABBIT_PORT,
                      help='port on which RabbitMQ is running; defaults to %d'
                      % DEFAULT_RABBIT_PORT)
    parser.add_option('--vhost', action='store', dest='vhost',
                      default=DEFAULT_RABBIT_VHOST,
                      help='name of pulse vhost; defaults to "%s"' %
                      DEFAULT_RABBIT_VHOST)
    parser.add_option('--user', action='store', dest='user',
                      default=DEFAULT_RABBIT_USER,
                      help='name of pulse RabbitMQ user; defaults to "%s"' %
                      DEFAULT_RABBIT_USER)
    parser.add_option('--password', action='store', dest='password',
                      default=DEFAULT_RABBIT_PASSWORD,
                      help='password of pulse RabbitMQ user; defaults to "%s"'
                      % DEFAULT_RABBIT_PASSWORD)
    (opts, args) = parser.parse_args()
    main(opts.__dict__)

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
