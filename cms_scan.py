import json
import sys
import subprocess
import os
import re


def cms_scan(input_dir):
    # Counts of wordpress, drupal, and joomla installations
    wordpress = 0
    drupal = 0
    joomla = 0

    # Versions of wordpress, drupal, and joomla installations
    versions = {}
    versions['wp'] = ""
    versions['dr'] = ""
    versions['jo'] = ""

    # Patterns to ignore old or backed up CMS installations
    pattern1 = re.compile('old', re.IGNORECASE)
    pattern2 = re.compile('bak', re.IGNORECASE)
    pattern3 = re.compile('bac', re.IGNORECASE)

    # Get cmsscanner results on temp.json
    json_out = "temp.json"
    subprocess.run("./cmsscanner_nosymlink.phar cmsscanner:detect --report=" + json_out + " " + input_dir, shell = True)

    # Extract cms info and remove json file
    with open(json_out, "r") as read_file:
        cms_data = json.load(read_file)
    os.remove("temp.json")

    # Narrow down on a single CMS based on the list provided by cmsscanner
    for cms_item in cms_data:
        cms_name = cms_item["name"]
        cms_ver  = cms_item["version"]
        cms_path = cms_item["path"]

        if (cms_name == "WordPress") or (cms_name == "Contenido"):
            # If cms is in an old or backed up installation, ignore it 
            old = len(re.findall(pattern1, cms_path))
            bak = len(re.findall(pattern2, cms_path)) 
            bac = len(re.findall(pattern3, cms_path))
            if old or bak or bac:
                continue
            else:
                wordpress += 1
                if (versions['wp'] != "") or (versions['wp'] == "None"):
                    versions['wp'] = cms_ver

        elif (cms_name == "Drupal"):
            # If cms is in an old or backed up installation, ignore it 
            old = len(re.findall(pattern1, cms_path))
            bak = len(re.findall(pattern2, cms_path)) 
            bac = len(re.findall(pattern3, cms_path))

            if old or bak or bac:
                continue
            else:
                drupal += 1
                if (versions['dr'] != "") or (versions['dr'] == "None"):
                    versions['dr'] = cms_ver

        elif (cms_name == "Joomla"):
            # If cms is in an old or backed up installation, ignore it 
            old = len(re.findall(pattern1, cms_path))
            bak = len(re.findall(pattern2, cms_path)) 
            bac = len(re.findall(pattern3, cms_path))

            if old or bak or bac:
                continue
            else:
                joomla += 1
                if (versions['jo'] != "") or (versions['jo'] == "None"):
                    versions['jo'] = cms_ver


    '''If a website has wordpress and/or drupal and/or joomla installations, resolve and 
    assign a single CMS.
    '''
    if ((wordpress and drupal) or (drupal and joomla) or ( wordpress and joomla)):
        # If one of the clashing CMSs is WordPress, odds are it is actually WordPress 
        if wordpress:
            # If #joomla or #drupal > #wordpress, then assign #joomla or #drupal
            if (joomla/wordpress > 2) or (drupal/wordpress > 2):
                if joomla:
                    cms = "Joomla"
                    ver = versions['jo']
                else:
                    cms = "Drupal"
                    ver = versions['dr']
            else:
                cms = "WordPress" #(odds are high that it is indeed wordpress)
                ver = versions['wp']
        else:
            # If Drupal and Joomla are clashing, randomly assign one 
            cms = "Drupal" if random.randrange(100) % 2 == 1 else "Joomla" 
            ver = versions['dr'] if cms == "Drupal" else versions['jo'] 
        #print("CMS Clash for website", input_dir)
    
    # If no clash between WordPress, Drupal, and Joomla, then prepare the return variables
    elif wordpress:
        cms = "WordPress"
        ver = versions['wp']
    elif drupal:
        cms = "Drupal"
        ver = versions['dr']
    elif joomla:
        cms = "Joomla"
        ver = versions['jo']
    else:
        cms = "None"
        ver = "None"
    return cms, ver


if __name__=="__main__":
    #print(sys.argv[0], sys.argv[1], sys.argv[2])
    print(sys.argv[1])
    cms = cms_scan(sys.argv[1])
    print(cms)

    #o_file = open("cms.txt", "a")
    #dirs = os.listdir(sys.argv[1]) 
    #for d in dirs:
    #    w_path = os.path.join(sys.argv[1], d)
    #    print(w_path)
    #    cms = cms_scan(w_path)
    #    o_file.write(w_path + " " + cms + "\n")
    #
