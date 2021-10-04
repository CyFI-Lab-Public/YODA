from base_analysis_class import BaseAnalysisClass
from sys import argv, path
import json, subprocess, os

class Analysis_API_Abuse(BaseAnalysisClass):
  def __init__(self):
    self.parser_cmd = [                                                  # Parser Command
                        'php', '-f',
                        './analysis_passes/api_parser.php'
                      ]

  def reprocessFile(self, pf_obj, lines=None):
    if 'php' not in pf_obj.mime_type:                               # only process if PHP
      return
    
    elif pf_obj.ast is None:                               # can't process without an AST
      return

    else:                                                              # Detect API Abuse
      try:                                                                   # Run Parser
        api_parser = subprocess.Popen(
                                      self.parser_cmd, 
                                      stdout = subprocess.PIPE, 
                                      stdin  = subprocess.PIPE,
                                      stderr = subprocess.PIPE,
                                    )
                                    
        api_out, api_err = api_parser.communicate(pf_obj.ast)  # send AST over stdin pipe

      except subprocess.CalledProcessError:                        # Something went wrong
        return

      if api_err:
        #print("ERR")
        #print(api_err.decode())
        #print()
        return
      elif api_out:
        api_out = json.loads(api_out.decode('utf-8'))
      else:
        return

      #print("API OUT")
      #print()
      #print(json.dumps(api_out, indent=2)) # debug
      #print()
    
      # Process API_Parser Output:
      if len(api_out['disable_plugins']):                                # Disabling Plugins
        if 'DISABLE_ALL_PLUGINS' not in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.append('DISABLE_ALL_PLUGINS')
        pf_obj.extracted_results.update({'DISABLE_ALL_PLUGINS':api_out['disable_plugins']})
      else:
        if 'DISABLE_ALL_PLUGINS' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('DISABLE_ALL_PLUGINS')

      if len(api_out['user_enum']):                            # User (Admin) Enumeration
        if 'USER_ENUM' not in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.append('USER_ENUM')
        pf_obj.extracted_results.update({'USER_ENUM':api_out['user_enum']})
      else:
        if 'USER_ENUM' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('USER_ENUM')

      if len(api_out['post_insert']) >= 6:                            # Malicious Post Insert
        funcs = set()
        for l_item in api_out['post_insert']:
          funcs.add(l_item.split(":")[1])
        if len(funcs) >= 6:  
          if 'POST_INSERT' not in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.append('POST_INSERT')
            pf_obj.extracted_results.update({'POST_INSERT':api_out['post_insert']})
        else:
          if 'POST_INSERT' in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.remove('POST_INSERT')
      else:
        if 'POST_INSERT' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('POST_INSERT')

      if len(api_out['spam_down']) >= 11:                            # Spam + downloader
        funcs = set()
        for l_item in api_out['spam_down']:
          funcs.add(l_item.split(":")[1])
        if len(funcs) >= 11:  
          if 'SPAM_DOWN' not in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.append('SPAM_DOWN')
            pf_obj.extracted_results.update({'SPAM_DOWN':api_out['spam_down']})
        else:
          if 'SPAM_DOWN' in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.remove('SPAM_DOWN')
      else:
        if 'SPAM_DOWN' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('SPAM_DOWN')

      if len(api_out['user_insert']):                             # User (Admin) Creation
        if 'USER_INSERT' not in pf_obj.suspicious_tags:
          #print("PNAME", pf_obj.plugin_name)
          if pf_obj.plugin_name not in ['Elegant Themes Support', 'InsideOut Solutions Hosting Extras', 'stability', 'Superadmin', 'Pirate Parrot']:
            pf_obj.suspicious_tags.append('USER_INSERT')
            pf_obj.extracted_results.update({'USER_INSERT':api_out['user_insert']})
      else:
        if 'USER_INSERT' in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.remove('USER_INSERT')

      if len(api_out['check4get']):                              # Check for GET function
        if 'CHECK_FOR_GET' not in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.append('CHECK_FOR_GET')
        pf_obj.extracted_results.update({'CHECK_FOR_GET':api_out['check4get']})
      else:
        if 'CHECK_FOR_GET' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('CHECK_FOR_GET')

      if len(api_out['fake_plugin']) >= 2:                        # Fake Plugin Functions
        if 'FAKE_FUNCTIONS' not in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.append('FAKE_FUNCTIONS')
        pf_obj.extracted_results.update({'FAKE_FUNCTIONS':api_out['fake_plugin']})
      else:
        if 'FAKE_FUNCTIONS' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('FAKE_FUNCTIONS')
    
      if len(api_out['user_backdoor']) >= 6:         # User Info Based Backdoor Functions
        funcs = set()
        for l_item in api_out['user_backdoor']:
          funcs.add(l_item.split(":")[1])
        if len(funcs) >= 6:  
          if 'USER_INFO_BASED_BACKDOOR' not in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.append('USER_INFO_BASED_BACKDOOR')
          pf_obj.extracted_results.update({'USER_INFO_BASED_BACKDOOR':api_out['user_backdoor']})
        else:
          if 'USER_INFO_BASED_BACKDOOR' in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.remove('USER_INFO_BASED_BACKDOOR')
      else:
        if 'USER_INFO_BASED_BACKDOOR' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('USER_INFO_BASED_BACKDOOR')

if __name__=='__main__':  # for debug only
  path.insert(0, '/media/ranjita/workspace/cms-defense')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST PLUGIN')

  try:    # Generate AST for Analysis Pass
    get_ast = ['php', '-f', './analysis_passes/generateAST.php', pf_obj.filepath]
    pf_obj.ast = subprocess.check_output(get_ast)
  except Exception:
    pass

  analysis = Analysis_API_Abuse()
  analysis.reprocessFile(pf_obj)

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
