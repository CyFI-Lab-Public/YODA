from varsfile import *
from base_analysis_class import BaseAnalysisClass
from base_class import Plugin , PluginFile
import re
import subprocess
import json
import time
import pickle
from IPython import embed
import os

class Analysis_WP_Plugin(BaseAnalysisClass):
    def __init__(self):
        self.grouped_plugin = None

    def find_param_str(self, file_read, start_index):
        final_param_str = ""
        open_parentheses = 0
        close_parentheses = 0
        started = False
        while start_index < len(file_read):
            if file_read[start_index] == '(':
                if open_parentheses:
                    final_param_str += file_read[start_index]
                else:
                    started = True
                open_parentheses += 1
            elif file_read[start_index] == ')':
                close_parentheses += 1
                if open_parentheses == close_parentheses:
                    return final_param_str
                else:
                    final_param_str += file_read[start_index]
            elif started:
                final_param_str += file_read[start_index]
            start_index += 1

    def regex_method(self, _file, file_info, references, score):
        with open(_file, 'r', errors="ignore") as f:
            file_read = f.read()
        i = 0
        max_score = (2*max(api_score, ref_score, header_score))
        (score, i) = self.find_plugin_header(file_read, file_info, score, i)
        for api in plugin_api:
            rexp = re.compile(func_before_regex + api + func_after_regex)
            iterator = rexp.finditer(file_read)
            for match in iterator:
                score += api_score/(2**i)
                i += 1
                index = match.span()[0]
                if api_keyword not in file_info:
                    file_info[api_keyword] = {}
                if api not in file_info[api_keyword]:
                    file_info[api_keyword][api] = []
                param = self.find_param_str(file_read, index)
                if param:
                    file_info[api_keyword][api].append(param)
        for ref in plugin_ref:
            rexp = re.compile(func_before_regex + ref + func_after_regex)
            iterator = rexp.finditer(file_read)
            for match in iterator:
                score += ref_score/(2**i)
                i += 1
                index = match.span()[0]
                param = self.find_param_str(file_read, index)
                if param:
                    references.append(param)
        formula = ((score*100)/max_score)
        if formula > 0:
            file_info[score_keyword] = str(formula) + "%"

    def find_plugin_header(self, file_read, file_info, score, i):
        #print("FREAD", file_read)
        for ph in plugin_header:
            rexp = re.compile(ph_before_regex + ph + ph_after_regex)
            for match in rexp.finditer(file_read):
                score += header_score/(2**i)
                i += 1
                index = match.span()[0]
                #print("INFO", ph, file_info)
                file_info[ph.rstrip(":")] = file_read[index:].split(':',1)[1].split('\n',1)[0].lstrip()
        return (score, i)

    def analyzing_later(self, grouped_file_dict, f_obj, to_update):
        max_path_depth = 0
        final_parent = ""
        # To find the lowest level plugin name
        for plugin_name in grouped_file_dict:
            if grouped_file_dict[plugin_name][path_keyword] in f_obj.filepath:
                plugin_path_length = len(grouped_file_dict[plugin_name][path_keyword].split("/"))
                if plugin_path_length > max_path_depth:
                    max_path_depth = plugin_path_length
                    final_parent = plugin_name
        if final_parent:
            grouped_file_dict[final_parent].update({f_obj.filepath:f_obj.file_info})
            f_obj.is_plugin = True
            f_obj.plugin_name = final_parent
        else:
            f_obj.analyze_later = True

    def find_parent_plugin(self, f_obj, plugins):
        max_path_depth = 0 
        final_parent = ""
        parent = []
        # To find the lowest level plugin name
        for p_name in plugins:
            if plugins[p_name].plugin_base_path in f_obj.filepath:
                plugin_path_length = len(plugins[p_name].plugin_base_path.split("/"))
                if plugin_path_length > max_path_depth:
                    max_path_depth = plugin_path_length
                    parent.clear()
                    parent.append(p_name)
                elif plugin_path_length == max_path_depth:
                    parent.append(p_name)
        if parent:
            parent.sort()
            final_parent = parent[0]
            # If parent is found, then tag the file as a plugin
            f_obj.is_plugin = True
            f_obj.plugin_name = final_parent
            plugins[final_parent].files[f_obj.filepath] = PluginFile(f_obj.filepath, f_obj.state, f_obj.mime_type, final_parent)
        f_obj.analyze_later = False

    def ast_method(self, _file, file_info, refrences, score):
        jstr = subprocess.check_output(
                                        "php -f ast_parser.php \"" + _file + "\"",
                                        stderr=DEVNULL,
                                        shell=True
                                      )
        i = 0
        max_score = (2*max(api_score, ref_score, header_score))
        with open(_file, 'r', errors="ignore") as f: # GET PLUGIN HEADER INFO
            (score, i) = self.find_plugin_header(f.read(), file_info, score, i)

        jdata = json.loads(jstr.decode('utf-8')) # PUT AST RESULTS INTO JSON
        if len(jdata[api_keyword]) or len(jdata[ref_keyword]):
            file_info[ast_keyword] = jdata;
        for api in jdata[api_keyword]:
            score += api_score/(2**i)
            i += 1
        for ref in jdata[ref_keyword]:
            score += ref_score/(2**i)
            i += 1
        formula = ((score*100)/max_score)
        if formula > 0:
            file_info[score_keyword] = str(formula) + "%"

    def processFile(self, f_obj):
        p_obj = None
        references = []
        score = 0
        files_analyze_later = []
        #print("AFOBJ", f_obj.state, f_obj.mime_type, f_obj.filepath)
        if 'php' in f_obj.mime_type:
            try:
                # Default try AST method
                #print("AST", f_obj.state, f_obj.filepath)
                self.ast_method(f_obj.filepath, f_obj.file_info, references, score)
            except Exception as e:
                # If it fails, switch to RegEx 
                #print("AST Method Failed: " + str(e) + "... Using RegEx Method")
                self.regex_method(f_obj.filepath, f_obj.file_info, references, score)

            #plugin_keyword = "Plugin Name"
            #print("PNAME", f_obj.filepath, f_obj.file_info)
            if  plugin_keyword in f_obj.file_info  and ("Name of Plugin" not in f_obj.file_info[plugin_keyword]):
                plugin_name = f_obj.file_info[plugin_keyword]
                f_obj.is_plugin   = True # For all plugins and themes
                f_obj.plugin_name = plugin_name 

                # Create plugin object
                p_obj = Plugin(plugin_name, f_obj.filepath)
                # Assign plugin score
                if score_keyword in f_obj.file_info:
                    p_obj.plugin_score = f_obj.file_info[score_keyword] 
                # Assign plugin author
                if wp_author in f_obj.file_info:
                    p_obj.author = f_obj.file_info[wp_author]
                # Assign plugin version
                if wp_version in f_obj.file_info:
                    p_obj.version= f_obj.file_info[wp_version]
                # Assign plugin author URI
                if wp_author_uri in f_obj.file_info:
                    p_obj.author_uri = f_obj.file_info[wp_author_uri]
                # Assign plugin author URI
                if wp_plugin_uri in f_obj.file_info:
                    p_obj.plugin_uri = f_obj.file_info[wp_plugin_uri]
                # Assign plugin license
                if wp_license in f_obj.file_info:
                    p_obj.license = f_obj.file_info[wp_license]
                # Assign plugin description
                if wp_description in f_obj.file_info:
                    p_obj.description = f_obj.file_info[wp_description]
                # Save plugin filepath
                #p_obj.files.append(PluginFile(f_obj.filepath, f_obj.state, f_obj.mime_type))
                p_obj.files[f_obj.filepath] = PluginFile(f_obj.filepath, f_obj.state, f_obj.mime_type, plugin_name)
                # It it was a PHP Theme, set theme tag
                if theme_keyword in f_obj.file_info:
                    p_obj.is_theme = True
                    print("IS_THEME", f_obj.filepath)
                    
            else:
                f_obj.is_plugin   = False
                f_obj.analyze_later = True
            
            # Free memory holding all of the plugin info in f_obj.file_info
            f_obj.file_info = {} 
            return p_obj

    def populate_other_theme_metadta(self, f_obj, c_obj, theme_name):
        references = []
        score = 0
        self.regex_method(f_obj.filepath, f_obj.file_info, references, score)
        # Assign plugin score
        if score_keyword in f_obj.file_info:
            c_obj.plugins[theme_name].plugin_score = f_obj.file_info[score_keyword] 
        # Assign plugin author
        if wp_author in f_obj.file_info:
            c_obj.plugins[theme_name].author = f_obj.file_info[wp_author]
        # Assign plugin version
        if wp_version in f_obj.file_info:
            c_obj.plugins[theme_name].version= f_obj.file_info[wp_version]
        # Assign plugin author URI
        if wp_author_uri in f_obj.file_info:
            c_obj.plugins[theme_name].author_uri = f_obj.file_info[wp_author_uri]
        # Assign plugin author URI
        if wp_theme_uri in f_obj.file_info:
            c_obj.plugins[theme_name].plugin_uri = f_obj.file_info[wp_theme_uri]
        # Assign plugin license
        if wp_license in f_obj.file_info:
            c_obj.plugins[theme_name].license = f_obj.file_info[wp_license]
        # Assign plugin description
        if wp_description in f_obj.file_info:
            c_obj.plugins[theme_name].description = f_obj.file_info[wp_description]
        # Assign theme name 
        if theme_keyword in f_obj.file_info:
            c_obj.plugins[theme_name].theme_name = f_obj.file_info[theme_keyword]

                
    def postProcessCommit(self, c_obj):
        # Get all Plugin base paths
        plugin_paths = []
        for p_obj in c_obj.plugins:
            plugin_paths.append(c_obj.plugins[p_obj].plugin_base_path)

        # Collect all the files that were not marked as a plugin within plugin dir
        # This helps us collect all the non-php files to get a full-picture of the plugin
        for f_obj in c_obj._file_list:
            if (not f_obj.analyze_later) and (not f_obj.is_plugin):
                f_obj.analyze_later = any(x in f_obj.filepath for x in plugin_paths)

            # Find parent plugin for all the files marked as analyze_later
            if f_obj.analyze_later:
                self.find_parent_plugin(f_obj, c_obj.plugins)
                # Reset analyze_later
                f_obj.analyze_later = None
            
            # A/M/R cases are handled in DoFileOperation 
            # [This doesn't work because when a deleted file is added bacl
            # the state doesn't get changed. => retag state for all plugin files
            # Update state of deleted plugins and NC plugins
            #if f_obj.is_plugin: #and f_obj.state not in ['A', 'M', 'R']:
            if f_obj.is_plugin: #and f_obj.state not in ['A', 'M', 'R']:
                c_obj.plugins[f_obj.plugin_name].files[f_obj.filepath].state = f_obj.state
                c_obj.plugins[f_obj.plugin_name].files[f_obj.filepath].version = c_obj.plugins[f_obj.plugin_name].version
            elif "wp-content/themes" in f_obj.filepath:
                theme_name = re.split("wp-content/themes/", f_obj.filepath)[1].split('/')[0]
                    
                if "index.php" != theme_name:
                    references = []
                    score = 0
                    f_obj.is_plugin   = True # For all plugins and themes
                    f_obj.plugin_name = theme_name 

                    if theme_name not in c_obj.plugins:
                        # Create plugin object
                        p_obj = Plugin(theme_name, f_obj.filepath)
                        p_obj.is_theme = True
                        c_obj.plugins[theme_name] = p_obj
                        c_obj.plugins[theme_name].files[f_obj.filepath] = PluginFile(f_obj.filepath, f_obj.state, f_obj.mime_type, theme_name)
                        if f_obj.filepath.endswith("style.css"):
                            self.populate_other_theme_metadta(f_obj, c_obj, theme_name)
                    else:
                        c_obj.plugins[theme_name].files[f_obj.filepath] = PluginFile(f_obj.filepath, f_obj.state, f_obj.mime_type, theme_name)
                        if f_obj.filepath.endswith("style.css"):
                            self.populate_other_theme_metadta(f_obj, c_obj, theme_name)
                    c_obj.plugins[f_obj.plugin_name].files[f_obj.filepath].state = f_obj.state

