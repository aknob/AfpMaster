#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvDialog
# AfpEvDialog module provides the dialogs and appropriate loader routines needed for eventhandling
#
#   History: \n
#       15 May 2018 - inital code generated - Andreas.Knoblauch@afptech.de \n

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright© 1989 - 2019 afptech.de (Andreas Knoblauch)
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
from AfpBase.AfpDatabase import AfpSuperbase
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpBaseDialog import *
from AfpBase.AfpBaseDialogCommon import *
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_DiAdEin_fromKNr, AfpAdresse_addAttributToAdresse
from AfpBase.AfpBaseAdRoutines import AfpAdresse_getAddresslistOfAttribut
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

import AfpEvent
from AfpEvent import AfpEvRoutines
from AfpEvent.AfpEvRoutines import *

## select a location as departure point and modify route \n
# return the row of location data selected
# @param afproute - AfpEvRoute Selection List which holds route data
# @param typ - typ of list to start with
# @param allow_new - add line to allow the selection that a new location entries are possible
def AfpEv_selectLocation(afproute, typ = None, allow_new = True):
    row = None
    add_to_route = False
    if typ is None:
        typ = ""
        list,idents = afproute.get_sorted_location_list('routeNoRaste', allow_new)
        name = "Route: " + afproute.get_value("Name")
        value, Ok = AfpReq_Selection(name, "Bitte Zustiegsort auswählen!".decode("UTF-8"), list, "Zustieg auswählen".decode("UTF-8"), idents)
        if Ok and value == -10: typ = "routeOnlyRaste"
        if Ok and value == -12: typ = "allNoRoute"
    if typ == "routeOnlyRaste":
        list, idents = afproute.get_sorted_location_list('routeOnlyRaste')
        value, Ok = AfpReq_Selection("Bitte Raststätte auswählen".decode("UTF-8"), "auf der der Zustieg erfolgt.", list, "Zustieg auf Raststätte".decode("UTF-8"), idents)
    elif typ == "allNoRoute" or typ == "all":
        list, idents = afproute.get_sorted_location_list(typ, allow_new)
        value, Ok = AfpReq_Selection("Bitte Ort auswählen".decode("UTF-8"), "an dem der Zustieg erfolgt.", list, "Zustiegsort".decode("UTF-8"), idents)
        if Ok and value == -11:
            #print "AfpDialog_EvClientEdit.On_CBOrt value = -11", allow_new
            ort, ken = AfpEv_editLocation()
            if ort and ken: 
                for i, entry in enumerate(list):
                    check = entry.split("[")[0].strip()
                    if check == ort: value = idents[i]
                if value < 0:
                    row = [-1, ort, ken]
        if typ == "allNoRoute" and Ok and (value > 0 or (value == -11 and row)):
            ok2 = AfpReq_Question("Ausgewählten Ort in die Route aufnehmen?".decode("UTF-8"),"","Route")
            if ok2: add_to_route = True
    #print "AfpDialog_EvClientEdit.On_CBOrt Ok:", value, Ok
    if Ok and value > 0: # location in route selected
        row = afproute.get_location_data(value)
        if add_to_route: 
            afproute.add_location_to_route(value)
    if Ok and value == -11 and row: # new location created
        if add_to_route:
            afproute.add_new_route_location(row[0], row[1])
        else:
            afproute.add_new_location(row[0], row[1])
    return row
    
## edit a location entry
# @param ort - name of location
# @param ken - short name of location
def AfpEv_editLocation(ort = "", ken = ""):
    res = AfpReq_MultiLine("Bitte Zustiegsort und Kennung (2 Buchstaben) eingeben.", "Kennung 'RA' für Raststätte.".decode("UTF-8"), "Text", [["Ort:", ort], ["Kennung:", ken]],"Eingabe Zustiegsort")
    if res and len(res) > 1: return res[0].strip(), res[1].strip()
    else: return None, None
## create a copy of the actuel tour with selection of parts to be copied
# @param data - tour data to be copied
def AfpEvent_copy(data):
    if data.is_debug(): print "AfpEvent_copy: copy Event data!"
    if AfpEvent_isVerein(data.get_value("Art")):
        data.set_new(True)
        return data
    elif AfpEvent_isTour(data.get_value("Art")):
        typ = "Reise"
        liste = ["Beginn/Ende","Veranstalter,Transferroute","Preise","Zusatzbeschreibung","Reisedaten"]
    else:
        typ = "Veranstaltung"
        liste = ["Datum/Uhrzeit","Veranstalter,Veranstaltungsort","Preise","Zusatzbeschreibung","Veranstaltungsdaten"]
    text1 =  "Soll eine Kopie der aktuellen " + typ + " erstellt werden?"
    text2 = "Bitte auswählen was übernommen werden soll,\n'Abbruch' kopiert alles bis auf Zeiten und Zusatzbeschreibung".decode("UTF-8")
    keep_flags = AfpReq_MultiLine(text1, text2, "Check", liste, typ +" kopieren?", 350)
    if keep_flags:
        data.set_new(keep_flags)
        return data
    else:
        return None
## create a copy of the actuel EvClient may be made completely or partly
# @param data - tourist data to be copied
# @param preset - if given no checkbox dialog is displayed and flags are delivered to set_new
def AfpEvClient_copy(data, preset = None):
    KNr = None
    keep_flags = None
    name = data.get_value("Name.Adresse")
    text = "Bitte Kunden für neue Anmeldung auswählen:"
    KNr = AfpLoad_AdAusw(data.get_globals(),"ADRESSE","NamSort",name, None, text)
    if KNr:
        if preset is None:
            text1 = "Soll eine Kopie der aktuellen Anmeldung erstellt werden?"
            text2 = "Wenn Ja, bitte auswählen was übernommen werden soll.".decode("UTF-8")
            liste = ["Rechnungsnummer (Mehrfachanmeldung)", "Reisebüro".decode("UTF-8"), "Fahrtextras", "Sonstige Daten"]
            keep_flags = AfpReq_MultiLine(text1, text2, "Check", liste, "Anmeldung kopieren?", 350)
        else:
            keep_flags = preset
        data.set_new(None, KNr, keep_flags)
        return data
    else:
        return None

## dialog for selection of tour data \n
# selects an entry from the EVENT table
class AfpDialog_EvAusw(AfpDialog_Auswahl):
    ## initialise dialog
    def __init__(self, flavour = None):
        self.flavour = flavour
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.typ = "Veranstaltungsauswahl"
        if self.flavour == "Tourist":
            self.typ = "Reiseauswahl"
        self.datei = "EVENT"
        self.modul = "Event"
        
    ## get the definition of the selection grid content \n
    # overwritten for "Event" use
    def get_grid_felder(self): 
        if self.flavour == "Verein":
            Felder = [["Kennung.EVENT",15], 
                                ["Bez.EVENT",75],
                                ["Anmeldungen.EVENT",10], 
                                ["EventNr.EVENT",None]] # Ident column
        else:
            Felder = [["Beginn.EVENT",15], 
                                ["Uhrzeit.EVENT", 15], 
                                ["Bez.EVENT",50], 
                                ["Kennung.EVENT",15], 
                                ["Anmeldungen.EVENT",5], 
                                ["EventNr.EVENT",None]] # Ident column
            if self.flavour == "Tourist":
                Felder[1] =  ["Ende.EVENT", 15]
        return Felder
    ## invoke the dialog for a new entry \n
    # overwritten for "Event" use
    def invoke_neu_dialog(self, globals, eingabe, filter):
        superbase = AfpSuperbase.AfpSuperbase(globals, debug)
        superbase.open_datei("EVENT")
        superbase.CurrentIndexName("Bez")
        superbase.select_key(eingabe)
        return AfpLoad_EventEdit_fromSb(globals, superbase, eingabe)      
 
## loader routine for event selection dialog 
# @param globals - global variables including database connection
# @param index - column which should give the order
# @param flavour - if given, flavour (certain type) of dialog 
# @param value -  if given,initial value to be searched
# @param where - if given, filter for search in table
# @param ask - flag if it should be asked for a string before filling dialog
def AfpLoad_EvAusw(globals, index, flavour = None, value = "", where = None, ask = False):
    result = None
    Ok = True
    #print "AfpLoad_EvAusw input:", index, value, where, ask
    if ask:
        sort_list = AfpEvClient_getOrderlistOfTable(globals.get_mysql(), index)        
        if flavour == "Tourist": name = "Reise"
        elif flavour == "Verein": name = "Sparten"
        else:  name = "Veranstaltungs"    
        value, index, Ok = Afp_autoEingabe(value, index, sort_list, name)
        #print "AfpLoad_EvAusw index:", index, value, Ok
    if Ok:
        DiAusw = AfpDialog_EvAusw(flavour)
        if flavour == "Tourist": text = "Bitte Reise auswählen:".decode("UTF-8")     
        elif flavour == "Verein": text = "Bitte Sparte auswählen:".decode("UTF-8")     
        else: text = "Bitte Veranstaltung auswählen:".decode("UTF-8")        
        DiAusw.initialize(globals, index, value, where, text)
        DiAusw.ShowModal()
        result = DiAusw.get_result()
        DiAusw.Destroy()
    elif Ok is None:
        # flag for direct selection
        result = Afp_selectGetValue(globals.get_mysql(), "EVENT", "EventNr", index, value)
    return result      

## allows the display and manipulation of an event 
class AfpDialog_EventEdit(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        self.change_data = False
        AfpDialog.__init__(self,*args, **kw)
        self.lock_data = True
        self.agent = None
        self.active = None
        self.routes = None
        self.routenr = None
        self.route = None
        self.has_route = False
        self.is_multidays = False
        self.SetSize((592,290))
        self.SetTitle("Veranstaltung")
        self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
        if self.debug: print "AfpDialog_EventEdit.init flavour:", self.flavour
        
    ## set up dialog widgets - overwritten from AfpDialog
    def InitWx(self):
        self.panel = wx.Panel(self, -1)
        panel = self.panel
        self.label_T_Dat = wx.StaticText(panel, -1, label="&Datum", pos=(16,44), size=(50,20), name="T_Dat")
        self.text_Datum = wx.TextCtrl(panel, -1, value="", pos=(76,42), size=(80,22), style=0, name="Datum")
        self.vtextmap["Datum"] = "Beginn.EVENT"
        self.text_Datum.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Datum)
        self.label_TZeit= wx.StaticText(panel, -1, label="&Zeit", pos=(162,44), size=(28,20), name="TZeit")
        self.text_Zeit = wx.TextCtrl(panel, -1, value="", pos=(196,42), size=(80,22), style=0, name="Zeit")
        self.vtextmap["Zeit"] = "Uhrzeit.EVENT"
        self.text_Zeit.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Zeit2)
        self.label_T_Bez = wx.StaticText(panel, -1, label="&Bez:", pos=(16,14), size=(50,18), name="T_Bez")
        self.text_Bez = wx.TextCtrl(panel, -1, value="", pos=(76,12), size=(200,22), style=0, name="Bez")
        self.textmap["Bez"] = "Bez.EVENT"
        self.text_Bez.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_T_Kenn = wx.StaticText(panel, -1, label="&EventNr:", pos=(280,14), size=(60,18), name="T_Kenn")
        self.text_Kenn = wx.TextCtrl(panel, -1, value="", pos=(350,12), size=(80,22), style=0, name="Kenn")
        self.textmap["Kenn"] = "Kennung.EVENT"
        self.text_Kenn.Bind(wx.EVT_SET_FOCUS, self.On_setKenn)
        self.text_Kenn.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_Anmeldungen = wx.StaticText(panel, -1, label="", pos=(458,12), size=(24,18), name="Anmeldungen")
        self.labelmap["Anmeldungen"] = "Anmeldungen.EVENT"
        self.label_TTeil = wx.StaticText(panel, -1, label="Teilnehmer", pos=(484,12), size=(78,18), name="TTeil")
        self.label_T_Personen = wx.StaticText(panel, -1, label="&max.:", pos=(460,42), size=(42,18), name="T_Personen")
        self.text_Personen = wx.TextCtrl(panel, -1, value="", pos=(510,40), size=(44,22), style=0, name="Personen")
        self.textmap["Personen"] = "Personen.EVENT"
        self.text_Personen.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_TBem = wx.StaticText(panel, -1, label="&Zusatz:", pos=(10,74), size=(56,18), name="TBem")
        self.text_Bem = wx.TextCtrl(panel, -1, value="", pos=(74,72), size=(480,40), style=wx.TE_MULTILINE|wx.TE_LINEWRAP, name="Bem")
        self.textmap["Bem"] = "Bem.EVENT"
        self.text_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
 
        self.list_Preise = wx.ListBox(panel, -1, pos=(298,120), size=(258,86), name="Preise")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Preise, self.list_Preise)
        self.listmap.append("Preise")
        #self.label_T_Art = wx.StaticText(panel, -1, label="Art:", pos=(16,130), size=(50,18), name="T_Art")
        #self.choice_Art = wx.Choice(panel, -1,  pos=(78,120), size=(198,30),  choices=AfpEvClient_possibleEventKinds(),  name="CArt")      
        #self.choicemap["CArt"] = "Art.EVENT"
        #self.Bind(wx.EVT_CHOICE, self.On_CArt, self.choice_Art)  
        self.label_T_Ort = wx.StaticText(panel, -1, label="Ort:", pos=(16,130), size=(50,18), name="T_Ort")
        self.choice_Ort = wx.Choice(panel, -1,  pos=(78,120), size=(198,30),  choices="",  name="COrt")      
        self.choicemap["COrt"] = "Route.EVENT"
        self.Bind(wx.EVT_CHOICE, self.On_COrt, self.choice_Ort)  
        self.label_T_Agent = wx.StaticText(panel, -1, label="Agent:", pos=(16,190), size=(50,18), name="T_Agent")
        self.label_AgentName = wx.StaticText(panel, -1, label="", pos=(78,190), size=(198,30), name="AgentName")
        self.labelmap["AgentName"] = "AgentName.EVENT"
        self.check_Kopie = wx.CheckBox(panel, -1, label="Kopie", pos=(10,226), size=(70,20), name="Kopie")
        self.button_Neu = wx.Button(panel, -1, label="&Neu", pos=(80,220), size=(90,30), name="Neu")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)
        self.button_Agent = wx.Button(panel, -1, label="&Agent", pos=(180,220), size=(90,30), name="Verst")
        self.Bind(wx.EVT_BUTTON, self.On_Agent, self.button_Agent)
        self.button_IntText = wx.Button(panel, -1, label="Te&xt", pos=(300,220), size=(80,30), name="IntText")
        self.Bind(wx.EVT_BUTTON, self.On_Text, self.button_IntText)
        self.setWx(panel, [390, 220, 80, 30], [480, 220, 80, 30]) # set Edit and Ok widgets

    ## attaches data to this dialog, invokes population of widgets (overwritten from AfpDialog)
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        if new:
            self.is_multidays = data.is_multidays()
            self.has_route = data.has_route()
            if self.flavour == "Tourist":
                self.is_multidays = True
        super(AfpDialog_EventEdit, self).attach_data(data, new, editable)
        if self.new: self.Pop_label()
 
    ## read values from dialog and invoke writing into data         
    def store_data(self):
        self.Ok = False
        data = {}
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        if not self.agent is None:
            data = self.add_agent_data(data)
        if self.route:  
            if self.route < 0:
                self.add_new_route()
            data["Route"] = self.route
        #print "AfpDialog_EventEdit.store_data data:",self.new,self.change_data, data
        if data or self.change_data:
            if self.new:
                data = self.complete_data(data)
                self.data.add_afterburner("PREISE", "Kennung = 100*EventNr + PreisNr")
            self.data.set_data_values(data, "EVENT")
            #self.data.mysql.set_debug()
            self.data.store()
            #self.data.mysql.unset_debug()
            self.Ok = True
        self.changed_text = []   
        self.change_data = False  
     
    ## complete data if plain dialog has been started
    # @param data - SelectionList where data has to be completed
    def complete_data(self, data):
        # all flavours preprocessing
        data["Anmeldungen"] = 0
        if not "Art" in data: 
            if self.flavour:
                data["Art"] = self.flavour
            else: 
                data["Art"] = "Event"
        if not "Beginn" in data: data["Beginn"] = self.data.globals.today()
        # special treatment for dofferent flavours
        if self.flavour is None: # self.flavour == "Event"
            data["ErloesKt"] = "ERL"
        elif self.flavour == "Touristik":
            if not "Kostenst" in data:
                if "Kennung" in data: data["Kostenst"] = Afp_intString(data["Kennung"])
            if not "Kennung" in data: 
                data["Kennung"] = ""
                if self.agent:
                    Kst = self.data.get_value("Kostenst")
                    if "Kostenst" in data: Kst = data["Kostenst"]
                    if Kst: data["Kennung"] = Afp_toString(Kst)
            if "Beginn" in data: 
                month = Afp_toString(data["Beginn"].month)
                if len(month) == 1: month = "0" + month
                data["ErloesKt"] = "ERL" + month  # ErloesKt nicht nur für Touristik (verschiedene Möglichkeiten über globals?)
        # all flavours postprocessing
        if not "Personen" in data: data["Personen"] = 0
        if not "Kostenst" in data: data["Kostenst"] = 0
        return data
        
    ## create a new route entry
    def add_new_route(self):
        rname = self.routes[self.routenr.index(self.route)]
        sel = self.data.get_selection("TNAME")
        sel.new_data(False, True) 
        sel.set_value("Name", rname)
 
    ## add additonal agent data, if agent has been changed
    # @param data - data where additional data is added
    def add_agent_data(self, data):
        if self.agent:
            data["AgentNr"] = self.agent.get_value("KundenNr")
            data["AgentName"] = self.agent.get_name(True)
            data["Kreditor"] = self.agent.get_account("Kreditor")
            data["Debitor"] = self.agent.get_account("Debitor")
        elif "AgentNr" in data or self.data.get_value("AgentNr"):
            # agent entry has been deleted
            data["AgentNr"] = None
            data["AgentName"] = None
            data["Kreditor"] = None
            data["Debitor"] = None
        return data
        
    ## dis-/enable wigdets according to kind of event
    # @param kind - kind for which widgets should be set
    def set_kind_widgets(self, kind):
        self.is_multidays = self.data.is_multidays(kind)
        ed_flag = self.is_editable()
        if self.agent and kind == "Reise":
            self.choice_Ort.Enable(False)
        else: # kind == "Event" or (self.agent and kind =="Reise")
            self.choice_Ort.Enable(ed_flag)
        if self.is_multidays:
            # set multi day labels
            self.label_TZeit.SetLabel("&Ende")
            self.vtextmap["Zeit"] = "Ende.EVENT"
        else:
            self.label_TZeit.SetLabel("&Zeit")
            self.vtextmap["Zeit"] = "Uhrzeit.EVENT"
            
    ## handle route selection
    def select_Route(self):
        sel = self.choice_Ort.GetCurrentSelection() 
        #print "AfpDialog_EventEdit.On_CRoute sel:", sel
        if sel:
            self.route = self.routenr[sel-1]
        else: # sel == 0 => generate new entry
            Ok, rname, KNr = self.get_new_route_name()
            if Ok and rname:
                self.choice_Ort.Append(rname)
                self.routes.append(rname)
                if KNr:
                    self.route = KNr
                else:
                    lastnr = 0
                    if len(self.routenr) and self.routenr[-1] < 0:
                        lastnr = self.routenr[-1]
                    self.route = lastnr-1
                #print"AfpDialog_EventEdit.On_CRoute:", self.route
                self.routenr.append(self.route)
                self.choice_Ort.SetSelection(len(self.routes))
            else:
                # reset
                if self.route: route = self.route
                else: route = self.data.get_value("Route")
                if route in self.routenr:
                    ind = self.routenr.index(route) + 1
                    self.choice_Ort.SetSelection(ind)
                    
    ## fill in available route data
    # may be overwritten in devired dialog
    def get_route_data(self):
        routes, routenr = AfpAdresse_getAddresslistOfAttribut(self.data.get_globals(), "Veranstaltungsort")
        routetext =" --- Neuer Veranstaltungsort --- "
        return routes, routenr, routetext
 
    ## handle dialog to get new route name
    # may be overwritten in devired dialog
    def get_new_route_name(self):
        Ok = False
        rname = None
        KNr = AfpLoad_AdAusw(self.data.get_globals(),"ADRESATT","AttName", "", "Attribut = \"Veranstaltungsort\"", "Bitte Adresse des neuen Veranstaltungsortes auswählen.".decode("UTF-8"))
        #rname, KNr = AfpAdresse_addAttributToAdresse(self.data.get_globals(),"Veranstaltungsort","Bitte Adresse des neuen Veranstaltungsortes auswählen.".decode("UTF-8"))
        if KNr: 
            adresse = AfpAdresse(self.data.get_globals(), KNr, None, self.data.get_globals().is_debug())
            rname = adresse.get_name()
            Ok = True
        if Ok and rname and rname in self.routes:
            AfpReq_Info("Name schon in Ortsliste enthalten!","Bitte dort auswählen.".decode("UTF-8"),"Warnung")
            Ok = False
        return Ok, rname, KNr

    ## execution in case the OK button ist hit - overwritten from AfpDialog
    def execute_Ok(self):
        self.store_data()
    
    ## population routine for choices
    # overwritten from AfpDialog
    def Pop_choice(self):
        #value = self.data.get_string_value(self.choicemap["CArt"])
        #self.choice_Art.SetStringSelection(value)
        value = self.data.get_value(self.choicemap["COrt"])
        #print "AfpDialog_EventEdit.Pop_choice:", self.has_route, self.routenr, self.routes, value
        if not self.has_route and self.routenr and value in self.routenr:
            self.choice_Ort.SetStringSelection(self.routes[self.routenr.index(value)])
        else:
            #print "AfpDialog_EventEdit.Pop_choice set selection:", Afp_toString(value)
            self.choice_Ort.SetStringSelection(Afp_toString(value))
            
        # -> ersetze letzte Zuweisung
        # if self.is_multidays() and self.data.get_globals(().get_value("multidays_has_route","Event"):
        
    ## populate the 'Preise' list, \n
    # this routine is called from the AfpDialog.Populate
    # @param liste - if given prefilled list for display, initial value is ommitted
    def Pop_Preise(self, liste=[]):
        rows = self.data.get_value_rows("PREISE", "Preis,Anmeldungen,Plaetze,Bezeichnung,Kennung,Typ,PreisNr")
        if len(liste) == 0:
            liste = ["--- Neuen Preis hinzufügen ---".decode("UTF-8")]
        #print "AfpDialog_EventEdit.Pop_Preise:", rows
        self.maxPreis = 0
        if rows:
            for row in rows:
                if row[6] > self.maxPreis: self.maxPreis = row[6]
                if row[5] == "Aufschlag": Plus = "+"
                else: Plus = " "
                if row[1] or row[2]:
                    if row[1] is None: row[1] = 0
                    middle = Afp_toString(row[1]).rjust(4) + Afp_toString(row[2]).rjust(3)
                else:
                    middle = "       "
                liste.append(Plus + Afp_toFloatString(row[0]).rjust(10) + middle + "  " + Afp_toString(row[3]))
        self.list_Preise.Clear()
        self.list_Preise.InsertItems(liste, 0)
        if not self.data.get_value("Route"):
            self.choice_Ort.SetSelection(0)

    ## event handler when window is activated
    # @param event - event which initiated this action   
    def On_Activate(self,event):
        if self.active is None:
            if self.debug: print "AfpDialog_EventEdit Event handler `On_Activate'"
            self.active = True
            self.routes, self.routenr, routetext = self.get_route_data()
            self.choice_Ort.Append(routetext)
            for route in self.routes:
                self.choice_Ort.Append(Afp_toString(route))
            self.Pop_choice()
            if self.new and self.data.get_globals().get_value("edit-date-first","Event"): 
                self.On_Set_Datum()
                if self.text_Datum.GetValue() == "":
                    self.text_Datum.SetFocus()

    ## Eventhandler TEXT-KILLFOCUS - check date syntax 
    # @param event - event which initiated this action 
    def On_Check_Zeit2(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_Check_Ende'" 
        if self.is_multidays:
            On_Check_Datum(event)
        else:
            object = event.GetEventObject()
            zeit = object.GetValue()
            time, days = Afp_ChZeit(zeit)
            if time:
                object.SetValue(time)
            self.On_KillFocus(event)
            event.Skip()
        
    ## Eventhandler TEXT-KILLFOCUS - check date syntax 
    # @param event - event which initiated this action 
    def On_Check_Datum(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_Check_Datum'" 
        object = event.GetEventObject()
        datum = object.GetValue()
        date = Afp_ChDatum(datum)
        object.SetValue(date)
        self.On_KillFocus(event)
        event.Skip()
        
    ## Eventhandler BUTTON - graphic pick for dates 
    # @param event - event which initiated this action   
    def On_Set_Datum(self,event = None):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_Set_Datum'"
        if not self.flavour == "Verein":
            start = self.text_Datum.GetValue()
            if start: start = Afp_ChDatum(start)
            x, y = self.text_Datum.ScreenPosition
            #x += self.text_Datum.GetSize()[0]
            y += self.text_Datum.GetSize()[1]
            if self.is_multidays:
                ende= self.text_Zeit.GetValue()
                if ende: ende = Afp_ChDatum(ende)
                dates = AfpReq_Calendar((x, y), [start, ende],  "Veranstaltungsdatum", None, ["Beginn", "0:Ende"])
            else:
                dates = AfpReq_Calendar((x, y), [start],  "Veranstaltungsdatum", None, ["Beginn"])
            if dates:
                self.text_Datum.SetValue(dates[0])
                self.choice_Edit.SetSelection(1)
                self.Set_Editable(True)
                self.text_Datum.SetFocus()
                if not "Datum" in self.changed_text: self.changed_text.append("Datum")
                if len(dates) > 1:
                    self.text_Zeit.SetValue(dates[1])
                    if not "Zeit" in self.changed_text: self.changed_text.append("Zeit")
                    self.text_Zeit.SetFocus()
        if event: event.Skip()

    ## Eventhandler BUTTON - select tour agent for not self organisied tours
    # @param event - event which initiated this action   
    def On_Agent(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_Agent'"
        name = self.data.get_value("AgentName")
        if not name: name = "a"
        if self.data.is_tour():
            text = "Bitte den Veranstalter der Reise auswählen:"
            filter = "Attribut = \"Reiseveranstalter\""
        else:
            text = "Bitte den Veranstalter auswählen:"
            filter = "Attribut = \"Veranstalter\""
        #self.data.globals.mysql.set_debug()
        KNr = AfpLoad_AdAusw(self.data.get_globals(),"ADRESATT","AttName",name, filter, text)
        #self.data.globals.mysql.unset_debug()
        #print "AfpDialog_EventEdit.On_Agent:", KNr
        if KNr:
            self.agent = AfpAdresse(self.data.get_globals(),KNr)
            self.label_AgentName.SetLabel(self.agent.get_name())
        else:
            self.agent = False
        event.Skip()
    
    ## Eventhandler TEXT-KILLFOCUS - set 'Kennung' from input
    # @param event - event which initiated this action 
    def On_setKenn(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_setKenn'"
        kennung = None
        preset = self.data.get_globals().get_value("preset-event-identifier","Event")
        if preset and not self.text_Kenn.GetValue() :
            kennung = self.get_kenn_preset(preset)
        if kennung: self.text_Kenn.SetValue(kennung)
        event.Skip()

    ## get preset value for 'Kennung' 
    # @param preset - preset string to be used
    def get_kenn_preset(self, preset):
        kennung = None
        if preset and self.text_Datum.GetValue():
            date = Afp_fromString(self.text_Datum.GetValue())
            kennung  = Afp_toDateString(date, preset)
        return kennung
        
    ## Eventhandler TEXT-KILLFOCUS - set 'Kst' from input for self organised tours 
    # @param event - event which initiated this action 
    def On_setKst(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_setKst'"
        if not "Kenn" in self.changed_text: self.changed_text.append("Kenn")
        nr = Afp_fromString(self.text_Kenn.GetValue())
        if nr and  Afp_isInteger(nr):
            kst = self.text_Kst.GetValue()
            Ok = False
            if kst == "": 
                Ok = True
            elif nr == int(nr) and Afp_fromString(kst) != nr:
                Ok = AfpReq_Question("Konto unterscheidet sich von Veranstaltungskennung,","Konto anpassen?","Veranstaltungskontierung")
            if Ok:
                self.text_Kst.SetValue(Afp_toString(nr))
                if not "Kst" in self.changed_text: self.changed_text.append("Kst")
        event.Skip()

    ## Eventhandler LIST-DOUBLECLICK - modify selected price
    # @param event - event which initiated this action   
    def On_Preise(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_Preise'"
        data = self.data
        Ok = True
        index = self.list_Preise.GetSelections()[0] - 1
        if index < 0: 
            index = None
        if Ok:
            data = AfpLoad_EventPrices(data, index)
            if data: 
                self.data = data
                self.change_data = True
                self.Pop_Preise()
        event.Skip()

    ## Eventhandler BUTTON - generate new tour entrys
    # @param event - event which initiated this action   
    def On_Neu(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_Neu'"
        copy = self.check_Kopie.GetValue()
        data = None
        if copy:
            data = AfpEvent_copy(self.data)
            if data: 
                self.data = data
            else:  
                self.data.set_new(True)
            self.change_data = True
        else:
            self.data.set_new()
        self.new = True
        self.Populate()
        self.Set_Editable(True)
        if self.data.get_globals().get_value("edit-date-first","Event"):
            self.On_Set_Datum()
        event.Skip()

    ## Eventhandler BUTTON - change additional free text of tour
    # @param event - event which initiated this action   
    def On_Text(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_Text'"
        if self.flavour == "Verein":
            oldtext = self.data.get_string_value("Bem.EVENT")
            text, ok = AfpReq_EditText(oldtext, "Zusatzinformation")
        else:
            oldtext = self.data.get_string_value("IntText.EVENT")
            text, ok = Afp_editExternText(oldtext, self.data.get_globals())
        #print "AfpDialog_EditEvent.On_Text:",ok, text
        if ok: 
            if self.flavour == "Verein":
                self.data.set_value("Bem.EVENT", text)
            else:
                self.data.set_value("IntText.EVENT", text)
            self.change_data = True
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()

    ## Eventhandler CHOICE - enable/disable widgets according to choice value
    # @param event - event which initiated this action   
    def On_CArt(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_CArt'"
        kind = self.choice_Art.GetStringSelection()
        self.data.set_value("Art", kind)
        self.change_data = True
        self.set_kind_widgets(kind)
        self.Refresh()
        event.Skip()
        
    ## Eventhandler CHOICE - handle route selection
    # @param event - event which initiated this action   
    def On_COrt(self,event):
        if self.debug: print "AfpDialog_EventEdit Event handler `On_COrt'"
        sel = self.choice_Ort.GetCurrentSelection() 
        #print "AfpDialog_EventEdit:", sel, type(sel)
        if sel: 
            self.route = self.routenr[sel-1]
        else:
            self.select_Route()
        event.Skip()
    
# end of class AfpDialog_EventEdit

## loader routine for dialog EventEin
# @param data - AfpEvent data to be loaded
# @param flavour - if given, flavour (certain type) of dialog 
# @param edit - if given, flag if dialog should open in edit modus
def AfpLoad_EventEdit(data, flavour = None, edit = False):
    DiEventEin = AfpDialog_EventEdit(flavour)
    new = data.is_new()
    DiEventEin.attach_data(data, new, edit)
    DiEventEin.ShowModal()
    Ok = DiEventEin.get_Ok()
    DiEventEin.Destroy()
    return Ok
    
## loader routine for dialog EventEin according to the given superbase object \n
# @param globals - global variables holding database connection
# @param sb - AfpSuperbase object, where data can be taken from
# @param flavour - if given, flavour (certain type) of dialog 
# @param edit - if given, flag if dialog should open in edit modus
def AfpLoad_EventEdit_fromSb(globals, sb, flavour = None, edit = False):
    Event = AfpEvent(globals, None, sb, sb.debug, False)
    if sb.eof(): 
        Event.set_new(True)
    return AfpLoad_EventEdit(Event, flavour, edit)
## loader routine for dialog DiChEin according to the given charter identification number \n
# @param globals - global variables holding database connection
# @param EventNr -  identification number of charter to be filled into dialog
def AfpLoad_EventEdit_fromFNr(globals, EventNr):
    Event = AfpEvent(globals, EventNr)
    flavour = Event.get_value("Art")
    if flavour == "Event": flavour = None
    return AfpLoad_EventEdit(Event, flavour)
 
 ## allows the display and manipulation of a tour price entry
class AfpDialog_EventPrices(AfpDialog):
    def __init__(self, *args, **kw):
        AfpDialog.__init__(self,None, -1, "")
        self.typ = None
        self.noPrv = None
        self.SetSize((484,163))
        self.SetTitle("Preis ändern".decode("UTF-8"))

    ## set up dialog widgets - overwritten from AfpDialog
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.label_T_Fuer = wx.StaticText(panel, -1, label="für".decode("UTF-8"), pos=(20,10), size=(24,18), name="T_Fuer")
        self.label_T_BezEv = wx.StaticText(panel, -1, pos=(50,10), size=(160,20), name="T_BezEv")
        self.labelmap["T_BezEv"] = "Bez.EVENT"
        self.label_Anmeld = wx.StaticText(panel, -1, pos=(220,10), size=(20,20), name="Anmeld")
        self.label_T_Anmeld = wx.StaticText(panel, -1, label="Anmeldungen", pos=(250,10), size=(120,20), name="T_Anmeld")
        self.label_T_Bez = wx.StaticText(panel, -1, label="&Bezeichnung:", pos=(20,42), size=(90,18), name="T_Bez")
        self.text_Bez = wx.TextCtrl(panel, -1, value="", pos=(120,40), size=(250,22), style=0, name="Bez")
        self.textmap["Bez"] = "Bezeichnung.Preise"
        self.text_Bez.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_T_Preis = wx.StaticText(panel, -1, label="&Preis:", pos=(70,72), size=(40,18), name="T_Preis")
        self.text_Preis = wx.TextCtrl(panel, -1, value="", pos=(120,70), size=(100,22), style=0, name="Preis")        
        self.vtextmap["Preis"] = "Preis.Preise"
        self.text_Preis.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_T_Plaetze = wx.StaticText(panel, -1, label="Pl&ätze:".decode("UTF-8"), pos=(240,72), size=(50,18), name="T_Plaetze")
        self.text_Plaetze = wx.TextCtrl(panel, -1, value="", pos=(300,70), size=(70,22), style=0, name="Plaetze")
        self.vtextmap["Plaetze"] = "Plaetze.Preise"
        self.text_Plaetze.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)

        self.choice_Typ = wx.Choice(panel, -1,  pos=(40,100), size=(180,25),  choices=["Grund","Aufschlag"],  name="CTyp")      
        self.choicemap["CTyp"] = "Typ.Preise"
        self.Bind(wx.EVT_CHOICE, self.On_CTyp, self.choice_Typ)  
        self.check_NoPrv = wx.CheckBox(panel, -1, label="ohne Pro&vision", pos=(248,104), size=(122,18), name="NoPrv")
        self.Bind(wx.EVT_CHECKBOX, self.On_CBNoPrv, self.check_NoPrv) 
        self.button_Loeschen = wx.Button(panel, -1, label="&Löschen".decode("UTF-8"), pos=(400,48), size=(75,36), name="Löoechen")
        self.Bind(wx.EVT_BUTTON, self.On_Preise_delete, self.button_Loeschen)
 
        self.setWx(panel, [400, 6, 75, 36], [400, 90, 75, 36]) # set Edit and Ok widgets

    ## attach data to dialog and invoke population of the graphic elements
    # @param data - AfpEvent object to hold the data to be displayed
    # @param index - if given, index of row of price to be displayed in data.selections["Preise"]
    def attach_data(self, data, index):
        art = data.get_value("Art")
        if data.get_value("Art") == "Verein": 
            self.check_NoPrv.SetLabel("&Einmalig")
        self.data = data
        self.debug = self.data.debug
        self.index = index
        self.new = (index is None)
        self.Populate()
        self.Set_Editable(self.new, True)
        if self.new:
            self.typ = "Grund"
            self.noPrv = False
            self.choice_Edit.SetSelection(1)
    
    ## execution in case the OK button ist hit - overwritten from AfpDialog
    def execute_Ok(self):
        self.store_data()

   ## read values from dialog and invoke writing into data         
    def store_data(self):
        self.Ok = False
        data = {}
        #print "AfpDialog_EventPrices.store_data changes:", self.changed_text
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        if not self.typ is None:
            data["Typ"] = self.typ
        if not self.noPrv is None:
            data["NoPrv"] = self.noPrv
        if data and (len(data) > 2 or not self.new):
            if self.new: data = self.complete_data(data)
            #print "AfpDialog_EventPrices.store_data data:", data
            self.data.set_data_values(data, "PREISE", self.index)
            self.Ok = True
        self.changed_text = []   
        
    ## initialise new empty data with all necessary values \n
    # or the other way round, complete new data entries with all needed input
    # @param data - data top be completed
    def complete_data(self, data):
        if not "Typ" in data: data["Typ"] = "Grund"
        #if not "noPrv" in data: data["noPrv"] = 0
        return data

    ## Population routine for the dialog overwritten from parent \n
    # due to special choice settings
    def Populate(self):
        super(AfpDialog_EventPrices, self).Populate()
        if self.index is None:
            self.index = self.data.get_value_length("PREISE") 
            #print "AfpDialog_EventPrices: no index given - NEW index created:", self.index
        if self.index < self.data.get_value_length("PREISE"):
            row = self.data.get_value_rows("PREISE","Bezeichnung,Preis,Typ,Plaetze,Anmeldungen,NoPrv", self.index)[0]
            #print "AfpDialog_EventPrices index:", self.index
            #print row
            self.text_Bez.SetValue(Afp_toString(row[0]))
            self.text_Preis.SetValue(Afp_toString(row[1]))
            if row[2] == "Aufschlag":
                self.choice_Typ.SetSelection(1)
            else:
                self.choice_Typ.SetSelection(0)
            self.text_Plaetze.SetValue(Afp_toString(row[3]))
            self.label_Anmeld.SetLabel(Afp_toString(row[4]))
            if row[5]:
                self.check_NoPrv.SetValue(True)
            else:
                self.check_NoPrv.SetValue(False)
        else:
            self.text_Bez.SetValue("")
            self.text_Preis.SetValue("")
            self.choice_Typ.SetSelection(0)
            self.text_Plaetze.SetValue("") 
            self.label_Anmeld.SetLabel("")
            self.check_NoPrv.SetValue(False)
                
    ## activate or deactivate changeable widgets \n
    # this method also calls the parent method
    # @param ed_flag - flag if widgets have to be activated (True) or deactivated (False)
    # @param initial - flag if data has to be locked, used in parent method 
    def Set_Editable(self, ed_flag, initial = False):
        super(AfpDialog_EventPrices, self).Set_Editable(ed_flag, initial)
        if ed_flag: 
            self.choice_Typ.Enable(True)
            self.check_NoPrv.Enable(True)
            self.button_Loeschen.Enable(True)
        else:  
            self.choice_Typ.Enable(False)
            self.check_NoPrv.Enable(False)
            self.button_Loeschen.Enable(False)
            #self.Populate()

    # Event Handlers 
    ##  Eventhandler BUTTON  delete current price from tour \n
    # @param event - event which initiated this action   
    def On_Preise_delete(self,event):
        if self.debug: print "AfpDialog_EventPrices Event handler `On_Preise_delete'", self.index
        self.data.delete_row("PREISE", self.index)
        self.Ok = True
        self.EndModal(wx.ID_OK)
    ##  Eventhandler CHOICE  change typ of price \n
    # - Grund - is a main price for the tour 
    # - Aufschlag - is an addtional price
    # @param event - event which initiated this action   
    def On_CTyp(self,event):
        if self.debug: print "AfpDialog_EventPrices Event handler `On_CTyp'"
        self.typ = self.choice_Typ.GetStringSelection()
        event.Skip()
    ##  Eventhandler CHECKBOX change tprovision typ of price \n
    # @param event - event which initiated this action   
    def On_CBNoPrv(self,event):
        if self.debug: print "AfpDialog_EventPrices Event handler `On_CBNoPrv'"
        self.noPrv = self.check_NoPrv.GetValue()
        event.Skip()

## loader routine for dialog EventPrices
# @param data - Event data where prices are attached
# @param index - index of price in event-data
def AfpLoad_EventPrices(data, index):
    EventPrices = AfpDialog_EventPrices(None)
    EventPrices.attach_data(data, index)
    EventPrices.ShowModal()
    Ok = EventPrices.get_Ok()
    data = EventPrices.get_data()
    EventPrices.Destroy()
    if Ok: return data
    else: return None

## allows the display and manipulation of a EvClient data 
class AfpDialog_EvClientEdit(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        self.change_preis = False
        super(AfpDialog_EvClientEdit, self).__init__(*args, **kw)
        self.lock_data = True
        self.active = None
        self.agent = None
        self.preisnr = None
        self.preisprv = None
        self.orte = None
        self.ortsnr = None
        self.ort = None
        self.route = None  #may hold AfpEvRoute object if necessary
        self.zustand = None
        self.sameRechNr = None
        self.zahl_data = None
        self.SetSize((500,430))
        self.SetTitle("Anmeldung")
        self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
    
    ## set up dialog widgets - overwritten from AfpDialog
    def InitWx(self):
        self.panel = wx.Panel(self, -1)
        panel = self.panel
        self.label_Zustand = wx.StaticText(panel, -1,  pos=(12,68), size=(140,18), name="Zustand")
        self.labelmap["Zustand"] = "Zustand.ANMELD"
        self.label_RechNr = wx.StaticText(panel, -1,  pos=(160,68), size=(130,18), name="RechNr")
        self.labelmap["RechNr"] = "RechNr.ANMELD"
        self.label_Datum = wx.StaticText(panel, -1,  pos=(300,68), size=(80,18), name="LDatum")
        self.labelmap["LDatum"] = "Anmeldung.ANMELD"
        self.label_TFuer = wx.StaticText(panel, -1, label="für".decode("UTF-8"), pos=(12,90), size=(20,16), name="TFuer")
        self.label_Bez = wx.StaticText(panel, -1, pos=(35,90), size=(180,34), name="Bez")
        self.labelmap["Bez"] = "Bez.EVENT"
        self.label_Buero = wx.StaticText(panel, -1, pos=(224,90), size=(156,34), style=wx.ST_NO_AUTORESIZE, name="Buero")
        self.labelmap["Buero"] = "Name.Agent"
        self.label_Vorname = wx.StaticText(panel, -1, pos=(12,134), size=(200,18), name="Vorname")
        self.labelmap["Vorname"] = "Vorname.ADRESSE"
        self.label_Nachname = wx.StaticText(panel, -1, pos=(12,150), size=(200,18), name="Nachname")
        self.labelmap["Nachname"] = "Name.ADRESSE"
        self.label_Info = wx.StaticText(panel, -1, pos=(224,134), size=(156,36), name="Info")
        self.labelmap["Info"] = "Info.ANFRAGE"
        self.label_TBem = wx.StaticText(panel, -1, label="&Bem:", pos=(10,174), size=(36,20), name="TBem")
        self.text_Bem = wx.TextCtrl(panel, -1, value="", pos=(50,174), size=(330,22), style=0, name="Bem")
        self.textmap["Bem"] = "Bem.ANMELD"
        self.text_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.text_ExtText = wx.TextCtrl(panel, -1, value="", pos=(10,204), size=(370,40), style=wx.TE_MULTILINE|wx.TE_LINEWRAP, name="ExtText")
        self.textmap["ExtText"] = "ExtText.ANMELD"
        self.text_ExtText.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_TAb = wx.StaticText(panel, -1, label="&Örtlichkeit:".decode("UTF-8"), pos=(14,350), size=(80,20), name="TAb")
        self.label_TAb.Show(False)
        self.label_TGrund = wx.StaticText(panel, -1, label="Preis:", pos=(210,264), size=(78,20), name="TGrund")
        self.label_Grund = wx.StaticText(panel, -1, pos=(300,264), size=(78,20), name="Grund")
        self.labelmap["Grund"] = "Preis.Preis"
        self.label_TExtra = wx.StaticText(panel, -1, label="Extras:", pos=(210,284), size=(78,20), name="TExtra")
        self.label_Extra = wx.StaticText(panel, -1, pos=(300,284), size=(78,20), name="Extra")
        self.labelmap["Extra"] = "Extra.ANMELD"
        self.label_TTransfer = wx.StaticText(panel, -1, label="Transfer:", pos=(208,304), size=(78,20), name="TTransfer")
        self.label_TTransfer.Show(False)
        self.label_Transfer = wx.StaticText(panel, -1, pos=(300,304), size=(78,20), name="Transfer")
        self.labelmap["Transfer"] = "Transfer.ANMELD"
        self.label_Transfer.Show(False)
        self.label_TPreis = wx.StaticText(panel, -1, label="Preis:", pos=(210,330), size=(78,20), name="TPreis")
        self.label_Preis = wx.StaticText(panel, -1, pos=(300,330), size=(78,20), name="Preis")
        self.labelmap["Preis"] = "Preis.ANMELD"
        self.label_TBezahlt = wx.StaticText(panel, -1, label="bezahlt:", pos=(210,354), size=(78,20), name="TBezahlt")
        self.label_Zahlung = wx.StaticText(panel, -1, pos=(300,354), size=(78,20), name="Zahlung")
        self.labelmap["Zahlung"] = "Zahlung.ANMELD"
        self.label_ZahlDat = wx.StaticText(panel, -1, pos=(300,374), size=(78,20), name="ZahlDat")
        self.labelmap["ZahlDat"] = "ZahlDat.ANMELD"
        # ListBoxes
        self.list_Preise = wx.ListBox(panel, -1, pos=(12,264), size=(194,82), name="Preise")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Anmeld_Preise, self.list_Preise)
        self.listmap.append("Preise")
        self.list_Alle = wx.ListBox(panel, -1, pos=(12,10), size=(476,50), name="Alle")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Anmeld_Alle, self.list_Alle)
        self.listmap.append("Alle")
        self.keepeditable.append("Alle")
    #FOUND: DialogComboBox "Weiter", conversion not implemented due to lack of syntax analysis!
    
        # COMBOBOX
        self.combo_Ort = wx.ComboBox(panel, -1, value="", pos=(12,368), size=(194,20), style=wx.CB_DROPDOWN|wx.CB_SORT, name="Ort")
        self.Bind(wx.EVT_COMBOBOX, self.On_CBOrt, self.combo_Ort)
        self.combo_Ort.Show(False)

        #self.combomap["Ort"] = "Ort.TORT" # will be set in 'attach_data' if needed
        # BUTTON
        self.choice_Zustand = wx.Choice(panel, -1,  pos=(390,62), size=(100,30),  choices= [""] + AfpEvent_getZustandList() ,  name="CZustand")      
        #self.choicemap["CZustand"] = "Zustand.ANMELD"
        self.Bind(wx.EVT_CHOICE, self.On_CZustand, self.choice_Zustand)  
        self.button_Agent = wx.Button(panel, -1, label="&Vermittler".decode("UTF-8"), pos=(390,96), size=(100,30), name="Agent")
        self.Bind(wx.EVT_BUTTON, self.On_Agent, self.button_Agent)
        self.button_Adresse = wx.Button(panel, -1, label="A&dresse", pos=(390,130), size=(100,30), name="Adresse")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_aendern, self.button_Adresse)
        self.check_Mehrfach = wx.CheckBox(panel, -1, label="Mehrfach", pos=(390,190), size=(100,14), name="Mehrfach")
        self.button_Neu = wx.Button(panel, -1, label="&Neu", pos=(390,204), size=(100,30), name="Neu")
        self.Bind(wx.EVT_BUTTON, self.On_Anmeld_Neu, self.button_Neu)
        self.button_Storno = wx.Button(panel, -1, label="&Stornierung", pos=(390,256), size=(100,30), name="Storno")
        self.Bind(wx.EVT_BUTTON, self.On_Storno, self.button_Storno)
        self.button_Zahl = wx.Button(panel, -1, label="&Zahlung", pos=(390,292), size=(100,30), name="Zahl")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahl)

        self.setWx(panel, [390, 328, 100, 30], [390, 364, 100, 30]) # set Edit and Ok widgets

    ## attaches data to this dialog overwritten from AfpDialog
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        super(AfpDialog_EvClientEdit, self).attach_data(data, new, editable)
        if new: self.Populate()
    ## only allow OK-button to exit dialog for automatic new creation \n
    # set 'only OK' mode
    def set_onlyOk(self):
        if self.new:
            self.Set_Editable(True)
            self.choice_Edit.SetSelection(1)
            self.choice_Edit.Enable(False)

    ## read values from dialog and invoke writing into data         
    def store_data(self):
        self.Ok = False
        data = {}
        #print "AfpDialog_EvClientEdit.store_data changed_text:",self.changed_text
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        if self.ort:
            data["Ab"] = self.ort
        if not self.agent is None:
            if self.agent:
                data["AgentNr"] = self.agent.get_value("KundenNr")
                data["AgentName"] = self.agent.get_value("Name")
            else:
                data["AgentNr"] = None
                data["AgentName"] = None
        if self.zustand:
            data["Zustand"] = self.zustand
        #print "AfpDialog_EvClientEdit.store_data data:",self.new, self.change_preis, data
        #self.data.view()
        if data or self.change_preis or self.new:
            if self.new:
                data = self.complete_data(data)
            if self.new or self.change_preis:
                if self.preisnr: data["PreisNr"] = self.preisnr
                if self.preisprv: data["ProvPreis"] = self.preisprv
                extra = Afp_floatString(self.label_Extra.GetLabel())
                if extra != self.data.get_value("Extra"):
                    data["Extra"] = extra
                preis = Afp_floatString(self.label_Preis.GetLabel())
                data["Preis"] = preis
            self.data.set_data_values(data, "ANMELD")
            # store data
            self.data.store()
            # count up number of tour participants
            if self.new: self.data.add_to_event()
            # execute payment
            if self.zahl_data:
                self.zahl_data.store()            
            # execute change in location data
            if self.route and self.route.has_changed():
                self.route.store()
            self.new = False
            self.Ok = True
        self.changed_text = []   
        self.preisnr = None
        self.ort = None
        self.agent = None
        self.change_preis = False  

    ## complete data before storing
    # @param data - data to be completed      
    def complete_data(self, data):
        IdNr = None
        if not "Zustand" in data:
            data["Zustand"] = AfpEvent_getZustandList()[-1]
        if not self.data.get_value("RechNr"):
            RNr = self.data.generate_RechNr(IdNr)
            data["RechNr"] = RNr
        if not "Ab" in data:
            data["Ab"] = 0
        return data
                    
    ## execution in case the OK button ist hit - overwritten from AfpDialog
    def execute_Ok(self):
        self.store_data()
    ## get created invoicenumber from data \n
    # only used in 'only Ok' mode
    def get_RechNr(self):
        return self.data.get_value("RechNr")
   ## common population routine overwritten from AfpDialog
    #def Populate(self):
        #super(AfpDialog_EvClientEdit, self).Populate()
        #ortsnr = self.data.get_value("Ab.Anmeld")
        #row = self.route.get_location_data(ortsnr)
        #ort = None
        #if row: ort = row[1]
        #self.combo_Ort.SetValue(Afp_toString(ort))

    ## populate the 'Preise' list, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_Preise(self):
        rows = self.data.get_value_rows("Preis", "Preis,Bezeichnung,Kennung")
        liste = ["--- Extraleistung hinzufügen ---".decode("UTF-8")]
        if rows:
            row = rows[0]
            liste.append(Afp_toFloatString(row[0]).rjust(10) + "  " + Afp_toString(row[1]))
        rows = self.data.get_value_rows("ANMELDEX", "Preis,Bezeichnung,Kennung")
        #print "AfpDialog_EvClientEdit.Pop_Preise:", rows
        for row in rows:
            liste.append(Afp_toFloatString(row[0]).rjust(10) + "  " + Afp_toString(row[1]))
        self.list_Preise.Clear()
        self.list_Preise.InsertItems(liste, 0)
    ## populate the 'Alle' list, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_Alle(self):
        dummy, self.sameRechNr, liste = self.data.get_sameRechNr()
        self.list_Alle.Clear()
        if liste: self.list_Alle.InsertItems(liste, 0)
        #print "AfpDialog_EvClientEdit.Pop_Alle:", self.sameRechNr

   ## Eventhandler TEXT-KILLFOCUS - check date syntax 
    # @param event - event which initiated this action 
    def On_Check_Datum(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_Check_Datum'" 
        object = event.GetEventObject()
        datum = object.GetValue()
        date = Afp_ChDatum(datum)
        object.SetValue(date)
        self.On_KillFocus(event)
        event.Skip()
    ## Eventhandler CHOICE - enable/disable widgets according to choice value
    # @param event - event which initiated this action   
    def On_CZustand(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_CZustand'"
        self.zustand = self.choice_Zustand.GetStringSelection()
        self.label_Zustand.SetLabel(self.zustand)
        self.choice_Zustand.SetSelection(0)
        event.Skip()
        
    ## event handler COMBOBOX - select location where to join tour
    # @param event - event which initiated this action   
    def On_CBOrt(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_CBOrt'"
        select = self.combo_Ort.GetStringSelection()
        row = []
        #print "AfpDialog_EvClientEdit.On_CBOrt:", select
        if select == self.route.get_spezial_text("raste"):
            row = AfpEv_selectLocation(self.route,"routeOnlyRaste")
        elif select == self.route.get_spezial_text("free"):
            row = AfpEv_selectLocation(self.route, "allNoRoute")
        if row: # selection from dependend dialog
            self.ort = row[0]
            self.combo_Ort.SetValue(row[1] + " [" + row[2] + "]")
        else:
            if row is None: # cancel selected, restore current selection
                if self.ort: ort = self.ort
                else: ort = self.data.get_value("Ab")
                row = self.route.get_location_data(ort)
                self.combo_Ort.SetValue(row[1] + " [" + row[2] + "]")
            else: # direct  selection
                self.ort = self.ortsnr[self.orte.index(select)]
    ## event handler when window is activated
    # @param event - event which initiated this action   
    def On_Activate(self,event):
        if self.active is None:
            if self.debug: print "AfpDialog_EvClientEdit Event handler `On_Activate'"
            if self.route:
                self.orte, self.ortsnr = self.route.get_sorted_location_list("routeNoRaste", True)
                for ort in self.orte:
                    self.combo_Ort.Append(Afp_toString(ort))
            self.active = True
        
    ## Eventhandler LISTBOX: extra price is doubleclicked
    # @param event - event which initiated this action   
    def On_Anmeld_Preise(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_Anmeld_Preise'"
        index = self.list_Preise.GetSelections()[0] - 2
        if index < 0: 
            #print "AfpDialog_EvClientEdit.On_Anmeld_Preise index:", index
            row = self.get_Preis_row(index)
            #print "AfpDialog_EvClientEdit.On_Anmeld_Preise row:", row
            if row:
                self.actualise_preise(row)
                self.change_preis = True
        else:
            row = self.data.get_value_rows("AnmeldEx", "Preis,NoPrv", index)[0]
            #print "AfpDialog_EvClientEdit.On_Anmeld_Preise loeschen:", index, row
            extra = row[0]
            noPrv = row[1]
            self.data.delete_row("AnmeldEx", index)
            self.add_extra_preis_value(-extra)
            if not noPrv: self.add_prov_preis_value(-extra)
            self.change_preis = True
        self.check_family()
        self.Pop_Preise()
        event.Skip()
        
    ## select or generate new basic or extra price \n
    # the result is delivered in following order: 
    # "Preis, Bezeichnung, NoPrv, Kennung, Typ"
    # @param index - action indicator
    # - -1: select basic price
    # - -2: select or generate extra price
    def get_Preis_row(self, index):
        res_row = None
        liste = []
        listentries = []
        idents = []
        name = self.data.get_name()
        rows = self.data.get_value_rows("PREISE", "Preis,Bezeichnung,NoPrv,PreisNr,Typ")
        exlgh = 0
        if index == -1:
            for row in rows:
                if row[4] == "Grund":
                    liste.append(Afp_toFloatString(row[0]).rjust(10) + "  " + Afp_toString(row[1]))
                    listentries.append(row)
                    idents.append(row[3])
            name = self.data.get_name()
            #print "AfpDialog_EvClientEdit.get_Preis_row:",  liste , idents
            value, Ok = AfpReq_Selection("Grundpreis für die Anmeldung von ".decode("UTF-8") + name + " ändern?".decode("UTF-8"), "Bitte neuen Grundpreis auswählen!".decode("UTF-8"), liste, "Grundpreis".decode("UTF-8"), idents)
            #print "AfpDialog_EvClientEdit.get_Preis_row value:",  Ok, value, idents.index(value)
        elif index == -2:
            liste.append(" --- freien Extrapreis eingeben --- ")
            listentries.append(liste[0])
            idents.append(-1)
            extras = self.data.get_value_rows("ExtraPreis", "Preis,Bezeichnung,NoPrv,PreisNr,Typ")
            exlgh = 1
            for ex in extras:
                liste.append(Afp_toFloatString(ex[0]).rjust(10) + "  " + Afp_toString(ex[1]))
                listentries.append(ex)
                idents.append(ind)
                exlgh += 1
            for row in rows:
                if row[4] == "Aufschlag":
                    liste.append(Afp_toFloatString(row[0]).rjust(10) + "  " + Afp_toString(row[1]))
                    listentries.append(row)
                    idents.append(row[3])
            value, Ok = AfpReq_Selection("Extrapreis für die Anmeldung von ".decode("UTF-8") + name + " eingeben?".decode("UTF-8"), "Bitte neues Extra auswählen!".decode("UTF-8"), liste, "Extrapreis".decode("UTF-8"), idents)
            #print "AfpDialog_EvClientEdit.get_Preis_row Extrapreis:", Ok, value, idents
        if Ok:
            if value == -1: # manual entry
                res_row = AfpReq_MultiLine("Bitte Extrapreis und Bezeichnung manuell eingeben.", "", ["Text","Text","Check"], [["Preis:", ""], ["Bezeichnung:", ""], "Verprovisionierbar"],"Eingabe Extrapreis")
                if res_row:
                    res_row[0] = Afp_fromString(res_row[0])
                    res_row[2] = not res_row[2]
                    res_row.append(0)
                    res_row.append("")
                #print "AfpDialog_EvClientEdit.get_Preis_row Manual:", Ok, value, res_row
            elif index == -2 and value < exlgh: # common extra price selected
                res_row = listentries[value]
                if not res_row[0]:
                    value, Ok = AfpReq_Text("Bitte Preis für das Extra".decode("UTF-8"), "'" + res_row[1] + "' eingeben!","0.0","Preiseingabe")
                    if Ok:
                        res_row[0] = Afp_floatString(value)
                #print "AfpDialog_EvClientEdit.get_Preis_row Common:", Ok, value, res_row
            else: # tour specific basic or extra price selected
                res_row = listentries[idents.index(value)]
                #print "AfpDialog_EvClientEdit.get_Preis_row Event:", Ok, value, res_row
        return res_row
    ## actualise all price data according to input row
    # @param row - holding data of selected or manually created price
    def actualise_preise(self, row):
        if row[4] == "Grund":
            ENr = self.data.get_string_value("EventNr")
            if self.preisnr: preisnr = self.preisnr
            else: preisnr = self.data.get_value("PreisNr") 
            if not preisnr == row[3]:
                self.preisnr = row[3]
                select = "EventNr = " + ENr + " AND PreisNr = " + Afp_toString(self.preisnr)
                self.data.get_selection("Preis").load_data(select)
                plus = 0.0
                if row[0]: plus = row[0]
                if self.label_Grund.GetLabel():
                    plus = plus - Afp_fromString(self.label_Grund.GetLabel())
                #print "AfpDialog_EvClientEdit.actualise_preise:", row, self.label_Grund.GetLabel(), plus
                if plus:
                    self.label_Grund.SetLabel( Afp_toString(row[0]))
                    preis = 0.0
                    if self.label_Preis.GetLabel():
                        preis = Afp_fromString(self.label_Preis.GetLabel())
                    preis += plus
                    self.label_Preis.SetLabel(Afp_toString(preis))
                    self.add_prov_preis_value(plus)
        else:
            changed_data = {"AnmeldNr": self.data.get_value("AnmeldNr"), "Preis": row[0], "Bezeichnung":row[1], "NoPrv":row[2]}
            self.data.get_selection("ANMELDEX").add_data_values(changed_data)
            self.add_extra_preis_value(row[0])
            if not row[2]: self.add_prov_preis_value(row[0])
    ## add value to 'extra' and 'preis' Lables
    # @param: plus - value to be added
    def add_extra_preis_value(self, plus):
            extra = Afp_floatString(self.label_Extra.GetLabel())
            extra += plus
            self.label_Extra.SetLabel(Afp_toString(extra))
            preis = Afp_floatString(self.label_Preis.GetLabel())
            preis += plus
            self.label_Preis.SetLabel(Afp_toString(preis))
    ## add value to internal ProvPreis
    # @param: plus - value to be added
    def add_prov_preis_value(self, plus):
        if self.preisprv is None:
            self.preisprv = self.data.get_value("ProvPreis")
            if not self.preisprv:
                self.preisprv = self.data.get_value("Preis")
        if not self.preisprv: self.preisprv = 0.0
        self.preisprv += plus
        
    ## Eventhandler LISTBOX: another EvClient entry is selected in same RechNr listbox
    # @param event - event which initiated this action   
    def On_Anmeld_Alle(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_Anmeld_Alle'"
        index = self.list_Alle.GetSelections()[0]
        ANr = self.sameRechNr[index] 
        #print "AfpDialog_EvClientEdit.On_Anmeld_Alle Index:", index, self.data.get_value("AnmeldNr") , ANr
        if self.data.get_value("AnmeldNr") != ANr:
            #print "AfpDialog_EvClientEdit.On_Anmeld_Alle: change data:", ANr
            data = self.get_client(ANr)
            if data:
                self.attach_data(data)
        event.Skip()

    ## Eventhandler BUTTON - select travel agency
    # @param event - event which initiated this action   
    def On_Agent(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_Agent'"
        name = self.data.get_value("Name.Agent")
        if not name: name = "a"
        text, agent = self.get_agent_text()
        if self.data.event_is_tour():
            text = "Bitte Reisebüro auswählen:"
            agent = "\"Reisebüro\""
        else:
            text = "Bitte Verkäufer an den Kunden auswählen:"
            agent =  "\"Verkäufer\""
        filter = "Attribut = " + agent
        #self.data.globals.mysql.set_debug()
        KNr = AfpLoad_AdAusw(self.data.get_globals(), "ADRESATT", "AttName", name, filter.decode("UTF-8"), text.decode("UTF-8"))
        #self.data.globals.mysql.unset_debug()
        #print "AfpDialog_EvClientEdit.On_Agent:", KNr
        changed = False
        if KNr:
            self.agent = AfpAdresse(self.data.get_globals(),KNr)
            self.label_Buero.SetLabel(self.agent.get_name())
            changed = True
        else:
            if self.data.get_value("AgentNr") or self.agent:
                Ok = AfpReq_Question("Buchung nicht über " + agent + "?".decode("UTF-8"),"Eintrag löschen?".decode("UTF-8"), agent + " löschen?".decode("UTF-8"))
                if Ok: 
                    if self.agent: self.agent = None
                    else: self.agent = False
                    self.label_Buero.SetLabel("")
                    changed = True
        if changed:
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()  
 
    ##Eventhandler BUTTON - change address \n
    # invokes the AfpDialog_DiAdEin dialog
    # @param event - event which initiated this action   
    def On_Adresse_aendern(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_Adresse_aendern'"
        KNr = self.data.get_value("KundenNr.ADRESSE")
        changed = AfpLoad_DiAdEin_fromKNr(self.data.get_globals(), KNr)
        if changed: self.Populate()
        event.Skip()
        
    ##Eventhandler BUTTON - add new client \n
    # @param event - event which initiated this action   
    def On_Anmeld_Neu(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_Anmeld_Neu'"
        mehr = self.check_Mehrfach.GetValue()
        self.Anmeld_neu(mehr)
        event.Skip()  
    ## execute new client generation
    # @param mehr - flag(s) for copying internal data    
    def Anmeld_Neu(self, mehr):
        new_data = AfpEvClient_copy(self.data, mehr)
        if new_data:
            self.new = True
            self.data = new_data
            self.Populate()
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)

    ##Eventhandler BUTTON - delete client \n
    # @param event - event which initiated this action   
    def On_Storno(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_Storno'"
        Ok = AfpLoad_EvClientCancel(self.data)
        event.Skip()
        if Ok: self.EndModal(wx.ID_OK)

    def On_Zahlung(self,event):
        if self.debug: print "AfpDialog_EvClientEdit Event handler `On_Zahlung'"
        Ok, data = AfpLoad_DiFiZahl(self.data,["RechNr","EventNr"])
        if Ok: 
            self.change_data = True
            self.zahl_data = data
            #data.view() # for debug
            self.data = data.get_data()
            self.Populate()
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()
    #
    # may be overwritten in derived class
    #
    ##  get a client object with given identnumber
    # @parm ANr - if given, identifier
    def get_client(self, ANr = None):
        if ANr is None: ANr = self.data.get_value()
        return  AfpEvClient(self.data.globals, ANr)
    #
    # to be overwritten in derived class
    #
    ##  get text to be dispalyed in agent selection dialog and attribut value
    def get_agent_text(self):
         return  "Bitte Verkäufer an den Kunden auswählen:", "\"Verkäufer\""
        
# end of class AfpDialog_EvClientEdit

## loader routine for dialog EvClientEdit
# @param data - data to be proceeded
# @param flavour - if given, flavour (certain type) of dialog 
# @param edit - if given, flag if dialog should open in edit modus
# @param onlyOk - flag if only the Ok exit is possible to leave dialog, used for 'Umbuchung'
def AfpLoad_EvClientEdit(data, flavour = None, edit = False, onlyOk = None):
    if data:
        print "AfpLoad_EvClientEdit:", flavour
        DiEvClientEin = AfpDialog_EvClientEdit(flavour)
        new = data.is_new()
        DiEvClientEin.attach_data(data, new, edit)
        if onlyOk: DiEvClientEin.set_onlyOk()
        DiEvClientEin.ShowModal()
        Ok = DiEvClientEin.get_Ok()
        if onlyOk: Ok = DiEvClientEin.get_RechNr()
        DiEvClientEin.Destroy()
        return Ok
    else: return False
## loader routine for dialog EvClientEdit according to the given superbase object \n
# @param globals - global variables holding database connection
# @param sb - AfpSuperbase object, where data can be taken from
# @param flavour - if given, flavour (certain type) of dialog 
# @param new - if given, flag if new Client entry should be edited
# @param edit - if given, flag if dialog should open in edit modus
def AfpLoad_EvClientEdit_fromSb(globals, sb, flavour = None, new = False, edit = False):
    if new:
        EvClient = AfpEvClient(globals, None, None, globals.is_debug(), False)
        edit = True
    else:
        EvClient = AfpEvClient(globals, None, sb, globals.is_debug(), False)
    #if sb.eof("EventNr","ANMELD"): EvClient.set_new(True)
    if EvClient.is_new():
        ENr = sb.get_value("EventNr.EVENT")
        text = "Bitte Kunden für neue Anmeldung auswählen:".decode("UTF-8")
        KNr = AfpLoad_AdAusw(globals,"ADRESSE","NamSort","", None, text, True)
        if KNr: EvClient.set_new(ENr, KNr)
        else: EvClient = None
    elif EvClient.is_cancelled():
        return AfpLoad_EvClientCancel(EvClient, edit)
    return AfpLoad_EvClientEdit(EvClient, flavour, edit)
## loader routine for dialog EvClientEdit according to the given EvClient identification number \n
# @param globals - global variables holding database connection
# @param anmeldnr -  identification number of EvClient emtry to be filled into dialog
def AfpLoad_EvClientEdit_fromANr(globals, anmeldnr):
    EvClient = AfpEvClient(globals, anmeldnr)
    flavour = EvClient.get_value("Art.Event")
    if flavour == "Event": flavour = None
    return AfpLoad_EvClientEdit(EvClient, flavour)
  
## allows cancellation and tour change for  EvClient data   
class AfpDialog_EvClientCancel(AfpDialog):
    def __init__(self, *args, **kw):
        AfpDialog.__init__(self,None, -1, "")
        self.charges = None
        self.sameRechNr = None
        self.sameCount = 0
        self.umbuchung = None
        self.clients = None
        self.SetSize((520,348))
        self.SetTitle("Stornierung")
        self.Bind(wx.EVT_ACTIVATE, self.On_Activate)

    def InitWx(self):
        panel = wx.Panel(self, -1)
        #FOUND: DialogFrame "RStorno", conversion not implemented due to lack of syntax analysis!
        self.label_TFuer = wx.StaticText(panel, -1, label="für".decode("UTF-8"), pos=(14,64), size=(20,16), name="TFuer")
        self.label_Bez = wx.StaticText(panel, -1, label="Bez.EVENT", pos=(34,64), size=(244,16), name="Bez")
        self.labelmap["Bez"] = "Bez.EVENT"
        self.label_TAm = wx.StaticText(panel, -1, label="am", pos=(280,64), size=(30,16), name="TAm")
        self.label_Beginn = wx.StaticText(panel, -1, label="", pos=(316,64), size=(80,16), name="Beginn")
        self.labelmap["Beginn"] = "Beginn.EVENT"
        self.label_Agent = wx.StaticText(panel, -1, pos=(94,82), size=(300,16), name="Agent")
        self.labelmap["Agent"] = "AgentName.ANMELD"
        self.label_TPreis = wx.StaticText(panel, -1, label="Preis:", pos=(14,176), size=(42,16), name="TPreis")
        self.label_Preis = wx.StaticText(panel, -1, label="", pos=(60,176), size=(80,16), name="Preis")
        self.labelmap["Preis"] = "Preis.ANMELD"
        self.label_TZahlung = wx.StaticText(panel, -1, label="Zahlung:", pos=(240,176), size=(60,16), name="TZahlung")
        self.label_Zahlung = wx.StaticText(panel, -1, label="", pos=(304,176), size=(80,16), name="Zahlung")
        self.labelmap["Zahlung"] = "Zahlung.ANMELD"
        self.label_T_Storno_Geb = wx.StaticText(panel, -1, label="Stornierungsgebühr:".decode("UTF-8"), pos=(8,222), size=(140,20), name="T_Storno_Geb")
        self.text_Storno_Geb= wx.TextCtrl(panel, -1, value="Gebuehr_Storno", pos=(152,220), size=(64,30), style=0, name="Storno_Geb")
        self.vtextmap["Storno_Geb"] = "Gebuehr_Storno"
        self.text_Storno_Geb.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        
        self.choice_Geb = wx.Choice(panel, -1,  pos=(230,220), size=(176,30),  name="CStornoGeb")      
        self.Bind(wx.EVT_CHOICE, self.On_CStornoGeb, self.choice_Geb)  
 
        self.label_T_Datum_Storno = wx.StaticText(panel, -1, label="Stornierungs&datum:", pos=(84,14), size=(130,20), name="T_Datum_Storno")
        self.text_Storno_Datum = wx.TextCtrl(panel, -1, value="Datum_Storno", pos=(224,12), size=(90,24), style=0, name="Storno_Datum")
        self.vtextmap["Storno_Datum"] = "Anmeldung.ANMELD"
        self.text_Storno_Datum.Bind(wx.EVT_KILL_FOCUS, self.On_Storno_Dat)
        
        self.label_Umb_Ort = wx.StaticText(panel, -1, label="Keine Umbuchung", pos=(14,272), size=(200,16), name="Umb_Ort")
        self.labelmap["Umb_Ort"] = "Ort.Umbuchung"
        self.label_T_Umb_am = wx.StaticText(panel, -1, pos=(244,272), size=(60,16), name="T_Umb_am")
        self.label_Umb_Beginn = wx.StaticText(panel, -1, label="", pos=(304,272), size=(80,16), name="Umb_Beginn")
        self.labelmap["Umb_Beginn"] = "Beginn.Umbuchung"
        self.label_Umb_Kst = wx.StaticText(panel, -1, label="", pos=(14,292), size=(140,16), name="Umb_Kst")
        self.labelmap["Umb_Kst"] = "Kennung.Umbuchung"
        self.label_T_Umb_Gutschrift = wx.StaticText(panel, -1, label="Gutschrift:", pos=(234,292), size=(68,16), name="T_Umb_Gutschrift")
        self.label_Gutschrift = wx.StaticText(panel, -1, label="", pos=(304,292), size=(80,16), name="Gutschrift")

        self.list_Mehrfach = wx.ListBox(panel, -1, pos=(10,106), size=(396,66), name="Mehrfach")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Storno_Mehr, self.list_Mehrfach)
        self.listmap.append("Mehrfach")
       
        self.button_Umbuchung = wx.Button(panel, -1, label="&Umbuchung", pos=(420,106), size=(90,36), name="Storno_Umb")
        self.Bind(wx.EVT_BUTTON, self.On_Umbuchung, self.button_Umbuchung)
        self.setWx(panel, [420, 220, 90, 36], [420, 270, 90, 50]) # set Edit and Ok widgets
        
    # Population routine
    ## populates list of involved EvClients, sets price and payments \n
    # called automatically from AfpDialog
    def Pop_Mehrfach(self):
        zahlen, self.sameRechNr, liste = self.data.get_sameRechNr()
        self.sameCount = len(liste)
        for i in range(len(liste)):
            liste[i] = "   " + liste[i]
        #print "AfpDialog_EvClientStorno.Pop_Mehrfach:", zahlen, self.sameRechNr, liste
        self.list_Mehrfach.Clear()
        self.list_Mehrfach.InsertItems(liste, 0)
        self.label_Preis.SetLabel(Afp_toString(zahlen[0]))
        self.label_Zahlung.SetLabel(Afp_toString(zahlen[1]))
    
   ## attaches data to this dialog overwritten from AfpDialog
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        super(AfpDialog_EvClientCancel, self).attach_data(data, new, editable)
        if not data.is_cancelled():
            self.set_new_cancel()
        if self.data.get_value("UmbFahrt"):
            self.label_T_Umb_am.SetLabel("am")
            self.button_Umbuchung.Enable(False)
            self.choice_Edit.SetSelection(0)
            self.choice_Edit.Enable(False)
    
    ## execution in case the OK button ist hit - overwritten from AfpDialog \n
    # if a new event is selected for all involved EvClients a new dialog is created
    def execute_Ok(self):
        self.store_data()
        if self.umbuchung and self.clients:
            ReNr = None
            for client in self.clients:
                if ReNr: tourist.set_value("RechNr", ReNr)
                ReNr = AfpLoad_EvClientEdit(client, False, True)

    ## read values from dialog and invoke writing into data  \n
    # don't rely on AfpDialog menchanismns, as 'mehrfach' list has to be applied
    def store_data(self):
        self.Ok = False
        if not self.data.is_cancelled():
            data = {}
            werte = []
            liste = []
            payment = []
            self.clients = []
            if self.umbuchung:
                self.clients.append(self.data)
            items = self.list_Mehrfach.GetItems()
            anr = self.data.get_value("AnmeldNr")
            for i in range(len(items)):
                if items[i][0] == " ":
                    nr = self.sameRechNr[i]
                    if i > 0 and nr == anr:
                        liste.append(liste[0])
                        liste[0] = anr
                    else:
                        liste.append(nr)
            anz = len(liste)
            name, wert = self.Get_TextValue("Storno_Datum")
            data["Anmeldung"] = wert
            name, wert = self.Get_TextValue("Storno_Geb")
            common, special = Afp_distributeCents(wert, anz)
            data["Preis"] = special
            data["Zustand"] = "Storno"
            if self.umbuchung:
                data["UmbFahrt"] = self.umbuchung.get_value("EventNr")
                data["Info"] = "Umb. -> " + self.umbuchung.get_value("Kennung")
                payment.append(self.data.get_value("Zahlung"))
                data, payment[0] = self.reset_payment(data, payment[0])
            self.data.set_data_values(data, "ANMELD")
            self.data.store()
            if anz > 1:
                data["Preis"] = common
                for i in range(1, anz):
                    client = AfpEvClient(self.data.get_globals(), liste[i])
                    if self.umbuchung:
                        payment.append(client.get_value("Zahlung"))
                        data, payment[i] = self.reset_payment(data, payment[i])
                    client.set_data_values(data, "ANMELD")
                    if self.umbuchung: self.clients.append(client)
                    client.store()
            self.data.delete_from_event(anz)
            if self.umbuchung:
                #print "AfpDialog_EvClientCancel.store_data: Umbuchungen:", anz, "Zahlung:", payment, "Anmeldungen:", self.clients
                for i in range(anz):
                    self.clients[i].set_new(self.umbuchung.get_value("EventNr"), None, [False, True, False, False])
                    #print "AfpDialog_EvClientCancel.store_data set payment:", self.clients[i].get_name(), payment[i]
                    self.clients[i].set_payment_values(payment[i], self.data.get_globals().today())
            self.Ok = True

    ## activate or deactivate changeable widgets \n
    # this method also calls the parent method
    # @param ed_flag - flag if widgets have to be activated (True) or deactivated (False)
    # @param initial - flag if data has to be locked, used in parent method 
    def Set_Editable(self, ed_flag, initial = False):
        super(AfpDialog_EvClientCancel, self).Set_Editable(ed_flag, initial)
        if ed_flag: 
            self.choice_Geb.Enable(True)
        else:  
            self.choice_Geb.Enable(False)
            
    ## set new cancellation date
    def set_new_cancel(self):
        self.text_Storno_Datum.SetValue(self.data.globals.today_string())
    ## set cancellation charges
    def set_charges(self):
        if self.data.is_cancelled():
            self.text_Storno_Geb.SetValue(self.label_Preis.GetLabel())
            cancel = self.data.get_value("Anmeldung")
            already_cancelled = True
        else:
            cancel = self.data.globals.today()
            already_cancelled = False
        cancel = Afp_fromString(self.text_Storno_Datum.GetValue())
        start = self.data.get_value("Beginn.EVENT")
        diff = Afp_diffDays(cancel, start)
        percent = 0
        index = len(self.charges) - 1
        for i in range(len(self.charges)):
        #for row in self.charges:
            row = self.charges[i]
            if diff < row[0]:
                percent = row[1]
                index = i
                break
        #print "AfpDialog_EvClientCancel.set_charges:",percent, index, diff, cancel, start
        self.choice_Geb.SetSelection(index)
        if not already_cancelled:
            self.set_charge()
    ## set value of charge depending on selection in choice
    def set_charge(self):
        index = self.choice_Geb.GetSelection()
        if index < len(self.charges)-1:
            percent = self.charges[index][1]
            preis = Afp_fromString(self.label_Preis.GetLabel())
            charge = percent*preis/100
        else:
            charge = self.charges[len(self.charges)-1][1] * self.sameCount
        self.text_Storno_Geb.SetValue(Afp_toFloatString(charge))
        zahl = Afp_fromString(self.label_Zahlung.GetLabel())
        if zahl > charge:
            gut = zahl - charge
            self.label_Gutschrift.SetLabel(Afp_toFloatString(gut))
        else: 
            self.label_Gutschrift.SetLabel(Afp_toFloatString(0.0))
            
    ## modify payment setting
    # @param data - dictionary where payment data should be set
    # @param payment - actuel payment data
    def reset_payment(self, data, payment):
        charge = data["Preis"]
        pay = 0.0
        leftover = 0.0
        if payment:
            if charge:
                if charge > payment: 
                    pay = payment
                else:
                    pay = charge
                    leftover = payment - charge
            data["ZahlDat"] = self.data.globals.today() 
        data["Zahlung"] = pay
        if self.debug: print "AfpDialog_EvClientCancel.reset_payment:", charge,  leftover, pay  
        return data, leftover
    
    ## get values from line in 'mehrfach' list
    def get_mehrfach_values(self, line):
        preis = 0.0
        zahl = 0.0
        split = line.split()
        #print "AfpDialog_EvClientCancel.get_mehrfach_values:", split
        if split[0] == "*":
            preis = Afp_fromString(split[2])
            zahl = Afp_fromString(split[3])
        else:
            preis = Afp_fromString(split[1])
            zahl = Afp_fromString(split[2])
        return preis, zahl
        
    ## modify preis and zahl labels
    def modify_mehrfach_values(self, diff_preis, diff_zahl):
        preis = Afp_fromString(self.label_Preis.GetLabel()) + diff_preis
        zahl = Afp_fromString(self.label_Zahlung.GetLabel()) + diff_zahl
        self.label_Preis.SetLabel(Afp_toString(preis))
        self.label_Zahlung.SetLabel(Afp_toString(zahl))
 
    # Event Handlers 
    ## event handler when window is activated
    # @param event - event which initiated this action   
    def On_Activate(self, event):
        #print "AfpDialog_EvClientCancel.OnActivate", self.charges
        if not self.charges:
            self.charges = self.data.globals.get_value("cancellation-charges","Event")
            if not self.charges: self.charges = [[0,50]]
            for row in self.charges:
                if row[0]:
                    text = "ab " + Afp_toString(row[0]) + " Tage: " + Afp_toString(row[1]) + "%"
                else:
                    text = "Standardgebühr: ".decode("UTF-8") + Afp_toString(row[1]) + " EUR"
                self.choice_Geb.Append(text)
            self.choice_Geb.SetSelection(len(self.charges) - 1)
            self.set_charges()
 
    ## event handler when charge choice has been changed
    # @param event - event which initiated this action   
    def On_CStornoGeb(self, event):
        if self.debug: print "AfpDialog_EvClientCancel Event handler `On_CStornoGeb'"
        self.set_charge()
        event.Skip()
       
    def On_Storno_Mehr(self,event):
        if self.debug: print "AfpDialog_EvClientCancel Event handler `On_Storno_Mehr'"
        index = self.list_Mehrfach.GetSelections()[0]
        if index == 0:
            AfpReq_Info("Referenzbuchung kann nicht markiert werden!","Bitte eine Buchung als Referenzbuchung auswählen, die storniert werden soll!".decode("UTF-8"))
        else:
            liste = self.list_Mehrfach.GetItems()
            preis, zahl = self.get_mehrfach_values(liste[index])
            if liste[index][0] == "*":
                liste[index] = "  " + liste[index][1:]
                self.modify_mehrfach_values(preis, zahl)
                self.sameCount -= 1
            else:
                liste[index] = "*" + liste[index][2:]
                self.modify_mehrfach_values(-preis, -zahl)
                self.sameCount += 1
            self.list_Mehrfach.Clear()
            self.list_Mehrfach.InsertItems(liste, 0)
            self.set_charge()
        event.Skip()

    def On_Storno_Dat(self,event):
        if self.debug: print "AfpDialog_EvClientCancel Event handler `On_Storno_Dat'"
        object = event.GetEventObject()
        datum = object.GetValue()
        date = Afp_ChDatum(datum)
        object.SetValue(date)
        self.On_KillFocus(event)
        self.set_charges()
        event.Skip()

    def On_Umbuchung(self,event):
        if self.debug: print "AfpDialog_EvClientCancel Event handler `On_Umbuchung'"
        globals = self.data.get_globals()
        start = Afp_addMonthToDate(globals.today(), 1, "-",1)
        where = "'Beginn' > \"" + Afp_toInternDateString(start) +"\""
        value = self.data.get_string_value("Beginn.EVENT")
        auswahl = AfpLoad_EvAusw(globals, "Beginn" , value, where, True)
        FNr = None
        if auswahl:  
            FNr = Afp_fromString(auswahl)
            if FNr == self.data.get_value("EventNr"): FNr = None
        if FNr:
            self.umbuchung = AfpEvent(globals, FNr)
            self.label_T_Storno_Geb.SetLabel("Umbuchungsgebühr:".decode("UTF-8"))
            ort = self.umbuchung.get_string_value("Ort")
            am = "am"
            ab = self.umbuchung.get_string_value("Beginn")
            kenn = self.umbuchung.get_string_value("Kennung")
        else:
            self.umbuchung = None
            self.label_T_Storno_Geb.SetLabel("Stornierungssgebühr:".decode("UTF-8"))
            ort = ""
            am = ""
            ab = ""
            kenn = ""
        self.label_Umb_Ort.SetLabel(ort)
        self.label_T_Umb_am.SetLabel(am)
        self.label_Umb_Beginn.SetLabel(ab)
        self.label_Umb_Kst.SetLabel(kenn)
        self.choice_Edit.SetSelection(1)
        self.Set_Editable(True)
        event.Skip()

# loader routine for dialog EvClientCancel
# @param data - client data to be proceeded
# @param edit - if given, flag if dialog should open in edit modus
def AfpLoad_EvClientCancel(data, edit = False):
    DiAnSt = AfpDialog_EvClientCancel(None)
    DiAnSt.attach_data(data, False, edit)
    DiAnSt.ShowModal()
    Ok = DiAnSt.get_Ok()
    DiAnSt.Destroy()
    return Ok


