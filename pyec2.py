import launchy
import sys, os

import glob
from CaselessDict import CaselessDict
from future_ntpath import expandvars

from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QVariant
from sip import wrapinstance, unwrapinstance

import collections
from boto import ec2

class PyEC2(launchy.Plugin):
    __version__ = "1.0"
    
    def __init__(self):
        launchy.Plugin.__init__(self)
        self.icon = os.path.join(launchy.getIconsPath(), "pyec2.ico")
        self.hash = launchy.hash(self.getName())
        self.labelHash = launchy.hash("ec2")
        
        self.tags = CaselessDict()
    
    def init(self):
        self.__readConfig()
        pass
    
    def getID(self):
        return self.hash
    
    def getName(self):
        return "PyEC2"
    
    def getIcon(self):
        return self.icon
    
    def getLabels(self, inputDataList):
        pass
    
    def getResults(self, inputDataList, resultsList):
        if len(inputDataList) != 2:
            return
            
        if not inputDataList[0].hasLabel(self.labelHash):
            return
        
        q = inputDataList[1].getText().lower()
        for tag, instances in self.tags.iteritems():
            if q in tag:
                for instance in instances:
                    resultsList.append(
                        launchy.CatItem(
                            '%s:%s.ec2' % (tag, instance),
                            instance,
                            self.getID(),
                            self.getIcon(),
                        )
                )

    def getCatalog(self, resultsList):
        for tag, instances in self.tags.items():
            for instance in instances:
                resultsList.push_back(
                    launchy.CatItem(
                        '%s:%s.ec2' % (tag, instance),
                        instance,
                        self.getID(),
                        self.getIcon()
                    )
                )
        
    def launchItem(self, inputDataList, catItemOrig):
        catItem = inputDataList[-1].getTopResult()
        if catItem.fullPath.endswith(".ec2"):
            # Launch the directory itself
            try:
                path = self.tags[catItem.shortName]
                launchy.runProgram(path, "")
            except:
                pass
        else:
            # Launchy a file or directory
            launchy.runProgram( catItem.fullPath, "" )
       
    def launchyShow(self):
        self._update()

    def __readConfig(self):
        settings = launchy.settings
        
        # Test if the settings file has PyEC2 configuration
        version = settings.value("PyEC2/version", QVariant("0.0")).toString()
        if version == "0.0":
            settings.beginWriteArray("PyEC2/settings")
            settings.setArrayIndex(0)
            settings.setValue("Name", QVariant(""))
            settings.setValue("Region", QVariant(""))
            settings.setValue("Access key", QVariant(""))
            settings.setValue("Secret key", QVariant(""))
            settings.endArray()
        
        # Set our version
        settings.setValue("PyEC2/version", QVariant(self.__version__))

        self._update()

    def _update(self):
        self.tags.clear()
        
        # Read directories from the settings file
        settings = launchy.settings
        size = settings.beginReadArray("PyEC2/settings")
        for i in range(0, size):
            settings.setArrayIndex(i)
            name = unicode(settings.value("Name").toString())
            region = unicode(settings.value("Region").toString())
            access_key_id = unicode(settings.value("Access Key").toString())
            secret_access_key = unicode(settings.value("Secret Key").toString())

            region = '[REGION]'
            access_key_id = '[ACCES_KEY_ID]'
            secret_access_key = '[SECRET_ACCES_KEY]'

            if not (region and access_key_id and secret_access_key):
                continue

            ec2_connection = self.get_ec2_connection(region, access_key_id,
                secret_access_key)

            tags = collections.defaultdict(list)
            for reservation in ec2_connection.get_all_instances():
                for instance in reservation.instances:
                    for tag in instance.tags.itervalues():
                        if instance.public_dns_name:
                            tags[tag].append(instance.public_dns_name)

            self.tags[name] = dict(tags)
        settings.endArray()

    @classmethod
    def get_ec2_connection(cls, region, access_key_id, secret_access_key):
        return ec2.connect_to_region(
            region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

launchy.registerPlugin(PyEC2)

