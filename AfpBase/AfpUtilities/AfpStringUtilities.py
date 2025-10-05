#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpUtilities.AfpStringUtilities
# AfpStringUtilities module provides general solely python dependend utilitiy routines
# it does not hold any classes
#
#   History: \n
#        29 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        29 Sep. 2020 - allow spaces between minus and digit for negativ values in Afp_fromString - Andreas.Knoblauch@afptech.de \n
#        08 May 2016 - allow negativ values in Afp_fromString - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
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


import datetime

from AfpBase.AfpUtilities.AfpBaseUtilities import *

## convert data to string
# @param data - data to be converted
def Afp_toString(data):
    string = ""
    typ  = type(data)   
    if typ == str:
        #string = data.decode('iso8859_15')
        string = data
    #elif typ == unicode: # py2
    #    string = data
    elif typ == int: # or typ == long: # py2
        string = str(data)
    elif typ == float:
        string = ("%8.2f")%(data)
    elif typ == datetime.date:
        string = data.strftime("%d.%m.%y")
    elif typ == datetime.timedelta or typ == datetime.time:
        if (typ == datetime.time and data == datetime.time.max) or (typ == datetime.timedelta and data.days > 0):
            string = "24:00"
        else:
            split = str(data).split(":")
            #print "Afp_toString",data,split
            if  len(split) > 2 and float(split[2]) > 59:
                split[1] = str(int(split[1]) + 1)
                if split[1] == "60":
                    split[1] = "00"
                    split[0] = str(int(split[0]) + 1)
            string = split[0] + ":" + split[1]
    elif typ == datetime.datetime:
        string = data.isoformat()
    elif typ == list:
        string = "".join(str(data))
    elif not data is None:
        print("WARNING: Afp_toString \"" + typ.__name__ + "\" conversion type not specified!", data)
    return string 
## convert data to string, string to quoted strings, 
# dates and times to strings describing the  timedelta or date creation
# @param data - data to be converted
# @param date_conv - flag if dates have to be converted, default: False
def Afp_toQuotedString(data, date_conv = False):
    if date_conv is None:
        string = Afp_toInternDateString(Afp_fromString(data))
        #print "Afp_toQuotedString None:", data, string
    else:
        string = Afp_toString(data)
    if Afp_isString(data): string = "\"" + string + "\""
    if date_conv:
        typ = type(data)
        if  typ == datetime.timedelta or typ == datetime.time:
            if string == "24:00": string = "datetime.timedelta(days=1)"
            else: 
                split = string.split(":")
                string = "datetime.timedelta(hours=" + split[0] + ", minutes=" + split[1] + ")"
        elif typ == datetime.date:
            split = string.split(".")
            if len(split[2]) < 3: split[2] = "20" + split[2]
            string = "datetime.date(" + split[2] + ", " + split[1] + ", " + split[0] + ")"
    return string
## convert data to date string according to input format, 
# dates and times are converted to internal representation (yyyy-mm-dd)
# @param data - data to be converted
# @param format - format for string creation
def Afp_toDateString(data, format):
    string = ""
    use = ""
    lg = len(format)
    for i in range(lg):
        char = format[i]
        if use and (not use[0] == char or i == lg-1):
            if i == lg-1: use += char
            if use[0] == "y":
                st = Afp_toString(data.year)
            elif use[0] =="m":
                st = Afp_toString(data.month)
            elif use[0] == "d":
                st = Afp_toString(data.day)
            else:
                st = use
            lgh = len(use)         
            if len(st) > lgh: st = st[-lgh:]
            elif len(st) < lgh: st = "0"*(lgh - len(st)) + st
            string += st
            use = ""
        use += char
    return string
## convert data to intern date string, 
# dates and times are converted to internal representation (yyyy-mm-dd)
# @param data - data to be converted
def Afp_toInternDateString(data):
    string = Afp_toString(data)
    if type(data) == datetime.date:
        string = data.strftime("%Y-%m-%d")
    elif type(data) == datetime.time:
        string = data.strftime("%H:%M:%S.%f")
    return string
## convert data to string, 
# dates are converted to short format without year (dd.mm)
# @param data - data to be converted
def Afp_toShortDateString(data):
    string = Afp_toString(data)
    if type(data) == datetime.date:
        split = string.split(".")
        string = split[0] + "." + split[1]
    return string
## direct conversion of integer data to string
# @param data - data to be converted
# @param lgh - minimal length of string, preceding zeros will be added
def Afp_toIntString(data, lgh = 3):
    if data is None: return ""
    string = Afp_toString(data)
    if len(string) < lgh:
        string = (lgh - len(string))*"0" + string
    return string.strip()
## direct conversion of float data to string
# @param data - data to be converted
# @param no_strip - flag if not stripped string should be returned
# @param format - format of data in string
def Afp_toFloatString(data, no_strip = False, format = "8.2f"):
    if data is None: return ""
    if type(data) == str: data = Afp_fromString(data)
    string = ("%" + format)%(data)
    if no_strip: return string
    else: return string.strip()
## direct conversion of a numeric data to string
# @param data - data to be converted
# @param ndec - decimal positions allowed in string
def Afp_toNumericString(data, ndec = 3):
    strg = ""
    if Afp_isString(data): strg = data
    if Afp_isNumeric(data):
        if type(data) == int:
            strg = Afp_toIntString(data, 0)
        else:
            strg = Afp_toFloatString(data, False, str(6+ndec) + "." + str(ndec) + "f")
            #print ("Afp_toNumericString:", ndec, data, str(6+ndec) + "." + str(ndec) + "f", strg)
    return strg
## convert number of month into string
# @param nr - number of month
def Afp_toMonthString(nr):
    if nr == 1: return "Januar"
    elif nr == 2: return "Februar"
    elif nr == 3: return "März"
    elif nr == 4: return "April"
    elif nr == 5: return "Mai"
    elif nr == 6: return "Juni"
    elif nr == 7: return "Juli"
    elif nr == 8: return "August"
    elif nr == 9: return "September"
    elif nr == 10: return "Oktober"
    elif nr == 11: return "November"
    elif nr == 12: return "Dezember"
    return ""
## analyse string and create data from it
# @param string - string to be converted
# - "xx.xx" or "xx,xx" -> float (x - digit)
# - "dd.mm.yy[yy]"  -> date, short year will be mapped in actuel century
# - "hh:mm[:ss]" -> time
# - "xxx" -> int (x - digit)
# - other -> string
def Afp_fromString(string):
    if not Afp_isString(string): return string
    #print ("Afp_fromString:", string)
    string = string.strip()
    data = None
    if " " in string and "-" in string and Afp_hasNumericValue(string):
        # find negative values with spaces (between - and digit)
        string = "-" + string.strip()[1:].strip()
    if not " " in string:
        if "." in string and not string == "." :
            split = string.split(".")
        elif "," in string  and not string == "," :
            split = string.split(",")
        else:
            split = [string]
        if len(split) > 2 and len(string) < 11:
            day = 0
            if split[0].isdigit(): day = int(split[0])
            month = 0
            if split[1].isdigit(): month = int(split[1])
            year = -1
            if split[2].isdigit(): year = int(split[2])
            if day > 0 and month > 0 and year > -1:
                if month > 12: month = (month - 1)%12 + 1
                maxday = 31
                if month == 2:
                    if year%4 == 0: maxday = 29
                    else: maxday = 28
                elif month == 4 or month == 6 or month == 9 or month == 11:
                    maxday = 30
                if day > maxday: day = maxday
                if year < 100: 
                    thisyear = datetime.date.today().year
                    year += 100* int(thisyear/100) 
                    if year > thisyear + 10:
                        year -= 100
                data = datetime.date(year, month, day)
        elif len(split) > 1:
            left = 0    
            if split[0].isdigit(): left = int(split[0])
            elif len(split[0]) > 1 and split[0][0] == "-" and split[0][1:].isdigit():
                left =  - int(split[0][1:])
            right = 0
            if split[1] == "-": split[1] = "00"
            if split[1].isdigit(): right = int(split[1])
            if (not left == 0 or Afp_isZeroString(split[0])) and (right > 0 or Afp_isZeroString(split[1])):
                data = float(split[0] + "." + split[1])
        elif ":" in string and len(string) < 9:
            split = string.split(":")
            hours = 0
            if split[0].isdigit(): hours = int(split[0])
            if hours > 23:
                #data = datetime.time.max
                data = datetime.timedelta(days=1)
            else:
                minutes = 0
                if len(split) > 1:
                    if split[1].isdigit(): minutes = int(split[1])
                seconds = 0
                if len(split) > 2:
                    if split[2].isdigit(): seconds = int(split[2])
                #data = datetime.time(hours, minutes, seconds)
                data = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
        elif string:
            val = None
            if string.isdigit() or (string[0] == "-" and string[1:].isdigit()) : val = int(string)
            if not val is None:
                data = val
    if not data is None:
        return data
    else:
        return string
## convert string to an integer
# @param string - string to be converted
# @param init - value, if no integer can be assigned
def Afp_intString(string, init = 0):
    integer = Afp_numericString(string, init)
    if not integer is None: 
        if Afp_isDate(integer): integer = integer.strftime('%Y%m%d')
        integer = int(integer)
    return integer
## convert string to a float
# @param string - string to be converted
# @param init - value, if no float can be assigned
def Afp_floatString(string, init = 0.0):
    flt = Afp_numericString(string, init)
    if not flt is None: flt = float(flt)
    return flt
## convert string to a numeric value
# @param string - string to be converted
# @param init - value, if no float can be assigned
def Afp_numericString(string, init = 0):
    result = init
    data = Afp_fromString(string)
    if Afp_isNumeric(data):
        result = data
    return result
## convert string to a date, if no conversion is found, today is returned
# @param string - string to be converted
def Afp_dateString(string):
    result = Afp_fromString(string)
    if type(result) != datetime.date:
        # look for date at start or end of string
        if len(string) > 5:
            if Afp_hasNumericValue(string[:6]) : string = string[:6]
            elif "." in string and Afp_hasNumericValue(string.split(".")[0][-6:]): string = string.split(".")[0][-6:]
            elif Afp_hasNumericValue(string[-6:]) : string = string[-6:]
            if Afp_hasNumericValue(string[:6]) : string = string[4:6] + "." + string[2:4] + "." + string[:2]
            result = Afp_fromString(string)
    if type(result) != datetime.date:
        result = datetime.datetime.now().date()
    return result
## convert string to a time value
# @param string - string to be converted
# @param end - indicates that maxtime should be set instead or mintime 
# in case no timevalue can be extracted
def Afp_timeString(string, end = False):
    result = Afp_fromString(string)
    typ = type(result)
    if typ == datetime.timedelta:      
        result = Afp_toTime(result)
    elif typ != datetime.time:
        if Afp_isNumeric(string):
            value = Afp_toFloat(string)
            if value:
                hours = int(value)
                mins = int(60*(value - hours))
                result = datetime.time(hours, minutes)
            else:
                if end:
                    result = datetime.time.max
                else:
                    result = datetime.time.min
    return result
## generate datetime data from date- and timestring
# @param datestring - string holding date
# @param timestring - string holding time
# @param end - for time creation: indicates that maxtime should be set instead or mintime 
def Afp_datetimeString(datestring, timestring, end = False):
    date = Afp_dateString(datestring)
    time = Afp_timeString(timestring, end)
    return datetime.datetime.combine(date, time)
## convert a number given by a string to a proper float string
# @param string - string to be converted
def Afp_stringFloatString(string):
    return Afp_toString(Afp_floatString(string))
 
##  convert all entries of a array to strings, routine will be called recursively for inner lists 
# @param array - value array to be converted
def Afp_ArraytoString(array):
    #print "Afp_ArraytoString"
    new_array = []
    if array:
        for row in array:
            if type(row) == list or type(row) == tuple:
                new_array.append(Afp_ArraytoString(row))
            else:
                new_array.append(Afp_toString(row))
    return new_array
## analyses a line and fills entries into array, dictionary or single values \n
# 2 dimensional-arrays are supported, if each entry holds another array, deeper recursion does actually not work!
# @param line - string to be anaysed
def Afp_ArrayfromLine(line):
    #print "Entry:", line
    if line:
        line = line.strip()
        if line[0] == "\"" and line[-1] == "\"":
             line = line[1:-1]
        if line[0] == "{" and line[-1] == "}":
            # dictionary        
            result = {}
            line = line[1:-1]
            split = line.split(",")
            for entry in split:
                spentry = entry.split(":")
                if len(spentry) > 1:
                    name = spentry[0].strip()
                    value = Afp_fromString(spentry[1].strip())
                    result[name] = value
        elif line[0] == "[" and line[-1] == "]":
            # array
            result = []
            line = line[1:-1].strip()
            if line[0] == "[" and line[-1] == "]":
                # inner list, invoke recursion
                split = Afp_split(line,["],[", "], [", "] ,[", "] , ["])
                split[0] = split[0][1:]
                split[-1] = split[-1][:-1]
                for entry in split:
                    entry = "[" + entry + "]"
                    #print "recursive:", entry
                    value = Afp_ArrayfromLine(entry)
                    result.append(value)
            else:
                split = line.split(",")
                for entry in split:
                    #print "value:", entry
                    value = Afp_fromString(entry.strip())
                    result.append(value)
        else:
            result = Afp_fromString(line)
    else:
        result = None
    return result
##merges an array into one string, separated by blanks
# @param liste - list of values to be merged
# @param separator - lelement to be filled between the values
# @param max - maximum number of elements used for merging
# @param append - appendix to be added to each line
def Afp_ArraytoLine(liste, separator = " ", max = None, append = ""):
    if max is None: max = len(liste) 
    sep = len(separator)
    count = 0
    zeile = ""
    for entry in liste:
        if count < max:
            zeile += Afp_toString(entry) + append+ separator
            count += 1
    return zeile[:-sep]
## joins two columns in a matrix to one
# @param matrix - matrix where column should be joined
# @param join - index of column to be joined with the next column
# @param sep - separator to be inserted between joined columns, default: comma 
def Afp_MatrixJoinCol(matrix, join = 0, sep = ", "):
    new_matrix = []
    for row in matrix:
        new_row = []
        for i in range(len(row)):
            if i == join: continue
            elif i == join+1:
                new_row.append(row[join] + sep + row[i])
            else:
                new_row.append(row[i])
        new_matrix.append(new_row)
    return new_matrix
## splits one column in a matrix into the maximal possible number of columns
# @param matrix - matrix where column should be split up
# @param col - number of column to be split up
# @param sep - separator where entry in column should be split up, if integer: number of parts column ist extended to, default: comma 
# @param ret - retired separator where entry in column should be split up, if first don't work
def Afp_MatrixSplitCol(matrix, col=0, sep=",", ret=None):
    column = []
    max = 1
    lgm = len(matrix[0])
    extend_col = False
    if type(sep) == int:
        max = sep
        extend_col = True
    for row in matrix:
        split = [""]
        if row[col]:
            if extend_col: 
                split = [row[col]]
            else:
                split = row[col].split(sep)
                if len(split) < 2 and ret: 
                    split = row[col].split(ret)
                if len(split) > max: max = len(split)
        column.append(split)
    #print "Afp_MatrixSplitCol:", max, column
    if max > 1:
        new_matrix = []
        for i in range(len(column)):
            lgh = len(column[i])
            if  lgh < max:
                for j in range(lgh,max): 
                    column[i].append("")
        lgm = len(matrix[0])
        for i in range(len(matrix)):
            new_row = []
            if col > 0: new_row += matrix [i][:col]
            new_row +=column[i] 
            if col < lgm: new_row += matrix[i][col+1:]
            new_matrix.append(new_row)
    else:
        new_matrix = matrix
    #print "Afp_MatrixSplitCol matrix:", matrix
    #print "Afp_MatrixSplitCol newmat:", new_matrix
    return new_matrix

# type of strings and values
## flag is value is a stringtype
# @param wert - value to be analysed
def Afp_isString(wert):
    typ = type(wert)
    if typ == str: return True # or typ == unicode: # py2
    return False
## flag is value is a string not enclosed by quotes
# @param wert - value to be analysed
def Afp_isPlainString(wert):
    if Afp_isString(wert):
        wert = wert.strip()
        if (wert[0] == "\""and wert[-1] == "\"") or (wert[0] == "'"and wert[-1] == "'"):
            return False
        else:
            return True
    return False
## flag is sign indicates a	comparison
# @param sign - string to be analysed
def Afp_isCompare(sign):
    if "=" in sign or ">" in sign or "<" in sign or "LIKE" in sign:
        return True
    else:
        return False
## flag if string represents an empty line
# @param string - string to be analysed
def Afp_isNewline(string):
    return string.strip() == ""
## flag if string represents an float value
# @param string - string to be analysed
def Afp_isFloatString(string):
    value = Afp_fromString(string)
    #print "Afp_isFloatString:", string, value, type(value)
    if type(value) == float: return True
    return False
## flag if string represents an zero value
# @param string - string to be analysed
def Afp_isZeroString(string):
    if len(string) > 1 and string[0] =="-": string = string[1:]
    for char in string.strip():
        if not char == "0": return False
    return True
## flag if string may represent IP4 address
# @param string - string to be analysed
def Afp_isIP4(string):
    return Afp_hasNumericValue(string, 4)
## flag if string may represent a mail address
# @param string - string to be analysed
def Afp_isMailAddress(string):
    if string:
        Ok = True
        if not "@" in string: Ok = False
        split = string.split(".")
        if len(split[-1].strip()) > 3: Ok = False
    else:
        Ok = False
    return Ok
## check if string is a BIC
# @param bic - string to be checked
def Afp_isBIC(bic):
    if len(bic) != 11 or not bic[4:6] == "DE":
        return None
    bic_list = ['TRBKDEBBXXX', 'MARKDEF1100', 'PBNKDEFFXXX', 'QNTODEB2XXX', 'REVODEB2XXX', 'TRZODEB2XXX', 'KLRNDEBEXXX', 'AARBDE5W100', 'AFOPDEB2XXX', 'FPEGDEB2XXX', 'NTSBDEB1XXX', 'SWNBDEBBXXX', 'HOLVDEB1XXX', 'FNOMDEB2XXX', 'ADYBDEB2XXX', 'BHFBDEFF100', 'BFSWDE33BER', 'HYVEDEMM488', 'BHYPDEB2XXX', 'ABKBDEB1XXX', 'LOEBDEBBXXX', 'GENODEF1OGK', 'DLGHDEB1XXX', 'EIEGDEB1XXX', 'SCFBDE33XXX', 'COBADEBBXXX', 'COBADEFFXXX', 'BELADEBEXXX', 'SKPADEB1XXX', 'LBSODEB1BLN', 'DGZFDEFFBER', 'GENODED1PA6', 'GENODED1KDB', 'DEUTDEBBXXX', 'DEUTDEDBBER', 'DEUTDEBB101', 'DEUTDEDB101', 'DEUTDEDBP30', 'DEUTDEBBP30', 'DEUTDEBBP31', 'DEUTDEBBP32', 'DEUTDEDB110', 'DEUTDEDBP31', 'DEUTDEDBP32', 'NORSDE51XXX', 'DRESDEFF100', 'DRESDEFFI26', 'DRESDEFFXXX', 'DRESDEFF112', 'DRESDEFF114', 'DRESDEFFI53', 'DRESDEFFI71', 'DRESDEFFI72', 'DRESDEFFI73', 'DRESDEFF199', 'DRESDEFFI14', 'DRESDEFFI99', 'BEVODEBBXXX', 'GENODEF1BSB', 'GENODEF1P01', 'MACODEB1XXX', 'IBBBDEBBXXX', 'QUBKDEBBXXX', 'WELADED1WBB', 'ISBKDEFXXXX', 'BIWBDE33XXX', 'BOFSDEB1XXX', 'SYBKDE22BER', 'TRDADEB1PBK', 'TRDADEBBDIR', 'MPAYDEB2XXX', 'SOBKDEBBXXX', 'SOBKDEB2XXX', 'PNTADEBBXXX', 'KFWIDEFF100', 'BYLADEM1001', 'MEFIDEMM100', 'COBADEBB120', 'NOLADE21DVS', 'GENODEFF120', 'DEUTDEBB160', 'DEUTDEBB172', 'DEUTDEBB122', 'DEUTDEBB161', 'DEUTDEBB180', 'DEUTDEBB173', 'DEUTDEBB174', 'DEUTDEBB182', 'DEUTDEBB170', 'DEUTDEBB175', 'DEUTDEBB187', 'DEUTDEBB121', 'DEUTDEBB163', 'DEUTDEBB123', 'DEUTDEBB120', 'DEUTDEBB166', 'DEUTDEBB167', 'DEUTDEBB176', 'DEUTDEBB177', 'DEUTDEBB185', 'DEUTDEBB186', 'DEUTDEBB189', 'DEUTDEBB183', 'DEUTDEBB169', 'DEUTDEBB124', 'DEUTDEBB171', 'DEUTDEBB162', 'DEUTDEBB181', 'DEUTDEBB125', 'DEUTDEBB188', 'DEUTDEBB164', 'DEUTDEBB184', 'DEUTDEBB126', 'DEUTDEBB178', 'DEUTDEBB127', 'DEUTDEBB168', 'DEUTDEBB165', 'DEUTDEDB160', 'DEUTDEDB171', 'DEUTDEDB172', 'DEUTDEDB122', 'DEUTDEDB161', 'DEUTDEDB180', 'DEUTDEDB173', 'DEUTDEDB174', 'DEUTDEDB162', 'DEUTDEDB182', 'DEUTDEDB181', 'DEUTDEDB170', 'DEUTDEDB175', 'DEUTDEDB183', 'DEUTDEDB125', 'DEUTDEDB187', 'DEUTDEDB121', 'DEUTDEDB163', 'DEUTDEDB188', 'DEUTDEDB164', 'DEUTDEDB184', 'DEUTDEDB165', 'DEUTDEDB123', 'DEUTDEDB120', 'DEUTDEDB166', 'DEUTDEDB167', 'DEUTDEDB126', 'DEUTDEDB176', 'DEUTDEDB177', 'DEUTDEDB185', 'DEUTDEDB186', 'DEUTDEDB178', 'DEUTDEDB127', 'DEUTDEDB189', 'DEUTDEDB168', 'DEUTDEDB169', 'DEUTDEDB124', 'DEUTDEFFVAC', 'DEUTDEDBPAL', 'DEUTDEBBP33', 'DEUTDEDBP33', 'DRESDEFF120', 'GENODEF1S10', 'MARKDEF1130', 'NOLADE21ROS', 'NOLADE21RUE', 'GENODEF1WOG', 'GENODEF1HWI', 'GENODEF1HWR', 'GENODEF1DBR', 'DEUTDEBRXXX', 'DEUTDEBB151', 'DEUTDEBR131', 'DEUTDEBR133', 'DEUTDEBB130', 'DEUTDEBB131', 'DEUTDEBR134', 'DEUTDEBR135', 'DEUTDEBB141', 'DEUTDEBB142', 'DEUTDEBB143', 'DEUTDEBB144', 'DEUTDEBB152', 'DEUTDEBB150', 'DEUTDEBB153', 'DEUTDEBB154', 'DEUTDEBR136', 'DEUTDEBB140', 'DEUTDEBR138', 'DEUTDEBB155', 'DEUTDEBB156', 'DEUTDEBB179', 'DEUTDEBB148', 'DEUTDEBB149', 'DEUTDEBB159', 'DEUTDEBB132', 'DEUTDEBB145', 'DEUTDEBB146', 'DEUTDEBB147', 'DEUTDEBR137', 'DEUTDEBB158', 'DEUTDEBB157', 'DEUTDEBR132', 'DEUTDEDBROS', 'DEUTDEDB151', 'DEUTDEDB131', 'DEUTDEDB133', 'DEUTDEDB130', 'DEUTDEDB128', 'DEUTDEDB132', 'DEUTDEDB134', 'DEUTDEDB135', 'DEUTDEDB141', 'DEUTDEDB142', 'DEUTDEDB143', 'DEUTDEDB144', 'DEUTDEDB152', 'DEUTDEDB150', 'DEUTDEDB153', 'DEUTDEDB145', 'DEUTDEDB146', 'DEUTDEDB147', 'DEUTDEDB154', 'DEUTDEDB136', 'DEUTDEDB137', 'DEUTDEDB140', 'DEUTDEDB138', 'DEUTDEDB155', 'DEUTDEDB156', 'DEUTDEDB179', 'DEUTDEDB157', 'DEUTDEDB158', 'DEUTDEDB148', 'DEUTDEDB149', 'DEUTDEDB159', 'DEUTDEBBP35', 'DEUTDEDBP35', 'DRESDEFF130', 'GENODEF1HR1', 'GENODEF1HST', 'GENODEF1HWV', 'NOLADE21WIS', 'NOLADE21PCH', 'NOLADE21SNS', 'NOLADE21LWL', 'GENODEF1GUE', 'GENODEF1GDB', 'DRESDEFF140', 'DRESDEFFI27', 'GENODEF1SN1', 'MARKDEF1150', 'NOLADE21WRN', 'NOLADE21NBS', 'NOLADE21PSW', 'NOLADE21GRW', 'NOLADE21MST', 'GENODEF1WRN', 'GENODEF1ANK', 'GENODEF1MAL', 'DRESDEFF150', 'GENODEF1DM1', 'GENODEF1PZ1', 'ILBXDE8XXXX', 'HYVEDEMM470', 'WELADED1PMB', 'WELADED1PRP', 'WELADED1OPR', 'LBSODEB1XXX', 'GENODEF1PER', 'GENODEF1NPP', 'GENODEF1LUK', 'GENODEF1BRB', 'DRESDEFF160', 'GENODEF1RN1', 'HYVEDEMM471', 'WELADED1GZE', 'WELADED1UMX', 'WELADED1MOL', 'WELADED1LOS', 'WELADED1UMP', 'GENODEF1BKW', 'DRESDEFF170', 'GENODEF1FW1', 'HYVEDEMM472', 'WELADED1CBN', 'WELADED1EES', 'WELADED1OSL', 'GENODEF1FWA', 'GENODEF1FOR', 'DRESDEFF180', 'GENODEF1LN1', 'GENODEF1SPM', 'MARKDEF1200', 'AARBDE5W200', 'ESSEDEFFHAM', 'JYBADEHHXXX', 'SIBSDEHHXXX', 'HYVEDEMM300', 'VGAGDEHHXXX', 'CHDBDEHHXXX', 'MCRDDEHHXXX', 'SYBKDE22HAM', 'MEFIDEMM200', 'COBADEHHXXX', 'COBADEHDXXX', 'COBADEHD001', 'COBADEHD044', 'COBADEHD055', 'COBADEHD066', 'COBADEHD077', 'COBADEHD088', 'COBADEHD099', 'HSHNDEHHXXX', 'HASPDEHHXXX', 'GENODEFF200', 'GENODEF1NDR', 'GENODEF1KLK', 'GENODEF1BBR', 'GENODEF1SST', 'GENODEF1GRS', 'GENODEF1STV', 'GENODEF1OWS', 'GENODEF1AST', 'GENODEF1APE', 'GENODEF1DRO', 'GENODEF1HAA', 'GENODEF1FRB', 'GENODEF1815', 'GENODEF1RRZ', 'GENODEF1RLT', 'GENODEF1WIM', 'GENODEF1WUL', 'DEUTDEHHXXX', 'DEUTDEHH205', 'DEUTDEHH202', 'DEUTDEHH207', 'DEUTDEHH219', 'DEUTDEHH221', 'DEUTDEHH241', 'DEUTDEHH201', 'DEUTDEHH200', 'DEUTDEHH203', 'DEUTDEHH209', 'DEUTDEHH206', 'DEUTDEHH204', 'DEUTDEHH211', 'DEUTDEHH213', 'DEUTDEDBHAM', 'DEUTDEDB201', 'DEUTDEDB219', 'DEUTDEDB207', 'DEUTDEDB211', 'DEUTDEDB241', 'DEUTDEDB221', 'DEUTDEDB205', 'DEUTDEDB200', 'DEUTDEDB203', 'DEUTDEDB202', 'DEUTDEDB206', 'DEUTDEDB213', 'DEUTDEDB209', 'DEUTDEDB204', 'DEUTDEHHP34', 'DEUTDEDBP34', 'DRESDEFF200', 'DRESDEFF207', 'DRESDEFF208', 'DRESDEFFI56', 'DRESDEFFI63', 'DRESDEFFI64', 'DRESDEFFI74', 'DRESDEFFI75', 'DRESDEFFJ33', 'DRESDEFFJ34', 'DRESDEFFJ35', 'DRESDEFFJ36', 'DRESDEFFJ37', 'DRESDEFFI06', 'DGHYDEH1XXX', 'EDEKDEHHXXX', 'GENODEF1P08', 'BOTKDEH1XXX', 'BKCHDEFFHMB', 'BEGODEHHXXX', 'WBWCDEHHXXX', 'BHFBDEFF200', 'DRBKDEH1XXX', 'BFSWDE33HAN', 'GOGODEH1XXX', 'HSTBDEHHXXX', 'GREBDEH1XXX', 'BARCDEHAXXX', 'GENODEF1HH2', 'GENODEF1HH4', 'GENODEF1HH1', 'GENODEF1HH3', 'GENODEF1MKB', 'MELIDEHHXXX', 'SIHRDEH1HAM', 'DNBADEHXXXX', 'SXPYDEHHXXX', 'OSCBDEH1XXX', 'MHSBDEHBXXX', 'EIHBDEHHXXX', 'GENODEF1S11', 'HYVEDEMME01', 'HYVEDEMME02', 'HYVEDEMME03', 'HYVEDEMME04', 'HYVEDEMME05', 'HYVEDEMME06', 'HYVEDEMME07', 'HYVEDEMME08', 'HYVEDEMME09', 'HYVEDEMME10', 'HYVEDEMME11', 'HYVEDEMME12', 'HYVEDEMME13', 'HYVEDEMME14', 'HYVEDEMME15', 'HYVEDEMME16', 'HYVEDEMME17', 'HYVEDEMME18', 'HYVEDEMME19', 'HYVEDEMME20', 'HYVEDEMME21', 'HYVEDEMME22', 'HYVEDEMME23', 'HYVEDEMME24', 'HYVEDEMME25', 'HYVEDEMME26', 'HYVEDEMME27', 'HYVEDEMME28', 'HYVEDEMME29', 'HYVEDEMME30', 'HYVEDEMME31', 'HYVEDEMME32', 'HYVEDEMME33', 'HYVEDEMME34', 'HYVEDEMME35', 'HYVEDEMME36', 'HYVEDEMME37', 'HYVEDEMME38', 'HYVEDEMME39', 'HYVEDEMME40', 'HYVEDEMME41', 'HYVEDEMME42', 'HYVEDEMME43', 'HYVEDEMME44', 'HYVEDEMME45', 'HYVEDEMME46', 'HYVEDEMME47', 'HYVEDEMME48', 'HYVEDEMME49', 'HYVEDEMME50', 'HYVEDEMME52', 'HYVEDEMME55', 'HYVEDEMME56', 'HYVEDEMME57', 'HYVEDEMME58', 'HYVEDEMME59', 'HYVEDEMME60', 'HYVEDEMME61', 'HYVEDEMME62', 'HYVEDEMME63', 'HYVEDEMME64', 'HYVEDEMME65', 'HYVEDEMME66', 'HYVEDEMME67', 'HYVEDEMME68', 'HYVEDEMME69', 'HYVEDEMME70', 'HYVEDEMME71', 'HYVEDEMME72', 'HYVEDEMME73', 'HYVEDEMME74', 'HYVEDEMME75', 'HYVEDEMME76', 'HYVEDEMME77', 'HYVEDEMME78', 'HYVEDEMME79', 'HYVEDEMME80', 'HYVEDEMME81', 'HYVEDEMME82', 'HYVEDEMME83', 'HYVEDEMME84', 'HYVEDEMME85', 'HYVEDEMME86', 'HYVEDEMME87', 'HYVEDEMME88', 'HYVEDEMME89', 'HYVEDEMME90', 'HYVEDEMME91', 'HYVEDEMME92', 'HYVEDEMME93', 'HYVEDEMME94', 'HYVEDEMME95', 'HYVEDEMME96', 'HYVEDEMME97', 'HYVEDEMME98', 'HYVEDEMME99', 'NOLADE21HAM', 'MARKDEF1210', 'SYBKDE22KIE', 'NOLADE21KIE', 'NOLADE21BOR', 'NOLADE21PLN', 'NOLADE21ECK', 'DEUTDEHH210', 'DEUTDEHH214', 'DEUTDEDB210', 'DEUTDEDB214', 'DRESDEFF210', 'DRESDEFFI07', 'GENODEF1KIL', 'GENODEF1P11', 'GENODEF1EFO', 'GENODEF1WAS', 'GENODEF1BOO', 'DEUTDEHH212', 'DEUTDEDB212', 'DRESDEFF212', 'GENODEF1NMS', 'NOLADE21HOL', 'GENODEF1NSH', 'GENODEF1EUT', 'NOLADE21RDB', 'NOLADE21BDF', 'NOLADE21HWS', 'GENODEF1NTO', 'GENODEF1TOB', 'DRESDEFF214', 'SYBKDE22XXX', 'UNBNDE21XXX', 'GENODEF1HDW', 'DEUTDEHH215', 'DEUTDEHH216', 'DEUTDEDB215', 'DEUTDEDB216', 'DEUTDEHHP01', 'DEUTDEDBP01', 'DRESDEFF215', 'GENODEF1RSL', 'GENODEF1SLW', 'NOLADE21NOS', 'NOLADE21BRD', 'GENODEF1HUM', 'GENODEF1BDS', 'DEUTDEHH217', 'DEUTDEDB217', 'GENODEF1SYL', 'GENODEF1WYK', 'NOLADE21WEB', 'GENODEF1RHE', 'GENODEF1DVR', 'NOLADE21ELH', 'NOLADE21WED', 'GENODEF1HTE', 'DRESDEFF221', 'DRESDEFF206', 'GENODEF1ELM', 'GENODEF1PIN', 'NOLADE21WHO', 'DRESDEFF201', 'GENODEF1VIT', 'MARKDEF1230', 'HSHNDEHH230', 'NOLADE21SPL', 'NOLADE21SHO', 'NOLADE21RZB', 'GENODEF1LZN', 'GENODEF1BAR', 'GENODEF1RLB', 'GENODEF1BCH', 'DEUTDEHHP02', 'DEUTDEDBP02', 'DEUTDEDB237', 'DEUTDEHH222', 'DRESDEFF230', 'DRESDEFFI08', 'GENODEF1HLU', 'NOLADE21LBG', 'GENODEF1NBU', 'GENODEF1DAB', 'DEUTDEDB240', 'DEUTDEDB242', 'DEUTDE2H240', 'DEUTDE2H241', 'DEUTDEDBP22', 'DEUTDE2HP22', 'DRESDEFF240', 'GENODEF1LUE', 'GENODED1RKI', 'BRLADE21CUX', 'NOLADE21STS', 'NOLADE21STK', 'BRLADE21ROB', 'GENODEF1SIT', 'GENODEF1LAS', 'DRESDEFF242', 'DRESDEFF241', 'GENODEF1SDE', 'MARKDEF1250', 'AARBDE5W250', 'DEHYDE2HXXX', 'CKVHDE21XXX', 'BHFBDEFF250', 'NOLADE2HXXX', 'NOLADE21CSH', 'NOLADE21CMV', 'SPKHDE2HXXX', 'NOLADE21LBS', 'GENODEFF250', 'GENODEFF280', 'HALLDE2HXXX', 'GENODEF1DES', 'GENODEF1NST', 'GENODEF1MUA', 'GENODEF1BNT', 'DEUTDEDBHAN', 'DEUTDEDB243', 'DEUTDEDB250', 'DEUTDEDB252', 'DEUTDEDB931', 'DEUTDEDB932', 'DEUTDEDB256', 'DEUTDEDB251', 'DEUTDEDB933', 'DEUTDEDB258', 'DEUTDE2H265', 'DEUTDE2HXXX', 'DEUTDE2H250', 'DEUTDE2H283', 'DEUTDE2H282', 'DEUTDE2H252', 'DEUTDE2H256', 'DEUTDE2H258', 'DEUTDE2H284', 'DEUTDE2H251', 'DEUTDEDBP24', 'DEUTDE2HP24', 'DRESDEFF250', 'DRESDEFFI65', 'DRESDEFFI09', 'GENODEF1BFS', 'GENODEF1S09', 'GENODEF1P09', 'NOLADE21BAH', 'NOLADE21BUF', 'NOLADE21WAL', 'NOLADE21WST', 'VOHADE2HXXX', 'GENODEF1PAT', 'NOLADE21PEI', 'GENODEF1PEV', 'BHWBDE2HXXX', 'NOLADE21HMS', 'NOLADE21SWB', 'NOLADE21PMT', 'GENODEF1HMP', 'GENODEF1COP', 'DEUTDEDB254', 'DEUTDEDB255', 'DEUTDE2H254', 'DEUTDEDB264', 'DEUTDE2H264', 'DRESDEFF254', 'GENODED1AEZ', 'NOLADE21SHG', 'GENODEF1BCK', 'OLBODEH2XXX', 'NOLADE21NIB', 'BRLADE21DHZ', 'GENODEF1STY', 'GENODEF1HOY', 'GENODEF1NIN', 'GENODEF1SUL', 'NOLADE21CEL', 'GENODEF1WIK', 'DEUTDEDB257', 'DEUTDE2H257', 'DRESDEFF257', 'GENODEF1HKB', 'GENODEF1HMN', 'NOLADE21UEL', 'NOLADE21SOL', 'GENODEF1CLZ', 'GENODEF1EUB', 'GENODEF1WOT', 'GENODEF1SOL', 'NOLADE21HIS', 'NOLADE21HIK', 'DEUTDEDB259', 'DEUTDE2H259', 'DEUTDEDB253', 'DEUTDEDB261', 'DEUTDE2H253', 'DEUTDE2H261', 'DRESDEFF259', 'GENODEF1HIH', 'GENODEF1SLD', 'MARKDEF1260', 'NOLADE21GOE', 'NOLADE21DUD', 'GENODEF1DUD', 'GENODEF1ADE', 'GENODEF1DRA', 'DEUTDEDB260', 'DEUTDEDB263', 'DEUTDE2H260', 'DEUTDE2H263', 'DRESDEFF260', 'GENODEF1GOE', 'NOLADE21NOM', 'NOLADE21EIN', 'GENODEF1EIN', 'GENODEF1HDG', 'DEUTDEDB262', 'DEUTDE2H262', 'DRESDEFF261', 'DRESDEFF262', 'NOLADE21OHA', 'NOLADE21HZB', 'NOLADE21SAC', 'MARKDEF1265', 'NOLADE22XXX', 'NOLADE21BEB', 'NOLADE21MEL', 'GENODEF1HTR', 'GENODEF1WHO', 'GENODEF1HGM', 'GENODEF1MRZ', 'GENODEF1NOP', 'DEUTDEDB265', 'DEUTDEDB921', 'DEUTDEDB922', 'DEUTDEDB923', 'DEUTDEDB924', 'DEUTDEDB266', 'DEUTDEDB925', 'DEUTDE3B265', 'DEUTDE3B270', 'DEUTDE3B269', 'DEUTDE3B268', 'DEUTDE3B271', 'DEUTDE3B266', 'DEUTDE3B272', 'DRESDEFF265', 'DRESDEFFI10', 'GENODEF1OSV', 'NOLADE21EMS', 'GENODEF1LIG', 'GENODEF1HLN', 'GENODEF1MEP', 'GENODEF1LEN', 'GENODEF1HAR', 'NOLADE21NOH', 'GENODEF1NDH', 'DEUTDEDB267', 'DEUTDEDB926', 'DEUTDEDB927', 'DEUTDEDB928', 'DEUTDE3B267', 'DEUTDE3B274', 'DEUTDE3B273', 'DEUTDE3B275', 'NOLADE21GSL', 'NOLADE21CLZ', 'NOLADE21SZG', 'DEUTDEDB268', 'DEUTDEDB929', 'DEUTDEDB934', 'DEUTDE2H268', 'DEUTDE2H280', 'DEUTDE2H285', 'DRESDEFF268', 'GENODEF1VNH', 'GENODEF1OHA', 'NOLADE21GFW', 'DEUTDEDB269', 'DEUTDE2H269', 'DRESDEFF269', 'DRESDEFFI11', 'GENODEF1WOB', 'VOWADE2BXXX', 'AUDFDE21XXX', 'SKODDE21XXX', 'ECBKDE21XXX', 'SEATDE21XXX', 'BCLSDE21XXX', 'GENODEF1BOH', 'DEUTDEDB270', 'DEUTDEDB278', 'DEUTDEDB271', 'DEUTDEDB930', 'DEUTDEDB274', 'DEUTDEDB272', 'DEUTDEDB279', 'DEUTDEDB273', 'DEUTDEDB275', 'DEUTDE2H270', 'DEUTDE2H271', 'DEUTDE2H274', 'DEUTDE2H281', 'DEUTDE2H278', 'DEUTDE2H279', 'DEUTDE2H272', 'DEUTDE2H273', 'DEUTDE2H275', 'DEUTDEDBP23', 'DEUTDE2HP23', 'DEUTDEDB277', 'DEUTDE2H277', 'DEUTDEDB276', 'DEUTDE2H276', 'DRESDEFF270', 'DRESDEFFI12', 'GENODEF1P02', 'GENODEF1WFV', 'GENODEF1RTS', 'GENODEF1HMV', 'GENODEF1BLG', 'GENODEF1SES', 'MARKDEF1280', 'FORTDEH4XXX', 'SLZODE22XXX', 'GENODEF1OL2', 'GENODEF1BRN', 'GENODEF1CLP', 'GENODEF1DAM', 'GENODEF1EDE', 'GENODEF1RSE', 'GENODEF1HUD', 'GENODEF1LON', 'GENODEF1GBH', 'GENODEF1BSL', 'GENODEF1WRE', 'GENODEF1ESO', 'GENODEF1BAM', 'GENODEF1VEC', 'GENODEF1NHE', 'GENODEF1LOG', 'GENODEF1DIK', 'GENODEF1SAN', 'GENODEF1VIS', 'GENODEF1WDH', 'GENODEF1FOY', 'GENODEF1NEO', 'GENODEF1GSC', 'GENODEF1LAP', 'GENODEF1BUT', 'GENODEF1ORF', 'GENODEF1HAT', 'GENODEF1EMK', 'GENODEF1GRR', 'GENODEF1VAG', 'GENODEF1BBH', 'GENODEF1WLT', 'GENODEF1BOG', 'GENODEF1MLO', 'GENODEF1WWM', 'GENODEF1KBL', 'GENODEF1HOO', 'GENODEF1LRU', 'GENODEF1NEV', 'GENODEF1LTH', 'GENODEF1SPL', 'DEUTDEDB280', 'DEUTDEDB281', 'DEUTDEHB280', 'DEUTDEHB281', 'BRLADE21WHV', 'BRLADE21WTM', 'GENODEF1JEV', 'GENODEF1VAR', 'DEUTDEDB282', 'DEUTDEDB283', 'DEUTDEHB282', 'DEUTDEHB283', 'DRESDEFF282', 'GENODEF1WHV', 'GENODEF1ESE', 'BRLADE21ANO', 'GENODEF1MAR', 'BRLADE21EMD', 'DEUTDEDB284', 'DEUTDEDB289', 'DEUTDEDB286', 'DEUTDEDB298', 'DEUTDEHB284', 'DEUTDEHB289', 'DEUTDEHB286', 'DEUTDEHB298', 'BRLADE21LER', 'GENODEF1UPL', 'GENODEF1WEF', 'GENODEF1HTL', 'GENODEF1MML', 'DEUTDEDB285', 'DEUTDEDB287', 'DEUTDEDB288', 'DEUTDEHB285', 'DEUTDEHB287', 'DEUTDEHB288', 'GENODEF1LER', 'GENODEF1PAP', 'GENODEF1WRH', 'MARKDEF1290', 'NEELDE22XXX', 'NFHBDE21XXX', 'PLUMDE29XXX', 'BRLADE22XXX', 'BRLADE22OLD', 'SBREDE22XXX', 'DEUTDEDBBRE', 'DEUTDEDB295', 'DEUTDEDB292', 'DEUTDEDB293', 'DEUTDEDB294', 'DEUTDEDB296', 'DEUTDEDB297', 'DEUTDEDB290', 'DEUTDEHBXXX', 'DEUTDEHB295', 'DEUTDEHB297', 'DEUTDEHB292', 'DEUTDEHB294', 'DEUTDEHB293', 'DEUTDEHB290', 'DEUTDEHB296', 'DEUTDEDBP21', 'DEUTDEHBP21', 'DRESDEFF290', 'DRESDEFFI13', 'GENODEF1P03', 'BRLADE21SYK', 'BRLADE21OHZ', 'BRLADE21SHL', 'BRLADE21VER', 'GENODEF1OHZ', 'GENODEF1SWW', 'GENODEF1VER', 'GENODEF1OYT', 'GENODEF1SUM', 'GENODEF1WOP', 'GENODEF1SHR', 'DEUTDEDB291', 'DEUTDEHB291', 'GENODEF1HB1', 'GENODEF1HB2', 'BRLADE21BRS', 'BRLADE21BRK', 'GENODEF1BRV', 'GENODEF1BEV', 'DRESDEFF292', 'GENODEF1HBV', 'MARKDEF1300', 'IKBDDEDDXXX', 'IKBDDEDDDIR', 'BOTKDEDXXXX', 'VPAYDE32XXX', 'BHFBDEFF300', 'MHCBDEDDXXX', 'CMCIDEDDXXX', 'NRWBDEDMXXX', 'PULSDEDDXXX', 'CUABDED1XXX', 'ETRIDE31XXX', 'TUBDDEDDXXX', 'MEFIDEMM300', 'COBADEDDXXX', 'COBADEFFSTS', 'WELADEDDXXX', 'DUSSDEDDXXX', 'GENODEDDXXX', 'DAAEDEDDXXX', 'GENODEF1P05', 'DEUTDEDDXXX', 'DEUTDEDD306', 'DEUTDEDD307', 'DEUTDEDD300', 'DEUTDEDD305', 'DEUTDEDD301', 'DEUTDEDD304', 'DEUTDEDD303', 'DEUTDEDD302', 'DEUTDEDBDUE', 'DEUTDEDB306', 'DEUTDEDB305', 'DEUTDEDB307', 'DEUTDEDB301', 'DEUTDEDB303', 'DEUTDEDB302', 'DEUTDEDB300', 'DEUTDEDB304', 'DEUTDEDDP06', 'DEUTDEDBP06', 'DRESDEFF300', 'DRESDEFFI28', 'DRESDEFFI29', 'DRESDEFFI30', 'DRESDEFF309', 'DRESDEFF316', 'DRESDEFFI31', 'DRESDEFFI32', 'DRESDEFFI76', 'DRESDEFFI77', 'DRESDEFFI78', 'DRESDEFFI79', 'DRESDEFFI80', 'DRESDEFFI81', 'DRESDEFFI82', 'DRESDEFFI83', 'DRESDEFFI84', 'DRESDEFFI85', 'DRESDEFFI33', 'DRESDEFFI02', 'DRESDEFFI03', 'SMBCDEDDXXX', 'DHBNDEDDXXX', 'UGBIDEDDXXX', 'ISBKDEFXDUS', 'WELADED1KSD', 'GENODED1DNE', 'HYVEDEMM414', 'BIWBDE33303', 'WELADED1HAA', 'RCIDDE3NXXX', 'RCIDDE3NPAY', 'KREDDEDDXXX', 'WERHDED1XXX', 'WEFZDED1XXX', 'WELADEDNXXX', 'WELADED1KST', 'GENODED1NSS', 'GENODED1NLD', 'MGLSDE33XXX', 'GENODED1GBM', 'GENODED1MRB', 'GENODED1KBN', 'GENODED1NKR', 'DEUTDEDD310', 'DEUTDEDD317', 'DEUTDEDD318', 'DEUTDEDD319', 'DEUTDEDB310', 'DEUTDEDB319', 'DEUTDEDB317', 'DEUTDEDB318', 'DEUTDEDDP05', 'DEUTDEDBP05', 'DRESDEFF310', 'DRESDEFFI34', 'WELADED1ERK', 'GENODED1EHE', 'GENODED1LOE', 'GENODED1VSN', 'DEUTDEDD314', 'DEUTDEDD315', 'DEUTDEDD316', 'DEUTDEDB314', 'DEUTDEDB316', 'DEUTDEDB315', 'SPKRDE33XXX', 'WELADED1STR', 'GENODED1HTK', 'GENODED1GDL', 'GENODED1KMP', 'DEUTDEDB320', 'DEUTDEDB323', 'DEUTDEDB327', 'DEUTDEDB328', 'DEUTDEDB329', 'DEUTDEDB936', 'DEUTDEDB322', 'DEUTDEDB321', 'DEUTDEDD320', 'DEUTDEDD323', 'DEUTDEDD327', 'DEUTDEDD328', 'DEUTDEDD331', 'DEUTDEDD329', 'DEUTDEDD322', 'DEUTDEDD321', 'DRESDEFF320', 'WELADED1GOC', 'WELADED1KLE', 'GENODED1KLL', 'DEUTDEDB324', 'DEUTDEDB326', 'DEUTDEDB325', 'DEUTDEDD324', 'DEUTDEDD325', 'DEUTDEDD326', 'AKFBDE31XXX', 'HYVEDEMM809', 'GGABDE31XXX', 'COBADEDHXXX', 'WUPSDE33XXX', 'GENODED1CVW', 'GENODED1SPW', 'DEUTDEDBWUP', 'DEUTDEDB331', 'DEUTDEDB332', 'DEUTDEDB333', 'DEUTDEDB334', 'DEUTDEDB330', 'DEUTDEDB335', 'DEUTDEDWXXX', 'DEUTDEDW331', 'DEUTDEDW333', 'DEUTDEDW332', 'DEUTDEDW330', 'DEUTDEDW334', 'DEUTDEDW335', 'DRESDEFFI86', 'DRESDEFF332', 'DRESDEFFI87', 'DRESDEFFI88', 'DRESDEFFI89', 'DRESDEFFI90', 'WELADED1VEL', 'WELADED1HGH', 'WELADEDRXXX', 'WELADED1RVW', 'WELADED1WMK', 'VBRSDE33XXX', 'VBRSDE33305', 'VBRSDE33343', 'VBRSDE33330', 'VBRSDE33342', 'VBRSDE33345', 'VBRSDE33341', 'VBRSDE33346', 'VBRSDE33347', 'DEUTDEDB340', 'DEUTDEDB344', 'DEUTDEDB345', 'DEUTDEDB346', 'DEUTDEDB341', 'DEUTDEDW340', 'DEUTDEDW344', 'DEUTDEDW346', 'DEUTDEDW341', 'DEUTDEDW345', 'DRESDEFF340', 'SOLSDE33XXX', 'DEUTDEDB342', 'DEUTDEDB343', 'DEUTDEDW342', 'DEUTDEDW343', 'DRESDEFF342', 'DUISDE33XXX', 'GENODED1DKD', 'GENODED1VRR', 'DEUTDEDB350', 'DEUTDEDB351', 'DEUTDEDB352', 'DEUTDEDB354', 'DEUTDEDB356', 'DEUTDEDE350', 'DEUTDEDE351', 'DEUTDEDE352', 'DEUTDEDE354', 'DEUTDEDE356', 'DRESDEFF350', 'DRESDEFFI91', 'DRESDEFFI92', 'DRESDEFFI93', 'DRESDEFFI94', 'DRESDEFFI95', 'GENODEF1BSD', 'WELADED1DIN', 'GENODED1DLK', 'WELADED1MOR', 'WELADED1NVL', 'WELADED1RHB', 'GENODED1NRH', 'WELADED1WES', 'GENODED1RLW', 'WELADED1EMR', 'GENODED1EMR', 'MARKDEF1360', 'AARBDE5W360', 'NBAGDE3EXXX', 'HYVEDEMM360', 'SPESDE3EXXX', 'GENODED1PA2', 'GENODED1BBE', 'GENODEM1GBE', 'GENODED1SPE', 'DEUTDEDBESS', 'DEUTDEDEXXX', 'DEUTDEDEP07', 'DEUTDEDBP07', 'DRESDEFF360', 'DRESDEFFI66', 'DRESDEFFI17', 'SPMHDE3EXXX', 'DEUTDEDB362', 'DEUTDEDE362', 'DRESDEFF362', 'WELADED1OBH', 'DEUTDEDB365', 'DEUTDEDE365', 'DRESDEFF365', 'MARKDEF1370', 'BNPADEFFXXX', 'BUNQDE82XXX', 'HYVEDEMM429', 'AXABDE31XXX', 'TOBADE33XXX', 'BFSWDE33XXX', 'FDBADE3KXXX', 'FDBADE8FXXX', 'LRFSDE31XXX', 'WWBADE3AXXX', 'ISBKDEFXKOL', 'COLSDE33XXX', 'COKSDE33XXX', 'GENODED1PA7', 'GENODED1PAX', 'GENODED1SPK', 'GENODEF1P13', 'GENODED1BGL', 'GENODED1FHH', 'GENODED1PAF', 'GENODED1FKH', 'GENODED1AEG', 'GENODED1ALD', 'GENODED1RKO', 'GENODED1HCK', 'GENODED1MBU', 'GENODED1ERE', 'GENODED1GLK', 'GENODED1GKK', 'GENODED1GRB', 'GENODED1EGY', 'GENODED1HAW', 'GENODED1KHO', 'GENODED1HMB', 'GENODED1SEG', 'GENODED1AHO', 'GENODED1IMM', 'GENODED1JUK', 'GENODED1KAA', 'GENODED1HRB', 'GENODED1DHK', 'GENODED1KNL', 'GENODED1ERF', 'GENODED1RST', 'GENODED1MNH', 'GENODED1MUC', 'GENODED1RBC', 'GENODED1WND', 'GENODED1SMR', 'GENODED1SAM', 'GENODED1SLE', 'GENODED1WVI', 'GENODED1WSL', 'GENODED1WPF', 'GENODED1BRL', 'DEUTDEDK402', 'DEUTDEDBKOE', 'DEUTDEDB379', 'DEUTDEDB938', 'DEUTDEDB373', 'DEUTDEDB370', 'DEUTDEDB939', 'DEUTDEDB353', 'DEUTDEDB940', 'DEUTDEDB355', 'DEUTDEDB372', 'DEUTDEDB941', 'DEUTDEDB357', 'DEUTDEDB358', 'DEUTDEDB386', 'DEUTDEDB360', 'DEUTDEDB371', 'DEUTDEDKXXX', 'DEUTDEDK372', 'DEUTDEDK370', 'DEUTDEDK373', 'DEUTDEDK351', 'DEUTDEDK354', 'DEUTDEDK352', 'DEUTDEDK355', 'DEUTDEDK356', 'DEUTDEDK360', 'DEUTDEDK386', 'DEUTDEDK371', 'DEUTDEDK379', 'DEUTDEDK357', 'DEUTDEDK353', 'DEUTDEDK358', 'DEUTDEDKP08', 'DEUTDEDBP08', 'DRESDEFF370', 'DRESDEFFI51', 'DRESDEFFI67', 'DRESDEFFI96', 'DRESDEFFI97', 'DRESDEFFI98', 'DRESDEFFJ01', 'DRESDEFFJ02', 'DRESDEFFJ03', 'DRESDEFFJ04', 'DRESDEFFJ05', 'DRESDEFFJ06', 'DRESDEFFJ07', 'DRESDEFFI36', 'DRESDEFFI04', 'DRESDEFFI05', 'GENODED1CGN', 'GENODED1BRH', 'WELADED1LEI', 'WELADEDLLEV', 'WELADED1LAF', 'GENODED1RWL', 'DEUTDEDB375', 'DEUTDEDB378', 'DEUTDEDB377', 'DEUTDEDK375', 'DEUTDEDK378', 'DEUTDEDK377', 'PBNKDEFF380', 'PBNKDEFFDSL', 'DTABDED1XXX', 'DTABDED1AUS', 'VZVDDED1XXX', 'VZVDDED1001', 'VZVDDED1002', 'VZVDDED1003', 'VZVDDED1004', 'VZVDDED1005', 'VZVDDED1006', 'VZVDDED1007', 'VZVDDED1008', 'HYVEDEMM402', 'COLSDE33BON', 'WELADED1HON', 'GENODED1BRS', 'DEUTDEDB380', 'DEUTDEDB944', 'DEUTDEDB943', 'DEUTDEDB946', 'DEUTDEDB942', 'DEUTDEDB945', 'DEUTDEDK380', 'DEUTDEDK385', 'DEUTDEDK389', 'DEUTDEDK388', 'DEUTDEDK384', 'DEUTDEDK387', 'DEUTDEDKP38', 'DEUTDEDBP38', 'DEUTDEDBXXX', 'DEUTDEDB383', 'DRESDEFF380', 'GENODED1HBO', 'WELADED1EUS', 'GENODED1EVB', 'WELADED1GMB', 'WELADED1WIE', 'GENODED1WIL', 'DEUTDEDB384', 'DEUTDEDB385', 'DEUTDEDB388', 'DEUTDEDB389', 'DEUTDEDB387', 'DEUTDEDW384', 'DEUTDEDW385', 'DEUTDEDW388', 'DEUTDEDW389', 'DEUTDEDW387', 'GENODED1STB', 'WELADED1SGB', 'WELADED1HEN', 'AABSDE31XXX', 'AACSDE33XXX', 'GENODED1AAC', 'GENODED1HNB', 'DEUTDEDK390', 'DEUTDEDK391', 'DEUTDEDK398', 'DEUTDEDK392', 'DEUTDEDK394', 'DEUTDEDK397', 'DEUTDEDK399', 'DEUTDEDK393', 'DEUTDEDK400', 'DEUTDEDK401', 'DEUTDEDB390', 'DEUTDEDB398', 'DEUTDEDB391', 'DEUTDEDB948', 'DEUTDEDB397', 'DEUTDEDB394', 'DEUTDEDB392', 'DEUTDEDB393', 'DEUTDEDB399', 'DEUTDEDB947', 'DEUTDEDKP09', 'DEUTDEDBP09', 'DRESDEFF390', 'DRESDEFFI37', 'DRESDEFFI38', 'GENODED1PA1', 'GENODED1AAS', 'GENODED1WUR', 'GENODED1RSC', 'SDUEDE33XXX', 'GENODED1DUE', 'DEUTDEDB395', 'DEUTDEDB396', 'DEUTDEDK395', 'DEUTDEDK396', 'DRESDEFF395', 'NRWBDEDMMST', 'MLBKDEH1MUE', 'WELADE3MXXX', 'WELADED1MST', 'LBSWDE31XXX', 'GENODEMSXXX', 'GENODEM1DKM', 'GENODEM1WLM', 'GENODEF1S08', 'GENODEM1GRV', 'GENODEM1CND', 'GENODEM1MAS', 'GENODEM1SLN', 'GENODEM1MDB', 'GENODEM1SAE', 'GENODEM1SMB', 'GENODEM1BTH', 'GENODEM1BAU', 'GENODEM1DWU', 'GENODEM1SDN', 'GENODEM1MAB', 'GENODEM1CAN', 'GENODEM1ERR', 'GENODEM1LSP', 'GENODEM1DLR', 'GENODEM1SCN', 'DEUTDEDB400', 'DEUTDEDB949', 'DEUTDEDB950', 'DEUTDEDB951', 'DEUTDEDB952', 'DEUTDEDB404', 'DEUTDE3B400', 'DEUTDE3B442', 'DEUTDE3B443', 'DEUTDE3B441', 'DEUTDE3B404', 'DEUTDE3B440', 'DEUTDE3BP10', 'DEUTDEDBP10', 'DRESDEFF400', 'DRESDEFFI68', 'GENODEF1P15', 'WELADED1EMS', 'WELADED1GRO', 'WELADED1LEN', 'WELADE3WXXX', 'WELADED1STL', 'GENODEM1MSC', 'GENODEM1SEE', 'GENODEM1GRN', 'GENODEM1LAE', 'GENODEM1CNO', 'GENODEM1LHN', 'GENODEM1OTR', 'GENODEM1GE1', 'GENODEM1SEM', 'GENODEM1LLE', 'GENODEM1BUL', 'WELADED1RHN', 'WELADED1STF', 'WELADED1IBB', 'GENODEM1WKP', 'GENODEM1IBB', 'GENODEM1HRL', 'DEUTDEDB403', 'DEUTDEDB405', 'DEUTDEDB406', 'DEUTDEDB401', 'DEUTDEDB407', 'DEUTDEDB408', 'DEUTDEDB409', 'DEUTDE3B403', 'DEUTDE3B406', 'DEUTDE3B405', 'DEUTDE3B401', 'DEUTDE3B409', 'DEUTDE3B408', 'DEUTDE3B407', 'WELADED1HAM', 'WELADED1WRN', 'WELADED1BGK', 'GENODEM1HBH', 'GENODEM1BAG', 'GENODEM1BO1', 'DEUTDEDB410', 'DEUTDEDB412', 'DEUTDEDE410', 'DEUTDEDE412', 'WELADED1BEK', 'GENODEM1BEK', 'GENODEM1EOW', 'GENODEM1OEN', 'GENODEM1AHL', 'DRESDEFF413', 'WELADED1SOS', 'WELADED1WRL', 'GENODEM1SOE', 'GENODEM1WRU', 'WELADED1LIP', 'WELADED1HSL', 'WELADED1ERW', 'WELADED1GES', 'GENODEM1LPS', 'GENODEM1ANR', 'GENODEM1LBH', 'GENODEM1BRI', 'GENODEM1SGE', 'GENODEM1WST', 'GENODEM1HOE', 'DEUTDEDB416', 'DEUTDEDB417', 'DEUTDEDB414', 'DEUTDEDB418', 'DEUTDE3B416', 'DEUTDE3B417', 'DEUTDE3B414', 'DEUTDE3B418', 'ISBKDEFXGEL', 'WELADED1GEK', 'DEUTDEDB420', 'DEUTDEDB422', 'DEUTDEDB423', 'DEUTDEDB424', 'DEUTDEDB366', 'DEUTDEDB426', 'DEUTDEDB425', 'DEUTDEDB421', 'DEUTDEDE420', 'DEUTDEDE384', 'DEUTDEDE422', 'DEUTDEDE424', 'DEUTDEDE423', 'DEUTDEDE425', 'DEUTDEDE426', 'DEUTDEDE421', 'DRESDEFF420', 'GENODEM1GBU', 'WELADED1GLA', 'WELADED1BOT', 'GENODEM1KIH', 'WELADED1REK', 'WELADED1HAT', 'GENODEM1MRL', 'GENODEM1HLT', 'GENODEM1WLW', 'GENODEM1DST', 'DRESDEFF426', 'WELADED1BOH', 'GENODEM1BOH', 'GENODEM1RKN', 'GENODEM1BOB', 'GENODEM1BOG', 'GENODEM1HEI', 'GENODEM1RHD', 'GENODEM1RAE', 'DEUTDEDB428', 'DEUTDEDB429', 'DEUTDE3B428', 'DEUTDE3B429', 'MARKDEF1430', 'WELADED1BOC', 'WELADED1HTG', 'GENODEM1BOC', 'GENODEM1GLS', 'DEUTDEDB430', 'DEUTDEDB433', 'DEUTDEDB432', 'DEUTDEDB434', 'DEUTDEDB431', 'DEUTDEDE430', 'DEUTDEDE433', 'DEUTDEDE434', 'DEUTDEDE432', 'DEUTDEDE431', 'DRESDEFF430', 'WELADED1HRN', 'MARKDEF1440', 'HYVEDEMM808', 'WELADE3DXXX', 'DORTDE33XXX', 'GENODEM1DNW', 'GENODED1KDD', 'DEUTDEDB440', 'DEUTDEDB441', 'DEUTDEDB442', 'DEUTDEDB444', 'DEUTDEDB443', 'DEUTDEDB447', 'DEUTDEDB448', 'DEUTDEDE440', 'DEUTDEDE441', 'DEUTDEDE442', 'DEUTDEDE443', 'DEUTDEDE444', 'DEUTDEDE447', 'DEUTDEDE448', 'DRESDEFF440', 'DRESDEFF446', 'DRESDEFF447', 'DRESDEFFI69', 'DRESDEFFI18', 'GENODEF1P04', 'WELADED1LUN', 'WELADED1SWT', 'GENODEM1DOR', 'WELADED1UNN', 'WELADED1KAM', 'WELADED1FRN', 'GENODEM1KWK', 'WELADED1ISL', 'WELADED1HEM', 'DEUTDEDW445', 'DEUTDEDW446', 'DEUTDEDW447', 'DEUTDEDW444', 'DEUTDEDW449', 'DEUTDEDW443', 'DEUTDEDW448', 'DEUTDEDB445', 'DEUTDEDB446', 'DEUTDEDB954', 'DEUTDEDB955', 'DEUTDEDB956', 'DEUTDEDB449', 'DEUTDEDB953', 'DRESDEFF445', 'DRESDEFFI70', 'GENODEM1MEN', 'GENODEM1NRD', 'MARKDEF1450', 'WELADE3HXXX', 'WELADED1HER', 'GENODEM1HGN', 'GENODEM1HLH', 'DEUTDEDW450', 'DEUTDEDW454', 'DEUTDEDW456', 'DEUTDEDW453', 'DEUTDEDW451', 'DEUTDEDB450', 'DEUTDEDB454', 'DEUTDEDB453', 'DEUTDEDB456', 'DEUTDEDB451', 'DRESDEFF450', 'WELADED1WTN', 'WELADED1WET', 'SPSHDE31XXX', 'GENODEM1WTN', 'GENODEM1BFG', 'GENODEM1SPO', 'WELADED1GEV', 'WELADED1ENE', 'WELADED1SLM', 'GENODEM1ALA', 'WELADED1LSD', 'WELADED1PLB', 'WELADED1KMZ', 'GENODEM1LHA', 'GENODEM1KIE', 'GENODEM1MOM', 'WELADED1SIE', 'WELADED1BUB', 'WELADED1FRE', 'WELADED1HIL', 'WELADED1SMB', 'WELADED1BEB', 'GENODEM1SNS', 'GENODEM1FRF', 'GENODEM1SMA', 'GENODEM1BB1', 'DEUTDEDB460', 'DEUTDEDB962', 'DEUTDEDB963', 'DEUTDEDB463', 'DEUTDEDB469', 'DEUTDEDB466', 'DEUTDEDB461', 'DEUTDEDB516', 'DEUTDEDB470', 'DEUTDEDB967', 'DEUTDEDB471', 'DEUTDEDB966', 'DEUTDEDB964', 'DEUTDEDB465', 'DEUTDEDB462', 'DEUTDEDB965', 'DEUTDEDB464', 'DEUTDEDK460', 'DEUTDEDK461', 'DEUTDEDK466', 'DEUTDEDK463', 'DEUTDEDK516', 'DEUTDEDK468', 'DEUTDEDK467', 'DEUTDEDK470', 'DEUTDEDK465', 'DEUTDEDK474', 'DEUTDEDK471', 'DEUTDEDK469', 'DEUTDEDK462', 'DEUTDEDK473', 'DEUTDEDK464', 'DEUTDEDK475', 'DEUTDEDK472', 'DRESDEFF460', 'WELADED1OPE', 'WELADED1FTR', 'WELADED1ALK', 'GENODEM1OLP', 'GENODEM1GLG', 'GENODEM1WDD', 'GENODEM1HUL', 'WELADED1MES', 'WELADED1BST', 'GENODEM1SRL', 'GENODEM1ANO', 'GENODEM1RET', 'WELADED1ARN', 'GENODEM1NEH', 'DEUTDEDW466', 'DEUTDEDW467', 'DEUTDEDW468', 'DEUTDEDB961', 'DEUTDEDB468', 'DEUTDEDB467', 'DEUTDEDWP03', 'DEUTDEDBP03', 'MARKDEF1470', 'WELADED1PBN', 'WELADED1HXB', 'WELADED1DEL', 'DGPBDE3MXXX', 'DGPBDE3MALT', 'DGPBDE3MDRI', 'DGPBDE3MLIP', 'DGPBDE3MBRA', 'DGPBDE3MBUR', 'DGPBDE3MDEL', 'DGPBDE3MHOV', 'DGPBDE3MHOX', 'DGPBDE3MWAR', 'DGPBDE3MSTE', 'DGPBDE3MSAL', 'DGPBDE3MDTM', 'DGPBDE3MHBM', 'DGPBDE3MLAG', 'DGPBDE3MLEM', 'DGPBDE3MOER', 'DGPBDE3MMND', 'DGPBDE3MEPW', 'GENODEM1EWB', 'GENODEM1BKC', 'GENODEM1WNH', 'GENODEM1BUS', 'GENODEM1WDE', 'GENODEM1DLB', 'GENODEM1STM', 'GENODEM1WAH', 'GENODEM1BOT', 'DEUTDEDB472', 'DEUTDEDB473', 'DEUTDEDB474', 'DEUTDEDB475', 'DEUTDEDB958', 'DEUTDE3B472', 'DEUTDE3B475', 'DEUTDE3B473', 'DEUTDE3B451', 'DEUTDE3B474', 'GENODEM1WBG', 'WELADE3LXXX', 'WELADED1BLO', 'DEUTDE3B476', 'DEUTDE3B450', 'DEUTDE3B477', 'DEUTDE3B478', 'DEUTDE3B453', 'DEUTDE3B452', 'DEUTDEDB476', 'DEUTDEDB477', 'DEUTDEDB957', 'DEUTDEDB959', 'DEUTDEDB960', 'DEUTDEDB478', 'DEUTDE3BP04', 'DEUTDEDBP04', 'GENODEM1OLB', 'WELADED1GTL', 'WELADED1RTG', 'WELADED1VSM', 'WELADED1WDB', 'GENODEM1GTL', 'VBGTDE3MXXX', 'GENODEM1CLL', 'GENODEM1HWI', 'GENODEM1MFD', 'GENODEM1RNE', 'GENODEM1VMD', 'DRESDEFF478', 'MARKDEF1480', 'HYVEDEMM344', 'HAUKDEFFXXX', 'LAMPDEDDXXX', 'DGPBDE3MBVW', 'SPBIDE3BXXX', 'WELADED1HAW', 'GENODEM1BIE', 'GENODEM1HLW', 'GENODEM1SHS', 'DEUTDE3BXXX', 'DEUTDE3B483', 'DEUTDE3B486', 'DEUTDEDBBIE', 'DEUTDEDB483', 'DEUTDEDB486', 'DEUTDEDB413', 'DEUTDEDB480', 'DEUTDEDB484', 'DEUTDEDB485', 'DEUTDEDB487', 'DEUTDEDB489', 'DEUTDEDB492', 'DEUTDEDB481', 'DEUTDEDB488', 'DEUTDE3B480', 'DEUTDE3B484', 'DEUTDE3B489', 'DEUTDE3B487', 'DEUTDE3B413', 'DEUTDE3B481', 'DEUTDE3B492', 'DRESDEFF480', 'DRESDEFFI19', 'WELADED1LEM', 'GENODEM1BSU', 'WELADED1MIN', 'WELADED1RHD', 'WELADED1OEH', 'WELADED1PWF', 'GENODEM1MPW', 'GENODEM1MND', 'GENODEM1STR', 'GENODEM1EPW', 'DEUTDEDB490', 'DEUTDEDB491', 'DEUTDEDB493', 'DEUTDEDB494', 'DEUTDEDB495', 'DEUTDE3B490', 'DEUTDE3B491', 'DEUTDE3B494', 'DEUTDE3B493', 'DEUTDE3B495', 'DRESDEFF491', 'GENODEM1LUB', 'GENODEM1SNA', 'WLAHDE44XXX', 'GENODEM1HFV', 'MARKDEF1500', 'AKBKDEFFXXX', 'FCBKDEFFXXX', 'AARBDE5W500', 'INGDDEFFXXX', 'DEGUDEFFXXX', 'BOFADEFXXXX', 'BOFADEFXVAM', 'ALTEDEFAXXX', 'JTBPDEFFXXX', 'WUIDDEF1XXX', 'BHFBDEFF500', 'KFWIDEFFXXX', 'LAREDEFFXXX', 'FBHLDEFFXXX', 'BCITDEFFXXX', 'INGBDEFFXXX', 'FFBKDEFFKRN', 'FFBKDEFFTHK', 'HCSEDEF1XXX', 'DEFFDEFFXXX', 'GMGGDE51XXX', 'CARDDEFFXXX', 'PSADDEF1XXX', 'BPNDDE52XXX', 'PARBDEFFXXX', 'DWPBDEFFXXX', 'ESBKDEFFXXX', 'TRODDEF1XXX', 'OPENDEFFXXX', 'ABOCDEFFXXX', 'COBADEFFPAR', 'COBADEFFVIE', 'COBADEFFMIL', 'COBADEFFAMS', 'COBADEFFBRU', 'COBADEFFMAD', 'COBADEFFNYC', 'COBADEFFSGP', 'COBADEFFLDN', 'COBADEFFZUR', 'COBADEFFPRA', 'COBADEFFMOS', 'COBADEFFHBG', 'COBADEF1BRS', 'HELADEFFXXX', 'HELADEF1822', 'DGZFDEFFXXX', 'GENODE55XXX', 'GENODEFFXXX', 'GENODEF1VK1', 'GENODEF1VK2', 'GENODEF1VK3', 'GENODEF1VK4', 'GENODEF1VK6', 'GENODEF1VK7', 'GENODEF1VK8', 'GENODEF1VK9', 'GENODEF1V20', 'GENODEF1V21', 'GENODEF1V22', 'GENODEF1V23', 'GENODEF1V24', 'GENODEF1V25', 'GENODEFFBRO', 'GENODE51OBU', 'GENODE51ABO', 'GENODE51GRC', 'GENODE51EGE', 'GENODE51ERB', 'GENODE51GWB', 'GENODE51HUT', 'GENODE51KIF', 'GENODE51BH1', 'GENODE51SWB', 'GENODE51WWI', 'DEUTDEFFXXX', 'DEUTDEFF500', 'DEUTDEFF542', 'DEUTDEFF541', 'DEUTDEFF504', 'DEUTDEFF503', 'DEUTDEFF540', 'DEUTDEFFSIP', 'DEUTDEDBFRA', 'DEUTDEDB500', 'DEUTDEDB503', 'DEUTDEDB535', 'DEUTDEDB536', 'DEUTDEDB504', 'DEUTDEDBP25', 'DEUTDEFFS25', 'DEUTDEDBEW1', 'DEUTDEDBEW2', 'DEUTDEDBEW3', 'DEUTDEDBEW4', 'DEUTDEDBEW5', 'DEUTDEFF502', 'DEUTDEFF543', 'DEUTDEDB502', 'DEUTDEDB537', 'DEUTDE5XXXX', 'DRESDEFFI39', 'DRESDEFFI40', 'DRESDEFF516', 'DRESDEFF522', 'DRESDEFFLDG', 'DRESDEFFBSP', 'DRESDEFFI41', 'DRESDEFFAVB', 'DRESDEFFI49', 'DRESDEFFJ08', 'DRESDEFFJ09', 'DRESDEFFJ10', 'DRESDEFFJ11', 'DRESDEFFFCO', 'DRESDEFFI42', 'DRESDEFF500', 'DRESDEFF502', 'DRESDEFFMBP', 'DRESDEFFI01', 'GENODEF1S12', 'GENODEF1P06', 'GENODE51BH2', 'GENODE51KEL', 'GENODE51USI', 'GENODE51RUS', 'GENODE51GAA', 'GENODE51KBH', 'ICBKDEFFXXX', 'AUSKDEFFXXX', 'NATXDEFFXXX', 'SCBLDEFXXXX', 'FBGADEF1XXX', 'CHASDEFXXXX', 'CHASDEFXVR1', 'JPMGDEFFXXX', 'MNBIDEF1XXX', 'MAIFDEFFXXX', 'ICICDEFFXXX', 'DELBDE33XXX', 'CRESDE55XXX', 'COMMDEFFXXX', 'BMPBDEF2XXX', 'TVBADEFFXXX', 'DOBADEF1XXX', 'BPKODEFFXXX', 'NBPADEFFXXX', 'MEFIDEMM501', 'UBSWDEFFXXX', 'ICBVDEFFXXX', 'FFVBDEFFXXX', 'GENODE51FHC', 'GENODE51FGH', 'RABODEFFTAR', 'RABODEFFXXX', 'PRCBDEFFXXX', 'CITIDEFFXXX', 'SMHBDEFFXXX', 'INVODEF2XXX', 'HVBKDEFFXXX', 'BOFSDEF1XXX', 'CAIXDEFFXXX', 'ABCADEFFXXX', 'METZDEFFXXX', 'PLFGDE5AXXX', 'PLFGDE5AIKB', 'KTAGDEFFXXX', 'DLFGDE51XXX', 'BARCDEFFXXX', 'PCBCDEFFXXX', 'OWHBDEFFXXX', 'HYVEDEMM430', 'BSCHDEFFXXX', 'BCMADEFFXXX', 'PICTDEFFXXX', 'FTSBDEFAXXX', 'SBINDEFFXXX', 'MHBFDEFFXXX', 'RAISDEFFXXX', 'IRVTDEFXXXX', 'BCDMDEF1XXX', 'SEPBDEFFXXX', 'BNYMDEF1XXX', 'PANXDEF2XXX', 'MARKDEFFXXX', 'SMBCDEFFXXX', 'HYVEDEMM467', 'FDDODEMMXXX', 'GENODE51CRO', 'HELADEF1OFF', 'GENODE51OF2', 'GENODE51OBH', 'DEUTDEFF505', 'DEUTDEFF507', 'DEUTDEFF549', 'DEUTDEFF546', 'DEUTDEFF548', 'DEUTDEFF545', 'DEUTDEFF544', 'DEUTDEFF547', 'DEUTDEFF550', 'DEUTDEDB505', 'DEUTDEDB538', 'DEUTDEDB539', 'DEUTDEDB529', 'DEUTDEDB528', 'DEUTDEDB527', 'DEUTDEDB507', 'DEUTDEDB526', 'DEUTDEDB525', 'DRESDEFF505', 'DRESDEFFJ12', 'GENODE51OF1', 'GENODE51DRE', 'HELADEF1HAN', 'HELADEF1SLS', 'GENODEF1LSR', 'GENODE51NIH', 'GENODEF1BKO', 'RBMFDEF1XXX', 'GENODEF1RDB', 'DEUTDEFF506', 'DEUTDEDB506', 'DRESDEFF506', 'DRESDEFFJ13', 'GENODEF1HUV', 'DZBMDEF1XXX', 'GENODE51SEL', 'HELADEF1GEL', 'GENODE51BUE', 'GENODEF1BIR', 'DRESDEFF524', 'GENODE51GEL', 'GENODE51BIV', 'GENODE51WBH', 'BBSPDE6KXXX', 'HYVEDEMM487', 'MKGMDE51XXX', 'HELADEFF508', 'HELADEF1DAS', 'HELADEF1ERB', 'HELADEF1GRG', 'HELADEF1DIE', 'GENODE51BKZ', 'GENODE51ABH', 'GENODE51WGH', 'GENODE51GRI', 'GENODE51REI', 'GENODE51SHM', 'GENODE51GIN', 'GENODE51MIC', 'GENODE51MWA', 'GENODE51EPT', 'DEUTDEFF508', 'DEUTDEFF551', 'DEUTDEFF552', 'DEUTDEDB508', 'DEUTDEDB554', 'DEUTDEDB555', 'DEUTDEDBP26', 'DEUTDEFFS26', 'DRESDEFF508', 'DRESDEFFJ14', 'DRESDEFFJ15', 'GENODEF1VBD', 'HELADEF1BEN', 'HELADEF1HEP', 'GENODE51RBU', 'GENODE51GRM', 'GENODE51FHO', 'GENODE51ABT', 'DEUTDEFF509', 'DEUTDEFF519', 'DEUTDEDB509', 'DEUTDEDB519', 'AARBDE5WXXX', 'BHFBDEFF510', 'HYVEDEMM478', 'NASSDE55XXX', 'PULSDE5WXXX', 'DEUTDEFF510', 'DEUTDEFF512', 'DEUTDEFF514', 'DEUTDEDB510', 'DEUTDEDB512', 'DEUTDEDB514', 'DRESDEFF510', 'DRESDEFFJ16', 'DRESDEFFJ17', 'DRESDEFFI20', 'WIBADE5WXXX', 'GENODE51RGG', 'VRBUDE51XXX', 'HELADEF1LIM', 'HELADEF1WEI', 'GENODE51LDD', 'DEUTDEFF511', 'DEUTDEDB511', 'DRESDEFF511', 'GENODE51LIM', 'GENODE51SBH', 'GENODE51WEM', 'NZFMDEF1XXX', 'SOGEDEFFXXX', 'SGSSDEFFXXX', 'NATXDEFPXXX', 'ESSEDEFFXXX', 'SIHRDEH1FFM', 'TCZBDEFFXXX', 'BRASDEFFXXX', 'MSFFDEFXXXX', 'MSFFDEFXCND', 'ARABDEFFXXX', 'HELADEF1TSK', 'MARKDEF1513', 'SKGIDE5FXXX', 'HELADEF1GRU', 'HELADEF1LAU', 'GENODE51HHE', 'DEUTDEFF513', 'DEUTDEDB513', 'DRESDEFF513', 'DRESDEFFJ18', 'VBMHDE5FXXX', 'BOFADEFFXXX', 'BKCHDEFFXXX', 'BOURDEFFXXX', 'MIBEDEFFXXX', 'BAERDEF1XXX', 'GOLDDEFFXXX', 'GOLDDEFBXXX', 'SABCDEFFXXX', 'HELADEF1WET', 'DEUTDEFF515', 'DEUTDEDB515', 'DRESDEFF515', 'GENODE51WBO', 'HELADEF1DIL', 'GENODE51DIL', 'GENODE51HER', 'HELADEF1BAT', 'GENODE51BIK', 'HELADEF1FRI', 'GENODEF1BVB', 'GENODE51BUT', 'GENODE51REW', 'GENODE51OBM', 'GENODE51ULR', 'GENODE51HSH', 'GENODE51FEL', 'GENODE51LB1', 'HELADEFF520', 'HELADEF1KAS', 'HELADEF1BOR', 'HELADEF1FEL', 'HELADEF1GRE', 'HELADEF1MEG', 'HELADEF1SWA', 'GENODEFF520', 'GENODEF1KS2', 'GENODEF1EK1', 'GENODEF1BOR', 'GENODEF1GUB', 'GENODEF1HRV', 'GENODEF1SPB', 'GENODEF1WOH', 'GENODEF1BTA', 'GENODEF1BHN', 'GENODEF1GMD', 'GENODEF1BUR', 'GENODEF1VLM', 'GENODEF1FBK', 'DEUTDEFF520', 'DEUTDEFF523', 'DEUTDEFF524', 'DEUTDEDB520', 'DEUTDEDB523', 'DEUTDEDB524', 'DEUTDEFF521', 'DEUTDEDB521', 'DRESDEFF520', 'DRESDEFFJ19', 'GENODE51KS1', 'HELADEF1ESW', 'GENODEF1ESW', 'DEUTDEFF522', 'DEUTDEDB522', 'HELADEF1KOR', 'GENODEF1KBW', 'RBAGDEF1XXX', 'RBAGDEF1CMI', 'KOEXDEFAXXX', 'BSUIDEFFXXX', 'SHBKDEFFXXX', 'ABGRDEFFXXX', 'SECGDEFFXXX', 'CMCIDEF1XXX', 'HELADEF1FDS', 'HELADEF1SLU', 'GENODE51FUL', 'GENODEF1HUE', 'GENODE51SLU', 'GENODEF1GLU', 'GENODEF1PBG', 'GENODEF1FLN', 'DEUTDEFF530', 'DEUTDEFF531', 'DEUTDEFF534', 'DEUTDEDB530', 'DEUTDEDB531', 'DEUTDEDB534', 'DEUTDEDBP27', 'DEUTDEFFS27', 'DRESDEFF530', 'GENODE51ALS', 'GENODE51AGR', 'HELADEF1HER', 'GENODEF1HFA', 'GENODEF1BEB', 'GENODEF1RAW', 'GENODEF1HNT', 'GENODEF1ROH', 'DEUTDEFF532', 'DEUTDEDB518', 'DRESDEFF532', 'GENODE51BHE', 'HELADEF1MAR', 'GENODEF1EBG', 'DEUTDEFF533', 'DEUTDEDB533', 'DRESDEFF533', 'DRESDEFF568', 'HYVEDEMM482', 'SCRUDE51XXX', 'MALADE51KLS', 'MALADE51KLK', 'MALADE51KUS', 'MALADE51LAS', 'MALADE51ROK', 'GENODE61LAN', 'GENODE61ALB', 'DEUTDEDB540', 'DEUTDEDB541', 'DEUTDESM540', 'DEUTDESM541', 'DRESDEFF540', 'GENODE61KL1', 'GENODE61LEK', 'GENODE61OB1', 'GENODE61GLM', 'HYVEDEMM485', 'MALADE51SWP', 'GENODE61ROA', 'DEUTDEDB542', 'DEUTDEDB543', 'DEUTDESM542', 'DEUTDESM543', 'DRESDEFF542', 'GENODE61DAH', 'MARKDEF1545', 'HYVEDEMM483', 'LUHSDE6AXXX', 'MALADE51LUH', 'GENODE61LBS', 'DEUTDEDB545', 'DEUTDEDB549', 'DEUTDEDB544', 'DEUTDEDB550', 'DEUTDEDB547', 'DEUTDEDB553', 'DEUTDESM545', 'DEUTDESM544', 'DEUTDESM549', 'DEUTDESM550', 'DEUTDESM547', 'DEUTDESM553', 'DRESDEFF545', 'HYVEDEMM620', 'MALADE51DKH', 'GENODE61FSH', 'GENODE61FHR', 'DEUTDEDB546', 'DEUTDEDB552', 'DEUTDEDB548', 'DEUTDESM546', 'DEUTDESM552', 'DEUTDESM548', 'DRESDEFF546', 'GENODE61DUW', 'MALADE51SPY', 'GENODE61SPE', 'SOLADES1SUW', 'MALADE51KAD', 'GENODE61EDH', 'GENODE61HXH', 'GENODE61SUW', 'GENODE61BZA', 'MARKDEF1550', 'AARBDE5WDOM', 'AARBDE5W550', 'AARBDE5WCLE', 'ISBRDE55XXX', 'BHFBDEFF550', 'BKMZDE51XXX', 'HYVEDEMM486', 'BFSWDE33MNZ', 'IMMODE5MXXX', 'SUFGDE51XXX', 'CPLADE55XXX', 'SOLADEST550', 'MALADE51MNZ', 'GENODE51MZ4', 'GENODE51MZ2', 'GENODE51MZ6', 'GENODE51BUD', 'GENODE51HDS', 'GENODE51NIS', 'DEUTDEDBMAI', 'DEUTDEDB563', 'DEUTDEDB561', 'DEUTDEDB551', 'DEUTDE5MXXX', 'DEUTDE5M552', 'DEUTDE5M550', 'DEUTDE5M551', 'DEUTDEDBP29', 'DEUTDE5MP29', 'DRESDEFF550', 'DRESDEFFJ20', 'DRESDEFFJ21', 'DRESDEFF555', 'GENODEF1S01', 'GENODE61AZY', 'MALADE51EMZ', 'GENODED1PA4', 'MVBMDE55XXX', 'MALADE51WOR', 'GENODE51AHM', 'GENODE51BEC', 'GENODE61WO1', 'HYVEDEMM515', 'MALADE51KRE', 'MALADE51SIM', 'GENODED1KSL', 'GENODED1KHK', 'GENODED1RBO', 'DEUTDEDB560', 'DEUTDE5M560', 'GENODE51KRE', 'BILADE55XXX', 'GENODED1FIN', 'DEUTDEDB562', 'DEUTDE5M562', 'GENODE51IDO', 'MARKDEF1570', 'HYVEDEMM401', 'MKBKDE51XXX', 'OYAKDE5KXXX', 'DEBKDE51XXX', 'MALADE51KOB', 'MALADE51BMB', 'MALADE51COC', 'GENODEDD570', 'GENODE51NWA', 'GENODED1MKA', 'GENODED1LUH', 'GENODED1MOK', 'GENODED1KAI', 'GENODED1ASN', 'GENODED1UMO', 'GENODED1SRH', 'GENODED1WLG', 'GENODED1IRR', 'GENODED1MBA', 'DEUTDEDB570', 'DEUTDEDB572', 'DEUTDEDB571', 'DEUTDEDB577', 'DEUTDEDB573', 'DEUTDEDB578', 'DEUTDE5M570', 'DEUTDE5M572', 'DEUTDE5M573', 'DEUTDE5M577', 'DEUTDE5M571', 'DEUTDE5M578', 'DEUTDEDBP28', 'DEUTDE5MP28', 'DRESDEFF570', 'GENODE51KOB', 'GENODEF1P12', 'GENODE51MON', 'GENODE51DIE', 'GENODE51ARZ', 'MALADE51AKI', 'GENODED1GBS', 'GENODED1NFB', 'GENODE51DAA', 'GENODE51HAM', 'GENODE51WW1', 'MALADE51NWD', 'GENODED1NWD', 'GENODED1MRW', 'DEUTDEDB574', 'DEUTDEDB575', 'DEUTDEDB576', 'DEUTDEDB579', 'DEUTDE5M574', 'DEUTDE5M575', 'DEUTDE5M576', 'DEUTDE5M579', 'MALADE51MYN', 'GENODED1KEH', 'GENODED1MPO', 'MALADE51AHR', 'GENODED1BNA', 'GENODED1GRO', 'HYVEDEMM437', 'TRISDE55XXX', 'GENODED1TVB', 'GENODED1PA3', 'GENODED1SRB', 'GENODED1MLW', 'GENODED1HWM', 'DEUTDEDB585', 'DEUTDEDB580', 'DEUTDEDB586', 'DEUTDE5M585', 'DEUTDE5M590', 'DEUTDE5M586', 'DRESDEFF585', 'GENODEF1P21', 'MALADE51BIT', 'MALADE51DAU', 'GENODED1BIT', 'GENODED1WSC', 'GENODED1OSE', 'GENODED1PRU', 'MALADE51BKS', 'GENODED1WTL', 'GENODED1BPU', 'DEUTDEDB587', 'DEUTDEDB589', 'DEUTDEDB588', 'DEUTDE5M587', 'DEUTDE5M589', 'DEUTDE5M588', 'MARKDEF1590', 'PBNKDEFF011', 'PBNKDEFF012', 'PBNKDEFF013', 'PBNKDEFF014', 'PBNKDEFF015', 'PBNKDEFF016', 'PBNKDEFF017', 'PBNKDEFF018', 'PBNKDEFF019', 'PBNKDEFF021', 'PBNKDEFF022', 'PBNKDEFF023', 'PBNKDEFF024', 'PBNKDEFF025', 'PBNKDEFF026', 'PBNKDEFF027', 'PBNKDEFF028', 'PBNKDEFF029', 'PBNKDEFF031', 'PBNKDEFF032', 'PBNKDEFF033', 'PBNKDEFF034', 'PBNKDEFF035', 'PBNKDEFF036', 'PBNKDEFF037', 'PBNKDEFF038', 'PBNKDEFF039', 'PBNKDEFF040', 'PBNKDEFF041', 'PBNKDEFF042', 'PBNKDEFF044', 'PBNKDEFF045', 'PBNKDEFF047', 'PBNKDEFF048', 'PBNKDEFF049', 'PBNKDEFF051', 'PBNKDEFF052', 'PBNKDEFF053', 'PBNKDEFF054', 'PBNKDEFF055', 'PBNKDEFF056', 'PBNKDEFF057', 'PBNKDEFF058', 'PBNKDEFF059', 'PBNKDEFF061', 'PBNKDEFF062', 'PBNKDEFF063', 'PBNKDEFF064', 'PBNKDEFF065', 'PBNKDEFF068', 'PBNKDEFF069', 'PBNKDEFF071', 'PBNKDEFF072', 'PBNKDEFF073', 'PBNKDEFF074', 'SIKBDE55XXX', 'HYVEDEMM432', 'MEGHDE81XXX', 'SALADE55XXX', 'SAKSDE55XXX', 'SALADE51VKS', 'DEUTDE5M555', 'DEUTDEDB595', 'DEUTDEDB590', 'DRESDEFF590', 'GENODEF1P19', 'GENODE51SB2', 'GENODE51NOH', 'SABADE5SXXX', 'GENODE51SLS', 'SALADE51WND', 'SALADE51NKS', 'GENODE51WEN', 'GENODE51BEX', 'HYVEDEMM838', 'KRSADE55XXX', 'MERZDE55XXX', 'GENODE51SLF', 'GENODE51UBH', 'GENODE51DSA', 'GENODE51LOS', 'GENODE51LEB', 'SALADE51HOM', 'GENODE51MBT', 'MARKDEF1600', 'AARBDE5W600', 'LKBWDE6K600', 'SOLADEST601', 'SCHWDESSXXX', 'HYVEDEMM473', 'MEBEDE6SDCB', 'BHBADES1XXX', 'ELGEDES1XXX', 'CPLUDES1XXX', 'CPLUDES1666', 'AKBADES1XXX', 'ISBKDEFXSTU', 'TRUFDE66XXX', 'BSWLDE61XXX', 'IBKBDES1XXX', 'SOLADESTXXX', 'SOLADEST600', 'SOLADEST493', 'SOLADEST880', 'SOLADEST447', 'SOLADEST829', 'SOLADEST457', 'SOLADEST490', 'SOLADEST437', 'SOLADEST864', 'SOLADEST454', 'SOLADEST896', 'SOLADEST836', 'SOLADEST484', 'SOLADEST487', 'SOLADEST428', 'GENODESGXXX', 'GENODESTXXX', 'GENODES1UTV', 'GENODES1ECH', 'GENODES1MCH', 'GENODES1DMS', 'GENODES1RBA', 'GENODES1RVG', 'GENODES1RSF', 'GENODES1SAA', 'GENODES1AID', 'GENODES1GWS', 'GENODES1BPF', 'GENODES1RGR', 'GENODES1RDI', 'GENODES1ERM', 'GENODES1RBS', 'GENODES1RIN', 'GENODES1MDH', 'GENODES1RMA', 'GENODES1RRI', 'GENODES1REH', 'GENODES1RRG', 'GENODES1EHN', 'GENODES1DEH', 'GENODES1DBE', 'GENODES1KIB', 'GENODES1UHL', 'GENODES1MBI', 'GENODES1OED', 'GENODES1RFS', 'GENODES1RVS', 'GENODES1OTT', 'GENODES1RRE', 'GENODES1WBB', 'GENODES1RKH', 'GENODES1DEA', 'GENODES1ROW', 'GENODES1VMT', 'GENODES1SCA', 'GENODES1RNS', 'GENODES1LOC', 'GENODES1RWN', 'GENODES1NUF', 'GENODES1HAR', 'GENODES1RVA', 'GENODES1SBB', 'GENODES1RIH', 'GENODES1EHZ', 'GENODES1EHB', 'GENODES1ABR', 'GENODES1BRZ', 'GENODES1RWA', 'GENODES1SLA', 'GENODES1MEH', 'GENODES1RGF', 'GENODES1IBR', 'GENODES1ROF', 'GENODES1FAN', 'GENODES1BBO', 'GENODES1HHB', 'GENODES1RHB', 'GENODES1RMO', 'GENODES1URB', 'GENODES1DHB', 'GENODES1VAI', 'GENODES1FED', 'GENODES1ROG', 'GENODES1PLE', 'GENODES1RUW', 'GENODES1REM', 'GENODES1ERL', 'GENODES1VBG', 'GENODES1BHB', 'GENODES1BGH', 'GENODES1TUN', 'GENODES1BOE', 'GENODES1RMH', 'DEUTDEDBSTG', 'DEUTDEDB602', 'DEUTDEDB647', 'DEUTDEDB609', 'DEUTDEDB624', 'DEUTDEDB605', 'DEUTDESSXXX', 'DEUTDESS602', 'DEUTDESS624', 'DEUTDESS609', 'DEUTDESS605', 'DEUTDESS647', 'DEUTDESSP13', 'DEUTDEDBP13', 'DRESDEFF600', 'DRESDEFF608', 'DRESDEFF609', 'DRESDEFFI50', 'DRESDEFFI54', 'DRESDEFFI57', 'DRESDEFFI58', 'DRESDEFFI21', 'VOBADESSXXX', 'GENODES1ZUF', 'SWBSDESSXXX', 'GENODEF1S02', 'GENODEF1P20', 'BHFBDEFF600', 'BFSWDE33STG', 'SOLADES1WBN', 'GENODES1FBB', 'GENODES1WNS', 'GENODES1RWT', 'GENODES1KOR', 'GENODES1KRN', 'DEUTDEDB606', 'DEUTDESS606', 'GENODES1VWN', 'GENODES1VBK', 'HYVEDEMM858', 'BBKRDE6BXXX', 'GENODES1WES', 'DRESDEFF601', 'GENODES1BBV', 'GENODES1LEO', 'GENODES1VBH', 'GENODES1MAG', 'WBAGDE61XXX', 'WBAGDEA1XXX', 'HYVEDEMM860', 'SABUDES1XXX', 'SOLADES1LBG', 'GENODES1EGL', 'GENODES1AMT', 'DEUTDEDB604', 'DEUTDEDB608', 'DEUTDEDB635', 'DEUTDEDB617', 'DEUTDEDB623', 'DEUTDEDB648', 'DEUTDESS604', 'DEUTDESS635', 'DEUTDESS617', 'DEUTDESS623', 'DEUTDESS608', 'DEUTDESS648', 'DRESDEFF604', 'GENODES1LBG', 'GENODES1VBB', 'GENODES1GHB', 'GENODES1WIM', 'GENODES1RCW', 'DEUTDEDB659', 'DEUTDESS659', 'MARBDE6GXXX', 'GOPSDE6GXXX', 'GOPSDE6G612', 'GENODES1VGP', 'DEUTDEDB610', 'DEUTDEDB627', 'DEUTDEDB618', 'DEUTDESS610', 'DEUTDESS618', 'DEUTDESS627', 'DRESDEFF610', 'GENODES1DGG', 'HYVEDEMM859', 'ESSLDE66XXX', 'GENODES1NHB', 'DEUTDEDB611', 'DEUTDEDB619', 'DEUTDEDB612', 'DEUTDEDB626', 'DEUTDESS611', 'DEUTDESS612', 'DEUTDESS619', 'DEUTDESS626', 'DRESDEFF611', 'GENODES1ESS', 'GENODES1VBP', 'GENODES1TEC', 'GENODES1HON', 'GENODES1WLF', 'GENODES1BBF', 'DRESDEFF612', 'GENODES1NUE', 'GENODES1HEU', 'GENODES1RML', 'DEUTDEDB613', 'DEUTDEDB614', 'DEUTDEDB637', 'DEUTDEDB638', 'DEUTDEDB639', 'DEUTDEDB615', 'DEUTDEDB633', 'DEUTDEDB616', 'DEUTDESS613', 'DEUTDESS639', 'DEUTDESS638', 'DEUTDESS614', 'DEUTDESS615', 'DEUTDESS616', 'DEUTDESS637', 'DEUTDESS633', 'GENODES1VGD', 'GENODES1WEL', 'HYVEDEMM272', 'OASPDE6AXXX', 'DRESDEFF614', 'GENODES1AAV', 'GENODES1ELL', 'HOEBDE61XXX', 'HEISDE66XXX', 'GENODES1VOS', 'GENODES1BIA', 'GENODES1VFT', 'GENODES1VLS', 'DEUTDEDB620', 'DEUTDEDB628', 'DEUTDEDB621', 'DEUTDEDB629', 'DEUTDEDB622', 'DEUTDESS620', 'DEUTDESS621', 'DEUTDESS629', 'DEUTDESS622', 'DEUTDESS628', 'DRESDEFF620', 'GENODES1VHN', 'GENODES1VBR', 'GENODES1VMN', 'GENODES1VHL', 'BSHHDE61XXX', 'SOLADES1SHA', 'SOLADES1KUN', 'DRESDEFF622', 'GENODES1SHA', 'GENODES1CRV', 'GENODES1VVT', 'MARKDEF1630', 'HYVEDEMM461', 'SOLADES1ULM', 'GENODES1LBK', 'DEUTDEDB630', 'DEUTDEDB631', 'DEUTDEDB632', 'DEUTDESS630', 'DEUTDESS631', 'DEUTDESS632', 'DRESDEFF630', 'DRESDEFFI59', 'ULMVDE66XXX', 'GENODES1EHI', 'GENODES1BLA', 'GENODES1LAI', 'HYVEDEMM271', 'SOLADES1HDH', 'GENODES1HDH', 'MARKDEF1640', 'HYVEDEMM374', 'SOLADES1REU', 'GENODES1STW', 'DEUTDEDB640', 'DEUTDEDB646', 'DEUTDEDB634', 'DEUTDEDB643', 'DEUTDEDB636', 'DEUTDEDB645', 'DEUTDEDB641', 'DEUTDESS640', 'DEUTDESS642', 'DEUTDESS641', 'DEUTDESS644', 'DEUTDESS645', 'DEUTDESS643', 'DEUTDESS646', 'DEUTDESSP14', 'DEUTDEDBP14', 'DRESDEFF640', 'VBRTDE6RXXX', 'GENODES1MTZ', 'GENODES1MUN', 'SOLADES1TUB', 'GENODES1AMM', 'GENODES1RHK', 'GENODES1VMO', 'GENODES1VHZ', 'DRESDEFF641', 'GENODES1TUE', 'GENODES1NAG', 'GENODES1HOR', 'SOLADES1RWL', 'SOLADES1FDS', 'GENODES1BAI', 'GENODES1MMO', 'GENODES1PGW', 'GENODES1VDS', 'GENODES1VRW', 'GENODES1FDS', 'GENODES1VDL', 'GENODES1SBG', 'GENODES1TRO', 'SOLADES1TUT', 'GENODES1RDH', 'DRESDEFF643', 'GENODES1TUT', 'HYVEDEMM588', 'SOLADES1RVB', 'GENODES1AUL', 'GENODES1RRV', 'GENODES1SAG', 'DEUTDEDB650', 'DEUTDEDB651', 'DEUTDEDB652', 'DEUTDEDB654', 'DEUTDEDB649', 'DEUTDEDB657', 'DEUTDEDB658', 'DEUTDESS650', 'DEUTDESS651', 'DEUTDESS658', 'DEUTDESS657', 'DEUTDESS654', 'DEUTDESS652', 'DEUTDESS649', 'DRESDEFF650', 'GENODES1LEU', 'GENODES1BWB', 'GENODES1VWG', 'GENODES1WAN', 'GENODES1VAH', 'GENODES1SLG', 'IBBFDE81XXX', 'GENODES1GMB', 'GENODES1OTE', 'DRESDEFF651', 'GENODES1VFN', 'GENODES1TET', 'SOLADES1SIG', 'SOLADES1BAL', 'GENODES1HBM', 'GENODES1WLB', 'GENODES1ONS', 'GENODES1GEI', 'DEUTDEDB653', 'DEUTDEDB655', 'DEUTDEDB603', 'DEUTDESS653', 'DEUTDESS655', 'DEUTDESS603', 'DRESDEFF653', 'GENODES1EBI', 'GENODES1BAL', 'GENODES1TAI', 'SBCRDE66XXX', 'GENODES1WAR', 'GENODES1ERO', 'GENODES1VBL', 'GENODES1VRR', 'MARKDEF1660', 'LKBWDE6KXXX', 'SOLADEST663', 'HYVEDEMM475', 'BFSWDE33KRL', 'SOLADEST660', 'KARSDE66XXX', 'SOLADES1ETT', 'GENODE6KXXX', 'GENODE61KA3', 'GENODE61RH2', 'GENODE61WGA', 'GENODE61EGG', 'GENODE61DET', 'GENODE61ELZ', 'GENODE61DAC', 'GENODE61KTH', 'DEUTDESM660', 'DEUTDESM661', 'DEUTDESM663', 'DEUTDESM664', 'DEUTDEDB660', 'DEUTDEDB663', 'DEUTDEDB661', 'DEUTDEDB664', 'DEUTDESMP12', 'DEUTDEDBP12', 'DRESDEFF660', 'GENODE61BBB', 'GENODEF1P10', 'GENODE61ETT', 'GENODE61KA1', 'SOLADES1BAD', 'SOLADES1BHL', 'GENODE61BHT', 'GENODE61ALR', 'DEUTDESM662', 'DEUTDESM667', 'DEUTDESM671', 'DEUTDESM665', 'DEUTDESM669', 'DEUTDEDB662', 'DEUTDEDB669', 'DEUTDEDB671', 'DEUTDEDB667', 'DEUTDEDB665', 'DRESDEFF662', 'VBRADE6KXXX', 'GENODE61ACH', 'GENODE61BHL', 'BRUSDE66XXX', 'GENODE61BTT', 'GENODE61ORH', 'FAITDE66XXX', 'SOLADES1OFG', 'SOLADES1GEB', 'SOLADES1HAL', 'SOLADES1KEL', 'SOLADES1WOF', 'DEUTDEDB968', 'DEUTDEDB970', 'DEUTDEDB969', 'DEUTDEDB971', 'DEUTDE6F664', 'DEUTDE6F665', 'DEUTDE6F666', 'DEUTDE6F667', 'GENODE61OG1', 'GENODE61APP', 'GENODE61KZT', 'SOLADES1RAS', 'GENODE61DUR', 'GENODE61IFF', 'PZHSDE66XXX', 'GENODE61NBT', 'GENODE61KBR', 'GENODE61NFO', 'GENODE61ERS', 'GENODE61KBS', 'DEUTDESM666', 'DEUTDESM677', 'DEUTDEDB666', 'DEUTDEDB677', 'DRESDEFF666', 'VBPFDE66XXX', 'GENODE61WIR', 'GENODE61KIR', 'GENODE61NEU', 'HYVEDEMM489', 'MANSDE66XXX', 'SOLADES1HOC', 'GENODE61MA3', 'DEUTDESMXXX', 'DEUTDESM676', 'DEUTDESM675', 'DEUTDESM673', 'DEUTDESM670', 'DEUTDEDBMAN', 'DEUTDEDB676', 'DEUTDEDB673', 'DEUTDEDB675', 'DEUTDEDB670', 'DRESDEFF670', 'DRESDEFFI60', 'DRESDEFFI61', 'DRESDEFFI22', 'GENODE61MA2', 'GENODE61WNM', 'HYVEDEMM479', 'MLPBDE61XXX', 'MLPBDE61001', 'SOLADES1HDB', 'GENODE61WIB', 'GENODE61LRO', 'DEUTDESM672', 'DEUTDESM674', 'DEUTDESM678', 'DEUTDEDB672', 'DEUTDEDB674', 'DEUTDEDB678', 'DRESDEFF672', 'GENODE61HD1', 'GENODE61HD3', 'GENODE61NGD', 'GENODE61SSH', 'GENODE61WIE', 'SOLADES1TBB', 'GENODE61WTH', 'SOLADES1MOS', 'GENODE61MOS', 'GENODE61BUC', 'GENODE61RNG', 'GENODE61LMB', 'MARKDEF1680', 'HYVEDEMM357', 'BKMADE61XXX', 'FRSPDE66XXX', 'SOLADES1HSW', 'SOLADES1BND', 'SOLADES1STB', 'SOLADES1STF', 'SOLADES1SCH', 'GENODE61IHR', 'GENODE61DEN', 'GENODE61WYH', 'GENODE61VOK', 'GENODE61GUN', 'DEUTDEDBFRE', 'DEUTDEDB681', 'DEUTDEDB685', 'DEUTDEDB689', 'DEUTDEDB687', 'DEUTDE6FXXX', 'DEUTDE6F681', 'DEUTDE6F685', 'DEUTDE6F687', 'DEUTDE6F689', 'DEUTDE6FP11', 'DEUTDEDBP11', 'DRESDEFF680', 'DRESDEFFI44', 'DRESDEFFI62', 'DRESDEFFJ22', 'GENODE61FR1', 'GENODEF1P07', 'GENODE61MHL', 'GENODE61EMM', 'GENODE61STF', 'DEUTDEDB682', 'DEUTDE6F682', 'GENODE61LAH', 'SKLODE66XXX', 'SOLADES1SFH', 'SOLADES1MGL', 'DEUTDEDB683', 'DEUTDEDB684', 'DEUTDEDB688', 'DEUTDEDB686', 'DEUTDEDB693', 'DEUTDEDB680', 'DEUTDEDB679', 'DEUTDE6F683', 'DEUTDE6F688', 'DEUTDE6F693', 'DEUTDE6F684', 'DEUTDE6F686', 'DEUTDE6F679', 'DEUTDE6F678', 'VOLODE66XXX', 'GENODE61SPF', 'SKHRDE6WXXX', 'GENODE61WUT', 'GENODE61BSK', 'GENODE61WT1', 'HYVEDEMM591', 'SOLADES1KNZ', 'SOLADES1REN', 'SOLADES1PFD', 'SOLADES1SAL', 'GENODE61UBE', 'DEUTDEDB690', 'DEUTDEDB691', 'DEUTDE6F690', 'DEUTDE6F691', 'GENODE61HAG', 'GENODE61PFD', 'HYVEDEMM590', 'SOLADES1SNG', 'SOLADES1ENG', 'SOLADES1STO', 'DEUTDEDB692', 'DEUTDEDB696', 'DEUTDE6F692', 'DEUTDE6F696', 'DRESDEFF692', 'GENODE61SIN', 'GENODE61RAD', 'GENODE61MES', 'MARKDEF1694', 'SOLADES1VSS', 'DEUTDEDB694', 'DEUTDEDB698', 'DEUTDEDB642', 'DEUTDEDB699', 'DEUTDEDB644', 'DEUTDEDB697', 'DEUTDE6F694', 'DEUTDE6F697', 'DEUTDE6F642', 'DEUTDE6F699', 'DEUTDE6F644', 'DEUTDE6F698', 'GENODE61VS1', 'GENODE61TRI', 'MARKDEF1700', 'AARBDE5W700', 'REBMDEMMXXX', 'REBMDEMM555', 'REBMDE7CXXX', 'REBMDEMMSCA', 'KHMIDEMMXXX', 'VONTDEM1XXX', 'BFWODE71XXX', 'SIBADEMMXXX', 'WEGBDE77XXX', 'BVDHDEMMXXX', 'ICRDDE71XXX', 'CLABDEM1XXX', 'VBANDEMMXXX', 'FLGMDE77XXX', 'SUSKDEM1XXX', 'DEPDDEMMXXX', 'FXBBDEM2XXX', 'EBSGDEMXXXX', 'EFSGDEM1XXX', 'CSHHDE71XXX', 'HERZDEM1XXX', 'TEZGDEB1XXX', 'TEZGDEB1001', 'TEZGDEB1002', 'TEZGDEB1003', 'PAGMDEM1XXX', 'HYVEDEMMXXX', 'WKVBDEM1XXX', 'BFSWDE33MUE', 'BCITDEFFMUC', 'HYVEDEMM418', 'HYVEDEMM643', 'FUBKDE71MUC', 'MEFIDEMMXXX', 'BHLSDEM1XXX', 'GAKDDEM1XXX', 'BDWBDEMMXXX', 'OLBODEH2700', 'BYLADEMMXXX', 'BYLADEM1FSI', 'BYLADEM1DAH', 'BYLADEM1ERD', 'BYLADEM1LLD', 'BYLADEM1FFB', 'BYLADEM1WOR', 'DEUTDEMMXXX', 'DEUTDEMM705', 'DEUTDEMM713', 'DEUTDEMM701', 'DEUTDEMM708', 'DEUTDEMM703', 'DEUTDEMM709', 'DEUTDEMM706', 'DEUTDEMM702', 'DEUTDEMM715', 'DEUTDEMM704', 'DEUTDEMM700', 'DEUTDEMM711', 'DEUTDEMM707', 'DEUTDEMM716', 'DEUTDEMM714', 'DEUTDEMM712', 'DEUTDEMM710', 'DEUTDEMM717', 'DEUTDEDBMUC', 'DEUTDEDB710', 'DEUTDEDB700', 'DEUTDEDB706', 'DEUTDEDB712', 'DEUTDEDB707', 'DEUTDEDB708', 'DEUTDEDB701', 'DEUTDEDB713', 'DEUTDEDB714', 'DEUTDEDB702', 'DEUTDEDB703', 'DEUTDEDB704', 'DEUTDEDB715', 'DEUTDEDB716', 'DEUTDEDB705', 'DEUTDEDB717', 'DEUTDEDB709', 'DEUTDEDB711', 'DEUTDEDBP16', 'DEUTDEMMP16', 'DRESDEFF700', 'DRESDEFF714', 'DRESDEFF724', 'DRESDEFFI55', 'DRESDEFFJ23', 'DRESDEFFJ24', 'DRESDEFFJ25', 'DRESDEFFI23', 'DRESDEFFI45', 'GENODEF1M04', 'GENODEF1MU4', 'GENODEF1S04', 'GENODEF1DCA', 'GENODEF1DSS', 'GENODEF1EDV', 'GENODEF1STH', 'GENODEF1ISV', 'MHYPDEMMXXX', 'SBOSDEMXXXX', 'DABBDEMMXXX', 'FMBKDEMMXXX', 'AGBMDEMMXXX', 'OBKLDEMXXXX', 'GENODEF1M06', 'SSKMDEMMXXX', 'GENODEFF701', 'GENODEF1FFB', 'GENODEF1OHC', 'GENODEF1HFG', 'GENODEF1SBC', 'GENODEF1RIW', 'GENODEF1ODZ', 'GENODEF1GKT', 'GENODEF1TEI', 'GENODEF1TRU', 'GENODEF1ALX', 'GENODEF1SSB', 'GENODEF1EUR', 'GENODEF1ELB', 'GENODEF1EDR', 'GENODEF1GIL', 'GENODEF1GMU', 'GENODEF1HMA', 'GENODEF1HHK', 'GENODEF1HZO', 'GENODEF1HUA', 'GENODEF1ASG', 'GENODEF1MTW', 'GENODEF1MOO', 'GENODEF1M07', 'GENODEF1M08', 'GENODEF1M03', 'GENODEF1GAA', 'GENODEF1NSV', 'GENODEF1NBK', 'GENODEF1PEI', 'GENODEF1RIG', 'GENODEF1RME', 'GENODEF1RWZ', 'GENODEF1SWO', 'GENODEF1THG', 'GENODEF1HHS', 'GENODEF1SGA', 'GENODEF1TAV', 'GENODEF1TAE', 'GENODEF1DTZ', 'GENODEF1TRH', 'GENODEF1TUS', 'GENODEF1UNS', 'GENODEF1MIB', 'GENODEF1WEI', 'GENODEF1WM1', 'GENODEF1ISE', 'GENODEF1FSR', 'GENODEF1ZOR', 'GENODEF1AIG', 'GENODEF1RHT', 'GENODEF1M01', 'GENODEF1M1Y', 'LFFBDEMMXXX', 'BHFBDEFF700', 'BMWBDEMUXXX', 'DRESDEFFBFC', 'ISBKDEFXMUN', 'BYLADEM1KMS', 'HYVEDEMM654', 'HYVEDEMM466', 'HYVEDEMM664', 'BYLADEM1GAP', 'BYLADEM1WHM', 'GENODEF1WAK', 'DRESDEFF703', 'GENODEF1GAP', 'GENODEF1PZB', 'HYVEDEMM410', 'HYVEDEMM629', 'HYVEDEMM453', 'HYVEDEMM632', 'BYLADEM1BGL', 'BYLADEM1AOE', 'BYLADEM1TST', 'GENODEF1AOE', 'GENODEF1AGE', 'GENODEF1BGL', 'HYVEDEMM448', 'HYVEDEMM644', 'HYVEDEMM438', 'HYVEDEMM457', 'BYLADEM1ROS', 'BYLADEM1MDF', 'BYLADEM1MIB', 'BYLADEM1WSB', 'GENODEF1VRR', 'GENODEF1ROR', 'GENODEF1PRV', 'GENODEF1OBD', 'GENODEF1ASU', 'GENODEF1AIB', 'DRESDEFF711', 'GENODEF1ROV', 'GENODEF1MUL', 'MARKDEF1720', 'BTVADE61XXX', 'HYVEDEMM408', 'HYVEDEMM236', 'HYVEDEMM259', 'FUBKDE71XXX', 'ANHODE77XXX', 'ANHODE7AXXX', 'AUGSDE77XXX', 'BYLADEM1AUG', 'BYLADEM1AIC', 'BYLADEM1GZK', 'GENODEF1MTG', 'GENODEF1ADZ', 'GENODEF1AIL', 'GENODEF1BSI', 'GENODEF1BOI', 'GENODEF1GZ2', 'GENODEF1HTF', 'GENODEF1HZH', 'GENODEF1HZR', 'GENODEF1ICH', 'GENODEF1JET', 'GENODEF1BBT', 'GENODEF1KRR', 'GENODEF1LST', 'GENODEF1MRI', 'GENODEF1BWI', 'GENODEF1OFF', 'GENODEF1RLI', 'GENODEF1RGB', 'GENODEF1SMU', 'GENODEF1THS', 'GENODEF1WTS', 'GENODEF1ZUS', 'GENODEF1WDN', 'GENODEF1NOE', 'GENODEF1BLT', 'GENODEF1PFA', 'DEUTDEMM720', 'DEUTDEMM727', 'DEUTDEMM725', 'DEUTDEMM723', 'DEUTDEMM726', 'DEUTDEMM724', 'DEUTDEDB720', 'DEUTDEDB723', 'DEUTDEDB724', 'DEUTDEDB725', 'DEUTDEDB726', 'DEUTDEDB727', 'DEUTDEDBP19', 'DEUTDEMMP19', 'DRESDEFF720', 'GENODEF1AUB', 'GENODEF1S03', 'GENODEF1P14', 'GENODEF1GZ1', 'HYVEDEMM426', 'HYVEDEMM665', 'BYLADEM1ING', 'BYLADEM1EIS', 'BYLADEM1PAF', 'BYLADEM1SSH', 'BYLADEM1NEB', 'GENODEF1INP', 'GENODEF1ARH', 'GENODEF1GSB', 'GENODEF1SBN', 'GENODEF1WFN', 'GENODEF1BLN', 'GENODEF1WDF', 'GENODEF1ND2', 'GENODEF1WRI', 'GENODEF1GAH', 'GENODEF1RBL', 'DEUTDEMM721', 'DEUTDEMM729', 'DEUTDEMM722', 'DEUTDEMM728', 'DEUTDEDB721', 'DEUTDEDB722', 'DEUTDEDB728', 'DEUTDEDB729', 'DEUTDEDBP17', 'DEUTDEMMP17', 'DRESDEFF721', 'GENODEF1PFI', 'HYVEDEMM255', 'HYVEDEMM263', 'BYLADEM1NLG', 'BYLADEM1DON', 'BYLADEM1DLG', 'GENODEF1RLH', 'GENODEF1DLG', 'GENODEF1DON', 'BYLADEM1NUL', 'GENODEF1NU1', 'GENODEF1NUV', 'HYVEDEMM436', 'BYLADEM1MLM', 'GENODEF1MIR', 'DRESDEFF731', 'GENODEF1MM1', 'HYVEDEMM428', 'HYVEDEMM567', 'HYVEDEMM570', 'GABLDE71XXX', 'BYLADEM1ALG', 'GENODEF1DTA', 'GENODEF1LBB', 'GENODEF1WWA', 'GENODEF1LIA', 'GENODEF1AIT', 'GENODEF1FCH', 'GENODEF1BIN', 'GENODEF1EGB', 'GENODEF1KM1', 'GENODEF1OKI', 'GENODEF1SFO', 'GENODEF1RHP', 'GENODEF1SER', 'GENODEF1WGO', 'DEUTDEMM733', 'DEUTDEMM734', 'DEUTDEMM735', 'DEUTDEMM736', 'DEUTDEMM737', 'DEUTDEDB733', 'DEUTDEDB737', 'DEUTDEDB736', 'DEUTDEDB734', 'DEUTDEDB735', 'DRESDEFF733', 'GENODEF1KEV', 'GENODEF1IMV', 'HYVEDEMM427', 'HYVEDEMM666', 'BYLADEM1KFB', 'BYLADEM1SOG', 'GENODEF1KFB', 'DRESDEFF734', 'HYVEDEMM445', 'RZOODE77XXX', 'RZOODE77050', 'BYLADEM1PAS', 'BYLADEM1FRG', 'GENODEF1RGS', 'GENODEF1NUI', 'GENODEF1ORT', 'GENODEF1PFK', 'GENODEF1VIR', 'GENODEF1TIE', 'GENODEF1WSD', 'GENODEF1SZT', 'GENODEF1HZN', 'GENODEF1POC', 'GENODEF1GRT', 'GENODEF1HHU', 'GENODEF1TKI', 'GENODEF1NHD', 'GENODEF1PA1', 'HYVEDEMM415', 'TEKRDE71XXX', 'BYLADEM1DEG', 'BYLADEM1REG', 'GENODEF1DEG', 'GENODEF1HBW', 'GENODEF1RGE', 'GENODEF1AUS', 'DRESDEFF741', 'GENODEF1DGV', 'GENODEF1LND', 'HYVEDEMM452', 'HYVEDEMM675', 'BYLADEM1SRG', 'BYLADEM1CHM', 'GENODEF1SR2', 'GENODEF1CHA', 'GENODEF1SR1', 'CBSRDE71XXX', 'HYVEDEMM433', 'BYLADEM1LAH', 'BYLADEM1EGF', 'BYLADEM1MSB', 'GENODEF1ARF', 'GENODEF1ERG', 'GENODEF1PFF', 'GENODEF1GSH', 'GENODEF1LWE', 'GENODEF1GPF', 'GENODEF1PST', 'GENODEF1RZK', 'GENODEF1ENA', 'GENODEF1EBV', 'GENODEF1MKO', 'DRESDEFF743', 'GENODEF1LH1', 'GENODEF1DGF', 'GENODEF1EGR', 'GENODEF1VBV', 'MARKDEF1750', 'HYVEDEMM447', 'HYVEDEMM804', 'BYLADEM1RBG', 'BYLADEM1SAD', 'BYLADEM1KEH', 'GENODEF1R02', 'GENODEF1SWN', 'GENODEF1REF', 'GENODEF1DST', 'GENODEF1ABS', 'GENODEF1NGG', 'GENODEF1BUK', 'GENODEF1FKS', 'GENODEF1GRW', 'GENODEF1HGA', 'GENODEF1HEM', 'GENODEF1SZV', 'GENODEF1KTZ', 'GENODEF1PAR', 'GENODEF1NKN', 'GENODEF1SWD', 'DEUTDEMM750', 'DEUTDEMM751', 'DEUTDEMM741', 'DEUTDEMM752', 'DEUTDEDB750', 'DEUTDEDB741', 'DEUTDEDB752', 'DEUTDEDB751', 'DRESDEFF750', 'GENODEF1R01', 'GENODEF1M05', 'GENODEF1S05', 'GENODEF1P18', 'GENODEF1BLF', 'HYVEDEMM405', 'BYLADEM1ABG', 'GENODEF1SZH', 'GENODEF1AMV', 'HYVEDEMM454', 'BYLADEM1WEN', 'BYLADEM1ESB', 'GENODEF1WEO', 'GENODEF1FLS', 'GENODEF1NEW', 'GENODEF1WEV', 'MARKDEF1760', 'HYVEDEMM460', 'HYVEDEMMCAR', 'NORSDE71XXX', 'CSDBDE71XXX', 'ISBKDEFXNUR', 'BIWBDE33760', 'TEAMDE71XXX', 'TEAMDE71TAT', 'UMWEDE7NXXX', 'SSKNDE77XXX', 'BYLADEM1NMA', 'GENODEFF760', 'GENODEF1N02', 'GENODEF1LAU', 'GENODEF1HSB', 'GENODEF1AUO', 'GENODEF1WDS', 'GENODEF1BEH', 'GENODEF1DSB', 'GENODEF1DIH', 'GENODEF1DIM', 'GENODEF1FEC', 'GENODEF1FEW', 'GENODEF1FRD', 'GENODEF1FYS', 'GENODEF1GDG', 'GENODEF1GU1', 'GENODEF1HSC', 'GENODEF1N08', 'GENODEF1NM1', 'GENODEF1NEA', 'GENODEF1BTO', 'GENODEF1BPL', 'GENODEF1HSE', 'GENODEF1SDM', 'GENODEF1URS', 'GENODEF1WBA', 'GENODEF1ZIR', 'DEUTDEMM760', 'DEUTDEMM773', 'DEUTDEMM762', 'DEUTDEMM763', 'DEUTDEMM783', 'DEUTDEMM764', 'DEUTDEMM769', 'DEUTDEMM774', 'DEUTDEMM768', 'DEUTDEMM761', 'DEUTDEMM765', 'DEUTDEMM766', 'DEUTDEMM767', 'DEUTDEMM772', 'DEUTDEMM771', 'DEUTDEDB760', 'DEUTDEDB765', 'DEUTDEDB761', 'DEUTDEDB762', 'DEUTDEDB773', 'DEUTDEDB783', 'DEUTDEDB763', 'DEUTDEDB768', 'DEUTDEDB764', 'DEUTDEDB774', 'DEUTDEDB772', 'DEUTDEDB767', 'DEUTDEDB771', 'DEUTDEDB766', 'DEUTDEDB769', 'DEUTDEDBP15', 'DEUTDEMMP15', 'DRESDEFF760', 'DRESDEFFAGI', 'DRESDEFFI25', 'DRESDEFFJ26', 'DRESDEFFJ27', 'DRESDEFFI24', 'DRESDEFFI46', 'GENODEF1N03', 'GENODEF1S06', 'GENODEF1P17', 'GENODEF1WHD', 'HYVEDEMM419', 'QUBADE71XXX', 'BYLADEM1SFU', 'BYLADEM1NEA', 'GENODEF1FUE', 'HYVEDEMM417', 'BYLADEM1ERH', 'BYLADEM1FOR', 'BYLADEM1HOS', 'GENODEF1ER1', 'GENODEF1FOH', 'HYVEDEMM065', 'BYLADEM1SRS', 'GENODEF1SWR', 'GENODEF1HPN', 'HYVEDEMM406', 'BYLADEM1ANS', 'BYLADEM1DKB', 'BYLADEM1GUN', 'BYLADEM1ROT', 'GENODEF1ANS', 'GENODEF1DKV', 'HYVEDEMM411', 'BYLADEM1SKB', 'GENODEF1BA2', 'GENODEF1ALK', 'GENODEF1EBR', 'GENODEF1BGB', 'GENODEF1SFF', 'GENODEF1KC2', 'GENODEF1HIS', 'GENODEF1HOB', 'GENODEF1SFD', 'GENODEF1GBF', 'GENODEF1THA', 'GENODEF1KEM', 'GENODEF1SPK', 'GENODEF1BGO', 'GENODEF1MGA', 'GENODEF1SZF', 'GENODEF1WSZ', 'GENODEF1ZSP', 'GENODEF1LIF', 'HYVEDEMM289', 'BYLADEM1KUB', 'GENODEF1KU1', 'MARKDEF1773', 'HYVEDEMM412', 'FODBDE77XXX', 'BYLADEM1SBT', 'GENODEF1GFS', 'GENODEF1HWA', 'HYVEDEMM424', 'BYLADEM1HOF', 'BYLADEM1FIG', 'GENODEF1HO1', 'GENODEF1MAK', 'GENODEF1WSS', 'HYVEDEMM480', 'BYLADEM1COB', 'GENODEF1COS', 'MARKDEF1790', 'HYVEDEMM455', 'FUCEDE77XXX', 'BSHADE71XXX', 'BYLADEM1SWU', 'GENODEF1EFD', 'GENODEF1HBG', 'GENODEF1BRK', 'GENODEF1WED', 'GENODEF1ATE', 'GENODEF1BHD', 'GENODEF1GEM', 'GENODEF1MLV', 'GENODEF1NDL', 'GENODEF1SLZ', 'GENODEF1RNM', 'DEUTDEMM790', 'DEUTDEMM791', 'DEUTDEMM792', 'DEUTDEDB790', 'DEUTDEDB792', 'DEUTDEDB791', 'DRESDEFF790', 'DRESDEFFJ28', 'GENODEF1WU1', 'GENODEF1ERN', 'GENODEF1OBR', 'GENODEF1KT1', 'HYVEDEMM451', 'FLESDEMMXXX', 'BYLADEM1SSW', 'BYLADEM1KSW', 'BYLADEM1KIS', 'BYLADEM1HAS', 'BYLADEM1NES', 'GENODEF1GZH', 'GENODEF1NDT', 'GENODEF1HAS', 'GENODEF1FWH', 'DRESDEFF793', 'HYVEDEMM407', 'BYLADEM1ASA', 'GENODEF1BAG', 'GENODEF1AB1', 'GENODEF1WAA', 'GENODEF1ALZ', 'GENODEF1HAC', 'DEUTDEDB795', 'DEUTDEDB796', 'DEUTDEFF795', 'DEUTDEFF796', 'DEUTDEDBP18', 'DEUTDEFFS18', 'DRESDEFF795', 'DRESDEFFI47', 'GENODEF1AB2', 'BYLADEM1MIL', 'GENODEF1EAU', 'GENODEF1OBE', 'GENODEF1ENB', 'GENODEF1MIL', 'HYVEDEMM440', 'HYVEDEMM462', 'NOLADE21MQU', 'NOLADE21BLK', 'NOLADE21DES', 'NOLADE21KOT', 'NOLADE21BTF', 'NOLADE21HAL', 'NOLADE21WSF', 'NOLADE21EIL', 'NOLADE21SES', 'GENODEF1JE1', 'GENODEF1QLB', 'GENODEF1SGH', 'GENODEF1WB1', 'GENODEF1KOE', 'GENODEF1NMB', 'GENODEF1ZTZ', 'GENODEF1EIL', 'DRESDEFF800', 'GENODEF1DS1', 'GENODEF1HAL', 'NOLADE21WBL', 'NOLADE21ZER', 'MARKDEF1810', 'NOLADE21LSA', 'BFSWDE33MAG', 'NOLADE21SDL', 'NOLADE21HRZ', 'NOLADE21MDG', 'NOLADE21JEL', 'NOLADE21HDL', 'NOLADE21SAW', 'GENODEF1KAB', 'GENODEF1BRG', 'GENODED1KDM', 'GENODEF1WZL', 'DEUTDE8MXXX', 'DEUTDE8M814', 'DEUTDE8M812', 'DEUTDE8M816', 'DEUTDE8M820', 'DEUTDE8M818', 'DEUTDE8M821', 'DEUTDE8M822', 'DEUTDE8M823', 'DEUTDE8M815', 'DEUTDE8M817', 'DEUTDE8M819', 'DEUTDE8M811', 'DEUTDE8M825', 'DEUTDEDBMAG', 'DEUTDEDB815', 'DEUTDEDB814', 'DEUTDEDB811', 'DEUTDEDB812', 'DEUTDEDB816', 'DEUTDEDB817', 'DEUTDEDB818', 'DEUTDEDB819', 'DEUTDEDB801', 'DEUTDEDB802', 'DEUTDEDB803', 'DEUTDEDB804', 'DEUTDEDB806', 'DRESDEFF810', 'GENODEF1GA1', 'GENODEF1SDL', 'GENODEF1MD1', 'MARKDEF1820', 'HYVEDEMM498', 'HYVEDEMM098', 'HYVEDEMM824', 'HELADEFF820', 'HELADEF1WEM', 'HELADEF1GTH', 'HELADEF1NOR', 'HELADEF1KYF', 'HELADEF1MUE', 'HELADEF1EIC', 'GENODED1PA5', 'GENODEF1MU2', 'GENODEF1ESA', 'GENODEF1GTH', 'GENODEF1WE1', 'ERFBDE8EXXX', 'DEUTDE8EXXX', 'DEUTDE8E828', 'DEUTDE8E829', 'DEUTDE8E842', 'DEUTDE8E843', 'DEUTDE8E832', 'DEUTDE8E830', 'DEUTDE8E827', 'DEUTDE8E833', 'DEUTDE8E844', 'DEUTDE8E831', 'DEUTDE8E845', 'DEUTDE8E825', 'DEUTDE8E824', 'DEUTDE8E835', 'DEUTDE8E847', 'DEUTDE8E848', 'DEUTDE8E849', 'DEUTDE8E822', 'DEUTDE8E850', 'DEUTDE8E823', 'DEUTDE8E840', 'DEUTDE8E820', 'DEUTDE8E836', 'DEUTDE8E841', 'DEUTDE8E826', 'DEUTDE8E851', 'DEUTDE8E846', 'DEUTDEDBERF', 'DEUTDEDB828', 'DEUTDEDB841', 'DEUTDEDB829', 'DEUTDEDB842', 'DEUTDEDB843', 'DEUTDEDB832', 'DEUTDEDB830', 'DEUTDEDB827', 'DEUTDEDB833', 'DEUTDEDB844', 'DEUTDEDB831', 'DEUTDEDB845', 'DEUTDEDB825', 'DEUTDEDB824', 'DEUTDEDB846', 'DEUTDEDB835', 'DEUTDEDB847', 'DEUTDEDB848', 'DEUTDEDB849', 'DEUTDEDB823', 'DEUTDEDB822', 'DEUTDEDB850', 'DEUTDEDB840', 'DEUTDEDB851', 'DEUTDEDB820', 'DEUTDEDB821', 'DEUTDEDB836', 'DEUTDEDBP20', 'DEUTDE8EP20', 'DRESDEFF827', 'GENODEF1HIG', 'GENODEF1NDS', 'HYVEDEMM468', 'HYVEDEMM463', 'HYVEDEMM484', 'HELADEF1GER', 'HELADEF1ALT', 'HELADEF1SAR', 'HELADEF1SOK', 'HELADEF1JEN', 'GENODEF1HMF', 'GENODEF1GEV', 'GENODEF1SLR', 'DRESDEFF830', 'GENODEF1PN1', 'GENODEF1RUJ', 'GENODEF1ESN', 'GENODEF1ETK', 'HYVEDEMM458', 'HELADEF1RRS', 'HELADEF1ILK', 'HELADEF1HIL', 'HELADEF1SON', 'HELADEF1WAK', 'GENODEF1MLF', 'GENODEF1SSG', 'DRESDEFF843', 'GENODEF1SAL', 'GENODEF1SHL', 'MARKDEF1850', 'SABDDE81XXX', 'HYVEDEMM496', 'BFSWDE33DRE', 'WELADED1GRL', 'OSDDDE81XXX', 'OSDDDE81SEB', 'OSDDDE81FTL', 'OSDDDE81HDN', 'OSDDDE81HOY', 'OSDDDE81KMZ', 'OSDDDE81RBG', 'OSDDDE81PIR', 'SOLADES1MEI', 'GENODEF1PR2', 'GENODEF1SEB', 'DRESDEFF850', 'DRESDEFFJ29', 'DRESDEFFJ30', 'DRESDEFF857', 'DRESDEFFI15', 'GENODEF1DRS', 'GENODEF1RIE', 'GENODEF1MEI', 'SOLADES1BAT', 'GENODEF1BZV', 'GENODEF1NGS', 'GENODEF1GR1', 'MARKDEF1860', 'AARBDE5W860', 'HYVEDEMM495', 'BFSWDE33LPZ', 'SOLADEST861', 'SOLADES1GRM', 'WELADED1TGU', 'SOLADES1DES', 'SOLADES1DLN', 'WELADE8LXXX', 'GENODEF1BOA', 'GENODEF1DL1', 'GENODEF1GMR', 'GENODEF1TGB', 'DEUTDE8LXXX', 'DEUTDE8L861', 'DEUTDE8L862', 'DEUTDE8L863', 'DEUTDE8L864', 'DEUTDE8L865', 'DEUTDE8L867', 'DEUTDE8L871', 'DEUTDE8L860', 'DEUTDE8L873', 'DEUTDE8L875', 'DEUTDE8L877', 'DEUTDE8L880', 'DEUTDE8L883', 'DEUTDE8L884', 'DEUTDE8L885', 'DEUTDE8L887', 'DEUTDE8L888', 'DEUTDE8L866', 'DEUTDE8L868', 'DEUTDE8L869', 'DEUTDE8L872', 'DEUTDE8L870', 'DEUTDE8L874', 'DEUTDE8L878', 'DEUTDE8L879', 'DEUTDE8L881', 'DEUTDE8L882', 'DEUTDEDBLEG', 'DEUTDEDB861', 'DEUTDEDB862', 'DEUTDEDB863', 'DEUTDEDB864', 'DEUTDEDB865', 'DEUTDEDB866', 'DEUTDEDB867', 'DEUTDEDB868', 'DEUTDEDB869', 'DEUTDEDB974', 'DEUTDEDB860', 'DEUTDEDB975', 'DEUTDEDB976', 'DEUTDEDB973', 'DEUTDEDB988', 'DEUTDEDB977', 'DEUTDEDB978', 'DEUTDEDB980', 'DEUTDEDB981', 'DEUTDEDB982', 'DEUTDEDB983', 'DEUTDEDB984', 'DEUTDEDB985', 'DEUTDEDB986', 'DEUTDEDB987', 'DEUTDEDB990', 'DEUTDEDB991', 'DEUTDE8LP37', 'DEUTDEDBP37', 'DRESDEFF860', 'DRESDEFF862', 'DRESDEFF867', 'DRESDEFFJ31', 'DRESDEFFJ32', 'DRESDEFFI16', 'GENODEF1GMV', 'GENODEF1DZ1', 'GENODEF1LVB', 'MARKDEF1870', 'HYVEDEMM497', 'HYVEDEMM481', 'HYVEDEMM441', 'CHEKDE81XXX', 'CHEKDE81MRN', 'CHEKDE81LTS', 'CHEKDE81LIM', 'CHEKDE81GLA', 'CHEKDE81HOT', 'WELADED1MTW', 'WELADED1FGX', 'WELADED1STB', 'WELADED1ZWI', 'WELADED1PLX', 'GENODEF1MBG', 'GENODEF1BST', 'DEUTDE8CXXX', 'DEUTDE8C871', 'DEUTDE8C874', 'DEUTDE8C877', 'DEUTDE8C870', 'DEUTDE8C879', 'DEUTDE8C880', 'DEUTDE8C881', 'DEUTDE8C882', 'DEUTDE8C883', 'DEUTDE8C885', 'DEUTDE8C886', 'DEUTDE8C887', 'DEUTDE8C888', 'DEUTDE8C890', 'DEUTDE8C892', 'DEUTDE8C894', 'DEUTDE8C895', 'DEUTDE8C897', 'DEUTDE8C898', 'DEUTDE8C899', 'DEUTDE8C901', 'DEUTDE8C902', 'DEUTDE8C903', 'DEUTDE8C906', 'DEUTDE8C907', 'DEUTDE8C909', 'DEUTDE8C910', 'DEUTDE8C872', 'DEUTDE8C873', 'DEUTDE8C875', 'DEUTDE8C876', 'DEUTDE8C884', 'DEUTDE8C889', 'DEUTDE8C891', 'DEUTDE8C893', 'DEUTDE8C896', 'DEUTDE8C900', 'DEUTDE8C905', 'DEUTDE8C908', 'DEUTDE8C878', 'DEUTDEDBCHE', 'DEUTDEDB871', 'DEUTDEDB872', 'DEUTDEDB873', 'DEUTDEDB874', 'DEUTDEDB875', 'DEUTDEDB876', 'DEUTDEDB877', 'DEUTDEDB870', 'DEUTDEDB878', 'DEUTDEDB879', 'DEUTDEDB880', 'DEUTDEDB881', 'DEUTDEDB882', 'DEUTDEDB883', 'DEUTDEDB884', 'DEUTDEDB885', 'DEUTDEDB886', 'DEUTDEDB887', 'DEUTDEDB888', 'DEUTDEDB897', 'DEUTDEDB889', 'DEUTDEDB890', 'DEUTDEDB891', 'DEUTDEDB892', 'DEUTDEDB893', 'DEUTDEDB894', 'DEUTDEDB895', 'DEUTDEDB896', 'DEUTDEDB898', 'DEUTDEDB899', 'DEUTDEDB900', 'DEUTDEDB901', 'DEUTDEDB902', 'DEUTDEDB903', 'DEUTDEDB905', 'DEUTDEDB906', 'DEUTDEDB907', 'DEUTDEDB908', 'DEUTDEDB909', 'DEUTDEDB910', 'DEUTDE8CP36', 'DEUTDEDBP36', 'DRESDEFF870', 'GENODEF1PL1', 'GENODEF1EXT', 'GENODEF1Z01', 'GENODEF1GC1', 'GENODEF1MIW', 'GENODEF1CH1']
    if bic in bic_list:
        return True
    return False
## check if string is an IBAN
# @param iban - string to be checked
def Afp_isIBAN(iban):
    iban = iban.replace(" ","")
    check = False
    length = {"AT":20,"BE":16,"BG":22,"HR":21,"CY":28,"CZ":24,"DK":18,"EE":20,"FI":18,"FR":27,"DE":22,"GI":23,"GR":27,"HU":28,"IS":26,"IE":22,"IT":27,"LV":21,"LI":21,"LT":20,"LU":20,"MT":31,"MC":27,"NL":18,"NO":15,"PL":28,"PT":25,"RO":24,"SM":27,"SK":24,"SI":19,"ES":24,"SE":24,"CH":21,"GB":22}
    # first check if lenght is correct
    country = iban[:2]
    if country in length:
        if not len(iban) == length[country]: 
            return None
    else:
        if len(iban) < 4 or len(iban) > 32:
            return None
    # second check if iban hash is correct
    digits = Afp_fromString(iban[2:4])
    nstring = iban[4:] + Afp_mapIChar(iban[0]) + Afp_mapIChar(iban[1]) + "00"
    number = Afp_fromString(nstring)
    if digits == 98 - (number % 97):
        # third check if number with hash digits % 97 is 1
        number = Afp_fromString(nstring[:-2] + iban[2:4])
        if number % 97 == 1:
            check = True
    return check
## check if string is an EAN-Code
# @param ean - string to be checked
def Afp_isEAN(ean):
    isEan = False
    lgh = len(ean)
    sum = 0
    if lgh == 13:
        fac = 3
        for i in range(lgh-1,-1,-1):
            sum += fac*int(ean[i])
            if fac == 3: fac = 1
            else: fac = 3
        diff = int(sum/10)*10 + 10 - sum
        if diff == int(ean[-1]): isEan = True
    return isEan
## flag if string may represent a numeric value
# @param string - string to be analysed
# @param check - maximum number of parts accepted when split at a "." \n
# - check == 2: default, less then 2 parts are accepted \n
# - check > 2: exact number of parts has to be available
def Afp_hasNumericValue(string, check=2):
    string = string.strip()
    if string[0] == "-":
        string = string[1:].strip()
    if "." in string  or "," in string:
        if "." in string:
            split = string.split(".")
        else:
            split = string.split(",")
        if check > 2 and not len(split) == check:
            #numeric = False
            return False
        #else:
            #numeric = True
        for i in range(0,len(split)):
            #if i < check and not split[i].isdigit():
                #numeric = False
            if i < check: 
                if not split[i].isdigit():
                    return False
            else:
                return False      
        #return numeric
        return True
    elif string.isdigit():
        if check < 3: return True
        else: return False
    else:
        return False
## mask double qoutes in string values
# @param value - value to be analysed
def Afp_maskiere(value):
    if value is None: return None
    if Afp_isString(value):
        return value.replace('"','\\"')
    return  value
## strip inner spaces from string
# @param string - string to be stripped
def Afp_stripSpaces(string):
    return "".join(string.split())
## combine values to one string, if only one value is indicated each value type is possible
# @param indices - indices of values to be extracted from array and combined
# @param array- list of values
def Afp_combineValues(indices, array):
    wert = ""
    if indices is None:
        for value in array:
            if wert == "": leer = ""
            else: leer = " "
            wert += leer +  Afp_maskiere(Afp_toString(value))
    else:
        if len(indices) == 1:
            # single index, each type possible
            wert = array[indices[0]]
            if type(wert) == str:
                wert = Afp_maskiere(wert)
        else:
            # multiple index, only string possible
            for ind in indices:
                if wert == "": leer = ""
                else: leer = " "
                wert += leer +  Afp_maskiere(Afp_toString(array[ind]))
    return wert
   
## DEPRECATED FUNCTION: use Afp_extractPureValues or Afp_extractStringValues instead
def Afp_extractValues(indices, array):
    #print "DEPRECATED FUNCTION: use Afp_extractPureValues or Afp_extractStringValues instead In:",indices, array
    if indices is None:
        wert = []
        for entry in array:
            wert.append(Afp_maskiere(Afp_toInternDateString(entry)))
    else:
        if len(indices) == 1:
            # single index, each type possible
            wert = array[indices[0]]
            if type(wert) == str:
                wert = Afp_maskiere(wert)
            #print "Afp_extractValues", wert, type(wert), array
        else:
            # multiple index, only string possible
            wert = []
            for ind in indices:
                wert.append(Afp_maskiere(Afp_toInternDateString(array[ind])))
    #print "DEPRECATED FUNCTION: Afp_extractValues Out:", wert
    return wert
## extract values from array (list) and convert them to strings
# @param indices - indices of values to be extracted from array, None all entries are extracted
# @param array - list of values
# @param date - flag if internal date representation should be used
def Afp_extractStringValues(indices, array, intern_date = False):
    #print "Afp_extractStringValues:", indices, array, date
    strings = []
    if array: werte = Afp_extractPureValues(indices,array)
    else: werte = []
    for entry in werte:
        if intern_date:
            strings.append(Afp_maskiere(Afp_toInternDateString(entry)))
        else:
            strings.append(Afp_maskiere(Afp_toString(entry)))
    return strings

## compare two values extracted from database
# @param v1 - first value
# @param v2 - second value
# @param debug - flag for debug output
def Afp_compareSql(v1, v2, debug = False):
    if v1 is None or v2 is None:
        return (v1 == v2)
    if Afp_isNumeric(v1):
        return (v1 == v2)
    elif  v1.lower() == v2.lower():
        return True
    v1 = Afp_replaceUml(v1.lower())
    v2 = Afp_replaceUml(v2.lower())
    if debug: print("Afp_compareSql:", v1,v2)
    return (v1 == v2)
## replace special german letters to compare words
# @param string - string to be manipulated
# @param skip - flag if strict alphanumeric should be used
def Afp_replaceUml(string, skip=False):
    umlaute = {196: 'Ae', 214: 'Oe', 220: "Ue", 228: 'ae', 246: 'oe', 252: 'ue', 223: 'ss', 225: 'a', 233: 'e'}
    strict = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 /?:().,'+-"
    newstring = ''
    for char in string:
        uni = ord(char)
        #print char, uni
        if uni in umlaute:
            char = umlaute[uni]
        elif skip and not char in strict:
            char = ""
        newstring += char
    return newstring
## set special german letters from strict presentaion
# @param string - string to be manipulated
def Afp_setUml(string):
    umlaute = {"Ae": "Ä", "Oe":"Ö", "Ue":"Ü", "ae": "ä", "oe": "ö", "ue":"ü", "ss": "ß"} 
    lastchar = None
    newstring = ""
    for char in string:
        if not lastchar is None:
            if lastchar + char in umlaute:
                newstring = newstring[:-1] + umlaute[lastchar + char]
            else:
                newstring += char
            #print("Afp_setUml:", lastchar+char, newstring)
        else:
            newstring = char
        lastchar = char
    return newstring
## map iban chars to integer string (A,a : 10; B,b : 11 ... Z,z : 35)
# @param char - char to be mapped
def Afp_mapIChar(char):
    asci = ord(char)
    if  asci > 90:
        val = asci - 87
    else:
        val = asci - 55
    if val > 9 and val <36:
        return Afp_toString(val)
    else:
        return "XX"
    
## extract word from string which include special phrases
# @param in_string - string to be analysed
# @param including - string to included in word
def Afp_getWords(in_string, including=None):
    words = []
    split = in_string
    str = ""
    if including:
        split = in_string.split(including)
    else:
        split = [in_string]
    lastwords = None
    for teilstr in split:
        str = ""
        currentwords = []
        for s in teilstr:
            if s.isalpha():
                str += s
            else:
                if str:  currentwords.append(str)
                str = ""
        if str: currentwords.append(str)
        if not lastwords is None:
            word = ""
            if lastwords: word += lastwords[-1]
            word += including
            if currentwords: word += currentwords[0]
            words.append(word)
        lastwords = currentwords
    if including is None:
        words = currentwords
    return words
## removes end of string behind last occurence of char
# @param string - string to be cut
# @param char - char where string should be cut
def Afp_getToLastChar(string, char):
    if char in string:
        split = string.split(char)
        result = ""
        for i in range(len(split)-1):
            result += split[i] + char
        return result
    else:
        return string
## get letters in front of numeric figures
# @param  string - string where letters have to be extracted
def Afp_getStartLetters(string):
    letters = ""
    test = True
    for s in string:
        if test:
            if s.isdigit(): test = False
            else: letters += s
    return letters
## get number behind letters
# @param  string - string where number has to be extracted
# @param  start - flag if number should be extracted at the beginning of the string
def Afp_getEndNumber(string, start=False):
    #print "Afp_getEndNumber:", string, type(string)
    number = ""
    test = True
    if not start: string = reversed(string)
    for s in string:
        if test:
            if s.isdigit(): number += s
            else: test = False
    if not start: number = number[::-1]
    return Afp_fromString(number)
## get sequence of words in the order they occur in the string
# @param string - string to be analysed
# @param words - list of words to be looked for
def Afp_getSequence(string, words):
    seq = []
    length = {}
    for word in words:
        length[word] = len(word)
    lgh = len(string)
    for i in range(lgh):
        for word in words:
            lend = i + length[word] 
            if lgh >= lend and string[i:lend] == word:
                seq.append(word)
    #print "Afp_getSequence:", string, words, seq
    return seq
        
## devide string into phrases inside and outside the start/end brackets
# nested brackets not possible 
# @param  string - string to be analysed
# @param  start - opening bracket
# @param  end  - closing bracket \n
# output: \n
# - string can be recreated as follows: out[i] + start + in[i] + end + out[i+1] + ... + out[n]
# - first and last out[]-value may be empty, if string starts with 'start' or ends with 'end'
def Afp_between(string, start, end):
    sstring = string.split(start)
    #print ("Afp_between:", sstring)
    instrings = []
    outstrings = []
    if start == end:
        lgh = len(sstring)
        for i in range(lgh):
            #if i==0 and not sstring[i]: continue
            #if i==lgh-1 and not sstring[i]: continue
            if i % 2 == 1 and i < lgh-1:
                instrings.append(sstring[i])
            else:
                outstrings.append(sstring[i])
        if lgh % 2 == 0:
            print("WARNING Afp_between: Asymmetric ", start , end,  " pair in \"" + string +"\"")
    else:
        for strg in sstring:
            split= strg.split(end)  
            if len(split) > 1: 
                instrings.append(split[0])
                outstrings.append(split[1])
                if len(split)>2:
                    print("WARNING Afp_between: Asymmetric ", start , end,  " pair in \"" + string +"\"")
            else:
                outstrings.append(split[0])
        if len(outstrings) > len(instrings) + 1:
            print("WARNING Afp_between: Asymmetric ", start , end,  " pair in \"" + string +"\"")
    return instrings,outstrings

## devide string into phrases inside and outside a double quote pair
# @param  string - string to be analysed
def Afp_maskedText(string):
    masked = []
    unmasked = []
    split = string.split("\"")
    mask = False
    for part in split:
        if mask: masked.append(part)
        else: unmasked.append(part)
        mask = not mask
    return unmasked, masked
   
## extract variable and function body from string \n
# split at "=". "+=","-=","*=" are handled also
# @param  string - string to be analysed
def Afp_getFuncVar(string):
    # get variable name and function
    if not "=" in string: return None, string
    split = string.split("=")
    if len(split) > 2: return None, string
    var = split[0].strip()
    func = split[1].strip()
    sign = ""
    if not var.isalpha():
        sign = var[-1]
        var = var[:-1].strip()
        func = var + sign + func
    return var, func
## split function fromula at signs, devide variables and signs
# @param  string - string to be analysed
def Afp_splitFormula(string):
    vars = []
    signs = []
    wort = ""
    for c in string:
        if c == "*" or c == "/" or c == "+" or c == "-" or c == ")": 
            if len(signs) > 0 and signs[-1] == ")":
                signs[-1] = signs[-1] + c
            else:
                signs.append(c)
                vars.append(wort.strip())
            wort = ""
        elif c =="(": 
            signs[-1] = signs[-1] + c
        else: 
            wort += c
    if wort: vars.append(wort.strip())
    return vars, signs  
 
## split string at different limiters
# @param in_string - string to be analysed
# @param limiters - list of limiters where string has to be split
def Afp_split(in_string, limiters):
    strings = [in_string]
    split = []
    for limit in limiters:
        split = []
        for string in strings:
            split.append(string.split(limit))
        strings = []
        for s1 in split:
            for s in s1:
                strings.append(s)
    return strings
    
## split string at different limiters
# @param in_string - string to be analysed
# @param limiter - limiter where string has to be split
# @param mask - sign between which limiter will be ignored
def Afp_splitMasked(string, limiter, mask):
    #print "Afp_splitMasked string:", string, limiter, mask
    masked = string.split(mask)
    result = []
    lgh = len(masked)
    for i in range(lgh):
        if masked[i].strip() == limiter: continue
        if i%2 == 0:
            if masked[i]:
                if i > 0 and masked[i][0] == limiter: masked[i] = masked[i][1:]
                if len(masked[i]) and i < lgh-1 and masked[i][-1] == limiter: masked[i] = masked[i][:-1]
                result += masked[i].split(limiter)
        else:
            result += [masked[i]]
    #print "Afp_splitMasked result:", result
    return result   
    
## assure pathname to recognise wanted conventions for the path separator, \n
#  used for either Unix "/" or Windows "\\" separator.
# @param path - pathname to be checked
# @param delimit - path separator, default Unix
# @param file - flag if path is a filename (otherwise an addtional delimiter is added at end)
def Afp_pathname(path, delimit = None, file = False):
    delimiter = "/"
    if delimit: delimiter = delimit
    if delimiter == "\\":
        path = path.replace("/",delimiter)
    else:
        path = path.replace("\\",delimiter)
    if not file and not path[-1] == delimiter: path += delimiter
    return path
## check if given name holds a complete path (includig a root)
def Afp_isRootpath(filename):
    if filename and (filename[0] == "/" or filename[1] == ":"):
        return True
    else:
        return False
## check if given name holds a complete path (includig a root), \n
# if not, given rootdir is added at the beginning of the name.
# @param rootdir - rootpath to be added
# @param filename - name to be checked (may be None: rootdir is returned)
def Afp_addRootpath(rootdir, filename):
    if  filename and Afp_isRootpath(filename):
        # root already in filename, don't do anything
        composite = filename
    else:
        if rootdir:
            if not (rootdir[-1] == "/" or rootdir[-1] == "\\"):
                if "\\" in rootdir:
                    rootdir += "\\"
                else:
                    rootdir += "/"
        if filename:
            composite = rootdir + filename
        else:
            composite = rootdir
    return composite

## counts the starting spaces in the string
# @param string - string to be analysed
def Afp_leftSpCnt(string):
    # left space count
    return  len(string) - len(string.lstrip())
  
## check if string holds a date, \n
# possibly complete date with current day, month or year.
# @param string - string to be analysed
# @param usepast - flag if date is assumed to lie in the past,  \n
# @param refdat - if given, date to be used as a reference, default: today  \n
# short years will be completed with the last century, if the normal completation would set them to ly in the future.
def Afp_ChDatum(string, usepast = None, refdat = None):
    if string is None: return string
    alldigits = False
    if not refdat:  refdat = datetime.date.today()
    day = refdat.day
    month = refdat.month
    year = refdat.year
    nodigits = []   
    chars = ""
    for char in string:
        if char.isdigit():
            if chars and not chars in nodigits: 
                nodigits.append(chars)
            chars = ""
        else:
            chars += char
    if chars and not chars in nodigits: 
        nodigits.append(chars)
    zahlen = Afp_split(string, nodigits)
    lgh = len(zahlen)
    if lgh > 2 and len(zahlen[2]) > 2: alldigits = True
    for i in range(lgh):
        zahlen[i] = Afp_fromString(zahlen[i])
    # complete date-string
    lgh = len(zahlen)
    for i in range(lgh-1,-1,-1):
        if not zahlen[i]: del zahlen[i]
    lgh = len(zahlen)
    if lgh < 3:
        if lgh == 0: zahlen.append(day)
        if lgh <= 1: 
            if usepast is None or (usepast and zahlen[-1] <= day) or (not usepast and zahlen[-1] >= day):
                zahlen.append(month)
            elif usepast and zahlen[-1] > day:
                if month < 2:
                    zahlen.append(12)
                else:
                    zahlen.append(month - 1)
            elif not usepast and zahlen[-1] < day:
                if month > 11:
                    zahlen.append(1)
                else:
                    zahlen.append(month + 1)
        if lgh <= 2: 
            if usepast is None or (usepast and zahlen[-1] <= month) or (not usepast and zahlen[-1] >= month):
                zahlen.append(year)
            elif usepast and zahlen[-1] > month:
                zahlen.append(year - 1)
            elif not usepast and zahlen[-1] < month:
                zahlen.append(year + 1)
    # check if year is in future
    if usepast and zahlen[2] < 100 and zahlen[2] > year - int(year/100) * 100:
        zahlen[2] =(int(year/100) - 1) * 100 + zahlen[2]
        alldigits = True
    # check date values
    monat = zahlen[1]
    if monat < 1: zahlen[1] = 1   
    if monat > 12: zahlen[1] = 12   
    tag = zahlen[0]
    if tag < 1: zahlen[0] = 1   
    if tag > 28: 
        if monat == 2:
            jahr = zahlen[2]
            if jahr%4 == 0: zahlen[0] = 29
            else: zahlen[0] = 28
        elif tag > 30:
            if monat%2:
                if monat > 7:  zahlen[0] = 30
                else:  zahlen[0] = 31
            else:
                if monat > 7:  zahlen[0] = 31
                else:  zahlen[0] = 30
    zahlstr = Afp_ArraytoString(zahlen)
    if len(zahlstr[1]) == 1:
        zahlstr[1] = '0' + zahlstr[1]
    if alldigits or len(zahlstr[2]) < 3:
        string = zahlstr[0] + "." + zahlstr[1] + "." + zahlstr[2]
    else:
        string = zahlstr[0] + "." + zahlstr[1] + "." + zahlstr[2][2:]
    return string
## check if string holds a time value, \n
# return the cleaned time string and the number of days extracted from this string
# @param string - string to be analysed
def Afp_ChZeit(string):
    if not string: return None, 0
    char = ":"
    if "." in string and not ":" in string: char = "."
    split = string.split(char)
    hours = int(split[0])
    minutes = None
    seconds = None
    if len(split) > 1:
        if split[1]:
            minutes = int(split[1])
        else:
            minutes = 0
        if len(split) > 2:
            if split[2]:
                seconds = int(split[2])
            else:
                seconds = 0
    else:
        minutes = 0
    added = 0
    if seconds:
        added = seconds/60
        seconds = seconds%60
    if minutes:
        minutes += added
        added = minutes/60
        minutes = minutes%60
    hours += added
    days = hours/24
    hours = hours%24
    zeitstr = str(hours)
    #if minutes:
    zeitstr += ":"
    if minutes < 10: zeitstr += "0"
    zeitstr += str(minutes)
    if seconds:
        zeitstr += ":"
        if seconds < 10: zeitstr += "0"
        zeitstr += str(seconds)
    if days == 1 and zeitstr == "0:00":
        days = 0
        zeitstr = "24:00"
    #print "Afp_ChZeit:", zeitstr, days
    return zeitstr, days

## convert "Superbase" Field.Filename to mysql tablenames used in select statements.
# @param string - string where names should be converted
# @param dateien - names of tables involved in this statement
def Afp_SbToDbName(string,dateien):
    unmasked, masked = Afp_maskedText(string)
    out_unmasked = []
    for part in unmasked:
        out_part = ""
        words = part.split()
        space = ""
        i = -1
        for word in words:
            i = -1
            if "." in word and not Afp_isFloatString(word):
                wsplit = word.split(".")
                if wsplit[1] in dateien: i = dateien.index(wsplit[1])
                else: i = dateien.index(wsplit[1].upper())
                if i > -1: 
                    out_part += space + "D" + str(i) + ".`" + wsplit[0] + "`"
            if i < 0: out_part += space + word
            space = " "
        out_unmasked.append(out_part)
    lgh = len(out_unmasked)
    lghm = len(masked)
    out_string = ""
    for i in range(0,lgh):
        if i: out_string += " "
        out_string += out_unmasked[i]
        if i < lghm: out_string += " \"" + masked[i] + "\""
    return out_string
## complete the select statement with the .table extension for all tablecolumns
# @param select - select statement to be completetd 
# @param dbname - name of table for extensions
def AfpSelectEnrich_dbname(select, dbname):
    if select is None: return None
    enriched = ""   
    if select:
        ssplit = select.split()
        lastentry = ""
        for entry in ssplit:
            if lastentry and  Afp_isCompare(entry):
                lastentry += "." + dbname
            if lastentry:
                if enriched: space = " "
                else: space = ""
                enriched += space + lastentry
            lastentry = entry
        enriched += " " + lastentry
    return enriched
         
   
    
