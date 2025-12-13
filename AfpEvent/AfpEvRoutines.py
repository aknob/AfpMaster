#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvRoutines
# AfpEvRoutines module provides classes and routines needed for event handling,\n
# no display and user interaction in this modul.
#
#   History: \n
#        16 Feb. 2025 - remove depricated routines - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        15 May 2018 - inital code generated - Andreas.Knoblauch@afptech.de \n

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
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_sortSimultan
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpSelectionLists import AfpSelectionList, AfpPaymentList, Afp_orderSelectionLists
from AfpBase.AfpBaseAdRoutines import AfpAdresse, AfpAdresse_getListOfTable

## returns all possible entries for kind of tours
def AfpEvClient_possibleEventKinds():
    #return ["Indi","Eigen","Fremd"]
    #return ["Eigen","Fremd"]
    #return ["Event","Reise","Eigen","Fremd"]
    return ["Event","Touristik"]
## returns if event is a club 
# @param art - kind of event
def AfpEvent_isVerein(art):
    #print ("AfpEvent_isVerein:", art, art == "Verein" or art == "Sparte")
    if art == "Verein" or art == "HauptSparte" or art == "Sparte":
        return True
    else:
        return False
## returns if event is a tour in the sense of the 'tourist' modul
# @param art - kind of event
def AfpEvent_isTour(art):
    if art == "Event":
        return False
    elif art == "Fremd" or art == "Eigen" or art == "Reise" or art == "Touristik":
        return True
    return False
## return 'Zustand' values where financial transaction are needed \n
# This is the definition routine for the above 'Zustand' values
def AfpEvent_getTransactionList():
    return ["Anmeldung"]
    
## extract all available client entries for given address indentifier
# @param globals - global values to be used
# @param knr - address identifier to be used
def AfpEvClient_getAnmeldListOfAdresse(globals, knr):
    rows = []
    raw_rows, name = AfpAdresse_getListOfTable(globals, knr, "ANMELD","Anmeldung,Info,Preis,AnmeldNr")
    #print "AfpEvClient_getAnmeldListOfAdresse raw_row:", raw_rows, name, knr
    if raw_rows:
        for entry in raw_rows:
            ANr = entry[-1]
            Anmeld = AfpEvClient(globals, ANr)
            row = Anmeld.get_value_rows("EVENT","Beginn,Ort")[0]
            row += entry
            #print "AfpEvClient_getAnmeldListOfAdresse row:", row
            rows.append(row)
    #print "AfpEvClient_getAnmeldListOfAdresse rows:", rows, name
    return rows, name  

## read all route names from table
# @param mysql - sql object to access datatable
def AfpEvClient_getRouteNames(mysql):
    rows = mysql.select("Name,TourNr","","TNAME","Name")
    namen = []
    idents = []
    for row in rows:
        namen.append(row[0])
        idents.append(row[1])
    return namen, idents
## read all route names from table
# @param mysql - sql object to access datatable
# @param route - identification number of route where locations should be extracted
def AfpEvClient_getLocations(mysql, route):
    knr = 100*route
    select = "KennNr >= " + Afp_toString(knr) + " AND KennNr < "  + Afp_toString(knr + 100)
    rows = mysql.select("KennNr",select,"TROUTE")
    namen = []
    kennungen = []
    for row in rows:
        select = "OrtsNr = " + Afp_toString(row[0])
        orte = mysql.select("Ort,Kennung",select,"TORT")
        namen.append(orte[0][0])
        idents.append(orte[0][1])
    return namen, kennungen
    
## check if vehicle is needed for this route
# @param mysql - sql object to access datatable
# @param route - identifier of route
def AfpEvClient_checkVehicle(mysql, route):
    bus = None
    if route:
        select = "TourNr = " + Afp_toString(route)
        rows = mysql.select("OhneBus",select,"TNAME")
        if rows:
            #print "AfpEvClient_checkVehicle", rows
            if Afp_fromString(rows[0][0]): 
                # OhneBus == 1
                bus = False
            else:
                # OhneBus = 0
                bus = True
    return bus
        
##  get the list of indecies of client table,
# @param mysql - database where values are retrieved from
# @param index  -  name sort criterium initially selected
# @param datei  -  name table to be used as primary
def AfpEvClient_getOrderlistOfTable(mysql, index, datei = "EVENT"):
    if index == "Kennung":
        liste = {'Beginn':'date', 'Kennung':'string','RechNr':'float'}
    else:
        liste = {'Beginn':'date', 'Ort':'string','RechNr':'float'}
    return liste

## baseclass for tour handling         
class AfpEvent(AfpSelectionList):
    ## initialize AfpEvent class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param EventNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either EventNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, EventNr = None, sb = None, debug = None, complete = False):
        AfpSelectionList.__init__(self, globals, "Event", debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.new = False
        self.maxPreisNr = 0
        self.mainindex = "EventNr"
        self.mainvalue = ""
        if sb:
            self.mainvalue = sb.get_string_value("EventNr.EVENT")
            Selection = sb.gen_selection("EVENT", "EventNr", debug)
            self.selections["EVENT"] = Selection
        else:
            if EventNr:
                self.mainvalue = Afp_toString(EventNr)
            else:
                self.new = True
        self.mainselection = "EVENT"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)   
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr = AgentNr.EVENT"] 
        self.selects["ANMELD"] = [ "ANMELD","EventNr = EventNr.EVENT","AnmeldNr"] 
        self.selects["PREISE"] = [ "PREISE","EventNr = EventNr.EVENT"] 
        self.selects["ERTRAG"] = [ "ERTRAG","FahrtNr = EventNr.EVENT"] 
        self.selects["EINSATZ"] = [ "EINSATZ","ReiseNr = EventNr.EVENT","EinsatzNr"] 
        self.selects["TNAME"] = [ "TNAME","TourNr = Route.EVENT","TourNr"] 
        self.selects["Ort"] = [ "ADRESSE","KundenNr = Route.EVENT"] 
        self.selects["ARCHIV"] = [ "ARCHIV","TabNr = EventNr.EVENT AND Tab = \"EVENT\""] 
        self.set_maxPreisNr()
        self.finance = None
        if complete: self.create_selections()
        if self.debug: print("AfpEvent Konstruktor, EventNr:", self.mainvalue)
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpEvent Destruktor")
    ## routine to set local pricenumbers before storing
    # overwritten from AfpSelectionList, needed 
    def store_preparation(self):
        self.set_maxPreisNr()
        self.complete_Preise()
        return
 
    ## clear current SelectionList to behave as a newly created List 
    # @param copy -  flag if a copy should be created or flags which data should be kept during creation of a copy
    # - True: a complete copy is created
    # - [0] == True: dates should be kept 
    # - [1] == True: agent or transfer route should be kept 
    # - [2] == True: prices should be kept 
    # - [3] == True: internal text should be kept 
    # - the rest of the data is kept if copy != [flag, flag, flag, flag]
    def set_new(self, copy = None):
        self.new = True
        data = {}
        keep = []
        if copy == True:
            keep_flag = [False, True, True, False]
        else:
            keep_flag = copy
        #print ("AfpEvent.set_new keep_flag:", keep_flag, copy)
        if keep_flag:
            if keep_flag[0]: # dates kept
                data["Beginn"] = self.get_value("Beginn") 
                data["Uhrzeit"] = self.get_value("Uhrzeit") 
                data["Ende"] = self.get_value("Ende") 
                data["ErloesKt"] = self.get_value("ErloesKt")
            if keep_flag[1]: # agent, transfer route kept
                data["AgentNr"] = self.get_value("AgentNr")
                data["Kreditor"] = self.get_value("Kreditor")
                data["Debitor"] = self.get_value("Debitor")
                data["AgentName"] = self.get_value("AgentName")
                data["Route"] = self.get_value("Route")
                keep.append("TNAME")
            if keep_flag[2] and "PREISE" in self.selections: # prices kept
                keep.append("PREISE")
                self.selections["PREISE"].new = True
                self.selections["PREISE"].spread_value("EventNr", None)
                self.selections["PREISE"].spread_value("Kennung", None)
                self.maxPreisNr = 0
            if keep_flag[3]: # internal text kept
                data["IntText"] = self.get_value("IntText")
            data["Art"] = self.get_value("Art")
            data["Kostenst"] = self.get_value("Kostenst") 
            data["Route"] = self.get_value("Route") 
            data["Personen"] = self.get_value("Personen") 
            data["Bem"] = self.get_value("Bem")
        data["RechNr"] = 0
        data["Anmeldungen"] = 0
        #print ("AfpEvent.set_new data:", data)
        #print ("AfpEvent.set_new keep:", keep, keep_flag, copy)
        self.clear_selections(keep)
        self.set_data_values(data,"EVENT")
    ## one line to hold all relevant values of this tour, to be displayed 
    def line(self):
        zeile =  self.get_string_value("Kennung").rjust(8) + "  "  + self.get_string_value("Art") + " " +  self.get_string_value("AgentName") + " " + self.get_string_value("Beginn") + " " + self.get_string_value("Ort")  
        return zeile
    ## internal routine to set the  filter on ANMELD selection
    # @param values - list of filter values to be applied on selection
    def set_anmeld_filter(self, values = None):
        filter = "EventNr = EventNr.EVENT"
        if values:
            inner = ""
            for val in values:
                if "=" in val or">" in val or "<" in val:
                    filter += " AND " + val
                else:
                    inner += " OR Zustand = \"" + val + "\""
            filter += " AND (" + inner[4:] + ")"
        #print "AfpEvent.set_anmeld_filter:", filter
        self.selects["ANMELD"] = [ "ANMELD",filter,"AnmeldNr"] 
    ## internal routine to set the appropriate agency name
    def set_agent_name(self):
        #name = self.get_name(False,"Kontakt") + " " + self.get_string_value("KontaktNr")
        name = self.get_name(False,"Agent")
        self.set_value("AgentName",name)
    ## decide whether this event a self organised tour
    def is_own_tour(self):
        if self.is_tour():
            if not self.get_value("AgentNr"):
                return True
        return False
   ## decide whether this event a tour
    # @param art - if given, art to be checked
    def is_tour(self, art = None):
        if not art:
            art = self.get_value("Art")
        return AfpEvent_isTour(art)
    ## decide whether this event may last over different days
    # @param art - if given, art to be checked
    def is_multidays(self, art = None):
         return self.is_tour(art)
    ## decide whether this event may holds a route insted of the location
    # at the moment the same as 'is_multidays'
    def has_route(self):
        return self.is_tour()
    ## set highest used pricenumber
    def set_maxPreisNr(self):
        sel = self.get_selection("PREISE")
        if sel:
            for i in range(sel.get_data_length()):
                PNr = sel.get_values("PreisNr", i)[0][0] 
                if PNr and PNr > self.maxPreisNr:
                    self.maxPreisNr = PNr
    ## complete price entries in case new prices have been added
    def complete_Preise(self):
        ENr = self.get_value("EventNr")
        sel = self.get_selection("PREISE")
        #print "AfpEvent.complete_Preise:", self.maxPreisNr, sel.get_data_length()
        for i in range(sel.get_data_length()):
            if not sel.get_values("PreisNr", i)[0][0]: # if PreisNr is not yet set
                self.maxPreisNr += 1
                sel.set_value("PreisNr", self.maxPreisNr, i)
            if ENr and not sel.get_values("EventNr", i)[0][0]: # if EventNr is not yet set
                sel.set_value("EventNr", ENr, i)
    ## clear all infos
    # @param text - if given text indicating info to be cleared
    def clear_all_infos(self, text = None):
        texte = self.get_value_rows("ANMELD", "Info")
        Anmeld = self.get_selection("ANMELD")
        store = False
        for i in range(len(texte)):
            if texte[i][0] == text:
                Anmeld.set_value("Info", "", i)
                store = True
        #print ("AfpEvent.clear_all_infos store:", text, store, texte)
        if store: Anmeld.store()
        
    ## get all clients
    # @param check_preis - flag if only paying clients should be collected, default: True
    # @param is_cancel - flag which clients should be collected, default: False
    # - None: all clients are collected
    # - True: canceled clients are collected
    # - False: active clienst are collected
    # @param sorttyp - if given, field to sort output
    # @param sortdef - if given, default value of field sorttyp to be set instead of 'None' values
    def get_clients(self, check_preis = True, is_cancel = False, sorttyp = None, sortdef = None):
        clients = []
        rows = self.get_value_rows("ANMELD","AnmeldNr")
        for row in rows:
            client = self.get_client(row[0])
            #print "AfpEvent.get_clients:", client.get_name(), client.is_canceled(), is_cancel, client.get_value("Zustand") 
            if (not check_preis or client.get_value("Preis")) and (is_cancel is None or is_cancel == client.is_canceled()): 
                #print "AfpEvent.get_clients:", client.get_name(), client.is_canceled(), is_cancel, client.get_value("Zustand"), client.get_value("Preis") 
                clients.append(client)
        if sorttyp:
            clients = Afp_orderSelectionLists(clients, sorttyp, sortdef)
        return clients
        
    # may be overwritten in devired class
            
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        if self.is_tour():
            return "Reise am "  +  self.get_string_value("Beginn") + " nach " + self.get_string_value("Bez")
        else:
            return "Veranstaltung (" +  self.get_string_value("Bez") + ") am "  +  self.get_string_value("Beginn") + " in " + self.get_string_value("Name.Ort")
    ## create client data
    # @param ANr - if given, data will be retrieved for this database entry
    def get_client(self, ANr = None):
        return AfpEvClient(self.globals, ANr)
    ## generate invoice number
    # @param Nr - if given, this counter will be used to generate RechNr-string
    def generate_RechNr(self, Nr=None):
        RechNr = None
        if self.get_value("AgentNr.EVENT"):
            Extern = AfpExternNr(self.get_globals(),"Month", None, self.debug)
            RechNr = Extern.get_number_string()
        else: 
            if Nr is None:
                #self.lock_data("EVENT")
                self.lock_data()
                Nr = self.get_value("RechNr") + 1
                self.set_value("RechNr", Nr)
            deci = self.globals.get_value("decimals-in-rechnr","Event")
            if not deci: deci = 2
            div = 10**deci
            while Nr/div > 0:  div*10
            RNr = float(Nr)/div
            RNr += self.get_value("Kostenst.EVENT")
            print("AfpEvClient.generate_RechNr RNr:", Kst, Nr, RNr)
            RechNr = Afp_toString(RNr)
        #elif typ == "Nummer.ExternNr":
            #Extern = AfpExternNr(self.get_globals(),"Month", None, self.debug)
            #RechNr = Extern.get_number_string()
        #else:
            #client.add_invoice()
            #RechNr will be set automatically after storing and has not to be returned here 
        return RechNr
    ## add clients to event-counter
    #@param cnt - number of clients to be added to counter, use negative value for removal
    def add_client_count(self, cnt = 1):
        self.set_value("Anmeldungen", self.get_value("Anmeldungen") + cnt) 
    ## add client to event
    #@param data - data to be completed by event dependent values
    def add_client(self, data):
        #print "AfpEvent.add_client:", data
        #self.lock_data("EVENT")
        self.lock_data()
        if not "RechNr" in data:
            if "IdNr" in data: IdNr = data["IdNr"]
            else: IdNr = None 
            #print "AfpEvent.add_client IdNr:", IdNr
            data["RechNr"]  = self.generate_RechNr(IdNr)
        self.add_client_count()
        return data

## baseclass for client handling         
class AfpEvClient(AfpPaymentList):
    ## initialize AfpEvClient class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param AnmeldNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either AnmeldNr or sb (superbase) has to be given for initialisation,otherwise a new, clean object is created
    def  __init__(self, globals, AnmeldNr = None, sb = None, debug = None, complete = False):
        AfpPaymentList.__init__(self, globals, "Client", debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.finance_modul = None
        self.bulk_data_set = False
        self.mainindex = "AnmeldNr"
        self.mainvalue = ""
        if sb:
            if self.debug: print("AfpEvClient Konstruktor, EventNr:", sb.get_value("EventNr.EVENT"), sb.get_value("EventNr.ANMELD"), sb.get_string_value("AnmeldNr.ANMELD"))
            #if  sb.get_value("EventNr.ANMELD") and sb.get_value("EventNr.EVENT") == sb.get_value("EventNr.ANMELD"):
            if  sb.get_value("EventNr.ANMELD"):
                self.mainvalue = sb.get_string_value("AnmeldNr.ANMELD")
                Selection = sb.gen_selection("ANMELD", "AnmeldNr", debug)
            else:
                self.new = True
                Selection = AfpSQLTableSelection(self.mysql, "ANMELD", self.debug, "AnmeldNr")
            self.selections["ANMELD"] = Selection
        else:
            if AnmeldNr:
                self.mainvalue = Afp_toString(AnmeldNr)
            else:
                self.new = True
        self.mainselection = "ANMELD"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)   
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["ADRESSE"] = [ "ADRESSE","KundenNr = KundenNr.ANMELD"] 
        self.selects["EVENT"] = [ "EVENT","EventNr = EventNr.ANMELD"] 
        self.selects["PREISE"] = [ "PREISE","EventNr = EventNr.ANMELD"] 
        self.selects["ANMELDER"] = [ "ANMELDER","AnmeldNr = AnmeldNr.ANMELD"] 
        self.selects["ANMELDEX"] = [ "ANMELDEX","AnmeldNr = AnmeldNr.ANMELD"] 
        self.selects["RECHNG"] = [ "RECHNG","RechNr = RechNr.ANMELD","RechNr"]
        self.selects["AUSGABE"] = [ "AUSGABE","Modul = \"Event\" AND Art = Art.EVENT AND Typ = Zustand.ANMELD"] 
        #self.selects["AUSGABE"] = [ "AUSGABE","Typ = Art.EVENT + Zustand.ANMELD"] 
        #self.selects["AUSGABE"] = [ "AUSGABE","Typ = \"EigenAnmeldung\""] 
        self.selects["RechNr"] = [ "ANMELD","RechNr = RechNr.ANMELD"] 
        self.selects["Agent"] = [ "ADRESSE","KundenNr = AgentNr.ANMELD"] 
        self.selects["Veranstalter"] = [ "ADRESSE","KundenNr = AgentNr.EVENT"] 
        #self.selects["ExtraPreis"] = [ "PREISE","!EventNr = 0"] 
        self.selects["ExtraPreis"] = [ "PREISE","EventNr = EventNr.ANMELD OR EventNr = 0"] 
        self.selects["Preis"] = [ "PREISE","EventNr = EventNr.ANMELD AND PreisNr = PreisNr.ANMELD"] 
        self.selects["Umbuchung"] = [ "EVENT","EventNr = UmbAuf.ANMELD"] 
        self.selects["Ort"] = [ "ADRESSE","KundenNr = Route.ANMELD"] 
        self.selects["ARCHIV"] = [ "ARCHIV","TabNr = AnmeldNr.ANMELD AND Tab = \"ANMELD\""] 
        # allow SEPA direct debit for the clients (moved in EvMember)
        #self.selects["SEPA"] = [ "ARCHIV","TabNr = AnmeldNr.ANMELD AND Tab = \"ANMELD\" AND Art = \"SEPA-DD\" AND Typ = \"Aktiv\""] 
        #self.selects["ERTRAG"] = [ "ERTRAG","EventNr = EventNr.ANMELD"] 
        if complete: self.create_selections()
        if not self.globals.skip_accounting():
            self.finance_modul = Afp_importAfpModul("Finance", self.globals)[0]
            if self.finance_modul:
                self.finance = self.finance_modul.AfpFinanceTransactions(self.globals)
        #print "AfpEvClient.finance:", self.finance
        # set payment related data
        payment_values = {"payer":"AgentNr,KundenNr", "account":"ErloesKt.EVENT"}
        self.set_payment_data(payment_values)
        if self.debug: print("AfpEvClient Konstruktor, AnmeldNr:", self.mainvalue)
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpEvClient Destruktor")
        #AfpSelectionList.__del__(self) 
    ## decide whether payment is possible or not
    def is_payable(self):
        zustand = self.get_string_value("Zustand")
        if zustand == "Anfrage": return False
        return True
    ## client will be tracked with financial transaction (accounted)
    def is_accountable(self):
        zustand = self.get_string_value("Zustand")
        if zustand == "Anfrage": return False
        return True
    ## client is connected to a separate invoice which has to be syncronised
    def is_invoice_connected(self):
        #return self.get_RechNr_name_depricated() == "RechNr.RECHNG"
        return False
    ## bulk data has been set
    def has_bulk_set(self):
        return self.bulk_data_set
    ## event is a tourists tour
    def event_is_tour(self):
        art = self.get_value("Art.EVENT")
        return AfpEvent_isTour(art)
    ## event is a club (Verein) entry
    def event_is_Verein(self):
        art = self.get_value("Art.EVENT")
        return AfpEvent_isVerein(art)
    ## event has valid route data
    def event_has_route(self):
        return self.event_is_tour() or self.event_is_Verein()
    ## clear current SelectionList to behave as a newly created List 
    # @param EventNr - identifier of event, == None if event is kept
    # @param KundenNr - KundenNr of newly selected adress, == None if address is kept
    # @param keep_flag -  flags which data should be kept while creation this copy
    # - [0] == True: same invoice number used 
    # - [1] == True: agent should be kept 
    # - [2] == True: prices and Anmeldex should be kept 
    # - [3] == True: the rest of the data should be kept 
    def set_new(self, EventNr, KundenNr = None, keep_flag = None):
        self.new = True
        data = {}
        keep = []
        if keep_flag == True:
            keep_flag = [True, True, True, True]
        if EventNr:
            data["EventNr"] = EventNr
            data["PreisNr"] = 100*EventNr + 1
        else:
            data["EventNr"] = self.get_value("EventNr.EVENT")
            keep.append("EVENT")
            keep.append("PREISE")
            keep.append("ExtraPreis")
        if KundenNr:
            data["KundenNr"] = KundenNr
        else:
            data["KundenNr"] = self.get_value("KundenNr")
            keep.append("ADRESSE")
        if keep_flag:
            if keep_flag[0]: # invoice number kept
                data["RechNr"] = self.get_value("RechNr") 
                keep.append("RechNr")
            if keep_flag[1]: # agent kept
                data["AgentNr"] = self.get_value("AgentNr")
                data["AgentName"] = self.get_value("AgentName")
                keep.append("Agent")
            if keep_flag[2] and "ANMELDEX" in self.selections: # Anmeldex kept
                keep.append("ANMELDEX")
                self.selections["ANMELDEX"].new = True
                keep.append("Preis")
                data["Extra"] = self.get_value("Extra") 
                data["PreisNr"] = self.get_value("PreisNr") 
                data["Preis"] = self.get_value("Preis") 
                data["Transfer"] = self.get_value("Transfer") 
                data["ProvPreis"] = self.get_value("ProvPreis") 
            if keep_flag[3]: # data kept
                data["Ab"] = self.get_value("Ab") 
                keep.append("TORT")
                data["Bem"] = self.get_value("Bem") 
                data["Info"] = self.get_value("Info") 
                data["ExText"] = self.get_value("ExText") 
                data["Zustand"] = self.get_value("Zustand") 
        data["Zustand"] = AfpEvent_getTransactionList()[0]
        data["Anmeldung"] = self.globals.today()
        #print "AfpEvClient.set_new data:", data, EventNr, KundenNr
        #print "AfpEvClient.set_new keep:", keep
        self.clear_selections(keep)
        self.set_data_values(data,"ANMELD")
        if keep_flag:
            if keep_flag[2]:
                self.spread_mainvalue()
        if EventNr:
            self.create_selection("EVENT", False)
            self.create_selection("PREISE", False)
            self.create_selection("ExtraPreis", False)
        if KundenNr:
            self.create_selection("ADRESSE", False)
        if not self.get_value("Preis"):
            preis, preisnr = self.get_basic_price()
            self.set_value("Preis", preis)
            self.set_value("PreisNr", preisnr)
            self.create_selection("Preis", False)
            self.add_optional_prices()
    ## store complete SelectionList
    # overwritten from SelectionList to handle bulk-data storage
    def store(self):
        #print "AfpEvClient.store:", self.bulk_data_set, "RechNr" in self.selections
        #if self.bulk_data_set and "RechNr" in self.selections:
        if "RechNr" in self.selections:
            # delete row in 'RechNr' SelectionList to avoid double storage of actuel tablerow
            # simple implementaion, never use 'RechNr' SelectionList for storage
            self.delete_selection("RechNr")
        super(AfpEvClient, self).store()
    ## extract basic price, 
    # default: return first basic price
    # may be overwirtten in devired class
    def get_basic_price(self):
        liste = self.get_value_rows("PREISE","Preis,PreisNr,Typ")
        #print ("AfpEvClient.get_basic_price:", liste)
        for entry in liste:
            if entry[2] == "Grund":
                return entry[0], entry[1]
        return None, None
    ## extract bulk price, 
    #@param initial - flag if initial bulk price is catched or normal bulk price
    # may be overwirtten in devired class 
    def get_bulk_price(self, initial = False):
        return self.get_basic_price()
    ## optionally add extra prices depending of data
    # may be overwritten in devired class, if necessary
    def add_optional_prices(self):
        return
    ## add bulk data to new SelectionList
    # @param ids - list of ids to be added 
    def add_new_bulk_ids(self, ids):
        if ids and self.new:
            self.bulk_data_set = True
            preis, pnr = self.get_bulk_price(True)
            self.set_value("Preis", preis)
            self.set_value("ProvPreis", preis)
            self.set_value("PreisNr", pnr)
            self.set_value("Zahlung", 0.0)
            self.delete_selection("Preis")
            row = self.get_value_rows("ANMELD")[0]
            RechNr = self.get_selection("RechNr")
            index = RechNr.get_data_length() - 1
            if index < 0: index = None
            RechNr.insert_row(index, row)
            index = RechNr.get_data_length() - 1
            preis, pnr = self.get_bulk_price()
            data = {"EventNr":self.get_value("EventNr"), "Zustand":self.get_value("Zustand"), "Anmeldung":self.get_value("Anmeldung"), "Preis":preis, "PreisNr":pnr, "ProvPreis":preis, "Zahlung":0.0}
            for id in ids:
                data["KundenNr"] = id
                RechNr.set_data_values(data, index)
                index += 1
        #print("AfpEvClient.add_new_bulk_ids:", self.bulk_data_set, ids, RechNr.data)
    ## add extra prices to registration
    #@param name - name of price to be added
    #@param appendix - if given, text to be appended to name
    def  add_extra_price(self, pname, appendix = None):
        print ("AfpEvClient.add_extra_price:", pname, appendix, type(appendix))
        if appendix:
            text = pname + " (" + appendix + ")"
        else:
            text = pname
        datas = self.get_value_rows("PREISE")
        nr = None
        preis = None
        for data in datas:
            #print ("AfpEvClient.add_extra_price:", Afp_toString(data[2]) , pname, Afp_toString(data[2]) == pname)           
            if Afp_toString(data[2]) == pname:
                nr = data[1]
                preis = data[5]
                break
        #print ("AfpEvClient.add_extra_price:", self.get_name(), nr, preis, pname, "TEXT:", text) 
        if nr:
            sel = self.get_selection("ANMELDEX")
            rows = sel.get_values()
            add = True
            for row in rows:
                if Afp_toString(row[2]) == text:
                    add = False
                    break
            if add:
                changed_data = {"Preis": preis, "Bezeichnung": text, "NoPrv": 1}
                ANr = self.get_value()
                if ANr: changed_data["AnmeldNr"] = ANr
                sel.add_data_values(changed_data)
 
    ## update internal price fields
    def update_prices(self):
        price = self.get_value("Preis.Preis")
        if not price: price = 0.0
        extra = 0.0
        noprv = 0.0
        rows = self.get_value_rows("ANMELDEX","NoPrv,Preis")
        #print ("AfpEvClient.update_prices:", price, rows)
        for row in rows:
            extra += row[1]
            if row[0]: noprv += row[1]
            #print ("AfpEvClient.update_prices:", extra, noprv, row[1])
        self.set_value("Extra", extra)
        self.set_value("Preis", extra + price)
        self.set_value("ProvPreis", extra + price - noprv)
    ## generate Event object for this client
    def get_event(self):
        ENr = self.get_value("EventNr.EVENT")
        return AfpEvent(self.get_globals(), ENr)
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
            original = AfpEvClient(self.globals, self.mainvalue)
            self.finance.add_financial_transactions(original, True)
    ## a separate invoice is created and filled with the appropriate values
    def add_invoice(self):
        if self.debug: print("AfpEvClient.add_invoice")
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
        data["RechBetrag"] = betrag
        data["Kontierung"] = Afp_getSpecialAccount(self.get_mysql(), "ERL")
        data["Zustand"] = "open"
        if self.event_is_tour:
            data["Wofuer"] = "Reiseanmeldung Nr " + self.get_string_value("AnmeldNr") + " am " + self.get_string_value("Beginn.EVENT") + " nach " + self.get_string_value("Bez.EVENT")
        else:
            data["Wofuer"] = "Veranstaltungsanmeldung Nr " + self.get_string_value("AnmeldNr") + " für " + self.get_string_value("Bez.EVENT") + " am " + self.get_string_value("Beginn.EVENT") 
        if self.get_value("ZahlDat"):
            data["Zahlung"] = self.get_value("Zahlung")
            data["ZahlDat"] = self.get_value("ZahlDat")
            if data["Zahlung"] >= betrag: data["Zustand"] = "closed"
        invoice.new_data()
        invoice.set_data_values(data)
        self.selections["RECHNG"] = invoice
    ## routine to hold separate invoice syncron to the actuel client values
    def syncronise_invoice(self):
        if self.debug: print("AfpEvClient.syncronise_invoice")
        betrag = self.get_value("Preis")
        data = {}
        data["Zahlbetrag"] = betrag
        #betrag2 = self.extract_taxfree_portion()
        #if betrag2:
            #betrag -= betrag2
            #data["Betrag2"] = betrag
        data["RechBetrag"] = betrag
        if self.get_value("ZahlDat"):
            data["Zahlung"] = self.get_value("Zahlung")
            data["ZahlDat"] = self.get_value("ZahlDat")
        #print "AfpEvClient.syncronise_invoice data:", data
        self.set_data_values(data, "RECHNG")
    ## one line to hold all relevant values of client, to be displayed 
    def line(self):
        zeile =  self.get_string_value("RechNr").rjust(8) + " " +  self.get_string_value("Anmeldung") + "  "  + self.get_name().rjust(35) 
        if self.event_has_route():
             zeile += " " + self.get_string_value("Kennung.TORT")  
        zeile += " " + self.get_string_value("Preis").rjust(10) + " " +self.get_string_value("Zahlung").rjust(10) 
        return zeile
    ## internal routine to set the appropriate agency name
    def set_agent_name(self):
        #name = self.get_name(False,"Kontakt") + " " + self.get_string_value("KontaktNr")
        name = self.get_name(False,"Agent")
        self.set_value("AgentName",name)
    ## get list of client entries having the same 'RechNr' (invoice number) \n
    # to be used in different dialogs
    def get_sameRechNr(self):
        rows = self.get_value_rows("RechNr", "RechNr,Preis,Zahlung,KundenNr,AnmeldNr,EventNr")
        ENr = self.get_value("EventNr")
        ANr = self.get_value("AnmeldNr")
        liste = [None]
        sameRechNr = [None]
        preis = 0.0
        zahlung = 0.0
        #print ("AfpEvClient.get_sameRechNr:", rows)
        for row in rows:
            if row[5] == ENr:
                if row[1]: preis += row[1]
                if row[2]: zahlung += row[2]
                if (row[1] and liste[0] is None) or len(rows) == 1:
                    liste[0] = self.get_sameRechLine(row[0], row[1], row[2], row[3])
                    sameRechNr[0] = row[4]  
                else:
                    liste.append(self.get_sameRechLine(row[0], row[1], row[2], row[3]))
                    sameRechNr.append(row[4])  
        if sameRechNr[0] is None:
            for i in range(len(sameRechNr)): 
                if sameRechNr[i] == ANr:
                    sameRechNr[0] = sameRechNr.pop(i)
                    liste[0] = liste.pop(i)
                    break
        #print ("AfpEvClient.get_sameRechNr Liste2:", liste, sameRechNr)
        return [preis, zahlung], sameRechNr, liste
    ## get one line of client entries having the same 'RechNr' (invoice number) \n
    # @param RNr - invoice number
    # @param preis - price to be payed
    # @param zahl - payment already made
    # @param KNr - address identifier to generate name
    def get_sameRechLine(self, RNr, preis, zahl, KNr):
        name = AfpAdresse(self.get_globals(), KNr).get_name()
        return Afp_toString(RNr) + Afp_toFloatString(preis).rjust(10) + Afp_toFloatString(zahl).rjust(10) + "  " + name
    ## scale the splitting values to given amount
    # @param amount - value to which splitting values should be scaled
    # @param splitting - list of rows, holding splitting values with the value at position [1]
    def scale_splitting(self, amount, splitting):
        sum = 0.0
        for row in splitting:
            sum += row[1]
        csum = 0.0
        for row in splitting:
            value = amount*(row[1]/sum)
            row[1] = float(int(value*100)/100)
            csum += row[1]
        if not csum == amount:
            splitting[0][1] += amount - csum
        return splitting
    #
    #  overwritten from SelectionList
    #
    ## get splitting values for payment
    # @param amount- if given: amount to be splitted pro rata
    def get_splitting_values(self, amount = None):
        splitting = None
        #print "AfpEvClient.get_splitting_values:", self.get_name(), self.get_value("Extra")
        if self.get_value("Extra"):
            rows = self.get_value_rows("ANMELDEX", "Bezeichnung,Preis")
            if rows:
                splitting = [None]
                sum = 0.0
                for row in rows: 
                    #print "AfpEvClient.get_splitting_values row:", row
                    KtNr = Afp_getSpecialAccount(self.get_mysql(), row[0], "Bezeichnung")
                    if not KtNr: 
                        if " " in row[0]:
                            KtNr = Afp_getSpecialAccount(self.get_mysql(), Afp_getWords(Afp_toString(row[0]))[0], "Bezeichnung")
                        else:
                            KtNr = Afp_getSpecialAccount(self.get_mysql(), "Gebühr " + Afp_toString(row[0]), "Bezeichnung")
                    if KtNr:
                        splitting.append([KtNr, row[1], row[0]])
                        sum += row[1]
                if len(splitting) > 1: 
                    if self.get_value("Extra") != sum:
                        #splitting[0] = [Afp_fromString(self.get_value("ErloesKt.EVENT")), self.get_value("Preis") - sum, ""]
                        splitting[0] = [self.get_account(), self.get_value("Preis") - sum, ""]
                    else:
                        splitting.pop(0)
                else:
                    splitting = None
        if amount and splitting:
            splitting = self.scale_splitting(amount, splitting)
        print ("AfpEvClient.get_splitting_values sum:", splitting) 
        return splitting
    ## set all necessary values to keep track of the payments
    # @param payment - amount that has been payed
    # @param datum - date when last payment has been made
    def set_payment_values(self, payment, datum):
        super(AfpEvClient, self).set_payment_values(payment, datum)
        if self.is_invoice_connected():
            self.set_value("Zahlung.RECHNG", payment)
            self.set_value("ZahlDat.RECHNG", datum)
    ## extract payment relevant data from SelectionList for 'Finance' modul, overwritten from AfpPaymentList
    # has to return the account number this payment has to be charged ("Gegenkonto")
    # @param paymentdata - payment data dictionary to be modified and returned
    def add_payment_data(self, paymentdata):
        paymentdata["Gegenkonto"] = self.get_account()
        paymentdata["GktName"] = self.get_value("AgentName.EVENT")
        #print "AfpEvent.add_payment_data:", paymentdata
        return paymentdata
    ## return the translated listname to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_listname_translation(self):
        return "Kunde"
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Anmeldung für die Veranstaltung '" +  self.get_string_value("Bez.EVENT") + "' am "  +  self.get_string_value("Beginn.EVENT") + " in " + self.get_string_value("Name.Ort")

## baseclass for departure route handling  \n
# not yet implemented completely, actually only used to retrieve route data!
class AfpEvRoute(AfpSelectionList):
    ## initialize AfpEvRoute class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param RouteNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either RouteNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, RouteNr = None, sb = None, debug = None, complete = False):
        AfpSelectionList.__init__(self, globals, "Route", debug)
        if debug: self.debug = debug
        else: self.debug = globals.is_debug()
        self.new = False
        self.mainindex = "TourNr"
        self.mainvalue = ""
        self.kennnr = None
        self.feldnamen_route = None
        self.feldnamen_orte = None
        self.spezial_orte = []
        self.free_text = " - anderen Ort auswählen - "
        self.new_text = " - neuen Ort eingeben - "
        self.raste_text = "Raststätten"
        self.new_location = None
        self.new_route_index = None
        if sb:
            self.mainvalue = sb.get_string_value("TourNr.TNAME")
            Selection = sb.gen_selection("TNAME", "TourNr", debug)
            self.selections["TNAME"] = Selection
        else:
            if RouteNr:
                self.mainvalue = Afp_toString(RouteNr)
            else:
                self.new = True
        if self.mainvalue:
            self.kennnr = 1000*Afp_fromString(self.mainvalue)
        self.mainselection = "TNAME"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)   
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["Route"] = [] 
        self.selects["Orte"] = [] 
        if complete: self.create_selections()
        if self.debug: print("AfpEvRoute Konstruktor, TourNr:", self.mainvalue)
    ## destuctor
    def __del__(self):    
        if self.debug: print("AfpEvRoute Destruktor")
        #AfpSelectionList.__del__(self) 
    ## special selection (overwritten from AfpSelectionList) \n
    # to handle the selection 'Orte'  which holds all attached location data of all departure points
    # @param selname - name of selection (in our case 'Orte' is implemented)
    # @param new - flag if a new empty list has to be created
    def spezial_selection(self, selname, new = False):
        LocSelection = None
        #print "AfpEvRoute.sepzial_selection:", selname, new
        if selname == "Route":
            if new:
                 LocSelection = AfpSQLTableSelection(self.mysql, "TROUTE", self.debug) 
                 LocSelection.new_data()
            else: 
                LocSelection = AfpSQLTableSelection(self.mysql, "TROUTE", self.debug) 
                select = "KennNr >= " + Afp_toString(self.kennnr) + " AND KennNr < " + Afp_toString(self.kennnr + 1000)
                LocSelection.load_data(select)
            self.feldnamen_route = LocSelection.get_feldnamen()
        elif selname == "Orte":
            if new:
                 LocSelection = AfpSQLTableSelection(self.mysql, "TORT", self.debug) 
                 LocSelection.new_data()
            else: 
                LocSelection = AfpSQLTableSelection(self.mysql, "TORT", self.debug) 
                data = []
                kenns = self.get_selection("Route").get_values("KennNr")
                for ken in kenns:
                    ort = ken[0] - int(ken[0]/1000)*1000
                    row = self.mysql.select("*","OrtsNr = " + Afp_toString(ort), "TORT")
                    if row: 
                        #print  "AfpEvRoute.sepzial_selection row:", ort, row
                        data.append(row[0])
                        self.spezial_orte.append(ort)
                    LocSelection.set_data(data)
            self.feldnamen_orte = LocSelection.get_feldnamen()
        return LocSelection
    ## special save (overwritten from AfpSelectionList) \n
    # store the special selection 'Bez'
    # @param selname - name of selection (in our case 'Route' is implemented)
    def spezial_save(self, selname):
        if selname == "Route": 
            route = self.get_selection("Route")
            if route.has_changed():
                route.store()
        elif selname == "Orte":
            if self.new_location:
                if self.new_location.get_value("OrtsNr") is None:
                    self.new_location.store()
                    if not self.new_route_index is None:
                        ortsnr = self.new_location.get_value("OrtsNr")
                        self.get_selection("Route").set_value("KennNr", self.gen_ident(ortsnr), self.new_route_index)
    ## retrieve spezial text
    # @param  typ - typ of text to be retrieved
    def get_spezial_text(self, typ = None):
        if typ is None or typ == "new":
            text = self.new_text
        elif typ == "free":
            text = self.free_text
        elif typ == "raste":
            text = self.raste_text
        else:
             text = None
        return text
    ## look if locations with given 'Kennung' are available
    # @param ken - if given only location having this 'Kennung' are selected (used for rest-point 'RA')
    def location_available(self, ken = None):
        if ken:
            available = False
            rows = self.get_selection("Orte").get_values("Kennung")
            for row in rows:
                if ken in row: available = True
            return available
        else:
            return self.get_selection("Orte").get_data_length() >= 1
    ## get all locations referred by route sorted alphabethically
    # @param typ -  see get_location_list
    # @param add - see get_location_list
    def get_sorted_location_list(self, typ = None, add = False):
        values, idents = self.get_location_list(typ, add)
        return Afp_sortSimultan(values, idents)    
    ## get all locations referred by route
    # @param typ -  the following locations are delivered:
    # - typ = None: all route locations 
    # - typ = 'routeOnlyRaste': all route rest-points
    # - typ = 'routeNoRaste': all route locations without rest-points, 
    # one common 'Raststätten' entry for the key -10, if a rest-point is available in this route
    # - typ = 'all': all locations in the database
    # - typ = 'allNoRoute': all locations in the database, which do not belong to this route
    # @param add - will add additonal text output list
    # - typ = 'routeNoRaste': text for free location selection for key -12
    # - typ = 'all...': text for new location entry for key -11
    def get_location_list(self, typ = None, add = False):
        if typ is None:
            ortsdict = self.get_all_locations()
        elif typ == "routeOnlyRaste":
            ortsdict = self.get_all_locations('RA') 
        elif typ == "routeNoRaste":
            ortsdict = self.get_all_locations('RA', True) 
            if self.location_available('RA'): 
                ortsdict[-10] = self.raste_text
            if add: 
                ortsdict[-12] = self.free_text
        elif typ == "all":
            ortsdict = self.get_possible_locations(True)
            if add: 
                ortsdict[-11] = self.new_text
        elif typ == "allNoRoute":
            ortsdict = self.get_possible_locations()
            if add: 
                ortsdict[-11] = self.new_text
                #ortsdict[0] = self.new_text
        return list(ortsdict.values()), list(ortsdict.keys())
    ## get all possible locations 
    # @param all - if given and true, all locations are extraced directly, 
    # otherwise only locations not in route are returned
    def get_possible_locations(self, all = None):
        rows = self.mysql.select("OrtsNr,Ort,Kennung", None, "TORT")
        orte = {}
        for row in rows:
            if row[1] and (all or not row[0] in self.spezial_orte):
                orte[row[0]] = Afp_toString(row[1]) + " [" + Afp_toString(row[2]) + "]"
        return orte
   ## get all locations referred by route
    # @param ken - if given only location having this 'Kennung' are selected (used for rest-point 'RA')
    # @param rev - if given the selection above is reversed (only locations without this 'Kennung' are selected)
    def get_all_locations(self, ken = None, rev = None):
        rows = self.get_selection("Orte").get_values("OrtsNr,Ort,Kennung")
        orte = {}
        #print "AfpEvRoute.get_all_locations:", rows
        for row in rows:
            if ken is None or (row[2] == ken and not rev) or (rev and row[2] != ken):
                orte[row[0]] = Afp_toString(row[1]) + " [" + Afp_toString(row[2]) + "]"
        return orte
    ## get location data
    # @param ortsnr - identifier of departure point
    # @param index - if ortsnr == None and given, index in location list
    def get_location_data(self, ortsnr, index = None):
        row = None
        if ortsnr and ortsnr in self.spezial_orte:
            index = self.spezial_orte.index(ortsnr)
        if not index is None:
            row_route = self.get_selection("Route").get_values(None, index)[0]
            row_ort = self.get_selection("Orte").get_values(None, index)[0]
            row =  row_ort + row_route
        else:
            row = self.mysql.select("*","OrtsNr = " + Afp_toString(ortsnr), "TORT")[0]
        return row
    ## set location data
    # @param changed_data - dictionary holding data to be stored
    # @param ortsnr - if given, identifier of departure point
    # @param index - if ortsnr == None and given, index in location list \n
    #  if ortsnr and index is None a new row is added
    def set_location_data(self, changed_data, ortsnr = None, index = None):
        route = self.get_selection("Route")
        orte = self.get_selection("Orte")
        if ortsnr and ortsnr in self.spezial_orte:
            index = self.spezial_orte.index(ortsnr)
        elif index is None:
            add = True
            index = orte.get_data_length()
        for data in changed_data:
            if data in self.feldnamen_route:
                route.set_value(data, changed_data[data], index)
            elif data in self.feldnamen_orte:
                orte.set_value(data, changed_data[data], index)
    ## generate rout identifier ("Kennung")
    # @param ortsnr - identifier of location
    def gen_ident(self, ortsnr):
        ken = 1000*self.get_value("TourNr") + ortsnr
        return ken
    ## add a location to this route
    # @param ortsnr - identfier of location to be added
    # @param time - if given, start time in route relativ to starting point of route (float)
    # @param preis - if given, additional price for departure at that location
    def add_location_to_route(self, ortsnr, time = None, preis = None):
        if ortsnr is None:
            changed_data = {"Zeit":time, "Preis":preis, "OrtsNr": -1} 
            self.new_route_index = len(self.spezial_orte)
        else:
            changed_data = {}
            if not ortsnr in self.spezial_orte:
                row = self.mysql.select("*","OrtsNr = " + Afp_toString(ortsnr), "TORT")[0]
                changed_data = {"OrtsNr":row[0], "Ort":row[1], "Kennung":row[2]}
            else:
                changed_data = {}
            changed_data["KennNr"] = self.gen_ident(ortsnr)
            changed_data["Zeit"] = time
            changed_data["Preis"] = preis 
        self.set_location_data(changed_data, ortsnr)
        if self.debug: print("AfpEvRoute.add_location_to_route:", ortsnr, time, preis)
    ## add location without adding route entry
    # @param ort - name of location
    # @param ken - short name of location ('Kennung')
    def add_new_location(self, ort, ken):
        changed_data = {"Ort":ort, "Kennung":ken} 
        #self.new_location_data = changed_data
        if self.new_location is None:
            self.new_location = AfpSQLTableSelection(self.mysql, "TORT", self.debug, "OrtsNr", self.feldnamen_orte)
            self.new_location.new_data(False, True)
        self.new_location.set_data_values(changed_data)
        #print "AfpEvRoute.add_new_location:", ort, ken
    ## add the identification number to the new location data
    # @param ortsnr - identification number
    def add_new_location_nr(self, ortsnr):
        if self.new_location:
            self_new_loacation.set_value("OrtsNr", ortsnr)
        if not self.new_route_index is None:
            self.get_selection("Route").set_value("KennNr", self.gen_ident(ortsnr), self.new_route_index)
    ## add location and add it to route
    # @param ort - name of location
    # @param ken - short name of location ('Kennung')
    # @param time - if given, start time in route relativ to starting point of route (float)
    # @param preis - if given, additional price for departure at that location
    def add_new_route_location(self, ort, ken, time = None, preis = None):
        self.add_new_location(ort, ken)
        self.add_location_to_route(None, time, preis)
        #print "AfpEvRoute.add_new_route_location"
                
