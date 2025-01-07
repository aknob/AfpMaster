#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseFiDialog
# AfpBaseFiDialog module provides the dialogs and appropriate loader routines needed for finance handling, \n
# payment userinteraction is performed here. \n
#
#   History: \n
#        17 Dez. 2024 - add MemberStorno selector - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        19 Nov. 2020 - add simple invoice handling - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        14 Feb. 2014 - inital code generated - Andreas.Knoblauch@afptech.de

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


from AfpBase.AfpBaseDialog import *
from AfpBase.AfpBaseDialogCommon import AfpLoad_DiReport
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpAdresse_addFileToArchiv
from AfpBase.AfpBaseFiRoutines import *

## deliver one client of a PaySelector 
# @param globals - global variables inclusive database access
# @param field - if given field for value selection
# @param fvalue - if given value of field for selection
def AfpFinance_getZahlVorgang(globals, field = None, fvalue = None):
    selectors = AfpFinance_get_ZahlSelectors(globals)
    liste = []
    names = []
    typs = []
    for sel in selectors:
        names.append(sel)
        liste.append(selectors[sel].get_label())
        typs.append("Button")
    names.append(None)
    #liste.append(["Sortierung nach Namen:", False])
    liste.append(["Sortierung nach Namen:", True])
    typs.append("Check")
    result = AfpReq_MultiLine("Übernahme der Daten aus einem Vorgang,", "die folgenden Vorgänge stehen zur Auswahl:", typs, liste, "Vorgangsauswahl", 250)
    #print ("AfpFinance_getZahlVorgang result:", result)
    ok = False 
    value = None    
    if result:
        selname = None
        for i in range(len(result)-1):
            if result[i]: selname = names[i]
        selector = selectors[selname] 
        if selector.is_editable():
             value = AfpLoad_PaySelectorAusw(selector)
             if value: ok = True
        else:
            text = selector.get_text()
            text2 = ""
            if result[-1]: 
                selector.set_sortfield("KundenNr")
                text2 = "Sortierung nach Namen!"
            rows = selector.get_rows(field, fvalue)
            liste = []
            ident = []
            if rows:
                lgh = len(rows[0]) - 1
                for row in rows:
                    liste.append(Afp_ArraytoLine(row, " ", lgh))
                    ident.append(row[-1])
            #print "AfpFinance_getZahlVorgang ident:", liste, ident
            value,ok = AfpReq_Selection("Bitte " + text + " für Zahlung auswählen!", text2, liste, text + " für Zahlung", ident)
    client = None 
    #print "AfpFinance_getZahlVorgang OK:", ok, value
    if ok and value:
        client = selector.get_client(value)
    return client


## deliver all ZahlSelectors for the actuel installed moduls
# @param globals - global variables inclusive database access
# @param in_filter - flag if selectors should be filtered due to payment direction, default: None - no filter
def AfpFinance_get_ZahlSelectors(globals , in_filter=None):
    selectors = {}    
    debug = globals.is_debug()
    finmods = []
    #print "AfpFinance_get_ZahlSelectors:", globals.get_value("only-direct-payment")
    if not globals.get_value("only-direct-payment"):
        modules = Afp_ModulNames(globals, True)
        finmods = modules[1:]
    #print "AfpFinance_get_ZahlSelectors:", finmods
    selects = []
    for mod in finmods:
        if mod == "Charter":
            selects.append(AfpFinance_CharterSelector(globals, debug))
        elif "Tourist" in mod or "Event" in mod:
            selects.append(AfpFinance_EventStornoSelector(globals, debug))
            if "Tourist" in mod:   selects.append(AfpFinance_TouristSelector(globals, debug))
            else:   selects.append(AfpFinance_EventSelector(globals, debug))
        elif "Verein" in mod:   
            selects.append(AfpFinance_MemberSelector(globals, debug))
            selects.append(AfpFinance_MemberStornoSelector(globals, debug))
            selects.append(AfpFinance_MemberPayBackSelector(globals, debug))
        elif mod == "Faktura":
            selects.append(AfpFinance_OrderSelector(globals, debug))
            #selects.append(AfpFinance_OfferSelector(globals, debug))
            selects.append(AfpFinance_InvoiceSelector(globals, debug))
    tables = globals.get_mysql().get_tables()
    if "VERBIND" in tables:
        selects.append(AfpFinance_ObligationSelector(globals, debug))
    if "RECHNG" in tables and not "Rechnung" in selectors:
        selects.append(AfpFinance_simpleInvoiceSelector(globals, debug))
    for sel in selects:
        if in_filter is None or (in_filter and sel.is_incoming()) or (not in_filter and not sel.is_incoming()):
            selectors[sel.get_name()] = sel
    #print ("AfpFinance_get_ZahlSelectors:", selectors)
    return selectors
        
## generate ZahlSelector for 'Charter' Modul
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_CharterSelector(globals, debug = False):
    name = "Mietfahrt"
    label = "&Mietfahrt"
    tablename = "FAHRTEN"
    felder = "Abfahrt,Preis,Zahlung,Zielort,Zustand,FahrtNr"
    filter =  "Zustand = \"Angebot\" OR Zustand = \"Rechnung\" OR Zustand = \"Storno Rechnung\""
    text = "Mietfahrt"
    object = "AfpCharter/AfpChRoutines/AfpCharter"
    edit = None
    return AfpPaySelector(globals, name, label, tablename, None, felder, filter, text, object, edit, debug)
## generate ZahlSelector for invoice part of the 'Charter'  and  'Tourist' Modul
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_simpleInvoiceSelector(globals, debug = False):
    name = "Rechnung"
    label = "&Rechnung"
    tablename = "RECHNG"
    #indexfield = None
    indexfield = "RechNr"
    #felder = "Datum,ZahlBetrag,Zahlung,Bem,Zustand,Betrag,RechNr"
    felder = [["RechNr.RECHNG",10], ["Datum.RECHNG",20], ["ZahlBetrag.RECHNG",15], ["Bem.RECHNG",30], ["Name.Adresse",25], 
                  ["KundenNr.ADRESSE = KundenNr.RECHNG",None], ["RechNr.RECHNG",None]] # Ident column  
    filter =  "Zustand = \"open\""
    text = "Rechnung" 
    object = "AfpCommonInvoice"
    #edit = None
    edit = "Afp_newSimpleInvoice" 
    return AfpPaySelector(globals, name, label,  tablename, indexfield, felder, filter, text, object, edit, debug)
## generate ZahlSelector for incomimg invoice
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_ObligationSelector(globals, debug = False):
    name = "Verbind"
    label = "&Verbindl."
    tablename = "VERBIND"
    indexfield = "RechNr"
    #felder = "Datum,ZahlBetrag,Betrag,Zahlung,Bem,Zustand,RechNr"
    felder = [["Datum.VERBIND",15], ["ZahlBetrag.VERBIND",15], ["ExternNr.VERBIND",15], ["Bem.VERBIND",30], ["Name.Adresse",25], 
                  ["KundenNr.ADRESSE = KundenNr.VERBIND",None], ["RechNr.VERBIND",None]] # Ident column  
    filter =  "( Zustand = \"Open\" OR Zustand = \"Static\" )"
    text = "Eingangsrechnung" 
    object = "AfpObligation"          
    #edit = None 
    edit = "Afp_newSimpleInvoice" 
    return AfpPaySelector(globals, name, label, tablename, indexfield, felder, filter, text, object, edit, debug, True)
## generate ZahlSelector for invoice part of the  'Event' Modul, flavour 'Tourist'
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_TouristSelector(globals, debug = False):
    name = "Anmeldung"
    label = "&Anmeldung"
    tablename = "ANMELD"
    indexfield = "EventNr"
    felder = "Beginn,Preis,Zahlung,Bez,Zustand,EventNr"
    filter =  "Zustand = \"Anmeldung\""
    text = "Reiseanmeldung"
    object = "AfpEvent/AfpEvScreenTourist/AfpEvTourist"
    edit = None
    return AfpPaySelector(globals, name, label,  tablename, indexfield, felder, filter, textl, object, modu, debug)
## generate ZahlSelector for invoice part of the  'Event' Modul flavour 'Verein'
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_MemberSelector(globals, debug = False):
    name = "Anmeldung"
    label = "&Beitrag"
    tablename = "ANMELD"
    indexfield = "EventNr"
    felder = "RechNr,Preis,KundenNr,Zahlung,ZahlDat,AnmeldNr"
    #felder = [["RechNr.ANMELD",10], ["Preis.ANMELD",20], ["Zahlung.ANMELD",20],  ["Vorname.ADRESSE.Name",20], ["Name.ADRESSE.Name",30],  
    #              ["KundenNr.ADRESSE = KundenNr.ANMELD",None], ["AnmeldNr.ANMELD",None]] # Ident column  
    filter =  "(Zustand = \"Anmeldung\" OR Zustand = \"PreStorno\") AND Preis > 0"
    text = "Anmeldung"
    object = "AfpEvent/AfpEvScreen_Verein/AfpEvMember"
    edit = None
    return AfpPaySelector(globals, name, label,  tablename, indexfield, felder, filter, text, object, edit, debug)
## generate ZahlSelector for invoice part of the  'Event' Modul flavour 'Verein', Storno
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_MemberStornoSelector(globals, debug = False):
    name = "AnmeldungStorno"
    label = "&Beitrag Storno"
    tablename = "ANMELD"
    indexfield = "EventNr"
    felder = "RechNr,Preis,KundenNr,Zahlung,ZahlDat,AnmeldNr"
    filter =  "Zustand = \"Storno\" AND Preis > 0"
    text = "Anmeldung"
    object = "AfpEvent/AfpEvScreen_Verein/AfpEvMember"
    edit = None
    return AfpPaySelector(globals, name, label,  tablename, indexfield, felder, filter, text, object, edit, debug)
## generate ZahlSelector for invoice part of the  'Event' Modul flavour 'Verein', pay back
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_MemberPayBackSelector(globals, debug = False):
    name = "Retoure"
    label = "&Retoure"
    tablename = "ANMELD"
    indexfield = "EventNr"
    felder = "RechNr,Preis,KundenNr,Zahlung,ZahlDat,AnmeldNr"
    filter =  "(Zustand = \"Anmeldung\" OR Zustand = \"PreStorno\") AND Preis > 0"
    text = "Anmeldung"
    object = "AfpEvent/AfpEvScreen_Verein/AfpEvMember"
    edit = None
    return AfpPaySelector(globals, name, label,  tablename, indexfield, felder, filter, text, object, edit, debug, True)
## generate ZahlSelector for invoice part of the  'Event' Modul
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_EventSelector(globals, debug = False):
    name = "Anmeldung"
    label = "&Anmeldung"
    tablename = "ANMELD"
    indexfield = "EventNr"
    felder = "Beginn,Preis,Zahlung,Bez,Zustand,EventNr"
    filter =  "Zustand = \"Anmeldung\""
    text = "Anmeldung"
    object = "AfpEvent/AfpEvRoutines/AfpEvClient"
    edit = None
    return AfpPaySelector(globals, name, label,  tablename, indexfield, felder, filter, text, object, edit, debug)
## generate ZahlSelector for cancellation part of the  'Event' Modul, includong all flavours
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_EventStornoSelector(globals, debug = False):
    name = "Storno"
    label = "&Stornierung"
    tablename = "ANMELD"
    indexfield = "EventNr"
    felder = "Abfahrt,Preis,Zahlung,Bez,Zustand,EventNr"
    filter =  "Zustand = \"Storno\""
    text = "Stornierung"
    object = "AfpEvent/AfpEvRoutines/AfpEvClient"
    edit = None
    return AfpPaySelector(globals, name, label,  tablename, indexfield, felder, filter, text, object, edit, debug, True)
## generate ZahlSelector for invoice part of the  'Faktura' Modul
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_InvoiceSelector(globals, debug = False):
    name = "Invoice"
    label = "&Rechnung"
    tablename = "RECHNG"
    felder = "RechNr,Datum,Pos,Betrag,ZahlBetrag,Zahlung,Bem"
    #filter_feld = "Zustand"
    #filter =  ["Offen","Mahnung","Beendet"]
    text = "Rechnung"
    object = "AfpFaktura/AfpFaRoutines/AfpInvoice"
    edit = None
    return AfpPaySelector(globals, name, label, tablename, None, felder, None, text, object, edit, debug)
## generate ZahlSelector for offer part of the  'Faktura' Modul
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_OfferSelector(globals, debug = False):
    name = "Offer"
    label = "&Auftrag"
    tablename = "KVA"
    felder = "RechNr,Datum,Pos,Betrag,Bem"
    filter =  "Zustand = \"Auftrag\""
    text = "Auftrag"
    object = "AfpFaktura/AfpFaRoutines/AfpOffer"
    edit = None
    return AfpPaySelector(globals, name, label, tablename, None, felder, None, text, object, edit, debug)
## generate ZahlSelector for order part of the  'Faktura' Modul
# @param globals -  global values including object for dadabase access
# @param debug - debug flag
def AfpFinance_OrderSelector(globals, debug = False):
    name = "Order"
    label = "&Bestellung"
    tablename = "BESTELL"
    felder = "RechNr,Datum, Pos,Betrag,ZahlBetrag,Bem"
    filter =  "Zustand = \"beglichen\" OR Zustand = \"erhalten\" OR Zustand = \"open\""
    text = "Bestellung"
    object = "AfpFaktura/AfpFaRoutines/AfpOrder"
    edit = None
    return AfpPaySelector(globals, name, label, tablename, None, felder, None, text, object, edit, debug)
    
## class to select additional payment entries
class AfpPaySelector(object):
   ## initialize payment class, \n
    # if avaulable attach modul to record financial transactions
    # @param globals - global values including database handle
    # @param name - name of button
    # @param label - label of button
    # @param tablename - name of database table
    # @param indexfield - name field on which given value should be selected
    # @param felder - name if columns given in the list
    # @param filter - filter for selection
    # @param text - text to be displayed in dialog
    # @param object - path of object to be created from selection
    # @param edit - path of routine to generate and edit new created object
    # @param debug - debug flag
    # @param outgoing - flag if payment direction is outgoing
    def  __init__(self, globals, name, label, tablename , indexfield, felder, filter, text, object, edit, debug = False, outgoing = False):
        self.globals = globals
        self.mysql = self.globals.get_mysql()
        self.name = name
        self.label = label
        self.tablename = tablename
        self.indexfield = indexfield
        self.sortfield = None
        self.felder = felder
        self.filter = filter
        self.text = text
        self.object = object
        self.edit = edit
        self.outgoing = outgoing
        self.debug = debug
    ## get flag if payment is incoming \n
    def is_incoming(self):
        return not self.outgoing
    ## get flag if payment may deliver 'edit' dialog \n
    def is_editable(self):
        if self.edit and self.indexfield:
            return True
        else:
            return False
    ## get name
    def get_name(self):
        return self.name
    ## get button label
    def get_label(self):
        return self.label
    ## get table name
    def get_tablename(self):
        return self.tablename
    ## get sort field name
    def get_indexfield(self):
        return self.indexfield
    ## get filter used
    def get_filter(self):
        return self.filter
    ## get fields values
    def get_felder(self):
        return self.felder
    ## get fields to be displayed in a string
    def get_felder_string(self):
        result = self.felder
        if type(self.felder) == list:
            result = ""
            for entry in self.felder:
                if self.tablename in entry[0] and not entry[1] is None:
                    result += "," + entry[0] .split(".")[0]
            result += "," + self.felder[-1][0].split(".")[0]
            #print("AfpPaySelector.get_felder:", result[1:])
            if result: result = result[1:]
        return result
    ## identify payment columns
    def identify_payment_indices(self):
        felder = self.get_felder_string().split(",")
        pay_ind = None
        price_ind = None
        pprice_ind = None
        for feld in felder:
            if "Zahlung" in feld:
                pay_ind = felder.index(feld)
            if "Betrag" in feld or "Preis" in feld:
                price_ind = felder.index(feld)
                if "Zahl" in feld:
                    pprice_ind = price_ind
        if not pprice_ind is None:
            return pay_ind, pprice_ind
        else:
            return pay_ind, price_ind
    ## get dialog text
    def get_text(self):
        return self.text
    ## get modul- and objectname from self.object
    def get_object_modul(self):
        return self.split_object_modul(self.object)
    ## get modul- and objectname from self.edit
    def get_edit_modul(self):
        return self.split_object_modul(self.edit)
    ## get modul- and objectname from entry
    # @param entry - string to be splitted into modul- and objectname
    def split_object_modul(self, entry):
        #print "AfpPaySelector.split_object_modul:", entry, self.object, self.edit
        modul = None
        object = None
        if entry and "/" in entry:
            split = entry.split("/")
            #modul = "/".join(split[:-1])
            modul = ".".join(split[:-1])
            object = split[-1]
        else:
            object = entry
        return modul, object
    ## method to retrieve client object
    # @param value - identifier for generated client object
    def get_client(self, value = None):
        client = None
        modulname, objectname = self.get_object_modul()
        befehl = None 
        #print ("AfpPaySelector.get_client:",  modulname, objectname)
        if modulname:
            befehl = "from " + modulname + " import *; client = "
        else:
            befehl = "from AfpBase.AfpBaseFiRoutines import *; client = "
        if befehl:
            if value is None:
                befehl +=  objectname + "(self.globals)"
            else:
                befehl +=  objectname + "(self.globals," + Afp_toString(value) +")"
            local = locals()
            #print ("AfpPaySelector.get_client exec:",  befehl, local)
            exec(befehl, {}, local)
            client = local["client"]
            if self.outgoing: client.outgoing = self.outgoing
        return client
    ## method to retrieve rows from database
    # @param field - database field holding common value in rows
    # @param value - value looked for in field
    def get_rows(self, field, value):
        if field and value:
            #print "AfpPaySelector.get_rows:", self.tablename, field, value, self.debug, self.felder, self.filter
            #if self.indexfield != field:
            #    field = None
            #    value = None
            rows = Afp_selectSameValue(self.mysql, self.tablename, field, value, self.debug, self.get_felder_string(), self.filter)
            if "KundenNr" in self.felder:
                ind = self.felder.split(",").index("KundenNr")
                for i in range(len(rows)):
                    rows[i][ind] = AfpFinance_getNameFromKNr(self.mysql, rows[i][ind], True)
            if self.sortfield:
                ind = self.felder.split(",").index(self.sortfield)
                sortlist = []
                for i in range(len(rows)):
                    sortlist.append(rows[i][ind])
                sortlist, rows = Afp_sortSimultan(sortlist, rows)
            return rows
        else:
            return None
    ## set and unset field for sorted output other than indexfield
    # @param field - name of column used for sorting
    def set_sortfield(self, field):
        if field in self.felder or field is None:
            self.sortfield = field
            
    ## select appropriate incident
    # @param KNr - address identifier for which incident has to be selected
    def select_incident_by_KNr(self, KNr):
        liste = []
        ident = []
        rows = self.get_rows("KundenNr", KNr)
        if rows:
            lgh = len(rows[0]) -1
            for row in rows:
                if row[1] is None and self.name == "Rechnung": row[1] = row[5]
                if row[1]:
                    zind, pind = self.identify_payment_indices()
                    if not zind is None and not pind is None:
                        if row[zind]:
                            row[zind] = row[pind] - row[zind]
                        else:
                            row[zind] = row[pind]
                liste.append(Afp_ArraytoLine(row, " ", lgh))
                ident.append(row[-1])
        value,ok = AfpReq_Selection("Bitte " + self.text + " für Zahlung auswählen!","",liste, self.text + " für Zahlung", ident)
        if ok and value:
            return self.tablename, value
        else:
            return None, None 
    ## select appropriate incident
    # @param KNr - address identifier for which incident has to be selected
    def select_client_by_KNr(self, KNr):
        table, tabNr = self.select_incident_by_KNr(KNr)
        if table and tabNr:
            return self.get_client(tabNr)
        else:
            return None
  
## display and manipulation of payments
class AfpDialog_DiFiZahl(AfpDialog):
    ## initialise dialog
    def __init__(self, globals,out=False):
        self.globals = globals        
        self.selector_buttons= []
        self.selectors = None
        self.is_full = False
        self.outgoing = out
        AfpDialog.__init__(self,None, -1, "")
        self.do_store = True
        self.allow_skonto = False
        if self.is_full:
            self.SetSize((570,400))
        else:
            self.SetSize((400,150))
        if self.outgoing:
            self.SetTitle("Zahlung (Ausgang)")
        else:
            self.SetTitle("Zahlung (Eingang)")

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
        self.label_T_Aus_Zahlung = wx.StaticText(self, -1, label="Aus&zug:", name="T_Aus_Zahlung")
        self.text_Auszug = wx.TextCtrl(self, -1, value="", style=0, name="Auszug")
        self.text_Auszug.Bind(wx.EVT_KILL_FOCUS, self.On_Zahlung_Auszug)
        self.label_T_Zahl_Zahlung = wx.StaticText(self, -1, label="&Betrag:", name="T_Zahl_Zahlung")
        self.text_Zahlung = wx.TextCtrl(self, -1, value="", style=0, name="Zahlung")
        self.text_Zahlung.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        
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
        incoming = not self.outgoing
        if selectors:
            ind = -1
            for sel in selectors:
                selector = selectors[sel]
                if selector.is_incoming() == incoming:
                    ind += 1                
                    button = wx.Button(panel, -1, label=selector.get_label(), pos=(20 + ind*100,160), size=(92,34), name=selector.get_name())
                    self.selector_buttons.append(button)
                    self.Bind(wx.EVT_BUTTON, self.On_Zahlung_Select, self.selector_buttons[ind])
        if self.selector_buttons:
            self.selectors = selectors
            self.is_full = True
        #print "AfpZahlung.gen_sel_buttons:", selectors, self.is_full
    ## attaches data to this dialog, invokes population of widgets \n
    # overwritten from AfpDialog
    # @param data - AfpSelectionList which holds data to be filled into dialog widgets 
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
        self.close_dialog = True
        value = Afp_fromString(self.text_Zahlung.GetValue())
        Auszug = self.text_Auszug.GetValue()
        direct_cash = self.globals.get_value("allow-direct-cash-payment")
        if not Auszug:
            ok = False
            if self.has_finance and direct_cash:
                ok = AfpReq_Question("Kein Auszug eingegeben!", "Barzahlung?","Zahlung")
            elif direct_cash:
                ok = True
            else: 
                 AfpReq_Info("Kein Auszug eingegeben!", "Bitte Eingabe nachholen.","Zahlung")
            if not ok:
                driect_cash = False
                value  = 0.0
                self.close_dialog = False
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
        print ("AfpDialog_DiFiZahl.execute_Ok:", Auszug, value, direct_cash, self.do_store, self.Ok)
    ## set flag to avoid writing into database when leaving the dialog \n
    # execution should then be performed by the caller
    def do_not_store(self):
        self.do_store = False
    ## check if statement of account (Auszug) exists, if not create one
    # @param auszug - identifier of statement of account to be checked
    def check_auszug(self, auszug):
        if auszug:
            checked = self.data.check_auszug(auszug)
            if not checked:
                datum, Ok = AfpReq_Date("Bitte Datum für Auszug '" + auszug + "' angeben,", "", "", "", True)
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
            
    ## invoke selection of another participent of this payment, triggerd by selectorname
    # @param selectorname - name of selector with which the selection should be made
    def select_selection_by_name(self, selectorname):
        if selectorname in self.selectors:
            selector = self.selectors[selectorname]
            KundenNr = self.data.get_value("KundenNr")
            table, number = selector.select_incident_by_KNr(KundenNr)
            if table and number:
                print("AfpDialog_DiFiZahl.select_selection_by_name:", table, number)
                self.data.add_selection(table, number)
                self.Pop_Zahlungen()

    # Event Handlers 
    ## event handler when cursor leaves the 'statement of account' (Auszug) textbox
    def On_Zahlung_Auszug(self,event):
        if self.debug: print("AfpDialog_DiFiZahl Event handler `On_Zahlung_Auszug'")
        Auszug = self.text_Auszug.GetValue()
        self.check_auszug(Auszug)
        event.Skip()

    ##Eventhandler BUTTON - add an entry to this payment, depending on name of the button \n
    def On_Zahlung_Select(self,event):
        if self.debug: print("AfpDialog_DiFiZahl Event handler `On_Zahlung_select'")
        object = event.GetEventObject()
        name = object.GetName()
        self.select_selection_by_name(name)
        event.Skip()

    ##Eventhandler BUTTON - remove an entry from this payment \n
    def On_Zahlung_Delete(self,event):
        if self.debug: print("AfpDialog_DiFiZahl Event handler `On_Zahlung_Delete'")
        index = self.list_Zahlungen.GetSelections()[0] 
        if index > 0:
            self.data.remove_selection(index)
            self.Pop_Zahlungen()
        event.Skip()

    ##Eventhandler BUTTON - show list of financial payment transaction \n
    def On_Zahlung_Liste(self,event):
        if self.debug: print("AfpDialog_DiFiZahl Event handler `On_Zahlung_Liste'")
        if self.data.finance:
            liste = {}
            for data in self.data.selected_list:
                tab = data.get_mainselection()
                tabnr = data.get_value()
                select = "Tab = \"" + tab + "\" AND TabNr = " + Afp_toString(tabnr) + " AND (Art = \"Zahlung\" OR Art = \"Zahlung in\")"
                felder = "Datum,GktName,Betrag,Beleg,Bem"
                rows = self.data.mysql.select(felder, select, "BUCHUNG")
                zahlungen = []
                for row in rows:
                    zahlungen.append(Afp_ArraytoLine(row))
                liste[ident] = zahlungen
                #print "AfpDialog_DiFiZahl.On_Zahlung_Liste:", liste
            Afp_printToInfoFile(self.data.globals, liste)
        else:
            AfpReq_Info("Finanzmodul nicht installiert!","Funktion steht nicht zur Verfügung!")
        event.Skip()

    ##Eventhandler BUTTON - allow manuel distribution of this payment \n
    # not implemented yet
    def On_Zahlung_Manuell(self,event):
        print("AfpDialog_DiFiZahl Event handler `On_Zahlung_Manuell' not implemented!")
        self.On_Zahlung_Bar(event)
        event.Skip()

   ##Eventhandler BUTTON - allow manuel distribution of this payment \n
    # not implemented yet
    def On_Zahlung_Bar(self,event):
        if self.debug: print("AfpDialog_DiFiZahl Event handler `On_Zahlung_Bar'")
        self.data.globals.set_value("allow-direct-cash-payment", 1)
        self.execute_Ok()
        event.Skip()
        self.EndModal(wx.ID_OK)

    ##Eventhandler BUTTON - show payment info \n
    def On_Zahlung_Info(self,event):
        if self.debug: print("AfpDialog_DiFiZahl Event handler `On_Zahlung_Info'")
        if self.data.finance:
            liste = {}
            for data in self.data.selected_list:
                payment = {}
                payment = self.data.finance.add_payment_data(payment, data) 
                liste[payment["Von"]] = [Afp_toString(payment["Gegenkonto"]) + " "  + data.get_name()]
            Afp_printToInfoFile(self.data.globals, liste)
        else:
            AfpReq_Info("Finanzmodul nicht installiert!","Funktion steht nicht zur Verfügung!")
        event.Skip()

## loader routine for dialog DiFiZahl \n
# @param data - initial data to be attached to this dialog
# @param multi - if given, additional entries will be retrieved from database with identic values in this column(s)
# @param do_not_store - flag if writing to database should be skipped
def AfpLoad_DiFiZahl(data, multi = None, do_not_store = False):
    DiZahl = AfpDialog_DiFiZahl(data.globals, data.is_outgoing() )
    Zahl = AfpZahlung(data, multi) 
    DiZahl.attach_data(Zahl, False, True)
    if do_not_store: DiZahl.do_not_store()
    DiZahl.ShowModal()
    Ok = DiZahl.get_Ok()
    data = DiZahl.get_data()
    DiZahl.Destroy()
    return Ok, data
 
## dialog for selection of dat depending of PaySelection data \n
# selects an entry from the appropriate table
class AfpDialog_PaySelectorAusw(AfpDialog_Auswahl):
    ## initialise dialog
    # @param selector - PaySelector object to be used
    def __init__(self, selector):
        self.selector = selector
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        if not self.selector.is_editable(): self.button_Neu.Enable(False)
        self.typ = self.selector.get_text() + "-Auswahl"
        self.datei = self.selector.get_tablename() 
       
    ## get the definition of the selection grid content \n
    # overwritten for "PaySelector" use
    def get_grid_felder(self): 
        Felder = self.selector.get_felder()
        return Felder
    ## invoke the dialog for a new entry \n
    # overwritten for "PaySelector" use
    def invoke_neu_dialog(self, my_globals, eingabe, filter):
        res = False
        data = self.selector.get_client()
        modulname, routinename = self.selector.get_edit_modul()
        befehl = None 
        #print "AfpDialog_PaySelectorAusw.invoke_neu_dialog:",  modulname, routinename
        if modulname:
            modul = Afp_importPyModul(modulname, self.selector.globals)
            if modul:
                befehl = "res = modul."
        else:
            befehl = "res = "
        if befehl:
            befehl +=  routinename + "(data)"
            local = locals()
            exec(befehl, globals(), local)
            res = local["res"]
            if res: self.Pop_grid()
        return res
## loader routine for event selection dialog 
# @param pselector - PaySelector to be used for selection
# @param value - if given value to be selected
def AfpLoad_PaySelectorAusw(pselector, value=None):
    DiAusw = AfpDialog_PaySelectorAusw(pselector)
    text = "Bitte " + pselector.get_text() + " auswählen:"   
    DiAusw.initialize(pselector.globals, pselector.get_indexfield(), value, pselector.get_filter(), text)
    DiAusw.ShowModal()
    result = DiAusw.get_result()
    DiAusw.Destroy()
    return result    
 
## handling routine for common invoices
# @param globals - global variables including database connection
# @param where - if given, filter for search in table
def Afp_handleCommonInvoice(globals, where = None):
    pselector = AfpFinance_simpleInvoiceSelector(globals)
    if not where is None:
        if where:
            pselector.filter = where
        else:
            pselector.filter = None
    ReNr = AfpLoad_PaySelectorAusw(pselector)
    Ok = False
    if ReNr:
        Ok = AfpLoad_SimpleInvoice_fromReNr(globals, ReNr)
    return Ok 
## load simple invoice dialog for common invoice with given invoice number
# @param globals - global variables including database connection
# @param ReNr - invoice number of invoice to be loaded
def AfpLoad_SimpleInvoice_fromReNr(globals, ReNr):
        data = AfpCommonInvoice(globals, ReNr)
        Ok = AfpLoad_SimpleInvoice(data)
        return Ok
## handling routine for obligations
# @param globals - global variables including database connection
# @param where - if given, filter for search in table
def Afp_handleObligation(globals, where = None):
    pselector = AfpFinance_ObligationSelector(globals)
    if not where is None:
        if where:
            pselector.filter = where
        else:
            pselector.filter = None
    ReNr = AfpLoad_PaySelectorAusw(pselector)
    Ok = False
    if ReNr:
        data = AfpObligation(globals, ReNr)
        Ok = AfpLoad_SimpleInvoice(data)
    return Ok  
 ## load simple invoice dialog for obligation with given invoice number
# @param globals - global variables including database connection
# @param VbNr - invoice number of obligation to be loaded
def AfpLoad_Obligation_fromVbNr(globals, VbNr):
        data = AfpObligation(globals, VbNr)
        Ok = AfpLoad_SimpleInvoice(data)
        return Ok
   
## class for simple Invoice dialog (incoming/outgoing)
class AfpDialog_SimpleInvoice(AfpDialog):
    def __init__(self, obligation = False, skonto=False):
        self.oblig = obligation   
        self.skonto = obligation or skonto
        AfpDialog.__init__(self,None, -1, "")
        self.checked_box = []
        self.data_changed = False

        self.SetSize((378,400))
        self.SetTitle("Rechnung")
        if self.oblig:
            self.SetTitle("Eingangsrechnung")   
        
    def InitWx(self): 
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.panel_sizer = wx.BoxSizer(wx.VERTICAL)
        # INVOICE DATA
        self.label_RechNr = wx.StaticText(self, -1, name="RechNr")
        self.labelmap["RechNr"] = "RechNr"
        self.line1_sizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.line1_sizer.AddStretchSpacer(1)           
        self.line1_sizer.Add(self.label_RechNr,1,wx.EXPAND)
        self.line1_sizer.AddStretchSpacer(1)  
        
        self.label_Vorname = wx.StaticText(self, -1, name="Vorname")
        self.labelmap["Vorname"] = "Vorname.ADRESSE"
        self.label_Nachname = wx.StaticText(self, -1, name="Nachname")
        self.labelmap["Nachname"] = "Name.ADRESSE"
        self.line2_sizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.line2_sizer.Add(self.label_Vorname,1,wx.EXPAND)
        self.line2_sizer.AddSpacer(5)        
        self.line2_sizer.Add(self.label_Nachname,1,wx.EXPAND)

        if self.oblig:
            self.label_TReNr = wx.StaticText(self, -1, label="Rechnungs Nr:", style=wx.ALIGN_RIGHT)
            self.text_ReNr = wx.TextCtrl(self, -1,  name="ReNr")
            self.textmap["ReNr"] = "ExternNr"
            self.text_ReNr.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
            self.line3_sizer =  wx.BoxSizer(wx.HORIZONTAL)
            self.line3_sizer.Add(self.label_TReNr,1,wx.EXPAND)
            self.line3_sizer.AddSpacer(5)        
            self.line3_sizer.Add(self.text_ReNr,1,wx.EXPAND)
            self.line3_sizer.AddSpacer(5) 
        else:
            self.label_TNetto = wx.StaticText(self, -1, label="Netto:", style=wx.ALIGN_RIGHT)
            self.text_Netto = wx.TextCtrl(self, -1,  name="Netto")
            self.vtextmap["Netto"] = "Netto"
            self.text_Netto.Bind(wx.EVT_KILL_FOCUS, self.On_Skonto)
            self.line3_sizer =  wx.BoxSizer(wx.HORIZONTAL)
            self.line3_sizer.Add(self.label_TNetto,1,wx.EXPAND)
            self.line3_sizer.AddSpacer(5)        
            self.line3_sizer.Add(self.text_Netto,1,wx.EXPAND)
            self.line3_sizer.AddSpacer(5)        

        self.label_TReDat = wx.StaticText(self, -1, label="Datum:", style=wx.ALIGN_RIGHT)
        self.text_ReDat = wx.TextCtrl(self, -1,  name="DatSI")
        self.vtextmap["DatSI"] = "Datum"
        self.text_ReDat.Bind(wx.EVT_KILL_FOCUS, self.On_Datum)
        self.line4_sizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.line4_sizer.Add(self.label_TReDat,1,wx.EXPAND)
        self.line4_sizer.AddSpacer(5)        
        self.line4_sizer.Add(self.text_ReDat,1,wx.EXPAND)
        self.line4_sizer.AddSpacer(5)        

        self.label_TBetrag = wx.StaticText(self, -1, label="Betrag:", style=wx.ALIGN_RIGHT)
        self.text_Betrag = wx.TextCtrl(self, -1,  name="BetragSI")
        self.vtextmap["BetragSI"] = "Betrag"
        self.text_Betrag.Bind(wx.EVT_KILL_FOCUS, self.On_Skonto)
        self.line5_sizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.line5_sizer.Add(self.label_TBetrag,1,wx.EXPAND)
        self.line5_sizer.AddSpacer(5)        
        self.line5_sizer.Add(self.text_Betrag,1,wx.EXPAND)
        self.line5_sizer.AddSpacer(5)        

        self.label_TZiel = wx.StaticText(self, -1, label="Falligkeit:", style=wx.ALIGN_RIGHT)
        self.text_Ziel = wx.TextCtrl(self, -1,  name="ZielDat")
        self.vtextmap["ZielDat"] = "ZahlZiel"
        self.text_Ziel.Bind(wx.EVT_KILL_FOCUS, self.On_Datum)
        self.line6_sizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.line6_sizer.Add(self.label_TZiel,1,wx.EXPAND)
        self.line6_sizer.AddSpacer(5)        
        self.line6_sizer.Add(self.text_Ziel,1,wx.EXPAND)
        self.line6_sizer.AddSpacer(5)        

        #self.label_TKred= wx.StaticText(self, -1, label="Debitor:", style=wx.ALIGN_RIGHT)
        #self.text_Kred = wx.TextCtrl(self, -1,  name="KreDeb")
        #self.textmap["KreDeb"] = "Debitor"
        #self.text_Kred.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        #self.line7_sizer =  wx.BoxSizer(wx.HORIZONTAL)
        #self.line7_sizer.Add(self.label_TKred,1,wx.EXPAND)
        #self.line7_sizer.AddSpacer(5)        
        #self.line7_sizer.Add(self.text_Kred,1,wx.EXPAND)
        #self.line7_sizer.AddSpacer(5)        

        self.label_TKonto= wx.StaticText(self, -1, label="Kontierung:", style=wx.ALIGN_RIGHT)
        self.text_Konto = wx.TextCtrl(self, -1,  name="Kontierung")
        self.textmap["Kontierung"] = "Kontierung"
        self.text_Konto.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.line8_sizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.line8_sizer.Add(self.label_TKonto,1,wx.EXPAND)
        self.line8_sizer.AddSpacer(5)        
        self.line8_sizer.Add(self.text_Konto,1,wx.EXPAND)
        self.line8_sizer.AddSpacer(5)        
 
        self.text_Bem = wx.TextCtrl(self, -1, style=wx.TE_MULTILINE|wx.TE_BESTWRAP,  name="Bem")
        self.textmap["Bem"] = "Bem"
        self.text_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.line9_sizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.line9_sizer.AddSpacer(5)        
        self.line9_sizer.Add(self.text_Bem,1,wx.EXPAND)
        self.line9_sizer.AddSpacer(5)           
        
        if self.skonto:
            self.label_TSkonto= wx.StaticText(self, -1, label="Prozent:", style=wx.ALIGN_RIGHT)
            self.text_SkPro = wx.TextCtrl(self, -1,  name="SkPro")
            self.textmap["SkPro"] = "SkPro._tmp"
            self.text_SkPro.Bind(wx.EVT_SET_FOCUS, self.In_SkPro)
            self.text_SkPro.Bind(wx.EVT_KILL_FOCUS, self.On_Skonto)
            self.text_Skonto = wx.TextCtrl(self, -1,  name="Skonto")
            self.textmap["Skonto"] = "Skonto"
            self.text_Skonto.Bind(wx.EVT_KILL_FOCUS, self.On_Skonto)
            self.line10_sizer =  wx.BoxSizer(wx.HORIZONTAL)
            self.line10_sizer.Add(self.label_TSkonto,1,wx.EXPAND)
            self.line10_sizer.AddSpacer(5)        
            self.line10_sizer.Add(self.text_SkPro,1,wx.EXPAND)
            self.line10_sizer.Add(self.text_Skonto,2,wx.EXPAND)
            self.line10_sizer.AddSpacer(5)

        self.label_TGesamt= wx.StaticText(self, -1, label="Zahlbetrag:", style=wx.ALIGN_RIGHT)
        self.text_ZahlBet = wx.TextCtrl(self, -1,  name="ZahlBet")
        self.vtextmap["ZahlBet"] = "ZahlBetrag"
        self.text_ZahlBet.Bind(wx.EVT_KILL_FOCUS, self.On_Skonto)
        self.line11_sizer =  wx.BoxSizer(wx.HORIZONTAL)
        self.line11_sizer.Add(self.label_TGesamt,1,wx.EXPAND)
        self.line11_sizer.AddSpacer(5)        
        self.line11_sizer.Add(self.text_ZahlBet,1,wx.EXPAND)
        self.line11_sizer.AddSpacer(5)          
        
        self.panel_sizer.AddSpacer(5)          
        self.panel_sizer.Add(self.line1_sizer,0,wx.EXPAND)
        self.panel_sizer.AddSpacer(5)          
        self.panel_sizer.Add(self.line2_sizer,0,wx.EXPAND)
        self.panel_sizer.AddSpacer(5)  
        if self.oblig:
            self.panel_sizer.Add(self.line3_sizer,0,wx.EXPAND)
            self.panel_sizer.AddSpacer(5)  
            self.panel_sizer.Add(self.line4_sizer,0,wx.EXPAND)
            self.panel_sizer.AddSpacer(5)   
        else:
            self.panel_sizer.Add(self.line4_sizer,0,wx.EXPAND)
            self.panel_sizer.AddSpacer(5)   
            self.panel_sizer.Add(self.line3_sizer,0,wx.EXPAND)
            self.panel_sizer.AddSpacer(5)  
        self.panel_sizer.Add(self.line5_sizer,0,wx.EXPAND)
        self.panel_sizer.AddSpacer(5)    
        self.panel_sizer.Add(self.line6_sizer,0,wx.EXPAND)
        self.panel_sizer.AddSpacer(5)    
        #self.panel_sizer.Add(self.line7_sizer,0,wx.EXPAND)
        #self.panel_sizer.AddSpacer(5)    
        self.panel_sizer.Add(self.line8_sizer,0,wx.EXPAND)
        self.panel_sizer.AddSpacer(5)     
        if self.skonto:
            self.panel_sizer.Add(self.line9_sizer,1,wx.EXPAND)
            self.panel_sizer.AddSpacer(5)
            self.panel_sizer.Add(self.line10_sizer,0,wx.EXPAND)
            self.panel_sizer.AddSpacer(5)  
        else:
            self.panel_sizer.Add(self.line9_sizer,2,wx.EXPAND)
            self.panel_sizer.AddSpacer(5)
        self.panel_sizer.Add(self.line11_sizer,0,wx.EXPAND)
        self.panel_sizer.AddSpacer(5)  
        
        # BUTTONs
        self.button_sizer = wx.BoxSizer(wx.VERTICAL)          
        self.label_Zustand = wx.StaticText(self, -1,  name="Zustand")
        self.labelmap["Zustand"] = "Zustand"        
        self.button_Zahl = wx.Button(self, -1, label="&Zahlung", name="Zahl")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahl)
        self.button_Neu = wx.Button(self, -1, label="&Neu", name="Neu")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)
        self.button_Storno = wx.Button(self, -1, label="&Stornierung", name="Storno")
        self.Bind(wx.EVT_BUTTON, self.On_Storno, self.button_Storno)
        self.button_Orig = wx.Button(self, -1, label="&Original", name="Orig")
        self.Bind(wx.EVT_BUTTON, self.On_Original, self.button_Orig)
        self.check_Dauer = wx.CheckBox(self, -1, label="Dauer", name="Dauer")
        self.checkmap["Dauer"] = "Zustand = Static"
        self.Bind(wx.EVT_CHECKBOX, self.On_Check, self.check_Dauer)
        if not self.oblig:
            self.check_Voraus = wx.CheckBox(self, -1, label="Voraus", name="Voraus")
            self.Bind(wx.EVT_CHECKBOX, self.On_Check, self.check_Voraus)
        self.button_Druck = wx.Button(self, -1, label="&Drucken", name="Druck")
        self.Bind(wx.EVT_BUTTON, self.On_drucken, self.button_Druck)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.label_Zustand,0,wx.EXPAND)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.button_Zahl,0,wx.EXPAND)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.button_Neu,0,wx.EXPAND)
        self.button_sizer.AddStretchSpacer(1)
        self.button_sizer.Add(self.button_Storno,0,wx.EXPAND)
        self.button_sizer.AddSpacer(5)
        self.button_sizer.Add(self.button_Orig,0,wx.EXPAND)
        self.button_sizer.AddStretchSpacer(1)
        self.button_sizer.Add(self.check_Dauer,0,wx.EXPAND)
        if not self.oblig:
            self.button_sizer.AddSpacer(1)
            self.button_sizer.Add(self.check_Voraus,0,wx.EXPAND)
        self.button_sizer.AddStretchSpacer(1)
        self.button_sizer.Add(self.button_Druck,0,wx.EXPAND)
        self.setWx(self.button_sizer, [1, 0, 0], [1, 0, 1]) # set Edit and Ok widgets

        self.sizer.AddSpacer(10)
        self.sizer.Add(self.panel_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.button_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)   
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        
    ## set all payment values due to change in wx-object
    # @param object - gaphic object where value has been changed
    def set_payment_change(self, object):
        name = object.GetName()
        #print "AfpDialog_SimpleInvoice.set_payment_change name:", name
        if name == "BetragSI":
            self.text_Betrag.SetValue(Afp_toString(Afp_fromString(self.text_Betrag.GetValue())))
        if name == "ZahlBet":
            self.text_ZahlBet.SetValue(Afp_toString(Afp_fromString(self.text_ZahlBet.GetValue())))
        netto = None
        if not self.oblig and name == "Netto":
            netto  = Afp_fromString(self.text_Netto.GetValue())
            betrag = AfpFinance_addTax(self.data.get_globals(), netto)
        else:
            betrag = Afp_fromString(self.text_Betrag.GetValue())
        if betrag:
            percent = self.get_percent()
            if not percent is None:
                skonto = Afp_fromString(self.text_Skonto.GetValue())
                if not skonto: skonto = 0.0
                zahl = Afp_fromString(self.text_ZahlBet.GetValue())
                if not zahl: zahl = 0.0
                if percent and (name == "BetragSI" or name == "Netto"  or name == "SkPro"):
                    skonto  = int(percent*betrag)/100.0
                elif zahl and name == "ZahlBet" :
                    skonto = betrag - zahl
                if skonto and (name == "Skonto" or name == "ZahlBet"):
                    initial = percent
                    percent = 100.0*skonto/betrag
                    if initial and percent and not Afp_isEps(percent - initial):
                        percent = initial
                if percent and skonto and name != "ZahlBet":
                    zahl = betrag - skonto
                #print "AfpDialog_SimpleInvoice.set_payment_change:", percent, "% von ", betrag, "ist",  skonto, "bleiben zu zahlen", zahl
                if percent:
                    self.text_SkPro.SetValue(Afp_toString(percent) + "%")
                    if skonto:
                        self.text_Skonto.SetValue(Afp_toFloatString(skonto))
                    else:
                        self.text_Skonto.SetValue("")
                    self.text_ZahlBet.SetValue(Afp_toFloatString(zahl))
                    if not "Skonto" in self.changed_text: self.changed_text.append("Skonto")
                    if not "ZahlBet" in self.changed_text: self.changed_text.append("ZahlBet")
            if name == "BetragSI" or name == "Netto":
                self.text_Betrag.SetValue(Afp_toFloatString(betrag))
                if not "BetragSI" in self.changed_text: self.changed_text.append("BetragSI")
                if not self.oblig:
                    if netto is None:
                        netto = AfpFinance_stripTax(self.data.get_globals(), betrag)
                    self.text_Netto.SetValue(Afp_toFloatString(netto))
                    if not "Netto" in self.changed_text: self.changed_text.append("Netto")
                    self.text_ZahlBet.SetValue(Afp_toFloatString(betrag))
                    if not "ZahlBet" in self.changed_text: self.changed_text.append("ZahlBet")
            if name == "ZahlBet":
                    if not "ZahlBet" in self.changed_text: self.changed_text.append("ZahlBet")
    ## get percent value from textinput (may extract %'-sign)
    def get_percent(self):
        valstring = None
        if self.skonto:
            valstring = self.text_SkPro.GetValue().strip()
        if valstring:
            if valstring[-1] == "%":
                valstring = valstring[:-1].strip()
            return Afp_fromString(valstring)
        else:
            return None
            
    ## add value according to checkbox 'Dauer' to data
    # @param data - dictionry where entries should be added
    def add_zustand_value(self, data):
        dauer = self.check_Dauer.GetValue()
        zust = self.label_Zustand.GetLabel()
        if zust == "Storno":
            data["Zustand"] = "Storno"
        elif dauer:
            data["Zustand"] = "Static"
        else:
            preis, zahlung, dummy = self.data.get_payment_values()
            print ("AfpDialog_SimpleInvoice.add_dauer_value:", preis, type(preis), zahlung, type(zahlung), dummy, data)
            if "BetragSI" in data or "ZahlBetrag" in data:
                if "ZahlBetrag" in data:
                    preis = data["ZahlBetrag"]
                else:
                    preis = data["BetragSI"]
            if zahlung < preis:
                data["Zustand"] = "Open"
            else:
                data["Zustand"] = "Closed"
        return data

    ## handle archiv entries of documents for obligations
    def handle_obligation_archiv(self):
        add = True
        wanted = False
        art = self.data.get_globals().get_value("name")
        if art[:3] == "Afp": art = art[3:]
        art = "Eingang " + art
        listname = self.data.get_listname()
        rows = self.data.get_value_rows("ARCHIV","Art,Typ,Gruppe,Datum,Extern")
        #print "AfpDialog_SimpleInvoice.handle_obligation_archiv:", rows
        if rows:
            fpath = None
            datum = Afp_fromString("1.1.1900") # assumtion: first entry not before 1.1.1900!
            for row in rows:
                if row[0] == art and listname in row[1] and row[2] == "Rechnungseingang" and row[3] > datum:
                    fpath = Afp_addRootpath(self.data.globals.get_value("archivdir"), row[4])
                    add = False
            if not add:
                if  self.check_Dauer.GetValue() and ("BetragSI" in self.changed_text or "ZahlBet" in self.changed_text):
                    add = AfpReq_Question("Eingangsrechnung wurde geändert!", "Soll neue Eingangsrechnung eingescannt und angehängt werden?")
                    wanted = True
                if not add:
                    if Afp_existsFile(fpath):
                        Afp_startFile(fpath,self.data.globals, self.debug)
                    else:
                        AfpReq_Info("Archiveintrag existiert, aber Datei ist nicht vorhanden!","")
        if add:
            if not wanted:
                wanted = AfpReq_Question("Bitte die Eingangsrechnung einscannen und die gescannte Datei auswählen!","")
            if wanted:
                fixed = {"Art": art, "Gruppe": "Rechnungseingang"}
                change = {"Eingangsdatum": self.data.get_globals().today_string(), "Bemerkung":""}
                data = AfpAdresse_addFileToArchiv(self.data, "Eingangsrechnung", fixed, change)
                if data:
                    self.data = data
                    self.data_changed = True
                    self.Set_Editable(True)
        
    ## execution in case the OK button ist hit - overwritten from AfpDialog
    def execute_Ok(self):
        self.close_dialog = True
        if self.data.is_new() and not "Kontierung" in self.changed_text:
            AfpReq_Info("Keine Kontierung angegeben,", "bitte nachholen!", "Fehlender Eintrag!")
            self.close_dialog = False
            return
        if self.data.is_new() and not "DatSI" in self.changed_text:
            self.changed_text.append("DatSI")
        data = {}
        for entry in self.changed_text:
            field, value = self.Get_TextValue(entry)
            data[field] = value
        if "Dauer" in self.checked_box or "Storno" in self.checked_box:
            data = self.add_zustand_value(data)
        #print("AfpDialog_SimpleInvoice.execute_Ok:", self.changed_text, data)
        if data:
            data = self.complete_data(data)
            self.data.set_data_values(data)
        if data or self.data_changed:
            self.data.store()
    ## complete data before storing
    # @param data - dictionary of changed values
    def complete_data(self, data):
        if  "BetragSI" in data:
            if not self.oblig and not "Netto" in data :
                data["Netto"] = Afp_toString(AfpFinance_stripTax(self.data.get_globals(), Afp_fromString(data["BetragSI"])))
            if not "ZahlBetrag" in data :
                data["ZahlBetrag"] = data["BetragSI"]
        if not "Zustand" in data and not self.data.get_value("Zustand"):
            data["Zustand"] = "Open"
        return data
        
    # Event Handlers 
    def On_Datum(self,event):
        if self.debug: print("Event handler `AfpDialog_SimpleInvoice.On_Datum'")
        object = event.GetEventObject()
        dat = object.GetValue()
        object.SetValue(Afp_ChDatum(dat))
        name = object.GetName()
        if not name in self.changed_text:
            self.changed_text.append(name)
        event.Skip()
        
    def In_SkPro(self,event):
        if self.debug: print("Event handler`AfpDialog_SimpleInvoice.In_SkPro'")
        valstring = self.text_SkPro.GetValue().strip()
        if not valstring:
            skonto = Afp_fromString(self.text_Skonto.GetValue())
            if skonto:
                self.set_payment_change(self.text_Skonto) 
            else:
                percent = self.data.get_globals().get_value("default-cash-discount","Finance")
                if not percent:
                    percent = 2
                valstring = Afp_toString(percent) + "%"
                self.text_SkPro.SetValue(valstring)
        event.Skip()
        
    def On_SkPro(self,event):   
        if self.debug: print("Event handler AfpDialog_SimpleInvoice.On_SkPro'")
        valstring = self.text_SkPro.GetValue().strip()
        if valstring[-1] == "%":
            valstring = valstring[:-1].strip()
        val = Afp_fromString(valstring)
        betrag = Afp_fromString(self.text_Betrag.GetValue())
        skonto  = int(val*betrag)/100.0
        print("AfpDialog_SimpleInvoice.On_SkPro:", val, "% von ", betrag, "ist",  skonto, "bleiben zu zahlen", betrag - skonto)
        self.text_Skonto.SetValue(Afp_toString(skonto))
        self.text_ZahlBet.SetValue(Afp_toString(betrag - skonto))
        event.Skip()

    ## event handler for payment changes
    def On_Skonto(self,event):
        if self.debug: print("Event handler `AfpDialog_SimpleInvoice.On_Skonto'")
        object = event.GetEventObject()
        self.set_payment_change(object)
        event.Skip()

    ## event handler for button 'Zahlung'
    def On_Zahlung(self,event):
        if self.debug: print("Event handler `AfpDialog_SimpleInvoice.On_Zahlung")
        ok, data = AfpLoad_DiFiZahl(self.data, None, True)
        if ok and data:
            self.data = data
            self.data_changed = True
            self.Set_Editable(True)
        event.Skip()
   
    ## event handler for button 'Neu'
    def On_Neu(self,event):
        if self.debug: print("Event handler AfpDialog_SimpleInvoice.On_Neu")
        KNr = None
        name = self.data.get_value("Name.Adresse")
        if self.oblig:
            text = "Bitte Adresse für neue Eingangsrechnung auswählen:"
        else:
            text = "Bitte Adresse für neue Rechnung auswählen:"
        KNr = AfpLoad_AdAusw(self.data.get_globals(),"ADRESSE","NamSort",name, None, text)
        if KNr:
            self.data.set_new(KNr)
            self.Populate()
            self.Set_Editable(True)
        event.Skip()
    
    ## event handler for button 'Stornierung'
    def On_Storno(self,event):
        if self.debug: print("AfpDialog_SimpleInvoice Event handler `On_Storno'")
        zu = self.data.get_value("Zustand")
        if zu == "Storno":
            zahl = self.data.get_value("Zahlung")
            if zahl and zahl >=  self.data.get_value("ZahlBetrag") - 0.01:
                self.data.set_value("Zustand", "Closed")
            else:
                self.data.set_value("Zustand", "Open")
        else:
            self.data.set_value("Zustand", "Storno")
        self.label_Zustand.SetLabel(self.data.get_string_value("Zustand"))
        self.On_Check(event)
        self.Set_Editable(True, True)
        #event.Skip()
        
    ## event handler for button 'Original'    
    def On_Original(self,event):
        if self.debug: print("Event handler AfpDialog_SimpleInvoice.On_Original'")
        if self.oblig:
            self.handle_obligation_archiv()
        else:
            print("Event handler`AfpDialog_SimpleInvoice.On_Original' not implemented!")
        event.Skip()

    ## event handler for checkbox 'Dauer'
    def On_Check(self,event):
        name = event.GetEventObject().GetName()
        if not name in self.checked_box:
            self.checked_box.append(name)
        event.Skip()

    ## event handler for button 'Drucken'
    def On_drucken(self,event):
        if self.debug: print("Event handler `On_drucken'")
        variables = {}
        prefix = self.data.get_listname() + "_"
        if self.oblig:
            header = "Rechnungseingang"
        else:
            header = "Rechnungsausgang"
        print("AfpDialog_SimpleInvoice.On_drucken:", header, self.data.view())
        AfpLoad_DiReport(self.data, self.data.get_globals(), variables, header, prefix)
        event.Skip()

    ## dummy event handler for panel dialogs
    def On_Dummy(self,event):
        print("Event handler `On_Dummy' not implemented!")
        event.Skip()

## loader routine for simple Invoice dialog 
# @param data - data to be edited with dialog
# @param new - flag if new data has to be created
def AfpLoad_SimpleInvoice(data, new = False):
    DiRech = AfpDialog_SimpleInvoice(data.is_outgoing())
    DiRech.attach_data(data, new)
    DiRech.ShowModal()
    Ok = DiRech.get_Ok()
    DiRech.Destroy()
    return Ok
    
## routine to fill new Invoice data
# @param data - data to be reset to new and edited
def Afp_newSimpleInvoice(data):
    KNr = None
    name = data.get_value("Name.Adresse")
    if data.is_outgoing():
        text = "Bitte Adresse für neue Eingangsrechnung auswählen:"
    else:
        text = "Bitte Adresse für neue Rechnung auswählen:"
    KNr = AfpLoad_AdAusw(data.get_globals(),"ADRESSE","NamSort",name, None, text)
    if KNr:
        data.set_new(KNr)
        Ok = AfpLoad_SimpleInvoice(data, True)
    else:
        Ok = False
    return Ok
  

