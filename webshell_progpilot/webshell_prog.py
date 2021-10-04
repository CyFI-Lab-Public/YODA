from progpilot import progpilot
import os
from utils import file_helpers
import json

class WebshellProgRunner:
    def __init__(self):
        # There needs to be two configs, first one is for duplicate sources that should be treated as arrays
        # Second is for duplicate sources that should be treated as objects
        # Can't have both sources in one file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config_path = os.path.join(dir_path, 'webshell_config.yml')
        config_path_second = os.path.join(dir_path, 'webshell_config_second.yml')

        self.prog_obj = progpilot.Progpilot(config_path)
        self.prog_obj_second = progpilot.Progpilot(config_path_second)
        self.sinks = ['system', 'exec', 'eval', 'shell_exec', 'passthru', 'proc_open']

    def run(self, filepath=None, file_contents=None, file_content_bytes=None):
        """Runs our webshell progpilot config"""
        # Read file contents if the filepath is supplied
        if filepath is not None:
            # Read file
            file_contents = file_helpers.read_file(filepath)

        result = None
        # If filepath or file_contents set run
        if file_contents is not None:
            result = self.prog_obj.run_contents(file_contents=file_contents, timeout=20)
        # If file_content bytes run
        else:
            result = self.prog_obj.run_contents(file_content_bytes=file_content_bytes, timeout=20)

        # Run second config if first one didn't find anything
        if len(result) == 0:
            # If filepath or file_contents set run
            if file_contents is not None:
                result = self.prog_obj_second.run_contents(file_contents=file_contents, timeout=20)
            # If file_content bytes run
            else:
                result = self.prog_obj_second.run_contents(file_content_bytes=file_content_bytes, timeout=20)

        return result
