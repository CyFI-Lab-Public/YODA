import json
import os
from utils import file_helpers
import shutil

deob_dir = '/home/brian/deob_samples_12-11-19'
mal_dir = '/home/brian/webshell_mal'

# Get files
files = os.listdir(deob_dir)
files = [file for file in files if 'original' not in file]
files = [file for file in files if '.json' not in file]

sinks = ['system', 'exec', 'eval', 'shell_exec', 'passthru', 'proc_open', 'preg_replace']

results = {}
i = 0
for file in files:
    if i == 50:
        break
    # Read file
    file_contents = file_helpers.read_file(os.path.join(deob_dir, file))

    # If any sinks are in file, run prog
    if any(sink in file_contents for sink in sinks):
        shutil.copy(os.path.join(deob_dir, file), os.path.join(mal_dir, file))
        i += 1
