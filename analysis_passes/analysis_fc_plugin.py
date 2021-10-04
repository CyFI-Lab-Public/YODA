from base_analysis_class import BaseAnalysisClass
from sys import argv, path, stderr, getsizeof, stdout
import json, subprocess, os

class Analysis_FC_Plugin(BaseAnalysisClass):
  def __init__(self):
    self.parser_cmd = [                                                  # Parser Command
                        'php', '-f',
                        './analysis_passes/fc_parser.php'
                      ]          
    self.skip_files = [
                        '/date/date_api/date_api.module'
                        '/phpseclib/Net/SSH2.php'
                      ]

    self.whitelist = [
                        "radium-importer.php",
                        "yellow-pencil.php",
                        "ot-functions-admin.php",
                        "option_table_export.php",
                        "option-tree",
                        "dental-care",
                        "nanosoft"
                      ]

    self.whitelist_funcs = [
                            "ot_decode", 
                            "optiontree_decode", 
                            "alchem_decode", 
                            "yp_decode"
                            ]

  def reprocessFile(self, pf_obj, r_data):
    if any(string in pf_obj.filepath for string in self.whitelist):
      return

    if any(string in r_data for string in self.whitelist_funcs):
      return

    if 'php' not in pf_obj.mime_type:                               # only process if PHP
      return
    
    elif pf_obj.ast is None:                               # can't process without an AST
      return

    else:                                                  # Detect Function Construction
      
      for skip in self.skip_files:                         # but first check if skip_file
        if skip in pf_obj.filepath:
          return


      try:                                                                   # Run Parser
        fc_parser = subprocess.Popen(
                                      self.parser_cmd,
                                      stdout = subprocess.PIPE,
                                      stdin  = subprocess.PIPE,
                                      stderr = subprocess.PIPE,
                                    )
                                    
        fc_out, fc_err = fc_parser.communicate(                # send AST over stdin pipe
                                                input=pf_obj.ast,
                                                timeout=5*60              # 5 min timeout
                                              )

      except subprocess.CalledProcessError:                        # Something went wrong
        return
      except subprocess.TimeoutExpired:
        fc_parser.terminate()
        return

      if fc_err:
        return
      elif fc_out:
        fc_out = json.loads(fc_out.decode('utf-8'))
      else:
        return

      # print()
      # print(json.dumps(fc_out, indent=2)) # debug
      # print()
      
      fc = False

      # process FC_Parser Output
      if (len(fc_out['constructed']) > 0) and fc_out['progpilot']:
        for result in fc_out['progpilot']:
          for func in fc_out['constructed']:
            if 'source_name' in result:
              if func in result['source_name']:
                fc = True
            if 'sink_name' in result:
              if func in result['sink_name']:
                fc = True
            if 'tainted_flow' in result:
              for taint in result['tainted_flow']:
                for t in taint:
                  if (func+'_return') in t['flow_name']:
                    fc = True

        if fc:                   # functions were constructed and progpilot found a taint
          if 'FUNCTION_CONSTRUCTION' not in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.append('FUNCTION_CONSTRUCTION')
          pf_obj.extracted_results.update({'FUNCTION_CONSTRUCTION':fc_out['constructed']})
        else:
          if 'FUNCTION_CONSTRUCTION' in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.remove('FUNCTION_CONSTRUCTION')

if __name__=='__main__':  # for debug only
  path.insert(0, '/media/ranjita/workspace/cms-defense')
  from base_class import PluginFile
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')

  with open(pf_obj.filepath, 'r', errors="ignore") as f:
    r_data = f.read()

  try:    # Generate AST for Analysis Pass
    get_ast = ['php', '-f', './analysis_passes/generateAST.php', pf_obj.filepath]
    pf_obj.ast = subprocess.check_output(get_ast)
  except Exception:
    pass

  FC = Analysis_FC_Plugin()
  FC.reprocessFile(pf_obj, r_data)

  print('Plugin File Object:')
  print('------------------------------------------')
  print('Plugin Name: {}'.format(pf_obj.plugin_name))
  print('State:       {}'.format(pf_obj.state))
  print('Mime Type:   {}'.format(pf_obj.mime_type))
  print('Tags:        {}'.format(pf_obj.suspicious_tags))
  print('Malicious:   {}'.format(pf_obj.is_malicious))
  print()
