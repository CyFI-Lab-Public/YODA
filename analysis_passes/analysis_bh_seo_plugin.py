from base_analysis_class import BaseAnalysisClass
from sys import argv, path
from vt import *
import json, subprocess
from urllib.parse import urlparse
path.insert(0, '/media/ranjita/workspace/cms-defense/')
from malicious_urls import *
from clean_urls import *

class Analysis_BlackhatSEO_Plugin(BaseAnalysisClass):
  def __init__(self):
    self.parser_cmd = [                                                  # Parser Command
                        'php', '-f',
                        './analysis_passes/bs_parser.php'
                      ]
    self.analyzed_links = {}

  def reprocessFile(self, pf_obj, lines=None):
    if 'php' not in pf_obj.mime_type:                               # only process if PHP
      return
    else:                                                           # Detect Blackhat SEO
      try:                                                                   # Run Parser
        bs_parser = subprocess.Popen(
                                      self.parser_cmd, 
                                      stdout=subprocess.PIPE, 
                                      stdin=subprocess.PIPE
                                    )
        bs_out, bs_err = bs_parser.communicate(pf_obj.ast)

      except subprocess.CalledProcessError as e:                   # Something went wrong
        print("ERROR:", e, "while parsing file", pf_obj.filepath)

      if bs_err:
        return
      elif bs_out:
        bs_out = bs_out.decode('utf-8')
      else:
        return

      detected_links = None
      if len(bs_out):
        bs_out = json.loads(bs_out)     
        if bs_out['detected'] == "True":
          detected_links = bs_out['detected_links']
      
      if detected_links is not None:
        vt_results = {}
        for link in detected_links:
            valid_url = False
            #print("LINK", link)
            url_link  = link['URL']
            #print("LINK", url_link)

            url_link = url_link.strip('"')
            url_link = url_link.strip("'")
            https = ['https://', 'http://', 'hxxp://', 'httx://']
            for htt in https:
                if htt in url_link: 
                    if url_link.startswith(htt):
                        valid_url = True
                        break 
                    else:
                        url_link = htt + url.split(htt,1)[1]
                    valid_url = True

            if valid_url:
                #print("VALID", url_link)
                p = urlparse(url_link)
                if not p[0] or not p[1]:
                    s = url_link.split("/")
                    domain = s[0] + "/" + s[1] + "/" + s[2] +"/"
                elif (not p[0]) and (not p[1]):
                    domain = ""
                else:
                    domain = p[0] + "://" + p[1]
                
                #if str(domain) not in self.analyzed_links:
                    #print("DOMAIN", str(domain))

                # Analyze only the Domain on VT
                if domain:
                    #print("IFDOMAIN", str(domain))
                    # If URL is clean, don't run VT scan
                    for c_url in c_urls:
                        #print("C_URL", c_url, domain)
                        if c_url in domain:
                            domain = "" 
                            break

                    if domain:
                        # Else run VT Scan        
                        if str(domain) in m_urls:
                            vt_results[str(url_link)] = "Known Malicious"
                        elif str(domain) not in self.analyzed_links:
                            res = run_VT_scan(str(domain))
                            self.analyzed_links[str(domain)] = res
                            #print("VT RES", res)
                            if res:
                                vt_results[str(url_link)] = res
                        else:
                            if self.analyzed_links[domain] in ["GET_REPORT_FAIL", "SCAN_FAIL"]:
                                res = run_VT_scan(str(domain))
                                self.analyzed_links[str(domain)] = res
                                if res:
                                    vt_results[str(url_link)] = res

                            if self.analyzed_links[str(domain)]:
                                vt_results[str(url_link)] = self.analyzed_links[str(domain)]

        if  vt_results:
            del_links = [] 
            for link in vt_results:
                # Invalid URL cases remove
                if 'results' in vt_results[link]:
                    if "Invalid" in vt_results[link]['results']['verbose_msg']:
                        del_links.append(link)
                        continue
            for link in del_links:
                del vt_results[link]
        if vt_results:
            categorize_later = False
            for url in vt_results:
                if "results" in vt_results[url]:
                    categorize_later = True

            if 'SEO' not in pf_obj.suspicious_tags and not categorize_later:
                pf_obj.suspicious_tags.append('SEO')
                pf_obj.extracted_results.update({'SEO': vt_results})
            elif  categorize_later:
                if 'MAYBE_SEO' not in pf_obj.suspicious_tags:
                    pf_obj.suspicious_tags.append('MAYBE_SEO')
                    pf_obj.extracted_results.update({'MAYBE_SEO':vt_results})
        else:
          if 'SEO' in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.remove('SEO')
          if 'MAYBE_SEO' in pf_obj.suspicious_tags:
            pf_obj.suspicious_tags.remove('MAYBE_SEO')

if __name__=='__main__':  # debug
  #path.insert(0, '/home/cyfi/mal_framework/')
  path.insert(0, '/media/ranjita/workspace/cms-defense')
  from base_class import PluginFile
  from mal_urls import *
  pf_obj = PluginFile(argv[1], 'A', ['php'], 'TEST_PLUGIN')

  try:    # Generate AST for Analysis Passes
    get_ast = ['php', '-f', './analysis_passes/generateAST.php', pf_obj.filepath]
    pf_obj.ast = subprocess.check_output(get_ast)
    
  except Exception as e:
    pass

  BS = Analysis_BlackhatSEO_Plugin()
  BS.reprocessFile(pf_obj)

  print('Plugin File Object:')
  print('------------------------------------------')
  print('Plugin Name: {}'.format(pf_obj.plugin_name))
  print('State:       {}'.format(pf_obj.state))
  print('Mime Type:   {}'.format(pf_obj.mime_type))
  print('Tags:        {}'.format(pf_obj.suspicious_tags))
  print('Malicious:   {}'.format(pf_obj.is_malicious))
  print('Malicious:   {}'.format(pf_obj.extracted_results))
  print()
