from base_analysis_class import BaseAnalysisClass
from sys import argv, path, stderr
import json, subprocess, os

class Analysis_Err_Report(BaseAnalysisClass):
  def __init__(self):
    self.parser_cmd = [
                        'php', '-f',
                        './analysis_passes/err_parser.php'
                      ]

  def reprocessFile(self, pf_obj, r_data=None):
    if 'php' not in pf_obj.mime_type:                               # only process if PHP
      return
  
    elif pf_obj.ast is None:                               # can't process without an AST
      return

    else:                                                        # Detect Error Disabling
      try:                                                                   # Run Parser
        err_parser = subprocess.Popen(
                                        self.parser_cmd,
                                        stdout = subprocess.PIPE,
                                        stdin  = subprocess.PIPE,
                                        stderr = subprocess.PIPE,
                                     )
                                    
        ep_out, ep_err = err_parser.communicate( input=pf_obj.ast ) # send AST over stdin

      except subprocess.CalledProcessError:                        # Something went wrong
        pass

      if ep_err:
        return
      elif ep_out:
        ep_out = json.loads(ep_out.decode('utf-8'))
      else:
        return

      # print()
      # print(ep_out)
      # print()

      if len(ep_out) > 0:
        if 'ERR_OFF' not in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.append('ERR_OFF')
        pf_obj.extracted_results.update({'ERR_OFF':ep_out})
      else:
        if 'ERR_OFF' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('ERR_OFF')
      
if __name__=='__main__':  # for debug only
  path.insert(0, '/home/cyfi/mal_framework')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')

  try:    # Generate AST for Analysis Pass
    get_ast = ['php', '-f', './analysis_passes/generateAST.php', pf_obj.filepath]
    pf_obj.ast = subprocess.check_output(get_ast)
  except Exception:
    pass

  EP = Analysis_Err_Report()
  EP.reprocessFile(pf_obj)

  print('Plugin File Object:')
  print('------------------------------------------')
  print('Plugin Name: {}'.format(pf_obj.plugin_name))
  print('State:       {}'.format(pf_obj.state))
  print('Mime Type:   {}'.format(pf_obj.mime_type))
  print('Tags:        {}'.format(pf_obj.suspicious_tags))
  print('Malicious:   {}'.format(pf_obj.is_malicious))
  print('Extracted Results')
  print(json.dumps(pf_obj.extracted_results, indent=2))
  print()

