from varsfile import *
from sys import argv, path
from base_analysis_class import BaseAnalysisClass
from base_class import Plugin , PluginFile
import re
import subprocess
import json
import time
import pickle
import IPython
import os

class Analysis_Cryptominer(BaseAnalysisClass):
    def __init__(self):
        self.pattern1 = re.compile(r'file_get_contents.*hxxp')
        self.pattern4 = re.compile(r'file_get_contents.*http')
        self.pattern2 = re.compile(r'file_put_contents')
        self.pattern3 = re.compile(r'chmod 0777')
        self.crypto_list = [
                            "Multios.Coinminer.Miner",
                            "BitCoinMiner-HE",
                            "Linux.Application.CoinMiner"
                           ]

    def reprocessFile(self, pf_obj, r_data):
        # Check if file contents are obfuscated
        p1 = re.findall(self.pattern1, r_data)
        p2 = re.findall(self.pattern2, r_data)
        p3 = re.findall(self.pattern3, r_data)
        p4 = re.findall(self.pattern4, r_data)

        # Test this p1 tested. Test the others
        if (p1 and p2 and p3) or (p4 and p2 and p3):
            pf_obj.suspicious_tags.append("CRYPTO")
        else:
            if "CRYPTO" in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.remove("CRYPTO")

        # Known binary names
        if any(plg_name in pf_obj.filepath for plg_name in self.crypto_list):
            pf_obj.suspicious_tags.append("CRYPTO_BIN")
        else:
            if "CRYPTO_BIN" in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.remove("CRYPTO_BIN")
    
if __name__=='__main__':  # for debug only
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')
  with open(pf_obj.filepath, 'r', errors="ignore") as f:
    r_data = f.read()

  analysis = Analysis_Cryptominer()
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
