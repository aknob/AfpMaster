#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseFiRoutines
# AfpBaseFiRoutines module provides classes and routines needed for finance handling,\n
# no display and user interaction in this modul.
#
#   History: \n
#        14 July. 2025 - add Archiv to AfpCommonInvoice - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        23 Dez. 2019 - move financial routines into selection list- Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        14 Feb. 2014 - inital code generated - Andreas.Knoblauch@afptech.de

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

from AfpBase.AfpSelectionLists import *
from AfpBase.AfpBaseRoutines import *
    
## get name from address with given identifier, when only sql connetion is given
# @param mysql - mysql connection to database
# @param KNr - KundenNr, identifier of address
# @param rev - rerverse flag, if true, lastname, firstname is retuned
def AfpFinance_getNameFromKNr(mysql, KNr, rev=False):
    rows = mysql.select("Vorname,Name", "KundenNr = " + Afp_toString(KNr), "ADRESSE")
    if rows and len(rows[0]) > 1:
        row = rows[0]
        if rev:
            return row[1] + " " + row[0]
        else:
            return row[0] + " " + row[1]
    else:
        return "Kein Adresseintrag für KundenNr " + Afp_toString(KNr)

## add tax to a given value
# @param globals - global variables, including tax values
# @param netto - value where tax has to be added
# @param halftax - if given, flag if half tax rate has to be used, at the moment: V,F -full rate, H- half rate
def AfpFinance_addTax(globals, netto,  halftax=None):
    if  globals.get_value("no-tax"):
        return netto
    if halftax:
        rate = globals.get_value("half-tax")
        if not rate: rate = 19    
    else:
        rate = globals.get_value("standard-tax")
        if not rate: rate = 19
    if not netto: netto = 0.0
    percent = netto/100.0
    return (100.0 + rate) *percent
## subtract tax from a given value
# @param globals - global variables, including tax values
# @param brutto - value where tax has to be sbstracted
# @param halftax - if given, flag if half tax rate has to be used, at the moment: V,F -full rate, H- half rate
def AfpFinance_stripTax(globals, brutto,  halftax=None):    
    if  globals.get_value("no-tax"):
        return brutto
    if halftax:
        rate = globals.get_value("half-tax")
        if not rate: rate = 19    
    else:
        rate = globals.get_value("standard-tax")
        if not rate: rate = 19
    one_percent = brutto/(100.0 + rate)
    return 100.0 *one_percent
    
##class for payment in afp-modules
class AfpZahlung(object):
    ## initialize payment class, \n
    # if avaulable attach modul to record financial transactions
    # @param data - SelectionList where payment is due to - this input is mandatory
    # @param multi - if given, additional entries will be retrieved from database with identic values in this column(s)
    def  __init__(self, data , multi = None):
        self.globals = data.get_globals()
        self.mysql = self.globals.get_mysql()
        self.moduls = {}
        self.debug = data.is_debug()
        self.amount = []
        self.partial = []
        self.balance = []
        self.distribution = None
        self.finance_modul = None
        self.finance = None
        self.auszug = None
        self.datum = self.globals.today()
        self.selected_list = [data]
        self.append_payment_data(data)
        if multi:
            if Afp_isString(multi):
                multi = [multi]
            select = ""
            for mult in multi:
                value = data.get_string_value(mult)
                if value:
                    if select: select += " AND "
                    select += mult + " = " + Afp_toQuotedString(value)
            if select:
                feld = data.get_mainindex()
                table = data.get_selection().get_tablename()
                rows = self.mysql.select(feld, select, table)
                #print "AfpZahlung mysql:", table, feld, select, rows
                if len(rows) > 1:
                    ident = Afp_fromString(data.get_value())
                    for row in rows:
                        if row[0] != ident: 
                            self.add_selection(table, row[0])
        if not self.globals.skip_accounting():
            self.finance_modul = Afp_importAfpModul("Finance", self.globals)[0]
            if self.finance_modul:
                #self.finance = self.finance_modul.AfpFinanceTransactions(self.globals)
                self.finance = self.finance_modul.AfpFinance(self.globals)
        #print "AfpZahlung.finance:", self.finance
        if self.debug: print("AfpZahlung Konstruktor:", multi)
    ## destructor
    def __del__(self):    
        if self.debug: print("AfpZahlung Destruktor")
    ## view data in console, convinience routine for debug purpose     
    def view(self):
        print("AfpZahlung.view():")
        for data in self.selected_list: data.view()
        if self.finance: self.finance.view() 
    ## return if finance modul is attached
    def has_finance(self):
        return not self.finance is None
    ## check if a tableselection according to given values is avauilable
    # @param tablename - name of database table to be checked
    # @param nr - identification number checked
    def check_selection(self, tablename, nr):
        found = False      
        for data in self.selected_list:
            if data.get_selection().get_tablename() == tablename and data.get_value() == nr: 
                found = True
        return found
    ## check if statement of account (Auszug) exists, if not create one
    # @param auszug - identifier of statemen of account
    def check_auszug(self, auszug):
        datum = None
        print("AfpZahlung.check_auszug:", auszug)
        if self.finance:
            check = self.finance.check_auszug(auszug)
            if check:
                datum = self.finance.get_value("BuchDat.AUSZUG") 
            else:
                datum = self.get_date_from_cash(auszug)
                if datum: check = True
        else:
            datum = self.get_date_from_cash(auszug)
            if datum: check =  True
        if check:   
            self.set_auszug(auszug, datum)
        return check
     ## get name of the statement of account for cash ("Bar") payment
    def get_cash_auszug(self):
        today = self.globals.today()
        return "BAR-" + Afp_toInternDateString(today)[5:]   
        #return "BAR-" + Afp_toShortDateString(today)  
    ## extract date from statement of account identifier, if possible
    # @param auszug - statement of account identifier to be analysed
    def get_date_from_cash(self, auszug):
        date = None
        if "-" in auszug:
            dat = auszug[4:]
            split = dat.split("-")
            if split and split[0]:
                month = int(split[0])
                if len(split) > 1:
                    if "/" in split[1]:
                        ssplit = split[1].split("/")
                        year = int(ssplit[1])
                        day = int(ssplit[0])
                    else:
                        day = int(split[1])
                        year = self.globals.today().year
                    date = Afp_genDate(year, month, day)
        return date
    ## check if statement of account (Auszug) exists, if not create one
    # @param auszug - identifier of statemen of account
    # @param datum -  the date when statement has been recorded
    def set_auszug(self, auszug, datum):
        if auszug == self.auszug and datum is None: return
        self.auszug = auszug 
        if self.finance:
                if datum is None: datum = self.globals.today()
                self.finance.set_auszug(auszug, datum)
        else:
            datum = self.globals.today()
        self.datum = datum
        #print "AfpZahlung.set_auszug:", self.auszug, self.datum
    ## append given data to participate from this payment
    # @param data - SelectionList holding data for payment
    def append_payment_data(self, data):
        amount, partial, dummy = data.get_payment_values()
        #print "AfpZahlung.append_payment_data:", amount, partial, dummy
        self.amount.append(amount)
        self.partial.append(partial)
        if self.partial[-1] is None: self.partial[-1] = 0.0      
        self.balance.append(int(100* (self.amount[-1] - self.partial[-1])))      
        #print "AfpZahlung.append_payment_data:", self.amount, self.partial, self.balance
    ## set values of partial payment in data, invoke financial transaction
    # @param index - index of payment part in selection list
    def set_payment_data(self, index):
        data = self.selected_list[index]
        payment = float(self.distribution[index])/100
        tablename = data.get_selection().get_tablename()
        if Afp_isEps(payment):
            sum = self.partial[index] + payment
            data.set_payment_values(sum, self.datum)
            self.add_payment_transaction(payment, data)
            self.partial[index] = sum
    ## add a selection made from the database to this payment
    # @param tablename - name of database table to added
    # @param nr - identification number of database row to be added
    def add_selection(self, tablename, nr):
        added = False
        sellist = None
        if not self.check_selection(tablename, nr):
            if tablename == "FAHRTEN":
                modul = self.get_modul("AfpCharter.AfpChRoutines")
                if modul:
                    sellist = modul.AfpCharter(self.globals, nr, None, self.debug)
            elif tablename == "RECHNG":
                sellist = AfpCommonInvoice(self.globals, nr, self.debug)
            elif tablename == "ANMELD":
                #modul = self.get_modul("AfpTourist.AfpToRoutines")
                modul = self.get_modul("AfpEvent.AfpEvRoutines")
                if modul:
                    sellist = modul.AfpEvClient(self.globals, nr, None, self.debug)
            # look if payment is needed
            if sellist and sellist.get_payment_values()[0]:
                sellist.lock_data()
                self.selected_list.append(sellist)
                self.append_payment_data(sellist)
                self.distribution = None
                added = True
        #print "AfpZahlung.add_selection:", tablename, nr, sellist, added
        return added
    ## invoke financial transaction for a payment. if desired
    # @param payment - amount of payment to be recorded
    # @param data - if given, SelectionList for which transaction should be recorded
    def add_payment_transaction(self, payment, data = None):
        # data == None: multiple payment to be booked through intermediate account
        if self.debug: print("AfpZahlung.add_payment_transaction():", payment, data)
        if self.finance: 
            self.finance.add_payment(payment, self.datum, self.auszug, self.get_KundenNr(), self.get_name(), data)
    ## remove a selection from selection list
    # @param index - index of selection of list
    def remove_selection(self, index):
        if index < len(self.selected_list):
            del self.selected_list[index]
            del self.amount[index]
            del self.partial[index]
            del self.balance[index]
    ## attach needed python-modul for dymanic access 
    # @param name - name of needed modul
    def get_modul(self, name):
        if not name in self.moduls:
            modul = Afp_importPyModul(name, self.globals)
            if modul: self.moduls[name] = modul
        if name in self.moduls:
            return self.moduls[name]
        else:
            return None
    # convinience routines simular to AfpSelectionList
    ## return global data
    def get_globals(self):
        return self.globals
    ## return mysql connection
    def get_mysql(self):
        return self.mysql
    ## return if debug flag is set
    def get_debug(self):
        return self.debug  
    ## return initial selection of this payment
    def get_data(self):
        return self.selected_list[0]
    ## return value of initial selection
    # @param DateiFeld - name of tablecoöumn (column.table)
    def get_value(self,DateiFeld):
        return self.get_data().get_value(DateiFeld)
    ## return value of initial selection as a string
    # @param DateiFeld - name of tablecoöumn (column.table)
    def get_string_value(self,DateiFeld):
        #print DateiFeld
        return self.get_data().get_string_value(DateiFeld)
    ## return the name of involved person for this payment
    def get_name(self):
        data = self.get_data()
        name = data.get_string_value("Vorname.ADRESSE") + " " + data.get_string_value("Name.ADRESSE") 
        return name  
    ## return the address identification number of involved person for this payment
    def get_KundenNr(self):
        KNr = self.get_data().get_value("KundenNr")
        return KNr
    ## return the sum of all selected prices as a string
    def get_preis(self):
        preis = 0.0
        for prs in self.amount:
            preis += prs
        return Afp_toString(preis)
    ## return the sum of all already recorded payments as a string
    def get_anzahlung(self):
        anzahlung = 0.0
        for anz in self.partial:
            anzahlung += anz
        return Afp_toString(anzahlung)
   ## return the payment left to balance all attached selections
    def get_payment_left(self):
        preis = Afp_floatString(self.get_preis())
        anz = Afp_floatString(self.get_anzahlung())
        return preis - anz
    ## return possibly made overpayment
    def get_gutschrift(self):
        anz = self.get_payment_left()
        if anz < 0: return Afp_toString(- anz)
        return ""
    ## return list to be displayed for the selections of this payment
    def get_display_list(self): 
        #print "AfpZahlung.get_display_list:", self.selected_list
        liste = []
        for entry in self.selected_list:
            liste.append(entry.get_listname()[:4] + ": " + entry.line())
        return liste
    ## distributes the given payment to all selected data entries \n
    # should only be called once, when all data has been gathered
    # @param value - amount of payment
    def distribute_payment(self, value):
        if Afp_isEps(value):
            self.generate_distribution(value)
            lgh = len(self.selected_list)
            # charge payment on intermediate account
            if lgh > 1: 
                self.add_payment_transaction(value)
            # execute each gathered payment
            for i in range(lgh):
                self.set_payment_data(i)
    ## core routine to generate distribution of payment to selected data, \n
    # pure integer calculation on cent basis is used.
    # @param value - amount of payment
    def generate_distribution(self, value):
        # pure integer calculation on cent basis
        if Afp_isEps(value):
            distribute = int(value*100)
            balance = 0
            for bal in self.balance:
                balance += bal
            if distribute >= balance:
                self.distribution = self.balance
                if distribute > balance:
                    self.distribution[0] += distribute -  balance
            else:
                #lgh = len(self.selected_list)
                lgh = len(self.amount)
                self.distribution = [0]*lgh  
                filled = 0
                while filled < lgh and distribute > lgh - filled:
                    entries = lgh - filled
                    per_entry = int(distribute/entries)
                    #print "while:", distribute, per_entry, filled
                    kept = 0
                    spend = 0
                    for i in range(0,lgh):
                        amount_left = self.balance[i] - self.distribution[i]
                        if amount_left:
                            if per_entry < amount_left:
                                self.distribution[i] += per_entry
                                spend += per_entry
                            else:
                                spend += self.balance[i] - self.distribution[i] 
                                self.distribution[i] = self.balance[i]
                                filled += 1
                        #print i, amount_left, self.distribution[i], spend
                    distribute -= spend
                #print "end while", filled, distribute, spend
                if distribute > 0:
                    self.distribution[0] += distribute
    ## write this payment to database
    def store(self):
        for entry in self.selected_list: entry.store()
        if self.finance: self.finance.store()
            
## common invoice base class (outgoing)
class AfpCommonInvoice(AfpPaymentList):
    ## initialise a invoice base class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param RechNr - if given, data will be retrieved this database entry
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # RechNr has to be supplied,  otherwise a new, clean object is created
    def  __init__(self, globals, RechNr = None, debug = False, complete = False):
        AfpPaymentList.__init__(self, globals, "Rechnung", debug)
        self.debug = debug
        self.new = False
        self.mainindex = "RechNr"
        self.mainvalue = ""
        if RechNr:
            self.mainvalue = Afp_toString(RechNr)
        else:
            self.new = True
        self.mainselection = "RECHNG"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)   
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr = KundenNr.RECHNG"] 
        self.selects["FAHRTEN"] = [ "FAHRTEN","RechNr = RechNr.RECHNG"] 
        self.selects["AUSGABE"] = [ "AUSGABE", "Modul = \"Finance\" AND Art = \"" + self.get_listname()  + "\" AND Typ = \"Common\""] 
        self.selects["ARCHIV"] = [ "ARCHIV","TabNr = RechNr.RECHNG AND Tab = \"RECHNG\""] 
        #self.selects["Original"] = [ Typ.RECHNG,"RechNr = TypNr.RECHNG"] 
        if complete: self.create_selections()
        # set payment related data
        payment_values = {"cancel":"Zustand",  "cancel_value":"Storno", "price":"ZahlBetrag,Betrag", "text":"Bem"}
        self.set_payment_data(payment_values)

        if self.debug: print("AfpCommonInvoice Konstruktor, RechNr:", self.mainvalue)
    ## destructor
    def __del__(self):    
        if self.debug: print("AfpCommonInvoice Destruktor")
        #AfpSelectionList.__del__(self) 
    ## clear current SelectionList to behave as a newly created List 
    # @param KundenNr - KundenNr of newly selected adress, == None if address is kept   
    def set_new(self, KundenNr):
        self.new = True
        data = {}
        keep = []
        if KundenNr:
            data["KundenNr"] = KundenNr
        else:
            data["KundenNr"] = self.get_value("KundenNr")
            keep.append("ADRESSE")
        data["Zustand"] = "Open"
        #data["Datum"] = self.globals.today_string()
        data["Datum"] = self.globals.today()
        #print data
        #print keep
        self.clear_selections(keep)
        self.set_data_values(data,"RECHNG")
        if KundenNr:
            self.create_selection("ADRESSE", False)
            self.set_value("Name", self.get_name(True))
    ## one line to hold all relevant values of this invoice to be displayed 
    def line(self):
        betrag = self.get_value("Betrag")
        if self.get_value("ZahlBetrag"):
            betrag = self.get_value("ZahlBetrag")
        zeile = self.get_string_value("RechNr").rjust(8) + " " + self.get_string_value("Datum") + " " + self.get_string_value("Bem") + " " 
        zeile += Afp_toString(betrag).rjust(10)  + " " + self.get_string_value("Zahlung").rjust(10)
        return zeile 
    ## switch 'Zustand' from open (open) to payed (closed) if necessary
    def set_zustand(self):
        if self.get_value("Zustand") == "Open" and self.get_value("Zahlung") >= self.get_value("ZahlBetrag"):
            self.set_value("Zustand","Closed")
    ## routine to retrieve payment data from SelectionList \n
    #  overwritten, from AfpSelectionList
    def get_payment_values(self):
        betrag = self.get_value("Betrag")
        if self.get_value("ZahlBetrag"):
            betrag = self.get_value("ZahlBetrag")
        zahlung = self.get_value("Zahlung")
        if betrag is None: betrag = 0.0
        if zahlung is None: zahlung = 0.0
        print("AfpCommonInvoice.get_payment_values:", betrag, zahlung)
        return betrag, zahlung, self.get_value("ZahlDat")
    ## set internal payment values
    # @param payment - amount of payment
    # @param datum - date when last payment has been done
    def set_payment_values(self, payment, datum):
        AfpSelectionList.set_payment_values(self, payment, datum)
        self.set_zustand()
        if self.get_value("Typ") and self.get_value("Typ")  == "FAHRTEN":
            self.set_value("Zahlung.FAHRTEN", payment)
            self.set_value("ZahlDat.FAHRTEN", datum)
    ## extract payment relevant data from SelectionList for 'Finance' modul, overwritten from AfpSelectionList
    # has to return the account number this payment has to be charged ("Gegenkonto")
    # @param paymentdata - payment data dictionary to be modified and returned
    def add_payment_data(self, paymentdata):
        paymentdata["Gegenkonto"] = self.get_value("Debitor.RECHNG") 
        if not paymentdata["Gegenkonto"]:
            paymentdata["Gegenkonto"]  = Afp_getIndividualAccount(self.get_mysql(), self.get_value("KundenNr"))
        paymentdata["GktName"] = self.get_name(True) 
        print("AfpCommonInvoice.add_payment_data:",paymentdata)
        return paymentdata

## common invoice base class (incoming)
class AfpObligation(AfpPaymentList):
    ## initialise a invoice base class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param RechNr - if given, data will be retrieved this database entry
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # RechNr has to be supplied,  otherwise a new, clean object is created
    def  __init__(self, globals, RechNr = None, debug = False, complete = False):
        AfpPaymentList.__init__(self, globals, "Verbindlichkeit", debug)
        self.debug = debug
        self.new = False
        self.mainindex = "RechNr"
        self.mainvalue = ""
        if RechNr:
            self.mainvalue = Afp_toString(RechNr)
        else:
            self.new = True
        self.mainselection = "VERBIND"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)   
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr = KundenNr.VERBIND"] 
        self.selects["ARCHIV"] = [ "ARCHIV","TabNr = RechNr.VERBIND AND Tab = \"VERBIND\""] 
        if complete: self.create_selections()
        # set payment related data
        payment_values = {"outgoing":True, "cancel":"Zustand",  "cancel_value":"Storno", "price":"ZahlBetrag,Betrag", "text":"ExternNr,Bem"}
        self.set_payment_data(payment_values)
        if self.debug: print("AfpObligation Konstruktor, RechNr:", self.mainvalue)
    ## destructor
    def __del__(self):    
        if self.debug: print("AfpObligation Destruktor")
    ## clear current SelectionList to behave as a newly created List 
    # @param KundenNr - KundenNr of newly seelected adress, == None if address is kept   
    def set_new(self, KundenNr):
        self.new = True
        data = {}
        keep = []
        if KundenNr:
            data["KundenNr"] = KundenNr
        else:
            data["KundenNr"] = self.get_value("KundenNr")
            keep.append("ADRESSE")
        data["Zustand"] = "Open"
        data["Datum"] = self.globals.today_string()
        #print data
        #print keep
        self.clear_selections(keep)
        self.set_data_values(data,"VERBIND")
        if KundenNr:
            self.create_selection("ADRESSE", False)
   ## switch 'Zustand' from open (open) to payed (closed) if necessary
    def set_zustand(self):
        if self.get_value("Zustand") == "Open" and self.get_value("Zahlung") >= self.get_value("ZahlBetrag"):
            self.set_value("Zustand","Closed")
    ## one line to hold all relevant values of this invoice to be displayed 
    def line(self):
        betrag, zahlung, dummy = self.get_payment_values()
        zeile = self.get_string_value("RechNr").rjust(8) + " " + self.get_string_value("Datum") + " " + self.get_string_value("Bem") + " " 
        zeile += Afp_toString(betrag).rjust(10) + " " + Afp_toString(zahlung).rjust(10)
        return zeile 
    ## extract payment relevant data from SelectionList for 'Finance' modul, overwritten from AfpSelectionList
    # has to return the account number this payment has to be charged ("Gegenkonto")
    # @param paymentdata - payment data dictionary to be modified and returned
    def add_payment_data(self, paymentdata):
        paymentdata["Konto"] = self.get_value("Kreditor")
        if not paymentdata["Konto"]:
            paymentdata["Konto"]  = self.get_value("Kontierung")
        if not paymentdata["Konto"]:
            paymentdata["Konto"]  = Afp_getIndividualAccount(self.get_mysql(), self.get_value("KundenNr"))
        paymentdata["KtName"] = self.get_name(True)
        print("AfpObligation.add_payment_data:",paymentdata)
        return paymentdata
    ## routine to retrieve payment data from SelectionList \n
    # overwritten from AfpPaymentList
    def get_payment_values(self):
        preis, zahlung, datum = AfpPaymentList.get_payment_values(self)
        if self.get_value("Zustand") == "Static": zahlung = 0.0
        return preis, zahlung, datum
