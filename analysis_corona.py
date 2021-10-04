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

class Analysis_Corona(BaseAnalysisClass):
    def __init__(self):
        self.pattern1 = re.compile(r'COVID-19', re.IGNORECASE)
        self.pattern2 = re.compile(r'COVID19', re.IGNORECASE)
        self.pattern3 = re.compile(r'COVID', re.IGNORECASE)
        self.pattern4 = re.compile(r'Coronavirus', re.IGNORECASE)
        self.pattern5 = re.compile(r'Corona virus', re.IGNORECASE)
        self.names = ["COVID-19 Coronavirus - Live Map WordPress Plugin", 
                      "Coronavirus Spread Prediction Graphs", 
                      "Covid-19"]


    def reprocessFile(self, pf_obj, r_data):
        # Check if file contents are obfuscated
        p1 = re.findall(self.pattern1, r_data)
        p2 = re.findall(self.pattern2, r_data)
        p3 = re.findall(self.pattern3, r_data)
        p4 = re.findall(self.pattern4, r_data)
        p5 = re.findall(self.pattern5, r_data)
        p6 = False

        if pf_obj.plugin_name in self.names:
            p6 = True

        if p1 or p2 or p3 or p4 or p5:
            if "CORONA" not in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.append("CORONA")
        else:
            if "CORONA" in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.remove("CORONA")
        if p6: 
            if "KNOWN_CORONA" not in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.append("KNOWN_CORONA")
        else:
            if "KNOWN_CORONA" in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.remove("KNOWN_CORONA")
    
        

if __name__=='__main__':  # for debug only
  path.insert(0, '/media/ranjita/workspace/cms-defense-aws')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')
  with open(pf_obj.filepath, 'r', errors="ignore") as f:
    r_data = f.read()

  analysis = Analysis_Corona()
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
