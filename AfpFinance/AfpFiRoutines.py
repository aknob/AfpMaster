#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFinance.AfpFiRoutines
# AfpFiRoutines module provides classes and routines needed for finance handling and accounting,\n
# no display and user interaction in this modul.
#
#   History: \n
#        27 Feb. 2019 - add SEPA direct debit handling - Andreas.Knoblauch@afptech.de \n
#        12 Nov. 2015 - add mysql-table define data - Andreas.Knoblauch@afptech.de \n
#        04 Feb. 2015 - add data export - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        14 Feb. 2014 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright© 1989 - 2019 afptech.de (Andreas Knoblauch)
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
from AfpBase import AfpBaseRoutines
from AfpBase.AfpBaseRoutines import *
from AfpBase import AfpAusgabe
from AfpBase.AfpAusgabe import AfpAusgabe

## class to handle SEPA direct debit handling, 
class AfpSEPADD(AfpSelectionList):
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
        self.selects["Konto"] = [ "ADRESATT","Attribut = \"Bankverbindung\" AND AttText = \"SEPA-DD\" AND KundenNr = " + data.get_string_value("KundenNr.ADRESSE")] 
        self.selects["Mandat"] = [ "ARCHIV","Art = \"SEPA-DD\" AND Typ = \"Aktiv\" AND Tab = \"" + self.ctable + "\""] 
        self.selects["Execution"] = [ "ARCHIV","Art = \"SEPA-DD\" AND Typ = \"Datei\" AND Tab = \"" + self.mainselection + "\""] 
        if self.debug: print "AfpSEPADD Konstruktor:", self.mainindex, self.mainvalue 
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpSEPADD Destruktor"
        
    ## set period from interval input
    def set_period(self):
        if self.interval > 1:
            month = self.today.month
            if self.interval == 12:
                self.period += "/" + Afp_toIntString(month, 2)
                self.actuel = month
            else:
                if self.interval == 2:
                    self.period += "/H" 
                elif self.interval == 4:
                    self.period += "/Q" 
                else:
                    self.period += "/" +  Afp_toString(self.interval) + "X"
                self.actuel = self.interval*(month-1)/12 + 1
                self.period += Afp_toString(self.actuel)
        print "AfpSEPADD.set_period:", self.interval, self.actuel, self.period
        
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
        print "AfpSEPADD.read_last_run:", rows
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
            if client.get_value(clientid) == EvNr:
                self.client_bic[row[0]] = row[3]
                self.client_iban[row[0]] = row[4]
                print "AfpSEPADD.gen_mandat_data amount:", row[2], client.get_value(self.datafields["regular"]), self.interval, self.datafields["regular"]
                amount = client.get_value(self.datafields["regular"])/self.interval
                first = not (self.lastrun and row[1] <=  self.lastrun)
                #print "AfpSEPADD.gen_mandat_data lastrun:", row[2], self.lastrun, row[1], first
                #print "AfpSEPADD.gen_mandat_data interval:", row[2], amount, first,self.is_first_in_year(), self.interval, self.actuel
                if first or self.is_first_in_year():
                    extra = client.get_value(self.datafields["extra"])
                    if first:
                        preis = client.get_value(self.datafields["total"])
                        preis = preis - (self.interval - self.actuel)*amount
                        if preis: amount = preis
                        else: amount += extra
                    else:
                        amount += extra                        
                #print "AfpSEPADD.gen_mandat_data amount:", row[2], amount
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
            if self.debug: print "AfpSEPADD.add_mandat_data copy file:", fname, "to",  fpath
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
            print "AfpSEPADD.add_mandat_data set mandat:", added, row
            self.get_selection("Mandat").set_data_values(added, row)
            if not self.newclients: self.newclients = [client]
            else: self.newclients.append(client)
        else:
            print "WARNING: SEPA mandat not all data supplied:", fname, datum, bic, iban
       
    ## generate SEPA Direct Debit XML-file from l data
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
        if self.debug: print "AfpSEPADD.gen_SEPA_xml:", self.serial, vars, source, target
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
        if self.debug: print "AfpSEPADD.gen_SEPA_xml Receipt:", self.serial, vars["Typ"], source, target
        rcpt = AfpAusgabe(self.debug, datalist, serial_tags)
        rcpt.set_variables(vars)
        rcpt.inflate(source)
        rcpt.write_resultfile(target, self.sourcedir + "empty.odt")
        return vars["MessageId"]
        
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
        master_data = {"Art":"SEPA-DD", "Typ":"Datei", "Gruppe": self.period}
        client_data = {"Art":"SEPA-DD", "Typ":"Einzug", "Gruppe": self.period, "Bem":"Beitrag"}
        if self.newclients_file:
            master_data["Bem"] = "Ersteinzug"
            master_data["Extern"] = self.newclients_file + ".xml"
            client_data["Extern"] = self.newclients_file + ".odt"
            self.data.add_to_Archiv(master_data)
            self.data.add_to_Archiv(dict(client_data))
            for client in self.newclients:
                # possibly add name of member, as sepa may be paid from other address
                client.add_to_Archiv(dict(client_data))
        if self.clients_file:
            master_data["Bem"] = "Folgeeinzug"
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
            if self.debug: print "AfpSEPADD.prepare_xml:", self.newclients, self.clients
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
            
    ## store all data
    def store(self):
        if self.has_changed():
            super(AfpSEPADD, self).store()
        self.data.store()
        if self.newclients:
            for client in self.newclients:
                client.store()
        if self.clients:
            for client in self.clients:
                client.store()
    
  ## class to handle finance depedencies, 
class AfpFinance(AfpSelectionList):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param debug - flag for debug information
    # @param Von - identifier of a certain incident
    # @param VorgangsNr - identifier of a certain action
    # @param BuchungsNr - identifier of a certain entry
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either Von, VorgangsNr or BuchungsNr has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, debug = False, Von = None, VorgangsNr = None, BuchungsNr = None,  complete = False):
        AfpSelectionList.__init__(self, globals, "BUCHUNG", debug)
        self.file = None
        self.transfer = None
        self.debug = debug
        if Von or VorgangsNr or BuchungsNr:     
            self.new = False
            if BuchungsNr:
                self.mainindex = "BuchungsNr"
                self.mainvalue = Afp_toString(BuchungsNr)
            elif VorgangsNr:
                self.mainindex = "VorgangsNr"
                self.mainvalue = Afp_toString(VorgangsNr)
            else:
                self.mainindex = "Von"
                self.mainvalue = Von
        else:
            # empty object to hold financial accounting data
            self.new = True
            self.mainindex = "VorgangsNr"
            self.mainvalue = ""
        self.mainselection = "BUCHUNG"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)
        self.selects["AUSZUG"] = [ "AUSZUG","Auszug = Beleg.BUCHUNG"] 
        self.selects["Konto"] = [ "KTNR","KtNr = Konto.BUCHUNG"] 
        self.selects["Gegenkonto"] = [ "KTNR","KtNr = Gegenkonto.BUCHUNG"] 
        if self.debug: print "AfpFinance Konstruktor:", self.mainindex, self.mainvalue 
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpFinance Destruktor"
        
## return financial transaction class, if possible
def AfpFi_getFinanceTransactions(globals):
    #print "AfpFi_getFinanceTransactions:", globals.get_mysql().get_tables()
    if "BUCHUNG" in globals.get_mysql().get_tables():
        return AfpFinanceTransactions(globals)
    else:
        return None
## class to sample all financial transaction entries needed for one action. \n
# central class for financial transactions of all kinds. \n
# this centralisation is considered to more usefull then following the object oriented approach.
class AfpFinanceTransactions(AfpSelectionList):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is mandatory
    # a new, clean object is created
    def  __init__(self, globals):
        AfpSelectionList.__init__(self, globals, "BUCHUNG", globals.is_debug())
        self.transfer = None
        # just empty object to hold financial accounting data
        self.new = True
        self.mainindex = "BuchungsNr"
        self.mainvalue = ""
        self.mainselection = "BUCHUNG"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)
        #self.selects["AUSZUG"] = [ "AUSZUG","Auszug = Beleg.BUCHUNG"] 
        self.selects["AUSZUG"] = [ "AUSZUG","Auszug = Reference.BUCHUNG"] 
        if self.debug: print "AfpFinanceTransactions Konstruktor:", self.mainindex, self.mainvalue 
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpFinanceTransactions Destruktor"
    ## check if identifier of statement of this account (Auszug) exists, if yes load it
    # @param auszug - identifier of statement of account
    def check_auszug(self, auszug):
        if not "/" in auszug:
            auszug += "/" + Afp_toString(self.globals.today().year)[-2:]
        if self.exists_selection("AUSZUG"): 
            #print "AfpFinanceTransactions.check_auszug exists:", auszug, type(auszug), self.get_value("Auszug.AUSZUG")
            if auszug == self.get_value("Auszug.AUSZUG"): return True
            self.delete_selection("AUSZUG")
        self.selects["AUSZUG"][1] = "Auszug = \"" + auszug + "\""
        #print "AfpFinanceTransactions.check_auszug create:", auszug, type(auszug), self.get_value("Auszug.AUSZUG")
        if auszug == self.get_value("Auszug.AUSZUG"): return True
        return False
    ## set identifier of statement of account (Auszug)
    # @param auszug - identifier of statement of account (xxnnn - xx identifier of bankaccount, nnn number)
    # @param datum, - date of statement of account 
    def set_auszug(self, auszug, datum):
        today = self.globals.today()
        if datum is None: datum = today
        if not "/" in auszug:
            auszug += "/" + Afp_toString(datum.year)[-2:]
        if auszug == self.get_value("Auszug.AUSZUG"): return
        ausname = Afp_getStartLetters(auszug) 
        if not ausname: return
        self.selects["Auszugkonto"] =  [ "KTNR","KtName = \"" + ausname.upper() + "\""] 
        self.create_selection("Auszugkonto", False)
        ktnr = self.get_value("KtNr.Auszugkonto")
        if ktnr is None: 
            print "WARNING: Account not found for ", auszug
            return
        self.set_value("Auszug.AUSZUG", auszug)
        self.set_value("BuchDat.AUSZUG", datum)
        self.set_value("Datum.AUSZUG", today)
        self.set_value("KtNr.AUSZUG", ktnr)
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
        print "AfpFinanceTransactions.store 0:",self.new, self.mainindex
        #self.view()
        AfpSelectionList.store(self)
        print "AfpFinanceTransactions.store 1:",self.new, self.mainindex 
        #self.view()
        if self.new:
            self.new = False
            VNr = self.get_value("BuchungsNr")
            print "VorgangsNr:", VNr
            changed_data = {"VorgangsNr": VNr}
            for i in range(0, self.get_value_length()):
                self.set_data_values(changed_data, None, i)
            print "AfpFinanceTransactions.store 2:",self.new, self.mainindex 
            for d in self.selections: print d,":", self.selections[d].data
            AfpSelectionList.store(self)
    ## set payment through indermediate account (payment has to be split)
    def set_payment_transfer(self):
        self.transfer = self.get_special_accounts("ZTF")
    ## add default values to payment data (if specific routines fail)
    # @param data - data dictionary to be modified, will be returned
    def add_payment_data_default(self, data):
        if not "Gegenkonto" in data:
            data["Gegenkonto"] = -1
        if not "Von" in data:
            data["Von"] = "AfpFinance: data not available"
        return data
    ## flip booking, add remark
    # @param data - data dictornary to be modified and returned
    # @param bem - remark to be added
    def set_storno_values(self, data, bem = "-STORNO-"):
        #data["Betrag"] = - data["Betrag"]
        Konto = data["Konto"]
        data["Konto"] = data["Gegenkonto"]
        data["Gegenkonto"] = Konto
        data["Bem"] = data["Bem"] + " " + bem
        return data
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
                von = data.get_identifier()
                acc = {"Datum": today,"Konto": konto, "Gegenkonto ": sgkt,"Beleg": beleg,"Betrag": skonto,"KtName": name ,"GktName": "SKTO","KundenNr": kdnr,"Bem":  sbem,"Von": von}
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
        print "AfpFinanceTransactions.add_payment:", payment, datum, auszug, KdNr, Name, data 
        if auszug: self.set_auszug(auszug, datum)
        accdata = {}
        accdata["Datum"] = datum
        accdata["Betrag"] = payment
        accdata["Beleg"] = auszug
        accdata["KundenNr"] = KdNr
        accdata["Art"] = "Zahlung"
        accdata["Eintrag"] = self.globals.today()
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
        if reverse: accdata = self.set_storno_values(accdata, "Auszahlung")
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
        # has to return the account number this payment has to be charged ("Gegenkonto"), the identifier ("Von")
        paymentdata["Von"] = data.get_identifier() 
        if data.get_listname() == "Charter":
            paymentdata = self.add_payment_data_charter(paymentdata, data)        
        elif data.get_listname() == "Rechnung":
            paymentdata = self.add_payment_data_rechnung(paymentdata, data)
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
                if not "Von" in acc: acc["Von"] = data.get_identifier()
                acc["Art"] = "Intern"
                acc["Eintrag"] = today
                if storno: acc = self.set_storno_values(acc)
                self.set_data_values(acc, None, -1)
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
            accdata["Von"] = data.get_identifier()  
            accdata["Beleg"] = "Intern"  
            accdata["Eintrag"] = today
            self.set_data_values(accdata, None, -1)
    ## Charter: deliver payment transaction data
    # @param paymentdata - payment data dictionary to be modified and returned
    # @param data - Charter data where relevant values have to be extracted
    def add_payment_data_charter(self, paymentdata, data):
        RNr = data.get_value("RechNr.Fahrten")
        if RNr: self.add_payment_data_rechnung(paymentdata, data)
        else: 
            paymentdata["Gegenkonto"] = Afp_getSpecialAccount(self.get_mysql(), "MFA")
            paymentdata["GktName"] = "MFA"
        return paymentdata   
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
    ## Rechnung (Invoice): deliver payment transaction data
    # @param paymentdata - payment data dictionary to be modified and returned
    # @param data - Rechnung data where relevant values have to be extracted
    def add_payment_data_rechnung(self, paymentdata, data):
        paymentdata["Gegenkonto"] = data.get_value("Debitor.RECHNG") 
        paymentdata["GktName"] = data.get_name(True, "RechAdresse") 
        print "AfpFinanceTransactions.add_payment_data_rechnung:",paymentdata
        if not paymentdata["Gegenkonto"]:
            paymentdata["Gegenkonto"]  = Afp_getIndividualAccount(self.get_mysql(), data.get_value("KundenNr"))
            paymentdata["GktName"] = data.get_name(True) 
            print "AfpFinanceTransactions.add_payment_data_rechnung fallback:", paymentdata
        return paymentdata 
    ## Rechnung (Invoice): deliver financial transaction data
    # @param data - Rechnung data where relevant values have to be extracted
    def add_transaction_data_rechnung(self, data):
        print "AfpFinanceTransactions.add_transaction_data_rechnung"
        accdata = []
        datum = data.get_value("Datum.RECHNG")
        preis =  data.get_value("RechBetrag.RECHNG")
        if Afp_isEps(preis):
            von =  data.get_identifier()
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
            acc = {"Datum": datum,"Konto": konto, "Gegenkonto": gkonto,"Beleg": beleg,"Betrag": preis,"KtName": name,"GktName": gktname,"KundenNr": kdnr,"Bem":  bem,"Von": von}
            accdata.append(acc)
            if gkonto2:
                acc = {"Datum": datum,"Konto": konto, "Gegenkonto ": gkonto2,"Beleg": beleg,"Betrag": preis,"KtName": name,"GktName": gkt2,"KundenNr": kdnr,"Bem":  bem,"Von": von}
                accdata.append(acc)
        return accdata
     
## class to export financial transactions
class AfpFinanceExport(AfpSelectionList):
    ## initialize class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param period - if given, [startdate, enddate] for data to be exported otherwise selectionlists must be given
    # @param selectionlists - if given and no period given, SelectionLists holdin the data to be exported
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

# database tables

## get dictionary with required database tables and mysql generation code
# @param flavour - if given flavour of modul
def AfpFinance_getSqlTables(flavour = None):
    required = {}
    return required
        