#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpInvoice.AfpInRoutines
# AfpInRoutines module provides classes and routines needed for invoice handling,\n
# no display and user interaction in this modul.
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        22 JNov 2016 - inital code generated - Andreas.Knoblauch@afptech.de \n

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
#    Copyright© 1989 - 2023  afptech.de (Andreas Knoblauch)
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


from AfpBase.AfpDatabase.AfpSQL import AfpSQLTableSelection
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_getNow
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpSelectionLists import AfpSelectionList, AfpPaymentList
#from AfpBase.AfpBaseAdRoutines import AfpAdresse, AfpAdresse_getListOfTable

## returns all payable incidents
def AfpFaktura_payableKinds():
    return ["Ausgabe","Waren","Bestellung","Rechnung","Mahnung","Einnahme"]
## returns all editable kinds which allow further processing
def AfpFaktura_processableKinds():
    return ["Ausgabe","Waren","Bestellung"]
## returns all editable incidents
def AfpFaktura_editableKinds():
    names, tables = AfpFaktura_possibleKinds()
    return names[:-2]
## returns all possible entries for open incidents
def AfpFaktura_possibleOpenKinds():
    names, tables = AfpFaktura_possibleKinds()
    return ["Merkzettel (Memo)"] + names[2:-2]
## returns possible change kind
# @param name - name of kind to be checked
# @param kind - name of actuel kind, if given
def AfpFaktura_changeKind(name, kind = None):
    change = ""
    table = ""
    newtable, filter = AfpFaktura_possibleKinds(name)    
    if kind:
        table, filter = AfpFaktura_possibleKinds(kind)
        if not newtable: name = kind
    if newtable == "KVA" or newtable == table or not newtable:
        change = name
    elif newtable == "BESTELL":
        change, ind = AfpFaktura_possibleKinds(None, "BESTELL", "neu")
    elif newtable == "RECHNG":
        change, ind = AfpFaktura_possibleKinds(None, "RECHNG", "open")
    return change, newtable == table or not newtable
 
 ## return index of name in filter list
 # @param name - if filter is None: name to be looked for in filter list, else: table indicator
 # @param filter - if given, filter on given table indicator
def AfpFaktura_inFilterList(name, filter = None):
    names =  AfpFaktura_FilterList()
    if filter:
        name, ind = AfpFaktura_possibleKinds(None, name, filter)
    if name in names:
        return names.index(name)
    return None
## returns all possible entries of filter list
# @param name - if given name indicator what has to be returned
# @param table - if given table indicator, only used together with filter entry
# @param filter - if given, filter indicator, only used together with table entry
# these parameters are evaluated as follows:
# - if table and filter are given and found in lists, the appropriate 'names' entry and index are returned
# - if name is given and found in 'names', the appropriate 'tables' and 'filters' entry are returned
# - if name is given and not found, two empty strings are returned
# - else: the 'names' and 'tables' lists are returned
def AfpFaktura_possibleKinds(name = None, table = None, filter = None):
    names = ["Ausgabe" , "Waren"     , "Bestellung", "Bestell-Liste", "Kostenvoranschlag","Angebot" , "Lieferschein", "Auftrag" , "Rechnung", "Mahnung", "Einnahme"]
    tables = ["BESTELL"  , "BESTELL" , "BESTELL"      , "BESTELL"           , "KVA"                           , "KVA"       , "KVA"                 , "KVA"         , "RECHNG"   , "RECHNG"   , "RECHNG"]
    filters =  ["closed"   ,"erhalten" , "open"           , "neu"                  , "KVA"                            , "Angebot",  "Liefer"          , "Auftrag" , "open"       ,  "Mahnung", "closed"]
    #print("AfpFaktura_possibleKinds:", name, table, filter)
    if table and not filter is None:
        for i in range(len(tables)):
            if tables[i] == table and filters[i] == filter:
                return names[i], i
        if not filter:
            if table == "BESTELL":
                return names[3], 3
            if table == "KVA":
                return names[4], 4
            if table == "RECHNG":
                return names[8], 8
        return None, None
    elif name:
        #print("AfpFaktura_possibleKinds name:", name, names)
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
def AfpFaktura_getClearName(tablename):
    if tablename == "KVA":
        return  "Kostenvoranschlag"
    elif tablename == "BESTELL":
        return  "Bestellung"
    else: #tablename == "RECHNG":
        return  "Rechnung"
        
## get the appropriate data object from database selection
def AfpFaktura_getSelectionList( globals, RechNr, tablename):
    if tablename == "ADMEMO":
        return  AfpMemo(globals, RechNr)
    elif tablename == "KVA":
        return  AfpOffer(globals, RechNr)
    elif tablename == "BESTELL":
        return  AfpOrder(globals, RechNr)
    else: #tablename == "RECHNG":
        return  AfpInvoice(globals, RechNr)

## decides if entry string indicates a wage entry
# @param id_string - string to be analysed
def AfpFaktura_isWage(id_string):
    if id_string[:2] == "00": # this is very special to AfpMotor
        return True
    else:
        return False
## extract manufacturer short name from article-number string
# @param globals - global data
# @param string - string to be tested
def AfpFaktura_getShortManu(globals, number):
    ken = number.split(" ")[0]
    mlen = globals.get_value("short-manu-max-len", "Faktura")
    if not mlen: mlen = 2
    if len(ken) <= mlen:
        return ken
    else:
        return None
## special handling for float string prepended by a colon endend string
# @param string - string to be converted
def AfpFaktura_colonFloat(string):
    fstring = string
    split = string.split(":")
    if len(split) == 2:
        fstring = split[1]
    return Afp_floatString(fstring)
## special handling for float string prepended by a colon endend string
# @param string - string to be converted
def AfpFaktura_colonInt(string):
    fstring = string
    split = string.split(":")
    if len(split) == 2:
        fstring = split[1]
    return Afp_intString(fstring)
    
## get selection rows for a given typ
# @param mysql - database handle to retrieve data from
# @param typ - indicated typ, where rows should be retrieved
# @param debug - flag if debug text should be written
def AfpFaktura_getSelectedRows(mysql, typ, debug):
    datei, filter = AfpFaktura_possibleKinds(typ)
    #print ("AfpFaktura_getSelectedRows:", typ, datei, filter)
    if datei == "":
        datei = "ADMEMO"
        filter = "Zustand." + datei + " = \"open\""
    else:
        filter = "Zustand." + datei + " = \"" + filter + "\""
    select = filter + " AND KundenNr." + datei + " = KundenNr.ADRESSE"
    #print ("AfpFaktura_getSelectedRows:", typ, datei, filter, "Select:", select)
    if datei == "ADMEMO":
        rows = mysql.select_strings("Name.ADRESSE,Vorname.ADRESSE,Datum.ADMEMO,MemoNr.ADMEMO,Memo.ADMEMO", select, datei + " ADRESSE")
    else:
        rows = mysql.select_strings("Name.ADRESSE,Vorname.ADRESSE,Datum." + datei +",RechNr."+datei + ",Bem." + datei, select, datei + " ADRESSE")
    if debug: print("AfpFaktura_getSelectedRows:", select, rows)
    #print("AfpFaktura_getSelectedRows:", select, rows)
    return datei, rows
## import articles from csv-file into manufacturer database
# @param globals - global data, inclusive mysql connection
# @param data - AfpManufact selection-list
# @param filename - name of csv-file to be imported
# @param debug - if given, flag for debug-modus
def AfpFaktura_importArtikels(globals, data, filename, debug = False):
    deli = None
    ken = data.get_value("Kennung")
    delis = globals.get_value("fabricator-delimiter", "Faktura")
    if ken in delis:
        deli = delis[ken]
    elif "default" in delis:
        deli = delis["default"]
    paras = globals.get_value("fabricator-import", "Faktura")
    if ken in paras:
        par = paras[ken]
        mantable = data.get_manufact_table()
        if mantable in globals.get_mysql().get_tables():
            #befehl = "TRUNCATE TABLE " + mantable + ";"
            befehl = "DELETE FROM " + mantable + "; COMMIT;"
            if debug: print("AfpFaktura_importArtikels delete/truncate mysql table:", befehl)
            globals.get_mysql().execute(befehl)
        else:
            befehl = "CREATE TABLE `" + mantable + "` (`ArtikelNr` tinytext CHARACTER SET latin1 COLLATE latin1_german2_ci NOT NULL,`Bezeichnung` tinytext CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL, `Listenpreis` float(9,2) DEFAULT NULL, `PreisGrp` char(5) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL, `EAN` char(25) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL, KEY `ArtikelNr` (`ArtikelNr`(50)), KEY `Bezeichnung` (`Bezeichnung`(50)), KEY `EAN` (`EAN`)) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"
            if debug: print("AfpFaktura_importArtikels create mysql table:", befehl)
            globals.get_mysql().execute(befehl)
            data = AfpManufact(globals, data.get_value())
        if debug: print ("AfpFaktura_importArtikels started:", Afp_getNow().time())
        imp = AfpImport(globals, filename, par, debug)
        imp.direct_mysql_storing = True
        if deli:
            imp.set_csv_parameter(deli[0], deli[1])
        res = imp.read_from_csv_file(data, mantable)
        if debug: print ("AfpFaktura_importArtikels loaded:", Afp_getNow().time(), data.get_value_length(mantable))
        if res:
            sel = res[0].get_selection(mantable)
            sel.new = True
            sel.store()
        if debug: print ("AfpFaktura_importArtikels stored:", Afp_getNow().time())
        return True
    else:
        return False
## baseclass for memo handling 
class AfpMemo(AfpSelectionList):
    ## initialize AfpMemo class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param value - mainvalue to initialise this class
    # @param debug - flag for debug information
    def  __init__(self, globals, value = None, debug = None):
        AfpSelectionList.__init__(self, globals, "Memo", debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.mainindex = "MemoNr"
        self.mainselection = "ADMEMO"
        self.mainvalue = ""
        if value: 
            self.mainvalue = Afp_toQuotedString(value)
        else:
            self.new = True
        self.set_main_selects_entry()
        self.create_selection(self.mainselection)
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr = KundenNr.ADMEMO"] 
        if self.debug: print("AfpMemo Konstruktor")
    ## destructor
    def __del__(self):    
        if self.debug: print("AfpMemo Destruktor")

    ## initialize new object with values
    # @param knr - identifier of address this memo belongs to
    # @param dat - if given date of the memo, otherwise today is used
    # @param memo - if given text of the memo
    def initialize(self, knr, dat = None, memo = None):
        self.set_value("KundenNr", knr)
        if dat is None: dat = self.globals.today()
        self.set_value("Datum", dat)
        if memo:
            self.set_value("Memo", memo)
        self.set_value("Zustand", "open")
    ## set memo text and store
    # @param memo - text to be stored in this memo
    def set_memo(self, memo):
        self.set_value("Memo", memo)
        self. store()
    ## deaktivate memo and store
    def deactivate(self):
        self.set_value("Zustand", "closed")
        self. store()
        
        
## baseclass for manufaturer handling 
class AfpManufact(AfpSelectionList):
    ## initialize AfpManufact class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param value - mainvalue to initialise this class
    # @param index - index in table to look for value
    # @param debug - flag for debug information
    def  __init__(self, globals, value = None, index = None, debug = None):
        AfpSelectionList.__init__(self, globals, "Manufact", debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.mainindex = "HersNr"
        if index: self.mainindex = index
        self.mainselection = "ARTHERS"
        self.mainvalue = ""
        if value: 
            self.mainvalue = Afp_toQuotedString(value)
        else:
            self.new = True
        self.set_main_selects_entry()
        self.create_selection(self.mainselection)
        self.herstable = "ART_" + Afp_toIntString(self.get_value("HersNr"))
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr = KundenNr.ARTHERS"] 
        self.selects["ARTDIS"] = [ "ARTDIS","HersNr = HersNr.ARTHERS"] 
        self.selects["ARTSUR"] = [ "ARTSUR","HersNr = HersNr.ARTHERS"] 
        self.selects["ARTIKEL"] = [ "ARTIKEL","HersNr = HersNr.ARTHERS"] 
        self.selects["GlobSUR"] = [ "ARTSUR","HersNr = 0"] 
        self.selects[self.herstable] = [ self.herstable,""] 
        if self.debug: print("AfpManufact Konstruktor")
    ## destructor
    def __del__(self):    
        if self.debug: print("AfpManufact Destruktor")
        
    ## get manufactur selection table
    def get_manufact_table(self):
        return self.herstable
    ## generate the manufacturer discount for this AfpArtikel SelectionList
    # @param article -  AfpArtikel SelectionList
    def gen_discount(self, article):
        lstp = article.get_value("Listenpreis")
        prsgrp = article.get_value("PreisGrp")
        print("AfpManufact.gen_discount:", lstp, prsgrp)
        disc = self.get_discount(prsgrp)
        if disc: 
            fac = (100.0 - disc)/100.0
            print("AfpManufact.gen_discount disc:", fac, disc)
            ek = int(100*fac*lstp)/100.0
        else:
            ek = lstp
        article.set_value("Einkaufspreis", ek)
        return article
    ## generate the manufacturer discount for the given in put
    # @param prsgrp -  group of price
    def get_discount(self, prsgrp):
        row = self.find_value_row(prsgrp, "PreisGrp.ARTDIS")
        if not row:
            row = self.find_value_row(None, "PreisGrp.ARTDIS")
        if row: 
            return int(row[-1])
        else:
            return None
    ## generate the manufacturer surcharge (supplement) for this AfpArtikel SelectionList
    # @param article -  AfpArtikel SelectionList
    def gen_surcharge(self, article):
        lstp = article.get_value("Listenpreis")
        prsgrp = article.get_value("PreisGrp")
        ek = article.get_value("Einkaufspreis")
        print("AfpManufact.gen_surcharge:", lstp, prsgrp)
        # find surcharge for price-group of manufacturer
        sur = self.get_surcharge(prsgrp, lstp)
        if sur:
            fac = (100.0 + sur)/100.0
            print("AfpManufact.gen_surcharge sur:", fac, sur) 
            netto = int(100*fac*ek)/100.0
        else:
            netto = lstp
        article.set_value("Nettopreis", netto)
        #article.set_value("Gewinn", netto - ek)
        return article
    ## generate the manufacturer surcharge for the given in put
    # @param prsgrp -  group of price
    # @param lstp - reference price
    def get_surcharge(self, prsgrp, lstp):
        row = self.find_value_row(prsgrp, "PreisGrp.ARTSUR")
        if not row: # find surcharge for individual price for manufacturer, resp. surcharge of manufacturer
            row = self.extract_surcharge(lstp, "ARTSUR")
        if not row:# find global surcharge for individual price resp. global surcharge
            row = self.extract_surcharge(lstp, "GlobSUR")
        if row:
            return int(row[-1])
        else:
            return None
    ## extract surchage from database table
    # @param preis -  price of article to be used fpr seaqrch
    # @param tablename -  name of table, where price debendent surcharge has to be extracted
    def extract_surcharge(self, preis, tablename):
        row = None
        rows = self.find_value_row(None, "PreisGrp." + tablename, True)
        print("AfpManufact.extract_surcharge rows:", tablename, rows)
        if rows:
            liste = {}
            for r in rows:
                if not r[2] is None:
                    liste[r[2]] = r
                else:
                    single = r
            for s in reversed(sorted(liste)):
                if preis >= s:
                    row = liste[s]
                    break
            # fallback in case price is below first value
            if row is None and liste:
                first = next(iter(sorted(liste)))
                row = liste[first]
            if row is None and single:
                row = single
        return row
    ## generate the prices for this AfpArtikel SelectionList
    # @param article -  AfpArtikel SelectionList
    def gen_prices(self, article):
        article = self.gen_discount(article)
        article = self.gen_surcharge(article)
        return article
    
    ## get new AfpArtikel SelectionList holding the data from the manufacturer database
    # @param ident - identifier of article in manufacturer database
    # @param index - if given, field to look for the ident value
    def get_articles(self, ident, index = None):
        article = None
        if not index: index = "ArtikelNr"
        sel = self.get_selection(self.herstable)
        sel.load_data(index + " = '" + ident + "'")
        print("AfpManufact.get_articles:", sel.data)
        anumber =  self.get_value("Kennung") + " " + sel.get_value("ArtikelNr")
        check = AfpSQLTableSelection(self.get_mysql(), "ARTIKEL")
        check.load_data("HersNr = " + self.get_string_value("HersNr") + " AND ArtikelNr = '" + anumber + "'") 
        print("AfpManufact.get_articles check:", check.data)
        if check.get_data_length() == 0:
            data = {"ArtikelNr": self.get_value("Kennung") + " " + sel.get_value("ArtikelNr"), "Bezeichnung": sel.get_value("Bezeichnung"), "Listenpreis": sel.get_value("Listenpreis"), "PreisGrp": sel.get_value("PreisGrp"), "HersNr": self.get_value("HersNr"), "EAN": sel.get_value("EAN")}
            print("AfpManufact.get_articles data:", data)
            article = AfpArtikel(self.globals, None)
            article.set_data_values(data)
            article = self.gen_prices(article)
        return article
        
## baseclass for article handling during faktura        
class AfpArtikel(AfpSelectionList):
    ## initialize AfpArtikel class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param value - mainvalue to initialise this class
    # @param debug - flag for debug information
    # @param table - name of selection list table to be used, default: "ARTIKEL"
    # @param index - unique sort index of table to be used, default: "ArtikelNr"
    def  __init__(self, globals, value, debug = None, table = "ARTIKEL", index = "ArtikelNr"):
        AfpSelectionList.__init__(self, globals, "Artikel", debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.id_column = "ArtikelNr"
        self.name_column = "Bezeichnung"
        self.sell_column = "Nettopreis"
        self.buy_column = "Einkaufspreis"
        self.amount_column = "Bestand"
        self.mainindex = index
        self.mainselection = table
        if value:
            self.mainvalue = Afp_toQuotedString(value)
            self.set_main_selects_entry()
        else:
            self.new = True
        self.create_selection(self.mainselection)
        if self.mainselection in self.selects:
            self.selects["Stack"] = self.selects[self.mainselection]
        if self.debug: print("AfpArtikel Konstruktor")
    ## destructor
    def __del__(self):    
        if self.debug: print("AfpArtikel Destruktor")
    ## initialisation routine for new mainvalue
    # @param value - new mainvalue
    def new_mainvalue(self, value):
        if value:
            self.mainvalue = Afp_toQuotedString(value)
            self.set_main_selects_entry()
            self.reload_selection(self.mainselection)
        else:
            self.mainvalue = None
            self.selects[self.mainselection] = ["",""]
        self.selects["Stack"] = self.selects[self.mainselection]
        self.delete_selection("Stack")
    ## routine to add another mainvalue to stack
    # @param value - new mainvalue to be added to stack
    def add_mainvalue(self, value):
        if self.mainvalue is None: add = False
        else: add = True
        self.mainvalue = Afp_toQuotedString(value)
        self.set_main_selects_entry()
        self.reload_selection(self.mainselection)
        if add:
            self.selects["Stack"][1] += " OR " + self.selects[self.mainselection][1]
        else:
            self.selects["Stack"] = self.selects[self.mainselection] 
            self.selects["Stack"][1] = "!" + self.selects["Stack"][1] 
    ## routine to load and lock stack data
    def load_lock(self):
        sel = self.get_selection("Stack", False)
        sel.lock_data()
        sel.reload_data() 
        print("AfpArtikel.load_lock selected:", sel.data)
    ## store stack data in table
    def store_stack(self):
        sel = self.get_selection("Stack")
        sel.store()
    ## book amount into stack
    # @param amount - dictonary holding the amount for each id, that should be added to stack
    def add_amount(self, amount):
        sel = self.get_selection("Stack") 
        #print "AfpArtikel.add_amount Stack:", sel.data
        id_rows = sel.get_values(self.id_column)
        amount_rows = sel.get_values(self.amount_column)
        #print "AfpArtikel.add_amount ID:", self.id_column, id_rows, "Amount:", self.amount_column, amount_rows
        for entry in amount:
            #print "AfpArtikel.add_amount entry:", entry, AfpFaktura_isWage(entry), amount[entry]
            if not AfpFaktura_isWage(entry):
                value = amount[entry]
                if [entry] in id_rows and Afp_isEps(value):
                    row = id_rows.index([entry])
                    anz = amount_rows[row][0]
                    anz += value
                    if anz < 0: anz = 0
                    print("AfpArtikel.add_amount add:", entry, anz)
                    sel.set_value(self.amount_column, anz, row) 
    ## get columns for line display
    def get_columns_for_line_display(self):
        line = "," + self.id_column + "," + self.name_column+ "," + self.amount_column + ","+ self.sell_column + ","+ self.sell_column+ "," + self.buy_column
        return line
        
## baseclass for invoice handling         
class AfpFaktura(AfpPaymentList):
    ## initialize AfpFaktura class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param debug - flag for debug information
    # @param name - name of selection list
    # this is the 'Faktura' baseclass, actually initialization is done by calling the 'initialize' method
    def  __init__(self, globals, debug = None, name = "Faktura"):
        AfpPaymentList.__init__(self, globals, name, debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.finance = None
        self.selection_table = AfpArtikel(globals, None, debug)
        self.new = False
        self.mainindex = "RechNr"
        self.mainvalue = ""
        self.maintable = "RECHNG"
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
        self.selects["ADRESATT"] = [ "ADRESATT","KundenNr = KundenNr.Main AND AttNr = AttNr.Main"] 
        self.selects["Content"] = [ "RECHIN","RechNr = RechNr.Main ORDER BY PosNr"] 
        #self.selects["Attribute"] = [ "ADRESATT","KundenNr = KundenNr.Main AND AttNr > 0"] 
        self.gen_dependent_selects()

        if not self.globals.skip_accounting():
            self.finance_modul = Afp_importAfpModul("Finance", self.globals)[0]
            if self.finance_modul:
                self.finance = self.finance_modul.AfpFi_getFinanceTransactions(self.globals)
        #print "AfpFaktura.finance:", self.finance
        if self.debug: print("AfpFaktura Konstruktor", self.listname)
    ## destructor
    def __del__(self):    
        if self.debug: print("AfpFaktura Destruktor", self.listname)
    ## helper routine to set archive and report dependencies
    def gen_dependent_selects(self):
        self.selects["ARCHIV"] = ["ARCHIV", "Tab = \"" + self.maintable + "\" AND TabNr = RechNr.Main"] 
        self.selects["AUSGABE"] = [ "AUSGABE","Modul = \"Faktura\" AND Art = \"" + self.get_listname() + "\" AND Typ = Zustand.Main"] 
        #print("AfpFaktura.gen_dependent_selects:", self.selects["ARCHIV"], self.selects["AUSGABE"])
    ## initialisation routine for the use of different database constructions
    # @param mainfield - name.tablename of the identifier of the mani selection
    # @param mainvalue - if given, value of the identifier of the main selection
    # @param sb - if given, AfpSuperbase object where initial selection should be extracted from
    #  REMARK: only selects which are given will be overwritten, selects not mentioned will not be touched \n
    # \n
    # either mainvalue or sb (superbase) has to be given for initialisation,otherwise a new, clean object is created
    def initialize(self, mainfield, mainvalue = None, sb = None):
        split = mainfield.split(".") 
        #print "AfpFaktura.initalize split:", split
        if len(split) > 1:
            self.mainindex = split[0]
            self.maintable = split[1]
            #print "AfpFaktura.initalize mainvalue:", mainvalue
            if mainvalue:
                self.mainvalue = Afp_toQuotedString(mainvalue)
                self.set_main_selects_entry()
                self.create_selection(self.mainselection)
            elif sb:
                self.mainvalue = sb.get_string_value(mainfield)
                self.selections[self.mainselection] = sb.gen_selection(self.maintable, self.mainindex, self.debug)
            self.gen_dependent_selects()
        #print "AfpFaktura.initalize mainselection:", self.mainselection in self.selections, self.debug
        if not self.mainselection in self.selections:
            self.new = True
            self.selections[self.mainselection] = AfpSQLTableSelection(self.mysql, self.maintable, self.debug, self.mainindex)
        self.content = self.get_selection("Content")
        if self.debug: print("AfpFaktura.initialize(d) with the following values:", self.mainvalue, self.mainindex, self.maintable)
    ## return if payment is possible
    def is_payable(self):
        kind = self.get_kind()
        print("AfpFaktura.is_payable:", kind)
        return kind in AfpFaktura_payableKinds()
    ## return if editing is possible
    def is_editable(self):
        kind = self.get_kind()
        #print("AfpFaktura.is_editable:", kind)
        return kind in AfpFaktura_editableKinds()
    ## return if further processing is possible
    def is_processable(self):
        if self.is_editable():
            kind = self.get_kind()
            #print("AfpFaktura.is_processable:", kind)
            return kind in AfpFaktura_processableKinds()
        else:
            return False
    ## set other selection table where data is used to fill content
    # @param articles - AfpArtikel object where data for content can be extracted from
    def set_selection_table(self, articles):
        self.selection_table = articles
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
    # @param stype - subtyp to be created
    # @param KNr - address identifier 
    # @param keep - if given, list of selections to be kept
    def set_new(self, stype, KNr = None, keep = []):
        self.new = True
        self.clear_selections(keep)
        self.set_value("Zustand", stype)
        self.set_value("Datum", self.globals.today())
        if not KNr is None:
            self.set_value("KundenNr", KNr)
            self.create_selection("ADRESSE", False)
    ## complete datavalues needed for storing
    def complete_data(self):
        #print("AfpFaktura.complete_data")
        Konto = self.get_account_number()
        self.set_value("Kontierung",Konto)
    ## get accountnumber for financial accounting
    def get_account_number(self):
        konto = 0
        if self.finance:
            if self.content_holds_wage():
                ident = "REP"
            else:
                ident = "VK"
            if self.get_value("Attribut.ADRESATT") == "PKW":
                ident += "-KFZ"
            konto = self.finance.get_special_accounts(ident)
        return konto
    ## get main table of SelectionList
    def get_maintable(self):
        return self.maintable
    ## get kind of faktura 
    def get_kind(self):
        kind, ind = AfpFaktura_possibleKinds(None, self.maintable, self.get_value("Zustand"))
        return kind
    ## get number of rows in content
    def get_content_length(self):
        return self.content.get_data_length()
    ## return if content has been changed
    # @param last - flag if content changes before last storage should be delivered
    def content_has_changed(self, last = False):
        if last:
            return self.content.has_changed(None, True)
        else:
            return self.content.has_changed()
    ## get ranges of rows in content where given criteria is fulfilled
    # @param field - field to fullfill criteria
    # @param crtiteria - criteria to be fulfilled 
    def get_content_range(self, field, criteria = "True"):
        ranges = []
        start = None
        pyBefehl = "bool = value " + criteria
        values = self.content.get_values(field)
        print("AfpFaktura.get_content_range value:", values)
        for i in range(len(values)):
            value = values[i][0]
            add = False
            if criteria == "True":
                if value: add = True
            elif criteria == "False":
                if not value: add = True
            else:
                #exec(pyBefehl)
                bool = eval("value " + criteria) 
                if bool: add = True
            print("AfpFaktura.get_content_range add:", i, add, value, criteria)
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
                if value and value[0]: sum += Afp_floatString(value[0])
            self.set_value(field, sum)
            #print("AfpFaktura.update_fields total:",field, values, sum)
        for field in self.tax_fields:
            tax = self.get_value(self.tax_fields[field]) * self.standard_tax / 100
            self.set_value(field, tax)   
            #print("AfpFaktura.update_fields tax:",field, tax)
        for field in self.brutto_fields:
            netto = self.get_value(self.brutto_fields[field]) 
            tax = netto * self.standard_tax / 100
            self.set_value(field, netto + tax)
            #print("AfpFaktura.update_fields brutto:",field, netto, tax, netto + tax)
        for field in self.formula_fields:
            res = self.evaluate_formula(self.formula_fields[field])
            self.set_value(field, res)
            #print("AfpFaktura.update_fields formula:",field, self.formula_fields[field], res)
    ## checks if invoice content holds wage positions
    def content_holds_wage(self):
        wage = False
        for i in range(self.get_content_length()):
            wage = self.content_row_holds_wage(i)
        return wage
    ## renumberation of content
    def content_numbering(self):
        pos = 0
        for i in range(self.content.get_data_length()):
            if self.check_position_line(i): 
                pos += 1
                self.content.set_value("Nr", pos, i)
            else: 
                #self.content.set_value("Nr", "", i)
                self.content.set_value("Nr", 0, i)
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
        print("AfpFaktura.replace_content_rows:", initial_rows, fields, rows)
        if initial_rows is None:
            initial_rows = [self.get_content_length(), self.get_content_length()]
            print("AfpFaktura.replace_content_rows:", initial_rows)
        olgh = initial_rows[1] - initial_rows[0] + 1
        nlgh = len(rows)
        if olgh > nlgh:
            diff = olgh - nlgh
            print("AfpFaktura.replace_content_rows delete:", diff)
            for i in range(diff):
                self.content.delete_row(initial_rows[0])
        if olgh < nlgh:
            diff = nlgh - olgh
            print("AfpFaktura.replace_content_rows insert:", diff)
            for i in range(diff):
                self.content.insert_data_row(initial_rows[1] + 1, True)
        for i in range(nlgh):
            data_values = {}
            for j in range(len(fields)):
                if rows[i][j]:
                    data_values[fields[j]] =  rows[i][j]
            print("AfpFaktura.replace_content_rows fill:", i, i + initial_rows[0], data_values)
            self.content.set_data_values(data_values, i + initial_rows[0])
        self.update_fields()
    ## change or add row in content
    # @param index - index of row to be changed - outside valid rows, row will be added at end
    # @param row - values of new row data delivered from screen
    def change_content_row(self, index, row):
        #print("AfpFaktura.change_content_row:", index, row)
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
    ## check if content row holds a wage entry
    # @param index - index of row to be checked
    def content_row_holds_wage(self, index):
        ANr = self.content.get_values("ErsatzteilNr", index)[0]
        return AfpFaktura_isWage(ANr)
    ## conversion between different faktura types
    # @param datei - tablename of targerttype
    # @param filter - filter on targerttype
    def get_converted_faktura(self, datei, filter):
        print("AfpFaktura.get_converted_faktura ", datei, filter)
        if datei == "RECHNG":
            faktura = AfpInvoice(self.get_globals(), None, None, self.is_debug())
        elif datei == "BESTELL":
            faktura = AfpOrder(self.get_globals(), None, None, self.is_debug())
        elif datei == "KVA":
            faktura = AfpOffer(self.get_globals(), None, None, self.is_debug())
        main = faktura.get_selection("Main")
        main.new_data()
        KNr = self.get_value("KundenNr")
        data = {"KundenNr": KNr, "AttNr": self.get_value("AttNr"), "Datum": self.globals.today(), "Zustand": filter}
        data["Pos"] = self.get_value("Pos")
        data["Ust"] = self.get_value("Ust")
        data["Kontierung"] = self.get_value("Kontierung")
        data["Debitor"] = Afp_getIndividualAccount(self.get_mysql(), KNr)
        data["Netto"] = self.get_value("Netto")
        data["Betrag"] = self.get_value("Betrag")
        data["Gewinn"] = self.get_value("Gewinn")
        main.set_data_values(data)
        # copy content
        content = faktura.get_selection("Content")
        data = Afp_copyArray(self.get_selection("Content").data)
        # reset 'RechNr' on position 0
        for i in range(len(data)):
            data[i][0] = None
        content.set_data(data)
        return faktura
    ## financial transaction will be initated if the appropriate modul is installed
    # @param initial - flag for initial call of transaction (interal payment may be added)
    def execute_financial_transaction(self, initial):
        if self.finance:
            self.finance.add_financial_transactions(self)
            if initial: self.finance.add_internal_payment(self)
            self.finance.store()
    #
    #  routines which have been overwritten
    #
    ## one line to hold all relevant values of faktura, to be displayed 
    def line(self):
        zeile =  self.get_string_value("RechNr").rjust(8) + " " +  self.get_string_value("Datum") + "  "  + self.get_name().rjust(35)  + " " + self.get_string_value("Betrag")  
        zeile += " " + self.get_string_value("Zahlbetrag").rjust(10) + " " +self.get_string_value("Zahlung").rjust(10) 
        return zeile
    ## routine to retrieve payment data from SelectionList \n
    # overwritten from AfpSelectionList
    def get_payment_values(self):
        preis = self.get_value("ZahlBetrag")
        if not preis: preis = self.get_value("Betrag")
        zahlung = self.get_value("Zahlung")
        if preis is None: preis = 0.0
        if zahlung is None: zahlung = 0.0
        return preis, zahlung, self.get_value("ZahlDat")
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
            raw = self.get_string_rows("Content", self.get_grid_columns(name))
            #raw = self.get_string_rows("Content","Nr,ErsatzteilNr,Bezeichnung,Anzahl,Einzelpreis,Gesamtpreis,Gewinn,Zeile,ErsatzteilNr")
            #print "AfpFaktura.get_grid_rows raw:",raw
            lgh = len(raw)
            rows = []
            for row in raw:
                zeile = Afp_intString(row[1])
                if row[7] or (zeile and row[2] == ""):
                    row[0] = ""
                    row[1] = ""
                    row[2] = self.get_zeile(row[7], zeile)
                    for j in range(3,len(row)):
                        row[j] = ""
                else:
                    anz = Afp_fromString(row[3])
                    if anz and anz == int(anz):
                        row[3] = Afp_toString(int(anz))
                rows.append(self.get_modified_grid_row(row))
        #print "AfpFaktura.get_grid_rows:",rows
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
    ## set the customised select_clause for the main selection
    # - overwritten from AfpSelectionList
    def set_main_selects_entry(self):  
        #print "AfpFaktura.set_main_selects_entry:",self.mainselection, self.mainindex, self.mainvalue
        if self.mainselection and self.mainindex and self.mainvalue:         
            self.selects[self.mainselection] = [self.maintable, self.mainindex + " = " + self.mainvalue, self.mainindex]
            #print "AfpFaktura.set_main_selects_entry selects:", self.selects
    ## complete an store data
    # - overwritten from AfpSelectionList
    def store(self):
        self.complete_data()
        #print("AfpFaktura.store view:")
        #self.view()
        AfpSelectionList.store(self)
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Fakturierung Nr "  +  self.get_string_value("RechNr") + " vom  " +  self.get_string_value("Datum") + " über "  + self.get_string_value("Betrag")
    #
    # routine to be overwritten in devired class
    #
    ## get line editing process description
    # to be overwritten if more then selection and number of entries is needed
    # @param typ - typ of line entry
    # @param param - optional parameter to come with certain types
    def get_grid_lineprocessing(self, typ = None, param = None):
        if typ: 
            if typ == "free":
                if param: 
                    return  [ ["set",[2,param]], [3,"Afp_intString"], ["set",[4,"EK:"]], [4,"AfpFaktura_colonFloat","$6 = $4"], ["set",[4,""]], [4,"Afp_floatString","$5 = $4 * $3,$6 =( $4 - $6 )* $3"] ] 
                else:
                   return  [ [2], [3,"Afp_intString"], ["set",[4,"EK:"]], [4,"AfpFaktura_colonFloat","$6 = $4"], ["set",[4,""]], [4,"Afp_floatString","$5 = $4 * $3,$6 =( $4 - $6 )* $3"] ] 
                #return  [ ["set",",,"+ value + ",,,,"], [3,"Afp_intString"], [4,"Afp_floatString","$6 = $4"], [4,"Afp_floatString","$5 = $4 * $3,$6 =( $4 - $6 )* $3"]] 
            elif typ == "stock":
                # param = [requested, delivered]
                return [["set",[3,Afp_intString(param[0]) + ":"]],[3,"AfpFaktura_colonInt"]]
            else:
                typ = None
        if not typ:
            felder = self.selection_table.get_columns_for_line_display()
            return  [ ["choose", felder], [3,"Afp_intString","$5 = $5 * $3,$6 =( $4 - $6 )* $3"]] 
            #return  [ ["choose",",ArtikelNr,Bezeichnung,,Nettopreis,Nettopreis,Einkaufspreis"], [3,"Afp_intString","$5 = $5 * $3,$6 =( $4 - $6 )* $3"]] 
    ## return names of data columns neede for different grids
    # @param name - name of grid data is designed for
    def get_grid_columns(self, name="Content"):
        if name == "Content":
            return "Nr,ErsatzteilNr,Bezeichnung,Anzahl,Einzelpreis,Gesamtpreis,Gewinn,Zeile,ErsatzteilNr"
     ## return names of data columns needed for different grids
    # @param row - row to be modified
    # @param name - name of grid data is designed for
    def get_modified_grid_row(self, row, name="Content"):
        # default implementation
        #print("AfpFaktura.get_modified_grid_row:", row)
        return row
     ## routine to expand data from view to full datarow to be filled into content
    # @param row - data to be expanded
    def expand_grid_row(self, row):
        # row == [None, ArtikelNr, Bezeichnung, Anzahl, Einzelpreis, Gesamtpreis, Gewinn]
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
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either KvaNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, RechNr = None, sb = None, debug = None, complete = False):
        AfpFaktura.__init__(self, globals, debug, "Rechnung")
        self.initial_content = None
        self.initialize("RechNr.RECHNG", RechNr, sb)
        if complete: self.create_selections()
        if self.get_content_length():
            self.initial_content = self.content.create_complete_copy()
        if self.debug: print("AfpInvoice Konstruktor, RechNr:", self.mainvalue)
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpInvoice Destruktor")
    ## complete datavalues needed for storing
    def complete_data(self):
        #print("AfpInvoice.complete_data")
        AfpFaktura.complete_data(self) 
        KNr = self.get_value("KundenNr")
        if KNr: 
            Konto = self.get_indi_account(KNr)
            self.set_value("Debitor",Konto)
            if  self.get_value("Zahlung") and self.get_value("ZahlBetrag") and self.get_value("Zahlung") >= self.get_value("ZahlBetrag"):
                self.set_value("Zustand","closed")
            if not self.get_value("Zustand"):
                self.set_value("Zustand","open")
        else:
            self.set_value("Zustand","closed")
            self.set_value("ZahlDat",self.get_value("Datum"))
            self.set_value("Zahlung",self.get_value("ZahlBetrag"))
    ## book content difference into stock
    def book_content(self):
        complete = [self.initial_content, self.content]
        amount = {}
        self.selection_table.new_mainvalue(None)
        add = True
        for content in complete:
            if content and content.get_data_length() > 0:
                for i in range(content.get_data_length()):
                    values = content.get_values("ErsatzteilNr,Anzahl", i)[0]
                    print("AfpInvoice.book_content values:", values)
                    if values[0] and values[1]:
                        if add: anz = Afp_fromString(values[1])
                        else: anz = - Afp_fromString(values[1])
                        if values[0] in amount: 
                            amount[values[0]] += anz
                        else: 
                            amount[values[0]] = anz
                            self.selection_table.add_mainvalue(values[0])
            add = False
        print("AfpInvoice.book_content amount:", amount)
        self.selection_table.load_lock()
        self.selection_table.add_amount(amount)
        self.selection_table.store_stack()
   ## get individual accountnumber for financial accounting
    def get_indi_account(self, KNr):
        konto = 0
        if self.finance:
             konto = self.finance.get_individual_account(KNr)
        return konto
    ## financial transaction will be canceled if the appropriate modul is installed
    def cancel_financial_transaction(self):
        if self.finance:
            original = AfpInvoice(self.globals, self.mainvalue)
            self.finance.add_financial_transactions(original, True)
    ## one line to hold all relevant values of this invoice, to be displayed 
    def line(self):
        zeile =  self.get_string_value("RechNr") + " Rechnung " + self.get_string_value("Zustand").rjust(8) + " vom "  + self.get_string_value("Datum") + " " +  self.get_string_value("Betrag") + " " + self.get_string_value("ZahlBetrag") + " " + self.get_string_value("Zahlung")  
        return zeile
    ## special storage, keep track stock
    # - overwritten from AfpFaktura
    def store(self):
        AfpFaktura.store(self)
        # book from/into stock due to changes
        #print("AfpInvoice.store book")   
        if self.content_has_changed(True):
            self.book_content()
    ## set all necessary values to keep track of the payments \n
    # - overwritten from AfpSelectionList
    # @param payment - amount that has been payed
    # @param datum - date when last payment has been made
    def set_payment_values(self, payment, datum):
        AfpSelectionList.set_payment_values(self, payment, datum)
        Betrag = self.get_value("ZahlBetrag")
        if not Betrag: Betrag = self.get_value("Betrag")
        if self.get_value("Zahlung") >=  Betrag:
            self.set_value("Zustand","closed")
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
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either KvaNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, KvaNr = None, sb = None, debug = None, complete = False):
        AfpFaktura.__init__(self, globals, debug, "KVA")
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["Content"] = [ "KVAIN","RechNr = RechNr.Main ORDER BY PosNr"] 
        self.selects["Rechnung"] = [ "RECHNG","RechNr = TypNr.Main","RechNr"] 
        self.initialize("RechNr.KVA", KvaNr, sb)
        if complete: self.create_selections()
        if self.debug: print("AfpOffer Konstruktor, KvaNr:", self.mainvalue)
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpOffer Destruktor")
    ## one line to hold all relevant values of this offer, to be displayed 
    def line(self):
        zeile =  self.get_string_value("RechNr") + " KVA " + self.get_string_value("Zustand").rjust(8) + " vom "  + self.get_string_value("Datum") + " " +  self.get_string_value("Betrag") + " " + self.get_string_value("ZahlBetrag") + " " + self.get_string_value("Zahlung")  
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
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either BestNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, BestNr = None, sb = None, debug = None, complete = False):
        AfpFaktura.__init__(self, globals, debug, "Bestellung")
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["Content"] = [ "BESTIN","RechNr = RechNr.Main ORDER BY PosNr"] 
        self.selects["Rechnung"] = [ "VERBIND","RechNr = RechNr.Main","RechNr"] 
        self.initialize("RechNr.BESTELL", BestNr, sb)
        if complete: self.create_selections()
        if self.debug: print("AfpOrder Konstruktor, BestNr:", self.mainvalue)
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpOrder Destruktor")
    ## one line to hold all relevant values of this order, to be displayed 
    def line(self):
        zeile =  self.get_string_value("RechNr") + " Bestellung " + self.get_string_value("Zustand").rjust(8) + " vom "  + self.get_string_value("Datum") + " " +  self.get_string_value("Betrag") + " " + self.get_string_value("ZahlBetrag") + " " + self.get_string_value("Zahlung")  
        return zeile
    ## set all necessary values to keep track of the payments \n
    # - overwritten from AfpSelectionList
    # @param payment - amount that has been payed
    # @param datum - date when last payment has been made
    def set_payment_values(self, payment, datum):
        AfpSelectionList.set_payment_values(self, payment, datum)
        if self.get_value("Zahlung") >=  self.get_value("Betrag"):
            self.set_value("Zustand","closed")
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Bestellung vom "  +  self.get_string_value("Datum") + " über " + self.get_string_value("Preis") + " von " + self.get_name()
    ## return names of data columns neede for different grids
    # @param name - name of grid data is designed for
    def get_grid_columns(self, name="Content"):
        if name == "Content":
            return "Nr,ErsatzteilNr,Bezeichnung,Anzahl,Einzelpreis,Gesamtpreis,Lieferung,Zeile,ErsatzteilNr"
    ## return names of data columns neede for different grids
    # @param row - nrow to be modified
    # @param name - name of grid data is designed for
    def get_modified_grid_row(self, row, name="Content"):
        if name == "Content":
            anz = Afp_fromString(row[6])
            if anz:
                if anz == int(anz):
                    anzstr = Afp_toString(int(anz))
                else:
                    anzstr = Afp_toString(anz)
                row[3] += " - " + anzstr
        return row
    def expand_grid_row(self, row):
        # row == [ArtikelNr, Bezeichnung, Anzahl, Einzelpreis, Gesamtpreis, Lieferung]
        change = {}
        if len(row) == 1:
            change["Zeile"] = row[0]
        else:
            change["ErsatzteilNr"] = row[1]
            change["Bezeichnung"] = row[2]
            change["Anzahl"] = row[3]
            change["Einzelpreis"] = row[4]
            change["Gesamtpreis"] = row[5]
            change["Lieferung"] = row[6]
        return change

    

