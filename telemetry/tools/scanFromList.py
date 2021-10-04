#!/usr/bin/python3

import os, subprocess
from sys import argv, stdout

if __name__=='__main__':
  slug_list = argv[1]

  with open(slug_list, 'r') as f:
    slugs = f.readlines()

  slugs = [s.strip('\n') for s in slugs]

  n = 0
  for slug in slugs:
    n = n+1
    cmd = 'python3 TelemetryScanner.py -j {}'.format(slug)

    try:
      subprocess.run(cmd, shell=True)
      print()
      print('Telemetry Scan Successful: {}/{}'.format(n, len(slugs)))
      print()
      print('==========================================\n')
      
    except:
      print()
      print('Something went wrong')
      print()
      print('==========================================\n')
    stdout.flush()

  print()
  print('TELEMETRY ANALYSIS COMPLETE')