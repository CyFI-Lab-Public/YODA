from git import Repo
from base_class import Website, Commit, FileMetadata, Plugin, PluginFile
import datetime
from pytz import timezone
from IPython import embed
from multiprocessing import Pool, cpu_count, Array, Process, Manager, SimpleQueue
from functools import partial
import os, git, magic, sys
import re, time, boto3, botocore
import shutil, copy, json, gzip
import filetype_dictionary as fd
import subprocess
import json
from pathlib import Path

from cms_scan import cms_scan
from analysis_wp_plugin import Analysis_WP_Plugin
from analysis_jo_plugin import Analysis_Jo_Plugin
from analysis_dr_plugin import Analysis_Dr_Plugin

sys.path.insert(0, './analysis_passes') # Import from subdirectory
from analysis_obf_plugin import Analysis_Obf_Plugin
from analysis_cryptominer import Analysis_Cryptominer
from analysis_corona import Analysis_Corona
from analysis_blacklist import Analysis_Blacklist
from analysis_fake_blacklist import Analysis_Fake_Blacklist
from analysis_err_report import Analysis_Err_Report
from analysis_shell_detect import Analysis_Shell_Detect
from analysis_fc_plugin import Analysis_FC_Plugin
from analysis_spam_plugin import Analysis_Spam_Plugin
from analysis_bh_seo_plugin import Analysis_BlackhatSEO_Plugin
from analysis_api_abuse import Analysis_API_Abuse
from analysis_covid_plugin import Analysis_Covid_Plugin
from analysis_downloader_plugin import Analysis_Downloader_Plugin
from analysis_gated_plugin import Analysis_Gated_Plugin
from analysis_bot_seo import Analysis_Bot_SEO
from analysis_newdown_plugin import Analysis_NewDown_Plugin

OUTPUT_BUCKET = "cyfi-plugins-results"
plugin_analyses = {}
plugin_analyses["WordPress"] = [Analysis_WP_Plugin()]
plugin_analyses["Joomla"]   = [Analysis_Jo_Plugin(), Analysis_WP_Plugin()]
plugin_analyses["Drupal"]   = [Analysis_Dr_Plugin(), Analysis_WP_Plugin()]

# Malicious plugin detection analyses
mal_plugin_analyses = [
        Analysis_Obf_Plugin(),         # Obfuscation
        Analysis_Cryptominer(),        # Cryptomining
        Analysis_Blacklist(),          # Blacklisted Plugin Names and versions
        Analysis_Fake_Blacklist(),     # Blacklisted Fake Plugin Names
        Analysis_Err_Report(),         # Disable Error Reporting
        Analysis_Shell_Detect(),       # Webshells in plugins
        Analysis_FC_Plugin(),          # Function Construction
        Analysis_Spam_Plugin(),        # Spam Injection
        Analysis_BlackhatSEO_Plugin(), # Blackhat SEO
        Analysis_API_Abuse(),          # Abuse of WP API
        Analysis_Covid_Plugin(),       # COVID-19
        Analysis_Downloader_Plugin(),  # Downloaders
        Analysis_Gated_Plugin(),       # Gated Plugins
        Analysis_Bot_SEO(),            # SEO against Google bot 
        Analysis_NewDown_Plugin(),     # Nulled Plugin 
        Analysis_Corona()              # Coronavirus regex
        # Analysis_Out_Extract()         # Extract Outputs
]


class EST5EDT(datetime.tzinfo):

    def utcoffset(self, dt):
        return datetime.timedelta(hours=-5) + self.dst(dt)

    def dst(self, dt):
        d = datetime.datetime(dt.year, 3, 8)        #2nd Sunday in March (2020)
        self.dston = d + datetime.timedelta(days=6-d.weekday())
        d = datetime.datetime(dt.year, 11, 1)       #1st Sunday in Nov (2020)
        self.dstoff = d + datetime.timedelta(days=6-d.weekday())
        if self.dston <= dt.replace(tzinfo=None) < self.dstoff:
            return datetime.timedelta(hours=1)
        else:
            return datetime.timedelta(0)

    def tzname(self, dt):
        return 'EST5EDT'


def delete_dir(path_to_dir):

    """ Delete the directory and all of its contents at  path_to_dir if dir 
    exists
    """
    #TODO check if path_to_dir is an abs path or jus dir name. If it is just a dir name => cwd/dir_name  
    if os.path.isdir(path_to_dir):
        shutil.rmtree(path_to_dir)

def mkdir(dir_name):

    """mkdir in cwd
    Check if dir_name exists in the present working directory (pwd). If it 
    doesn't, make an empty directory named dir_name in the present working directory.
    """
    pwd = os.getcwd()
    dir_path = pwd + "/" + dir_name
    # If dir doesn't exist, make dir
    if os.path.isdir(dir_path) == 0 :
        os.mkdir(dir_path)

class Framework():

    def __init__(self, website_path =None):
        if website_path.endswith("/"):
            pass
        else:
            website_path = website_path + "/"
        self.website = Website(website_path)    
        self.commits = []
        # Variables used to fix git mistakes in filenames that contain non-ascii characters
        self.octals = re.compile('((?:\\\\\d\d\d)+)')
        self.three_digits = re.compile('\d\d\d')
        print("CMS", self.website.cms)

    def print_repository(self, repo):
        print('Repo description: {}'.format(repo.description))
        print('Repo active branch is {}'.format(repo.active_branch))
        for remote in repo.remotes:
            print('Remote named "{}" with URL "{}"'.format(remote, remote.url))
        print('Last commit for repo is {}.'.format(str(repo.head.commit.hexsha)))


    def print_commit(self, commit):
        print('----')
        print(str(commit.hexsha))
        print("\"{}\" by {} ({})".format(commit.summary,
                                         commit.author.name,
                                         commit.author.email))
        print(str(commit.authored_datetime))
        print(str("count: {} and size: {}".format(commit.count(),
                                                    commit.size)))


    def GetCommitList(self, repo):
        ''' Get git commit objects and create a list of Commit objects for each
        commit 
        '''
        commit_list = list(repo.iter_commits('master'))
        commits = []
        for c in commit_list:
            commits.append(Commit(c))
        return commits


    def fix_git_trash_strings(self, git_trash):
        ''' Git diff.a_path and b_path replace non-ascii chacters by their
        octal values and replace it as characters in the string. This function 
        fixes thhis BS.
        '''
        git_trash = git_trash.lstrip('\"').rstrip('\"') 
        match = re.split(self.octals, git_trash)
        pretty_strings = []
        for words in match:
            if re.match(self.octals,words):
                ints = [int(x, 8) for x in re.findall(self.three_digits, words)]
                pretty_strings.append(bytes(ints).decode())
            else:
                pretty_strings.append(words)
        return ''.join(pretty_strings)

    def GetExtension(self, f_name):
    # Used Victor's hacky code from TARDIS to get the extension
        is_hidden = False
        if f_name[0] == '.':
            is_hidden = True

        f_type = f_name.split('.')
        possible_ft = []
        if len(f_type) > 1 and not is_hidden:
            for ft in f_type:
                if ft in fd.readable_to_ext:
                    #possible_ft.append(fd.readable_to_ext[ft])
                    possible_ft.append(ft)
        elif len(f_type) > 2:
            for ft in f_type:
                if ft in fd.readable_to_ext:
                    possible_ft.append(fd.readable_to_ext[ft])        
                    possible_ft.append(ft)        
        if len(possible_ft) > 1:
            for pfg in possible_ft:
                if pfg != "svn-base":
                    file_extension = pfg
        elif len(possible_ft) == 1:
            file_extension = possible_ft[0]
            # Re-assigning type for some cases based on extn, only for ease of sorting outputs 
            if file_extension== 'ini':
                file_extension = 'php'
            elif file_extension == 'jsx':
                file_extension = 'js'
            elif (file_extension == 'json') or (file_extension == 'md'):
                file_extension = 'txt'
            elif (file_extension == 'woff') or (file_extension == 'ttf') or (file_extension == 'otf') or (file_extension == 'woff2') or (file_extension == 'eot'):
                file_extension = 'font'
        else:
            file_extension = None
        return file_extension

    def getType(self, f_path, pf_obj):
        # Wrapper around GetExtension
        mime = str(pf_obj.mime_type)
        if 'php' in mime:
            extn = 'php'
        else:
            extn = self.GetExtension(f_path)

        if extn != None:
            mime = extn 
        else:
            if 'text' in mime:
                mime = 'txt'
            elif 'xml' in mime:
                mime = 'xml'
        return mime

    def CountPluginFiles(self, c_obj, p_obj):
        # First Commit: Count all files
        if c_obj.initial == True:
            p_obj.num_files = 0
            # Save effective file states of all plugin files 
            for p_filepath, pf_obj in p_obj.files.items():
                #print("DBG1", pf_obj.state, c_obj.commit_id, p_filepath)
                #Count num files
                p_obj.num_files += 1

                # Count number of file types
                mime = self.getType(p_filepath, pf_obj)
                if mime not in p_obj.num_file_types:
                    p_obj.num_file_types[mime] = 1
                else:
                    p_obj.num_file_types[mime] += 1

            #print("COUNT", p_obj.num_file_types, c_obj.commit_id, p_obj.plugin_name)
            # In the first commit, all files are added
            add = True
            mod = False
            dlt = False
            nc = False
            nc_d = False
            return add, mod, dlt, nc, nc_d
        # 2nd commit onwards, only count added or deleted files
        else:
            if p_obj.num_files == None:
                p_obj.num_files = 0
            add = False 
            mod = False
            dlt = False
            nc = False
            nc_d = False
            p_obj.error = False
            #print("PLG", p_obj.plugin_name, p_obj.num_file_types)
            for p_filepath, pf_obj in p_obj.files.items():
                #print("DBG2", pf_obj.state, c_obj.commit_id, p_filepath)
                #Count num files
                if pf_obj.state in ['A', 'R']:
                    p_obj.num_files += 1
                    mime = self.getType(p_filepath, pf_obj)
                    if mime not in p_obj.num_file_types:
                        p_obj.num_file_types[mime] = 1
                    else:
                        p_obj.num_file_types[mime] += 1
                elif pf_obj.state == 'D':
                    p_obj.num_files -= 1
                    mime = self.getType(p_filepath, pf_obj)
                    try: 
                        p_obj.num_file_types[mime] -= 1
                        # If all files of a given type are deleted, remove it from dict
                        if p_obj.num_file_types[mime] == 0:
                            p_obj.num_file_types.pop(mime)
                    except:
                        print("ERROR", mime, "not in num_file_ftypes", p_obj.num_file_types, p_obj.plugin_name, p_filepath)
                        p_obj.error = True
                # Derive final state of the plugin
                if (not nc) and pf_obj.state == 'NC':
                    nc = True
                elif (not nc_d) and pf_obj.state == 'NC_D':
                    nc_d = True
                elif (not add) and pf_obj.state == 'A':
                    add = True
                elif (not mod) and pf_obj.state == 'M':
                    mod = True
                elif (not dlt) and pf_obj.state == 'D':
                    dlt = True
            #print("COUNT2", p_obj.num_file_types, c_obj.commit_id, p_obj.plugin_name)
            return add, mod, dlt, nc, nc_d
        
    def GetFileList(self, c_obj, init):
        exclude  = ['.codeguard' , '.git' , '.gitattributes']
        file_list       = []
        ma        = magic.Magic(mime = True)
         
        # Parse through all the directories and get all files for the first commit or if the previous commit has zero files
        num_files = 0  
        if c_obj == self.commits[0] or init:
            for fpath, dirs, files in os.walk(self.website.website_path, topdown = True):
                # Exclude files in .git and .codeguard directories
                dirs[:] = [d for d in dirs if d not in exclude]
                files[:] = [fs for fs in files if fs not in exclude]

                # If no files in this commit, then set c_obj.initial to False so we get full filelist again in the next commit
                if files:
                    c_obj.initial = True
                
                # For the first commit, the state is considered as file added(A)
                for f in files:
                    full_path = os.path.join(fpath, f)
                    if  os.path.islink(full_path):
                        mime = 'sym_link'
                    else:
                        #mime = ma.from_file(full_path.encode(sys.getfilesystemencoding(), 'surrogateescape'))
                        try:
                            mime = ma.from_file(full_path.encode("utf-8", 'surrogateescape'))
                            #mime = ma.from_file(full_path)
                        except  Exception as e:
                            print("MIME_ERROR:", e, "Could no encode filename", full_path)
                            mime = None
                        file_list.append(FileMetadata(full_path, f, 'A', mime))
            num_files = len(file_list)
        else:
            '''Second commit onwards, copy the file_list from the previous commit, 
            and only modify changed files. Add new files if any, and change the state
            of modified or renamed files.
            '''
            prev_index = self.commits.index(c_obj) -1
            file_list = copy.deepcopy(self.commits[prev_index]._file_list)
            
            # Free up memory
            self.commits[prev_index]._file_list = None

            found_index_list = []
            for diff in c_obj.parent.diff(c_obj.commit_obj):
                # Ignore all the changes in .codeguard directors
                if '.codeguard' not in diff.b_path:
                    '''Side note:
                    diff.a_path -> path of the file in parent (older) commit object
                    diff.b_path -> path of the file in child (newer)commit object
                    If a file is renamed, the old name is considered 'deleted' in the new commit
                    '''
                    # Clean up git python string madness for non-ascii characters
                    if re.search(self.octals,diff.a_path):
                        diff_a_path = self.fix_git_trash_strings(diff.a_path)  
                    else:
                        diff_a_path = diff.a_path
                    if re.search(self.octals,diff.b_path):
                        diff_b_path = self.fix_git_trash_strings(diff.b_path)  
                    else:
                        diff_b_path = diff.b_path

                    # Note for @Victor                    
                    #print("A_MODE", diff.a_mode, diff_a_path)
                    #print("B_MODE", diff.b_mode, diff_b_path)

                    # For renamed files, consider the orginal path as deleted
                    if diff.change_type == 'R':
                        search_path = self.website.website_path + '/' + diff_a_path
                        found_index = self.search_file_list(search_path, file_list)
                        if found_index != None:
                            file_list[found_index].state = 'D'

                    ''' Check if diff result is already in our file list. 
                    Yes => update 'state' No => Add new instance to file_list
                    '''
                    ''' ******************************************************
                    NOTE: WEBSITE_PATH should end in "/"
                    *********************************************************
                    '''
                    search_path = self.website.website_path + diff_b_path
                    found_index = self.search_file_list(search_path, file_list)
                    #print(found_index,diff_b_path, diff.change_type)
                    if (found_index != None):
                        file_list[found_index].state = diff.change_type
                        found_index_list.append(found_index)
                        # If there is permission change, update fileMetadata object
                        if diff.a_mode != 0 and diff.b_mode != 0:
                            if diff.a_mode != diff.b_mode:
                                file_list[found_index].permission_change = True
                        #print('FOUND', diff.change_type, diff.b_path)
                    else:
                        # Index not found implies a new file is being added
                        f_name_only = search_path.split('/')[-1]
                        try:
                            mime_type = ma.from_file(search_path.encode("utf-8", 'surrogateescape'))
                        except OSError as e:
                            print("=> Handled" + str(e))
                            mime_type = None
                        file_list.append(FileMetadata(search_path, f_name_only, diff.change_type, mime_type))
                        found_index_list.append(len(file_list) -1)
                        #print('NOT_FOUND', diff.change_type, diff.b_path, f_name_only)
            #priint(found_index_list)
        
            #If a file wasn't modified, set its state = NC for no change
            num_del_files = 0
            for indx, file_obj in enumerate(file_list):
                if file_obj.state in [ 'D', 'NC_D']:
                    num_del_files +=1
                if indx not in found_index_list:
                    if file_obj.state == 'D' or file_obj.state == 'NC_D':
                        file_obj.state = 'NC_D' # Deleted in the previous commit and did not come back in this commit
                    else:
                        file_obj.state = 'NC'
            num_files = len(file_list) - num_del_files
                            
        return file_list, num_files
 

    def has_method(self, a_class_object, func_name):
        has = hasattr(a_class_object, func_name)
        print ('has_method: ', func_name, has)
        return has


    def search_file_list(self, search_item, file_list):
        #print(search_item)
        for f_item in file_list:
            if f_item.filepath == search_item:
                return file_list.index(f_item)
        return None

    def process_outputs(self, website, commits, cms, analysis_start):
        op = {}
        op["website_id"] = website.website_path.split('/')[-2]
        if cms == "noCMS":
            op["cms"] = "NoCMS"
        else:
            op["cms"] = website.cms
            op["cms_ver"] = website.cms_version
            op["c_ids"] = []
            op["plugin_info"] = {}
            has_mal_plugins = False
            for c_obj in commits:
                #print('---------------------------------------------------')
                #print('Current Commit ID:', c_obj.commit_id, c_obj.date.strftime('%m/%d/%Y, %H:%M:$S')) 
                #print('---------------------------------------------------')
                op["c_ids"].append(c_obj.commit_id)
                c_out = {}
                c_out["date"] = c_obj.date.strftime('%m/%d/%Y, %H:%M:%S')
                c_out["num_files"] = c_obj.num_files
                #print("Number of files:", c_obj.num_files, len(c_obj._file_list))
                c_out["has_mal_plugins"] = c_obj.has_mal_plugins
                if not has_mal_plugins:
                    has_mal_plugins = c_obj.has_mal_plugins
                c_out["num_active_plugins"] = c_obj.num_active_plugins
                #print("Number of active plugins:", c_obj.num_active_plugins)
                c_out["mal_pnames"] = copy.deepcopy(c_obj.mal_pnames)
                c_out["plugins_changed"] = c_obj.plugins_changed
                c_out["num_mal_plugins"] = c_obj.num_mal_plugins
                c_out["tot_mal_pfiles"] = c_obj.tot_mal_pfiles
                c_out["plugins"] = {}
                #print("Number of mal plugins", c_obj.num_mal_plugins, c_obj.commit_id)
                #print("Plugins changed:", c_obj.plugins_changed)
                if c_obj.plugins_changed:
                    for p_name in c_obj.plugins:
                        p_out = {}
                        p_obj = c_obj.plugins[p_name] 
                        p_out["p_name"] = p_obj.plugin_name
                        p_out["base_path"] = p_obj.plugin_base_path
                        p_out["plugin_state"] = p_obj.plugin_state
                        p_out["error"] = p_obj.error
                        if p_obj.plugin_state not in ['NC', 'NC_D']:
                            p_out["size"] = p_obj.size
                            #print("SIZE", p_out["size"], p_out["p_name"])
                            p_out["num_files"] = p_obj.num_files
                            p_out["num_file_types"] = p_obj.num_file_types
                            p_out["author"] = p_obj.author
                            p_out["author_uri"] = p_obj.author_uri
                            p_out["author_email"] = p_obj.author_email
                            p_out["plugin_score"] = p_obj.plugin_score
                            p_out["plugin_state"] = p_obj.plugin_state
                            p_out["is_theme"] = p_obj.is_theme
                            if p_obj.is_theme:
                                p_out["theme_name"] = p_obj.theme_name
                            p_out["cms"] = p_obj.cms
                            p_out["fake_wp_plugin"] = p_obj.fake_wp_plugin
                            p_out["version"] = p_obj.version
                            p_out["is_mal"] = p_obj.is_mal
                            if p_obj.fake_wp_plugin:
                                p_out["is_mal"] = True
                            p_out["files"] = {}
                            for pf_name in p_obj.files:
                                f_out = {}
                                pf_obj = p_obj.files[pf_name]
                                f_out["state"] = pf_obj.state
                                if pf_obj.suspicious_tags:
                                    f_out["suspicious_tags"] = pf_obj.suspicious_tags
                                f_out["is_mal"] = pf_obj.is_malicious
                                if pf_obj.extracted_results and pf_obj.state not in ["NC", "NC_D"]:
                                    #print("EXT_RES", pf_obj.state, pf_obj.filepath, pf_obj.suspicious_tags, pf_obj.extracted_results)
                                    f_out["extracted_results"] = pf_obj.extracted_results
                                #elif not pf_obj.extracted_results:
                                #print("NO_RES", pf_obj.state, pf_obj.filepath, pf_obj.suspicious_tags)
                                p_out["files"][pf_name] = f_out
                            p_out["num_mal_pfiles"] = p_obj.num_mal_p_files
                            #if p_obj.num_mal_p_files:
                            #   print("Number of mal p_files", p_obj.num_mal_p_files, "in plugin", p_obj.plugin_name)
                        c_out["plugins"][p_name] = p_out
                op["plugin_info"][c_obj.commit_id] = c_out
            op["has_mal_plugins"] = has_mal_plugins
            
        analysis_end = time.time()
        op["time"] = analysis_end - analysis_start
        if 'ENVIRONMENT' in os.environ:
            op["size"] = os.path.getsize("Repos/temp.tar.gz")
            with gzip.open('output.json.gz', 'w') as f:
                f.write(json.dumps(op, default=str).encode('utf-8'))
            if os.environ['ENVIRONMENT'] == 'BATCH':
                CYFI_ACCESS_KEY = os.environ['CYFI_ACCESS_KEY']
                CYFI_SECRET_KEY = os.environ['CYFI_SECRET_KEY']
                cyfis3 = boto3.resource('s3', 
                  aws_access_key_id=CYFI_ACCESS_KEY,
                  aws_secret_access_key=CYFI_SECRET_KEY,
                )
            bucket = cyfis3.Bucket(OUTPUT_BUCKET)
            website = os.environ['WEBSITE']
            key = website + "_" + datetime.datetime.now(tz=EST5EDT()).isoformat()  + ".json.gz"
            bucket.upload_file('output.json.gz', key)
        #print("OP", op)
        return op
        

    def run(self):
        analysis_start = time.time()
        repo = Repo(self.website.website_path)
        #print('***************************************************')
        #print('***************************************************')
        #print('Current Website:', self.website.website_path)
        #print('***************************************************')
        #print('***************************************************')
    
        # Create worker pool so the workers are alive for all commits
        p = Pool(cpu_count())

        if self.website.cms not in ["WordPress", "Drupal", "Joomla"]:
            website_output = self.process_outputs(self.website, None, "noCMS", analysis_start)
            if 'ENVIRONMENT' in os.environ:
                pass
            else:
            # Save output in local tests
                op_path = "results/" + self.website.website_path.split('/')[-2] + ".json.gz"
                if not os.path.isdir('results'):     # mkdir results if not exists
                    os.makedirs('results')

                with gzip.open(op_path, 'w') as f:
                   f.write(json.dumps(website_output, default=str).encode('utf-8'))
            return
            

        if not repo.bare:
            # Get all commits
            self.commits = self.GetCommitList(repo)
            self.commits.reverse() #Reversing to start with the oldest commit first
            
            # Initial commit -- use init and flag to assign cms if first commit has no files
            # Use init with getFileList if first commit has no files
            init = True
            flag = True 

            for c_obj in self.commits:
                try:
                    repo.git.checkout(c_obj.commit_id)
                except git.GitCommandError as e:
                    # If local change error, delete em and re run :)
                    if 'overwritten by checkout:' in str(e):
                        repo.git.reset('--hard')
                        repo.git.checkout(c_obj.commit_id) 
                #print('---------------------------------------------------')
                #print('Current Commit ID:', c_obj.commit_id, repo.head.commit.authored_datetime)
                #print('---------------------------------------------------')

                # Get all Files
                files, c_obj.num_files = copy.deepcopy(self.GetFileList(c_obj, init))
                #print("Number of files:", c_obj.num_files)
                
                # No point processing anything if the commit has no files
                if not files:
                    continue
                init = False  
               
                # If first commit had no files, cms will be unassigned. Reassign CMS 
                if flag and self.website.cms == None:
                    self.website.cms, self.website.cms_version  = cms_scan(self.website.website_path)
                    flag = False 

                # processCommit
                for analysis in plugin_analyses[self.website.cms]:
                    analysis.processCommit(c_obj)

                ''' Copy plugin info from the prev commit to this one for all 
                commits except the first commit. If first commit has no files, then wait
                until we find a commit that has files.
                '''
                prev_index = self.commits.index(c_obj) -1
                if prev_index != -1: 
                    c_obj.plugins = copy.deepcopy(self.commits[prev_index].plugins) 

                # Do file operations on all files in a commit in parallel 
                FixedCMSFileOps = partial(DoFileOperations, cms=self.website.cms) # DoFileOperations has only one argument f_obj (cms is fixed)
                file_outs = p.map(FixedCMSFileOps, files)

                # files will contain the list of updated file objects (f_obj)
                files = []
                plugins = {}
                
                ''' file_outs = oputput from DoFileOperations is a tuple of 
                f_obj, file_info for plugins
                file_outs = [outs0, outs1, ...]
                outs[0] = f_obj
                outs[1] = file_info 
                '''
                if file_outs:
                    for indx, outs in enumerate(file_outs):
                        # outs[1] will be not None only for A/M/R plugins 
                        if outs[1]:
                            if outs[1].plugin_name in plugins:
                                i = 0
                                # Duplicate plugin_name --- create p_name_#number
                                new_plugin_name = outs[1].plugin_name + '_' + str(i)
                                #print("NEW", new_plugin_name, outs[0].filepath)
                                while new_plugin_name in plugins:
                                    i += 1
                                    new_plugin_name = outs[1].plugin_name + '_' + str(i)
                                # Update corresponding plugin name in f_obj and p_obj
                                outs[0].plugin_name = new_plugin_name
                                outs[1].plugin_name = new_plugin_name
                            else:
                                new_plugin_name = outs[1].plugin_name
                            if outs[1].cms != self.website.cms:
                                outs[1].fake_wp_plugin = True
                                #print("Mismatch CMS Plugin:", new_plugin_name, outs[1].cms)
                            plugins[new_plugin_name] = outs[1] 

                            # TODO Add a output processing field for this

                            # Update the corresponding plugin name in pf_obj
                            plugins[new_plugin_name].files[outs[0].filepath].plugin_name = new_plugin_name
                        else:
                            #If plugin state = NC then update state
                            if outs[0].is_plugin: 
                                c_obj.plugins[outs[0].plugin_name].files[outs[0].filepath].state = outs[0].state
                        files.append(outs[0])
                        
                    #print("Number of added/modified plugins", len(plugins))

                    # New plugins from added or modified files
                    new_plugins = plugins #Could be this for deepcopy TODO

                # Code snoppet to test without parallel processing
                #for f_obj in files:
                #   DoFileOperations(f_obj, c_obj)

                # Update the list of fileMetadata to the Commit object
                c_index = self.commits.index(c_obj)
                self.commits[c_index]._file_list = copy.deepcopy(files)
                
                ''' Copy plugin info from the prev commit to this one for all 
                commits except the first commit. If first commit has no files, then wait
                until we find a commit that has files.
                '''
                if c_obj.initial == True:
                    c_obj.plugins = new_plugins

                else:
                # Update modified plugin info in c_obj.plugins, or add thm to c_obj, if new_plugins are added 
                    for p_name in new_plugins:
                        # New plugin added
                        if p_name not in c_obj.plugins:
                            c_obj.plugins[p_name] = new_plugins[p_name]
                        else:
                            # Plugin modified
                            for pf_name in new_plugins[p_name].files: 
                                if pf_name not in c_obj.plugins[p_name].files:
                                    c_obj.plugins[p_name].files[pf_name] = new_plugins[p_name].files[pf_name]
                            c_obj.plugins[p_name].version = new_plugins[p_name].version
                            c_obj.plugins[p_name].author = new_plugins[p_name].author
                            c_obj.plugins[p_name].author_uri = new_plugins[p_name].author_uri
                            c_obj.plugins[p_name].author_email = new_plugins[p_name].author_email
                            c_obj.plugins[p_name].plugin_uri = new_plugins[p_name].plugin_uri
                            #c_obj.plugins[p_name].num_files= new_plugins[p_name].num_files
                            #c_obj.plugins[p_name].num_file_types= new_plugins[p_name].num_file_types
                 
                # All plugins get populated here 
                # postProcessCommit
                # Since all plugins have the same postprocesscommit, we don't want to repeat it each time
                analysis = plugin_analyses[self.website.cms][0]
                #for analysis in plugin_analyses[self.website.cms]:
                analysis.postProcessCommit(c_obj)

                # By now, all plugin f_objs are tagged correctly with is_plugin
                # set to true. Now we count number of files and file types in 
                # each plugin and assign an effective state for the full plugin
                del_plugins = 0
                for p_name in c_obj.plugins:
                    p_obj = c_obj.plugins[p_name]
                    # Debug Print
                    add, mod, dlt, nc, nc_d = self.CountPluginFiles(c_obj, p_obj)
                            
                    # Derive and assign plugin state 
                    if add and not(mod or dlt or nc or nc_d):
                        if c_obj.plugins[p_name].plugin_state in ['A', 'NC', 'M']:
                            c_obj.plugins[p_name].plugin_state = 'M'
                        else:
                            c_obj.plugins[p_name].plugin_state = 'A'
                    elif dlt and not(add or mod or nc or nc_d):
                        if p_obj.num_files > 0:
                            c_obj.plugins[p_name].plugin_state = 'M'
                        else:
                            c_obj.plugins[p_name].plugin_state = 'D'
                            del_plugins += 1
                    elif nc and not(add or dlt or mod or nc_d):
                        c_obj.plugins[p_name].plugin_state = 'NC'
                    elif nc_d and not(add or dlt or mod or nc):
                        c_obj.plugins[p_name].plugin_state = 'NC_D'
                        del_plugins += 1
                    else:
                        c_obj.plugins[p_name].plugin_state = 'M'

                    #print("PLG_STATE", c_obj.plugins[p_name].plugin_state, c_obj.commit_id, c_obj.date, add, mod, dlt, nc, nc_d, p_name)
                c_obj.num_active_plugins = len(c_obj.plugins) - del_plugins
                #print("Number of active plugins:", c_obj.num_active_plugins)
                # NC to plugins till here

                to_analyze_plugins = []
                p_state_nc = True
                for p_name in c_obj.plugins:
                    p_obj = c_obj.plugins[p_name]
                    if p_state_nc and p_obj.plugin_state in ['A', 'M', 'R', 'D']:
                        p_state_nc = False
                    #if p_obj.is_theme:
                    #print("************************************************")
                    #print("FINAL PLUGIN", p_name)
                    #print("theme_name", p_obj.theme_name)
                    #print("Base path:", p_obj.plugin_base_path)
                    #print("Version", p_obj.version)
                    #print("Author", p_obj.author)
                    #print("Author URI", p_obj.author_uri)
                    #print("Plugin URI", p_obj.plugin_uri)
                    #print("Plugin Score", p_obj.plugin_score)
                    #if p_obj.fake_wp_plugin:
                    #    print("Fake WordPress Plugin", p_obj.fake_wp_plugin)
                    ## Debug Print
                    #print("NUM OF FILES",p_obj.num_files)
                    #print("TYPES",p_obj.num_file_types)
                    #print("STATE", p_obj.plugin_state)
                    #print("************************************************")
                    for pf_name in p_obj.files:
                        pf_obj = p_obj.files[pf_name]
                        if (pf_obj.state in ['A', 'M', 'R']) and ('php' in pf_obj.mime_type):
                            to_analyze_plugins.append(pf_obj)

                # If there are A/M/D/R plugins, then c_obj.plugins_changed = True. If all plugins are NC/NC_D, then c_obj.plugins_changed = False
                c_obj.plugins_changed = not (p_state_nc)
                print("Plugins changed:", c_obj.plugins_changed)

                p_outs = p.map(DoMalFileDetect, to_analyze_plugins)
                
                if os.path.exists('./tmp'): # rm FC pass's tempfile
                  os.remove('./tmp')
                if os.path.exists('./urls'): # rm SEO pass's tempfile
                  os.remove('./urls')

                # Update the plugin info on the commit object
                for pf_obj in p_outs:
                    c_obj.plugins[pf_obj.plugin_name].files[pf_obj.filepath] = pf_obj
                tot_mal_pfiles = 0
                num_mal_plugins = 0
                mal_pnames = []
                for p_name in c_obj.plugins:
                    p_obj = c_obj.plugins[p_name]
                    dir_path = Path(p_obj.plugin_base_path)
                    plg_size = sum(f.stat().st_size for f in dir_path.glob('**/*') if f.is_file()) 
                    c_obj.plugins[p_name].size = plg_size                    
                    num_mal_p_files = 0
                    for pf_name in p_obj.files:
                        pf_obj = p_obj.files[pf_name]
                        if (pf_obj.state in ['A', 'M', 'R', 'NC']) and ('php' in pf_obj.mime_type):
                            if pf_obj.suspicious_tags:
                                num_mal_p_files += 1
                                #print("M_PFILE", pf_obj.state, pf_obj.filepath, pf_obj.suspicious_tags, pf_obj.plugin_name)
                        if (pf_obj.state in ['D']): 
                            pf_obj.suspicious_tags = []
                    tot_mal_pfiles += num_mal_p_files
    
                    if num_mal_p_files:
                        #print("Number of mal p_files", num_mal_p_files, "in plugin", p_obj.plugin_name, "size", plg_size)
                        c_obj.plugins[p_name].num_mal_p_files = num_mal_p_files

                    if num_mal_p_files or p_obj.fake_wp_plugin:
                        c_obj.plugins[p_name].is_mal = True
                        num_mal_plugins += 1
                        mal_pnames.append(p_name)
                    else:
                        c_obj.plugins[p_name].is_mal = False
                #print("Number of mal plugins", num_mal_plugins, c_obj.commit_id)
                #print("Total number of mal files", tot_mal_pfiles, c_obj.commit_id)
                if num_mal_plugins:
                    c_obj.has_mal_plugins = True
                    c_obj.num_mal_plugins = num_mal_plugins
                    c_obj.tot_mal_pfiles  = tot_mal_pfiles
                    c_obj.mal_pnames = copy.deepcopy(mal_pnames)
                else:
                    c_obj.has_mal_plugins = False

                #break #This breaks after first commit. Use for dbg purposex
                
            #postProcessWebsite
            for analysis in mal_plugin_analyses:
                 analysis.postProcessWebsite(self.commits, self.website)

            website_output = self.process_outputs(self.website, self.commits, "Valid CMS", analysis_start)
            if 'ENVIRONMENT' in os.environ:
                pass
            else:
                op_path = "results/" + self.website.website_path.split('/')[-2] + ".json.gz"
                if not os.path.isdir('results'):     # mkdir results if not exists
                    os.makedirs('results')

                with gzip.open(op_path, 'w') as f:
                   f.write(json.dumps(website_output, default=str).encode('utf-8'))
            
        else:
            print('Could not load repository at {} :('.format(self.website.website_path))

        p.close()
        p.join()


def DoMalFileDetect(pf_obj):
    with open(pf_obj.filepath, 'r', errors="ignore") as f:
        read_data = f.read()

    try:    # Generate AST for Analysis Passes
        cmd = [
                  'php',
                  '-f',
                  './analysis_passes/generateAST.php',
                  pf_obj.filepath
              ]
        
        pf_obj.ast = subprocess.check_output(cmd)  

    except Exception as e:
        print("ENCOUNTERED EXCEPTION {} FOR {}".format(e, pf_obj.filepath)) 

    for reanalysis in mal_plugin_analyses:
        reanalysis.reprocessFile(pf_obj, read_data)

    pf_obj.ast=None # mem cleanup

    if pf_obj.suspicious_tags:
        pf_obj.is_malicious = True

    return pf_obj

def DoFileOperations(f_obj, cms):
    if f_obj.state not in ['A', 'D', 'M', 'R', 'NC', 'NC_D']:
        print("ERROR: New state found. State: ", f_obj.state, f_obj.filepath)

    '''
    To filter files by extension or collect any metrics based on extension
    Filter to get newly added js and rb files based on extension
    You may need some other filter, or many not need a filter at all.
    #extension = f_obj.filename.split('.')[-1]
    if f_obj.state == 'A':
        if extension == 'js':
            js_count += 1
        elif extension == 'rb':
            rb_count += 1
    '''

    #grouped_plugin = None
    grouped_plugin = []

    if f_obj.state == 'D':
        # Reset the suspicious tags when a file is deleted.
        # Check annalysis_example.py to understand suspicious_tags.
        if f_obj.suspicious_tags:
            f_obj.suspicious_tags = []
    
    # Run analyses only if the file changed. We don't want to repeat
    # the analyses on unchanged files.
    if f_obj.state == 'A' or f_obj.state == 'M' or f_obj.state == 'R':
        if not os.path.isfile(f_obj.filepath):
            return f_obj, grouped_plugin

        #processFile
        for analysis in plugin_analyses[cms]:
            grouped_plugin.append(analysis.processFile(f_obj))

        # postProcessFile - This is done for all files regardless of its state (A/D/M/NC etc.) 
        # to accomodate for tracking FileMetadata in certain plugin like AnalysisFileLine. 
        # NOTE: Add state filter in the respective analyses that use postProcessFile
        for analysis in plugin_analyses[cms]:
            analysis.postProcessFile(f_obj)

    if grouped_plugin:
        if grouped_plugin[0]:
            grouped_plugin[0].cms = cms
            return f_obj, grouped_plugin[0]
        elif cms != "WordPress":
            if grouped_plugin[1]:
                grouped_plugin[1].cms = "WordPress"
                return f_obj, grouped_plugin[1]
            else:
                grouped_plugin = None
        else:
            grouped_plugin = None
    return f_obj, grouped_plugin

if __name__=="__main__":
    if 'ENVIRONMENT' in os.environ:
        if os.environ['ENVIRONMENT'] == 'BATCH':
            print('Running on AWS Batch')
            CODEGUARD_ACCESS_KEY = os.environ['CODEGUARD_ACCESS_KEY']
            CODEGUARD_SECRET_KEY = os.environ['CODEGUARD_SECRET_KEY']
            
            CODEGUARD_BUCKET = 'cg-prod-repos'
            CYFI_RESULTS_BUCKET = 'codeguard-analysis-test-results'
            
            s3 = boto3.resource('s3', 
                aws_access_key_id=CODEGUARD_ACCESS_KEY,
                aws_secret_access_key=CODEGUARD_SECRET_KEY,
            )

            website = os.environ['WEBSITE']
            website_repo = os.environ['WEBSITE_REPO']

            os.makedirs('Repos')

            prod_bucket = s3.Bucket(CODEGUARD_BUCKET).download_file(website_repo, 'Repos/temp.tar.gz')
            os.system('tar -xf Repos/temp.tar.gz -C Repos/')
            os.system('git clone Repos/website-%s.git Repos/website-%s' % (website, website))
            website_path = './Repos/website-%s' % (website) 
    else: 
        #outfile = outdir +"/test.txt"
        # NOTE: WHILE TESTING LOCALLY SWITCH TO YOUR OWN LOCAL WEBSITE PATH 
        # NOTE: WHILE TESTING LOCALLY SET THESE ENVIRONMENT VARIABLES
        #website_path = os.environ['WEBSITE_PATH']
        #####################################################################
        #
        # NOTE: To run this use python3 framework.py path/to/website/ 
        # DO NOT FORGET FINAL "/" AT THE END OF WEBSITE PATH
        #
        #####################################################################
        website_path = sys.argv[1] 
    
    start = time.time()
    my_framework = Framework(website_path=website_path)
    my_framework.run()

    print("Time taken: ", time.time() - start)
