import os
import email
import utils
import sys
import json
import datetime

path = "tests/html/"
file = sys.argv[1] if len(sys.argv) > 1 else None
passes = 0
failures = 0

def exec_test(path):
    fp = open(path)
    contents = fp.read()
    fp.close()
    contents = contents.split("===EXPECTED===")
    msg = email.message_from_string(contents[0])
    bug_data = utils.extract_bug_info(msg)
    expected = '' if not contents[1].strip() else eval(contents[1].strip())
    if bug_data != expected:
        print "%s\n  Got |%s|, expected |%s|" % (f, str(bug_data), expected)
    return bug_data == expected

files = [file] if file else os.listdir(path)
for f in files:
    if exec_test(path + f):
        passes += 1
    else:
        failures += 1

print "%d tests run, %d failed" % (passes + failures, failures)
sys.exit(failures)
