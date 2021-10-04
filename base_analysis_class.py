class BaseAnalysisClass:
    '''Each analysis can be processed at a website level, commit level, file 
    level, or file line level. Please add your code to the respective level  
    in the derived class
    '''

    def __init__(self):
        # This tag specifies if the check is complete upon first match or if all
        # the lines need to be analyzed. (Implemented for processFileLine)
        self.first_match = None

    def processWebsite(self, website_object):
        pass

    def processCommit(self, commit_object):
        pass

    def processFile(self, file_object):
        pass

    def postProcessFile(self, file_object):
        pass

    def processFileLine(self, line):
        pass

    def postProcessCommit(self, commit_obj):
        pass

    # TODO Post processing might require different objects, think this through
    def postProcessWebsite(self, commits, website = None):
        pass

    # For malicious plugin detection, we need to reprocess the file
    def reprocessFile(self, file_object, r_data):
        pass

    # For malicious plugin detection, we need to reprocess the commit
    def postReprocessCommit(self, commit_object):
        pass

    
