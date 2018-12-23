#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseRoutines
# AfpBaseRoutines module provides the base class for all 'Selection Lists', \n
# and Afp specific utility routines with or without database access \n
# it holds the calsses
# - AfpSelectionList
#
#   History: \n
#        31 Jan. 2018 - AfpSelectionList: allow tagged value evaluation - Andreas.Knoblauch@afptech.de \n
#        28 Mar. 2016 - AfpSelectionList: add afterburner to be used in second save step - Andreas.Knoblauch@afptech.de \n
#        04 Feb. 2015 - add data export to dbf - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de


#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2018  afptech.de (Andreas Knoblauch)
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

import sys
import AfpDatabase.AfpSQL
from AfpDatabase.AfpSQL import AfpSQL, AfpSQLTableSelection

import AfpUtilities
from AfpUtilities import *
from AfpUtilities.AfpStringUtilities import *
from AfpUtilities.AfpBaseUtilities import *

# definition routines
## get all possible module with own graphical interfaces (screens) \n
# if globals are given, only modules available for this program are returned
# @param globals - if given, global variables holding graphic modulnames
def Afp_graphicModulNames(globals = None):
    modules = ["Adresse","Charter","Event:Tourist","Event","Faktura"]
    if globals:
        mods = globals.get_value("graphic-moduls")
        if mods: modules = mods
    return modules
## get all possible internal moduls\n
# if globals are given, only modules available for this program are returned
# @param globals - if given, global variables holding  graphic modulnames
def Afp_internalModulNames(globals = None):
    modules = ["Finance","Einsatz","Calendar"]
    if globals:
        modules = ["Finance"]
        mods = globals.get_value("graphic-moduls")
        if not mods: mods = []
        if "Charter" in mods or "Tourist" in mods:
            modules.append("Einsatz")
        if "Einsatz" in modules or "Event" in mods:
            modules.append("Calendar")
    return modules
## get modul short names - used for filename generation
# @param modul - long name of modul
def Afp_getModulShortName(modul):
    if modul == "Einsatz" or modul == "Calendar": 
        return modul[:3]
    else:
        return modul[:2]
## return possible user-moduls \n
# and check if needed python moduls are present, if globals are given
# @param globals - global variables holding program name
# @param flavour - None: names are given as they come, False: only modul part is listed, True: flavour parts are listed, if given, else modul parts
def Afp_ModulNames(globals = None, flavour = None):
    mods = Afp_graphicModulNames(globals)
    #print "Afp_ModulNames input:", mods, flavour
    modules = []
    # check if appropriate python files exists, if global variables are given
    if globals and mods:
        modi = []
        path = globals.get_programpath()
        deli = globals.get_value("path-delimiter") 
        for mod in mods:   
            if Afp_existsModulFiles(mod, deli, path):
                modi.append(mod)
        mods = modi
    #print "Afp_ModulNames files:", mods
    if not flavour is None:
        for mod in mods:
            #print "Afp_ModulNames mods:", mod
            if ":" in mod:
                md = mod.split(":")
                #print "Afp_ModulNames md:", md
                if flavour and len(md) > 1:
                    modules.append(md[1])
                else:
                    modules.append(md[0])
            else:
                modules.append(mod)
    else:
        modules = mods
    #print "Afp_ModulNames modules:", modules
    return modules
## get all possible afp-modul names
def Afp_allModulNames():
    modules = []
    mods = Afp_graphicModulNames()
    for mod in mods:
        modules.append(mod)
    mods = Afp_internalModulNames()
    for mod in mods:
        modules.append(mod)
    return modules
## check if modul is available
# @param input - name of modul or main table name
def Afp_getModulName(input):
    modul = None
    modules = Afp_ModulNames()
    if input:
        modul = input
        if input == "Fahrten": modul = "Charter"
    if modul and not modul in modules: return None
    return modul
## get flavour of a afp-modul
# @param modul - name of afp-modul
def Afp_getModulFlavour(modul):
    name = ""
    flavour = ""
    if ":" in modul:
        mod = modul.split(":")
        name = mod[0]
        if len(mod) > 1 and mod[1]:
            flavour = mod[1]
    else:
        flavours = Afp_ModulNames(None, True)
        names = Afp_ModulNames(None, False)
        if modul in names:
            name = modul
        elif modul in flavours:
            name = names[flavours.index(modul)]
            flavour = modul
        else:
            name = None
    return name, flavour
## return of given modul identifier is valid
# @param modul - name of afp-modul
# @param globals - if given, global values
def Afp_inModuls(modul, globals = None):
    names = Afp_ModulNames(globals, False)
    flavours = Afp_ModulNames(globals, True)
    modules = Afp_ModulNames(globals)
    return modul in names or modul in flavours or modul in modules
## get all python-modules needed for a afp-modul
# @param modul - name of afp-modul
def Afp_ModulPyNames(modul):
    md = Afp_getModulShortName(modul)  
    name, fl = Afp_getModulFlavour(modul)
    if name is None: name = modul
    #print "Afp_ModulPyNames:", modul, name, fl
    if fl: fl = "_" + fl
    parent = "Afp" + name  + "."
    files = [parent + "Afp" + md + "Screen" + fl, parent + "Afp" + md + "Dialog", parent + "Afp" + md + "Routines" ]
    if modul in Afp_internalModulNames():
        if modul == "Finance" or modul == "Calendar":
            return [files[2]]
        else:
            return files[1:3]
    elif modul in Afp_graphicModulNames():
        if modul == "Adresse":
            return [files[0]]
        else:
            return files
    return []
## get all python-modul file names for a afp-modul
# @param modul - name of afp-modul
# @param delimiter - path delimiter
# @param path - rootpath to python-modules
def Afp_ModulFileNames(modul, delimiter, path):
    files = []
    names = Afp_ModulPyNames(modul)
    for name in names:
        name = name.replace(".",delimiter)
        fname = Afp_addRootpath(path, name + ".py")
        files.append(fname)
    return files
## get information if all python-modul files exist for a afp-modul
# @param modul - name of afp-modul
# @param delimiter - path delimiter
# @param path - rootpath to python-modules
def Afp_existsModulFiles(modul, delimiter, path):
    filenames = Afp_ModulFileNames(modul, delimiter, path)
    if filenames:
        #print "Afp_existsModulFiles filenames:", filenames
        exists = True
        for file in filenames:
                # look if appropriate .py or .pyc file exists im path
                exists = exists and (Afp_existsFile(file) or Afp_existsFile(file + "c"))
                #print "Afp_existsModulFiles exists:", exists
        return exists
    return False
## get 'modul info' (timestamp) of all python-modul files for a afp-modul
# @param modul - name of afp-modul
# @param delimiter - path delimiter
# @param path - rootpath to python-modules
def Afp_getModulInfo(modul, delimiter, path):
    filenames = Afp_ModulFileNames(modul, delimiter, path)
    line = ""
    for file in filenames:
        split = file.split(delimiter)
        time = Afp_getFileTimestamp(file)
        line += split[-1] + ": " + Afp_toInternDateString(time.date()) + "-" + Afp_toString(time.time()).replace(":","-") + '\n'
    return line
 
## look if text represents the name of archieved file (only used for compability of already created data) \n
# should return None for actuel created data
# @param text - text to be analysed
# @param delimiter - path delimiter
def Afp_archivName(text, delimiter):
    filename = None
    if text and "." in text:
        is_name = False
        is_archiv = False
        if "Archiv" == text[:6]: 
            is_name = True
            is_archiv = True
        else:
            mods = Afp_allModulNames()
            for mod in mods:
                if mod == text[:len(mod)]: is_name = True
        if is_name:
            if is_archiv:
                filename = Afp_pathname(text[6:], delimiter, True) 
            else:
                filename = Afp_pathname(text, delimiter, True) 
    return filename
  
## read extra info from file
# @param fname - name of file to be checked
def Afp_readExtraInfo(fname):
    lines = Afp_readLinesFromFile(fname, 5)
    modul = None
    text = fname
    for i in range(2,4):
        if lines[i][:11] == "# AfpModul:":
            modul = lines[i].split(":")[1].strip()
        elif lines[i][:13] == "# AfpPurpose:":
            text = lines[i].split(":")[1].strip()
    #print "Afp_readExtraInfo:", modul, text
    return modul, text
##  starts an extra python-programfile delivered as extension to this program \n
# in this case the file must hold a routine "AfpExtra(globals, debug)"
# @param filepath - name and path of file to be opened
# @param globals - global variables
# @param debug - flag for debug messages
def Afp_startExtraProgram(filepath, globals, debug = False):
    if debug: print "Afp_startExtraProgram:",filepath
    split = filepath.split(globals.get_value("path-delimiter"))
    modul = split[-1]
    path = filepath[:-len(modul)]
    modul = modul.split(".")[0]
    pymodul = AfpPy_Import(modul, path)
    if pymodul:
        pymodul.AfpExtra(globals, debug)
    else:
        print "WARNING: extra program not available -",filepath
##  starts a programfile with the associated program
# @param filename - name of file to be opened
# @param globals - global variables to hold file associations
# @param debug - flag for debug messages
# @param noWait - flag if execution of python program should be continued direct after starting execution of file
def Afp_startFile(filename, globals=None, debug = False, noWait = False):
    if debug: print "Afp_startFile:",filename
    program = None
    param = None
    if globals:
        if globals.os_is_windows():
            if noWait: program = "start"
        else:
            if "." in filename:
                split = filename.split(".")
                ext = "." + split[-1]
                program = globals.get_value(ext)
            if noWait: param = "&"
        #Afp_startProgramFile(program, debug, filename, "--invisible")
    Afp_startProgramFile(program, debug, filename, param)
##  starts a routine in given modul, returns True if at least one routine has been executed
# @param globals - global variables to hold file associations
# @param instring - string to define used pythonmodul, executed routine and input parameter directly 
# or holds the path of a  file in which each line represents one call \n
# at the moment the following format is supported:\n
# - python.modul.name.routinename:parameter1 - the routine 'routinename' in the modul python.modul.name 
# is called via the interface routinename(globals, parameter1)
# @param debug - flag for debug messages
def Afp_startRoutine(globals, instring, debug = False):
    executed = False
    if not instring: return False
    if Afp_isRootpath(instring):
        routines = Afp_importFileLines(instring)
    else:
        routines = [instring]
    for routine in routines:
        #print "Afp_startRoutine:", routine
        split = routine.split(".")
        if len(split) > 1:
            mname = Afp_ArraytoLine(split,".",len(split)-1)
            modul = Afp_importPyModul(mname, globals)
            rsplit = split[-1].split(":")
            rname = rsplit[0]
            rvalue = Afp_fromString(rsplit[-1])
            pyBefehl = "modul." + rname + "(globals, rvalue)"
            if debug: print "Afp_startRoutine:", pyBefehl
            exec pyBefehl
            executed = True
    return executed

##   dynamic import of a python module from modulname,
# a handle to the modul will be returned
# @param modulname -  name of modul to be imported, in python modul syntax "package.modul"
# @param globals - global variables including the path delimiter to be used for filesystem pathes
def Afp_importPyModul(modulname, globals):
    deli = globals.get_value("path-delimiter")
    path = globals.get_programpath()
    if not path[-1] == deli: path += deli
    split = modulname.split(".")
    modul = split[-1]
    for i in range(len(split)-1):
        path += split[i] + deli
    if globals.is_debug(): print "Afp_importPyModul:", modulname, modul, path
    return AfpPy_Import(modul, path)
## dynamic import of 'Afp' modules,
#  depending on the modul there are one to three pythonfiles to be imported
# @param modulname - name of Afp-modul to be imported
# @param globals        - global variables
def Afp_importAfpModul(modulname, globals):
    moduls = []
    modulfiles = Afp_ModulPyNames(modulname)
    for mod in modulfiles:
        modul =  Afp_importPyModul(mod, globals)
        moduls.append(modul)
    if moduls:
        return moduls
    return None

##  write available data in 'Selection List' into a file
# @param selectionlist -  nselection list where data is extracted from
# @param fname - name and path of output file
def Afp_printSelectionListDataInfo(selectionlist, fname):
    info = selectionlist.get_data_info()
    info_keys = info.keys()
    info_keys.sort()
    fout = open(fname , 'w') 
    for entry in info_keys:
        fout.write(entry +  ':\n')
        for name in info[entry]:
            fout.write("   " + name + "." + entry  + '\n')
    fout.close()
    
##  write given data to an infofile and start editor
# @param globals -  global variables, holding temporary directory 
# @param lines -  dictionary holding the lines to be displayed 
# @param sort - flag if keys should be sorted due to theri values, default: False \n
# @param fname - if given, name of file were data has to be printed to
#  lines[key] = [entry1, entry2, ...] to be evaluated as follows:
# - for each key,
# - "key:" is displayed - newline
# - "    entryN" newline "    entryN+1" newline ...
def Afp_printToInfoFile(globals, lines, sort = False, fname = None):
    if fname is None:
          fname = Afp_addRootpath(globals.get_value("tempdir") , "DataInfo.txt")
    line_keys = lines.keys()
    if sort: line_keys.sort()
    fout = open(fname , 'w') 
    for key in line_keys:
        fout.write(key +  ':\n')
        for entry in lines[key]:
            fout.write("   " + entry  + '\n')
    fout.close()
    Afp_startFile( fname, globals, globals.is_debug(), True) 
## convert input date and time to datetime, will return a result for any input, 
# not delivered values are taken from 'now'
# @param date - input date value 
# @param time - input time value 
# @param hightime - flag how time should be initialised, if no valid time is given (None, True. False)
def Afp_toDatetime(date, time, hightime = None):
    if Afp_isString(date):
        date = Afp_fromString(Afp_ChDatum(date))
    if Afp_isString(time):
        time = Afp_fromString(Afp_ChZeit(time)) 
    time = Afp_toTime(time, hightime)
    return Afp_genDatetime(date.year, date.month, date.day, time.hour, time.minute, time.second)
##  provide a list from a SQLTableSelection object - \n
#    mostly to allow additional selection
# @param table_sel - input AfpSQLTableSelection object for which an additional selection has to be made
# @param select     - filter to get possible additional selections from database
# @param ident      - identification column for filtered data entries 
# @param order     - order in which list is displayed
# @param keep      - column which could skip check for double entries 
def Afp_getListe_fromTableSelection(table_sel, select, ident, order = None, keep = None):
    attributs = table_sel.create_initialized_copy()
    attributs.load_data(select, order)
    print "Afp_getListe_fromTableSelection init:",  table_sel, table_sel.data, attributs, attributs.data
    if keep and not keep in attributs.get_feldnamen():
        keep = None
    manipulate = []
    deleted = 0
    if table_sel.get_data_length():
        for i in range(attributs.get_data_length()):
            if keep is None or  not attributs.get_values(keep, i)[0][0]:
                check = True
            else:
                check = False
            #print "Afp_getListe_fromTableSelection keep:", i, attributs.get_values(keep, i)[0][0], check
            if check:
                for j in range(table_sel.get_data_length()):
                    # delete entries already in table_sel 
                    if table_sel.get_values(ident, j) == attributs.get_values(ident, i):
                        manipulate.append([i - deleted, None])
                        deleted += 1
    print "Afp_getListe_fromTableSelection:", manipulate
    if manipulate:
        attributs.manipulate_data(manipulate)
    liste = []
    for i in range(attributs.get_data_length()):
        liste.append(attributs.get_values(ident, i)[0][0])
    # return a slice to be shown (liste) and the complete values (attributs.get_values()) for further use
    print "Afp_getListe_fromTableSelection exit:",  table_sel, table_sel.data, attributs, attributs.data
    return liste, attributs.get_values()

# with database access

##  check if needed database tables are present, if flag is set, generate them \n 
# output: list of not available tables, resp. generated tables
# param globals - global data holding mysql-connection and modul data
# param create - flag if needed database tables should be generated
def Afp_verifyDatabase(globals, create = False):
    mysql = globals.get_mysql()
    debug = globals.is_debug()
    tables = mysql.get_tables()
    if not tables: tables = []
    required = {}
    modules = Afp_ModulNames(globals)
    internals = Afp_internalModulNames(globals)
    for intern in internals:
        modules.append(intern)
    # get common tables
    required = AfpBase_getSqlTables()
    # get afp-modul tables
    if debug: print "Afp_verifyDatabase available modules:", modules
    global_flavour = None
    # proceed "Adresse" first, as tables may filled from other modules
    if "Adresse" in modules:
        modul = modules[modules.index("Adresse")]
        if ":" in modul:
            global_flavour = modul.split(":")[1]
        required = Afp_getPyModTables(globals, required, "Adresse", global_flavour)
    for mod in modules:
        if mod =="Adresse": continue # already proceeded
        if mod =="Calendar": continue # no tables for calendar modul needed
        if mod =="Finance" : continue # will be proceeded later
        if ":" in mod:
            modul = mod.split(":")[0]
            flavour = mod.split(":")[1]
            global_flavour = flavour
        else:
            modul = mod
            flavour = None
        required = Afp_getPyModTables(globals, required, modul, flavour)
    # proceed "Finance" modul, no tables if accounting is skipped
    if "Finance" in modules and not globals.skip_accounting(): 
        required = Afp_getPyModTables(globals, required, "Finance", global_flavour)
    #print "Afp_verifyDatabase required Tables :", required
    for tab in required:
        if tab in tables:
            required[tab] = ""
    needed = []
    for tab in required:
        if required[tab]:
            needed.append(tab)        
    if debug: 
        print "Afp_verifyDatabase tables to be created:", needed
    if create:
        for tab in required:
            if required[tab]:
                mysql.execute(required[tab])
    return needed
## get required tables from python module 'Routines'
# @param globals - global values needed
# @param required - dictionary where table data should be added
# @param modul - name of modul
# @param flavour - flavour needed to extract table names
def Afp_getPyModTables(globals, required, modul, flavour):
    md = Afp_getModulShortName(modul)  
    file = "Afp" + modul  + "."+ "Afp" + md + "SqlTemplate" 
    pymod =  Afp_importPyModul(file, globals)
    if pymod:
        befehl = "local = pymod.Afp" + modul + "_getSqlTables" + "(flavour)"
        if globals.is_debug(): print "Afp_getPyModTables execute:", befehl
        exec befehl
        if local:
            required = Afp_addDict(required, local)
    return required

##   retrieve a list of database entries with same "KundenNr" from table
# @param mysql - database where values are retrieved from
# @param table  - name of database table where values are retrieved from
# @param KNr      - value of "KundenNr" for values to be retrieved
# @param debug  - flag for debug messages
# @param felder  - names of tablecolumns from which values are catched
# @param filter_feld  - name tablecolumn where additional filter is used
# @param wanted_values  - values which are accepted in the tablecolumn 'filter_feld'
def Afp_selectSameKundenNr(mysql, table, KNr, debug = False, felder = None, filter_feld = None, wanted_values = None):
    selection = AfpSQLTableSelection(mysql, table, debug, False)
    selection.load_data("KundenNr = " + Afp_toString(KNr))
    if filter_feld and wanted_values:
        values = selection.get_values(filter_feld)
        lgh = len(values)
        for i in range(lgh-1,-1,-1):
            delete = True
            for want in wanted_values:
                 if  values[i][0] == want: delete = False
            if delete: selection.delete_row(i)
    return selection.get_values(felder)
##  get special account from 'KtNr' table
#     return the accountnumber
# @param mysql - database where values are retrieved from
# @param ident  - identifier of account to be selected
def Afp_getSpecialAccount(mysql, ident):
    rows = mysql.select("KtNr","KtName = \"" + ident + "\"","KTNR")
    if rows: return rows[0][0]
    else: return 0
##  get individual account from 'KtNr' table
#     return the accountnumber
# @param mysql - database where values are retrieved from
# @param KNr  -  'KundenNr' of account to be selected
# @param typ   -  typ of account to be selected for this 'KNr'
def Afp_getIndividualAccount(mysql, KNr, typ = "Debitor"):
    # first step individual account
    KundenNr = Afp_toString(KNr)
    rows = mysql.select("KtNr","KtName = \"" + KundenNr + "\" AND Bezeichnung = \"" + typ + "\"","KTNR")
    if rows:
        return rows[0][0]
    if typ == "Debitor" or typ == "Kreditor":
        # extract name of Address
        name = None
        rows = mysql.select("Name","KundenNr = " + KundenNr,"ADRESSE")
        if rows:
            name = rows[0][0]
        # second step, try sample account with max, first three letters of name
        if name:
            for i in range(3,0,-1):
                search = "DIV." + name[:i].upper()
                rows = mysql.select("KtNr","KtName = \"" + search + "\" AND Bezeichnung = \"" + typ + "\"","KTNR")
                if rows:
                    return rows[0][0]
        # third step, try global sample account
        rows = mysql.select("KtNr","KtName = \"DIVER\" AND Bezeichnung = \"" + typ + "\"","KTNR")
        if rows:
            return rows[0][0]
    return 0
## returns a single value from database for given criterium, mostly this value ought to be the unique identifier of the table \n
# if value does not exist in table, the value of the next row in sort order will be extracted
# @param mysql - database where values are retrieved from
# @param table  - name of database table where value has to be retrieved from
# @param column - column where value has to be retrieved from-
# @param index -  sort criterium
# @param value -  value of sort criterium to be searched
def Afp_selectGetValue(mysql, table, column, index, value):
    string = Afp_toInternDateString(value)
    rows = mysql.select(column, index + " >= " + string, table, index, "0,1")
    if rows:
        if rows[0]:
            return rows[0][0]
    return None
##  get the list of indecies of named table,
# return a dictionary of names with typ as value. \n
# following types are possible: \n
# - string, int, date, time, float
# @param mysql - database where values are retrieved from
# @param datei  -  name of database table
# @param keep  -  if given, array with name of entries whose values are kept - others will be set to 'None'
# @param indirect  -  if given, array with name of entries whose values will be set to  "" instead of 'None'
# @param special  -  if given, dictionary with special values for string evaluation
def Afp_getOrderlistOfTable(mysql, datei, keep = None, indirect = None, special = None):
    fields, types = mysql.get_info(datei, "fields",  [0, 1])
    indices, columns = mysql.get_info(datei, "index", [2, 4])
    #print "Afp_getOrderlistOfTable input:", datei, keep, indirect, special
    #print "Afp_getOrderlistOfTable:", fields, types, indices, columns
    liste = {}
    name = ""
    for entry in indices:
        if not entry == name:
            name = entry
            if entry == "PRIMARY": name = columns[indices.index(entry)]
            ind = None
            if name in fields:
                ind = fields.index(name)
                if keep is None or name in keep:
                    if "text" in types[ind] or "char" in types[ind]:
                        typ = "string"
                    elif "int" in types[ind]:
                        typ = "int"
                    elif "date" in types[ind]:
                        typ = "date"
                    elif "time" in types[ind]:
                        typ = "time"
                    elif "float" in types[ind]:
                        typ = "float"
                    else:
                        typ = "string"
                    liste[name]  = typ
                else:
                    liste[name] = None
    if special:
        for entry in special:
            if entry in liste:
                liste[entry] = special[entry]
    if indirect:
        for entry in indirect:
            if entry in liste and liste[entry] is None:
                liste[entry] = ""
    return liste

# classes for different uses

##   base class of all Afp-database objects
# common class to hold and manipulate the data for a given afp-module \ņ
# self.selects holds the information how the database tables are connected \n
# The syntax is as follows: \n
# self.selects["selectionname"] = ["tablename","select criterium","unique key"] \n
# - selectionname - string with name of this selection
# - tablename - string with name of table in database
# - select criterium - string holding criterium for selection, references to earlier created selections (mostly mainselection) are possible
# - unique key - (optional) string holding name of unique key in slave-table (tablename), to be refilled into mainselection during storage \n
# Example: \n
# self.selects["ADRESSE"] = ["ADRESSE","KundenNr = KundenNr.Main","KundenNr"] \n
# this will fill the selection ADRESSE with the data of the address with the same id (KundenNr) as in table Main, 
# in case new address data is created, this data gets the internal id during storage. As 'KundenNr' is written in the third place,
# this new created value will be written into the 'Main' table before storing it.
# \n the 'select criterium'  (KundenNr = KundenNr.Main) evaluates as follows: \n
# - if the criterium starts with a '!' the rest of the entry will be taken as select clause as it is written
# - if there is a '.' in the righthand side, this string will be replaced by the appropriate value string (in this case 'KundenNr' in the selection 'Main') and the result is taken as select clause
# -  if there is a '+' in the righthand side, all evaluated value strings will be concatinated to one value string
# - instead of '=' , '>=' and '<=' can be used also
# - more of those criteria can be added using the 'AND' keyword \n\n
# self.selections holds the data retrieved from or to be returned to the table \n
class AfpSelectionList(object):
    ## initialize AfpSelectionList class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param listname - name of this selction list
    # @param debug - flag for debug information
    def  __init__(self, globals, listname, debug = False):
        self.mysql = globals.get_mysql()
        self.globals = globals
        self.listname = listname
        self.mainindex = None
        self.mainvalue = None
        self.mainselection = None
        self.selects = {}
        self.selections = {}
        self.tagmap = None
        self.debug = debug
        self.new = False
        if self.debug: print "AfpSelectionList Konstruktor",listname
    ## destructor
    def __del__(self):   
        if self.debug: print "AfpSelectionList Destruktor" 
    ## return if debug flag is set
    def is_debug(self):
        return self.debug
    ## return if data is new (not yet stored in database)
    def is_new(self):
        return self.new
    ## return globals
    def get_globals(self):
        return self.globals
    ## return mysql connection
    def get_mysql(self):
        return self.mysql   
    ## return name of this SelectionList
    def get_listname(self):
        return self.listname
    ## return main index of this SelectionList
    def get_mainindex(self):
        return self.mainindex
    ## return if this SelectionList has changed
    def has_changed(self):
        has_changed = self.new
        for sel in self.selections:
            has_changed = has_changed or self.selections[sel].has_changed()
        return has_changed
    ## return the names of all Tableselections
    # @param include_mainselection - flas if mainselection name should be included
    def get_selection_names(self, include_mainselection = False):
        names = []
        for sel in self.selects:
            append = True
            if sel == self.mainselection and not include_mainselection: append = False
            if append:
                names.append(sel)
        return names
    ## return column name to be connected to mainindex for indicated selection
    # @param selname - name of selection where target column is extracted
    def get_select_target(self, selname):
        target = None
        if self.selects[selname]:
            select = self.selects[selname][1]
            split = select.split("=")
            target = split[0].strip()
            if  "." in target: target = target.split(".")[0]
        return target
    ## return an afp-unique identifier of this SelectionList
    def get_identifier(self):
        return self.listname + self.get_string_value()
    ## return the name of involved persons
    # @param rev - reverse, first name, followed by surname
    # @param selname - name of TableSelection where to retrieve names
    def get_name(self, rev = False, selname = "ADRESSE"):
        name = ""
        sel = self.get_selection(selname, False)
        if sel:
            if rev:
                name = sel.get_string_value("Name") + " " + sel.get_string_value("Vorname")
            else:
                name = sel.get_string_value("Vorname") + " " + sel.get_string_value("Name")
        return name
    ## show data in console (used for debug)
    def view(self):
        # convenience routine for debug purpose
        print "AfpSelectionList.view():", self.get_listname()
        print self.selects, self.selections
        for sel in self.selections: 
            print sel+":", self.selections[sel].select, self.selections[sel].data
    ## get the user-relevant data in a line \n
    # this routine may (or rather should) be overwritten
    def line(self): 
        row = self.get_value_rows(None, None, 0)
        zeile = Afp_ArraytoLine(row)
        return zeile
    ## generate the customised select_clause of this SelectionList for indicated TableSelection
    # @param selname - name of TableSelection
    def evaluate_selects(self, selname):
        select_clause = None
        order_clause = None
        if selname is None: selname = self.mainselection
        if selname in self.selects:
            if self.selects[selname] == []:
                select_clause = []
            else:
                select = self.selects[selname][1]
                if select[0] == "!": 
                    # fixed fromula, no evaluation
                    select_clause = select[1:]
                else:
                    if "ORDER BY" in select:
                        ord = select.split("ORDER BY")
                        if len(ord) == 2:
                            order_clause = ord[1]
                            select = ord[0]
                    select_clause = ""
                    clauses = select.split("AND")
                    for clause in clauses:
                        sels = clause.split("=")
                        feld = sels[1].strip()
                        if "." in feld: value = self.get_string_value(feld, True)
                        else: value = feld
                        if value:
                            if select_clause: select_clause += " AND "
                            # <=, >= work also, as < and > are kept on the left (not evaluated) side
                            select_clause += sels[0].strip() + " = " + value
            #print "AfpSelectionList.evaluate_selects:", selname, self.selects[selname], "CLAUSE:", select_clause, order_clause
        return select_clause, order_clause
    ## set the customised select_clause for the main selection
    def set_main_selects_entry(self):  
        if self.mainselection and self.mainindex and self.mainvalue:         
            selname = self.mainselection
            self.selects[selname] = [selname, self.mainindex + " = " + self.mainvalue, self.mainindex]
    ## overwrite customised selects with new self.mainvalue
    def reset_selects(self):
        self.set_main_selects_entry()
        self.reload_selection(self.mainselection)
        for selname in self.selects:
            if selname in self.selections and not selname == self.mainselection :   
                self.reload_selection(selname)
    # selection handling
    ## return if a TableSelection exists in selections
    # @param selname - name of TableSelection
    # @param possibly - flag if also the descriptions should be checked
    def exists_selection(self, selname, possibly = False):
        if selname is None: selname = self.mainselection
        if selname in self.selections:
            return  True
        elif possibly and selname in self.selects:
            return True
        else:
            return False
    ## constitute selection formally, no data attached
    # @param selname - name of TableSelection
    def constitute_selection(self, selname):
        selection = None
        if selname is None: selname = self.mainselection
        if selname in self.selects:        
            sel_vals = self.selects[selname]
            if len(sel_vals) > 1:
                implicit = False
                unique = None
                if len(sel_vals) > 2: unique = sel_vals[2]
                #print "AfpSelectionList.constitute_selection:", sel_vals, unique
                selection = AfpSQLTableSelection(self.mysql, sel_vals[0], self.debug, unique)
        return selection  
    ## create selection - retrieve values from database
    # @param select - name of TableSelection
    # @param allow_new - allow creation of a new TableSelection with no data attached
    def create_selection(self, select, allow_new = True):
        if allow_new and self.new: new = True
        else: new = False
        selection = self.constitute_selection(select)
        select_clause, order_clause = self.evaluate_selects(select)
        #print "AfpSelectionList.create_selection:", "\"" + select + "\"", select_clause, new, selection
        if selection is None and select_clause == []:
            if new: selection = self.spezial_selection(select, True)
            else:   selection = self.spezial_selection(select)
        elif selection and select_clause:
            if new: selection.new_data()
            else:   selection.load_data(select_clause, order_clause)
        elif selection is None and select == self.mainselection:
            selection = AfpSQLTableSelection(self.mysql, select, self.debug, self.mainindex)
        if not selection is None:
            self.selections[select] = selection
    ## create all TableSelections
    def create_selections(self):
        for select in self.selects:
            if not select in self.selections:
                self.create_selection(select)
    ## add formula to afterburner of TableSelection
    # @param selname - name of TableSelection
    # @param formula - formula to be evaluated after storage
    def add_afterburner(self, selname, formula):
        selection = self.get_selection(selname)
        selection.add_afterburner(formula)
    ## attach new data to selection
    # @param selname - name of TableSelection
    def reload_selection(self, selname):
        selection = self.get_selection(selname)
        select_clause, order_clause = self.evaluate_selects(selname)
        if selection and select_clause:
            selection.load_data(select_clause, order_clause)
    ## return selection, create new if not existend
    # @param name - if given, name of TableSelection, otherwise get main selection
    # @param allow_new_creation - if selection has to be created allow new plain creation if approritate flag is set
    def get_selection(self, name = None, allow_new_creation = True):
        selection = None
        if name is None: selname = self.mainselection
        else: selname = name
        #print "AfpSelectionList.get_selection:", selname in self.selections, selname#, self.selections
        if not selname in self.selections:  
            self.create_selection(selname, allow_new_creation)
            #print "AfpSelectionList.get_selection created:", selname in self.selections, selname#, self.selections
        if selname in self.selections: 
            selection = self.selections[selname]  
        else:
            selname = selname.upper()
            if not selname in self.selections:  
                self.create_selection(selname)
            if selname in self.selections: 
                selection = self.selections[selname]
        return selection
    ## clear data in selections
    # @param keep - list of names of selections not cleared
    def clear_selections(self, keep):
        self.mainvalue = None
        for sel in self.selections:
            if not sel in keep: 
                if sel == self.mainselection:
                    self.selections[sel].new_data(False, True)
                else:
                    self.selections[sel].new_data(True)
    ## delete selection completely
    # @param selname - name of TableSelection 
    # -  main selection can not be deleted
    def delete_selection(self, selname):
        if selname in self.selections and not selname == self.mainselection:
            del self.selections[selname]
    ## retrieve a selection row and deliver it as a single TableSelection \n
    # use set_row_to_selection_values to write manipulated values to the row again
    # @param selname - name of TableSelection 
    # @param row - index of row in TableSelection where data is retrieved
    def get_selection_from_row(self, selname, row):
        select = self.get_selection(selname)
        selection = select.create_initialized_copy()
        if row is None:
            selection.new_data()
        else:
            rows = select.get_values(None, row)         
            selection.set_data(rows)
        #print "AfpSelectionList.get_selection_from_row:",selname, row, selection
        return selection
    ## insert an empty row to a TableSelection
    # @param selname - name of TableSelection 
    # @param rowNr- index where row in TableSelection should be inserted
    def insert_row(self, selname, rowNr):
        self.get_selection(selname).insert_data_row(rowNr, True)
    ## delete a selection row from a TableSelection
    # @param selname - name of TableSelection 
    # @param rowNr- index of row in TableSelection to be deleted
    def delete_row(self, selname, rowNr):
        self.get_selection(selname).delete_row(rowNr)
      
    ## special selection handling routine to be overwritten for individual selection programming
    # @param selname - name of special TableSelection 
    # @param new - iflag if a new selection without data should be created
    def spezial_selection(self, selname, new = False):
        return None
    ## special selection save routine to be overwritten for individual selection programming
    # @param name - name of special TableSelection 
    def spezial_save(self, name = None):
        return None
      
    ## get number of rows in indicated TableSelection
    # @param name - name of special TableSelection 
    def get_value_length(self, name = None):
        return self.get_selection(name).get_data_length()
    ## extract values from a single TableSelection
    # @param sel - if given name of TableSelection
    # - sel == None: data from mainselection, resp. row
    # - sel == 'Name': data from selection 'name', resp. row
    # @param felder - column names to be retrieved
    # - felder == 'Name1, Name2, ...': data from columns 'Name1, Name2, ... of selection
    # @param row - index of row in TableSelection
    def get_value_rows(self, sel = None, felder = None, row = -1):
        if sel is None and felder is None and row == -1:
            return self.mainvalue
        if sel is None:
            selname = self.mainselection
        else:
            selname = sel
        selection = self.get_selection(selname, False)
        if selection is None:
            return None
        else:
            return selection.get_values(felder, row)
    ## extract values from a different TableSelections
    # @param felder - column and selection names where data has to be retrieved from
    # - felder == None: complete data from mainselection
    # - felder == 'Feld1.Name1, Feld2.Name2, ...': data from column 'Feld1' of selection 'Name1', etc.
    def get_values(self, felder = None):
        if felder is None:
            return self.get_value_rows()
        else: 
            result = []
            fsplit = felder.split(",")
            for feld in fsplit:
                wert = self.get_value(feld)
                result.append(wert)
            return [result]
    ## extract one value from a TableSelection
    # @param DateiFeld - column.selection name where data has to be retrieved from
    def get_value(self, DateiFeld = None):
        if DateiFeld is None:
            return self.mainvalue
        split = DateiFeld.split(".")
        feld = split[0]
        selname = self.mainselection
        if len(split) > 1: selname = split[1]
        selection = self.get_selection(selname, False)
        if selection is None:
            return None
        else:
            return selection.get_value(feld)  
    ## retrieve text from selection, eventually import extern file data into textfield  \n
    # - only needed for intermediate use, may be removed later
    # @param DateiFeld - column.selection name where data has to be retrieved from
    def get_ausgabe_value(self, DateiFeld = None):
        value = self.get_value(DateiFeld)
        #print "AfpSelectionList.get_ausgabe_value:", DateiFeld, ":", value
        if value:
            if Afp_isString(value):
                if len(value) == 16 and value[:6] == "Archiv" and value[-4:] == ".sbt":
                    fname = self.globals.get_value("antiquedir") + Afp_archivName(value, self.globals.get_value("path-delimiter"))
                    wert = Afp_importFileData(fname)
                else:
                    wert = value
            else:
                wert = Afp_toString(value)
        else:
            wert = ""
        return wert
    ## extract one value from a TableSelection, return it as a string
    # @param DateiFeld - column.selection name where data has to be retrieved from
    # @param quoted_string - retuns values as a string, returns strings in quotes
    def get_string_value(self, DateiFeld = None, quoted_string = False):
        value = self.get_value(DateiFeld)
        if value:
            if quoted_string:
                wert = Afp_toQuotedString(value, True) # False?
            else:
                wert = Afp_toString(value)
        else:
            wert = ""
        return wert
    ## extract values from a single TableSelection, return values as strings
    # @param sel - if given name of TableSelection
    # @param felder - column names to be retrieved
    # @param row - index of row in TableSelection
    def get_string_rows(self,  sel = None, felder = None, row = -1):
        rows = self.get_value_rows(sel, felder,row)
        strings =  Afp_ArraytoString(rows)
        return strings
    ## extract one value from a tagged field in a TableSelection, return it as a string
    # @param TaggedFeld - column#i.selection name with i being an integer on which position tagged data has to be retrieved from
    # the i-th part of the comma separated field will be returned, starting the count with 1!
    def get_tagged_value(self, TaggedFeld = None):
        value = ""
        if "#" in TaggedFeld: 
            split = TaggedFeld.split("#")
            datei = ""
            if "." in split[1]:
                splitsplit = split[1].split(".")
                datei = splitsplit[1]
                ind = Afp_fromString(splitsplit[0])
            else:
                ind = Afp_fromString(split[1])
            DateiFeld = split[0]
            if datei: DateiFeld += "." + datei
            string = self.get_string_value(DateiFeld)
            splitstring = string.split(",")
            #print "AfpSelectionList.get_tagged_value analysed", ind, split, DateiFeld, string, splitstring
            if ind > 0 and ind <= len(splitstring): value = splitstring[ind-1]
            if not value and self.tagmap:
                value = self.get_string_value(self.tagmap[TaggedFeld])
            #print "AfpSelectionList.get_tagged_value:", TaggedFeld, ind, value
        else:
            value = self.get_string_value(TaggedFeld)
        return value
    ## set a database lock on the main selection (table) of the SelectionList
    # @param selname - if given name of TableSelection to be locked
    def lock_data(self, selname = None):
        if not self.new:
            self.get_selection(selname).lock_data()   
    ## remove a database lock from the main selection (table) of the SelectionList
    # @param selname - if given name of TableSelection to be unlocked
    def unlock_data(self, selname = None):
        if not self.new:
            self.get_selection(selname).unlock_data()
    ## propgate new mainvalue to the dependent TableSelections
    def spread_mainvalue(self):
        #print "AfpTableSelectionList.spread_mainvalue"
        target = None
        # mainindex 
        source = self.mainindex + "." + self.mainselection
        value = Afp_fromString(self.mainvalue)
        # mainindex filled into all depending selections
        for sel in self.selections:
            if not sel == self.mainselection and self.selections[sel].data:
                select = self.selects[sel][1]
                #print "AfpTableSelectionList.spread_mainvalue select:", sel, select, self.selections[sel].data
                if source in select:
                    split = select.split("=")
                    target = split[0].strip()
                    if  "." in target: target = target.split(".")[0]
                    #print "AfpTableSelectionList.spread_mainvalue target:", sel, target, value
                    if len(split) > 1 and "-" in split[1]:
                        self.selections[sel].spread_value(target, -value)
                    else:
                        self.selections[sel].spread_value(target, value)
    ## sample newly created unique identifier value of dependent selection to the appropriate entries in the main selectrion
    # @param selname - name of TableSelection where new identifier has been created
    def resample_value(self, selname):
        #print "AfpTableSelectionList.resample_value initiated:", selname
        target = None
        source = None 
        value = None 
        # uniqueindex
        selarr = self.selects[selname]
        if len(selarr) > 2:
            source = selarr[2] + "." + selname
        target = selarr[1].split("=")[1].strip()
        #print "AfpTableSelectionList.resample_value source:",source
        if source:
            split = source.split(".")
            #print "AfpTableSelectionList.resample_value split:", source, split
            if self.get_selection(split[1]).is_last_inserted_id(split[0]):
                value = self.get_value(source)
                #print "AfpTableSelectionList.resample_value executed:", source, target, value
                # uniqueindex filled back into mainselection
                self.set_value(target, value)
    ## set a single value of individual TableSelection 
    # @param DateiFeld - column.selection name where data has to be written to
    # @param value - new vaolue of above column
    def set_value(self, DateiFeld, value):
        split = DateiFeld.split(".")
        feld = split[0]
        selname = self.mainselection
        if len(split) > 1: selname = split[1]
        selection = self.get_selection(selname)
        selection.set_value(feld, value)
    ## set multiple  values of indicated TableSelection 
    # @param changed_data - dictionary with changed_data[column] = value
    # @param name - name of TableSelection where data should be written to
    # @param row - index of row in TableSelection where data should be written to \n
    #                        if row < 0: add row with given data
    def set_data_values(self, changed_data, name = None, row = 0):
        selection = self.get_selection(name)
        if row < 0:
            selection.add_data_values(changed_data) 
        else:
            selection.set_data_values(changed_data, row)  
    ## set a row in a TableSelection to the modified values beeing hold in a single TableSelection \n
    # - this single TableSelection should have been extracted with get_selection_from_row from the destination TableSelection \n
    # - it is assumed that both TableSelections have the same tablename
    # @param value_selection - TableSelection holding the changed values
    # @param row - index of row in original TableSelection where data should be written to
    def set_row_to_selection_values(self, value_selection, row = None):
        selection = self.get_selection(value_selection.get_tablename())
        value_row = value_selection.get_values(None)[0]
        mani = [row, value_row]
        #print "AfpSelectionList.set_row_to_selection_values:", mani
        selection.manipulate_data([mani])
    ## extract all possible values and fill it into the own list, if possible complete TableSelections are moved \n
    # this makes only sence for closely related SelectionLists,
    # it works in 4 steps as follows: \n
    # step 1: fill all unset values of the mainselection with value of same name from the victim mainselection \n
    # step 2: get complete data if both refer the same database table \n
    # step 3: get complete data if field names are identic
    # step 4: copy colums needed from data (fill new colums with 'None's) \n
    # @param victim - SelectionList, where data or TableSelections are taken from
    def cannibalise(self, victim, selnames=None):
        names = self.get_selection().get_feldnamen()
        unique = self.get_selection().unique_feldname
        vnames = victim.get_selection().get_feldnamen()
        # step 1: fill all unset values of the mainselection with value of same name from the victim mainselection
        for name in names:
            if not self.get_value(name) and not name == unique:
                if name in vnames:
                    value = victim.get_value(name)
                    if value:
                        self.set_value(name, value)
                        print "AfpSelectionList.cannibalise step 1:", name, value
        if selnames:
            names = selnames
        else:
            names = self.get_selection_names()
        vnames = victim.get_selection_names()
        for name in names:
            if name in vnames:
                to_sel = self.get_selection(name)
                from_sel = victim.get_selection(name)
                indices = [None]
                # step 2: get complete data if both refer the same database table
                if to_sel.get_tablename() == from_sel.get_tablename():
                    identic = True
                    print "AfpSelectionList.cannibalise step 2:", name, identic
                else:
                    # step 3: get complete data if field names are identic
                    indices = Afp_findIndices(to_sel.get_feldnamen(), from_sel.get_feldnamen())
                    identic = True
                    for i in range(len(indices)):
                        if identic and i != indices[i]: 
                            identic = False
                    print "AfpSelectionList.cannibalise step 3:", name, identic
                if identic:
                    # fulfill step 2 and 3 (cannibalise)
                    to_sel.set_data(from_sel.get_values())
                    to_sel.new = from_sel.new
                    to_sel.manipulation = from_sel.manipulation
                    from_sel.set_data(None)
                else:
                    # step 4: copy colums needed from data (fill new colums with 'None's)
                    data = Afp_getColumns(indices, from_sel.get_values())
                    print "AfpSelectionList.cannibalise step 4:", name, indices, data
                    to_sel.set_data(data)
    ## store complete SelectionList
    def store(self):
        self.store_preparation()
        #print "AfpTableSelectionList.store()", self.mainselection
        #print "AfpTableSelectionList.store() selections:", self.selections
        if self.mainselection:
            select = self.selections[self.mainselection]
            print "AfpTableSelectionList.store mainselection:", self.mainselection
            select.store()
            if self.new:
                self.mainvalue = select.get_string_value(self.mainindex)
                # spread mainvalue into selections
                # self.spread_value()
                self.spread_mainvalue()
                print "AfpTableSelectionList.store new mainvalue spreaded to other selections:", self.mainvalue
        #print "AfpTableSelectionList.store() selections 2:", self.selections
        for sel in self.selections: 
            print "AfpTableSelectionList.store:", sel,"ListNew:", self.new,"New:", self.selections[sel].new,"hasChanged:", self.selections[sel].has_changed(),"Select:", self.selections[sel].select,"\n", self.selections[sel].data
            if not (sel == self.mainselection) and self.selections[sel].has_changed():
                if self.selects[sel] == []:
                    self.spezial_save(sel)
                else:
                    self.selections[sel].store()
                # eventually spread unique index back to mainselection
                self.resample_value(sel)
        # second try to catch all spreaded values
        for sel in self.selections:
            print "AfpTableSelectionList.store second try:",sel,"hasChanged:", self.selections[sel].has_changed() 
            if self.selections[sel].has_changed():
                if self.selects[sel] == []:
                    self.spezial_save(sel)
                else:
                    self.selections[sel].store()
    ## get data info (column names of all attached TableSelections)
    def get_data_info(self):
        self.create_selections()
        info = {}
        for entry in self.selections:
            info[entry] = self.get_selection(entry).feldnamen
        return info
    ## complete data to be stored in archive \n
    # @param new_data - data to be completed and written into "ARCHIV" TableSelection \n
    # new_data should already hold the values ["Gruppe"],[ "Bem"], ["Extern"]:
    # - Gruppe: (group) 3rd level identification
    # - Bem:  remark on this entry
    # - Extern:  name of archived file (relativ to archiv path) \n
    # it will be completed by:
    # - Art: (kind) 1st level identification, will be set to "BusAfp"
    # - Typ: (type) 2nd level identification, will be set to SelectionList listname
    def add_to_Archiv(self, new_data):
        selection = self.get_selection("ARCHIV")
        if selection:
            row = selection.get_data_length()
            new_data["Art"] = self.globals.get_value("name")
            new_data["Typ"] = self.listname
            new_data["KundenNr"] = self.get_value("KundenNr")
            new_data["Datum"] = self.globals.today()
            new_data = self.set_archiv_data(new_data)
            selection.set_data_values(new_data, row)
        else:
            print "WARNING SelectionList.add_to_Archiv called but not implemented for", self.listname
    #
    # routines which may be overwritten in devired class, if necessary
    #
    ## routine for preparation of data before storing
    # may be overwritten, if special handling is necessary
    def store_preparation(self):
        return
    ## routine to retrieve payment data from SelectionList \n
    # may be overwritten, default implementation: return "Preis", "Zahlung" and "ZahlDat" column from main selection
    def get_payment_values(self):
        preis = self.get_value("Preis")
        zahlung = self.get_value("Zahlung")
        if preis is None: preis = 0.0
        if zahlung is None: zahlung = 0.0
        return preis, zahlung, self.get_value("ZahlDat")
    ## routine to set payment data in SelectionList \n
    # may be overwritten, default implementation: "Zahlung" and "ZahlDat" columns of main selection are set
    # @param payment - amount that already has been payed
    # @param datum - date of last payment
    def set_payment_values(self, payment, datum):
        self.set_value("Zahlung", payment)
        self.set_value("ZahlDat", datum)
    ## set identification data for archive \n
    # default implementation: add name of maintable and mainvalue \n
    # - may be overwritten if necessary
    # @param data - dictionary where identifiers should be added
    def set_archiv_data(self, data):
        data["Tab"] = self.get_selection().get_tablename()
        data["TabNr"] = self.get_value()
        return data
    #    
    # routines to be overwritten in devired class
    #
    ## return specific identification string to be used in dialogs \n
    # - should be overwritten in devired class
    def get_identification_string(self):
        return ""
        
    ## class for handling extern numberations       
class AfpExternNr(AfpSQLTableSelection):
    ## initialize AfpExternNr class
    # @param globals - global values including the mysql connection - this input is mandatory
    def  __init__(self, globals, Typ = None, debug = None):
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        AfpSQLTableSelection.__init__(self, globals.get_mysql(), "EXTERNNR", self.debug)
        self.typ = Typ
        if Typ == "Monat":
            today = globals.today()
            jahr = Afp_toString(today.year)[-2:]
            mon = Afp_toString(today.month)
            if len(mon) < 2: mon = "0" + mon
            self.prefix = jahr + mon
            self.separator = "."
        if self.debug: print "AfpExternNr Konstruktor"
    ## destuctor
    def __del__(self):    
        if self.debug: print "AfpExternNr Destruktor"
    ## generate new extern number for given prefix and separator
    def get_number(self):
        ExtNr = None
        nr = None
        self.select = "Typ = \"" + self.typ + "\" AND Pre = \"" + self.prefix + "\""
        self.lock_data()
        self.load_data(self.select)
        lgh = self.get_data_length()
        if lgh == 0:
            nr = 1
            self.add_row([self.typ, self.prefix, nr, self.typ+self.prefix])
        elif lgh > 1:
            print "WARNING: AfpExternNr.gen_number datalength not 1 but:", lgh
        else:
            nr = self.get_value("Nummer") + 1
            self.set_value("Nummer", nr)
        if nr:
            self.store()
            ExtNr = self.prefix + self.separator + Afp_toString(nr)
        #self.unlock_data()
        return ExtNr
          
##  class to export Afp-database entries to other formats 
class AfpExport(object):
    ## initialize AfpExport class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param data - TableSelection holding the data to be written    
    # @param filename - name of file data is written to, \n
    #  at the moment the following formats are supported \n
    #  - .asc - ASCII file, static length \n
    #  - .csv - ASCII file, comma separated values \n
    #  - .dbf - DBF database file \n
    # @param debug - flag for debug information
    def  __init__(self, globals, data, filename, debug = False):
        self.globals = globals
        self.mysql = globals.get_mysql()
        self.data = data
        self.filename = filename
        self.fieldlist = None
        self.information = None
        self.export_available = False
        self.module = None
        self.debug = debug
        split = filename.split(".")
        self.type = split[-1].lower()
        if self.type == "asc" or self.type == "csv":
            self.export_available = True
        elif self.type == "dbf":
            if AfpPy_checkModule('dbfpy'):
                self.module = Afp_importPyModul("AfpBase.AfpDatabase.AfpDBF", globals)
            if self.module:
                self.export_available = True
        if self.debug: print "AfpExport Konstruktor",filename
        if not self.export_available:
            print "WARNING Export-modul for file of type \"." +self.type + "\" not available!"
    ## destructor
    def __del__(self):   
        if self.debug: print "AfpExport Destruktor" 
    ## append data to each accounting row
    # @param liste - dicionary of names of appendend columns, holding the fieldnames of addressdata to be appended (["Name,Vorname","Strasse"]) 
    # @param table - name of table where additional data should be extracted from (default: "ADRESSE")
    # @param ident - name of column which provides the connection value between both tables (default: "KundenNr")
    def append_data(self, liste, table = "ADRESSE", ident = "KundenNr"):
        #print "AfpExport.append_data enty:",liste 
        if liste:
            select = self.data
            #print "AfpExport.append_data 1:", select.data, select.feldnamen
            indices = []
            rowinds = [0]
            count = 0
            felder = ""
            for name in liste:
                if not name in select.feldnamen:
                    select.feldnamen.append(name)
                indices.append(select.feldnamen.index(name))
                fields = liste[name].replace(" ",",")
               # print name, fields, fields.count(",")
                count += fields.count(",") + 1
                rowinds.append(count)
                felder +=  fields + ","
            felder = felder[:-1]
            #print "AfpExport.append_data indices:", liste, indices, rowinds, felder
            for i in range(select.get_data_length()):
                val = select.get_values(ident, i)[0][0]
                row = self.mysql.select(felder,ident + " = " + Afp_toInternDateString(val), table)[0]
                for j in range(len(liste)):
                    data = Afp_ArraytoLine(row[rowinds[j]:rowinds[j+1]])
                    if len(select.data[i]) <= indices[j]:
                        select.data[i].append(data)
                    else:
                        select.data[i][indices[j]] = data
            self.data = select
    ## writes data to fixed lenght ascii file
    # @param data - array with names of values read from data 
    # @param fixed - length of each fields, if not given the following parameters are used
    # @param separator - field separator to be used
    # @param paranthesis - paranthesis to be used to enclose strings
    def write_ascii_field(self, data, fixed, separator, paranthesis):
        string = Afp_toString(data)
        if fixed:
            lgh = len(string)
            if lgh < fixed:
                if Afp_isNumeric(data):
                    num = True
                else:
                    num = False
                for i in range(lgh,fixed):
                    if num: string = " " + string
                    else: string += " "
            if lgh > fixed: string = string[:fixed]
        else:
            if paranthesis:
                string = paranthesis + string + paranthesis
            string += separator
        return string
   ## writes data to fixed lenght ascii file
    # @param fieldlist - array with names of values read from data 
    # @param info - linfo for ascii output, as follows
    # - .asc - length of each fields (default: 50)
    # - .csv - field delimiter, text bracket, separated by spaces (default: delimiter - ",", no brackets)
    def write_to_ascii_file(self, fieldlist, info):
        if fieldlist: write = True
        else: write = False
        cut = False
        fix = 0
        sep = ","
        paras = None
        if self.type == "asc":
            if info: fix = int(info)
            if fix < 1: fix = 50
        elif self.type == "csv": 
            if info:
                split = info.split()
                if split[0]: sep = split[0]
                if len(split) > 1 and split[1]:
                    paras = split[1]
            cut = True
        else:
            write = False
        if write:
            fout = open(self.filename, 'w')
            felder = Afp_ArraytoLine(fieldlist,",")
            daten = self.data.get_values(felder)
            for row in daten:
                line = ""
                for entry in row: 
                    string = self.write_ascii_field(entry, fix, sep, paras)
                    line += string
                if cut: line = line[:-1]
                #print "exportline:",line
                fout.write(line + '\n')
            fout.close()
    ## writes data to different fileformats
    # @param fieldlist - is used as follows: \n
    # - .asc,csv - array with names of values read from data \n
    # - .dbf - dictionary how data is mapped into output file (output[entry] = value(parameter[entry])), \n 
    # @param info - if given, is used as follows:
    # - .asc - length of each fields (default: 50)
    # - .csv - field delimiter, text bracket, separated by spaces (default: delimiter - ",", no brackets)
    # - .dbf - template file which is used to create output, 
    #            if type is list, description for generation of dbf-file fields: [name, typ, parameter]
    def write_to_file(self, fieldlist, info):
        if self.debug: print "AfpExport.write_to_file:",fieldlist, info
        if self.type == "asc" or self.type == "csv" :
            self.write_to_ascii_file(fieldlist, info)
        elif self.type == "dbf":
            if self.module:
                self.module.Afp_writeToDBFFile(self.data, self.filename, info, fieldlist, self.debug)
        else:
            print "WARNING: AfpExport, output to a file of type \"." + self.type + "\" not yet implemented!"

##   smtp mail-sender
class AfpMailSender(object):
    ## initialize AfpMailSender class
    # @param globals - globals variables possibly holding smtp-server data
    # @param debug - flag for debug information
    def  __init__(self, globals, debug = False):
        self.globals = globals
        self.subject = None
        self.sender = None
        self.recipients = []
        self.debug = debug
        self.message = None
        self.htmltext = None
        self.attachments = []
        self.server = None
        self.serverport = 25
        self.starttls = None
        self.user = None
        self.word = None
        # look for data in globals
        server = self.globals.get_value("smtp-host")
        if server:
            split = server.split(":")
            self.server = split[0]
            if len(split) > 1:
                self.serverport = int(split[1])
            self.starttls =  self.globals.get_value("smtp-starttls")
            self.user =  self.globals.get_value("smtp-user")
            self.word =  self.globals.get_value("smtp-word")
            self.sender = self.globals.get_value("mail-sender")
            if self.sender is None and self.user and Afp_isMailAddress(self.user):
                self.sender = self.user
        if self.debug: print "AfpMailSender Konstruktor"
    ## return if automatic sending may be possible
    def is_possible(self):
        return self.server and self.sender
    ## return if mail is ready to be send
    def is_ready(self):
        ready = True
        if not self.is_possible():
            ready = False
        elif not self.recipients:
            ready = False
        elif self.subject is None:
            ready = False
        elif self.message is None and self.htmltext is None:
            ready = False
        return ready
    ## clear data for new email
    def clear(self):
        self.subject = None
        self.recipients = []
        self.message = None
        self.htmltext = None
        self.attachments = []
    ## fill line with attachment names
    def get_attachment_names(self):
        deli = self.globals.get_value("path-delimiter")
        attachs = ""
        for attach in self.attachments:
            if attach: attachs += attach.split(deli)[-1] + ", "
        if attachs: attachs = attachs[:-2]
        return attachs
    ## set emali-addresses 
    # @param sender -  sender mailaddress
    # @param recipient - if given, recipient mailaddress
    def set_addresses(self, sender, recipient = None):
        if Afp_isMailAddress(sender):
            self.sender = sender
        if recipient:
            self.add_recipient(recipient)
    ## set plain text message body
    # @param subject - subject of message
    # @param message - message body
    def set_message(self, subject, message):
        if subject: self.subject = subject.encode('iso8859_15')
        self.message = message.encode('iso8859_15')
    ## set html text message body
    # @param subject - subject of message
    # @param message - message body
    def set_html_message(self, subject, message):
        if subject: self.subject = subject.encode('iso8859_15')
        self.htmltext = message
    ## add attachment file to message (may be invoked several times)
    # @param filename - path of file to be attached
    def add_attachment(self, filename):
        filename = filename.strip()
        if Afp_existsFile(filename):
            self.attachments.append(filename)
    ## add attachment file to message (may be invoked several times)
    # @param recipient - mail address where mail is to be send to
    def add_recipient(self, recipient):
        if Afp_isMailAddress(recipient):
            self.recipients.append(recipient)
    ## set connection information of smtp-server where mail has to be delivered
    # @param host - string defining host[:port] to be connected
    # @param user - if given, username to be used for login
    # @param word - if given, password to be used for login (login will only be invoked if user and word are given)
    # @param tls - flag if starttls connection has to be used DEFAULT: False
    def set_server(self, host, user = None, word = None, tls = False):
        split = host.split(":")
        self.server = split[0]
        if len(split) > 1:
            self.serverport = int(split[1])
        self.user = user
        self.word = word
        self.starttls = tls
    ## deliver mail to smtp server
    def send_mail(self):
        Afp_sendOverSMTP(self.sender, self.recipients, self.subject, self.message, self.htmltext,  self.attachments, self.server, self.serverport, self.debug, self.starttls, self.user, self.word)
    ## view mailer details (for debug)
    def view(self):
        print "AfpMailSender server:", self.server
        print "AfpMailSender serverport:", self.serverport
        print "AfpMailSender starttls:", self.starttls
        print "AfpMailSender user:", self.user
        print "AfpMailSender word:", self.word
        print "AfpMailSender subject:", self.subject
        print "AfpMailSender sender:", self.sender
        print "AfpMailSender recipients:", self.recipients
        print "AfpMailSender message:", self.message
        print "AfpMailSender htmltext:", self.htmltext
        print "AfpMailSender attachments:", self.attachments

# database tables
## get dictionary with required database tables and mysql generation code
# @param flavours - if given list of flavours of moduls
def AfpBase_getSqlTables(flavours = None):
    required = {}
    required["AUSGABE"] = """CREATE TABLE `AUSGABE` (
  `BerichtNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `Modul` tinytext CHARACTER SET latin1 NOT NULL,
  `Art` tinytext CHARACTER SET latin1 NOT NULL,
  `Typ` tinytext CHARACTER SET latin1 NOT NULL,
  `Datei` char(20) CHARACTER SET latin1 NOT NULL,
  `Bez` tinytext CHARACTER SET latin1 NOT NULL,
  `Stempel` tinytext CHARACTER SET latin1 DEFAULT NULL,
  PRIMARY KEY (`BerichtNr`),
  KEY `BerichtNr` (`BerichtNr`),
  KEY `Bez` (`Bez`(50))
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # return data
    return required