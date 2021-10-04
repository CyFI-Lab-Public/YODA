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

class Analysis_Fake_Blacklist(BaseAnalysisClass):
    def __init__(self):
        self.p1 = re.compile(r'Pingatorpin', re.IGNORECASE)
        self.p2 = re.compile(r'WP-Spam Shield Pro', re.IGNORECASE)
        self.p3 = re.compile(r'X-WP-SPAM-SHIELD-PRO', re.IGNORECASE)
        self.fake_list = [
                "/aciry/",
                "/acismittory/",
                "/Akismet3/",
                "/disable-commenis/",
                "/page-links-mo/",
                "/regenerate-thumbnaius/",
                "/research_plugin_URQe/",
                "/theme-check/",
                "/WPupdate/",
                "/WPupdate1/",
                "/wp-amazing-updater/",
                "/wp-arm-config/",
                "/xcalendar-1/",
                "/xcalendar-2/",
                "/initiatorseo/",
                "/updrat123/",
                "/all-in-one-wp-security-and-firewall/all-in-one-wp-security-and-firewall.php",
                "/ls-oembed/ls-oembed.php",
                "/pluginmonsters/pluginmonsters.php",
                "/pluginsmonsters/pluginsmonsters.php",
                "/pluginsamonsters/pluginsamonsters.php",
                "/wpppm.php",
                "/supersociall/",
                "/blockspluginn/",
                "/wpframework/",
                "/1wpframework/", #https://walkingbyfaithchurch.org/wp-content/plugins/
                "/1groupdocs-assembly/", #https://walkingbyfaithchurch.org/wp-content/plugins/
                "/1tassembly/", #https://walkingbyfaithchurch.org/wp-content/plugins/
                "/LoginWall-XyXYXY/",
                "/research_plugin_",
                "/wpsecurity/"
                "/thesis_/"

        ]
        pass

    def reprocessFile(self, pf_obj, r_data):
        # Pingatorpin
        if re.findall(self.p1, pf_obj.plugin_name) or re.findall(self.p1, pf_obj.filepath): 
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        # WP SPam Shield Pro
        elif re.findall(self.p2, pf_obj.plugin_name) or re.findall(self.p3, pf_obj.plugin_name):
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        # Keyscaptcha
        elif "keyscaptcha/keysfunctions.php" in pf_obj.filepath:
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        # Docs
        elif pf_obj.plugin_name == "Docs":
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        # WordPress Researcher
        elif pf_obj.plugin_name == "WordPress Researcher":
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        # Super Socialat
        elif pf_obj.plugin_name == "Super Socialat" or "/super-socialat/" in pf_obj.filepath:
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        # Plugin Monsters
        elif pf_obj.plugin_name == "pluginsmonsters":
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        # Wordpress Plugin Manager
        elif pf_obj.plugin_name == "Wordpress Plugin Manager":
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        elif pf_obj.plugin_name == "WordPress Framework":
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        # Fake names list
        elif any(plg_name in pf_obj.filepath for plg_name in self.fake_list):
            pf_obj.suspicious_tags.append("FAKE_PLUGIN")
        
        else:
            if "FAKE_PLUGIN" in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.remove("FAKE_PLUGIN")
    
        


if __name__=='__main__':  # for debug only
  path.insert(0, '/home/cyfi/Documents/mal_framework')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')
  with open(pf_obj.filepath, 'r', errors="ignore") as f:
    r_data = f.read()

  analysis = Analysis_Fake_Blacklist()
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
