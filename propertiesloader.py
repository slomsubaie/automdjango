import os
from jproperties import Properties
import configparser

class PropertiesLoader:
    properties = Properties()
    configLoader = configparser.RawConfigParser()
    browserName = ""
    protocol=""
    url=""
    path=""

    def __init__(self):
        self.initializeProperties()
        self.setBrowserName(self.getProperty('details','browserName'))
        self.setProtocol(self.getProperty('details', 'protocol'))
        self.setUrl(self.getProperty('details', 'url'))
        self.setPath(self.getProperty('details', 'path'))

    def initializeProperties(self):
        configPath = "configinfo.properties"
        self.configLoader.read(configPath)

    def getProperty(self, section, option) -> str:
        return self.configLoader.get(section,option)


    def getBrowserName(self) -> str:
        return self.browserName
    def setBrowserName(self,browserName):
        if browserName is not None:
            self.browserName = browserName
        else:
            print("Browser name is not defined")


    def getProtocol(self) -> str:
        return self.protocol
    def setProtocol(self,protocol):
        if protocol is not None:
            self.protocol = protocol
        else:
            print("Protocol is not defined")


    def getUrl(self) -> str:
        return self.url
    def setUrl(self,url):
        if url is not None:
            self.url = url
        else:
            print("URL is not defined")


    def getPath(self) -> str:
        return self.path
    def setPath(self,path):
        if path is not None:
            self.path = path
        else:
            print("Path is not defined")

    def getWebsite(self) -> str:
        return self.getProtocol()+self.getUrl()+self.getPath()