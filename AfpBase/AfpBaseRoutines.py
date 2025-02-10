#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseRoutines
# AfpBaseRoutines module provides the base class for all 'Selection Lists', \n
# and Afp specific utility routines with or without database access \n
# it holds the calsses
# - AfpSelectionList
#
#   History: \n
#        21 Feb. 2022 - AfpEmailSender: add attachment conversion to pdf - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        15 Jan 2020 - add mainfilter in AfpSelectionList- Andreas.Knoblauch@afptech.de \n 
#        22 Aug 2019 - Enhence export and add import- Andreas.Knoblauch@afptech.de \n 
#        31 Jan. 2018 - AfpSelectionList: allow tagged value evaluation - Andreas.Knoblauch@afptech.de \n
#        28 Mar. 2016 - AfpSelectionList: add afterburner to be used in second save step - Andreas.Knoblauch@afptech.de \n
#        04 Feb. 2015 - add data export to dbf - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de


#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
#    Copyright© 1989 - 2023 afptech.de (Andreas Knoblauch)
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
from AfpBase.AfpDatabase.AfpSQL import AfpSQL, AfpSQLTableSelection
from AfpBase.AfpUtilities import *
from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpUtilities.AfpBaseUtilities import *

# definition routines
## get all possible module with own graphical interfaces (screens) \n
# if globals are given, only modules available for this program are returned
# @param globals - if given, global variables holding graphic modulnames
def Afp_graphicModulNames(globals = None):
    modules = ["Adresse","Charter","Event:Tourist","Event:Verein","Event","Faktura","Finance"]
    if globals:
        mods = globals.get_value("graphic-moduls")
        if mods: modules = mods
    return modules
## get all possible internal moduls\n
# if globals are given, only modules available for this program are returned
# @param globals - if given, global variables holding  graphic modulnames
def Afp_internalModulNames(globals = None):
    #modules = ["Finance","Einsatz","Calendar"]
    modules = ["Einsatz","Calendar"]
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
    if globals and not globals.is_strict() and mods:
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
        if modul == "Calendar":
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
                if ":" in mod: mod = mod.split(":")[1]
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
# @param data - data for program execution
# @param debug - flag for debug messages
def Afp_startExtraProgram(filepath, globals, data, debug = False):
    if debug: print("Afp_startExtraProgram:",filepath)
    split = filepath.split(globals.get_value("path-delimiter"))
    modul = split[-1]
    path = filepath[:-len(modul)]
    modul = modul.split(".")[0] 
    pymodul = AfpPy_Import(modul, path)
    if pymodul:
        pymodul.AfpExtra(globals, data, debug)
    else:
        print("WARNING: extra program not available -",filepath)
##  starts a programfile with the associated program
# @param filename - name of file to be opened
# @param globals - global variables to hold file associations
# @param debug - flag for debug messages
# @param noWait - flag if execution of python program should be continued direct after starting execution of file
def Afp_startFile(filename, globals=None, debug = False, noWait = False):
    if debug: print("Afp_startFile:",filename)
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
            if debug: print("Afp_startRoutine:", pyBefehl)
            exec(pyBefehl)
            executed = True
    return executed

##   dynamic import of a python module from modulname,
# a handle to the modul will be returned
# @param modulname -  name of modul to be imported, in python modul syntax "package.modul"
# @param globals - global variables including the path delimiter to be used for filesystem pathes
def Afp_importPyModul(modulname, globals):
    debug = globals.is_debug()
    strict = globals.get_value("strict-modul-handling")
    if debug: print("Afp_importPyModul direct:", modulname)
    modul = AfpPy_Import(modulname)
    if not modul and not strict:
        deli = globals.get_value("path-delimiter")
        path = globals.get_programpath()
        if not path[-1] == deli: path += deli
        split = modulname.split(".")
        mod = split[-1]
        for i in range(len(split)-1):
            path += split[i] + deli
        if debug: print("Afp_importPyModul dynamic:", modulname, mod, path)
        modul = AfpPy_Import(mod, path)
    return modul
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
    info_keys = list(info.keys())
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
    line_keys = list(lines.keys())
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
## get age of input date
# @param datum - string of birthdate for which age has to be determined
# @param daysharp - flag if age has to be determinded day sharp or year sharp, default: False
# @param default - default age returned, when no date is given, default: 1
def Afp_getAge(datum, daysharp = False, default = 1):
    age = default
    date = Afp_fromString(datum)
    if date:
        today = Afp_getToday()
        age = today.year - date.year
        if daysharp and (date.month > today.month or (date.month == today.month and date.day >= today.day)):
            age -= 1
    if age < 0: age = 100 + age
    #print "Afp_getAge:", datum, age
    return age
## get a birthday list (firtsname, name, birthday)
# @param mysql - mysql connection
# @param interval - lentgh of interval from today
def Afp_getBirthdayList(mysql, interval, secondtable, filter):
    com1 = "SELECT a.Vorname, a.Name, a.Geburtstag FROM ADRESSE AS a"
    com2 =  "(DATE_ADD(a.Geburtstag, INTERVAL YEAR(CURDATE())-YEAR(a.Geburtstag) + IF(DAYOFYEAR(CURDATE()) > DAYOFYEAR(a.Geburtstag),1,0) YEAR) BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL " + Afp_toIntString(interval) + " DAY))"
    if secondtable:
        com1 += "," + secondtable + " AS b"
        com2 = filter + " AND " + com2
    command = com1 + " WHERE " + com2 +";"
    rows = mysql.execute(command)
    if not rows: rows = []
    dats = []
    todat = Afp_toDateString(Afp_getToday(),"mm-dd")
    for row in rows:
        dats.append(Afp_toDateString(row[2],"mm-dd"))
    if dats: dats, rows = Afp_sortSimultan(dats, rows)
    index = None
    for i in range(len(dats)):
        dat = dats[i]
        if dat < todat: index = i
    if not index is None:
        if index < len(dats):
            index += 1
            dats = dats[index:] + dats[:index]
            rows = rows[index:] + rows[:index]
    #print ("Afp_getBirthdayList dats year:", dats)
    return rows

##  provide a list from a SQLTableSelection object - \n
#    mostly to allow additional selection
# @param table_sel - input AfpSQLTableSelection object for which an additional selection has to be made
# @param filter       - filter to get possible additional selections from database
# @param ident      - identification column for filtered data entries 
# @param order     - order in which list is displayed
# @param keep      - column which could skip check for double entries 
def Afp_getListe_fromTableSelection(table_sel, filter, ident, order = None, keep = None):
    #print ("Afp_getListe_fromTableSelection input:",  table_sel, filter, ident, order, keep)
    attributs = table_sel.create_initialized_copy()
    attributs.load_data(filter, order)
    #print ("Afp_getListe_fromTableSelection init:",  table_sel, table_sel.data, attributs, attributs.data)
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
            #print ("Afp_getListe_fromTableSelection keep:", i, attributs.get_values(keep, i)[0][0], check)
            if check:
                for j in range(table_sel.get_data_length()):
                    # delete entries already in table_sel 
                    #print ("Afp_getListe_fromTableSelection check:", i, j, i-deleted, table_sel.get_values(ident, j) == attributs.get_values(ident, i), table_sel.get_values(ident, j), attributs.get_values(ident, i))
                    if table_sel.get_values(ident, j) == attributs.get_values(ident, i):
                        manipulate.append([i - deleted, None])
                        deleted += 1
                        break
    #print ("Afp_getListe_fromTableSelection:", manipulate)
    if manipulate:
        attributs.manipulate_data(manipulate)
    liste = []
    for i in range(attributs.get_data_length()):
        liste.append(attributs.get_values(ident, i)[0][0])
    # return a slice to be shown (liste) and the complete values (attributs.get_values()) for further use
    #print "Afp_getListe_fromTableSelection exit:",  table_sel, table_sel.data, attributs, attributs.data
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
    if debug: print("Afp_verifyDatabase available modules:", modules)
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
    #print ("Afp_verifyDatabase required Tables :", required)
    for tab in required:
        if tab in tables:
            required[tab] = ""
    needed = []
    for tab in required:
        if required[tab]:
            needed.append(tab)        
    if debug: print("Afp_verifyDatabase tables to be created:", needed)
    if create:
        for tab in required:
            if required[tab]:
                #print ("Afp_verifyDatabase required tab:", required[tab])
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
        if globals.is_debug(): print("Afp_getPyModTables execute:", befehl)
        loc = locals()
        exec(befehl, {}, loc)
        local = loc["local"]
        if local:
            required = Afp_addDict(required, local)
    return required

##  retrieve a list of database entries with same field values from table
# @param mysql - database where values are retrieved from
# @param table  - name of database table where values are retrieved from
# @param field   - name of field for which data with a given value is to be retrieved
# @param value  - value of field for which data is to be retrieved
# @param debug  - flag for debug messages
# @param felder  - names of tablecolumns from which values are catched
# @param filter  - additional filter to be used
def Afp_selectSameValue(mysql, table, field, value, debug = False, felder = None, filter = None):
    #debug = True # for testreasons
    selection = AfpSQLTableSelection(mysql, table, debug, False)
    sel = ""
    if field and not value is None:
        sel = field + " = " + Afp_toString(value) 
    if filter:
        if sel:
            filter =  " AND " + filter
    else:
        filter = ""
    #print "Afp_selectSameValue:", table, field, sel, "Filter:", filter
    selection.load_data(sel + filter)
    return selection.get_values(felder)
##  retrieve a list of database entries with same "KundenNr" from table
# @param mysql - database where values are retrieved from
# @param table  - name of database table where values are retrieved from
# @param KNr      - value of "KundenNr" for values to be retrieved
# @param debug  - flag for debug messages
# @param felder  - names of tablecolumns from which values are catched
# @param filter_feld  - name tablecolumn where additional filter is used
# @param wanted_values  - values which are accepted in the tablecolumn 'filter_feld'
def Afp_selectSameKundenNr(mysql, table, KNr, debug = False, felder = None, filter_feld = None, wanted_values = None):
    if filter_feld and wanted_values:
        filter = ""
        for want in wanted_values:
            filter += " AND " + filter_feld + " = " + Afp_toString(want)
        filter = filter[5:]
    else:
        filter = None
    return  Afp_selectSameValue(mysql, table, "KundenNr", KNr, debug, felder, filter)
##  get special account from 'KtNr' table
#     return the accountnumber
# @param mysql - database where values are retrieved from
# @param ident  - identifier of account to be selected
# @param index  - index to be searched, default: 'KtName'
# @param field  - field to be returned, default: 'KtNr'
def Afp_getSpecialAccount(mysql, ident, index = "KtName", field = "KtNr"):
    rows = mysql.select(field, index + " = \"" + ident + "\"","KTNR")
    #print ("Afp_getSpecialAccount:", ident,  index, field, index + " = \"" + ident + "\"", rows)
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
        
## class for handling extern numberations       
class AfpExternNr(AfpSQLTableSelection):
    ## initialize AfpExternNr class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param typ - Typ of number generation, at the moment possible are: 'Month', 'Count'
    # @param data - if given, prefix for string creation for type 'Count'
    # @param debug - if given, debug flag
    def  __init__(self, globals, Typ = None, data = None, debug = None):
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        AfpSQLTableSelection.__init__(self, globals.get_mysql(), "EXTERNNR", self.debug)
        self.typ = Typ
        self.prefix = ""
        self.separator = ""
        if Typ == "Month":
            tp = type(data)
            if tp == datetime.date or tp == datetime.datetime:
                day = data
            else:
                day = globals.today()
            jahr = Afp_toString(day.year)[-2:]
            mon = Afp_toString(day.month)
            if len(mon) < 2: mon = "0" + mon
            self.prefix = jahr + mon
            self.separator = "."
        elif Typ == "Count":
            if data: self.prefix = data
        if self.debug: print("AfpExternNr Konstruktor")
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpExternNr Destruktor")
    ## generate new extern number for given prefix and separator
    def get_number(self):
        Nr = None
        self.select = "Typ = \"" + self.typ + "\" AND Pre = \"" + self.prefix + "\""
        #print("AfpExternNr.get_number select:", self.select)
        self.lock_data()
        self.load_data(self.select)
        lgh = self.get_data_length()
        if lgh == 0:
            Nr = 1
            self.add_row([self.typ, self.prefix, Nr, self.typ+self.prefix])
        elif lgh > 1:
            print("WARNING: AfpExternNr.get_number datalength not 1 but:", lgh)
        else:
            Nr = self.get_value("Nummer") + 1
            self.set_value("Nummer", Nr)
        if Nr:
            self.store()
        else:
            self.unlock_data()
        return Nr
    ## generate new number string
    def get_number_string(self):
        ExtNr = None
        Nr = self.get_number()
        if Nr:
            ExtNr = self.prefix + self.separator + Afp_toString(Nr)
        return ExtNr
    ## store given value into database
    def set_number(self, Nr):
        self.select = "Typ = \"" + self.typ + "\" AND Pre = \"" + self.prefix + "\""
        #print("AfpExternNr.set_number select:", self.select)
        self.lock_data()
        self.load_data(self.select)
        lgh = self.get_data_length()
        if lgh > 1:
            print("WARNING: AfpExternNr.set_number datalength not 1 but:", lgh)
        else:
            if lgh == 0:
                self.add_row([self.typ, self.prefix, Nr, self.typ+self.prefix])
                self.store()
            else: 
                act = self.get_value("Nummer")
                print("AfpExternNr.set_number nummer:", act, "->", Nr)
                if Nr > act:
                    self.set_value("Nummer", Nr)
                    self.store()
        self.unlock_data()

##  class to import files into Afp-Objects
class AfpImport(object):
    ## initialize AfpImport class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param filename - name of file to be imported, \n
     # @param parameter - if given, parameter for import, depending of import type, \n
    #                                   type csv: column map { fieldname1: column1, ...}, where column can be name from first line or indexnumber,\n
    #  at the moment the following formats are supported \n
    #  - .xml - XML file according to namespace http://www.afptech.de/XML/AfpDocument \n
    #  - .csv- CSV file, data (AfpSelectionList) is given direct into the read_file method \n
    # @param debug - flag for debug information
    def  __init__(self, globals, filename, parameter = None, debug = False):
        self.globals = globals
        self.filename = filename
        self.parameter = parameter
        self.debug = debug
        self.modul = None
        # values used for csv-import
        self.csv_delimiter = [","]
        self.csv_reverseflag = False
        self.csv_textbrackets = ["\""]
        self.csv_use_column_header = None
        self.column_map = None
        # values used for xml-import
        self.value_tags =  ["AfpValue"]
        self.value_end_tags =  ["/AfpValue"]
        self.valid_tags =  ["AfpDocument"]
        self.valid_end_tags =  ["/AfpDocument"]
        self.tag_interpreter = None
        # internal values
        self.import_available = False
        split = filename.split(".")
        self.type = split[-1].lower()
        if self.type == "xml" or self.type == "csv":
            self.import_available = True
            if self.type == "csv" and self.parameter:
                self.csv_use_column_header = False
                for par in self.parameter:
                    if Afp_isString(self.parameter[par]): 
                        self.csv_use_column_header = True
        if self.debug: print("AfpImport Konstruktor",filename)
        if not self.import_available:
            print("WARNING Import-modul for file of type \"." +self.type + "\" not available!")
    ## destructor
    def __del__(self):   
        if self.debug: print("AfpImport Destruktor")  
              
    ## create object from given type
    # @param type - modul of object (taken from python class definition)
    def create_object(self, type):
        data = None
        split = type.split(".")
        objname = split.pop()
        modulname =".".join(split)
        modulpath = self.globals.get_value("path-delimiter").join(split) + ".py"  
        self.modul = AfpPy_Import(modulname, modulpath)
        #print "AfpImport.create_object:", modulname, self.modul
        if self.modul:
            befehl = "data = self.modul." + objname + "(self.globals)"
            #local = locales()
            local = locals()
            exec(befehl, {}, local)
            data = local["data"]
        #print "AfpImport.create_object:", data
        return data
        
    ## get file header
    # @param nlines - number of lines to be read
    def get_file_header(self, nlines = 3):
        lines = []
        fin  = open(self.filename, 'r')
        for i, line in enumerate(fin):
            lines.append(line)
            if i >= nlines-1: break
        fin.close()
        return lines
            
    ## read file
    # @param data - if given, AfpSelectionlList where data has to be filled into the main selection
    def read_from_file(self, data=None):
        res = None
        if self.type == "xml":
            res = self.read_from_xml_file()
        elif self.type == "csv":
            res = self.read_from_csv_file(data)
        return res
    #
    # specific methods for csv import
    #
    ## set parameter for csv-import
    # @param delimiter - list holding all valid delimiters between the columns
    # @param brackets - list with max. 2 entries holding the signs which delimit connected text, where delimiters do not split up the text
    # @param rev - if given, reverse flag, the lines are read in the reverse order
    def set_csv_parameter(self, delimiter, brackets, rev = None):
        if self.type == "csv":
            if delimiter:
                self.csv_delimiter = delimiter
            if not rev is None:
                self.csv_reverseflag = rev
            self.csv_textbrackets = brackets
    ## set column indices due to parameter
    # @param header - line with identifiers for columns
    def set_column_map(self, header):
        head = self.split_csv_line(header)
        self.column_map = {}
        #print ("AfpImport.set_column_map:", head)
        for entry in self.parameter:
            if Afp_isString(self.parameter[entry]):
                self.column_map[entry] = head.index(self.parameter[entry])
            else:
                self.column_map[entry] = int(self.parameter[entry])
    ## read a csv line according to given parameters
    # @param line - line to be splitted
    def split_csv_line(self, line):
        line = line.strip()
        inside = []
        if self.csv_textbrackets:
            start = self.csv_textbrackets[0]
            if len(self.csv_textbrackets) > 1:
                end = self.csv_textbrackets[1]
            else:
                end = start
            inside, outside = Afp_between(line, start, end)
        else:
            outside = [line]
        #print ("AfpImport.split_csv_line:", inside, outside)
        list = []
        lgh = len(outside)
        lin = len(inside)
        for i in range(lgh):
            split = Afp_split(outside[i], self.csv_delimiter)
            #print ("AfpImport.split_csv_line split:", i, outside[i], split)
            if i == 0 and not split[0]: split = split[1:]
            if i == lgh-1 and not split[-1]: split = split[:-1]
            for sp in split:
                list.append(sp)
            if i < lin:
                list.append(inside[i])
           # print ("AfpImport.split_csv_line list:", list)
        #print ("AfpImport.split_csv_line result:", list)
        return list
    ## load data from column data into dictionary
    # @param list - list of columns of one row
    def read_column_data(self, list):
        data = None
        if self.column_map and list:
            data = {}
            lgh = len(list)
            for entry in self.column_map:
                index = self.column_map[entry]
                if index < lgh and list[index] != "":
                    data[entry] = Afp_fromString(list[index])
        return data
                
    ## read a csv file according to given parameters
    # @param data - AfpSelectionList where data has to be filled into the main selection
    def read_from_csv_file(self, data):
        fdata = Afp_importFileLines(self.filename)
        if  self.csv_use_column_header:
            self.set_column_map(fdata[0])
            fdata = fdata[1:]
        if self.csv_reverseflag: fdata.reverse()
        for line in fdata:
            list = self.split_csv_line(line)
            #print ("AfpImport.read_from_csv_file:", list)
            new_data = self.read_column_data(list)
            data.set_data_values(new_data, None, -1)
        return [data]
    #
    # specific methods for xml import
    #
    ## set tags and routine for customised xml- import
    # @param valid_tags - list of tags to enclose valid parts
    # @param value_tags - list of tags to directly enclose values
    # @param interpreter - if given, name of routine to interprete tags
    # @param parameter - if given, additional parameterstring for interpreter routine
    def customise_xml(self, valid_tags, value_tags, interpreter = None, parameter = None):
        if self.debug: print("AfpImport.customise_xml:", valid_tags, value_tags, interpreter, parameter)
        if valid_tags:
            self.valid_tags = valid_tags
            self.valid_end_tags = []
            for tag in valid_tags:
                self.valid_end_tags.append("/"+tag)
        if value_tags:
            self.value_tags = value_tags
            self.value_end_tags = []
            for tag in value_tags:
                self.value_end_tags.append("/"+tag)
        if interpreter:
            split = interpreter.split(".")
            routine = split.pop()
            modulname =".".join(split)
            modulpath = self.globals.get_value("path-delimiter").join(split) + ".py"  
            self.modul = AfpPy_Import(modulname, modulpath)
            self.tag_interpreter = routine
            self.parameter = parameter
    ## extract xml tags from file
    def extract_xml_tags(self):
        tags = None
        fdata = Afp_importFileLines(self.filename)
        #print ("Afp_extractXMLTags fdata:", fdata) 
        #print ("Afp_extractXMLTags valid tags:", self.valid_tags) 
        if fdata:
            tags = []
            is_valid = False
            for line in fdata:
                inval, outval= Afp_between(line, "<",">") 
                #print ("Afp_extractXMLTags line:", line, inval, outval)
                if len(outval) > len(inval):
                    outval.pop(0) # first value outside brackets is not relevant
                for i in range(len(inval)):
                    typ = None
                    if not is_valid:
                        for entry in self.valid_tags:
                            if entry == inval[i].split(" ")[0]: is_valid = True
                    if is_valid:
                        for entry in self.valid_end_tags:
                            if entry == inval[i]: is_valid = False
                        if inval[i] in self.value_end_tags:
                            typ, attrib = self.get_xml_attribs(inval[i-1])
                            name = None
                            if attrib and "name" in attrib: name = attrib["name"]
                            value = outval[i-1]
                        else:
                            active = True
                            for entry in self.value_tags:
                                if entry == inval[i].split(" ")[0]: active = False
                            if active: 
                                typ, attrib = self.get_xml_attribs(inval[i])
                                name = None
                                if attrib and "name" in attrib: name = attrib["name"]
                                value = None
                        if typ:
                            tags.append([typ, name, value, attrib])
        return tags        
    ## extract xml attributes from tag
    # @param tag - tag to be analysed
    def get_xml_attribs(self, tag):
        #print "AfpImport.get_xml_attribs:", tag
        split = tag.split()
        typ = split.pop(0)
        attribs = None
        if len(split) > 0:
            attribs = {}
            for att in split:
                sp = att.split("=")
                if len(sp) > 1:
                    attribs[sp[0]] = Afp_fromString(sp[1][1:-1])
        return typ, attribs
    ## default execution routine to interprete Afp-xml files
    # @param tags - list of tags read from file to be used for object generation
    def interprete_xml_tags(self, tags):
        datalist = []        
        is_doc = False
        data = None
        sel = None
        sel_index = None
        for tag in tags:
            #print "AfpImport.read_from_xml_file tag:", tag
            typ = tag[0]
            if is_doc:
                if data:
                    if sel:
                        if typ == "AfpTableRow":
                            atts = tag[3]
                            if atts and "count" in atts:
                                sel_index = atts["count"]
                            else: 
                                sel_index = sel.get_data_length()
                        elif typ == "AfpValue":
                            if tag[1] and tag[2] and not sel_index is None:
                                sel.set_value(tag[1], Afp_fromString(tag[2]), sel_index)
                                #print "AfpImport.read_from_xml_file set_value:", tag[1], tag[2], sel_index, type(tag[1]), type(tag[2])
                        elif typ == "/AfpTableRow":
                            sel_index = None
                        elif typ == "/AfpSelection":
                            sel = None
                    elif  typ == "AfpSelection":
                        sel = data.get_selection(tag[1])
                        #print "AfpImport.read_from_xml_file get_selection:", tag[1],"\n", sel.data
                    elif  typ == "/AfpSelectionList":
                        datalist.append(data)
                        data = None
                elif typ == "AfpSelectionList":
                    atts = tag[3]
                    if atts and "type" in atts:
                        data = self.create_object(atts["type"])
                elif typ == "/AfpDocument":
                    is_doc = False
            else:
                if typ == "AfpDocument":
                    is_doc = True
        return datalist
    ## read Afp-xml file
    def read_from_xml_file(self):
        tags = self.extract_xml_tags()
        #print ("AfpImport.read_from_xml_file:", tags)
        if self.modul and self.tag_interpreter:
            befehl = "datalist = self.modul." + self.tag_interpreter + "(self.globals, tags)"
            if self.parameter: befehl = befehl[:-1] + ", " + self.parameter + ")"
            if self.debug: print("AfpImport.read_from_xml_file Befehl:", befehl)
            #print("AfpImport.read_from_xml_file Befehl:", befehl)
            #local = locales()
            local = locals()
            exec(befehl, {}, local)
            datalist = local["datalist"]
            #print("AfpImport.read_from_xml_file datalist:", datalist)
        else:
            if self.debug: print("AfpImport.read_from_xml_file type: AfpDocument")
            datalist = self.interprete_xml_tags(tags)
        if self.debug: print("AfpImport.read_from_xml_file datalist:", datalist[0])
        #print("AfpImport.read_from_xml_file datalist:", datalist[0])
        return datalist
##  class to export Afp-database entries to other formats 
class AfpExport(object):
    ## initialize AfpExport class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param data - TableSelection holding the data to be written    
    # @param filename - name of file data is written to, \n
    #  at the moment the following formats are supported \n
    #  - .asc - ASCII file, static length \n
    #  - .csv - ASCII file, comma separated values \n
    #  - .xml - XML file according to namespace http://www.afptech.de/XML/AfpDocument \n
    #  - .dbf - DBF database file \n
    # @param debug - flag for debug information
    def  __init__(self, globals, data, filename, debug = False):
        self.globals = globals
        self.mysql = globals.get_mysql()
        self.data = data
        self.filename = filename
        self.fieldlist = None
        self.xml_embedded_data = None
        self.information = None
        self.export_available = False
        self.module = None
        self.debug = debug
        split = filename.split(".")
        self.type = split[-1].lower()
        if self.type == "asc" or self.type == "csv" or self.type == "xml":
            self.export_available = True
        elif self.type == "dbf":
            if AfpPy_checkModule('dbfpy'):
                self.module = Afp_importPyModul("AfpBase.AfpDatabase.AfpDBF", globals)
            if self.module:
                self.export_available = True
        if self.debug: print("AfpExport Konstruktor",filename)
        if not self.export_available:
            print("WARNING Export-modul for file of type \"." +self.type + "\" not available!")
    ## destructor
    def __del__(self):   
        if self.debug: print("AfpExport Destruktor") 
    ## add embedded data to
    # @param propname - name of self.data property holding the data to be embbeded into output
    def add_embedded_data(self, propname):
        self.xml_embedded_propname = propname
        befehl = "xml_embedded_data = self.data." + propname
        #local = locales()
        local = locals()
        exec(befehl, {}, local)
        self.xml_embedded_data = local["xml_embedded_data"]
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
    ## fill all fields availabe in data into fieldlist
    # @param data - datat where fieldnames are read from
    def complete_fieldlist(self, data):
        fieldlist = []
        if type(data) == "AfpSQLTableSelection":
            fieldlist = data.get_feldnamen()
        else:
            for sel in data.selections:
                select = data.selections[sel]
                for feld in select.get_feldnamen():
                    fieldlist.append(feld + "." + sel)
        return fieldlist
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
    ## writes data to fixed lenght ascii file or to comma separated  file
    # @param fieldlist - array with names of values read from data 
    # @param info - info for ascii output, as follows
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
    ## writes field data to xml file
    # @param fields - array with names of values 
    # @param values - array with values 
    # @param preind - global prefix of spaces    
    # @param indent - prefix of spaces for inner loops
    # @param fout - filehandler for output file
    # @param count - number of row
    def write_xml_fields(self, fields, values, preind, indent, fout, count = -1): 
        if count >= 0:
            fout.write(preind + "<AfpTableRow count=\""+ Afp_toString(count) + "\"> \n")
        else:
            fout.write(preind + "<AfpTableRow> \n")
        if len(values) < len(fields): 
            lgh = len(values)
        else:
            lgh = len(fields)
        for i in range(lgh):
            #fout.write(preind + indent + "<AfpValue name=\"" + fields[i] + "\">" + Afp_toString(values[i]).encode("UTF-8") + "</AfpValue> \n")
            fout.write(preind + indent + "<AfpValue name=\"" + fields[i] + "\">" + Afp_toString(values[i]) + "</AfpValue> \n")
        fout.write(preind + "</AfpTableRow> \n")
    ## writes field data to xml file
    # @param selection - given table selection
    # @param selname - name of table selection
    # @param preind - global prefix of spaces    
    # @param indent - prefix of spaces for inner loops    
    # @param fout - filehandler for output file
    # @param fieldlist - array with names of values
    def write_xml_selection(self, selection, selname, preind, indent, fout): 
        fout.write(preind + "<AfpSelection name=\"" + selname +"\"> \n") 
        daten = selection.get_values(None)
        count = 0
        for values in daten:
            self.write_xml_fields(selection.get_feldnamen(), values, preind + indent, indent, fout, count)
            count += 1
        fout.write(preind + "</AfpSelection> \n")
    ## writes field data to xml file
    # @param data - data where values are read from
    # @param preind - global prefix of spaces
    # @param indent - prefix of spaces for inner loops
    # @param fout - filehandler for output file
    # @param complete -flag if closing 'AfpSelectionList' tag should be written also
    def write_xml_selection_list(self, data, preind, indent, fout, complete=True):
            fout.write(preind + "<AfpSelectionList name=\"" + self.data.get_listname() + "\" type=\"" + str(type(self.data))[8:-2] + "\"> \n")
            for sel in data.selections:
                self.write_xml_selection(data.selections[sel], sel, preind + indent, indent, fout)
            if complete: fout.write(preind + "</AfpSelectionList> \n")
    ## writes data to xml  file
    # @param fieldlist - array with names of values read from data 
    # @param ilgh - info for xml output, length of indent
    def write_to_xml_file(self, fieldlist, ilgh=4):
        indent = ilgh*" "
        if self.type == "xml":
            fout = open(self.filename, 'w')
            fout.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>" + "\n")
            fout.write("<AfpDocument xmlns=\"http://www.afptech.de/XML/AfpDocument\">" + "\n")
            self.write_xml_selection_list(self.data, indent, indent, fout, not self.xml_embedded_data)
            if self.xml_embedded_data:
                fout.write(2*indent + "<AfpEmbeddedList property=\"" + self.xml_embedded_propname + "\"> \n")
                for data in self.xml_embedded_data:
                    self.write_xml_selection_list(data, 3*indent, indent, fout)
                fout.write(2*indent + "</AfpEmbeddedList> \n")
                fout.write(indent + "</AfpSelectionList> \n")
            fout.write("</AfpDocument> \n")
            fout.close()
    ## writes data to different fileformats
    # @param fieldlist - is used as follows: \n
    # - .asc,csv,xml - array with names of values read from data \n
    # - .dbf - dictionary how data is mapped into output file (output[entry] = value(parameter[entry])), \n 
    # - == None - complete availabel data will be exported
    # @param info - if given, is used as follows:
    # - .asc - length of each fields (default: 50)
    # - .csv - field delimiter, text bracket, separated by spaces (default: delimiter - ",", no brackets)
    # - .xml - number of spaces used for Indent
    # - .dbf - template file which is used to create output, 
    #            if type is list, description for generation of dbf-file fields: [name, typ, parameter]
    def write_to_file(self, fieldlist, info):
        if self.debug: print("AfpExport.write_to_file:",fieldlist, info)
        if self.type == "asc" or self.type == "csv" :
            self.write_to_ascii_file(fieldlist, info)
        elif self.type == "xml":
            self.write_to_xml_file(fieldlist, info)
        elif self.type == "dbf":
            if self.module:
                self.module.Afp_writeToDBFFile(self.data, self.filename, info, fieldlist, self.debug)
        else:
            print("WARNING: AfpExport, output to a file of type \"." + self.type + "\" not yet implemented!")

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
        self.serverport = None
        self.starttls = None
        self.security = None
        self.user = None
        self.word = None
        self.dry_run = None
        # look for data in globals
        if self.globals.get_value("mail-dry-run"):
            self.dry_run = True
        server = self.globals.get_value("smtp-host")
        if server:
            split = server.split(":")
            self.server = split[0]
            if len(split) > 1:
                self.serverport = int(split[1])
            self.security =  self.globals.get_value("smtp-security")
            if self.security is None and self.globals.get_value("smtp-starttls"):
                self.security = "STARTTLS" 
            self.user =  self.globals.get_value("smtp-user")
            self.word =  self.globals.get_value("smtp-word")
            self.sender = self.globals.get_value("mail-sender")
            if self.sender is None and self.user and Afp_isMailAddress(self.user):
                self.sender = self.user
        if self.debug: print("AfpMailSender Konstruktor")
    ## return if automatic sending may be possible
    def is_possible(self):
        return self.server and self.sender
    ## return if mail is ready to be send
    # @param norp - flag if recipient check could be skipped
    def is_ready(self, norp=False):
        ready = True
        if not self.is_possible():
            ready = False
        elif not (norp or self.recipients):
            ready = False
        elif self.subject is None:
            ready = False
        elif self.message is None and self.htmltext is None:
            ready = False
        return ready
    ## clone data for new email
    def clone(self):
        mail = AfpMailSender(self.globals, self.debug)
        mail.subject = self.subject
        mail.message = self.message
        mail.htmltext = self.htmltext
        if self.recipients:
            for recip in self.recipients:
                mail.add_recipient(recip)
        if self.attachments:
            for attach in self.attachments:
                mail.attachments.append(attach)
        return mail
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
            if not (filename[-4:] == ".pdf" or filename[-4:] == ".PDF"):
                filename = self.convert_to_pdf(filename)
            self.attachments.append(filename)
            return True
        else:
            print ("AfpMailSender.add_attachment File not found:", filename)
            return False
    ## add attachment file to message (may be invoked several times)
    # @param recipient - mail address where mail is to be send to
    # @param front - flag, if the mail addressshoud be prepended to the list
    def add_recipient(self, recipient, front = False):
        if Afp_isMailAddress(recipient):
            if front:
                self.recipients =[recipient] + self.recipients
            else:
                self.recipients.append(recipient)
    ## set connection information of smtp-server where mail has to be delivered
    # @param host - string defining host[:port] to be connected
    # @param user - if given, username to be used for login
    # @param word - if given, password to be used for login (login will only be invoked if user and word are given)
    # @param security - flag for smtp security, possible values:None, STARTTLS, SSL, if not given explicit in 'smtpport' DEFAULT: None
    def set_server(self, host, user = None, word = None, security = None):
        split = host.split(":")
        self.server = split[0]
        if len(split) > 1:
            self.serverport = int(split[1])
        self.user = user
        self.word = word
        self.security = security
    ## convert attachmentfile to pdf, if possible
    # @param filename - name of file to be converted
    def convert_to_pdf(self, filename):
        converter =  self.globals.get_value("pdf-converter")
        convtime =  self.globals.get_value("pdf-converter-time")
        if converter:
            pdfname =self.globals.get_value("tempdir") + Afp_extractBase(filename).split(".")[0] + ".pdf"
            Afp_startProgramFile(converter, self.debug, filename)
            if convtime: Afp_wait(2*convtime)
            if self.debug: print ("AfpMailSender.convert_to_pdf:", convtime, pdfname, Afp_existsFile(pdfname))
            if Afp_existsFile(pdfname):
                filename = pdfname
        return filename
    ## deliver mail to smtp server
    def send_mail(self):     
        if self.dry_run: 
            print ("AfpMailSender: --- DRY RUN!! ---")
            self.view() 
            return None
        else:
            if self.debug: self.view()
            #return Afp_sendOverSMTP(self.sender, self.recipients, self.subject, self.message, self.htmltext,  self.attachments, self.server, self.serverport, self.debug, self.starttls, self.security, self.user, self.word, self.globals.get_value("maildir"))
            return Afp_sendOverSMTP(self.sender, self.recipients, self.subject, self.message, self.htmltext,  self.attachments, self.server, self.user, self.word, self.debug, self.security, self.serverport, self.globals.get_value("maildir"))
    ## view mailer details (for debug or dry run)
    def view(self):
        print("AfpMailSender server:", self.server)
        print("AfpMailSender serverport:", self.serverport)
        #print("AfpMailSender starttls:", self.starttls)
        print("AfpMailSender security:", self.security)
        print("AfpMailSender user:", self.user)
        print("AfpMailSender word:", self.word)
        print("AfpMailSender subject:", self.subject)
        print("AfpMailSender sender:", self.sender)
        print("AfpMailSender recipients:", self.recipients)
        print("AfpMailSender message:", self.message)
        print("AfpMailSender htmltext:", self.htmltext)
        print("AfpMailSender attachments:", self.attachments, "\n")

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
    required["ExternNr"] = """CREATE TABLE `EXTERNNR` (
  `Typ` char(20) COLLATE latin1_german2_ci NOT NULL,
  `Pre` char(5) COLLATE latin1_german2_ci NOT NULL,
  `Nummer` mediumint(8) unsigned zerofill NOT NULL,
  `TypPre` tinytext COLLATE latin1_german2_ci NOT NULL,
  KEY `TypPre` (`Typ`,`Pre`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    required["RECHNG"] = """CREATE TABLE `RECHNG` (
  `RechNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `AttNr` smallint(5) unsigned zerofill DEFAULT NULL,
  `Datum` date NOT NULL,
  `Bem` text CHARACTER SET latin1,
  `Pos` smallint(6) DEFAULT NULL,
  `Ust` char(1) CHARACTER SET latin1 DEFAULT NULL,
  `Netto` float(7,2) DEFAULT NULL,
  `Betrag` float(7,2) NOT NULL,
  `Skonto` float(7,2) DEFAULT NULL,
  `ZahlBetrag` float(7,2) DEFAULT NULL,
  `ZahlZiel` date DEFAULT NULL,
  `Zahlung` float(7,2) DEFAULT NULL,
  `ZahlDat` date DEFAULT NULL,
  `Kontierung` mediumint(8) unsigned zerofill NOT NULL,
  `Debitor` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Zustand` char(7) CHARACTER SET latin1 NOT NULL,
  `Gewinn` float(7,2) DEFAULT NULL,
  `Typ` char(7) CHARACTER SET latin1 DEFAULT NULL,
  `TypNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Name` tinytext CHARACTER SET latin1,
  `Ausgabe` char(10) CHARACTER SET latin1 DEFAULT NULL,
  `BerichtNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  PRIMARY KEY (`RechNr`),
  KEY `RechNr` (`RechNr`),
  KEY `KundenNr` (`KundenNr`),
  KEY `Datum` (`Datum`),
  KEY `Zustand` (`Zustand`),
  KEY `Name` (`Name`(50)),
  KEY `TypNr` (`TypNr`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    required["VERBIND"] = """CREATE TABLE `VERBIND` (
  `RechNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `ExternNr` varchar(45) COLLATE latin1_german2_ci DEFAULT NULL,
  `AttNr` smallint(5) unsigned zerofill DEFAULT NULL,
  `Datum` date NOT NULL,
  `Bem` text CHARACTER SET latin1,
  `Betrag` float(7,2) NOT NULL,
  `Skonto` float(7,2) DEFAULT NULL,
  `ZahlBetrag` float(7,2) DEFAULT NULL,
  `ZahlZiel` date DEFAULT NULL,
  `Zahlung` float(7,2) DEFAULT NULL,
  `ZahlDat` date DEFAULT NULL,
  `Kontierung` mediumint(8) unsigned zerofill NOT NULL,
  `Kreditor` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Zustand` char(7) CHARACTER SET latin1 NOT NULL,
  `Typ` char(7) CHARACTER SET latin1 DEFAULT NULL,
  `TypNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  PRIMARY KEY (`RechNr`),
  KEY `RechNr` (`RechNr`),
  KEY `KundenNr` (`KundenNr`),
  KEY `Datum` (`Datum`),
  KEY `Zustand` (`Zustand`),
  KEY `TypNr` (`TypNr`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # return data
    return required
