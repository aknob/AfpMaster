#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvScreen_Verein
# AfpEvScreen_Verein module provides the graphic screen to access all data of the Afp-'Verein' modul 
# it holds the class
# - AfpEvScreen_Verein
#
#   History: \n
#        16 Feb. 2025 - remove depricated routines - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2022 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        25 Aug. 2022 - add main Verein type sampling all members - Andreas.Knoblauch@afptech.de
#        10 Apr. 2019 - integrate all devired flavour classes into one deck - Andreas.Knoblauch@afptech.de
#        10 Jan 2019 - inital code generated - Andreas.Knoblauch@afptech.de


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

import wx
import wx.grid

from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile, Afp_lastIntervalDate, Afp_minDate, Afp_addDaysToDate
from AfpBase.AfpDatabase.AfpSQL import AfpSQL
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import Afp_archivName, Afp_startFile, Afp_getBirthdayList, Afp_getAge
from AfpBase.AfpSelectionLists import Afp_orderSelectionLists
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Question, AfpReq_Text, AfpReq_Selection, AfpReq_Date, AfpReq_MultiLine,  AfpReq_FileName, AfpDialog
from AfpBase.AfpBaseDialogCommon import AfpLoad_DiReport, AfpDialog_Auswahl, Afp_autoEingabe
from AfpBase.AfpBaseScreen import AfpScreen, Afp_loadScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_AdIndiAusw, AfpLoad_DiAdEin_fromSb
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

from AfpEvent.AfpEvScreen import AfpEvScreen
from AfpEvent.AfpEvRoutines import *
from AfpEvent.AfpEvDialog import AfpDialog_EventEdit, AfpDialog_EvClientEdit, AfpLoad_EvClientEdit, AfpEv_addRegToArchiv
    
## service function to determine adjacent 'Sparte' to given pricenumber
# @param mysql - database connection
# @param PNr - price number to determine chapter of club
def AfpEvVerein_getAccountFromChapterPrice(mysql, IdNr):
    KtNr = None
    PNr, dummy = AfpEvVerein_splitSectionPriceNumber(IdNr)
    rows = mysql.select("EventNr","PreisNr = " + Afp_toString(PNr),"PREISE")
    if rows:
        ENr = rows[0][0]
        rows = mysql.select("ErloesKt","EventNr = " + Afp_toString(ENr),"EVENT")
        if rows:
            KtNr = Afp_getSpecialAccount(mysql, rows[0][0])
    return KtNr
## set section price entry of field 'Kennung' in ANMELDEX
# @param preisnr - priceidentifier
# @param anmeldnr - membershipidentifier
def AfpEvVerein_setSectionPriceNumber(preisnr, anmeldnr):
    return Afp_intString(anmeldnr)*100 + Afp_intString(preisnr)
## split section price entry of field 'Kennung' in ANMELDEX
# @param preisnr - number holding identnr and pricenumber
def AfpEvVerein_splitSectionPriceNumber(preisnr):
    anr = None
    if preisnr and preisnr > 99:
        pstr = Afp_toString(preisnr)
        preisnr = Afp_fromString(pstr[-2:])
        anr = Afp_fromString(pstr[:-2])
    return preisnr, anr

## dialog for selection of tour data \n
# selects an entry from the EVENT table
class AfpDialog_EvAwVerein(AfpDialog_Auswahl):
    ## initialise dialog
    def __init__(self):
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.typ = "Spartenauswahl"
        self.datei = "EVENT"
        self.modul = "Event"
        
    ## get the definition of the selection grid content \n
    # overwritten for "Event" use
    def get_grid_felder(self): 
        Felder = [["Kennung.EVENT",15], 
                            ["Bez.EVENT",75],
                            ["Anmeldungen.EVENT",10], 
                            ["EventNr.EVENT",None]] # Ident column
        return Felder
    ## invoke the dialog for a new entry \n
    # overwritten for "Event" use
    def invoke_neu_dialog(self, globals, eingabe, filter):
        data = AfpEvVerein(globals)
        return AfpLoad_EvVereinEdit(data, "Verein")      
 
## loader routine for event selection dialog 
# @param globals - global variables including database connection
# @param index - column which should give the order
# @param value -  if given,initial value to be searched
# @param where - if given, filter for search in table
# @param ask - flag if it should be asked for a string before filling dialog
def AfpLoad_EvAwVerein(globals, index, value = "", where = None, ask = False):
    result = None
    Ok = True
    if ask:
        sort_list = AfpEvClient_getOrderlistOfTable(globals.get_mysql(), index)        
        value, index, Ok = Afp_autoEingabe(value, index, sort_list, "Sparten")
    if Ok:
        DiAusw = AfpDialog_EvAwVerein()
        DiAusw.initialize(globals, index, value, where, "Bitte Sparte auswählen:")
        DiAusw.ShowModal()
        result = DiAusw.get_result()
        DiAusw.Destroy()
    elif Ok is None:
        # flag for direct selection
        result = Afp_selectGetValue(globals.get_mysql(), "EVENT", "EventNr", index, value)
    return result      


## baseclass for club handling, section of the club         
class AfpEvVerein(AfpEvent):
    ## initialize AfpEvVerein class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param EventNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either EventNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, EventNr = None, sb = None, debug = None, complete = False):
        AfpEvent.__init__(self, globals, EventNr, sb, debug, complete)
        self.listname = "Verein"
        self.is_main = None
        self.auxilary = None
        self.section_PriceToEvent = None
        self.section_PriceInRows = None
        self.special_filter = {"ANMELD": "(Zustand = \"Anmeldung\" OR Zustand = \"PreStorno\")","Anmeldung": "Zustand = \"Anmeldung\"", "PreStorno": "Zustand = \"PreStorno\"", "PreAnmeld": "Zustand = \"PreAnmeld\""}
        if not self.get_value("AgentNr") and sb:
            KNr = sb.get_value("KundenNr.ADRESSE")
            Name = sb.get_value("Name.ADRESSE")
            #print("AfpEvVerein Konstruktor, Agent:", Name, KNr)
            #self.view()
            self.set_value("AgentNr.EVENT", KNr)
            self.set_value("AgentName.EVENT", Name)
       # overwrite ARCHIV
        days = globals.get_value("show-archiv-interval-Verein","Event")
        if not days: days = 365
        past = Afp_toInternDateString(Afp_addDaysToDate(globals.today(), days, "-"))
        self.selects["ARCHIV"] = [ "ARCHIV","TabNr = EventNr.EVENT AND Tab = \"EVENT\" AND Datum >= \"" + past + "\""] 
        self.selects["AUSGABE"] = [ "AUSGABE","Modul = \"Event\" AND Art = Art.EVENT"] 
        self.selects["Anmeldung"] = [ "ANMELD", "EventNr = EventNr.EVENT AND " + self.special_filter["Anmeldung"],"AnmeldNr"]  
        self.selects["PreStorno"] = [ "ANMELD", "EventNr = EventNr.EVENT AND " + self.special_filter["PreStorno"],"AnmeldNr"] 
        self.selects["PreAnmeld"] = [ "ANMELD", "EventNr = EventNr.EVENT AND " + self.special_filter["PreAnmeld"],"AnmeldNr"] 
        self.selects["Verein"] = [ "ADRESATT","KundenNr = AgentNr.EVENT AND Attribut = \"Verein\""] 
        self.selects["Sparten"] = [ "PREISE",""] 
        Art = self.get_value("Art")
        #print("AfpEvVerein Konstruktor selects:", Art, self.selects)
        if Art == "Sparte":
            #print("AfpEvVerein Konstruktor delete ANMELD:")
            self.delete_selection("ANMELD")
            self.selects["ANMELD"] = [ ]   # special selection for "ANMELD"
            self.delete_selection("Anmeldung")
            self.selects["Anmeldung"] = [ ] 
            self.delete_selection("PreStorno")
            self.selects["PreStorno"] = [ ] 
            self.delete_selection("PreAnmeld")
            self.selects["PreAnmeld"] = [ ] 
            if not self.mainselection in self.selections:
                self.create_selection(self.mainselection) 
        if complete: self.create_selections()
        if self.debug: print("AfpEvVerein Konstruktor EventNr:", self.mainvalue)

    ## special selection (overwritten from AfpSelectionList) \n
    # to handle the selection 'ANMELD' (Clients, Members) where the relation to the EVENT is specified in the ANMELDEX table
    # @param selname - name of selection (in our case 'ANMELD' is implemented)
    # @param new - flag if a new empty list has to be created
    def spezial_selection(self, selname, new = False):
        # SELECT T1.AnmeldNr FROM  AfpMTV.ANMELDEX AS T2, AfpMTV.ANMELD AS T1 WHERE T1.AnmeldNr = T2.AnmeldNr AND (T2.Kennung = 9 OR T2.Kennung = 10 OR T2.Kennung = 11);
        Selection = None
        if selname == "ANMELD" or selname == "Anmeldung" or selname == "PreStorno":
            #print("AfpEvVerein.spezial_selection:", selname)
            if new:
                Selection = AfpSQLTableSelection(self.mysql, "ANMELD", self.debug, "AnmeldNr") 
                Selection.new_data()
            else:
                pnrs = self.get_value_rows("PREISE", "PreisNr")
                #print("AfpEvVerein.spezial_selection PreisNr:", pnrs)
                kwhere = ""
                for nr in pnrs:
                    kwhere += "T2.Kennung = " + Afp_toString(nr[0]) + " OR "
                if kwhere: kwhere = kwhere[:-4]
                sfilter = self.special_filter[selname]
                if "Preis" in sfilter: sfilter = sfilter.replace("Preis","T1.Preis")
                if "Zahlung" in sfilter: sfilter = sfilter.replace("Zahlung","T1.Zahlung")
                befehl = "SELECT T1.AnmeldNr FROM  ANMELDEX AS T2, ANMELD AS T1 WHERE T1.AnmeldNr = T2.AnmeldNr AND (" + kwhere + ") AND " + sfilter
                #print("AfpEvVerein.spezial_selection befehl:", befehl)
                anrs = self.globals.get_mysql().execute(befehl)
                #print("AfpEvVerein.spezial_selection AnmeldNr:", anrs)
                Selection = AfpSQLTableSelection(self.mysql, "ANMELD", self.debug, "AnmeldNr") 
                if anrs:
                    clause = ""
                    for nr in anrs:
                        clause += "AnmeldNr = " + Afp_toString(nr[0]) + " OR "
                    if clause: clause = clause[:-4]
                    #print("AfpEvVerein.spezial_selection clause:", clause)
                    Selection.load_data(clause)
                    #print("AfpEvVerein.spezial_selection Anzahl:", len(Selection.data))
                else:
                    Selection.new_data()
            return Selection
            
    ## special save (overwritten from AfpSelectionList) \n
    # store the special selection 'Bez'
    # @param selname - name of selection (in our case 'ANMELD' is implemented)
    def spezial_save(self, selname):
        if selname == "ANMELD" or selname == "Anmeldung" or selname == "PreStorno": 
            if selname in self.selections:
                self.selections[selname].store()
        
    ## decide, if this section represents the whole club
    def is_main_section(self): 
        #print("AfpEvVerein.is_main_section:", self.get_value(), type(self.get_value()))
        if self.is_main is None: self.is_main = Afp_fromString(self.get_value()) == 1
        return self.is_main
    ## decide, if there are other sections in the club
    def has_auxilary_sections(self): 
        if self.auxilary is None:
            if not self.is_main_section(): self.auxilary = True
            else: self.auxilary = len(self.get_mysql().select("EventNr", None, "EVENT")) > 1
        return self.auxilary
                 
    ## execute cancel action for all prepared member
    # @param refdat - if given: referencedate to which the cancellation should be executed
    def execute_cancel(self, refdat = None):
        leftover = None
        rows = self.get_value_rows("PreStorno", "AnmeldNr,InfoDat,Abmeldung") 
        #print("AfpEvVerein.execute_cancel rows:", refdat, rows)
        if rows:
            leftover = []
            cancelled = []
            sepas = []
            for row in rows:
                if refdat and row[1] > refdat: continue
                cancelled.append(row[0])
                client = self.get_client(row[0])
                if leftover and row[0] in leftover:
                    leftover.pop(leftover.index(row[0]))
                AnNrs = client.execute_cancel(refdat)
                if AnNrs:
                    for nr in AnNrs:
                        if not nr in leftover and not nr in cancelled:
                            leftover.append(nr)
                cad = AfpAdresse(client.get_globals(), client.get_value("KundenNr"))
                if cad.get_bankaccounts("SEPA"):
                    sepas.append([cad, AnNrs])
                elif client.get_value("AgentNr"):
                    cad = AfpAdresse(client.get_globals(), client.get_value("AgentNr"))
                    if cad.get_bankaccounts("SEPA"):
                        sepas.append([cad, AnNrs])
                client.store()
            if sepas:
                #print("AfpEvVerein.execute_cancel SEPAs:", sepas)
                for sepa in sepas:
                    deact = True
                    if sepa[1]:
                        for nr in sepa[1]:
                            if nr in leftover: 
                                deact = False
                    if deact: 
                        sepa[0].deactivate_SEPA(True)
                        print("AfpEvVerein.execute_cancel SEPA deactivated:", sepa[0].get_name())
            #print("AfpEvVerein.execute_cancel cancelled:", cancelled, len(cancelled))
            if len(cancelled)  == 0:
                leftover = None
            else:
                self.add_client_count(-len(cancelled))
                self.store()
        return leftover
        
   ## execute registration for all candidate entries 
    # @param refdat - if given: referencedate, which the registration should be executed
    def execute_candidates(self, refdat = None):
        rows = self.get_value_rows("PreAnmeld", "AnmeldNr, Anmeldung") 
        #print("AfpEvVerein.execute_candidates rows:", refdat, rows)
        if rows:
            cnt = 0
            for row in rows:
                if refdat and row[1] > refdat: continue
                client = self.get_client(row[0])
                cnt += 1
                client.set_value("Zustand", "Anmeldung")
                client.store()
                print("AfpEvVerein.execute_candidates client:", client.get_name(), "->", client.get_value("Zustand"))
            self.add_client_count(cnt)
            
    ## reset payment for new financial period
    def reset_payment(self):
        rows = self.get_value_rows("Anmeldung", "AnmeldNr")
        rows += self.get_value_rows("PreStorno", "AnmeldNr")
        if rows:
            for row in rows:
                client = self.get_client(row[0])
                client.reset_payment()
                client.store()
    
    ## set all prices for a given section
    def set_sections_of_prices(self):
        if self.has_auxilary_sections():
            if not self.section_PriceToEvent:
                self.section_PriceToEvent = {}
                self.section_PriceInRows = {}
                for i in range(self.get_value_length("Sparten")):
                    row = self.get_value_rows("Sparten","PreisNr,EventNr", i)[0]
                    self.section_PriceToEvent[row[0]] = row[1]
                    if row[1] in self.section_PriceInRows:
                        self.section_PriceInRows[row[1]].append(i)
                    else:
                        self.section_PriceInRows[row[1]] = [i]
    ## get all prices for a given section
    # @param pnr - internal number of price to which all prices belonging to where section should be extracted
    def get_section_of_price(self, pnr):
        section = None   
        if self.has_auxilary_sections():
            if not self.section_PriceToEvent:
                self.set_sections_of_prices()
            section =  self.section_PriceToEvent[pnr]
        return section
    ## get all prices for a given section
    # @param preisnr - internal number of price to which all prices belonging to same section should be extracted
    # @param felder - names of columns to be listed from prices
    def get_prices_of_section(self, preisnr, felder):
        preise = []   
        if preisnr is None: return preise
        if self.has_auxilary_sections():
            ENr =  self.get_section_of_price(preisnr)
            inds = self.section_PriceInRows[ENr]
            #print("AfpEvVerein.get_prices_of_section inds:",  ENr, inds)
            for i in inds:
                row = self.get_value_rows("Sparten",felder, i)[0]
                preise.append(row)
        #print("AfpEvVerein.get_prices_of_section OUT:", preisnr, preise)
        return preise
    ## check if a given price is of the given typ
    # @param preisnr - internal number of price to be checked
    # @param typ - typ of price for a positive check
    def price_is_typ(self, preisnr, typ):
        is_typ = False
        pnr = AfpEvVerein_setSectionPriceNumber(preisnr, self.get_value())
        rows = self.get_value_rows("Sparten")
        for row in rows:
            if pnr == row[1]:
                if typ == row[7]:
                    is_typ = True
                break
        return is_typ
    
    ## get all members in a given period
    # @param period - year for which  members should be extracted
    # @param sorttyp - if given, field to sort output
    def get_members_of_period(self, period, sorttyp = None):
        all_clients = self.get_clients(False, None)
        year = Afp_toString(period)
        ps = Afp_fromString("1.1." + year)
        pe = Afp_fromString("31.12." + year)
        clients = []
        for client in all_clients:
            zu= client.get_value("Zustand")
            start = client.get_value("Anmeldung")
            end = client.get_value("InfoDat")
            #print "AfpEvVerein.get_members_of_period:", client.get_name(), start, zu, end, "Periode:", ps, pe, start < pe, (end is None or end > ps)
            if start and start < pe and (zu == "Anmeldung" or zu == "PreStorno" or zu == "Storno") and  (end is None or end > ps):
                clients.append(client)
        if sorttyp:
            clients = Afp_orderSelectionLists(clients, sorttyp)
        return clients  
    
    ## generate identification number (membership number for "Verein")  
    def generate_IdNr(self):
        old = False
        #old = True
        if old:
            self.lock_data()
            IdNr = self.get_value("RechNr") + 1
            self.set_value("RechNr", IdNr)
        else:
            tag = self.get_value("Tag.Verein")
            Extern = AfpExternNr(self.get_globals(),"Count", tag, self.debug)
            IdNr = Extern.get_number()
        #print("AfpEvVerein.generate_IdNr IdNr:",  old, tag, IdNr)
        return IdNr
    ## reset maximal given identification number (needed for extern input)
    # @param id - given identification number
    def set_max_IdNr(self, id):
        old = False
        #old = True
        if old:
            self.lock_data()
            last = self.get_value("RechNr")
            if id > last:
                self.set_value("RechNr", id)
        else:
            tag = self.get_value("Tag.Verein")
            Extern = AfpExternNr(self.get_globals(),"Count", tag, self.debug)
            #Extern = AfpExternNr(self.get_globals(),"Count", tag, True)
            Extern.set_number(id)
       
        
    ## internal routine to set the  filter on ANMELD selection
    # - overwritten from AfpEvent
    # @param values - list of filter values to be applied on selection 
    def set_anmeld_filter(self, values = None):
        filter = ""
        if values:
            inner = ""
            for val in values:
                if "=" in val or">" in val or "<" in val or " LIKE " in val:
                    filter += " AND " + val
                else:
                    inner += " OR Zustand = \"" + val + "\""
            filter += " AND (" + inner[4:] + ")"
            if len(filter)  > 4 and filter[:5] == " AND ": filter = filter[5:]
        if self.is_main_section():
            filter = "EventNr = EventNr.EVENT AND " + filter
            self.selects["ANMELD"] = [ "ANMELD",filter,"AnmeldNr"] 
        else:
            self.special_filter["ANMELD"] = "(" + filter + ")"
        #print ("AfpVerein.set_anmeld_filter selects:", filter, self.selects["ANMELD"])
    
    ## clear current SelectionList to behave as a newly created List 
    # - overwritten from AfpEvent
    # @param keep -  flag if a copy should be created or flags which data should be kept during creation of a copy
    def set_new(self, keep = None):
        #print ("AfpEvVerein.set_new old:", keep)
        #self.view()
        if keep == True:
            keep = [False, True, False, False]
        super(AfpEvVerein, self).set_new(keep)
        #print ("AfpEvVerein.set_new new:") 
        #self.view()
    ## decide whether this event may hold a route insted of the location
    # - overwritten from AfpEvent
    def has_route(self):
        return True
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpEvent
    def get_identification_string(self):
        return "Verein '" +  self.get_string_value("AgentName") + "', Sparte "  +  self.get_string_value("Bez") + " mit " + self.get_string_value("Anmeldungen") + " Mitgliedern"
    ## create client data
    # overwritten from AfpEvent
    # @param ANr - data will be retrieved for this database entry
    # @param IdNr - if ANr is None, data will be retrieved for this Id of this club
    def get_client(self, ANr = None, IdNr = None):
        if ANr is None and IdNr:
            rows = self.get_value_rows("ANMELD")
            for row in rows:
                if row[3] == IdNr:
                    ANr = row[0]
                    break
        return AfpEvMember(self.globals, ANr)
    ## generate invoice number
    # overwritten from AfpEvent
    # @param Nr - if given, this counter will be used to generate RechNr-string
    def generate_RechNr(self, Nr=None):
        #print ("AfpEvVerein.generate_RechNr Nr:", Nr)
        if Nr is None: Nr = self.generate_IdNr()
        deci = self.globals.get_value("decimals-in-rechnr","Event")
        if not deci: deci = 2
        RechNr = self.get_string_value("Kennung") + "-" + Afp_toIntString(Nr, deci)
        #print("AfpEvVerein.generate_RechNr RNr:", RechNr)
        return RechNr

## baseclass for member handling         
class AfpEvMember(AfpEvClient):
    ## initialize AfpEvMember class, derivate from AfpEvClient
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param AnmeldNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either AnmeldNr or sb (superbase) has to be given for initialisation,otherwise a new, clean object is created
    def  __init__(self, globals, AnmeldNr = None, sb = None, debug = None, complete = False):
        AfpEvClient.__init__(self, globals, AnmeldNr, sb, debug, complete)
        self.listname="Member"
        self.keptNr = None
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        #self.selects["PREISE"] = [ "PREISE","EventNr = EventNr.ANMELD OR EventNr = 0"] 
        self.selects["TORT"] = [ "TORT","OrtsNr = Ab.ANMELD"] 
        self.selects["ANMELDATT"] = [ "ANMELDATT","AnmeldNr = AnmeldNr.ANMELD"] 
        self.selects["SEPA"] = [ "ARCHIV","Art = \"SEPA-DD\" AND Tab = \"ANMELD\" AND TabNr = AnmeldNr.ANMELD AND Typ = \"Aktiv\""] 
        self.selects["allSEPA"] = [ "ARCHIV","Art = \"SEPA-DD\" AND Tab = \"ANMELD\" AND TabNr = AnmeldNr.ANMELD"] 
        self.selects["Sparten"] = [ "PREISE",""] 
        #self.selects["RechNrEx"] = [ ] 
        #print "AfpEvMember Konstruktor RechNrEx:", self.get_selection("RechNrEx").data
        if complete: self.create_selections()
        if self.debug: print("AfpEvMember Konstruktor, AnmeldNr:", self.mainvalue)
        
    ## special selection (overwritten from AfpSelectionList) \n
    # to handle the selection 'RechNrEx'  getting all entries of ANMELDEX for all rows in selection 'RechNr'
    # @param selname - name of selection (in our case 'RechNrEx' is implemented)
    # @param new - flag if a new empty list has to be created
    def spezial_selection(self, selname, new = False):
        Selection = None
        if selname == "RechNrEx":
            #print  self.selections["ADRESSE"].get_feldnamen()
            feldnamen = self.selections["ANMELDEX"].get_feldnamen()
            if new:
                Selection = AfpSQLTableSelection(self.mysql, "ANMELDEX", self.debug, None, feldnamen) 
                Selection.new_data()
            else: 
                Selection = AfpSQLTableSelection(self.mysql, "ANMELDEX", self.debug, None, feldnamen) 
                ANrs = self.get_value_rows("RechNr","AnmeldNr")
                
        return Selection
        
    ## execute cancel procedures if flagged \n
    # if more clients are involved, the appropriate RechNr is returned
    # @param refdat - if given: referencedate to which the cancellation should me executed
    def execute_cancel(self, refdat=None):
        AnNr = None
        if self.get_value("Zustand") == "PreStorno": 
            if not refdat: refdat = Afp_addDaysToDate(self.get_globals().today(), 31)
            if refdat >= self.get_value("InfoDat"):
                print ("AfpEvMember.execute_cancel executed:", refdat, self.get_value("InfoDat"), self.get_name())
                self.set_value("Zustand","Storno")
                self.set_value("Abmeldung", self.get_value("InfoDat"))
                self.keptNr = False
                lgh = self.get_value_length("RechNr")
                if lgh > 1: 
                    rows = self.get_value_rows("RechNr","Zustand,AnmeldNr")
                    for row in rows:
                        if row[0] == "Anmeldung": 
                            if AnNr is None:
                                AnNr = [row[1]]
                                self.keptNr = row[1]
                            else:
                                AnNr.append(row[1])
        #print "AfpEvMember.execute_cancel:", self.get_name(), self.get_value(), self.get_value("Zustand"), self.get_value("InfoDat"), dat, AnNr, ReNr
        return AnNr    

    ## store complete SelectionList
    # overwritten from AfpEvClient to handle possible sepa-dd cancelation
    def store(self):
        super(AfpEvMember, self).store()
        if self.keptNr and self.finance_modul:
            KNr = self.get_value("AgentNr")
            if not KNr: KNr = self.get_value("KundenNr")
            self.finance_modul.AfpFinance_swapSEPAMandat(self.globals, KNr, "ANMELD", self.get_value("AnmeldNr"), self.keptNr)
            self.keptNr = None
    ## reset payment for new financial period
    def reset_payment(self):
        zahlung = self.get_value("Zahlung")
        if zahlung:
            diff = self.get_value("Preis") - zahlung
        else:
            diff = self.get_value("Preis")
        #if diff < 0: diff = 0.0
        print("AfpEvMember.reset_payment Zahlung:", self.get_name(), zahlung, diff)
        rows = self.get_value_rows("ANMELDEX","NoPrv")
        #print("AfpEvMember.reset_payment Rows:", rows)
        #if rows: self.view()
        for i in range(len(rows)-1, -1, -1):
            if rows[i][0]: 
                self.delete_row("ANMELDEX", i)
                #print("AfpEvMember.reset_payment Rows deleted:",i)
        if diff > 0:
            jahr = Afp_toString(self.globals.today().year - 1)
            data = {"AnmeldNr": self.get_value(), "Bezeichnung": "Restbeitrag " + jahr, "Preis": diff, "NoPrv": 1}
            self.set_data_values(data, "ANMELDEX", -1)
        preis, extra, dummy = self.gen_price()
        if zahlung is None or preis < 0.01:
            data = {"Preis": preis, "Extra": extra, "Zahlung": None, "ZahlDat":  None}
        else:
            if diff < 0: 
                data = {"Preis": preis, "Extra": extra, "Zahlung": -diff} 
            else: 
                data = {"Preis": preis, "Extra": extra, "Zahlung": 0.0, "ZahlDat":  None} 
        #print("AfpEvMember.reset_payment new:", preis, extra, data, dummy)
        self.set_data_values(data)
    ## generate price for actuel selections   
    def gen_price(self):
        preis = self.get_value("Preis.Preis")
        if not preis: preis = 0.0
        rows = self.get_value_rows("ANMELDEX","Preis,NoPrv")
        ex = 0.0
        prv = 0.0
        for row in rows:
            ex += row[0]
            if not row[1]: prv += ex
        return preis + ex, ex, preis + prv

    ## remove extra price row, if found
    # @param new_data - dictionary of price data to be inserted
    # @param prices - possible price identifier for the same event
    def replace_indirect_section_price(self, new_data, prices):
        rows = self.get_value_rows("ANMELDEX")
        index= -1
        #print ("AfpEvMember.replace_indirect_section_price prices:", new_data["Kennung"], type(new_data["Kennung"]))
        for row in rows:
            #print ("AfpEvMember.replace_indirect_section_price row:", row[1], prices)
            if row[1] in prices:
                index = rows.index(row)
                break
        if index < 0: new_data["AnmeldNr"] = self.get_value()
        self.set_data_values(new_data, "ANMELDEX", index)
                    
        
    ## remove extra price row, if found
    # @param idicator - string searched for in name of proce - or priceidentifier
    def remove_extra_price(self, indicator):
    #def remove_partitial_price(self):
        delete = False
        for i in range(self.get_value_length("ANMELDEX")):
            if Afp_isString(indicator):
                text = self.get_value_rows("ANMELDEX","Bezeichnung", i)[0][0]
                #print ("AfpEvMember.remove_extra_price row:", i, text, text[:12]  == "Beitragsfrei")
                if indicator in text: delete = True
            else:
                ken = self.get_value_rows("ANMELDEX","Kennung", i)[0][0]
                if indicator == ken: delete = True
                #print ("AfpEvMember.remove_extra_price ken:", i, indicator, ken, delete)
            if delete:  
                self.delete_row("ANMELDEX", i)
                return True
        return False
    ## add disount if price-change is pro rata
    # @param price - new yearly price to be reached
    # @param initial_price - old yearly price given (if price changes during the year) or None
    # @param date - date on which change becomes active
    def add_partitial_price(self, price, initial_price, date):
        if date.month < 2: return
        factor = (date.month-1)/12.0
        initial = 0.0 
        new = price*(1.0 - factor)
        #print ("AfpEvMember.add_partitial_price:", price, initial_price, date, factor, new)
        month = Afp_toMonthString(date.month)
        text = "Beitragsfrei bis " +  month 
        if initial_price:
            initial = initial_price*factor
            text = "Beitragsänderung im " +  month
        new += initial
        #print ("AfpEvMember.add_partitial_price:", price, initial_price, month, factor, new, text, new-price)
        sel = self.get_selection("ANMELDEX")
        rows = sel.get_values()
        index = None
        for row in rows:
            # print "AfpEvMember.add_partitial_price row:",row[2], text, Afp_toString(row[2]) == text
            if Afp_toString(row[2]) == text:
                index = rows.index(row)
                diff = row[3]
        if index is None:
            changed_data = {"Preis":new - price, "Bezeichnung":text, "NoPrv":1}
            if self.get_value("AnmeldNr"): 
                changed_data ["AnmeldNr"] =  self.get_value("AnmeldNr")
            sel.add_data_values(changed_data)
        else:
            changed_data = {"Preis": new - price, "Bezeichnung":text}
            sel.set_data_values(changed_data, index)   
            
    ## add SEPA Direct Debit mandate or replace filename
    # @param fname - name of scan of mandat
    # @param datum - date when mandat has been signed
    # @param bic - BIC of client account for which mandat has been signed
    # @param iban - IBAN of client account for which mandat has been signed
    def add_sepa_data(self, fname, datum = None, bic = None, iban = None):
        if (Afp_existsFile(fname) or Afp_existsFile(self.get_globals().get_value("archivdir") + fname)) and ((datum and bic and iban) or (self.get_value("Extern.Sepa") and self.get_value("Extern.Sepa")[:7] == "No-Scan")):
            if self.get_globals().get_value("path-delimiter") in fname:
                ext = fname.split(".")[-1]
                max = 1
                fpath = None
                fresult = None
                while not fpath:
                    if max < 10:  null = "0"
                    else:  null = ""
                    fresult = "SEPA" + "_Adresse_" + self.get_string_value() + "_" + null + str(max) + "." + ext 
                    fpath = Afp_addRootpath(self.get_globals().get_value("archivdir"), fresult)
                    if Afp_existsFile(fpath):
                        max+= 1
                        fpath = None
                if self.debug: print("AfpSEPAdd.add_sepa_data copy file:", fname, "to",  fpath)
                Afp_copyFile(fname, fpath)
                fname = fresult
            #print("AfpSEPAdd.add_sepa_data fname:", fname, datum, bic, iban)
            if datum and bic and iban:
                added = {}
                added["Art"] = "SEPA-DD"
                added["Typ"] = "Aktiv"
                added["Datum"] = datum
                added["Gruppe"] = bic
                added["Bem"] = iban
                added["Extern"] = fname
                if self.get_value("AgentNr"):
                    added["KundenNr"] = self.get_value("AgentNr")
                #self.add_to_Archiv(added, False, fresult)
                self.add_to_Archiv(added)
            elif fname:
                self.set_value("Extern.Sepa", fname)
        else:
            print("WARNING: SEPA mandat not all data supplied:", fname, datum, bic, iban)
            
    ## set family member price
    def set_family_price(self):
        preis = None
        nr = None
        #print "AfpMember.set_family_price  in:", self.get_value("PreisNr"), self.get_value("Preis"), self.get_value("Extra")
        datas = self.get_value_rows("Preise")
        for data in datas:
            if data[2] == "Familienmitglied":
                nr = data[1]
                preis = data[5]
                break
        if not preis is None:
            self.set_value("PreisNr", nr)
            self.set_value("Preis", preis)
            self.set_value("ProvPreis", preis)
            self.set_value("Extra", 0.0)
            self.delete_selection("Preis")
            self.delete_selection("ANMELDEX")
            self.add_optional_prices()
        #print "AfpMember.set_family_price out:", self.get_value("PreisNr"), self.get_value("Preis"), self.get_value("Extra")
    ## get next possible resign date 
    # @param rdat - if given date of resignment
    def get_resign_date(self, rdat=None):
        if rdat is None:
            rdat = self.get_globals().today()
        interval= self.get_globals().get_value("resign-interval", "Event")
        if not interval: interval = 12
        period= self.get_globals().get_value("resign-period", "Event")
        if not period: period = 90
        p_end = Afp_addDaysToDate(rdat, period)
        date = Afp_lastIntervalDate(p_end, interval)
        datum = Afp_toString(date)
        #print ("AfpMember.get_resign_date:", interval, period, rdat, p_end, date, datum, type(rdat))
        #self.get_globals().view()
        return datum
    ## extract bulk price, overwritten from AfpEvClient
    #@param initial - flag if initial bulk price is catched or normal bulk price
    def get_bulk_price(self, initial = False):
        datas = self.get_value_rows("PREISE")
        for data in datas: 
            if initial and (data[2] == "Familie" or data[2][:8] == "Familie "):
                return data[5], data[1]
            elif data[2] == "Familienmitglied":
                return data[5], data[1]
        return None, None
   ## optionally add extra prices depending of data
    # overwirtten from AfpEvClient
    def add_optional_prices(self):
        #print "AfpEvMember.add_optional_prices:", self.new, self.get_name()
        if self.new:
            preis, pnr = self.get_bulk_price()
            add = False
            #print ("AfpEvMember.add_optional_prices Preis:", preis, pnr, self.get_value("PreisNr") != pnr, self.get_value("Anmeldung"))
            if self.get_value("PreisNr") != pnr:
                self.remove_extra_price("Beitragsfrei")
                self.add_partitial_price(self.get_value("Preis"), None, self.get_value("Anmeldung"))
                self.add_extra_price("Schlüsselpfand")
                add = True
            if Afp_getAge(self.get_string_value("Geburtstag.ADRESSE"), True) >= 18:
                self.add_extra_price("Aufnahmegebühr")
                add = True
            if add:
                preis, extra, prov = self.gen_price()
                self.set_value("Preis", preis)
                self.set_value("Extra", extra)
                self.set_value("ProvPreis", prov)
                #print "AfpEvMember.add_optional_prices:", self.get_selection("ANMELDEX").data
    ## get attributs for a year
    # @param attribut - name of attribut to be extracted
    # @param period - if given, year for which the attributes have to be extracted, default: actuel year
    def set_attribut_period(self, attribut, period=None):  
        if not period:
            period = self.globals.today().year
        jahr = Afp_toString(period)
        fromdat = Afp_fromString("1.1." + jahr)
        todat = Afp_fromString("31.12." + jahr)
        self.selects["ANMELDATT"] =  [ "ANMELDATT","AnmeldNr = AnmeldNr.ANMELD AND Attribut = \"" + attribut + "\" AND Datum >= '" + Afp_toInternDateString(fromdat)  + "' AND Datum <= '" + Afp_toInternDateString(todat) + "'"]
        #print "AfpEvMember.set_period:", self.selects["ANMELDATT"], self.get_selection("ANMELDATT").data
        
    ## get first aktiv sepa mandat
    # @param felder - if given, fields to be extracted from aktiv sepa row
    # @param all - if given and no active mandat available, return lastest inactive mandat
    def get_aktiv_sepa(self, felder=None, all=False):
        lgh = 9
        if felder: lgh = len(felder.split(","))
        res = [None]*lgh
        #row = None
        for i in range(self.get_value_length("ARCHIV")):
            row = self.get_value_rows("ARCHIV", "Art,Typ,Datum", i)[0]
            dat = Afp_minDate()
            if row[0] == "SEPA-DD":
                if row[1] == "Aktiv" or (all and row[2] > dat):
                    if felder:
                        res = self.get_value_rows("ARCHIV", felder, i)[0]
                    else:
                        res = rows[i]
                    if all: dat = row[2]
                if row[1] == "Aktiv": break
        return res
    ## deaktivate all sepa mandats
    def deactivate_sepa(self):
        # don't use SEPA SelectionList, as it is overwritten by ARCHIV
         for i in range(self.get_value_length("ARCHIV")):
            row = self.get_value_rows("ARCHIV", "Art,Typ", i)[0]
            if row[0] == "SEPA-DD" and row[1] == "Aktiv":
                self.set_data_values({"Typ": "Inaktiv"},"ARCHIV", i) 
    ## get attribut row
    # @param attribut - name of attribut to be extracted
    # @param period - if given, year for which the attributes have to be extracted, default: actuel year
    def get_attributs(self, attribut, period=None):
        self.set_attribut_period(attribut, period)
        rows = self.get_value_rows("ANMELDATT")
        values = []
        indices = []
        for i in range(len(rows)):
            row = rows[i]
            indices.append(i)
            values.append([row[2], row[4], row[3]])
        return values, indices
    ## generate selection sum
    def get_attribut_sum(self):
        rows = self.get_value_rows("ANMELDATT")
        sum = 0.0
        skip = False
        if rows:
            for row in rows:
                if row and len(row) > 3 and row[2]:
                    if row[3] is None:
                        skip = True
                    else:
                        sum += row[3]
       # print "AfpEvMember.get_attribut_sum:", self.get_name(), sum, skip, "\n", rows
        if not sum and skip:
            return None
        else:
            return sum
    ## return one line holding the different 'Sparten'
    # @param deli - delimiter betwenn the different entries
    def get_sparten_line(self, deli = " "):
        line = ""
        mysql = self.get_mysql()
        db = self.get_mysql().get_dbname()
        befehl = "SELECT Bez FROM " + db +".EVENT AS EV, " + db + ".PREISE AS P, " + db + ".ANMELDEX AS EX WHERE EX.AnmeldNr = " + self.get_string_value() + " AND NOT EX.KENNUNG IS NULL AND EX.Kennung < 100 AND P.PreisNr = EX.Kennung AND EV.EventNr = P.EventNr"
        #print ("AfpMember.get_sparten_line:", befehl)
        rows = self.get_mysql().execute(befehl)
        #print ("AfpMember.get_sparten_line rows:", self.get_string_value(), rows)
        if rows:
            for row in rows:
                line += row[0] + deli
            if line:
                line = line[:-1]
        #print ("AfpMember.get_sparten_line line:", self.get_string_value(), line)
        return line
        
            
    ## check if  the name of the price holds string
    # @param check - string to be checked
    def pricename_holds(self, check):
        if self.get_value("Bezeichnung.Preis") :
            return check in self.get_value("Bezeichnung.Preis")  
        else:
            return False
            
    ## generate Event object for this client
    # overwritten from AfpEvClient
    def get_event(self):
        ENr = self.get_value("EventNr.EVENT")
        return AfpEvVerein(self.get_globals(), ENr)
    ## retrieve value from temporary field  \n
    # @param feld - key in _tmp dictionary, where data has to be retrieved from
    # - overwritten from AfpSelectionList
    def get_tmp_value(self, feld):
        value = super().get_tmp_value(feld)
        if value is None:
            if feld == "Alter":
                value = Afp_getAge(self.get_value("Geburtstag.ADRESSE"))
            if feld == "Senior":
                value = Afp_getAge(self.get_value("Anmeldung"))
                #print ("AfpEvMember.get_tmp_value Senior:", self.get_value("Anmeldung"), value)
            if feld == "Sparte":
                value = self.get_sparten_line(";")
            if not (value is None):
                if self._tmp is None:
                    self._tmp = {}
                self._tmp[feld] = value
        return value
    ## get splitting values for payment
    # @param amount- if given: amount to be splitted pro rata
    # -  overwritten from AfpSelectionList
    def get_splitting_values(self, amount = None):
        splitting = None
        #print ("AfpEvMember.get_splitting_values:", self.get_name(), self.get_value("Extra"), amount,  self.get_value("Art.EVENT"))
        sparte = "Sparte" in self.get_value("Art.EVENT")
        if self.get_value("Extra") or sparte:
            rows = self.get_value_rows("ANMELDEX", "Bezeichnung,Preis,Kennung")
            if rows:
                splitting = [None]
                sum = 0.0
                for row in rows: 
                    #print ("AfpEvMember.get_splitting_values row:", row)
                    KtNr = None
                    if row[2] or "Abteilung" in row[0]: # Sparte detected
                        #print("AfpEvMember.get_splitting_values: Sparte detected!") 
                        if Afp_isEps(row[1]): # only split, if price is set
                            snr = row[2]
                            if not snr:
                                snr = Afp_fromString(row[0].split(" ")[-1])
                            KtNr = AfpEvVerein_getAccountFromChapterPrice(self.get_mysql(), snr)
                    elif row[1] > 0.0:  # don't split a discount
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
                    if self.get_value("Extra") != sum or (sparte and self.get_value("Preis") != sum):
                        splitting[0] = [Afp_getSpecialAccount(self.get_mysql(), self.get_value("ErloesKt.EVENT")), self.get_value("Preis") - sum, ""]
                    else:
                        splitting.pop(0)
                else:
                    splitting = None
        if amount and splitting:
            splitting = self.scale_splitting(amount, splitting)
        #print "AfpEvMember.get_splitting_values sum:", splitting 
        return splitting
    ## return the translated listname to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_listname_translation(self):
        return "Mitglied"
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Anmeldung für den Verein"  +  self.get_string_value("Vorname.Veranstalter") + " " +   self.get_string_value("Name.Veranstalter") 

# end of class AfpMember        
        
## Class AfpEvScreen_Verein shows 'Event' screen and handles interactions
class AfpEvScreen_Verein(AfpEvScreen):
    ## initialize AfpEvScreen_Verein, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        #self.einsatz = None # to invoke import of 'Einsatz' modules in 'init_database'
        self.clubnr = None
        self.auswname = None
        self.finance_moduls = None
        self.active = False
        self.filter_kept = True
        self.white = wx.Colour(255, 255, 255)
        AfpEvScreen.__init__(self, debug)
        self.flavour = "Verein"
        self.members_complete = "0"
        self.special_agent_output = False
        self.SetTitle("Afp Verein")
        self.grid_sort_rows = {} # enable sorting 
        self.grid_row_selected = None
        self.dynamic_grid_col_percents = [ 6, 20, 20, 14, 13, 13, 14]
        if self.debug: print("AfpEvScreen_Verein Konstruktor")
       
    ## initialize widgets
    def InitWx(self):
        # set up sizer strukture
        self.sizer =wx.BoxSizer(wx.HORIZONTAL)
        
        self.panel_left_sizer =wx.BoxSizer(wx.VERTICAL)
        self.button_sizer =wx.BoxSizer(wx.VERTICAL)
        self.button_low_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.button_mid_sizer =wx.BoxSizer(wx.VERTICAL)
        
        self.top_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.top_mid_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.modul_button_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.event_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.event_panel_sizer =wx.StaticBoxSizer(wx.StaticBox(self, -1,label="Sparte"), wx.HORIZONTAL)
        self.client_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.client_panel_sizer =wx.StaticBoxSizer(wx.StaticBox(self, -1,label="Anmeldung"), wx.VERTICAL)
        self.grid_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        
        # right BUTTON sizer
        self.combo_Sortierung = wx.ComboBox(self, -1, value="Mitglieder", choices=["Mitglieder","Sparte"], size=(100,30), style=wx.CB_DROPDOWN, name="Sortierung")
        #self.combo_Sortierung = wx.ComboBox(self, -1, value="Sparte", choices=["Mitglieder","Sparte"], size=(100,30), style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Index, self.combo_Sortierung)
        self.indexmap = {"Mitglieder":"RechNr","Sparte":"Bez"}
        
        self.button_Auswahl = wx.Button(self, -1, label="Aus&wahl",size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Ausw, self.button_Auswahl)
        self.button_Abschluss = wx.Button(self, -1, label="A&bschluss",size=(77,50), name="BAbschluss")
        self.Bind(wx.EVT_BUTTON, self.On_Abschluss, self.button_Abschluss)      
        self.button_Event = wx.Button(self, -1, label="&Sparte",size=(77,50), name="BEvent")
        self.Bind(wx.EVT_BUTTON, self.On_modify, self.button_Event)
        self.button_Anmeldung = wx.Button(self, -1, label="&Anmeldung", size=(77,50),name="BAnmeldung")
        self.Bind(wx.EVT_BUTTON, self.On_Anmeldung, self.button_Anmeldung)
        self.button_Zahlung = wx.Button(self, -1, label="&Zahlung",size=(77,50), name="BZahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahlung)
        self.button_Dokumente = wx.Button(self, -1, label="&Dokumente",size=(77,50), name="BDokumente")
        self.Bind(wx.EVT_BUTTON, self.On_Documents, self.button_Dokumente)
        self.button_Ende = wx.Button(self, -1, label="Be&enden",size=(77,50), name="BEnde")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Ende)
        
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Auswahl,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Abschluss,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Event,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Anmeldung,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Zahlung,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Dokumente,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Ende,0,wx.EXPAND)
        
        self.button_low_sizer.AddStretchSpacer(1)
        self.button_low_sizer.Add(self.button_mid_sizer,0,wx.EXPAND)
        self.button_low_sizer.AddStretchSpacer(1)
        
        self.button_sizer.AddSpacer(10)
        self.button_sizer.Add(self.combo_Sortierung,0,wx.EXPAND)
        self.button_sizer.AddSpacer(10)
        self.button_sizer.Add(self.button_low_sizer,1,wx.EXPAND)
        self.button_sizer.AddSpacer(20)
     
        # COMBOBOX
        self.combo_Filter = wx.ComboBox(self, -1, value="Mitglieder", size=(164,20), choices=["Kandidaten","Gäste","Mitglieder","Basismitglieder","Beitragszahler","Zahlung offen","Abgemeldet","Ausgetreten"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        self.filtermap = {"Mitglieder":"Verein Anmeldung PreStorno","Beitragszahler":"Verein Anmeldung PreStorno Preis>=0.01","Zahlung offen":"Verein Anmeldung PreStorno Preis>Zahlung","Basismitglieder":"Verein Anmeldung","Kandidaten":"Verein PreAnmeld","Gäste":"Verein Gast","Abgemeldet":"Verein PreStorno","Ausgetreten":"Verein Storno"}
        self.combo_PayFilter = wx.ComboBox(self, -1, value="", size=(120,20), choices=["","SEPA","Retoure","Rechnung"], style=wx.CB_DROPDOWN, name="PayFilter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_PayFilter)
        self.payfiltermap = {"SEPA":"ZahlArt LIKE 'SEPA-Mandat%'","Retoure":"ZahlArt='Retoure'","Rechnung":"ZahlArt='Rechnung'"}
        self.top_mid_sizer.AddStretchSpacer(1)
        self.top_mid_sizer.Add(self.combo_Filter,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
        self.top_mid_sizer.Add(self.combo_PayFilter,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
      
        # Event
        self.label_Event = wx.StaticText(self, -1, label="", name="Verein")
        self.labelmap["Verein"] = "AgentName.EVENT"
        self.label_Sparte = wx.StaticText(self, -1, label="", name="Sparte")
        self.labelmap["Sparte"] = "Bez.EVENT"
        self.label_Kennung = wx.StaticText(self, -1, label="", name="Kennung")
        self.labelmap["Kennung"] = "Kennung.EVENT"
        self.label_Mitglieder = wx.StaticText(self, -1,  label="Mitglieder: ", name="LMitglieder")
        self.label_Anmeldungen = wx.StaticText(self, -1, label="", name="Anmeldungen")
        self.labelmap["Anmeldungen"] = "Anmeldungen.EVENT"
        
        self.event_panel_sizer.AddSpacer(10)
        self.event_panel_sizer.Add(self.label_Event, 6, wx.EXPAND)
        self.event_panel_sizer.AddSpacer(10)
        self.event_panel_sizer.Add(self.label_Sparte, 6, wx.EXPAND)
        self.event_panel_sizer.Add(self.label_Kennung, 1)
        self.event_panel_sizer.AddSpacer(10)
        self.event_panel_sizer.Add(self.label_Mitglieder, 2)
        self.event_panel_sizer.Add(self.label_Anmeldungen, 1)
        self.event_panel_sizer.AddSpacer(10)
        self.event_sizer.AddSpacer(20)
        self.event_sizer.Add(self.event_panel_sizer, 1)
        
        # Client
        self.label_Typ = wx.StaticText(self, -1, label="", name="Typ")
        self.labelmap["Typ"] = "Zustand.ANMELD"
        self.label_Typ_map = {"Anmeldung":"Mitglied","PreStorno":"Mitglied abgemeldet","Storno":"Austritt","Reservierung":"Interessent"}
        self.label_RechNr = wx.StaticText(self, -1, label="", name="RechNr")
        self.labelmap["RechNr"] = "RechNr.ANMELD"
        self.label_LNr = wx.StaticText(self, -1, label="Nr:", name="LNr")
        self.label_IdNr = wx.StaticText(self, -1, label="", name="IdNr")
        self.labelmap["IdNr"] = "IdNr.ANMELD"
        self.label_Seit = wx.StaticText(self, -1, label="seit:", name="LSeit")
        self.label_Anmeldung = wx.StaticText(self, -1, label="", name="Anmeldung")
        self.labelmap["Anmeldung"] = "Anmeldung.ANMELD"
        
        self.top_client_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_client_sizer.AddSpacer(10)
        self.top_client_sizer.Add(self.label_Typ, 3, wx.EXPAND)
        self.top_client_sizer.AddSpacer(10)
        self.top_client_sizer.Add(self.label_RechNr, 2, wx.EXPAND)
        self.top_client_sizer.AddSpacer(10)
        self.top_client_sizer.Add(self.label_LNr, 0)
        self.top_client_sizer.AddSpacer(10)
        self.top_client_sizer.Add(self.label_IdNr, 1, wx.EXPAND)
        self.top_client_sizer.AddSpacer(10)
        self.top_client_sizer.Add(self.label_Seit, 0)
        self.top_client_sizer.AddSpacer(10)
        self.top_client_sizer.Add(self.label_Anmeldung, 3)
        self.top_client_sizer.AddSpacer(10)
    
        #Adress
        self.label_Vorname = wx.StaticText(self, -1, label="", name="Vorname")
        self.labelmap["Vorname"] = "Vorname.ADRESSE"
        self.label_Name = wx.StaticText(self, -1, label="", name="Name")
        self.labelmap["Name"] = "Name.ADRESSE"
        self.name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.name_sizer.Add(self.label_Vorname, 1, wx.EXPAND)
        self.name_sizer.AddSpacer(10)
        self.name_sizer.Add(self.label_Name, 1, wx.EXPAND)
 
        self.label_Strasse = wx.StaticText(self, -1, label="", name="Strasse")
        self.labelmap["Strasse"] = "Strasse.ADRESSE"
       
        self.label_Plz = wx.StaticText(self, -1, label="", name="Plz")
        self.labelmap["Plz"] = "Plz.ADRESSE"
        self.label_Ort = wx.StaticText(self, -1, label="", name="AdOrt")
        self.labelmap["AdOrt"] = "Ort.ADRESSE"
        self.ort_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ort_sizer.Add(self.label_Plz, 1, wx.EXPAND)
        self.ort_sizer.AddSpacer(10)
        self.ort_sizer.Add(self.label_Ort, 4, wx.EXPAND)

        self.label_Telefon = wx.StaticText(self, -1, label="", name="Telefon")
        self.labelmap["Telefon"] = "Telefon.ADRESSE"
        self.label_Handy = wx.StaticText(self, -1, label="", name="Handy")
        self.labelmap["Handy"] = "Tel2.ADRESSE"
        self.tel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tel_sizer.Add(self.label_Telefon, 1, wx.EXPAND)
        self.tel_sizer.AddSpacer(10)
        self.tel_sizer.Add(self.label_Handy, 1, wx.EXPAND)
 
        self.label_Mail = wx.StaticText(self, -1, label="", name="Mail")
        self.labelmap["Mail"] = "Mail.ADRESSE"
        self.label_Box = wx.StaticText(self, -1, label="", name="Ab")
        self.labelmap["Ab"] = "Name.TOrt"
        self.mail_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mail_sizer.Add(self.label_Mail, 4, wx.EXPAND)
        self.mail_sizer.AddSpacer(10)
        self.mail_sizer.Add(self.label_Box, 1, wx.EXPAND)
        
        self.adress_sizer = wx.BoxSizer(wx.VERTICAL)
        self.adress_sizer.Add(self.name_sizer, 1, wx.EXPAND)
        #self.adress_sizer.AddSpacer(10)
        self.adress_sizer.Add(self.label_Strasse, 1, wx.EXPAND)
        self.adress_sizer.Add(self.ort_sizer, 1, wx.EXPAND)
        self.adress_sizer.Add(self.tel_sizer, 1, wx.EXPAND)
        self.adress_sizer.Add(self.mail_sizer, 1, wx.EXPAND)
       
        #price
        self.list_service= wx.ListBox(self, -1, name="service")
        self.listmap.append("service")
        self.label_LPreis = wx.StaticText(self, -1, label="Preis:", name="LPreis")
        self.label_Preis = wx.StaticText(self, -1, label="", name="Preis")
        self.labelmap["Preis"] = "Preis.ANMELD"
        self.label_LZahl = wx.StaticText(self, -1, label="bezahlt", name="LZahl")
        self.label_Zahl = wx.StaticText(self, -1, label="", name="Zahl")
        self.labelmap["Zahl"] = "Zahlung.Anmeld"
        self.price_lower_sizer=wx.GridSizer(2,2,10,10)
        self.price_lower_sizer.Add(self.label_LPreis, 1, wx.EXPAND)
        self.price_lower_sizer.Add(self.label_Preis, 1, wx.EXPAND)
        self.price_lower_sizer.Add(self.label_LZahl, 1, wx.EXPAND)
        self.price_lower_sizer.Add(self.label_Zahl, 1, wx.EXPAND)
 
        self.price_sizer = wx.BoxSizer(wx.VERTICAL)
        self.price_sizer.Add(self.list_service, 3, wx.EXPAND)
        self.price_sizer.AddSpacer(10)
        self.price_sizer.Add(self.price_lower_sizer, 2, wx.EXPAND)
        
        # complete layout
        self.bottom_client_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.bottom_client_sizer.AddSpacer(10)
        #self.bottom_client_sizer.Add(self.adress_sizer, 3, wx.EXPAND)
        self.bottom_client_sizer.Add(self.adress_sizer, 3, wx.EXPAND)
        self.bottom_client_sizer.AddSpacer(10)
        self.bottom_client_sizer.Add(self.price_sizer, 2, wx.EXPAND)
        
        self.client_panel_sizer.Add(self.top_client_sizer, 0, wx.EXPAND)
        self.client_panel_sizer.AddSpacer(10)
        self.client_panel_sizer.Add(self.bottom_client_sizer, 1, wx.EXPAND)
        self.client_sizer.AddSpacer(20)
        self.client_sizer.Add(self.client_panel_sizer, 1)
        
        # GRID
        # self.grid_custs = wx.grid.Grid(self, -1, pos=(23,256) , size=(653, 264), name="Customers")
        self.grid_custs = wx.grid.Grid(self, -1, name="Customers")
        self.grid_custs.CreateGrid(self.grid_rows["Customers"], self.grid_cols["Customers"])
        self.grid_custs.SetRowLabelSize(0)
        self.grid_custs.SetColLabelSize(18)
        self.grid_custs.EnableEditing(False)
        self.grid_custs.EnableDragColSize(0)
        self.grid_custs.EnableDragRowSize(0)
        self.grid_custs.EnableDragGridSize(0)
        self.grid_custs.SetSelectionMode(wx.grid.Grid.GridSelectRows)
        self.grid_custs.SetColLabelValue(0, "Nr")
        self.grid_custs.SetColLabelValue(1, "Vorname")
        self.grid_custs.SetColLabelValue(2, "Name")
        self.grid_custs.SetColLabelValue(3, "Eintritt")
        self.grid_custs.SetColLabelValue(4, "Beitrag")
        self.grid_custs.SetColLabelValue(5, "Zahlung")
        self.grid_custs.SetColLabelValue(6, "Info")
        for row in range(0,self.grid_rows["Customers"]):
            for col in range(0,self.grid_cols["Customers"]):
                self.grid_custs.SetReadOnly(row, col)
        self.gridmap.append("Customers")
        self.grid_minrows["Customers"] = self.grid_custs.GetNumberRows()
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick_Custs, self.grid_custs)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_CLICK, self.On_Click_Custs, self.grid_custs)
        self.grid_custs.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.On_GridSort)
        
        self.grid_panel_sizer.AddSpacer(20)
        self.grid_panel_sizer.Add(self.grid_custs,1,wx.EXPAND)
        self.grid_panel_sizer.AddSpacer(10)
       
        self.top_sizer.Add(self.modul_button_sizer,0,wx.EXPAND)
        self.top_sizer.Add(self.top_mid_sizer,1,wx.EXPAND)
       
        self.panel_left_sizer.AddSpacer(10)
        self.panel_left_sizer.Add(self.top_sizer,0,wx.EXPAND)
        self.panel_left_sizer.AddSpacer(10)
        self.panel_left_sizer.Add(self.event_sizer,0,wx.EXPAND)
        self.panel_left_sizer.AddSpacer(10)
        self.panel_left_sizer.Add(self.client_sizer,0,wx.EXPAND)
        self.panel_left_sizer.AddSpacer(10)
        self.panel_left_sizer.Add(self.grid_panel_sizer,1,wx.EXPAND)
        self.panel_left_sizer.AddSpacer(20)
    
        self.sizer.Add(self.panel_left_sizer,1,wx.EXPAND)
        self.sizer.Add(self.button_sizer,0,wx.EXPAND)   
        
        self.dynamic_grid_sizer = self.grid_panel_sizer
        self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
        
   ## execution routine- set date filter
   # dummy only needed to use the AfpEvScreen-routines
    def set_jahr_filter(self,event = None): 
        return
        
    ## reverse selection from filtermap
    # @param word - word to be looked for
    def re_filtermap(self, word):
        remap = None
        for map in self.filtermap:
            if " " + word in self.filtermap[map]:
                remap = map
        return remap
        
    ## show initial information dialog or screen
    # @param typ - typ of information to be shown
    def show_splash_screen(self, typ):
        if typ == "birthday":
            interval = self.globals.get_value("birthday-splash-screen-interval","Event")
            rows = Afp_getBirthdayList(self.globals.get_mysql(), interval, "ANMELD", "b.Zustand = \"Anmeldung\" AND b.KundenNr = a.KundenNr")
            #print "AfpEvScreen_Verein.show_spalsh_screen:", rows
            text = ""
            for row in rows:
                text += Afp_ArraytoLine(row) + "\n"
            dat = Afp_addDaysToDate(self.globals.today(), interval)
            AfpReq_Info("Geburtstagsliste bis zum " + Afp_toString(dat) + "! \n", text[:-1], "Geburtstagsliste")

    ## routine to execute prepared cancellations
    # @param refdat - if given: referencedate to which the cancellation should be executed
    def execute_storno(self, refdat):
        leftover = self.data.execute_cancel(refdat)
        if leftover is None:
            AfpReq_Info("Keine Kündigungen vorgemerkt,","keine Kündigungen durchgeführt!","Kündigungen umsetzen")
        elif not leftover:
            AfpReq_Info("Kündigungen umgesetzt!","Keine Nacharbeiten nötig!","Kündigungen umsetzen")
        else:
            for left in leftover:
                client = AfpEvMember(self.data.get_globals(), left)
                ok = AfpLoad_EvMemberEdit(client, True, True)
        
    ## create first record in database
    def create_initial_record(self):
        AfpReq_Info("Kein Verein angelegt!","Zum Einrichten bitte Adresse auswählen und eine Sparte einrichten!","Vereinsdaten eingeben!")
        verein = AfpEvVerein(self.globals, None, None, self.debug)
        text = "Bitte Adresse für den Verein auswählen:"
        name = verein.get_value("AgentName")
        KNr = AfpLoad_AdAusw(self.globals,"ADRESSE","NamSort",name, None, text, True)
        if KNr:
            verein.set_value("AgentNr.EVENT", KNr)
            adresse = AfpAdresse(self.globals, KNr)
            name =  adresse.get_name()
            verein.set_value("AgentName.EVENT", name)
            #if not adresse.get_attributes("Verein"):
            if not verein.get_value_rows("Verein") or not verein.get_value_rows("Verein")[0]:
                text, ok = AfpReq_Text("Neuer Verein '" + name + "' wird angelegt,", "bitte die Kennung für den Verein eingeben.", "",  "Kennung")
                if ok and text:
                    data = {"KundenNr": KNr, "Name": name, "Attribut": "Verein", "Tag": text, "Aktion": "Kennung"}
                    verein.set_data_values(data, "Verein", -1)
        ok = self.load_event_edit(verein)
        return ok
    ## select gridrow holding the indicated entry 
    # @param id - client identifier
    def select_current_gridrow(self, id):
        if id and "Customers" in self.grid_id and id in  self.grid_id["Customers"]:
            self.grid_row_selected = True
            index = self.grid_id["Customers"].index(id)
            self.grid_custs.SelectRow(index)
            self.grid_custs.MakeCellVisible(index, 0)
        return
    ## deselect the current selected gridrow
    def deselect_current_gridrow(self):
        if self.grid_row_selected:
            index = None
            ANr = self.slave_data.get_value("AnmeldNr")
            if ANr in self.grid_id["Customers"]:
                index = self.grid_id["Customers"].index(ANr)
            if not index is None:
                self.grid_custs.DeselectRow(index)
            self.grid_row_selected = False       
    ## event handler when window is activated
    # @param event - event which initiated this action   
    def On_Activate(self,event):
        #print ("AfpEvScreen_Verein.On_Activate:", self.GetSize())
        if not self.active:
            if self.globals.get_value("birthday-splash-screen-interval","Event") and not self.globals.get_value("splash-screen-shown"):
                self.globals.set_value("splash-screen-shown", 1)
                self.show_splash_screen("birthday")
            add_method = self.data.get_globals().get_value("additional-payment-methods", "Event")
            method_filters = self.data.get_globals().get_value("additional-payment-methods-filter", "Event")
            if add_method:
                for method in add_method:
                    self.combo_PayFilter.Append(method)
                    if method_filters and method in method_filters:
                        self.payfiltermap[method] = (method_filters[method])
                    else:
                        self.payfiltermap[method] = ("ZahlArt='"+method+"'")
            self.active = True

   ## Eventhandler COMBOBOX - filter
   # overwritten from AfpEvScreen
    def On_Filter(self,event=None):
        #print ("AfpEvScreen_Verein.On_Filter called")
        self.filter_kept = False
        self.grid_row_selected = False
        self.grid_custs.ClearSelection()
        self.grid_scrollback()
        self.CurrentData()
        if "Customers" in self.grid_sort_col:
            self.mark_grid_column("Customers", self.grid_sort_col["Customers"])
        if event: event.Skip()    

    ## compose event specific menu parts
    # overwritten from AfpEvScreen
    def create_specific_menu(self):
        super(AfpEvScreen_Verein, self).create_specific_menu()
        if not self.globals.skip_accounting():
            self.finance_moduls = Afp_importAfpModul("Finance",self.globals)
        if self.finance_moduls:
            tmp_menu = self.menubar.Remove(1)
            #print "AfpEvScreen_Verein.create_specific_menu menu:", tmp_menu
            mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "SEPA Überweisung", "")
            self.Bind(wx.EVT_MENU, self.On_SEPAct, mmenu)
            tmp_menu.Append(mmenu)
            mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "SEPA Lastschrifteinzug", "")
            self.Bind(wx.EVT_MENU, self.On_SEPAdd, mmenu)
            tmp_menu.Append(mmenu)
            self.menubar.Insert(1, tmp_menu, "Verein")
    ## perform additional data input,
    # overwritten From AfpEvScreen
    # @param data - client data, where additional input should be made
    def Anmeldung_add_data(self, data):
        sepa = self.globals.get_value("sepa-in-registration","Event")
        if sepa and self.finance_moduls and len(self.finance_moduls) > 1 and self.finance_moduls[1]:
            fname = data.last_selected_file 
            client = self.finance_moduls[1].AfpFinance_addSEPAdd(data, fname)
            if client:
                data = client
                row = data.get_value_length("ARCHIV") - 1
                dat = data.get_value_rows("ARCHIV", "Datum", row)[0][0]
                text = "SEPA-Mandat "  + Afp_toString(dat)
                data.set_value("ZahlArt", text)
            else:
                data.set_value("ZahlArt", "Rechnung")
        return data
    ## populate label widgets
    def Pop_label(self):
        no_slave =  not self.slave_exists()
        #print "AfpEvScreen_Verein.Pop_label:", no_slave
        for entry in self.labelmap:
            Label = self.FindWindowByName(entry)
            is_slave = self.is_slave(self.labelmap[entry])
            if  is_slave and (no_slave or not self.slave_data):
                value = ""
            elif is_slave:
                value = self.slave_data.get_tagged_value(self.labelmap[entry])
                if entry == "Typ" and value in self.label_Typ_map: 
                    value = self.label_Typ_map[value]
            elif self.data:
                value = self.data.get_tagged_value(self.labelmap[entry])
            else:
                value = self.sb.get_string_value(self.textmap[entry])
            Label.SetLabel(value)
            #print "AfpEvScreen_Verein.Pop_label:",  entry, "=", value.strip(), "Flags:", is_slave, len(value.strip()) > 0 and is_slave
            if len(value.strip()) > 0 and is_slave: Label.SetBackgroundColour(self.white)
    ## population routine for special treatment 
    # - overwritten from AfpScreen
    #  to reload labels after grid loading (cause grid sets number of rows)
    def Pop_special(self):
        #if self.data.is_main_section():
        self.label_Anmeldungen.SetLabel(self.members_complete)

    ## Eventhandler Menu - handle SEPA creditor transfer debit
    def On_SEPAct(self,event):
        if self.debug: print("AfpEvScreen_Verein Event handler `On_SEPAct'")
        #print "AfpEvScreen_Verein.On_SEPAct:", self.finance_moduls
        if self.finance_moduls and len(self.finance_moduls) > 1 and self.finance_moduls[1]:
            mandator = self.data.get_value("AgentNr")
            self.finance_moduls[1].AfpLoad_SEPAct(self.data.get_globals(), mandator)
    ## Eventhandler Menu - handle SEPA direct debit
    def On_SEPAdd(self,event):
        if self.debug: print("AfpEvScreen_Verein Event handler `On_SEPAdd'")
        #print "AfpEvScreen_Verein.On_SEPAdd:", self.finance_moduls
        if self.finance_moduls and len(self.finance_moduls) > 1 and self.finance_moduls[1]:
            self.finance_moduls[1].AfpLoad_SEPAdd(self.data)
        
    ## Eventhandler BUTTON - selection
    def On_Ausw(self,event=None):
        if self.debug: print("AfpEvScreen_Verein Event handler `On_Ausw'")
        if self.combo_Sortierung.GetValue() == "Mitglieder":
            value = self.data.get_value("EventNr") # all events of this agent are needed
            name = ""
            filter = None
            ok = True
            if self.auswname:
                name =  self.auswname
                self.auswname = None
            elif self.slave_exists():
                name = self.slave_data.get_value("Name.ADRESSE")
            else:
                name, ok = AfpReq_Text("Mitglied wird gesucht,","bitte Namen eingeben!", name, "Mitgliedssuche")
            knr = None
            if ok:
                #print ("AfpEvScreen_Verein.On_Ausw:", value, name, filter)
                knr = AfpLoad_AdIndiAusw(self.globals, "EventNr.ANMELD", value, name, filter, "Bitte Mitglied auswählen, das angezeigt werden soll.")
            if knr:
                adresse = AfpAdresse(self.globals, knr)
                select = "KundenNr = " + Afp_toString(knr) + " AND EventNr = " + Afp_toString(value) # enhance for possible list
                adresse.get_selection("ANMELD").load_data(select)
                rows = adresse.get_value_rows("ANMELD", "AnmeldNr,EventNr,RechNr,Zustand")
                ANr = rows[0][0]
                filter = self.re_filtermap(rows[0][3])
                self.grid_row_selected = False
                #print "AfpEvScreen_Verein.On_Ausw:", rows[0][3], filter
                if not filter ==  self.combo_Filter.GetValue():
                    self.combo_Filter.SetValue(filter)
                    self.On_Filter()
                self.load_direct(None, ANr)
                self.select_current_gridrow(ANr)
                self.Pop_label()
                self.Reload()
        else:
            super(AfpEvScreen_Verein, self).On_Ausw(event)
        if event: event.Skip()

    ## Eventhandler BUTTON - close current financial year and open new year - or - execute resignments
    def On_Abschluss(self,event):
        if self.debug: print("AfpEvScreen_Verein Event handler `On_Abschluss'")
        Types = ["Check", "Check", "Text", "Check"]
        today = self.data.get_globals().today()
        interval= self.data.get_globals().get_value("resign-interval", "Event")
        if not interval: interval = 12
        date = Afp_lastIntervalDate(today, interval, True)
        Liste = [["Abmeldungen umsetzen:", True], ["Zahlung zurücksetzen:", today.month == 1], ["Umsetzungsdatum:", Afp_toString(date)], ["Abschluss Finanzperiode:", today.month == 1]]
        res = AfpReq_MultiLine("Bitte auswählen, welcher Abschluss umgesetzt werden soll.","Bei Abmeldungen auch das gewünscht Umsetzugsdatum angeben.",Types, Liste, "Abschluss")
        if not res: return
        resign = False
        reset_payment  = False
        finance = False
        if res[0]:
            resign = True
        if res[1]:
            reset_payment = True 
        if res[2]:
            date = Afp_fromString(res[2])
            if not Afp_isDate(date): date = None
        if res[3]:
            finance = True
        print("AfpEvScreen_Verein.On_Abschluss:", res, resign, reset_payment, date, finance)
        Ok = None
        Ok1 = None
        Ok2 = None
        if resign:
            if date: text = "Kündigungen und Anmeldungen zum " + Afp_toString(date) + " umsetzten?"
            else: text = "Kündigungen und Anmeldungen umsetzen?"
            Ok = AfpReq_Question(text ,"", "Kündigungen, Anmeldungen")
            if Ok:
                self.execute_storno(date)
                self.data.execute_candidates(Afp_addDaysToDate(date, 31)) #automated registration for all entries in the first month
        if reset_payment:
            Ok1 = AfpReq_Question("Zahlungsverpflichtungen für das neue Jahr erzeugen?" ,"", "Jahresabschluss")
            if Ok1: self.data.reset_payment()           
        if finance:
            if self.finance_moduls and self.finance_moduls[0]:
                balances = self.finance_moduls[0].AfpFinanceBalances(self.globals)
                akt = Afp_fromString(balances.get_period())
                print("AfpEvScreen_Verein.On_Abschluss finance balances generated:", akt)
                if akt and Afp_isInteger(akt) and akt < self.globals.today().year:
                    Ok2 = AfpReq_Question("Das Jahr '" + Afp_toString(akt) + "' abschliessen und das Jahr '" + Afp_toString(self.globals.today().year) + "' eröffnen?","", "Jahresabschluss")
                    if Ok2: balances.switch_period()
        if Ok or Ok1 or Ok2: 
            self.Reload()
            self.Pop_label()
            #self.set_current_record()
            #self.Populate()
        event.Skip()
            
    ## Eventhandler BUTTON , MENU - modify event
    def On_modify(self, event):     
        if self.debug: print("AfpEvScreen_Verein Event handler `On_modify'")
        if not self.clubnr:
            self.On_Ausw()
        if self.clubnr:
            #super(AfpEvScreen_Verein, self).On_modify()
            self.sb.select_key(self.clubnr, "KundenNr","ADRESSE")
            AfpEvScreen.On_modify(self)
        event.Skip()
        
    ## Eventhandler BUTTON, MENU - document generation
    def On_Documents(self, event = None):
        if self.debug and event: print("AfpEvScreen_Verein  Event handler `On_Documents'")
        if self.grid_row_selected:
            super(AfpEvScreen_Verein, self).On_Documents()
        else:
            clients = []
            rows = self.data.get_value_rows( "ANMELD", "AnmeldNr,Preis")
            #print "AfpEvScreen_Verein.On_Documents:", rows
            for row in rows:
                clients.append(self.get_client(row[0]))
            prefix = "Verein " + Afp_toDateString(self.globals.today(),"yymmdd")
            header = "Vereinsinfo"
            archiv = "Serie"
            variables = self.get_output_variables(self.data)
            variables["Name"] = self.data.get_value("AgentName")
            variables["Filter"] = self.combo_Filter.GetValue()
            variables["Count"] = len(clients)
            print ("AfpEvScreen_Verein.On_Documents:", header, prefix, archiv, variables, self.data.get_selection("AUSGABE").data)
            AfpLoad_DiReport(clients, self.globals, variables, header, prefix, archiv, self.data)
        if event:
            self.Reload()
            event.Skip()
    #
    # (overwritten from AfpEvScreen) 
    #
    ## set database to show indicated tour
    # @param ENr - number of event 
    # @param ANr - if given, will overwrite ENr, number of client entry (AnmeldNummer)
    def load_direct(self, ENr, ANr = None):
        AfpEvScreen.load_direct(self, ENr, ANr)
        if ANr:
            self.slave_data = self.get_client(ANr)
        else:
            self.slave_data = None
    ## switch to other modul screen
    # @param modul - name of modul to switch to
    def SwitchModulScreen(self, modul):
        pos = self.GetPosition().Get()
        if modul == "Adresse" and not self.slave_data:
            Afp_loadScreen(self.globals, modul, self.sb, self.clubnr, pos)
        else:
            Afp_loadScreen(self.globals, modul, self.sb, self.typ, pos)
        self.Close()
     
    ## Eventhandler Menu - select and start additional programs
    #  overwritten from AfpScreen
    # @param data - optional input of data for indirect use
    def On_ScreenZusatz(self, event, data = None):
        if self.debug: print("AfpEvScreen_Verein Event handler `On_ScreenZusatz'!")
        #print "AfpEvScreen_Verein.On_ScreenZusatz:", self.grid_row_selected, self.slave_data, data
        if self.grid_row_selected:
            super(AfpEvScreen_Verein, self).On_ScreenZusatz(event, self.slave_data)
        else:
            super(AfpEvScreen_Verein, self).On_ScreenZusatz(event)
     
    ## Eventhandler Keyboard - handle key-down events 
    #  overwritten from AfpScreen
    def On_KeyDown(self, event):
        keycode = event.GetKeyCode()        
        if self.debug: print("AfpEvScreen_Verein Event handler `On_KeyDown'", keycode)
        if self.combo_Sortierung.GetValue() == "Mitglieder":
            grid_id = self.grid_id["Customers"]
            if keycode == wx.WXK_UP or keycode == wx.WXK_DOWN or keycode == wx.WXK_LEFT or keycode == wx.WXK_RIGHT:
                if keycode == wx.WXK_UP or keycode == wx.WXK_LEFT: next = -1
                elif keycode == wx.WXK_DOWN or keycode == wx.WXK_RIGHT: next = 1
                if grid_id:
                    if  self.grid_row_selected:
                        ANr = self.slave_data.get_value("AnmeldNr")
                        if ANr in grid_id:
                            index = grid_id.index(ANr) + next
                            if index < 0: index = 0
                            if index >= len(grid_id): index = len(grid_id) - 1
                        else:
                            self.grid_row_selected = False
                    if not self.grid_row_selected:
                        self.grid_row_selected = True
                        if next < 0:
                            index = len(grid_id) - 1
                        else:
                            index = 0
                    ANr = grid_id[index]
                    self.grid_custs.SelectRow(index)
                    self.grid_custs.MakeCellVisible(index, 0)
                    self.load_direct(0, ANr)
                    self.Reload()
            elif keycode == wx.WXK_ESCAPE:
                if self.grid_row_selected:
                    self.deselect_current_gridrow()
                    self.Reload()
        else:
            self.deselect_current_gridrow()
            super(AfpEvScreen_Verein, self).On_KeyDown(event)

    ## generate the dedicated event
    # (overwritten from AfpEvScreen) 
    # @param ENr - if given:True - new event; Number - EventNr of event
    def get_event(self, ENr = None):
        #print ("AfpEvScreen_Verein.get_event called")
        if ENr == True: return AfpEvVerein(self.globals)
        elif ENr:  return  AfpEvVerein(self.globals, ENr)
        #if self.data and self.sb: print ("AfpEvScreen_Verein.get_event sb:", self.sb.get_value("EventNr.EVENT"),  self.data.get_value("EventNr.EVENT"), self.filter_kept, self.sb.get_value("EventNr.EVENT") == self.data.get_value("EventNr.EVENT"))
        #else: print ("AfpEvScreen_Verein.get_event sb:", self.sb,  self.data, self.filter_kept)
        if self.data and self.sb and self.sb.get_value("EventNr.EVENT") == self.data.get_value("EventNr.EVENT") and self.filter_kept:
            return self.data
        else:
            Verein =  AfpEvVerein(self.globals, None, self.sb)
            filters = self.filtermap[self.combo_Filter.GetValue()].split()
            if self.combo_PayFilter.GetValue(): 
                filters.append(self.payfiltermap[self.combo_PayFilter.GetValue()])
            #print ("AfpEvScreen_Verein.get_event filters:", filters)
            Verein.set_anmeld_filter(filters[1:])
            self.filter_kept = True
            return  Verein
    ## load event selection dialog (Ausw)
    # (overwritten from AfpEvScreen)     
    # @param index - column which should give the order
    # @param value -  initial value to be searched
    # @param where - filter for search in table
    def load_event_ausw(self,  index, value, where):
        return AfpLoad_EvAwVerein(self.globals, index, value, where, True)
    ## load event edit dialog
    # (overwritten from AfpEvScreen) 
    # @param data - data to be edited
    def load_event_edit(self, data):
        return AfpLoad_EvVereinEdit(data, self.flavour)    
    ## generate the dedicated event client
    # (overwritten from AfpEvScreen) 
    # @param ANr - if given:True - new client; Number - AnmeldNr of client
    def get_client(self, ANr = None):
        #print ("AfpEvScreen_Verein.get_client:", ANr)
        if ANr == True: return AfpEvMember(self.globals)
        elif ANr:  return  AfpEvMember(self.globals, ANr)
        return  AfpEvMember(self.globals, None, self.sb)
    ## load client edit dialog
    # (overwritten from AfpEvScreen) 
    # @param data - data to be edited
    def load_client_edit(self, data):
        changed = AfpLoad_EvMemberEdit(data) 
        if changed: self.filter_kept = False
        return  changed     
        #return AfpLoad_EvClientEdit(data)   
    ## generate needed oiutput variables
    # (overwritten from AfpEvScreen) 
    # @param data - data to be used for output
    def get_output_variables(self, data):
        today = self.globals.today()
        vars= {"Today" : today} 
        if not data.get_listname() == "Verein":
            thisday = data.get_value("Anmeldung")
            vars["ThisYear"] = today.year
            if  thisday.year < today.year:
                vars["ThisMonth"] = 0
            else:
                vars["ThisMonth"] = thisday.month - 1
            if self.globals.get_value("duty-parameter-Verein","Event"):
                vars["Duties"] = self.globals.get_value("duty-parameter-Verein","Event")[0]
        #print "AfpEvScreen_Verein.get_output_variables:", data.get_listname() , vars
        return vars
        
    ## set current record to be displayed 
    # (overwritten from AfpEvScreen) 
    def set_current_record(self):
        ini = True
        if self.data and self.clubnr == self.data.get_value("AgentNr"): ini = False
        #print ("AfpEvScreen_Verein.set_current_record ini: ", ini, self.data, self.clubnr, self.sb.get_value("AgentNr.EVENT"))
        if ini:
            self.sb.select_key(self.clubnr , "AgentNr","EVENT")
            self.sb.set_index("Kennung","EVENT","AgentNr")            
            #self.sb.CurrentIndexName("Kennung","EVENT")
        self.data = self.get_event() 
        #print ("AfpEvScreen_Verein.set_current_record: ", ini, self.sb_master, self.sb.CurrentFile.name, self.sb.get_value("AnmeldNr.ANMELD"))
        if self.grid_row_selected and not self.no_data_shown:
            self.slave_data = self.get_client()
        else:
            self.slave_data = None
        #print ("AfpEvScreen_Verein.set_current_record slave_data: ", self.slave_data)
        if self.debug: 
            print("AfpEvScreen_Verein.set_current_record:")
            self.data.view()
        return

    ## set initial record to be shown, when screen opens the first time
    # (overwritten from AfpEvScreen) 
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        self.clubnr = 1
        if origin == "Adresse": 
            self.auswname = self.sb.get_value("Name.ADRESSE")
            origin = ""
        AfpEvScreen.set_initial_record(self, origin)
        return
    ## set initial gridrow to be selected, when screen opens the first time
    # (overwritten from AfpScreen) 
    def set_initial_gridrow(self):
        if self.slave_exists():
            ANr = self.slave_data.get_value()
            if Afp_isString(ANr):
                ANr = Afp_fromString(ANr)
            self.select_current_gridrow(ANr)
            #wx.CallAfter(self.select_current_gridrow, ANr)
        return
    ## check if slave exists
    def slave_exists(self):
        #print "AfpEvScreen_Verein.slave_exists:", self.slave_data,  not self.slave_data is None
        return not self.slave_data is None
    ## prepare the reload on the data of screen
    # @param complete - flag if a complete reload from database should be performed, default: True
    def prepare_reload(self, complete = True):
        if complete: self.filter_kept = False
    ## get rows to populate lists \n
    # default - empty, to be overwritten if grids are to be displayed on screen \n
    # possible selection criterias have to be separated by a "None" value
    # @param typ - name of list to be populated 
    def get_list_rows(self, typ):
        rows = [] 
        #print "AfpEvScreen_Verein.get_list_rows typ:", typ, self.slave_data, self.slave_exists() 
        if typ == "service" and self.slave_exists() and self.slave_data:
            bez = self.slave_data.get_string_value("Bezeichnung.Preis")  
            preis = self.slave_data.get_string_value("Preis.Preis")   
            if not bez: bez = "Beitrag"
            if not preis: preis = self.slave_data.get_string_value("ProvPreis.ANMELD")  
            if not preis: preis = self.slave_data.get_string_value("Preis.ANMELD")  
            #print "AfpEvScreen_Verein.get_list_rows Preis:", preis, bez
            if preis:
                rows.append(preis + "  " + bez)
            else:
                rows.append(bez)
            extra = self.slave_data.get_value("Extra.ANMELD")
            anmeld = self.slave_data.get_value("Preis.ANMELD")
            #print ("AfpEvScreen_Verein.get_list_rows Extra:", extra, preis, anmeld, extra == 0.0 and anmeld == 0.0)
            #if extra or (extra == 0.0 and anmeld == 0.0):
            if extra == anmeld and extra:
                rows[0] = Afp_toString(0.0) + " " + bez
            ex_row = self.slave_data.get_selection("ANMELDEX").get_values("Bezeichnung,Preis")
            #print "AfpEvScreen_Verein.get_list_rows Extra:", ex_row
            for row in ex_row:
                if row[1] or anmeld:
                    rows.append(Afp_toString(row[1]) + "  " + Afp_toString(row[0]))
                else:
                    rows.append(Afp_toString(row[0]))
        return rows
        
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param typ - name of grid to be populated
    def get_grid_rows(self, typ):
        rows = []
        if self.debug: print("AfpEvScreen_Verein.get_grid_rows typ:", typ)
        #print("AfpEvScreen_Verein.get_grid_rows typ:", typ, self.no_data_shown, self.data, self.data.selections)
        if self.no_data_shown: return  rows
        if typ == "Customers" and self.data:
            tmps = self.data.get_value_rows("ANMELD","IdNr,Zahlung,Preis,Info,Anmeldung,KundenNr,Zustand,AnmeldNr")
            #print("AfpEvScreen_Verein.get_grid_rows tmps:", tmps) 
            if tmps:
                KNrs = []
                for tmp in tmps:
                    if self.data.is_main_section() and tmp[5] in KNrs: continue
                    KNrs.append(tmp[5])
                    if tmp[5] in self.name_cache:
                        namen = self.name_cache[tmp[5]]
                    else:
                        adresse = AfpAdresse(self.globals, tmp[5])
                        namen = [adresse.get_string_value("Vorname"), adresse.get_string_value("Name")]
                        self.name_cache[tmp[5]] = namen
                    rows.append([Afp_toString(tmp[0]), namen[0], namen[1],  Afp_toString(tmp[4]), Afp_toString(tmp[2]), Afp_toString(tmp[1]), Afp_toString(tmp[3]), tmp[7]])
            if self.data.get_selection("ANMELD").is_empty(): self.members_complete = "0"
            else: self.members_complete = Afp_toString(len(rows))
        if self.debug: print("AfpEvScreen_Verein.get_grid_rows rows:", rows) 
        #print ("AfpEvScreen_Verein.get_grid_rows length:", len(rows) )
        return rows

 # end of class AfpEvScreen_Verein
 
## allows the display and manipulation of an event 
class AfpDialog_EvVereinEdit(AfpDialog_EventEdit):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        super(AfpDialog_EvVereinEdit, self).__init__( *args, **kw)
        self.SetTitle("Vereinssparte")
        if self.debug: print("AfpDialog_EvVereinEdit.init")

    ## set up dialog widgets for flavour "Verein"
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.label_T_Agent = wx.StaticText(panel, -1, label="Verein:", pos=(16,11), size=(50,18), name="T_Agent")
        self.label_AgentName = wx.StaticText(panel, -1, label="", pos=(78,10), size=(498,20), name="AgentName")
        self.labelmap["AgentName"] = "AgentName.EVENT"
        
        self.label_T_Bez = wx.StaticText(panel, -1, label="&Sparte:", pos=(16,37), size=(50,18), name="T_Bez")
        self.text_Bez = wx.TextCtrl(panel, -1, value="", pos=(76,35), size=(200,22), style=0, name="Bez")
        self.textmap["Bez"] = "Bez.EVENT"
        self.text_Bez.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_T_Kenn = wx.StaticText(panel, -1, label="&SpartenNr:", pos=(280,37), size=(60,18), name="T_Kenn")
        self.text_Kenn = wx.TextCtrl(panel, -1, value="", pos=(350,35), size=(80,22), style=0, name="Kenn")
        self.textmap["Kenn"] = "Kennung.EVENT"
        self.text_Kenn.Bind(wx.EVT_SET_FOCUS, self.On_setKenn)
        self.text_Kenn.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_Anmeldungen = wx.StaticText(panel, -1, label="", pos=(458,37), size=(24,18), name="Anmeldungen")
        self.labelmap["Anmeldungen"] = "Anmeldungen.EVENT"
        self.label_TTeil = wx.StaticText(panel, -1, label="Mitglieder", pos=(484,37), size=(78,18), name="TTeil")
        self.label_T_Ort = wx.StaticText(panel, -1, label="Ort:", pos=(16,68), size=(50,18), name="T_Ort")
        self.choice_Ort = wx.Choice(panel, -1,  pos=(78,60), size=(474,30),  choices=[],  name="COrt")      
        self.choicemap["COrt"] = "Name.TName"
        self.Bind(wx.EVT_CHOICE, self.On_COrt, self.choice_Ort)  
 
        self.label_TBem = wx.StaticText(panel, -1, label="&Beiträge:", pos=(10,100), size=(56,18), name="TBem")
        #self.list_Preise = wx.ListBox(panel, -1, pos=(298,120), size=(258,86), name="Preise")
        self.list_Preise = wx.ListBox(panel, -1, pos=(74,95), size=(482,110), name="Preise")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Preise, self.list_Preise)
        self.listmap.append("Preise")
        #self.text_Bem = wx.TextCtrl(panel, -1, value="", pos=(348,95), size=(208,110), style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="Bem")
        #self.textmap["Bem"] = "Bem.EVENT"
        #self.text_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)

        self.check_Kopie = wx.CheckBox(panel, -1, label="Kopie", pos=(10,226), size=(70,20), name="Kopie")
        self.check_Kopie.SetValue(True)
        self.check_Kopie.Enable(False)
        self.button_Neu = wx.Button(panel, -1, label="&Neu", pos=(80,220), size=(90,30), name="Neue Sparte")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)
        self.button_IntText = wx.Button(panel, -1, label="Te&xt", pos=(300,220), size=(80,30), name="IntText")
        self.Bind(wx.EVT_BUTTON, self.On_Text, self.button_IntText)
        self.setWx(panel, [390, 220, 80, 30], [480, 220, 80, 30]) 
        
    ## populate the 'Preise' list, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_Preise(self):
        liste = ["--- Neuen Beitrag hinzufügen ---"]
        AfpDialog_EventEdit.Pop_Preise(self, liste)
    
    ## get preset value for 'Kennung' 
    # @param preset - preset string -not used here
    def get_kenn_preset(self, preset):
        return self.data.get_value("Tag.Verein")
        
    ## complete data if plain dialog has been started 
    # overwritten from AfpDialog_EventEdit
    # @param data - SelectionList where data has to be completed
    def complete_data(self, data):
        if not "Bez" in data:  
            data["Bez"] = "Hauptverein" 
            if not "Art" in data: data["Art"] = self.flavour
        if not "Art" in data: data["Art"] = "Sparte"
        data["ErloesKt"] = "EBT"
        AfpDialog_EventEdit.complete_data(self, data)
        return data

    ## fill in available route data
    # overwritten from AfpDialog_EventEdit
    def get_route_data(self):
        routes, routenr = AfpEvClient_getRouteNames(self.data.globals.get_mysql())
        routetext = " --- Neuer Veranstaltungsort --- "
        return routes, routenr, routetext

    ## handle dialog to get new route name
    # overwritten from AfpDialog_EventEdit
    def get_new_route_name(self):
        Ok = False
        rname = None
        KNr = AfpLoad_AdAusw(self.data.get_globals(),"ADRESATT","AttName", "", "Attribut = \"Veranstaltungsort\"", "Bitte Adresse des neuen Veranstaltungsortes auswählen.")
        #rname, KNr = AfpAdresse_addAttributToAdresse(self.data.get_globals(),"Veranstaltungsort","Bitte Adresse des neuen Veranstaltungsortes auswählen.")
        if KNr: 
            adresse = AfpAdresse(self.data.get_globals(), KNr, None, self.data.get_globals().is_debug())
            rname = adresse.get_name()
            Ok = True
            KNr = 0
        if Ok and rname and rname in self.routes:
            AfpReq_Info("Name schon in Ortsliste enthalten!","Bitte dort auswählen.","Warnung")
            Ok = False
        return Ok, rname, KNr

 
## loader routine for dialog EventEdit flavour 'Verein'
# @param data - AfpEvent data to be loaded
# @param flavour - if given, flavour (certain type) of dialog 
# @param edit - if given, flag if dialog should open in edit modus
def AfpLoad_EvVereinEdit(data, flavour = None, edit = False):
    DiVerein = AfpDialog_EvVereinEdit(flavour)
    new = data.is_new()
    DiVerein.attach_data(data, new, edit)
    DiVerein.ShowModal()
    Ok = DiVerein.get_Ok()
    DiVerein.Destroy()
    return Ok    
        
## allows the display and manipulation of a EvClient data, flavour 'Verein' 
class AfpDialog_EvMemberEdit(AfpDialog_EvClientEdit):
    ## initialise dialog
    def __init__(self, *args, **kw): 
        super().__init__(*args, **kw)
        self.modifyWx()
        self.verein = None
        self.extra_provision_possible = False
        self.extra_provision_default = 0 #No provision flag for extra price -> extra price only for current year
        self.storno = None
        self.stornodirect = False
        self.storno_adressstatus = None
        self.stornotext = None
        self.stornodata = None
        self.stornofile = None
        self.initial_price = None
        self.merge_sameRechData = True
        
    ##  modify Wx objects defined in parent class
    # @param typ - if given, typ of special dialog modifications
    def modifyWx(self, typ=None):
        #print ("AfpDialog_EvMemberEdit.modifyWx:", typ)
        if typ is None:
           #self.label_Datum.Enable(False)
            self.label_TGrund.SetLabel("&Beitrag:")
            self.label_TPreis.SetLabel("&Gesamt:")
            self.button_Agent.SetLabel("&Zahler")
            self.button_Storno.SetLabel("A&bmeldung")
            self.check_Mehrfach.SetLabel("&Familie")  
            self.label_TZArt.Show(True)
            self.combo_ZArt.Show(True)
            self.combomap["ZArt"] = "ZahlArt.ANMELD"
        elif typ == "Verein":
            self.combo_Ort.Show(True)
            self.combomap["Ort"] = "Ort.TORT"
            if "Buero" in self.labelmap: self.labelmap.pop("Buero")
            self.label_TAb.Show(True)
            self.label_TAb.SetLabel("&Liegeplatz:")
        elif "Sparte" in typ:
            self.label_TExtra.SetLabel("Sparten und Extra:")
            self.combo_Ort.Show(False)
            self.label_TAb.Show(False)
            if "Ort" in self.combomap: self.combomap.pop("Ort")
 
    ## attaches data to this dialog overwritten from AfpDialog
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        routenr = data.get_value("Route.EVENT")
        self.route = AfpEvRoute(data.get_globals(), routenr, None, self.debug, True)
        self.verein = data.get_event()
        self.modifyWx(data.get_value("Art.EVENT"))
        super(AfpDialog_EvMemberEdit, self).attach_data(data, new, editable)
        self.check_family()
        self.check_finance_moduls()

    ## set possible entries for 'Zustand'-list in dialog \n
    def get_ZustandList(self):
        return ["Reservierung","Gast","Anmeldung"]
    ## read values from dialog and invoke writing into data         
    def store_data(self):
        if self.storno:
            # set the cancel stamp here
            self.data = self.set_Storno(self.data)
            if self.stornodata:
                for i in range(len(self.stornodata)):
                    self.stornodata[i] = self.set_Storno(self.stornodata[i])
                if self.sameRechIndex is None: # only needed to invoke possible sameRechData storage
                    self.sameRechIndex = 0
        if self.stornofile:
            if self.storno:
                datum = self.storno
            else:
                datum = self.data.get_value("InfoDat")
            data = AfpEv_addRegToArchiv(self.data, "exit", self.stornofile, Afp_toString(datum))
            if data and not data == True: 
                self.data = data
                self.change_preis = True # assure data to be stored
        if self.zustand and self.zustand != "Storno" and self.zustand != self.data.get_value("Zustand"): 
            if self.data.get_value("Abmeldung"):
                self.data.set_value("Abmeldung", None)
            if self.data.get_value("Info") and "Abmeldung" in self.data.get_value("Info"):
                self.data.set_value("Info", "")
        super(AfpDialog_EvMemberEdit, self).store_data()
        if self.stornodirect:
            self.event.add_client_count(-1)
            self.event.store()
            
    ## set 'Storno' and 'PreStorno' values in data
    # @param data - data object, where values have to be set
    def set_Storno(self, data):
        if self.stornodirect: self.zustand = "Storno"
        else: self.zustand = "PreStorno"
        if self.storno_adressstatus: data.set_value("Kennung.ADRESSE", self.storno_adressstatus)
        data.set_value("Zustand", self.zustand)
        data.set_value("InfoDat", self.storno)
        if self.stornotext: 
            data.set_value("Info",  self.stornotext + " " + Afp_toString(self.storno))
        else:
            data.set_value("Info",  Afp_toString(self.storno) + " Abmeldung" )
        if self.stornodirect: 
            data.set_value("Abmeldung", self.storno)
            data.deactivate_sepa()
        #print "AfpDialog_EvMemberEdit.set_Storno:", data, data.view()
        return data
        
    ## complete data before storing
    # @param data - data to be completed
    def complete_data(self, data): 
        #print "AfpDialog_EvMemberEdit.complete_data:", data
        if not "IdNr" in data:
            IdNr= self.event.generate_IdNr() 
            data["IdNr"] = IdNr 
        if "Preis" in data and data["Preis"] > 0.0:
            data["Zahlung"] = 0.0
        super(AfpDialog_EvMemberEdit, self).complete_data(data)
        return data
        
    ## check if finence moduls are available
    def check_finance_moduls(self):
        if self.finance_moduls is None:
            self.finance_moduls = Afp_importAfpModul("Finance", self.data.get_globals())
    ## check if 'family' is allowed for 'verein'-member
    def check_family(self):
        enable = True
        if  self.data and self.data.get_globals().get_value("strict-family-handling","Event"):
            enable = False
            #print "AfpDialog_EvMemberEdit.check_family:", self.data.pricename_holds("Familie"), self.data.pricename_holds("Familien")
            if self.data.pricename_holds("Familie") and not self.data.pricename_holds("Familien"):
                enable = True
            elif self.sameRechData and self.sameRechData[0]:
                #print "AfpDialog_EvMemberEdit.check_family RechNr:", self.sameRechData[0] ,  self.sameRechData[0].pricename_holds("Familie"), self.sameRechData[0].pricename_holds("Familien")
                if self.sameRechData[0].pricename_holds("Familie") and not self.sameRechData[0].pricename_holds("Familien"):
                    enable = True
        self.check_Mehrfach.Enable(enable)
        
    ## resign from the club
    # @param onlyfile - flag for file selection only, default: False
    def resign(self, onlyfile = False):
        dat = self.data.get_resign_date()
        if onlyfile:
            text1 = "Abmeldung von " + self.data.get_name() +  " von '" + self.data.get_value("Bez.EVENT") + "' der " + self.data.get_value("Name.Veranstalter") + " aussuchen?"
        else:
            text1 = self.data.get_name() +  " von '" + self.data.get_value("Bez.EVENT") + "' der " + self.data.get_value("Name.Veranstalter") + " abmelden?"
        dir = self.data.get_globals().get_value("docdir")
        fname, Ok = AfpReq_FileName(dir, text1, "*.pdf" , True)
        stext = None
        if onlyfile:
            if Ok and fname:
                self.stornofile = fname
        else:
            if not Ok:
                fname = None
                stext, Ok = AfpReq_Text("Keine Abmeldung ausgewählt,","bitte Begründung für den Austritt eingeben,\n z.B. 'verstorben' bei Tod, 'freigesetzt' bei Rauswurf","", "Abmeldung")
            if Ok and (stext or fname):
                if fname:
                    sdat = Afp_dateString(fname)
                    if sdat:
                        dat = self.data.get_resign_date(sdat)
                if self.sameRechNr:
                    liste = [["Austrittsdatum",dat]]
                    if not self.sameRechData:
                        self.sameRechData = []
                        for rnr in self.sameRechNr:
                            self.sameRechData.append(self.get_client(rnr))
                    datas = []
                    for data in self.sameRechData:
                        if data.get_value() == self.data.get_value(): continue
                        liste.append(data.get_name())
                        datas.append(data)
                    text2 = "Bitte Austrittsdatum eingeben und weitere austretende Mitglieder anwählen!"
                    values = AfpReq_MultiLine(text1, text2, ["Text","Check"], liste, "Abmeldungen")
                    if values:
                        dat = Afp_ChDatum(values[0])
                        self.stornodata = []
                        for i in range (1,len(values)):
                            if values[i]: self.stornodata.append(datas[i-1])
                    else:
                        Ok = False
                else:
                    text2 = "Die Kündigung wird wirksam zum:"
                    dat, Ok = AfpReq_Date(text1, text2, dat, "Abmeldung")
            if Ok and dat:
                self.storno = Afp_fromString(dat)
                if self.storno < self.data.get_globals().today():
                    status = None
                    text2 = "Das Austrittsdatum (" + dat + ") liegt in der Vergangenheit, Kündigung direkt umsetzen"
                    if stext == "verstorben":
                        text2 += " und Adresse deaktivieren"
                        status = 9
                    elif stext == "freigesetzt":
                        text2 += " und Adresse markieren"
                        status = 6
                    text2 += "?"
                    Ok = AfpReq_Question(text1, text2, "Abmeldung")
                    if Ok: 
                        self.stornodirect = True
                        if status: self.storno_adressstatus = status
                if fname:
                    self.stornofile = fname
                if stext:
                    self.stornotext = stext
            else:
                self.storno = None
    ## show resignment file from archiv
    def show_resignment_file(self):
        data = self.data.get_value_rows("ARCHIV")
        ok = False
        #print "AfpDialog_EvMemberEdit.show_resignment_file:", data
        if data:
            fname = None
            for row in data:
                if row[3] == "Abmeldung":
                    fname = row[5]
            if fname:
                fpath = Afp_addRootpath(self.data.get_globals().get_value("archivdir"), fname)
                Afp_startFile(fpath,self.data.get_globals(), self.debug, True)
                ok = True
        return ok

    ## Interface to activate, deactivate or generate a SEPA direct debit mandat
    def select_SEPAdd(self):
        changed = False
        res = None
        while res is None:
            rows = self.data.get_value_rows("ARCHIV", "Datum,Bem,Gruppe,Typ,Art")
            liste = []
            indices = []
            active = []
            act_cnt = 0
            for i in range(len(rows)):
                row = rows[i]
                if row[4] == "SEPA-DD":
                    if row[3] == "Aktiv":
                        aktiv = True
                        act_cnt += 1
                    else:
                        aktiv = False
                    liste.append([Afp_toString(row[0]) + " IBAN:" + row[1] + " BIC:" + row[2], aktiv])
                    indices.append(i)
                    active.append(aktiv)
            if act_cnt > 1 and liste[-1][1] == True: # propably freshly added mandate
                for i in range(len(liste)-1):
                    liste[i][1]  = False
            res = AfpReq_MultiLine("Bitte das entsprechende SEPA Mandat für " + self.data.get_name() +" aktivieren oder deaktivieren!", "Nur ein Mandat kann als 'Aktiv' gekennzeichnet werden. \nBei Kennzeichnung mehrerer wird das erste Mandat ausgewählt.","Check",liste,"SEPA-Mandat aktivieren", 250, "Neu")
            #print ("AfpDialog_EvMemberEdit.select_SEPAdd Mandat:", res, changed, liste) 
            if res:
                first = True
                for i in range(len(res)):
                    if res[i] and first:
                        if not active[i] : 
                            self.data.set_data_values({"Typ": "Aktiv"},"ARCHIV", indices[i])
                            changed = True
                        first = False
                    elif active[i]:
                        self.data.set_data_values({"Typ": "Inaktiv"},"ARCHIV", indices[i])
                        changed = True
            elif res is None:
                changed = self.add_SEPAdd() 
        return changed
    ## Routine to add SEPA direct debit mandat to sepa object
    def add_SEPAdd(self):
        if self.finance_moduls and len(self.finance_moduls) > 1 and self.finance_moduls[1]:
            #self.data.deactivate_sepa()
            client =  self.finance_moduls[1].AfpFinance_addSEPAdd(self.data)
            if client: 
                bic, iban = client.get_aktiv_sepa("Gruppe,Bem")
                print ("AfpDialog_EvMemberEdit.add_SEPAdd:", bic, iban)
                adresse = AfpAdresse(client.get_globals(), client.get_value("KundenNr"))
                adresse.add_bankaccount(bic, iban)
                adresse.store()
                self.data = client
                return True
        return False
    ## Routine to provide  SEPA direct debit mandat for this client
    def provide_SEPAdd(self):
        zahlart = None
        changed = self.select_SEPAdd()
        row = self.data.get_aktiv_sepa("Datum")
        #print("AfpDialog_EvMemberEdit.provide_SEPAdd:", changed, row)
        if row and row[0]: 
            text = "SEPA-Mandat " + Afp_toString(row[0])
            zahlart = text
        elif changed:
            zahlart = "Rechnung"
            wx.CallAfter(self.combo_ZArt.SetValue, "Rechnung")
        return zahlart
    ## Routine to provide additional Information for this Retoure
    def provide_Retoure(self):
        text = ""
        text, ok = AfpReq_Text("SEPA Lastschrift ist zurückbehalten worden.", "Bitte Rückgabegrund der Lastschrift angeben:", text, "SEPA-Retoure")
        if ok:
            info = self.data.get_value("Info")
            if info: self.data.set_value("Info",info + " '" + text + "'")
            else: self.data.set_value("Info","'" + text +"'")
        return ok
    ## Routine to provide the timeframe of the payment of an institution
    def provide_ARGE(self):
        zahlart = None
        liste = [["Startdatum:",""], ["Enddatum:",""]]
        res = AfpReq_MultiLine("Beitragszahlungen werden von einer Behörde (Stadt/Arge) übenommen.", "Bitte Zeitraum der Übernahme angeben:", "Text", liste, "Behörden-Zahlungen")
        if res:
            found = False
            for i in range(len(res)):
                if res[i]:
                    res[i] = Afp_ChDatum(res[i])
                    found = True
            if found:
                zahlart = "ARGE bis " + res[1]
                text = zahlart + " Beginn: " + res[0]
            else:
                today = self.data.get_globals().today()
                zahlart = "ARGE beantragt " + Afp_toString(today)
                text = zahlart
            info = self.data.get_value("Info")
            if info: self.data.set_value("Info",info + " '" + text + "'")
            else: self.data.set_value("Info","'" + text +"'")
        return zahlart
    ## Eventhandler BUTTON - graphic pick for dates, 
    # - not applicable for 'Members' 
    # @param event - event which initiated this action   
    def On_Set_Datum(self,event = None):
        return
 
   ## Eventhandler BUTTON - select travel agency
    # @param event - event which initiated this action   
    def On_Agent(self,event):
        if self.debug: print("AfpDialog_EvMemberEdit Event handler `On_Agent'")
        if  self.data.get_value("AgentNr"):
            name = self.data.get_value("Name.Agent")
        else:
            name = self.data.get_value("Name.ADRESSE")
        #print ("AfpDialog_EvMemberEdit.On_Agent:", name, self.data.get_value("AgentNr"), self.data.get_selection("Agent").data)
        #print ("AfpDialog_EvMemberEdit.On_Agent:", name, self.data.get_value("AgentNr"))
        text = "Bitte Ansprechpartner für diese Anmeldung auswählen:"
        KNr = AfpLoad_AdAusw(self.data.get_globals(), "ADRESSE", "Name", name, None, text)
        changed = False
        if KNr:
            self.agent = AfpAdresse(self.data.get_globals(),KNr)
            name = self.agent.get_name()
            self.label_Buero.SetLabel(name)
            changed = True
            if not self.data.get_aktiv_sepa():
                sepa = self.agent.get_active_SEPA()
                if sepa:
                    Ok = AfpReq_Question("Aktives SEPA-Mandat von " + name + " gefunden!","SEPA-Mandat auch für Beiträge von " + self.data.get_name() + " nutzen?", "SEPA_Mandat nutzen?")
                    if Ok:
                        sepa["Art"] = "SEPA-DD"
                        sepa["Typ"] = "Aktiv"
                        self.data.add_to_Archiv(sepa)
                        text = "SEPA-Mandat " + Afp_toString(sepa["Datum"])
                        self.zahlart = text
                        self.combo_ZArt.SetValue(text)
                        #wx.CallAfter(self.combo_ZArt.SetValue, text)
        else:
            if self.data.get_value("AgentNr") or self.agent:
                agent = self.label_Buero.GetLabel()
                #if ":" in agent:
                #    agent = agent.split(":")[1].strip()
                Ok = AfpReq_Question("Anmeldung nicht mehr über " + agent + "?","Eintrag löschen?", agent + " löschen?")
                if Ok: 
                    if self.agent: self.agent = None
                    else: self.agent = False
                    self.label_Buero.SetLabel("")
                    changed = True
        if changed:
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()  

    ## event handler COMBOBOX - select the type of payment
    # @param event - event which initiated this action   
    def On_ZahlungsArt(self,event):
        if self.debug: print("AfpDialog_EvMemberEdit Event handler `On_ZahlungsArt'")
        if self.data.get_value("Preis") < 0.01 and self.data.get_value("Bezeichnung.Preis") == "Familienmitglied":
            AfpReq_Info("Keine Beitragszahlungen von " + self.data.get_name() + "!","Zahlungsart bitte über Hauptzahler ändern.", "Familienanmeldung!")
            self.combo_ZArt.SetValue("")
        else:
            sel = self.combo_ZArt.GetValue()
            if sel == "SEPA" or sel == "ARGE":
                if sel == "ARGE":
                    zahlart = self.provide_ARGE()
                else:
                    zahlart = self.provide_SEPAdd()
                if zahlart: self.zahlart = zahlart
                if self.zahlart:
                    wx.CallAfter(self.combo_ZArt.SetValue, self.zahlart)
                else:
                    wx.CallAfter(self.combo_ZArt.SetValue, self.data.get_value("ZahlArt"))
            elif sel == "Retoure":
                ok = self.provide_Retoure()
                if ok:
                    self.zahlart = sel
            else:
                self.zahlart = sel
            if not self.zahlart or self.zahlart[:4] != "SEPA":
                self.data.deactivate_sepa()
            if  self.zahlart != "Retoure" and  self.zahlart[:4] != "ARGE" :
                info = self.data.get_value("Info")
                if info and "'" in info: 
                    self.data.set_value("Info",info.split("'")[0].strip())
        event.Skip()
    ##Eventhandler BUTTON - delete client \n
    # @param event - event which initiated this action   
    def On_Storno(self, event):
        if self.debug: print("AfpDialog_EvMemberEdit Event handler `On_Storno'")
        if self.data.get_value("Zustand") == "PreStorno":
            shown = self.show_resignment_file()
            if not shown:
                self.resign(True)
        elif not self.data.get_value("Zustand") == "Storno":
            #if self.sameRechData and len(self.sameRechData) > 1:
                # self.isolate_member()
            self.resign()
            if self.storno:
                self.label_Zustand.SetLabel("Abmeldung " + Afp_toString(self.storno))
        #print "AfpDialog_EvMemberEdit.On_Storno:", self.storno, self.stornodata, self.stornofile
        self.Set_Editable(True)
        event.Skip()
 
    
    ## Eventhandler LISTBOX: extra price is doubleclicked - overwritten from AfpDialog_EvClientEdit
    # @param event - event which initiated this action   
    def On_Anmeld_Preise(self,event):
        if self.debug: print("AfpDialog_EvMemberEdit Event handler `On_Anmeld_Preise'")
        if self.verein.has_auxilary_sections():
            index = self.list_Preise.GetSelections()[0] - 2
            row = self.get_Preis_row(index)
            #print ("AfpDialog_EvClientEdit.On_Anmeld_Preise row:", row)
            if row:
                self.actualise_preise(row, index)
                self.change_preis = True
            elif row is None:
                self.data.delete_row("AnmeldEx", index)
            #print ("AfpDialog_EvClientEdit.On_Anmeld_Preise ANMELDEX:", self.data.get_selection("ANMELDEX").data)        
            today = self.data.get_globals().today()
            if self.data.is_new() or (self.data.get_value("Anmeldung").month == today.month and self.data.get_value("Anmeldung").year == today.year): 
                removed = self.data.remove_extra_price("Beitragsfrei")
                #print ("AfpDialog_EvClientEdit.On_Anmeld_Preise removed:", removed)
                if removed:
                    self.data.update_prices()
                    self.data.add_partitial_price(self.data.get_value("Preis"), None, self.data.get_value("Anmeldung"))
                    self.data.update_prices()
                    self.label_Extra.SetLabel(self.data.get_string_value("Extra"))
                    self.label_Preis.SetLabel(self.data.get_string_value("Preis"))
            self.Pop_Preise()
            #self.Pop_label() # do not pop labels, as changed prices have been written there
        else:
            super().On_Anmeld_Preise()
        self.check_family()
        event.Skip()
    ## select or generate new basic or extra price \n
    # overwritten from AfpDialog_EvClientEdit
    def get_Preis_row(self, index):
        res_row = ""
        if self.verein.has_auxilary_sections():
            Ok = False
            name = self.data.get_name()                
            if index == -1:
                value, res_row = self.get_TypPreis("Grund")
                Ok = not value is None
                if self.sameRechData and self.data != self.sameRechData[0]:
                    # trigger writing only into the main registration
                    index = -3
            elif index == -2:
                value, res_row = self.get_TypPreis("Sparte,Aufschlag", "Sparten- und Extrapreis", " --- freien Extrapreis eingeben --- ", "Sparten")
                Ok = not value is None
            else:
                value = 0
                row = self.data.get_value_rows("AnmeldEx", "Preis,NoPrv,Kennung,Bezeichnung", index)[0]
                if "(" in row[3]:
                    name2 = Afp_between(row[3],"(", ")")[0][0]
                    no_auto = False
                    if row[2]:
                        no_auto = self.verein.price_is_typ(row[2], "Grund")
                    if no_auto:
                        Ok = AfpReq_Question("Eigenen Mitgliedsbeitrag für " + name2 + " aus der Anmeldung von " + name + " löschen?", Afp_toString(row[0]) + " für " + row[3],"Löschen")
                        value = -2
                        preisnr = 0
                        anr = 0
                    else:
                        AfpReq_Info("Automatischer Eintrag von Familienanmeldung!","Eintrag bitte über die Anmeldung von '" + name2 + "' ändern.")
                        return res_row
                #print ("AfpDialog_EvMemberEdit.get_Preis_row Sparte bearbeiten:", index, row)
                extra = row[0]
                noPrv = row[1]
                if value != -2:
                    if row[2]:
                        preisnr, anr = AfpEvVerein_splitSectionPriceNumber(row[2])
                        if anr and "(" in row[3]:
                            text = row[3].split("(")[1] [:-1]+ " über " + name
                        else:
                            text = name
                        #print ("AfpDialog_EvMemberEdit.get_Preis_row splitted:", row[2], preisnr, anr)
                        liste = ["--- Aus der Sparte abmelden ---"]
                        listentries = [None]
                        idents = [-2]
                        rows = self.verein.get_prices_of_section(preisnr, "Preis,Bezeichnung,NoPrv,PreisNr,Typ")
                        for row in rows:
                            liste.append(Afp_toFloatString(row[0]).rjust(10) + "  " + Afp_toString(row[1]))
                            listentries.append(row)
                            idents.append(row[3])
                        value, Ok = AfpReq_Selection("Spartenpreis für die Anmeldung von " + text + " ändern?", "Bitte neuen Spartenpreis auswählen!", liste, "Sparte", idents)
                    else:
                        Ok = AfpReq_Question("Extrapreis löschen?", Afp_toString(row[0]) + " für " + row[3],"Löschen")
                        value = -2
                        preisnr = 0
                        anr = 0
                if Ok and not value == preisnr:            
                    self.add_extra_preis_value(-extra)
                    if not noPrv: self.add_prov_preis_value(-extra)
                    self.change_preis = True
                    if value == -2:
                        res_row = None
                        #print ("AfpDialog_EvMemberEdit.get_Preis_row delete:", row[2], preisnr,self.data.get_value())
                        if self.sameRechData and self.data != self.sameRechData[0]:
                            kennung = AfpEvVerein_setSectionPriceNumber(preisnr, self.data.get_value())
                            self.sameRechData[0].remove_extra_price(kennung)
                            self.sameRechData[0].update_prices()
                        elif anr and self.sameRechData: # not used at the moment
                            for entry in self.sameRechData:
                                if anr == entry.get_value():
                                    entry.remove_extra_price(preisnr)
                    else:
                        res_row = listentries[idents.index(value)]
            if Ok and value == -1:
                res_row = self.get_manualPreis("Extrapreis")
            if Ok and index != -1 and res_row:
                if self.sameRechData and self.data != self.sameRechData[0]:
                    new_data = {"Preis": res_row[0], "NoPrv": res_row[2], "Typ": res_row[4]} 
                    new_data["Bezeichnung"] = res_row[1] + " (" + name + ")"
                    anr = self.data.get_value()
                    new_data["Kennung"] = AfpEvVerein_setSectionPriceNumber(res_row[3], anr)
                    event_prices = self.verein.get_prices_of_section(res_row[3], "PreisNr")
                    for i in range(len(event_prices)):
                        event_prices[i] = AfpEvVerein_setSectionPriceNumber(event_prices[i][0], anr)
                    self.sameRechData[0].replace_indirect_section_price(new_data, event_prices)
                    self.sameRechData[0].update_prices()
                    res_row[0]= 0.0
                    if index == -3: res_row = ""
        else:
            res_row = super().get_Preis_row(index)
        return res_row

   ##Eventhandler BUTTON - add new client \n
    # @param event - event which initiated this action   
    def On_Anmeld_Neu(self,event):
        if self.debug: print("AfpDialog_EvMemberEdit Event handler `On_Anmeld_Neu'")
        super(AfpDialog_EvMemberEdit, self).On_Anmeld_Neu()
        if self.check_Mehrfach.GetValue():
            self.data.set_family_price()
            self.merge_extra_prices(True)
            self.Pop_Preise()
            self.check_family()
            self. Populate()
        event.Skip()
    ## get multiflags according to multi checkbox
    # overwritten from AfpDialog_EvClientEdit
    def get_multiflags(self):
        multi = self.check_Mehrfach.GetValue()
        if multi:
            return [True, True, False, False]
        return multi

    ##  get a client object with given identnumber
    # overwritten from AfpDialog_EvEventEdit
    # @parm ANr - if given, identifier
    # -                     if = True new empty client is delivered
    def get_client(self, ANr = None):
        if ANr == True: return AfpEvMember(self.data.globals)
        if ANr is None: ANr = self.data.get_value()
        return  AfpEvMember(self.data.globals, ANr)
        
## loader routine for dialog EvMemberEdit
# @param data - data to be proceeded
# @param edit - if given, flag if dialog should open in edit modus
# @param onlyOk - flag if only the Ok exit is possible to leave dialog, used for 'Umbuchung'
def AfpLoad_EvMemberEdit(data, edit = False, onlyOk = None):
    if data:
        DiEvMember = AfpDialog_EvMemberEdit(style=wx.RESIZE_BORDER|wx.DEFAULT_DIALOG_STYLE)
        new = data.is_new()
        DiEvMember.attach_data(data, new, edit)
        if onlyOk: DiEvMember.set_onlyOk()
        DiEvMember.ShowModal()
        Ok = DiEvMember.get_Ok()
        if onlyOk: Ok = DiEvMember.get_RechNr()
        DiEvMember.Destroy()
        return Ok
    else: return False
    
## load member edit dialog only by given id (needed for address screen)
# @param globals - global variabloes given, including mysql connection
# @param ANr - identifiers of this member
def AfpLoad_EvMemberEdit_fromANr(globals, ANr):
    data = AfpEvMember(globals, ANr)
    Ok = AfpLoad_EvMemberEdit(data)
    return Ok
    
    
