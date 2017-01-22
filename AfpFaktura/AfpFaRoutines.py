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
 
 ## return index of name in filter list
 # @param name - name to be looked for in filter list
def AfpFa_inFilterList(name):
    names =  AfpFaktura_FilterLists("names")
    if name in names:
        return names.index(name)
    return None
## returns all possible entries of filter list
# @param name - indicator what has to be returned \n
# - if name is in 'names', the appropriate 'tables' and 'filters' entry is returned
# - if name == "names": the list 'names' is returned
# - else: all three lists are returned
def AfpFaktura_FilterLists(name):
    #names = ["Ausgabe","Forderung","Waren","Bestellung","KVA","Angebot","Auftrag","Rechnung","Mahnung","Einnahme"]
    names = ["Ausgabe","Waren","Bestellung", "-------------------------", "KVA","Angebot","Auftrag", "-------------------------","Rechnung","Mahnung","Einnahme"]
    tables = ["BESTELL","BESTELL","BESTELL","",                                               "KVA", "KVA",       "KVA",      "",                                            "RECHNG",    "RECHNG",  "RECHNG"]
    filters = ["beglichen","erhalten","offen","",                                               "",     "Angebot", "Auftrag","",                                            "offen",    "Mahnung",  "bezahlt"]
    if name in names:
        ind = names.index(name)
        return tables[ind], filters[ind]
    elif name == "names":
        return names
    else:
        return names, tables, filters

##  get the list of indecies of the appropriate faktura table,
def AfpFaktura_getOrderlistOfTable():
    #liste = {'RechNr':'int','Datum':'date', 'KundenNr':'string'}
    liste = {'RechNr':None,'Datum':'date', 'KundenNr':'string'}
    return liste
    
## baseclass for invoice handling         
class AfpFaktura(AfpSelectionList):
    ## initialize AfpFaktura class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param AnmeldNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved durin initialisation \n
    # \n
    # either AnmeldNr or sb (superbase) has to be given for initialisation,otherwise a new, clean object is created
    def  __init__(self, globals, debug = None, Name = "Faktura"):
        AfpSelectionList.__init__(self, globals, Name, debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.finance = None
        self.new = False
        self.mainindex = "RechnungsNr"
        self.mainvalue = ""
        self.maintable = "RECHNG"
        self.spezial_bez = []

        self.mainselection = "Main"
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr = KundenNr.Main"] 
        self.selects["Dependance1"] = [ "GERAETE","KundenNr = KundenNr.Main AND GeraeteNr = AttNr.Main"] 
        self.selects["Content"] = [ "RECHIN","RechNr = RechNr.Main"] 
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
    #  REMARK: only selects wihich are given will be overwritten, selects not mentioned will not be touched \n
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
        if self.debug: print "AfpFaktura.initialize(d) with the following values:", self.mainvalue, self.mainindex, self.maintable
    ## set the customised select_clause for the main selection - overwritten from AfpSelectionList
    def set_main_selects_entry(self):  
        #print "AfpFaktura.set_main_selects_entry:",self.mainselection, self.mainindex, self.mainvalue
        if self.mainselection and self.mainindex and self.mainvalue:         
            self.selects[self.mainselection] = [self.maintable, self.mainindex + " = " + self.mainvalue, self.mainindex]
            #print "AfpFaktura.set_main_selects_entry selects:", self.selects
                
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
            raw = self.get_string_rows("Content","Nr,ErsatzteilNr,Bezeichnung,Anzahl,Einzelpreis,Gesamtpreis,ErsatzteilNr")
            #print "AfpFaktura.get-grid_rows raw:",raw
            lgh = len(raw)
            rows = []
            for i in range(len(raw)-1, -1, -1):
                row = raw[i]
                zeile = Afp_intString(row[1])
                if zeile:
                    row[0] = ""
                    row[1] = self.get_zeile(zeile)
                    for j in range(2,len(row)):
                        row[j] = ""
                else:
                    anz = Afp_fromString(row[3])
                    if anz == int(anz):
                        row[3] = Afp_toString(int(anz))
                rows.append(row)
        #print "AfpFaktura.get-grid_rows:",rows
        return rows
    ## get text form 'Zeilen' database
    # @param ZNr - identifier of text in database
    def get_zeile(self, ZNr):
        rows = self.globals.get_mysql().select("Zeile","ZeilenNr = " + Afp_toString(ZNr), "ZEILEN")
        #print "AfpFaktura.get_zeile:", Afp_toString(rows[0][0])
        if rows:
            return Afp_toString(rows[0][0])
        else:
            return ""
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Mietfahrt am "  +  self.get_string_value("Abfahrt") + " nach " + self.get_string_value("Zielort")
        
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
    ## initialize AfpTour class
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
        self.selects["Content"] = [ "KVAIN","RechNr = RechNr.Main"] 
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
        self.selects["Content"] = [ "BESTIN","RechNr = RechNr.Main"] 
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


