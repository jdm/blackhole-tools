import os
import email
import utils
import sys

passes = 0
failures = 0
for f in os.listdir("tests"):
    fp = open("tests/" + f)
    contents = fp.read()
    fp.close()
    contents = contents.split("===EXPECTED===")
    msg = email.message_from_string(contents[0])
    bug_data = utils.extract_bug_data(msg)
    if str(bug_data) == contents[1]:
        passes += 1
    else:
        failures += 1
        print "Got |" + str(bug_data) + "|, expected |" + contents[1] + "|"

print "%d tests run, %d failed" % (passes + failures, failures)
sys.exit(failures)
