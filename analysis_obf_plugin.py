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

class Analysis_Obf_Plugin(BaseAnalysisClass):
    def __init__(self):
        self.pattern1 = re.compile(r'\$[0Oo]+[{=]')
        self.pattern2 = re.compile(r'\$__=\$__.')
        self.pattern3 = re.compile(r'base64_decode[\s\(]')
        self.pattern4 = re.compile(r'/\*[a-z0-9]+\*/') #/*6g33*/ pattern 
        self.pattern5 = re.compile(r'eval[\s\(]')
        self.pattern6 = re.compile(r'^[A-Za-z0-9]+$') #Jumbled letters and numbers only in the entire line
        self.pattern7 = re.compile(r'my_sucuri_encoding') # Legit sucuri file that look slike bad file
        self.pattern8 = re.compile(r'\'.\'=>\'.\'') # Array map obfus
        self.pattern9 = re.compile(r'chr\([0-9]+\)') # int to ascii
        self.pattern12 = re.compile(r'gzinflate[\s\(]') # int to ascii
        self.pattern15 = re.compile(r'\$[li]+[{=]')

    def reprocessFile(self, pf_obj, r_data):
        #print(r_data)
        # Check if file contents are obfuscated
        p1 = re.findall(self.pattern1, r_data)
        #print("P1", p1)
        p2 = re.findall(self.pattern2, r_data)
        #print("P2", p2)
        p3 = re.findall(self.pattern3, r_data)
        #print("P3", p3)
        p4 = re.findall(self.pattern4, r_data)
        #print("P4", p4)
        p5 = re.findall(self.pattern5, r_data)
        #print("P5", p5)
        p6 = re.findall(self.pattern6, r_data)
        #print("P6", p6)
        p7 = re.findall(self.pattern7, r_data)
        #print("P7", p7)
        p8 = re.findall(self.pattern8, r_data)
        #print("P8", p8)
        p9 = re.findall(self.pattern9, r_data)
        #print("P9", p9)
        p12 = re.findall(self.pattern12, r_data)
        #print("P12", p12)
        p15 = re.findall(self.pattern15, r_data)
        #print("P15", p15)
        susp = False
        p10=None
        p11=None
        p13=None
        p14=None
        if len(p9) > 15 or p3 or (p3 and p5 and p12) or p15:
            f = open(pf_obj.filepath, 'r', encoding='ISO-8859-1')
            comment_block = False
            for line in f:
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
                p10 = re.findall(self.pattern9, current_line)
                # Find base64_decde in line
                p11 = re.findall(self.pattern3, current_line) #base64_decode
                p13 = re.findall(self.pattern12, current_line) #gzinflate
                p14 = re.findall(self.pattern5, current_line) #eval
                p15 = re.findall(self.pattern15, current_line)
                #print()
                #print(p15)
                if p11 and len(current_line) > 700:
                    p11.append("long_line")
                    p11.append(len(current_line))
                    susp = True 
                    break
                if len(p15)>10 and len(current_line) > 1000:
                    susp = True 
                    break

                if len(p10) > 15:
                    susp = True
                    break
                if p11 and p13 and p14:
                    #print(p12, p13, p14)
                    susp = True
                    break

        # Test this p1 tested. Test the others
        if (len(p1) > 10) or (len(p2) > 10) or  (p3 and p4 and p5) or (len(p8)>10) or (susp) or (len(p4)>15) or len(p15)>10:
            pf_obj.suspicious_tags.append("OBF")
            pf_obj.extracted_results["OBF"] = [p1,p2,p3, p4,p5,p6,p7,p8,p10,p11, p12,p13,p14, p15]
        elif p6:
            if ((len(p6[0]) > 25) and (len(p6) > 30 ) and (len(p5)>0) and (len(p7)==0)):
                pf_obj.suspicious_tags.append("OBF")
                pf_obj.extracted_results["OBF"] = [p1,p2,p3, p4,p5,p6,p7,p8,p10, p11,p12,p13,p14, p15]
        else:
            if "OBF" in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.remove("OBF")
    
        


if __name__=='__main__':  # for debug only
  path.insert(0, '/home/cyfi/Documents/mal_framework')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')
  with open(pf_obj.filepath, 'r', errors="ignore") as f:
    r_data = f.read()

  analysis = Analysis_Obf_Plugin()
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
