from base_analysis_class import BaseAnalysisClass
from base_class import Website, Commit, FileMetadata, Plugin, PluginFile 
from sys import argv, path
import json, subprocess, os

class Analysis_Covid_Plugin(BaseAnalysisClass):
  def __init__(self):
    self.parser_cmd = [                                                  # Parser Command
                        'php', '-f',
                        './analysis_passes/covid_parser.php'
                      ]          

  def reprocessFile(self, pf_obj, lines=None):
    if 'php' not in pf_obj.mime_type:                               # only process if PHP
      return
    
    elif pf_obj.ast is None:                               # can't process without an AST
      return

    else:                                                       # Detect COVID-19 Malware
      try:                                                                   # Run Parser
        covid_parser = subprocess.Popen(
                                      self.parser_cmd, 
                                      stdout = subprocess.PIPE, 
                                      stdin  = subprocess.PIPE,
                                      stderr = subprocess.PIPE,
                                    )
                                    
        covid_out, covid_err = covid_parser.communicate(pf_obj.ast) # send AST over stdin

      except subprocess.CalledProcessError:                        # Something went wrong
        return

      if covid_err:
        return
      elif covid_out:
        covid_out = json.loads(covid_out.decode('utf-8'))
      else:
        return

      # print()
      # print(json.dumps(covid_out, indent=2)) # debug
      # print()
      
      covid = False
      if covid_out['WP_CD_CODE'] == True:
        covid = True

      if covid:
        if 'COVID_WP_VCD' not in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.append('COVID_WP_VCD')
        pf_obj.extracted_results.update({'COVID_WP_VCD':covid_out})
      else:
        if 'COVID_WP_VCD' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('COVID_WP_VCD')
      
if __name__=='__main__':  # for debug only
  path.insert(0, '/home/cyfi/mal_framework')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')

  try:    # Generate AST for Analysis Pass
    get_ast = ['php', '-f', './analysis_passes/generateAST.php', pf_obj.filepath]
    pf_obj.ast = subprocess.check_output(get_ast)
  except Exception:
    pass

  Covid = Analysis_Covid_Plugin()
  Covid.reprocessFile(pf_obj)

  print('Plugin File Object:')
  print('------------------------------------------')
  print('Plugin Name: {}'.format(pf_obj.plugin_name))
  print('State:       {}'.format(pf_obj.state))
  print('Mime Type:   {}'.format(pf_obj.mime_type))
  print('Tags:        {}'.format(pf_obj.suspicious_tags))
  print('Malicious:   {}'.format(pf_obj.is_malicious))
  print()
