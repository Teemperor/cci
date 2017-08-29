#!/usr/bin/python

import re
import os
import time
import datetime
import subprocess
import codecs
from urllib.request import urlopen
from bs4 import BeautifulSoup

diff_reg = re.compile('^D[0-9]+$')
git_reg = re.compile('^git:[a-zA-Z0-9_]+$')
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
  contents = open(path).readlines()[::-1]
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

def is_review_good(review):
  with open(report_dir + review) as f:
    for line in f:
      if "BUILD SUCCESS" in line:
        return 0
      if "error:" in line.lower() and not "error: pathspec " in line:
        return 2
      if "exit code 1" in line.lower():
        return 2
      if "+ exit 1" in line.lower():
        return 2
      if "build failure" in line.lower():
        return 2
    for line in f:
      if "warning:" in line.lower():
        return 1
  return 3

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
   if review_status == 2:
     return '<span style="color: red;">✗</span>'
   elif review_status == 1:
     return '<span style="color: #ffaf00;">⚠</span>'
   elif review_status == 0:
     return '<span style="color: green;">✓</span>'
   else:
     return '?'

def is_queued(review):
  return os.path.isfile(queue_dir + review)

def get_ccache_stats():
  return subprocess.check_output('ccache -s | grep cache | grep -v ccache', shell=True).decode('utf-8')

def get_log_tail(review):
  if review == "NULL":
    return ""
  return subprocess.check_output('tail -n14 ' + report_dir + review + ' | recode utf8..html', shell=True).decode('utf-8')

def is_review(job):
  return diff_reg.match(job)

def generate_report(output_file, current_job):
    out = codecs.open(output_file + ".tmp", "w", "utf-8")
    current_percent = get_progress(current_job)
    if is_review(current_job):
      out.write('<p>Running: <a href="' + report_url + current_job + '">' + current_job + '</a> - <a href="' + reviews_page + current_job + '">' + get_title(current_job) + '</a>')
    else:
      out.write('<p>Running: <a href="' + report_url + current_job + '">' + current_job + '</a> ')
    out.write('<br><progress style="width: 34em;" value="' + str(current_percent) + '" max="100"> </p>\n')
    out.write('<p style="font-size: 8px;"> Last update: ' + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S') + '</p>')
    out.write('<pre style="font-size: 8px;">' + get_ccache_stats() + '</pre>')
    out.write('<pre style="background-color: #073642; color: #839496; border-style: double;">' + get_log_tail(current_job) + '</pre>')
    out.write("<h2>Queued</h2>\n")
    out.write("<ul>\n")
    for f in sorted_ls(queue_dir)[1:15]:
        if diff_reg.match(f):
            out.write('<li style="list-style-type: none;">' + f + ' - <a href="' + reviews_page + f + '"> ')
            out.write(get_title(f))
            out.write('</a></li>\n')
        elif git_reg.match(f):
            out.write('<li style="list-style-type: none;">' + f + '</li>\n')

    out.write("</ul>\n")

    out.write("<h2>Done jobs</h2>\n")
    out.write("<ul>\n")
    for f in sorted_ls(report_dir)[0:100][::-1]:
        if f != current_job and not is_queued(f):
            if diff_reg.match(f) or git_reg.match(f):
                if diff_reg.match(f):
                  out.write('<li style="list-style-type: none;">' + get_review_image(f) + '<a href="' + report_url + f + '">' + f + '</a> - <a href="' + reviews_page + f + '">')
                  out.write(get_title(f))
                else:
                  out.write('<li style="list-style-type: none;">' + get_review_image(f) + '<a href="' + report_url + f + '">'  + f)
                out.write('</a>')
                if is_review_format_bad(f):
                  out.write('<span style="color: rgb(255, 46, 0); font-weight: bold;"> [clang-format]</span>')
                out.write('<a href="https://teemperor.de/cci-submit.php?rev=' + f + '"> [rerun]</a>')
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
