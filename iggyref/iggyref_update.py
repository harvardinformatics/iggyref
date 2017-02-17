#!/usr/bin/env python

import os.path as path
import os, sys, traceback
import re
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import yaml
import logging

from iggyref.repoClass import Repo
from iggyref.utils.util import mkdir_p
from iggyref import getReposAndCollections, parameterdefs, UserException

VERSION = '1.0'

LOGLEVELS = {
    'DEBUG'     : 10,
    'INFO'      : 20,
    'WARNING'   : 30,
    'ERROR'     : 40,
    'CRITICAL'  : 50,
}

# This is just for the purposes of setting tracebacks on
DEBUG = False

def update(inputArgs):

    # Setup arguments using the parameterdefs
    # First, apply any envs that are appropriate.
    # Second, setup the argument parser using these parameters with the 
    # envs as defaults.
    # Then, if a pref file is specified on the command line, 
    # get those values and use them to set anything they define.  
    # Finally, use any values passed on the command line.     
    
    try:
        # Add the repo and collection options based on what is in the iggyref.sources path
        repos = getReposAndCollections()
        repoChoices = repos.keys()
        parameterdefs.append(
            {
                'name'  : 'IGGYREF_REPOSITORIES',
                'switches'  : ['--repositories'],
                'nargs'     : '*',
                'default'   : repoChoices,
                'choices'   : repoChoices,
                'help'      : 'Repositories to update',
             }
        )
        
        for repo, colls in repos.iteritems():
            parameterdefs.append(
                {
                    'name'  : 'IGGYREF_%s_COLLECTIONS' % repo.upper(),
                    'switches' : '--%s-collections' % repo.lower(),
                    'nargs'    : '*',
                    'default'  : colls,
                    'choices'  : colls,
                    'required'  : False,
                    'help'     : 'Collections for %s. Only valid if repository is selected.' % repo,
                 }
            )
        
        # Check for environment variable values
        # Set to 'default' if they are found
        for parameterdef in parameterdefs:            
            if os.environ.get(parameterdef['name'],None) != None:
                value = os.environ.get(parameterdef['name'])
                if 'nargs' in parameterdef and parameterdef['nargs'] == '*':
                    value = re.split(r'\s*,\s*',value)
                parameterdef['default'] = value
                
                
        # Setup argument parser
        parser = ArgumentParser(description='Update public databases', formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument('-V', '--version', action='version', version=VERSION)
        
        
        # Use the parameterdefs for the ArgumentParser
        for parameterdef in parameterdefs:
            switches = parameterdef.pop('switches')
            if not isinstance(switches, list):
                switches = [switches]
                
            #Gotta take it off for add_argument
            name = parameterdef.pop('name')
            parameterdef['dest'] = name
            if 'default' in parameterdef:
                parameterdef['help'] += '  [default: %s]' % parameterdef['default']
            parser.add_argument(*switches,**parameterdef)
            
            # Gotta put it back on for later
            parameterdef['name'] = name
                   
        args = parser.parse_args()
        
        prefs = {}
        
        
        # If a prefs file was defined, go get those values and assign them.
        if args.IGGYREF_PREFERENCES_FILE:
            pfile = args.IGGYREF_PREFERENCES_FILE
            if not os.path.isfile(pfile):
                raise UserException('Specified preferences file %s does not exist.' % (pfile))
            try:
                prefs = yaml.load(open(pfile,'r'))
            except Exception, e:
                raise UserException('Unable to load preferences file %s\n%s' % (pfile,str(e)))
                
        # Set arg values if a preferences file was used
        for key, value in prefs.iteritems():
            setattr(args,key,value)
                
        #
        # Some post parse processing, including 
        #    - conversion of boolean-like values to booleans
        #    - array values to arrays if they are not
        #    - convert log level strings to logging numbers
        #    - valid lists are honored 
        #    - unset collection prefs for repositories that are not listed
        #
        for parameterdef in parameterdefs:
    
            value = getattr(args,parameterdef['name'])
            
            # Make sure list types are lists
            if 'nargs' in parameterdef and parameterdef['nargs'] == '*':            
                if not isinstance(value,list):
                    value = re.split(r'\s*,\s*',value)
                    
            # Translate booleans
            if 'action' in parameterdef and parameterdef['action'] == 'store_true':
                if isinstance(value,int):
                    if value == 0:
                        value = False
                    else:
                        value = True
                if isinstance(value,basestring):
                    if value == '' or value == '0' or value.lower() == 'false':
                        value = False
                    else:
                        value = True
            
            # Double check the choices values
            if 'choices' in parameterdef:
                valuelist = value
                if not isinstance(valuelist,list):
                    valuelist = [valuelist]
                for v in valuelist:
                    if not v in parameterdef['choices']:
                        raise UserException('Parameter %s is set to %s, but must be one of %s' % (parameterdef['name'],str(v), ','.join(parameterdef['choices'])))
    
            # Translate log levels into numbers
            if parameterdef['name'] == 'IGGYREF_LOG_LEVEL':
                value = LOGLEVELS[value]
                
            prefs[parameterdef['name']] = value
           
           
        # Remove collections for repositories that are not in the specified IGGYREF_REPOSITORIES list
        for repo in repoChoices:
            collectionname = 'IGGYREF_%s_COLLECTIONS' % repo.upper()
            if not repo in prefs['IGGYREF_REPOSITORIES'] and collectionname in prefs:
                del prefs[collectionname]
                  
        
        # Gotta have a repository dir
        if not prefs['IGGYREF_REPOSITORY_DIR']:
            raise UserException('A repository dir (--repository-dir or IGGYREF_REPOSITORY_DIR) must be set ')
        
        # Setup defaults for working directories
        if prefs['IGGYREF_WORKING_DIR'] is None:
            prefs['IGGYREF_WORKING_DIR'] = os.path.join(prefs['IGGYREF_REPOSITORY_DIR'],'.work')
        if prefs['IGGYREF_LOG_DIR'] is None:
            prefs['IGGYREF_LOG_DIR'] = os.path.join(prefs['IGGYREF_WORKING_DIR'],'log')
        if prefs['IGGYREF_DOWNLOAD_DIR'] is None:
            prefs['IGGYREF_DOWNLOAD_DIR'] = os.path.join(prefs['IGGYREF_WORKING_DIR'],'download')
        if prefs['IGGYREF_INTERMED_DIR'] is None:
            prefs['IGGYREF_INTERMED_DIR'] = os.path.join(prefs['IGGYREF_WORKING_DIR'],'intermed')
        if prefs['IGGYREF_TEMP_DIR'] is None:
            prefs['IGGYREF_TEMP_DIR'] = os.path.join(prefs['IGGYREF_WORKING_DIR'],'temp')
           
    
        # Output the final arrangement 
        if args.IGGYREF_VERBOSE or args.IGGYREF_DRY_RUN or args.IGGYREF_SHOW_PARAMETERS:
            for parameterdef in parameterdefs:
                if parameterdef['name'] in prefs:
                    print "%30s %s" % (parameterdef['name'],prefs[parameterdef['name']])
    
           
        # Now that log dir is determined, setup the logging 
        logging.basicConfig(datefmt = '%m/%d/%Y %I:%M:%S %p')
          
        logger = logging.getLogger('iggyref')
        
        if not os.path.exists(prefs['IGGYREF_LOG_DIR']):
            try:
                mkdir_p(prefs['IGGYREF_LOG_DIR'])
            except Exception, e:
                raise UserException('Unable to create log directory: %s' % str(e))
            
        logfilename = path.join(prefs['IGGYREF_LOG_DIR'], 'iggyref.log')
        
        # File formatter
        fh = logging.FileHandler(logfilename)
        fh.setLevel(prefs['IGGYREF_LOG_LEVEL'])
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    
        #Stdout formatter    
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(prefs['IGGYREF_LOG_LEVEL'])
        sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'))
        logger.addHandler(sh)
        
           
        # Actually process the repository collections
        sourceNames = prefs['IGGYREF_REPOSITORIES']
        if args.IGGYREF_VERBOSE: print '\nRepos to update: %s' % ', '.join(sourceNames)
        
        if not prefs['IGGYREF_SHOW_PARAMETERS']:
            for source in sourceNames:
                if args.IGGYREF_VERBOSE: print '\nUpdating repo %s... ' % source
                R = Repo(source, prefs)
                R.downloadCollections(prefs['IGGYREF_FORCE'])
                R.postProcessCollections(prefs['IGGYREF_FORCE_PROCESS'])

    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    
    except Exception, e:
        if hasattr(e, 'user_msg') and not DEBUG:
            sys.stderr.write('\niggyref: %s\n' % e.user_msg)
        else:
            sys.stderr.write('\niggyref: %s\n%s\n' % (str(e),traceback.format_exc()))
        return 2


if __name__ == "__main__":
    
    update(sys.argv[1:])
