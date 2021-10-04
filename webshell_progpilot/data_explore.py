import json

data_file = 'webshell_results.json'

with open(data_file) as f:
    results = json.load(f)

shells_found = 0
for file in results.keys():
    if len(results[file]) == 0:
        print(file)
        shells_found += 1

print('Shells: {}'.format(shells_found))