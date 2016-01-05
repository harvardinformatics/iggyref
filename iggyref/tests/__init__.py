'''
Created on Dec 29, 2015

@author: Aaron Kitzmiller <aaron_kitzmiller@harvard.edu>
'''
import shutil, os, os.path as path, posixpath, re
from iggyref.FTPclass import iggyrefFTP

class mockIggyRefFTP(iggyrefFTP):
    
    def __init__(self, site, tempDir):
        self.tempDir = tempDir
        self.site = site

    def getTimeString(self,path):
        return '2016-01-01'        
    
    '''
    Copy instead of doing an FTP operation
    '''
    def copyFile(self, srcFile, destFile, overwrite = True):
        '''
        Just does a copy from the test directory
        '''
        if srcFile.startswith('/'):
            srcFile = srcFile[1:]
            
        if os.path.isfile(srcFile):
            shutil.copy(srcFile, destFile)
        else:
            raise Exception('No such file or directory %s' % srcFile)

    def closeFtp(self):
        pass
