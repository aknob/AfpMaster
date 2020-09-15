#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvScreen_Verein
# AfpEvScreen_Verein module provides the graphic screen to access all data of the Afp-'Verein' modul 
# it holds the class
# - AfpEvScreen_Verein
#
#   History: \n
#        10 Apr. 2019 - integrate all devired flavour classes into one deck - Andreas.Knoblauch@afptech.de
#        10 Jan 2019 - inital code generated - Andreas.Knoblauch@afptech.de


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

import wx
import wx.grid

import AfpBase
from AfpBase import *
from AfpBase.AfpUtilities import *
from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile
from AfpBase.AfpDatabase import *
from AfpBase.AfpDatabase.AfpSQL import AfpSQL
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import Afp_archivName, Afp_startFile, Afp_getBirthdayList, Afp_orderSelectionLists
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Selection, AfpReq_Question, AfpReq_Text, AfpReq_Date, AfpDialog
from AfpBase.AfpBaseDialogCommon import AfpLoad_DiReport
from AfpBase.AfpBaseScreen import AfpScreen, Afp_loadScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_AdIndiAusw, AfpLoad_DiAdEin_fromSb
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

import AfpEvent
from AfpEvent import AfpEvRoutines, AfpEvDialog, AfpEvScreen
from AfpEvent.AfpEvScreen import AfpEvScreen
from AfpEvent.AfpEvRoutines import *
from AfpEvent.AfpEvDialog import AfpLoad_EvAusw, AfpDialog_EventEdit, AfpDialog_EvClientEdit, AfpLoad_EvClientEdit

## routine to execute prepared cancellations
# @param verein - AfpEvVerein object to be worked on
def AfpEvVerein_closeYear(verein):
    verein.reset_payment()
    AfpEvVerein_exeStorno(verein)
    
## routine to execute prepared cancellations
# @param verein - AfpEvVerein object to be worked on
def AfpEvVerein_exeStorno(verein):
    leftover = verein.execute_cancel()
    if leftover is None:
        AfpReq_Info("Keine Kündigungen vorgemerkt,".decode("UTF-8"),"keine Kündignungen durchgeführt!".decode("UTF-8"),"Kündigungen umsetzen".decode("UTF-8"))
    elif not leftover:
        AfpReq_Info("Kündigungen umgesetzt!".decode("UTF-8"),"Keine Nacharbeiten nötig!".decode("UTF-8"),"Kündigungen umsetzen".decode("UTF-8"))
    else:
        for left in leftover:
            client = AfpEvMember(verein.get_globals(), left)
            ok = AfpLoad_EvMemberEdit(client, True, True)

## baseclass for club handling         
class AfpEvVerein(AfpEvent):
    ## initialize AfpEvent class
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
        if not self.get_value("AgentNr") and sb:
            KNr = sb.get_value("KundenNr.ADRESSE")
            Name = sb.get_value("Name.ADRESSE")
            print "AfpEvVerein Konstruktor, Agent:", Name, KNr
            self.set_value("AgentNr.EVENT", KNr)
            self.set_value("AgentName.EVENT", Name)
        # overwrite ARCHIV
        days = globals.get_value("show-archiv-interval-Verein","Event")
        if not days: days = 365
        past = Afp_toInternDateString(Afp_addDaysToDate(globals.today(), days, "-"))
        self.selects["ARCHIV"] = [ "ARCHIV","TabNr = EventNr.EVENT AND Tab = \"EVENT\" AND Datum >= \"" + past + "\""] 
        self.selects["AUSGABE"] = [ "AUSGABE","Modul = \"Event\" AND Art = Art.EVENT"] 
        self.selects["Anmeldung"] = [ "ANMELD","EventNr = EventNr.EVENT AND Zustand = \"Anmeldung\"","AnmeldNr"] 
        self.selects["PreStorno"] = [ "ANMELD","EventNr = EventNr.EVENT AND Zustand = \"PreStorno\"","AnmeldNr"] 
        self.selects["Verein"] = [ "ADRESATT","KundenNr = AgentNr.EVENT AND Attribut = \"Verein\""] 
        if complete: self.create_selections()
        if self.debug: print "AfpEvVerein Konstruktor, EventNr:", self.mainvalue

    ## execute cancel action for all prepared member
    def execute_cancel(self):
        leftover = None
        rows = self.get_value_rows("PreStorno", "AnmeldNr") 
        if rows:
            leftover = []
            cancelled = []
            for row in rows:
                cancelled.append(row[0])
                client = self.get_client(row[0])
                if leftover and row[0] in leftover:
                    leftover.pop(leftover.index(row[0]))
                AnNrs = client.execute_cancel()
                if AnNrs:
                    for nr in AnNrs:
                        if not nr in leftover and not nr in cancelled:
                            leftover.append(nr)
                client.store()
                client.delete_from_event()
        return leftover
        
    ## reset payment for new financial period
    def reset_payment(self):
        rows = self.get_value_rows("Anmeldung", "AnmeldNr")
        if rows:
            for row in rows:
                client = self.get_client(row[0])
                client.reset_payment()
                client.store()
    
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

    ## decide whether this event may holds a route insted of the location
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
    def get_client(self, ANr = None):
        return AfpEvMember(self.globals, ANr)

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
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["TORT"] = [ "TORT","OrtsNr = Ab.ANMELD"] 
        self.selects["ANMELDATT"] = [ "ANMELDATT","AnmeldNr = AnmeldNr.ANMELD"] 
        if complete: self.create_selections()
        if self.debug: print "AfpEvMember Konstruktor, AnmeldNr:", self.mainvalue
    
    ## execute cancel procedures if flagged \n
    # if more clients are involved, the appropriate RechNr is returned
    def execute_cancel(self):
        AnNr = None
        dat = Afp_addDaysToDate(self.get_value("InfoDat"), 31, "-")
        if self.get_value("Zustand") == "PreStorno" and self.get_globals().today() > dat:
            self.set_value("Zustand","Storno")
            lgh = self.get_value_length("RechNr")
            if lgh > 1: 
                rows = self.get_value_rows("RechNr","Zustand,AnmeldNr")
                for row in rows:
                    if row[0] == "Anmeldung": 
                        if AnNr is None:
                            AnNr = [row[1]]
                        else:
                            AnNr.append(row[1])
        #print "AfpEvMember.execute_cancel:", self.get_name(), self.get_value(), self.get_value("Zustand"), self.get_value("InfoDat"), dat, AnNr, ReNr
        return AnNr    

    ## reset payment for new financial period
    def reset_payment(self):
        zahlung = self.get_value("Zahlung")
        if zahlung:
            diff = self.get_value("Preis") - zahlung
        else:
            diff = self.get_value("Preis")
        if diff < 0: diff = 0.0
        rows = self.get_value_rows("ANMELDEX","NoPrv")
        for i in range(len(rows)-1, -1, -1):
            if rows[i][0]: self.delete_row("ANMELDEX", i)
        if diff:
            jahr = Afp_toString(self.globals.today().year - 1)
            data = {"AnmeldNr": self.get_value(), "Bezeichnung": "Restbeitrag " + jahr, "Preis": diff, "NoPrv": 1}
            self.set_data_values(data, "ANMELDEX", -1)
        preis, extra = self.gen_price()
        if zahlung is None or preis < 0.01:
            data = {"Preis": preis, "Extra": extra, "Zahlung": None, "ZahlDat":  None}
        else:
            data = {"Preis": preis, "Extra": extra, "Zahlung": 0.0, "ZahlDat":  None}
        self.set_data_values(data)
    ## generate price for actuel selections   
    def gen_price(self):
        preis = self.get_value("Preis.Preis")
        rows = self.get_value_rows("ANMELDEX","Preis")
        ex = 0.0
        for row in rows:
            ex += row[0]
        return preis + ex, ex
        
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
   ## generate identification number (membership number for "Verein")  
    def generate_IdNr(self):
        IdNr = None
        # ToDo: for different 'Sparten' in 'Verein' look for already given id
        IdNr = self.get_next_RechNr_value()
        #tag = self.get_value("Tag.Verein")
        #Extern = AfpExternNr(self.get_globals(),"Count", tag, self.debug)
        #IdNr = Extern.get_number()
        return IdNr
    ## return field to be increased to generate 'RechNr'  
    def get_RechNr_name(self):
        return "RechNr.EVENT"
    ## check if  the name of the price holds string
    # @param check - string to be checked
    def pricename_holds(self, check):
        if self.get_value("Bezeichnung.Preis") :
            return check in self.get_value("Bezeichnung.Preis")  
        else:
            return False

    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Anmeldung für den Verein".decode("UTF-8")  +  self.get_string_value("Vorname.Veranstalter") + " " +   self.get_string_value("Name.Veranstalter") 
# end of class AfpMember        
        
## Class AfpEvScreen_Verein shows 'Event' screen and handles interactions
class AfpEvScreen_Verein(AfpEvScreen):
    ## initialize AfpEvScreen_Verein, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        #self.einsatz = None # to invoke import of 'Einsatz' modules in 'init_database'
        self.clubnr = None
        self.finance_moduls = None
        self.white = wx.Colour(255, 255, 255)
        AfpEvScreen.__init__(self, debug)
        self.flavour = "Verein"
        self.SetTitle("Afp Verein")
        self.grid_sort_rows = {} # enable sorting 
        self.grid_row_selected = None
        self.dynamic_grid_col_percents = [ 5, 20, 20, 14, 14, 14, 13]
        if self.debug: print "AfpEvScreen_Verein Konstruktor"
       
    ## initialize widgets
    def InitWx(self):
       #panel = self.panel
        panel = self
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
        self.event_panel_sizer =wx.StaticBoxSizer(wx.StaticBox(panel, -1,label="Sparte"), wx.HORIZONTAL)
        self.client_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.client_panel_sizer =wx.StaticBoxSizer(wx.StaticBox(panel, -1,label="Anmeldung"), wx.VERTICAL)
        self.grid_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        
        # right BUTTON sizer
        #self.combo_Sortierung = wx.ComboBox(panel, -1, value="Mitglieder", choices=[], size=(100,30), style=wx.CB_DROPDOWN, name="Sortierung")
        self.combo_Sortierung = wx.ComboBox(panel, -1, value="Mitglieder", choices=["Mitglieder","Sparte"], size=(100,30), style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Index, self.combo_Sortierung)
        self.indexmap = {"Mitglieder":"RechNr","Sparte":"Bez"}
        
        self.button_Auswahl = wx.Button(panel, -1, label="Aus&wahl",size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Ausw, self.button_Auswahl)
        self.button_Abschluss = wx.Button(panel, -1, label="A&bschluss",size=(77,50), name="BAbschluss")
        self.Bind(wx.EVT_BUTTON, self.On_Abschluss, self.button_Abschluss)      
        self.button_Event = wx.Button(panel, -1, label="&Sparte",size=(77,50), name="BEvent")
        self.Bind(wx.EVT_BUTTON, self.On_modify, self.button_Event)
        self.button_Anmeldung = wx.Button(panel, -1, label="&Anmeldung", size=(77,50),name="BAnmeldung")
        self.Bind(wx.EVT_BUTTON, self.On_Anmeldung, self.button_Anmeldung)
        self.button_Zahlung = wx.Button(panel, -1, label="&Zahlung",size=(77,50), name="BZahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahlung)
        self.button_Dokumente = wx.Button(panel, -1, label="&Dokumente",size=(77,50), name="BDokumente")
        self.Bind(wx.EVT_BUTTON, self.On_Documents, self.button_Dokumente)
        self.button_Einsatz = wx.Button(panel, -1, label="Ein&satz",size=(77,50), name="BEinsatz")
        self.Bind(wx.EVT_BUTTON, self.On_VehicleOperation, self.button_Einsatz)               
        self.button_Einsatz.Enable(False)
        self.button_Ende = wx.Button(panel, -1, label="Be&enden",size=(77,50), name="BEnde")
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
        self.button_mid_sizer.Add(self.button_Einsatz,0,wx.EXPAND)
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
        self.combo_Filter = wx.ComboBox(panel, -1, value="Mitglieder", size=(164,20), choices=["Kandidaten","Mitglieder","Beitragszahler","Zahlung offen","Basismitglieder","Abgemeldet","Ausgetreten"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        #self.filtermap = {"Mitglieder":"Verein-Anmeldung-PreStorno","Kandidaten":"Verein-Reserv","Abgemeldet":"Verein-PreStorno","Ausgetreten":"Verein-Storno"}
        #self.filtermap = {"Mitglieder":"Verein-Anmeldung-PreStorno","Hauptmitglieder":"Verein-Anmeldung-PreStorno-Preis >= 0.01","Hauptmitglieder offen":"Verein-Anmeldung-PreStorno-Preis >= 0.01-Preis - Zahlung > 0.0","Basismitglieder":"Verein-Anmeldung","Kandidaten":"Verein-Reserv","Abgemeldet":"Verein-PreStorno","Ausgetreten":"Verein-Storno"}
        self.filtermap = {"Mitglieder":"Verein Anmeldung PreStorno","Beitragszahler":"Verein Anmeldung PreStorno Preis>=0.01","Zahlung offen":"Verein Anmeldung PreStorno Preis>Zahlung","Basismitglieder":"Verein Anmeldung","Kandidaten":"Verein Reservierung","Abgemeldet":"Verein PreStorno","Ausgetreten":"Verein Storno"}
        self.top_mid_sizer.AddStretchSpacer(1)
        self.top_mid_sizer.Add(self.combo_Filter,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
      
        # Event
        self.label_Event = wx.StaticText(panel, -1, label="", name="Verein")
        self.labelmap["Verein"] = "AgentName.EVENT"
        self.label_Sparte = wx.StaticText(panel, -1, label="", name="Sparte")
        self.labelmap["Sparte"] = "Bez.EVENT"
        self.label_Kennung = wx.StaticText(panel, -1, label="", name="Kennung")
        self.labelmap["Kennung"] = "Kennung.EVENT"
        self.label_Mitglieder = wx.StaticText(panel, -1,  label="Mitglieder:", name="LMitglieder")
        self.label_Anmeldungen = wx.StaticText(panel, -1, label="", name="Anmeldungen")
        self.labelmap["Anmeldungen"] = "Anmeldungen.EVENT"
        
        self.event_panel_sizer.AddSpacer(10)
        self.event_panel_sizer.Add(self.label_Event, 3, wx.EXPAND)
        self.event_panel_sizer.AddSpacer(10)
        self.event_panel_sizer.Add(self.label_Sparte, 3, wx.EXPAND)
        self.event_panel_sizer.Add(self.label_Kennung, 0)
        self.event_panel_sizer.AddSpacer(10)
        self.event_panel_sizer.Add(self.label_Mitglieder, 0)
        self.event_panel_sizer.Add(self.label_Anmeldungen, 0)
        self.event_panel_sizer.AddSpacer(10)
        self.event_sizer.AddSpacer(20)
        self.event_sizer.Add(self.event_panel_sizer, 1)
        
        # Client
        self.label_Typ = wx.StaticText(panel, -1, label="", name="Typ")
        self.labelmap["Typ"] = "Zustand.ANMELD"
        self.label_Typ_map = {"Anmeldung":"Mitglied","PreStorno":"Mitglied abgemeldet","Storno":"Austritt","Reservierung":"Kandidat"}
        self.label_RechNr = wx.StaticText(panel, -1, label="", name="RechNr")
        self.labelmap["RechNr"] = "RechNr.ANMELD"
        self.label_LNr = wx.StaticText(panel, -1, label="Nr:", name="LNr")
        self.label_IdNr = wx.StaticText(panel, -1, label="", name="IdNr")
        self.labelmap["IdNr"] = "IdNr.ANMELD"
        self.label_Seit = wx.StaticText(panel, -1, label="seit:", name="LSeit")
        self.label_Anmeldung = wx.StaticText(panel, -1, label="", name="Anmeldung")
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
        self.label_Vorname = wx.StaticText(panel, -1, label="", name="Vorname")
        self.labelmap["Vorname"] = "Vorname.ADRESSE"
        self.label_Name = wx.StaticText(panel, -1, label="", name="Name")
        self.labelmap["Name"] = "Name.ADRESSE"
        self.name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.name_sizer.Add(self.label_Vorname, 1, wx.EXPAND)
        self.name_sizer.AddSpacer(10)
        self.name_sizer.Add(self.label_Name, 1, wx.EXPAND)
 
        self.label_Strasse = wx.StaticText(panel, -1, label="", name="Strasse")
        self.labelmap["Strasse"] = "Strasse.ADRESSE"
       
        self.label_Plz = wx.StaticText(panel, -1, label="", name="Plz")
        self.labelmap["Plz"] = "Plz.ADRESSE"
        self.label_Ort = wx.StaticText(panel, -1, label="", name="Ort")
        self.labelmap["Ort"] = "Ort.ADRESSE"
        self.ort_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ort_sizer.Add(self.label_Plz, 1, wx.EXPAND)
        self.ort_sizer.AddSpacer(10)
        self.ort_sizer.Add(self.label_Ort, 4, wx.EXPAND)

        self.label_Telefon = wx.StaticText(panel, -1, label="", name="Telefon")
        self.labelmap["Telefon"] = "Telefon.ADRESSE"
        self.label_Handy = wx.StaticText(panel, -1, label="", name="Handy")
        self.labelmap["Handy"] = "Tel2.ADRESSE"
        self.tel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tel_sizer.Add(self.label_Telefon, 1, wx.EXPAND)
        self.tel_sizer.AddSpacer(10)
        self.tel_sizer.Add(self.label_Handy, 1, wx.EXPAND)
 
        self.label_Mail = wx.StaticText(panel, -1, label="", name="Mail")
        self.labelmap["Mail"] = "Mail.ADRESSE"
        self.label_Box = wx.StaticText(panel, -1, label="", name="Ab")
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
        self.list_service= wx.ListBox(panel, -1, name="service")
        self.listmap.append("service")
        self.label_LPreis = wx.StaticText(panel, -1, label="Preis:", name="LPreis")
        self.label_Preis = wx.StaticText(panel, -1, label="", name="Preis")
        self.labelmap["Preis"] = "Preis.ANMELD"
        self.label_LZahl = wx.StaticText(panel, -1, label="bezahlt", name="LZahl")
        self.label_Zahl = wx.StaticText(panel, -1, label="", name="Zahl")
        self.labelmap["Zahl"] = "Zahlung.Anmeld"
        self.price_lower_sizer=wx.GridSizer(2,2)
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
        # self.grid_custs = wx.grid.Grid(panel, -1, pos=(23,256) , size=(653, 264), name="Customers")
        self.grid_custs = wx.grid.Grid(panel, -1, name="Customers")
        self.grid_custs.CreateGrid(self.grid_rows["Customers"], self.grid_cols["Customers"])
        self.grid_custs.SetRowLabelSize(0)
        self.grid_custs.SetColLabelSize(18)
        self.grid_custs.EnableEditing(False)
        self.grid_custs.EnableDragColSize(0)
        self.grid_custs.EnableDragRowSize(0)
        self.grid_custs.EnableDragGridSize(0)
        self.grid_custs.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)
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
        
    ## event handler when window is activated
    # @param event - event which initiated this action   
    def On_Activate(self,event):
        if self.globals.get_value("birthday-splash-screen-interval","Event") and not self.globals.get_value("splash-screen-shown"):
            self.globals.set_value("splash-screen-shown", 1)
            self.show_splash_screen("birthday")

   ## Eventhandler COMBOBOX - filter
   # overwritten from AfpEvScreen
    def On_Filter(self,event=None):
        self.grid_row_selected = False
        self.grid_custs.ClearSelection()
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
            mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "SEPA Überweisung".decode("UTF-8"), "")
            self.Bind(wx.EVT_MENU, self.On_SEPAct, mmenu)
            tmp_menu.AppendItem(mmenu)
            mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "SEPA Lastschrifteinzug", "")
            self.Bind(wx.EVT_MENU, self.On_SEPAdd, mmenu)
            tmp_menu.AppendItem(mmenu)
            self.menubar.Insert(1, tmp_menu, "Verein")

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

    ## Eventhandler Menu - handle SEPA creditor transfer debit
    def On_SEPAct(self,event):
        if self.debug: print "AfpEvScreen_Verein Event handler `On_SEPAct'"
        #print "AfpEvScreen_Verein.On_SEPAct:", self.finance_moduls
        if self.finance_moduls and len(self.finance_moduls) > 1 and self.finance_moduls[1]:
            mandator = self.data.get_value("AgentNr")
            self.finance_moduls[1].AfpLoad_SEPAct(self.data.get_globals(), mandator)
    ## Eventhandler Menu - handle SEPA direct debit
    def On_SEPAdd(self,event):
        if self.debug: print "AfpEvScreen_Verein Event handler `On_SEPAdd'"
        #print "AfpEvScreen_Verein.On_SEPAdd:", self.finance_moduls
        if self.finance_moduls and len(self.finance_moduls) > 1 and self.finance_moduls[1]:
            self.finance_moduls[1].AfpLoad_SEPAdd(self.data)
        
    ## Eventhandler BUTTON - selection
    def On_Ausw(self,event=None):
        if self.debug: print "AfpEvScreen_Verein Event handler `On_Ausw'"
        if self.combo_Sortierung.GetValue() == "Mitglieder":
            value = self.data.get_value("EventNr") # all events of this agent are needed
            name = ""
            filter = None
            if self.slave_exists():
                name = self.slave_data.get_value("Name.ADRESSE")
                ok = True
            else:
                name, ok = AfpReq_Text("Mitglied wird gesucht,","bitte Namen eingeben!", name, "Mitgliedssuche")
            knr = None
            if ok:
                knr = AfpLoad_AdIndiAusw(self.globals, "EventNr.ANMELD", value, name, filter, "Bitte Mitglied auswählen, das abgezeigt werden soll.".decode("UTF-8"))
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
                grid_id = self.grid_id["Customers"]
                if grid_id and ANr in grid_id:
                    self.grid_row_selected = True
                    index = grid_id.index(ANr)
                    self.grid_custs.SelectRow(index)
                    self.grid_custs.MakeCellVisible(index, 0)
                self.load_direct(None, ANr)
                self.Pop_label()
        else:
            name = self.data.get_name(True, "Agent")
            filter = "Attribut = \"Verein\""
            auswahl = AfpLoad_AdAusw(self.globals, "ADRESATT", "AttName", name, filter, "Bitte Verein auswählen, der bearbeitet werden soll.".decode("UTF-8"))
            if not auswahl is None:
                self.clubnr = int(auswahl)
                self.set_current_record()
                self.Populate()
        if event: event.Skip()

    ## Eventhandler BUTTON - close current financial year and open new year
    def On_Abschluss(self,event):
        if self.debug: print "AfpEvScreen_Verein Event handler `On_Abschluss'"
        Ok = None
        if self.finance_moduls and self.finance_moduls[0]:
            balances = self.finance_moduls[0].AfpFinanceBalances(self.globals)
            akt = Afp_fromString(balances.get_period())
            if akt and Afp_isInteger(akt) and akt < self.globals.today().year:
                Ok = AfpReq_Question("Das Jahr '" + Afp_toString(akt) + "' abschliessen und das Jahr '" + Afp_toString(self.globals.today().year) + "' eröffnen?".decode("UTF-8"),"", "Jahresabschluss")
                if Ok: 
                    balances.switch_period()
        else:
            Ok = AfpReq_Question("Das aktuelle Jahr abschliessen und das neuen Zahlungsverpflichtungen erzeugen?" ,"", "Jahresabschluss")
        if Ok:
            AfpEvVerein_closeYear(self.data)
            self.Reload()
            self.Pop_label()
            #self.set_current_record()
            #self.Populate()
        event.Skip()
            
    ## Eventhandler BUTTON , MENU - modify event
    def On_modify(self, event):     
        if self.debug: print "AfpEvScreen_Verein Event handler `On_modify'"
        if not self.clubnr:
            self.On_Ausw()
        if self.clubnr:
            #super(AfpEvScreen_Verein, self).On_modify()
            self.sb.select_key(self.clubnr, "KundenNr","ADRESSE")
            AfpEvScreen.On_modify(self)
        event.Skip()
        
    ## Eventhandler BUTTON, MENU - document generation
    def On_Documents(self, event = None):
        if self.debug and event: print "AfpEvScreen_Verein  Event handler `On_Documents'"
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
            #print "AfpEvScreen_Verein.On_Documents:", header, prefix, archiv, variables
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
        #print "AfpEvScreen_Verein.load_direct:", ENr, ANr, self.slave_data
   
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
        if self.debug: print "AfpEvScreen_verein Event handler `On_ScreenZusatz'!"
        print "AfpEvScreen_verein.On_ScreenZusatz:", self.grid_row_selected, self.slave_data, data
        if self.grid_row_selected:
            super(AfpEvScreen_Verein, self).On_ScreenZusatz(event, self.slave_data)
        else:
            super(AfpEvScreen_Verein, self).On_ScreenZusatz(event)
     
    ## Eventhandler Keyboard - handle key-down events 
    #  overwritten from AfpScreen
    def On_KeyDown(self, event):
        keycode = event.GetKeyCode()        
        if self.debug: print "AfpEvScreen_Verein Event handler `On_KeyDown'", keycode
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
                    index = None
                    ANr = self.slave_data.get_value("AnmeldNr")
                    if ANr in grid_id:
                        index = grid_id.index(ANr)
                    if not index is None:
                        self.grid_custs.DeselectRow(index)
                    self.grid_row_selected = False
                    self.Reload()
        else:
            super(AfpEvScreen_Verein, self).On_KeyDown(event)

    ## generate the dedicated event
    # (overwritten from AfpEvScreen) 
    # @param ENr - if given:True - new event; Number - EventNr of event
    def get_event(self, ENr = None):
        if ENr == True: return AfpEvVerein(self.globals)
        elif ENr:  return  AfpEvVerein(self.globals, ENr)
        Verein =  AfpEvVerein(self.globals, None, self.sb)
        filters = self.filtermap[self.combo_Filter.GetValue()].split()
        #print "AfpEvScreen_Verein.get_event filters:", filters
        Verein.set_anmeld_filter(filters[1:])
        return  Verein
    ## load event edit dialog
    # (overwritten from AfpEvScreen) 
    # @param data - data to be edited
    def load_event_edit(self, data):
        return AfpLoad_EvVereinEdit(data, self.flavour)    
    ## generate the dedicated event client
    # (overwritten from AfpEvScreen) 
    # @param ANr - if given:True - new client; Number - AnmeldNr of client
    def get_client(self, ANr = None):
        if ANr == True: return AfpEvMember(self.globals)
        elif ANr:  return  AfpEvMember(self.globals, ANr)
        #elif ANr:  return  AfpEvMember(self.globals, ANr, None, True)
        return  AfpEvMember(self.globals, None, self.sb)
    ## load client edit dialog
    # (overwritten from AfpEvScreen) 
    # @param data - data to be edited
    def load_client_edit(self, data):
        return AfpLoad_EvMemberEdit(data)       
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
            vars["Duties"] = self.globals.get_value("hours-of-duty","Event")
        #print "AfpEvScreen_Verein.get_output_variables:", data.get_listname() , vars
        return vars
        
    ## set current record to be displayed 
    # (overwritten from AfpEvScreen) 
    def set_current_record(self):
        ini = True
        if self.data and self.clubnr == self.data.get_value("AgentNr"): ini = False
        if ini:
            self.sb.select_key(self.clubnr , "AgentNr","EVENT")
            self.sb.set_index("Kennung","EVENT","AgentNr")            
            #self.sb.CurrentIndexName("Kennung","EVENT")
        self.data = self.get_event() 
        #print "AfpEvScreen_Verein.set_current_record: ", ini, self.sb_master, self.sb.CurrentFile.name
        if self.sb_master == "Anmeld" or self.grid_row_selected and not self.no_data_shown:
            self.slave_data = self.get_client()
        else:
            self.slave_data = None
        if self.debug: 
            print "AfpEvScreen_Verein.set_current_record: ",
            self.data.view()
        return

    ## set initial record to be shown, when screen opens the first time
    #(overwritten from AfpEvScreen) 
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        ENr = 0
        #self.sb.set_debug()     
        self.sb.CurrentIndexName("KundenNr","ADRESSE")
        self.sb.CurrentIndexName("EventNr","ANMELD")   
        self.sb.CurrentIndexName("EventNr","EVENT")        
        if origin:
            ENr = self.globals.get_value("EventNr", origin)
        if ENr is None: ENr = 0
        if ENr:
            self.sb.select_key(ENr, "EventNr","EVENT")
            self.sb.set_index("Kennung","EVENT","EventNr")            
            self.sb.CurrentIndexName("Kennung","EVENT")
        else:
            self.sb.select_last() 
        self.clubnr = self.sb.get_value("AgentNr.EVENT")
        #print "AfpEvScreen_Verein.set_initial_record initial record set:", self.sb.get_value(), self.sb_master
        self.On_Index()
        #print "AfpEvScreen_Verein.set_initial_record index set:", self.sb_master, self.sb.CurrentFile.name
        self.sb.select_current()
        return
    ## check if slave exists
    def slave_exists(self):
        #print "AfpEvScreen_Verein.slave_exists:", self.slave_data,  not self.slave_data is None
        return not self.slave_data is None
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
            # ToDo: anteiliger Beitrag, wenn Anmeldung im Jahr
            #rows.append(bez + "  " + preis)
            #print "AfpEvScreen_Verein.get_list_rows Preis:", preis, bez
            rows.append(preis + "  " + bez)
            if self.slave_data.get_value("Extra.ANMELD"):
                if self.slave_data.get_value("Extra.ANMELD") == Afp_fromString(preis):
                    rows[0] = Afp_toString(0.0) + " " + bez
                ex_row = self.slave_data.get_selection("ANMELDEX").get_values("Bezeichnung,Preis")
                #print "AfpEvScreen_Verein.get_list_rows Extra:", ex_row
                for row in ex_row:
                    #rows.append(row[0] + "  " + row[1])
                    rows.append(Afp_toString(row[1]) + "  " + Afp_toString(row[0]))
        return rows
        
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param typ - name of grid to be populated
    def get_grid_rows(self, typ):
        rows = []
        if self.debug: print "AfpEvScreen_Verein.get_grid_rows typ:", typ
        if self.no_data_shown: return  rows
        if typ == "Customers" and self.data:
            #filter = self.filtermap[self.combo_Filter.GetValue()].split("-")
            tmps = self.data.get_value_rows("ANMELD","IdNr,Zahlung,Preis,Info,Anmeldung,KundenNr,Zustand,AnmeldNr")
            #print "AfpEvScreen_Verein.get_grid_rows tmps:", tmps 
            #self.data.view()
            if tmps:			
                for tmp in tmps:
                    add = True
                    #add = False
                    #for i in range(1, len(filter)):
                        #if tmp[6] == filter[i]:
                            #add = True
                    if add:
                        adresse = AfpAdresse(self.globals, tmp[5])
                        rows.append([Afp_toString(tmp[0]), adresse.get_string_value("Vorname"), adresse.get_string_value("Name"),  Afp_toString(tmp[4]), Afp_toString(tmp[2]), Afp_toString(tmp[1]), Afp_toString(tmp[3]), tmp[7]])
        if self.debug: print "AfpEvScreen_Verein.get_grid_rows rows:", rows 
        return rows

 # end of class AfpEvScreen_Verein
 
 ## allows the display and manipulation of an event 
class AfpDialog_EvVereinEdit(AfpDialog_EventEdit):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        super(AfpDialog_EvVereinEdit, self).__init__( *args, **kw)
        self.SetTitle("Vereinssparte")
        if self.debug: print "AfpDialog_EvVereinEdit.init"

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
        self.choice_Ort = wx.Choice(panel, -1,  pos=(78,60), size=(474,30),  choices="",  name="COrt")      
        self.choicemap["COrt"] = "Name.TName"
        self.Bind(wx.EVT_CHOICE, self.On_COrt, self.choice_Ort)  
 
        self.label_TBem = wx.StaticText(panel, -1, label="&Beiträge:".decode("UTF-8"), pos=(10,100), size=(56,18), name="TBem")
        #self.list_Preise = wx.ListBox(panel, -1, pos=(298,120), size=(258,86), name="Preise")
        self.list_Preise = wx.ListBox(panel, -1, pos=(74,95), size=(482,110), name="Preise")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Preise, self.list_Preise)
        self.listmap.append("Preise")
        #self.text_Bem = wx.TextCtrl(panel, -1, value="", pos=(348,95), size=(208,110), style=wx.TE_MULTILINE|wx.TE_LINEWRAP, name="Bem")
        #self.textmap["Bem"] = "Bem.EVENT"
        #self.text_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)

        self.check_Kopie = wx.CheckBox(panel, -1, label="Kopie", pos=(10,226), size=(70,20), name="Kopie")
        self.button_Neu = wx.Button(panel, -1, label="&Neu", pos=(80,220), size=(90,30), name="Neue Sparte")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)
        self.button_IntText = wx.Button(panel, -1, label="Te&xt", pos=(300,220), size=(80,30), name="IntText")
        self.Bind(wx.EVT_BUTTON, self.On_Text, self.button_IntText)
        self.setWx(panel, [390, 220, 80, 30], [480, 220, 80, 30]) 
        
    ## populate the 'Preise' list, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_Preise(self):
        liste = ["--- Neuen Beitrag hinzufügen ---".decode("UTF-8")]
        AfpDialog_EventEdit.Pop_Preise(self, liste)
    
    ## get preset value for 'Kennung' 
    # @param preset - preset string -not used here
    def get_kenn_preset(self, preset):
        return self.data.get_value("Tag.Verein")

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
        KNr = AfpLoad_AdAusw(self.data.get_globals(),"ADRESATT","AttName", "", "Attribut = \"Veranstaltungsort\"", "Bitte Adresse des neuen Veranstaltungsortes auswählen.".decode("UTF-8"))
        #rname, KNr = AfpAdresse_addAttributToAdresse(self.data.get_globals(),"Veranstaltungsort","Bitte Adresse des neuen Veranstaltungsortes auswählen.".decode("UTF-8"))
        if KNr: 
            adresse = AfpAdresse(self.data.get_globals(), KNr, None, self.data.get_globals().is_debug())
            rname = adresse.get_name()
            Ok = True
            KNr = 0
        if Ok and rname and rname in self.routes:
            AfpReq_Info("Name schon in Ortsliste enthalten!","Bitte dort auswählen.".decode("UTF-8"),"Warnung")
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
        super(AfpDialog_EvMemberEdit, self).__init__(self, *args, **kw)
        self.modifyWx()
        self.storno = None
        self.stornofile = None
        self.initial_price = None
        self.initial_price_factor = None
        
    ##  modify Wx objects defined in parent class
    def modifyWx(self):
        self.label_Datum.Enable(False)
        #self.text_Datum = wx.TextCtrl(self.panel, -1,  pos=(290,68), size=(95,18), name="Datum")
        #self.vtextmap["Datum"] = "Anmeldung.ANMELD"
        #self.text_Datum.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Datum)
        self.combo_Ort.Show(True)
        self.combomap["Ort"] = "Ort.TORT"
        self.label_TAb.Show(True)
        self.label_TAb.SetLabel("&Liegeplatz:")
        self.label_TGrund.SetLabel("&Beitrag:")
        self.label_TPreis.SetLabel("&Gesamt:")
        self.button_Agent.SetLabel("&Entsender")
        self.button_Storno.SetLabel("A&bmeldung")
        self.check_Mehrfach.SetLabel("&Familie")
    
    ## attaches data to this dialog overwritten from AfpDialog
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        self.check_family(data)
        routenr = data.get_value("Route.EVENT")
        self.route = AfpEvRoute(data.get_globals(), routenr, None, self.debug, True)
        super(AfpDialog_EvMemberEdit, self).attach_data(data, new, editable)

    ## read values from dialog and invoke writing into data         
    def store_data(self):
        if self.storno:
            # only set the cancel stamp here
            self.zustand = "PreStorno"
            self.data.set_value("InfoDat", self.storno)
            self.data.set_value("Info",  Afp_toString(self.storno) + "  Abmeldung")
            if self.stornofile:
                ext = self.stornofile.split(".")[-1]
                fname = "AfpVerein_Abmeldung_" + self.data.get_string_value("AnmeldNr") + "." + ext
                Afp_copyFile(self.stornofile, Afp_addPath(self.globals.get_value("archivdir"), fname))
                self.data.add_to_Archiv({"Gruppe": "Abmeldung","Bem": Afp_toString(self.storno), "Extern": fname})
        super(AfpDialog_EvMemberEdit, self).store_data()
        #if self.storno:
            #self.data.delete_from_event()
        
    ## complete data before storing
    # @param data - data to be completed
    def complete_data(self, data):
        if not self.data.get_value("IdNr"):
            IdNr= self.data.generate_IdNr() 
            data["IdNr"] = IdNr 
        if self.data.get_value("Zahlung") is None and "Preis" in data and data["Preis"] > 0.0:
            data["Zahlung"] = 0.0
        super(AfpDialog_EvMemberEdit, self).complete_data(data)
        return data
        
    ## actualise all price data according to input row
    # (overwritten from AfpDialog_EvClientEdit)
    # @param row - holding data of selected or manually created price
    def actualise_preise(self, row):
        if row[4] == "Grund":
            ENr = self.data.get_string_value("EventNr")
            if self.preisnr: preisnr = self.preisnr
            else: preisnr = self.data.get_value("PreisNr") 
            if not preisnr == row[3]:
                self.preisnr = row[3]
                if self.initial_price_factor is None:
                    if not self.new:
                        self.initial_price = self.data.get_value("Preis.Preis") 
                    self.initial_price_factor = self.data.get_globals().today().month/12.0
                select = "EventNr = " + ENr + " AND PreisNr = " + Afp_toString(self.preisnr)
                self.data.get_selection("Preis").load_data(select)
                preis = 0.0
                if row[0]: preis = row[0]
                self.add_partitial_price(preis)
        else:
            changed_data = {"AnmeldNr": self.data.get_value("AnmeldNr"), "Preis": row[0], "Bezeichnung":row[1], "NoPrv":row[2]}
            self.data.get_selection("ANMELDEX").add_data_values(changed_data)
        self.data.update_prices()
        self.Pop_label()

    ## add rabat if price-change is pro rata
    # @param preis - new yearly price to be reached
    def add_partitial_price(self, preis):
        initial = 0.0
        new = preis*(1.0 - self.initial_price_factor)
        month = Afp_toString(self.data.get_globals().today().month)
        text = "Beitragsfrei bis Monat " +  month 
        if self.initial_price:
            initial = self.initial_price*self.initial_price_factor
            text = "Beitragsänderung in Monat ".decode("UTF-8") +  month
        new += initial
        print "AfpDialog_EvMemberEdit.add_partitial_price:", preis, month, new, text
        sel = self.data.get_selection("ANMELDEX")
        rows = sel.get_values()
        index = None
        for row in rows:
            print "AfpDialog_EvMemberEdit.add_partitial_price row:",row[2], text, Afp_toString(row[2]) == text
            if Afp_toString(row[2]) == text:
                index = rows.index(row)
                diff = row[3]
        if index is None:
            changed_data = {"AnmeldNr": self.data.get_value("AnmeldNr"), "Preis": new - preis, "Bezeichnung":text, "NoPrv":1}
            sel.add_data_values(changed_data)
        else:
            changed_data = {"Preis": new - preis, "Bezeichnung":text}
            sel.set_data_values(changed_data, index)
            
    ## check if 'family' id allowed for 'verein'-member
    # @param data - if given, data to be checked, otherwise self.data is used
    def check_family(self, data = None):
        if not data:
            data = self.data
        if  data:
            if self.check_Mehrfach.GetValue() or (data.pricename_holds("Familie") and not data.pricename_holds("Familien")):
                self.check_Mehrfach.Enable(True)
            else:
                self.check_Mehrfach.Enable(False)

    ## Eventhandler BUTTON - graphic pick for dates, 
    # - not applicable for 'Members' 
    # @param event - event which initiated this action   
    def On_Set_Datum(self,event = None):
        return
 
   ## Eventhandler BUTTON - select travel agency
    # @param event - event which initiated this action   
    def On_Agent(self,event):
        if self.debug: print "AfpDialog_EvMemberEdit Event handler `On_Agent'"
        name = self.data.get_value("Name.Agent")
        if not name: name = self.data.get_value("Name.Adresse")
        text = "Bitte Ansprechpartner für diese Anmeldung auswählen:"
        KNr = AfpLoad_AdAusw(self.data.get_globals(), "ADRESSE", "Name", name)
        changed = False
        if KNr:
            self.agent = AfpAdresse(self.data.get_globals(),KNr)
            self.label_Buero.SetLabel(self.agent.get_name())
            changed = True
        else:
            if self.data.get_value("AgentNr") or self.agent:
                Ok = AfpReq_Question("Anmeldung nicht mehr über " + agent + "?".decode("UTF-8"),"Eintrag löschen?".decode("UTF-8"), agent + " löschen?".decode("UTF-8"))
                if Ok: 
                    if self.agent: self.agent = None
                    else: self.agent = False
                    self.label_Buero.SetLabel("")
                    changed = True
        if changed:
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()  
 
    
    ##Eventhandler BUTTON - delete client \n
    # @param event - event which initiated this action   
    def On_Storno(self, event):
        if self.debug: print "AfpDialog_EvMemberEdit Event handler `On_Storno'"
        if self.data.get_value("Zustand") == "PreStorno":
            name = self.data.get_name()
            dat = self.data.get_string_value("InfoDat")
            Ok = AfpReq_Question("Abmeldung für " + name + " liegt vor,".decode("UTF-8"),"Austritt zum " + dat + " umsetzten?", "Austritt")
            if Ok:
                print "AfpDialog_EvMemberEdit.On_Storno abmelden nicht implementiert!"
        else:
            dat = "31.12." + Afp_toString(self.data.get_globals().today().year)
            text1 = self.data.get_name() +  " von '" + self.data.get_value("Bez.EVENT") + "' der " + self.data.get_value("Name.Veranstalter") + " abmelden?"
            dir = ""            
            fname, Ok = AfpReq_FileName(dir, text1, "Kündigungsschreiben auswählen!".decode("UTF-8") , True)
            if Ok and fname:
                text2 = "Die Kündigung wird wirksam zum:".decode("UTF-8")
                dat, Ok = AfpReq_Date(text1, text2, dat, "Abmeldung")
            if Ok and dat and fname:
                self.storno = Afp_fromString(dat)
                self.stornofile = fname
            else:
                self.storno = None
        self.Set_Editable(True)
        event.Skip()
 
    
    ##Eventhandler BUTTON - add new client \n
    # @param event - event which initiated this action   
    def On_Anmeld_Neu(self,event):
        if self.debug: print "AfpDialog_EvMemberEdit Event handler `On_Anmeld_Neu'"
        new = self.new
        super(AfpDialog_EvMemberEdit, self).On_Anmeld_Neu()
        if new:
            self.data.set_value("PreisNr", 12)
            self.Pop_Preise()
            self.check_family()
        event.Skip()
    ## get multiflags accorfing to multi checkbox
    # overwritten from AfpEvDialog
    def get_multiflags(self):
        multi = self.check_Mehrfach.GetValue()
        if multi:
            return [True, True, False, False]
        return multi

   
    ##  get a client object with given identnumber
    # overwritten from AfpDialog_EvEventEdit
    # @parm ANr - if given, identifier
    def get_client(self, ANr = None):
        if ANr is None: ANr = self.data.get_value()
        return  AfpEvMember(self.data.globals, ANr)
        
## loader routine for dialog EvMemberEdit
# @param data - data to be proceeded
# @param edit - if given, flag if dialog should open in edit modus
# @param onlyOk - flag if only the Ok exit is possible to leave dialog, used for 'Umbuchung'
def AfpLoad_EvMemberEdit(data, edit = False, onlyOk = None):
    if data:
        DiEvMember = AfpDialog_EvMemberEdit()
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
    
    
