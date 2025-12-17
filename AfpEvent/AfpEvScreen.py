#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvScreen
# AfpEvScreen module provides the graphic screen to access all data of the Afp-'Event' modul 
# it holds the class
# - AfpEvScreen
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        15 May 2018 - inital code generated - Andreas.Knoblauch@afptech.de


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
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile
from AfpBase.AfpDatabase.AfpSQL import AfpSQL
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import Afp_archivName, Afp_startFile, Afp_startExtraProgram
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Selection, AfpReq_Question, AfpReq_Text, AfpReq_MultiLine, AfpReq_FileName
from AfpBase.AfpBaseDialogCommon import AfpLoad_DiReport, AfpReq_extraProgram, Afp_editMail
from AfpBase.AfpBaseScreen import AfpScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_DiAdEin_fromSb
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

from AfpEvent.AfpEvRoutines import *
from AfpEvent.AfpEvDialog import AfpLoad_EvAusw, AfpLoad_EvClientEdit, AfpLoad_EventEdit, AfpEv_addRegToArchiv

## Class AfpEvScreen shows 'Event' screen and handles interactions
class AfpEvScreen(AfpScreen):
    ## initialize AfpEvScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        AfpScreen.__init__(self,None, -1, "")
        self.typ = "Event"
        self.flavour = None
        #self.einsatz = None # to invoke import of 'Einsatz' modules in 'init_database'
        self.special_agent_output = True
        self.slave_data = None
        #self.grid_rows["Customers"] = 12 
        self.grid_rows["Customers"] = 7
        self.grid_cols["Customers"] = 7
        self.grid_row_selected = False
        self.dynamic_grid_name = "Customers"
        self.dynamic_grid_col_percents = [20, 20, 11, 5, 14, 14, 16]
        self.fixed_width = 80
        self.fixed_height = 300
        self.font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "DejaVu Sans")
        self.sb_master = "EVENT"
        self.sb_date_filter = ""
        self.sb_re_filter = ""
        self.sb_an_filter = ""
        self.name_cache = {}
        if debug: self.debug = debug
        # self properties
        self.SetTitle("Afp Event")
        self.InitWx()
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.SetForegroundColour(wx.Colour(20, 19, 18))
        self.SetFont(self.font)
        self.Bind(wx.EVT_SIZE, self.On_ReSize)
        if self.debug: print("AfpEvScreen Konstruktor")
    
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
        self.event_panel_sizer =wx.GridBagSizer(10,10)
        self.client_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.grid_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        
        # right BUTTON sizer
        self.combo_Sortierung = wx.ComboBox(self, -1, value="Kennung", choices=["Kennung","Bezeichnung","Beginn"], size=(100,30), style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Index, self.combo_Sortierung)
        self.indexmap = {"Kennung":"Kennung","Bezeichnung":"Bez","Ort":"Bez","Beginn":"Beginn"}
        
        self.button_Auswahl = wx.Button(self, -1, label="Aus&wahl",size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Ausw, self.button_Auswahl)
        self.button_Anfrage = wx.Button(self, -1, label="An&frage",size=(77,50), name="BAnfrage")
        self.Bind(wx.EVT_BUTTON, self.On_Anfrage, self.button_Anfrage)      
        self.button_Event = wx.Button(self, -1, label="&Event",size=(77,50), name="Event")
        self.Bind(wx.EVT_BUTTON, self.On_modify, self.button_Event)
        self.button_Anmeldung = wx.Button(self, -1, label="&Anmeldung", size=(77,50),name="BAnmeldung")
        self.Bind(wx.EVT_BUTTON, self.On_Anmeldung, self.button_Anmeldung)
        self.button_Zahlung = wx.Button(self, -1, label="&Zahlung",size=(77,50), name="BZahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahlung)
        self.button_Dokumente = wx.Button(self, -1, label="&Dokumente",size=(77,50), name="BDokumente")
        self.Bind(wx.EVT_BUTTON, self.On_Documents, self.button_Dokumente)
        self.button_Einsatz = wx.Button(self, -1, label="Ein&satz",size=(77,50), name="BEinsatz")
        self.Bind(wx.EVT_BUTTON, self.On_VehicleOperation, self.button_Einsatz)               
        self.button_Einsatz.Enable(False)
        self.button_Ende = wx.Button(self, -1, label="Be&enden",size=(77,50), name="BEnde")
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
        #self.combo_Filter = wx.ComboBox(self, -1, value="Veranstaltung-Anmeldungen", size=(164,20), choices=["Veranstaltung-Anmeldungen","Veranstaltung-Stornierungen","Veranstaltung-Reservierungen","Reisen-Anmeldungen","Reisen-Stornierungen"], style=wx.CB_DROPDOWN, name="Filter")
        self.combo_Filter = wx.ComboBox(self, -1, value="Anmeldungen", size=(164,20), choices=["Anmeldungen","Stornierungen","Reservierungen","Reisen-Anmeldungen","Reisen-Stornierungen"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        self.filtermap = {"Anmeldungen":"Event-Anmeldung","Stornierungen":"Event-Storno","Reservierungen":"Event-Reserv","Reisen-Anmeldungen":"Reisen-Anmeldung","Reisen-Stornierungen":"Reisen-Storno"}
        self.combo_Jahr = wx.ComboBox(self, -1, value="Aktuell", size=(84,20), style=wx.CB_DROPDOWN, name="Jahr")
        self.Bind(wx.EVT_COMBOBOX, self.On_Jahr_Filter, self.combo_Jahr)
        self.Bind(wx.EVT_TEXT_ENTER, self.On_Jahr_Filter, self.combo_Jahr)
        self.top_mid_sizer.AddStretchSpacer(1)
        self.top_mid_sizer.Add(self.combo_Jahr,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
        self.top_mid_sizer.Add(self.combo_Filter,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
      
        # Event
        self.label_Event = wx.StaticText(self, -1, label="Veranstaltung:", name="LEvent")
        self.text_Bez = wx.TextCtrl(self, -1, value="", style=wx.TE_READONLY, name="Bez")
        self.textmap["Bez"] = "Bez.EVENT"
        self.text_Verst = wx.TextCtrl(self, -1, value="", style=wx.TE_READONLY, name="Verst")
        self.textmap["Verst"] = "AgentName.EVENT"
        self.text_Kennung = wx.TextCtrl(self, -1, value="", style=wx.TE_READONLY, name="Kennung")
        self.textmap["Kennung"] = "Kennung.EVENT"
        self.label_Beginn = wx.StaticText(self, -1, label="Beginn:", name="LBeginn")
        self.text_Beginn = wx.TextCtrl(self, -1, value="", style=wx.TE_READONLY, name="Beginn")
        self.textmap["Beginn"] = "Beginn.EVENT"
        self.label_Ende = wx.StaticText(self, -1, label="Zeit:", name="LEnde")
        self.text_Ende = wx.TextCtrl(self, -1, value="", style=wx.TE_READONLY, name="Ende")
        self.textmap["Ende"] = "Uhrzeit.EVENT"
        self.label_Teilnehmer = wx.StaticText(self, -1,  label="Teilnehmer:", name="LTeilnehmer")
        self.text_Personen = wx.TextCtrl(self, -1, value="", style=wx.TE_READONLY, name="Personen")
        self.textmap["Personen"] = "Personen.EVENT"
        self.label_Anmeldungen = wx.StaticText(self, -1,  label="Anmeldungen:", name="LAnmeldungen")
        self.text_Anmeldungen = wx.TextCtrl(self, -1, value="", style=wx.TE_READONLY, name="Anmeldungen")
        self.textmap["Anmeldungen"] = "Anmeldungen.EVENT"
        #self.text_Bem= wx.TextCtrl(self, -1, value="", pos=(135,123), size=(370,35), style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="ReiseBem")
        #self.textmap["ReiseBem"] = "Bem.EVENT"
        #self.text_IntText = wx.TextCtrl(self, -1, value="", pos=(509,50), size=(164,101), style=wx.TE_MULTILINE, name="IntText")
        #self.extmap["IntText"] = "IntText.EVENT"
        
        self.event_panel_sizer.Add( self.label_Event, pos=(0,0), span=(1,2), flag=wx.ALIGN_RIGHT|wx.LEFT|wx.EXPAND, border=10)
        self.event_panel_sizer.Add( self.text_Bez, pos=(0,2), span=(1,4), flag = wx.EXPAND)
        self.event_panel_sizer.Add( self.text_Verst, pos=(0,6), span=(1,2), flag = wx.EXPAND)
        
        self.event_panel_sizer.Add( self.text_Kennung, pos=(1,0), span=(1,2), flag=wx.LEFT|wx.EXPAND, border=10)
        self.event_panel_sizer.Add( self.label_Beginn, pos=(1,2), flag=wx.ALIGN_RIGHT)
        self.event_panel_sizer.Add( self.text_Beginn, pos=(1,3))
        self.event_panel_sizer.Add( self.label_Ende, pos=(1,4), flag=wx.ALIGN_RIGHT)
        self.event_panel_sizer.Add( self.text_Ende, pos=(1,5))
        
        self.event_panel_sizer.Add( self.label_Teilnehmer, pos=(2,0), span=(1,2), flag=wx.ALIGN_RIGHT|wx.LEFT|wx.EXPAND, border=10)
        self.event_panel_sizer.Add( self.text_Personen, pos=(2,2))
        self.event_panel_sizer.Add( self.label_Anmeldungen, pos=(2,3), span=(1,2),flag=wx.ALIGN_RIGHT|wx.EXPAND)
        self.event_panel_sizer.Add( self.text_Anmeldungen, pos=(2,5))

        # GRID
        # self.grid_custs = wx.grid.Grid(self, -1, pos=(23,256) , size=(653, 264), name="Customers")
        self.grid_custs = wx.grid.Grid(self, -1, name="Customers")
        self.grid_custs.CreateGrid(self.grid_rows["Customers"], self.grid_cols["Customers"])
        #self.grid_custs.SetDefaultCellFont(self.font)
        self.grid_custs.SetRowLabelSize(0)
        self.grid_custs.SetColLabelSize(18)
        self.grid_custs.EnableEditing(False)
        self.grid_custs.EnableDragColSize(0)
        self.grid_custs.EnableDragRowSize(0)
        self.grid_custs.EnableDragGridSize(0)
        self.grid_custs.SetSelectionMode(wx.grid.Grid.SelectRows)
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
        
        self.setup_date_filter()
        self.dynamic_grid_sizer = self.grid_panel_sizer

    ## compose event specific menu parts
    def create_specific_menu(self):
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Anmeldung", "")
        self.Bind(wx.EVT_MENU, self.On_Anmeldung, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Kopie", "")
        self.Bind(wx.EVT_MENU, self.On_MEvent_copy, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Bearbeiten", "")
        self.Bind(wx.EVT_MENU, self.On_modify, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Zahlung", "")
        self.Bind(wx.EVT_MENU, self.On_Zahlung, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Dokumente", "")
        self.Bind(wx.EVT_MENU, self.On_Documents, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Einsatz", "")
        self.Bind(wx.EVT_MENU, self.On_VehicleOperation, mmenu)
        tmp_menu.Append(mmenu)
        if self.flavour:
            self.menubar.Append(tmp_menu, self.flavour)
        else:
            self.menubar.Append(tmp_menu, "Event")
        # setup address menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Anfrage", "")
        self.Bind(wx.EVT_MENU, self.On_MAnfrage, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Suchen", "")
        self.Bind(wx.EVT_MENU, self.On_MAddress_search, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Bearbeiten", "")
        self.Bind(wx.EVT_MENU, self.On_Adresse_aendern, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&E-Mail versenden", "")
        self.Bind(wx.EVT_MENU, self.On_MEMail, mmenu)
        tmp_menu.Append(mmenu)
        self.menubar.Append(tmp_menu, "Adresse")
        return
    ## setup date combobox
    def setup_date_filter(self):
        today = Afp_getToday()
        year = today.year
        self.combo_Jahr.Append("Aktuell")
        for i in range(1,5):
            self.combo_Jahr.Append(Afp_toString(year - i))
        self.combo_Jahr.Append("Alle")
        return

    ## Eventhandler COMBOBOX - set date filter
    def On_Jahr_Filter(self,event = None): 
        s_key = self.sb.get_value()        
        self.set_jahr_filter()
        self.sb.select_key(s_key)
        self.CurrentData()
        if event: event.Skip()    
   ## execution routine- set date filter
    def set_jahr_filter(self,event = None): 
        Jahr= Afp_fromString(self.combo_Jahr.GetValue())
        if self.debug: print("AfpEvScreen.set_jahr_filter Combo-String:", Jahr)
        print("AfpEvScreen.set_jahr_filter Combo-String:", Jahr)
        self.set_sb_date_filter(Jahr)
        self.set_client_filter()
    ## set date filter phrase for given input
    # @param Jahr - string or number from which filter has to be build
    def set_sb_date_filter(self, Jahr):
        if Jahr == "Alle":
            self.sb_date_filter = ""
            start = None
        elif Afp_isNumeric(Jahr) and Jahr > 1900:
            start = Afp_genDate(int(Jahr), 1, 1)
            end = Afp_genDate(int(Jahr), 12, 31)
            self.sb_date_filter = "Beginn >= \"" + Afp_toInternDateString(start) + "\" AND Beginn <= \"" + Afp_toInternDateString(end) + "\"" 
        else:
            combo = "Aktuell"
            today = self.globals.today()
            split = Jahr.split()  
            period = None
            if len(split) > 1:
                peri = Afp_fromString(split[1])
                if Afp_isNumeric(peri):
                    if peri < 0:
                        period = -12*peri + today.month - 1
                    elif peri < 100:
                        period = 12*(today.year - 100*int(today.year/100) - peri) + today.month - 1
                    elif peri < today.year - 1900:
                        period = 12*(today.year - peri) + today-month - 1
                    if period: combo += " " + Afp_toString(peri)
            else:
                period = self.globals.get_value("minimum-date-period","Event")
            if not period or period < 0: period = 6
            self.combo_Jahr.SetValue(combo)
            if today.month <= period:
                start = Afp_addMonthToDate(today, period, "-", 1)
            else:    
                start = Afp_genDate(today.year, 1, 1)
            self.sb_date_filter = "Beginn >= \"" + Afp_toInternDateString(start) + "\"" 
        if self.debug: print("AfpEvScreen.set_sb_date Startdate:", start, self.sb_date_filter, "CURRENT RECORD:", self.sb.get_value())
        
    ## Eventhandler COMBOBOX - filter
    def On_Filter(self,event=None):
        s_key = self.sb.get_value()        
        self.set_client_filter()
        self.sb.select_key(s_key)
        self.CurrentData()
        if event: event.Skip()    
    ## execution routine for tourist- filter
    def set_client_filter(self):
        value = self.combo_Filter.GetValue()
        if self.debug: print("AfpEvScreen.set_client_filter:", value)      
        s_key = self.sb.get_value()
        value = self.filtermap[value]
        filter = value.split("-")
        print("AfpEvScreen.set_client_filter Combo:", self.combo_Filter.GetValue(), "Value:", value, "Filter:", filter)
        re_filter = "Art LIKE \"" + filter[0] + "\""
        an_filter = "Zustand LIKE \"" + filter[1] + "\""
        if self.sb_date_filter:
            if self.sb_master == "ANMELD":
                an_filter += " AND " + self.get_minor_date_filter()
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
        print("AfpEvScreen.set_client_filter EVENT:", self.sb_re_filter,"ANMELD:", self.sb_an_filter, "CURRENT RECORD:", self.sb.get_value())
    ## return "ANMELD" filter clause from date filter
    def get_minor_date_filter(self):
        return self.sb_date_filter.replace("Beginn","Anmeldung")

    ## Eventhandler COMBOBOX - sort index
    def On_Index(self, event = None):
        value = self.combo_Sortierung.GetValue()
        if self.debug: print("AfpEvScreen Event handler `On_Index'",value)
        index = self.indexmap[value]
        if index == "RechNr": 
            master = "ANMELD"
            self.sb.CurrentIndexName("EventNr","EVENT")
            self.sb.CurrentIndexName("AnmeldNr","ANMELD")
        else: master = "EVENT"
        if self.sb_master != master:
            self.sb_master = master
            #print "AfpEvScreen.On_Index master:", master
            self.sb.CurrentFileName(self.sb_master) 
        #print ("AfpEvScreen.On_Index index:", index, self.sb_master, master)
        self.sb.set_index(index)
        self.sb.CurrentIndexName(index)
        #print ("AfpScreen.On_Index current index", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.CurrentFile.indexname, self.sb.CurrentFile.name, self.sb.CurrentFile.CurrentIndex.name)
        self.set_jahr_filter()
        #print ("AfpScreen.On_Index filter", self.sb.get_value("AnmeldNr.ANMELD"))
        #breakpoint()
        self.CurrentData()
        #print ("AfpScreen.On_Index End", self.sb.get_value("AnmeldNr.ANMELD"))
        if event: event.Skip()

    ## Eventhandler BUTTON - change address
    def On_Adresse_aendern(self,event):
        if self.debug: print("AfpEvScreen Event handler `On_Adresse_aendern'")
        changed = AfpLoad_DiAdEin_fromSb(self.globals, self.sb)
        if changed: self.Reload()
        event.Skip()
    
    ## Eventhandler BUTTON - proceed inquirery 
    def On_Anfrage(self,event):
        print("AfpEvScreen Event handler `On_Anfrage' not implemented!")
        #print "AfpEvScreen.On_Anfrage globals:", self.globals.view()
        event.Skip()
            
    ## Eventhandler BUTTON - payment
    def On_Zahlung(self,event):
        if self.debug: print("AfpEvScreen Event handler `On_Zahlung'")
        Client = self.get_client()
        #print "AfpEvScreen.On_Zahlung:", Client.is_new()
        if not Client.is_new():
            Ok, data = AfpLoad_DiFiZahl(Client,["RechNr","EventNr"])
            if Ok: 
                #data.view() # for debug
                data.store()
                self.Reload()
        event.Skip()

    ## Eventhandler BUTTON - selection
    def On_Ausw(self,event):
        if self.debug: print("AfpEvScreen Event handler `On_Ausw'")
        #self.sb.set_debug()
        index = self.sb.identify_index().get_name()
        where = AfpSelectEnrich_dbname(self.sb.identify_index().get_where(), "EVENT")
        #value = self.sb.get_string_value(index, True)
        value = self.sb.get_string_value(index)
        auswahl = self.load_event_ausw(index, value, where)
        #auswahl = AfpLoad_EvAusw(self.globals, index, value, where, True)
        if not auswahl is None:
            if self.sb_master == "ANMELD":
                self.sb.CurrentIndexName(Index, "EVENT")
                self.sb_master = "EVENT"
            FNr = int(auswahl)
            self.sb.select_key(FNr, "EventNr", "EVENT")
            self.sb.set_index(index, "EVENT", "EventNr")  
            self.set_current_record()
            if self.sb.eof(): 
                #print "AfpEvScreen.On_Ausw: remove date filter"
                self.combo_Jahr.SetValue("Alle")
                self.set_jahr_filter()
                self.sb.select_key(FNr, "EventNr", "EVENT")
                self.sb.set_index(index, "EVENT", "EventNr")  
                self.set_current_record()
            self.Populate()
        #self.sb.unset_debug()
        if event: event.Skip()

    ## Eventhandler BUTTON, MENU - document generation
    def On_Documents(self, event=None):
        if self.debug and event: print("AfpEvScreen Event handler `On_Documents'")
        Client = self.get_client()
        if not Client.is_new():
            prefix = "Event_Client " + Client.get_string_value("Zustand").strip()
            header = "Anmeldung"
            archiv = ""
            if self.special_agent_output and Client.get_value("AgentNr"):
                if Client.event_is_tour():
                    header = "Reisebüro"
                else:
                    header = "Verkäufer"
                archiv = Client.get_string_value("AgentName")
                agent = "Verkauf"
            else: 
                agent = ""
            if Client.get_value("AgentNr.EVENT"):
                art =  "Fremd"
            else:
                art = "Eigen"
            select = "Modul = \"Event\" AND Art = \"" + art + Client.get_string_value("Art.EVENT")+ "\" and Typ = \""  + Client.get_string_value("Zustand") + agent + "\""
            Client.get_selection("AUSGABE").load_data(select)
            #Client.view()
            variables = self.get_output_variables(Client)
            #print ("AfpEvScreen.On_Documents:", header, prefix, archiv, select, variables)
            AfpLoad_DiReport(Client, self.globals, variables, header, prefix, archiv)
        if event:
            self.Reload()
            event.Skip()

    ## Eventhandler BUTTON, MENU - tour operation \n
    # skeletton handler, to be overwritten if tour opwerations are needed \n
    # - not really needed here - but kept als long als menu-entry holds a reference
    def On_VehicleOperation(self,event):
        if self.debug: print("AfpEvScreen Event handler `On_VehicleOperation'")
        AfpReq_Info("Für diese Veranstaltung" , "ist kein Einsatz möglich!")
        event.Skip()

    ## Eventhandler BUTTON, MENU - modify client entry \n
    def On_Anmeldung(self,event):   
        #self.sb.set_debug()      
        if self.debug: print("AfpEvScreen Event handler `On_Anmeldung'")
        #print("AfpEvScreen Event handler `On_Anmeldung'")
        if self.sb.get_value("EventNr"):
            if self.grid_row_selected:
                data = self.get_client()
            else:
                add = self.globals.get_value("add-registration-to-archive","Event")
                if add:
                    fname = self.get_client_registration()
                data = self.get_client(True)
                ENr = self.sb.get_value("EventNr.EVENT")
                text = "Bitte Person für neue Anmeldung auswählen:"
                KNr = AfpLoad_AdAusw(self.globals,"ADRESSE","NamSort","", None, text, True)
                if KNr:
                    rows, name = AfpAdresse_getListOfTable(self.globals, KNr, "ANMELD", "AnmeldNr,IdNr", "EventNr = " + Afp_toString(ENr))
                    if rows and rows[0]:
                        AfpReq_Info("'" + name + "' ist schon angemeldet!","Bitte die Anmeldung unter der Mitgliedsnummer '" + Afp_toString(rows[0][1]) + "' bearbeiten.")
                        KNr = None
                if KNr: 
                    data.set_new(ENr, KNr) 
                    if data.get_value("Bez.ADRESSE"):
                        ok = AfpReq_Question("Verbundene Adressen gefunden,", "alle Beteiligten gemeinsam anmelden?", "Mehrfachanmeldung")
                        if ok:
                            Bez = AfpAdresse(self.globals, KNr).get_selection("Bez").get_values("KundenNr")
                            bulk = []
                            for b in Bez:
                                bulk.append(b[0])
                            data.add_new_bulk_ids(bulk)
                    if add:
                        client = AfpEv_addRegToArchiv(data, "check", fname)
                        if client is None:
                            if add == "mandatory": 
                                data = None
                        else:
                            if not client == True:
                                data = client                    
                    data = self.Anmeldung_add_data(data)
                else: 
                    data = None
            if data:
                changed = self.load_client_edit(data)
                #print ("AfpEvSreen.On_Anmeldung:", changed)
                if changed: 
                    self.Reload()
                #self.sb.unset_debug()
        event.Skip() 
    ## perform additional data input, may be overwritten in devired class
    # @param client - client data, where additional input shpuld be made
    def Anmeldung_add_data(self, client):
        return client
    ## Eventhandler BUTTON , MENU - modify event
    def On_modify(self,event=None):     
        if self.debug: print("AfpEvScreen Event handler `On_modify'")
        data = self.get_event()
        changed = self.load_event_edit(data)
        if changed: 
            self.Reload()
        if event: event.Skip()
      
    ## Eventhandler Grid - double click Grid 'Customers'
    def On_DClick_Custs(self, event):
        if self.debug: print("AfpEvScreen Event handler `On_DClick_Custs'")
        self.On_Click_Custs(event)
        data = self.get_client()
        changed = self.load_client_edit(data)
        self.grid_row_selected = True
        if changed: 
            self.Reload()      
        
    ## Eventhandler Grid - single click Grid 'Customers'
    def On_Click_Custs(self, event):
        if self.debug: print("AfpEvScreen Event handler `On_Click_Custs'")
        index = event.GetRow()
        #print "AfpEvScreen.On_Click_Custs:", self.grid_id["Customers"], len(self.grid_id["Customers"]), index
        if len(self.grid_id["Customers"]) > index:
            self.grid_row_selected = True
            ANr = Afp_fromString(self.grid_id["Customers"][index])
            if ANr:
                #col = event.GetColumn(), Spalte extrahieren, evtl. Selectionsmethode in der Deklaration ändern
                col = event.GetCol()
                self.load_direct(0, ANr)
                #print ("AfpEvScreen.On_Click_Custs ANr:", ANr)
                self.Reload()
                if col == 6:
                    #print "AfpEvScreen.On_Click_Custs last column selected"
                    #text_g = self.grid_custs.getCellValue(index, col)
                    name = AfpAdresse(self.globals, self.sb.get_value("KundenNr.ANMELD")).get_name()
                    text = Afp_toString(self.sb.get_value("Info.ANMELD"))
                    if not text: text = ""
                    new_text, Ok = AfpReq_Text("Bitte Information für Anmeldung",  name+ " eingeben.", text, "Info")
                    if Ok:
                        Ok = False
                        if text and new_text == "#":
                            Ok = AfpReq_Question("Alle Einträge mit dem Text '" + text + "' löschen?","", "Einträge löschen?")
                        if Ok:
                            data = self.get_event()
                            data.clear_all_infos(text)
                        else:
                            data = self.get_client(ANr)
                            data.set_value("Info", new_text)
                            data.store()
                        self.prepare_reload()
                        self.Reload()
        event.Skip()
      
    ## Eventhandler MENU - copy an event \n
    def On_MEvent_copy(self,event):   
        print("AfpEvScreen Event handler `On_MEvent_copy' not implemented!")
        event.Skip()  
   
    ## Eventhandler MENU - tourist seach via address 
    def On_MAddress_search(self, event):
        if self.debug: print("AfpEvScreen Event handler `On_MAddress_search'")
        name = self.sb.get_string_value("Name.ADRESSE")
        text = "Bitte Adresse auswählen für die Anmeldungen gesucht werden."
        KNr = AfpLoad_AdAusw(self.globals,"ADRESSE","NamSort",name, None, text)
        if KNr:
            rows, name = AfpEvClient_getAnmeldListOfAdresse(self.globals, KNr)
            if rows:
                liste = []
                idents = []
                for row in rows:
                    entry = Afp_ArraytoLine(row, " ", 5)
                    liste.append(entry)
                    idents.append(row[5])
                text = "Bitte Anmeldung von " + name + " auswählen:"
                if len(rows) > 1:
                    ANr, ok = AfpReq_Selection(text, "", liste, "Anmeldung Auswahl", idents)
                else:
                    ANr = idents[0]
                    ok = True
                #print "AfpEvScreen.On_MAddress_search:", ANr, ok
                if ok:
                    self.load_direct(0, ANr)
                    self.Reload()
        event.Skip()

    ## Eventhandler MENU - tourist menu - not yet implemented!
    def On_MEvent(self, event):
        print("AfpEvScreen Event handler `On_MEvent' not implemented!")
        event.Skip()
    def On_MAnfrage(self, event):
        print("Event handler `On_MAnfrage' not implemented!")
        event.Skip()
    ## Eventhandler MENU - send an e-mail
    def On_MEMail(self, event):
        if self.debug: print("Event handler `On_MEMail'")
        an = self.data.get_value("Mail.ADRESSE")
        if an:
            mail = AfpMailSender(self.globals, self.debug)
            mail.add_recipient(an)
            mail, send = Afp_editMail(mail)
            if send: mail.send_mail()
        else:
            AfpReq_Info("Keine Mailadresse gefunden,","keine E-Mail erzeugt!")
        event.Skip()

    ## Eventhandler Resize - for test reasons
    #def On_ReSize(self, event):
    def On_ReSize_test(self, event):
        print("Event handler `On_ReSize' for Test!", event)
        print("AfpEvScreen.On_ReSize Size:", self.GetSize())
        print("AfpEvScreen.On_ReSize Top size:", self.top_sizer.GetSize())
        print("AfpEvScreen.On_ReSize Event size:", self.event_panel_sizer.GetSize())
        print("AfpEvScreen.On_ReSize Grid size:", self.grid_panel_sizer.GetSize())
        print("AfpEvScreen.On_ReSize Grid size:", self.grid_custs.GetSize())
        print("AfpEvScreen.On_ReSize Button size:", self.button_sizer.GetSize())
        super(AfpEvScreen, self).On_ReSize(event)
        event.Skip()
        
    ## Eventhandler Keyboard - handle key-down events - overwritten from AfpScreen
    def On_KeyDown(self, event):
        keycode = event.GetKeyCode()        
        if self.debug: print("AfpEvScreen Event handler `On_KeyDown'", keycode)
        if keycode == wx.WXK_ESCAPE or keycode == wx.WXK_DELETE:
            self.grid_row_selected = False
            self.grid_custs.ClearSelection()
            if "Customers" in self.grid_sort_col:
                self.mark_grid_column("Customers")
                self.Pop_grid()
        super(AfpEvScreen, self).On_KeyDown(event)

    ## set database to show indicated tour
    # @param ENr - number of event 
    # @param ANr - if given, will overwrite ENr, number of client entry (AnmeldNummer)
    def load_direct(self, ENr, ANr = None):
        index = self.combo_Sortierung.GetValue()  
        if ANr:
            #self.sb.set_debug()
            self.sb_master = "ANMELD"
            self.sb.CurrentIndexName("AnmeldNr","ANMELD")
            self.sb.select_key(ANr,"AnmeldNr","ANMELD") 
            self.sb.set_index("RechNr","ANMELD","AnmeldNr")   
            #print ("AfpEvScreen.load_direct select key:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD"))
            ENr = self.sb.get_value("EventNr.ANMELD")
        self.sb.select_key(ENr,"EventNr","EVENT")
        #print ("AfpEvScreen.load_direct:", ANr, ENr)
        self.On_Index()
        #print ("AfpEvScreen.load_direct Index set:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD"))
        self.set_current_record()
        #print ("AfpEvScreen.load_direct current record:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD"))
    
    ## select and show registration form
    def get_client_registration(self):
        fname = None
        wanted = AfpReq_Question("Bitte die Anmeldung einscannen und die gescannte Datei auswählen!","")
        if wanted:
            dir = self.data.get_globals().get_value("docdir")
            fname, ok = AfpReq_FileName(dir, "Anmeldung auswählen!" ,"", True)
            if ok:
                Afp_startFile(fname, self.data.get_globals(), self.data.is_debug(), True)
        return fname
   ## generate AfpEvent or AfpEvClient object from the present screen, overwritten from AfpScreen
    # @param event - flag if 'Event'  should be generated, otherwise 'EvClient'
    def get_data(self, event = None):
        if event is None:
            event = self.sb_master == "EVENT"
            if not self.grid_row_selected is None:
                 event = not self.grid_row_selected
        if event:
            return  self.get_event()
        else:
            return  self.get_client()
    #
    # methods which may be overwritten in devired classes        
    #
    ## generate the dedicated event
    # @param ENr - if given:True - new event; Number - EventNr of event
    def get_event(self, ENr = None):
        if ENr == True: return AfpEvent(self.globals)
        elif ENr:  return  AfpEvent(self.globals, ENr)
        if self.sb.get_value() == self.data.get_value():
            return self.data
        else:
            return  AfpEvent(self.globals, None, self.sb)
    ## load event selection dialog (Ausw)
    # @param index - column which should give the order
    # @param value -  initial value to be searched
    # @param where - filter for search in table
    def load_event_ausw(self,  index, value, where):
        return AfpLoad_EvAusw(self.globals, index, value, where, True)
    ## load event edit dialog
    # @param data - data to be edited
    def load_event_edit(self, data):
        return AfpLoad_EventEdit(data, self.flavour)
    ## generate the dedicated event client
    # @param ANr - if given:True - new client; Number - AnmeldNr of client
    def get_client(self, ANr = None):
        if ANr == True: return AfpEvClient(self.globals)
        elif ANr:  return  AfpEvClient(self.globals, ANr)
        return  AfpEvClient(self.globals, None, self.sb)
    ## load client edit dialog
    # @param data - data to be edited
    def load_client_edit(self, data):
        return AfpLoad_EvClientEdit(data, self.flavour)
    ## generate nedded oiutput variables
    # @param data - data to be used for output
    def get_output_variables(self, data):
        vars= {"Today" : self.globals.today()}
        return vars
        
    ## set current record to be displayed 
    # (overwritten from AfpScreen) 
    def set_current_record(self):
        self.data = self.get_event() 
        if self.debug: print("AfpEvScreen.set_current_record EventNr: ", self.data.get_value())
        if self.debug: self.data.view()
        #print ("AfpEvScreen.set_current_record: ", self.data.get_value())
        #self.data.view()
        return

    ## set initial record to be shown, when screen opens the first time
    #overwritten from AfpScreen) 
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        ENr = 0
        ANr = 0    
        #self.sb.CurrentIndexName("KundenNr","ADRESSE")
        self.sb.CurrentIndexName("EventNr","ANMELD")   
        self.sb.CurrentIndexName("EventNr","EVENT") 
        if origin == "Adresse":
            KNr = self.sb.get_value("KundenNr.ADRESSE")
            self.sb.CurrentIndexName("KundenNr","ANMELD") 
            self.sb.select_key(KNr, "KundenNr","ANMELD")
            if self.sb.get_value("KundenNr.ANMELD") == KNr: ANr = self.sb.get_value("AnmeldNr.ANMELD")
        elif origin:
            #ENr = self.sb.get_value("Reise.ADRESSE")
            ENr = self.globals.get_value("EventNr", origin)
        if ENr is None: ENr = 0
        # only for testing: in real life startdate  date + 14 should be selected
        #if ENr == 0: ENr = 2213
        if ENr or ANr:
            self.load_direct(ENr, ANr)
        else:
            #self.sb.select_last() # fallback
            self.sb.select_first() # fallback
            self.On_Index()
            self.sb.select_current()
        #self.set_current_record() # needed?
        return
    ## check if slave exists
    def slave_exists(self):
        FNr =  self.sb.get_value("EventNr.EVENT")     
        fnr =  self.sb.get_value("EventNr.ANMELD") 
        if not FNr: FNr = -1
        if self.sb.eof(): fnr = FNr + 1
        return FNr == fnr
    ## check if string points to slave data
    def is_slave(self, string):
        Ok = False
        split = string.split(".")
        if len(split) > 1:
            if split[1] == "ANMELD" or split[1] == "Anmeld" or split[1] == "ADRESSE" or split[1] == "Adresse":
                Ok = True
        if self.sb.eof(): Ok = True
        return Ok
    ## prepare the reload on the data of screen
    # @param complete - flag if a complete reload from database should be performed, default: True
    def prepare_reload(self, complete = True):
        return
    ## supply list of graphic object where keydown events should not be traced.
    def get_no_keydown(self):
        return ["Customers"]
        #return []
    ## get names of database tables to be opened for this screen
    # (overwritten from AfpScreen)
    def get_dateinamen(self):
        return ["EVENT","ANMELD","PREISE","ANMELDEX","ADRESSE"]
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param typ - name of grid to be populated
    def get_grid_rows(self, typ):
        rows = []
        if self.debug: print("AfpEvScreen.get_grid_rows typ:", typ)
        if self.no_data_shown: return  rows
        if typ == "Customers" and self.data:
            id_col = 5      
            tmps = self.data.get_value_rows("ANMELD","RechNr,Zahlung,Preis,Info,AnmeldNr,Ab,KundenNr")
            #print "AfpEvScreen.get_grid_rows tmps:", tmps
            #print "AfpEvScreen.get_grid_rows data:", 
            #self.data.view()
            if tmps:			
                for tmp in tmps:
                    if tmp[6] in self.name_cache:
                        namen = self.name_cache[tmp[6]]
                    else:
                        adresse = AfpAdresse(self.globals, tmp[6])
                        namen = [adresse.get_string_value("Vorname"), adresse.get_string_value("Name")]
                        self.name_cache[tmp[6]] = namen
                    ab = "" 
                    if self.data.has_route() and tmp[5]:
                        print("WARNING: AfpEvScreen.get_grid_rows data has route not implemented!")
                    rows.append([namen[0], namen[1], Afp_toString(tmp[0]), ab, Afp_toString(tmp[1]), Afp_toString(tmp[2]), Afp_toString(tmp[3]), tmp[4]])
        if self.debug: print("AfpEvScreen.get_grid_rows rows:", rows) 
        return rows
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param typ - name of grid to be populated
    def get_grid_rows_clients(self, typ):
        rows = []
        if self.debug: print("AfpEvScreen.get_grid_rows typ:", typ)
        if self.no_data_shown: return  rows
        if typ == "Customers" and self.data:
            id_col = 5      
            clients = self.data.get_clients(False)
            if clients:			
                for client in clients:
                    rows.append([client.get_string_value("Vorname.ADRESSE"), client.get_string_value("Name.ADRESSE"), client.get_string_value("RechNr"),  client.get_string_value("Name.TNAME"), client.get_string_value("Zahlung"),  client.get_string_value("Preis"),  client.get_string_value("Info"),  client.get_value("AnmeldNr")])
        if self.debug: print("AfpEvScreen.get_grid_rows rows:", rows) 
        print("AfpEvScreen.get_grid_rows_clients length:", typ, len(clients), len(rows))
        return rows
# end of class AfpEvScreen
