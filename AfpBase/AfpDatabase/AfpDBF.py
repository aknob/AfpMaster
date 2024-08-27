#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpDatabase.AfpExport
# AfpExport module provides the utilities to export Afp-database entries to different formats,
# the following formats are supported:
# - asc - ascii, fixed length (default length = 50)
# - csv - comma separated values (default field separator = ".")
# - dbf - dbase database format (either to be constructed or a template database is filled)
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        04 Feb. 2015 - data export to dbf inital code generated - Andreas.Knoblauch@afptech.de \n

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2023  afptech.de (Andreas Knoblauch)
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

import dbfpy
from dbfpy import dbf

from AfpBase.AfpUtilities.AfpBaseUtilities import *
from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpDatabase.AfpSQL import *

## writes data to dbf_file
# @param data - TableSelection holding the data to be written
# @param filename - name of file data is written to, \n
# @param template - template file which is used to create output, if type == list: description how to generate dbf-file fields [name, typ, parameter] 
# @param parameter -  dictionary how data is mapped into output file (output[entry] = value(parameter[entry])),
def Afp_writeToDBFFile(data, filename, template, parameter = None, debug = False):
    if debug: print("Afp_writeToDBFFile Entry: File:", filename, " Template:", template," Parameter:",  parameter)
    #print "Afp_writeToDBFFile Entry: Data:", data.data
    file = None
    if data:
        typ = type(template)
        if template: 
            if typ == list and type(template[0]) == list: 
                # create empty DBF, set fields
                file = Afp_createDbfFile(filename, template)
            elif Afp_existsFile(template):
                Afp_copyFile(template, filename)
                file = dbf.Dbf(filename)
            else:
                print("WARNING: Afp_writeToDBFFile, template file does not exist!")
    if not file is None and not parameter is None:
        felder = ""
        cols = []
        for entry in parameter:
            cols.append(entry)
            name = parameter[entry]
            #print "Afp_writeToDBFFile Entry:", entry, name
            felder +=  name + ","
        if felder: 
            felder = felder[:-1]
            #print "Afp_writeToDBFFile Felder:", felder, cols
            #print "Afp_writeToDBFFile Data:", data.data
            daten = data.get_values(felder)
            #print "Afp_writeToDBFFile Daten:", daten
            for i in range(len(daten)):
                rec = file.newRecord()
                lgh = len(daten[i])
                for j in range(len(cols)):
                    if j < lgh:
                        rec[cols[j]] = Afp_toDbfFormat(daten[i][j])
                if debug: print("Afp_writeToDBFFile Recording:", rec)
                rec.store()
        file.close()
## create a new dbf-file and return handle
# @param filename - name of file to be created
# @param parameter - parameter of file creation, list of  [name, typ, parameter 1, parameter 2, parameter 3]  for each field to be created
def Afp_createDbfFile(filename, parameter):
    file = dbf.Dbf(filename, new=True)
    for entry in parameter:
        #print "entry:", entry
        if len(entry) == 4:
            # ("BRUTTO", "N", 12, 2),
            file.addField((entry[0],entry[1],entry[2],entry[3]))
        elif len(entry) == 3:
            # ("NAME", "C", 15),
            file.addField((entry[0],entry[1],entry[2]))
        elif len(entry) == 2:
            # ("BIRTHDATE", "D"),
            file.addField((entry[0],entry[1]))
    return file
## convert data into dbf-compatible format
# @param data - data to be converted
def Afp_toDbfFormat(data):
    if type(data) == datetime.date:
        data = data.strftime("%y%m%d")
    return data
## print out content of dbf-file
# @param filename - name of file to be printed
def Afp_viewDbfFile(filename):
    if Afp_existsFile(filename):
        file = dbf.Dbf(filename)
        index = 0
        for rec in file:
            print("Display Record:", index)
            print(rec)
            index += 1
        print()
