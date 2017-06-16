#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpInvoice.AfpInRoutines
# AfpInRoutines module provides classes and routines needed for invoice handling,\n
# no display and user interaction in this modul.
#
#   History: \n
#        22 JNov 2016 - inital code generated - Andreas.Knoblauch@afptech.de \n

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright© 1989 - 2017  afptech.de (Andreas Knoblauch)
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

import AfpBase
from AfpBase import *
from AfpBase.AfpDatabase import AfpSQL
from AfpBase.AfpDatabase.AfpSQL import AfpSQLTableSelection
from AfpBase.AfpBaseRoutines import *
#from AfpBase.AfpBaseAdRoutines import AfpAdresse, AfpAdresse_getListOfTable

## returns all possible entries for kind of tours
def AfpFaktura_possibleInvoiceKinds():
    #return ["Indi","Eigen","Fremd"]
    return ["Rechnung","Mahnung"]
## returns all possible entries for open incidents
def AfpFaktura_possibleOpenKinds():
    names, tables = AfpFaktura_possibleKinds()
    return ["Merkzettel (Memo)"] + names[2:-2]
 
 ## return index of name in filter list
 # @param name - name to be looked for in filter list
def AfpFa_inFilterList(name):
    names =  AfpFaktura_FilterList()
    if name in names:
        return names.index(name)
    return None
## returns all possible entries of filter list
# @param name - if given name indicator what has to be returned
# @param table - if given table indicator, only used together with filter entry
# @param filter - if given, filter indicator, only used together with table entry
# these parameters are evaluated as follows:
# - if table and filter are given and found in lists, the appropriate 'names' entry and index is returned
# - if name is given and found in 'names', the appropriate 'tables' and 'filters' entry is returned
# - if name is given and not found, two empty strings are returned
# - else: the 'names' and 'tables' lists are returned
def AfpFaktura_possibleKinds(name = None, table = None, filter = None):
    names = ["Ausgabe" , "Waren"     , "Bestellung", "Disposition", "Kostenvoranschlag","Angebot"  , "Lieferschein", "Auftrag" , "Rechnung", "Mahnung", "Einnahme"]
    tables = ["BESTELL"  , "BESTELL" , "BESTELL"      , "BESTELL"       , "KVA"                        , "KVA"        , "KVA"                , "KVA"        , "RECHNG"   , "RECHNG"  , "RECHNG"]
    filters = ["beglichen","erhalten", "offen"         , "neu"              ,  "KVA"                        ,  "Angebot",  "Liefer"          , "Auftrag" , "offen"    ,  "Mahnung", "bezahlt"]
    if table and filter:
        for i in range(len(tables)):
            if tables[i] == table and filters[i] == filter:
                return names[i], i
    if name:
        print "AfpFaktura_possibleKinds name:", name, names
        if  name in names:
            ind = names.index(name)
            return tables[ind], filters[ind]
        else:
            return "",""
    else:
        return names, tables
## returns entries for filter list
def AfpFaktura_FilterList():
    names, tables = AfpFaktura_possibleKinds()
    list = []
    table = tables[0]
    for name in names:
        step = tables[names.index(name)]
        if table != step:
            list. append ("-------------------------")
            table = step
        list.append(name)
    return list

##  get the list of indecies of the appropriate faktura table,
def AfpFaktura_getOrderlistOfTable():
    #liste = {'RechNr':'int','Datum':'date', 'KundenNr':'string'}
    liste = {'RechNr':None,'Datum':'date', 'KundenNr':'string'}
    return liste
    
## get clear name for dialogs from database tablename
def AfpFa_getClearName(tablename):
    if tablename == "KVA":
        return  "Kostenvoranschlag"
    elif tablename == "BESTELL":
        return  "Bestellung"
    else: #tablename == "RECHNG":
        return  "Rechnung"
        
## get the appropriate data object from database selection
def AfpFaktura_getSelectionList( globals, RechNr, tablename):
    if tablename == "KVA":
        return  AfpOffer(globals, RechNr)
    elif tablename == "BESTELL":
        return  AfpOrder(globals, RechNr)
    else: #tablename == "RECHNG":
        return  AfpInvoice(globals, RechNr)
        
## special handling for float string prependen by a colon endend string
# @param string - string to be converted
def AfpFa_colonFloat(string):
    fstring = string
    split = string.split(":")
    if len(split) == 2:
        fstring = split[1]
    return Afp_floatString(fstring)
    
## baseclass for invoice handling         
class AfpFaktura(AfpSelectionList):
    ## initialize AfpFaktura class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param debug - flag for debug information
    # @param name - name of selection list
    # this is the 'Faktura' baseclass, actually initialization is done by calling the 'initialize' method
    def  __init__(self, globals, debug = None, name = "Faktura"):
        AfpSelectionList.__init__(self, globals, name, debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.finance = None
        self.new = False
        self.mainindex = "RechNr"
        self.mainvalue = ""
        self.maintable = "RECHNG"
        self.spezial_bez = []
        self.content = None # shortcut to selection "Content"
        self.standard_tax=globals.get_value("standard-tax","Faktura")
        self.totable_fields = {"Netto":"Gesamtpreis", "Gewinn":"Gewinn"}
        #self.tax_fields = {"Mwst":"Netto"}
        self.tax_fields = {}
        self.brutto_fields = {"Betrag":"Netto", "ZahlBetrag": "Netto"}
        #self.formula_fields = {"Betrag":"Netto + Mwst"}
        self.formula_fields = {}

        self.mainselection = "Main"
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr = KundenNr.Main"] 
        self.selects["Dependance1"] = [ "GERAETE","KundenNr = KundenNr.Main AND GeraeteNr = AttNr.Main"] 
        self.selects["Content"] = [ "RECHIN","RechNr = RechNr.Main ORDER BY PosNr"] 
        self.selects["ARCHIV"] = [ "ARCHIV","RechNr = RechNr.Main"] 
        #self.selects["AUSGABE"] = [ "AUSGABE","Typ = Art.Main + Zustand.Main"] 
        if not self.globals.skip_accounting():
            self.finance_modul = Afp_importAfpModul("Finance", self.globals)[0]
            if self.finance_modul:
                self.finance = self.finance_modul.AfpFi_getFinanceTransactions(self.globals)
        #print "AfpFaktura.finance:", self.finance
        if self.debug: print "AfpFaktura Konstruktor", self.listname
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpFaktura Destruktor", self.listname
    
    ## initialisation routine for the use of different database constructions
    # @param mainfield - name.tablename of the identifier of the mani selection
    # @param mainvalue - if given, value of the identifier of the main selection
    # @param sb - if given, AfpSuperbase object where initial selection should be extracted from
    # @param selects - if given, database contructions to replace the initial values of self.selects \n
    #  REMARK: only selects which are given will be overwritten, selects not mentioned will not be touched \n
    # \n
    # either mainvalue or sb (superbase) has to be given for initialisation,otherwise a new, clean object is created
    def initialize(self, mainfield, mainvalue = None, sb = None, selects = None):
        split = mainfield.split(".") 
        #print "AfpFaktura.initalize split:", split
        if len(split) > 1:
            self.mainindex = split[0]
            self.maintable = split[1]
            #print "AfpFaktura.initalize mainvalue:", mainvalue
            if mainvalue:
                self.mainvalue = Afp_toString(mainvalue)
                self.set_main_selects_entry()
                self.create_selection(self.mainselection)
            elif sb:
                self.mainvalue = sb.get_string_value(mainfield)
                self.selections[self.mainselection] = sb.gen_selection(self.maintable, self.mainindex, self.debug)
        #print "AfpFaktura.initalize mainselection:", self.mainselection in self.selections, self.debug
        if not self.mainselection in self.selections:
            self.new = True
            self.selections[self.mainselection] = AfpSQLTableSelection(self.mysql, self.maintable, self.debug, self.mainindex)
        if selects:
            for sel in selects:
                self.selects[sel] = selects[sel]
        self.content = self.get_selection("Content")
        if self.debug: print "AfpFaktura.initialize(d) with the following values:", self.mainvalue, self.mainindex, self.maintable
    ## set the customised select_clause for the main selection - overwritten from AfpSelectionList
    def set_main_selects_entry(self):  
        #print "AfpFaktura.set_main_selects_entry:",self.mainselection, self.mainindex, self.mainvalue
        if self.mainselection and self.mainindex and self.mainvalue:         
            self.selects[self.mainselection] = [self.maintable, self.mainindex + " = " + self.mainvalue, self.mainindex]
            #print "AfpFaktura.set_main_selects_entry selects:", self.selects
    ## set field names for special treatment
    # @param totables - dictionary: 'value' fields in content will be summarized in 'key' field in main 
    # @param taxes - dictionary: 'key' field in main the tax of 'value' field in main 
    # @param bruttos - dictionary: 'key' field in main the tax-brutto of 'value' field in main 
    # @param formulas - dictionary: 'key' field in main will be evaluated according to 'value'-formula 
    def set_special_fields(self, totables, taxes, bruttos, formulas):
        if totables: self.totable_fields = totables
        if taxes: self.tax_fields = taxes
        if bruttos: self.brutto_fields = bruttos
        if formulas: self.formula_fields = formulas
    ## inizialise new data
    # @param KNr - address identifier 
    # @param stype - subtyp to be cerated
    def set_new(self, KNr, stype, keep = []):
        self.new = True
        self.clear_selections(keep)
        self.set_value("KundenNr", KNr)
        self.set_value("Ziustand", stype)
        self.create_selection("ADRESSE", False)
    ## get main table of SelectionList
    def get_main_table(self):
        return self.maintable
    ## get number of rows in content
    def get_content_length(self):
        return self.content.get_data_length()
    ## get ranges of rows in content where given criteatia is fulfilled
    # @param field - field to fullfill criteria
    # @param crtiteria - criteria to be fulfilled 
    def get_content_range(self, field, criteria = "True"):
        ranges = []
        start = None
        pyBefehl = "bool = value " + criteria
        values = self.content.get_values(field)
        print "AfpFaktura.get_content_range value:", values
        for i in range(len(values)):
            value = values[i][0]
            add = False
            if criteria == "True":
                if value: add = True
            elif criteria == "False":
                if not value: add = True
            else:
                exec pyBefehl
                if bool: add = True
            print "AfpFaktura.get_content_range add:", i, add, value, criteria
            if add:
                if start is None:
                    start = i
            else:
                if not start is None:
                    ranges.append([start, i-1])
                start = None
        if not start is None:
            ranges.append([start,len(values) - 1])
        return ranges
    ## update sums and set tax values
    def update_fields(self):
        self.content_numbering()
        for field in self.totable_fields:
            values = self.content.get_values(self.totable_fields[field])
            sum = 0.0
            for value in values:
                if value and value[0]: sum += Afp_fromString(value[0])
            self.set_value(field, sum)
            print "AfpFaktura.update_fields total:",field, values, sum
        for field in self.tax_fields:
            tax = self.get_value(self.tax_fields[field]) * self.standard_tax / 100
            self.set_value(field, tax)   
            print "AfpFaktura.update_fields tax:",field, tax
        for field in self.brutto_fields:
            netto = self.get_value(self.brutto_fields[field]) 
            tax = netto * self.standard_tax / 100
            self.set_value(field, netto + tax)
            print "AfpFaktura.update_fields brutto:",field, netto, tax, netto + tax
        for field in self.formula_fields:
            res = self.evaluate_formula(self.formula_fields[field])
            self.set_value(field, res)
            print "AfpFaktura.update_fields formula:",field, self.formula_fields[field], res
    ## renumberation of content
    def content_numbering(self):
        pos = 0
        for i in range(self.content.get_data_length()):
            if self.check_position_line(i): 
                pos += 1
                self.content.set_value("Nr", pos, i)
            else: 
                self.content.set_value("Nr", "", i)
            self.content.set_value("PosNr", i+1, i)
            #print "AfpFaktura.content_numbering Nr:", pos, "PosNr:", i+1
    ## simple formula evaluation
    # @param form - formula to be evaluated
    def evaluate_formula(self, form):
        value = None
        vars, signs = Afp_splitFormula(form)
        #print "AfpFaktura.evaluate_formula:",form, vars, signs
        if vars and signs:
            for i in range(len(vars)):
                if Afp_hasNumericValue(vars[i]):
                    vars[i] = Afp_fromString(vars[i])
                else:
                    vars[i] = self.get_value(vars[i])
                    #print "AfpFaktura.evaluate_formula value:", vars
        if vars and signs:
            value = vars[0]
            for i in range(1,len(vars)):
                if signs[i-1] == "+":
                    value += vars[i]
                elif signs[i-1] == "-":
                    value -= vars[i]
        return value
    ## check if anzahl and nettopreis are set in content line
    # @param rowNr - index of row to be checked
    def check_position_line(self, rowNr):
        values = self.content.get_values("Anzahl,Einzelpreis",rowNr) 
        #print "AfpFaktura.check_position_line:", rowNr, values
        return (values[0][0] or values[0][1])
    ## change or add row in content
    # @param initial_rows - range of old rows to be changed
    # @param fileds - list of fieldnames, for which data is delvered in 'rows' (used for each row)
    # @param rows - values of new row data to be filled into data structure
    def replace_content_rows(self, initial_rows, fields, rows):
        print "AfpFaktura.replace_content_rows:", initial_rows, fields, rows
        olgh = initial_rows[1] - initial_rows[0] + 1
        nlgh = len(rows)
        if olgh > nlgh:
            diff = olgh - nlgh
            print "AfpFaktura.replace_content_rows delete:", diff
            for i in range(diff):
                self.content.delete_row(initial_rows[0])
        if olgh < nlgh:
            diff = nlgh - olgh
            print "AfpFaktura.replace_content_rows insert:", diff
            for i in range(diff):
                self.content.insert_data_row(initial_rows[1] + 1, True)
        for i in range(nlgh):
            data_values = {}
            for j in range(len(fields)):
                if rows[i][j]:
                    data_values[fields[j]] =  rows[i][j]
            print "AfpFaktura.replace_content_rows fill:", i, i + initial_rows[0], data_values
            self.content.set_data_values(data_values, i + initial_rows[0])
    ## change or add row in content
    # @param index - index of row to be changed - outside valid rows, row will be added at end
    # @param row - values of new row data delivered from screen
    def change_content_row(self, index, row):
        print "AfpFaktura.change_content_row:", index, row
        if row is None:
            self.content.delete_row(index)
        else:
            datavals = self.expand_grid_row(row)
            if index is None or index < 0 or index >= self.content.get_data_length():
                RNr = self.get_value("RechNr")
                if RNr: datavals["RechNr"] = RNr
                self.content.add_data_values(datavals)
            else:
                self.content.set_data_values(datavals, index)
        self.update_fields()
    ## financial transaction will be initated if the appropriate modul is installed
    # @param initial - flag for initial call of transaction (interal payment may be added)
    def execute_financial_transaction(self, initial):
        if self.finance:
            self.finance.add_financial_transactions(self)
            if initial: self.finance.add_internal_payment(self)
            self.finance.store()
    
    ## one line to hold all relevant values of tourist, to be displayed 
    def line(self):
        zeile =  self.get_string_value("RechNr").rjust(8) + " " +  self.get_string_value("Anmeldung") + "  "  + self.get_name().rjust(35)  + " " + self.get_string_value("Kennung.TORT")  
        zeile += " " + self.get_string_value("Preis").rjust(10) + " " +self.get_string_value("Zahlung").rjust(10) 
        return zeile
    ## set all necessary values to keep track of the payments
    # @param payment - amount that has been payed
    # @param datum - date when last payment has been made
    def set_payment_values(self, payment, datum):
        AfpSelectionList.set_payment_values(self, payment, datum)
        if self.is_invoice_connected():
            self.set_value("Zahlung.RECHNG", payment)
            self.set_value("ZahlDat.RECHNG", datum)
    ## return names of columns of different grids
    # @param name - name of grid data is designed for
    def get_grid_colnames(self, name="Content"):
        if name == "Content":
            return ["Pos","ErsatzteilNr","Bezeichnung","Anzahl","Einzel","Gesamt"]
    ## return rows of different grids
    # @param name - name of grid data is designed for
    def get_grid_rows(self, name="Content"):
        rows = None
        if name == "Content":
            raw = self.get_string_rows("Content","Nr,ErsatzteilNr,Bezeichnung,Anzahl,Einzelpreis,Gesamtpreis,Gewinn,Zeile,ErsatzteilNr")
            #print "AfpFaktura.get-grid_rows raw:",raw
            lgh = len(raw)
            rows = []
            #for i in range(len(raw)-1, -1, -1):
            for i in range(len(raw)):
                row = raw[i]
                zeile = Afp_intString(row[1])
                if row[7] or (zeile and row[2] == ""):
                    row[0] = ""
                    row[1] = self.get_zeile(row[7], zeile)
                    for j in range(2,len(row)):
                        row[j] = ""
                else:
                    anz = Afp_fromString(row[3])
                    if anz and anz == int(anz):
                        row[3] = Afp_toString(int(anz))
                rows.append(row)
        #print "AfpFaktura.get-grid_rows:",rows
        return rows
    ## get text form 'Zeilen' database
    # @param zeile - direct text inpuu
    # @param ZNr - identifier of text in database
    def get_zeile(self, zeile, ZNr):
        if zeile: 
            return Afp_toString(zeile)
        elif ZNr:
            rows = self.globals.get_mysql().select("Zeile","ZeilenNr = " + Afp_toString(ZNr), "ZEILEN")
            #print "AfpFaktura.get_zeile:", Afp_toString(rows[0][0])
            if rows:
                return Afp_toString(rows[0][0])
        else:
            return ""
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Fakturierung Nr "  +  self.get_string_value("RechNr") + " vom  " +  self.get_string_value("Datum") + " über ".decode("UTF-8")  + self.get_string_value("Betrag")
    #
    # routine to be overwritten in devired class to handle
    # editing of content
    #
    ## get line editing process description
    # to be overwritten if more then selection and number of entries is needed
    # @param typ - typ of line entry
    # @param param - optional parameter to come with certain types
    def get_grid_lineprocessing(self, typ = None, param = None):
        if typ and typ == "free":
            value = ""
            if param: 
                return  [ ["set",[2,param]], [3,"Afp_intString"], ["set",[4,"EK:"]], [4,"AfpFa_colonFloat","$6 = $4"], ["set",[4,""]], [4,"Afp_floatString","$5 = $4 * $3,$6 =( $4 - $6 )* $3"]] 
            else:
               return  [ [2], [3,"Afp_intString"], ["set",[4,"EK:"]], [4,"AfpFa_colonFloat","$6 = $4"], ["set",[4,""]], [4,"Afp_floatString","$5 = $4 * $3,$6 =( $4 - $6 )* $3"]] 
            #return  [ ["set",",,"+ value + ",,,,"], [3,"Afp_intString"], [4,"Afp_floatString","$6 = $4"], [4,"Afp_floatString","$5 = $4 * $3,$6 =( $4 - $6 )* $3"]] 
        else:
            return  [ ["choose",",ArtikelNr,Bezeichnung,,Nettopreis,Nettopreis,Einkaufspreis"], [3,"Afp_intString","$5 = $5 * $3,$6 =( $4 - $6 )* $3"]] 
       
    ## routine to expand data from view to full datarow to be filled into content
    def expand_grid_row(self, row):
        # row == [ArtikelNr, Bezeichnung, Anzahl, Einzelpreis, Gesamtpreis, Gewinn]
        change = {}
        if len(row) == 1:
            change["Zeile"] = row[0]
        else:
            change["ErsatzteilNr"] = row[1]
            change["Bezeichnung"] = row[2]
            change["Anzahl"] = row[3]
            change["Einzelpreis"] = row[4]
            change["Gesamtpreis"] = row[5]
            change["Gewinn"] = row[6]
        return change

        
## baseclass for invoices in faktura handling         
class AfpInvoice(AfpFaktura):
    ## initialize AfpInvoice class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param RechNr - if given, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved durin initialisation \n
    # \n
    # either KvaNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, RechNr = None, sb = None, debug = None, complete = False):
        AfpFaktura.__init__(self, globals, debug, "Rechnung")
        self.initialize("RechNr.RECHNG", RechNr, sb)
        if complete: self.create_selections()
        if self.debug: print "AfpInvoice Konstruktor, RechNr:", self.mainvalue
    ## destuctor
    def __del__(self):    
        if self.debug: print "AfpInvoice Destruktor"
    ## financial transaction will be canceled if the appropriate modul is installed
    def cancel_financial_transaction(self):
        if self.finance:
            original = AfpInvoice(self.globals, self.mainvalue)
            self.finance.add_financial_transactions(original, True)
    ## one line to hold all relevant values of this tour, to be displayed 
    def line(self):
        zeile =  self.get_string_value("Kennung").rjust(8) + "  "  + self.get_string_value("Art") + " " +  self.get_string_value("AgentName") + " " + self.get_string_value("Abfahrt") + " " + self.get_string_value("Zielort")  
        return zeile
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Rechnung vom "  +  self.get_string_value("Datum") + " über " + self.get_string_value("Preis") + " an " + self.get_name()

## baseclass for offers in faktura handling         
class AfpOffer(AfpFaktura):
    ## initialize AfpOffer class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param KvaNr - if given, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved durin initialisation \n
    # \n
    # either KvaNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, KvaNr = None, sb = None, debug = None, complete = False):
        AfpFaktura.__init__(self, globals, debug, "KVA")
        selects = {}
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["Content"] = [ "KVAIN","RechNr = RechNr.Main ORDER BY PosNr"] 
        self.selects["Rechnung"] = [ "RECHNG","RechNr = RechNr.Main","RechNr"] 
        self.initialize("RechNr.KVA", KvaNr, sb, selects)
        if complete: self.create_selections()
        if self.debug: print "AfpOffer Konstruktor, KvaNr:", self.mainvalue
    ## destuctor
    def __del__(self):    
        if self.debug: print "AfpOffer Destruktor"
    ## a separate invoice is created and filled with the appropriate values
    def add_invoice(self):
        print "AfpOffer.add_invoice"
        invoice = AfpSQLTableSelection(self.get_mysql(), "RECHNG", self.debug, "RechNr")
        KNr = self.get_value("KundenNr")
        data = {"Datum": self.globals.today(), "KundenNr": KNr, "Name": self.get_name(True), "Anmeld": self.get_value("AnmeldNr")}
        data["Debitor"] = Afp_getIndividualAccount(self.get_mysql(), KNr)
        betrag = self.get_value("Preis")
        data["Zahlbetrag"] = betrag
        #betrag2 = self.extract_taxfree_portion()
        #if betrag2:
            #betrag -= betrag2
            #data["Betrag2"] = betrag
            #data["Konto2"] = Afp_getSpecialAccount(self.get_mysql(), "EMFA")
        data["Betrag"] = betrag
        data["Kontierung"] = Afp_getSpecialAccount(self.get_mysql(), "ERL")
        data["Zustand"] = "offen"
        data["Wofuer"] = "Reiseanmeldung Nr " + self.get_string_value("AnmeldNr") + " am " + self.get_string_value("Abfahrt.REISEN") + " nach " + self.get_string_value("Zielort.REISEN")
        if self.get_value("ZahlDat"):
            data["Zahlung"] = self.get_value("Zahlung")
            data["ZahlDat"] = self.get_value("ZahlDat")
            if data["Zahlung"] >= betrag: data["Zustand"] = "bezahlt"
        invoice.new_data()
        invoice.set_data_values(data)
        self.selections["RECHNG"] = invoice

    ## one line to hold all relevant values of this tour, to be displayed 
    def line(self):
        zeile =  self.get_string_value("Kennung").rjust(8) + "  "  + self.get_string_value("Art") + " " +  self.get_string_value("AgentName") + " " + self.get_string_value("Abfahrt") + " " + self.get_string_value("Zielort")  
        return zeile
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "KVA vom "  +  self.get_string_value("Datum") + " über " + self.get_string_value("Preis") + " an " + self.get_name()

## baseclass for orders in faktura handling         
class AfpOrder(AfpFaktura):
    ## initialize AfpOrder class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param BestNr - if given, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved durin initialisation \n
    # \n
    # either BestNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, BestNr = None, sb = None, debug = None, complete = False):
        AfpFaktura.__init__(self, globals, debug, "KVA")
        selects = {}
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["Content"] = [ "BESTIN","RechNr = RechNr.Main ORDER BY PosNr"] 
        self.selects["Rechnung"] = [ "VERBIND","RechNr = RechNr.Main","RechNr"] 
        self.initialize("RechNr.BESTELL", BestNr, sb, selects)
        if complete: self.create_selections()
        if self.debug: print "AfpOrder Konstruktor, BestNr:", self.mainvalue
    ## destuctor
    def __del__(self):    
        if self.debug: print "AfpOrder Destruktor"
    ## a separate invoice is created and filled with the appropriate values
    def add_invoice(self):
        print "AfpOrder.add_invoice"
        invoice = AfpSQLTableSelection(self.get_mysql(), "RECHNG", self.debug, "RechNr")
        KNr = self.get_value("KundenNr")
        data = {"Datum": self.globals.today(), "KundenNr": KNr, "Name": self.get_name(True), "Anmeld": self.get_value("AnmeldNr")}
        data["Debitor"] = Afp_getIndividualAccount(self.get_mysql(), KNr)
        betrag = self.get_value("Preis")
        data["Zahlbetrag"] = betrag
        #betrag2 = self.extract_taxfree_portion()
        #if betrag2:
            #betrag -= betrag2
            #data["Betrag2"] = betrag
            #data["Konto2"] = Afp_getSpecialAccount(self.get_mysql(), "EMFA")
        data["Betrag"] = betrag
        data["Kontierung"] = Afp_getSpecialAccount(self.get_mysql(), "ERL")
        data["Zustand"] = "offen"
        data["Wofuer"] = "Bestellung Nr " + self.get_string_value("AnmeldNr") + " am " + self.get_string_value("Abfahrt.REISEN") + " nach " + self.get_string_value("Zielort.REISEN")
        if self.get_value("ZahlDat"):
            data["Zahlung"] = self.get_value("Zahlung")
            data["ZahlDat"] = self.get_value("ZahlDat")
            if data["Zahlung"] >= betrag: data["Zustand"] = "bezahlt"
        invoice.new_data()
        invoice.set_data_values(data)
        self.selections["RECHNG"] = invoice

    ## one line to hold all relevant values of this tour, to be displayed 
    def line(self):
        zeile =  self.get_string_value("Kennung").rjust(8) + "  "  + self.get_string_value("Art") + " " +  self.get_string_value("AgentName") + " " + self.get_string_value("Abfahrt") + " " + self.get_string_value("Zielort")  
        return zeile
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Bestellung vom "  +  self.get_string_value("Datum") + " über " + self.get_string_value("Preis") + " von " + self.get_name()

## baseclass for tourist in faktura handling  (mainly for test-reasons)        
class AfpFaTourist(AfpFaktura):
    ## initialize AfpFaTourist class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param AnmeldNr - if given, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved durin initialisation \n
    # \n
    # either KvaNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, AnmeldNr = None, sb = None, debug = None, complete = False):
        AfpFaktura.__init__(self, globals, debug, "Tourist-Faktura-View")
        selects = {}
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["Content"] = [ "ANMELDEX","AnmeldNr = AnmeldNr.Main"] 
        self.selects["Dependance1"] = [ "REISEN","FahrtNr = FahrtNr.Main"] 
        self.initialize("AnmeldNr.ANMELD", AnmeldNr, sb, self.selects)
        if complete: self.create_selections()
        if self.debug: print "AfpFaTourist Konstruktor AnmeldNr:", self.mainvalue
    ## destuctor
    def __del__(self):    
        if self.debug: print "AfpFaTourist Destruktor"
    ## a separate invoice is created and filled with the appropriate values
    def add_invoice(self):
        print "AfpFaTourist.add_invoice"
        invoice = AfpSQLTableSelection(self.get_mysql(), "RECHNG", self.debug, "RechNr")
        KNr = self.get_value("KundenNr")
        data = {"Datum": self.globals.today(), "KundenNr": KNr, "Name": self.get_name(True), "Anmeld": self.get_value("AnmeldNr")}
        data["Debitor"] = Afp_getIndividualAccount(self.get_mysql(), KNr)
        betrag = self.get_value("Preis")
        data["Zahlbetrag"] = betrag
        #betrag2 = self.extract_taxfree_portion()
        #if betrag2:
            #betrag -= betrag2
            #data["Betrag2"] = betrag
            #data["Konto2"] = Afp_getSpecialAccount(self.get_mysql(), "EMFA")
        data["Betrag"] = betrag
        data["Kontierung"] = Afp_getSpecialAccount(self.get_mysql(), "ERL")
        data["Zustand"] = "offen"
        data["Wofuer"] = "Reiseanmeldung Nr " + self.get_string_value("AnmeldNr") + " am " + self.get_string_value("Abfahrt.REISEN") + " nach " + self.get_string_value("Zielort.REISEN")
        if self.get_value("ZahlDat"):
            data["Zahlung"] = self.get_value("Zahlung")
            data["ZahlDat"] = self.get_value("ZahlDat")
            if data["Zahlung"] >= betrag: data["Zustand"] = "bezahlt"
        invoice.new_data()
        invoice.set_data_values(data)
        self.selections["RECHNG"] = invoice

    ## one line to hold all relevant values of this tour, to be displayed 
    def line(self):
        zeile =  self.get_string_value("Kennung").rjust(8) + "  "  + self.get_string_value("Art") + " " +  self.get_string_value("AgentName") + " " + self.get_string_value("Abfahrt") + " " + self.get_string_value("Zielort")  
        return zeile
    ## return names of columns of different grids - overwritten from AfpFaktura
    # @param name - name of grid data is designed for
    def get_grid_colnames(self, name="Content"):
        if name == "Content":
            return ["Kennung","Bezeichnung","Preis","",""]
    ## return rows of different grids - overwritten from AfpFaktura
    # @param name - name of grid data is designed for
    def get_grid_rows(self, name="Content"):
        rows = []
        if name == "Content":
            rows = self.get_string_rows("Content","Kennung,Bezeichnung,Preis,AnmeldNr")
            rows = Afp_MatrixSplitCol(rows, 2, 3)
        return rows   
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "KVA vom "  +  self.get_string_value("Datum") + " über " + self.get_string_value("Preis") + " an " + self.get_name()

    

