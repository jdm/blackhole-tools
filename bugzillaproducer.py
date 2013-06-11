import datetime
from mozillapulse.messages.base import GenericMessage
from mozillapulse.config import PulseConfiguration
from mozillapulse.publishers import GenericPublisher
import time
import traceback

def publish_message(publisher, data, routing_key):
    msg = GenericMessage()
    msg.routing_parts = routing_key.split('.')
    assert(isinstance(data, dict))
    for key, value in data.iteritems():
        msg.set_data(key, value)

    failures = []
    while True:
        # keep re-trying in case of failure
        try:
            publisher.publish(msg)
            break
        except Exception:
            #logger.exception(routing_key)
            traceback.print_exc()
            now = datetime.datetime.now()
            failures = [x for x in failures
                        if now - x < datetime.timedelta(seconds=60)]
            failures.append(now)
            if len(failures) >= 5:
                failures = []
                time.sleep(5 * 60)
            else:
                time.sleep(5)

class BugzillaPublisher(GenericPublisher):
    def __init__(self, **kwargs):
        GenericPublisher.__init__(self,
                                  PulseConfiguration(**kwargs),
                                  'org.mozilla.exchange.bugzilla')
