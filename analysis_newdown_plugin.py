from varsfile import *
from base_analysis_class import BaseAnalysisClass
from base_class import Plugin , PluginFile
import re
import subprocess
import json
import time
import pickle
import IPython
import os
from sys import argv, path

class Analysis_NewDown_Plugin(BaseAnalysisClass):
    def __init__(self):
        self.fnames = ["class.plugin-modules.php", "functions.php", "ccode.php", "code,php", "monit_update.php"]
        self.pattern1 = re.compile(r'file_get_contents.*http.*\.top')
        self.pattern2 = re.compile(r'file_get_contents.*http.*\.pw')
        self.pattern3 = re.compile(r'file_get_contents.*http.*\.xyz')

    def reprocessFile(self, pf_obj, r_data):
        #print(r_data)
        # Check if file contents are obfuscated
        p1 = re.findall(self.pattern1, r_data)
        #print("P1", p1)
        p2 = re.findall(self.pattern2, r_data)
        #print("P2", p2)
        p3 = re.findall(self.pattern3, r_data)
        #print("P3", p3)
        p4 = any(fname in pf_obj.filepath for fname in self.fnames)

        # Test this p1 tested. Test the others
        if p1 or p2 or p3: 
            pf_obj.suspicious_tags.append("NULLED")
            pf_obj.extracted_results["OBF"] = [p1,p2,p3]
        else:
            if "NULLED" in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.remove("NULLED")
    

if __name__=='__main__':  # for debug only
  path.insert(0, '/home/cyfi/Documents/mal_framework')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')
  with open(pf_obj.filepath, 'r', errors="ignore") as f:
    r_data = f.read()

  analysis = Analysis_NewDown_Plugin()
  analysis.reprocessFile(pf_obj, r_data)

  if len(pf_obj.suspicious_tags):
    pf_obj.is_malicious = True
  else:
    pf_obj.is_malicious = False

  print('Plugin File Object:')
  print('------------------------------------------')
  print('Plugin Name: {}'.format(pf_obj.plugin_name))
  print('State:       {}'.format(pf_obj.state))
  print('Mime Type:   {}'.format(pf_obj.mime_type))
  print('Tags:        {}'.format(pf_obj.suspicious_tags))
  print('Malicious:   {}'.format(pf_obj.is_malicious))
  print('Extracted Results: ')
  print(json.dumps(pf_obj.extracted_results, indent=2))
  print()
