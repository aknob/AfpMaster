#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpGlobal
# AfpGlobal module provides global enviroment and modul variables and flags
# it holds the calsses
# - AfpSettings
# - AfpGlobal
#
#   History: \n
#        23 May 2015 - enable variable setting via configuration string - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright© 1989 - 2018  afptech.de (Andreas Knoblauch)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
#    See the GNU General Public License for more details.
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>. 
#

import tempfile

import AfpUtilities
from AfpUtilities import *
from AfpUtilities.AfpStringUtilities import Afp_toString, Afp_fromString, Afp_pathname, Afp_isIP4, Afp_isMailAddress
from AfpUtilities.AfpBaseUtilities import *
import AfpBaseRoutines
from AfpBaseRoutines import Afp_getModulInfo

## set global system variables
# @param settings - dictionary where values are added
def Afp_setGlobalVars(settings):
    settings["python-version"] = Afp_getGlobalVar("python-version")
    pythonpath = Afp_getGlobalVar("python-path")
    if pythonpath: settings["python-path"] = pythonpath
    settings["op-system"] = Afp_getGlobalVar("op-system")
    settings["net-name"] = Afp_getGlobalVar("net-name")
    settings["user"] = Afp_getGlobalVar("user")
    settings["path-delimiter"] = Afp_getGlobalVar("path-delimiter")
    settings["homedir"] = Afp_genHomeDir()
    settings["tempdir"] = tempfile.gettempdir()
    settings["today"] = Afp_getToday()
    return settings
## initialize needed global variables, if they aren't already set
# @param settings - dictionary where values are checked and possibly added
# @param modul - name of initialized modul
def Afp_iniGlobalVars(settings, modul = None):
    if modul is None:
        if not "database" in settings:
            settings["database"] = "BusAfp"
        if not "database-user" in settings:
            settings["database-user"] = "server"      
        if not "database-host" in settings:
            settings["database-host"] = "127.0.0.1"
        if not "Umst" in settings:
            settings["Umst"] = 19
        # decode passwords, when loaded from file
        if "database-word" in settings:
            settings["database-word"] = settings["database-word"].decode('base64')
        if "smtp-word" in settings:
            settings["smtp-word"] = settings["smtp-word"].decode('base64')
        # set mailsender to user if possible
        if not "mail-sender" in settings and "smtp-user" in settings:
            if Afp_isMailAddress(settings["smtp-user"]):
                settings["mail-sender"] = settings["smtp-user"]
        # set directory pathes
        if not "afpdir" in settings:
            settings["afpdir"] = settings["homedir"]
        if not "templatedir" in settings:
            settings["templatedir"] = settings["afpdir"] + "Template" + settings["path-delimiter"]
        if not "archivdir" in settings:
            settings["archivdir"] = settings["afpdir"] + "Archiv" + settings["path-delimiter"]
        if not "antiquedir" in settings:
            settings["antiquedir"] = settings["archivdir"]
        if not "extradir" in settings:
            settings["extradir"] =  settings["afpdir"] + "Extra" + settings["path-delimiter"]
        # set default file handles (not needed for windows)
        if not "office" in settings:
            settings["office"] = "libreoffice"
        if not ".odt" in settings:
            settings[".odt"] = "libreoffice"
        if not ".fodt" in settings:
            settings[".fodt"] = "libreoffice"
        if not ".txt" in settings:
            settings[".txt"] = "vim"
    elif modul =="Adresse":
        if not "standard-location" in settings:
            settings["standard-location"] = "Braunschweig"
    return settings

## class to hold global of modul specific varaiables
class AfpSettings(object):
    ## initialize AfpSettings class
    # @param debug - flag for debug information
    # @param conf_path - if given path to configuration file
    # - only used for systemwide global configuration
    # @param modulname - name of afp-modul these settings are for
    # @param homedir - if given, path to home directory, where configuration files are found
    # - only used for modul specific settings
    def  __init__(self, debug, conf_path = None, modulname = None, homedir = None):
        #print "AfpSettings.init:", debug, conf_path, modulname, homedir
        self.debug = debug
        self.modul = None
        self.config = conf_path       
        self.settings = {}
        if modulname : self.modul = modulname 
        else: self.settings = Afp_setGlobalVars(self.settings)
        if self.config is None or self.config == "":
            if self.modul is None:
                self.config = Afp_addPath(self.settings["homedir"], "AfpBase.cfg")
            elif homedir:
                self.config = Afp_addPath(homedir, "Afp" + self.modul + ".cfg")
        if not Afp_existsFile(self.config):
            Afp_genEmptyFile(self.config)
        #print self.config
        # read variables from configuratioin file
        self.read(self.config)
        self.set_pathdelimiter()       
        self.settings = Afp_iniGlobalVars(self.settings, self.modul)
        if self.modul:
            # load variables from database
            # self.load(modulname)
            print "AfpSettings.load(" + modulname + ") loading from database not implemented!"
        if self.debug: print "AfpSettings Konstruktor",self.modul
    ## destructor
    def __del__(self):
        if self.debug: print "AfpSettings Destruktor",self.modul
    ## return debug flag
    def is_debug(self):
        return self.debug
    ## loop through all settings, if name ends with "dir" reset pathdelimiter with actuel pathdelimiter
    def set_pathdelimiter(self):
        # convention: names of folder pathes end with "dir" (directory)
        delimiter = Afp_getGlobalVar("path-delimiter")
        for entry in self.settings:
            if entry[-3:] == "dir":
                self.settings[entry] = Afp_pathname(self.settings[entry], delimiter)
    ## read data from file and set appropriate variables
    # @param path - filename including path of file to be read
    def read(self, path):
        if self.debug: print "AfpSettings.read:", path
        fin = open(path , 'r') 
        for line in fin:
            cline = line.split("#")
            sline = cline[0].split("=",1)
            if len(sline) > 1:
                if self.debug: print "AfpSettings.read:", line[:-1]
                name = sline[0].strip()
                value = self.fromString(sline[1].strip())
                #print name, value
                self.set(name, value)
        fin.close()
    #def load(self, modul):
    ## extract value from string, take care of special setting possibillities before conversion:
    # - evaluation of string
    # - special formats
    # @param string - string to be analysed
    def fromString(self, string):
        if self.evalString(string):
            befehl = "value = " + string
            exec befehl
        elif self.keepString(string):
            value = string
        else:
            value = Afp_fromString(string)
        return value
    ## take care if string has special formats, which require string output,
    # when the standard analysis would suggest an other format   
    # - IP4 addresses
    # - windows root pathes
    # @param string - string to be analysed
    def keepString(self, string):
        # identifiy special strings to be not interpreted and converted to other data types
        if Afp_isIP4(string): # IP4 Adresses
            return True
        # windows pathnames with ":" in second place
        if len(string) > 1 and string[1] == ":" and not string[0].isdigit():
            return True
        return False
    ## check if string holds a formula
    # @param string - string to be analysed
    def evalString(self, string):
        if string[0] == "{" and string[-1] == "}":
            return True
        if string[0] == "[" and string[-1] == "]":
            return True
        return False
    ## set a setting value
    # @param name - name of global variable
    # @param value - value to be assigned to this variable
    def set(self, name, value):
        #print name, value
        self.settings[name] = value
    ## check if variable exists in setting
    # @param name - name of global variable
    def exists_key(self, name):
        return name in self.settings
    ## return all available variable names
    def get_keys(self):
        return self.settings.keys()
    ## return value of indicates variable
    # @param name - name of variable   
    def get(self, name):
        if name in self.settings: return self.settings[name]
        else: return None

## object to hold all globally used values
class AfpGlobal(object):
    ## initialize AfpGlobal class
    # @param name - name of this program package
    # @param mysql - connection to database
    # @param setting - initial global variables used systemwide
    def  __init__(self, name, mysql, setting):
        self.mysql = mysql
        self.setting = setting
        self.setting.set("name", name)
        self.debug = self.setting.is_debug()
        self.confdir = Afp_extractPath(self.setting.config) + self.get_value("path-delimiter")
        self.settings = {}
        if self.debug: print "AfpGlobal Konstruktor"
    ## destructor
    def __del__(self):
        if self.debug: print "AfpGlobal Destruktor"
    ## return debug flag
    def is_debug(self):
        return self.debug
    ## return database connection
    def get_mysql(self):
        return self.mysql
    ## add another modul setting
    # @param module - name of afp-module using these settings
    # @param setting - settings
    def add_setting(self, module, setting):
        self.settings[module] = setting
    ## return setting
    # @param module - if given, name of afp-module using returned settings
    def get_setting(self, module = None):
        if module is None: return self.setting   
        if module in self.settings: return self.settings[module]
        return None
    ## set value in settings
    # @param name - name of variable to be set
    # @param value - value of variable
    # @param module - if given, name of afp-module using returned settings
    def set_value(self, name, value, module = None):
        set = self.get_setting(module)
        if set is None and module:
            set = AfpSettings(self.is_debug(), None, module, self.confdir)
            self.add_setting(module, set)
        if set and name:
            set.set(name, value)
    ## set values according to direct configuration string
    # @param conf - configuration string to be evaluated
    def set_configuration(self, conf):
        config = conf.split(",")
        for entry in config:
            split = entry.split("=")
            if len(split) == 2:
                value = split[1]
                vars = split[0].split(".")
                if len(vars) == 2:
                    variable = vars[1]
                    modul = vars[0]
                else:
                    variable = vars[0]
                    modul = None
                self.set_value(variable, value, modul)
    ## set common information for this program package
    # @param version - version the apf main program
    # @param baseversion - version number of this base package
    # @param copyright - copyright of this package
    # @param website - website information for this package
    # @param description - description of this package
    # @param license - license information of this package
    # @param picture - logo of this package
    # @param developer - developer information of this package
    def set_infos(self,  version = None,  baseversion = None, copyright = None, website = None, description = None, license = None, picture = None, developer = None):
        if version: self.set_value("version", version)
        if baseversion: self.set_value("baseversion", baseversion)
        if copyright: self.set_value("copyright", copyright)
        if website: self.set_value("website", website)
        if description: self.set_value("description", description)
        if license: self.set_value("license", license)
        if picture: self.set_value("picture", picture)
        if developer: self.set_value("developer", developer)
    ## retrieve value as a string
    # @param name - name of variable to be retrieved
    # @param module - if given, name of afp-module otherwise get value from common variables
    def get_string_value(self, name, module = None):
        value = self.get_value(name, module)
        return Afp_toString(value)
    ## retrieve value
    # @param name - name of variable to be retrieved
    # @param module - if given, name of afp-module otherwise get value from common variables
    def get_value(self, name, module = None):
        set = self.get_setting(module)
        if set is None and module:
            set = AfpSettings(self.is_debug(), None, module, self.get_value("homedir"))
            self.add_setting(module, set)
        if set:
            return set.get(name)
        else:
            return None
    ##  show all entries, for debug purpose
    def view(self):
        print "AfpGlobal.view: Global", self.setting.settings
        for set in self.settings: 
            print "AfpGlobal.view:", self.settings[set].modul, self.settings[set].settings
    ## return if operating system is assumed to be windows
    def os_is_windows(self):
        op_sys = self.get_value("op-system")
        is_win = "win" in op_sys or "Win" in op_sys
        if self.debug: "AfpGlobal.os_is_windows:", is_win, op_sys
        return is_win
    # special retrieve routines
    ## get header with database information
    def get_host_header(self):
        return self.get_value("name") + " auf " + self.get_value("database-host") + ", User: \""  + self.get_value("database-user") + "\""
    ## sample infomation about all modules
    def get_modul_infos(self):
        infos = ""
        for set in self.settings:
            setting = self.settings[set]
            if setting.modul:
                if not "Info" in setting.settings:
                    pythonpath = self.get_value("python-path")
                    if not pythonpath: pythonpath = self.get_value("start-path")
                    setting.settings["Info"] = Afp_getModulInfo(setting.modul, self.get_value("path-delimiter"), pythonpath)
                infos += setting.get("Info")
        return infos[:-1]
    # shortcuts to common flags and variables
    ## return if accounting should be skipped
    def skip_accounting(self):
        if self.get_value("skip-accounting"): return True
        else: return False
    ## return the date of today
    def today(self):
        return self.get_value("today")
    ## return the date of today as a string
    def today_string(self):
        return Afp_toString(self.today())
    ## get the python program path
    def get_programpath(self):
        path = self.get_value("python-path")
        if path is None: path = self.get_value("start-path")
        return path
      