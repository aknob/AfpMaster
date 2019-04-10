#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvScreen_Verein
# AfpEvScreen_Verein module provides the graphic screen to access all data of the Afp-'Verein' modul 
# it holds the class
# - AfpEvScreen_Verein
#
#   History: \n
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
from AfpEvent.AfpEvDialog import AfpLoad_EvAusw, AfpLoad_EventEdit_fromSb, AfpLoad_EvClientEdit_fromSb

## Class AfpEvScreen_Verein shows 'Event' screen and handles interactions
class AfpEvScreen_Verein(AfpEvScreen):
    ## initialize AfpEvScreen_Verein, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        self.flavour = "Verein"
        #self.einsatz = None # to invoke import of 'Einsatz' modules in 'init_database'
        self.clubnr = None
        AfpEvScreen.__init__(self, debug)
        self.SetTitle("Afp Verein")
        self.grid_row_selected = None
        self.dynamic_grid_col_percents = [ 5, 20, 20, 11, 14, 14, 16]
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
        self.event_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.event_right_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.event_left_sizer =wx.GridBagSizer(10,10)
        self.grid_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        
        # right BUTTON sizer
        self.combo_Sortierung = wx.ComboBox(panel, -1, value="Kennung", choices=["Kennung","Bezeichnung"], size=(100,30), style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Index, self.combo_Sortierung)
        self.indexmap = {"Kennung":"Kennung","Bezeichnung":"Bez","Ort":"Bez","Beginn":"Beginn"}
        
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
        self.button_sizer.Add(self.button_low_sizer,0,wx.EXPAND)
     
        # COMBOBOX
        self.combo_Filter = wx.ComboBox(panel, -1, value="Anmeldungen", size=(164,20), choices=["Anmeldungen","Stornierungen","Reservierungen"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        self.filtermap = {"Anmeldungen":"Verein-Anmeldung","Stornierungen":"Verein-Storno","Reservierungen":"Verein-Reserv"}
        self.top_mid_sizer.AddStretchSpacer(1)
        self.top_mid_sizer.Add(self.combo_Filter,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
      
        # Event
        self.label_Event = wx.StaticText(panel, -1, label="Verein:", name="LEvent")
        self.text_Event = wx.TextCtrl(panel, -1, value="", size=(100,20), style=wx.TE_READONLY, name="Verein")
        self.textmap["Verein"] = "Name.Agent"
        self.text_Verst = wx.TextCtrl(panel, -1, value="", style=wx.TE_READONLY, name="VKenn")
        self.textmap["VKenn"] = "Tag#1.Verein"
        self.label_Sparte = wx.StaticText(panel, -1, label="Sparte:", name="LSparte")
        self.text_Kennung = wx.TextCtrl(panel, -1, value="", style=wx.TE_READONLY, name="Kennung")
        self.textmap["Kennung"] = "Kennung.EVENT"
        self.text_Bez = wx.TextCtrl(panel, -1, value="", style=wx.TE_READONLY, name="Bez")
        self.textmap["Bez"] = "Bez.EVENT"
        self.label_Mitglieder = wx.StaticText(panel, -1,  label="Mitglieder:", name="LMitglieder")
        self.text_Anmeldungen = wx.TextCtrl(panel, -1, value="", style=wx.TE_READONLY, name="Anmeldungen")
        self.textmap["Anmeldungen"] = "Anmeldungen.EVENT"
        self.text_Bem= wx.TextCtrl(panel, -1, value="", style=wx.TE_MULTILINE|wx.TE_LINEWRAP|wx.EXPAND, name="EventBem")
        self.textmap["EventBem"] = "Bem.EVENT"
        
        self.event_left_sizer.Add( self.label_Event, pos=(0,0), flag=wx.ALIGN_RIGHT|wx.LEFT|wx.EXPAND)
        self.event_left_sizer.Add( self.text_Event, pos=(0,1), span=(1,2), flag = wx.EXPAND)
        self.event_left_sizer.Add( self.text_Verst, pos=(0,3), flag = wx.EXPAND)
        self.event_left_sizer.Add( self.label_Sparte, pos=(1,0), flag=wx.ALIGN_RIGHT|wx.LEFT|wx.EXPAND)
        self.event_left_sizer.Add( self.text_Kennung, pos=(1,1), flag=wx.LEFT|wx.EXPAND)
        self.event_left_sizer.Add( self.text_Bez, pos=(1,2), span=(1,2), flag = wx.EXPAND)
        self.event_left_sizer.Add( self.label_Mitglieder, pos=(1,4), flag=wx.ALIGN_RIGHT|wx.LEFT|wx.EXPAND)
        self.event_left_sizer.Add( self.text_Anmeldungen, pos=(1,5), flag = wx.EXPAND)
        self.event_left_sizer.AddGrowableCol(1)
        self.event_left_sizer.AddGrowableCol(2)
        self.event_left_sizer.AddGrowableCol(3)
        
        self.event_right_sizer.Add( self.text_Bem, 1, wx.EXPAND)
        self.event_panel_sizer.AddSpacer(10)
        self.event_panel_sizer.Add(self.event_left_sizer, 3, wx.EXPAND)
        self.event_panel_sizer.AddSpacer(10)
        self.event_panel_sizer.Add(self.event_right_sizer, 1, wx.EXPAND)
        self.event_panel_sizer.AddSpacer(10)

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
        
        self.grid_panel_sizer.AddSpacer(10)
        self.grid_panel_sizer.Add(self.grid_custs,1,wx.EXPAND)
        self.grid_panel_sizer.AddSpacer(10)
       
        self.top_sizer.Add(self.modul_button_sizer,0,wx.EXPAND)
        self.top_sizer.Add(self.top_mid_sizer,1,wx.EXPAND)
       
        self.panel_left_sizer.AddSpacer(10)
        self.panel_left_sizer.Add(self.top_sizer,0,wx.EXPAND)
        self.panel_left_sizer.AddSpacer(10)
        self.panel_left_sizer.Add(self.event_panel_sizer,0,wx.EXPAND)
        self.panel_left_sizer.AddSpacer(10)
        self.panel_left_sizer.Add(self.grid_panel_sizer,1,wx.EXPAND)
        self.panel_left_sizer.AddSpacer(10)
    
        self.sizer.Add(self.panel_left_sizer,1,wx.EXPAND)
        self.sizer.Add(self.button_sizer,0,wx.EXPAND)   
        
        self.dynamic_grid_sizer = self.grid_panel_sizer
        
   ## execution routine- set date filter
   # dummy only needed to use the AfpEvScreen-routines
    def set_jahr_filter(self,event = None): 
        return

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

    ## set current record to be displayed 
    # (overwritten from AfpEvScreen) 
    def set_current_record(self):
        ini = True
        if self.data and self.clubnr == self.data.get_value("AgentNr"): ini = False
        if ini:
            self.sb.select_key(self.clubnr , "AgentNr","EVENT")
            self.sb.set_index("Kennung","EVENT","AgentNr")            
            self.sb.CurrentIndexName("Kennung","EVENT")
        self.data = self.get_data(True) 
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
        #print "AfpEvScreen_Verein.set_initial_record initial record set:", self.sb.get_value()
        self.On_Index()
        self.sb.select_current()
        return
        
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param typ - name of grid to be populated
    def get_grid_rows(self, typ):
        rows = []
        if self.debug: print "AfpEvScreen.get_grid_rows typ:", typ
        if self.no_data_shown: return  rows
        if typ == "Customers" and self.data:
            tmps = self.data.get_value_rows("ANMELD","IdNr,Zahlung,Preis,Info,Anmeldung,KundenNr,AnmeldNr")
            if tmps:			
                for tmp in tmps:
                    adresse = AfpAdresse(self.globals, tmp[5])
                    rows.append([Afp_toString(tmp[0]), adresse.get_string_value("Vorname"), adresse.get_string_value("Name"),  Afp_toString(tmp[4]), Afp_toString(tmp[2]), Afp_toString(tmp[1]), Afp_toString(tmp[3]), tmp[6]])
        if self.debug: print "AfpEvScreen.get_grid_rows rows:", rows 
        return rows

 # end of class AfpEvScreen_Verein
