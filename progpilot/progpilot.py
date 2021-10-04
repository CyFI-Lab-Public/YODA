import json
import subprocess

import os.path
import tempfile
from utils import file_helpers

# from proto.python.module_pb2 import ModuleResult, ModuleSummary, ModuleStatic

package_directory = os.path.dirname(os.path.abspath(__file__))

class Progpilot():
    def __init__(self, config_path='astgen_php_smt.config', prog_exec_path=None):
        self.config_path = config_path
        if prog_exec_path is None:
            # Default to use exec path in current directory
            self.prog_exec_path = os.path.join(package_directory, 'progpilot.phar')
        else:
            self.prog_exec_path = prog_exec_path

    def run(self, filepath, timeout=15):
        """executes the actual progpilot command and returns the output as a JSON object
           timeout is in seconds
           raises a subprocess.TimeoutExpired exception if the call to progpilot times out"""
        completed_proc = subprocess.run(['php',
                                         self.prog_exec_path,
                                         '--configuration',
                                         self.config_path,
                                         filepath
                                         ],
                                        stderr=subprocess.STDOUT,
                                        stdout=subprocess.PIPE,
                                        timeout=timeout,
                                        universal_newlines=True
                                        )

        json_start_idx = completed_proc.stdout.find('[')
        if json_start_idx == -1:
            print('----------Progpilot Error-----------')
            print(completed_proc.stdout)
            return []
        else:
            try:
                json_str = completed_proc.stdout[json_start_idx:]
                data = json.loads(json_str)
            except:
                print('JSON Parse Error: {}'.format(filepath))
                data = []

            # Only return results w/ taint-flows
            parsed_data = []
            for result in data:
                if 'tainted_flow' in result:
                    parsed_data.append(result)

            return parsed_data
        

    def run_contents(self, file_contents=None, file_content_bytes=None, timeout=15):
        """timeout is in seconds"""
        # If bytes are passed convert to text
        if file_content_bytes is not None:
            file_contents = file_helpers.decode(file_content_bytes)

        # Add blocks to contents if needed
        file_contents = file_helpers.add_tags_to_file_text(file_contents)

        # Create tmp file for progpilot
        tmp_file = tempfile.NamedTemporaryFile('w', delete=False)
        with tmp_file:
            tmp_file.write(file_contents)

        # Run progpilot
        result = self.run(tmp_file.name, timeout)

        # Delete temp file
        os.remove(tmp_file.name)

        return result
