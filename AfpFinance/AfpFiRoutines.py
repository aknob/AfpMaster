#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFinance.AfpFiRoutines
# AfpFiRoutines module provides classes and routines needed for finance handling and accounting,\n
# no display and user interaction in this modul.
#
#   History: \n
#        23 Dez. 2019 - move financial routines into selection list- Andreas.Knoblauch@afptech.de \n
#        27 Feb. 2019 - add SEPA direct debit handling - Andreas.Knoblauch@afptech.de \n
#        12 Nov. 2015 - add mysql-table define data - Andreas.Knoblauch@afptech.de \n
#        04 Feb. 2015 - add data export - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        14 Feb. 2014 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
#    Copyright© 1989 - 2021 afptech.de (Andreas Knoblauch)
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
from AfpBase.AfpSelectionLists import AfpSelectionList, AfpOrderedList
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpUtilities.AfpStringUtilities import Afp_getEndNumber
from AfpBase.AfpAusgabe import AfpAusgabe
from AfpBase.AfpBaseAdRoutines import AfpAdresse, AfpAdresse_getKNrFromSingleName
 
## interprete tags of a SEPA direct debit file and create the appropriate data
# @param globals - global values include mysql connection
# @param tags - list of tags [tag, name of tag, value, properties]
# @param datstring - string holding the accounting date of this sepa direct debit
# @param konto - accounting number of bank account
# @param gkonto - accounting number of purpose of payment
# @param beleg - number of receipt
# @param auszug - identifer of bank account receipt
# @param flavour - flavour of analyse-routine
def AfpFinance_SEPAddTagInterpreter(globals, tags, datstring, konto, transfer, gkonto, beleg, auszug,  flavour):
    return AfpFinance_SEPATagInterpreter(globals, tags, datstring, konto, transfer, gkonto, beleg, auszug,  flavour, False)
## interprete tags of a SEPA direct debit file and create the appropriate data
# @param globals - global values include mysql connection
# @param tags - list of tags [tag, name of tag, value, properties]
# @param datstring - string holding the accounting date of this sepa direct debit
# @param konto - accounting number of bank account
# @param gkonto - accounting number of purpose of payment
# @param beleg - number of receipt
# @param auszug - identifer of bank account receipt
# @param flavour - flavour of analyse-routine
def AfpFinance_SEPActTagInterpreter(globals, tags, datstring, konto, transfer, gkonto, beleg, auszug,  flavour):
    return AfpFinance_SEPATagInterpreter(globals, tags, datstring, konto, transfer, gkonto, beleg, auszug,  flavour, True)
## interprete tags of a SEPA direct debit file and create the appropriate data
# @param globals - global values include mysql connection
# @param tags - list of tags [tag, name of tag, value, properties]
# @param datstring - string holding the accounting date of this sepa direct debit
# @param konto - accounting number of bank account
# @param gkonto - accounting number of purpose of payment
# @param beleg - number of receipt
# @param auszug - identifer of bank account receipt
# @param flavour - flavour of analyse-routine
# @param credit - flag if interpreter is used for a creditor payment, default: False
def AfpFinance_SEPATagInterpreter(globals, tags, datstring, konto, transfer, gkonto, beleg, auszug,  flavour, credit = False):
    mysql = globals.get_mysql()
    #print "AfpFinance_SEPATagInterpreter:", datstring, konto, transfer, gkonto, auszug, flavour
    datum = Afp_fromString(datstring)
    data = AfpFinance(globals)
    is_transaction = False
    is_header = False
    accdata = {}
    sel = None
    sel_index = None
    name = None
    unidentified = []
    for tag in tags:
        #print "AfpFinance_SEPATagInterpreter tag:", tag
        typ = tag[0]
        if is_transaction:
            if typ == "InstdAmt":
                accdata["Betrag"] = Afp_fromString(tag[2])
            elif typ == "Nm":
                accdata = AfpFinance_specialXMLTag(mysql, flavour, typ, tag[2], accdata)
                #print "AfpFinance_SEPATagInterpreter add_direct_transaction Nm:", accdata
                name = tag[2]
            #elif typ == "DtOfSgntr":
            #    accdata["Datum"] = tag[2]
            elif typ == "Ustrd":
                accdata["Bem"] = tag[2]
            elif typ == "MndtId":
                if flavour == "Verein":
                    accdata = AfpFinance_specialXMLTag(mysql, flavour, typ, tag[2], accdata)
                    #print "AfpFinance_SEPATagInterpreter add_direct_transaction MndtId:", accdata
                else:
                    accdata["RechNr"] = tag[2]
            elif typ == "/DrctDbtTxInf" or typ == "/CdtTrfTxInf":
                is_transaction = False
                if accdata and "Datum" in accdata  and "Konto" in accdata and "Gegenkonto" in accdata  and "Betrag" in accdata:
                    #print "AfpFinance_SEPATagInterpreter add_direct_transaction <" + typ + ">:", accdata
                    data.add_direct_transaction(accdata)
                    if name and not "KundenNr" in accdata:
                        unidentified.append([data.get_value_length(), name])
                    name = None
        elif is_header:
            if typ  == "NbOfTxs":
                if credit:
                    accdata["Bem"] = "Sammelüberweisung ".decode("UTF-8") + Afp_toString(tag[2]) + " Positionen"
                else:
                    accdata["Bem"] = "SEPA-Einzug " + Afp_toString(tag[2]) + " Positionen"
            elif typ == "CtrlSum":   
                accdata["Betrag"] = tag[2] 
            elif typ == "/GrpHdr":
                is_header = False
                if accdata and "Datum" in accdata  and "Konto" in accdata and "Gegenkonto" in accdata  and "Betrag" in accdata:
                    #print "AfpFinance_SEPATagInterpreter add_direct_transaction /GrpHdr:", accdata
                    data.add_direct_transaction(accdata)
                    if name and not "KundenNr" in accdata:
                        unidentified.append([data.get_value_length(), name])
                    name = None
        else:
            if typ == "DrctDbtTxInf":
                is_transaction = True
                #accdata = {"Datum":datum, "BelegDatum":datum, "Konto": transfer, "Gegenkonto":gkonto, "Art":"Zahlung intern", "Beleg":beleg}
                accdata = {"Datum":datum, "BelegDatum":datum, "Konto": transfer, "Gegenkonto":gkonto, "Art":"Zahlung intern", "Beleg":beleg, "Reference":auszug}
                #print "AfpFinance_SEPATagInterpreter add_direct_transaction DrctDbtTxInf:", accdata
            elif typ == "CdtTrfTxInf":
                is_transaction = True
                accdata = {"Datum":datum, "BelegDatum":datum, "Konto": gkonto, "Gegenkonto":transfer, "Art":"Zahlung intern", "Beleg":beleg, "Reference":auszug}
            elif typ == "GrpHdr":
                is_header = True
                if credit:
                    accdata = {"Datum":datum, "BelegDatum":datum, "Konto": transfer, "Gegenkonto": konto, "Art":"Zahlung", "Beleg":beleg, "Reference":auszug}
                else:
                    accdata = {"Datum":datum, "BelegDatum":datum, "Konto": konto, "Gegenkonto": transfer, "Art":"Zahlung", "Beleg":beleg, "Reference":auszug}
    if unidentified: return[data, unidentified]
    else: return [data]

## routine for special handling of xml-tags for this flavour
# @param globals - global values include mysql connection
# @param KNr - address identifier
# @param tab - table name to be used
# @param tabnr - actuel used identifier in given tabe
# @param newtabnr - if given, identifier to which entrie should be changes, default: None; set mandat inaktiv
def AfpFinance_swapSEPAMandat(globals, KNr, tab, tabnr, newtabnr = None):
    #print "AfpFinance_swapSEPAMandat:", globals, KNr, tab, tabnr, newtabnr
    selection = AfpSQLTableSelection(globals.get_mysql(),  "ARCHIV", globals.is_debug())
    if newtabnr:
        criteria = "KundenNr = " + Afp_toString(KNr) + " AND Art = \"SEPA-DD\" AND Typ = \"Aktiv\" AND Tab = \"" + tab + "\"" 
    else:
        criteria = "KundenNr = " + Afp_toString(KNr) + " AND Art = \"SEPA-DD\" AND Typ = \"Aktiv\" AND Tab = \"" + tab + "\" AND TabNr = " + Afp_toString(tabnr)
    selection.load_data(criteria)
    chg = False
    for i in range(selection.get_data_length()):
        aktnr = selection.get_values("TabNr", i)[0][0]
        #print "AfpFinance_swapSEPAMandat tabnr:", aktnr,  tabnr, aktnr == tabnr, type(aktnr), type(tabnr)
        if selection.get_values("TabNr", i)[0][0] == tabnr:
            chg = True
            if newtabnr:
               selection.set_value("TabNr", newtabnr, i)
            else:
               selection.set_value("Typ", "Inaktiv", i)
    if chg: selection.store()
    #print "AfpFinance_swapSEPAMandat stored:", chg, KNr, tabnr, newtabnr
    return chg
## routine for special handling of xml-tags for this flavour
# @param mysql - link to databese
# @param typ - interpation type (p.e. flavour)
# @param value - value supplied with this tag
# @param value - value supplied with this tag
# @param accdata - dictionary to be completed
def AfpFinance_specialXMLTag(mysql, typ, tag, value, accdata):
    if typ == "Verein":
        if tag == "MndtId":
            rows = mysql.select("AnmeldNr,KundenNr,AgentNr,RechNr,Preis", "RechNr = " + Afp_toQuotedString(value), "Anmeld")
            row = None
            if len(rows) > 1:
                for r in rows:
                    if r[-1] and r[-1] > 0.0: 
                        row = r
                        break
            elif rows:
                row = rows[0]
            else:
                print "WARNING: AfpFinance_specialXMLTag Reference not found for", tag, value
            if row:
                if not "Reference" in accdata: accdata["Reference"] = row[3]
                accdata["Tab"] = "Anmeld"
                accdata["TabNr"] = row[0]
                if row[2]:
                    accdata["KundenNr"] = row[2]
                else:
                    accdata["KundenNr"] = row[1]
    if tag == "Nm":
        split = value.split(",")
        name = ""
        if len(split) > 1:
            name += split[1] .strip() + " "
        name += split[0].strip()
        KNr = AfpAdresse_getKNrFromSingleName(mysql, name)
        if KNr:
             accdata["KundenNr"] = KNr
        #print "AfpFinance_specialXMLTag:", tag, value, KNr
    return accdata
    
## set period from input data
# @param period - input value for period, may be None
# @param globals - global values to handle period creation
# @param datum - if given reference date
# @param mandant - if given identifier of active mandant
# @param inter - if given number of intervals per year
def AfpFinance_setPeriod(period, globals, datum=None, mandant=None,  inter=None):
    if not period is None: 
        period = Afp_toString(period)
    actuel = 1
    interval = inter
    if not datum: 
        datum = globals.today()
    if not interval:
        interval = globals.get_value("transaction-period-interval","Finance")
    if not period:
        period = globals.get_string_value("actuel-transaction-period","Finance")
    if not period:
        period = Afp_toString(datum.year) 
        if interval and interval > 1:
            month = datum.month
            if interval == 12:
                period += "/" + Afp_toIntString(month, 2)
                actuel = month
            else:
                if interval == 2:
                    period += "/H" 
                elif interval == 3:
                    period += "/T" 
                elif interval == 4:
                    period += "/Q" 
                else:
                    period += "/" +  Afp_toString(interval) + "X"
                actuel = interval*(month-1)/12 + 1
                period += Afp_toString(actuel)
    if not mandant:
         mandant = globals.get_value("actuel-transaction-mandator", "Finance")
    if period and mandant and globals.get_value("multiple-transaction-mandats", "Finance"):
        if not "-" in period:
            period = Afp_toString(mandant) + "-" + period
    return period
## generate next period from input period string
# @param period - input value for period, may be None
def AfpFinance_nextPeriod(period):
    next = None
    man = None
    if "-" in period:
        split = period.split("-")
        man = split[0]
        peri = Afp_fromString(split[1])
    else:
        peri = Afp_fromString(period)
    #print "AfpFinance_nextPeriod isInteger:", Afp_isInteger(peri)
    if Afp_isInteger(peri):
        next = Afp_toString(peri + 1)
    else:
        max = None
        if "Q" in period:
            max = 4
        elif "H" in period:
            max = 2
        elif "T" in period:
            max = 3
        elif "X" in period:
            max = Afp_fromString(Afp_between(period,"/","X")[0][0])
            #print "AfpFinance_nextPeriod max:", max, type(max)
        nr = Afp_getEndNumber(period)
        lgh = len(period) - len(str(nr))
        if max and nr+1 > max:
            start = Afp_getEndNumber(period, True)
            lg = len(str(start))
            nr = 1
            next = Afp_toString(start + 1) + period[lg:lgh] + Afp_toString(nr)
        else:
           next = period[:lgh] + Afp_toString(nr + 1)
    if man:
        next = man + "-" + next
    return next

## class to generate SEPA creditor transfer xml- or receiptfile
class AfpSEPAct(AfpSelectionList):
    ## initialize class
    # @param globals - global data to e used
    # @param mandator -  if given, identifier of mandator the transfer should be generated for
    # @param filename - name of xml-file in sourcedir to be used for output
    # @param debug - flag for debug information
    def  __init__(self, globals, mandator = None, filename = None, debug = None):
        AfpSelectionList.__init__(self, globals, "SEPA-CT", globals.is_debug())
        if not debug is None: 
            self.debug = debug
        if not mandator:
            self.mandator = globals.get_value("actuel-transaction-mandator", "Finance")
            if not self.mandator: self.mandator = 1
        else:
            self.mandator = mandator
        if filename:
            self.sourcefile = filename
        else:
            self.sourcefile = "SEPA_credit_transfer.xml"
        self.sourcedir = globals.get_value("templatedir")
        self.targetdir = globals.get_value("archivdir")
        self.output_file = None
        self.serial = 1
        self.sum = 0.0
        self.today = self.globals.today()
        self.period = Afp_toString(self.today.year)
        self.debit_IBAN = None
        self.debit_BIC = None
        self.transactions = []
        self.transaction_IBAN = []
        self.transaction_BIC = []

        self.selects["ADRESSE"] = ["ADRESSE",   "KundenNr = " + Afp_toString(self.mandator)]
        self.selects["ARCHIV"] = ["ARCHIV",   "KundenNr = " + Afp_toString(self.mandator)]
        self.selects["Konto"] = ["ADRESATT",   "Attribut = \"Bankverbindung\" AND KundenNr = " + Afp_toString(self.mandator)]
        if self.debug: print "AfpSEPAct Konstruktor:", self.mandator
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpSEPAct Destruktor" 
        
    ## get possible bank accounts for SEPA Creditor Transfer
    def get_bankaccounts(self):
        acc = []
        lgh = self.get_value_length("Konto")
        debit = self.get_value_rows("Konto","Tag")
        for de in debit:
            acc.append(de[0])
        if len(acc) == 1:
            split = acc[0].split(",")
            self.set_debit_data(split[0], split[1])
            return []
        return acc
    ## generate sum
    def get_sum(self):
        sum = 0.0
        for trans in self.transactions:
            sum += trans.get_value("Betrag")
        return sum
    ## set SEPA Creditor Transfer bankaccount debitor data
    # @param iban - IBAN of debit account
    # @param bic - BIC of debit account
    def set_debit_data(self, iban, bic):
        self.debit_IBAN = iban
        self.debit_BIC = bic
    ## add transfer data to current creditor transfer
    # @param KNr - address isdentifier
    # @param iban - iban number for transaction
    # @param bic - bic number for transaction
    # @param betrag - amount of transaction
    # @param bem - if given, description oftransfer
    # @param tab - if given, incident table
    # @param tab nr- if given, incident number
    def set_transfer_data(self, index, KNr, iban, bic, betrag, bem=None, tab=None, tabnr=None):
        if not KNr or not iban or not betrag: return
        accdata = {"KundenNr": KNr, "Betrag": betrag, "Art": "Zahlung"}
        if bem:
            accdata["Bem"] = bem
        if tab and tabnr:
            accdata["Tab"] = tab
            accdata["TabNr"] = tabnr
        if index is None or index  < 0 or index > len(self.transactions):
            self.transaction_IBAN.append(iban.replace(" ",""))
            self.transaction_BIC.append(bic)
            trans = AfpFinanceTransactions(self.globals)
            trans.add_direct_transaction(accdata)
            self.transactions.append(trans)
        else:
            self.transaction_IBAN[index] = iban.replace(" ","")
            self.transaction_BIC[index] = bic
            self.transactions[index].set_data_values(accdata)
    ## add transfer data to current creditor transfer
    # @param KNr - address isdentifier
    # @param iban - iban number for transaction
    # @param bic - bic number for transaction
    # @param betrag - amount of transaction
    # @param bem - if given, description oftransfer
    # @param tab - if given, incident table
    # @param tab nr- if given, incident number
    def add_transfer_data(self, KNr, iban, bic, betrag, bem=None, tab=None, tabnr=None):
        if not KNr or not iban or not betrag: return
        accdata = {"KundenNr": KNr, "Betrag": betrag, "Art": "Zahlung"}
        if bem:
            accdata["Bem"] = bem
        if tab and tabnr:
            accdata["Tab"] = tab
            accdata["TabNr"] = tabnr
        self.transaction_IBAN.append(iban.replace(" ",""))
        self.transaction_BIC.append(bic)
        trans = AfpFinanceSingleTransaction(self.globals)
        trans.add_direct_transaction(accdata)
        self.transactions.append(trans)
        self.sum += betrag
    ## delete transfer data row
    # @param index - index of row to be deleted
    def delete_transfer_data(self, index):
        #lgh = self.transactions.get_value_length()
        #if  index < lgh and lgh == len(self.transaction_IBAN) and lgh == len(self.transaction_BIC):
            #self.tansactions.delete_row(None, index)
        betrag = self.transactions[index].get_value("Betrag")
        self.transactions.pop(index)
        self.transaction_IBAN.pop(index)
        self.transaction_BIC.pop(index)
        self.sum -= betrag
    ## get transaction data
    # @param fileds - names of fields to be retrieved
    def get_transaction_data(self, fields):
        rows = []
        for trans in self.transactions:
            row = trans.get_values(fields)
            rows.append(row[0])
        return rows
    ## get single transaction row to poulate dialog
    #@param index - index of transaction to be retri8eved
    def get_transaction_row(self, index=0):
        if self.transactions:
            trans = self.transactions[index]
            row = trans.get_values("KundenNr,Betrag,Bem")
            row[0].append(self.transaction_IBAN[index])
            row[0].append(self.transaction_BIC[index])
            return row[0]
        return None
    ## get transaction rows to poulate grid
    def get_transaction_rows(self):
        raws = self.get_transaction_data("KundenNr.BUCHUNG,Betrag.BUCHUNG,Bem.BUCHUNG")
        #print "AfpSEPAct.get_transaction_rows:", raws
        rows = []
        for i in range(len(raws)):
            adresse = AfpAdresse(self.get_globals(), raws[i][0])
            row = [adresse.get_name(True), self.transaction_BIC[i], self.transaction_IBAN[i], Afp_toFloatString(raws[i][1]), raws[i][2]]
            rows.append(row)
        return rows
    ## generate SEPA Creditor Transfer XML-file from data
    def gen_SEPA_xml(self):
        exe_date = Afp_addDaysToDate(self.today, 1)
        sum = self.get_sum()
        datalist = self.transactions
        vars = {"DbBIC": self.debit_BIC, "DbIBAN": self.debit_IBAN}
        vars["One"] = 1
        vars["Serial"] = 0
        vars["Name"] = self.get_name()
        vars["Total"] = sum
        vars["Count"] = len(self.transactions)
        vars["Period"] = Afp_toString(self.period)
        vars["Timestamp"] = Afp_getNow(True)
        vars["Execute"] = Afp_toInternDateString(exe_date)
        vars["MessageId"] = "SEPA-CT-" + self.debit_BIC + Afp_toDateString(self.today,"yymmdd") + Afp_toIntString(self.serial)
        target = self.targetdir  + vars["MessageId"] + ".xml"
        while Afp_existsFile(target):
            self.serial += 1
            vars["MessageId"] = "SEPA-CT-" + self.debit_BIC + Afp_toDateString(self.today,"yymmdd") + Afp_toIntString(self.serial)
            target = self.targetdir  + vars["MessageId"] + ".xml"
        vars["PaymentId"] = vars["MessageId"] [8:]+ "00"
        vars["TransId"] = Afp_intString(Afp_toDateString(self.today,"yymmdd") + Afp_toIntString(self.serial) + "00")
        # write xml file
        serial_tags = ["<CdtTrfTxInf>", "</CdtTrfTxInf>", 1]
        source = self.sourcedir  + self.sourcefile
        dvars = []
        for iban,bic in zip(self.transaction_IBAN,self.transaction_BIC):
            var = {"IBAN": iban, "BIC": bic}
            dvars.append(var)
        for data in datalist: 
            data.set_international_output(True)
        if self.debug: print "AfpSEPAct.gen_SEPA_xml:", self.serial, vars, dvars, source, target
        out = AfpAusgabe(self.debug, datalist, serial_tags)
        out.set_variables(vars)
        out.set_datas_variables(dvars)
        out.inflate(source)
        out.write_resultfile(target)
        # write receipt file
        serial_tags = ["<table:table-row>", "</table:table-row>", 1, 1]
        source = source[:-4] + ".fodt"
        target = self.targetdir  + vars["MessageId"] + ".odt"
        for data in datalist: data.set_international_output(False)
        if self.debug: print "AfpSEPAct.gen_SEPA_xml Receipt:", self.serial, vars["Typ"], source, target
        rcpt = AfpAusgabe(self.debug, datalist, serial_tags)
        rcpt.set_variables(vars)
        rcpt.set_datas_variables(dvars)
        rcpt.inflate(source)
        rcpt.write_resultfile(target, self.sourcedir + "empty.odt")
        return vars["MessageId"]
    
    ## generate SEPA Creditor Transfer xml file
    def execute_xml(self):
        self.output_file = self.gen_SEPA_xml()
        self.add_all_archives(self.output_file)
    
    ## get filepathes to created SEPA xml-files
    def get_filepathes(self):
        return self.targetdir + self.output_file + ".xml"

    ## set identification data for archive \n
    # do nothing - overwritten from AfpSelectionList
    # @param data - dictionary where identifiers should be added
    def set_archiv_table(self, data):
        return data
    ## add archiv data
    # @param filename - name of file created (without extension)
    def add_all_archives(self, filename):
        bem = Afp_toString(len(self.transactions)) + " Pos. " + Afp_toString(self.get_sum())
        art = "Sammelüberweisung".decode("UTF-8")
        typ = Afp_toString(self.period)
        master_data = {"KundenNr": Afp_toString(self.mandator), "Art": art, "Typ": typ, "Gruppe": "XML-Datei", "Bem": bem}
        client_data = {"KundenNr": Afp_toString(self.mandator), "Art": art, "Typ": typ, "Gruppe": "Beleg", "Bem": bem}
        if filename:
            master_data["Extern"] = filename + ".xml"
            client_data["Extern"] = filename+ ".odt"
            self.add_to_Archiv(master_data)
            self.add_to_Archiv(dict(client_data))
            client_data.pop("KundenNr")
            used_KNr = []
            for trans in self.transactions:
                #print "AfpSEPAct.add_all_archives KNr:", trans.get_value("KundenNr"), used_KNr
                if trans.get_value("KundenNr") in used_KNr: continue
                trans.add_to_Archiv(dict(client_data))
                trans.get_selection("ARCHIV").store()
                used_KNr.append(trans.get_value("KundenNr"))

## class to handle SEPA direct debit handling, 
class AfpSEPAdd(AfpSelectionList):
    ## initialize class
    # @param data - SelectionList data where sepa direct debit is handled for
    # @param fields - dictionary with field names to be used to extract debits from clients
    # - "regular" - field for regular payment per year
    # - "extra" - field for extra payment for this year in first draw
    # - "total" - field where total payment for this year  is hold
    # - "actuel" - field where the actuel payment amount is written to, may be a temporary field (._tmp)    
    # @param filename - name of xml-file in sourcedir to be used for output
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved duringl initialisation
    def  __init__(self, data, fields = None, filename = None, debug = False, complete = False):
        self.globals = data.get_globals()
        AfpSelectionList.__init__(self, self.globals, "SEPA-DD", debug)
        self.data = data
        self.ctable = data.get_client().get_mainselection()
        if fields:
            self.datafields = fields
        else:
            self.datafields = {"regular":"ProvPreis", "extra":"Extra", "total":"Preis", "actuel":"Actuel._tmp"}
        if filename:
            self.sourcefile = filename
        else:
            self.sourcefile = "SEPA_direct_debit.xml"
        self.debug = debug
        self.sourcedir = self.globals.get_value("templatedir")
        self.targetdir = self.globals.get_value("archivdir")
        self.serial = 1
        self.today = self.globals.today()
        self.period = Afp_toString(self.today.year)
        self.interval = 1   # - number of runs per year, default: once a year, possible values 1, 2, 3, 4, 6, 12
        self.actuel = 1     # - actuel number of current run in year
        self.creditor_Id= None
        self.creditor_IBAN = None
        self.creditor_BIC = None
        self.lastrun = None
        self.clients = None
        self.clients_file= None
        self.temp = None
        self.newclients = None
        self.newclients_file= None
        self.newtemp = None
        self.mainselection = data.get_mainselection()
        self.mainindex = data.get_mainindex()
        self.mainvalue = data.get_value()
        self.selections[self.mainselection] = data.get_selection()
        self.selections["ADRESSE"] = data.get_selection("ADRESSE")
        self.selects["Kreditor"] = [ "ADRESATT","Attribut = \"SEPA Kreditor ID\" AND KundenNr = " + data.get_string_value("KundenNr.ADRESSE")] 
        self.selects["Konto"] = [ "ADRESATT","Attribut = \"Bankverbindung\" AND KundenNr = " + data.get_string_value("KundenNr.ADRESSE") + " AND (AttText = \"SEPA\" OR AttText = \"SEPA-DD\")"] 
        self.selects["Mandat"] = [ "ARCHIV","Art = \"SEPA-DD\" AND Typ = \"Aktiv\" AND Tab = \"" + self.ctable + "\""] 
        self.selects["Execution"] = [ "ARCHIV","Art = \"SEPA-DD\" AND Typ = \"Datei\" AND Tab = \"" + self.mainselection + "\""] 
        if self.debug: print "AfpSEPAdd Konstruktor:", self.mainindex, self.mainvalue 
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpSEPAdd Destruktor"
        
    ## set period from interval input
    def set_period(self):
        self.period = AfpFinance_setPeriod(None, self.globals, self.today, None, self.interval)
        self.actuel = Afp_getEndNumber(self.period)
        print "AfpSEPAdd.set_period:", self.interval, self.actuel, self.period
        
    ## look if this SEPA Direct Debit is the first run in the year
    def is_first_in_year(self):
        if self.lastrun and self.lastrun.year == self.today.year:
            return False
        else:
            return True
        
    ## check if SEPA Direct Debit creditor data is availabe, if not try to load it
    def creditor_data_available(self):
        if not (self.creditor_Id and self.creditor_IBAN and self.creditor_BIC):
            self.read_creditor_data()
        if self.creditor_Id and self.creditor_IBAN and self.creditor_BIC:
            return True
        else:
            return False
    ## set SEPA Direct Debit creditor data
    # @param iban - IBAN of creditor account
    # @param bic - BIC of creditor account
    # @param interval - number of runs during a year for this SEPA direct debit account
    def set_creditor_data(self, iban, bic, interval):
        if iban:
            self.creditor_IBAN = iban.replace(" ","")
        if bic:
            self.creditor_BIC = bic
        if interval:
            self.interval = interval
            self.set_period()
        Tag = self.creditor_IBAN + "," + self.creditor_BIC
        if self.interval > 1: Tag += "," + Afp_toString(self.interval)
        self.set_value("Tag.Konto", Tag)
    ## get SEPA Direct Debit creditor data
    def read_creditor_data(self):
        self.creditor_Id = self.get_value("AttText.Kreditor")
        bank = self.get_value("Tag.Konto")
        if bank: 
            split = bank.split(",") 
            if len(split) > 1:
                self.creditor_IBAN = split[0].replace(" ","")
                self.creditor_BIC = split[1].strip()
                if len(split) > 2:
                    self.interval = Afp_fromString(split[2].strip())
                    self.set_period()
 
    ## get date of last SEPA Direct Debit run 
    def read_last_run(self):    
        rows = self.get_values("Datum.Execution")
        datum = None
        #print "AfpSEPAdd.read_last_run:", rows
        for row in rows:
            if datum is None: datum = row[0]
            elif row[0] > datum: datum = row[0]
        self.lastrun = datum 
        
    ## get SEPA Direct Debit mandates or files from designated table
    def gen_mandat_data(self):
        where = self.data.selects[self.ctable][1]
        split = where.split("=")
        clientid = split[0].strip()
        masterid = split[1].split(".")[0].strip()
        EvNr = self.get_value(masterid)
        selection = self.get_selection("Mandat")
        rows = selection.get_values("KundenNr,Datum,TabNr,Gruppe,Bem")
        self.temp = []
        self.newtemp = []
        self.clients = []
        self.newclients = []
        self.client_bic = {}
        self.client_iban = {}
        self.sum = 0
        self.newsum = 0
        for row in rows:
            client = self.data.get_client(row[2])
            payed = client.get_value("Zahlung") 
            if payed is None: payed = 0.0
            if client.get_value(clientid) == EvNr and payed < client.get_value(self.datafields["total"]):
                self.client_bic[row[0]] = row[3]
                self.client_iban[row[0]] = row[4]
                #print "AfpSEPAdd.gen_mandat_data amount:", row[2], row[3], row[4], client.get_value(self.datafields["regular"]), self.interval, self.datafields["regular"]
                value = client.get_value(self.datafields["regular"])
                if not value: 
                    value = 0.0
                    print "AfpSEPAdd.gen_mandat_data ProvPreis not set for:", row[2], client.get_name()
                amount = value/self.interval
                first = not (self.lastrun and row[1] <=  self.lastrun)
                #print "AfpSEPAdd.gen_mandat_data lastrun:", row[2], self.lastrun, row[1], first
                #print "AfpSEPAdd.gen_mandat_data interval:", row[2], amount, first,self.is_first_in_year(), self.interval, self.actuel
                if first or self.is_first_in_year():
                    extra = client.get_value(self.datafields["extra"])
                    if first:
                        preis = client.get_value(self.datafields["total"])
                        preis = preis - (self.interval - self.actuel)*amount
                        if preis: amount = preis
                        else: amount += extra
                    else:
                        amount += extra                        
                #print "AfpSEPAdd.gen_mandat_data amount:", row[2], amount
                client.set_value(self.datafields["actuel"], amount)
                if first:
                    self.newclients.append(client)
                    self.newsum += amount
                else:
                    self.clients.append(client)
                    self.sum += amount

    ## add SEPA Direct Debit mandate 
    # @param client - client object to be added
    # @param fname - name of scan of mandat
    # @param datum - date when mandat has been signed
    # @param bic - BIC of client account for which mandat has been signed
    # @param iban - IBAN of client account for which mandat has been signed
    def add_mandat_data(self, client, fname, datum, bic, iban):
        if Afp_existsFile(fname) and client and datum and bic and iban:
            ext = fname.split(".")[-1]
            max = 1
            fpath = None
            while not fpath:
                if max < 10:  null = "0"
                else:  null = ""
                fresult = "SEPA" + "_" + client.get_listname() + "_" + client.get_string_value() + "_" + null + str(max) + "." + ext 
                fpath = Afp_addRootpath(client.get_globals().get_value("archivdir"), fresult)
                if Afp_existsFile(fpath):
                    max+= 1
                    fpath = None
            if self.debug: print "AfpSEPAdd.add_mandat_data copy file:", fname, "to",  fpath
            Afp_copyFile(fname, fpath)
            added = {}
            added["Art"] = "SEPA-DD"
            added["Typ"] = "Aktiv"
            added["Datum"] = datum
            added["Gruppe"] = bic
            added["Bem"] = iban
            added["Extern"] = fresult
            if client.get_value("AgentNr"):
                added["KundenNr"] = client.get_value("AgentNr")
            added = client.set_archiv_data(added)
            row = self.get_selection("Mandat").get_data_length()
            #print "AfpSEPAdd.add_mandat_data set mandat:", added, row
            self.get_selection("Mandat").set_data_values(added, row)
            if not self.newclients: self.newclients = [client]
            else: self.newclients.append(client)
        else:
            print "WARNING: SEPA mandat not all data supplied:", fname, datum, bic, iban
       
    ## generate SEPA Direct Debit XML-file from data
    # @param firstflag - if given, flag if this is the first time a SEPA Driect Debit is invoked for all data (please separate first and follow-up actions)
    def gen_SEPA_xml(self, firstflag = False):
        today = self.globals.today()
        if firstflag:
            exe_date = Afp_addDaysToDate(today, 8)
            first = "True"
            typ = "Erstlastschrift"
            datalist = self.newclients
            sum = self.newsum
        else:
            exe_date = Afp_addDaysToDate(today, 5)
            first = ""
            typ = "Folgelastschrift"
            datalist = self.clients
            sum = self.sum
        vars = {"BIC": self.creditor_BIC, "IBAN": self.creditor_IBAN}
        vars["One"] = 1
        vars["Serial"] = 0
        vars["Name"] = self.data.get_name()
        vars["ID"] = self.creditor_Id
        vars["Total"] = sum
        vars["First"] = first
        vars["Count"] = len(datalist)
        vars["Period"] = Afp_toString(self.period)
        vars["Timestamp"] = Afp_getNow(True)
        vars["Execute"] = Afp_toInternDateString(exe_date)
        vars["MessageId"] = "SEPA-" + self.creditor_BIC + Afp_toDateString(today,"yymmdd") + Afp_toIntString(self.serial)
        target = self.targetdir  + vars["MessageId"] + ".xml"
        while Afp_existsFile(target):
            self.serial += 1
            vars["MessageId"] = "SEPA-" + self.creditor_BIC + Afp_toDateString(today,"yymmdd") + Afp_toIntString(self.serial)
            target = self.targetdir  + vars["MessageId"] + ".xml"
        vars["PaymentId"] = vars["MessageId"] [5:]+ "00"
        vars["TransId"] = Afp_intString(Afp_toDateString(today,"yymmdd") + Afp_toIntString(self.serial) + "00")
        # write xml file
        serial_tags = ["<DrctDbtTxInf>", "</DrctDbtTxInf>", 1]
        source = self.sourcedir  + self.sourcefile
        for data in datalist: data.set_international_output()
        if self.debug: print "AfpSEPAdd.gen_SEPA_xml:", self.serial, vars, source, target
        out = AfpAusgabe(self.debug, datalist, serial_tags)
        out.set_variables(vars)
        out.inflate(source)
        out.write_resultfile(target)
        # write receipt file
        serial_tags = ["<table:table-row>", "</table:table-row>", 1, 1]
        vars["Typ"] = typ
        source = source[:-4] + ".fodt"
        target = self.targetdir  + vars["MessageId"] + ".odt"
        for data in datalist: data.set_international_output(False)
        if self.debug: print "AfpSEPAdd.gen_SEPA_xml Receipt:", self.serial, vars["Typ"], source, target
        rcpt = AfpAusgabe(self.debug, datalist, serial_tags)
        rcpt.set_variables(vars)
        rcpt.inflate(source)
        rcpt.write_resultfile(target, self.sourcedir + "empty.odt")
        return vars["MessageId"]
        
    ## generate one client for outside use
    # @param KNr - address idetifier for generated client
    def gen_client(self, KNr):
        return self.data.get_client(KNr)
    ## get all non-SEPA clients for outside use
    def get_possible_clients(self):
        possible = []
        clients = self.data.get_clients()
        for client in clients:
            if client.get_value(self.datafields["total"]):
                rows = client.get_selection("ARCHIV").get_values("Art,Typ")
                add = True
                for row in rows:
                    if row[0].strip() == "SEPA-DD" and row[1].strip() == "Aktiv": add = False
                if add: possible.append(client)
        return possible
    ## get SEPA client sums for outside use
    def get_sums(self):
        return self.sum, self.newsum
    ## get SEPA clients for outside use
    def get_clients(self):
        return self.clients, self.newclients
    ## get BIC of client mandat
    # @param KNr - address identifier for this mandat
    def get_client_BIC(self, KNr):
        bic = None
        if self.client_bic and KNr in self.client_bic:
            bic = self.client_bic[KNr]
        return bic
    ## get IBAN of client mandat
    # @param KNr - address identifier for this mandat
    def get_client_IBAN(self, KNr):
        iban = None
        if self.client_iban and KNr in self.client_iban:
            iban = self.client_iban[KNr]
        return iban
    ## get filednames of client for different uses
    # @param typ - identifier which fieldname should be extracted, possible typs:
    # - "regular" - field for regular payment per year
    # - "extra" - field for extra payment for this year in first draw
    # - "total" - field where total payment for this year  is hold
    # - "actuel" - field where the payment amount is written to
    def get_client_fieldname(self, typ):
        if typ in self.datafields:
            return self.datafields[typ]
        else:
            return ""
     ## set clients after outside manipulation
    # @param clients - list of client data to be written to clients
    # @param newclients - list of client data to be written to newclients
    def set_clients(self, clients, newclients):
        self.newclients = newclients
        self.newsum = 0
        for client in newclients:
            self.newsum += client.get_value(self.datafields["actuel"])
        self.clients = clients
        self.sum = 0
        for client in clients:
            self.sum += client.get_value(self.datafields["actuel"])
        
    ## reset clients to stored values before changing data
    def reset_clients(self):
        if self.newclients:
            for i in range(len(self.newclients)):
                self.newclients[i].reset_selects()
        if self.clients:
            for i in range(len(self.clients)):
                self.clients[i].reset_selects()
          
    ## add archiv data
    def add_to_archiv(self):
        master_data = {"Typ": Afp_toString(self.period), "Gruppe": "XML-Datei"}
        client_data = {"Typ": Afp_toString(self.period), "Gruppe": "Beleg"}
        if self.newclients_file:
            bem = Afp_toString(len(self.newclients)) + " Pos. " + Afp_toString(self.newsum)
            master_data["Art"] = "Lastschrift Erst"
            client_data["Art"] = "Lastschrift Erst"
            master_data["Bem"] = bem
            client_data["Bem"] = bem            
            master_data["Extern"] = self.newclients_file + ".xml"
            client_data["Extern"] = self.newclients_file + ".odt"
            self.data.add_to_Archiv(master_data)
            self.data.add_to_Archiv(dict(client_data))
            for client in self.newclients:
                # possibly add name of member, as sepa may be paid from other address
                client.add_to_Archiv(dict(client_data))
        if self.clients_file:
            bem = Afp_toString(len(self.clients)) + " Pos. " + Afp_toString(self.sum)
            master_data["Art"] = "Lastschrift Folge"
            client_data["Art"] = "Lastschrift Folge"            
            master_data["Bem"] = bem
            client_data["Bem"] = bem            
            master_data["Extern"] = self.clients_file + ".xml"
            client_data["Extern"] = self.clients_file + ".odt"
            self.data.add_to_Archiv(master_data)
            self.data.add_to_Archiv(dict(client_data))
            for client in self.clients:
                client.add_to_Archiv(dict(client_data))
                
    ## create SEPA Direct Debit data
    def prepare_xml(self):
        if self.creditor_data_available():
            self.read_last_run()
            self.gen_mandat_data()
            if self.debug: print "AfpSEPAdd.prepare_xml:", self.newclients, self.clients
            return True
        else:
            return False
            
    ## generate SEPA Direct Debit xml file
    def execute_xml(self):
        #newamount = []
        if self.newclients:
            #for client in self.newclients:
            #    newamount.append(client.get_paymentvalues()[0])
            self.newclients_file = self.gen_SEPA_xml(True)
        if self.clients:
            self.clients_file = self.gen_SEPA_xml()
        self.reset_clients()
        self.add_to_archiv()
            
    ## generate SEPA Direct Debit for designated data
    def generate_xml(self):
        if self.prepare_xml():
            self.execute_xml()
            
    ## get filepathes to created SEPA xml-files
    def get_filepathes(self):
        #print "AfpSEPAdd.get_filepathes:", self.targetdir, self.clients_file, self.newclients_file 
        pathes = ""
        if self.newclients_file:
            pathes += self.targetdir + self.newclients_file + ".xml "
        if self.clients_file:
            pathes += self.targetdir + self.clients_file + ".xml"
        return pathes
            
    ## store all data
    def store(self):
        if self.has_changed():
            super(AfpSEPAdd, self).store()
        self.data.store()
        if self.newclients:
            for client in self.newclients:
                client.store()
        if self.clients:
            for client in self.clients:
                client.store()
    
## return financial transaction class, if possible
def AfpFi_getFinanceTransactions(globals):
    #print "AfpFi_getFinanceTransactions:", globals.get_mysql().get_tables()
    if "BUCHUNG" in globals.get_mysql().get_tables():
        return AfpFinanceTransactions(globals)
    else:
        return None
## class to sample all financial transaction entries needed for one action. \n
# central class for financial transactions of all kinds. \n
# this centralisation is considered to be more usefull then following the object oriented approach.
class AfpFinanceTransactions(AfpSelectionList):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param value - if given, identifier for which this list is created, default: None - a new, clean object is created
    # @param mainindex - main sort index for list, default: "BuchungsNr"
    # @param period - if given, financial period, default: None - will be set automatically
    # @param skip - flag if atumated creation should be skipped, default: False
    def  __init__(self, globals, value = None, mainindex="BuchungsNr", period = None, skip = False):
        AfpSelectionList.__init__(self, globals, "BUCHUNG", globals.is_debug())
        #print "AfpFinanceTransactions Konstruktor:", value, mainindex, period
        self.mainfilter = None
        self.set_period(period)
        self.transfer = None
        self.spread_key = True
        self.fixed_auszug = False
        if value:  
        # load financial accounting data from database
            self.new = False
            self.mainvalue = Afp_toQuotedString(value)
        else:
       # just empty object to hold financial accounting data
            self.new = True
            self.mainvalue = ""
        self.mainindex = mainindex
        self.mainselection = "BUCHUNG"
        #print "AfpFinanceTransactions select entriy:", self.mainindex, self.mainselection, self.mainfilter, self.mainvalue, self.mainselection in self.selections
        self.set_main_selects_entry()
        if not skip and not self.mainselection in self.selections:
            self.create_selection(self.mainselection)
        self.selects["AUSZUG"] = [ "AUSZUG","Period = \"" + self.period + "\""] 
        if self.debug: print "AfpFinanceTransactions Konstruktor:", self.mainindex, self.mainvalue 
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpFinanceTransactions Destruktor"

    ## set period marker for financial transactions
    # @param period - if given, period marker to be set, defaut: period is set to current year \n
    #                            or global variable 'actuel-transaction-period' for 'Finance' modul
    def set_period(self, period = None):
        self.period = AfpFinance_setPeriod(period, self.globals)
    ## set the customised select_clause for the main selection
    # overwritten from SelectionList to set period
    def set_main_selects_entry(self):  
        selname = "BUCHUNG"
        self.mainselection= selname
        #print "AfpFinanceTransactions.set_main_selects_entry:",  self.mainindex, self.mainvalue , self.period, self.mainfilter
        if self.mainfilter:
            self.selects[selname] = [selname, self.mainfilter, "BuchungsNr"]
        elif self.mainindex and self.mainvalue:         
            self.selects[selname] = [selname, self.mainindex + " = " + self.mainvalue  + " AND Period = \"" + self.period + "\"", "BuchungsNr"]
        else:
            self.selects[selname] = [selname, "Period = \"" + self.period + "\"", "BuchungsNr"]
        
    ## check if identifier of statement of this account (Auszug) exists, if yes load it
    # @param auszug - identifier of statement of account
    def check_auszug(self, auszug):
        auszug, period = self.extract_period(auszug)
        if auszug == self.get_value("Auszug.AUSZUG") and period == self.period: return True
        if not self.fixed_auszug:
            self.delete_selection("AUSZUG")
            self.selects["AUSZUG"][1] = "Auszug = \"" + auszug + "\"AND Period = \"" + period + "\""
            self.period = period
            if auszug == self.get_value("Auszug.AUSZUG"): return True
        return False
    ## set identifier of statement of account (Auszug)
    # @param auszug - identifier of statement of account (xxnnn - xx identifier of bankaccount, nnn number)
    # @param datum, - if given, date of statement of account 
    # @param saldo, - if given, startsaldo of statement of account 
    # @param fixed, - if given, flag if statement is only set once and never changed again, default: False 
    def set_auszug(self, auszug, datum = None, saldo = None, fixed = False):  
        today = self.globals.today()
        if datum is None: datum = today
        if self.check_auszug(auszug) or self.fixed_auszug: return
        #print "AfpFinanceTransactions.set_auszug needed:", auszug        
        auszug, period = self.extract_period(auszug)
        ausname = Afp_getStartLetters(auszug) 
        if not ausname: return
        self.selects["Auszugkonto"] =  [ "KTNR","KtName = \"" + ausname.upper() + "\""] 
        self.create_selection("Auszugkonto", False)
        ktnr = self.get_value("KtNr.Auszugkonto")
        if ktnr is None: 
            print "WARNING: AfpFinance Account not found for", auszug
            return
        if not saldo:
            self.selects["Auszugs"] =  [ "AUSZUG","KtNr = " +  Afp_toString(ktnr) +" AND Period = \"" + period + "\"" ] 
            self.create_selection("Auszugs", False)
            if self.get_selection("Auszugs").get_data_length():
                lgh = len(ausname)
                ausnr = Afp_intString(auszug[lgh:].strip())
                vals = self.get_selection("Auszugs").get_values("Auszug,EndSaldo")
                for row in vals:
                    nr = Afp_intString(row[0][lgh:].strip())
                    if nr == ausnr - 1 and not row[1] is None:
                        saldo = row[1]
                        break
        self.set_value("Auszug.AUSZUG", auszug)
        if datum: self.set_value("BuchDat.AUSZUG", datum) 
        if saldo: 
            self.set_value("StartSaldo.AUSZUG", saldo)
            self.set_value("EndSaldo.AUSZUG", saldo)
        if ktnr: self.set_value("KtNr.AUSZUG", ktnr)
        self.set_value("Datum.AUSZUG", today)
        self.set_value("Period.AUSZUG", period)
        self.get_selection("AUSZUG").store()
        self.period = period
        #print "AfpFinanceTransactions.set_auszug:", self.period
        self.fixed_auszug = fixed
    ## extract period from statement of account input
    # @param auszug - string holding information of statement
    def extract_period(self, auszug):
        period = None
        if "/" in auszug:
            split = auszug.split("/")
            auszug = split[0]
            if len(split) > 1:
                jahr = Afp_fromString(split[1][:2])
                year = self.globals.today().year 
                if Afp_toString(year)[2:] < split[1][:2]:
                    jahr+= (int(year/100)-1) * 100
                else:
                    jahr += int(year/100) * 100
                period = Afp_toString(jahr)
                if len(split[1]) > 2:
                    period += "/" + split[1][2:]
                    # check valid period identifier ?
        #print "AfpFinanceTransactions.extract_period:", auszug, period
        if not period: period = self.period
        return auszug, period
    ## set transaction key generation during data storage 
    # @param flag - flag to turn key generation on (True) or off (False); default: on (True)
    def set_key_generation(self, flag = True):
        self.spread_key = flag
    ## export generated data
    # @param filename - destination file for export
    def export(self, filename):
        Export = AfpExport(self.get_globals(), self.get_selection(), filename, self.is_debug())
        vname = "export." + filename.split(".")[-1]
        #print "AfpFinanceExport.export:", vname
        append =  Afp_ArrayfromLine(self.get_globals().get_value(vname + ".ADRESSE", "Finance"))
        Export.append_data(append)
        fieldlist =  Afp_ArrayfromLine(self.get_globals().get_value(vname, "Finance"))
        information = self.get_globals().get_value(vname + ".info", "Finance")
        Export.write_to_file(fieldlist, information)
    ## overwritten 'store' of the AfpSelectionList, the parent 'store' is called and a common action-number spread.          
    def store(self):
        #print "AfpFinanceTransactions.store 0:",self.new, self.mainindex
        #self.view()
        AfpSelectionList.store(self)
        #print "AfpFinanceTransactions.store 1:",self.new, self.mainindex 
        #self.view()
        if self.spread_key and self.new:
            self.new = False
            VNr = self.get_value("BuchungsNr")
           # print "AfpFinanceTransactions.store VorgangsNr:", VNr
            changed_data = {"VorgangsNr": VNr}
            for i in range(0, self.get_value_length()):
                self.set_data_values(changed_data, None, i)
            #print "AfpFinanceTransactions.store 2:",self.new, self.mainindex 
            #for d in self.selections: print d,":", self.selections[d].data
            AfpSelectionList.store(self)
    ## set payment through indermediate account (payment has to be split)
    def set_payment_transfer(self):
        self.transfer = self.get_special_accounts("ZTF")
    ## add default values to payment data (if specific routines fail)
    # @param data - data dictionary to be modified, will be returned
    def add_payment_data_default(self, data):
        if not "Gegenkonto" in data:
            data["Gegenkonto"] = -1
        return data
    ## flip booking, add remark
    # @param data - data dictornary to be modified and returned
    # @param bem - remark to be added
    def set_storno_values(self, data, bem = "-STORNO-"):
        #data["Betrag"] = - data["Betrag"]
        Konto = data["Konto"]
        data["Konto"] = data["Gegenkonto"]
        data["Gegenkonto"] = Konto
        KtName = data["KtName"]
        data["KtName"] = data["GktName"]
        data["GktName"] = KtName
        data["Bem"] = bem + " " + data["Bem"] 
        return data
    ## retrieve last used receipt number
    # @pßaram colname - name of column checked
    def get_highest_value(self, colname):
        val= None
        rows = self.get_value_rows("BUCHUNG", colname)
        if rows:
            val = rows[0][0]
            for row in rows:
                if row[0] > val: val = row[0]
        #print "AfpFinanceTransactions.get_highest_value:", val
        return val
    ## retrieve individual account from database
    # @param KNr - address identifier
    # @param Typ - typ of account, default: Debitor
    def get_individual_account(self, KNr, Typ = "Debitor"):
         return Afp_getIndividualAccount(self.get_mysql(), KNr, Typ)
    ## retrieve special account from database
    # @param ident - identifier of account
    def get_special_accounts(self, ident):
         return Afp_getSpecialAccount(self.get_mysql(), ident)
    ## get name of account
    # @param nr - number of account of which name is searched
    def get_account_name(self, nr):
         rows = self.get_mysql().select("Bezeichnung","KtNr = " + Afp_toString(nr),"KTNR")
         if rows: return rows[0][0]
         else: return None
    ## add tax identifier to account, due to german tax laws
    # @param konto - number of account
    # @param stkenn - identifier fo tax
    def get_tax_account(self, konto, stkenn):
        steuer = 0
        if stkenn == "UV": steuer = 300000 
        elif stkenn == "UH": steuer = 200000 
        elif stkenn == "VV": steuer = 900000 
        elif stkenn == "VH": steuer = 800000 
        return steuer + konto
    ##  add entries for adhoc discount during payment (only usable for invoice)
    # @param data - incident data where discount is given
    def data_create_skonto_accounting(self, data):
        acc = None
        if data.get_listname() == "Rechnung":
            preis = data.get_value("RechBetrag")
            zahlung = data.get_value("Zahlung")
            if zahlung < preis and zahlung >= data.get_value("ZahlBetrag"):
                kdnr = data.get_value("KundenNr.RECHNG")
                name = data.get_name(True)
                beleg =  data.get_string_value("RechNr.RECHNG")
                konto =  data.get_value("Debitor.RECHNG")
                today = self.globals.today()
                skonto = preis - zahlung
                sgkt = self.get_special_accounts("SKTO")
                sbem = "Skonto: " + name
                tab = data.get_mainselection()
                tabnr = data.get_value()
                acc = {"Datum": today,"Konto": konto, "Gegenkonto ": sgkt,"Beleg": beleg,"Betrag": skonto,"KtName": name ,"GktName": "SKTO","KundenNr": kdnr,"Bem":  sbem,"Tab": tab,"TabNr":tabnr}
        return acc
    ## add one payment entry according to input
    # @param payment - amount of payment
    # @param datum - date when  payment has been recorded
    # @param auszug -  statement of account where payment has been recorded
    # @param KdNr -  number of address this payment is assigned to
    # @param Name -  name of the address this payment is assigned to
    # @param data -  incident data where financial values have to be extracted, if == None: payment is assigned to transferaccount
    # @param reverse -  accounting data has to be swapped
    def add_payment(self, payment, datum, auszug, KdNr, Name, data = None, reverse = False):
        print "AfpFinanceTransactions.add_payment:", self.period, payment, datum, auszug, KdNr, Name, reverse 
        if auszug: self.set_auszug(auszug, datum)
        accdata = {}
        accdata["Datum"] = datum
        accdata["Betrag"] = payment
        accdata["Beleg"] = auszug
        accdata["KundenNr"] = KdNr
        accdata["Art"] = "Zahlung"
        accdata["Eintrag"] = self.globals.today()
        accdata["Reference"] = auszug
        accdata["Period"] = self.period
        if data is None: 
            # received payment, has to be distributed
            self.set_payment_transfer()         
            KtNr = self.get_value("KtNr.AUSZUG")
            accdata["Konto"] = KtNr
            accdata["KtName"] = self.get_account_name(KtNr)
            accdata["Gegenkonto"] = self. transfer
            accdata["GktName"] = "ZTF"
            accdata["Bem"] = "Mehrfach (" + Name + ")"
        else:
            if data.is_outgoing(): reverse = not reverse
            # distribute according to data-types
            if self.transfer: 
                accdata["Konto"] = self.transfer
                accdata["KtName"] = "ZTF"
                accdata["Bem"] = "Mehrfach (" + Name + "): " + data.get_name()
            else: 
                KtNr = self.get_value("KtNr.AUSZUG")
                accdata["Konto"] = KtNr
                accdata["KtName"] = self.get_account_name(KtNr)
                accdata["Bem"] = "Zahlung: " + Name
            accdata = self.add_payment_data(accdata, data)
        accdata = self.add_payment_data_default(accdata)
        if reverse: accdata = self.set_storno_values(accdata, "-Ausgabe-")
        self.set_data_values(accdata, None, -1)
        # possible Skonto has to be accounted during payment
        if data:
            accdata = self.data_create_skonto_accounting(data)
            if accdata:
                self.set_data_values(accdata, None, -1)
    ## extract payment relevant data from 'data' input
    # @param paymentdata - payment data dictionary to be modified and returned
    # @param data - incident data where relevant values have to be extracted
    def add_payment_data(self, paymentdata, data):
        # has to return the account number this payment has to be charged ("Gegenkonto"), the table identifier ("Tab","TabNr")        
        paymentdata["Tab"] = data.get_mainselection()
        paymentdata["TabNr"] = data.get_value()
        data.add_payment_data(paymentdata)
        return paymentdata
    ## financial transaction entries for payment are generated according to incident data given
    # @param data - incident data where entries are created from
    # @param storno - flag if incident should be cancelled
    def add_payment_transactions(self, data, storno = False):
        print "AfpFinanceTransactions.add_paymenmt_transactions", storno
        today = self.globals.today()
        amount, payment, paydate = data.get_payment_values()
        KdNr = data.get_value("KundenNr")
        name = data.get_name(True)
        beleg = "PT" + Afp_toInternDateString(today)
        self.add_payment(payment, paydate, beleg ,KdNr, name, data, storno)
    ## financial transaction entries are generated according to incident data given
    # @param data - incident data where entries are created from
    # @param storno - flag if incident should be cancelled
    def add_financial_transactions(self, data, storno = False):
        print "AfpFinanceTransactions.add_financial_transactions", storno
        today = self.globals.today()
        accdata = self.add_financial_transaction_data(data)
        print "AfpFinanceTransactions.add_financial_transactions accdata:", accdata
        if accdata:
            for acc in accdata:
                if not "Tab" in acc: 
                    acc["Tab"] = data.get_maiselection()
                    acc["TabNr"] = data.get_Value()
                acc["Art"] = "Intern"
                acc["Eintrag"] = today
                acc["Period"] = self.period
                if storno: acc = self.set_storno_values(acc)
                self.set_data_values(acc, None, -1)
    ## direct financial transaction is added to SelectionList
    # @param accdata - dictionary of financial transaction data the following values have to be given: \n
    # - 'Datum' - date of transaction
    # - 'Konto'' - account of left side (Soll)
    # - 'Gegenkonto' - account of right side (Haben)
    # - 'Betrag' - amount of this transaction
    # - 'Beleg' - number of receipt
    # - 'KundenNr' - address identifier of involved person
    # - Optional:
    # - 'Bem' -  remark
    # - 'Art' -  typ of financial transaction
    # - 'Tab' - tablename of involved incident
    # - 'TabNr' - table identifier of involved incident
    # - 'VorgangsNr' - if given,
    # - 'Reference' - reference to accountiong receipt
    def add_direct_transaction(self, accdata):
        today = self.globals.today()
        if accdata:
            if not "Art" in accdata: accdata["Art"] = "Direct"
            if not "KtName" in accdata and "Konto" in accdata:
                accdata["KtName"] = self.get_account_name(accdata["Konto"])
            if not "GktName" in accdata and "Gegenkonto" in accdata:
                accdata["GktName"] = self.get_account_name(accdata["Gegenkonto"])
            accdata["Eintrag"] = today
            accdata["Period"] = self.period
            #print "AfpFinanceTransactions.add_direct_transactions", accdata, self.get_value_length()
            self.set_data_values(accdata, None, -1)
    ## financial transaction data is delivered in a list of dictionaries from incident data \n
    # this routine splits into the different incident routines. \n
    # REMARK: as it is planned to hold the financial tarnsactions for all the different incidents central in this deck \n
    # no use is made of the object-orientated approach, but this routine is used to split into the appropriate extraction routine.
    # @param data - incident data enrties are extracted from \n
    # this routine has to return a list of the following data: \n
    #[{"Datum":   .                                 "Konto":  ,                 "Gegenkonto ":   ,            "Betrag":  ,"Beleg":  ,     "Bem":  },{}, ...] \n
    # [date where accounting gets valid, first accountnumber, second accountnumber, balance, receiptnumber, remark]
    def add_financial_transaction_data(self, data):
        print "AfpFinanceTransactions.add_financial_transaction_data"
        if data.get_listname() == "Charter":
            accdata = self.add_transaction_data_charter(data)
        elif data.get_listname() == "Rechnung":
            accdata = self.add_transaction_data_rechnung(data)
        else:
            return None
        for acc in accdata:
            acc["VorgangsNr"] = 0
        return accdata
    ## shift a payment from the internal general account to the specified account
    # @param data - incident data according to which payment has to be shifted
    def add_internal_payment(self, data):
        # shifts an already received payment to another account if necessary
        print "AfpFinanceTransactions.add_internal_payment"
        accdata = {}
        listname = data.get_listname()
        if listname == "Charter":
            accdata = self.add_internal_payment_charter(accdata, data)      
        if accdata:
            today = self.globals.today()
            accdata["Datum"] = today
            accdata["Bem"] = "Anzahlung " + listname
            accdata["Art"] = "Zahlung intern" 
            accdata["Tab"] = data.get_mainselection()  
            accdata["TabNr"] = data.get_value()  
            accdata["Beleg"] = "Intern"  
            accdata["Eintrag"] = today
            accdata["Period"] = self.period
            self.set_data_values(accdata, None, -1)
    ## Charter: deliver financial transaction data
    # @param data - Charter data where relevant values have to be extracted
    def add_transaction_data_charter(self, data):
        print "AfpFinanceTransactions.add_transaction_data_charter"
        accdata = []
        if data.exists_selection("RECHNG") or data.get_value("RechNr"):
            accdata = self.add_transaction_data_rechnung(data)
        return accdata
    ## Charter: deliver internal payment transaction data
    # @param paymentdata - payment data dictionary to be modified and returned
    # @param data - Charter data where relevant values have to be extracted
    def add_internal_payment_charter(self, paymentdata, data):
        print "AfpFinanceTransactions.add_internal_payment_charter:"
        #for d in self.selections: print d,":", self.selections[d].data
        #for d in data.selections: print d,":", data.selections[d].data
        zahlung = data.get_value("Zahlung.RECHNG")
        if Afp_isEps(zahlung):
            paymentdata["Betrag"] = zahlung
            paymentdata["Konto"] = Afp_getSpecialAccount(self.get_mysql(), "MFA")
            paymentdata["KtName"] = "MFA"
            paymentdata["KundenNr"] = data.get_value("KundenNr")        
            paymentdata = self.add_payment_data_rechnung(paymentdata, data)
        return paymentdata
    ## Rechnung (Invoice): deliver financial transaction data
    # @param data - Rechnung data where relevant values have to be extracted
    def add_transaction_data_rechnung(self, data):
        print "AfpFinanceTransactions.add_transaction_data_rechnung"
        accdata = []
        datum = data.get_value("Datum.RECHNG")
        preis =  data.get_value("RechBetrag.RECHNG")
        if Afp_isEps(preis):
            tab =  data.get_maiselection()
            tabnr =  data.get_value()
            bem = "Rechnung"
            if data.get_value("Fahrt.RECHNG"):
                bem = "Charter"
                if von[:8] == "Rechnung":
                    von = "Charter" + data.get_string_value("Fahrt.RECHNG")
            kdnr = data.get_value("KundenNr.RECHNG")
            name = data.get_name(True)
            bem += " " + name
            beleg =  data.get_string_value("RechNr.RECHNG")
            konto =  data.get_value("Debitor.RECHNG")
            gkonto = self.get_tax_account(data.get_value("Kontierung.RECHNG"), "U" + data.get_string_value("Ust.RECHNG"))
            gktname = self.get_account_name(data.get_value("Kontierung.RECHNG"))
            # Skonto
            acc = self.data_create_skonto_accounting(data)
            if acc: accdata.append(acc)
            # second account involved
            gkonto2 = 0
            if data.get_value("Konto2.RECHNG") and Afp_isEps(data.get_value("Preis2.RECHNG")):
                gkonto2 = data.get_value("Konto2.RECHNG")
                gkt2 = self.get_account_name(gkonto2)
                preis2 = data.get_value("Betrag2.RECHNG")
                preis -= preis2         
            acc = {"Datum": datum,"Konto": konto, "Gegenkonto": gkonto,"Beleg": beleg,"Betrag": preis,"KtName": name,"GktName": gktname,"KundenNr": kdnr,"Bem":  bem,"Tab": tab,"TabNr":tabnr}
            accdata.append(acc)
            if gkonto2:
                acc = {"Datum": datum,"Konto": konto, "Gegenkonto ": gkonto2,"Beleg": beleg,"Betrag": preis,"KtName": name,"GktName": gkt2,"KundenNr": kdnr,"Bem":  bem,"Tab": tab,"TabNr":tabnr}
                accdata.append(acc)
        return accdata
 

## class to handle a single finance transaction, 
class AfpFinanceSingleTransaction(AfpFinanceTransactions):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param BuchNr - if given, identifier of  transactions
    # @param period - if given, period marker for transactions
    def  __init__(self, globals, BuchNr = None, period = None):
        AfpFinanceTransactions.__init__(self, globals, BuchNr, None, period)   
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr =  KundenNr.BUCHUNG"] 
        self.selects["ARCHIV"] = [ "ARCHIV","KundenNr =  KundenNr.BUCHUNG"] 
        if self.debug: print "AfpFinanceSingleTransaction Konstruktor:", self.period
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpFinanceSingleTransaction Destruktor" 
    ## set identification data for archive \n
    # do nothing - overwritten from AfpSelectionList
    # @param data - dictionary where identifiers should be added
    def set_archiv_table(self, data):
        return data
        
## class to handle finance depedencies, 
class AfpFinance(AfpFinanceTransactions):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param period_input - if given, period marker for transactions
    # @param parlist - if given, list of parameter; 
    # -   Auszug: identifier of statement of account
    # -   Datum: if Auzug; date of statement of account
    # -   Saldo; if given, start balance of account for this statement of account
    # @param mandant - if given, identifier of mandant where transactions are looked for
    def  __init__(self, globals, period_input = None, parlist = None, mandant = None):
        #print "AfpFinance.init:", period_input, parlist, mandant
        self.client_factory = None
        self.auszug = None
        self.batch = None
        self.bank = None     
        self.konto = None     
        self.transfer = None     
        self.accounts_set = None
        self.data_absorbed = None
        self.addressdata = []
        period = AfpFinance_setPeriod(period_input, globals, None, mandant)
        if parlist:
            if "BuchungsNr" in parlist:
                value = parlist["BuchungsNr"]
                mainindex = "BuchungsNr"
            elif "Auszug" in parlist:
                self.auszug = parlist["Auszug"]
                value = self.auszug
                mainindex = "Reference"
            elif "Stapel" in parlist:
                self.batch = parlist["Stapel"]
                value = self.batch
                mainindex = "Reference"
            elif "VorgangsNr" in parlist:
                value= parlist["VorgangsNr"]
                mainindex = "VorgangsNr"
            elif "KundenNr" in parlist:
                value= parlist["KundenNr"]
                mainindex = "KundenNr"
            elif "Konto" in parlist:
                value= parlist["Konto"]
                mainindex = "Konto"
            elif "Gegenkonto" in parlist:
                value= parlist["Gegenkonto"]
                mainindex = "Gegenkonto"
        else:
            value = period_input
            mainindex = "Period"
        #print "AfpFinance.init AfpFinanceTransactions:", value, mainindex, period, parlist
        AfpFinanceTransactions.__init__(self, globals, value, mainindex, period, True)
        if parlist and "Konto" in parlist and "Gegenkonto" in parlist:
            konto = Afp_toString(parlist["Konto"])
            gkonto = Afp_toString(parlist["Gegenkonto"])
            self.mainfilter ="(Konto = " + konto + " OR Gegenkonto = " + gkonto + ") AND Period = \"" + self.period + "\""
            self.konto = konto
            self.set_main_selects_entry() 
        self.selects["KTNR"] = [ "KTNR","NOT Typ = \"Debitor\" AND NOT Typ = \"Kreditor\""] 
        self.selects["AUSGABE"] = [ "AUSGABE","Modul = \"Finance\""] 
        self.selects["Mandant"] = [ "ADRESSE"," KundenNr = " + Afp_toString(mandant)] 
        # only needed for "Konto" or "Gegenkonto"
        if mainindex == "Konto" or mainindex == "Gegenkonto":
            konto = Afp_toString(value)
            self.selects["Konto"] = [ "KTNR"," KtNr = " + konto] 
            self.selects["AUSZUG"][1] = "KtNr = " + konto + " AND Auszug = \"SALDO\" AND " + self.selects["AUSZUG"] [1]
        elif mainindex == "Reference":
            self.selects["AUSZUG"][1] = "Auszug = \"" + Afp_toString(value) + "\" AND " + self.selects["AUSZUG"] [1]
            self.selects["Konto"] = [ "KTNR"," KtNr = KtNr.AUSZUG"] 
        #print "AfpFinance.init selects:", self.selects, self.mainselection
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)
        #print "AfpFinance.init set_auszug:", self.auszug, self.mainfilter
        if self.auszug:
            ausdat = None
            aussald = None
            if "Datum" in parlist:
                ausdat = parlist["Datum"]
            if "Saldo" in parlist:
                aussald = parlist["Saldo"]
            #print "AfpFinance.init set_auszug:", self.auszug, ausdat, aussald
            self.set_auszug(self.auszug, ausdat, aussald, True)
            self.bank = self.get_value("KtNr.AUSZUG")
        elif self.batch:
            self.set_batch(self.batch)
        #print "AfpFinance Konstruktor:", self.mainindex, self.mainvalue 
        if self.debug: print "AfpFinance Konstruktor:", self.mainindex, self.mainvalue 
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpFinance Destruktor" 
    ## return if this SelectionList has changed    
    # overwritten from AfpSelectionList
    def has_changed(self):
        return self.data_absorbed or super(AfpFinance, self).has_changed()

    ## set identifier of statement of account (Auszug)
    # @param batchname - identifier of batch-bookings for statement of account 
    # @param datum, - if given, date of batch-bookings 
    def set_batch(self, batchname, datum = None):  
        today = self.globals.today()
        if not datum: datum = today
        batchname, period = self.extract_period(batchname)
        self.set_value("Auszug.AUSZUG", batchname)
        self.set_value("BuchDat.AUSZUG", datum) 
        self.set_value("Datum.AUSZUG", today)
        self.set_value("Period.AUSZUG", period)
    ## overwritten 'store' of the AfpSelectionList, to take care of "AUSZUG" selection which is only a fake in this case.          
    def store(self):
        if self.batch:
            self.delete_selection("AUSZUG")
        super(AfpFinance, self).store()
    ## extract values from a single TableSelection and flavour it with addressdata \n
    # overwritten from AfpSelectionList
    # @param sel - if given name of TableSelection
    # @param felder - column names to be retrieved
    # @param row - index of row in TableSelection
    def get_value_rows(self, sel = None, felder = None, row = -1):
        rows = super(AfpFinance, self).get_value_rows(sel, felder, row) 
        if sel == "BUCHUNG" and felder and row < 0:
            if not self.addressdata: self.gen_addressdata()
            if self.addressdata and len(self.addressdata) >= len(rows):
                orig = self.get_selection("BUCHUNG").get_feldnamen()
                #print "AfpFinance.get_value_rows orig:", orig
                fields = felder.split(",")
                for j in range(len(fields)):
                    if fields[j] in orig: continue
                    for i in range(len(rows)):
                        rows[i][j] = self.addressdata[i].get_value(fields[j])
            #print "AfpFinance.get_value_rows:", rows
        return rows
    ## attach all needed addressdata
    def gen_addressdata(self):
        for i in range(self.get_value_length("BUCHUNG")):
            KNr = self.get_value_rows("Buchung","KundenNr", i)[0][0]
            #print "AfpFinance.gen_addressdata KNr:", KNr
            self.addressdata.append(AfpAdresse(self.get_globals(), KNr))
    ## set all available accouts
    def set_accounts(self):
        self.accounts_set = True
        self.revenue_accounts = []
        self.expense_accounts = []
        self.cash_accounts = []
        self.internal_accounts = []
        self.revenue_account_names = []
        self.expense_account_names = []
        self.cash_account_names = []
        self.internal_account_names = []
        rows = self.get_value_rows("KTNR")
        if rows:
            for row in rows:
                if not row[0] == "SALDO":
                    if row[4] == "Kosten":
                        self.expense_accounts.append(row[1])
                        self.expense_account_names.append(Afp_toString(row[2]))     
                    elif row[4] == "Ertrag":
                        self.revenue_accounts.append(row[1])
                        self.revenue_account_names.append(Afp_toString(row[2]))           
                    elif row[4] == "Bank" or row[4] == "Kasse":
                        self.cash_accounts.append(row[1])
                        self.cash_account_names.append(Afp_toString(row[2])) 
                        if not self.bank and row[4]  == "Bank":
                            self.bank = row[1]
                    else:
                        self.internal_accounts.append(row[1])
                        self.internal_account_names.append(Afp_toString(row[2]))    
                        if row[0] == "ZTF": 
                            self.transfer = row[1]
   ## return mayor type of this SelectionList,
    def get_mayor_type(self):
        #print "AfpFinance.get_mayor_type:", "AfpFinance"
        return "AfpFinance"
    ## get all available accouts of a given typ
    # @param typ - typ of returned account list, possible are 'Kosten', 'Ertrag', 'Cash', 'Other'
    def get_accounts(self, typ):
        if not self.accounts_set:
            self.set_accounts()
        if typ == "Kosten":
            return  self.expense_accounts
        elif typ == "Ertrag":
            return  self.revenue_accounts
        elif typ == "Cash":
            return  self.cash_accounts
        elif typ == "Other":
            return  self.internal_accounts
        else:
            return None
    ## get the name of a given account number
    # @param nr - number of account wherer name is looked for
    def get_account_name(self, nr):
        if not self.accounts_set:
            self.set_accounts()
        name = None
        if nr in self.expense_accounts:
            name = self.expense_account_names[self.expense_accounts.index(nr)]
        elif nr in self.revenue_accounts:
            name = self.revenue_account_names[self.revenue_accounts.index(nr)]
        elif nr in self.cash_accounts:
            name = self.cash_account_names[self.cash_accounts.index(nr)]
        elif nr in self.internal_accounts:
            name = self.internal_account_names[self.internal_accounts.index(nr)]
        return name
    ## get the lines of a given account types
    # @param types - comma separated list of types to be extracted
    def get_account_lines(self, types):
        lines = []
        typs = types.split(",")
        if not self.accounts_set:
            self.set_accounts()
        for typ in typs:
            typ =  typ.strip()
            if typ == "Cash":
                for i in range(len(self.cash_accounts)):
                    lines.append(Afp_toString(self.cash_accounts[i]) + " " + self.cash_account_names[i])
            if typ == "Internal":
                for i in range(len(self.internal_accounts)):
                    lines.append(Afp_toString(self.internal_accounts[i]) + " " + self.internal_account_names[i])
            if typ == "Kosten":
                for i in range(len(self.expense_accounts)):
                    lines.append(Afp_toString(self.expense_accounts[i]) + " " + self.expense_account_names[i])
            if typ == "Ertrag":
                for i in range(len(self.revenue_accounts)):
                    lines.append(Afp_toString(self.revenue_accounts[i]) + " " + self.revenue_account_names[i])
        return lines

    ## check if account is a cash account
    # @param ktnr - account number to be checked
    def is_cash(self, ktnr):
        if not self.accounts_set:
            self.set_accounts()
        return ktnr in self.cash_accounts
    ## add client factory to genertae client objects
    def add_client_factory(self, factory):
        self.client_factory = factory
    ## return client object if possible
    #@param ident - identifier of created client onject
    def get_client(self, ident):
        client = None
        if self.client_factory:
            client = self.client_factory.get_client(ident)
        return client
    ## return period for transactions
    def get_period(self):
        return self.period
    ## return identierfier of statement of account, if available
    def get_auszug(self):
        return self.auszug
    ## return identierfier of batch booking, if available
    def get_batch(self):
        return self.batch
    ## return accounting number of involved bank account
    def get_bank(self):
        if not self.accounts_set:
            self.set_accounts()
        return self.bank
    ## return accounting number of involved bank account
    def get_transfer(self):
        if not self.accounts_set:
            self.set_accounts()
        return self.transfer
    ## generate next receipt number
    def gen_next_rcptnr(self):
        nr = self.get_highest_value("Beleg")
        if not nr:
            select = "SELECT MAX(CONVERT(Beleg,UNSIGNED)) FROM BUCHUNG WHERE Period = \"" + self.period + "\""
            res = self.get_globals().get_mysql().execute(select)
            nr = Afp_fromString(res[0][0])
            #print "AfpFinance.gen_next_rcptnr select:", select, nr, res
        if Afp_isNumeric(nr):
            nr += 1
        #print "AfpFinance.gen_next_rcptnr:", nr,  Afp_isNumeric(nr)
        return nr
    ## generate bank-account sum
    def get_salden(self):
        start = 0.0
        end = 0.0
        rows = self.get_value_rows("AUSZUG","Auszug,StartSaldo,EndSaldo,KtNr")
        konto = Afp_fromString(self.konto)
        for row in rows:
            if row[0] == "SALDO" and row[3] == konto:
                start = row[1]
                end = row[2]
        sum = self.gen_sum(konto)
        #print "AfpFinance.get_salden:", sum
        return start, start + sum
    ## generate bank-account sum
    def gen_bank_sum(self):
        start = 0.0
        if self.auszug:
            start = self.get_value("StartSaldo.Auszug")
            if not start: start = 0.0
        sum = self.gen_sum(self.bank)
        sum += start
        if self.auszug:
            self.set_value("EndSaldo.Auszug", sum) 
        #print "AfpFinance.gen_bank_sum:", sum
        return sum
    ## generate account sum
    # @param konto - accountnumber to be summerized
    def gen_sum(self, konto):
        #print "AfpFinance.gen_sum:", self.view()
        sum = 0.0
        rows = self.get_value_rows("BUCHUNG","Konto,Gegenkonto,Betrag")   
        for row in rows:
            betrag = Afp_fromString(row[2])
            if row[0] == konto: sum -= betrag
            elif row[1] == konto: sum += betrag
        if self.is_cash(konto):
            sum*= -1
        return sum
    ## absorb finance bookings from another AfpFinance object
    # @param object - AfpFinance object where to absorb data
    def booking_absorber(self, object):
        #print "AfpFinance.booking_absorber:", type(self), type(object), object.get_value_length("BUCHUNG")
        if type(self) == type(object) and object.get_value_length("BUCHUNG"):
            if self.client_factory:
                rows = object.get_value_rows("BUCHUNG", "Tab,TabNr,Art")
                #print "AfpFinance.booking_absorber rows:", rows
                splist = []
                for i in range(len(rows)):
                    row = rows[i]
                    if row[0] and row[1] and row[2] != "Intern":
                        client = self.get_client(row[1])
                        split = client.get_splitting_values() 
                        #print "AfpFinance.booking_absorber rows:", split, row[0], client.get_mainselection(), row[0] == client.get_mainselection(), client.get_listname()
                        if split and row[0].upper() == client.get_mainselection().upper():
                            for j in range(len(split)):
                                split[j].append(i)
                            splist += split
                if splist:
                    object.split_bookings(splist)
            if object.get_value_length("BUCHUNG"):
                self.get_selection("BUCHUNG").data += object.get_selection("BUCHUNG").data
                self.data_absorbed = True
    ## add split bookings to given booking row
    # @param split_values - list of [accoutNr, value, name of account, rowNr] to be used in splitting
    def split_bookings(self, split_values):
        if self.debug: print "AfpFinance.split_booking:", split_values
        #print "AfpFinance.split_booking:", split_values
        add = 0
        split_indices = []
        for row in split_values:
            split_indices.append(row[3])
            if row[2]:
                add += 1
        if add:
            data = self.get_selection("BUCHUNG").data
            dlen = len(data)
            data += [None]*add 
            index = len(split_values)-1
            new_i = dlen+add-1
            for i in range(dlen-1, -1, -1):
                if i == split_indices[index]:
                    #print "AfpFinance.split_booking loop:", i, index, split_indices[index]
                    while index >= 0 and i == split_indices[index]:
                        #print "AfpFinance.split_booking while:", i, index, split_indices[index], split_values[index]
                        values = split_values[index]
                        row = Afp_copyArray(data[i])
                        row[4] = values[0]
                        row[7] = values[1] # possibly scaling needed
                        if values[2]:
                            row[5] = values[2]
                            row[9] = Afp_toString(values[2]) +  " " + row[9]
                        data[new_i] = row
                        index -= 1
                        new_i -=1
                else:
                    data[new_i] = data[i]
                    new_i -= 1
            #print "AfpFinance.split_booking data:", data
            #self.get_selection("BUCHUNG").data = data   # not needed

## class to handle account balances
class AfpFinanceBalances(AfpSelectionList):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is 
    # @param period - if given, period marker for transactions
    def  __init__(self, globals, period = None, mandant=None):
        AfpSelectionList.__init__(self, globals, "BUCHUNG", globals.is_debug())
        self.mandant = mandant
        self.cash = None
        self.salden = {}
        self.typen = None
        self.namen = None
        self.typs = None
        self.mainselection = "BUCHUNG"
        self.mainindex = "Period"
        self.mainvalue = AfpFinance_setPeriod(period, globals, None, self.mandant)
        self.period = self.mainvalue
        print "AfpFinanceBalances.init:", self.period
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)
        self.selects["KTNR"] = [ "KTNR","NOT Typ = \"Debitor\" AND NOT Typ = \"Kreditor\""] 
        self.selects["Saldo"] = [ "KTNR","KtName = \"SALDO\""] 
        self.selects["Salden"] = [ "AUSZUG","Period = \"" + self.period + "\" AND Auszug = \"SALDO\""] 
        self.selects["Mandant"] = [ "ADRESSE"," KundenNr = " + Afp_toString(self.mandant)] 
        if self.debug: print "AfpFinanceBalances Konstruktor:", self.mainindex, self.mainvalue 
        #self.view()
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpFinanceBalances Destruktor" 
        
    ## generate startdate of period
    def start_of_period(self):
        if Afp_isInteger(Afp_fromString(self.period)):
            return Afp_fromString("1.1." + self.period)
        return None
    ## generate enddate of period
    def end_of_period(self):
        if Afp_isInteger(Afp_fromString(self.period)):
            dat =  Afp_fromString("31.12." + self.period)
            if self.get_globals().today() < dat:
                dat = self.get_globals().today()
            return dat
        return None
    ## get actuel period
    def get_period(self):
        return self.period
    ## generate next period
    def gen_next_period(self):
        next = AfpFinance_nextPeriod(self.period)
        return next
    ## generate typ and name dictionaries of accounts
    def gen_typname(self):
        if not self.typen or not self.namen:
            self.typen = {}
            self.namen = {}
            rows = self.get_value_rows("KTNR","KtNr,Typ,KtName,Bezeichnung")
            for row in rows:
                if not row[2] == "SALDO":
                    self.typen[row[0]] = row[1]
                    self.namen[row[0]] = row[3]
                else:
                    self.namen[row[0]] = "SUMME " + row[3].upper()
    ## get typ of account
    # @param ktnr - account number
    def get_typ(self, ktnr):
        if not self.typen:
            self.gen_typname()
        if ktnr in self.typen:
            return self.typen[ktnr]
        else:
            return None
    ## get name of account
    # @param ktnr - account number
    def get_name(self, ktnr):
        if not self.namen:
            self.gen_typname()
        if ktnr in self.namen:
            return self.namen[ktnr]
        else:
            return ""
    ## set cash account numbers
    def set_cash(self):
        self.cash = []
        rows = self.get_value_rows("KTNR")
        if rows:
            for row in rows:
                if not row[0] == "SALDO":
                    if row[4] == "Bank" or row[4] == "Kasse":
                        self.cash.append(row[1])
    ## check if account is cash-account
    # @param ktnr - account number to bec checked
    def is_cash(self, ktnr):
        if not self.cash:
            self.set_cash()
        return ktnr in self.cash
        
    ## reset salden property from 'Salden' selection list
    def reset_salden(self):
        self.salden = {}
        self.set_salden(True)
    ## set salden property from 'Salden' selection list
    # @param reset - flag if salden should be resetted for balance generation
    def set_salden(self, reset=False):
        rows = self.get_value_rows("Salden")
        for row in rows:
            if reset:
                if row[3]:
                    row[4] = row[3]
                else:
                    row[4] = 0.0
            self.salden[row[-1]] = row
        #print "AfpFinanceBalances.set_salden:", self.salden
    ## store all generated balances ('salden')
    def store_salden(self):
        if self.salden:
            salden = self.get_selection("Salden")
            #print "AfpFinanceBalances.store_salden original:", salden.data
            salden.set_data(self.salden.values())
            #print "AfpFinanceBalances.store_salden modified:", salden.data
            salden.store()
        
    ## generate sums of all accounts which have been touched by the bookings of the period
    # @param upto - if given, date to which the bookings should be respected
    def gen_balances(self, upto=None):
        rows = self.get_value_rows("BUCHUNG","Datum,Konto,Gegenkonto,Betrag")   
        for row in rows:
            if not upto or row[0] <= upto:
                betrag = Afp_fromString(row[3])
                if betrag:
                    if self.is_cash(row[1]):
                        bet1 = -betrag
                    else:
                        bet1 = betrag
                    if self.is_cash(row[2]):
                        bet2 = -betrag
                    else:
                        bet2 = betrag
                    if row[1] in self.salden:
                        self.salden[row[1]][4] -=bet1
                        if row[0] > self.salden[row[1]][2]:
                            self.salden[row[1]][2] = row[0]
                    else:
                        self.salden[row[1]] = ["SALDO", row[0], row[0], 0.0, -bet1, self.period, row[1]]
                    if row[2] in self.salden:
                        self.salden[row[2]][4] +=bet2
                        if row[0] > self.salden[row[1]][2]:
                            self.salden[row[1]][2] = row[0] 
                    else:
                        self.salden[row[2]] = ["SALDO", row[0], row[0], 0.0, bet2, self.period, row[2]]                        
    ## generate sums of all accounts which have been touched by the bookings of the period
    def gen_sums(self):
        rows = self.get_value_rows("Saldo","KtNr,Bezeichnung,Typ")
        self.typs = {}
        for row in rows:
            split = row[2].split(",")
            for sp in split:
                self.typs[sp] = row[0]
            self.salden[row[0]] =  ["SALDO", self.start_of_period(), self.end_of_period(), 0.0, 0.0, self.period, row[0]]
        for sald in self.salden:
            typ = self.get_typ(sald)
            if typ and typ in self.typs:
                if self.salden[sald][3]:
                    self.salden[self.typs[typ]][4] += self.salden[sald][4] - self.salden[sald][3]
                else:
                    self.salden[self.typs[typ]][4] += self.salden[sald][4]
        #print "AfpFinanceBalances.gen_sums:"
        #for sald in sorted(self.salden):
            #print sald, "=", Afp_toString(self.salden[sald][4]), Afp_toString(self.salden[sald][3]), "(" + self.get_name(sald) + ")"
    ## generate all sums and balances for the current period and store it in database
    def gen_salden(self):
        self.reset_salden()
        self.gen_balances()
        self.gen_sums()
        self.store_salden()
    ## close actuel period and switch to next period
    def switch_period(self):
        self.gen_salden()
        self.period = AfpFinance_setPeriod(self.gen_next_period(), self.globals, None, self.mandant)
        new_salden = {}
        for saldo in self.salden:
            sald = self.salden[saldo]
            if sald[3]:
                sald[3] = sald[4]
                sald[1] = self.start_of_period()
                sald[2] = sald[1]
                sald[5] = self.period
                new_salden[saldo] = sald
        self.salden = new_salden
        self.clear_selections(["KTNR", "Saldo", "Mandant"])
        self.mainvalue = self.period
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)
        self.selects["Salden"] = [ "AUSZUG","Period = \"" + self.period + "\" AND Auszug = \"SALDO\""] 
        self.store_salden()
        if self.globals.get_value("actuel-transaction-period","Finance"):
            self.globals.set_value("actuel-transaction-period", self.period,"Finance")
            self.globals.modify_config("Finance", ["actuel-transaction-period"])
                 
## class to export financial transactions
class AfpFinanceExport(AfpSelectionList):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param period - if given, [startdate, enddate] for data to be exported otherwise selectionlists must be given
    # @param selectionlists - if given and no period given, SelectionLists holding the data to be exported
    # @param only_payment - flag if only payments shouzld be extracted
    # - None: all entries are extracted
    # - False: only internal transitions are extracted
    # - True: only payments are extracted
    def  __init__(self, globals, period, selectionlists = None, only_payment = None):
        AfpSelectionList.__init__(self, globals, "Export", globals.is_debug())
        self.filename = None
        self.type = None
        self.information = None
        self.finance = None
        self.singledate = None
        self.selectionlists = selectionlists
        self.use_payments = True
        self.use_transactions = True
        if only_payment:
            self.use_transactions = False
        if period:
            if selectionlists: print "WARNING:AfpFinanceExport selectionlist given - only period used!"
            self.period  = period
            if len(period) == 1: self.singledate = period[0]
        else:
            if not selectionlists: print "WARNING:AfpFinanceExport no selectionlist and no period given!"
            self.singledata = globals.today()
        if self.singledate:
            # in case of a single date look for transactions already exported at that date
            self.selects["BUCHUNG"] = [ "BUCHUNG", self.set_period_select("Export")]   
        else:
            # otherwise for transaction becoming valid in this period
            self.selects["BUCHUNG"] = [ "BUCHUNG", self.set_period_select("Datum")]   
        self.mainselection = "BUCHUNG"
        if self.debug: print "AfpFinanceExport Konstruktor"
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpFinanceExport Destruktor"
    ## compose the period select string
    # @param field - name of tablefield to be involved in this selection
    def set_period_select(self, field):
        select = ""
        if self.singledate:
            select = field + " = \"" + Afp_toInternDateString(self.singledate)  + "\""
        else:  
            select =  field + " >= \"" + Afp_toInternDateString(self.period[0]) + "\" AND " 
            select +=   field + " <= \"" + Afp_toInternDateString(self.period[1]) + "\""
            select = "!"+ select
        return select
    ## set output files
    # @param filename - name of file where data should be written (see AfpBaseRoutines.AfpExport)
    # @param template - if given, name of templatefile to be used for output (only used for dbf output)
    def set_output(self, filename, template):
        self.filename = filename
        self.type = filename.split(".")[-1]
        #print"AfpFinanceExport.set_output:", template, Afp_existsFile(template)
        if Afp_existsFile(template):
            self.information = template
    ## set information data for export
    # @param info - information data (see AfpBaseRoutines.AfpExport)
    def set_information(self, info):
        self. information = info
    ## actually generate transactions to be exported
    def generate_transactions(self):
        if self.selectionlists:
            self.finance = AfpFinanceTransactions(self.globals)
            for liste in self.selectionlists:
                sellist = self.selectionlists[liste]
                if sellist:
                    if self.use_transactions:
                        self.finance.add_financial_transactions(sellist)
                    if self.use_payments:
                        self.finance.add_payment_transactions(sellist)
    ## get the appropriate table selections
    def get_accounting(self):
        #print "AfpFinanceExport.get_accounting:", self.mainselection, self.selects, self.selections
        if self.finance:
            return self.finance.get_selection()
        else:
            return self.get_selection()
    ## perform export
    def export(self):
        if self.selectionlists:
            self.generate_transactions()
        select = self.get_accounting()            
        Export = AfpExport(self.get_globals(), select, self.filename, self.debug)
        vname = "export." + self.type 
        #print "AfpFinanceExport.export:", vname
        append =  Afp_ArrayfromLine(self.get_globals().get_value(vname + ".ADRESSE", "Finance"))
        Export.append_data(append)
        fieldlist =  Afp_ArrayfromLine(self.get_globals().get_value(vname, "Finance"))
        if not self.information:
            self.information = self.get_globals().get_value(vname + ".info", "Finance")
        Export.write_to_file(fieldlist, self.information)

## class holding sorted invoices
class AfpBulkInvoices(AfpOrderedList):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param index -if given, column where sorting should occur
    # @param filter - if given, filter for sorted data on database
    # @param debug - flag for debug information
    def  __init__(self, globals, filter = None, index = None, debug = False):
        if index is None: Index = "RechNr"
        AfpOrderedList.__init__(self, globals, "BulkInvoices", index, filter, debug)
        self.debug = debug
        self.new = False
        self.mainselection = "RECHNG"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)   
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        if self.debug: print "AfpBulkInvoices Konstruktor"
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpBulkInvoices Destruktor"
    ## get client object
    def get_client(self):
        row = 0
        if self.mainposition: row = self.mainposition
        value = self.get_value_row("RECHNG","RechNr", row)[0]
        client = AfpCommonInvoice(self.get_globals(), self.get_value_row("RECHNG","RechNr", row)[0])
        return client

## class holding sorted obligations
class AfpBulkObligations(AfpOrderedList):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param index -if given, column where sorting should occur
    # @param filter - if given, filter for sorted data on database
    # @param debug - flag for debug information
    def  __init__(self, globals, filter = None, index = None, debug = False):
        if index is None: Index = "RechNr"
        AfpOrderedList.__init__(self, globals, "BulkObligations", index, filter, debug)
        self.debug = debug
        self.new = False
        self.mainselection = "VERBIND"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)   
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        #print "AfpBulkObligations Konstruktor:", filter, self.selects, self.selections
        if self.debug: print "AfpBulkObligations Konstruktor"
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpBulkObligations Destruktor"
    ## get client object
    def get_client(self):
        row = 0
        if self.mainposition: row = self.mainposition
        value = self.get_value_row("VERBIND","RechNr", row)[0]
        client = AfpObligation(self.get_globals(), self.get_value_row("VERBIND","RechNr", row)[0])
        return client

