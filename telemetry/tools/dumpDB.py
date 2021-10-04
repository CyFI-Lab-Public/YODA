#!/usr/bin/python3

import sqlite3
from sys import argv

if __name__=='__main__':
  db_name = argv[1]

  try:
    database = sqlite3.connect(db_name)
  except:
    print('Couldn\'t connect to database: {}'.format(db_name))

  db = database.cursor()

  db.execute('SELECT name FROM wp_mkt')
  
  print('WORDPRESS MARKETPLACE:')
  for name in db.fetchall():
    print(name[0])

  
  db.execute('SELECT name FROM drupal_mkt')
  
  print('\n\nDRUPAL MARKETPLACE:')
  for name in db.fetchall():
    print(name[0])

  
  db.execute('SELECT name FROM joomla_mkt')
  
  print('\n\nJOOMLA MARKETPLACE:')
  for name in db.fetchall():
    print(name[0])


  db.execute('SELECT name FROM jext')
  
  print('\n\nSTOREJEXTENSIONS:')
  for name in db.fetchall():
    print(name[0])


  db.execute('SELECT name FROM codecanyon')
  
  print('\n\nCODECANYON:')
  for name in db.fetchall():
    print(name[0])

  db.execute('SELECT name FROM edd')
  
  print('\n\nEDD:')
  for name in db.fetchall():
    print(name[0])

  db.execute('SELECT name FROM wpmudev')
  
  print('\n\nWPMU-DEV:')
  for name in db.fetchall():
    print(name[0])

  db.execute('SELECT name FROM github')
  
  print('\n\nGITHUB:')
  for name in db.fetchall():
    print(name[0])

  db.execute('SELECT * FROM themeforest')
  
  print('\n\nTHEMEFOREST:')
  for name in db.fetchall():
    print(name)
