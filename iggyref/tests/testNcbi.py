'''
Created on Dec 22, 2015

@author: aaronkitzmiller
'''
import unittest, os, shutil, sys
import datetime
import logging
import math

# Clean up in the tearDown
CLEAN = True


# Setup logging before the imports so they can't set it for me
LOGDIR = '%s/log' % os.getcwd()
LOGLEVEL = 'DEBUG'
LOGGINGLEVEL = logging.DEBUG

try:
    os.mkdir(LOGDIR)
except Exception:
    pass

logfilename = os.path.join(LOGDIR,'iggyref.log')
logger = logging.getLogger('iggyref')

logger.setLevel(LOGGINGLEVEL)

# Stdout formatter
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(LOGGINGLEVEL)
sh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'))
logger.addHandler(sh)

# File formatter
fh = logging.FileHandler(logfilename)
fh.setLevel(LOGGINGLEVEL)
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)


from iggyref.repoClass import Repo
from iggyref.tests import mockIggyRefFTP
from iggyref.utils.util import mkdir_p


class Test(unittest.TestCase):
    '''
    Test ncbi collection handling
    '''

    def setUp(self):
        
        self.workingdir = os.path.abspath(os.path.dirname(__file__))
        self.cwd = os.path.abspath(os.getcwd())
        os.chdir(self.workingdir)
#        raise Exception('wd %s; cwd %s' % (self.workingdir,os.getcwd()))
        
        # Setup dirs via env
        self.dirs = {
            'IGGYREF_REPOSITORY_DIR' : 'repo',
            'IGGYREF_WORKING_DIR'   : 'work',
            'IGGYREF_LOG_DIR'       : LOGDIR,
            'IGGYREF_DOWNLOAD_DIR'  : 'download',
            'IGGYREF_INTERMED_DIR'  : 'intermed',
            'IGGYREF_TEMP_DIR'      : 'work/temp',
            
        }
        for key, idir in self.dirs.iteritems():
            if key != 'IGGYREF_LOG_DIR':
                shutil.rmtree(idir, ignore_errors=True)
                try:
                    os.mkdir(idir)
                except Exception:
                    pass
            
        # Only use 00-02 to make sure that 03 is not included
        self.nrs = [
            'nr.00',
            'nr.01',
            'nr.02',
        ]
        self.goodchecksum = '85ea83e206562392415c16737ab4a01a nr.00.tar.gz'
        self.checksumfilename = 'blast/db/nr.00.tar.gz.md5'


    def clean(self):
        '''
        Clean up after the tests are run
        '''
        global CLEAN
        
        if CLEAN:
            for key in ['IGGYREF_REPOSITORY_DIR','IGGYREF_WORKING_DIR','IGGYREF_DOWNLOAD_DIR','IGGYREF_INTERMED_DIR','IGGYREF_TEMP_DIR']:
                if os.path.exists(self.dirs[key]):
                    shutil.rmtree(self.dirs[key], ignore_errors=True)

            
    def tearDown(self):
        self.clean()
        with open(self.checksumfilename,'w') as f:
            f.write('%s\n' % self.goodchecksum)
        os.chdir(self.cwd)
        
    
    def testRemoveOlder(self):
        '''
        If there are already two nr dirs, after writing the third,
        remove the oldest
        '''
        #
        # Setup directories
        #
        nrdir = os.path.join(self.dirs['IGGYREF_REPOSITORY_DIR'],'ncbi','nr')
        mkdir_p(nrdir)
        
        # Two quarters ago
        qminustwodate = datetime.datetime.now() + datetime.timedelta(weeks=-24)
        qminustwo = (qminustwodate.month)//3.0 + 1
        qminustwodir = '%d-%d' % (qminustwodate.year, qminustwo)
        os.mkdir(os.path.join(nrdir,qminustwodir))
        
        # One quarter ago
        qminusonedate = datetime.datetime.now() + datetime.timedelta(weeks=-12)
        qminusone = (qminusonedate.month)//3.0 + 1
        qminusonedir = '%d-%d' % (qminusonedate.year, qminusone)
        os.mkdir(os.path.join(nrdir,qminusonedir))
        
        self.assertTrue(os.path.isdir(os.path.join(nrdir,qminustwodir)),'Directory %s not created' % qminustwodir)
        
        
        #
        # Run the download
        #
        extraenv = {
            'IGGYREF_REPOSITORIES'      : ['ncbi'],
            'IGGYREF_NCBI_COLLECTIONS'  : ['nr'],
            'IGGYREF_FORCE'             : True,
            'IGGYREF_LOG_LEVEL'         : LOGLEVEL,
            'IGGYREF_DRY_RUN'           : False,
            'IGGYREF_DB_TYPE'           : 'sqlite',
        }
        env = dict(self.dirs,**extraenv)
        
        ftp = mockIggyRefFTP('ncbi',self.dirs['IGGYREF_TEMP_DIR'])
                
        for source in env['IGGYREF_REPOSITORIES']:
            R = Repo(source, env, ftp=ftp)
            R.downloadCollections(True)       
            R.postProcessCollections(True)
        
        #
        # Qminustwo is gone
        #
        self.assertFalse(os.path.exists(os.path.join(nrdir,qminustwodir)),'Directory %s still exists!' % qminustwodir)
        
        
    def testChecksumFail(self):
        '''
        Make sure that a bad checksum fails
        '''
          
        # Write a bad checksum that should cause an error
        with open(self.checksumfilename,'w') as f:
            f.write('badchecksum nr.00.tar.gz')
          
        extraenv = {
            'IGGYREF_REPOSITORIES'      : ['ncbi'],
            'IGGYREF_NCBI_COLLECTIONS'  : ['nr'],
            'IGGYREF_FORCE'             : False,
            'IGGYREF_LOG_LEVEL'         : LOGLEVEL,
            'IGGYREF_DRY_RUN'           : False,
            'IGGYREF_DB_TYPE'           : 'sqlite',
        }
        env = dict(self.dirs,**extraenv)
        ftp = mockIggyRefFTP('ncbi',self.dirs['IGGYREF_TEMP_DIR'])
          
        try:
            for source in env['IGGYREF_REPOSITORIES']:
                R = Repo(source, env, ftp=ftp)
                R.downloadCollections(env['IGGYREF_FORCE'])       
                R.postProcessCollections(True)
        except Exception, e:
            self.assertTrue('failed remote/local checksum comparison' in str(e))
              
           
        #   
        # Write the good one and make sure it doesn't cause an error
        #
        with open(self.checksumfilename,'w') as f:
            f.write('%s\n' % self.goodchecksum)
  
        for source in env['IGGYREF_REPOSITORIES']:
            R = Repo(source, env, ftp=ftp)
            R.downloadCollections(True)       
            R.postProcessCollections(True)                
        
        

    def testNr(self):
        '''
        Test the download and processing of the nr collection.  
        
        Make sure the FORCE=False will not download and FORCE=True will when there is an 
        existing set of matching files.
        '''
        extraenv = {
            'IGGYREF_REPOSITORIES'      : ['ncbi'],
            'IGGYREF_NCBI_COLLECTIONS'  : ['nr'],
            'IGGYREF_FORCE'             : True,
            'IGGYREF_LOG_LEVEL'         : LOGLEVEL,
            'IGGYREF_DRY_RUN'           : False,
            'IGGYREF_DB_TYPE'           : 'sqlite',
        }
        env = dict(self.dirs,**extraenv)
        
        ftp = mockIggyRefFTP('ncbi',self.dirs['IGGYREF_TEMP_DIR'])
        
        
        for source in env['IGGYREF_REPOSITORIES']:
            R = Repo(source, env, ftp=ftp)
            R.downloadCollections(env['IGGYREF_FORCE'])       
            R.postProcessCollections(True)
         
        #   
        # Get all of the files and compare them to a benchmark list
        #
        files = []
        for root, dirnames, filenames in os.walk(self.dirs['IGGYREF_REPOSITORY_DIR']):
            for filename in filenames:
                files.append(os.path.join(root, filename))
                
        quarter = (datetime.datetime.now().month)//3.0 + 1
        expectedsubdir = '%d-%d' % (datetime.datetime.now().year, quarter)
        
        expectednrfiles = []
        for nr in self.nrs:
            for ext in ['phd','phi','phr','pin','pnd','pni','pog','ppd','ppi','psd','psi','psq']:
                expectednrfiles.append(os.path.join(self.dirs['IGGYREF_REPOSITORY_DIR'],'ncbi','nr',expectedsubdir,'%s.%s' % (nr,ext)))
        expectednrfiles.append(os.path.join(self.dirs['IGGYREF_REPOSITORY_DIR'],'ncbi','nr',expectedsubdir,'nr.pal'))
                
        expectedstr = ','.join(sorted(expectednrfiles))
        actualstr = ','.join(sorted(files))
        self.assertTrue(expectedstr == actualstr, 'nr files do not match: \nExpected: %s\nActual:   %s' % (expectedstr,actualstr))          
        
        
        # Do it a second time with no FORCE
        force = False
        for source in env['IGGYREF_REPOSITORIES']:
            R = Repo(source, env, ftp=ftp)
            R.downloadCollections(force)       
            R.postProcessCollections(True)
            
        # Check the log 
        with open(logfilename,'r') as f:
            logstr = f.read()
            for nr in self.nrs:
                checkphrase = 'Not downloading %s.tar.gz since remote, local timestrings match' % nr
                self.assertTrue(checkphrase in logstr, 'Log file does not contain match phrase: %s\n%s' % (checkphrase,logstr))
                        
        
        # Do it a third time with FORCE
        force = True
        for source in env['IGGYREF_REPOSITORIES']:
            R = Repo(source, env, ftp=ftp)
            R.downloadCollections(True)       
            R.postProcessCollections(True)

        # Check the log 
        with open(logfilename,'r') as f:
            loglines = f.readlines()
            logstr = ' '.join(loglines[-30:])
            for nr in self.nrs:
                checkphrase = 'Downloading blast/db/%s.tar.gz' % nr
                self.assertTrue(checkphrase in logstr, 'Log file does not contain match phrase: %s\n%s' % (checkphrase,logstr))
            
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()