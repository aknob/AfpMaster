#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package BusAfp
# BusAfp is a software to manage coach and travel activities \n
#    Copyright© 1989 - 2025  afptech.de (Andreas Knoblauch) \n
# \n
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        05 Mar. 2020 - allow individual database config files additionally- Andreas.Knoblauch@afptech.de \n
#        15 Nov. 2018 - set initial database name to product name - Andreas.Knoblauch@afptech.de \n
#        16 Jan. 2017 - separate software specific code from parameter extraction - Andreas.Knoblauch@afptech.de \n
#        26 Aug. 2015 - change direct execution parameter to normal input, to be used via os - Andreas.Knoblauch@afptech.de \n
#        11 Jun. 2015 - enable direct routine execution via command line option - Andreas.Knoblauch@afptech.de \n
#        23 May 2015 - enable variable setting via command line option - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright© 1989 - 2025 afptech.de (Andreas Knoblauch)
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


import wx
import sys
import os.path
from . import AfpDatabase, AfpBaseRoutines, AfpBaseDialog, AfpBaseScreen ,AfpGlobal
from AfpBase.AfpDatabase import AfpSQL

## class for software information
class AfpSoftwareInformation(object):
     ## initialize AfpSoftwareInformation class
    # @param name - name of the software package
    # @param moduls - name of possible graphic moduls
    # @param version - version of the software package
    # @param description - description of the software package
    # @param picture - picture to be shown on information tab
    # @param website - homepage of the software package
    def  __init__(self, name, moduls, description, picture = None, website = None, version = None):
        self.name = name
        self.moduls = moduls
        self.description = description
        self.picture = picture
        self.website = website
        self.version = version
   ## extract name from object
    def get_name(self):
        return self.name
    ## extract description from object
    def get_description(self):
        return self.description
    ## extract picture from object
    def get_picture(self):
        return self.picture
    ## extract website from object
    def get_website(self):
        return self.website
    ## extract version from object
    def get_version(self):
        return self.version
    ## extract possible graphic modulnames from object
    def get_moduls(self):
        return self.moduls

## main class to invoke Afp Software
class AfpMainApp(wx.App):
    ## initialize mysql connection, global variables and application
    # @param debug - flag for debug information
    # @param pars - parameter dictionary, possible values:
    # - startpath: path where program has been started from
    # - confpath: path to configuration file
    # - dbhost: host for database
    # - dbname: name of schema for database
    # - dbuser: user on host for database
    # - dbword: password for user on host for database
    # - config: configuration string to set global variables
    # - strict: flag if only strict modul handling should be used
    # @param info - software information object
    def initialize(self, debug, pars, info): 
        name = "BusAfp"
        description = None
        picture = None
        website = "http://www.afptech.de"
        baseversion = "6.1.1 beta"       
        version = baseversion    
        copyright = 'Copyright (C) 1989 - 2025  AfpTech.de'
        moduls = ["Adresse"]
        if info:
            name = info.get_name()
            description = info.get_description()
            picture = info.get_picture()
            if info.get_moduls(): moduls = info.get_moduls()
            if info.get_website(): website = info.get_website()
            if info.get_version(): version = info.get_version()
      
        license = name + """ ist eine freie Software, sie kann weiterverteilt und 
        modifiziert werden, gemäß den Bestimmungen der 
        'GNU General Public License' wie von der  'Free Software Foundation' 
        in Version 3 oder höher veröffentlicht,
        Da diese Lizenz nicht in Deutsch zur Verfügung steht folgt hier die 
        rechtssichere englische Version:
        
        """ + name + """ is a software to manage coach and travel acivities
         Copyright© 1989 - 2025  afptech.de (Andreas Knoblauch)

         This program is free software: you can redistribute it and/or modify
         it under the terms of the GNU General Public License as published by
         the Free Software Foundation, either version 3 of the License, or
         (at your option) any later version.
         This program is distributed in the hope that it will be useful, but
         WITHOUT ANY WARRANTY; without even the implied warranty of
         MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
         See the GNU General Public License for more details.
         You should have received a copy of the GNU General Public License
         along with this program.  If not, see <http://www.gnu.org/licenses/>.
         """ 
        developers = "Andreas Knoblauch - initiale Version"
       
        self.globals = None
        confpath = None
        if "confpath" in pars: confpath = pars["confpath"]
        set = AfpGlobal.AfpSettings(debug, confpath)
        set.set("graphic-moduls", moduls)
        if "startpath" in pars: set.set("start-path", pars["startpath"])
        if "dbhost" in pars: set.set("database-host", pars["dbhost"]) 
        if not set.get("database") and not "dbname" in pars: pars["dbname"] = name
        if "dbname" in pars: set.set("database", pars["dbname"])    
        set.read_db_config()
        if "dbuser" in pars: 
            set.set("database-user", pars["dbuser"])      
            set.set("database-word", "")      
        if not set.exists_key("database-word") and not "dbword" in pars:
            if not "dbuser" in pars: pars["dbuser"] = set.get("database-user")
            dbword, ok = AfpBaseDialog.AfpReq_Text("Für die Verbindung zur Datenbank wird eine Authentifizierung benötigt!","Bitte das Passwort für den Benutzer '" + pars["dbuser"] + "' eingeben:","","Passwort Eingabe",True)
            pars["dbword"] = dbword
        if "dbword" in pars: set.set("database-word", pars["dbword"])
        if "strict" in pars: set.set("strict-modul-handling",1)
        if "dry-run" in pars: 
            set.set("dry-run",1)
            set.set("readonly",1)
        mysql = AfpDatabase.AfpSQL.AfpSQL(set.get("database-host"), set.get("database-user"), set.get("database-word"), set.get("database"), set.is_debug())
        self.globals = AfpGlobal.AfpGlobal(name, mysql, set)
        self.globals.set_infos(version, baseversion, copyright, website, description, license, picture, developers)
        if "config" in pars: self.globals.set_configuration(pars["config"])
        if mysql.database_created(): AfpBaseRoutines.Afp_verifyDatabase(self.globals, True)
        #wx.InitAllImageHandlers() # deprecated function, obvoiusly not needed here
    
    ## load appropriate modul     
    # @param modulname - afp-modul name to be loaded
    def load_modul(self, modulname):
        Modul = AfpBaseScreen.Afp_loadScreen(self.globals, modulname)
        if Modul: 
            self.SetTopWindow(Modul)
            return True
        else:
            return False
   ## invoke direct execution of a routine    
    # @param routine - string to define used pythonmodul, executed routine and input parameter
    def direct_execution(self, routine):
        return AfpBaseRoutines.Afp_startRoutine(self.globals, routine, self.globals.is_debug())                    
# end of class AfpMainApp

def AfpStart(info):
    # main program
    debug = False
    execute = True
    direct = False
    parameter = {}
    modul = "Adresse"
    routine = None
    lgh = len(sys.argv)
    ev_indices = []
    name = info.get_name()
    parameter["startpath"] = os.path.dirname(os.path.abspath(sys.argv[0]))
    for i in range(1,lgh):
        if sys.argv[i] == "-p" or sys.argv[i] == "--password": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": parameter["dbword"] = sys.argv[i+1]
        if sys.argv[i] == "-s" or sys.argv[i] == "--server": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": parameter["dbhost"] = sys.argv[i+1]
        if sys.argv[i] == "-d" or sys.argv[i] == "--database": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": parameter["dbname"] = sys.argv[i+1] 
        if sys.argv[i] == "-u" or sys.argv[i] == "--user": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": parameter["dbuser"] = sys.argv[i+1] 
        if sys.argv[i] == "-o" or sys.argv[i] == "--option": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": parameter["config"] = sys.argv[i+1] 
        if sys.argv[i] == "-c" or sys.argv[i] == "--config": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": parameter["confpath"] = sys.argv[i+1] 
        if sys.argv[i] == "-m" or sys.argv[i] == "--modul": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": modul = sys.argv[i+1]
        if sys.argv[i] == "-v" or sys.argv[i] == "--verbose": debug = True
        if sys.argv[i] == "-x" or sys.argv[i] == "--strict": parameter["strict"] = None
        if sys.argv[i] == "-y" or sys.argv[i] == "--dry": parameter["dry-run"] = 1
        if sys.argv[i] == "-h" or sys.argv[i] == "--help": execute = False
    if execute:
        App = AfpMainApp(0)
        App.initialize(debug, parameter, info)
        if lgh > 1 and sys.argv[lgh-1][0] != "-"  and not lgh-1 in ev_indices:
            routine = sys.argv[lgh-1] 
            protocol = False
            if routine[:7] == "afpp://": 
                protocol = True
                fout = open("/tmp/" + name + ".log", 'w')
                fout.write(("direct execution started with parameter: %s \n") % routine)
                routine = routine[7:]
            executed = App.direct_execution(routine)
            if executed: 
                if protocol: fout.write(("Routine or file '%s' directly executed!") % routine)
                else:  print("Routine or file '", routine, "' directly executed!")
            else: 
                if protocol: fout.write(("ERROR: Routine or file '%s' not found!") % routine)
                else:  print("ERROR: Routine or file '", routine, "' not found!")
            if protocol: fout.close()
        else:
            loaded = App.load_modul(modul)
            if loaded:
                App.MainLoop()
            else:
                print("ERROR: " + name + " Modul '" + modul + "' not available!")
    else:
        print("usage: " + name + " [option] [routine, file]")
        print("Options and arguments:")
        print("-h,--help      display this text")
        print("-m,--modul     modul to be started follows")
        print("               Default: modul \"Adresse\" will be invoked")
        print("-c,--config    configuration for AfpBase follows in a python script file")
        print("-s,--server    database servername or IP-address follows")
        print("               Default: loclahost (127.0.0.1) will be used")
        print("-d,--database  database name or schema follows")
        print("               Default: 'BusAfp' will be used")
        print("-u,--user      user for mysql authentification follows")
        print("               Default: user \"server\" will be used")
        print("-p,--password  plain text password for mysql authentification follows")
        print("               Default: password has to be entered during program start")
        print("-o,--option    manuel setting of different configuration settings follows")
        print("               Usage: [modulname.]variablename=value[, ...]")
        print("-v,--verbose   display comments on all actions (debug-information)")
        #print("-x,--strict    don't allow dynamic modul handling (needed for py2exe compilation)")
        print("-y,--dry       start program in dry-run mode: no writing to database, no emails, no imports!")
        print("routine, file  pythonmodul and name of routine to be executed")
        print("               or path of a file in which each line represents one call")
        print("               Usage: python.modul.routinename:parameter1[,param2 ...]")
        print("               Example: AfpEinsatz.AfpEinDialog.AfpLoad_DiEinsatz_fromENr:231")
        print("               Remark: if protocol identifier is needed, 'afpp://' may be used")
        print("               Remark: routine to be called must take 'globals' as first parameter")
        

   
