'''
Copyright (c) 2015
Harvard FAS Research Computing
All rights reserved.

@author: Aaron Kitzmiller
'''



class UserException(Exception):
    '''
    I can actually get a message from this exception
    '''
    def __init__(self,message):
        super(UserException,self).__init__(message)
        self.user_msg = message        


#
# Initialize the configuration with defaults and user config file
#

def getReposAndCollections():
    """
    Returns a dictionary of collection names keyed by repo name.
    """
    
    # Add options from the repo classes
    # First, iterate through the sources path to get all of the available modules
    import os
    import pkgutil,inspect
    import iggyref.sources as sources
    
    repos = {}
    # Load the modules in the soruces path.  Use iter_modules to avoid 
    # sub packages
    for loader, name, is_pkg in pkgutil.iter_modules(sources.__path__):
        if is_pkg:
            repos[name] = []
            
    for repo in repos.keys():
        for loader, name, is_pkg in pkgutil.iter_modules([os.path.join(sources.__path__[0],repo,'collections')]):
            repos[repo].append(name)
            
    return repos
                
                

parameterdefs = [
    {
        'name'      : 'IGGYREF_REPOSITORY_DIR',
        'switches'  : ['--repository-dir'],
        'help'      : 'Directory for genomes and databases',
     },
    {
        'name'      : 'IGGYREF_LOG_LEVEL',
        'switches'  : ['-l','--log-level'],
        'help'      : 'Level of logging detail',
        'choices'   : ['INFO','DEBUG','WARNING','ERROR','CRITICAL'],
        'default'   : 'INFO',
     },
    {
        'name'      : 'IGGYREF_DB_TYPE',
        'switches'  : ['--db-type'],
        'help'      : 'Database type.',
        'default'   : 'sqlite',
     },
    {
        'name'      : 'IGGYREF_DB_HOST',
        'switches'  : ['--db-host'],
        'help'      : 'Database hostname if not using sqlite',
        'default'   : 'localhost',
        
     },
    {
        'name'      : 'IGGYREF_DB',
        'switches'  : ['--database'],
        'help'      : 'Database name if not using sqlite.',
        'default'   : 'iggypipe_db',
     },
    {
        'name'      : 'IGGYREF_DB_USER',
        'switches'  : ['--db-user'],
        'help'      : 'Database user if not using sqlite.',
        'default'   : 'iggypipe'
     },
    {
        'name'      : 'IGGYREF_DB_PASSWORD',
        'switches'  : ['--db-password'],
        'help'      : 'Database password if not using sqlite.',
        'default'   : 'iggypipe'
     },
    {
        'name'      : 'IGGYREF_WORKING_DIR',
        'switches'  : ['--working-dir'],
        'help'      : 'Working directory',
     },
    {
        'name'      : 'IGGYREF_LOG_DIR',
        'switches'  : ['--log-dir'],
        'help'      : 'Log file directory',
     },
    {
        'name'      : 'IGGYREF_DOWNLOAD_DIR',
        'switches'  : ['--download-dir'],
        'help'      : 'Root of the path to which files will be downloaded',
     },
    {
        'name'      : 'IGGYREF_INTERMED_DIR',
        'switches'  : ['--intermed-dir'],
        'help'      : 'Intermediate download directory',
     },
    {
        'name'      : 'IGGYREF_TEMP_DIR',
        'switches'  : ['--temp-dir'],
        'help'      : 'Temp dir',
     },
    {
        'name'      : 'IGGYREF_FORCE',
        'switches'  : ['--force','-f'],
        'action'    : 'store_true',
        'default'   : False,
        'help'      : 'Force download and postprocessing of all files in repo.',
     },
    {
        'name'      : 'IGGYREF_FORCE_PROCESS',
        'switches'  : ['--force-process'],
        'action'    : 'store_true',
        'default'   : False,
        'help'      : 'Force postprocessing only.',
     },
    {
        'name'      : 'IGGYREF_PREFERENCES_FILE',
        'switches'  : ['--preferences-file','-p'],
        'help'      : 'Preferences file.',
     },
    {
        'name'      : 'IGGYREF_VERBOSE',
        'switches'  : ['--verbose','-v'],
        'action'    : 'store_true',
        'default'   : False,
        'help'      : 'Increase chattiness of output.',
     },
    {
        'name'      : 'IGGYREF_DRY_RUN',
        'switches'  : ['--dry-run'],
        'action'    : 'store_true',
        'default'   : False,
        'help'      : "Print out what would happen, but don't do it.",
     },
    {
        'name'      : 'IGGYREF_SHOW_PARAMETERS',
        'switches'  : ['--show-parameters'],
        'action'    : 'store_true',
        'default'   : False,
        'help'      : 'Just print the parameter settings.',
     },
]
