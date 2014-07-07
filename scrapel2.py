#!/usr/bin/python

# TODO: refactor with other files.

import argparse
import os
import time

URL_PREFIX = 'http://sfbay.craigslist.org'

WGET = '/usr/local/bin/wget'
RETRIES = 5
SLEEP_SEC = 1

MAX_FAILURES = 10

def get_url(path):
  return '%s/%s' % (URL_PREFIX, path)

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

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--l2_file', required=True)
  parser.add_argument('--l2_dir', required=True)
  parser.add_argument('--overwrite', action='store_true')
  args = parser.parse_args()

  pd_map = dict()
  with open(args.l2_file, 'r') as fp:
    while True:
      line = fp.readline()
      if line == '': break
      if line.startswith('#'): continue
      assert line[-1] == '\n'
      p, d = line[:-1].split(' ')
      pd_map[p] = d
  print 'loaded %d paths' % len(pd_map)

  count, failures = 0, 0
  for p, d in pd_map.iteritems():
    if failures > MAX_FAILURES:
      print "wholly shit, we've failed %d times, die now" % failures
      break
    count += 1
    print 'processing %d/%d: %s. total failures so far: %d' % (
        count, len(pd_map), p, failures)
    output_dir = '%s/%s' % (args.l2_dir, d)
    if not os.path.isdir(output_dir):
      os.mkdir(output_dir)
    output_path = '%s/%s' % (output_dir, p.replace('/', '_'))
    if os.path.isfile(output_path):
      if not args.overwrite:
        print 'file exists and not overwritable: %s' % output_path
        continue
      os.remove(output_path)
    if not download(get_url(p), output_path):
      print 'crap, download failed'
      failures += 1

if __name__ == '__main__':
  main()

