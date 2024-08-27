#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpCharter.AfpChDialog
# AfpChDialog module provides the dialogs and appropriate loader routines needed for charter handling
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        15 Jan. 2015 - add auto selection- Andreas.Knoblauch@afptech.de \n
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


from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpBaseDialog import *
from AfpBase.AfpBaseDialogCommon import *
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_DiAdEin_fromKNr
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

from AfpCharter.AfpChRoutines import *

## select a 'fahrtinfo'  or select a new enty is desired \n
# return index in AfpSQLTableSelection or 'None' in case nothing is selected
# @param fahrtinfo_selection - AfpSQLTableSelection holding the fahrtinfo data
# @param allow_new - add line to allow the selection that a new entry is desired
def AfpChInfo_selectEntry(fahrtinfo_selection, allow_new = False):
    index = None
    rows = fahrtinfo_selection.get_values()
    liste = []
    if allow_new: liste.append(" --- Neue Fahrtinformation eingeben --- ")
    for row in rows:
        zeile = AfpChInfo_genLine(row[5], row[2], row[3], row[1])
        liste.append(zeile)
    value,ok = AfpReq_Selection("Bitte Fahrtinformation auswählen!","",liste,"Fahrtinformation")
    if ok:
        index = liste.index(value)
        if allow_new: index -= 1
    return index

## create a copy of the actuel charter may be made completely or partly
# @param data - charter data to be copied
def AfpCharter_copy(data):
    text1 = "Soll eine Kopie der aktuellen Fahrt erstellt werden?"
    text2 = "Wenn Ja, bitte auswählen was übernommen werden soll."
    liste = ["Adresse","Kontakt","Fahrtinfo","Fahrtextra","Fahrtdaten"]
    keep_flags = AfpReq_MultiLine(text1, text2, "Check", liste, "Mietfahrt kopieren?", 350)
    new_address = True
    if keep_flags: new_address = not keep_flags[0]
    KNr = None
    if new_address:
        name = data.get_value("Name.Adresse")
        text = "Bitte Auftraggeber für neue Mietfahrt auswählen:"
        KNr = AfpLoad_AdAusw(data.get_globals(),"ADRESSE","NamSort",name, None, text)
    if keep_flags or KNr:
        data.set_new(KNr, keep_flags)
        return data
    else:
        return None

## dialog for selection of charter data \n
# selects an entry from the fahrten table
class AfpDialog_ChAusw(AfpDialog_Auswahl):
    ## initialise dialog
    def __init__(self):
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.typ = "Fahrtenauswahl"
        self.datei = "FAHRTEN"
        self.modul = "Charter"
    ## get the definition of the selection grid content \n
    # overwritten for "Charter" use
    def get_grid_felder(self): 
        Felder = [["Abfahrt.Fahrten",10], 
                            ["Zustand.Fahrten", 8], 
                            ["Art.Fahrten", 7], 
                            ["SortNr.Fahrten", 10], 
                            ["Zielort.Fahrten",30], 
                            ["Name.Fahrten",20], 
                            ["Kontakt.Fahrten",15], 
                            ["FahrtNr.Fahrten",None]] # Ident column
        return Felder
    ## invoke the dialog for a new entry \n
    # overwritten for "Charter" use
    def invoke_neu_dialog(self, globals, eingabe, filter):
        superbase = AfpSuperbase.AfpSuperbase(globals, debug)
        if eingabe is None: eingabe = globals.get_value("standard-location", "Adresse")
        superbase.open_datei("FAHRTEN")
        superbase.CurrentIndexName("Ort")
        superbase.select_key(eingabe)
        return AfpLoad_DiChEin_fromSb(globals, superbase, eingabe)      
 
## loader routine for charter selection dialog 
# @param globals - global variables including database connection
# @param index - column which should give the order
# @param value -  if given,initial value to be searched
# @param where - if given, filter for search in table
# @param ask - flag if it should be asked for a string before filling dialog
def AfpLoad_ChAusw(globals, index, value = "", where = None, ask = False):
    result = None
    Ok = True
    if ask:
        sort_list = AfpCharter_getOrderlistOfTable(globals.get_mysql(), index)
        value, index, Ok = Afp_autoEingabe(value, index, sort_list, "Mietfahrt")
        print("AfpLoad_ChAusw index:", index, value, Ok)
    if Ok:
        DiAusw = AfpDialog_ChAusw()
        #print Index, value, where
        text = "Bitte Mietfahrt auswählen:"
        DiAusw.initialize(globals, index, value, where, text)
        DiAusw.ShowModal()
        result = DiAusw.get_result()
        #print result
        DiAusw.Destroy()
    elif Ok is None:
        # flag for direct selection
        result = Afp_selectGetValue(globals.get_mysql(), "FAHRTEN", "FahrtNr", index, value)
        #print result
    return result      

## allows the display and manipulation of a charter entry
class AfpDialog_DiChEin(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        self.distance = None
        self.choicevalues = {}
        self.change_data = False
        self.changed_label = False
        self.zahl_data = None
        AfpDialog.__init__(self,None, -1, "")
        self.lock_data = True
        self.active = None
        self.SetSize((574,410))
        self.SetTitle("Mietfahrt")
        self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
    
    ## initialise graphic elements
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.label_Zustand = wx.StaticText(panel, -1, label="Zustand.Fahrten", pos=(8,8), size=(140,20), name="Zustand")
        self.labelmap["Zustand"] = "Zustand.FAHRTEN"
        self.label_Datum = wx.StaticText(panel, -1, label="Datum.Fahrten", pos=(150,8), size=(60,20), name="Datum")
        self.labelmap["Datum"] = "Datum.FAHRTEN"
        self.label_Vorname = wx.StaticText(panel, -1, label="Vorname.Adresse", pos=(12,54), size=(200,16), name="Vorname")
        self.labelmap["Vorname"] = "Vorname.ADRESSE"
        self.label_Nachname = wx.StaticText(panel, -1, label="Name.Adresse", pos=(12,72), size=(200,16), name="Nachname")
        self.labelmap["Nachname"] = "Name.ADRESSE"
        self.label_Tel = wx.StaticText(panel, -1, label="Telefon.Adresse", pos=(12,92), size=(200,16), name="Tel")
        self.labelmap["Tel"] = "Telefon.ADRESSE"
        self.label_T_Abfahrt = wx.StaticText(panel, -1, label="Ab&fahrt:", pos=(10,136), size=(52,16), name="T_Abfahrt")
        self.text_Abfahrt = wx.TextCtrl(panel, -1, value="", pos=(90,130), size=(120,24), style=0, name="Abfahrt")
        self.vtextmap["Abfahrt"] = "Abfahrt.FAHRTEN"
        self.text_Abfahrt.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Dauer)
        self.label_T_Ende = wx.StaticText(panel, -1, label="Fahrt&ende:", pos=(240,136), size=(76,16), name="T_Ende")
        self.text_Ende = wx.TextCtrl(panel, -1, value="", pos=(320,130), size=(120,24), style=0, name="Ende")
        self.vtextmap["Ende"] = "Fahrtende.FAHRTEN"
        self.text_Ende.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Dauer)
        self.text_Von = wx.TextCtrl(panel, -1, value="", pos=(50,160), size=(160,24), style=0, name="Von")
        self.textmap["Von"] = "Abfahrtsort.FAHRTEN"
        self.text_Von.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Strecke)
        self.text_Nach = wx.TextCtrl(panel, -1, value="", pos=(280,160), size=(160,24), style=0, name="Nach")
        self.textmap["Nach"] = "Zielort.FAHRTEN"
        self.text_Nach.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Strecke)
        self.label_T_Pers = wx.StaticText(panel, -1, label="Pe&rsonen:", pos=(340,194), size=(60,18), name="T_Pers")
        self.text_Pers = wx.TextCtrl(panel, -1, value="", pos=(400,190), size=(40,24), style=0, name="Pers")
        self.vtextmap["Pers"] = "Personen.FAHRTEN"
        self.text_Pers.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_T_Km = wx.StaticText(panel, -1, label="&Km:", pos=(10,194), size=(24,16), name="T_Km")
        self.text_Km = wx.TextCtrl(panel, -1, value="", pos=(30,190), size=(40,24), style=0, name="Km")
        self.vtextmap["Km"] = "Km.FAHRTEN"      
        self.label_T_Preis = wx.StaticText(panel, -1, label="&Preis:", pos=(290,318), size=(60,18), name="T_Preis")
        self.text_Km.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)           
        self.text_Preis = wx.TextCtrl(panel, -1, value="", pos=(354,316), size=(84,24), style=0, name="Preis")
        self.vtextmap["Preis"] = "Preis.FAHRTEN"
        self.text_Preis.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
      
        self.label_T_KmFrei = wx.StaticText(panel, -1, label="Frei", pos=(110,194), size=(20,16), name="T_KmFrei")
        self.text_KmFrei = wx.TextCtrl(panel, -1, value="", pos=(140,190), size=(30,24), style=0, name="KmFrei")
        self.text_KmFrei.SetEditable(False)
        self.text_KmFrei.SetBackgroundColour(self.readonlycolor)   
        self.label_T_KmAusland = wx.StaticText(panel, -1, label="Ausland", pos=(220,194), size=(40,16), name="T_KmAusland")
        self.text_KmAusland = wx.TextCtrl(panel, -1, value="", pos=(280,190), size=(40,24), style=0, name="KmAusland")
        self.textmap["KmAusland"] = "Ausland.FAHRTEN"      
        self.text_VonT = wx.TextCtrl(panel, -1, value="", pos=(10,160), size=(40,24), style=0, name="VonT")
        self.textmap["VonT"] = "Von.FAHRTEN"
        self.text_VonT.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.text_NachT = wx.TextCtrl(panel, -1, value="", pos=(240,160), size=(40,24), style=0, name="NachT")
        self.textmap["NachT"] = "Nach.FAHRTEN"
        self.text_NachT.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_T_Ausstatt = wx.StaticText(panel, -1, label="Ausstattung.Fahrten", pos=(10,220), size=(430,32), name="Ausstatt")
        self.labelmap["Ausstatt"] = "Ausstattung.FAHRTEN"
        self.label_T_Vorgang = wx.StaticText(panel, -1, label="Vor&gang:", pos=(228,42), size=(60,18), name="T_Vorgang")
        #FOUND: DialogComboBox "Vorgang", conversion not implemented due to lack of syntax analysis!
        self.label_T_Kontakt = wx.StaticText(panel, -1, label="K&ontakt:", pos=(234,66), size=(54,18), name="T_Kontakt")
        self.text_Kontakt = wx.TextCtrl(panel, -1, value="", pos=(290,64), size=(150,24), style=0, name="Kontakt")
        self.textmap["Kontakt"] = "Kontakt.FAHRTEN"
        self.text_Kontakt.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_ReVorname = wx.StaticText(panel, -1, label="", pos=(228,90), size=(80,18), name="ReVorname")
        self.labelmap["ReVorname"] = "Vorname.RechAdresse"
        self.conditioned_display["ReVorname"] = "KundenNr.RECHNG != KundenNr.FAHRTEN"
        self.label_ReName = wx.StaticText(panel, -1, label="", pos=(315,90), size=(120,18), name="ReName")
        self.labelmap["ReName"] = "Name.RechAdresse"
        self.conditioned_display["ReName"] = "KundenNr.RECHNG != KundenNr.FAHRTEN"
        self.choice_Art = wx.Choice(panel, -1,  pos=(290,6), size=(150,24),  choices=AfpCharter_getArtList(),  name="CArt")      
        self.choicemap["CArt"] = "Art.FAHRTEN"
        self.Bind(wx.EVT_CHOICE, self.On_CArt, self.choice_Art)
        self.label_T_Gebucht = wx.StaticText(panel, -1, label="Gebucht:", pos=(290,260), size=(60,18), name="T_Gebucht")
        self.label_Auftrag = wx.StaticText(panel, -1, label="Auftrag.Fahrten", pos=(354,260), size=(84,18), name="Auftrag")
        self.labelmap["Auftrag"] = "Auftrag.FAHRTEN"
        self.label_T_Zahl = wx.StaticText(panel, -1, label="Zahlung:", pos=(290,278), size=(60,18), name="T_Zahl")
        self.label_Zahldat = wx.StaticText(panel, -1, label="ZahlDat.Fahrten", pos=(354,278), size=(84,18), name="ZahlDat")
        self.labelmap["ZahlDat"] = "ZahlDat.FAHRTEN"
        self.label_Zahl = wx.StaticText(panel, -1, label="Zahlung.Fahrten", pos=(354,296), size=(80,18), name="Zahl")
        self.labelmap["Zahl"] = "Zahlung.FAHRTEN"
        self.label_proPers = wx.StaticText(panel, -1, label="pro Pers:", pos=(290,342), size=(60,18), name="proPers")
        self.label_PersPreis = wx.StaticText(panel, -1, label="", pos=(354,342), size=(80,18), name="PersPreis")
        self.labelmap["PersPreis"] = "PersPreis.FAHRTEN"
        self.list_Extras = wx.ListBox(panel, -1, pos=(8,260), size=(272,82), name="Extras")      
        self.listmap.append("Extras")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Fahrt_Extras, self.list_Extras)
        self.label_T_Extra = wx.StaticText(panel, -1, label="Extra:", pos=(150,342), size=(40,18), name="T_Extra")
        self.label_Extra = wx.StaticText(panel, -1, label="Extra.Fahrten", pos=(196,342), size=(66,18), name="Extra")
        self.labelmap["Extra"] = "Extra.FAHRTEN"
        self.choice_Zustand = wx.Choice(panel, -1,  pos=(460,6), size=(100,24),  choices=AfpCharter_getZustandList(True),  name="CZustand")      
        self.choicemap["CZustand"] = "Zustand.FAHRTEN"
        self.Bind(wx.EVT_CHOICE, self.On_CZustand, self.choice_Zustand)
        self.button_Adresse = wx.Button(panel, -1, label="A&dresse", pos=(460,40), size=(100,24), name="Adresse")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_aendern, self.button_Adresse)
        self.button_BKontakt = wx.Button(panel, -1, label="&Kontakt", pos=(460,64), size=(100,24), name="BKontakt")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_Kontakt, self.button_BKontakt)
        self.button_BRechAd = wx.Button(panel, -1, label="&Rechnung", pos=(460,88), size=(100,24), name="BRechAd")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_RechAd, self.button_BRechAd)
        self.button_Datum = wx.Button(panel, -1, label="&Datum", pos=(460,130), size=(100,24), name="Datum")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_Datum, self.button_Datum)
        self.button_Ausstatt = wx.Button(panel, -1, label="A&usstattung", pos=(460,154), size=(100,24), name="Ausstatt")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_Ausstatt, self.button_Ausstatt)
        self.button_Info = wx.Button(panel, -1, label="&Info", pos=(460,178), size=(100,24), name="Info")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_Info, self.button_Info)
        self.button_Text = wx.Button(panel, -1, label="Te&xt", pos=(460,202), size=(100,24), name="Text")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_Text, self.button_Text)
        self.button_Neu = wx.Button(panel, -1, label="Ko&pie", pos=(460,250), size=(100,30), name="Neu")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_Neu, self.button_Neu)
        self.button_Zahlung = wx.Button(panel, -1, label="&Zahlung", pos=(460,280), size=(100,30), name="Zahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Fahrt_Zahl, self.button_Zahlung)

        self.setWx(panel, [460, 310, 100, 30], [460, 340, 100, 30]) # set Edit and Ok widgets
   
    ## attach data to dialog and invoke population of the graphic elements
    # @param data - AfpCharter object to hold the data to be displayed
    # @param KNr - if given data is reset and intialized with the address indicated by this number \n
    #                         set KNr = 0 to directly edit given data without reste
    def attach_data(self, data, KNr = None):
        self.data = data
        self.debug = self.data.debug
        self.new = not KNr is None
        if KNr: self.data.set_new(KNr)
        if self.new: self.choice_Edit.SetSelection(1)
        self.Populate()
        self.Set_Editable(self.new, False)
   
    ## read values from dialog and invoke writing to database
    def store_database(self):
        self.Ok = False
        data = {}
        if self.new: 
            data["Art"] =  self.choice_Art.GetStringSelection()
        if self.changed_label:
            data["Ausstattung"] = self.label_T_Ausstatt.GetLabel()
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        for entry in self.choicevalues:
            name = entry.split(".")[0]
            data[name] = self.choicevalues[entry]
        if data or self.change_data:
            if "Preis" in data or "Personen" in data:
                data["PersPreis"] = Afp_fromString(self.label_PersPreis.GetLabel())
            if self.becomes_payable():
                data["Auftrag"] = self.data.get_globals().get_value("today")
            transaction_needed = False
            print("self.needs_transaction:", self.needs_transaction(), self.initial_transaction())
            if self.needs_transaction():
                if self.initial_transaction():
                    transaction_needed = True
                else:
                    transaction_needed = self.check_transaction(data) 
            print("self.had_transaction:", self.had_transaction())
            if self.had_transaction():
                if transaction_needed or self.is_storno(): self.cancel_transaction()
            print("store_database:", data)
            if data: self.data.set_data_values(data)
            print("transaction needed:", transaction_needed)
            if transaction_needed:
                print("self.initial_transaction:", self.initial_transaction())
                if self.initial_transaction(): self.add_invoice()
                else: self.syncronise_invoice()
            # write data to database
            #self.data.view() # show data for debugging
            self.data.store()
            # execute financial transactions
            if transaction_needed:
                self.execute_transaction(self.initial_transaction())
            # execute payment
            if self.zahl_data:
                self.zahl_data.store()
            self.new = False          
            self.Ok = True              
        self.changed_text = []   
        self.choicevalues = {}
      
    # handling routines
    ## financial transaction needed for selection in dialog
    def needs_transaction(self):
        transaction = False
        zustand = self.choice_Zustand.GetStringSelection()
        if AfpCharter_needsTransaction(zustand): transaction = True
        return transaction
    ## financial transaction needed for data loaded into dialog
    def had_transaction(self):
        transaction = False
        zustand = self.label_Zustand.GetLabel()
        if AfpCharter_needsTransaction(zustand): transaction = True
        return transaction
    ## payment possible for selection in dialog
    def is_payable(self):
        payable = False
        zustand = self.choice_Zustand.GetStringSelection()
        if AfpCharter_isPayable(zustand):payable = True
        return payable 
    ##  payment not possible for loaded  data, but possible for selection in dialog
    def becomes_payable(self):
        payable = False
        zustand = self.label_Zustand.GetLabel()
        if not AfpCharter_isPayable(zustand) and self.is_payable(): payable = True
        return payable
    ## this charter will be canceled
    def is_storno(self):
        zustand = self.choice_Zustand.GetStringSelection()
        if zustand == "Storno": return True     
        return False
    ## when storing this data initial financial transactions are needed
    def initial_transaction(self):
        transaction = False
        if self.needs_transaction() and not self.had_transaction(): transaction = True
        return transaction
    ## check if relevant data for financial transactions has changed
    # @param data - data to be checked, not yet inserted into the internal data object \n
    # additionally the internal data object will be checked for relevant changes
    def check_transaction(self, data):
        # checks data if accounting may be needed for changed fields
        print("AfpDialog_DiChEin.check_transaction", data)
        bookable = False
        if "Preis" in data: bookable = True 
        elif "Extra" in data: bookable = True 
        elif self.change_data:
            extras = self.data.get_selection("FAHRTEX")
            if extras.has_changed("Preis"): bookable = True
            elif extras.has_changed("Inland"): bookable = True
        return bookable
    ## financial transactions have to be executed
    # @param initial - flag if no transaction have been tracked up to now
    def execute_transaction(self, initial):
        print("AfpDialog_DiChEin.execute_transaction")
        self.data.execute_financial_transaction(initial)
    ## all financial transactions have to be cancelled
    def cancel_transaction(self):
        print("AfpDialog_DiChEin.cancel_transaction")
        self.data.cancel_financial_transaction()
    ## an internal invoice dataset has to be created 
    def add_invoice(self):
        print("AfpDialog_DiChEin.add_invoice")
        self.data.add_invoice()
    ## the internal invoice dataset has to be syncronised
    def syncronise_invoice(self):
        print("AfpDialog_DiChEin.syncronise_invoice")
        self.data.syncronise_invoice()
    
    ## generate durance of trip \n
    # output will be [hours on startday, complete days, hours on endday]
    def get_durance(self):
        tage = 0
        start = self.text_Abfahrt.GetValue()
        if start: start = Afp_ChDatum(start)
        ende= self.text_Ende.GetValue()
        if ende: ende = Afp_ChDatum(ende)
        if start and ende:
            sdat = Afp_fromString(start)
            edat = Afp_fromString(ende)
            tage = Afp_diffDays(sdat, edat) + 1
            if tage > 32000:  # > 90 years!
                tage = -1
        elif start:
            tage = 1
        return start, ende, tage
    ## check if durance and 'Art' selector coincident \n
    # try to syncronise
    # @param choice_prio - give the choice selector priority during syncronisation
    # @param reset_end - end date may be resetted for one day operation
    def ch_durance(self, choice_prio = False, reset_end = False):
        start, ende, tage = self.get_durance()
        select = self.choice_Art.GetCurrentSelection()
        if tage < 1:  
            if self.debug: print("AfpDialog_DiChEin.ch_durance: days < 0, reset enddate!")
            if choice_prio:
                if select == 0: ende = start
                else: ende = Afp_toString(Afp_addDaysToDate(Afp_fromString(start), 1))
        if tage == 1:
            if choice_prio: 
                if select > 0: 
                    ende = Afp_toString(Afp_addDaysToDate(Afp_fromString(start), 1))
                elif reset_end: 
                    ende = start
            elif select > 0: select = 0 # MTF, Transfer -> Tagesfahrt
        elif tage > 1:
            if choice_prio:
                if select == 0: ende = start
            elif select == 0: select = 1 # Tagesfahrt -> MTF
        self.text_Abfahrt.SetValue(start)
        self.text_Ende.SetValue(ende)
        self.choice_Art.SetSelection(select)   
        self.ch_km()
    ## toggle distance setting due to 'Art' selection
    def ch_km(self):
        if self.distance:
            select = self.choice_Art.GetCurrentSelection()
            if select == 2:
                self.text_Km.SetValue(Afp_toString(2*self.distance))
            else:
                self.text_Km.SetValue(Afp_toString(self.distance))
        
    ## Population routine for the dialog
    # the parent populate (AfpDialog.Populate) will also be called
    def Populate(self):
        super(AfpDialog_DiChEin, self).Populate()
        self.set_distance()
        self.set_extraPreis()
    ## populate the 'Extra' list, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_Extras(self):
        pers = Afp_fromString(self.text_Pers.GetValue())
        rows = self.data.get_value_rows("FAHRTEX", "Info,Preis,Extra,noPausch")
        liste = ["--- Extraleistung hinzufügen ---"]
        #print "Pop_Extras:", rows
        for row in rows:
            preis = Afp_floatString(row[1])
            if row[3]: preis *= Afp_intString(row[3])
            liste.append(Afp_toString(row[0]) + Afp_toString(preis).rjust(10) + " " + Afp_toString(row[2]))
        self.list_Extras.Clear()
        self.list_Extras.InsertItems(liste, 0)
    
    ## set internal distance value from input \n
    # the value is assumed to be the distance between start and destination and the way back ,\n
    # for a 'Transfer' this way has to be made twice 
    def set_distance(self):
        km = self.text_Km.GetValue()
        if km:
            km = int(km)
            if self.choice_Art.GetCurrentSelection() < 2:
                self.distance = km
            else:
                self.distance = km/2
        else:
            self.distance = None
    ## set the price per person
    def set_proPers(self):
        pers = self.text_Pers.GetValue()
        preis = self.text_Preis.GetValue()
        if preis and pers:
            value = float(preis)/int(pers)
            self.label_PersPreis.SetLabel(Afp_toString(value))
        else:
            self.label_PersPreis.SetLabel("")
    ## set the price for the extras entered \n
    # this routine also takes care of the 'per person' extras, when the number of persons has been changed
    def set_extraPreis(self):
        extra = Afp_floatString(self.label_Extra.GetLabel())
        newextra = 0.0
        newpers = Afp_intString(self.text_Pers.GetValue())
        if not newpers: newpers = 1
        rows = self.data.get_value_rows("FAHRTEX","Preis,noPausch,Info")
        for row in rows:
            if row[2] and len(row[2]) > 1 and row[2][1] == "#":
                rowextra = 0.0
            else:
                rowextra = Afp_floatString(row[0])
            if row[1]: 
                rowextra = newpers*rowextra
                data = {"noPausch": Afp_toString(newpers)}
                self.data.set_data_values(data, "FAHRTEX", rows.index(row))
            newextra += rowextra
        diff = newextra - extra 
        #print "set_extraPreis Extra:", extra, newextra, diff, Afp_isEps(diff), pers, newpers
        if Afp_isEps(diff):
            self.data.set_value("Extra.FAHRTEN", newextra)
            preis = Afp_floatString(self.text_Preis.GetValue())
            newpreis = preis + diff
            self.text_Preis.SetValue(Afp_toString(newpreis))
            if not "Preis" in self.changed_text: self.changed_text.append("Preis")
            self.Pop_Extras()
        self.set_proPers()
        self.label_Extra.SetLabel(Afp_toString(newextra))
    
    ## activate or deactivate changeable widgets \n
    # this method also calls the parent method
    # @param ed_flag - flag if widgets have to be activated (True) or deactivated (False)
    # @param lock_data - flag if data has to be locked, used in parent method 
    def Set_Editable(self, ed_flag, lock_data = None):
        super(AfpDialog_DiChEin, self).Set_Editable(ed_flag, lock_data)
        self.button_BRechAd.Enable(self.needs_transaction())
        self.button_Zahlung.Enable(self.is_payable())      
        if ed_flag: 
            if self.data.is_accountable(): self.choice_Art.Enable(False)
        else:  
            self.choicevalues = {}
            
    ## event handler when window is activated
    # @param event - event which initiated this action   
    def On_Activate(self,event):
         if self.active is None:
            if self.debug: print("Event handler `On_Activate'")
            self.active = True
            if self.new and self.data.get_globals().get_value("edit-date-first","Charter"): 
                self.On_Fahrt_Datum()
                if self.text_Abfahrt.GetValue() == "":
                    self.text_Abfahrt.SetFocus()

    ## event handler when cursor leave textbox
    # @param event - event which initiated this action   
    def On_KillFocus(self,event):
        object = event.GetEventObject()
        name = object.GetName()
        if not name in self.changed_text: self.changed_text.append(name)
        if name == "Km": self.set_distance()
        if name == "Pers": self.set_extraPreis()
        if name == "Preis": self.set_proPers()
  
    ## event handler when one of the durance relevant textboxes is left 
    # @param event - event which initiated this action   
    def On_Check_Dauer(self,event):
        if self.debug: print("Event handler `On_Check_Dauer'")
        object = event.GetEventObject()
        name = object.GetName()
        self.ch_durance(True, name == "Ende")
        self.On_KillFocus(event)
        event.Skip()

    ## event handler when start or destination textbox is left \n
    # only invokes the On_KillFocus method \n
    # may be used for connection to a route map
    # @param event - event which initiated this action   
    def On_Check_Strecke(self,event):
        if self.debug: print("Event handler `On_Check_Strecke'")        
        object = event.GetEventObject()
        name = object.GetName()
        if name == "Von" and self.text_Von.GetValue() == "":
            self.text_Von.SetValue(self.data.get_globals().get_string_value("standard-location","Adresse"))
        self.On_KillFocus(event)
        event.Skip()

    ## event handler for click into the 'Extra' listbox \n
    # invokes the AfpDialog_DiMfEx dialog to edit additional tour features
    # @param event - event which initiated this action   
    def On_Fahrt_Extras(self,event):
        if self.debug: print("Event handler `On_Fahrt_Extras'")
        index = self.list_Extras.GetSelections()[0] - 1
        pers =Afp_fromString(self.text_Pers.GetValue())
        extra =Afp_fromString(self.label_Extra.GetLabel())
        if not extra: extra = 0.0
        if index < 0: 
            index = None
            exval = 0.0
        else:
            exval = Afp_fromString(self.data.get_value_rows("FAHRTEX","Preis", index))
        #print "On_Fahrt_Extra:",index, extra
        data = AfpLoad_DiMfEx(self.data, index, pers)
        if data: 
            self.data = data
            self.change_data = True
            self.Pop_Extras()
            self.set_extraPreis()
        event.Skip()

    ##Eventhandler BUTTON - change address \n
    # invokes the AfpDialog_DiAdEin dialog
    # @param event - event which initiated this action   
    def On_Adresse_aendern(self,event):
        if self.debug: print("Event handler `On_Adresse_aendern'")
        KNr = self.data.get_value("KundenNr.ADRESSE")
        changed = AfpLoad_DiAdEin_fromKNr(self.data.get_globals(), KNr)
        if changed: self.Populate()
        event.Skip()

    ##Eventhandler BUTTON - change contact address \n
    # invokes the address selection dialog
    # @param event - event which initiated this action   
    def On_Fahrt_Kontakt(self,event):
        if self.debug: print("Event handler `On_Fahrt_Kontakt'") 
        name = self.data.get_value("Name.Kontakt")
        if name is None: name = self.data.get_value("Name.ADRESSE")
        text = "Bitte Kontaktadresse für diese Mietfahrt auswählen:"
        KNr = AfpLoad_AdAusw(self.data.get_globals(),"ADRESSE","NamSort",name, None, text)
        if KNr:
            self.data.set_value("KontaktNr",KNr)
            self.data.reload_selection("Kontakt")
            self.data.set_kontakt_name()
            if not "Kontakt" in self.changed_text: self.changed_text.append("Kontakt")
            self.Populate()         
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()
      
    ## Eventhandler BUTTON - change invoice address,
    # only available whe an invoice is attached to this charter \n
    # invokes the address selection dialog
    # @param event - event which initiated this action   
    def On_Fahrt_RechAd(self,event):
        if self.debug: print("Event handler `On_Fahrt_RechAd'")
        if self.data.get_value("RechNr"):
            name = self.data.get_value("Name.RechAdresse")
            if name is None: name = self.data.get_value("Name.ADRESSE")
            text = "Bitte Rechnungsadresse für diese Mietfahrt auswählen:"
            KNr = AfpLoad_AdAusw(self.data.get_globals(),"ADRESSE","NamSort",name, None, text)
            if KNr:
                self.data.set_value("KundenNr.RECHNG",KNr)
                self.data.reload_selection("RechAdresse")
                self.change_data = True
                self.Populate()         
                self.choice_Edit.SetSelection(1)
                self.Set_Editable(True)
        event.Skip()

    ##  Eventhandler BUTTON  for new entry \n
    # a copy of the actuel charter may be made completely or partly
    # @param event - event which initiated this action   
    def On_Fahrt_Neu(self,event):
        if self.debug: print("Event handler `On_Fahrt_Neu'")
        new_data = AfpCharter_copy(self.data)
        if new_data:
            self.new = True
            self.data = new_data
            self.Populate()
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()

    ##  Eventhandler BUTTON  for a payment \n
    # @param event - event which initiated this action   
    def On_Fahrt_Zahl(self,event):
        if self.debug: print("Event handler `On_Fahrt_Zahl'")
        Ok, data = AfpLoad_DiFiZahl(self.data, None, True)
        if Ok:
            self.zahl_data = data
            data.view() # for debug
            self.data = data.get_data()
            self.change_data = True
            self.Populate()
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()

    ## Eventhandler BUTTON - graphic pick for dates 
    # @param event - event which initiated this action   
    def On_Fahrt_Datum(self,event = None):
        if self.debug: print("Event handler `On_Fahrt_Datum'")
        start = self.text_Abfahrt.GetValue()
        if start: start = Afp_ChDatum(start)
        ende= self.text_Ende.GetValue()
        if ende: ende = Afp_ChDatum(ende)
        x, y = self.button_Datum.ScreenPosition
        x += self.button_Datum.GetSize()[0]
        y += self.button_Datum.GetSize()[1]
        dates = AfpReq_Calendar((x, y), [start, ende],  "Fahrtdaten Mietfahrt", False, ["Abfahrt", "0:Fahrtende"])
        if dates:
            self.text_Abfahrt.SetValue(dates[0])
            self.text_Ende.SetValue(dates[1])
            self.ch_durance(False)
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
            if not "Abfahrt" in self.changed_text: self.changed_text.append("Abfahrt")
            if not "Ende" in self.changed_text: self.changed_text.append("Ende")
        if event: event.Skip()

    ## Eventhandler BUTTON - change bus configuration desired- not yet implemented! 
    # @param event - event which initiated this action   
    def On_Fahrt_Ausstatt(self,event):
        if self.debug: print("Event handler `On_Fahrt_Ausstatt'")
        liste =  ["Klima-Anlage","DvD-Spieler", "WC","Anhänger"]
        result = AfpReq_MultiLine("Bitte Ausstattung der Fahrzeuges auswählen,", 
                                            "folgende Ausstattunsmerkmale stehen zur Verfügung:", 
                                            "Check", liste, "Ausstattung")
        if result:
            aus = ""
            for i in range(len(result)):
                if result[i]:
                    aus += liste[i].split("-")[0] + ", "
            aus = aus.strip()
            if aus: aus = aus[:-1]
            self.label_T_Ausstatt.SetLabel(aus)
            self.changed_label = True
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()

    ##  Eventhandler BUTTON  change charter information \n
    # arrival- or departure- -times and -.adresses may be set here for different fixpoints of the journey
    # @param event - event which initiated this action   
    def On_Fahrt_Info(self,event):
        if self.debug: print("Event handler `On_Fahrt_Info'")
        index = AfpChInfo_selectEntry(self.data.get_selection("FAHRTI"), True)
        print(index)
        if not index is None:
            if index < 0: index = None
            data = AfpLoad_DiMInfo(self.data, index)
            if data: 
                self.data = data
                self.change_data = True
                self.choice_Edit.SetSelection(1)
                self.Set_Editable(True)
        event.Skip()

    ##  Eventhandler BUTTON  change charter freetext infos \n
    # additional informations or remarks may be stored here
    # @param event - event which initiated this action   
    def On_Fahrt_Text(self,event):
        if self.debug: print("Event handler `On_Fahrt_Text'")
        oldtext = self.data.get_string_value("Brief.FAHRTEN")
        text, ok = Afp_editExternText(oldtext, self.data.get_globals())
        print("AfpDialog_DiChEin.On_Fahrt_Text:",ok, text)
        if ok: 
            self.data.set_value("Brief.FAHRTEN", text)
            self.change_data = True
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()

    ##  Eventhandler CHOICE  change the 'art' of charter \n
    # available values are 'Tagesfahrt' (day trip), MTF (Mehrtagesfahrt, serveral day journey) or 'Transfer'
    # @param event - event which initiated this action   
    def On_CArt(self,event):
        if self.debug: print("Event handler `On_CArt'")  
        select = self.choice_Art.GetCurrentSelection()
        self.choicevalues["Art.FAHRTEN"] = self.choice_Art.GetString(select)
        self.ch_durance(True)
        self.ch_km()
        event.Skip()  
    ##  Eventhandler CHOICE  change the state (zustand) of the charter \n
    # depending on the state, payment is available, an invoice is created and financial transactions are recorded
    # @param event - event which initiated this action   
    def On_CZustand(self,event):
        if self.debug: print("Event handler `On_CZustand'")
        select = self.choice_Zustand.GetCurrentSelection()
        liste = AfpCharter_getZustandList()
        zustand = self.data.get_value("Zustand.FAHRTEN")
        if select == 0 or select > liste.index(zustand):
            if self.is_editable():
                wert = self.choice_Zustand.GetString(select)
            if select == 0: wert += " " + zustand
            self.choicevalues["Zustand.FAHRTEN"] = wert
            if self.needs_transaction():
                self.button_BRechAd.Enable(True)
            else:
                self.button_BRechAd.Enable(False)
            if self.is_payable():
                self.button_Zahlung.Enable(True)
            else:
                self.button_Zahlung.Enable(False)
        else:
            self.choice_Zustand.SetStringSelection(zustand)   
        event.Skip()  
    ## execution in case the OK button ist hit - to be overwritten in derived class
    def execute_Ok(self):
        self.store_database()
# end of class AfpDialog_DiChEin

## loader routine for dialog DiChEin \n
# @param Charter - AfpCharter data to be altered
# @param eingabe - if given, address identification number to generate a new charter entry
def AfpLoad_DiChEin(Charter, eingabe = None):
    DiChEin = AfpDialog_DiChEin(None)
    DiChEin.attach_data(Charter, eingabe)
    DiChEin.ShowModal()
    Ok = DiChEin.get_Ok()
    DiChEin.Destroy()
    return Ok  
## loader routine for dialog DiChEin according to the given superbase object \n
# @param globals - global variables holding database connection
# @param sb - AfpSuperbase object, where data can be taken from
# @param eingabe - if given, address identification number to generate a new charter entry
def AfpLoad_DiChEin_fromSb(globals, sb, eingabe = None):
    Charter = AfpCharter(globals, None, sb, sb.debug, False)
    return AfpLoad_DiChEin(Charter, eingabe)
## loader routine for dialog DiChEin according to the given charter identification number \n
# @param globals - global variables holding database connection
# @param fahrtnr -  identification number of charter to be filled into dialog
def AfpLoad_DiChEin_fromFNr(globals, fahrtnr):
    Charter = AfpCharter(globals, fahrtnr)
    return AfpLoad_DiChEin(Charter)

## Dialog for additional tour features
class AfpDialog_DiMfEx(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        self.index = None
        self.plus = False
        self.personen = None
        self.choicevalues = {}
        AfpDialog.__init__(self,None, -1, "")
        self.SetSize((446,146))
        self.SetTitle("Fahrtextra")
   
    ## initialise graphic elements
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.text_Extra = wx.TextCtrl(panel, -1, value="", pos=(20,20), size=(324,24), style=0, name="Extra")
        self.textmap["Extra"] = "Extra"
        self.text_Extra.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.text_Preis = wx.TextCtrl(panel,-1, value="", pos=(350,20), size=(80,24), style=0, name="Preis")
        self.vtextmap["Preis"] = "Preis"
        self.text_Preis.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.choice_Sicht = wx.Choice(panel, -1, pos=(20,55), size=(100,24), choices=["versteckt", "sichtbar"], style=0, name="Sicht")
        self.choice_Sicht.SetSelection(0)      
        self.Bind(wx.EVT_CHOICE, self.On_CSicht, self.choice_Sicht)
        self.choice_Indi = wx.Choice(panel, -1, pos=(150,55), size=(100,24), choices=["Pauschal", "pro Person"], style=0, name="Indi")
        self.choice_Indi.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.On_CIndi, self.choice_Indi)
        self.choice_Umst = wx.Choice(panel, -1, pos=(274,55), size=(156,24), choices=["mit Umsatzsteuer", "Umsatzsteuer-frei"], style=0, name="Umst")
        self.choice_Umst.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.On_CUmst, self.choice_Umst)
        self.button_Loeschen = wx.Button(panel, -1, label="&Löschen", pos=(150,100), size=(100,30), name="Loeschen")
        self.Bind(wx.EVT_BUTTON, self.On_Loeschen, self.button_Loeschen)     
        self.setWx(panel, [20, 100, 100, 30], [330, 100, 100, 30])
   
    ## execution in case the OK button ist hit - to be overwritten in derived class   
    def execute_Ok(self):
        self.store_data()

    ## attach data to dialog and invoke population of the graphic elements
    # @param data - AfpCharter object to hold the data to be displayed
    # @param index - if given, index of row of additional data to be displayed in data.selections["FahrtEx"]
    # @param pers - number of persons set on this tour, needed for calculation of the per person prices
    def attach_data(self, data, index, pers):
        self.data = data
        self.debug = self.data.debug
        self.index = index
        self.new = (index is None)
        self.plus = self.data.is_accountable()
        self.personen = pers
        self.Populate()
        self.Set_Editable(self.new, True)
        if self.new:
            self.choice_Edit.SetSelection(1)

    ## read values from dialog and invoke writing into data         
    def store_data(self):
        self.Ok = False
        data = {}
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        for entry in self.choicevalues:
            data[entry] = self.choicevalues[entry]
        if data:
            if self.new: data = self.complete_data(data)
            self.data.set_data_values(data, "FAHRTEX", self.index)
            self.Ok = True
        self.changed_text = []   
        self.choicevalues = {}  
    ## initialise new empty data with all necessary values \n
    # or the other way round, complete new data entries with all needed input
    # @param data - data top be completed
    def complete_data(self, data):
        self.choicevalues = {}
        self.On_CSicht()
        self.On_CIndi()
        self.On_CUmst()
        for entry in self.choicevalues:
            data[entry] = self.choicevalues[entry]  
        for entry in self.textmap:
            TextBox = self.FindWindowByName(entry)
            wert = TextBox.GetValue()
            name = entry.split(".")[0]
            data[name] = wert 
        #print "AfpDialog_MfEx.complete_data()",data         
        return data

    ## Population routine for the dialog overwritten from parent \n
    # due to special choice settings
    def Populate(self):
        if self.index is None:
            self.index = self.data.get_value_length("FAHRTEX") 
            #print "AfpDialog_DiMfEx: no index given - NEW index created:", self.index
        if self.index < self.data.get_value_length("FAHRTEX"):
            row = self.data.get_value_rows("FAHRTEX","Info,Preis,Inland,Extra,noPausch", self.index)[0]
            #print "AfpDialog_DiMfEx index:", self.index
            #print row
            self.text_Extra.SetValue(Afp_toString(row[3]))
            self.text_Preis.SetValue(Afp_toString(row[1]))
            if row[0] and row[0][0] == "*":
                self.choice_Sicht.SetSelection(1)
            else:
                self.choice_Sicht.SetSelection(0)
            if row[2] == "A":
                self.choice_Umst.SetSelection(1)
            else:
                self.choice_Umst.SetSelection(0)
            if row[4]:
                self.choice_Indi.SetSelection(1)
            else:
                self.choice_Indi.SetSelection(0)
   
    ## activate or deactivate changeable widgets \n
    # this method also calls the parent method
    # @param ed_flag - flag if widgets have to be activated (True) or deactivated (False)
    # @param initial - flag if data has to be locked, used in parent method 
    def Set_Editable(self, ed_flag, initial = False):
        super(AfpDialog_DiMfEx, self).Set_Editable(ed_flag, initial)
        if ed_flag: 
            self.choice_Sicht.Enable(True)
            self.choice_Indi.Enable(True)
            self.choice_Umst.Enable(True)
            self.button_Loeschen.Enable(True)
        else:  
            self.choice_Sicht.Enable(False)
            self.choice_Indi.Enable(False)
            self.choice_Umst.Enable(False)
            self.button_Loeschen.Enable(False)
            self.choicevalues = {}
            self.Populate()
         
     # Event Handlers 
    ##  Eventhandler CHOICE  change the state of visablity in output \n
    # depending on the state this entry may be listed as a separate line in the output
    # @param event - event which initiated this action   
    def On_CSicht(self,event = None):
        if self.debug: print("Event handler `On_CSicht'")
        select = self.choice_Sicht.GetCurrentSelection()
        if self.plus: plus = "+"
        else: plus = " "
        if select == 1:
            self.choicevalues["Info"] = "*" + plus
        else:
            self.choicevalues["Info"] = " " + plus
        if event: event.Skip()  
    ##  Eventhandler CHOICE  flag if price has to be interpreted on a per person base \n
    # toggelling this flag, the price will be multiplied by or devided through the number of persons
    # @param event - event which initiated this action   
    def On_CIndi(self,event = None):
        if self.debug: print("Event handler `On_CIndi'")
        select = self.choice_Indi.GetCurrentSelection()
        pers = self.personen
        if not pers: pers = 1
        if select == 1:
            self.choicevalues["noPausch"] = Afp_toString(pers)
            if event:
                preis = Afp_fromString(self.text_Preis.GetValue())
                if preis and pers:
                    preis = float(preis)/pers
                    self.text_Preis.SetValue(Afp_toFloatString(preis))
        else:
            self.choicevalues["noPausch"] = ""
            if event:
                preis = Afp_fromString(self.text_Preis.GetValue())
                if preis and pers:
                    preis = float(preis)*pers
                    self.text_Preis.SetValue(Afp_toFloatString(preis))
        if event: event.Skip()  
    ##  Eventhandler CHOICE  toggle tax choice \n
    # depending on the choice, the price will be assumed to be tax relevant or not
    # @param event - event which initiated this action   
    def On_CUmst(self,event = None):
        if self.debug: print("Event handler `On_CUmst'")
        select = self.choice_Umst.GetCurrentSelection()
        if select == 1:
            self.choicevalues["Inland"] = "A"
        else:
            self.choicevalues["Inland"] = "I"
        if event: event.Skip()

    ##  Eventhandler BUTTON  delete this line from list in calling dialog, \n
    # resp. mark it to be ignored for price calculation
    # @param event - event which initiated this action   
    def On_Loeschen(self,event):
        if self.debug: print("Event handler `On_Loeschen'", self.index)
        self.changed_text = []
        self.choicevalues = {} 
        if not self.new:
            info = self.data.get_value_rows("FAHRTEX","Info",self.index)[0][0]
            print("On_loeschen:", info, len(info), info[1])
            plus = False
            left = " "
            if info and len(info) > 1:
                if info[1] == "+": plus = True
                left = info[0]
            print(plus, self.plus)
            if plus == self.plus:
                self.data.delete_row("FAHRTEX", self.index)
            else:
                self.choicevalues["Info.FAHRTEX"] = left + "#"
            self.store_data()
            self.Ok = True
        event.Skip()  
        self.EndModal(wx.ID_CANCEL)
   
## loader routine for dialog DiMfEx 
# @param data - AfpCharter object to hold the data to be displayed
# @param index - if given, index of row of additional data to be displayed in data.selections["FahrtEx"], \n
# otherwise a new row has to be added
# @param pers - number of persons set on this tour, needed for calculation of the per person prices
def AfpLoad_DiMfEx(data, index, pers):
    dialog = AfpDialog_DiMfEx(None)
    dialog.attach_data(data, index, pers)
    dialog.ShowModal()
    Ok = dialog.get_Ok()
    data = dialog.get_data()
    dialog.Destroy()
    if Ok:
        return data
    else:
        return None
      
##Dialog for additional tour data information
class AfpDialog_DiMfInfo(AfpDialog):
    def __init__(self, *args, **kw):   
        self.index = None
        self.choice_changed = False
        AfpDialog.__init__(self,None, -1, "")
        self.SetSize((446,176))
        self.SetTitle("Fahrtinfo")

    ## initialise graphic elements
    def InitWx(self):
        panel = wx.Panel(self, -1)
        choices_Richtung, choices_Zeitpunkt = AfpChInfo_getDirSelValues()
        self.choice_Richtung = wx.Choice(panel, -1, pos=(20,20), size=(80,24), choices=choices_Richtung, style=0, name="Richtung")
        self.choice_Richtung.SetSelection(0)      
        self.Bind(wx.EVT_CHOICE, self.On_ChangeChoice, self.choice_Richtung)
        self.choice_Zeitpunkt = wx.Choice(panel, -1, pos=(120,20), size=(60,24), choices=choices_Zeitpunkt, style=0, name="Zeitpunkt")
        self.choice_Zeitpunkt.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.On_ChangeChoice, self.choice_Zeitpunkt)
        self.label_Datum = wx.StaticText(panel, -1, label="&Datum:", pos=(205,24), size=(40,18), name="LDatum")
        self.text_Datum = wx.TextCtrl(panel,-1, value="", pos=(250,20), size=(80,24), style=0, name="Datum")
        self.vtextmap["Datum"] = "Datum"
        self.text_Datum.Bind(wx.EVT_KILL_FOCUS, self.On_ChangeDatum)
        self.label_Zeit = wx.StaticText(panel, -1, label="&Zeit:", pos=(340,24), size=(20,18), name="LZeit")
        self.text_Zeit = wx.TextCtrl(panel,-1, value="", pos=(370,20), size=(60,24), style=0, name="Zeit")
        self.vtextmap["Zeit"] = "Abfahrtszeit"
        self.text_Zeit.Bind(wx.EVT_KILL_FOCUS, self.On_ChangeZeit)
        self.text_Adresse = wx.TextCtrl(panel, -1, value="", pos=(20,55), size=(410,24), style=0, name="Adresse")
        self.textmap["Adresse"] = "Adresse1"
        self.text_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
      
        self.button_Loeschen = wx.Button(panel, -1, label="&Löschen", pos=(150,100), size=(100,30), name="Loeschen")
        self.Bind(wx.EVT_BUTTON, self.On_Loeschen, self.button_Loeschen)     
        self.setWx(panel, [20, 100, 100, 30], [330, 100, 100, 30])
   
    ## execution in case the OK button ist hit - overwritten from parent class   
    def execute_Ok(self):
        self.store_data()

    ## attach data to dialog and invoke population of the graphic elements
    # @param data - AfpCharter object to hold the data to be displayed
    # @param index - if given, index of row of additional data to be displayed in data.selections["FahrtI"]
    def attach_data(self, data, index):
        self.data = data
        self.debug = self.data.debug
        self.index = index
        self.new = (index is None)
        self.choice_changed = False
        self.Populate()
        #self.Set_Editable(self.new)
        self.Set_Editable(True)
        if self.new:
            self.SetTitle("Fahrtinfo NEU")
            #self.choice_Edit.SetSelection(1)
        self.choice_Edit.SetSelection(1)
         
  ## read values from dialog and invoke writing into data         
    def store_data(self):
        self.Ok = False
        data = {}
        if self.new:
            if not "Datum" in self.changed_text:
                self.changed_text.append("Datum")
            if not "Adresse" in self.changed_text:
                self.changed_text.append("Adresse")
        #print self.changed_text
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        #print "store_data", self.choice_changed
        if self.choice_changed:
            data = self.set_choicevalues(data)
        #print "store_data data:", data
        if data:
            if self.new: data = self.complete_data(data)
            self.data.set_data_values(data, "FAHRTI", self.index)
            self.Ok = True
        self.changed_text = []   
        self.choice_changed = False  
    ## set textvalue in data, depending on choice settings
    # @param data - dictionary to hold data for modification
    def set_choicevalues(self, data):
        selfahrt = self.choice_Richtung.GetCurrentSelection()
        select = self.choice_Zeitpunkt.GetCurrentSelection()
        data["Adresse2"] = AfpChInfo_setDirSelection(selfahrt, select)
        return data
         
    ## initialise new empty data with all necessary values \n
    # or the other way round, complete new data entries with all needed input
    # @param data - data top be completed
    def complete_data(self, data):
        self.set_choicevalues(data)
        for entry in self.textmap:
            TextBox = self.FindWindowByName(entry)
            wert = TextBox.GetValue()
            #name = entry.split(".")[0]
            name = entry
            data[name] = wert 
        #print "AfpDialog_MfInfo.complete_data()",data         
        return data

    ## Population routine for the dialog overwritten from parent \n
    # due to special choice settings
    def Populate(self):
        if self.index is None:
            self.index = self.data.get_value_length("FAHRTI") 
            datum = self.data.get_string_value("Abfahrt")
            adresse = self.data.get_string_value("Abfahrtsort")
            self.text_Datum.SetValue(datum)
            self.text_Adresse.SetValue(adresse)
        if self.index < self.data.get_value_length("FAHRTI"):
            row = self.data.get_value_rows("FAHRTI","Adresse1,Abfahrtszeit,Datum,Adresse2", self.index)[0]
            self.text_Adresse.SetValue(Afp_toString(row[0]))
            self.text_Zeit.SetValue(Afp_toString(row[1]))
            self.text_Datum.SetValue(Afp_toString(row[2]))
            selfahrt, selaban = AfpChInfo_getDirSelection(row[3])
            self.choice_Richtung.SetSelection(selfahrt)
            self.choice_Zeitpunkt.SetSelection(selaban)
   
    ## activate or deactivate changeable widgets \n
    # this method also calls the parent method
    # @param ed_flag - flag if widgets have to be activated (True) or deactivated (False)
    # @param initial - flag if data has to be locked, used in parent method 
    def Set_Editable(self, ed_flag, initial = False):
        super(AfpDialog_DiMfInfo, self).Set_Editable(ed_flag, initial)
        if ed_flag: 
            self.choice_Richtung.Enable(True)
            self.choice_Zeitpunkt.Enable(True)
            self.button_Loeschen.Enable(True)
        else:  
            self.choice_Richtung.Enable(False)
            self.choice_Zeitpunkt.Enable(False)
            self.button_Loeschen.Enable(False)
            self.choicevalues = {}
            self.Populate()
         
    ##  Eventhandler TEXT,  check if date entry has the correct format, \n
    # complete date-text if necessary 
    # @param event - event which initiated this action   
    def On_ChangeDatum(self,event):
        if self.debug: print("Event handler `On_ChangeDatum'")
        datum = self.text_Datum.GetValue()
        datum =  Afp_ChDatum(datum)
        self.text_Datum.SetValue(datum)
        self.On_KillFocus(event)
        event.Skip()  
   ##  Eventhandler TEXT,  check if time entry has the correct format, \n
    # complete date-text if necessary 
    # @param event - event which initiated this action   
    def On_ChangeZeit(self,event):
        if self.debug: print("Event handler `On_ChangeZeit'")
        zeit = self.text_Zeit.GetValue()
        zeit, dum =  Afp_ChZeit(zeit)
        self.text_Zeit.SetValue(zeit)
        self.On_KillFocus(event)
        event.Skip()  

    ##  Eventhandler CHOICE,  record if a choice had been changed \n
    # and the set_choicevalues method has to be invoked during storing
    # @param event - event which initiated this action   
    def On_ChangeChoice(self,event):
        if self.debug: print("Event handler `On_ChangeChoice'")
        self.choice_changed = True
        event.Skip()  
      
    ##  Eventhandler BUTTON  delete this line from list in calling dialog,
    # @param event - event which initiated this action   
    def On_Loeschen(self,event):
        if self.debug: print("Event handler `On_Loeschen'", self.index)
        self.changed_text = []
        self.choicevalues = {} 
        self.data.delete_row("FAHRTI", self.index)
        self.store_data()
        self.Ok = True
        event.Skip()  
        self.EndModal(wx.ID_CANCEL)
  
## loader routine for dialog DiMfInfo
# @param data - AfpCharter object to hold the data to be displayed
# @param index - if given, index of row of information data to be displayed in data.selections["FahrtI"], \n
# otherwise a new row has to be added
def AfpLoad_DiMInfo(data, index):
    dialog = AfpDialog_DiMfInfo(None)
    dialog.attach_data(data, index)
    dialog.ShowModal()
    Ok = dialog.get_Ok()
    data = dialog.get_data()
    dialog.Destroy()
    if Ok:
        return data
    else:
        return None

 

 
