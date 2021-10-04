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

class Analysis_Blacklist(BaseAnalysisClass):
    def __init__(self):
        self.p1 = re.compile(r'SI CAPTCHA Anti-Spam', re.IGNORECASE)
        self.p2 = re.compile(r'Fast Secure Contact Form', re.IGNORECASE)
        self.p3 = re.compile(r'Fast Secure reCAPTCHA', re.IGNORECASE)
        self.p4 = re.compile(r'Visitor Maps and Who\'s Online', re.IGNORECASE)
        self.p5 = re.compile(r'WP-Base-SEO', re.IGNORECASE)
        self.p6 = re.compile(r'404 to 301', re.IGNORECASE)
        self.p7 = re.compile(r'WP Slimstat', re.IGNORECASE)
        self.p8 = re.compile(r'WP Maintenance Mode', re.IGNORECASE)
        self.p9 = re.compile(r'NewStatPress', re.IGNORECASE)
        self.p10 = re.compile(r'Menu Image', re.IGNORECASE)
        self.p11 = re.compile(r'Image Slider Widget', re.IGNORECASE)
        self.p12 = re.compile(r'No Comments', re.IGNORECASE)
        self.p13 = re.compile(r'Sweet Captcha', re.IGNORECASE)
        self.p14 = re.compile(r'Duplicate Page And Post', re.IGNORECASE)
        self.p15 = re.compile(r'No Follow All External Links', re.IGNORECASE)
        self.p16 = re.compile(r'WP No External Links', re.IGNORECASE)
        self.p17 = re.compile(r'Adsense High CPC', re.IGNORECASE)
        self.p18 = re.compile(r'WP-reCAPTCHA', re.IGNORECASE)
        self.p19 = re.compile(r'Social Media Widget', re.IGNORECASE)


        # Versions
        self.wp_slimstat_vers = ["3.4", "3.5", "3.6", "3.7", "3.8", "3.9", "4.0", "4.1", "4.2", "4.3"]
        self.wp_mmode_vers = ["1.8.9", "1.8.10", "1.8.11", "2.0.0"]
        self.ns_press_vers = ["0.6.2", "0.6.3", "0.6.4", "0.6.5", "0.6.6", "0.6.7"]
        self.mimage_vers = ["2.6.4", "2.6.5" , "2.6.6", "2.6.7", "2.6.8", "2.6.9", "2.7.0"]
        self.no_comm_vers = ["1.1.5", "1.1.6", "1.2"]
        self.dpp_vers = ["2.1.0", "2.1.1"]
        self.nfael_vers = ["2.1", "2.2", "2.3"]
        self.cap_vers = ["4.3.6", "4.3.7", "4.3.8", "4.3.9", "4.4.0", "4.4.1", "4.4.2", "4.4.3", "4.4.4"]
        pass

    def reprocessFile(self, pf_obj, r_data):
        # Display Widgets
        if "Display Widgets" in pf_obj.plugin_name and pf_obj.version.startswith("2.6"):
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "Display Widgets"
        # SI Captcha
        elif re.findall(self.p1, pf_obj.plugin_name):
            if pf_obj.version.startswith("3.0.1") or pf_obj.version.startswith("3.0.2"):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "SI CAPTCHA Anti-Spam"
        # Fast Secure Contact Form
        elif re.findall(self.p2, pf_obj.plugin_name):
            if pf_obj.version.startswith("4.0.52") or pf_obj.version.startswith("4.0.53") or \
               pf_obj.version.startswith("4.0.54") or pf_obj.version.startswith("4.0.55"):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "Fast Secure Contact Form"
        # Fast Secure reCAPTCHA 
        elif re.findall(self.p3, pf_obj.plugin_name):
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "Fast Secure reCAPTCHA"
        # Visitor Maps and Who's Online
        elif re.findall(self.p4, pf_obj.plugin_name):
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "Visitor Maps and Who\'s Online"
        # WP-Base-SEO
        elif re.findall(self.p5, pf_obj.plugin_name) and "FUNCTION_CONSTRUCTION" in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "WP-Base-SEO"
        # 404 to 301
        elif re.findall(self.p6, pf_obj.plugin_name) and pf_obj.version.startswith("2.2."):
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "404 to 301"
        # WP Slimstat
        elif re.findall(self.p7, pf_obj.plugin_name):
            if any(pf_obj.version.startswith(ver) for ver in self.wp_slimstat_vers):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "WP Slimstat"
        # WP Maintenance Mode
        elif re.findall(self.p8, pf_obj.plugin_name):
            if any(pf_obj.version.startswith(ver) for ver in self.wp_mmode_vers):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "WP Maintenance Mode"
        # NewStatPress 
        elif re.findall(self.p9, pf_obj.plugin_name):
            if any(pf_obj.version.startswith(ver) for ver in self.ns_press_vers):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "NewStatPress"
        # Menu Image 
        elif re.findall(self.p10, pf_obj.plugin_name):
            if any(pf_obj.version.startswith(ver) for ver in self.mimage_vers):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "Menu Image"
        # Weptile Image Slider Widget
        elif re.findall(self.p11, pf_obj.plugin_name):
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "Image Slider Widget / Weptile Image Slider Widget"
        # No Comments 
        elif re.findall(self.p12, pf_obj.plugin_name):
            if any(pf_obj.version.startswith(ver) for ver in self.no_comm_vers):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "No Comments"
        # Sweet Captcha
        elif re.findall(self.p13, pf_obj.plugin_name) or "/jumpple/" in pf_obj.filepath:
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "Sweet Captcha"
        # Duplicate Page And Post 
        elif re.findall(self.p14, pf_obj.plugin_name):
            if any(pf_obj.version.startswith(ver) for ver in self.dpp_vers):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "Duplicate Page And Post"
        # No Follow All External Links 
        elif re.findall(self.p15, pf_obj.plugin_name):
            if any(pf_obj.version.startswith(ver) for ver in self.nfael_vers):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "No Follow All External Links"
        # WP No External Links 
        elif re.findall(self.p16, pf_obj.plugin_name):
            if pf_obj.version.startswith("4.2"):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "WP No External Links"
        # Adsense_high_CPC.v2.0.5 
        elif re.findall(self.p17, pf_obj.plugin_name) or "Adsense_high_CPC.v2.0.5" in pf_obj.filepath:
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "Adsense High CPC"
        # WP-reCAPTCHA 
        elif re.findall(self.p18, pf_obj.plugin_name):
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "WP-reCAPTCHA"
        # Social Media Widget 
        elif re.findall(self.p19, pf_obj.plugin_name) and pf_obj.version.startswith("4.0"):
            pf_obj.suspicious_tags.append("KNOWN_MAL")
            pf_obj.extracted_results["KNOWN_MAL"] = "Social Media Widget"
        # Captcha
        elif pf_obj.plugin_name == "Captcha":
            if any(pf_obj.version.startswith(ver) for ver in self.cap_vers):
                pf_obj.suspicious_tags.append("KNOWN_MAL")
                pf_obj.extracted_results["KNOWN_MAL"] = "Captcha"
        else:
            if "KNOWN_MAL" in pf_obj.suspicious_tags:
                pf_obj.suspicious_tags.remove("KNOWN_MAL")
    
        


