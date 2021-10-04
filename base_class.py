from collections import OrderedDict
import subprocess
import json
import IPython
from cms_scan import cms_scan
import os

class Website():

        def __init__(self, website_path = None):

                self.website_path = website_path
                self.compromised             = None 
                self.rollback                = None 
                self.failed_rollback         = None 
                self.num_comp_files          = None 
                self.num_drop_files          = None 
                self.num_all_files           = None 
                self.compromise_window       = None 
                self.phases                  = None 
                self.lmd                     = None
                self.cms                     = None
                self.cms_version             = None

                if website_path:
                        self.cms, self.cms_version  = cms_scan(website_path)
        
class FileMetadata():
        def __init__(self, filepath = None, filename = None, state = None, mime = None):
                self.file_info           = {}
                self.filename                = filename # filename only
                self.filepath                = filepath # full filepath wrt website-xxx/<filepath>
                self.state                   = state        # holds A | D | M (added, deleted, modified etc.)
                self.empty_file          = None         # If the file is empty, this is True
                self.mime_type           = mime
                self.extension           = None         # file extension    (filename.<extension>)
                self.hidden_file         = None         # True if file is hidden
                self.in_hidden_dir   = None         # If the file belongs to a directory 
                                                                                # hidden at some level, this is True
                self.suspicious_tags = []               # If the file is flagged suspicious by
                                                                                # of our analyses, append string here
                self.is_plugin = None
                self.plugin_name = None
                self.analyze_later = None
        

class Commit():
        def __init__(self, commit_obj = None):
                self._file_list = []                        # FileMetadata object at each commit ID
                self.commit_obj = commit_obj
                if commit_obj:
                        self.commit_id  = self.commit_obj.hexsha
                        self.date               = self. commit_obj.authored_datetime 
                        self.parent         = self.commit_obj.parents[0] if self.commit_obj.parents else None #parent commit object corresponds to commit id just before the present commit
                self.tags               = []                        # If the commit is flagged suspicious by of our analyses, append string here
                self.initial        = None # If the commit is initial commit in our repo
                self.filetypes_count = OrderedDict()
                self.diff_count = None
                self.grouped_plugin = {}
                self.plugins = {}
                self.num_active_plugins = None
                self.has_mal_plugins = None
                self.mal_pnames = []
                self.num_files = None
                self.plugins_changed= None
                self.num_mal_plugins = 0
                self.tot_mal_pfiles = 0
        
class Plugin():
        def __init__(self, plugin_name = None, plugin_path = None):
                self.plugin_name = plugin_name
                self.can_plugin_name = None
                self.plugin_base_path = os.path.dirname(os.path.abspath(plugin_path))
                self.files = {}
                self.version = None
                self.author = None
                self.author_uri = None
                self.author_email = None
                self.plugin_uri = None
                self.num_files = None
                self.plugin_score = None
                self.plugin_state = None
                self.license = None
                self.description = None
                self.num_file_types = {}
                self.cms = None
                self.fake_wp_plugin = None
                self.is_mal = None
                self.is_theme = None
                self.num_mal_p_files = 0
                self.theme_name = None
                self.error = False


class PluginFile():
        def __init__(self, filepath = None, state = None, mime = None, plugin_name = None):
                self.plugin_name         = plugin_name
                self.filepath                = filepath # full filepath wrt website-xxx/<filepath>
                self.state                   = state        # holds A | D | M (added, deleted, modified etc.)
                self.version        = None
                self.mime_type           = mime
                self.suspicious_tags = [] 
                self.is_malicious           = None
                self.extracted_results = {} #Key suspicious tag. Nested dictionary of values
                self.ast               = None
