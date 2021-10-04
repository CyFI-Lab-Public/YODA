from base_analysis_class import BaseAnalysisClass
from sys import argv, path
import json, subprocess

class Analysis_Spam_Plugin(BaseAnalysisClass):
  def __init__(self):
    self.parser_cmd = [                                                  # Parser Command
                        'php', '-f',
                        './analysis_passes/spam_parser.php'
                      ]   

  def reprocessFile(self, pf_obj, lines=None):
    if 'php' not in pf_obj.mime_type:                               # only process if PHP
      return

    elif pf_obj.ast is None:                               # can't process without an AST
      return

    else:                                                         # Detect Spam Injection
      try:                                                                   # Run Parser
        spam_parser = subprocess.Popen(
                                        self.parser_cmd, 
                                        stdout = subprocess.PIPE, 
                                        stdin  = subprocess.PIPE,
                                        stderr = subprocess.PIPE
                                      )

        spam_out, spam_err = spam_parser.communicate(pf_obj.ast)    # send AST over stdin

      except subprocess.CalledProcessError:                        # Something went wrong
        pass

      if spam_err:
        #print()
        #print(spam_err.decode())
        #print()
        return
      elif spam_out:
        spam_out = json.loads(spam_out.decode('utf-8'))              # Decode JSON result
      else:
        return

      # print()
      # print(json.dumps(spam_out, indent=2))
      # print()
      
      if len(spam_out) > 0:                                      # Did we find any links?
        if 'SPAM_INJECTION' not in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.append('SPAM_INJECTION')
        pf_obj.extracted_results.update({'SPAM_INJECTION':spam_out})
      else:
        if 'SPAM_INJECTION' in pf_obj.suspicious_tags:
          pf_obj.suspicious_tags.remove('SPAM_INJECTION')
      
if __name__=='__main__':  # for debug only
  #path.insert(0, '/home/cyfi/mal_framework/')
  path.insert(0, '/media/ranjita/workspace/cms-defense')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')

  try:    # Generate AST for Analysis Pass
    get_ast = ['php', '-f', './analysis_passes/generateAST.php', pf_obj.filepath]
    pf_obj.ast = subprocess.check_output(get_ast)
    
  except Exception as e:
    pass

  SI = Analysis_Spam_Plugin()
  SI.reprocessFile(pf_obj)

  print('Plugin File Object:')
  print('------------------------------------------')
  print('Plugin Name: {}'.format(pf_obj.plugin_name))
  print('State:       {}'.format(pf_obj.state))
  print('Mime Type:   {}'.format(pf_obj.mime_type))
  print('Tags:        {}'.format(pf_obj.suspicious_tags))
  print('Malicious:   {}'.format(pf_obj.is_malicious))
  print('Results:\n{}'.format(json.dumps(pf_obj.extracted_results, indent=2)))
  print()
