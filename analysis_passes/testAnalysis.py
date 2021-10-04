#!/bin/python3

import json
import subprocess
import sys
import os

analysis = sys.argv[1]
_file = sys.argv[2]

generate = "php -f generateAST.php {}".format(_file)
subprocess.run(generate, shell=True)

ast_path = os.path.join('./ast_cache/', os.path.basename(_file)) + '.ast'

analysis_pass = 'php -f {}_parser.php {}'.format(analysis, ast_path)
subprocess.run(analysis_pass, shell=True)

# print(generate)
# print(analysis_pass)

