#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseFiDialog
# AfpBaseFiDialog module provides the dialogs and appropriate loader routines needed for finance handling, \n
# payment userinteraction is performed here. \n
#
#   History: \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        14 Feb. 2014 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2015  afptech.de (Andreas Knoblauch)
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

import AfpDatabase
from AfpDatabase import AfpSuperbase
import AfpBaseRoutines
from AfpBaseRoutines import *
import AfpBaseDialog
from AfpBaseDialog import *
import AfpBaseFiRoutines
from AfpBaseFiRoutines import *


## deliver all ZahlSelectors for the actuel installed moduls
# @param globals - global variables inclusive database access
def AfpFinance_get_ZahlSelectors(globals = None):
    selectors = {}    
    mysql = globals.get_mysql()
    debug = globals.is_debug()
    finmods = []
    print "AfpFinance_get_ZahlSelectors:", globals.get_value("only-direct-payment")
    if not globals.get_value("only-direct-payment"):
        modules = Afp_ModulNames(globals)
        finmods = modules[1:]
    print "AfpFinance_get_ZahlSelectors:", finmods
    for mod in finmods:
        select = []
        if mod == "Charter":
            select.append(AfpFinance_CharterSelector(mysql, debug))
            select.append(AfpFinance_RechSelector(mysql, debug))
            select.append(AfpFinance_VerbindSelector(mysql, debug))
        elif mod == "Tourist" or mod == "Event":
            select.append(AfpFinance_EventStornoSelector(mysql, debug))
            if mod == "Tourist":   select.append(AfpFinance_TouristSelector(mysql, debug))
            else:   select.append(AfpFinance_EventSelector(mysql, debug))
            select.append(AfpFinance_RechSelector(mysql, debug))
            select.append(AfpFinance_VerbindSelector(mysql, debug))
        elif mod == "Faktura":
            select.append(AfpFinance_OrderSelector(mysql, debug))
            #select.append(AfpFinance_OfferSelector(mysql, debug))
            select.append(AfpFinance_InvoiceSelector(mysql, debug))
        for sel in select:
            selectors[sel.get_name()] = sel
    return selectors
        
## generate ZahlSelector for 'Charter' Modul
# @param mysql -  object for dadabase access
# @param debug - debug flag
def AfpFinance_CharterSelector(mysql, debug = False):
    name = "Mietfahrt"
    label = "&Mietfahrt"
    tablename = "FAHRTEN"
    felder = "Abfahrt,Preis,Zahlung,Zielort,Zustand,FahrtNr"
    filter_feld = "Zustand"
    filter =  ["Angebot","Rechnung","Storno Rechnung"]
    text = "Mietfahrt"
    return AfpZahlSelector(mysql, name, label, tablename, felder, filter_feld, filter, text, debug)
## generate ZahlSelector for invoice part of the 'Charter'  and  'Tourist' Modul
# @param mysql -  object for dadabase access
# @param debug - debug flag
def AfpFinance_RechSelector(mysql, debug = False):
    name = "Rechnung"
    label = "&Rechnung"
    tablename = "RECHNG"
    felder = "Datum,Zahlbetrag,Zahlung,Wofuer,Zustand,RechBetrag,RechNr"
    filter_feld = "Zustand"
    filter = ["offen"]
    text = "Rechnung"            
    return AfpZahlSelector(mysql, name, label, tablename, felder, filter_feld, filter, text, debug)
## generate ZahlSelector for incomimg invoice part of the 'Charter'  and  'Tourist' Modul
# @param mysql -  object for dadabase access
# @param debug - debug flag
def AfpFinance_VerbindSelector(mysql, debug = False):
    name = "Verbind"
    label = "&Verbindl."
    tablename = "Verbind"
    felder = "Datum,Zahlbetrag,Zahlung,Wofuer,Zustand,RechBetrag,RechNr"
    filter_feld = "Zustand"
    filter = ["offen"]
    text = "Verbindlichkeit"            
    return AfpZahlSelector(mysql, name, label, tablename, felder, filter_feld, filter, text, debug, True)
## generate ZahlSelector for invoice part of the  'Event' Modul, flavour 'Tourist'
# @param mysql -  object for dadabase access
# @param debug - debug flag
def AfpFinance_TouristSelector(mysql, debug = False):
    name = "Anmeldung"
    label = "&Anmeldung"
    tablename = "ANMELD"
    felder = "Abfahrt,Preis,Zahlung,Bez,Zustand,EventNr"
    filter_feld = "Zustand"
    filter =  ["Angebot","Rechnung","Storno Rechnung"]
    text = "Reiseanmeldung"
    return AfpZahlSelector(mysql, name, label, tablename, felder, filter_feld, filter, text, debug)
## generate ZahlSelector for invoice part of the  'Event' Modul
# @param mysql -  object for dadabase access
# @param debug - debug flag
def AfpFinance_EventSelector(mysql, debug = False):
    name = "Anmeldung"
    label = "&Anmeldung"
    tablename = "ANMELD"
    felder = "Abfahrt,Preis,Zahlung,Bez,Zustand,EventNr"
    filter_feld = "Zustand"
    filter =  ["Angebot","Rechnung","Storno Rechnung"]
    text = "Veranstalungsanmeldung"
    return AfpZahlSelector(mysql, name, label, tablename, felder, filter_feld, filter, text, debug)
## generate ZahlSelector for cancellation part of the  'Event' Modul, includong all flavours
# @param mysql -  object for dadabase access
# @param debug - debug flag
def AfpFinance_EventStornoSelector(mysql, debug = False):
    name = "Storno"
    label = "&Stornierung"
    tablename = "ANMELD"
    felder = "Abfahrt,Preis,Zahlung,Bez,Zustand,EventNr"
    filter_feld = "Zustand"
    filter =  ["Angebot","Rechnung","Storno Rechnung"]
    text = "Stornierung"
    return AfpZahlSelector(mysql, name, label, tablename, felder, filter_feld, filter, text, debug, True)
## generate ZahlSelector for invoice part of the  'Faktura' Modul
# @param mysql -  object for dadabase access
# @param debug - debug flag
def AfpFinance_InvoiceSelector(mysql, debug = False):
    name = "Invoice"
    label = "&Rechnung"
    tablename = "RECHNG"
    felder = "RechNr,Datum,Pos,Betrag,ZahlBetrag,Zahlung,Bem"
    #filter_feld = "Zustand"
    #filter =  ["offen","Mahnung","bezahlt"]
    text = "Rechnung"
    return AfpZahlSelector(mysql, name, label, tablename, felder, None, None, text, debug)
## generate ZahlSelector for offer part of the  'Faktura' Modul
# @param mysql -  object for dadabase access
# @param debug - debug flag
def AfpFinance_OfferSelector(mysql, debug = False):
    name = "Offer"
    label = "&Auftrag"
    tablename = "KVA"
    felder = "RechNr,Datum,Pos,Betrag,Bem"
    filter_feld = "Zustand"
    filter =  ["Auftrag"]
    text = "Auftrag"
    return AfpZahlSelector(mysql, name, label, tablename, felder, filter_feld, filter, text, debug)
## generate ZahlSelector for order part of the  'Faktura' Modul
# @param mysql -  object for dadabase access
# @param debug - debug flag
def AfpFinance_OrderSelector(mysql, debug = False):
    name = "Order"
    label = "&Bestellung"
    tablename = "BESTELL"
    felder = "RechNr,Datum, Pos,Betrag,ZahlBetrag,Bem"
    filter_feld = "Zustand"
    filter =  ["beglichen","erhalten","offen"]
    text = "Bestellung"
    return AfpZahlSelector(mysql, name, label, tablename, felder, filter_feld, filter, text, debug, True)
    
## class to select additional payment entries
class AfpZahlSelector(object):
   ## initialize payment class, \n
    # if avaulable attach modul to record financial transactions
    # @param mysql - database handle
    # @param name - name of button
    # @param label - label of button
    # @param tablename - name of database table
    # @param felder - name if columns given in the list
    # @param filter_feld - name of colums where a filter is involved
    # @param filter - filter value of the above column
    # @param text - text to be displayed in dialog
    # @param debug - debug flag
    # @param outgoing - flag if payment direction is outgoing
    def  __init__(self, mysql, name, label, tablename , felder, filter_feld, filter, text, debug = False, outgoing = False):
        self.mysql = mysql
        self.name = name
        self.label = label
        self.tablename = tablename
        self.felder = felder
        self.filter_feld = filter_feld
        self.filter = filter
        self.text = text
        self.outgoing = outgoing
        self.debug = debug
    ## get name
    def get_name(self):
        return self.name
    ## get button label
    def get_label(self):
        return self.label
    ## get flag if button should be enabled \n
    # if used without parameter returnvalue indicates if payment is incoming
    # @param out - input, if dialog is for incoming or outgoing payments
    def get_enable(self, out=False):
        if out == self.outgoing: return True
        return  False
    ## method to retrieve rows from database
    # @param KundenNr - address identifier for which entries should be found
    def get_rows(self, KundenNr):
         return Afp_selectSameKundenNr(self.mysql, self.tablename, KundenNr, self.debug, self.felder, self.filter_feld, self.filter)

## display and manipulation of payments
class AfpDialog_DiFiZahl(AfpDialog):
    ## initialise dialog
    def __init__(self, globals):
        self.globals = globals        
        self.selector_buttons= []
        self.is_full = False
        AfpDialog.__init__(self,None, -1, "")
        self.do_store = True
        self.allow_skonto = False
        if self.is_full:
            self.SetSize((570,400))
        else:
            self.SetSize((400,150))
        self.SetTitle("Zahlung")

    ## initialise graphic elements
    def InitWx(self):
        #self.InitWx_panel()
        self.InitWx_sizer()
            
    ## initialise graphic elements for full payment dialog
    def InitWx_panel(self):
        panel = wx.Panel(self, -1)
    #FOUND: DialogFrame "Von_Zahlung", conversion not implemented due to lack of syntax analysis!
        self.label_Vorname = wx.StaticText(panel, -1, label="Vorname.Adresse", pos=(26,32), size=(200,20), name="Vorname")
        self.labelmap["Vorname"] = "Vorname.ADRESSE"
        self.label_Name = wx.StaticText(panel, -1, label="Name.Adresse", pos=(26,54), size=(200,20), name="Name")
        self.labelmap["Name"] = "Name.ADRESSE"
        self.label_Strasse = wx.StaticText(panel, -1, label="Strasse.Adresse", pos=(26,76), size=(200,20), name="Strasse")
        self.labelmap["Strasse"] = "Strasse.ADRESSE"
        self.label_Plz = wx.StaticText(panel, -1, label="Plz.Adresse", pos=(26,98), size=(48,20), name="Plz")
        self.labelmap["Plz"] = "Plz.ADRESSE"
        self.label_Ort = wx.StaticText(panel, -1, label="Ort.Adresse", pos=(70,98), size=(200,20), name="Ort")
        self.labelmap["Ort"] = "Ort.ADRESSE"
        self.label_T_Bet_Zahlung = wx.StaticText(panel, -1, label="zu zahlen:", pos=(330,10), size=(110,20), name="T_Bet_Zahlung")
        self.label_Gesamt = wx.StaticText(panel, -1, label="Betrag_Zahlung$", pos=(460,10), size=(84,20), name="Gesamt")
        self.label_T_Anz_Zahlung = wx.StaticText(panel, -1, label="bereits bezahlt:", pos=(310,32), size=(130,20), name="T_Anz_Zahlung")
        self.label_Anzahlung = wx.StaticText(panel, -1, label="Anz_Zahlung$", pos=(460,32), size=(84,20), name="Anzahlung")
        self.label_TGut = wx.StaticText(panel, -1, label="Gutschrift:", pos=(310,54), size=(130,16), name="TGut")
        self.label_Gut = wx.StaticText(panel, -1, label="", pos=(460,54), size=(84,18), name="Gut")
        self.label_T_Zahl_Zahlung = wx.StaticText(panel, -1, label="&Betrag:", pos=(460,82), size=(84,20), name="T_Zahl_Zahlung")
        self.text_Zahlung = wx.TextCtrl(panel, -1, value="", pos=(460,102), size=(84,24), style=0, name="Zahlung")
        self.text_Zahlung.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_T_Aus_Zahlung = wx.StaticText(panel, -1, label="Aus&zug:", pos=(330,82), size=(110,20), name="T_Aus_Zahlung")
        self.text_Auszug = wx.TextCtrl(panel, -1, value="", pos=(330,102), size=(110,24), style=0, name="Auszug")
        self.text_Auszug.Bind(wx.EVT_KILL_FOCUS, self.On_Zahlung_Auszug)

        self.gen_sel_buttons(panel)

        self.list_Zahlungen = wx.ListBox(panel, -1, pos=(22,200), size=(530,100), name="Zahlungen")
        self.listmap.append("Zahlungen")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Zahlung_Delete, self.list_Zahlungen)
        self.button_ZListe_Zahlung = wx.Button(panel, -1, label="&Liste", pos=(14,320), size=(90,44), name="ZListe_Zahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Liste, self.button_ZListe_Zahlung)
        self.button_Manuell = wx.Button(panel, -1, label="Ma&nuell", pos=(120,320), size=(90,44), name="Manuell")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Manuell, self.button_Manuell)
        self.button_Info = wx.Button(panel, -1, label="&Info", pos=(226,320), size=(90,44), name="Info")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Info, self.button_Info)
        self.setWx(panel, [370, 320, 90, 44], [470, 320, 90, 44])

    ## initialise graphic elements for simple payment dialog
    def InitWx_sizer(self):
        self.label_Vorname = wx.StaticText(self, -1, label="Vorname.Adresse", name="Vorname")
        self.labelmap["Vorname"] = "Vorname.ADRESSE"
        self.label_Name = wx.StaticText(self, -1, label="Name.Adresse", name="Name")
        self.labelmap["Name"] = "Name.ADRESSE"
        self.label_Strasse = wx.StaticText(self, -1, label="Strasse.Adresse", name="Strasse")
        self.labelmap["Strasse"] = "Strasse.ADRESSE"
        self.label_Plz = wx.StaticText(self, -1, label="Plz.Adresse",  name="Plz")
        self.labelmap["Plz"] = "Plz.ADRESSE"
        self.label_Ort = wx.StaticText(self, -1, label="Ort.Adresse", name="Ort")
        self.labelmap["Ort"] = "Ort.ADRESSE"
        self.label_T_Bet_Zahlung = wx.StaticText(self, -1, label="zu zahlen:", name="T_Bet_Zahlung")
        self.label_Gesamt = wx.StaticText(self, -1, label="Betrag_Zahlung$", name="Gesamt")
        self.label_T_Anz_Zahlung = wx.StaticText(self, -1, label="bereits bezahlt:", name="T_Anz_Zahlung")
        self.label_Anzahlung = wx.StaticText(self, -1, label="Anz_Zahlung$",  name="Anzahlung")
        self.label_TGut = wx.StaticText(self, -1, label="Gutschrift:", name="TGut")
        self.label_Gut = wx.StaticText(self, -1, label="", name="Gut")
        self.label_T_Zahl_Zahlung = wx.StaticText(self, -1, label="&Betrag:", name="T_Zahl_Zahlung")
        self.text_Zahlung = wx.TextCtrl(self, -1, value="", style=0, name="Zahlung")
        self.text_Zahlung.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_T_Aus_Zahlung = wx.StaticText(self, -1, label="Aus&zug:", name="T_Aus_Zahlung")
        self.text_Auszug = wx.TextCtrl(self, -1, value="", style=0, name="Auszug")
        self.text_Auszug.Bind(wx.EVT_KILL_FOCUS, self.On_Zahlung_Auszug)
        
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.topleft_sizer = wx.BoxSizer(wx.VERTICAL)
        #self.topleft_sizer.AddSpacer(10)
        self.topleft_sizer.Add(self.label_Vorname,0,wx.EXPAND)
        self.topleft_sizer.Add(self.label_Name,0,wx.EXPAND)
        self.topleft_sizer.Add(self.label_Strasse,0,wx.EXPAND)
        self.topleftort_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.topleftort_sizer.Add(self.label_Plz,0,wx.EXPAND)
        self.topleftort_sizer.Add(self.label_Ort,0,wx.EXPAND)
        self.topleft_sizer.Add(self.topleftort_sizer,0,wx.EXPAND)

        self.topright_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.toprightleft_sizer = wx.BoxSizer(wx.VERTICAL)
        self.toprightleft_sizer.Add(self.label_T_Bet_Zahlung,0,wx.EXPAND)
        self.toprightleft_sizer.Add(self.label_T_Anz_Zahlung,0,wx.EXPAND)
        self.toprightleft_sizer.Add(self.label_TGut,0,wx.EXPAND)
        #self.toprightleft_sizer.Add(self.label_T_Aus_Zahlung,0,wx.EXPAND)
        #self.toprightleft_sizer.Add(self.text_Auszug,0,wx.EXPAND)
        self.toprightright_sizer = wx.BoxSizer(wx.VERTICAL)
        self.toprightright_sizer.Add(self.label_Gesamt,0,wx.EXPAND)
        self.toprightright_sizer.Add(self.label_Anzahlung,0,wx.EXPAND)
        self.toprightright_sizer.Add(self.label_Gut,0,wx.EXPAND)
        #self.toprightright_sizer.Add(self.label_T_Zahl_Zahlung,0,wx.EXPAND)
        #self.toprightright_sizer.Add(self.text_Zahlung,0,wx.EXPAND)
        self.topright_sizer.AddSpacer(10)        
        self.topright_sizer.Add(self.toprightleft_sizer,1,wx.EXPAND)
        self.topright_sizer.AddSpacer(10)
        self.topright_sizer.Add(self.toprightright_sizer,1,wx.EXPAND)
        self.topright_sizer.AddSpacer(10)
        self.top_sizer.AddSpacer(10)
        self.top_sizer.Add(self.topleft_sizer,1,wx.EXPAND)
        self.top_sizer.Add(self.topright_sizer,1,wx.EXPAND)
        self.top_sizer.AddSpacer(10)
        
        self.topentry_sizer=wx.BoxSizer(wx.HORIZONTAL) 
        self.topentryleft_sizer=wx.BoxSizer(wx.VERTICAL) 
        self.topentryleft_sizer.Add(self.label_T_Aus_Zahlung,0,wx.EXPAND)
        self.topentryleft_sizer.Add(self.text_Auszug,0,wx.EXPAND)
        self.topentryright_sizer=wx.BoxSizer(wx.VERTICAL) 
        self.topentryright_sizer.Add(self.label_T_Zahl_Zahlung,0,wx.EXPAND)
        self.topentryright_sizer.Add(self.text_Zahlung,0,wx.EXPAND)
        self.topentry_sizer.AddSpacer(10)
        self.topentry_sizer.Add(self.topentryleft_sizer,1,wx.EXPAND)        
        self.topentry_sizer.AddSpacer(10)
        self.topentry_sizer.Add(self.topentryright_sizer,1,wx.EXPAND)        
        self.topentry_sizer.AddSpacer(10)

        self.gen_sel_buttons(self)
        self.button_ZListe_Zahlung = wx.Button(self, -1, label="&Liste", name="ZListe_Zahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Liste, self.button_ZListe_Zahlung)
        
        self.uppermid_sizer=wx.BoxSizer(wx.HORIZONTAL) 
        self.uppermid_sizer.AddSpacer(10)   
        self.mid_sizer=wx.BoxSizer(wx.HORIZONTAL) 
        self.mid_sizer.AddSpacer(10)   
        if self.is_full:
            for button in self.selector_buttons:
                self.uppermid_sizer.Add(button,0,wx.EXPAND)        
                self.uppermid_sizer.AddSpacer(10)   
            self.list_Zahlungen = wx.ListBox(self, -1, name="Zahlungen")
            self.listmap.append("Zahlungen")
            self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Zahlung_Delete, self.list_Zahlungen)
            self.mid_sizer.Add(self.list_Zahlungen,1,wx.EXPAND)        
            self.mid_sizer.AddSpacer(10)   
        self.bottom_sizer=wx.BoxSizer(wx.HORIZONTAL) 
        self.bottom_sizer.AddSpacer(10)   
        self.bottom_sizer.Add(self.button_ZListe_Zahlung,0,wx.EXPAND) 
        if self.is_full:        
            self.button_Manuell = wx.Button(self, -1, label="Ma&nuell", name="Manuell")
            self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Manuell, self.button_Manuell)
            self.button_Info = wx.Button(self, -1, label="&Info", name="Info")
            self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Info, self.button_Info)
            self.bottom_sizer.AddSpacer(10)   
            self.bottom_sizer.Add(self.button_Manuell,0,wx.EXPAND)        
            self.bottom_sizer.AddSpacer(10)   
            self.bottom_sizer.Add(self.button_Info,0,wx.EXPAND)        
            self.setWx(self.bottom_sizer,[1, 3, 1], [0, 3, 1]) 
        else:
            self.button_Ko = wx.Button(self, -1, label="&Abbruch", name="Ko")
            self.Bind(wx.EVT_BUTTON, self.On_CEdit, self.button_Ko)
            self.button_Bar = wx.Button(self, -1, label="&Bar", name="Bar")
            self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Bar, self.button_Bar)
            self.button_Ok = wx.Button(self, -1, label="&Ok", name="Ok")
            self.Bind(wx.EVT_BUTTON, self.On_Button_Ok, self.button_Ok)
            self.bottom_sizer.AddStretchSpacer(1)
            self.bottom_sizer.Add(self.button_Ko,3,wx.EXPAND)
            self.bottom_sizer.AddStretchSpacer(1)
            self.bottom_sizer.Add(self.button_Bar,3,wx.EXPAND)
            self.bottom_sizer.AddStretchSpacer(1)
            self.bottom_sizer.Add(self.button_Ok,3,wx.EXPAND)
            self.bottom_sizer.AddStretchSpacer()

        self.sizer=wx.BoxSizer(wx.VERTICAL)  
        self.sizer.AddSpacer(10)     
        self.sizer.Add(self.top_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)   
        self.sizer.Add(self.topentry_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)   
        if self.is_full:
            self.sizer.Add(self.uppermid_sizer,0,wx.EXPAND)
            self.sizer.AddSpacer(10)     
            self.sizer.Add(self.mid_sizer,1,wx.EXPAND)
            self.sizer.AddSpacer(10)     
        self.sizer.Add(self.bottom_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)    
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    ## gernerate selector buttons to add entries to payment list
    # @param panel - object where buttons should be placed (panel, self)
    def gen_sel_buttons(self, panel):
        selectors = AfpFinance_get_ZahlSelectors(self.globals)
        out = False
        if selectors:
            ind = -1
            for sel in selectors:
                selector = selectors[sel]
                if not selector.get_enable():
                    ind += 1                
                    button = wx.Button(panel, -1, label=selector.get_label(), pos=(20 + ind*100,160), size=(92,34), name=selector.get_name())
                    self.selector_buttons.append(button)
                    self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Select, self.selector_buttons[ind])
                    self.selector_buttons[ind].Enable(selector.get_enable(out))
            for sel in selectors: 
                selector = selectors[sel]
                if selector.get_enable():
                    ind += 1                
                    button = wx.Button(panel, -1, label=selector.get_label(), pos=(20 + ind*100,160), size=(92,34), name=selector.get_name())
                    self.selector_buttons.append(button)
                    self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Select, self.selector_buttons[ind])
                    self.selector_buttons[ind].Enable(selector.get_enable(out))
        if self.selector_buttons:
            self.is_full = True
        #print "AfpZahlung.gen_sel_buttons:", selectors, self.is_full
    ## attaches data to this dialog, invokes population of widgets \n
    # overwritten from AfpDialog
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        super(AfpDialog_DiFiZahl, self).attach_data( data, new, editable)
        self.has_finance = data.has_finance()
        if not self.has_finance:
            self.text_Auszug.Enable(False)
    ## population routine for labels \n
    # overwritten from AfpDialog to fill 'Zahlung'-labels if list does not exist
    def Pop_label(self):
        super(AfpDialog_DiFiZahl, self).Pop_label()
        if not self.is_full:
            self.Pop_Zahl_Label()
    ## populate the 'Zahlung' list, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_Zahlungen(self):
        self.Pop_Zahl_Label()
        liste = self.data.get_display_list()
        self.list_Zahlungen.Clear()
        self.list_Zahlungen.InsertItems(liste, 0)
    ## populate 'Zahlung'-labels
    def Pop_Zahl_Label(self):
        gesamt = self.data.get_preis()
        anz = self.data.get_anzahlung()
        gut = self.data.get_gutschrift()
        self.label_Gesamt.SetLabel(gesamt)
        self.label_Anzahlung.SetLabel(anz)
        self.label_Gut.SetLabel(gut)
    ## execution routine for pushing the Ok button \n
    # distribute and enter all payments into the database
    def execute_Ok(self):
        value = Afp_fromString(self.text_Zahlung.GetValue())
        Auszug = self.text_Auszug.GetValue()
        direct_cash = self.globals.get_value("allow-direct-cash-payment")
        if direct_cash:
            if not value: 
                value = self.data.get_payment_left() 
            if not Auszug:
                self.set_cash_auszug()  
        if Afp_isEps(value):
            if direct_cash or self.check_auszug(Auszug):
                self.data.distribute_payment(value)
                if self.do_store: self.data.store()
                self.Ok = True
        print "AfpDialog_DiFiZahl.execute_Ok:", Auszug, value, direct_cash, self.do_store, self.Ok
    ## set flag to avoid writing into database when leaving the dialog \n
    # execution should then be performed by the caller
    def do_not_store(self):
        self.do_store = False
    ## check if statement of account (Auszug) exists, if not create one
    # @param auszug - identifier of statement of account to be checked
    def check_auszug(self, auszug):
        if not auszug:
            if self.has_finance:
                Ok = AfpReq_Question("Barzahlung?","","Zahlung")
            else:
                 Ok = True
            if Ok:
                auszug = self.data.get_cash_auszug()
                self.text_Auszug.SetValue(auszug)
        if auszug:
            checked = self.data.check_auszug(auszug)
            if not checked:
                datum, Ok = AfpReq_Date("Bitte Datum für Auszug '".decode("UTF-8") + auszug + "' angeben,", "", "", "", True)
                if Ok: 
                    self.set_auszug(auszug, Afp_fromString(datum)) 
                    checked = True
            return checked
        else:
            return False
    ## set statement of account for cash ("Bar") payment
    def set_cash_auszug(self):
         self.set_auszug(self.data.get_cash_auszug(), self.data.globals.today())
    ## create an new statement of account 
    # @param auszug - identifier of statement of account to be created
    # @param datum - date when statement has become valid
    def set_auszug(self, auszug, datum):
        if auszug:
            self.data.set_auszug(auszug, datum)
    ## invoke selection of another participent of this payment
    # @param tablename - name of database taable, where selection should be made
    def select_selection(self, tablename):
        liste = []
        ident = []
        KundenNr = self.data.get_value("KundenNr")
        if tablename == "FAHRTEN":
            felder = "Abfahrt,Preis,Zahlung,Zielort,Zustand,FahrtNr"
            filter_feld = "Zustand"
            filter =  ["Angebot","Rechnung","Storno Rechnung"]
            text = "Mietfahrt"
        elif tablename == "RECHNG":
            felder = "Datum,Zahlbetrag,Zahlung,Wofuer,Zustand,RechBetrag,RechNr"
            filter_feld = "Zustand"
            #filter_feld = None
            filter = ["offen"]
            text = "Rechnung"
        rows = Afp_selectSameKundenNr(self.data.get_mysql(), tablename, KundenNr, self.debug, felder, filter_feld, filter)
        for row in rows:
            if row[1] is None and tablename == "RECHNG": row[1] = row[5]
            if row[1]:
                if row[2]: row[2] = row[1] - row[2]
                else: row[2] = row[1]
            liste.append(Afp_ArraytoLine(row, " ", 5))
            ident.append(row[-1])
        value,ok = AfpReq_Selection("Bitte " + text + " für Zahlung auswählen!","",liste, text + " für Zahlung", ident)
        if ok and value:
            self.data.add_selection(tablename, value)
            self.Pop_Zahlungen()
            
    ## invoke selection of another participent of this payment, triggerd by lanlename
    # @param tablename - name of database table, where selection should be made
    def select_selection_by_name(self, tablename):
        if tablename in self.selectors:
            selector = self.selectors[tablename]
            liste = []
            ident = []
            KundenNr = self.data.get_value("KundenNr")
            rows = selector.get_rows(self.data.get_mysql(), KundenNr, self.debug)
            for row in rows:
                if row[1] is None and tablename == "RECHNG": row[1] = row[5]
                if row[1]:
                    if row[2]: row[2] = row[1] - row[2]
                    else: row[2] = row[1]
                liste.append(Afp_ArraytoLine(row, " ", 5))
                ident.append(row[-1])
            value,ok = AfpReq_Selection("Bitte " + text + " für Zahlung auswählen!","",liste, text + " für Zahlung", ident)
            if ok and value:
                self.data.add_selection(selector.get_tablename(), value)
                self.Pop_Zahlungen()

    # Event Handlers 
    ## event handler when cursor leaves the 'statement of account' (Auszug) textbox
    def On_Zahlung_Auszug(self,event):
        if self.debug: print "Event handler `On_Zahlung_Auszug'"
        print "Event handler `On_Zahlung_Auszug'"
        Auszug = self.text_Auszug.GetValue()
        self.check_auszug(Auszug)
        event.Skip()

    ##Eventhandler BUTTON - add an entry to this payment, depending on name of the button \n
    def On_Zahlung_Select(self,event):
        if self.debug: print "Event handler `On_Zahlung_select'"
        object = event.GetEventObject()
        name = object.GetName()
        self.select_selection_by_name(name)
        event.Skip()

    ##Eventhandler BUTTON - remove an entry from this payment \n
    def On_Zahlung_Delete(self,event):
        if self.debug: print "Event handler `On_Zahlung_Delete'"
        index = self.list_Zahlungen.GetSelections()[0] 
        if index > 0:
            self.data.remove_selection(index)
            self.Pop_Zahlungen()
        event.Skip()

    ##Eventhandler BUTTON - show list of financial payment transaction \n
    def On_Zahlung_Liste(self,event):
        if self.debug: print "Event handler `On_Zahlung_Liste'"
        if self.data.finance:
            liste = {}
            for data in self.data.selected_list:
                ident = data.get_identifier()
                select = "Von = \"" + ident + "\" AND (Art = \"Zahlung\" OR Art = \"Zahlung in\")"
                felder = "Datum,GktName,Betrag,Beleg,Bem"
                rows = self.data.mysql.select(felder, select, "BUCHUNG")
                zahlungen = []
                for row in rows:
                    zahlungen.append(Afp_ArraytoLine(row))
                liste[ident] = zahlungen
                print "AfpDialog_DiFiZahl.On_Zahlung_Liste:", liste
            Afp_printToInfoFile(self.data.globals, liste)
        else:
            AfpReq_Info("Finanzmodul nicht installiert!","Funktion steht nicht zur Verfügung!".decode("UTF-8"))
        event.Skip()

    ##Eventhandler BUTTON - allow manuel distribution of this payment \n
    # not implemented yet
    def On_Zahlung_Manuell(self,event):
        print "Event handler `On_Zahlung_Manuell' not implemented!"
        self.On_Zahlung_Bar(event)
        event.Skip()

   ##Eventhandler BUTTON - allow manuel distribution of this payment \n
    # not implemented yet
    def On_Zahlung_Bar(self,event):
        if self.debug: print "Event handler `On_Zahlung_Bar'"
        self.data.globals.set_value("allow-direct-cash-payment", 1)
        self.execute_Ok()
        event.Skip()
        self.EndModal(wx.ID_OK)

    ##Eventhandler BUTTON - show payment info \n
    def On_Zahlung_Info(self,event):
        if self.debug: print "Event handler `On_Zahlung_Info'"
        if self.data.finance:
            liste = {}
            for data in self.data.selected_list:
                payment = {}
                payment = self.data.finance.add_payment_data(payment, data) 
                liste[payment["Von"]] = [Afp_toString(payment["Gegenkonto"]) + " "  + data.get_name()]
            Afp_printToInfoFile(self.data.globals, liste)
        else:
            AfpReq_Info("Finanzmodul nicht installiert!","Funktion steht nicht zur Verfügung!".decode("UTF-8"))
        event.Skip()

## loader routine for dialog DiFiZahl \n
# @param data - initial data to be attached to this dialog
# @param multi - if given, additional entries will be retrieved from database with identic values in this column(s)
# @param do_not_store - flag if writing to database should be skipped
def AfpLoad_DiFiZahl(data, multi = None, do_not_store = False):
    DiZahl = AfpDialog_DiFiZahl(data.globals)
    Zahl = AfpZahlung(data, multi) 
    DiZahl.attach_data(Zahl, False, True)
    if do_not_store: DiZahl.do_not_store()
    DiZahl.ShowModal()
    Ok = DiZahl.get_Ok()
    data = DiZahl.get_data()
    DiZahl.Destroy()
    return Ok, data

