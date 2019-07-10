#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvScreen_Verein
# AfpEvScreen_Verein module provides the graphic screen to access all data of the Afp-'Verein' modul 
# it holds the class
# - AfpEvScreen_Verein
#
#   History: \n
#        10 Apr. 2019 - integrate all dervired flavour classes into one deck - Andreas.Knoblauch@afptech.de
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
from AfpBase.AfpBaseRoutines import Afp_archivName, Afp_startFile
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Selection, AfpReq_Question, AfpReq_Text, AfpDialog
from AfpBase.AfpBaseScreen import AfpScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_DiAdEin_fromSb, AfpAdresse_addAttributToAdresse
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

import AfpEvent
from AfpEvent import AfpEvRoutines, AfpEvDialog, AfpEvScreen
from AfpEvent.AfpEvScreen import AfpEvScreen
from AfpEvent.AfpEvRoutines import *
from AfpEvent.AfpEvDialog import AfpLoad_EvAusw, AfpDialog_EventEdit, AfpDialog_EvClientEdit, AfpLoad_EvClientEdit

## baseclass for club handling         
class AfpEvVerein(AfpEvent):
    ## initialize AfpEvent class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param EventNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved durin initialisation \n
    # \n
    # either EventNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, EventNr = None, sb = None, debug = None, complete = False):
        AfpEvent.__init__(self, globals, EventNr, sb, debug, complete)
        self.listname = "Verein"
        if not self.get_value("AgentNr") and sb:
            KNr = sb.get_value("KundenNr.ADRESSE")
            Name = sb.get_value("Name.ADRESSE")
            self.set_value("AgentNr.EVENT", KNr)
            self.set_value("AgentName.EVENT", Name)
        self.selects["Verein"] = [ "ADRESATT","KundenNr = AgentNr.EVENT AND Attribut = \"Verein\""] 
        if complete: self.create_selections()
        if self.debug: print "AfpEvVerein Konstruktor, EventNr:", self.mainvalue

    ## return specific identification string to be used in dialogs \n
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
    # @param complete - flag if data from all tables should be retrieved durin initialisation \n
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
        return check in  self.get_value("Bezeichnung.Preis")  

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
        self.grid_row_selected = None
        self.dynamic_grid_col_percents = [ 5, 20, 20, 14, 14, 14, 13]
        if self.debug: print "AfpEvScreen_Verein Konstruktor"
       
    ## initialize widgets
    def initWx(self):
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
        self.combo_Sortierung = wx.ComboBox(panel, -1, value="Mitglieder", choices=["Mitglieder","Sparte"], size=(100,30), style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Index, self.combo_Sortierung)
        self.indexmap = {"Mitglieder":"RechNr","Sparte":"Bez"}
        
        self.button_Auswahl = wx.Button(panel, -1, label="Aus&wahl",size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Ausw, self.button_Auswahl)
        self.button_Anfrage = wx.Button(panel, -1, label="An&frage",size=(77,50), name="BAnfrage")
        self.Bind(wx.EVT_BUTTON, self.On_Anfrage, self.button_Anfrage)      
        self.button_Event = wx.Button(panel, -1, label="&Sparte",size=(77,50), name="BEvent")
        self.Bind(wx.EVT_BUTTON, self.On_modify, self.button_Event)
        self.button_Anmeldung = wx.Button(panel, -1, label="&Anmeldung", size=(77,50),name="BAnmeldung")
        self.Bind(wx.EVT_BUTTON, self.On_Anmeldung, self.button_Anmeldung)
        self.button_Zahlung = wx.Button(panel, -1, label="&Zahlung",size=(77,50), name="BZahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahlung)
        self.button_Dokumente = wx.Button(panel, -1, label="&Dokumente",size=(77,50), name="BDokumente")
        self.Bind(wx.EVT_BUTTON, self.On_Listen_Ausgabe, self.button_Dokumente)
        self.button_Einsatz = wx.Button(panel, -1, label="Ein&satz",size=(77,50), name="BEinsatz")
        self.Bind(wx.EVT_BUTTON, self.On_VehicleOperation, self.button_Einsatz)               
        self.button_Einsatz.Enable(False)
        self.button_Ende = wx.Button(panel, -1, label="Be&enden",size=(77,50), name="BEnde")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Ende)
        
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Auswahl,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Anfrage,0,wx.EXPAND)
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
        self.combo_Filter = wx.ComboBox(panel, -1, value="Mitglieder", size=(164,20), choices=["Mitglieder","Austritte","Kandidaten"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        self.filtermap = {"Mitglieder":"Verein-Anmeldung","Austritte":"Verein-Storno","Kandidaten":"Verein-Reserv"}
        self.top_mid_sizer.AddStretchSpacer(1)
        self.top_mid_sizer.Add(self.combo_Filter,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
      
        # Event
        self.label_Event = wx.StaticText(panel, -1, label="", name="Verein")
        self.labelmap["Verein"] = "Name.Agent"
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
        self.label_Typ_map = {"Anmeldung":"Mitglied","Storno":"Austritt","Reservierung":"Kandidat"}
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
        #self.labelmap["Ab"] = "Name.TOrt"
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
        
   ## execution routine- set date filter
   # dummy only needed to use the AfpEvScreen-routines
    def set_jahr_filter(self,event = None): 
        return

    ## compose event specific menu parts
    # overwritten from AfpEvScreen
    def create_specific_menu(self):
        super(AfpEvScreen_Verein, self).create_specific_menu()
        if not self.globals.skip_accounting():
            self.finance_moduls = Afp_importAfpModul("Finance",self.globals)
        if self.finance_moduls:
            tmp_menu = self.menubar.Remove(1)
            print "AfpEvScreen_Verein.create_specific_menu menu:", tmp_menu
            mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "SEPA Lastschrifteinzug", "")
            self.Bind(wx.EVT_MENU, self.On_SEPADD, mmenu)
            tmp_menu.AppendItem(mmenu)
            self.menubar.Insert(1, tmp_menu, "Verein")

    ## populate label widgets
    def Pop_label(self):
        no_slave =  not self.slave_exists()
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

    ## Eventhandler Menu - handle SEPA direct debit
    def On_SEPADD(self,event):
        if self.debug: print "AfpEvScreen_Verein Event handler `On_SEPADD'"
        print "AfpEvScreen_Verein.On_SEPADD:", self.finance_moduls
        result = self.finance_moduls[0].AfpLoad_SEPADD(self.data)
        
    ## Eventhandler BUTTON - selection
    def On_Ausw(self,event=None):
        if self.debug: print "AfpEvScreen_Verein Event handler `On_Ausw'"
        name = self.data.get_name(True, "Agent")
        filter = "Attribut = \"Verein\""
        auswahl = AfpLoad_AdAusw(self.globals, "ADRESATT", "AttName", name, filter, "Bitte Verein auswählen, der bearbeitet werden soll.".decode("UTF-8"))
        if not auswahl is None:
            self.clubnr = int(auswahl)
            self.set_current_record()
            self.Populate()
        if event: event.Skip()
            
    ## Eventhandler BUTTON , MENU - modify event
    def On_modify(self, event):     
        if self.debug: print "AfpEvScreen_Verein Event handler `On_modify'"
        if not self.clubnr:
            self.On_Ausw()
        if self.clubnr:
            #super(AfpEvScreen_Verein, self).On_modify()
            self.sb.select_key(self.clubnr, "KundeNr","ADRESSE")
            AfpEvScreen.On_modify(self)
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
    
    ## Eventhandler Keyboard - handle key-down events - overwritten from AfpScreen
    def On_KeyDown(self, event):
        keycode = event.GetKeyCode()        
        if self.debug: print "AfpEvScreen_Verein Event handler `On_KeyDown'", keycode
        if keycode == wx.WXK_UP or keycode == wx.WXK_DOWN:
            if keycode == wx.WXK_UP: next = -1
            elif keycode == wx.WXK_DOWN: next = 1
            grid_id = self.grid_id["Customers"]
            if  self.grid_row_selected:
                ANr = self.slave_data.get_value("AnmeldNr")
                index = grid_id.index(ANr) + next
                if index < 0: index = 0
                if index >= len(grid_id): index = len(grid_id) - 1
            else:
                self.grid_row_selected = True
                if next < 0:
                    index = len(grid_id) - 1
                else:
                    index = 0
            ANr = grid_id[index]
            #print "AfpEvScreen_Verein.On_KeyDown:", index, ANr
            self.grid_custs.SelectRow(index)
            self.grid_custs.MakeCellVisible(index, 0)
            self.load_direct(0, ANr)
            #print "AfpEvScreen_Verein.On_KeyDown direct:", ANr, self.sb.get_value("AnmeldNr.ANMELD")
            self.Reload()
            #print "AfpEvScreen_Verein.On_KeyDown reload:", ANr, self.sb.get_value("AnmeldNr.ANMELD")
        super(AfpEvScreen_Verein, self).On_KeyDown(event)

        

    ## generate the dedicated event
    # (overwritten from AfpEvScreen) 
    # @param ENr - if given:True - new event; Number - EventNr of event
    def get_event(self, ENr = None):
        if ENr == True: return AfpEvVerein(self.globals)
        elif ENr:  return  AfpEvVerein(self.globals, ENr)
        return  AfpEvVerein(self.globals, None, self.sb)
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
        return  AfpEvMember(self.globals, None, self.sb)
    ## load client edit dialog
    # (overwritten from AfpEvScreen) 
    # @param data - data to be edited
    def load_client_edit(self, data):
        return AfpLoad_EvMemberEdit(data)       
        #return AfpLoad_EvClientEdit(data)   
    ## generate nedded oiutput variables
    # (overwritten from AfpEvScreen) 
    # @param data - data to be used for output
    def get_output_variables(self, data):
        today = self.globals.today()
        vars= {"Today" : today}
        thisday = data.get_value("Anmeldung")
        vars["ThisYear"] = thisday.year
        if  thisday.year < today.year:
            vars["ThisMonth"] = 0
        else:
            vars["ThisMonth"] = thisday.month - 1
        vars["Duties"] = self.globals.get_value("hours-of-duty","Event")
        #print "AfpEvScreen_Verein.get_output_variables:", vars
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
            if not preis: preis = self.sb.get_string_value("ProvPreis.ANMELD")  
            if not preis: preis = self.sb.get_string_value("Preis.ANMELD")  
            # ToDo: anteiliger Beitrag, wenn Anmeldung im Jahr
            #rows.append(bez + "  " + preis)
            #print "AfpEvScreen_Verein.get_list_rows Preis:", preis, bez
            rows.append(preis + "  " + bez)
            if self.slave_data.get_value("Extra.ANMELD"):
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
            filter = self.filtermap[self.combo_Filter.GetValue()].split("-")
            tmps = self.data.get_value_rows("ANMELD","IdNr,Zahlung,Preis,Info,Anmeldung,KundenNr,Zustand,AnmeldNr")
            if tmps:			
                for tmp in tmps:
                    if tmp[6] == filter[1]:
                        adresse = AfpAdresse(self.globals, tmp[5])
                        rows.append([Afp_toString(tmp[0]), adresse.get_string_value("Vorname"), adresse.get_string_value("Name"),  Afp_toString(tmp[4]), Afp_toString(tmp[2]), Afp_toString(tmp[1]), Afp_toString(tmp[3]), tmp[7]])
        if self.debug: print "AfpEvScreen.get_grid_rows rows:", rows 
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
        
    ##  modify Wx objects defined in parent class
    def modifyWx(self):
        self.label_Datum.Enable(False)
        self.text_Datum = wx.TextCtrl(self.panel, -1,  pos=(290,68), size=(95,18), name="Datum")
        self.vtextmap["Datum"] = "Anmeldung.ANMELD"
        self.text_Datum.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Datum)
        self.combo_Ort.Show(True)
        self.combomap["Ort"] = "Ort.TORT"
        self.label_TAb.Show(True)
        self.label_TAb.SetLabel("&Liegeplatz:")
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

    ## complete data before storing
    # @param data - data to be completed
    def complete_data(self, data):
        if not self.data.get_value("IdNr"):
            IdNr= self.data.generate_IdNr() 
            data["IdNr"] = IdNr
        super(AfpDialog_EvMemberEdit, self).complete_data(data)
        return data

    ## check if 'family' id allowed for 'verein'-member
    # @param data - if given, data to be checked, otherwise self.data is used
    def check_family(self, data = None):
        if not data:
            data = self.data
        if  data:
            if data.pricename_holds("Familie") and not data.pricename_holds("Familien"):
                self.check_Mehrfach.Enable(True)
            else:
                self.check_Mehrfach.Enable(False)

    ## Eventhandler BUTTON - graphic pick for dates, 
    # - not applicable for 'Members' 
    # @param event - event which initiated this action   
    def On_Set_Datum(self,event = None):
        return
    
    ##Eventhandler BUTTON - add new client \n
    # @param event - event which initiated this action   
    def On_Anmeld_Neu(self,event):
        if self.debug: print "AfpDialog_EvMemberEdit Event handler `On_Anmeld_Neu'"
        family = self.check_Mehrfach.GetValue()
        if family:
            family = [True, True, False, False]
        self.Anmeld_Neu(family)
        if self.new:
            self.data.set_value("PreisNr", 0)
            self.Pop_Preise()
            self.check_family()
        event.Skip()
   
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
