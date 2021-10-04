from base_analysis_class import BaseAnalysisClass
from sys import argv, path
import json, subprocess

class Analysis_Gated_Plugin(BaseAnalysisClass):
  def __init__(self):
    self.parser_cmd = [                                                  # Parser Command
                        'php', '-f'
                        './analysis_passes/gp_parser.php'
                      ]

  def reprocessFile(self, pf_obj, lines=None):
    if 'php' not in pf_obj.mime_type:                               # only process if PHP
      return
    
    elif pf_obj.ast is None:                               # can't process without an AST
      return

    else:                                                          # Detect Gated Plugins
      try:                                                                   # Run Parser
        gp_parser = subprocess.Popen(
                                      self.parser_cmd,
                                      stdout = subprocess.PIPE,
                                      stdin  = subprocess.PIPE,
                                      stderr = subprocess.PIPE
                                    )
        
        gp_out, gp_err = gp_parser.communicate(pf_obj.ast)     # send AST over stdin pipe

      except subprocess.CalledProcessError:                          # Something went wrong
        return

      if gp_err:
        #print(gp_err)
        return
      
      elif gp_out:
        gp_out = json.loads(gp_out.decode('utf-8'))
      else:
        return

      # print()
      # print(json.dumps(gp_out, indent=2))
      # print()

      # check GP_Parser Output
      if len(gp_out['plugin_gates']):
        if 'GATED_PLUGIN' not in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.append('GATED_PLUGIN')
        pf_obj.extracted_results.update({'GATED_PLUGIN':gp_out})
      else:
        if 'GATED_PLUGIN' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('GATED_PLUGIN')

if __name__=='__main__':  # for debug only
  #path.insert(0, '/home/cyfi/mal_framework')
  path.insert(0, '/home/cyfi/mal_framework')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')

  try:    # Generate AST for Analysis Pass
    get_ast = ['php', '-f', './analysis_passes/generateAST.php', pf_obj.filepath]
    pf_obj.ast = subprocess.check_output(get_ast)
  except Exception:
    pass

  GP = Analysis_Gated_Plugin()
  GP.reprocessFile(pf_obj)

  if len(pf_obj.suspicious_tags):
    pf_obj.is_malicious = True

  print('Plugin File Object:')
  print('------------------------------------------')
  print('Plugin Name: {}'.format(pf_obj.plugin_name))
  print('State:       {}'.format(pf_obj.state))
  print('Mime Type:   {}'.format(pf_obj.mime_type))
  print('Tags:        {}'.format(pf_obj.suspicious_tags))
  print('Malicious:   {}'.format(pf_obj.is_malicious))
  print('Extracted Results:')
  print(json.dumps(pf_obj.extracted_results, indent=2))
  print()

