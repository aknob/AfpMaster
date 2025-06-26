#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpDatabase.AfpSuperbase
# AfpSuperbase module provides 'Superbase' like interface to a MySql database. \n
# 'Superbase' was a database machine originally designed for Amiga and Atari machines in the late '80. \n
# It was ported to the Windows 16-bit system in the '90 and died with XP. \n
# This is the initial file of the 'BusAfp' project, as 'BusAfp' has been designed on 'Superbase' and started running in 1989. \n
# As this file has been created during the feasibility study of the project no proper documentation is available up to now, only the
# extern used methods of AfpSuperbase are documented - may be i'll find the time eventually. \n
# \n
# The AfpSuperbase module holds the classes:
# - AfpSbIndex
# - AfpSbDatei
# - AfpSuperbase
#
#   History: \n
#        26 Jum. 2025 - keep limit od database call constant for inner offset movement in 'select_plus_step' - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        15 Nov. 2018 - remove deprecated function 'Afp_extractValues' - Andreas.Knoblauch@afptech.de \n
#        20 Jan. 2015 - add array cache for next step selection \n
#                            -  shortcut for duplicate check - Andreas.Knoblauch@afptech.de \n
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

import MySQLdb

from AfpBase.AfpDatabase.AfpSQL import *
from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpUtilities.AfpBaseUtilities import *



## provides information if the field is numeric
# @param typ - type string of field description
# @param pure - flag if dates should not be considered numeric
def AfpSb_isNumericType(typ, pure = False):
    #print "AfpSb_isNumericType:", typ, pure
    if "int(" in typ:
        return True  
    elif not pure and AfpSb_isDateType(typ):
        return True
    else:
        return False
## provides information if the field is a date field
# @param typ - type string of field description
def AfpSb_isDateType(typ):
    if typ == "date": return True
    else: return False

## generates a dicitonaty of two lists
# @param keys - array of key values#
# @param values - array of values
def AfpSb_genDict(keys, values):
    dic = {}
    lgh = len(keys)
    if lgh == len(values):
        for i in range(0,lgh):
            dic[keys[i]] = values[i]
    return dic
  
## counts duplicate entries in rows
# @param rows - array of arrays to be analized
# @param direct - flag if the python '==' has to be used to compare values (True) or the internal routine 'Afp_compareSql'
# @param ind - same index for each row where values are compared
# @param ref - reference value is in row  number 'ref'
def AfpSb_countDuplicates(rows, direct, ind, ref = 0):
    count = -1
    ref_ind = -1
    all = False
    complete = False
    prev = Afp_combineValues(ind,rows[ref])
    if ref == 0: 
        # shortcut when complete array holds same values, or when last holds different value
        last = Afp_combineValues(ind,rows[-1])
        if direct: all = prev == last
        else: all = Afp_compareSql(prev, last)
        if all:
            count = len(rows) - 1
        elif len(rows) > 1:
            secondlast = Afp_combineValues(ind,rows[-2])
            if direct: complete = prev == secondlast
            else: complete = Afp_compareSql(prev, secondlast)
            if complete:
                count = len(rows) - 2
        if count > -1: ref_ind = 0
    if count < 0:
        if direct:
            for row in rows:
                value = Afp_combineValues(ind,row)
                if prev == value:
                    count += 1
                    if  rows.index(row) == ref:
                        ref_ind = count
        else:
            for row in rows:
                value = Afp_combineValues(ind,row)
                if Afp_compareSql(prev, value):
                    count += 1
                    if  rows.index(row) == ref:
                        ref_ind = count      
    #print "AfpSb_countDuplicates:", all, complete, direct, len(rows), count, ref_ind, prev 
    return count,ref_ind

## Index class to hold all values of current record (current row) of one table retrieved form database. \n
# This class provides a unique order which works symmertic moving forward and backward through the tables. \n
# This is problematic, as mysql does not provide such a thing especially on multiple identic index entries. \n
# \n
# In this class currently only the constructor is documented!
class AfpSbIndex(object):
    ## initialise index, load data from database table
    # @param db - name of database
    # @param dateiname - name of table to be used
    # @param indexname - name this index of the table
    # @param typename -  typestring of  this index 
    # @param index_ind -  index in fieldlist where data for this database-index comes from
    # @param db_cursor -  object (cursor) to point to database and allow queries
    # @param debug - flag for debug info
    def  __init__(self, db, dateiname, indexname, typename, index_ind, db_cursor, debug = False):
        # name of the index
        self.name = indexname 
        self.type = typename 
        self.db = db
        self.db_cursor = db_cursor
        self.datei = dateiname  # name of 'Datei' where index belongs to
      
        self.debug = False
        self.cache_threshold = 200
        self.imaxident = 2            # max. number of identic index-entries up to now
        self.index_ind =[]             # indices of fields used to generate this index
        self.index_bez = None      # names of fields used to generate this index
        self.indexwert = None      # index-entry used to find the actuel dataset
        self.indexoffset = None    # for identic entries: offset from dataset found by actuel index-entry
        self.indexdups = None      # for identic entries: number of identic entries
        self.uind_ind = None          # if unique index exsists in 'Datei': index of field building the unique index
        self.uindexwert = None     # if unique index exsists in 'Datei': value of unique index field
        self.where = None            # filter clause to be implied on  this index
        self.felder = None            # values of actuel dataset
        self.modified = False        # flag, if values have been modified
        self.endoffile = False        # flag if last action hit end of index      
        self.eofrev = None            # flag of direction of end of index      
        if index_ind > -1:  
            self.index_ind.append(index_ind)
            self.select_first()
            if not self.felder is None:
                self.indexwert = self.get_indexwert()
        self.debug = debug # set here to avoid SELECT output from select_first
        if self.debug: print("Superbase",self.datei,"Index Konstruktor",self.name)  
        # self.print_values()
    def __del__(self):
        if self.debug: print("Superbase",self.datei,"Index Destruktor",self.name)
    def set_debug(self):
        self.debug = True
    def unset_debug(self):
        self.debug = False
    def add_index_feld(self, index_ind, index_bez):
        self.index_ind  = index_ind 
        self.index_bez  = index_bez 
        self.select_first()
        if not self.felder is None:
                self.indexwert = self.get_indexwert()
    def eof(self):
        return self.endoffile
    def get_name(self):
        return self.name
    def get_where(self):
        return self.where
    def get_value(self, ind):
        if self.felder == None: return ""
        if type(ind) == int: # single value
            if len(self.felder) <= ind: return ""
            wert = self.felder[ind]
        else: # array
            wert = Afp_extractStringValues(ind, self.felder)
        #print "AfpSbIndex.get_value:", self.name, ind, type(ind),  wert
        return wert
    def get_values(self, indices=None):
        if self.felder == None: return None
        values = None
        if indices is None:
            values = self.felder
        else:
            for ind in indices:
                if values is None:
                    values = [self.felder[ind]]
                else:
                    values.append(self.felder[ind])
        return values
    def set_values(self, values, indices=None):
        if not self.felder is None:
            lgh = len(values)
            if (len(self.felder) == lgh):
                self.felder = values
                self.modified = True
            elif not indices is None and len(indices) == lgh:
                    for i in range(0,lgh):
                        ind = indices[i]
                        if ind in range(0,len(self.felder)):
                            if self.debug: print("AfpSbIndex.set_values:",self.felder[ind], values[i])
                            self.felder[ind] = values[i]
                            self.modified = True
            self.indexwert = self.get_indexwert()
            self.indexoffset = None
            self.indexdups = None
            self.endoffile = False
    def clear_values(self):
        if not self.felder is None:
            for i in range(0,len(self.felder)):
                if Afp_isString(self.felder[i]): self.felder[i] = ""
                else: self.felder[i] = 0
    def sync_to_index(self, index):
        if self.datei == index.datei:
            #print self.name, index.name
            FNr = index.get_value(0)
            #print FNr
            self.indexoffset = None
            self.indexdups = None
            indexwert = Afp_extractStringValues(self.index_ind, index.felder, True)
            #print "AfpSbIndex.sync_to_index:", indexwert, type(indexwert)
            self.indexwert = indexwert
            self.select_plus_step(0)
            equal = self.is_equal(index)
            while not equal and not self.endoffile and self.indexwert == indexwert:
                self.select_plus_step(1)
                equal =  self.is_equal(index)
                #print "AfpISbndex.sync_to_index:", equal, self.indexwert, indexwert, self.indexoffset, self.endoffile, FNr 
            return equal
        else: 
            return False
    def print_values(self):
        print(self.felder)
    def is_numeric(self, pure = False):
        if self.type == None:  return False
        return AfpSb_isNumericType(self.type, pure)   
    def is_date(self):
        if self.type == None:  return False
        return AfpSb_isDateType(self.type)
    def is_equal(self, index):
        equal = False
        if self.datei == index.datei:
            if not self.uindexwert is None:
                equal = self.uindexwert == index.uindexwert
                #print "AfpSbIndex.is_equal:", self.uindexwert, index.uindexwert
            else:
                lgh = len(self.felder)
                equal = True 
                for i in range(0,lgh):
                    equal = equal and self.felder[i] == index.felder[i]
        return equal
    def set_uind(self):
        self.uindexwert = self.get_indexwert(True)
    def set_uind_ind(self, ind):
        self.uind_ind = ind
        self.set_uind()
    def set_indexoffset(self, rows, offset, dup, ref, reverse):
        if offset > dup:
            self.indexoffset = None
            self.indexdups = None
            dup, reff = AfpSb_countDuplicates(rows,self.is_numeric(),self.index_ind,offset) 
            #print "AfpSbIndex.set_indexoffset:", dup, reff
            if dup > 0:
                self.indexdups = dup
                if reverse: self.indexoffset = self.indexdups - reff     
                else: self.indexoffset = reff     
        else:
            if ref > 0:
                self.indexdups = dup
                if reverse: self.indexoffset = self.indexdups - ref    
                else: self.indexoffset = ref    
            else:
                self.indexdups = dup
                if reverse: self.indexoffset = self.indexdups - offset     
                else: self.indexoffset = offset     
        #print "AfpSbIndex.set_indexoffset:", self.indexwert, self.indexoffset, self.indexdups
    def get_indexwert(self, use_uind = False):
        if use_uind:
            if self.uind_ind is None: return None
            index_ind = self.uind_ind
        else:
            index_ind = self.index_ind
        #print "AfpSbIndex.get_indexwert:", use_uind, self.index_ind, self.uind_ind, Afp_extractStringValues(index_ind, self.felder, True)
        return Afp_extractStringValues(index_ind, self.felder, True)
    def reverse_dup_bloc(self, rows, index, offset = 0):
        if self.is_date(): return rows # may be is_numeric() has to be used here
        ind = 0
        check_dup = True
        lgh = len(rows)
        rows_o = None
        while ind < lgh:
            dup = 0
            if check_dup: dup, ref = AfpSb_countDuplicates(rows,self.is_numeric(),index, ind)
            dup += 1
            if dup > 1:
                for i in range(dup):
                    if rows_o is None:
                        rows_o = [rows[ind+dup-i-1]]
                    else:
                        rows_o.append(rows[ind+dup-i-1])
                ind += dup
                #if self.debug: print "check_dup",ind, offset
                if ind > offset+1: check_dup = False
            else:  
                if rows_o is None:
                    rows_o = [rows[ind]]
                else:
                    rows_o.append(rows[ind])
                ind += 1
        #if self.debug:
            #ind = 0
            #print "reverse_dup_bloc:"
            #while ind < lgh:
                #print rows[ind][1],rows[ind][2],"  ",rows_o[ind][1],rows_o[ind][2]
                #ind += 1
        return rows_o
    def gen_index_clause(self, desc = False, first = False, indexwert = None):
        if self.debug: print("AfpSbIndex.gen_index_clause:", self.name, self.indexwert, self.index_bez, desc, first, indexwert)
        index_clause = ""
        if desc:
            unequal = "<="
            postfix = " DESC"
        else:
            unequal = ">="
            postfix = ""
        if indexwert is None:
            indexwert = self.indexwert
        if not indexwert:
            if self.is_numeric(True): indexwert = [1]
            else: indexwert = [""]
        if not type(indexwert) is list:
            indexwert = [indexwert]
        if self.index_bez is None:
            if first:
                index_clause =  " ORDER BY (" + self.name + ")" + postfix
            elif self.is_numeric(True):
                index_clause = (self.name + " " + unequal + " \"%d\" ORDER BY (" + self.name + ")" + postfix) % Afp_numericString(indexwert[0])
            else:
                index_clause = self.name + " " + unequal + " \"" + Afp_toInternDateString(indexwert[0]) + "\" ORDER BY (" + self.name + ")" + postfix
        else:
            lgh = len(self.index_bez)
            if Afp_isString(indexwert):
                indices = indexwert.split(" ")
            else: 
                indices = indexwert
            if len(indices) < lgh:
                for i in range(len(indices),lgh):
                    indices.append("")
            if lgh <= len(indices):
                for i in range(0,lgh):
                    if index_clause == "": plus = " "
                    else: plus = " and "
                    if i == lgh-1: sign = unequal
                    else : sign = "="
                    clause = self.index_bez[i] + " " + sign + " \"" + Afp_toString(indices[i]) + "\""
                    # skip this entry, if it is already set in where_clause
                    if self.where and clause in self.where: continue
                    index_clause += plus + clause
                index_clause += " ORDER BY " 
                for bez in self.index_bez:
                    index_clause += bez + " " + postfix + ","
                index_clause = index_clause[:-1]
        #print "AfpSbIndex.gen_index_clause:", index_clause
        return index_clause
    def gen_first_indexwert(self, order, where_clause):
        values = []
        index_clause = ""
        for name in self.index_bez:
            Befehl = "SELECT " + name + " FROM " + self.db + "." + self.datei + where_clause + index_clause +" ORDER BY (" + name + ")" + order + " LIMIT 0,1"
            if self.debug: print("AfpSbIndex.gen_first_indexwert execute:", Befehl)
            self.db_cursor.execute (Befehl)
            row = self.db_cursor.fetchone()
            if row: values.append(row[0])
        self.indexwert =  Afp_extractStringValues(None, values, True)
        if self.debug: print("AfpSbIndex.gen_first_indexwert:", self.indexwert)
    def gen_next_indexwert(self, order):
        values = []
        lgh = len(self.index_bez)
        indices = self.indexwert[:]
        #print "AfpSbIndex,gen_next_indexwert in:",self.indexwert, indices, self.index_bez
        indices[lgh - 1] = ""
        if order == "DESC": unequal = "<"
        else:  unequal = ">"
        eof = True
        ind = lgh - 2   
        where_clause = ""
        if not self.where is None: where_clause = "(" + self.where + ") and "
        namen = Afp_ArraytoLine(self. index_bez,", ")
        if order == "DESC": 
            orderby = Afp_ArraytoLine(self. index_bez,", ",None," " + order)
        else:
            orderby = namen
        while eof and ind >= 0:
            name = self. index_bez[ind]
            equal_clause = name + " = \"" + indices[ind] + "\""
            # skip this entry, if value is fixed in where_clause
            if equal_clause in where_clause: 
                ind -= 1
                continue
            index_clause = name + " " + unequal +" \"" + indices[ind] + "\""
            Befehl = "SELECT " + namen + " FROM " + self.db + "." + self.datei +  " WHERE " + where_clause + index_clause + " ORDER BY " + orderby + " LIMIT 0,1"
            if self.debug: print("AfpSbIndex.gen_next_indexwert:", Befehl)
            self.db_cursor.execute (Befehl)
            row = self.db_cursor.fetchone()
            if row:
                for i in range(lgh - ind):
                    indices[ind+i] = row[i]
                eof = False
            else:
                indices[ind] = ""
                ind -= 1
        if not eof:
            self.endoffile = False
            self.indexoffset = None
            self.indexdups = None
            self.indexwert =  Afp_extractStringValues(None, indices, True)
        if self.debug: print("AfpSbIndex,gen_next_indexwert:", self.indexwert)
    def cached_select(self, Befehl):
        rows = None
        use_cache = False
        ident = Afp_getToLastChar(Befehl, ",")
        anz = int(Befehl[len(ident):])
        #print "AfpSbIndex.cached_select:", self.imaxident, anz, self.cache_threshold
        #print "AfpSbIndex.cached_select ident:", ident
        if anz > self.cache_threshold:
            use_cache = True
            if self.cache:
                if self.cache.is_valid(ident):
                    lgh = self.cache.get_length()
                    if lgh < anz-1:
                        Add = ident[:-2] + str(lgh) + "," + str(anz) 
                        if self.debug: print("AfpSbIndex.cached_select add:", Add)
                        self.db_cursor.execute (Add)     
                        added = self.db_cursor.fetchall ()
                        self.cache.add_array(ident, added)
                    rows = self.cache.read_array(ident)  
        else:
            use_cache = False
            self.cache = None
        if rows is None:
            if self.debug: print("AfpSbIndex.cached_select:", Befehl)
            self.db_cursor.execute (Befehl)     
            rows = self.db_cursor.fetchall ()
            if use_cache:
                self.cache = AfpArrayCache(ident, rows, self.debug)
        return rows
    def select_first_last(self, order):
        where_clause = ""
        if not self.where is None: 
            where_clause = " WHERE ("+ self.where + ")"
        if  not self.index_bez is None: 
            self.gen_first_indexwert(order, where_clause)
            if where_clause != "": where_clause += " and" 
            else: where_clause = " WHERE"
        index_clause = self.gen_index_clause(order == "DESC", True)
        if order == "DESC":      
            anz = self.imaxident 
            while anz > 0:
                limit =  (" LIMIT 0,%d") %  anz
                Befehl = "SELECT * FROM " + self.db + "." + self.datei + where_clause + index_clause + limit
                if self.debug: print("AfpSbIndex.select_first_last:",Befehl)
                self.db_cursor.execute (Befehl)
                rows = self.db_cursor.fetchall ()
                if rows:
                    rows = self.reverse_dup_bloc(rows, self.index_ind)
                    dup, ref = AfpSb_countDuplicates(rows, self.is_numeric(), self.index_ind)
                else:
                    dup = 0
                # print rows
                # print "Ende rows", anz, dup
                if dup == anz-1:
                    anz += dup
                else:
                    anz = 0
                    if dup >= self.imaxident:
                        self.imaxident = dup + 2
                        # print "MaxIdent:",self.imaxident , self.indexoffset   
                    self.set_indexoffset(rows, 0, dup, dup, True)
                    if self.debug: print("AfpSbIndex.select_first_last indexoffset:", self.indexoffset, self.indexdups)
        else:
            Befehl = "SELECT * FROM " + self.db + "." + self.datei + where_clause + index_clause + " LIMIT 0,1"
            if self.debug: print("AfpSbIndex.select_first_last:", Befehl)
            self.db_cursor.execute (Befehl)
            rows = self.db_cursor.fetchall ()
        if len(rows) > 0:
            # datenfelder einfuellen
            self.felder = list(rows[0])    
            self.modified = False
            self.indexwert = self.get_indexwert()
            self.indexoffset = None
            self.indexdups = None
            self.set_uind()
            self.endoffile = False
        else:
            self.endoffile = True
            self.eofrev = (order == "DESC")
        if self.debug: print("AfpSbIndex.select_first_last:", self.indexwert, self.endoffile, self.eofrev)
    def select_step(self, in_step):
        #print  "AfpSbIndex.select_step:", self.name, self.endoffile, self.index_bez, in_step
        self.select_plus_step(in_step)
        if self.endoffile and  not self.index_bez is None:
            if in_step < 0: order = "DESC"
            else: order = ""
            self.gen_next_indexwert(order)
            if self.endoffile == False:
                self.select_plus_step(0)
    def select_plus_step(self, in_step):
        if self.debug: print("AfpSbIndex.select_plus_step input:", in_step)
        step = in_step
        if in_step < 0:
            step *= -1
        if self.indexoffset is None:
            offset = 0
        else:
            if in_step < 0: offset = self.indexdups - self.indexoffset
            else: offset = self.indexoffset
        index_clause = self.gen_index_clause(in_step < 0)
        where_clause = ""
        if not self.where is None: where_clause = "(" + self.where + ") and "
        anz = self.imaxident
        if offset + step > anz: anz = offset + step
        while anz > 0:          
            limit =  (" LIMIT 0,%d") % anz
            Befehl = "SELECT * FROM " + self.db + "." + self.datei +" WHERE "+ where_clause + index_clause + limit
            if self.debug: print("AfpSbIndex.select_plus_step:",Befehl, "Offset:", offset)
            rows = self.cached_select(Befehl)
            dup = 0
            ref = 0
            dup_next = 0 
            #print "AfpSbIndex.select_plus_step: 1",Afp_getNow(), dup
            if rows and len(rows) > 1:
                dup, ref = AfpSb_countDuplicates(rows,self.is_numeric(),self.index_ind)        
            offstep = offset + step 
            #print "AfpSbIndex.select_plus_step: 2",Afp_getNow(), dup, offset
            if in_step < 0:
                rows = self.reverse_dup_bloc(rows,self.index_ind, offstep)
            # dup has to be checked for one step in advance
            if rows and offstep > dup and offstep < len(rows):
                dup_next, reff = AfpSb_countDuplicates(rows,self.is_numeric(),self.index_ind,offstep) 
                dup_next += 1
            #print "AfpSbIndex.select_plus_step 3:",Afp_getNow(), dup, dup_next, anz, dup+dup_next == anz-1
            if dup+dup_next == anz-1:
                anz += dup+dup_next
            else:
                anz = 0
                if dup >= self.imaxident:
                    self.imaxident = dup + 2
                    self.set_indexoffset(rows, offset, dup, ref, in_step < 0)
                    if self.indexoffset is None:
                        offset = 0
                    else:
                        if  in_step < 0: offset = self.indexdups - self.indexoffset
                        else: offset = self.indexoffset
                    # print "MaxIdent:",self.imaxident , self.indexoffset   
        # datenfelder einfuellen
        offset += step      
        #print "AfpSbIndex.select_plus_step rows:", in_step, "\n", rows
        if self.endoffile and self.eofrev != (in_step < 0): offset -= step
        if rows and len(rows) > offset:
            self.felder = list(rows[offset])   
            self.modified = False        
            self.indexwert = self.get_indexwert()
            self.set_indexoffset(rows, offset, dup, ref,  in_step < 0)
            self.set_uind()
            self.endoffile = False
        else:
            self.endoffile = True
            self.eofrev = (in_step < 0)
        if self.debug: print("AfpSbIndex.select_plus_step:", self.indexwert, self.indexoffset, self.indexdups, self.endoffile)
    def select_keywert(self, indexwert):
        if self.is_numeric() != Afp_isNumeric(indexwert): 
            print("WARNING: AfpSuperbase.select_keywert: FALSCHER EINGABETYP", Afp_isNumeric(indexwert))
            if self.debug: print(self.datei, self.name, self.type, type(indexwert))
            if self.is_numeric(): 
                if not indexwert: indexwert = 0
                indexwert = int(indexwert)
            else: 
                indexwert =  ("%5.2f")%(indexwert)
        do_selection = True
        anz = 0
        dup = -1
        ident = self.imaxident
        where_clause = ""
        if not self.where is None: where_clause = "("+self.where+") and "
        index_clause = self.gen_index_clause(False, False, indexwert) 
        while do_selection:        
            limit =  (" LIMIT 0,%d") % ident
            #print "AfpSbIndex.select_keywert where:", where_clause, "Index:", index_clause
            Befehl = "SELECT * FROM " + self.db + "." + self.datei +" WHERE "+ where_clause + index_clause + limit
            if self.debug: print("AfpSbIndex.select_keywert:", Befehl)
            self.db_cursor.execute (Befehl)
            rows = self.db_cursor.fetchall() 
            anz =  self.db_cursor.rowcount
            do_selection = False
            if anz > 0 :
                dup, ref = AfpSb_countDuplicates(rows,self.is_numeric(),self.index_ind)
            else:
                dup = 0
            #print rows
            #print 'Ende rows',anz,dup
            if anz == dup+1 and dup > 0 and anz == ident:
                ident *= 2
                do_selection = True
        if dup >= self.imaxident:
            self.imaxident = dup + 2
            # print "MaxIdent:",self.imaxident
        if len(rows) > 0:
            self.felder = list(rows[0]) 
            self.modified = False         
            self.indexwert = Afp_maskiere(indexwert)
            self.indexoffset = None
            self.indexdups = None
            self.set_uind()
            self.endoffile = False
        else:
            self.endoffile = True
            self.eofrev = None 
        if self.debug: print("AfpSbIndex.select_keywert:", indexwert, self.indexwert)
    def select_where(self, where_clause):
        if where_clause == "":
            self.where = None
        else:   
            self.where = where_clause
    def select_first(self):
        # print "AfpSbIndex SELECT FIRST", self.date, self.name   
        self.select_first_last("")
    def select_last(self):
        # print "AfpSbIndex SELECT LAST",self.date, self.name   
        self.select_first_last("DESC")
    def select_current(self):
        # print "AfpSbIndex SELECT CURRENT", self.date, self.name
        self.select_step(0)
    def select_next(self):
        if self.debug: print("AfpSbIndex SELECT NEXT", self.datei, self.name)
        self.select_step(1)
    def select_previous(self):
        if self.debug: print("AfpSbIndex SELECT PREVIOUS", self.datei, self.name)
        self.select_step(-1)
    def select_key(self, wert):
        # print "AfpSbIndex SELECT KEY",wert, self.date, self.name
        self.select_keywert(wert)
      
## Table (Datei) class, to generate and hold all indices of a table, provide syncronation 
# and handle locks and database access apart from reading from the table.  \n
# \n
# In this class currently only the constructor is documented!
class AfpSbDatei(object):
    ## initialise 'Datei' object
    # @param db - name of database
    # @param dateiname - name of table to be used
    # @param db_cursor -  object (cursor) to point to database and allow queries
    # @param debug - flag for debug info
    def  __init__(self, db, dateiname, db_cursor, debug = False):
        self.db = db
        self.db_cursor = db_cursor
        self.name = dateiname
        self.debug = debug
        self.feld = None
        self.feldtyp = None
        self.index = None
        self.indexname = None
        self.CurrentIndex = None
        self.UniqueIndex = None
        if self.debug: print("AfpSbDatei Konstruktor",dateiname)      
        self.open()
    def __del__(self):
        if self.debug: print("AfpSbDatei Destruktor",self.name)
    def open(self):
        name = self.name
        db = self.db
        db_cursor = self.db_cursor
        db_cursor.execute ("SHOW FIELDS FROM " + name)
        rows = db_cursor.fetchall ()
        count = 0;
        for row in rows:
            feldname = row[0]
            feldtyp = row[1]
            feldindex = row[3]
            if self.feld is None:
                self.feld = [feldname]
                self.feldtyp = [feldtyp]
            else:
                self.feld.append(feldname)
                self.feldtyp.append(feldtyp)
            if feldindex != "":
                if self.index is None:
                    self.index = [AfpSbIndex(db, name,feldname,feldtyp,count,db_cursor,self.debug)]
                    self.indexname = [feldname]
                else:
                    self.index.append(AfpSbIndex(db, name,feldname,feldtyp,count,db_cursor,self.debug))
                    self.indexname.append(feldname)
                if feldindex == "PRI":
                    self.UniqueIndex = self.index[-1]
                    self.UniqueIndex.set_uind_ind([count])
            count += 1
        db_cursor.execute ("SHOW INDEX FROM " + name)
        rows = db_cursor.fetchall ()
        inds = []
        felds = []
        for row in rows:
            feldname = row[4]
            indexname = row[2]
            if indexname == "PRIMARY": indexname = feldname
            if indexname != feldname:
                seq = int(row[3])
                if seq == 1:
                    if inds:
                        self.index[-1].add_index_feld(inds, felds)
                        inds = []
                        felds = []
                    self.index.append(AfpSbIndex(db, name,indexname,None,-1,db_cursor,self.debug))  
                    self.indexname.append(indexname)
                inds.append(self.feld.index(feldname))
                felds.append(feldname)
        if inds:
            self.index[-1].add_index_feld(inds, felds)
        if self.UniqueIndex == None:
            self.CurrentIndex = self.index[0]
        else:
            self.CurrentIndex = self.UniqueIndex
            for index in self.index:
                index.set_uind_ind(self.UniqueIndex.uind_ind)
    def set_debug(self):
        self.debug = True
        for ind in self.index:
            ind.set_debug()
    def unset_debug(self):
        self.debug = False
        for ind in self.index:
            ind.unset_debug()
    def set_index(self, indexname=None, permanent=False):
        CurrentIndex = self.CurrentIndex
        if not(indexname is None):
            ind = -1
            if indexname in self.indexname: ind = self.indexname.index(indexname)
            if ind >= 0: CurrentIndex = self.index[ind]  
        if permanent: self.CurrentIndex = CurrentIndex
        #print self.name,CurrentIndex.name, self.CurrentIndex.name
        return CurrentIndex
    def sync_index(self, syncronise = None, reference = None):
            ref = self.set_index(reference)
            if syncronise is None:
                sync_indices = self.index
            else:
                sync_indices = [self.set_index(syncronise)]
            for index in sync_indices:
                index.sync_to_index(ref)
    def set_lock(self, typ, indexname=None, post_exe=True):
        Befehl = ""
        Index = self.set_index(indexname)
        uni = not self.UniqueIndex is None 
        # manipulate all table-entries having the actuel index-value
        # if a unique index exsits, only this actuel entry will be manipulated
        if uni:  where_clause = (self.UniqueIndex.name + " = \"%d\" ") % Index.uindexwert
        else:
            if Index.is_numeric():  where_clause = (Index.name + " = \"%d\" ") % Index.indexwert     
            else:  where_clause = Index.name + " = \"" + Index.indexwert +"\"" 
        pure = True
        commit = False
        if typ == "lesen":
            # readlock: SELECT ... FROM ... LOCK IN SHARED MODE
            Befehl = "SELECT * FROM "  + self.db + "." + self.name + " WHERE "  + where_clause + " LOCK IN SHARE MODE;"
        elif typ == "sperren":
            # writelock: SELECT ... FROM ... FOR UPDATE 
            Befehl = "SELECT * FROM "  + self.db + "." + self.name + " WHERE "  + where_clause + " FOR UPDATE;"
        elif typ == "neu":
            # Neu: INSERT INTO ... VALUES (...)
            value_clause =  (" ( %(items)s ) VALUES ( %(values)s );") %  {"items" : ",".join( self.feld), "values" : ",".join( ["%s"]*len(Index.felder) ) }
            Befehl = "INSERT INTO "  + self.db + "." + self.name + value_clause + ";"
            pure = False
            commit = True
        elif typ == "speichern":
            # update: UPDATE ... SET ... WHERE ...
            if uni and Index.modified:
                # unique index is numeric!
                set_clause =    (" SET %(set)s WHERE ") %   {"set"  : ",".join( [str(i)+"=%s" for i in self.feld] ) }
                Befehl =  "UPDATE " + self.db + "." + self.name +  set_clause + where_clause +";" 
                pure = False
                commit =True
        elif typ == "loeschen":    
            # deletes all table-entries having the actuel index-value
            # if a unique index exsits, only this actuel entry will be deleted
            Befehl = "DELETE FROM " + self.db + "." + self.name + " WHERE "  + where_clause + ";"
            commit = True
        elif typ == "alle":
            # Table Lock
            Befehl = "LOCK TABLES"    
        elif typ == "freigeben":
            # Table Lock
            Befehl = "ROLLBACK;"
        # mysql statement will be executed here
        if self.debug: print("AfpSbDatei.set_lock ",typ, pure, commit, ": ",Befehl)
        res = 0
        if pure:
            res = self.db_cursor.execute(Befehl)
        else:
            res = self.db_cursor.execute(Befehl, Index.felder)
        if uni and res != 1 and not typ == "freigeben": print("ERROR AfpSbDatei: Fehler in Datenbankbefehl!", res)
        if post_exe:
            # write modification to database
            if commit: self.db_cursor.execute("COMMIT;")
            if typ == "loeschen": Index.select_current()
    def set_lock_replace(self, values, indexname=None):
        Index = self.set_index(indexname)
        uni = not self.UniqueIndex is None 
        if uni:
            self.set_lock("speichern", indexname)
        else:
            lgh = len(self.feld)
            exe = True
            for value in values:
                if len(value) != lgh: exe = False
            if exe:
                self.set_lock("loeschen", indexname, False)
                for value in values:
                    Index.set_values(value)
                    self.set_lock("neu", indexname, False)
                self.db_cursor.execute("COMMIT;")
                Index.select_current()
    def get_value(self, feldname=None):
        ind = self.CurrentIndex.index_ind
        if not(feldname is None):
            if feldname in self.feld: ind = self.feld.index(feldname)
        wert = self.CurrentIndex.get_value(ind)
        #print feldname,self.CurrentIndex.name,self.name,ind, wert
        return wert
    def get_values(self, feldnamen=None, indexname=None):
        Index = self.set_index(indexname)
        if feldnamen is None:
            values = Index.get_values(None)
        else:
            indices = None
            for name in feldnamen:
                ind =   self.feld.index(name)
                if indices is None:
                    indices = [ind]
                else:
                    indices.append(ind)
            values = Index.get_values(indices)
        return values
    def set_values(self, feldvalues, feldnamen=None, indexname=None):
        Index = self.set_index(indexname)
        lgh = len(feldvalues)
        indices = None
        if feldnamen is None:
            if len(self.feld) == lgh:
                Index.set_values(feldvalues)
        elif len(feldnamen) == lgh:
            for i in range(0,lgh):
                ind = self.feld.index(feldnamen[i])
                if indices is None:
                    indices = [ind]
                else:
                    indices.append(ind)
            Index.set_values(feldvalues, indices)
    def set_new_values(self, feldvalues, feldnamen=None, indexname=None):
        Index = self.set_index(indexname)
        Index.clear_values()
        self.set_values(feldvalues, feldnamen, indexname)
      
## This class provides the frontend of the database in a way 'Superbase' used to do. \n
class AfpSuperbase(object):
    ## initialise frontend, load data from database table
    # @param globals - global variables including the database connection
    # @param debug - flag for debug info
    def  __init__(self, globals, debug = False):
        self.globals = globals
        self.datei =  None
        self.dateiname = None
        self.debug = debug
        self.dats = 0 
        self.CurrentFile = None
        self.selections = None
        if self.debug: print("AfpSuperbase Konstruktor")
    ## destructor
    def __del__(self):
        if self.debug: print("AfpSuperbase Destruktor")
    ## method to switch debug on,
    # to allow debugging from a certain point in the programflow
    def set_debug(self):
        self.debug = True
        if self.debug: print("AfpSuperbase: DEBUG flag set!")
        self.globals.get_mysql().set_debug()
        for dat in self.datei:
            dat.set_debug()
    ## method to switch debug off again
    def unset_debug(self):
        if self.debug: print("AfpSuperbase: DEBUG flag removed!")
        self.debug = False
        self.globals.get_mysql().unset_debug()
        for dat in self.datei:
            dat.unset_debug()
    ## hand over the used mysql database connection
    def get_mysql(self):
        return self.globals.get_mysql()
    ## open connection to a certain table (Datei) and retrieve data for the different indices
    # @param Dateiname - name of the table
    def open_datei(self, Dateiname):
        if self.datei == None:
            self.datei = [AfpSbDatei(self.globals.get_mysql().get_dbname(Dateiname), Dateiname, self.globals.get_mysql().get_cursor(), self.debug)] 
            self.dateiname = [Dateiname]
            self.CurrentFile = self.datei[self.dats]
            self.dats += 1
        else:
            if self.is_open(Dateiname):
                ind = self.dateiname.index(Dateiname)
                self.CurrentFile = self.datei[ind]
            else:
                self.datei.append(AfpSbDatei(self.globals.get_mysql().get_dbname(Dateiname), Dateiname, self.globals.get_mysql().get_cursor(), self.debug))
                self.dateiname.append(Dateiname)
                self.CurrentFile = self.datei[self.dats]
                self.dats += 1
    ## return flag if table has been opened
    # @param Dateiname - name of the table
    def is_open(self, Dateiname):
        return Dateiname in self.dateiname
    ## return table 'Datei' object 
    # @param dateiname - name of the table
    # @param permanent - flag to mark this as the actuel table 'Datei' object
    def identify_file(self, dateiname=None, permanent=False):
        CurrentFile = self.CurrentFile
        if not(dateiname is None):
            ind = -1
            if dateiname in self.dateiname: ind = self.dateiname.index(dateiname)
            if ind >= 0: CurrentFile = self.datei[ind]
        if permanent: 
            self.CurrentFile = CurrentFile
        return CurrentFile
  ## return index object 
    # @param indexname - name of the index
    # @param dateiname - name of the table the index belongs to. None - actuel table is used
    # @param permanent - flag to mark this as the actuel table 'Datei' object
    def identify_index(self, indexname=None, dateiname=None, permanent=False):
        CurrentFile = self.identify_file(dateiname, permanent)
        CurrentIndex = CurrentFile.set_index(indexname, permanent)
        return CurrentIndex
    ## syncronise two or all indices to point to the same database entry
    # @param syncronise - indexname to be syncronised. None - all indices of indicated table are syncronised
    # @param dateiname - name of the table both indices belong to. None - actuel table is used
    # @param reference - indexname of index which points to target database entry. None - current index of table is used
    def set_index(self, syncronise=None, dateiname=None, reference=None):
        if self.debug: print("AfpSuperbase: SET INDEX",syncronise,dateiname,reference)
        CurrentFile = self.identify_file(dateiname)
        CurrentFile.sync_index(syncronise, reference)
    ## set the actuel table 'Datei' object
    # @param dateiname - name of the table
    def CurrentFileName(self, dateiname):
        if self.debug: print("AfpSuperbase: CurrentFileName",dateiname)
        self.identify_file(dateiname, True)
    ## set the actuel index object
    # @param indexname - name of index
    # @param dateiname - name of the table, index belongs to.
    def CurrentIndexName(self, indexname, dateiname=None):
        if self.debug: print("AfpSuperbase: CurrentIndexName", indexname, dateiname)
        self.identify_index(indexname, dateiname, True)
    ## set and reload the actuel or named index
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def select_current(self, indexname=None, dateiname=None):
        if self.debug: print("AfpSuperbase: SELECT CURRENT") 
        CurrentIndex = self.identify_index(indexname, dateiname)
        CurrentIndex.select_current()
        if CurrentIndex.eof():
            CurrentIndex.select_last()
    ## set the actuel or named index to first database entry in order
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def select_first(self, indexname=None, dateiname=None):
        if self.debug: print("AfpSuperbase: SELECT FIRST")
        CurrentIndex = self.identify_index(indexname, dateiname)
        CurrentIndex.select_first()
    ## set the actuel or named index to last database entry in order
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def select_last(self, indexname=None, dateiname=None):
        if self.debug: print("AfpSuperbase: SELECT LAST")
        CurrentIndex = self.identify_index(indexname, dateiname)
        CurrentIndex.select_last()
    ## set the actuel or named index to previous database entry in order
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def select_previous(self, indexname=None, dateiname=None):
        if self.debug: print("AfpSuperbase: SELECT PREVIOUS", dateiname, indexname)
        CurrentIndex = self.identify_index(indexname, dateiname)
        CurrentIndex.select_previous()
    ## set the actuel or named index to next database entry in order
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def select_next(self, indexname=None, dateiname=None):
        if self.debug: print("AfpSuperbase: SELECT NEXT", dateiname, indexname)
        CurrentIndex = self.identify_index(indexname, dateiname)
        CurrentIndex.select_next()
    ## set the actuel or named index to first database entry which matches the indicated keyword, \n
    # if no entry matching this keyword is found, index is set to next entry following in index order.
    # @param wert - keyword for database entry searched
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def select_key(self, wert, indexname=None, dateiname=None):
        if self.debug: print("AfpSuperbase: SELECT KEY", wert, dateiname, indexname)
        CurrentIndex = self.identify_index(indexname, dateiname)
        CurrentIndex.select_key(wert)     
    ## set a filter on index, only database entries are accepted which match that filter, \n
    # the filter is set permanently and has to be removed by the call of this method with an empty filter clause.
    # @param where_clause - filter clause to be applied on index
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def select_where(self, where_clause, indexname=None, dateiname=None):
        CurrentIndex = self.identify_index(indexname, dateiname)
        CurrentIndex.select_where(where_clause) 
    ## set a lock on the current database entry  or perform database transaction 
    # @param typ - typ of lock/transaction:
    # - "lesen": readlock
    # - "sperren": writelock (update)
    # - "alle": lock complete table
    # - "neu": insert data in index into table
    # - "speichern": execute update data in table
    # - "loeschen": delete all data from table having the actuel index value
    # - "freigeben": rollback
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def set_lock(self, typ, indexname=None, dateiname=None): 
        CurrentFile = self.identify_file(dateiname)
        CurrentFile.set_lock(typ, indexname) 
    ## return flag if end of file is reached in indexorder
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def eof(self, indexname=None, dateiname=None):  
        CurrentIndex = self.identify_index(indexname, dateiname)       
        if self.debug: print("AfpSuperbase: EOF", dateiname, indexname, CurrentIndex.eof()) 
        return CurrentIndex.eof() 
    ## return flag if end of file is NOT reached in indexorder
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def neof(self, indexname=None, dateiname=None):
        if self.eof(indexname, dateiname):
            return False
        else:
            return True
    ## get value of a field in the actuel or indicated table
    # @param DateiFeld - "column.table" of the actuel index (row)
    def get_value(self, DateiFeld=None):
        datei = self.CurrentFile
        feld = DateiFeld
        if not DateiFeld is None:
            liste = DateiFeld.split(".")
            feld = liste[0]
            if len(liste) > 1: 
                datei = self.datei[self.dateiname.index(liste[1])]
        wert = datei.get_value(feld)  
        return wert
    ## get a string of the value of a field in the actuel or indicated table, 
    # @param DateiFeld - "column.table" of the actuel index (row)
    # @param intern - flag for date representation: 
    # - true - yyyy-mm-dd, 
    # - false - dd.mm.yy
    def get_string_value(self, DateiFeld=None, intern = False):
        wert = self.get_value(DateiFeld)
        if intern:
            string = Afp_toInternDateString(wert)
        else:
            string = Afp_toString(wert)
        return string
    ## generate a AfpSQLTableSelection object from the current status \n
    # used for interaction of the AfpSuperbase and the AfpSQL model
    # @param dateiname - name of the table
    # @param main_index - unique index for data extraction, None - use actuel index   
    # @param debug - flag for debug info
    def gen_selection(self, dateiname, main_index = None, debug = False):
        if self.is_open(dateiname):
            datei = self.identify_file(dateiname)
            select = None
            if not main_index is None:
                wert = self.get_string_value(main_index + "." + dateiname)
                select = main_index + " = " + wert
            mysql = self.globals.get_mysql()
            selection = AfpSQLTableSelection(mysql, dateiname, debug,  main_index, datei.feld)
            selection.load_datei_data(datei, select)
            return selection
    ## modify data values in an index 
    # @param feldnamen - list of column (field) names of this index (row)
    # @param feldwerte - list of new values for this fileds  
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def set_values(self, feldnamen, feldwerte, indexname=None, dateiname=None):
        datei = self.identify_file(dateiname)
        datei.set_values(feldwerte, feldnamen, indexname)
    ## modify data values in an index, clear all other values
    # @param feldnamen - list of column (field) names of this index (row)
    # @param feldwerte - list of new values for this fileds  
    # @param indexname - name of index. None - the actuel index is used.
    # @param dateiname - name of the table, index belongs to. None - the actuel table is used.
    def set_new_values(self, feldnamen, feldwerte, indexname=None, dateiname=None):
        datei = self.identify_file(dateiname)
        datei.set_new_values(feldwerte, feldnamen, indexname)
    ## set value of one field in the actuel or indicated table
    # @param wert - new value of indicated field
    # @param DateiFeld - "column.table" of the actuel index (row)
    def set_value(self, wert, DateiFeld = None):
        dateiname = None
        feldname = None
        if not DateiFeld is None:
            split = DateiFeld.split(".")
            if len(split) > 1: dateiname = split[1]
            feldname = split[0]
        datei = self.identify_file(dateiname)      
        if feldname is None: 
            feldname = datei.CurrentIndex.get_name()
        datei.set_values([wert],[feldname])
    ## display data in console - for debug purpose only
    # @param DateiFeld - list of "column.table" of the actuel index (row) \n
    #  - None: display all data of the current index in the current table
    def view(self, DateiFeld=None):
        if DateiFeld is None:
            self.CurrentFile.CurrentIndex.print_values()
        else:
            liste = DateiFeld.split(",")
            line = ''
            for li in liste:
                wert = self.get_value(li)
                line += (li + ": " + "%s ") % wert 
            print(line)
