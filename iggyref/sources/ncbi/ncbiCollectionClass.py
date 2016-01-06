import os.path as path
import datetime
import math
from iggyref.baseCollectionClass import baseCollection
from iggyref.utils.util import parse_NCBI_aliasFile, extractFromTar, mkdir_p


# ncbi Collection class

class ncbiCollection(baseCollection):

    def __init__(self, primaryID, repo, ftpConn = None):

        collMod = __import__('iggyref.sources.%s.collections.%s' % (repo.source, primaryID),fromlist=[primaryID])
        collProp = getattr(collMod,'collectionProperties')
        if collProp['aliasFileType']:
            aliasFilename = '%s.%s' % (primaryID, collProp['aliasFileType'])
            dbFile_ftpSubDir = collProp['dbFileProp']['ftpSubDir']
        
            if not ftpConn:  #look at local pal/nal flie for file list
                aliasFile = path.join(repo.downloadDir, aliasFilename)

            else: #get remote pal/nal file

                firstDBFilename = '%s.00.tar.gz' % primaryID
#                aliasFilename = path.join('%s.00' % primaryID,aliasFilename)
                firstDBFile_remote = path.join( dbFile_ftpSubDir, firstDBFilename )
                firstDBFile_local = path.join( repo.tempDir, firstDBFilename )
                ftpConn.copyFile(firstDBFile_remote, firstDBFile_local)            

                print "Extracting %s from %s to %s" % (aliasFilename,firstDBFile_local,repo.tempDir)
                extractFromTar(firstDBFile_local, aliasFilename, repo.tempDir)
                aliasFile = path.join(repo.tempDir, aliasFilename)

                
            #set collection fileList from .pal/.nal alias file
            dbFiles = ['%s.tar.gz' % x for x in parse_NCBI_aliasFile(aliasFile)]
            collProp['fileList'] = dbFiles

            for filename in dbFiles:

                #set file properties
                collProp['fileProperties'][filename]                  = dict()
                collProp['fileProperties'][filename]['ftpSubDir']     = dbFile_ftpSubDir
                collProp['fileProperties'][filename]['checksumFile']  = '%s.md5' % filename

                #add task 
                collProp['tasks'].append( dict(taskName = 'unzip-untar', inFiles = filename) )

        baseCollection.__init__(self, primaryID, repo, ftpConn = ftpConn, collectionProperties = collProp)

        self.setLocalDirs()
        self.collectionSetup()


    def setLocalFilePath(self, File):
        '''
        Sets a subdirectory that is a combination of the year and "quarter",
        e.g. 2015-1
        '''
        if not File.localPath:
            quarter = (datetime.datetime.now().month - 1)// 3.0 + 1
            subdir = '%d-%d' % (datetime.datetime.now().year, quarter)
            pth = path.join(self.downloadDir,subdir)
            mkdir_p(pth)
            File.localPath = path.join(pth, File.name)


    def setFtpFilePath(self, File):
        File.ftpPath = path.join(File.ftpSubDir, File.name)


    def setChecksumFtpFilePath(self, File):
        if not File.checksumFile: raise Exception('File.checksumFile must be set')
        File.checksumFtpPath = path.join(File.ftpSubDir, File.checksumFile)

