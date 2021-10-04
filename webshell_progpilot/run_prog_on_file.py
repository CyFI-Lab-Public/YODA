import progpilot
from utils import file_helpers
from webshell_prog import WebshellProgRunner

#prog_obj = progpilot.Progpilot('analysis/shell_detection/webshell_progpilot/webshell_config.yml')
file_path = '/home/brian/malware_samples/prog_debug.php'
prog_obj = WebshellProgRunner()

content = file_helpers.read_file(file_path)
result = prog_obj.run(file_contents=content)
# result = prog_obj.run_contents(content)

print(result)
