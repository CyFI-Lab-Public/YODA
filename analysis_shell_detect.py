from base_analysis_class import BaseAnalysisClass
import hashlib
import subprocess
import os
import utils
import copy
from webshell_progpilot.webshell_prog import WebshellProgRunner
from sys import argv, path
import json

class Analysis_Shell_Detect(BaseAnalysisClass):
    def __init__(self):
        self.tag = 'shell_detect'
        self.fingerprints = []
        self.sensitive_funcs = [' system(', 'exec(', 'shell_exec(', 'proc_open(', 'popen(', 'eval(']
        #self.sensitive_funcs = ['system(', 'exec(', 'shell_exec(', 'passthru(', 'proc_open(', 'popen(', 'extract(', 'eval(']
        self.collects_data = True
        self.prog_runner = WebshellProgRunner()

        # Load in webshell hashes
        #hash_path = os.path.abspath('./analysis/shell_detection/hashes.db')
        #with open('./analysis/shell_detection/hashes.db', encoding='utf-8') as hash_file:
        #    line = hash_file.readline()

        #    while line:
        #        parsed = line.split(',')
        #        # Each line has a hash and the name of the webshell
        #        self.fingerprints.append({'hash': parsed[0], 'name': parsed[1]})
        #        line = hash_file.readline()

        # Setup results
        self.results = {}

    def processWebsite(self, website_object):
        pass

    def processCommit(self, commit_object):
        pass

    def reprocessFile(self, pf_obj, r_data):
        file_hash = None
        file_content = r_data

        #file_hash = utils.hash_file_contents(file_content)

        potential_shell = {'type': []}
        # Check if any fingerprints match
        #for fingerprint in self.fingerprints:
        #    if file_hash == fingerprint['hash']:
        #        potential_shell['path'] = pf_obj.filepath
        #        potential_shell['db_name'] = fingerprint['name']
        #        potential_shell['type'].append('fingerprint')
        #        pf_obj.suspicious_tags.append('SHELL_KNOWN_HASH')

        shell_funcs = False
        
        #for func in self.sensitive_funcs:
        #    if func in file_content:
        #        print("SENSITIVE FUNC", func)

        # Check for sensitive funcs
        if any(func in file_content for func in self.sensitive_funcs):
            info = {'path': pf_obj.filepath, 'type': 'sensitive_funcs'}
            potential_shell['path'] = pf_obj.filepath
            potential_shell['type'].append('sensitive_funcs')
            #print(potential_shell['type'])
            shell_funcs = True
        else:
            if shell_funcs:
                if "SHELL_PROG" in pf_obj.suspicious_tags:
                    pf_obj.suspicious_tags.remove("SHELL_PROG")

        # Use progpilot to see if it is shell
        # Only run if there are any sensitive functions, progpilot only looks for those sinks
        if shell_funcs: 
            did_timeout = False
            try:
                prog_results = self.prog_runner.run(file_contents=file_content)
            except subprocess.TimeoutExpired:
                did_timeout = True

            if not did_timeout and len(prog_results) > 0:
                if pf_obj.plugin_name not in ['SEO Power', 'TNG Wordpress Integration', 'ManageWP - Worker', 's2Member Framework', 'Sermon Browser', 'ThemePortal']:
                    oput = []
                    for res in prog_results:
                        #print(res['source_name'][0], res['sink_name'])
                        o = []
                        o.append(res['source_name'][0]) 
                        o.append(res['sink_name'])
                        #if res['sink_name'] == 'eval':
                        #    #if res['source_name'][0].startswith("$_") or "base64" in res['source_name'][0] or "gzinflate" in res['source_name'][0]:
                        #        oput.append(o)
                        #else:
                        #    oput.append(o)
                        if res['sink_name'] in ['query', 'view']:
                           pass 
                        else:
                            oput.append(o)
                    if oput:
                        pf_obj.suspicious_tags.append('SHELL_PROG')
                        pf_obj.extracted_results["shell"] = copy.deepcopy(oput)
            else:
                if "SHELL_PROG" in pf_obj.suspicious_tags:
                    pf_obj.suspicious_tags.remove("SHELL_PROG")


    def postProcessCommit(self, commit_obj):
        pass
if __name__=='__main__':  # for debug only
  path.insert(0, '/media/ranjita/workspace/cms-defense/')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')

  with open(pf_obj.filepath, 'r', errors="ignore") as f:
    r_data = f.read()

  SI = Analysis_Shell_Detect()
  SI.reprocessFile(pf_obj, r_data)

  print('Plugin File Object:')
  print('------------------------------------------')
  print('Plugin Name: {}'.format(pf_obj.plugin_name))
  print('State:       {}'.format(pf_obj.state))
  print('Mime Type:   {}'.format(pf_obj.mime_type))
  print('Tags:        {}'.format(pf_obj.suspicious_tags))
  print('Malicious:   {}'.format(pf_obj.is_malicious))
  print('Results:\n{}'.format(json.dumps(pf_obj.extracted_results, indent=2)))
  print()
