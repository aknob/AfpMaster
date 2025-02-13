#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFinance.AfpFiScreen_Chash
# AfpFiScreen_Cash module provides the graphic screen to access all data finance data of the petty cash (Barkasse)
# it holds the class
# - AfpFiScreen_Cash
#
#   History: \n
#        03 Jan 2025 - inital code generated - Andreas.Knoblauch@afptech.de


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
from AfpFinance import AfpFiRoutines, AfpFiDialog, AfpFiScreen
from AfpFinance.AfpFiRoutines import *
from AfpFinance.AfpFiDialog import *
from AfpFinance.AfpFiScreen import *

## Class AfpFiScreen shows 'Event' screen and handles interactions
class AfpFiScreen_Cash(AfpFiScreen):
    ## initialize AfpFiScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        self.flavour = "Cash"
        AfpFiScreen.__init__(self, debug)
        #self.einsatz = None # to invoke import of 'Einsatz' modules in 'init_database'
        self.SetTitle("Afp Barkasse")
        if self.debug: print("AfpFiScreen_Chash Konstruktor")
    
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
        self.combo_Filter = wx.ComboBox(panel, -1, value="Auszug", size=(164,20), choices=["Konten","Auszug"], style=wx.CB_DROPDOWN, name="Filter")
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
        return  
    ## create buttons to switch modules 
    def create_modul_buttons(self):
        self.button_modules = {}
        self.button_modules["Finance"] = wx.Button(self, -1, label="Finance", size=(75,30), name="BFinance")
        self.button_modules["Finance"].SetBackgroundColour(self.actuelbuttoncolor)
        self.modul_button_sizer.AddSpacer(10)
        self.modul_button_sizer.Add(self.button_modules["Finance"] ,0,wx.EXPAND)
        return
    ## set initial record to be shown, when screen opens the first time
    #overwritten from AfpScreen) 
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        self.sb.CurrentIndexName("KtNr","KTNR")
        self.sb.CurrentIndexName("Auszug","AUSZUG")   
        if self.combo_Filter.GetValue() == "Konten":
            master = "KTNR"
            filter = "NOT KtName = \"SALDO\" AND Typ = \"Kasse\""
        else:
            master = "AUSZUG"
            filter = "Period = " + AfpFinance_setPeriod(None, self.globals) + " AND Auszug LIKE \"BA%\""
        print ("AfpFiScreen_Cash.set_initial_record:", master, filter)
        self.sb.CurrentFileName(master)  
        self.sb.select_where(filter, None, master) 
        self.sb.select_key("BAR01")
        self.sb.select_current()
        self.set_current_record() 
        self.sb_master = master
        return
    ## Event handler filter combo box
    def On_Filter(self,event=None):
        s_key = self.sb.get_value("KtNr")        
        period = self.get_period()
        value = self.combo_Filter.GetValue()
        #print "AfpFiScreen.On_Filter:", period, value  
        if self.debug: print("AfpFiScreen.On_Filter:", period, value)   
        self.dynamic_grid_col_labels = self.grid_col_labels[0]
        self.sort_choices = self.sort_choices_list[0]
        self.indexmap = self.indexmap_list[0]
        self.button_Zahlung.Enable(False)
        for col in range(self.grid_cols["Bookings"]):
            self.grid_custs.SetColLabelValue(col, self.dynamic_grid_col_labels[col])
        self.combo_Sortierung.SetItems(self.sort_choices)
        self.combo_Sortierung.SetSelection(0)
        filter = "Period = " + period
        master = "AUSZUG"
        if value == "Konten":
            filter = "NOT KtName = \"SALDO\" AND Typ = \"Kasse\""
            master = "KTNR"
        elif value == "Auszug":
            filter += " AND Auszug LIKE \"BA%\""
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

   ## Eventhandler BUTTON - generate new statement of account 
    def On_Neu(self,event):
        if self.debug: print("AfpFiScreen_Cash Event handler `On_Neu'")
        filter = self.combo_Filter.GetValue()
        if filter == "Konten":
            ktnr = Afp_fromString(self.text_Auszug.GetValue())
            changed = AfpLoad_FiBuchung(self.data.get_globals(), self.data.get_period(), {"Konto": ktnr, "Gegenkonto": ktnr, "no_strict_accounting": None})
            #changed = AfpLoad_FiBuchung(self.data.get_globals(), self.data.get_period(), {"no_strict_accounting": None})
        else: # filter == "Auszug"
            period = self.data.get_period()
            konto = self.data.get_string_value("KtNr.KTNR")
            ktname =  self.data.get_string_value("KtName.KTNR")
            auszug, saldo = self.data.get_unused_auszug()
            print("AfpFiScreen.On_Neu:", period, konto, ktname, auszug, saldo, type(saldo))
            parlist = AfpFinance_modifyStatement(period, konto, ktname, auszug, Afp_toString(saldo), "")
            print("AfpFiScreen.On_Neu parlist:", parlist)
            if parlist:
                if "Period" in parlist: period = parlist["Period"]
                res = AfpLoad_FiBuchung(self.data.get_globals(), period, parlist)
                print("AfpFiScreen.On_Neu res:", res)
                if res:
                    self.sb.select_key(ausz, "Auszug", "AUSZUG")
                    self.set_current_record()
                    self.Populate()
        event.Skip()
    ## Eventhandler BUTTON - selection
    def On_Ausw(self,event):
        if self.debug: print("AfpFiScreen Event handler `On_Ausw'")
        self.grid_scrollback()
        filter = self.combo_Filter.GetValue()
        if filter == "Auszug":
            ok, out, dum = AfpFinance_selectStatement(self.globals.get_mysql(),  self.get_period(), None, "Ba", None)
            if ok:
                ausz = out.split()[0]
                self.sb.select_key(ausz, "Auszug", "AUSZUG")
                self.set_current_record()
                self.Populate()
        elif filter == "Konten":
            #list = self.data.get_account_lines("Cash,Bank,Other,Kosten,Ertrag")
            list = self.data.get_account_lines("Cash")
            kt, ok = AfpReq_Selection("Bitte Konto auswählen:", "", list)
            if ok:
                ktnr = Afp_fromString(kt.split()[0])
                self.sb.select_key(ktnr, "KtNr", "KTNR")
                self.set_current_record()
                self.Populate()
        event.Skip()

# end of class AfpFiScreen_Cash
