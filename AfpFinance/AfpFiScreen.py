#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFinance.AfpFiScreen
# AfpFiScreen module provides the graphic screen to access all data of the Afp-'Event' modul 
# it holds the class
# - AfpFiScreen
#
#   History: \n
#        28 Nov 2019 - inital code generated - Andreas.Knoblauch@afptech.de


#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright© 1989 - 2020 afptech.de (Andreas Knoblauch)
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
from AfpBase.AfpBaseRoutines import Afp_archivName, Afp_startFile, Afp_startExtraProgram
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Selection, AfpReq_Question, AfpReq_Text, AfpReq_MultiLine
from AfpBase.AfpBaseDialogCommon import AfpLoad_DiReport, AfpReq_extraProgram
from AfpBase.AfpBaseScreen import AfpScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_DiAdEin_fromSb
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

import AfpFinance
from AfpFinance import AfpFiRoutines, AfpFiDialog
from AfpFinance.AfpFiRoutines import *
from AfpFinance.AfpFiDialog import *

import AfpEvent
from AfpEvent import AfpEvRoutines, AfpEvDialog
from AfpEvent.AfpEvRoutines import *
from AfpEvent.AfpEvDialog import AfpLoad_EvAusw, AfpLoad_EvClientEdit, AfpLoad_EventEdit

## Class AfpFiScreen shows 'Event' screen and handles interactions
class AfpFiScreen(AfpScreen):
    ## initialize AfpFiScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        AfpScreen.__init__(self,None, -1, "")
        self.typ = "Finance"
        self.flavour = None
        #self.einsatz = None # to invoke import of 'Einsatz' modules in 'init_database'
        self.slave_data = None
        self.grid_rows["Bookings"] = 14 
        #self.grid_rows["Bookings"] = 7
        self.grid_cols["Bookings"] = 7
        self.grid_row_selected = False
        self.dynamic_grid_name = "Bookings"
        self.dynamic_grid_col_percents = [12, 8, 10, 10, 10, 30, 20]
        self.dynamic_grid_col_labels = ["Datum", "Beleg", "Soll", "Haben", "Betrag", "Bezeichnung", "Name"]
        self.fixed_width = 80
        self.fixed_height = 300
        self.font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "DejaVu Sans")
        self.sb_master = "AUSZUG"
        self.sb_period_filter = ""
        self.sb_filter = ""
        if debug: self.debug = debug
        # self properties
        self.SetTitle("Afp Finance")
        self.initWx()
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.SetForegroundColour(wx.Colour(20, 19, 18))
        self.SetFont(self.font)
        self.Bind(wx.EVT_SIZE, self.On_ReSize)
        if self.debug: print "AfpFiScreen Konstruktor"
    
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
        self.master_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.client_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.grid_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        
        # right BUTTON sizer
        self.combo_Sortierung = wx.ComboBox(panel, -1, value="Auszug", choices=["Auszug","Datum"], size=(100,30), style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Index, self.combo_Sortierung)
        self.indexmap = {"Auszug":"Auszug","Datum":"BuchDat"}
        
        self.button_Auswahl = wx.Button(panel, -1, label="Aus&wahl",size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Ausw, self.button_Auswahl)
        self.button_Neu = wx.Button(panel, -1, label="&Neu",size=(77,50), name="BAnfrage")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)      
        self.button_Modify = wx.Button(panel, -1, label="&Bearbeiten", size=(77,50),name="BBearbeiten")
        self.Bind(wx.EVT_BUTTON, self.On_modify, self.button_Modify)
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
        self.button_mid_sizer.Add(self.button_Neu,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Modify,0,wx.EXPAND)
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
        #self.combo_Filter = wx.ComboBox(panel, -1, value="Veranstaltung-Anmeldungen", size=(164,20), choices=["Veranstaltung-Anmeldungen","Veranstaltung-Stornierungen","Veranstaltung-Reservierungen","Reisen-Anmeldungen","Reisen-Stornierungen"], style=wx.CB_DROPDOWN, name="Filter")
        self.combo_Filter = wx.ComboBox(panel, -1, value="Journal", size=(164,20), choices=["Journal","Auszug","Konten"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        self.combo_Period = wx.ComboBox(panel, -1, value="", size=(84,20), style=wx.CB_DROPDOWN, name="Period")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Period)
        #self.Bind(wx.EVT_TEXT_ENTER, self.On_Jahr_Filter, self.combo_Jahr)
        self.top_mid_sizer.AddStretchSpacer(1)
        self.top_mid_sizer.Add(self.combo_Period,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
        self.top_mid_sizer.Add(self.combo_Filter,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
      
        # Auszug
        self.label_Auszug = wx.StaticText(panel, -1, label="Auszug:", name="LAusz")
        self.text_Auszug= wx.TextCtrl(panel, -1, value="", style=wx.TE_READONLY, name="Ausz")
        self.textmap["Ausz"] = "Auszug.AUSZUG"
        self.text_Dat = wx.TextCtrl(panel, -1, value="", style=wx.TE_READONLY, name="Dat")
        self.textmap["Dat"] = "BuchDat.AUSZUG"
        self.label_SSaldo = wx.StaticText(panel, -1, label="Start:", name="LSSaldo")
        self.text_SSaldo = wx.TextCtrl(panel, -1, value="", style=wx.TE_READONLY, name="SSaldo")
        self.textmap["SSaldo"] = "StartSaldo.AUSZUG"
        self.label_Saldo = wx.StaticText(panel, -1, label="Saldo:", name="LSaldo")
        self.text_Saldo = wx.TextCtrl(panel, -1, value="", style=wx.TE_READONLY, name="Saldo")
        self.textmap["Saldo"] = "EndSaldo.AUSZUG"
      
        self.master_panel_sizer.AddSpacer(10)
        self.master_panel_sizer.Add( self.label_Auszug, 0, wx.EXPAND)
        self.master_panel_sizer.Add( self.text_Auszug, 1, wx.EXPAND)
        self.master_panel_sizer.AddSpacer(10)
        self.master_panel_sizer.Add( self.text_Dat, 1, wx.EXPAND)
        self.master_panel_sizer.AddSpacer(10) 
        self.master_panel_sizer.Add( self.label_SSaldo, 0, wx.EXPAND)
        self.master_panel_sizer.Add( self.text_SSaldo, 1, wx.EXPAND)
        self.master_panel_sizer.AddSpacer(10)
        self.master_panel_sizer.Add( self.label_Saldo, 0, wx.EXPAND)
        self.master_panel_sizer.Add( self.text_Saldo, 1, wx.EXPAND)
        self.master_panel_sizer.AddSpacer(10)

        # GRID
        # self.grid_custs = wx.grid.Grid(panel, -1, pos=(23,256) , size=(653, 264), name="Bookings")
        self.grid_custs = wx.grid.Grid(panel, -1, name="Bookings")
        self.grid_custs.CreateGrid(self.grid_rows["Bookings"], self.grid_cols["Bookings"])
        #self.grid_custs.SetDefaultCellFont(self.font)
        self.grid_custs.SetRowLabelSize(0)
        self.grid_custs.SetColLabelSize(18)
        self.grid_custs.EnableEditing(False)
        self.grid_custs.EnableDragColSize(0)
        self.grid_custs.EnableDragRowSize(0)
        self.grid_custs.EnableDragGridSize(0)
        self.grid_custs.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)
        for col in range(self.grid_cols["Bookings"]):
            self.grid_custs.SetColLabelValue(col, self.dynamic_grid_col_labels[col])
        for row in range(0,self.grid_rows["Bookings"]):
            for col in range(0,self.grid_cols["Bookings"]):
                self.grid_custs.SetReadOnly(row, col)
        self.gridmap.append("Bookings")
        self.grid_minrows["Bookings"] = self.grid_custs.GetNumberRows()
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
        self.panel_left_sizer.Add(self.master_panel_sizer,0,wx.EXPAND)
        self.panel_left_sizer.AddSpacer(10)
        self.panel_left_sizer.Add(self.grid_panel_sizer,1,wx.EXPAND)
        self.panel_left_sizer.AddSpacer(20)
    
        self.sizer.Add(self.panel_left_sizer,1,wx.EXPAND)
        self.sizer.Add(self.button_sizer,0,wx.EXPAND)   
        
        self.setup_period_filter()
        self.dynamic_grid_sizer = self.grid_panel_sizer

    ## compose event specific menu parts
    def create_specific_menu(self):
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Neu", "")
        self.Bind(wx.EVT_MENU, self.On_Neu, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Bearbeiten", "")
        self.Bind(wx.EVT_MENU, self.On_modify, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Zahlung", "")
        self.Bind(wx.EVT_MENU, self.On_Zahlung, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Dokumente", "")
        self.Bind(wx.EVT_MENU, self.On_Listen_Ausgabe, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Einsatz", "")
        self.Bind(wx.EVT_MENU, self.On_VehicleOperation, mmenu)
        tmp_menu.AppendItem(mmenu)
        if self.flavour:
            self.menubar.Append(tmp_menu, self.flavour)
        else:
            self.menubar.Append(tmp_menu, "Event")
        # setup address menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Suche", "")
        self.Bind(wx.EVT_MENU, self.On_MAddress_search, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Be&arbeiten", "")
        self.Bind(wx.EVT_MENU, self.On_Adresse_aendern, mmenu)
        tmp_menu.AppendItem(mmenu)
        self.menubar.Append(tmp_menu, "Adresse")
        return
        
    ## setup date combobox
    def setup_period_filter(self):
        # ToDo: here a selection of all available periods has to be made, possibly with mandate identifier
        year = Afp_getToday().year
        for i in range(5):
            self.combo_Period.Append(Afp_toString(year - i))
        return
        
    ## return globals
    def get_globals(self):
        return self.globals
    ## return actuel valid period
    def get_period(self):
        return self.combo_Period.GetValue()
    ## return mandant if applicable
    def get_mandant(self):
        return None

    ## population routine for special treatment - to be overwritten in derived class
    def Pop_special(self):
        filter = self.combo_Filter.GetValue()
        if filter == "Journal":
            self.text_Auszug.SetValue("")
            self.text_Dat.SetValue("")
            self.text_SSaldo.SetValue("")
            self.text_Saldo.SetValue("")
        elif filter == "Konten":
            self.text_Auszug.SetValue(self.sb.get_string_value("KtNr.KTNR"))
            self.text_Dat.SetValue(self.sb.get_string_value("Bezeichnung.KTNR"))
            ssaldo, saldo = self.data.get_salden()
            self.text_SSaldo.SetValue(Afp_toString(ssaldo))
            self.text_Saldo.SetValue(Afp_toString(saldo))
        return
        
    ## Eventhandler COMBOBOX - filter
    def On_Filter(self,event=None):
        s_key = self.sb.get_value("KtNr")        
        period = self.get_period()
        value = self.combo_Filter.GetValue()
        if self.debug: print "AfpFiScreen.set_filter:", period, value   
        filter = "Period = " + period
        master = "AUSZUG"
        if value == "Konten":
            filter = "NOT KtName = \"SALDO\" AND NOT Typ = \"Kreditor\" AND NOT Typ = \"Debitor\""
            master = "KTNR"
        elif value == "Auszug":
            filter += " AND NOT Auszug = \"SALDO\""
        self.sb.select_where("", None, self.sb_master) # clear old filter
        if self.sb_master != master:
            self.sb_master = master
            self.sb.CurrentFileName(master) 
        self.sb.select_where(filter, None, self.sb_master) 
        #print "AfpFiScreen.set_filter Master:", master, self.sb.CurrentFile.name, self.sb.CurrentFile.CurrentIndex.name, filter
        self.sb.select_current()
        self.CurrentData()
        if event: event.Skip()    
        
    ## return "ANMELD" filter clause from date filter
    def get_minor_date_filter(self):
        return self.sb_date_filter.replace("Beginn","Anmeldung")

    ## Eventhandler COMBOBOX - sort index
    def On_Index(self, event = None):
        value = self.combo_Sortierung.GetValue()
        if self.debug: print "AfpFiScreen Event handler `On_Index'",value
        index = self.indexmap[value]
        if index == "RechNr": 
            master = "ANMELD"
            self.sb.CurrentIndexName("EventNr","EVENT")
            self.sb.CurrentIndexName("AnmeldNr","ANMELD")
        else: master = "EVENT"
        if self.sb_master != master:
            self.sb_master = master
            #print "AfpFiScreen.On_Index master:", master
            self.sb.CurrentFileName(self.sb_master) 
        #print "AfpFiScreen.On_Index index:", index, self.sb_master, master
        self.sb.set_index(index)
        self.sb.CurrentIndexName(index)
        #print "AfpScreen.On_Index current index", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.CurrentFile.indexname, self.sb.CurrentFile.name, self.sb.CurrentFile.CurrentIndex.name
        self.set_jahr_filter()
        #print "AfpScreen.On_Index filter", self.sb.get_value("AnmeldNr.ANMELD")
        self.CurrentData()
        if event: event.Skip()

    ## Eventhandler BUTTON - change address
    def On_Adresse_aendern(self,event):
        if self.debug: print "AfpFiScreen Event handler `On_Adresse_aendern'"
        changed = AfpLoad_DiAdEin_fromSb(self.globals, self.sb)
        if changed: self.Reload()
        event.Skip()
    
    ## Eventhandler BUTTON - proceed inquirery 
    def On_Neu(self,event):
        print "AfpFiScreen Event handler `On_Neu' not implemented!"
        filter = self.combo_Filter.GetValue()
        if filter == "Auszug":
            print "AfpFiScreen.On_Neu:", filter
        elif filter == "Konten":
            print "AfpFiScreen.On_Neu:", filter
        elif filter == "Journal":
            print "AfpFiScreen.On_Neu:", filter
        event.Skip()
            
    ## Eventhandler BUTTON - payment
    def On_Zahlung(self,event):
        print "AfpFiScreen Event handler `On_Zahlung' not implemented!"
        event.Skip()

    ## Eventhandler BUTTON - selection
    def On_Ausw(self,event):
        if self.debug: print "AfpFiScreen Event handler `On_Ausw'"
        filter = self.combo_Filter.GetValue()
        if filter == "Auszug":
            ok, out = AfpFinance_selectStatement(self.globals.get_mysql(), self.get_period(), False)
            if ok:
                ausz = out.split()[0]
                self.sb.select_key(ausz, "Auszug", "AUSZUG")
                self.set_current_record()
                self.Populate()
        elif filter == "Konten":
            list = self.data.get_account_lines("Cash,Other,Kosten,Ertrag")
            kt, ok = AfpReq_Selection("Bitte Konto auswählen:".decode("UTF-8"), "", list)
            if ok:
                ktnr = Afp_fromString(kt.split()[0])
                self.sb.select_key(ktnr, "KtNr", "KTNR")
                self.set_current_record()
                self.Populate()
        event.Skip()

    ## Eventhandler BUTTON, MENU - document generation
    def On_Listen_Ausgabe(self,event):
        if self.debug and event: print "AfpFiScreen Event handler `On_Listen_Ausgabe'"
        Client = self.get_client()
        if not Client.is_new():
            prefix = "Event " + Client.get_string_value("Zustand").strip()
            header = "Anmeldung"
            archiv = "direkt"
            if Client.get_value("AgentNr"):
                if Client.event_is_tour():
                    header = "Reisebüro".decode("UTF-8")
                else:
                    header = "Verkäufer".decode("UTF-8")
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
            #print "AfpFiScreen.On_Listen_Ausgabe:", header, prefix, archiv
            #Client.view()
            variables = self.get_output_variables(Client)
            AfpLoad_DiReport(Client, self.globals, variables, header, prefix, archiv)
        if event:
            self.Reload()
            event.Skip()

    ## Eventhandler BUTTON, MENU - tour operation \n
    # skeletton handler, to be overwritten if tour opwerations are needed \n
    # - not really needed here - but kept als long als menu-entry holds a reference
    def On_VehicleOperation(self,event):
        if self.debug: print "AfpFiScreen Event handler `On_VehicleOperation'"
        AfpReq_Info("Für diese Veranstaltung".decode("UTF-8") , "ist kein Einsatz möglich!".decode("UTF-8"))
        event.Skip()

    ## Eventhandler BUTTON , MENU - modify event
    def On_modify(self,event=None):     
        if self.debug: print "AfpFiScreen Event handler `On_modify'"
        print "AfpFiScreen Event handler `On_modify' not implmented"
        filter = self.combo_Filter.GetValue()
        if filter == "Auszug":
            parlist = {"Auszug": self.text_Auszug.GetValue()}
            res = AfpLoad_FiBuchung(self.get_globals(), self.get_period(), parlist, data)
            print "AfpFiScreen.On_modify:", filter
        elif filter == "Konten":
            print "AfpFiScreen.On_modify:", filter
        elif filter == "Journal":
            print "AfpFiScreen.On_modify:", filter
        if event: event.Skip()
      
    ## Eventhandler Grid - double click Grid 'Bookings'
    def On_DClick_Custs(self, event):
        if self.debug: print "AfpFiScreen Event handler `On_DClick_Custs'"
        self.On_Click_Custs(event)
        data = self.get_client()
        changed = self.load_client_edit(data)
        self.grid_row_selected = True
        if changed: 
            self.Reload()      
        
    ## Eventhandler Grid - single click Grid 'Bookings'
    def On_Click_Custs(self, event):
        if self.debug: print "AfpFiScreen Event handler `On_Click_Custs'"
        index = event.GetRow()
        #print "AfpFiScreen.On_Click_Custs:", self.grid_id["Bookings"], len(self.grid_id["Bookings"]), index
        if len(self.grid_id["Bookings"]) > index:
            self.grid_row_selected = True
            ANr = Afp_fromString(self.grid_id["Bookings"][index])
            if ANr:
                #col = event.GetColumn(), Spalte extrahieren, evtl. Selectionsmethode in der Deklaration ändern
                col = event.GetCol()
                self.load_direct(0, ANr)
                self.Reload()
                if col == 6:
                    #print "AfpFiScreen.On_Click_Custs last column selected"
                    #text_g = self.grid_custs.getCellValue(index, col)
                    name = AfpAdresse(self.globals, self.sb.get_value("KundenNr.ANMELD")).get_name()
                    text = self.sb.get_value("Info.ANMELD")
                    if not text: text = ""
                    text, Ok = AfpReq_Text("Bitte Information für Anmeldung".decode("UTF-8"),  name+ " eingeben.", text, "Info")
                    if Ok:
                        data = self.get_client(ANr)
                        data.set_value("Info", text)
                        data.store()
                        self.Reload()
        event.Skip()
      
    ## Eventhandler MENU - copy an event \n
    def On_MEvent_copy(self,event):   
        print "AfpFiScreen Event handler `On_MEvent_copy' not implemented!"
        event.Skip()  
   
    ## Eventhandler MENU - tourist seach via address 
    def On_MAddress_search(self, event):
        if self.debug: print "AfpFiScreen Event handler `On_MAddress_search'"
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
                text = "Bitte Anmeldung von " + name + " auswählen:".decode("UTF-8")
                if len(rows) > 1:
                    ANr, ok = AfpReq_Selection(text, "", liste, "Anmeldung Auswahl", idents)
                else:
                    ANr = idents[0]
                    ok = True
                #print "AfpFiScreen.On_MAddress_search:", ANr, ok
                if ok:
                    self.load_direct(0, ANr)
                    self.Reload()
        event.Skip()

    ## Eventhandler MENU - tourist menu - not yet implemented!
    def On_MEvent(self, event):
        print "AfpFiScreen Event handler `On_MEvent' not implemented!"
        event.Skip()

    ## Eventhandler Resize - for test reasons
    #def On_ReSize(self, event):
    def On_ReSize_test(self, event):
        print "Event handler `On_ReSize' for Test!"
        print "AfpFiScreen.On_ReSize Top size:", self.top_sizer.GetSize()
        print "AfpFiScreen.On_ReSize Event size:", self.master_panel_sizer.GetSize()
        print "AfpFiScreen.On_ReSize Grid size:", self.grid_panel_sizer.GetSize()
        print "AfpFiScreen.On_ReSize Grid size:", self.grid_custs.GetSize()
        print "AfpFiScreen.On_ReSize Button size:", self.button_sizer.GetSize()
        super(AfpFiScreen, self).On_ReSize(event)
        event.Skip()
        
    ## Eventhandler Keyboard - handle key-down events - overwritten from AfpScreen
    def On_KeyDown(self, event):
        keycode = event.GetKeyCode()        
        if self.debug: print "AfpFiScreen Event handler `On_KeyDown'", keycode
        if keycode == wx.WXK_ESCAPE or keycode == wx.WXK_DELETE:
            self.grid_row_selected = False
            self.grid_custs.ClearSelection()
            if "Bookings" in self.grid_sort_col:
                self.mark_grid_column("Bookings")
                self.Pop_grid()
        super(AfpFiScreen, self).On_KeyDown(event)

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
            #print "AfpFiScreen.load_direct select key:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD")
            ENr = self.sb.get_value("EventNr.ANMELD")
        self.sb.select_key(ENr,"EventNr","EVENT")
        #print "AfpFiScreen.load_direct:", ANr, ENr
        self.On_Index()
        #print "AfpFiScreen.load_direct Index set:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD")
        self.set_current_record()
        #print "AfpFiScreen.load_direct current record:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD")
    
    ## generate appropriate data object for the present screen, overwritten from AfpScreen
    def get_data(self):
        KtNr = self.sb.get_value("KtNr")
        filter = self.combo_Filter.GetValue()
        #print "AfpFiScreen.get_data:", filter, KtNr, self.get_period()
        if filter == "Journal" or not KtNr: 
            return  AfpFinance(self.get_globals(), self.get_period(), None, self.get_mandant())
        elif filter == "Auszug":
            auszug =  self.sb.get_value("Auszug.AUSZUG")
            return  AfpFinance(self.get_globals(), self.get_period(), {"Auszug": auszug}, self.get_mandant())
        else:
            return  AfpFinance(self.get_globals(), self.get_period(), {"Konto": KtNr, "Gegenkonto": KtNr}, self.get_mandant())
    #
    # methods which may be overwritten in devired classes        
    #
    ## set current record to be displayed 
    # (overwritten from AfpScreen) 
    def set_current_record(self):
        self.data = self.get_data() 
        if not self.get_period():
             self.combo_Period.SetValue(self.data.get_period())
        if self.debug: 
            print "AfpFiScreen.set_current_record:",
            self.data.view()
        return

    ## set initial record to be shown, when screen opens the first time
    #overwritten from AfpScreen) 
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        self.sb.CurrentIndexName("KtNr","KTNR")
        self.sb.CurrentIndexName("Auszug","AUSZUG")   
        self.sb.CurrentFileName("AUSZUG")  
        #filter = "Period = " + self.get_period()
        filter = "Period = " + AfpFinance_setPeriod(None, self.globals)
        #print "AfpFiScreen.set_initial_record:", filter
        self.sb.select_where(filter, None, "AUSZUG") 
        self.sb.select_current()
        self.set_current_record() 
        self.sb_master = "Auszug"
        return
    ## supply list of graphic object where keydown events should not be traced.
    def get_no_keydown(self):
        return ["Bookings"]
        #return []
    ## get names of database tables to be opened for this screen
    # (overwritten from AfpScreen)
    def get_dateinamen(self):
        return ["AUSZUG","KTNR"]
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param typ - name of grid to be populated
    def get_grid_rows(self, typ):
        rows = []
        if self.debug: print "AfpFiScreen.get_grid_rows typ:", typ
        #if self.no_data_shown: return  rows
        if typ == "Bookings" and self.data:
            tmps = self.data.get_value_rows("BUCHUNG","Datum,Beleg,Konto,Gegenkonto,Betrag,Bem,KundenNr,BuchungsNr")
            #print "AfpFiScreen.get_grid_rows tmps:", tmps
            #print "AfpFiScreen.get_grid_rows data:", 
            #self.data.view()
            if tmps:			
                for tmp in tmps:
                    name = ""
                    if tmp[6]:
                        name = AfpAdresse(self.globals, tmp[6]).get_name(True)
                    rows.append([Afp_toString(tmp[0]), Afp_toString(tmp[1]), Afp_toString(tmp[2]), Afp_toString(tmp[3]), Afp_toString(tmp[4]), Afp_toString(tmp[5]), name, tmp[7]])
        if self.debug: print "AfpFiScreen.get_grid_rows rows:", rows 
        return rows
# end of class AfpFiScreen
