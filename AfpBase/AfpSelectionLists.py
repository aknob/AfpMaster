#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpSelectionLists
# AfpSelectionLists module provides the base class for all 'Selection Lists',
# it holds the calsses
# - AfpSelectionList
# - AfpPaymentList
# - AfpOrderedList
#
#   History: \n
#        24 Nov. 2024 - AfpPaymentList.get_account: always check if output ist numeric - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        21 Dez. 2020 - separated from AfpBaseRoutines and AfpOrderedList implemented- Andreas.Knoblauch@afptech.de

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

from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpUtilities.AfpBaseUtilities import *
from AfpBase.AfpBaseRoutines import Afp_getSpecialAccount


## routine to order list of selection lists due to one field
# @param datas - list of selection lists to be sorted
# @param sorttyp - field to sort output 
# @param sortdef - if given, default value to be set instead of 'None' values
# - sorttyp == "Namen": special routine for complete names, the method 'get_name' has to be supplied
# - the method 'get_value(sorttyp)' will be called
def Afp_orderSelectionLists(datas, sorttyp, sortdef=None):
        sortlist = []
        for data in datas:
            if sorttyp == "Namen":
                sortlist.append(data.get_name(True))
            else:
                sortlist.append(data.get_value(sorttyp))
                if sortdef and sortlist[-1] is None:
                    sortlist[-1] = sortdef
        sortlist, datas = Afp_sortSimultan(sortlist, datas)
        return datas
        
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
        self._tmp = None
        self.tagmap = None
        self.debug = debug
        self.new = False
        self.international_output= False
        self.tables = self.mysql.get_tables()
        # if copies of files into the archiv are needed, fill in here
        self.archiv_copy_needed = []
        self.last_selected_file = None
        if self.debug: print("AfpSelectionList Konstruktor",listname)
    ## destructor
    def __del__(self):   
        if self.debug: print("AfpSelectionList Destruktor") 
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
    ## return main selection table of this SelectionList
    def get_mainselection(self):
        return self.mainselection
    ## return main index of this SelectionList
    def get_mainindex(self):
        return self.mainindex
    ## return mayor type of this SelectionList, default: program name read from globals
    def get_mayor_type(self):
        #print "AfpSelectionList.get_mayor_type:", self.get_globals().get_value("name")
        return self.get_globals().get_value("name")
    ## set if intern date shoulkd be used for output
    # @param flag - if given, flag if value should be set to 'True'
    def set_international_output(self, flag=True):
        if flag:
            self.international_output = True
        else:
            self.international_output = False
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
            if "AND" in select:
                split = select.split("AND")
                for sp in split:
                    if "." in sp: select = sp.strip()
            split = select.split("=")
            target = split[0].strip()
            if  "." in target: target = target.split(".")[0]
        return target
    ## return an afp-unique identifier of this SelectionList
    def get_identifier(self):
        return self.mainselection + self.get_string_value()
        #return self.listname + self.get_string_value()
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
        print("AfpSelectionList.view():", self.get_listname())
        print(self.get_mainindex(), self.get_value())
        print(self.selects, self.selections)
        for sel in self.selections: 
            print(sel+":", self.selections[sel].select, self.selections[sel].data)
    ## get the user-relevant data in a line \n
    # this routine may (or rather should) be overwritten
    def line(self): 
        row = self.get_value_rows(None, None, 0)
        zeile = Afp_ArraytoLine(row)
        return zeile
    ## copy selection data, needed for deep copies, when not already stored in database
    # @param data - SelectionList, where selections are copied from
    def copy_selections_from_data(self, data):
        selections = data.selections
        for sel in selections:
            self.selections[sel] = selections[sel].create_complete_copy(True, True)
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
                if len(select) > 0 and select[0] == "!": 
                    # fixed fromula, no evaluation
                    select_clause = select[1:]
                else:
                    if "ORDER BY" in select:
                        ord = select.split("ORDER BY")
                        if len(ord) == 2:
                            order_clause = ord[1]
                            select = ord[0]
                    select_clause = ""
                    #clauses = select.split("AND")
                    clauses = Afp_split(select, ["AND", "OR"])
                    seq = None
                    if len(clauses) > 1:
                        seq = Afp_getSequence(select,  ["AND", "OR"])
                    #print ("AfpSelectionList.evaluate_selects clauses:", clauses, seq)
                    for clause in clauses:
                        #print ("AfpSelectionList.evaluate_selects clause:", clause)
                        if  "=" in clause:
                            splitter = "="
                        elif ">" in clause:
                            splitter = ">"
                        elif "<" in clause:
                            splitter = "<"
                        elif "LIKE" in clause:
                            splitter = "LIKE"
                        else:
                            continue
                        sels = clause.split(splitter)
                        feld = sels[1].strip()
                        if "." in feld and not Afp_isNumeric(Afp_fromString(feld)) and not (feld[0] == "\"" and feld[-1] == "\""): 
                            value = self.get_string_value(feld, True)
                            if value == "":
                                #print ("AfpSelectionList.evaluate_selects value:", feld, self.mainindex, self.mainselection) 
                                split = feld.split(".")
                                if split[0] == self.mainindex and split[1] == self.mainselection:
                                    return None, None
                        else: 
                            value = feld
                        if value or value == "":
                            if select_clause: 
                                if seq:
                                    select_clause += " " + seq.pop(0) + " "
                                else:
                                    select_clause += " AND "
                            if value:
                                # <=, >= work also with splitter '=', as < and > are kept on the left (not evaluated) side
                                if sels[0][-1] == ">" or sels[0][-1] == "<":
                                    select_clause += sels[0].strip() + splitter + " " + value
                                else:
                                    select_clause += sels[0].strip() + " " + splitter + " " + value
                            elif value == "":
                                select_clause += sels[0].strip() + " " + splitter + " NULL"
            #print ("AfpSelectionList.evaluate_selects:", selname, self.selects[selname], "CLAUSE:", select_clause, order_clause)
        return select_clause, order_clause
    ## set the customised select_clause for the main selection
    def set_main_selects_entry(self):  
        if self.mainselection and self.mainindex and self.mainvalue:         
            selname = self.mainselection
            #print ("AfpSelectionList.set_main_selects_entry:", selname, self.mainindex, self.mainvalue)
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
            if  len(sel_vals) > 1:
                if sel_vals[0] in self.tables:
                    implicit = False
                    unique = None
                    if len(sel_vals) > 2: unique = sel_vals[2]
                    #print "AfpSelectionList.constitute_selection:", sel_vals, unique
                    selection = AfpSQLTableSelection(self.mysql, sel_vals[0], self.debug, unique)
                else:
                    print("WARNING: AfpSelectionList.constitute_selection table not found:", selname, sel_vals[0], self.tables)
        return selection  
    ## create selection - retrieve values from database
    # @param name - name of TableSelection
    # @param allow_new - allow creation of a new TableSelection with no data attached
    def create_selection(self, name, allow_new = True):
        #print ("AfpSelectionList.create_selection:", name, allow_new, name in self.selects, self.selects)
        if allow_new and self.new: new = True
        else: new = False
        selection = self.constitute_selection(name)
        select_clause, order_clause = self.evaluate_selects(name)
        #print ("AfpSelectionList.create_selection clause:", "\"" + name + "\"", select_clause, order_clause, new, selection)
        if selection is None and select_clause == []:
            if new: selection = self.spezial_selection(name, True)
            else:   selection = self.spezial_selection(name)
        elif selection and (select_clause or select_clause == ""):
            if new: selection.new_data()
            else: selection.load_data(select_clause, order_clause)
        elif selection is None and name == self.mainselection:
            selection = AfpSQLTableSelection(self.mysql, name, self.debug, self.mainindex)
        if not selection is None:
            self.selections[name] = selection
    ## create all TableSelections
    def create_selections(self):
        for name in self.selects:
            if not name in self.selections:
                self.create_selection(name)
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
        #print ("AfpSelectionList.get_selection:", selname in self.selections, selname, self.selects) #, self.selections
        if not selname in self.selections:  
            self.create_selection(selname, allow_new_creation)
            #print ("AfpSelectionList.get_selection created:", selname in self.selections, selname, self.selects) #, self.selections
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
    # @param unique - if given, unique fieldname of TableSelection to be created
    def get_selection_from_row(self, selname, row, unique = None):
        sel = self.get_selection(selname)
        selection = sel.create_initialized_copy(unique)
        if row is None:
            selection.new_data()
        else:
            rows = sel.get_values(None, row)         
            selection.set_data(rows)
        #print "AfpSelectionList.get_selection_from_row:",selname, row, unique, selection
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
        #print ("AfpSelectionList.get_value_rows:", selname, selection, felder)
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
            if selname == "_tmp" :
                return self.get_tmp_value(feld)
            else:
                return None
        else:
            return selection.get_value(feld)  
    ## retrieve value from temporary field  \n
    # @param feld - key in _tmp dictionary, where data has to be retrieved from
    def get_tmp_value(self, feld):
        if self._tmp  and feld in self._tmp:
            return self._tmp[feld]
        else:
            return None
     ## retrieve text from selection, eventually import extern file data into textfield  \n
    # - only needed for intermediate use, may be removed later
    # @param DateiFeld - column.selection name where data has to be retrieved from
    def get_ausgabe_value(self, DateiFeld = None):
        value = self.get_value(DateiFeld)
        #print "AfpSelectionList.get_ausgabe_value:", DateiFeld, ":", value
        if value or value == 0 or value == 0.0:
            if Afp_isString(value):
                if len(value) == 16 and value[:6] == "Archiv" and value[-4:] == ".sbt":
                    fname = self.globals.get_value("antiquedir") + Afp_archivName(value, self.globals.get_value("path-delimiter"))
                    wert = Afp_importFileData(fname)
                else:
                    wert = value
                if self.international_output: 
                    wert = Afp_replaceUml(wert, True)
            else:
                if self.international_output: 
                    wert = Afp_toInternDateString(value)
                    #print "AfpSelectionList.get_ausgabe_value:", value, type(value), wert
                else:
                    wert = Afp_toString(value)
        else:
            wert = ""
        return wert
    ## extract one value from a TableSelection, return it as a string
    # @param DateiFeld - column.selection name where data has to be retrieved from
    # @param quoted_string - retuns values as a string, returns strings in quotes
    def get_string_value(self, DateiFeld = None, quoted_string = False):
        if DateiFeld is None:
            fields = [None]
        else:
            fields = DateiFeld.split("+")
        wert = ""
        for field in fields:
            value = self.get_value(field)
            if value or value == 0 or value == 0.0:
                if quoted_string:
                    wert += Afp_toQuotedString(value, True)  + " "# False?
                else:
                    wert += Afp_toString(value) + " "
        if wert: wert = wert[:-1]
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
        #print "AfpSelectionList.spread_mainvalue"
        target = None
        # mainindex 
        source = self.mainindex + "." + self.mainselection
        value = Afp_fromString(self.mainvalue)
        # mainindex filled into all depending selections
        for sel in self.selections:
            if not sel == self.mainselection and self.selections[sel].data and len(self.selects[sel]) > 1:
                #print "AfpSelectionList.spread_mainvalue selects:", sel, self.selects
                select = self.selects[sel][1]
                #print "AfpSelectionList.spread_mainvalue select:", sel, select, #self.selections[sel].data
                if source in select:
                    if "AND" in select:
                        split = select.split("AND")
                        for  sp in split:
                            if source in sp:
                                select = sp
                    split = select.split("=")
                    target = split[0].strip()
                    if  "." in target: target = target.split(".")[0]
                    #print "AfpSelectionList.spread_mainvalue target:", sel, target, value
                    if len(split) > 1 and "-" in split[1]:
                        self.selections[sel].spread_value(target, -value)
                    else:
                        self.selections[sel].spread_value(target, value)
    ## sample newly created unique identifier value of dependent selection to the appropriate entries in the main selectrion
    # @param selname - name of TableSelection where new identifier has been created
    def resample_value(self, selname):
        #print "AfpSelectionList.resample_value initiated:", selname, self.selects[selname]
        target = None
        source = None 
        value = None 
        # uniqueindex
        selarr = self.selects[selname]
        if selarr:
            if len(selarr) > 2:
                source = selarr[2] + "." + selname
            target = selarr[1].split("=")[1].strip()
            #print "AfpSelectionList.resample_value source:",source
            if source:
                split = source.split(".")
                #print "AfpSelectionList.resample_value split:", source, split
                if self.get_selection(split[1]).is_last_inserted_id(split[0]):
                    value = self.get_value(source)
                    #print "AfpSelectionList.resample_value executed:", source, target, value
                    # uniqueindex filled back into mainselection
                    self.set_value(target, value)
    ## get index of first row with given value in column of the appropriate table
    # @param value -  value to be found in indicated column
    # @param DateiFeld - column.selection name where data has to be found
    def find_value_row(self, value, DateiFeld):
        split = DateiFeld.split(".")
        feld = split[0]
        if len(split) > 1: 
            selname = split[1]
        else:
            selname = self.mainselection
        #print ("AfpSelectionList.find_value_row:", value, feld, selname)
        return self.get_selection(selname).find_value_row(value, feld)
        
    ## set a single value of individual TableSelection 
    # @param DateiFeld - column.selection name where data has to be written to
    # @param value - new vaolue of above column
    def set_value(self, DateiFeld, value):
        split = DateiFeld.split(".")
        feld = split[0]
        selname = self.mainselection
        if len(split) > 1: selname = split[1]
        selection = self.get_selection(selname)
        if selection is None:
            if selname == "_tmp":
                if self._tmp:
                    self._tmp[feld] = value
                else:
                    self._tmp = {feld: value}
        else:
            selection.set_value(feld, value)
    ## set multiple  values of indicated TableSelection 
    # @param changed_data - dictionary with changed_data[column] = value
    # @param name - name of TableSelection where data should be written to
    # @param row - index of row in TableSelection where data should be written to \n
    #                        if row < 0: add row with given data
    def set_data_values(self, changed_data, name = None, row = 0):
        selection = self.get_selection(name)
        if row < 0 and selection.get_data_length() == 1 and selection.is_empty():
            row = 0
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
                        if self.debug: print("AfpSelectionList.cannibalise step 1:", name, value)
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
                    if self.debug: print("AfpSelectionList.cannibalise step 2:", name, identic)
                else:
                    # step 3: get complete data if field names are identic
                    indices = Afp_findIndices(to_sel.get_feldnamen(), from_sel.get_feldnamen())
                    identic = True
                    for i in range(len(indices)):
                        if identic and i != indices[i]: 
                            identic = False
                    if self.debug: print("AfpSelectionList.cannibalise step 3:", name, identic)
                if identic:
                    # fulfill step 2 and 3 (cannibalise)
                    to_sel.set_data(from_sel.get_values())
                    to_sel.new = from_sel.new
                    to_sel.manipulation = from_sel.manipulation
                    from_sel.set_data(None)
                else:
                    # step 4: copy colums needed from data (fill new colums with 'None's)
                    data = Afp_getColumns(indices, from_sel.get_values())
                    if self.debug: print("AfpSelectionList.cannibalise step 4:", name, indices, data)
                    to_sel.set_data(data)
    ## store complete SelectionList
    def store(self):
        self.store_preparation()
        if self.mainselection:
            select = self.selections[self.mainselection]
            if self.debug: print("AfpSelectionList.store mainselection:", self.mainselection)
            select.store()
            if self.new:
                self.mainvalue = select.get_string_value(self.mainindex)
                # spread mainvalue into selections
                # self.spread_value()
                self.spread_mainvalue()
                if self.debug: print("AfpSelectionList.store new mainvalue spreaded to other selections:", self.mainvalue)
        # look if filecopy is needed for archiv - invoke after spreading of new mainvalue
        if self.archiv_copy_needed: self.move_to_archiv()
        #print "AfpSelectionList.store() selections 2:", self.selections
        for sel in self.selections: 
            if self.debug: print("AfpSelectionList.store:", sel,"ListNew:", self.new,"New:", self.selections[sel].new,"hasChanged:", self.selections[sel].has_changed(),"Select:", self.selections[sel].select,"\n", self.selections[sel].data)
            if not (sel == self.mainselection) and self.selections[sel].has_changed():
                if self.selects[sel] == []:
                    self.spezial_save(sel)
                else:
                    self.selections[sel].store()
                # eventually spread unique index back to mainselection
                self.resample_value(sel)
        # second try to catch all spreaded values
        for sel in self.selections:
            if self.debug: print("AfpSelectionList.store second try:",sel,"hasChanged:", self.selections[sel].has_changed())
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
    # - Art: (kind) 1st level identification, will be set to program name
    # - Typ: (type) 2nd level identification, will be set to SelectionList listname
    # @param initiate_copy - flag if copying of the extern file during storages should be initiated 
    # @param selname - name of TableSelection holding data from "ARCHIV" table 
    # @param archivname - if given, name of copied file in archiv 
    def add_to_Archiv(self, new_data, initiate_copy = False, archivname=None, selname = "ARCHIV"):
        selection = self.get_selection(selname, False)
        if selection:
            row = selection.get_data_length()
            new_data = self.set_archiv_data(new_data)
            if initiate_copy and self.globals.get_value("path-delimiter") in new_data["Extern"]:
                if archivname:
                    self.archiv_copy_needed.append([selname, row, archivname])
                else:
                    self.archiv_copy_needed.append([selname, row])
            #print ("AfpSelectionList.add_to_Archiv:", new_data, self.archiv_copy_needed)
            selection.set_data_values(new_data, row)
        else:
            print("WARNING SelectionList.add_to_Archiv called but not implemented for", self.listname, "with selection", selname)
    # add missing data to archiv entry
    # @param data - dictionary where identifiers should be added
    def set_archiv_data(self, data):
        if not "Datum" in data: data["Datum"] = self.globals.today()
        if not "Art" in data: 
            data["Art"] = self.globals.get_value("name")
            if data["Art"][:3] == "Afp": data["Art"] = data["Art"][3:]
        if not "Typ" in data: data["Typ"] = self.get_listname_translation()
        if not "KundenNr" in data: data["KundenNr"] = self.get_value("KundenNr")
        if not data["KundenNr"]:  data["KundenNr"] = self.get_value("KundenNr.ADRESSE")
        data = self.set_archiv_table(data)
        return data
    ## move files to archive, if needed
    def move_to_archiv(self):
        if self.archiv_copy_needed:
            archivdir = self.globals.get_value("archivdir")
            modul = self.globals.get_value("name")
            if modul[:3] == "Afp": modul = modul[3:]
            fname = modul + "_" + self.get_listname() + "_" + self.get_string_value()
            #print "AfpSelectionList.move_to_archiv:", archivdir, modul, fname
            #print("AfpSelectionList.move_to_archiv:", self.archiv_copy_needed)
            for entry in self.archiv_copy_needed:
                if len(entry) < 2: continue
                row = self.get_value_rows(entry[0], "Gruppe,Bem,Extern",entry[1])[0]
                #print "AfpSelectionList.move_to_archiv row:", row
                from_name = row[2]
                ext = from_name.split(".")[-1]
                if len(entry) > 2:
                    to_name = entry[2]
                else:
                    to_name = fname + "_" + Afp_replaceUml(Afp_toString(row[0])) + "_"
                    if row[1] and not "." in row[1]:
                       to_name += Afp_replaceUml(Afp_stripSpaces(Afp_toString(row[1] ))) + "_"
                cnt = 1
                while Afp_existsFile(archivdir + to_name + Afp_toIntString(cnt) + "." + ext):
                    cnt += 1
                to_name += Afp_toIntString(cnt) + "." + ext
                #print ("AfpSelectionList.move_to_archiv copy:", from_name, to_name)
                Afp_copyFile(from_name, archivdir + to_name)
                self.set_data_values({"Extern": to_name}, entry[0], entry[1])
            self.archiv_copy_needed = []
    #
    # routines which may be overwritten in devired class, if necessary
    #
    ## return the translated listname to be used in dialogs \n
    # - may be overwritten in devired class, default implemetation: return listname
    def get_listname_translation(self):
        return self.get_listname()
    ## routine for preparation of data before storing
    # may be overwritten, if special handling is necessary
    def store_preparation(self):
        return
    ## routine to retrieve payment data from SelectionList \n
    # may be overwritten, default implementation: return "Preis", "Zahlung" and "ZahlDat" column from main selection
    def get_payment_values_dep(self):
        preis = self.get_value("Preis")
        zahlung = self.get_value("Zahlung")
        if preis is None: preis = 0.0
        if zahlung is None: zahlung = 0.0
        return preis, zahlung, self.get_value("ZahlDat")
    ## routine to set payment data in SelectionList \n
    # may be overwritten, default implementation: "Zahlung" and "ZahlDat" columns of main selection are set
    # @param payment - amount that already has been payed
    # @param datum - date of last payment
    def set_payment_values_dep(self, payment, datum):
        self.set_value("Zahlung", payment)
        self.set_value("ZahlDat", datum)
    ## routine to retrieve splitting data for payment from SelectionList \n
    # may be overwritten, default implementation: return None
    def get_splitting_values_dep(self):
        return None
    ## set identification data for archive \n
    # default implementation: add name of maintable and mainvalue \n
    # - may be overwritten if necessary
    # @param data - dictionary where identifiers should be added
    def set_archiv_table(self, data):
        data["Tab"] = self.get_selection().get_tablename()
        data["TabNr"] = self.get_value()
        return data
    #    
    # routines to be overwritten in devired class
    #
    ## extract payment relevant data from SelectionList for 'Finance' modul (onlý needed if bookkeeping is considered)
    # has to return the account number this payment has to be charged ("Gegenkonto")
    # @param paymentdata - payment data dictionary to be modified and returned
    def add_payment_data_dep(self, paymentdata):
        print("AfpSelecxtionList.add_payment_data not implemented for list:", self.listname)
        return paymentdata
     
    ## return specific identification string to be used in dialogs \n
    # - should be overwritten in devired class
    def get_identification_string(self):
        return ""
        
## class for Selection Lists handling payments
class AfpPaymentList(AfpSelectionList):
    ## initialize AfpSelectionList class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param listname - name of this selction list
    # @param debug - flag for debug information
    def  __init__(self, globals, listname, debug = False):
        AfpSelectionList.__init__(self, globals, listname, debug)
        self.outgoing = False
        self.payer_fields= ["KundenNr"]
        self.price_fields = ["Preis"]
        self.payment_field = "Zahlung"
        self.payment_date = "ZahlDat"
        self.payment_text = "Zahlung: "
        self.payment_text_fields = None
        self.account_field = "Kontierung"
        self.personal_account = None
        self.cancel_field = "Zustand"
        self.cancel_value = "Storno"
        if self.debug:  print("AfpPaymentList Construktor")
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpPaymentList Destruktor")
    ## routine to set payment data in one step using a dictionary
    # @param data - dictionary to be evaluated, the following entries are possile:
    # - "outgoing" - if set, outgoing flag will be set to 'True'
    # - "payer" - see input of self.set_payer_fields()
    # - "account" - database field were accountnumber is hold
    # - "personal" - database field were personal accountnumber is hold (creditor/debitor)
    # - "price"  - database field were price is hold
    # - "payment" - database field were payment value  is hold 
    # - "date"  - database field were payment date is hold 
    # - ,"text" -  database field were payment text is hold,
    # - "cancel" - database field were  value  for cancel decission is hold 
    # - "canvel_value" value defining the Is_canceled flag is set
    def set_payment_data(self, data): 
        #print "AfpPaymentList.set_payment_data:", data
        if "outgoing" in data: self.outgoing = True
        if "payer" in data: self.payer_fields = self.set_field_list(data["payer"])
        if  "account" in data: self.account_field = data["account"]
        if  "personal" in data: self.personal_account  = data["personal"]
        if  "price" in data: self.price_fields = self.set_field_list(data["price"])
        if  "payment" in data: self.payment_field = data["payment"]
        if  "date" in data: self.payment_date = data["date"]
        if  "text" in data: self.payment_text_fields = data["text"]
        if  "cancel" in data: self.cancel_field = data["cancel"]
        if  "cancel_value" in data: self.cancel_value = data["cancel_value"]
        
     ## set field where identifier of person which pays for this event
    # @param payer - database field name were adressidentifier is hold, different value may be separated by a ','
    def set_field_list(self, instring):
        split = instring.split(",")
        list = []
        for entry in split:
            list.append(entry.strip())
        return list
    ## return flag, if this has been canceled
    def is_canceled(self):
        is_canceled = None
        if self.cancel_field:
            if not self.cancel_value is None:
                is_canceled = self.get_value(self.cancel_field) == self.cancel_value
            elif self.get_value(self.cancel_field):
                is_canceled = True
            else:
                is_canceled = False
        return is_canceled
   ## routine to retrieve payment direction 
    def is_outgoing(self):
        return self.outgoing
    ## return address identifier of payer
    def get_payer(self):
        for entry in self.payer_fields:
            #print ("AfpPaymentList.get_payer:", entry,  self.get_value(entry) , type(self.get_value(entry)))
            if self.get_value(entry): return self.get_value(entry)
        return None
    ## routine to retrieve account number to book payment
    def get_account(self):
        #print ("AfpPaymentList.get_account:",  self.account_field,  self.get_value(self.account_field))
        if self.account_field: 
            KtNr = self.get_value(self.account_field)
        else:
            KtNr = "ERL"
        if not (Afp_isNumeric(KtNr)):
            KtNr = Afp_getSpecialAccount(self.get_mysql(),  Afp_getStartLetters(KtNr))
        return KtNr
    ## retrieve payment text
    def get_payment_text(self):
        if self.payment_text_fields:
            text = None
            split = self.payment_text_fields.split(",")
            for sp in split:
                if text: text += " " + self.get_value(sp)
                else: text = self.get_value(sp)
            return text
        else:
            text = self.payment_text + self.get_name(True)
            KNr = self.get_payer()
            if KNr and KNr != self.get_value("KundenNr"):
                for sel in self.selects:
                    if KNr == self.get_value("KundenNr." + sel):
                        #print ("AfpPaymentList.get_payment_text sel found:", sel, self.get_name(True, sel))
                        text += " von " + self.get_name(True, sel)
            return text
    ## routine to retrieve payment data from SelectionList \n
    def get_payment_values(self):
        preis = None
        for entry in self.price_fields:
            if preis: continue
            #print "AfpPaymentList.get_payment_values preis:", preis, entry, self.get_value(entry)
            if self.get_value(entry): preis = self.get_value(entry)
        #print "AfpPaymentList.get_payment_values Zahlung:", self.payment_field, self.get_value(self.payment_field)
        zahlung = self.get_value(self.payment_field)
        if preis is None: preis = 0.0
        if zahlung is None: zahlung = 0.0
        #print "AfpPaymentList.get_payment_values", preis, zahlung, self.get_value(self.payment_date)
        return preis, zahlung, self.get_value(self.payment_date)
    ## routine to set payment data in SelectionList \n
    # overwritten from SelectionList
    def store_preparation(self):
        status = self.get_value("Zustand")
        #print "AfpPaymentList.store_preparation status:", status
        if status == "Offen":
            preis, zahlung, datum = self.get_payment_values() 
            if zahlung >=preis:
                self.set_value("Zustand", "Beendet")
            
    ## routine to set payment data in SelectionList \n
    # @param payment - amount that already has been payed
    # @param datum - date of last payment
    def set_payment_values(self, payment, datum):
        self.set_value(self.payment_field , payment)
        self.set_value(self.payment_date , datum)
    ## routine to retrieve splitting data for desired payment from SelectionList \n
    # may be overwritten, default implementation: return None
    # @param amount - if given, amount to be splitted
    # needed output: list of [accountNr, value, name of account]
    def get_splitting_values(self, amount = None):
        return None        
    #    
    # routines to be overwritten in devired class
    #
    ## extract payment relevant data from SelectionList for 'Finance' modul (onlý needed if bookkeeping is considered)
    # has to return the account number this payment has to be charged ("Gegenkonto")
    # @param paymentdata - payment data dictionary to be modified and returned
    def add_payment_data(self, paymentdata):
        print("AfpPaymentList.add_payment_data not implemented for list:", self.listname)
        return paymentdata

## class for Selection Lists handling filter and sorted data
class AfpOrderedList(AfpSelectionList):
    ## initialize AfpSelectionList class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param listname - name of this selction list
    # @param index - if given, column where sorting should occur
    # @param filter -  if given, filter for sorted data on database
    # @param debug - flag for debug information
    def  __init__(self, globals, listname, index = None, filter = None, debug = False):
        AfpSelectionList.__init__(self, globals, listname, debug)
        self.mainindex = index
        self.mainfilter = filter
        self.mainposition = None
    
        if self.debug:  print("AfpOrderedList Construktor")
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpOrderedList Destruktor")
        
    ## set the searched value for this selection
    def set_mainvalue(self, value):  
        self.mainvalue = value
        self.set_main_selects_entry()
     ## set the searched value for this selection
    def set_mainfilter(self, filter):  
        self.mainfilter = filter
        self.set_main_selects_entry()
    ## set the customised select_clause for the main selection
    def set_main_selects_entry(self): 
        self.mainposition = None
        if self.mainfilter and self.mainselection and self.mainindex:
            selname = self.mainselection            
            filter = ""
            if not self.mainvalue is None:  
                filter = self.mainindex + " = " + self.mainvalue + " AND "
            self.selects[selname] = [selname,  filter + self.mainfilter, self.mainindex]
        else:
            super(AfpOrderedList, self).set_main_selects_entry() 
        #print "AfpOrderedList.set_main_selects_entry:", self.mainselection, self.selects[selname] 

