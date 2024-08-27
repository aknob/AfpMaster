#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpCharter.AfpChRoutines
# AfpChRoutines module provides classes and routines needed for charter handling,\n
# no display and user interaction in this modul.
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        23 Dez. 2019 - move financial routines into selection list- Andreas.Knoblauch@afptech.de \n
#        15 Jan. 2015 - add order list- Andreas.Knoblauch@afptech.de \n
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

from AfpBase.AfpDatabase.AfpSQL import AfpSQLTableSelection
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpSelectionLists import AfpSelectionList

## available 'Zustand' values are set here \n
# This is the definition routine for all available 'Zustand' values
# @param storno - storno possibillity attached to list 
def AfpCharter_getZustandList(storno = False):
    #return ["","KVA","Angebot","Auftrag","Rechnung","Mahnung"]
    if storno:
        return ["Storno","KVA","Angebot","Auftrag","Rechnung","Mahnung"]
    else:
        return ["KVA","Angebot","Auftrag","Rechnung","Mahnung"]
## return 'Zustand' values where financial transaction are needed \n
# This is the definition routine for the above 'Zustand' values
def AfpCharter_getTransactionList():
    return ["Rechnung","Mahnung"]
## return 'Zustand' values where payment is possible  \n
# This is the definition routine for the above 'Zustand' values
def AfpCharter_getPayableList():
    return ["Auftrag","Rechnung","Mahnung","Storno Rechnung"]
## return 'Zustand' values where coach operation planning is possible  \n
# This is the definition routine for the above 'Zustand' values
def AfpCharter_getOperateList():
    return ["Angebot", "Auftrag","Rechnung","Mahnung"]
## returns the different kinds of Charters \n
# - Tagesfahrt - one day trip
# - MTF - (MehrTagesFahrt) journey over serveral days
# - Transfer - just bring and take the group
def AfpCharter_getArtList():
    return ["Tagesfahrt","MTF","Transfer"]
 
## check if 'Zustand' needs financial transactions   
# @param zustand - value to be checked
def AfpCharter_needsTransaction(zustand):
    list = AfpCharter_getTransactionList()
    return zustand in list
## check if 'Zustand' allows payment
# @param zustand - value to be checked
def AfpCharter_isPayable(zustand):
    list = AfpCharter_getPayableList()
    return zustand in list
## check if 'Zustand' allows coach operation actions
# @param zustand - value to be checked
def AfpCharter_isOperational(zustand):
    list = AfpCharter_getOperateList()
    return zustand in list
    
##  get the list of indecies of charter table,
# @param mysql - database where values are retrieved from
# @param index  -  name sort criterium initially selected
def AfpCharter_getOrderlistOfTable(mysql, index):
    keep = ["Abfahrt"]
    if index == "Name":
        keep.append("Name")
    else:
        keep.append("Zielort")
    if index == "Vorgang":
        keep.append("Vorgang")
    else:
        keep.append("SortNr")
    indirect = ["Zielort","Name","SortNr"]
    liste = Afp_getOrderlistOfTable(mysql, "FAHRTEN", keep, indirect)
    return liste
## samples a charter info line from input in 'Fahrtinfo' format
# @param datum, zeit - date and time of info   
# @param dirflags - common string to hold driving direction ("Hin","Her", "Aus") and start or endflag ("Ab","An")   
# @param adresse - adress, to be reached at above time \n
# description of the dirflags see in the routines AfpChInfo_getDirSelValues and AfpChInfo_[s,g]etDirSelection
def AfpChInfo_genLine(datum, zeit, dirflags, adresse):
    if len(dirflags) < 6: 
        dirtag = "Hin Ab"
    else: 
        dirtag = Afp_toString(dirflags)[:6] 
    zeile = Afp_toString(datum)[:5] + " " + Afp_toString(zeit) + "  " + dirtag  + "  " + Afp_toString(adresse)
    return zeile
## text to be shown in selection for the different possibillities of the dirflags
def AfpChInfo_getDirSelValues():
    return ["Hinfahrt", "Rückfahrt","Ausflugsfahrt"],["Ab", "An"]
## translation routine between above text indices and the dirflag values
# @param selfahrt - index in 'Fahrt' array (AfpChInfo_getDirSelValues()[0])
# @param selaban - index in start/end (ab/an) array (AfpChInfo_getDirSelValues()[1])
def AfpChInfo_setDirSelection(selfahrt, selaban):
    if selfahrt == 0: zeile = "Hin"
    elif selfahrt == 1: zeile = "Her"   
    else: zeile = "Aus"
    if selaban == 1: zeile += " An"
    else: zeile += " Ab"
    return zeile
## translation routine between the dirflag values and the text indices 
# @param dirtags - string to hold dirflags ("Hin","Her", "Aus") and ("Ab","An") \n
# "Hin" and "Ab" are assumed as default and will be altered if one of the other keyword is in string
def AfpChInfo_getDirSelection(dirtags):
    selfahrt = 0
    selaban = 0
    if dirtags:
        if "Aus" in dirtags: selfahrt = 2
        elif "Her" in dirtags: selfahrt = 1
        if "An" in dirtags: selaban = 1
    return selfahrt, selaban

## baseclass for charter handling         
class AfpCharter(AfpSelectionList):
    ## initialize AfpCharter class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param FahrtNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either FahrtNr or sb (superbase) has to be given for initialisation,otherwise a new, clean object is created
    def  __init__(self, globals, FahrtNr = None, sb = None, debug = None, complete = False):
        AfpSelectionList.__init__(self, globals, "Charter", debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.finance = None
        self.new = False
        self.mainindex = "FahrtNr"
        self.mainvalue = ""
        if sb:
            self.mainvalue = sb.get_string_value("FahrtNr.FAHRTEN")
            Selection = sb.gen_selection("FAHRTEN", "FahrtNr", debug)
            self.selections["FAHRTEN"] = Selection
        else:
            if FahrtNr:
                self.mainvalue = Afp_toString(FahrtNr)
            else:
                self.new = True
        self.mainselection = "FAHRTEN"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)   
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr = KundenNr.FAHRTEN"] 
        self.selects["FAHRTI"] = [ "FAHRTI","FahrtNr = FahrtNr.FAHRTEN"] 
        self.selects["FAHRTEX"] = [ "FAHRTEX","FahrtNr = FahrtNr.FAHRTEN"] 
        self.selects["ARCHIV"] = ["ARCHIV", "Tab = \"FAHRTEN\" AND TabNr = FahrtNr.FAHRTEN"]
        self.selects["AUSGABE"] = [ "AUSGABE", "Modul = \"Charter\" AND Art = \"" + self.get_listname()  + "\" AND Typ = Zustand.FAHRTEN"] 
        #self.selects["AUSGABE"] = [ "AUSGABE","Typ = Zustand.FAHRTEN"] 
        self.selects["FAHRTVOR"] = [ "FAHRTVOR","VorgangsNr = Vorgang.FAHRTEN","VorgangsNr"] 
        self.selects["RECHNG"] = [ "RECHNG","RechNr = RechNr.FAHRTEN","RechNr"] 
        self.selects["ERTRAG"] = [ "ERTRAG","FahrtNr = -FahrtNr.FAHRTEN"] 
        self.selects["EINSATZ"] = [ "EINSATZ","MietNr = FahrtNr.FAHRTEN"] 
        self.selects["Kontakt"] = [ "ADRESSE","KundenNr = KontaktNr.FAHRTEN"] 
        self.selects["RechAdresse"] = [ "ADRESSE","KundenNr = KundenNr.RECHNG"] 
        if complete: self.create_selections()
        if not self.globals.skip_accounting():
            self.finance_modul = Afp_importAfpModul("Finance", self.globals)[0]
            if self.finance_modul:
                self.finance = self.finance_modul.AfpFi_getFinanceTransactions(self.globals)
        print("AfpCharter.finance:", self.finance)
        if self.debug: print("AfpCharter Konstruktor, FahrtNr:", self.mainvalue)
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpCharter Destruktor")
        #AfpSelectionList.__del__(self) 
    ## decide whether this incident has been cancelled
    def is_canceled(self):
        return "Storno" in self.get_value("Zustand")
    ## decide whether payment is possible or not
    def is_payable(self):
        payable = False
        zustand = self.get_string_value("Zustand")
        if AfpCharter_isPayable(zustand): payable = True
        return payable
    ## charter will be tracked with financial transaction (accounted)
    def is_accountable(self):
        zustand = self.get_value("Zustand.FAHRTEN")
        return AfpCharter_needsTransaction(zustand)
    ## clear current SelectionList to behave as a newly created List 
    # @param KundenNr - KundenNr of newly seelected adress, == None if address is kept
    # @param keep_flag -  flags which data should be kept while creation this copy
    # - [0] == True: address should be kept (should coincident with KundenNr == None)
    # - [1] == True: contact should be kept 
    # - [2] == True: Fahrtinfo should be kept 
    # - [3] == True: Fahrtextra should be kept 
    # - [4] == True: the rest of the data should be kept 
    def set_new(self, KundenNr, keep_flag = None):
        self.new = True
        data = {}
        keep = []
        if KundenNr:
            data["KundenNr"] = KundenNr
        else:
            data["KundenNr"] = self.get_value("KundenNr")
            keep.append("ADRESSE")
        if keep_flag:
            if keep_flag[1]: # contact kept
                data["Kontakt"] = self.get_value("Kontakt")
                data["Name"] = self.get_value("Name")
                keep.append("Kontakt")
            if keep_flag[2] and "FAHRTI" in self.selections: # Fahrtinfo kept
                keep.append("FAHRTI")
                self.selections["FAHRTI"].new = True
            if keep_flag[3] and "FAHRTEX" in self.selections: # Fahrtextra kept
                keep.append("FAHRTEX")
                self.selections["FAHRTEX"].new = True
                data["Extra"] = self.get_value("Extra") 
                data["Preis"] = self.get_value("Preis") 
                data["PersPreis"] = self.get_value("PersPreis") 
            elif keep_flag[4] and not "FAHRTEX" in self.selections: # Fahrtextra kept
                data["Preis"] = self.get_value("Preis") 
                data["PersPreis"] = self.get_value("PersPreis") 
            if keep_flag[4]: # data kept
                data["Abfahrt"] = self.get_value("Abfahrt") 
                data["Fahrtende"] = self.get_value("Fahrtende") 
                data["Abfahrtsort"] = self.get_value("Abfahrtsort") 
                data["Zielort"] = self.get_value("Zielort") 
                data["Personen"] = self.get_value("Personen") 
                data["Km"] = self.get_value("Km") 
                data["Kostenst"] = self.get_value("Kostenst") 
                data["Vorgang"] = self.get_value("Vorgang") 
                data["Ausstattung"] = self.get_value("Ausstattung") 
                data["Von"] = self.get_value("Von") 
                data["Nach"] = self.get_value("Nach") 
        data["Zustand"] = AfpCharter_getZustandList()[0]
        data["Art"] = self.get_value("Art")
        if data["Art"] is None:  data["Art"] = AfpCharter_getArtList()[0]
        if not "Von" in data: data["Von"] = "von"
        if not "Nach" in data: data["Nach"] = "nach"
        data["Datum"] = self.globals.today()
        print("AfpCharter.set_new data:", data)
        print("AfpCharter.set_new keep:", keep)
        self.clear_selections(keep)
        self.set_data_values(data,"FAHRTEN")
        if keep_flag:
            if keep_flag[2] or keep_flag[3]:
                self.spread_mainvalue()
        if KundenNr:
            self.create_selection("ADRESSE", False)
    ## financial transaction will be initated if the appropriate modul is installed
    # @param initial - flag for initial call of transaction (interal payment may be added)
    def execute_financial_transaction(self, initial):
        if self.finance:
            self.finance.add_financial_transactions(self)
            if initial: self.finance.add_internal_payment(self)
            self.finance.store()
    ## financial transaction will be canceled if the appropriate modul is installed
    def cancel_financial_transaction(self):
        if self.finance:
            original = AfpCharter(self.globals, self.mainvalue)
            self.finance.add_financial_transactions(original, True)
    ## a separate invoice is created and filled with the appropriate values
    def add_invoice(self):
        print("AfpCharter.add_invoice")
        invoice = AfpSQLTableSelection(self.get_mysql(), "RECHNG", self.debug, "RechNr")
        KNr = self.get_value("KundenNr")
        data = {"Datum": self.globals.today(), "KundenNr": KNr, "Name": self.get_name(True), "Fahrt": self.get_value("FahrtNr")}
        data["Debitor"] = Afp_getIndividualAccount(self.get_mysql(), KNr)
        betrag = self.get_value("Preis")
        data["Zahlbetrag"] = betrag
        betrag2 = self.extract_taxfree_portion()
        if betrag2:
            betrag -= betrag2
            data["Betrag2"] = betrag
            data["Konto2"] = Afp_getSpecialAccount(self.get_mysql(), "EMFA")
        data["RechBetrag"] = betrag
        data["Kontierung"] = Afp_getSpecialAccount(self.get_mysql(), "EMF")
        data["Zustand"] = "open"
        data["Wofuer"] = "Mietfahrt Nr " + self.get_string_value("FahrtNr") + " am " + self.get_string_value("Abfahrt") + " nach " + self.get_string_value("Zielort")
        if self.get_value("ZahlDat"):
            data["Zahlung"] = self.get_value("Zahlung")
            data["ZahlDat"] = self.get_value("ZahlDat")
            if data["Zahlung"] >= betrag: data["Zustand"] = "closed"
        invoice.new_data()
        invoice.set_data_values(data)
        self.selections["RECHNG"] = invoice
    ## taxfree portion of price is extracted and returned
    def extract_taxfree_portion(self):
        print("AfpCharter.extract_taxfree_portion")
        betrag = self.get_value("Preis")
        netto = self.get_value("Netto.ERTRAG")
        umst = self.get_value("Umst.ERTRAG")
        if netto and umst:
            betrag -= (netto + umst)
        else:
            betrag = self.generate_taxfree_portion(betrag)
        return betrag
    ## taxfree portion of price is generated from the different data entries
    # @param betrag - price where taxfree portion has to be extracted
    def generate_taxfree_portion(self, betrag):
        print("AfpCharter.generate_taxfree_portion")
        taxfree = 0.0
        tax = 0.0
        if self.get_value("Extra"):
            rows = self.get_value_rows("FAHRTEX","Preis,Inland")
            for row in rows:
                if row[1] == "A":
                    taxfree += row[0]
                elif row[1] == "I":
                    tax += row[0]
        km = self.get_value("km")
        kmA = self.get_value("Ausland")
        if kmA:
            betrag -=  (tax + taxfree)
            taxfree += kmA*betrag/km
        return taxfree
    ## routine to hold separate invoice syncron to the actuel charter values
    def syncronise_invoice(self):
        print("AfpCharter.syncronise_invoice")
        betrag = self.get_value("Preis")
        data = {}
        data["Zahlbetrag"] = betrag
        betrag2 = self.extract_taxfree_portion()
        if betrag2:
            betrag -= betrag2
            data["Betrag2"] = betrag
        data["RechBetrag"] = betrag
        if self.get_value("ZahlDat"):
            data["Zahlung"] = self.get_value("Zahlung")
            data["ZahlDat"] = self.get_value("ZahlDat")
        #print "AfpCharter.syncronise_invoice data:", data
        self.set_data_values(data, "RECHNG")
    ## one line to hold all relevant values of charter, to be displayed 
    def line(self):
        zeile =  self.get_string_value("SortNr").rjust(8) + "  "  + self.get_string_value("Datum") + " " +  self.get_string_value("Zustand") + " " + self.get_string_value("Art") + " " + self.get_string_value("Zielort")  
        zeile += " " + self.get_string_value("Preis").rjust(10) + " " +self.get_string_value("Zahlung").rjust(10) 
        return zeile
    ## internal routine to set the appropriate contact name
    def set_kontakt_name(self):
        #name = self.get_name(False,"Kontakt") + " " + self.get_string_value("KontaktNr")
        name = self.get_name(False,"Kontakt")
        self.set_value("Kontakt",name)
    ## set all necessary values to keep track of the payments
    # @param payment - amount that has been payed
    # @param datum - date when last payment has been made
    def set_payment_values(self, payment, datum):
        AfpSelectionList.set_payment_values(self, payment, datum)
        if self.get_value("RechNr"):
            self.set_value("Zahlung.RECHNG", payment)
            self.set_value("ZahlDat.RECHNG", datum)
    ## extract payment relevant data from SelectionList for 'Finance' modul, overwritten from AfpSelectionList
    # has to return the account number this payment has to be charged ("Gegenkonto")
    # @param paymentdata - payment data dictionary to be modified and returned
    def add_payment_data(self, paymentdata):
        if self.get_value("RechNr.Fahrten"):
            paymentdata["Gegenkonto"] = self.get_value("Debitor.RECHNG") 
            paymentdata["GktName"] = self.get_name(True, "RechAdresse") 
            print("AfpCharter.add_payment_data:",paymentdata)
            if not paymentdata["Gegenkonto"]:
                paymentdata["Gegenkonto"]  = Afp_getIndividualAccount(self.get_mysql(), self.get_value("KundenNr"))
                paymentdata["GktName"] = self.get_name(True) 
                print("AfpCharter.add_payment_data fallback:", paymentdata)
        else:
            paymentdata["Gegenkonto"] = Afp_getSpecialAccount(self.get_mysql(), "MFA")
            paymentdata["GktName"] = "MFA"
        return paymentdata
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Mietfahrt am "  +  self.get_string_value("Abfahrt") + " nach " + self.get_string_value("Zielort")

