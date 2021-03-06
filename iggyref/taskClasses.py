import logging
import os.path as path, os
import shutil
from iggyref.utils.util import flatlist
from iggyref.rFileClass import rFile
from iggyref.postProcess.genePred2gtf import genePred2gtf
from iggyref.postProcess.fasta2index import fasta2index
from iggyref.postProcess.util import decompress, untar, concatFiles

logger = logging.getLogger('iggyref')


class baseTask(object):

    @classmethod
    def getInstance(cls, taskDict, C):
        taskName = taskDict['taskName']
        if taskName.lower() == 'unzip':
            return Unzip(taskDict, C)
        elif taskName.lower() == 'unzip-untar':
            return Unzip_untar(taskDict, C)
        elif taskName.lower() == 'unzip-untar-merge':
            return Unzip_untar_merge(taskDict, C)
        elif taskName.lower() in ['unzip-txt2gtf', 'txt2gtf']:
            return Txt2gtf(taskDict, C)
        elif taskName.lower() == 'fasta2index':
            return Fasta2index(taskDict, C)
        elif taskName.lower() == 'nrremoveolddirs':
            return NrRemoveOldDirs(taskDict, C)
        else:
            raise Exception('Unrecognized taskName: %s' % taskName)

    def __init__(self, taskDict, C):
        self.C = C

        inFileNames = list()
        if 'inFiles' in taskDict.keys():
            inFileNames = taskDict['inFiles']
        if type(inFileNames) != list:
            inFileNames = [inFileNames]

        outFileNames = list()
        if 'outFiles' in taskDict.keys():
            outFileNames = taskDict['outFiles']
        if type(outFileNames) != list:
            outFileNames = [outFileNames]

        self.inFiles = list()
        for filename in inFileNames:
            self.inFiles.append(self.getFileObj(filename))

        self.outFiles = list()
        for filename in outFileNames:
            self.outFiles.append(self.getFileObj(filename))

    def getFileObj(self, filename):
        allFiles = self.C.allFiles()
        filesNames = [x.name for x in allFiles]
        try:
            File = allFiles[filesNames.index(filename)]
        except:
            try: 
                File = rFile(filename, self.C.fileProperties[filename])
            except:
                File = rFile(filename)
            self.C.setLocalFilePath(File)
        return File

    def validateInOut(self, numIn, numOut):
        if len(self.inFiles) not in flatlist(numIn):
            raise Exception('In %s: Expected %s input file(s) for task %s, found %s: %s' % (self.C, numIn, self.taskName, len(self.inFiles), ', '.join(map(str,self.inFiles))))
        if len(self.outFiles) not in flatlist(numOut):
            raise Exception('In %s: Expected %s output file(s) for task %s, found %s: %s' % (self.C, numIn, self.taskName, len(self.outFiles), ', '.join(map(str,self.outFiles))))

    def validateExt(self, filename, extensions):
        if type(extensions) != list:
            extensions = [extensions]
        for ext in extensions:
            if filename.lower()[-len(ext):] == ext.lower():
                return
        raise Exception('Did not find file extension(s) ["%s"] in filename %s. Collection, Task: %s, %s' % ('", "'.join(extensions), filename, self.C, self))
    
    def __repr__(self):
        return '<Task(%s -- %s -- %s)>' % (self.taskName, ','.join(map(str,self.inFiles)), ','.join(map(str,self.outFiles)))


class Unzip(baseTask):
    def __init__(self, taskDict, C):
        baseTask.__init__(self, taskDict, C)
        self.taskName = 'unzip'

        self.validateInOut(1,[0,1])  # 1 input, 0 or 1 outputs 

        inFile = self.inFiles[0]
        self.validateExt(inFile.localPath, ['.gz'])

        if len(self.outFiles) == 0:
            outFileName = inFile.name[:-3]
            outFile = self.getFileObj(outFileName)
            self.outFiles.append(outFile)

    def run(self):
        decompress(self.inFiles[0].localPath, destFile = self.outFiles[0].localPath)


class Unzip_untar(baseTask):
    def __init__(self, taskDict, C):
        baseTask.__init__(self, taskDict, C)
        self.taskName = 'unzip-untar'

        self.validateInOut(1,[0,1])  # 1 input, 0 or 1 outputs 

        inFile = self.inFiles[0]
        self.validateExt(inFile.localPath, '.tar.gz')

        if len(self.outFiles) == 0:  # if output was unspecified, untar files into directory containing input file
            outFileName = inFile.name[:-7]
            outFile = self.getFileObj(outFileName)
            outFile.localPath = path.dirname(inFile.localPath)  
            self.outFiles.append(outFile)

    def run(self):
        untar(self.inFiles[0].localPath, destDir = self.outFiles[0].localPath) 


class Unzip_untar_merge(baseTask):
    def __init__(self, taskDict, C):
        baseTask.__init__(self, taskDict, C)
        self.taskName = 'unzip-untar-merge'  
        self.validateInOut(1,2)  # 1 input, 2 outputs
        self.validateExt(self.inFiles[0].localPath, '.tar.gz')

    def run(self):
        untarredDir = untar(self.inFiles[0].localPath, self.outFiles[0].localPath)
        concatFiles(untarredDir, outFile = self.outFiles[1].localPath)


class Txt2gtf(baseTask):
    def __init__(self, taskDict, C):
        baseTask.__init__(self, taskDict, C)
        self.taskName = 'txt2gtf'  
        self.validateInOut(1,1)  # 1 inputs, 1 output

        self.genePredFile = self.inFiles[0].localPath
        self.gtfFile = self.outFiles[0].localPath

        self.validateExt(self.genePredFile, '.txt')
        self.validateExt(self.gtfFile, '.gtf')

    def run(self):
        genePred2gtf(self.genePredFile, self.C.repo.source, outFile = self.gtfFile)


class Fasta2index(baseTask):
    def __init__(self, taskDict, C):
        baseTask.__init__(self, taskDict, C)
        self.taskName = 'fasta2index'  

    def run(self):
        self.validateInOut(1,0)  # 1 input, 0 outputs
        inFile = self.inFiles[0].localPath
        fasta2index(inFile, self.C)
        
        
class NrRemoveOldDirs(baseTask):
    '''
    If there are 3 directories in the ncbi/nr repository, removes the oldest one.
    '''
    def __init__(self, taskDict, C):
        baseTask.__init__(self, taskDict, C)
        self.taskName = 'NrRemoveOldDirs'  

    def run(self):
        logger.debug('Checking dir for more than %d subdirs %s' % (self.C.properties['maxnrdirs'], self.C.finalDir))

        if os.path.exists(self.C.finalDir):
            dirs = [d for d in os.listdir(self.C.finalDir) if os.path.isdir(os.path.join(self.C.finalDir, d))]
            if len(dirs) >= self.C.properties['maxnrdirs']:
                dirs = sorted(dirs, key=lambda d: os.path.getctime(os.path.join(self.C.finalDir, d)))
                while len(dirs) >= self.C.properties['maxnrdirs']:
                    toremove = os.path.join(self.C.finalDir,dirs.pop(0))                   
                    logger.debug('Gonna remove dir %s' % toremove)
                    try:
                        shutil.rmtree(toremove, ignore_errors=False)
                    except Exception, e:
                        logger.info('Failure while removing old nr path \n%s' % str(e))
