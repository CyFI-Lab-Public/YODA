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

class Analysis_Bot_SEO(BaseAnalysisClass):
    def __init__(self):
        self.pattern1 = re.compile(r'mb_strtolower')
        self.pattern2 = re.compile(r'str_replace')
        self.pattern3 = re.compile(r'sqrt')
        self.pattern4 = re.compile(r'curl_setopt')
        self.pattern5 = re.compile(r'HTTP_USER_AGENT')
        self.pattern6 = re.compile(r'HTTP_HOST') 
        self.pattern7 = re.compile(r'curl_exec') 
        
        # SEO injeted
        self.pattern8  = re.compile(r'preg_match') 
        self.pattern9  = re.compile(r'crawl') 
        self.pattern10 = re.compile(r'bot') 
        self.pattern11 = re.compile(r'spider') 
        self.pattern12 = re.compile(r'google') 
        self.pattern13 = re.compile(r'teoma') 
        self.pattern14 = re.compile(r'libwww') 
        self.pattern15 = re.compile(r'facebookexternalhit') 
        self.pattern16 = re.compile(r'SERVER') 
        self.pattern17 = re.compile(r'HTTP_USER_AGENT') 

    def reprocessFile(self, pf_obj, r_data):
        lines = r_data.splitlines()
        comment_block = False
        for line in lines:
            # Check for empty line
            if not line.strip():
                continue
            current_line = line.rstrip('\n')
            current_line = current_line.lstrip()

            if comment_block == True:
                if '*/' not in current_line:
                    continue
                elif current_line.endswith('*/'):
                    comment_block = False
                    continue
                elif '*/' in current_line:
                    comment_block = False
                    #current_line = Everythin after */

            # Single line comments
            if current_line.startswith('#') or current_line.startswith('//'):
                continue
            if current_line.startswith('/*') and current_line.endswith('*/'):
                continue
            # Multiline comment
            if current_line.startswith('/*') and '*/' not in current_line:
                comment_block = True
                continue
            p1 = re.findall(self.pattern1, current_line)
            #print("P1", p1)
            p2 = re.findall(self.pattern2, current_line)
            #print("P2", p2)
            p3 = re.findall(self.pattern3, current_line)
            #print("P3", p3)
            p4 = re.findall(self.pattern4, current_line)
            #print("P4", p4)
            p5 = re.findall(self.pattern5, current_line)
            #print("P5", p5)
            p6 = re.findall(self.pattern6, current_line)
            #print("P6", p6)
            p7 = re.findall(self.pattern7, current_line)

            p8  = re.findall(self.pattern8, current_line)
            p9  = re.findall(self.pattern9, current_line)
            p10 = re.findall(self.pattern10, current_line)
            p11 = re.findall(self.pattern11, current_line)
            p12 = re.findall(self.pattern12, current_line)
            p13 = re.findall(self.pattern13, current_line)
            p14 = re.findall(self.pattern14, current_line)
            p15 = re.findall(self.pattern15, current_line)
            p16 = re.findall(self.pattern16, current_line)
            p17 = re.findall(self.pattern17, current_line)

            if p1 and p2 and p3 and p4 and p5 and p6 and p7:
                susp = True
                res = current_line
                break
            if p8 and p9 and p10 and p11 and p12 and p13 and p14 and p15 and p16 and p17:
                susp = True
                res = current_line
                break
            else:
                susp = False

        # Test this p1 tested. Test the others
        if susp: 
            pf_obj.suspicious_tags.append("BOT_SEO")
            pf_obj.extracted_results["BOT_SEO"] = res 
        else:
            if "BOT_SEO" in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.remove("BOT_SEO")
    
        


if __name__=='__main__':  # for debug only
  path.insert(0, '/home/cyfi/Documents/mal_framework')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')
  with open(pf_obj.filepath, 'r', errors="ignore") as f:
    r_data = f.read()

  analysis = Analysis_Bot_SEO()
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
