#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFinance.AfpFiScreen
# AfpFiScreen module provides the graphic screen to access all data of the Afp-'Event' modul 
# it holds the class
# - AfpFiScreen
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        28 Nov 2019 - inital code generated - Andreas.Knoblauch@afptech.de


#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
#    Copyright© 1989 - 2025 afptech.de (Andreas Knoblauch)
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
from AfpBase.AfpBaseFiDialog import *
from AfpBase.AfpBaseFiRoutines import *

import AfpFinance
from AfpFinance import AfpFiRoutines, AfpFiDialog
from AfpFinance.AfpFiRoutines import *
from AfpFinance.AfpFiDialog import *

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
        self.grid_col_labels =[["Datum", "Beleg", "Soll", "Haben", "Betrag", "Bezeichnung", "Name"], ["Datum", "Nr", "Pos", "Konto", "Betrag", "Bezeichnung", "Name"], ["Datum", "Nr", "Ext", "Konto", "Betrag", "Bezeichnung", "Name"]]
        self.dynamic_grid_name = "Bookings"
        self.dynamic_grid_col_percents = [12, 8, 10, 10, 10, 30, 20]
        self.dynamic_grid_col_labels = self.grid_col_labels[0]
        self.sort_choices_list = [["Auszug","Datum"],["Offen","Einzeln","Dauer","Beglichen","Jahr"]]
        self.indexmap_list = [{"Auszug":"Auszug","Datum":"BuchDat"},{"Offen":"Zustand = \"Open\" OR Zustand = \"Static\"", "Einzeln": "Zustand = \"Open\"", "Beglichen":  "Zustand = \"Closed\"", "Dauer": "Zustand = \"Static\"","Jahr": None}]
        self.sort_choices = self.sort_choices_list[0]
        self.indexmap = self.indexmap_list[0]
        self.sort_filter = "Zustand = \"Open\" OR Zustand = \"Static\""
        self.sort_index = 0
        self.search = None
        self.search_indices = None
        self.fixed_width = 80
        self.fixed_height = 300
        self.font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "DejaVu Sans")
        self.sb_master = "AUSZUG"
        self.sb_period_filter = ""
        self.sb_filter = ""
        self.mandant = None
        if debug: self.debug = debug
        # self properties
        self.SetTitle("Afp Finance")
        self.initWx()
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.SetForegroundColour(wx.Colour(20, 19, 18))
        self.SetFont(self.font)
        self.Bind(wx.EVT_SIZE, self.On_ReSize)
        if self.debug: print("AfpFiScreen Konstruktor")
    
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
        self.combo_Sortierung = wx.ComboBox(panel, -1, value="Auszug", choices=self.sort_choices, size=(100,30), style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Index, self.combo_Sortierung)
        
        self.button_Auswahl = wx.Button(panel, -1, label="Aus&wahl",size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Ausw, self.button_Auswahl)
        self.button_Neu = wx.Button(panel, -1, label="&Neu",size=(77,50), name="BAnfrage")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)      
        self.button_Modify = wx.Button(panel, -1, label="&Bearbeiten", size=(77,50),name="BBearbeiten")
        self.Bind(wx.EVT_BUTTON, self.On_modify, self.button_Modify)
        self.button_Zahlung = wx.Button(panel, -1, label="&Zahlung",size=(77,50), name="BZahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahlung)
        self.button_Zahlung.Enable(False)
        self.button_Dokumente = wx.Button(panel, -1, label="&Dokumente",size=(77,50), name="BDokumente")
        self.Bind(wx.EVT_BUTTON, self.On_Documents, self.button_Dokumente)
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
        self.combo_Filter = wx.ComboBox(panel, -1, value="Konten", size=(164,20), choices=["Journal","Konten","Auszug","Ausgang","Eingang"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        self.combo_Period = wx.ComboBox(panel, -1, value="", size=(84,20), style=wx.CB_DROPDOWN, name="Period")
        self.Bind(wx.EVT_COMBOBOX, self.On_Jahr_Filter, self.combo_Period)
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
        self.grid_custs.SetSelectionMode(wx.grid.Grid.GridSelectRows)
        for col in range(self.grid_cols["Bookings"]):
            self.grid_custs.SetColLabelValue(col, self.dynamic_grid_col_labels[col])
        for row in range(0,self.grid_rows["Bookings"]):
            for col in range(0,self.grid_cols["Bookings"]):
                self.grid_custs.SetReadOnly(row, col)
        self.gridmap.append("Bookings")
        self.grid_minrows["Bookings"] = self.grid_custs.GetNumberRows()
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick_Custs, self.grid_custs)
        
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

    ## compose event specific menu parts
    def create_specific_menu(self):
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Auswahl", "")
        self.Bind(wx.EVT_MENU, self.On_Ausw, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Neu", "")
        self.Bind(wx.EVT_MENU, self.On_Neu, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Dokumente", "")
        self.Bind(wx.EVT_MENU, self.On_Documents, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Barkasse", "")
        self.Bind(wx.EVT_MENU, self.On_MKasse, mmenu)
        tmp_menu.Append(mmenu)
        self.menubar.Append(tmp_menu, "Finance")
        # setup address menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Suche", "")
        self.Bind(wx.EVT_MENU, self.On_MAddress_search, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Be&arbeiten", "")
        self.Bind(wx.EVT_MENU, self.On_Adresse_aendern, mmenu)
        tmp_menu.Append(mmenu)
        self.menubar.Append(tmp_menu, "Adresse")
        return
                
    ## setup date combobox
    def setup_period_filter(self):
        # ToDo: here a selection of all available periods has to be made, possibly with mandate identifier
        year = Afp_getToday().year
        for i in range(5):
            self.combo_Period.Append(Afp_toString(year - i))
        return
    ## execution routine- set date filter from period indicator
    def setup_date_filter(self): 
        filter = None
        Jahr= Afp_fromString(self.get_period())
        if Afp_isNumeric(Jahr) and Jahr > 1900:
            start = Afp_genDate(int(Jahr), 1, 1)
            end = Afp_genDate(int(Jahr), 12, 31)
            filter = "Datum >= \"" + Afp_toInternDateString(start) + "\" AND Datum <= \"" + Afp_toInternDateString(end) + "\"" 
        return filter
        
    ## return globals
    def get_globals(self):
        return self.globals
    ## return actuel valid period
    def get_period(self):
        return self.combo_Period.GetValue()
    ## return mandant if applicable
    def get_mandant(self):
        if self.mandant: return self.mandant
        if self.data:
            return self.data.get_globals().get_value("actuel-transaction-mandat","Finance")
        return None
    
    ## generate appropriate data object for seleted grid-row
    def get_selected_data(self):
        filter = self.combo_Filter.GetValue()
        indices = self.grid_custs.GetSelectedRows()
        index = None
        if indices: index = indices[0]
        #print("AfpFiScreen.get_selected_data:", filter, indices, self.grid_id, not index is None and "Bookings" in self.grid_id and len(self.grid_id["Bookings"]) > index)
        if not index is None and "Bookings" in self.grid_id and len(self.grid_id["Bookings"]) > index:
            self.grid_row_selected = True
            Nr = Afp_fromString(self.grid_id["Bookings"][index])
            #print("AfpFiScreen.get_selected_data Nr:", filter, index, Nr)
            if filter == "Journal" or  filter == "Auszug" or filter == "Konten": 
                return  AfpFinanceSingleTransaction(self.get_globals(), Nr)
            elif filter == "Ausgang":
                return AfpCommonInvoice(self.data.get_globals(), Nr)
            elif filter == "Eingang":
                return AfpObligation(self.data.get_globals(), Nr)
        return None

    ## population routine for special treatment - to be overwritten in derived class
    def Pop_special(self):
        filter = self.combo_Filter.GetValue()
        #print "AfpFiScreen.Pop_special Filter:",  filter
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
        elif filter == "Auszug":
            ssaldo, saldo = self.data.get_salden()
            self.text_SSaldo.SetValue(Afp_toString(ssaldo))
            self.text_Saldo.SetValue(Afp_toString(saldo))
        return
        
    ## Eventhandler COMBOBOX - jahr
    def On_Jahr_Filter(self,event=None):
        period = self.get_period()            
        value = self.combo_Filter.GetValue()
        #print "AfpFiScreen.On_Jahr_Filter:", period, value  
        if self.debug: print("AfpFiScreen.On_Jahr_Filter:", period, value)   
        if value == "Ausgang" or value == "Eingang":
            if self.sort_choices[self.sort_index] == "Jahr":
                self.sort_filter = self.setup_date_filter()
                self.data = self.get_data()
                self.Pop_grid()
        else:
            self.On_Filter()
        if event: event.Skip()  
        
    ## Event handler filter combo box
    def On_Filter(self,event=None):
        s_key = self.sb.get_value("KtNr")        
        period = self.get_period()
        value = self.combo_Filter.GetValue()
        #print "AfpFiScreen.On_Filter:", period, value  
        if self.debug: print("AfpFiScreen.On_Filter:", period, value)   
        if value == "Ausgang" or value == "Eingang":
            if value == "Eingang":
                self.dynamic_grid_col_labels = self.grid_col_labels[2]
            else:
                self.dynamic_grid_col_labels = self.grid_col_labels[1]
            self.sort_choices = self.sort_choices_list[1] 
            self.indexmap = self.indexmap_list[1]
            sort_index = self.sort_index
            self.button_Zahlung.Enable(True)
        else:
            self.dynamic_grid_col_labels = self.grid_col_labels[0]
            self.sort_choices = self.sort_choices_list[0]
            self.indexmap = self.indexmap_list[0]
            sort_index = 0
            self.button_Zahlung.Enable(False)
        for col in range(self.grid_cols["Bookings"]):
            self.grid_custs.SetColLabelValue(col, self.dynamic_grid_col_labels[col])
        self.combo_Sortierung.SetItems(self.sort_choices)
        self.combo_Sortierung.SetSelection(sort_index)
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
        #print ("AfpFiScreen.set_filter Master:", master, self.sb.CurrentFile.name, self.sb.CurrentFile.CurrentIndex.name, filter)
        self.sb.select_current()
        self.grid_scrollback()
        self.CurrentData()
        if event: event.Skip()    
 
    ## Eventhandler COMBOBOX - sort index
    def On_Index(self, event = None):
        value = self.combo_Sortierung.GetValue()
        typ = self.combo_Filter.GetValue()
        if self.debug: print("AfpFiScreen Event handler `On_Index'",value)
        index = self.indexmap[value]
        if typ == "Ausgang" or typ == "Eingang":
            if index  is None: index = self.setup_date_filter()
            #print("AfpFiScreen.On_Index:",value, typ, index)
            self.sort_filter = index
            self.sort_index = self.sort_choices.index(value)
            self.data = self.get_data()
            self.Pop_grid()
        else:
            if index == "RechNr": 
                master = "ANMELD"
                self.sb.CurrentIndexName("EventNr","EVENT")
                self.sb.CurrentIndexName("AnmeldNr","ANMELD")
            else: master = "EVENT"
            if self.sb_master != master:
                self.sb_master = master
                self.sb.CurrentFileName(self.sb_master) 
            self.sb.set_index(index)
            self.sb.CurrentIndexName(index)
            #self.set_jahr_filter()
            self.CurrentData()
        if event: event.Skip()

    ## Eventhandler BUTTON - change address
    def On_Adresse_aendern(self,event):
        if self.debug: print("AfpFiScreen Event handler `On_Adresse_aendern'")
        changed = AfpLoad_DiAdEin_fromSb(self.globals, self.sb)
        if changed: self.Reload()
        event.Skip()
    
    ## Eventhandler BUTTON - proceed inquirery 
    def On_Neu(self,event):
        if self.debug: print("AfpFiScreen Event handler `On_Neu'")
        filter = self.combo_Filter.GetValue()
        if filter == "Eingang" or filter == "Ausgang":
            if filter == "Eingang": 
                data = AfpObligation(self.get_globals())
            else:
                data = AfpCommonInvoice(self.get_globals())
            #print "AfpFiScreen.On_Neu:", data.view()
            ok = Afp_newSimpleInvoice(data)  
            if ok: self.Reload()
        elif filter == "Konten":
            ktnr = Afp_fromString(self.text_Auszug.GetValue())
            #changed = AfpLoad_FiBuchung(self.data.get_globals(), self.data.get_period(), {"Konto": ktnr, "Gegenkonto": ktnr, "no_strict_accounting": None})
            changed = AfpLoad_FiBuchung(self.data.get_globals(), self.data.get_period(), {"no_strict_accounting": None})
        else:
            print("AfpFiScreen.On_Neu:", filter)
        event.Skip()
            
    ## Eventhandler BUTTON - payment
    def On_Zahlung(self,event):
        if self.debug: print("AfpFiScreen Event handler `On_Zahlung'")
        ok = None
        data = None
        filter = self.combo_Filter.GetValue()
        if filter == "Ausgang" or filter == "Eingang":
            data = self.get_selected_data()
            ok, data = AfpLoad_DiFiZahl(data)
        else:
            print("AfpFiScreen Event handler `On_Zahlung' not implemented for filter '" + filter + "'")
        #print("AfpFiScreen.On_Zahlung:", ok, data)
        event.Skip()

    ## Eventhandler BUTTON - selection
    def On_Ausw(self,event):
        if self.debug: print("AfpFiScreen Event handler `On_Ausw'")
        self.grid_scrollback()
        filter = self.combo_Filter.GetValue()
        if filter == "Journal":
            period = self.combo_Period.GetValue()
            self.search = None
            text = ""
            text, ok = AfpReq_Text("Bitte Begriff eingeben welcher ausgewählt werden soll.","Leere Eingabe lädt komplettes Journal.", text, "Buchungsauswahl")
            if ok and text:
                self.search = text
                self.Populate()
            elif not self.search_indices is None:
                self.search_indices = None
                self.Populate()
                #print ("AfpFiScreen.On_Ausw:", filter, text, BNr)
        elif filter == "Auszug":
            ok, out, dum = AfpFinance_selectStatement(self.globals.get_mysql(),  self.get_period(), None, None, None)
            if ok:
                ausz = out.split()[0]
                self.sb.select_key(ausz, "Auszug", "AUSZUG")
                self.set_current_record()
                self.Populate()
        elif filter == "Konten":
            list = self.data.get_account_lines("Cash,Bank,Other,Kosten,Ertrag")
            kt, ok = AfpReq_Selection("Bitte Konto auswählen:", "", list)
            if ok:
                ktnr = Afp_fromString(kt.split()[0])
                self.sb.select_key(ktnr, "KtNr", "KTNR")
                self.set_current_record()
                self.Populate()
        elif filter == "Eingang":
            ok = Afp_handleObligation(self.globals)
            if ok: self.Reload()
        event.Skip()

    ## Eventhandler BUTTON, MENU - document generation
    def On_Documents(self,event):
        if self.debug and event: print("AfpFiScreen Event handler `On_Documents'")
        filter = self.combo_Filter.GetValue()
        if filter == "Ausgang" or filter == "Eingang":
            data = self.get_selected_data()
            #print "AfpFiScreen.On_Documents data:", filter, data
            if data:
                variables = {}
                prefix = data.get_listname() + "_"
                if  filter == "Eingang":
                    header = "Rechnungseingang"
                else:
                    header = "Rechnungsausgang" 
                #print "AfpFiScreen.On_Documents:", filter, header, data.view()
                AfpLoad_DiReport(data, self.globals, variables, header, prefix)
        else:
           data = self.get_data()            
           if data:
                mandant = self.get_mandant()
                adresse = AfpAdresse(self.data.get_globals(), mandant)
                variables = {"Period":self.get_period()}
                variables["Name"] = adresse.get_name()
                variables["Strasse"] = adresse.get_value("Strasse")
                variables["Ort"] = adresse.get_value("Ort")
                variables["Tel"] = adresse.get_value("Telefon")
                if filter == "Konten" or filter == "Auszug":
                    variables["Wert"] = data.get_value()
                    variables["Bezeichnung"] = data.get_string_value("Bezeichnung.Konto")
                    variables["KontoNr"] = data.get_string_value("KtNr.Konto")
                    variables["Start"] = data.get_string_value("StartSaldo.Auszug")
                    variables["Ende"] = data.get_string_value("EndSaldo.Auszug")
                    if filter == "Auszug":
                        variables["TransferNr"] = data.get_transfer() 
                    if filter == "Konten":
                        variables["Saldo"] = variables["Start"]
                        variables["StartDat"] = data.get_string_value("BuchDat.Auszug")
                        variables["EndDat"] = data.get_string_value("Datum.Auszug")
                        #data.get_selection("BUCHUNG").reload_data("Beleg")
                #print "AfpFiScreen.On_Documents:", data.get_listname(), data.get_mayor_type(), filter, data.get_value(), data.get_string_value(), data.get_period()
                #data.view()
                #print ("AfpFiScreen.On_Documents variables:", variables)
                prefix = data.get_listname()+ "_" + filter + "_"
                header = "Auswertungen"
                sel = "Modul = \"Finance\" AND Art = \"Report\" and Typ = \""+ filter + "\""
                data.get_selection("AUSGABE").load_data(sel)
                AfpLoad_DiReport(data, self.globals, variables, header, prefix, None, adresse)
        if event:
            #self.Reload()
            event.Skip()

    ## Eventhandler BUTTON , MENU - modify event
    def On_modify(self,event=None):     
        if self.debug: print("AfpFiScreen Event handler `On_modify'")
        indices = self.grid_custs.GetSelectedRows()
        index = None
        if indices: index = indices[0]
        changed = False
        if "Bookings" in self.grid_id:
            if not index is None and len(self.grid_id["Bookings"]) > index:
                self.grid_row_selected = True
                Nr = Afp_fromString(self.grid_id["Bookings"][index])
                filter = self.combo_Filter.GetValue() 
                if filter == "Ausgang":
                    data = AfpCommonInvoice(self.data.get_globals(), Nr)
                    changed = AfpLoad_SimpleInvoice(data)
                elif filter == "Eingang": 
                    data = AfpObligation(self.data.get_globals(), Nr)
                    changed = AfpLoad_SimpleInvoice(data)
                else: # filter == "Journal", "Auszug", "Konten"
                    #print("AfpFiScreen.On_modify:",  self.search_indices, index)
                    if self.search_indices: index = self.search_indices[index]
                    #beleg, ref = self.data.get_value_rows("BUCHUNG", "Beleg,Reference", index)[0][0]
                    beleg, ref, vnr = self.data.get_value_rows("BUCHUNG", "Beleg,Reference,VorgangsNr", index)[0] 
                    print("AfpFiScreen.On_modify:", beleg, ref, vnr)
                    disable = "strict_accounting"
                    if self.flavour == "Cash":
                        disable += ",load,transaction"
                    if vnr:
                        changed = AfpLoad_FiBuchung(self.data.get_globals(), self.data.get_period(), {"VorgangsNr": vnr,  "disable": disable})
                    else:
                        changed = AfpLoad_FiBuchung(self.data.get_globals(), self.data.get_period(), {"Beleg": beleg, "disable": disable, "Reference": ref})
            else:
                changed = AfpLoad_FiBuchung_fromData(self.data.get_globals(), self.data)
        if changed: self.Reload()      
        if event: event.Skip()
      
    ## Eventhandler Grid - double click Grid 'Bookings'
    def On_DClick_Custs(self, event):
        if self.debug: print("AfpFiScreen Event handler `On_DClick_Custs'")
        self.On_modify()
        event.Skip()       
    ## Eventhandler MENU - modify cash in hand accounts \n
    def On_MKasse(self,event):   
        print("AfpFiScreen Event handler `On_MKasse' not implemented!")
        today = self.globals.today()
        auszug = "BAR" + Afp_toDateString(today,"mm")
        changed = AfpLoad_FiBuchung(self.data.get_globals(), self.data.get_period(), {"Auszug": auszug, "Datum": today})
        if changed: self.Reload()      
        event.Skip()  
   
    ## Eventhandler MENU - tourist seach via address 
    def On_MAddress_search(self, event):
        if self.debug: print("AfpFiScreen Event handler `On_MAddress_search'")
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
                #print "AfpFiScreen.On_MAddress_search:", ANr, ok
                if ok:
                    self.load_direct(0, ANr)
                    self.Reload()
        event.Skip()

    ## Eventhandler MENU - tourist menu - not yet implemented!
    def On_MEvent(self, event):
        print("AfpFiScreen Event handler `On_MEvent' not implemented!")
        event.Skip()

    ## Eventhandler Resize - for test reasons
    #def On_ReSize(self, event):
    def On_ReSize_test(self, event):
        print("Event handler `On_ReSize' for Test!")
        print("AfpFiScreen.On_ReSize Top size:", self.top_sizer.GetSize())
        print("AfpFiScreen.On_ReSize Event size:", self.master_panel_sizer.GetSize())
        print("AfpFiScreen.On_ReSize Grid size:", self.grid_panel_sizer.GetSize())
        print("AfpFiScreen.On_ReSize Grid size:", self.grid_custs.GetSize())
        print("AfpFiScreen.On_ReSize Button size:", self.button_sizer.GetSize())
        super(AfpFiScreen, self).On_ReSize(event)
        event.Skip()
        
    ## Eventhandler Keyboard - handle key-down events - overwritten from AfpScreen
    def On_KeyDown(self, event):
        keycode = event.GetKeyCode()        
        if self.debug: print("AfpFiScreen Event handler `On_KeyDown'", keycode)
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
        filter = self.combo_Filter.GetValue()
        #print ("AfpFiScreen.get_data:", filter, self.sb.get_value("KtNr"), self.get_period())
        if filter == "Journal": 
            return  AfpFinance(self.get_globals(), self.get_period(), None, self.get_mandant())
        elif filter == "Auszug":
            auszug =  self.sb.get_value("Auszug.AUSZUG")
            return  AfpFinance(self.get_globals(), self.get_period(), {"Auszug": auszug}, self.get_mandant())
        elif filter == "Konten":
            KtNr = self.sb.get_value("KtNr")
            return  AfpFinance(self.get_globals(), self.get_period(), {"Konto": KtNr, "Gegenkonto": KtNr}, self.get_mandant())
        elif filter == "Ausgang":
            #print  "AfpFiScreen.get_data:", filter, self.sort_filter
            return AfpBulkInvoices(self.get_globals(),self.sort_filter, "RechNr")
        elif filter == "Eingang":
            return AfpBulkObligations(self.get_globals(),self.sort_filter, "RechNr")
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
            print("AfpFiScreen.set_current_record:", end=' ')
            self.data.view()
        return

    ## set initial record to be shown, when screen opens the first time
    #overwritten from AfpScreen) 
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        self.sb.CurrentIndexName("KtNr","KTNR")
        self.sb.CurrentIndexName("Auszug","AUSZUG")   
        if self.combo_Filter.GetValue() == "Konten":
            master = "KTNR"
            filter = "NOT KtName = \"SALDO\" AND NOT Typ = \"Kreditor\" AND NOT Typ = \"Debitor\""
        else:
            master = "AUSZUG"
            filter = "Period = " + AfpFinance_setPeriod(None, self.globals)
        #print ("AfpFiScreen.set_initial_record:", filter)
        self.sb.CurrentFileName(master)  
        self.sb.select_where(filter, None, master) 
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
        if self.debug: print("AfpFiScreen.get_grid_rows typ:", typ)
        #if self.no_data_shown: return  rows
        if typ == "Bookings" and self.data:
            if self.data.get_listname() == "BulkInvoices":
                tmps = self.data.get_value_rows("RECHNG","Datum,RechNr,Pos,Kontierung,ZahlBetrag,Bem,KundenNr,RechNr")
            elif self.data.get_listname() == "BulkObligations":
                tmps = self.data.get_value_rows("VERBIND","Datum,RechNr,ExternNr,Kontierung,ZahlBetrag,Bem,KundenNr,RechNr")
            else:
                tmps = self.data.get_value_rows("BUCHUNG","Datum,Beleg,Konto,Gegenkonto,Betrag,Bem,KundenNr,BuchungsNr")
            #print "AfpFiScreen.get_grid_rows tmps:", tmps
            #print "AfpFiScreen.get_grid_rows data:", 
            #self.data.view()
            if self.search: self.search_indices = {} 
            if tmps:			
                for tmp in tmps:
                    if self.search: show = False
                    else: show = True
                    name = ""
                    if tmp[6]:
                        name = AfpAdresse(self.globals, tmp[6]).get_name(True)
                        if self.search and self.search in name: 
                            self.search_indices[len(rows)] = tmps.index(tmp)
                            show = True
                    for i in range(6):
                        tmp[i] = Afp_toString(tmp[i])
                        if self.search and self.search in tmp[i]: 
                            self.search_indices[len(rows)] = tmps.index(tmp)
                            show = True
                    if show: rows.append([tmp[0], tmp[1], tmp[2], tmp[3], tmp[4], tmp[5], name, tmp[7]])
        #self.search = None
        if self.debug: print("AfpFiScreen.get_grid_rows rows:", rows) 
        #print ("AfpFiScreen.get_grid_rows search:", self.search, self.search_indices) 
        #print ("AfpFiScreen.get_grid_rows rows:", self.data, len(rows)) 
        return rows
# end of class AfpFiScreen
