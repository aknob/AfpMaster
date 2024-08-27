#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpAdresse.AfpAdScreen
# AfpAdScreen module provides the graphic screen to access all data of the Afp-'Adressen' modul 
# it holds the class
# - AfpAdScreen
#
#   History: \n
#        11 Mai  2024 - add right double click to manipulate archiv entries
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de


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

from AfpBase.AfpUtilities.AfpStringUtilities import Afp_MatrixSplitCol, AfpSelectEnrich_dbname, Afp_ArraytoString, Afp_toString, Afp_fromString, Afp_addRootpath
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile, Afp_isInteger
from AfpBase.AfpDatabase.AfpSQL import AfpSQL
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import AfpMailSender, Afp_ModulNames, Afp_startFile, Afp_importPyModul
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Question, AfpReq_MultiLine
from AfpBase.AfpBaseDialogCommon import  AfpReq_Information, Afp_editMail, AfpLoad_DiReport
from AfpBase.AfpBaseScreen import AfpScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse_StatusStrings, AfpAdresse_StatusMap, AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_DiAdEin, AfpLoad_DiAdEin_fromSb, AfpLoad_AdAusw
from AfpBase.AfpBaseFiDialog import AfpLoad_SimpleInvoice_fromReNr, AfpLoad_Obligation_fromVbNr

## Class_Adresse shows Window Adresse and handles interactions
class AfpAdScreen(AfpScreen):
    ## initialize AfpAdScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        AfpScreen.__init__(self,None, -1, "")
        self.typ = "Adresse"
        self.sb_master = "ADRESSE"
        self.sb_filter = ""
        self.data_objects = {}
        self.grid_cols["Archiv"] = 5
        self.grid_rows["Archiv"] = 10
        self.archiv_colnames = [["Datum","Art","Ablage","Fach","Bem."],["AnmeldNr","Datum","Veranstaltung","Preis","Zahlung"],["Zustand","Datum","Zielort","Art","Preis"],["RechNr","Datum","Text","Preis","Zahlung"],["RechNr","Datum","Text","Preis","Zahlung"],["Merkmal","Text","-","-","-"],["Datum","Buchung","Betrag","Text","Periode"],["Name","Vorname","Strasse","Ort","Telefon"]]
        self.archiv_colname = self.archiv_colnames[0]
        self.dynamic_grid_name = "Archiv"
        self.dynamic_grid_col_percents = [20, 20, 20, 20, 20]
        # self properties
        self.SetTitle("Afp Adresse")
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.SetForegroundColour(wx.Colour(20, 19, 18))
        self.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "DejaVu Sans"))
        self.InitWx()
        self.Bind(wx.EVT_SIZE, self.On_ReSize)
        if self.debug: print("AfpAdScreen Konstruktor")
  
    ## initialize widgets
    def InitWx(self):
        # set up sizer strukture
        self.sizer =wx.BoxSizer(wx.HORIZONTAL)
        
        self.left_sizer =wx.BoxSizer(wx.VERTICAL)
        self.button_sizer =wx.BoxSizer(wx.VERTICAL)
        self.button_low_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.button_mid_sizer =wx.BoxSizer(wx.VERTICAL)
        self.top_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.top_mid_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.modul_button_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.grid_mid_sizer =wx.BoxSizer(wx.VERTICAL)
        self.grid_panel_sizer =wx.BoxSizer(wx.HORIZONTAL)
        
        # right BUTTON sizer
        #self.text_MerkT_Archiv = wx.TextCtrl(self, -1,value="", size=(80,18), style=0, name="MerkT_Archiv")
        self.text_MerkT_Archiv = wx.TextCtrl(self, -1,value="", style=0, name="MerkT_Archiv")
        
        self.button_Auswahl = wx.Button(self, -1, label="Aus&wahl",size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_AuswErw, self.button_Auswahl)
        self.button_Bearbeiten = wx.Button(self, -1, label="&Bearbeiten",size=(77,50), name="BBearbeiten")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_AendF, self.button_Bearbeiten)      
        self.button_Voll = wx.Button(self, -1, label="&Suche",size=(77,50), name="BSuche")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Volltext, self.button_Voll)
        self.button_Voll.Enable(False)        
        self.button_Doppelt = wx.Button(self, -1, label="Do&ppelte", size=(77,50),name="BDoppelt")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_Doppelt, self.button_Doppelt)
        self.button_Dokumente = wx.Button(self, -1, label="&Dokumente",size=(77,50), name="BDokumente")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_Doku, self.button_Dokumente)
        #self.button_Listen = wx.Button(self, -1, label="&Listen",size=(77,50), name="BListen")
        #self.Bind(wx.EVT_BUTTON, self.On_Adresse_Listen, self.button_Listen)               
        #self.button_Listen.Enable(False)
        self.button_Ende = wx.Button(self, -1, label="Be&enden",size=(77,50), name="BEnde")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Ende)
        
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Auswahl,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Bearbeiten,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Voll,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Doppelt,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Dokumente,0,wx.EXPAND)
        self.button_mid_sizer.AddStretchSpacer(1)
        #self.button_mid_sizer.Add(self.button_Listen,0,wx.EXPAND)
        #self.button_mid_sizer.AddStretchSpacer(1)
        self.button_mid_sizer.Add(self.button_Ende,0,wx.EXPAND)
        
        self.button_low_sizer.AddStretchSpacer(1)
        self.button_low_sizer.Add(self.button_mid_sizer,0,wx.EXPAND)
        self.button_low_sizer.AddStretchSpacer(1)
        
        self.button_sizer.AddSpacer(10)
        self.button_sizer.Add(self.text_MerkT_Archiv,0,wx.EXPAND)
        self.button_sizer.AddSpacer(10)
        self.button_sizer.Add(self.button_low_sizer,1,wx.EXPAND)
        self.button_sizer.AddSpacer(20)
     
        # COMBOBOX
        self.combo_Filter_Merk = wx.ComboBox(self, -1, value="", size=(150,20), choices=[], style=wx.CB_DROPDOWN, name="Filter_Merk")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter_Merk, self.combo_Filter_Merk)
        self.top_mid_sizer.AddStretchSpacer(1)
        self.top_mid_sizer.Add(self.combo_Filter_Merk,0,wx.EXPAND)
        self.top_mid_sizer.AddSpacer(10)
        
        self.label_LAdresse = wx.StaticText(self, -1,label="Adresse:", name="LAdresse")
        self.label_Geschlecht = wx.StaticText(self, -1,label="", name="Geschlecht_AdScreen")
        self.labelmap["Geschlecht_AdScreen"] = "Geschlecht.ADRESSE"
        self.label_Anrede = wx.StaticText(self, -1,label="",  name="Anrede_AdScreen")
        self.labelmap["Anrede_AdScreen"] = "Anrede.ADRESSE"
        #self.choice_Status = wx.Choice(self, -1, size=(77,18), choices=["Passiv", "Aktiv", "Neutral", "Markiert", "Inaktiv"],  name="RStatus")
        self.choice_Status = wx.Choice(self, -1, choices=AfpAdresse_StatusStrings(),  name="RStatus")
        #self.choice_Status.SetSelection(0)
        self.choice_Status.Enable(False)
        self.Bind(wx.EVT_CHOICE, self.On_CStatus, self.choice_Status)
        self.choicemap = AfpAdresse_StatusMap()
        
        self.top_client_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_client_sizer.Add(self.label_LAdresse, 0, wx.EXPAND)
        self.top_client_sizer.AddStretchSpacer(1)
        self.top_client_sizer.Add(self.label_Geschlecht, 0, wx.EXPAND)
        self.top_client_sizer.AddStretchSpacer(1)
        self.top_client_sizer.Add(self.label_Anrede, 0, wx.EXPAND)
        self.top_client_sizer.AddStretchSpacer(1)
        self.top_client_sizer.Add(self.choice_Status, 0, wx.EXPAND)
    
        #Adress
        self.label_Vorname = wx.StaticText(self, -1, label="", name="Vorname_AdScreen")
        self.labelmap["Vorname_AdScreen"] = "Vorname.ADRESSE"
        self.label_Name = wx.StaticText(self, -1, label="", name="Name_AdScreen")
        self.labelmap["Name_AdScreen"] = "Name.ADRESSE"
        self.label_Strasse = wx.StaticText(self, -1, label="", name="Strasse_AdScreen")
        self.labelmap["Strasse_AdScreen"] = "Strasse.ADRESSE"
       
        self.label_Plz = wx.StaticText(self, -1, label="", name="Plz_AdScreen")
        self.labelmap["Plz_AdScreen"] = "Plz.ADRESSE"
        self.label_Ort = wx.StaticText(self, -1, label="", name="Ort_AdScreen")
        self.labelmap["Ort_AdScreen"] = "Ort.ADRESSE"
        self.ort_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.ort_sizer.Add(self.label_Plz, 1, wx.EXPAND)
        self.ort_sizer.AddSpacer(10)
        self.ort_sizer.Add(self.label_Ort, 4, wx.EXPAND)
        
        self.adress_sizer = wx.BoxSizer(wx.VERTICAL)
        self.adress_sizer.Add(self.top_client_sizer, 1, wx.EXPAND)
        self.adress_sizer.Add(self.label_Vorname, 1, wx.EXPAND)
        self.adress_sizer.Add(self.label_Name, 1, wx.EXPAND)
        #self.adress_sizer.AddSpacer(10)
        self.adress_sizer.Add(self.label_Strasse, 1, wx.EXPAND)
        self.adress_sizer.Add(self.ort_sizer, 1, wx.EXPAND)
        
        self.contact_sizer = wx.BoxSizer(wx.VERTICAL)
        self.label_LTelefon = wx.StaticText(self, -1, label="Telefon:", size=(50,16), name="LTelefon")
        self.label_Telefon = wx.StaticText(self, -1, label="", name="Telefon_AdScreen")
        self.labelmap["Telefon_AdScreen"] = "Telefon.ADRESSE"
        self.label_Handy = wx.StaticText(self, -1, label="", name="Handy_AdScreen")
        self.labelmap["Handy_AdScreen"] = "Tel2.ADRESSE"
        self.tel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.tel_sizer.Add(self.label_LTelefon, 0, wx.EXPAND)
        self.tel_sizer.AddSpacer(10)
        self.tel_sizer.Add(self.label_Telefon, 1, wx.EXPAND)
        self.tel_sizer.AddSpacer(10)
        self.tel_sizer.Add(self.label_Handy, 1, wx.EXPAND)        
        self.label_LMail = wx.StaticText(self, -1, label="E-Mail:", size=(50,16), name="LMail")
        self.label_Mail = wx.StaticText(self, -1, label="", name="Mail_AdScreen")
        self.labelmap["Mail_AdScreen"] = "Mail.ADRESSE"
        self.label_LFax= wx.StaticText(self, -1, label="Fax:", size=(50,16), name="LFax")
        self.label_Fax = wx.StaticText(self, -1, label="", name="Fax_AdScreen")
        self.labelmap["Fax_AdScreen"] = "Fax.ADRESSE"
        #self.labelmap["Ab"] = "Name.TOrt"
        self.fax_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.fax_sizer.Add(self.label_LFax, 0, wx.EXPAND)
        self.fax_sizer.AddSpacer(10)
        self.fax_sizer.Add(self.label_Fax, 1, wx.EXPAND)
        self.mail_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mail_sizer.Add(self.label_LMail, 0, wx.EXPAND)
        self.mail_sizer.AddSpacer(10)
        self.mail_sizer.Add(self.label_Mail, 1, wx.EXPAND)
        self.mail_sizer.AddSpacer(10)
        self.label_Bem = wx.StaticText(self, -1,label="", name="Bem_AdScreen")
        self.labelmap["Bem_AdScreen"] = "Bem.ADRESSE"
        self.label_BemExt = wx.StaticText(self, -1,label="", name="BemExt_AdScreen")
        self.labelmap["BemExt_AdScreen"] = "BemExt.ADRESSE"        
        self.contact_sizer.Add(self.tel_sizer, 1, wx.EXPAND)
        self.contact_sizer.Add(self.fax_sizer, 1, wx.EXPAND)
        self.contact_sizer.Add(self.mail_sizer, 1, wx.EXPAND)
        self.contact_sizer.Add(self.label_Bem, 1, wx.EXPAND)
        self.contact_sizer.Add(self.label_BemExt, 2, wx.EXPAND)
        
        # complete layout
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_sizer.AddSpacer(20)
        self.panel_sizer.Add(self.adress_sizer, 1, wx.EXPAND)
        self.panel_sizer.AddSpacer(10)
        self.panel_sizer.Add(self.contact_sizer, 1, wx.EXPAND)
        self.panel_sizer.AddSpacer(10)
        
        # Combo Box to control grid
        self.combo_Archiv = wx.ComboBox(self, -1, value="Dokumente", size=(186,20), choices=["Dokumente","Merkmale","Beziehungen"], style=wx.CB_DROPDOWN, name="Archivtyp")
        #self.combo_Archiv = wx.ComboBox(self, -1, value="Rechnungs-Ausgang", pos=(23,236), size=(186,20), choices=["Dokumente","Anmeldungen","Mietfahrten","Rechnungs-Ausgang","Rechnungs-Eingang"], style=wx.CB_DROPDOWN, name="Archiv")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter_Archiv, self.combo_Archiv)
        # GRID
        self.grid_archiv = wx.grid.Grid(self, -1, pos=(23,256) , size=(653, 264), name="Archiv")
        self.grid_archiv.CreateGrid(self.grid_rows["Archiv"], self.grid_cols["Archiv"])
        self.grid_archiv.SetRowLabelSize(3)
        self.grid_archiv.SetColLabelSize(18)
        self.grid_archiv.EnableEditing(0)
        self.grid_archiv.EnableDragColSize(0)
        self.grid_archiv.EnableDragRowSize(0)
        self.grid_archiv.EnableDragGridSize(0)
        self.grid_archiv.SetSelectionMode(wx.grid.Grid.GridSelectRows)
        self.grid_archiv.SetColLabelValue(0, self.archiv_colname[0])
        self.grid_archiv.SetColSize(0, 130)
        self.grid_archiv.SetColLabelValue(1, self.archiv_colname[1])
        self.grid_archiv.SetColSize(1, 130)
        self.grid_archiv.SetColLabelValue(2, self.archiv_colname[2])
        self.grid_archiv.SetColSize(2, 130)
        self.grid_archiv.SetColLabelValue(3, self.archiv_colname[3])
        self.grid_archiv.SetColSize(3, 130)
        self.grid_archiv.SetColLabelValue(4, self.archiv_colname[4])
        self.grid_archiv.SetColSize(4, 130)
        for row in range(0,self.grid_rows["Archiv"]):
            for col in range(0,self.grid_cols["Archiv"]):
                self.grid_archiv.SetReadOnly(row, col)
        self.gridmap.append("Archiv")
        self.grid_minrows["Archiv"] = self.grid_archiv.GetNumberRows()
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick_Archiv, self.grid_archiv)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_RIGHT_DCLICK, self.On_DClickRight_Archiv, self.grid_archiv)
        
        self.grid_mid_sizer.Add(self.combo_Archiv,0,wx.EXPAND)
        self.grid_mid_sizer.Add(self.grid_archiv,1,wx.EXPAND)
        self.grid_panel_sizer.AddSpacer(20)
        self.grid_panel_sizer.Add(self.grid_mid_sizer,1,wx.EXPAND)
        self.grid_panel_sizer.AddSpacer(10)
       
        self.top_sizer.Add(self.modul_button_sizer,0,wx.EXPAND)
        self.top_sizer.Add(self.top_mid_sizer,1,wx.EXPAND)
       
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.top_sizer,0,wx.EXPAND)
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.panel_sizer,0,wx.EXPAND)
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.grid_panel_sizer,1,wx.EXPAND)
        self.left_sizer.AddSpacer(20)
    
        self.sizer.Add(self.left_sizer,1,wx.EXPAND)
        self.sizer.Add(self.button_sizer,0,wx.EXPAND)   
        
        self.dynamic_grid_sizer = self.grid_panel_sizer
        #self.Bind(wx.EVT_ACTIVATE, self.On_Activate)

    ## compose address specific menu parts
    def create_specific_menu(self):
        # setup address menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Anfrage", "")
        self.Bind(wx.EVT_MENU, self.On_MAnfrage, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Suchen", "")
        self.Bind(wx.EVT_MENU, self.On_Adresse_AuswErw, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Bearbeiten", "")
        self.Bind(wx.EVT_MENU, self.On_Adresse_AendF, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&E-Mail versenden", "")
        self.Bind(wx.EVT_MENU, self.On_MEMail, mmenu)
        tmp_menu.Append(mmenu)
        self.menubar.Append(tmp_menu, "Adresse")
        return
        
    ## connect to database and populate widgets
    # overwritten from AfpScreen
    # @param globals - global variables, including database connection
    # @param sb - AfpSuperbase database object , if supplied, otherwise it is created
    # @param origin - string from where to get data for initial record, 
    # to allow syncronised display of screens (only works if 'sb' is given)
    def init_database(self, globals, sb, origin):
        super(AfpAdScreen, self).init_database(globals, sb, origin)
        self.add_grid_choices()

    ## check available choices for grid
    def add_grid_choices(self):
        choices = []
        tables = self.mysql.get_tables()
        mods = Afp_ModulNames(self.globals, True)
        #print "AfpAdScreen.add_grid_choices:", mods
        if "ANMELD" in tables and "EVENT" in tables:
            choices.append("Anmeldungen")
            if "Verein" in mods:
                modul = Afp_importPyModul("AfpEvent.AfpEvScreen_Verein", self.globals)
                self.data_objects["Anmeldungen"] = modul.AfpLoad_EvMemberEdit_fromANr
            elif "Tourist" in mods:
                modul = Afp_importPyModul("AfpEvent.AfpEvScreen_Tourist", self.globals)
                self.data_objects["Anmeldungen"] = modul.AfpLoad_EvTouristEdit_fromANr
            elif "Event" in mods:
                modul = Afp_importPyModul("AfpEvent.AfpEvDialog", self.globals)
                self.data_objects["Anmeldungen"] = modul.AfpLoad_EvClientEdit_fromANr
        if "Charter" in mods and "FAHRTEN" in tables:
            choices.append("Mietfahrten")
            modul = Afp_importPyModul("AfpCharter.AfpChDialog", self.globals)
            self.data_objects["Mietfahrten"] = modul.AfpLoad_DiChEin_fromFNr
        if "RECHNG" in tables:
            choices.append("Rechnungs-Ausgang")
        if "VERBIND" in tables:
            choices.append("Rechnungs-Eingang")
        if "Finance" in mods and "BUCHUNG" in tables:
            choices.append("Finanzbuchungen")
        if choices:
            for choice in choices:
                self.combo_Archiv.Append(choice)

    ## Eventhandler double click on grid
    def On_DClick_Archiv(self,event):
        if self.debug: print("Event handler `On_DClick_Archiv'!")
        index = event.GetRow()
        typ= self.combo_Archiv.GetValue()
        #print "AfpAdScreen.On_DClick_Archiv:", index, typ
        if len(self.grid_id["Archiv"]) > index:
            value = Afp_fromString(self.grid_id["Archiv"][index])
            #print ("AfpAdScreen.On_DClick_Archiv Archiv:", typ, index, value)
            if typ == "Dokumente":
                if "|" in value:
                    value = value.split("|")
                else:
                    value = [value]
                for val in value:
                    fpath = Afp_addRootpath(self.globals.get_value("archivdir"), val)
                    if not Afp_existsFile(fpath):
                        fpath = Afp_addRootpath(self.globals.get_value("antiquedir"), val)
                    if Afp_existsFile(fpath):
                        Afp_startFile(fpath,self.globals, self.debug, True)
                    else:
                        print("WARNING: File not found in archiv:", fpath)
            elif typ == "Merkmale":
                print("AfpAdScreen.On_DClick_Archiv: 'Merkmal' clicked, no action implemented yet.")
            elif typ == "Beziehungen":
                self.select_from_KNr(value)
            elif typ == "Rechnungs-Eingang":
                AfpLoad_Obligation_fromVbNr(self.globals, value)
            elif typ == "Rechnungs-Ausgang":
                AfpLoad_SimpleInvoice_fromReNr(self.globals, value)
            elif typ in self.data_objects:
                self.data_objects[typ](self.globals, value)
        event.Skip()
    ## Eventhandler right double click on grid
    def On_DClickRight_Archiv(self,event):
        if self.debug: print("Event handler `On_DClickRight_Archiv'!")
        typ= self.combo_Archiv.GetValue()
        if typ == "Dokumente":
            index = event.GetRow()
            if len(self.grid_id["Archiv"]) > index:
                lgh = self.data.get_value_length("ARCHIV")
                ind = lgh - index - 1
                row = self.data.get_value_rows("ARCHIV","Datum,Art,Typ,Gruppe,Bem,Extern", ind)[0]
                #print("AfpAdScreen.On_DClickRight_Archiv:", index, row)
                liste = [["Datum:", Afp_toString(row[0])],["Art:", row[1]], ["Ablage:", row[2]], ["Fach:", row[3]], ["Bemerkung:", row[4]]]
                result = AfpReq_MultiLine( "  Bitte Archiveintrag von " + self.data.get_name()  +" für das Dokument  ", "  '" + row[5] + "' ändern." , "Text", liste, "Archiveintrag", 300, None)
                #print("AfpAdScreen.On_DClickRight_Archiv result:", ind, result)
                if result:
                    changed = {}
                    if result[0] != liste[0][1]: changed["Datum"] =  result[0]
                    if result[1] != liste[1][1]: changed["Art"] =  result[1]
                    if result[2] != liste[2][1]: changed["Typ"] =  result[2]
                    if result[3] != liste[3][1]: changed["Gruppe"] =  result[3]
                    if result[4] != liste[4][1]: changed["Bem"] =  result[4]
                    if changed:
                        self.data.set_data_values(changed, "ARCHIV", ind)
                        self.data.get_selection("ARCHIV").store()
                        self.Pop_grid("Archiv")
            event.Skip()
        else:
            self.On_DClick_Archiv(event)
    ## Eventhandler MENU; BUTTON - select other address, either direkt or via attribut
    def On_Adresse_AuswErw(self,event):
        if self.debug: print("Event handler `On_Adresse_AuswErw'!")
        #self.sb.set_debug()
        index = self.sb.identify_index().get_name()
        where = AfpSelectEnrich_dbname(self.sb.identify_index().get_where(), self.sb_master)
        values = self.sb.identify_index().get_indexwert()
        #print ("On_Adresse_AuswErw Ind:",index, "VAL:",values,"Where:", where)
        #print "On_Adresse_AuswErw Merkmal:", self.combo_Filter_Merk.GetValue()
        attrib = None
        value = ""
        if values:
            if self.sb_master == "ADRESATT": 
                value = values[1]
                attrib = values[0]
            else: 
                #value = values[0]
                if values[0]:
                    value = values[0].split()[0]
        auswahl = AfpLoad_AdAusw(self.globals, self.sb_master, index, value, where, attrib, True)
        if not auswahl is None:
            KNr = int(auswahl)
            self.select_from_KNr(KNr)
        event.Skip() 
    ## select screen from adress-identifier (KNr)
    # @param KNr - address identifier
    def select_from_KNr(self, KNr):
        index = self.sb.identify_index().get_name()
        if self.sb_filter: self.sb.select_where(self.sb_filter, "KundenNr", self.sb_master)
        self.sb.select_key(KNr, "KundenNr", self.sb_master)
        if self.sb_filter: self.sb.select_where("", "KundenNr", self.sb_master)
        self.sb.set_index(index, self.sb_master, "KundenNr")   
        if self.sb_master == "ADRESATT":
            self.sb.select_key(KNr,"KundenNr","ADRESSE")
        self.data = AfpAdresse(self.globals, KNr)
        self.Populate()
    ## create first record in database, the own address
    def create_initial_record(self):
        AfpReq_Info("Leere Adressdatei!","Zum Einrichten bitte die eigene Adresse eingeben!","Eigene Adresse eingeben!")
        adresse = AfpAdresse(self.globals, None, None, self.debug)
        ok = AfpLoad_DiAdEin(adresse)
        return ok
    ## Eventhandler BUTTON - resolve duplicate addresses 
    def On_Adresse_Doppelt(self,event):
        if self.debug: print("AfpAdScreen Event handler `On_Adresse_Doppelt'")
        name = self.sb.get_string_value("Name.ADRESSE")
        vorname = self.sb.get_string_value("Vorname.ADRESSE")
        KdNr = self.sb.get_value("KundenNr.ADRESSE")
        text = "Bitte Adressduplikat für '" + vorname + " " +  name +" (" + Afp_toString(KdNr) + ") auswählen!"  
        auswahl = AfpLoad_AdAusw(self.globals, "ADRESSE", "NamSort", name, None, text)
        if auswahl:
            if auswahl == KdNr:
                AfpReq_Info("Identische Adresse ausgewählt,", "keine Übernahme möglich!","Adressduplikat")
            else:
                Adresse = AfpAdresse(self.globals, None, self.sb, self.sb.debug)
                victim = AfpAdresse(self.globals, auswahl, None, self.globals.is_debug())
                text0 = ""
                if auswahl < KdNr: text0 = "VORSICHT: ältere Adresse wird durch neuere Adresse ersetzt!\n\n"
                text1 = "Die Adresse: \n(" + Afp_toString(auswahl) + ") "+ victim.get_name() + ", "  + victim.get_string_value("Strasse") + ", "  + victim.get_string_value("Plz") + " " + victim.get_string_value("Ort")
                text2 = "ersetzen durch: \n(" + Afp_toString(KdNr) + ") "+ Adresse.get_name() + ", "  + Adresse.get_string_value("Strasse") + ", "  + Adresse.get_string_value("Plz") + " " + Adresse.get_string_value("Ort") + "?"
                text3 = "\n\nVORSICHT, diese Aktion ist nicht rückgängig zu machen!!"
                ok = AfpReq_Question(text0 + text1,text2 + text3,"Adressduplikat")
                if ok:
                    Adresse.hostile_takeover(victim)
        event.Skip()
    ## Eventhandler BUTTON - show different lists, not implemented yet!
    def On_Adresse_Listen(self,event):
        print("Event handler `On_Adresse_Listen' not implemented!")
        event.Skip()
    ## Eventhandler MENU, BUTTON - change address
    def On_Adresse_AendF(self,event):
        if self.debug: print("AfpAdScreen Event handler `On_Adresse_AendF'")
        AfpLoad_DiAdEin_fromSb(self.globals, self.sb)
        event.Skip()
    ## Eventhandler BUTTON - invoke full text search over addresses an all attached data - not yet implemented
    def On_Ad_Volltext(self,event):
        print("Event handler `On_Ad_Volltext' not implemented!")
        event.Skip()
    ## Eventhandler BUTTON - invoke dokument generation - not yet implemented
    def On_Adresse_Doku(self,event):
        if self.debug and event: print("AfpAdScreen Event handler `On_Adresse_Doku'")
        data = self.get_data()
        if data:
            variables = {}
            prefix = data.get_listname() + "_"
            header = "Adressen" 
            #print ("AfpAdScreen.On_Adresse_Doku:", prefix, header, variables)
            AfpLoad_DiReport(data, self.globals, variables, header, prefix)
        
    ## Eventhandler COMBOBOX - allow filter due to attributes
    def On_Filter_Merk(self,event): 
        value = self.combo_Filter_Merk.GetValue()
        if self.debug: print("AfpAdScreen Event handler `On_Filter_Merk'", self.sb_master, value)      
        where = ""
        changed = (value != "" and  self.sb_master == "ADRESSE") or (value == "" and  self.sb_master == "ADRESATT")
        vorname =  self.sb.get_string_value("Vorname.ADRESSE")
        name = self.sb.get_string_value("Name")
        KNr = self.sb.get_value("KundenNr")
        if value == "":   
            if self.sb_master == "ADRESATT":
                self.sb.select_where("")
            self.sb_master = "ADRESSE"
            Index = "NamSort"
            s_key = name + " " + vorname
        else:
            if self.sb_master =="ADRESSE": 
                self.sb.CurrentIndexName("KundenNr")
            self.sb_master = "ADRESATT"
            Index = "AttName"
            where = "Attribut = \"" +  value + "\" and KundenNr > 0"
            s_key =  value + " " + name 
        if changed:
            self.sb.CurrentIndexName(Index, self.sb_master)  
        if where != "" and self.sb_filter != where: 
            self.sb.select_where(where)
            changed = True
        self.sb_filter = where
        if changed:
            #print "AfpAdScreen.On_Filter_Merk:", self.sb_master, "KEY:", s_key, "VALUE:", value, "WHERE:", where
            #self.sb.set_debug()
            self.sb.select_key(s_key)
            while KNr != self.sb.get_value("KundenNr") and name ==  self.sb.get_string_value("Name") and vorname ==  self.sb.get_string_value("Vorname.ADRESSE") and self.sb.neof():
              self.sb.select_next()
            #self.sb.unset_debug()
        self.CurrentData()
        event.Skip()
    ## Eventhandler COMBOBOX - fill grid 'Archiv' due to the new setting
    def On_Filter_Archiv(self,event):
        self.Pop_grid("Archiv")        
        if self.debug: print("AfpAdScreen Event handler `On_Filter_Archiv'") 
        event.Skip()
    ## Eventhandler RADIOBOX - only implemented to reset selection due to database entry
    def On_CStatus(self, event):
        self.Pop_choice_status()
        if self.debug: print("Event handler `On_CStatus' only implemented to reset selection!")
        event.Skip()
        
    ## Eventhandler MENU - add an enquirery - not yet implemented! \n
    def On_MAnfrage(self, event):
        print("Event handler `On_MAnfrage' not implemented!")
        event.Skip()
    ## Eventhandler MENU - send an e-mail - not yet implemented! 
    def On_MEMail(self, event):
        if self.debug: print("Event handler `On_MEMail'")
        #mail = AfpMailSender(self.globals, self.debug)
        mail = AfpMailSender(self.globals,True)
        an = self.sb.get_value("Mail.ADRESSE")
        if an: mail.add_recipient(an)
        mail, send = Afp_editMail(mail)
        if send: mail.send_mail()
        event.Skip()
      
    ## set right status-choice for this address
    def Pop_choice_status(self):
        status = self.sb.get_value("Kennung.ADRESSE")
        if not status: status = 0
        map = AfpAdresse_StatusMap()
        index = map[status]
        self.choice_Status.SetSelection(index)
        if self.debug: print("AfpAdScreen Population routine`Pop_choice_status'", status, index)
    ## populate attribut filter with entries from database table
    def Pop_Filter_Merk(self):
        if self.debug:  print("AfpAdScreen Population routine`Pop_Filter_Merk'")      
        rows = self.mysql.select_strings("Attribut","KundenNr = 0","ADRESATT")
        values = []
        values.append("")
        for value in rows:
            if value[0]: values.append(value[0])
        values.sort()
        self.combo_Filter_Merk.AppendItems(values)
      
    # routines to be overwritten in explicit class
    ## generate AfpAdresse object from the present screen, overwritten from AfpScreen
    # @param complete - flag if all TableSelections should be generated
    def get_data(self, complete = False):
        return  AfpAdresse(self.globals, None, self.sb, self.sb.debug, complete)
    ## set current record to be displayed 
    # (overwritten from AfpScreen) 
    def set_current_record(self):
        KNr = self.sb.get_value("KundenNr")
        if self.sb_master == "ADRESATT":
            self.sb.select_key(KNr,"KundenNr","ADRESSE")
        self.data = AfpAdresse(self.globals, KNr)
        #print ("AfpAdScreen.set_current_record:",self.sb, self.data, self.sb_master, KNr)
        #self.data.view()
        self.Pop_choice_status()
        return  
    ## set initial record to be shown, when screen opens the first time
    #overwritten from AfpScreen) 
    # @param origin -  initial data, if Integer, KNr is assumed, else string, where to find the data
    def set_initial_record(self, origin = None):
        if Afp_isInteger(origin):
            KNr = origin
        else:
            KNr = 0
        if origin == "Charter":
            KNr = self.sb.get_value("KundenNr.FAHRTEN")
            #KNr = self.globals.get_value("KundenNr", origin)
        if origin == "Event":
            KNr = self.sb.get_value("KundenNr.ANMELD")
        #print ("AfpAdScreen.set_initial_record:", origin, KNr)
        if KNr == 0:
            self.sb.CurrentIndexName("KundenNr","ADRESSE")
            self.sb.select_last()
            KNr = self.sb.get_value("KundenNr.ADRESSE")
            if KNr:
                self.sb.CurrentIndexName("NamSort","ADRESSE")
            else: # create initial entry
                ok = self.create_initial_record()
                if ok: self.sb.select_last()
        else:
            self.sb.select_key(KNr,"KundenNr","ADRESSE")
            self.sb.set_index("NamSort","ADRESSE","KundenNr")
            self.sb.CurrentIndexName("NamSort","ADRESSE")
        self.Pop_Filter_Merk()
        return
    ## get identifier of graphical objects, 
    # where the keydown event should not be catched
    # (overwritten from AfpScreen)
    def get_no_keydown(self):
        return ["Bem","BemExt","MerkT_Archiv","Archiv"]
    ## get names of database tables to be opened for this screen
    # (overwritten from AfpScreen)
    def get_dateinamen(self):
        #return  ["ADRESATT", "ADRESSE", "ANFRAGE", "ARCHIV"]
        return  ["ADRESATT", "ADRESSE", "ARCHIV"]
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param name - name of grid to be populated
    def get_grid_rows(self, name):
        rows = []
        if self.debug: print("AfpAdScreen.get_grid_rows Population routine",name)
        if name == "Archiv":
            typ= self.combo_Archiv.GetValue()
            KundenNr =  self.sb.get_value("KundenNr") 
            if not KundenNr: KundenNr = 0
            id_col = 5      
            select = ( "KundenNr = %d")% KundenNr
            if typ == "Dokumente":
                self.archiv_colname = self.archiv_colnames[0]
                rows = self.mysql.select_strings("Datum,Art,Typ,Gruppe,Bem,Extern",select,"ARCHIV") 
                rows = rows[::-1] # reverse list
            elif typ == "Anmeldungen":
                self.archiv_colname = self.archiv_colnames[1]
                # select += " and FahrtNr.REISEN = FahrtNr.ANMELD"
                # rows = self.mysql.select_strings("RechNr.ANMELD,Anmeldung,Zielort.REISEN,Preis.ANMELD,Zahlung.ANMELD,AnmeldNr",select,"ANMELD REISEN")
                select += " and EventNr.EVENT = EventNr.ANMELD"
                rows = self.mysql.select_strings("RechNr.ANMELD,Anmeldung,Bez.EVENT,Preis.ANMELD,Zahlung.ANMELD,AnmeldNr",select,"ANMELD EVENT")
                rows = rows[::-1] # reverse list
            elif typ == "Mietfahrten":
                self.archiv_colname = self.archiv_colnames[2]
                rows = self.mysql.select_strings("Zustand,Abfahrt,Zielort,Art,Preis,FahrtNr",select,"FAHRTEN")
                rows = rows[::-1] # reverse list
            elif typ == "Rechnungs-Ausgang":
                self.archiv_colname = self.archiv_colnames[3]
                rows = self.mysql.select_strings("RechNr,Datum,Bem,Betrag,Zahlung,RechNr",select,"RECHNG")
                rows = rows[::-1] # reverse list
            elif typ == "Rechnungs-Eingang":
                self.archiv_colname = self.archiv_colnames[4]
                select += " and RechNr > 0"
                rows = self.mysql.select_strings("ExternNr,Datum,Bem,Betrag,Zahlung,RechNr",select,"VERBIND") 
                rows = rows[::-1] # reverse list
            elif typ == "Merkmale":
                self.archiv_colname = self.archiv_colnames[5]
                rows = self.mysql.select_strings("Attribut,AttText,Tag,Attribut",select,"ADRESATT") 
                rows = self.split_tag_rows(rows)
            elif typ == "Finanzbuchungen":
                self.archiv_colname = self.archiv_colnames[6]
                raws = self.mysql.select_strings("Datum,Konto,Gegenkonto,Betrag,Bem,Period,BuchungsNr",select,"BUCHUNG") 
                rows = []
                for raw in raws:
                    rows.append([Afp_toString(raw[0]), raw[1] + " - " + raw[2], raw[3], raw[4], raw[5], raw[6]])
                rows = rows[::-1] # reverse list
            elif typ == "Beziehungen":
                self.archiv_colname = self.archiv_colnames[7]
                rows = []
                stack = [int(KundenNr)]
                if self.sb.get_value("Bez.ADRESSE"):
                    KNr = int(self.sb.get_value("Bez.ADRESSE")) 
                else:
                    KNr = 0
                while not KNr in stack and KNr != 0:
                    stack.append(KNr)
                    select = ( "KundenNr = %d")% KNr
                    row = self.mysql.select_strings("Name,Vorname,Strasse,Ort,Telefon,Bez,KundenNr",select ,"ADRESSE") 
                    rows.append(row[0])
                    KNr = int(row[0][5])
            for col in range(0,5):
                self.grid_archiv.SetColLabelValue(col, self.archiv_colname[col])
        #print "get_grid_rows:", rows
        return rows
    ## split tag columns to show maximum of content
    # @param rows - matrix, where tag column should be split up
    def split_tag_rows(self, rows):
        if rows:
            rows = Afp_MatrixSplitCol(rows, 2,",", " ")
        return rows
