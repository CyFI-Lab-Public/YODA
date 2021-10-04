from varsfile import *
import xml.etree.ElementTree as ET
from base_analysis_class import BaseAnalysisClass
from base_class import Plugin , PluginFile
import re
import subprocess
import json
import time
import pickle
import IPython
import os

class Analysis_Dr_Plugin(BaseAnalysisClass):
    def __init__(self):
        self.grouped_plugin = None

    def processFile(self, f_obj):
        p_obj = None
        if f_obj.filepath.endswith(".info") or f_obj.filepath.endswith(".info.yml"):
            #print("Processing", f_obj.filepath)
            with open(f_obj.filepath, "r") as f:
                lines = f.readlines()
            for line in lines:
                line = line.strip("\n")
                if " = " in line:
                    header, value = line.split("=", 1)
                    header = header.lstrip(" ").rstrip(" ")
                    value = value.lstrip("\" ").rstrip("\" ")
                    if header.endswith("[]"):
                        if header not in f_obj.file_info:
                            f_obj.file_info[header] = []
                        f_obj.file_info[header].append(value)
                    else:
                        if header == dr_name:
                            if f_obj.filepath.endswith(".info"):
                                if value in dr7_core_modules:
                                    break
                            elif f_obj.filepath.endswith(".info.yml"):
                                if value in dr8_core_modules:
                                    break
                        f_obj.file_info[header] = value

        if dr_name in f_obj.file_info:
            plugin_name = f_obj.file_info[dr_name]
            f_obj.is_plugin = True
            f_obj.plugin_name = plugin_name
            
            # Create plugin object
            p_obj = Plugin(plugin_name, f_obj.filepath)
            
            # Assign plugin version
            if dr_version in f_obj.file_info:
                p_obj.version = f_obj.file_info[dr_version]
            # Assign plugin description
            if dr_description in f_obj.file_info:
                p_obj.description = f_obj.file_info[dr_description]
            # Assign plugin version
            if dr_version in f_obj.file_info:
                p_obj.version = f_obj.file_info[dr_version]
            
            p_obj.files[f_obj.filepath] = PluginFile(f_obj.filepath, f_obj.state, f_obj.mime_type, plugin_name)
        else:
            f_obj.is_plugin = False
            f_obj.analyze_later = True

        # Free memory holding all of the plugin info in f_obj.file_info
        f_obj.file_info = {}
        return p_obj

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
                #print("STATE", f_obj.state)
                #print(c_obj.plugins[f_obj.plugin_name])
                #print("BREAK", f_obj.filepath, f_obj.state, len(c_obj.plugins[f_obj.plugin_name].files))
                #for kys in c_obj.plugins[f_obj.plugin_name].files:
                #       print("KEYS", kys)
                #print(c_obj.plugins[f_obj.plugin_name].files[f_obj.filepath])
                c_obj.plugins[f_obj.plugin_name].files[f_obj.filepath].state = f_obj.state
                c_obj.plugins[f_obj.plugin_name].files[f_obj.filepath].version = c_obj.plugins[f_obj.plugin_name].version
