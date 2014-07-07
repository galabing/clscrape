#!/usr/bin/python

from bs4 import BeautifulSoup
from datetime import datetime
import argparse
import os
import time

URL_PREFIX = 'http://sfbay.craigslist.org/apa'
URL_SUFFIX = '#list'
STEP = 100

WGET = '/usr/local/bin/wget'
RETRIES = 5
SLEEP_SEC = 10

TMP_PAGE = '/tmp/sfbay.html'
MAX_PAGES = 1000000

YEAR = 2014
DATE_PATTERN = '%Y-%m-%d'

def get_url(page):
  # l1 urls are like:
  #   http://sfbay.craigslist.org/apa/index0.html
  #   http://sfbay.craigslist.org/apa/index100.html
  # etc
  return '%s/index%d.html%s' % (URL_PREFIX, page*STEP, URL_SUFFIX)

def download(url, output_path):
  for i in range(RETRIES):
    if os.path.isfile(output_path):
      os.remove(output_path)
    cmd = '%s -q -O %s "%s"' % (WGET, output_path, url)
    print 'sleeping for %d secs' % SLEEP_SEC
    time.sleep(SLEEP_SEC)
    print 'executing cmd: %s' % cmd
    if os.system(cmd) == 0: return True
  return False

def collect_paths(paths_file):
  if not os.path.isfile(paths_file): return None
  soup = BeautifulSoup(open(paths_file))
  content = soup.find_all('div', class_='content')
  if len(content) != 1: return None
  rows = content[0].find_all('p', class_='row')
  pd = dict()
  for row in rows:
    a = row.find_all('a', class_='i')
    if len(a) != 1: return None
    if 'href' not in a[0].attrs: return None
    p = a[0].attrs['href']
    date = row.find_all('span', class_='date')
    if len(date) != 1: return None
    try:
      d = datetime.strptime(date[0].text, '%b %d')
    except ValueError: return None
    d = d.replace(year=YEAR)
    pd[p] = d
  return pd

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--l2_file', required=True)
  args = parser.parse_args()

  existing_paths = set()
  if os.path.isfile(args.l2_file):
    with open(args.l2_file, 'r') as fp:
      while True:
        line = fp.readline()
        if line == '': break
        if line.startswith('#'): continue
        p = line.find(' ')
        assert p > 0
        existing_paths.add(line[:p])
  print 'loaded %d existing paths' % len(existing_paths)

  pd_map = dict()  # path => date
  for page in range(MAX_PAGES):
    url = get_url(page)
    print 'downloading page %s to %s' % (url, TMP_PAGE)
    if not download(url, TMP_PAGE):
      print 'crap, download failed'
      break
    print 'download successful, collecting paths from %s' % TMP_PAGE
    pd = collect_paths(TMP_PAGE)
    if pd is None:
      # TODO: maybe retry download.
      print 'crap, file corrupted? %s' % TMP_PAGE
      break
    print 'collected %d paths' % len(pd)
    found_something_new = False
    count = 0
    for p, d in pd.iteritems():
      if p not in existing_paths:
        pd_map[p] = d
        found_something_new = True
        count += 1
    if not found_something_new:
      print 'nothing new now, bye'
      break
    print 'found %d new paths, continue next page' % count

  with open(args.l2_file, 'a') as fp:
    print >> fp, '# from run %s' % datetime.now()
    for p in sorted(pd_map.keys()):
      print >> fp, '%s %s' % (p, pd_map[p].strftime(DATE_PATTERN))

if __name__ == '__main__':
  main()

