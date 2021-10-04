from progpilot import progpilot
import os
from utils import file_helpers
import json
import time

prog_obj = progpilot.Progpilot('webshell_config.yml')
deob_dir = '/home/brian/webshell_mal'

# Get files
files = os.listdir(deob_dir)
files = [file for file in files if 'original' not in file]
files = [file for file in files if '.json' not in file]

sinks = ['system', 'exec', 'eval', 'shell_exec', 'passthru', 'proc_open', 'preg_replace']

results = {}
i = 0
for file in files:
    # Read file
    file_contents = file_helpers.read_file(os.path.join(deob_dir, file))

    # If any sinks are in file, run prog
    result = prog_obj.run_contents(file_contents)

    # Save result
    results[file] = result
    i += 1

with open('webshell_results.json', 'w') as f:
    json.dump(results, f)
