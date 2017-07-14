#!/usr/bin/python

import re
import os
import time

diff_reg = re.compile('^D[0-9]+$')
queue_dir = "/var/www/cciq/"
report_dir = "/var/www/ccir/"

def sorted_ls(path):
    mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
    return list(sorted(os.listdir(path), key=mtime))

while True:
  print("queuing")
  time.sleep(1)
  for f in sorted_ls(queue_dir):
    print(f)
    if (diff_reg.match(f)):
        print("Running CI on " + f)
        os.system("bash cci.sh " + f + " > " + report_dir + "/" + f)
        os.remove(queue_dir + "/" + f)
    else:
        print("Failed to match " + f)
