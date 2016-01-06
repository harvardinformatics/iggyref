'''
Created on Dec 22, 2015

@author: Aaron Kitzmiller <aaron_kitzmiller@harvard.edu>
'''
import unittest
import os, sys, subprocess


class Test(unittest.TestCase):
    '''
    Make sure that environment variables, preferences files and command line arguments
    set things in the right priority
    '''

    def setUp(self):
        '''
        Remove existing environment variable settings.
        ''' 
        self.vars = [
            'IGGYREF_REPOSITORY_DIR',
            'IGGYREF_LOG_LEVEL',
            'IGGYREF_DB_TYPE',
            'IGGYREF_DB_HOST',
            'IGGYREF_DB',
            'IGGYREF_DB_USER',
            'IGGYREF_DB_PASSWORD',
            'IGGYREF_WORKING_DIR',
            'IGGYREF_LOG_DIR',
            'IGGYREF_DOWNLOAD_DIR',
            'IGGYREF_INTERMED_DIR',
            'IGGYREF_TEMP_DIR',
            'IGGYREF_FORCE',
            'IGGYREF_FORCE_PROCESS',
            'IGGYREF_PREFERENCES_FILE',
            'IGGYREF_VERBOSE',
            'IGGYREF_DRY_RUN',
            'IGGYREF_SHOW_PARAMETERS',
            'IGGYREF_REPOSITORIES',
            'IGGYREF_UNIPROT_COLLECTIONS',
            'IGGYREF_UCSC_COLLECTIONS',
            'IGGYREF_EBI_COLLECTIONS',
            'IGGYREF_NCBI_COLLECTIONS',
            'IGGYREF_ENSEMBL_COLLECTIONS',
        ]
        for v in self.vars:
            if v in os.environ:
                del os.environ[v]
         
        self.env = {
            'PATH'                  : os.environ['PATH'],
            'PYTHONPATH'            : os.environ.get('PYTHONPATH',''),
            'LD_LIBRARY_PATH'       : os.environ.get('LD_LIBRARY_PATH',''),
            'DYLD_LIBRARY_PATH'     : os.environ.get('DYLD_LIBRARY_PATH',''),
        }
        
        self.preferencesfile = 'preferences.yaml'
        self.logdir = 'log'

        print 'Current file is %s' % __file__


    def tearDown(self):
        if os.path.exists(self.preferencesfile):
            os.remove(self.preferencesfile)
            
        if os.path.exists(self.logdir):
            try:
                os.remove(os.path.join(self.logdir,'iggyref.log'))
                os.remove(os.path.join(self.logdir,'iggyref.db'))
                os.rmdir(os.path.join(self.logdir,'ncbi'))
            except Exception:
                pass
            os.rmdir(self.logdir)
    
    
    
    def testOverridePreferencesFile(self):
        '''
        Override env settings using a preferences file
        '''
        preffilevals = {
            'IGGYREF_REPOSITORY_DIR'    : ('repodir-override','repodir-override'),
            'IGGYREF_LOG_LEVEL'         : ('DEBUG',10),
            'IGGYREF_FORCE'             : ('False','False'),
            'IGGYREF_UCSC_COLLECTIONS'  : ('[human, mouse, rat]',"['human', 'mouse', 'rat']"),
            'IGGYREF_EBI_COLLECTIONS'   : ('pfam',"['pfam']"),      
        }
        
        
        with open(self.preferencesfile,'w') as f:
            for key, values in preffilevals.iteritems():
                f.write('%s: %s\n' % (key,values[0]))
                
        
        # Initial env variables 
        vals = {
            'IGGYREF_REPOSITORY_DIR'    : ('repodir',preffilevals['IGGYREF_REPOSITORY_DIR'][1]),
            'IGGYREF_LOG_LEVEL'         : ('INFO', preffilevals['IGGYREF_LOG_LEVEL'][1]),
            'IGGYREF_DB_TYPE'           : ('sqlite','sqlite'),
            'IGGYREF_DB_HOST'           : ('db-user','db-user'),
            'IGGYREF_DB'                : ('db','db'),
            'IGGYREF_DB_USER'           : ('user','user'),
            'IGGYREF_DB_PASSWORD'       : ('password','password'),
            'IGGYREF_WORKING_DIR'       : ('workdir','workdir'),
            'IGGYREF_LOG_DIR'           : (self.logdir,self.logdir),
            'IGGYREF_DOWNLOAD_DIR'      : ('downloaddir','downloaddir'),
            'IGGYREF_INTERMED_DIR'      : ('intermeddir','intermeddir'),
            'IGGYREF_TEMP_DIR'          : ('tempdir','tempdir'),
            'IGGYREF_FORCE'             : ('1',preffilevals['IGGYREF_FORCE'][1]),
            'IGGYREF_FORCE_PROCESS'     : ('','False'),
            'IGGYREF_VERBOSE'           : ('0','False'),
            'IGGYREF_DRY_RUN'           : ('Yes','True'),
            'IGGYREF_SHOW_PARAMETERS'   : ('1','True'),
            'IGGYREF_REPOSITORIES'      : ('uniprot,ucsc,ebi,ncbi',"['uniprot', 'ucsc', 'ebi', 'ncbi']"),
            'IGGYREF_UNIPROT_COLLECTIONS' : ('uniref100',"['uniref100']"),
            'IGGYREF_UCSC_COLLECTIONS'  : ('chicken_galGal3',preffilevals['IGGYREF_UCSC_COLLECTIONS'][1]),
            'IGGYREF_EBI_COLLECTIONS'   : ('interpro,pfam',preffilevals['IGGYREF_EBI_COLLECTIONS'][1]),
            'IGGYREF_NCBI_COLLECTIONS'  : ('nr',"['nr']"),
            'IGGYREF_ENSEMBL_COLLECTIONS' : ('fruitfly',None),
        }
       
        env = self.env
        
        for key, values in vals.iteritems():
            env[key] = values[0]
            
        # Construct the command line
        cmd = 'iggyref_update --show-parameters --preferences-file %s' % self.preferencesfile
        print 'Command string is %s' % cmd
        
        p = subprocess.Popen(cmd,shell=True,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = p.communicate()
        
        for key, values in vals.iteritems():
            if values[1] is None:
                self.assertTrue(key not in stdout, '%s should not be in the output.\n%s\n%s' % (key,stdout,stderr))
            else:
                self.assertTrue('%s %s' % (key, values[1]) in stdout, 'Value for %s should be %s\n%s\n%s' % (key,values[1],stdout,stderr))
        

    def testOverrideCommandLine(self):
        '''
        Override values on the command line after setting by env.
        '''
        
        # Command line switches to override
        cmdvals = {
            '--repository-dir' : ('repodir-override','repodir-override'),
            '--log-level'      : ('DEBUG',10),
            '--ucsc-collections' : ('human mouse rat',"['human', 'mouse', 'rat']"),
            '--force'          : ('','True'),
            '--ebi-collections' : ('pfam',"['pfam']"),
        }   
        
        # Initial env variables 
        vals = {
            'IGGYREF_REPOSITORY_DIR'    : ('repodir',cmdvals['--repository-dir'][1]),
            'IGGYREF_LOG_LEVEL'         : ('INFO', cmdvals['--log-level'][1]),
            'IGGYREF_DB_TYPE'           : ('sqlite','sqlite'),
            'IGGYREF_DB_HOST'           : ('db-user','db-user'),
            'IGGYREF_DB'                : ('db','db'),
            'IGGYREF_DB_USER'           : ('user','user'),
            'IGGYREF_DB_PASSWORD'       : ('password','password'),
            'IGGYREF_WORKING_DIR'       : ('workdir','workdir'),
            'IGGYREF_LOG_DIR'           : (self.logdir,self.logdir),
            'IGGYREF_DOWNLOAD_DIR'      : ('downloaddir','downloaddir'),
            'IGGYREF_INTERMED_DIR'      : ('intermeddir','intermeddir'),
            'IGGYREF_TEMP_DIR'          : ('tempdir','tempdir'),
            'IGGYREF_FORCE'             : ('1',cmdvals['--force'][1]),
            'IGGYREF_FORCE_PROCESS'     : ('','False'),
            'IGGYREF_VERBOSE'           : ('0','False'),
            'IGGYREF_DRY_RUN'           : ('Yes','True'),
            'IGGYREF_SHOW_PARAMETERS'   : ('1','True'),
            'IGGYREF_REPOSITORIES'      : ('uniprot,ucsc,ebi',"['uniprot', 'ucsc', 'ebi']"),
            'IGGYREF_UNIPROT_COLLECTIONS' : ('uniref100',"['uniref100']"),
            'IGGYREF_UCSC_COLLECTIONS'  : ('chicken_galGal3',cmdvals['--ucsc-collections'][1]),
            'IGGYREF_EBI_COLLECTIONS'   : ('interpro,pfam',cmdvals['--ebi-collections'][1]),
            'IGGYREF_NCBI_COLLECTIONS'  : ('nr',None),
            'IGGYREF_ENSEMBL_COLLECTIONS' : ('fruitfly',None),
        }
       
        env = self.env
        
        for key, values in vals.iteritems():
            env[key] = values[0]
            
        # Construct the command line
        cmdarr = ['iggyref_update','--show-parameters']
        for key, values in cmdvals.iteritems():
            cmdarr.append(key)
            cmdarr.append(values[0])
            
        cmd = ' '.join(cmdarr)
        print 'Command string is %s' % cmd
        
        p = subprocess.Popen(cmd,shell=True,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = p.communicate()
        
        for key, values in vals.iteritems():
            if values[1] is None:
                self.assertTrue(key not in stdout, '%s should not be in the output.\n%s\n%s' % (key,stdout,stderr))
            else:
                self.assertTrue('%s %s' % (key, values[1]) in stdout, 'Value for %s should be %s\n%s\n%s' % (key,values[1],stdout,stderr))
        

    def testAllByEnv(self):
        '''
        Set all of the variables using environment variables
        '''
        # Dict of tuples
        # key is the environment variable
        # first tuple entry is value to set
        # second is the expected result
        
        vals = {
            'IGGYREF_REPOSITORY_DIR'    : ('repodir','repodir'),
            'IGGYREF_LOG_LEVEL'         : ('INFO', 20),
            'IGGYREF_DB_TYPE'           : ('sqlite','sqlite'),
            'IGGYREF_DB_HOST'           : ('db-user','db-user'),
            'IGGYREF_DB'                : ('db','db'),
            'IGGYREF_DB_USER'           : ('user','user'),
            'IGGYREF_DB_PASSWORD'       : ('password','password'),
            'IGGYREF_WORKING_DIR'       : ('workdir','workdir'),
            'IGGYREF_LOG_DIR'           : (self.logdir,self.logdir),
            'IGGYREF_DOWNLOAD_DIR'      : ('downloaddir','downloaddir'),
            'IGGYREF_INTERMED_DIR'      : ('intermeddir','intermeddir'),
            'IGGYREF_TEMP_DIR'          : ('tempdir','tempdir'),
            'IGGYREF_FORCE'             : ('1','True'),
            'IGGYREF_FORCE_PROCESS'     : ('','False'),
            'IGGYREF_VERBOSE'           : ('0','False'),
            'IGGYREF_DRY_RUN'           : ('Yes','True'),
            'IGGYREF_SHOW_PARAMETERS'   : ('1','True'),
            'IGGYREF_REPOSITORIES'      : ('uniprot,ucsc',"['uniprot', 'ucsc']"),
            'IGGYREF_UNIPROT_COLLECTIONS' : ('uniref100',"['uniref100']"),
            'IGGYREF_UCSC_COLLECTIONS'  : ('chicken_galGal3',"['chicken_galGal3']"),
            'IGGYREF_EBI_COLLECTIONS'   : ('interpro,pfam',None),
            'IGGYREF_NCBI_COLLECTIONS'  : ('nr',None),
            'IGGYREF_ENSEMBL_COLLECTIONS' : ('fruitfly',None),
        }
        
        env = self.env
        
        for key, values in vals.iteritems():
            env[key] = values[0]
            
        cmd = 'iggyref_update --show-parameters'
        
        p = subprocess.Popen(cmd,shell=True,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        stdout,stderr = p.communicate()
        
        for key, values in vals.iteritems():
            if values[1] is None:
                self.assertTrue(key not in stdout, '%s should not be in the output.\n%s\n%s' % (key,stdout,stderr))
            else:
                self.assertTrue('%s %s' % (key, values[1]) in stdout, 'Value for %s should be %s\n%s\n%s' % (key,values[1],stdout,stderr))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()