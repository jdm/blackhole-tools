import email
import datetime
from email.parser import Parser

from mozillapulse.config import PulseConfiguration
from mozillapulse.consumers import GenericConsumer
from mongotools import MongoConnection

# Default RabbitMQ host settings are as defined in the accompanying
# vagrant puppet files.
DEFAULT_RABBIT_HOST = '192.168.33.10'
DEFAULT_RABBIT_PORT = 5672
DEFAULT_RABBIT_VHOST = 'pulse'
DEFAULT_RABBIT_USER = 'pulse'
DEFAULT_RABBIT_PASSWORD = 'pulse'

# Global pulse configuration.
pulse_cfg = {}


class BugzillaConsumer(GenericConsumer):
    def __init__(self, **kwargs):
        super(BugzillaConsumer, self).__init__(PulseConfiguration(**kwargs),
                                               'org.mozilla.exchange.bugzilla',
                                               **kwargs)

def on_pulse_message(data, message):
    with MongoConnection() as conn:
        all_data = data['payload']
        print all_data
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

        # Remove it from the queue
        message.ack()

def main(pulse_opts):
    global pulse_cfg
    pulse_cfg.update(pulse_opts)
    pulse_cfg['applabel'] = 'blackhole_bugzilla_consumer'
    pulse = BugzillaConsumer(**pulse_cfg)
    pulse.configure(topic='#',
                    callback=on_pulse_message,
                    durable=True)
    pulse.listen()


if __name__ == "__main__":
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

