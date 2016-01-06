import os, glob, sys, logging, re, traceback
import os.path as path
from iggyref.FTPclass import iggyrefFTP
from iggyref.DBclass import iggyrefDB
from iggyref.rFileClass import rFile
from iggyref.baseCollectionClass import baseCollection
from iggyref.depGraph.graphClasses import depGraph
from iggyref.utils.util import intersect, flatten, mkdir_p, unique, insert, pysync


logger = logging.getLogger('iggyref')

class Repo(object):


    def __init__(self, source, prefs, selectedCollections = None, ftp = None):

        os.umask(002)

        self.pref = prefs
        
        if not selectedCollections:
            self.selectedCollections = self.pref['IGGYREF_%s_COLLECTIONS' % source.upper()]  #source is one of ebi, ucsc, ncbi, etc.
        else:
            self.selectedCollections = selectedCollections

        repoPropertiesMod = __import__('iggyref.sources.%s.properties' % source, fromlist=['properties'])
        self.properties = getattr(repoPropertiesMod,'repoProperties')

        self.logDir = path.join(self.pref['IGGYREF_LOG_DIR'], source)
        self.tempDir = path.join(self.pref['IGGYREF_TEMP_DIR'], source)
        self.downloadDir = path.join(self.pref['IGGYREF_DOWNLOAD_DIR'], source) 
        self.finalDir = path.join(self.pref['IGGYREF_REPOSITORY_DIR'], source)

        try:
            mkdir_p(self.logDir)
            mkdir_p(self.tempDir)
            mkdir_p(self.downloadDir)
            mkdir_p(self.finalDir)
        except Exception, e:
            raise UserException('Unable to create directories for repository %s: %s' % (source,str(e)))

#        self.log = logging.getLogger('iggyref')

        self.source = source
        self.updatedCollections = list()
        self.db = None
        self.ftp = ftp
        
        self.dryrun = self.pref['IGGYREF_DRY_RUN']


    def updateSpeciesTable(self, C):
        if C.type == 'genome':
            self.db.addSpeciesCommonName(C.secondaryID, C.properties['commonName'])


    def downloadCollections(self, force=False):
        
        if not self.db: self.db =  iggyrefDB(self.pref)
        
        if self.pref['IGGYREF_DRY_RUN']:
            print 'Setting up ftp connection'
        else:
            if not self.ftp: self.ftp = iggyrefFTP(self.properties['ftpSite'], path.join(self.tempDir, 'temp_ftp'))
        
        for primaryID in self.selectedCollections:
            if self.pref['IGGYREF_DRY_RUN']:
                print 'Processing collection %s' % primaryID
                continue
            
            C = baseCollection.getInstance(primaryID, self, self.ftp)
            if not C: raise Exception('Unable to instantiate Collection object for %s from %s' % (primaryID, self.source))
            self.updatedCollections.append(C)
            self.updateSpeciesTable(C)

            logger.info('Collection to download: ' + primaryID)
            logger.info('Filenames: ' + ', '.join(map(str,C.downloadFiles)))

            for File in C.downloadFiles:
                C.setFtpFilePath(File)
                #get remote timestamp. Get checksum from any previous download of this file
                C.setRemoteTimeString(File)
                logger.info('Remote TimeString for file %s: %s' % (File.ftpPath, File.remoteTimeString))
                C.setRemoteChecksum(File)
                logger.info('Remote checksum for file %s: %s' % (File.ftpPath, File.remoteChecksum))
                File.prevChecksum = self.db.getFileAttribute(File, C, 'download_ended', 'checksum')  #checksum of file the last time it was downloaded

                #check if we need to download this file, based on timestamps and checksums
                if not force and path.isfile(File.localPath):
                    #compare stored timestring to remote timestring:
                    prevTimeString = self.db.getFileAttribute(File, C, 'download_ended', 'remoteTimeString') #remote timestamp from previous download
                    logger.debug('TimeString of %s in DB: %s' % (File.name, prevTimeString))
                    if prevTimeString and File.remoteTimeString == prevTimeString:  #then do not download this file
                        logger.debug('Not downloading %s since remote, local timestrings match (%s).' % (File.name, prevTimeString))
                        continue

                    #check if remote checksum has changed since previous download
                    if File.prevChecksum and File.prevChecksum == File.remoteChecksum: #then file has not changed. Update timestring in DB and do not download file.
                        self.db.writeFileRecord(File, C, status='download_ended', addendum='timestring_updated')
                        continue

                self.downloadFile(File, C)
            self.db.writeCollectionRecord(C, 'download_complete')
            
        if self.pref['IGGYREF_DRY_RUN']:
            print 'Closing ftp connection'
        else:
            self.ftp.closeFtp()


    def downloadFile(self, File, C):
        fileIsModified = True
        downloadAttempts = 0
    
        while True: #attempt to download file
            if self.dryrun:
                print "Writing file record: downloading"
            else:
                self.db.writeFileRecord(File, C, status='downloading')
                logger.info('Downloading %s to %s ...' % (File.ftpPath, File.localPath))
                
            downloadAttempts += 1
        
            if self.dryrun:
                print "Copying file from %s to %s" % (File.ftpPath,File.localPath)
                
            else:
                try:
                    self.ftp.copyFile(File.ftpPath, File.localPath)  # copyFile() will attempt to download file three times, then raise an exception.
                except:
                    self.db.writeFileRecord(File, C, status='download_fail')
                    self.db.writeCollectionRecord(C, 'download_fail', addendum=File.name)
                    errStr = "Unable to download %s: %s" % (File.ftpPath, traceback.format_exc())
                    logger.error(errStr)
                    raise Exception(errStr)

            if self.dryrun:
                print "Download finished."
            else:
                File.setLocalChecksum()
                logger.debug('Download ended.')
                self.db.writeFileRecord(File, C, status='download_ended')

            if self.dryrun:
                print "Testing checksums."
            else:
                if not File.remoteChecksum: #if no remote checksum exists, determine if file has changed based on comparison to checksum from previous download
                    if File.prevChecksum and File.prevChecksum == File.localChecksum: #then file has not changed, so no postprocessing is needed. Update checksum in DB.
                        self.db.writeFileRecord(File, C, status='download_ended', addendum='checksum_updated')
                        fileIsModified = False
                    break
                elif File.remoteChecksum == File.localChecksum: #download successful
                    logger.debug("Local and remote checksums for %s agree." % File.ftpPath)
                    self.db.writeFileRecord(File, C, status='download_ended', addendum='remote_checksum_verified')
                    break
    
                if downloadAttempts > 2: #report failure
                    self.db.writeFileRecord(File, C, status='remote_checksum_fail', addendum='local:%s, remote:%s' % (File.localChecksum,File.remoteChecksum))
                    self.db.writeCollectionRecord(C, 'download_fail', addendum=File.name)
                    errStr = "Downloaded file '%s' failed remote/local checksum comparison\n" % File.ftpPath + \
                            'Local checksum: _%s_\n' % File.localChecksum + \
                            'Remote checksum: _%s_\n'  % File.remoteChecksum
                    logger.error(errStr)
                    raise Exception(errStr)

        if fileIsModified:
            C.modifiedFiles.append(File)


    def postProcessCollections(self, force=False):

        logger.info('Post-processing %s collections' % (self.source))

        if self.updatedCollections: 
            collectionsToProcess = self.updatedCollections
        else:
            collectionsToProcess = [baseCollection.getInstance(primaryID, self, self.ftp) for primaryID in self.selectedCollections]
            force = True

        for C in collectionsToProcess:

                self.postProcess(C, force=force)

        self.copyRepoToFinal()


    def copyRepoToFinal(self):
        if not self.db: self.db =  iggyrefDB(self.pref)

        logger.info('Updating final directory: %s (DEBUG = %s)' % (self.finalDir, self.pref['IGGYREF_LOG_LEVEL']))

        if self.updatedCollections: 
            collectionsToCopy = self.updatedCollections
        else:
            collectionsToCopy = [baseCollection.getInstance(primaryID, self, self.ftp) for primaryID in self.selectedCollections]

        for C in collectionsToCopy:

                self.db.writeCollectionRecord(C,'copying_to_final')
                pysync(C.downloadDir, C.finalDir)
                self.db.writeCollectionRecord(C,'copying_complete')

        logger.info('Updating of final repo directory complete: %s (DEBUG = %s)' % (self.finalDir, self.pref['IGGYREF_LOG_LEVEL']))

        if self.db: self.db.close()


    def postProcess(self, C, force=False):
        if not self.db: self.db = iggyrefDB(self.pref)
        self.updateSpeciesTable(C)

        if force: #force post-postprocessing of all files
            C.modifiedFiles = C.downloadFiles
        elif not C.modifiedFiles or not C.Tasks: # then no post-processsing to be done
            self.db.writeCollectionRecord(C,'postprocessing_complete')
            return

        self.db.writeCollectionRecord(C, 'postprocessing')
        logger.debug('Collection to post-process: ' + C.primaryID)
        logger.debug('Modified files (all files if force=True): ' + ', '.join(map(str,C.modifiedFiles)))

        # Tasks that should be done independent of input / output file processing
        independenttasks = []
        
        G = depGraph()
        for T in C.Tasks:
            if not T.inFiles and not T.outFiles:
                independenttasks.append(T)
            else:
                G.addTask(T) #add task to dependency graph

        G.setExpired(C.modifiedFiles)  #mark descendants of modified files as expired.
        for File in unique(flatten([t.outFiles for t in C.Tasks])): #mark any missing output files as expired.
            if not path.exists(File.localPath):
                G.setExpired(File)

        for T in G.orderedTasks(): #run tasks ordered by dependancy
            logger.info('Postprocessing %s, %s, %s. Task: %s -- %s -- %s ...' % (C.primaryID, C.secondaryID, C.repo.source,
                                                                               T.taskName, ','.join(map(str,T.inFiles)), ','.join(map(str,T.outFiles))))
            for outFile in T.outFiles:
                self.db.writeFileRecord(outFile, C, status='postprocessing', addendum=T.taskName)
            T.run()
            for outFile in T.outFiles:
                self.db.writeFileRecord(outFile, C, status='postprocessing_complete', addendum=T.taskName)

        for T in independenttasks:
            logger.info('Postprocessing %s, %s, %s. Task: %s' % (C.primaryID, C.secondaryID, C.repo.source, T.taskName))
            T.run()
            
            
        self.db.writeCollectionRecord(C,'postprocessing_complete')


    def update(self):
        self.downloadCollections()
        self.postProcessCollections()


    def __repr__(self):
        return '<Repo(%s)>' % (self.source)

