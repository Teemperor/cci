#!/usr/bin/python

import re
import os
import time
import datetime
import subprocess
import codecs
from urllib.request import urlopen
from bs4 import BeautifulSoup

git_reg = re.compile('^[a-zA-Z0-9_]+$')
queue_dir = "/var/www/cciq/"
report_dir = "/var/www/ccir/"
report_url = "https://teemperor.de/ccir/"
reviews_page = "https://reviews.llvm.org/"

cached_titles = {}

ninja_status = re.compile(r'\[(\d+)/(\d+)\]')
test_status = re.compile(r'\((\d+) of (\d+)\)')

def get_progress(f):
  if f == "NULL":
    return 100
  path = report_dir + f
  try:
    contents = open(path).readlines()[::-1]
  except FileNotFoundError:
    return 0
  for line in contents:
    left = 0
    right = 0
    percent = 0
    m1 = ninja_status.search(line)
    if m1:
      left = int(m1.group(1))
      right = int(m1.group(2))
    m2 = test_status.search(line)
    if not m1 and m2:
      percent = 0.5
      left = int(m2.group(1))
      right = int(m2.group(2))
    if m1 or m2:
      #print("l" + str(left) + ":" + str(right))
      percent += (left / right) * 0.5
      return int(percent * 100)
  return 0

def get_title_impl(review):
  print("Getting title for review " + review)
  soup = BeautifulSoup(urlopen(reviews_page + review), "html.parser")
  return ''.join([i if ord(i) < 128 else '' for i in soup.title.string]).strip().split(' ', 1)[1]

def get_title(review):
  if not review in cached_titles:
    cached_titles[review] = get_title_impl(review)
  return cached_titles[review]

ignored_tests = set([
  "LLVM-Unit :: Support/./SupportTests/CrashRecoveryTest.Basic",
  "LLVM-Unit :: Support/./SupportTests/CrashRecoveryTest.Cleanup",
  "LLVM :: Transforms/SampleProfile/indirect-call.ll",
  "LLVM :: Transforms/SampleProfile/inline-combine.ll",
  "LLVM :: Transforms/SampleProfile/inline-coverage.ll",
  "LLVM :: Transforms/SampleProfile/inline.ll",
  "LLVM :: Transforms/SampleProfile/remarks.ll"
])

def get_failed_tests(review):
  failed_tests = set()
  parsing_tests = False
  with open(report_dir + review) as f:
    for line in f:
      if parsing_tests:
        content = line[len("00:00:00"):].strip()
        if len(content) == 0:
          break
        failed_tests.add(content)
      if "Failing Tests " in line:
        parsing_tests = True
  return list(failed_tests.difference(ignored_tests))

def is_review_good(review):
  with open(report_dir + review) as f:
    for line in f:
      if "BUILD SUCCESS" in line:
        return 0
      #if "error:" in line.lower() and not "error: pathspec " in line:
      #  if not "==ERROR:" in line:
      #    if not "FileCheck error:" in line:
      #      return 2
      if "exit code 1" in line.lower():
        return 2
      if "warning:" in line.lower():
        return 1
      if "+ exit 1" in line.lower():
        return 2
      if "failing tests " in line.lower():
        failed_tests = get_failed_tests(review)
        #print(failed_tests)
        if len(failed_tests) == 0:
          return 0
        else:
          return 2
      if "build failure" in line.lower():
        return 2
  return 2

def is_review_format_bad(review):
  with open(report_dir + review) as f:
    for line in f:
      if "CLANG-FORMAT-OK" in line:
        return False
      if "CLANG-FORMAT-FALSE" in line:
        return True
  return True

def get_review_image(review):
   review_status = is_review_good(review)
   if review_status >= 1:
     return '<span class="fail">☒</span>'
   #elif review_status == 1:
   #  return '<span class="warning">⚠</span>'
   elif review_status == 0:
     return '<span class="good">☑</span>'
   else:
     return '?'

def is_queued(review):
  return os.path.isfile(queue_dir + review)

def get_ccache_stats():
  return subprocess.check_output('ccache -s | grep cache | grep -v ccache | tr "\n" "|" | tr -s " "; echo -n "LOAD:" ; cat /proc/loadavg', shell=True).decode('utf-8')

def get_log_tail(review):
  if review == "NULL":
    return ""
  return subprocess.check_output('tail -n10 ' + report_dir + review + ' | recode utf8..html', shell=True).decode('utf-8')

def is_review(job):
  return False # diff_reg.match(job)

def generate_report(output_file, current_job):
    out = codecs.open(output_file + ".tmp", "w", "utf-8")
    current_percent = get_progress(current_job)
    out.write('<div class="meta_stats"><p class="current_time"> Last update: ' + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + '</p>')
    out.write('<p class="ccache_stats">' + get_ccache_stats() + '</p></div>\n')
    if is_review(current_job):
      out.write('<p class="current">Running: <a href="' + report_url + current_job + '">' + current_job + '</a> - <a href="' + reviews_page + current_job + '">' + get_title(current_job) + '</a>')
    else:
      out.write('<p class="current">Running: <a href="' + report_url + current_job + '">' + current_job + '</a> ')
    out.write('<progress class="current_prog" value="' + str(current_percent) + '" max="100"> </p>\n')
    out.write('<pre class="log">' + get_log_tail(current_job) + '</pre>')
    out.write('<div class="queued"><h2 class="queued_h">Queued</h2>\n')
    out.write('<ul class="queued_ul">\n')
    for f in sorted_ls(queue_dir)[1:15]:
      out.write('<li class="job_item">' + f + '</li>\n')

    out.write("</ul><br></div>\n")

    out.write('<div class="done"><h2 class="done_h">Done jobs</h2>\n')
    out.write('<ul class="done_ul">\n')
    for f in sorted_ls(report_dir)[::-1][0:25]:
        if f != current_job and not is_queued(f):
            if git_reg.match(f):
                out.write('<li class="job_item">' + get_review_image(f) + '<a href="' + report_url + f + '">'  + f)
                out.write('</a>')
                try:
                  if is_review_format_bad(f):
                    out.write('<span class="clang_format_warn">[clang-format]</span>')
                except UnicodeDecodeError:
                  out.write('<span class="clang_format_warn">[failed to parse log]</span>')
                out.write('<a class="patch_link" href="' + report_url + f + '.patch">[patch]</a>')
                out.write('<a class="rerun_link" href="https://teemperor.de/cci-submit.php?rev=' + f + '">[rerun]</a>')
                out.write('</li>\n')
    out.write("</ul>\n")
    out.close()
    os.rename(output_file + ".tmp", output_file)

def sorted_ls(path):
    mtime = lambda f: os.stat(os.path.join(path, f)).st_mtime
    return list(sorted(os.listdir(path), key=mtime))

while True:
    time.sleep(1)
  #try:
    current_running = "NULL"
    jobs = sorted_ls(queue_dir)
    if len(jobs):
      current_running = jobs[0]
    generate_report("/var/www/cci_inc.html", current_running)
  #except:
    #pass
