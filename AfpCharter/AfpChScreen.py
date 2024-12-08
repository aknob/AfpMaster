#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpCharter.AfpChScreen
# AfpChScreen module provides the graphic screen to access all data of the Afp-'Charter' modul 
# it holds the class
# - AfpChScreen
#
#   History: \n
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

import AfpBase
from AfpBase import *
from AfpBase.AfpUtilities import *
from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile
from AfpBase.AfpDatabase import *
from AfpBase.AfpDatabase.AfpSQL import AfpSQL
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import Afp_archivName, Afp_startFile
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Selection, AfpReq_Question
from AfpBase.AfpBaseDialogCommon import AfpLoad_DiReport
from AfpBase.AfpBaseScreen import AfpScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse_getListOfTable
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_DiAdEin_fromSb
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

import AfpCharter
from AfpCharter import AfpChRoutines, AfpChDialog
from AfpCharter.AfpChRoutines import AfpCharter, AfpChInfo_genLine, AfpCharter_isOperational
from AfpCharter.AfpChDialog import AfpLoad_DiChEin, AfpLoad_DiChEin_fromSb, AfpLoad_ChAusw, AfpCharter_copy

## Class AfpChScreen shows 'Charter' screen and handles interactions
class AfpChScreen(AfpScreen):
    ## initialize AfpChScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        AfpScreen.__init__(self,None, -1, "")
        self.typ = "Charter"
        self.einsatz = None # to invoke import of 'Einsatz' modules in 'init_database'
        if debug: self.debug = debug
        # self properties
        self.SetTitle("BusAfp Charter")
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.SetForegroundColour(wx.Colour(20, 19, 18))
        self.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "DejaVu Sans"))

        panel = self.panel
      
        # BUTTON
        self.button_Auswahl = wx.Button(panel, -1, label="Aus&wahl", pos=(692,50), size=(77,50), name="Auswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_AuswF, self.button_Auswahl)
        self.button_Neu = wx.Button(panel, -1, label="&Neu", pos=(692,110), size=(77,50), name="Neu")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_neu, self.button_Neu)
        self.button_Bearbeiten = wx.Button(panel, -1, label="&Bearbeiten", pos=(692,170), size=(77,50), name="Bearbeiten")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_aendern, self.button_Bearbeiten)
        self.button_Adresse = wx.Button(panel, -1, label="&Adresse", pos=(692,230), size=(77,50), name="Adresse")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_aendern, self.button_Adresse)      
        self.button_Zahlung = wx.Button(panel, -1, label="&Zahlung", pos=(692,290), size=(77,50), name="BZahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_ZahlungF, self.button_Zahlung)
     
        self.button_Dokumente = wx.Button(panel, -1, label="&Dokumente", pos=(692,350), size=(77,50), name="Dokumente")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_Ausgabe, self.button_Dokumente)
        self.button_Einsatz = wx.Button(panel, -1, label="Ein&satz", pos=(692,410), size=(77,50), name="Einsatz")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_EinF, self.button_Einsatz)      
        self.button_Ende = wx.Button(panel, -1, label="Be&enden", pos=(692,470), size=(77,50), name="Ende")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Ende)
       
        # COMBOBOX
        self.combo_Filter = wx.ComboBox(panel, -1, value="Alle", pos=(529,16), size=(150,20), choices=["Alle","Kostenvoranschläge","Angebote","Aufträge","Rechnungen","Mahnungen","Stornierungen"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Anmiet_Filter, self.combo_Filter)
        self.filtermap = {"Alle":"","Kostenvoranschläge":"KVA","Angebote":"Angebot","Aufträge":"Auftrag","Rechnungen":"Rechnung","Mahnungen":"Mahnung","Stornierungen":"Storno %"}
        self.combo_Sortierung = wx.ComboBox(panel, -1, value="Datum", pos=(689,16), size=(80,20), choices=["Datum","Zielort","Name","Vorgang"], style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Anmiet_Index, self.combo_Sortierung)
        self.indexmap = {"Datum":"Abfahrt","Zielort":"Zielort","Name":"Name","Vorgang":"Vorgang"}
      
        # LABEL
        self.label_Vom = wx.StaticText(panel, -1, label="vom", pos=(334,169), size=(28,19), name="LVom")
        self.label_Fuer = wx.StaticText(panel, -1, label="für", pos=(200,169), size=(20,20), name="LFuer")
        self.label_BisZum = wx.StaticText(panel, -1, label="bis zum", pos=(238,50), size=(47,20), name="LBisZum")
        self.label_Vom2 = wx.StaticText(panel, -1, label="vom", pos=(135,50), size=(23,20), name="LVom2")
        self.label_LAdresse = wx.StaticText(panel, -1, label="Adresse:", pos=(30,218), size=(96,20), name="LAdresse")
        self.label_LZahlung = wx.StaticText(panel, -1, label="Zahlung:", pos=(511,288), size=(70,20), name="LZahlung")
        self.label_BExtra = wx.StaticText(panel, -1, label="Extra:", pos=(511,238), size=(70,20), name="BExtra")
        self.label_BPreis = wx.StaticText(panel, -1, label="Preis:", pos=(511,263), size=(70,20), name="BPreis")
        self.label_BVorgang = wx.StaticText(panel, -1, label="Vorgang:", pos=(30,326), size=(95,20), name="BVorgang")
        self.label_BKontakt = wx.StaticText(panel, -1, label="Kontakt:", pos=(30,191), size=(95,20), style = wx.ALIGN_RIGHT, name="BKontakt")
        self.label_Fahrt_Info = wx.StaticText(panel, -1, label="Info:", pos=(375,50), size=(70,20), name="Fahrt_Info")
        self.label_LMietfahrt = wx.StaticText(panel, -1, label="Mietfahrt:", pos=(30,51), size=(95,20), name="LMietfahrt")
        self.label_BPers = wx.StaticText(panel, -1, label="Personen:", pos=(30,96), size=(95,20), name="BPers")
        self.label_BKm = wx.StaticText(panel, -1, label="Fahrkm:", pos=(200,96), size=(95,20), name="BKm")
        self.label_BArchiv = wx.StaticText(panel, -1, label="Archiv:", pos=(30,350), size=(95,15), name="BArchiv")
        self.label_BAus = wx.StaticText(panel, -1, label="Ausstattung:", pos=(30,120), size=(95,20), name="BAus")
      
        # TEXTBOX
        #Adresse
        self.text_Vorname = wx.TextCtrl(panel, -1, value="", pos=(296,220), size=(140,20), style=wx.TE_READONLY, name="Vorname")
        self.textmap["Vorname"] = "Vorname.ADRESSE"
        self.text_Name = wx.TextCtrl(panel, -1, value="", pos=(136,220), size=(150,20), style=wx.TE_READONLY, name="Name")
        self.textmap["Name"] = "Name.ADRESSE"
        self.text_Strasse = wx.TextCtrl(panel, -1, value="", pos=(136,240), size=(228,20), style=wx.TE_READONLY, name="Strasse")
        self.textmap["Strasse"] = "Strasse.ADRESSE" 
        self.text_Plz = wx.TextCtrl(panel, -1, value="", pos=(136,260), size=(50,20), style=wx.TE_READONLY, name="Plz")
        self.textmap["Plz"] = "Plz.ADRESSE"
        self.text_Ort = wx.TextCtrl(panel, -1, value="", pos=(184,260), size=(176,20), style=wx.TE_READONLY, name="Ort")
        self.textmap["Ort"] = "Ort.ADRESSE"
        self.text_Tel = wx.TextCtrl(panel, -1, value="", pos=(136,280), size=(139,20), style=wx.TE_READONLY, name="Tel")
        self.textmap["Tel"] = "Telefon.ADRESSE"
        self.text_Tel2 = wx.TextCtrl(panel, -1, value="", pos=(285,280), size=(139,20), style=wx.TE_READONLY, name="Tel2")
        self.textmap["Tel2"] = "Tel2.ADRESSE"
        self.text_Mail = wx.TextCtrl(panel, -1, value="", pos=(136,300), size=(310,22), style=0, name="Mail")
        self.textmap["Mail"] = "Mail.ADRESSE"
      
        # Fahrt
        self.text_Zielort = wx.TextCtrl(panel, -1, value="", pos=(273,74), size=(172,20), style=wx.TE_READONLY, name="Zielort")
        self.textmap["Zielort"] = "Zielort.FAHRTEN"
        self.text_Vorgang = wx.TextCtrl(panel, -1, value="", pos=(132,327), size=(124,20), style=wx.TE_READONLY, name="Vorgang")
        #self.textmap["Vorgang"] = "Bez.FAHRTVOR"
        self.text_Datum = wx.TextCtrl(panel, -1, value="", pos=(370,169), size=(75,20), style=wx.TE_READONLY, name="Datum")
        self.textmap["Datum"] = "Datum.FAHRTEN"
        self.text_Kontakt = wx.TextCtrl(panel, -1, value="", pos=(137,193), size=(145,20), style=wx.TE_READONLY, name="Kontakt")
        self.textmap["Kontakt"] = "Kontakt.FAHRTEN"
        self.text_Ausland = wx.TextCtrl(panel, -1, value="", pos=(345,98), size=(36,20), style=wx.TE_READONLY, name="Ausland")
        self.textmap["Ausland"] = "Ausland.FAHRTEN"
        self.text_Ausstattung = wx.TextCtrl(panel, -1, value="", pos=(135,120), size=(304,40), style=wx.TE_READONLY, name="Ausstattung")
        self.textmap["Ausstattung"] = "Ausstattung.FAHRTEN"
        self.text_Zahlung = wx.TextCtrl(panel, -1, value="", pos=(595,288), size=(63,20), style=wx.TE_READONLY, name="Zahlung")
        self.textmap["Zahlung"] = "Zahlung.FAHRTEN"
        self.text_Preis = wx.TextCtrl(panel, -1, value="", pos=(595,263), size=(63,20), style=wx.TE_READONLY, name="Preis")
        self.textmap["Preis"] = "Preis.FAHRTEN"
        self.text_Text_Fahrten = wx.TextCtrl(panel, -1, value="", pos=(274,325), size=(406,195), style=wx.TE_MULTILINE, name="Text_Fahrten")
        self.extmap["Text_Fahrten"] = "Brief.FAHRTEN"
        self.text_Art = wx.TextCtrl(panel, -1, value="", pos=(225,169), size=(105,20), style=wx.TE_READONLY, name="Art")
        self.textmap["Art"] = "Art.FAHRTEN"
        self.text_Zustand= wx.TextCtrl(panel, -1, value="", pos=(88,169), size=(105,20), style=wx.TE_READONLY, name="Zustand")
        self.textmap["Zustand"] = "Zustand.FAHRTEN"
        self.text_Nummer = wx.TextCtrl(panel, -1, value="", pos=(30,169), size=(53,20), style=0, name="Nummer")
        #self.textmap["Nummer"] = "SortNr.FAHRTEN"
        self.textmap["Nummer"] = "RechNr.FAHRTEN"
        self.text_Abfahrt = wx.TextCtrl(panel, -1, value="", pos=(163,50), size=(70,20), style=wx.TE_READONLY, name="Abfahrt")
        self.textmap["Abfahrt"] = "Abfahrt.FAHRTEN"
        self.text_Ende = wx.TextCtrl(panel, -1, value="", pos=(290,50), size=(71,20), style=wx.TE_READONLY, name="Fahrtende")
        self.textmap["Fahrtende"] = "Fahrtende.FAHRTEN"
        self.text_Personen = wx.TextCtrl(panel, -1, value="", pos=(139,98), size=(30,20), style=wx.TE_READONLY, name="Personen")
        self.textmap["Personen"] = "Personen.FAHRTEN"
        self.text_KM = wx.TextCtrl(panel, -1, value="", pos=(303,98), size=(36,20), style=wx.TE_READONLY, name="KM")
        self.textmap["KM"] = "Km.FAHRTEN"
        self.text_AbOrt = wx.TextCtrl(panel, -1, value="", pos=(78,74), size=(134,20), style=wx.TE_READONLY, name="AbOrt")
        self.textmap["AbOrt"] = "Abfahrtsort.FAHRTEN"
        self.text_VonT = wx.TextCtrl(panel, -1, value="", pos=(30,74), size=(42,20), style=wx.TE_READONLY, name="VonT")
        self.textmap["VonT"] = "Von.FAHRTEN"
        self.text_NachT = wx.TextCtrl(panel, -1, value="", pos=(215,74), size=(54,20), style=wx.TE_READONLY, name="NachT")
        self.textmap["NachT"] = "Nach.FAHRTEN"
      
        # Fahrtextra
        self.text_TExtra = wx.TextCtrl(panel, -1, value="", pos=(595,238), size=(63,20), style=wx.TE_READONLY, name="TExtra")
        self.textmap["TExtra"] = "Extra.FAHRTEN"
        self.list_extra= wx.ListBox(panel, -1, pos=(450,170) , size=(230, 60), name="Extra")
        self.listmap.append("Extra")
      
        # Fahrtinfo
        self.list_info= wx.ListBox(panel, -1, pos=(450,50) , size=(230, 110), name="Info")
        self.listmap.append("Info")
      
        # Archiv
        #ListBox
        self.list_archiv = wx.ListBox(panel, -1, pos=(30,365) , size=(226, 155), name="Archiv")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Archiv, self.list_archiv)
        self.listmap.append("Archiv")
      
        if self.debug: print("AfpChScreen Konstruktor")
    ## compose charter specific menu parts
    def create_specific_menu(self):
        # setup charter menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Neu", "")
        self.Bind(wx.EVT_MENU, self.On_Fahrt_neu, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Kopie", "")
        self.Bind(wx.EVT_MENU, self.On_MCharter_copy, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Bearbeiten", "")
        self.Bind(wx.EVT_MENU, self.On_Fahrt_aendern, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Zahlung", "")
        self.Bind(wx.EVT_MENU, self.On_Fahrt_ZahlungF, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Dokumente", "")
        self.Bind(wx.EVT_MENU, self.On_Fahrt_Ausgabe, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Einsatz", "")
        self.Bind(wx.EVT_MENU, self.On_Fahrt_EinF, mmenu)
        tmp_menu.Append(mmenu)
        self.menubar.Append(tmp_menu, "Charter")
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
      
    ## Eventhandler BUTTON - change address
    def On_Adresse_aendern(self,event):
        if self.debug: print("Event handler `On_Adresse_aendern'")
        changed = AfpLoad_DiAdEin_fromSb(self.globals, self.sb)
        if changed: self.Reload()
        event.Skip()
      
    ## Eventhandler BUTTON - payment
    def On_Fahrt_ZahlungF(self,event):
        if self.debug: print("Event handler `On_Fahrt_ZahlungF'")
        Charter = self.get_data()
        if Charter.is_payable():
            Ok, data = AfpLoad_DiFiZahl(Charter)
            if Ok: 
                data.view() # for debug
                data.store()
                self.Reload()
        event.Skip()

    ## Eventhandler BUTTON - selection
    def On_Fahrt_AuswF(self,event):
        if self.debug: print("Event handler `On_Fahrt_AuswF'!")
        #self.sb.set_debug()
        index = self.sb.identify_index().get_name()
        where = AfpSelectEnrich_dbname(self.sb.identify_index().get_where(), "FAHRTEN")
        #value = self.sb.get_string_value(index, True)
        value = self.sb.get_string_value(index)
        auswahl = AfpLoad_ChAusw(self.globals, index, value, where, True)
        if not auswahl is None:
            FNr = int(auswahl)
            if self.sb_filter: self.sb.select_where(self.sb_filter, "FahrtNr", "FAHRTEN")
            self.sb.select_key(FNr, "FahrtNr", "FAHRTEN")
            if self.sb_filter: self.sb.select_where("", "FahrtNr", "FAHRTEN")
            self.sb.set_index(index, "FAHRTEN", "FahrtNr")   
            self.Populate()
        #self.sb.unset_debug()
        event.Skip()

    ## Eventhandler BUTTON, MENU - document generation
    def On_Fahrt_Ausgabe(self,event):
        if self.debug and event: print("Event handler `On_Fahrt_Ausgabe'")
        Charter = self.get_data()
        zustand = Charter.get_string_value("Zustand").strip()
        prefix = "Charter " + zustand
        archiv = Charter.get_string_value("Art").strip()
        if archiv == "Tagesfahrt" : archiv = ""
        AfpLoad_DiReport(Charter, self.globals, None, zustand, prefix, archiv)
        if event:
            self.Reload()
            event.Skip()

    ## Eventhandler BUTTON, MENU - charter operation
    def On_Fahrt_EinF(self,event):
        if self.debug: print("Event handler `On_Fahrt_EinF'")
        Charter = self.get_data()
        zustand = Charter.get_string_value("Zustand")
        if self.einsatz and AfpCharter_isOperational(zustand):
            selection = Charter.get_selection("EINSATZ")
            ENr = None
            #print "AfpChScreen.On_Fahrt_EinF Einsatz:", self.einsatz
            #print "AfpChScreen.On_Fahrt_EinF:", selection.get_data_length(), selection, Charter.selections
            New = False
            if selection.get_data_length() == 0:
                New = AfpReq_Question("Kein Einsatz für diese Mietfahrt vorhanden,","neuen Einsatz erstellen?","Einsatz?")
                if New:
                    transfer = Charter.get_value("Art") == "Transfer"
                    print("AfpChScreen.On_Fahrt_EinF Art:", transfer)
                    if transfer: typ = "start"
                    else: typ = None
                    Einsatz = self.einsatz[1].AfpEinsatz(Charter.get_globals(), None, Charter.get_value("FahrtNr"), None, typ)  
                    Einsatz.store()                    
                    print("AfpChScreen.On_Fahrt_EinF Einsatz:", Einsatz)
                    if transfer:
                        Einsatz2 = self.einsatz[1].AfpEinsatz(Charter.get_globals(), None, Charter.get_value("FahrtNr"), None, "end") 
                        Einsatz2.store()
                        print("AfpChScreen.On_Fahrt_EinF Einsatz2:", Einsatz2)
                    selection.reload_data()
            if selection.get_data_length() > 0: 
                if selection.get_data_length() > 1:
                    liste = selection.get_value_lines("StellDatum,StellZeit,StellOrt,Bus")
                    ident = selection.get_values("EinsatzNr")
                    #print "Liste:", liste
                    #print ident
                    Zielort = Charter.get_string_value("Abfahrt") + " " + Charter.get_string_value("Nach") + " " +Charter.get_string_value("Zielort") 
                    ENr, Ok = AfpReq_Selection("Bitte Einsatz für Fahrt am " , Zielort + " auswählen.", liste, "Einsatzauswahl", ident)
                    ENr = ENr[0]
                else:
                    ENr = selection.get_value("EinsatzNr")
                    Ok = True
                if Ok: 
                    print("AfpChScreen.On_Fahrt_EinF EinsatzNr:", ENr)
                    Einsatz = self.einsatz[1].AfpEinsatz(Charter.get_globals(), ENr)
                    Ok = self.einsatz[0].AfpLoad_DiEinsatz(Einsatz, New)
        else:
            AfpReq_Info("'" + zustand + "' für eine Mietfahrt," , "es ist kein Einsatz möglich!")
        event.Skip()

    ## Eventhandler BUTTON, MENU - new charter entry \n
    # only complete new entries are created here, no copiing possible.
    def On_Fahrt_neu(self,event):   
        if self.debug: print("AfpChScreen Event handler `On_Fahrt_neu'")
        name = self.sb.get_string_value("Name.ADRESSE")
        text = "Bitte Auftraggeber für neue Mietfahrt auswählen:"
        KNr = AfpLoad_AdAusw(self.globals,"ADRESSE","NamSort",name, None, text)
        if KNr:
            Charter = AfpCharter(self.globals)
            Ok = AfpLoad_DiChEin(Charter, KNr)
            #print"On_Fahrt_Neu", Ok
            if Ok: 
                FNr = Charter.get_value("FahrtNr")
                self.load_direct(FNr)
                self.On_Fahrt_Ausgabe(None)
                self.Reload()
        event.Skip()  
        
    ## Eventhandler BUTTON , MENU - change charter
    def On_Fahrt_aendern(self,event):
        #self.sb.set_debug()      
        if self.debug: print("AfpChScreen Event handler `On_Fahrt_aendern'")
        changed = AfpLoad_DiChEin_fromSb(self.globals, self.sb)
        #print "AfpChScreen.On_Fahrt_aendern", changed
        if changed: 
            self.Reload()
            self.On_Fahrt_Ausgabe(None)
            self.Reload()
        #self.sb.unset_debug()
        event.Skip()

    ## Eventhandler COMBOBOX - filter
    def On_Anmiet_Filter(self,event):
        value = self.combo_Filter.GetValue()
        if self.debug: print("AfpChScreen Event handler `On_Anmiet_Filter'", value)      
        s_key = self.sb.get_value()
        filter = self.filtermap[value]
        if filter == "":
            if self.sb_filter:
                self.sb.select_where("")
                self.sb_filter = ""
        else:
            self.sb_filter = "Zustand LIKE \"" + filter + "\""
            self.sb.select_where(self.sb_filter)
        self.sb.select_key(s_key)
        self.CurrentData()
        event.Skip()
      
    ## Eventhandler COMBOBOX - sort index
    def On_Anmiet_Index(self,event):
        value = self.combo_Sortierung.GetValue()
        if self.debug: print("Event handler `On_Anmiet_Index'",value)
        index = self.indexmap[value]
        FNr = self.sb.get_value("FahrtNr")
        self.sb.set_index(index)
        self.sb.CurrentIndexName(index)
        self.CurrentData()
        event.Skip()
      
    ## Eventhandler ListBox - double click ListBox 'Archiv'
    def On_DClick_Archiv(self, event):
        if self.debug: print("Event handler `On_DClick_Archiv'", event)
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
                        print("WARNING in AfpChScreen: External file", filename, "does not exist, look in 'antiquedir'.") 
                        filename = Afp_addRootpath(self.globals.get_value("antiquedir"), file)
                    if Afp_existsFile(filename):
                        Afp_startFile(filename, self.globals, self.debug, True)
                    else:
                        print("WARNING in AfpChScreen: External file", filename, "does not exist!") 
        event.Skip()
      
    ## Eventhandler MENU - copy charter entry \n
    def On_MCharter_copy(self,event):   
        if self.debug: print("AfpChScreen Event handler `On_MCharter_copy'")
        data = self.get_data(True)
        charter = AfpCharter_copy(data)
        if charter:
            Ok = AfpLoad_DiChEin(charter, 0)
            if Ok: 
                FNr = charter.get_value("FahrtNr")
                self.load_direct(FNr)
                self.On_Fahrt_Ausgabe(None)
                self.Reload()
        event.Skip()  
   
    ## Eventhandler MENU - charte seach via address 
    def On_MAddress_search(self, event):
        if self.debug: print("AfpChScreen Event handler `On_MAddress_search'")
        name = self.sb.get_string_value("Name.ADRESSE")
        text = "Bitte Adresse auswählen für die Mietfahrten gesucht werden."
        KNr = AfpLoad_AdAusw(self.globals,"ADRESSE","NamSort",name, None, text)
        if KNr:
            rows, name = AfpAdresse_getListOfTable(self.globals, KNr, "FAHRTEN","Abfahrt,Art,Zielort,Preis,Zustand,FahrtNr")
            if rows:
                liste = []
                idents = []
                for row in rows:
                    entry = Afp_ArraytoLine(row, " ", 5)
                    liste.append(entry)
                    idents.append(row[5])
                text = "Bitte Mietfahrt von " + name + " auswählen:"
                FNr, ok = AfpReq_Selection(text, "", liste, "Mietfahrt Auswahl", idents)
                if ok:
                    self.load_direct(FNr)
                    self.Reload()
        event.Skip()

  ## Eventhandler MENU - touristk menu - not yet implemented!
    def On_MTouristik(self, event):
        print("Event handler `On_MTouristik' not implemented!")
        event.Skip()

    ## set database to show indicated charter
    # @param FNr - number of charter (FahrtNummer)
    def load_direct(self, FNr):
        value = self.combo_Sortierung.GetValue()
        index = self.indexmap[value]     
        self.sb.select_key(FNr,"FahrtNr","FAHRTEN")
        self.sb.set_index(index, "FAHRTEN", "FahrtNr")
        self.sb.CurrentIndexName(index)
        self.set_current_record()
     
    # routines to be overwritten
    ## load global veriables for this afp-module
    # (overwritten from AfpScreen) 
    def load_additional_globals(self):
        self.globals.set_value(None, None, "Einsatz")
    ## generate AfpCharter object from the present screen, overwritten from AfpScreen
    # @param complete - flag if all TableSelections should be generated
    def get_data(self, complete = False):
        return  AfpCharter(self.globals, None, self.sb, self.sb.debug, complete)
    ## set current record to be displayed 
    # (overwritten from AfpScreen) 
    def set_current_record(self):
        FNr = self.sb.get_value("FahrtNr")
        KNr = self.sb.get_value("KundenNr")
        print("AfpChScreen.set_current_record()", FNr,KNr)
        self.sb.select_key(KNr,"KundenNr","ADRESSE")
        return   
    ## set initial record to be shown, when screen opens the first time
    #overwritten from AfpScreen) 
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        FNr = 0
        #self.sb.set_debug()      
        self.sb.CurrentIndexName("KundenNr","ADRESSE")
        self.sb.CurrentIndexName("FahrtNr","FAHRTEN")      
        if origin:
            FNr = self.sb.get_value("Miet.ADRESSE")
            #FNr = self.globals.get_value("FahrtNr", origin)
        if FNr == 0: FNr = 1436
        #self.sb.select_key(FNr, "FahrtNr","FAHRTEN")      
        self.sb.CurrentIndexName("Abfahrt","FAHRTEN")
        self.sb.select_last() # for tests
        self.set_current_record() # needed?
        return
    ## supply list of graphic object where keydown events should not be traced.
    def get_no_keydown(self):
        return []
    ## get names of database tables to be opened for this screen
    # (overwritten from AfpScreen)
    def get_dateinamen(self):
        return ["FAHRTEN","FAHRTI","FAHRTEX","FAHRTVOR","ADRESSE","ARCHIV"]
    ## get rows to populate lists \n
    # default - empty, to be overwritten if grids are to be displayed on screen \n
    # possible selection criterias have to be separated by a "None" value
    # @param typ - name of list to be populated 
    def get_list_rows(self, typ):
        rows = []
        FahrtNr =  self.sb.get_value("FahrtNr")     
        select = ( "FahrtNr = %d")% FahrtNr
        if typ == "Archiv":
            select = ( "Tab = \"FAHRTEN\" AND TabNr = %d")% FahrtNr
            rawrow = self.mysql.select_strings("Datum,Gruppe,Bem,Extern",select,"ARCHIV")
            for row in rawrow:
                rows.append(row[0] + " " + row[1] + " " + row[2])
            rows.append(None)
            for row in rawrow:
                rows.append(row[3])           
        elif typ =="Info":
            rawrow = self.mysql.select("Datum,Abfahrtszeit,Adresse1,Adresse2",select,"FAHRTI")
            for row in rawrow:
                rows.append(AfpChInfo_genLine(row[0], row[1], row[3], row[2]))   
        elif typ =="Extra":
            rawrow = self.mysql.select_strings("Preis,Extra,noPausch",select,"FAHRTEX")
            for row in rawrow:
                preis = Afp_floatString(row[0])
                if row[2]: preis *= Afp_intString(row[2])
                rows.append(Afp_toString(preis) + " " + row[1] )
        return rows
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param typ - name of grid to be populated
    def get_grid_rows(self, typ):
        rows = []
        FahrtNr =  self.sb.get_value("FahrtNr")     
        select = ( "FahrtNr = %d")% FahrtNr
        if typ == "Archiv":
            select = ("Tab = \"FAHRTEN\" AND TabNr = %d")% FahrtNr
            rows = self.mysql.select("Datum,Gruppe,Bem,Extern",select,"ARCHIV")
        return rows

# end of class AfpChScreen
