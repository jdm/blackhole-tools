import os
import email
import utils
import sys
import json
import datetime

passes = 0
failures = 0
for f in os.listdir("tests"):
    fp = open("tests/" + f)
    contents = fp.read()
    fp.close()
    contents = contents.split("===EXPECTED===")
    msg = email.message_from_string(contents[0])
    bug_data = utils.extract_bug_info(msg)
    expected = eval(contents[1].strip())
    if bug_data == expected:
        passes += 1
    else:
        failures += 1
        print "%s\n  Got |%s|, expected |%s|" % (f, str(bug_data), expected)

print "%d tests run, %d failed" % (passes + failures, failures)
sys.exit(failures)
