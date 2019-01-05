#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvScreen
# AfpEvScreen module provides the graphic screen to access all data of the Afp-'Event' modul 
# specialized screen for 'tourist' handling, intergrated from former 'Tourist' modul
# it holds the class
# - AfpEvScreen
#
#   History: \n
#        15 Jan. 2016 - inital code of 'Tourist' modul generated - Andreas.Knoblauch@afptech.de
#        15 May 2018 - integrated into 'Event' modul - Andreas.Knoblauch@afptech.de
#        25 Oct 2018 - corrections due to database changes in 'Event' modul- Andreas.Knoblauch@afptech.de

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
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Selection, AfpReq_Question, AfpReq_Text
from AfpBase.AfpBaseDialogCommon import AfpLoad_DiReport
from AfpBase.AfpBaseScreen import AfpScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_DiAdEin_fromSb
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

import AfpEvent
from AfpEvent import AfpEvRoutines, AfpEvDialog, AfpEvScreen
from AfpEvent.AfpEvScreen import AfpEvScreen
from AfpEvent.AfpEvRoutines import *
from AfpEvent.AfpEvDialog import AfpEvent_copy, AfpLoad_EvAusw, AfpLoad_EventEdit_fromSb, AfpLoad_EvClientEdit_fromSb

## Class AfpEvScreen_Tourist shows 'Tourist' screen and handles interactions
class AfpEvScreen_Tourist(AfpEvScreen):
    ## initialize AfpEvScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        self.flavour = "Tourist"
        self.einsatz = None # to invoke import of 'Einsatz' modules in 'init_database'
        AfpEvScreen.__init__(self, debug)
        self.SetTitle("Afp Tourist")
        self.grid_row_selected = None
        if self.debug: print "AfpEvScreen_Tourist Konstruktor"
    
    ## initialize widgets
    # overwritten from AfpEvScreen
    def initWx(self):
        self.custs_rows = 8
        self.grid_rows["Customers"] = self.custs_rows
        self.grid_cols["Customers"] = 7
        panel = self.panel
        # BUTTON
        self.button_Auswahl = wx.Button(panel, -1, label="Aus&wahl", pos=(692,50), size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Event_Ausw, self.button_Auswahl)
        #self.button_Adresse = wx.Button(panel, -1, label="A&dresse", pos=(692,110), size=(77,50), name="BAdresse")
        #self.Bind(wx.EVT_BUTTON, self.On_Adresse_aendern, self.button_Adresse)      
        self.button_Anfrage = wx.Button(panel, -1, label="An&frage", pos=(692,110), size=(77,50), name="BAnfrage")
        self.Bind(wx.EVT_BUTTON, self.On_Event_Anfrage, self.button_Anfrage)      
        self.button_Reise = wx.Button(panel, -1, label="&Reise", pos=(692,170), size=(77,50), name="Reise")
        self.Bind(wx.EVT_BUTTON, self.On_Event_modify, self.button_Reise)
        self.button_Anmeldung = wx.Button(panel, -1, label="&Anmeldung", pos=(692,230), size=(77,50), name="BAnmeldung")
        self.Bind(wx.EVT_BUTTON, self.On_Anmeldung, self.button_Anmeldung)
        self.button_Zahlung = wx.Button(panel, -1, label="&Zahlung", pos=(692,290), size=(77,50), name="BZahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahlung)
        self.button_Dokumente = wx.Button(panel, -1, label="&Dokumente", pos=(692,350), size=(77,50), name="BDokumente")
        self.Bind(wx.EVT_BUTTON, self.On_Listen_Ausgabe, self.button_Dokumente)
        self.button_Einsatz = wx.Button(panel, -1, label="Ein&satz", pos=(692,410), size=(77,50), name="BEinsatz")
        self.Bind(wx.EVT_BUTTON, self.On_VehicleOperation, self.button_Einsatz)               
        self.button_Ende = wx.Button(panel, -1, label="Be&enden", pos=(692,470), size=(77,50), name="BEnde")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Ende)
      
        # COMBOBOX
        self.combo_Filter = wx.ComboBox(panel, -1, value="Eigen-Anmeldungen", pos=(509,16), size=(164,20), choices=["Eigen-Anmeldungen","Eigen-Stornierungen","Eigen-Reservierungen","Fremd-Buchungen","Fremd-Anfragen","Fremd-Anmeldungen","Fremd-Stornierungen"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Event_Filter, self.combo_Filter)
        self.filtermap = {"Eigen-Anmeldungen":"Eigen-Anmeldung","Eigen-Stornierungen":"Eigen-Storno","Eigen-Reservierungen":"Eigen-Reserv","Fremd-Buchungen":"Fremd-","Fremd-Anfragen":"Fremd-Anfrage","Fremd-Anmeldungen":"Fremd-Anmeldung","Fremd-Stornierungen":"Fremd-Storno"}
        self.combo_Sortierung = wx.ComboBox(panel, -1, value="Kennung", pos=(689,16), size=(80,20), choices=["Kennung","Ort","Beginn","Anmeldung"], style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Event_Index, self.combo_Sortierung)
        self.indexmap = {"Kennung":"Kennung","Ort":"Bez","Beginn":"Beginn","Anmeldung":"RechNr"}
        self.combo_Jahr = wx.ComboBox(panel, -1, value="Aktuell", pos=(420,16), size=(84,20), style=wx.CB_DROPDOWN, name="Jahr")
        self.Bind(wx.EVT_COMBOBOX, self.On_Jahr_Filter, self.combo_Jahr)
        self.Bind(wx.EVT_TEXT_ENTER, self.On_Jahr_Filter, self.combo_Jahr)
      
        # LABEL
        self.label_Reise = wx.StaticText(panel, -1, label="Reise:", pos=(32,51), size=(95,18), name="LReise")
        self.label_Bem = wx.StaticText(panel, -1, label="Bemerkung:", pos=(32,260), size=(95,18), name="LBem")
        self.label_AZusatz = wx.StaticText(panel, -1, label="Zusatz:", pos=(32,285), size=(95,18), name="LAZusatz")
        self.label_Teilnehmer = wx.StaticText(panel, -1,  label="Teilnehmer:", pos=(32,98), size=(95,18), name="LTeilnehmer")
        self.label_Route = wx.StaticText(panel, -1,  label="Route:", pos=(196,98), size=(47,18), name="LRoute")
        self.label_RZusatz = wx.StaticText(panel, -1, label="Zusatz:", pos=(32,126), size=(95,18), name="LRZusatz")
        self.label_Anmeldung = wx.StaticText(panel, -1, label="Anmeldung:", pos=(32,166), size=(95,18), name="LAnmeldung")
        self.label_Adresse = wx.StaticText(panel, -1, label="Adresse:", pos=(32,191), size=(96,18), name="LAdresse")
        self.label_Leistung = wx.StaticText(panel, -1,label="Leistungen:", pos=(430,166), size=(80,18), name="LLeistung")
        #self.label_Transfer = wx.StaticText(panel, -1,label="Transfer:", pos=(433,187), size=(75,19), name="LTransfer")
        self.label_Label8 = wx.StaticText(panel, -1, label="vom", pos=(302,167), size=(26,16), name="Label8")
        self.label_Label2 = wx.StaticText(panel, -1, label="vom", pos=(138,75), size=(30,15), name="Label2")
        self.label_Label3 = wx.StaticText(panel, -1, label="bis zum", pos=(240,75), size=(51,15), name="Label3")
        self.label_Preis = wx.StaticText(panel, -1, label="Preis:", pos=(550,271), size=(50,18), name="LPreis")
        self.label_Zahlung = wx.StaticText(panel, -1, label="Zahlung:", pos=(550,293), size=(50,18), name="LZahlung")
      
        # TEXTBOX
        #Adresse
        self.text_Vorname = wx.TextCtrl(panel, -1, value="", pos=(135,184), size=(140,20), style=wx.TE_READONLY, name="Vorname")
        self.textmap["Vorname"] = "Vorname.ADRESSE"
        self.text_Name = wx.TextCtrl(panel, -1, value="", pos=(135,203), size=(224,20), style=wx.TE_READONLY, name="Name")
        self.textmap["Name"] = "Name.ADRESSE"
        self.text_Strasse = wx.TextCtrl(panel, -1, value="", pos=(135,222), size=(224,20), style=wx.TE_READONLY, name="Strasse")
        self.textmap["Strasse"] = "Strasse.ADRESSE"
        self.text_Plz = wx.TextCtrl(panel, -1, value="", pos=(135,241), size=(50,20), style=wx.TE_READONLY, name="Plz")
        self.textmap["Plz"] = "Plz.ADRESSE"
        self.text_Ort = wx.TextCtrl(panel, -1, value="", pos=(185,241), size=(175,20), style=wx.TE_READONLY, name="Ort")
        self.textmap["Ort"] = "Ort.ADRESSE"
        self.text_Telefon = wx.TextCtrl(panel, -1, value="", pos=(367,222), size=(139,20), style=wx.TE_READONLY, name="Telefon")
        self.textmap["Telefon"] = "Telefon.ADRESSE"
        self.text_Tel2 = wx.TextCtrl(panel, -1, value="", pos=(367,241), size=(139,20), style=wx.TE_READONLY, name="Tel2")
        self.textmap["Tel2"] = "Tel2.ADRESSE"
        self.text_Mail = wx.TextCtrl(panel, -1, value="", pos=(367,203), size=(139,20), style=0, name="Mail")
        self.textmap["Mail"] = "Mail.ADRESSE"

        # Event
        self.text_Bez = wx.TextCtrl(panel, -1, value="", pos=(138,51), size=(230,20), style=wx.TE_READONLY, name="Bez")
        self.textmap["Bez"] = "Bez.EVENT"
        self.text_Beginn = wx.TextCtrl(panel, -1, value="", pos=(168,75), size=(60,20), style=wx.TE_READONLY, name="Beginn")
        self.textmap["Beginn"] = "Beginn.EVENT"
        self.text_Ende = wx.TextCtrl(panel, -1, value="", pos=(308,75), size=(60,20), style=wx.TE_READONLY, name="Ende")
        self.textmap["Ende"] = "Ende.EVENT"
        self.text_Kennung = wx.TextCtrl(panel, -1, value="", pos=(35,75), size=(100,20), style=wx.TE_READONLY, name="Kennung")
        self.textmap["Kennung"] = "Kennung.EVENT"
        self.text_Route = wx.TextCtrl(panel, -1, value="", pos=(240,96), size=(128,20), style=wx.TE_READONLY, name="Route")
        self.textmap["Route"] = "Name.TNAME"
        self.text_Personen = wx.TextCtrl(panel, -1, value="", pos=(135,98), size=(25,20), style=wx.TE_READONLY, name="Personen")
        self.textmap["Personen"] = "Personen.EVENT"
        self.text_Anmeldungen = wx.TextCtrl(panel, -1, value="", pos=(168,98), size=(25,20), style=wx.TE_READONLY, name="Anmeldungen")
        self.textmap["Anmeldungen"] = "Anmeldungen.EVENT"
        self.text_Bem= wx.TextCtrl(panel, -1, value="", pos=(135,123), size=(370,35), style=wx.TE_MULTILINE|wx.TE_LINEWRAP, name="ReiseBem")
        self.textmap["ReiseBem"] = "Bem.EVENT"
        self.text_Verst = wx.TextCtrl(panel, -1, value="", pos=(377,51), size=(126,20), style=wx.TE_READONLY, name="Verst")
        self.textmap["Verst"] = "AgentName.EVENT"
        self.text_IntText = wx.TextCtrl(panel, -1, value="", pos=(509,50), size=(164,101), style=wx.TE_MULTILINE, name="IntText")
        self.extmap["IntText"] = "IntText.EVENT"

        # Client
        self.text_Zustand = wx.TextCtrl(panel, -1, value="", pos=(135,163), size=(87,20), style=wx.TE_READONLY, name="Zustand")
        self.textmap["Zustand"] = "Zustand.ANMELD"
        self.text_Anmeldung = wx.TextCtrl(panel, -1, value="", pos=(332,163), size=(60,20), style=wx.TE_READONLY, name="Anmeldung")
        self.textmap["Anmeldung"] = "Anmeldung.ANMELD"
        self.text_RechNr = wx.TextCtrl(panel, -1, value="", pos=(231,163), size=(64,20), style=wx.TE_READONLY, name="RechNr")
        self.textmap["RechNr"] = "RechNr.ANMELD"
        self.text_Agent = wx.TextCtrl(panel, -1, value="", pos=(285,184), size=(143,20), style=wx.TE_READONLY, name="Agent")
        self.textmap["Agent"] = "AgentName.ANMELD"
        self.text_Bem = wx.TextCtrl(panel, -1, value="", pos=(135,260), size=(370,20), style=wx.TE_READONLY, name="Bem")
        self.textmap["Bem"] = "Bem.ANMELD"
        self.text_ExtText = wx.TextCtrl(panel, -1, value="", pos=(135,280), size=(370,30), style=0, name="ExtText")
        self.textmap["ExtText"] = "ExtText.ANMELD"
        self.text_Preis= wx.TextCtrl(panel, -1, value="", pos=(600,269), size=(71,20), style=wx.TE_READONLY, name="Preis")
        self.textmap["Preis"] = "Preis.ANMELD"
        self.text_Zahlung = wx.TextCtrl(panel, -1, value="", pos=(600,291), size=(71,20), style=wx.TE_READONLY, name="Zahlung")
        self.textmap["Zahlung"] = "Zahlung.ANMELD"
        
        #ListBox
        self.list_service= wx.ListBox(panel, -1, pos=(512,163) , size=(160, 100), name="service")
        #self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Archiv, self.list_service)
        self.listmap.append("service")
        
        # GRID
       # self.grid_custs = wx.grid.Grid(panel, -1, pos=(23,256) , size=(653, 264), name="Customers")
        self.grid_custs = wx.grid.Grid(panel, -1, pos=(23,315) , size=(653, 204), name="Customers")
        self.grid_custs.CreateGrid(self.custs_rows, 7)
        self.grid_custs.SetRowLabelSize(3)
        self.grid_custs.SetColLabelSize(18)
        self.grid_custs.EnableEditing(0)
        self.grid_custs.EnableDragColSize(0)
        self.grid_custs.EnableDragRowSize(0)
        self.grid_custs.EnableDragGridSize(0)
        self.grid_custs.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)
        self.grid_custs.SetColLabelValue(0, "Vorname")
        self.grid_custs.SetColSize(0, 130)
        self.grid_custs.SetColLabelValue(1, "Name")
        self.grid_custs.SetColSize(1, 130)
        self.grid_custs.SetColLabelValue(2, "RechNr")
        self.grid_custs.SetColSize(2, 75)
        self.grid_custs.SetColLabelValue(3, "Ab")
        self.grid_custs.SetColSize(3, 35)
        self.grid_custs.SetColLabelValue(4, "Zahlung")
        self.grid_custs.SetColSize(4, 90)
        self.grid_custs.SetColLabelValue(5, "Preis")
        self.grid_custs.SetColSize(5, 90)
        self.grid_custs.SetColLabelValue(6, "Info")
        self.grid_custs.SetColSize(6, 110)
        for row in range(0,self.custs_rows):
            for col in range(0,7):
                self.grid_custs.SetReadOnly(row, col)
        self.gridmap.append("Customers")
        self.grid_minrows["Customers"] = self.grid_custs.GetNumberRows()
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick_Custs, self.grid_custs)
        self.setup_date_filter()

        
    ## execution routine for client (tourist) filter
    # overwritten from AfpEvScreen
    def set_client_filter(self):
        value = self.combo_Filter.GetValue()
        if self.debug: print "AfpEvScreen_Tourist.set_client_filter:", value      
        s_key = self.sb.get_value()
        value = self.filtermap[value]
        filter = value.split("-")
        re_filter = "Art LIKE \"Reise\""
        if filter[0] == "Fremd":
            re_filter += " AND AgentNr > 0"
        else:
            re_filter += " AND NOT AgentNr > 0"
        if filter[1]: an_filter = "Zustand LIKE \"" + filter[1] + "\""
        else: an_filter = ""
        if self.sb_date_filter:
            if self.sb_master == "ANMELD":
                if an_filter: an_filter += " AND "
                an_filter += self.get_minor_date_filter()
            else:
                re_filter += " AND " + self.sb_date_filter
        if re_filter != self.sb_re_filter:
            self.sb_re_filter = re_filter
            self.sb.select_where(self.sb_re_filter, None, "EVENT")        
        if an_filter != self.sb_an_filter:
            if not filter[1]:
                self.sb.select_where("", None, "ANMELD")
                self.sb_an_filter = "" 
            else:
                self.sb_an_filter = an_filter
                self.sb.select_where(self.sb_an_filter, None, "ANMELD")   
        #print "AfpEvScreen_Tourist.set_client_filter EVENT:", self.sb_re_filter,"ANMELD:", self.sb_an_filter, "CURRENT RECORD:", self.sb.get_value()

    ## Eventhandler BUTTON, MENU - tour operation
    def On_VehicleOperation(self,event):
        if self.debug: print "AfpEvScreen_Tourist Event handler `On_VehicleOperation'"
        Event = self.get_data(True)
        if not Event.is_new() and Event.is_own_tour():
            needed = AfpEvClient_checkVehicle(self.globals.get_mysql(), Event.get_string_value("Route"))
            #print "AfpEvScreen.On_VehicleOperation needed:", needed
            if needed and self.einsatz:
                selection = Event.get_selection("EINSATZ")
                ENr = None
                #print "AfpEvScreen.On_VehicleOperation Einsatz:", self.einsatz
                #print "AfpEvScreen.On_VehicleOperation:", selection.get_data_length(), selection, Event.selections
                New = False
                if selection.get_data_length() == 0:
                    New = AfpReq_Question("Kein Einsatz für diese Reise vorhanden,".decode("UTF-8"),"neuen Einsatz erstellen?","Einsatz?")
                    if New:
                        Einsatz = self.einsatz[1].AfpEinsatz(Event.get_globals(), None, None, Event.get_value("EventNr"), None, None)  
                        Einsatz.store()                    
                        #print "AfpEvScreen.On_VehicleOperation neuer Einsatz:", Einsatz
                        selection.reload_data()
                if selection.get_data_length() > 0: 
                    if selection.get_data_length() > 1:
                        liste = selection.get_value_lines("StellDatum,StellZeit,StellOrt,Bus")
                        ident = selection.get_values("EinsatzNr")
                        #print "Liste:", liste
                        #print ident
                        Ort = Event.get_string_value("Beginn") + " nach " +Event.get_string_value("Ort") 
                        ENr, Ok = AfpReq_Selection("Bitte Einsatz für Reise am ".decode("UTF-8") , Ort + " auswählen.".decode("UTF-8"), liste, "Einsatzauswahl", ident)
                        ENr = ENr[0]
                    else:
                        ENr = selection.get_value("EinsatzNr")
                        Ok = True
                    if Ok: 
                        #print "AfpEvScreen.On_VehicleOperation EinsatzNr:", ENr
                        Einsatz = self.einsatz[1].AfpEinsatz(Event.get_globals(), ENr)
                        Ok = self.einsatz[0].AfpLoad_DiEinsatz(Einsatz, New)
            else:
                AfpReq_Info("Für eine eigene Reise mit dieser Route".decode("UTF-8") , "ist kein Einsatz nötig!".decode("UTF-8"))
        else:
            AfpReq_Info("Für diese Veranstaltung" , "ist kein Einsatz möglich!".decode("UTF-8"))
        event.Skip()

    ## Eventhandler BUTTON, MENU - modify touristic entry \n
    # overwritten from AfpEvScreen - for depricated use of superbase
    def On_Anmeldung(self,event):   
        #self.sb.set_debug()      
        if self.debug: print "AfpEvScreen_Tourist Event handler `On_Anmeldung'"
        changed = AfpLoad_EvClientEdit_fromSb(self.globals, self.sb, self.flavour)
        #print"On_Anmeldung", changed
        if changed: 
            self.Reload()
        #self.sb.unset_debug()
        event.Skip()  
              
    ## Eventhandler ListBox - double click ListBox 'Archiv'
    def On_DClick_Archiv(self, event):
        if self.debug: print "AfpEvScreen_Tourist Event handler `On_DClick_Archiv'", event
        rows = self.list_id["Archiv"]
        if rows:
            object = event.GetEventObject()
            index = object.GetSelection()
            if index < len(rows):
                delimiter = self.globals.get_value("path-delimiter")
                file = Afp_archivName(rows[index], delimiter)
                if file:
                    filename = Afp_addRootpath(self.globals.get_value("archivdir"), file)
                    if not Afp_existsFile(filename):
                        print "WARNING in AfpEvScreen_Tourist: External file", filename, "does not exist, look in 'antiquedir'." 
                        filename = Afp_addRootpath(self.globals.get_value("antiquedir"), file)
                    if Afp_existsFile(filename):
                        Afp_startFile(filename, self.globals, self.debug, True)
                    else:
                        print "WARNING in AfpEvScreen_Tourist: External file", filename, "does not exist!" 
        event.Skip()
        
    ## Eventhandler Grid - double click Grid 'Customers'
    def On_DClick_Custs(self, event):
        if self.debug: print "AfpEvScreen_Tourist Event handler `On_DClick_Custs'", event
        index = event.GetRow()
        ANr = Afp_fromString(self.grid_id["Customers"][index])
        if ANr:
            #col = event.GetColumn(), Spalte extrahieren, evtl. Selectionsmethode in der Deklaration ändern
            col =event.GetCol()
            self.load_direct(0, ANr)
            self.Reload()
            if col == 6:
                #print "AfpEvScreen.On_DClick_Custs last column selected"
                #text_g = self.grid_custs.getCellValue(index, col)
                name = AfpAdresse(self.globals, self.sb.get_value("KundenNr.ANMELD")).get_name()
                text = self.sb.get_value("Info.ANMELD")
                if not text: text = ""
                text, Ok = AfpReq_Text("Bitte Information für Anmeldung".decode("UTF-8"),  name+ " eingeben.", text, "Info")
                if Ok:
                    data = AfpEvClient(self.globals, ANr)
                    data.set_value("Info", text)
                    data.store()
                    self.Reload()
        event.Skip()
    
    # routines overwritten from grandparent class
    ## load global veriables for this afp-module
    # (overwritten from AfpScreen) 
    def load_additional_globals(self):
        self.globals.set_value(None, None, "Einsatz")
        
    ## set database to show indicated tour
    # @param ENr - number of event 
    # @param ANr - if given, will overwrite ENr, number of tourist entry (AnmeldNummer)
    def load_direct(self, ENr, ANr = None):
        index = self.combo_Sortierung.GetValue()  
        if ANr:
            #self.sb.set_debug()
            self.sb_master = "ANMELD"
            self.sb.CurrentIndexName("AnmeldNr","ANMELD")
            self.sb.select_key(ANr,"AnmeldNr","ANMELD") 
            #print "AfpEvScreen_Tourist.load_direct select key:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD")
            ENr = self.sb.get_value("EventNr.ANMELD")
            if self.combo_Sortierung.FindString("Anmeldung"):
                self.combo_Sortierung.SetValue("Anmeldung")
        elif self.combo_Sortierung.GetValue() == "Anmeldung":
            self.combo_Sortierung.SetSelection(0)
        self.sb.select_key(ENr,"EventNr","EVENT")
        #print "AfpEvScreen_Tourist.load_direct:", ANr, ENr
        self.On_Event_Index()
        #print "AfpEvScreen_Tourist.load_direct Index set:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD")
        self.set_current_record()
        #print "AfpEvScreen_Tourist.load_direct current record:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD")
    ## set current record to be displayed 
    # (overwritten from AfpEvScreen - to allow depricated use of superbase) 
    def set_current_record(self):
        #self.data = self.get_data() 
        #return
        FNr = self.sb.get_value("EventNr")
        #print "AfpEvScreen_Tourist.set_current_record initial:", FNr, self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("RechNr.ANMELD")
        if self.sb_master == "ANMELD": slave = "EVENT"
        else: slave = "ANMELD"
        self.sb.select_key(FNr,"EventNr",slave)
        ANr = self.sb.get_value("AnmeldNr.ANMELD")    
        #print "AfpEvScreen_Tourist.set_current_record ANr:", ANr, FNr, slave
        KNr = self.sb.get_value("KundenNr.ANMELD")      
        TNr = self.sb.get_value("Route.EVENT")      
        PNr = self.sb.get_value("PreisNr.ANMELD") 
        PNr = PNr - 100*(int(PNr/100))
        self.sb.select_key(KNr,"KundenNr","ADRESSE")        
        self.sb.select_key(TNr,"TourNr","TNAME")        
        self.sb.select_key(FNr,"EventNr","PREISE")
        nr = self.sb.get_value("PreisNr.PREISE")
        fnr = FNr
        while self.sb.neof("EventNr","PREISE") and nr != PNr and fnr == FNr:
            self.sb.select_next("EventNr","PREISE")
            nr = self.sb.get_value("PreisNr.PREISE")
            fnr = self.sb.get_value("EventNr.PREISE")
        if fnr != FNr: self.sb.select_key(FNr,"EventNr","PREISE")
        #print "AfpEvScreen_Tourist.set_current_record Fahrt:", FNr,"Anmeld:",ANr,"Kunde:",KNr,"Tour:",TNr,"Preis:",PNr,nr
        return 
        
    ## get names of database tables to be opened for this screen
    # (overwritten from AfpScreen)
    def get_dateinamen(self):
        return ["EVENT","ANMELD","PREISE","ANMELDEX","ADRESSE","TORT", "TNAME"]

    ## get grid rows to populate grids \n
    # (overwritten from AfpEvScreen - to allow depricatesd use of superbase) 
    # @param typ - name of grid to be populated
    def get_grid_rows(self, typ):
        rows = []
        EventNr =  self.sb.get_value("EventNr")     
        select = ( "EventNr = %d")% EventNr
        if typ == "Customers" and self.sb.neof():
            select = ( "EventNr = %d")% EventNr
            if self.sb_an_filter: select = "(" + select +") and (" + self.sb_an_filter + ")"
            tmps = []
            tmps = self.mysql.select_strings("RechNr,Zahlung,Preis,Info,AnmeldNr,Ab,KundenNr",select,"ANMELD")
            for tmp in tmps:
                select =  "KundenNr = " + tmp[-1]
                name = self.mysql.select_strings("Vorname,Name", select,"ADRESSE")
                if not name: name = [["",""]]
                if not tmp[-2]: tmp[-2] = "0"
                select =  "OrtsNr = " + tmp[-2]
                ort = self.mysql.select_strings("Kennung", select,"TORT")
                if not ort: ort = [["--"]]
                #print "AfpEvScreen_Tourist.get_grid_rows append:", name, ort, tmp
                rows.append([name[0][0], name[0][1], tmp[0], ort[0][0]] + tmp[1:-2])
        return rows
# end of class AfpEvScreen_Tourist
