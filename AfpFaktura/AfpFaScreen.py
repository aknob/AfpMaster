#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFaktura.AfpFaScreen
# AfpFaScreen module provides the graphic screen to access all data of the Afp-'Faktura' modul 
# it holds the class
# - AfpFaScreen
#
#   History: \n
#        22 Nov. 2016 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2017  afptech.de (Andreas Knoblauch)
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
from AfpBase.AfpUtilities.AfpStringUtilities import AfpSelectEnrich_dbname, Afp_ArraytoString, Afp_fromString, Afp_toString
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile
from AfpBase.AfpDatabase import *
from AfpBase.AfpDatabase.AfpSQL import AfpSQL
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import AfpMailSender
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Question
from AfpBase.AfpBaseDialogCommon import  AfpReq_Information, Afp_editMail
from AfpBase.AfpBaseScreen import AfpScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse_StatusMap, AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_DiAdEin_fromSb, AfpLoad_AdAusw

import AfpFaktura
from AfpFaktura import AfpFaRoutines
from AfpFaktura import AfpFaDialog
from AfpFaktura.AfpFaRoutines import AfpFaktura_FilterLists, AfpInvoice, AfpOffer, AfpOrder, AfpFa_inFilterList
from AfpFaktura.AfpFaDialog import AfpLoad_FaAusw

## Class Faktura shows Window for Invoices and handles interactions
class AfpFaScreen(AfpScreen):
    ## initialize AfpAdScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None, use_labels = True):
        AfpScreen.__init__(self,None, -1, "")
        self.typ = "Faktura"
        self.sb_master = "RECHNG"
        self.sb_filter = ""
        self.use_labels = use_labels
        self.content_rows = 10
        self.content_colname = ["Pos","ErsatzteilNr","Bezeichnung","Anzahl","Einzel","Gesamt"]
        self.index = None
        self.index_nr = None
        # self properties
        self.SetTitle("Afp-Fakturierung und Warenwirtschaft")
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.SetForegroundColour(wx.Colour(20, 19, 18))
        self.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "DejaVu Sans"))

        panel = self.panel
      
        # BUTTON
        self.button_Auswahl = wx.Button(panel, -1, label="Aus&wahl", pos=(692,50), size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Faktura_Ausw, self.button_Auswahl)
        self.button_Bearbeiten = wx.Button(panel, -1, label="&Bearbeiten", pos=(692,110), size=(77,50), name="Bearbeiten")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_AendF, self.button_Bearbeiten)
        self.button_Voll = wx.Button(panel, -1, label="&Volltext", pos=(692,170), size=(77,50), name="BVoll")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Volltext, self.button_Voll)
        self.button_Voll.Enable(False)
       
        self.button_Dokument = wx.Button(panel, -1, label="&Dokument", pos=(692,256), size=(77,50), name="BDokument")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_Doku, self.button_Dokument)
        self.button_Dokument.Enable(False)
        self.button_Edit = wx.Button(panel, -1, label="Bearbeiten", pos=(692,338), size=(77,50), name="Edit")
        self.Bind(wx.EVT_BUTTON, self.On_Edit, self.button_Edit)
        self.button_Listen = wx.Button(panel, -1, label="&Listen", pos=(692,405), size=(77,50), name="Listen")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_Listen, self.button_Listen)
        self.button_Listen.Enable(False)        
        self.button_Ende = wx.Button(panel, -1, label="Be&enden", pos=(692,470), size=(77,50), name="Ende")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Ende)

        # COMBOBOX
        self.combo_Filter = wx.ComboBox(panel, -1, value="Rechnung", pos=(526,16), size=(150,20), choices=AfpFaktura_FilterLists("names"), style=wx.CB_READONLY, name="Filter_Zustand")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        self.combo_Filter.SetSelection(AfpFa_inFilterList("Rechnung"))
        #self.filtermap = {"Alle":"","Kostenvoranschläge".decode("UTF-8"):"KVA","Angebote":"Angebot","Aufträge".decode("UTF-8"):"Auftrag","Rechnungen":"Rechnung","Mahnungen":"Mahnung","Stornierungen":"Storno %"}
        self.combo_Sortierung = wx.ComboBox(panel, -1, value="RechNr", pos=(689,16), size=(80,20), choices=["RechNr","Datum","Name"], style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Sortierung, self.combo_Sortierung)
        self.indexmap = {"RechNr":"RechNr","Datum":"Datum","Name":"KundenNr"}
        
        # LABEL
        self.label_Archiv = wx.StaticText(panel, -1, label="Archiv:", pos=(500,80), size=(46,18), name="LArchiv")
        self.label_Datum = wx.StaticText(panel, -1, label="Datum:", pos=(400,52), size=(45,18), name="LDatum")
        self.label_RechNr = wx.StaticText(panel, -1, label="Nummer:", pos=(540,52), size=(55,18), name="LRechNr")
        self.label_Tel = wx.StaticText(panel, -1, label="Telefon:", pos=(36,150), size=(48,23), name="LTel")
        self.label_Mail = wx.StaticText(panel, -1, label="E-Mail:", pos=(36,175), size=(42,23), name="LMail")
        self.label_Gew = wx.StaticText(panel, -1, label="", pos=(603,80), size=(75,20), name="LGewinn")
        #self.labelmap["LGewinn"] = "Gewinn.Main"
        self.label_Netto = wx.StaticText(panel, -1, label="Netto:", pos=(290,475), size=(45,18), name="LNetto")
        self.label_Mwst = wx.StaticText(panel, -1, label="Mwst:", pos=(425,475), size=(45,18), name="LMwst")
        self.label_Summe = wx.StaticText(panel, -1, label="Summe:", pos=(550,475), size=(47,18), name="LSumme")
        self.label_ZahlDat = wx.StaticText(panel, -1, label="Datum:", pos=(290,495), size=(50,18), name="LZahlDat")
        self.label_Zahlung = wx.StaticText(panel, -1, label="Zahlung:", pos=(418,495), size=(50,18), name="LZahlung")
        self.label_Betrag = wx.StaticText(panel, -1, label="Betrag:", pos=(550,495), size=(45,18), name="LBetrag")
        
        # address as LABEL
        if self.use_labels:
            self.label_Vorname = wx.StaticText(panel, -1, "", pos=(35,50), size=(195,23), name="Vorname")
            self.labelmap["Vorname"] = "Vorname.ADRESSE"
            self.label_Name = wx.StaticText(panel, -1,label="", pos=(35,75), size=(195,23), name="Name")
            self.labelmap["Name"] = "Name.ADRESSE"
            
            self.label_Strasse = wx.StaticText(panel, -1,label="", pos=(35,100), size=(195,23), name="Strasse")
            self.labelmap["Strasse"] = "Strasse.ADRESSE"
            
            self.label_Plz = wx.StaticText(panel, -1,label="", pos=(35,125), size=(40,23), name="Plz")
            self.labelmap["Plz"] = "Plz.ADRESSE"
            self.label_Ort = wx.StaticText(panel, -1,label="", pos=(75,125), size=(155,23), name="Ort")
            self.labelmap["Ort"] = "Ort.ADRESSE"
            
            self.label_Telefon = wx.StaticText(panel, -1,label="", pos=(90,150), size=(140,23), name="Telefon")
            self.labelmap["Telefon"] = "Telefon.ADRESSE"
            self.label_Mail = wx.StaticText(panel, -1,label="", pos=(90,175), size=(140,23), style=0, name="Mail")
            self.labelmap["Mail"] = "Mail.ADRESSE"
            
            self.label_Art = wx.StaticText(panel, -1, label="", pos=(230,100), size=(80,18), name="Art")               
            self.labelmap["Art"] = "Art.Dependance1"
            self.label_Hersteller = wx.StaticText(panel, -1, label="", pos=(320,100), size=(70,18), name="Hersteller")               
            self.labelmap["Hersteller"] = "Hersteller.Dependance1"
            self.label_Typ = wx.StaticText(panel, -1, label="", pos=(400,100), size=(90,18), name="Typ")               
            self.labelmap["Typ"] = "Typ.Dependance1"
            self.label_Motor = wx.StaticText(panel, -1, label="", pos=(230,125), size=(80,18), name="Motor")               
            self.labelmap["Motor"] = "Motormodell.Dependance1"
            self.label_MotorNr = wx.StaticText(panel, -1, label="", pos=(320,125), size=(176,18), name="MotorNr")               
            self.labelmap["MotorNr"] = "MotorNr.Dependance1"
            self.label_TypNr= wx.StaticText(panel, -1, label="", pos=(320,150), size=(176,18), name="TypNr")               
            self.labelmap["TypNr"] = "TypNr.Dependance1"
            self.label_Kenn = wx.StaticText(panel, -1, label="", pos=(230,175), size=(80,18), name="Kenn")               
            self.labelmap["Kenn"] = "Kennzeichen.Dependance1"
            self.label_HU = wx.StaticText(panel, -1, label="", pos=(320,175), size=(70,18), name="HU")               
            self.labelmap["HU"] = "HU.Dependance1"
            self.label_Zul = wx.StaticText(panel, -1, label="", pos=(400,175), size=(90,18), name="Zul")               
            self.labelmap["Zul"] = "ZulVerkauf.Dependance1"
        else:
            # address as TEXTBOX
            self.text_Vorname = wx.TextCtrl(panel, -1, "", pos=(35,50), size=(195,23), style=wx.TE_READONLY, name="Vorname")
            self.textmap["Vorname"] = "Vorname.ADRESSE"
            self.text_Name = wx.TextCtrl(panel, -1,value="", pos=(35,75), size=(217,23), style=wx.TE_READONLY, name="Name")
            self.textmap["Name"] = "Name.ADRESSE"
            
            self.text_Strasse = wx.TextCtrl(panel, -1,value="", pos=(35,100), size=(271,23), style=wx.TE_READONLY, name="Strasse")
            self.textmap["Strasse"] = "Strasse.ADRESSE"
            
            self.text_Plz = wx.TextCtrl(panel, -1,value="", pos=(35,125), size=(53,23), style=wx.TE_READONLY, name="Plz")
            self.textmap["Plz"] = "Plz.ADRESSE"
            self.text_Ort = wx.TextCtrl(panel, -1,value="", pos=(91,125), size=(215,23), style=wx.TE_READONLY, name="Ort")
            self.textmap["Ort"] = "Ort.ADRESSE"
            
            self.text_Telefon = wx.TextCtrl(panel, -1,value="", pos=(89,150), size=(215,23), style=wx.TE_READONLY, name="Telefon")
            self.textmap["Telefon"] = "Telefon.ADRESSE"
            self.text_Mail = wx.TextCtrl(panel, -1,value="", pos=(89,175), size=(215,23), style=0, name="Mail")
            self.textmap["Mail"] = "Mail.ADRESSE"
            
            self.text_Art = wx.TextCtrl(panel, -1,value="", pos=(320,100), size=(80,18), style=wx.TE_READONLY, name="Art")               
            self.textmap["Art"] = "Art.Dependance1"
            self.text_Hersteller = wx.TextCtrl(panel, -1,value="", pos=(410,100), size=(80,18), style=wx.TE_READONLY, name="Hersteller")               
            self.textmap["Hersteller"] = "Hersteller.Dependance1"
            self.text_MotorNr = wx.TextCtrl(panel, -1,value="", pos=(500,100), size=(176,18), style=wx.TE_READONLY, name="MotorNr")               
            self.textmap["MotorNr"] = "MotorNr.Dependance1"
            self.text_Motor = wx.TextCtrl(panel, -1,value="", pos=(320,125), size=(80,18), style=wx.TE_READONLY, name="Motor")               
            self.textmap["Motor"] = "Motormodell.Dependance1"
            self.text_Typ = wx.TextCtrl(panel, -1,value="", pos=(410,125), size=(80,18), style=wx.TE_READONLY, name="Typ")               
            self.textmap["Typ"] = "Typ.Dependance1"
            self.text_TypNr= wx.TextCtrl(panel, -1,value="", pos=(500,125), size=(176,18), style=wx.TE_READONLY, name="TypNr")               
            self.textmap["TypNr"] = "TypNr.Dependance1"
            self.text_Zul = wx.TextCtrl(panel, -1,value="", pos=(320,150), size=(80,18), style=wx.TE_READONLY, name="Zul")               
            self.textmap["Zul"] = "ZulVerkauf.Dependance1"
            self.text_HU = wx.TextCtrl(panel, -1,value="", pos=(410,150), size=(80,18), style=wx.TE_READONLY, name="HU")               
            self.textmap["HU"] = "HU.Dependance1"
            self.text_Kenn = wx.TextCtrl(panel, -1,value="", pos=(500,150), size=(176,18), style=wx.TE_READONLY, name="Kenn")               
            self.textmap["Kenn"] = "Kennzeichen.Dependance1"

        # TEXTBOX
        self.text_Datum = wx.TextCtrl(panel, -1,value="", pos=(449,50), size=(77,23), style=wx.TE_READONLY, name="Datum")
        self.textmap["Datum"] = "Datum.Main"
        self.text_RechNr = wx.TextCtrl(panel, -1,value="", pos=(599,50), size=(77,23), style=wx.TE_READONLY, name="RechNr")
        self.textmap["RechNr"] = "RechNr.Main"
        
        self.text_Netto = wx.TextCtrl(panel, -1,value="", pos=(335,475), size=(77,18), style=wx.TE_READONLY, name="Netto")
        self.textmap["Netto"] = "Netto.Main"  
        self.text_Mwst = wx.TextCtrl(panel, -1,value="", pos=(470,475), size=(77,18), style=wx.TE_READONLY, name="Mwst")
        self.textmap["Mwst"] = "Mwst.Main"  
        self.text_Summe = wx.TextCtrl(panel, -1,value="", pos=(599,475), size=(77,18), style=wx.TE_READONLY, name="Summe")
        self.textmap["Summe"] = "Betrag.Main"  
        self.text_ZahlDat = wx.TextCtrl(panel, -1,value="", pos=(335,495), size=(77,18), style=wx.TE_READONLY, name="ZahlDat")
        self.textmap["ZahlDat"] = "ZahlDat.Main"  
        self.text_Zahlung = wx.TextCtrl(panel, -1,value="", pos=(470,495), size=(77,18), style=wx.TE_READONLY, name="Zahlung")
        self.textmap["Zahlung"] = "Zahlung.Main"  
        self.text_Betrag = wx.TextCtrl(panel, -1,value="", pos=(599,495), size=(77,18), style=wx.TE_READONLY, name="Betrag")
        self.textmap["Betrag"] = "ZahlBetrag.Main"  

        #ListBox - Archiv
        self.list_archiv = wx.ListBox(panel, -1, pos=(500,100) , size=(176, 100), name="Archiv")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Archiv, self.list_archiv)
        self.listmap.append("Archiv")

        # OPTIONBUTTON
        self.choice_Status = wx.Choice(panel, -1, pos=(230,52), size=(76,18), choices=["Passiv", "Aktiv", "Neutral", "Markiert", "Inaktiv"],  name="RStatus")
        self.choice_Status.SetSelection(0)
        #self.choice_Status.Enable(False)
        self.Bind(wx.EVT_CHOICE, self.On_CStatus, self.choice_Status)
        self.choicemap = AfpAdresse_StatusMap()
        
        # GRID
        self.grid_content = wx.grid.Grid(panel, -1, pos=(23,206) , size=(653, 264), name="Content")
        self.grid_content.CreateGrid(self.content_rows, 6)
        self.grid_content.SetRowLabelSize(3)
        self.grid_content.SetColLabelSize(18)
        self.grid_content.EnableEditing(0)
        self.grid_content.EnableDragColSize(0)
        self.grid_content.EnableDragRowSize(0)
        self.grid_content.EnableDragGridSize(0)
        self.grid_content.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)
        self.grid_content.SetColLabelValue(0, self.content_colname[0])
        self.grid_content.SetColSize(0, 30)
        self.grid_content.SetColLabelValue(1, self.content_colname[1])
        self.grid_content.SetColSize(1, 130)
        self.grid_content.SetColLabelValue(2, self.content_colname[2])
        self.grid_content.SetColSize(2, 300)
        self.grid_content.SetColLabelValue(3, self.content_colname[3])
        self.grid_content.SetColSize(3, 50)
        self.grid_content.SetColLabelValue(4, self.content_colname[4])
        self.grid_content.SetColSize(4, 65)
        self.grid_content.SetColLabelValue(5, self.content_colname[5])
        self.grid_content.SetColSize(5, 75)
        for row in range(0,self.content_rows):
            for col in range(0,5):
                self.grid_content.SetReadOnly(row, col)
        self.gridmap.append("Content")
        self.grid_minrows["Content"] = self.grid_content.GetNumberRows()

    ## compose address specific menu parts
    def create_specific_menu(self):
        # setup address menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Anfrage", "")
        self.Bind(wx.EVT_MENU, self.On_MAnfrage, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Suchen", "")
        self.Bind(wx.EVT_MENU, self.On_Faktura_Ausw, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Bearbeiten", "")
        self.Bind(wx.EVT_MENU, self.On_Adresse_AendF, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&E-Mail versenden", "")
        self.Bind(wx.EVT_MENU, self.On_MEMail, mmenu)
        tmp_menu.AppendItem(mmenu)
        self.menubar.Append(tmp_menu, "Adresse")
        # setup address menu
        #tmp_menu = wx.Menu() 
        #mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Suche", "")
        #self.Bind(wx.EVT_MENU, self.On_MAddress_search, mmenu)
        #tmp_menu.AppendItem(mmenu)
        #mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Be&arbeiten", "")
        #self.Bind(wx.EVT_MENU, self.On_Adresse_aendern, mmenu)
        #tmp_menu.AppendItem(mmenu)
        #self.menubar.Append(tmp_menu, "Adresse")
        return

    ## Eventhandler MENU; BUTTON - select other invoice, either direkt or via attribut
    def On_Faktura_Ausw(self,event):
        if self.debug: print "Event handler `On_Faktura_Ausw'!"
        #self.sb.set_debug()
        index = self.index
        where = AfpSelectEnrich_dbname(self.sb.identify_index().get_where(), self.sb_master)
        value = self.sb.identify_index().get_indexwert()
        if index == "KundenNr":
            value = self.data.get_value("Name.ADRESSE")
        #print "On_Faktura_Ausw Ind:",index, "VAL:",values,"Where:", where
        #print "On_Faktura_Ausw Merkmal:", self.combo_Filter.GetValue()
        #self.sb.set_debug()
        auswahl = AfpLoad_FaAusw(self.globals, index, Afp_toString(value), where, True)
        #self.sb.unset_debug()
        if not auswahl is None:
            RNr = int(auswahl)
            if self.sb_filter: self.sb.select_where(self.sb_filter, "RechNr", self.sb_master)
            self.sb.select_key(RNr, "RechNr", self.sb_master)
            if self.sb_filter: self.sb.select_where("", "RechNr", self.sb_master)
            self.sb.set_index(index, self.sb_master, "RechNr")   
            self.set_current_record()
            if index == "KundenNr":
                self.sb.select_key(self.data.get_value("KundenNr"),"KundenNr","ADRESSE")
                self.sb.set_index("Name","ADRESSE","KundenNr")
            self.Populate()
        #self.sb.unset_debug()
        event.Skip()
    ## Eventhandler BUTTON - resolve duplicate addresses - not implemented yet!
    def On_Edit(self,event):
        if  self.is_editable() :
            self.Set_Editable(False)
            print "AfpFaScreen.On_Edit ReadOnly:", self.is_editable()
        else:
            self.Set_Editable(True)
            print "AfpFaScreen.On_Edit Edit:", self.is_editable()
        self.panel.Refresh()
        event.Skip()
    ## Eventhandler BUTTON - show different lists, not implemented yet!
    def On_Adresse_Listen(self,event):
        print "Event handler `On_Adresse_Listen' not implemented!"
        event.Skip()
    ## Eventhandler MENU, BUTTON - change address
    def On_Adresse_AendF(self,event):
        if self.debug: print "AfpAdScreen Event handler `On_Adresse_AendF'"
        AfpLoad_DiAdEin_fromSb(self.globals, self.sb)
        event.Skip()
    ## Eventhandler BUTTON - invoke full text search over addresses an all attached data - not yet implemented
    def On_Ad_Volltext(self,event):
        print "Event handler `On_Ad_Volltext' not implemented!"
        event.Skip()
    ## Eventhandler BUTTON - invoke dokument generation - not yet implemented
    def On_Adresse_Doku(self,event):
        print "Event handler `On_Adresse_Doku' not implemented!"
        event.Skip()
        
    ## Eventhandler COMBOBOX - allow filter due to attributes, change master table
    def On_Filter(self,event): 
        value = self.combo_Filter.GetValue()
        if self.debug: print "AfpFaScreen Event handler `On_Filter'", value
        datei, filter = AfpFaktura_FilterLists(value)
        reset = False
        if not datei: 
            datei = self.sb_master
            reset = True
        #print "AfpFaScreen.On_Filter filter:", datei, filter
        where = ""
        if filter:
            where = "Zustand = \"" +  filter + "\""
        if datei != self.sb_master:
            #self.sb.set_debug()
            self.sb.select_where("")
            self.find_adjacent_entry(datei)
            self.sb.select_where(where)
            #print "AfpFaScreen.On_Filter where:", where
            self.sb_master = datei
            self.sb_filter = where
            self.index = ""
            self.On_Sortierung()
            #self.sb.unset_debug()
        else:
            if self.sb_filter != where: 
                self.sb.select_where(where)
                self.sb_filter = where
            self.CurrentData()
        if reset:
            if self.sb_master == "RECHNG": index = AfpFa_inFilterList("Rechnung")
            elif self.sb_master == "KVA": index = AfpFa_inFilterList("KVA")
            elif self.sb_master == "BESTELL": index = AfpFa_inFilterList("Bestellung")
            self.combo_Filter.SetSelection(index)
        event.Skip()
    ## Eventhandler COMBOBOX - sort index
    def On_Sortierung(self,event = None):
        value = self.combo_Sortierung.GetValue()
        index = self.indexmap[value]
        if self.debug: print "Event handler `On_Sortierung'",self.index, index
        if index != self.index:
            #print "AfpFaScreen.On_Sortierung index:",  index
            self.index = index
            self.sb.set_index(index)
            self.sb.CurrentIndexName(index)
            if index == "KundenNr":
                self.index_nr =  self.sb.get_value("KundenNr")
                self.sb.select_key(self.index_nr, "KundenNr", "ADRESSE")
                self.sb.set_index("Name","ADRESSE","KundenNr")
        self.CurrentData()
        if event: event.Skip()

    ## Eventhandler RADIOBOX - only implemented to reset selection due to databas entry
    def On_CStatus(self, event):
        self.Pop_choice_status()
        print "Event handler `On_CStatus' only implemented to reset selection!"
        event.Skip()
        
    ## Eventhandler MENU - add an enquirery - not yet implemented! \n
    def On_MAnfrage(self, event):
        print "Event handler `On_MAnfrage' not implemented!"
        event.Skip()
    ## Eventhandler MENU - send an e-mail - not yet implemented! 
    def On_MEMail(self, event):
        if self.debug: print "Event handler `On_MEMail'"
        mail = AfpMailSender(self.globals, self.debug)
        an = self.sb.get_value("Mail.ADRESSE")
        if an: mail.add_recipient(an)
        mail, send = Afp_editMail(mail)
        if send: mail.send_mail()
        event.Skip()

    ## Eventhandler ListBox - double click ListBox 'Archiv'
    def On_DClick_Archiv(self, event):
        if self.debug: print "Event handler `On_DClick_Archiv'", event
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
                        print "WARNING in AfpFaScreen: External file", filename, "does not exist, look in 'antiquedir'." 
                        filename = Afp_addRootpath(self.globals.get_value("antiquedir"), file)
                    if Afp_existsFile(filename):
                        Afp_startFile(filename, self.globals, self.debug, True)
                    else:
                        print "WARNING in AfpFaScreen: External file", filename, "does not exist!" 
        event.Skip()
      
    ## set right status-choice for this address
    def Pop_choice_status(self):
        stat = self.data.get_value("Kennung.ADRESSE")
        if not stat: stat = 0
        choice = self.choicemap[stat]
        self.choice_Status.SetSelection(choice)
        if self.debug: print "AfpFaScreen Population routine`Pop_choice_status'", choice
    ## population routine for special treatment - overwritten from AfpScreen
    def Pop_special(self):
        summe = self.data.get_value("Betrag")
        netto = self.data.get_value("Netto")
        gewinn = self.data.get_value("Gewinn")
        if self.is_editable():
            if netto:
                pro = Afp_toString(int(100*gewinn/netto))
            else:
                pro = "0"
            label = Afp_toString(gewinn)
            label = pro + "00" + label[:-3].strip() + label[-2:]
            self.label_Gew.SetLabel(label)
        else:
            self.label_Gew.SetLabel("")
        if self.text_Betrag.GetValue() == "":
            self.text_Betrag.SetValue(Afp_toString(summe)) 
        if self.text_Mwst.GetValue() == "":
            if summe is None or netto is None:
                Mwst = ""
            else:
                Mwst = summe - netto
            self.text_Mwst.SetValue(Afp_toString(Mwst)) 
        return
    ## set or unset editable mode - overwritten from AfpScreen
    # @param ed_flag - flag to turn editing on or off
    # @param lock_data - flag if invoking of editable mode needs a lock on the database
    def Set_Editable(self, ed_flag, lock_data = None):
        AfpScreen.Set_Editable(self, ed_flag, lock_data)
        self.Pop_special()
    # find an adjacent entry in other database table and set the sb.object pointer to this entry
    # @param table - databasetable where to look
    def find_adjacent_entry(self, table):
        Typ = self.sb.get_value("Typ")
        TNr = self.sb.get_value("TypNr")
        # first look for adjacent entry
        if Typ and Typ == table:
            self.sb.CurrentIndexName("RechNr", table)
            self.sb.select_key(TNr)
        else:
            # second look the other way round
            RNr = self.sb.get_value("RechNr")
            KNr = self.sb.get_value("KundenNr")
            self.sb.CurrentIndexName("TypNr", table)
            self.sb.select_key(RNr)
            #print "AfpFaScreen.find_adjacent_entry TypNr:", RNr, self.sb.get_value("TypNr") , self.sb.get_value("Typ") 
            while self.sb.neof() and self.sb.get_value("TypNr") == RNr and self.sb.get_value("Typ") != self.sb_master:
                self.sb.select_next()
                #print "AfpFaScreen.find_adjacent_entry next:", self.sb.get_value("RechNr")
            # third look for other entries of same client
            if self.sb.get_value("TypNr") != RNr or self.sb.get_value("Typ") != self.sb_master:
                self.sb.CurrentIndexName("KundenNr")
                self.sb.select_key(KNr)
    # routines to be overwritten in explicit class
    ## generate AfpSelectionList object from the present screen, overwritten from AfpScreen
    # @param complete - flag if all TableSelections should be generated
    def get_data(self, complete = False):
        if self.sb_master == "KVA":
            return  AfpOffer(self.globals, None, self.sb, self.sb.debug, complete)
        elif self.sb_master == "BESTELL":
            return  AfpOrder(self.globals, None, self.sb, self.sb.debug, complete)
        else: #self.sb_master == "RECHNG":
            return  AfpInvoice(self.globals, None, self.sb, self.sb.debug, complete)
    ## set current record to be displayed 
    # (overwritten from AfpScreen) 
    def set_current_record(self):
        self.data = self.get_data() 
        #print "AfpFaScreen.set_current_record View:" 
        #self.data.view()
        self.Pop_choice_status()
        return  
    ## set initial record to be shown, when screen opens the first time
    #overwritten from AfpScreen) 
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        ReNr = 0
        if origin == "Charter":
            ReNr = self.sb.get_value("RechNr.FAHRTEN")
            # FNr = self.globals.get_value("FahrtNr", origin)
        if ReNr == 0:
            self.sb.CurrentIndexName("RechNr","RECHNG")
            #self.sb.set_debug()
            self.sb.select_key(11658) # for tests
            #self.sb.select_key(21167) # for tests
            #self.sb.select_last() # for tests
        else:
            self.sb.CurrentIndexName("RechNr","RECHNG")
            self.sb.select_key(ReNr)
        self.index = "RechNr"
        return
    ## get identifier of graphical objects, 
    # where the keydown event should not be catched
    # (overwritten from AfpScreen)
    def get_no_keydown(self):
        return ["Bem","BemExt","MerkT_Archiv","Content"]
    ## get names of database tables to be opened for this screen
    # (overwritten from AfpScreen)
    def get_dateinamen(self):
        return  ["RECHNG","KVA","BESTELL","ADRESSE"]
    ## get rows to populate lists \n
    # possible selection criterias have to be separated by a "None" value
    # @param typ - name of list to be populated 
    def get_list_rows(self, typ):
        rows = []
        if self.debug: print "AfpFaScreen.get_list_rows:", typ
        if typ == "Archiv" and self.data:
            #rawrow = self.data.get_string_rows("ARCHIV", "Datum,Gruppe,Bem,Extern")
            #for row in rawrow:
                #rows.append(row[0] + " " + row[1] + " " + row[2])
            #rows.append(None)
            #for row in rawrow:
                #rows.append(row[3])
            if not rows: # for test reasons
                rows.append("17.9.1958 Rechnung Test")
                rows.append("21.12.2016 Rechnung Test2")
        return rows
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param name - name of grid to be populated
    def get_grid_rows(self, name):
        rows = []
        if self.debug: print "AfpFaScreen.get_grid_rows Population routine", name
        if name == "Content" and self.data:
            id_col = 5      
            self.content_colname = self.data.get_grid_colnames()
            rows = self.data.get_grid_rows()
            for col in range(0,5):
                self.grid_content.SetColLabelValue(col, self.content_colname[col])
        #print "AfpFaScreen.get_grid_rows:", rows
        return rows
    ## set current screen data - overwritten from AfpScreen for indirect Inedx handling
    # @param plus - indicator to step forwards, backwards or stay
    def CurrentData(self, plus = 0):
        if self.debug: print "AfpFaScreen.CurrentData", plus
        #self.sb.set_debug()
        done = None
        while not done:
            if plus == 1:
                self.sb.select_next()
            elif plus == -1:
                self.sb.select_previous()
            if self.index == "KundenNr":
                if done is None:
                    if self.index_nr != self.sb.get_value("KundenNr"):
                        self.sb.CurrentIndexName("Name","ADRESSE")
                        done = False
                    else:
                        done = True
                else: 
                    self.index_nr = self.sb.get_value("KundenNr")
                    self.sb.select_key(self.index_nr, "KundenNr", self.sb_master)
                    if self.sb.eof() or self.index_nr == self.sb.get_value("KundenNr." + self.sb_master):
                        self.sb.CurrentIndexName("KundenNr",self.sb_master)
                        done = True
            else:
                done = True
        self.set_current_record()
        #self.sb.unset_debug()
        self.Populate()
