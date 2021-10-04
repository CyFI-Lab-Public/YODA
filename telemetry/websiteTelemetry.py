#!/bin/python3

from Telemetry import TelemetryScanner
import os, json, multiprocessing
import contextlib, sys

class DummyFile(object):
    def write(self, x): pass

@contextlib.contextmanager
def nostdout():
    save_stdout = sys.stdout
    sys.stdout = DummyFile()
    yield
    sys.stdout = save_stdout
### ^ silence TelemetryScanner.run()'s print statements - from stack overflow 

def get_FW_results(website_id):
  results_file = '../results/{}.json'.format(website_id)

  with open(results_file, 'r') as rFile:
    results = rFile.read()
  jData = json.loads(results)

  return jData

def TelemetryScans(plugin):
  slug = plugin[0]
  name = plugin[1]

  print('Telemetry Scan for: {}'.format(name))

  TS = TelemetryScanner()
  with nostdout():
    plugin_telemetry = TS.run(slug)
  # print()
  # print('--------------------------------------------------')
  # print()

  return {name:plugin_telemetry}

def WebsiteTelemetry(site_id):
  report_file = 'website_telemetry/{}.json'.format(site_id)
  slugs = []
  names = []

  results = get_FW_results(site_id)
  commits = results['c_ids']

  for commit in commits:
    commit_plugins = results['plugin_info'][commit]['plugins']
    
    for plugin in commit_plugins:
      plugin_path = results['plugin_info'][commit]['plugins'][plugin]['base_path']
      slug = os.path.basename(os.path.normpath(plugin_path))
      if slug not in slugs:
        slugs.append(slug)
      if plugin not in names:
        names.append(plugin)

  p = multiprocessing.Pool(multiprocessing.cpu_count())
  tData = p.map(TelemetryScans, zip(slugs, names))

  # print(json.dumps(tData, indent=2))

  if not os.path.exists('website_telemetry/'):
    os.makedirs('website_telemetry')
  with open(report_file, 'w') as outfile:
    json.dump(tData, outfile)
  print('Telemetry Report written to {}'.format(report_file))

  print('Telemetry Scan Complete')
  p.close()

def batchScan():
  results_dir = '../results/'
  files = [f for f in os.listdir(results_dir) if os.path.isfile(os.path.join(results_dir, f))]
  jsons = [f[:-5] for f in files if '.json' in f]

  for site in jsons:
    print('--------------------------------------------------')
    print('Running Telemetry on {}... '.format(site), end='')
    WebsiteTelemetry(site)
    print('Done')
    print('--------------------------------------------------')

if __name__=='__main__':
  WebsiteTelemetry(sys.argv[1])