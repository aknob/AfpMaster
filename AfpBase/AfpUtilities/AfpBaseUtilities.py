#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpUtilities.AfpBaseUtilities
# AfpBaseUtilities module provides general solely python dependend utilitiy routines
# it does not hold any classes
#
#   History: \n
#        24 Okt. 2024 - adaption to python 3.12 - Andreas.Knoblauch@afptech.de \n
#        29 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        20 Jan. 2015 - add array cache - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
#    Copyright© 1989 - 2025  afptech.de (Andreas Knoblauch)
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
import os.path
import os
import time
import platform
import getpass
import datetime
import base64
import tzlocal
#import logging
import shutil
import glob
import importlib
from importlib.machinery import SourceFileLoader
# for email sending
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.utils import formatdate
#from email.encoders import Encoders

##  get system infos
# @param name - name of value to be extracted
def Afp_getGlobalVar(name):
    if name == "python-version": return sys.version
    if name == "python-path":
        if 'PYTHONPATH' in os.environ:
            return os.environ['PYTHONPATH'].split(os.pathsep)[0]  
        else:
            return None
    if name == "op-system": return platform.system()
    if name == "net-name": return platform.node()
    if name == "user": return getpass.getuser()
    if name == "path-delimiter": 
        deli = os.sep
        if deli == '\\': deli = "\\"
        return deli
    return None
## type check 'integer'
# @param wert - value to be checked
def Afp_isInteger(wert):
    typ = type(wert)
    if typ == int: return True
    #if typ == long: return True # py2
    return False
## type check 'numeric'
# @param wert - value to be checked
def Afp_isNumeric(wert):
    typ = type(wert)
    if typ == int: return True
    #if typ == long: return True # py2
    if typ == float: return True
    if typ == datetime.date: return True
    return False
## type check 'date'
# @param wert - value to be checked
def Afp_isDate(wert):
    return type(wert) == datetime.date
## type check 'time'
# @param wert - value to be checked
def Afp_isTime(wert):
    if type(wert) == datetime.datetime: return True
    if type(wert) == datetime.time: return True
    if type(wert) == datetime.timedelta: return True
    return False
   
## numerical check +- eps
# @param value - value to be checked
# @param eps   -  value has to be numerical and abs(value) > eps 
def Afp_isEps(value, eps = 0.01):
    if Afp_isDate(value): return False
    if Afp_isNumeric(value):
        return (value >= eps or value <= -eps)
    else:
        return False
        
## check rekursiv if iterables hold values
# @param iter - iterable to be checked
def Afp_holdsValue(iter):
    #print "Afp_holdsValue:", iter
    res = False
    if iter:
        typ = type(iter)
        if typ == list or typ == tuple:
            for it in iter:
                res = Afp_holdsValue(it)
                if res: break
        else:
            res = True
    #print "Afp_holdsValue result:", res
    return res
      
## extract values from array (list)
# @param indices - indices of values to be extracted from array, None all entries are extracted
# @param array- list of values
def Afp_extractPureValues(indices, array):
    #print "Afp_extractPureValues:",indices, array
    if indices is None:
        werte = []
        for entry in array:
            werte.append(entry)
    else:
        werte = []
        if array:
            for ind in indices:
                if ind is None:
                    werte.append(None)
                else:
                    werte.append(array[ind])
    return werte
 
## distributes given value in given parts, \n 
# returns the common portion and the special portion to get the full cent sum
# @param value - value to be distributed
# @param count - number of protions to be generated
def Afp_distributeCents(value, count):
    if count < 2: return value, value
    count = int(count)
    intval = int(value * 100)
    part = intval/count
    rest = intval - part*count
    fpart = float(part)/100
    frest = float(rest)/100
    return fpart, fpart+frest
   
# date and time routines
## wait a number of seconds
# @param sec - number of seconds to sleep, may be floatingpoint
def Afp_wait(sec):
    time.sleep(sec)
## return minimum date
def Afp_minDate():
    return datetime.date.min
## return today
def Afp_getToday():
    return datetime.date.today()
## return a datetime object holding the actuel date and time
# @param settz - flag if local timezone should be added
def Afp_getNow(settz = False):
    if settz:
        return datetime.datetime.now(tzlocal.get_localzone())
    else:
        return datetime.datetime.now()
## add number of days to given date
# @param date - initial date
# @param ndays - number of days to be added
# @param sign - sign to be used, default: add days, "-": subtract days
def Afp_addDaysToDate(date, ndays, sign = None):
    minus = False
    if sign:
        if  "-" in sign: minus = True
    if minus:
        newdate = date -  datetime.timedelta(days=ndays)
    else:
        newdate = date +  datetime.timedelta(days=ndays)
    return newdate
## add number of month to given date
# @param date - initial date
# @param nmonth - number of month to be added
# @param sign - sign to be used, default: add month, "-": subtract month
# @param day - day of month to be used instead of proper addition
def Afp_addMonthToDate(date, nmonth, sign = None, day=None):
    plus = 1
    if sign:
        if  "-" in sign: plus = -1
    month = date.month + plus*nmonth
    addyear = 0
    while month > 12 or month < 1:
        addyear += 1
        month -= plus*12
    if day is None:
        shortmonth = [4, 6, 9, 11]
        oldday = date.day
        if month == 2 and oldday > 28: day = 28
        elif month in shortmonth and oldday > 30: day = 30
    if day:
        date = date.replace(day=day)
    date = date.replace(month=month)
    if addyear:
        year = date.year + plus*addyear
        date = date.replace(year=year)
    return date
## return the last date of interval where given date belongs to
# @param date - given date
# @param interval - interval length in month
# @param previous - if given, flag if end of previous interval should be determined
def Afp_lastIntervalDate(date, interval, previous = False):
        month = date.month
        year = date.year
        while not month%interval == 0:
            if previous: month -= 1
            else: month += 1
        month += 1
        while month > 12: 
            month -= 12
            year += 1
        outdate = Afp_addDaysToDate(Afp_genDate(year, month, 1), 1, "-")
        return outdate
      
## return difference of two dates
# @param start - startdate
# @param ende - enddate
def Afp_diffDays(start, ende):
    diff = ende - start
    if type(diff) == datetime.timedelta: 
        return diff.days
    else:
        return diff
## generate datettime from given values
# @param year - year of date
# @param month - month of date
# @param day - day of date
def Afp_genDate(year, month, day):
    return datetime.date(year, month, day)
## generate datettime from given values
# @param year - year of date
# @param month - month of date
# @param day - day of date
# @param hour - hour of time 
# @param minute - minute of time 
# @param second - second of time 
# @param settz - flag if local timezone should be added
def Afp_genDatetime(year, month, day, hour = 0, minute = 0, second  = 0, settz = False):
    if settz:
        return datetime.datetime(year, month, day, hour, minute, second, tzinfo=tzlocal.get_localzone())
    else:
        return datetime.datetime(year, month, day, hour, minute, second)
## assign local timzone to datetime object
# @param dtime - input datetime object
def Afp_toTzDatetime(dtime):
    return datetime.datetime(dtime.year, dtime.month, dtime.day, dtime.hour, dtime.minute, dtime.second, tzinfo=tzlocal.get_localzone())
## convert timedelta to time
# @param timedelta - timedelta to be converted
# @param high - flag how time should be initialised, if no valid time is given:
# - None - normal initialisation 12:34.56
# - False - low initialisation 01:23.45
# - True - high initialisation 23:45.42
def Afp_toTime(timedelta, high = None):
    if type(timedelta) == datetime.time: return timedelta
    elif type(timedelta) != datetime.timedelta: 
        if high is None: return datetime.time(12, 34, 56)
        elif high: return datetime.time(23, 45, 42)
        else: return datetime.time(1, 23, 45)
    hours = int(timedelta.total_seconds()/3600)
    minutes = int((timedelta.total_seconds() - 3600*hours)/60)
    return datetime.time(hours, minutes)
## convert time to timedelta
# @param time - time to be converted
# @param complement - flag if difference to 24:00 should be used instead of 0:00
def Afp_toTimedelta(time, complement = False):
    if time is None: return datetime.timedelta()
    if  type(time) == datetime.timedelta: return time
    if not Afp_isTime(time): return datetime.timedelta()
    hour = time.hour
    minute = time.minute
    second = time.second
    micro = time.microsecond
    if complement:
        hour = 24 - hour
        minute = 60 -  minute
        if minute < 60: hour -= 1
        else: minute = 0
        second = 60 - second
        if second < 60: 
            minute -= 1
            if minute < 0:
                hour -= 1
                minute = 60 - minute
        else: second = 0
        micro = 1000000 - micro
        if micro < 1000000:
            second -= 1
            if second < 0:
                minute -= 1
                second = 60 - second
                if minute < 0:
                    hour -= 1
                    minute = 60 - minute
        else:
            micro = 0
    return datetime.timedelta(hours=hour, minutes=minute, seconds=second, microseconds=micro)
## convert time to float hours
# @param time - time to be converted
# @param end - flag if difference to 24:00 should be used instead of 0:00
def Afp_TimeToFloat(time, end = False):
    value = 0.0
    mins = 0.0
    if type(time) == datetime.timedelta: time = Afp_toTime(time)
    if type(time) == datetime.time: 
        value = float(time.hour)
        mins = time.minute/60.0
    if end: 
        value = 24.0 -  value
        value -= mins
    else: 
        value += mins
    return value
## convert float hours to time
# @param fhours - hours to be converted
def Afp_floatHoursToTime(fhours):
    hours = int(fhours)
    mins = int((fhours - hours)*60)
    time = datetime.timedelta(hours=hours, minutes=mins)
    return time
## add  two time values, return timedelta 
# @param time1 - first time value
# @param time2 - second time value
def Afp_plusTime(time1, time2):
    time = datetime.timedelta()
    if time1: time += time1
    if time2: time += time2
    return time
## generate full days, half days and remaining hours, \n
# full days (a 24 hours) will be counted, if 'day' or 'hday' is given the remaining hours are compared to those values and another full or half day may be added.
# @param timedelta - timevalue which should be analysed
# @param day - number of hours to represent a full (working) day
# @param hday - number of hours to represent half a (working) day
def Afp_daysFromTime(timedelta, day = None, hday = None):
    days = float(timedelta.days)
    secs = timedelta.total_seconds()
    #print "Afp_daysFromTime input", timedelta, days, secs
    std = 3600
    tag = 24*std
    secs_h = secs - days*tag
    hours = float(secs_h/std)
    #print "Afp_daysFromTime secs", secs_h, hours, tag, std
    #print day, type(day), hday, type(hday)
    if day and hours >= day: 
        hours = 0.0
        days += 1
    if hday and hours >= hday: 
        hours = 0.0
        days += 0.5
    return days, hours    
## get the right extension triggerd by date and indicator
# @param date - date which initiates the extension
# @param indicator - given period interval in month
#    == 0.1  weekly period, == 0.01 dayliy period
def Afp_genPeriodExtension(date, indicator):
    res = 0
    if indicator > 0.5:
        res = (int)((date.month-1)/indicator) 
    elif indicator > 0.05:
        dum, res, dum = date.isocalendar()
    else:
        res = date.timetuple().tm_yday
    return res
## camouflage given string, to be not readable at first sight
# @param word - string to be camouflaged (covered)
# @param uncover - flag if string should be uncovered insted of covered
def Afp_coverString(word, uncover=False):
    if type(word) == str:
        if uncover:
            word = base64.b64decode(word).decode("UTF-8")
        else:
            word = base64.b64encode(word.encode("UTF-8"))
    return word
    
## check if standard python modul has been installed
# @param modul - name of standard modul to be checked
def AfpPy_checkModule(modul):
    try:
        #imp.find_module(modul)
        importlib.util.find_spec(modul)
        return True
    except ImportError:
        return False
## dynamic import of a python module from modulname or path, 
# a handle to the modul will be returned
# @param modul - name of modul to be imported
# @param path - path to modul to be imported
def AfpPy_Import(modul, path=None):
    mod = None
    filename = None
    #print("AfpPy_Import wanted:", modul, path)
    try:
        return sys.modules[modul]
    except KeyError:
        pass
    try:
        if path: 
            filename = path + modul
            mod = importlib.import_module(filename)
        else:
            mod = importlib.import_module(modul)
    except:
        if filename:   
            if not (filename[-3:] == ".py" or filename[-3:] == ".PY"):
                filename += ".py"
            try:
                #loader = importlib.machinery.SourceFileLoader(modul, filename)
                loader = SourceFileLoader(modul, filename)
                spec = importlib.util.spec_from_file_location(modul, filename, loader=loader)
                mod = importlib.util.module_from_spec(spec)
                # The module is always executed and not cached in sys.modules.
                # Uncomment the following line to cache the module.
                # sys.modules[mod.__name__] = mod
                loader.exec_module(mod)
            except:
                print("ERROR: dynamic modul " + modul + " not found!")
                if Afp_existsFile(filename):
                    print("WARNING: File \"" + filename + "\" exists, propably a syntax problem.")
        else:
            print("ERROR: dynamic modul " + modul + " not found!")
    return mod

## import data of extern file and return it
# @param fname - name of file
def Afp_importFileData(fname):
    if Afp_existsFile(fname):
         fin = open(fname , 'r') 
         data = fin.read()
         fin.close()
         delete = "\x04\x1B" # remove 'EOT' and 'ESC' from filedata
         data = data.translate(None, delete)
         return data
    else:
        return fname
## import lines of extern file and return it
# @param fname - name of file
def Afp_importFileLines(fname):
    lines = []
    if Afp_existsFile(fname):
         fin = open(fname , 'r') 
         for line in fin:
             lines.append(line)
         fin.close()
    return lines

## generate and initialize 2 dimensional nxm array 
# @param n - lentgh of first dimension
# @param m - lentgh of second dimension
# @param init - value for initialisation
def Afp_initMatrix(n, m, init = None):
    matrix = []
    for i in range(m):
        row = []
        for j in range(n):
            row.append(init)
        matrix.append(row)
    return matrix
## check 2 dimensional array if it represents a nxm matrix
# @param matrix - matrix to be checked
# @param n - lentgh of first dimension
# @param m - lentgh of second dimension
def Afp_checkMatrix(matrix, n, m):
    if len(matrix) == m:
        check = True
    else:
        check = False
    if check:
        for row in matrix:
            check = check and len(row) == n
    return check
## extract a columns of a 2 dimensional array, 
# if only one index is given as integer, only a 1-dim array is returned, otherwise 2-dimensions are returned
# @param inds - index of column or list of indices, if None is a list entry, this column will be filled with 'None's
# @param matrix - matrix where columns are extraced from
def Afp_extractColumns(inds, matrix):
    columns = []
    dim1 = Afp_isInteger(inds)
    if dim1:
        indices = [inds]
    else:
        indices = inds
    for row in matrix:
        newrow = []
        for ind in indices:
            if ind is None or ind >= len(row) or ind < 0:
                newrow.append(None)
            else:
                newrow.append(row[ind])
        if dim1:
            columns.append(newrow[0])
        else:
            columns.append(newrow)
    return columns
## get maximum of column
# @param matrix - matrix where maximum of column should be found
# @param col - index of column where maximum shoud be found
def Afp_getMaxOfColumn(matrix, col=3):
    Max = None
    for row in matrix:
        if len(row) > col and row[col]:
            if Max is None or row[col] > Max:
                Max = row[col]
    return Max
## deep copy of an array (list), diving recursively into arrays
# @param array - array to be copied, may be combined 'list' and 'dict'
def Afp_copyArray(array):
    dict = False
    if type(array) == dict: 
        dict = True
        new_array = {}
    else:
        new_array = []
    for ent in array:
        if dict: entry = array[ent]
        else: entry = ent
        if type(entry) == list or type(entry) == dict: 
            new_entry = Afp_copyArray(entry)
        else: 
            new_entry = entry
        if dict: new_array[ent] = new_entry
        else: new_array.append(new_entry)
    return new_array
## get an array (list) of dictionary witth two entries per line
# @param dict - dictionary to be converted
def Afp_getArrayfromDict(dict):
    new_array = []
    for entry in dict:
        new_array.append([entry, dict[entry]])
    return new_array
## swap keys and values of a dictionary (does only work for 1:1 relations)
# @param dict - dictionary to be swapped
def Afp_swapDict(dict):
    new_dict = {}
    for entry in dict:
        new_dict[dict[entry]] = entry
    return new_dict
## add values to dictionary, if already present add new value to old
# @param dict - original dictionary
# @param adddict - dictionary holding values to be added
def Afp_addDict(dict, adddict):
    new_dict = {}
    for entry in adddict:
        if entry in dict:
            dict[entry] += adddict[entry]
        else:
            dict[entry] = adddict[entry]
    return dict
## compare two arrays and return list of indices where values of first array occur in second \n
# i = index in first array, indices[i] = index in second array or None, if value doesen't occur in second array
# @param master - array from which entries should be found in second
# @param slave - array where entries should be found
def Afp_findIndices(master, slave):
    indices = []
    for entry in master:
        if entry in slave:
            indices.append(slave.index(entry))
        else:
            indices.append(None)
    return indices
## sort two lists simultan
# @param master - list which triggers the sorting
# @param slave - list which is sorted simultan to master list
# @param sorter_out - if given, flag to return sorter insted of master
def Afp_sortSimultan(master, slave, sorter_out=False):
    #if len(master) == len(slave):
        #master, slave = (list(x) for x in zip(*sorted(zip(master, slave))))  
    #print ("Afp_sortSimultan:", master, slave)
    result = None
    sorter = None
    lgh = len(master)
    if lgh == len(slave):
        sorter = [] # sorter needed for to not '<' comparable objects in slave list
        cnt = 0
        for entry in master:
            sorter.append(cnt)
            cnt +=1
        master, sorter = (list(x) for x in zip(*sorted(zip(master, sorter)))) 
        result = [None]*lgh
        for i in range(lgh):
            result[i] = slave[sorter[i]]
    if sorter_out: return sorter, result
    return master, result
# path and file handling 
## add filername to path
# @param path - path
# @param file - name of file
def Afp_addPath(path, file):
    return os.path.join(path, file)
## extract path from complete filname
# @param path -complete path of a file
def Afp_extractBase(path):
    return os.path.basename(path)
## extract path from complete filname
# @param file - name of file
def Afp_extractPath(file):
    return os.path.dirname(file)
## return home directory
def Afp_genHomeDir():
    if 'HOME' in os.environ:
        path = os.environ['HOME']
    else:
        path =  os.environ['HOMEDRIVE'] + os.environ['HOMEPATH']
    return path
## copy a file
# @param fromFile - file to be copied
# @param toFile - destination
def Afp_copyFile(fromFile, toFile):
    #print ("Afp_copyFile:", fromFile, toFile)
    shutil.copyfile(fromFile, toFile) 
## delete a file
# @param filename - file to be deleted
def Afp_deleteFile(filename):
    if Afp_existsFile(filename):
        os.remove(filename) 
## generate an empty file
# @param filename - name of file
def Afp_genEmptyFile(filename):
    fout = open(filename, 'w')
    fout.write(" ")
    fout.close()
## generate an empty file
# @param filename - name of file
# @param max - if given, maximum numer of lines read
def Afp_readLinesFromFile(filename, max = None):
    fin = open(filename, 'r')
    cnt = 0
    lines = []
    for line in fin:
        lines.append(line)
        cnt += 1
        if max and cnt >= max: break
    fin.close()
    return lines
## read filename from path
# @param path - path to directory to be searched
# @param filter - filter for filenames (e.g. "*.py")
def Afp_readFileNames(path, filter = None):
    if filter is None: filter = "*"
    liste = []
    for fname in glob.glob(path + filter):
        liste.append(fname)
    return liste
## check if file exists
# @param filename - name of file
def Afp_existsFile(filename):
    if filename:
        return os.path.exists(filename)
    return None
## return timestamp from file
# @param filename - name of file
def Afp_getFileTimestamp(filename):
    return datetime.datetime.fromtimestamp(os.path.getmtime(filename))
 
## start different program form here \n
# may be this routine should be replaced by subprocess calls 
# @param programname - if given name of program to be started
# @param debug - flag for debug information
# @param filename - file to be started with program or directly via OS connections
# @param parameter - if given parameter for program start
def Afp_startProgramFile(programname, debug, filename, parameter = None):
    befehl = ""
    if programname: befehl += programname + " " 
    if filename: befehl += filename  
    if parameter:
        befehl += " " + parameter
    if debug: print("Afp_startProgramFile:", befehl)
    #print ("Afp_startProgramFile:", befehl, "Encoding:", sys.getfilesystemencoding())
    os.system(befehl)
    #subprocess.call("soffice -pt HP_Color_LaserJet *", shell=True)
    #subprocess.call("soffice --invisible --convert-to pdf filename)
  
# start of implementation of a logger
# - not used (yet) -
# @param level - debug level
# @param to_file - if given logs are send to this file
#def Afp_configLogger(level, to_file):
    # level specify --log=DEBUG or --log=debug
#    numeric_level = getattr(logging, level.upper(), None)
#    if not isinstance(numeric_level, int):
#         print  "WARNING: Invalid log level:", level
#         return
#    logging.basicConfig(level=numeric_level)
#    if to_file:
#        logging.basicConfig(filename=to_file)
# get a logger
# @param name - name of the newly generated logger
#def Afp_getLogger(name):
#    return logging.getLogger(name)

## send an email over a SMTP-server \n
# sender, recipient, smtphost and message or html_message have to be given.
# @param sender - string giving sender mailaddress
# @param recipients - list of target mailadresses
# @param subject - string describing subject of mail
# @param message - plain text message body
# @param html_message - html text message body
# @param attachments - list of filepathes of files to be attached
# @param smtphost - string defining host[:port] to be connected
# @param user - if given, username to be used for login
# @param word - if given, password to be used for login (login will only be invoked if user and word are given)
# @param debug - flag for debug information DEFAULT: False
# @param security - flag for smtp secutity, possible values:None, STARTTLS, SSL, if not given explicit in 'smtpport' DEFAULT: None
# @param smtpport - if given, integer defining the port of server, if not given, port 25 will be used
# @param dir - if given, directory, where sent mails should be stored
#def Afp_sendOverSMTP(sender, recipients, subject, message, html_message, attachments, smtphost, smtpport = None, debug = False, tls = False, security = None, user = None, word = None, dir = None):
def Afp_sendOverSMTP(sender, recipients, subject, message, html_message, attachments, smtphost, user = None, word = None, debug = False, security = None, smtpport = None, dir = None):
    fname = None
    #decoder = 'us-ascii'
    decoder = 'latin-1'
    if sender and recipients and smtphost and (message or html_message):
        port = 25
        tls = False
        if smtpport:
            port = smtpport
        elif security == "SSL":
            port = 465
        elif tls or security == "STARTTLS":
            tls = True
            port = 587
        msg = MIMEMultipart()
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject.decode(decoder)
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)
        if message:
            part = MIMEText(message.decode(decoder), 'plain')
            msg.attach(part)
        if html_message:
            part = MIMEText(html_message.decode(decoder), 'html')
            msg.attach(part)
        if debug: print("Afp_sendOverSMTP attachments:", attachments)
        if attachments:
            for attach in attachments:
                part = MIMEBase('application', "octet-stream")
                part.set_payload(open(attach, "rb").read())
                email.encoders.encode_base64(part)
                #part.add_header('Content-Disposition', 'attachment; filename=' + attach)
                part.add_header('Content-Disposition', 'attachment; filename=' + Afp_extractBase(attach))
                msg.attach(part)
        if debug: print("Afp_sendOverSMTP Server:",smtphost + ":" + str(port), security)
        if security == "SSL":
            server = smtplib.SMTP_SSL(smtphost, port)
            if debug: server.set_debuglevel(1)
        else:
            server = smtplib.SMTP(smtphost, port)
            if debug: server.set_debuglevel(1)
            if tls: 
                if debug: print("Afp_sendOverSMTP: STARTTLS")
                server.starttls()
        if user and word:
            if debug: print("Afp_sendOverSMTP: LOGIN:",user, word)
            server.login(user,  base64.b64decode(word).decode("UTF-8"))
        if debug: print("Afp_sendOverSMTP: send mail:", msg)
        server.sendmail(sender, recipients + [sender], msg.as_string())
        server.quit()
        if dir:
            if Afp_existsFile(dir):
                monat = {"Jan":"01", "Feb":"02", "Mar":"03", "Apr":"04", "May":"05", "Jun":"06", "Jul":"07", "Aug":"08", "Sep":"09", "Okt":"10", "Nov":"11", "Dec":"12"}
                split = msg['Date'].split()
                date = split[3][2:] + monat[split[2]] + split[1] + "_" + split[4].replace(":","")
                fname = "Mail_" + date + "_" + recipients[0]  + "__" +  subject.decode(decoder).replace(" ", "_")   + ".eml"
                fpath = dir + fname
                file = open(fpath, 'w')
                file.write(str(msg))
                file.close()
            else:
                print("WARNING: Afp_sendOverSMTP maildir '" + dir + "' does not exists, mail not stored!")
    else:
        text = "No"
        if  not sender: text += " originator address,"
        if  not recipients: text += " target address,"
        if  not smtphost: text += " host address,"
        if  not message: text += " message body,"
        if  not html_message: 
            if  not message:
                text = text[:-1] + " or"
            text += " html-message body"
        if text[-1] == ",": text = text[:-1]
        text += " delivered!"
        print("WARNING: Afp_sendOverSMTP Mail not send due to the lack of input!", text)
    return fname
        
##   class to hold cached database requests for multiple use
class AfpArrayCache(object):
    ## initialize AfpArrayCache class
    # @param identifier - if given, identifier string for cached array
    # @param array - if given, data of array to be cached
    # @param debug - flag for debug information
    def  __init__(self, identifier = None, array = None, debug = False):
        self.lifetime  = 10
        self.step = 1
        self.debug = debug        
        self.identifier = None
        self.cache = None
        self.birth = None
        self.death = None
        self.last_use = None
        self.looks = 0
        if identifier and array:
            self.set_array(identifier, array)
        if self.debug: print("AfpArrayCache Konstruktor",identifier)
    ## destructor
    def __del__(self):   
        if self.debug: print("AfpArrayCache Destruktor" , Afp_getNow(), "Looks:", self.looks)
    ## get length of cached array
    def get_length(self):
        if self.cache:
            return len(self.cache)
        else:
            return None
    ## check if cache still is valid
    # @param identifier - identifier string for array looked for
    def is_valid(self, identifier):
        valid = False
        now = Afp_getNow()
        if self.identifier and self.identifier == identifier:
            if now < self.death: valid = True
            elif now < self.last_use + self.interval: valid = True
        if valid:
            self.last_use = now
            self.looks += 1
            #print "AfpArrayCache use:", now, self.identifier, "Birth:", self.birth, "Death:", self.death, "Looks:", self.looks, self.get_length()
        else:
            if self.debug: print("AfpArrayCache clear:", now, self.identifier, "Birth:", self.birth, "Death:", self.death, "Looks:", self.looks)
            self.identifier = None
            self.cache = None
            self.looks = 0
        return valid
    ## fill cache
    # @param identifier - identifier string for cached array
    # @param array - data of array to be cached
    def set_array(self, identifier, array):
        self.identifier = identifier
        self.cache = array
        self.birth = Afp_getNow()
        self.death = self.birth + datetime.timedelta(seconds=self.lifetime)
        self.interval = datetime.timedelta(seconds=self.step)
        self.last_use = self.birth
        self.looks = 0
        if self.debug: print("AfpArrayCache create:", self.birth, self.identifier, "Birth:", self.birth, "Death:", self.death)
    ## retrieve array from cache if possible
    # @param identifier - identifier for array intended to be read
    def read_array(self, identifier):
        if self.is_valid(identifier):
            return self.cache
        return None
    ## add array to current cache
    # @param identifier - if identifier string for given array
    # @param array - data of array to be cached
    def add_array(self, identifier, array):
        if self.is_valid(identifier):
            if self.cache:
                self.cache += array
        else:
            self.set_array(identifier, array)
        
