#!/usr/bin/python3

from sys import argv

if __name__=='__main__':
  filename = argv[1]

  with open(filename, 'r') as f:
    content = f.readlines()

  # extract plugin name
  