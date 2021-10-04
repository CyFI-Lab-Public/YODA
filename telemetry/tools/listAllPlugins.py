#!/usr/bin/python3

####################################################################
#                                                                  #
#       RETRIEVE A LIST OF PLUGINS INSTALLED ON A WEBSITE          #
#         AND VERSION NUMBERS IF FOUND                             #
#                                                                  #
#       * Argument 1: Directory of JSON files to process           #
#                                                                  #
####################################################################

import json, os
from sys import argv as arg
from collections import Counter
from itertools import repeat, chain

def list_files(directory):
  file_list = []
  for root, dirs, files in os.walk(directory, topdown=True):
    files[:] = [f for f in files if '.json' in f]
    for name in files:
      file_list.append(os.path.join(root, name))
  return sorted(file_list)

def get_jdata(json_file):
  # OPEN JSON AND GET DICTIONARY
  jfile = open(json_file)
  jstr = jfile.read()
  jdata = json.loads(jstr)
  jfile.close()
  return jdata

def get_slug(jdata, plugin):
  plugin_data = jdata[plugin]
  path = plugin_data['Plugin Path']
  slug = os.path.basename(os.path.normpath(path))
  return slug

def Remove(duplicate): 
  final_list = [] 
  for num in duplicate: 
      if num not in final_list: 
          final_list.append(num) 
  return final_list 

def dump_results(plugins, slugs):    
  with open('sorted_slugs.txt', 'w') as outfile:
    for s in slugs:
      outfile.write(s[0]+'\n')

  print('Plugin List Generated')

if __name__=='__main__':
  scan_dir = arg[1]
  plugin_list = []
  slug_list = []
  final = []

  file_list = list_files(scan_dir)

  for _file in file_list:
    site = os.path.basename(os.path.normpath(_file))[:-5]
    print('Generating Plugin List for: {}'.format(site))
    jdata = get_jdata(_file)

    for plugin in jdata: # POST PROCESS PLUGIN INFO
      if 'Orphaned Plugins' not in plugin:
        if plugin not in plugin_list:
          plugin_list.append(plugin)
        slug = get_slug(jdata, plugin)
        slug_list.append(slug)

  slugs = list(chain.from_iterable(repeat(i, c) for i,c in Counter(slug_list).most_common()))
  unique_slugs = Remove(slugs)
  
  for slug in unique_slugs:
    final.append((slug, slugs.count(slug)))

  dump_results(plugin_list, final)