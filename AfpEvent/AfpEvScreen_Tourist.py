#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvScreen
# AfpEvScreen module provides the graphic screen to access all data of the Afp-'Event' modul 
# specialized screen for 'tourist' handling, intergrated from former 'Tourist' modul
# it holds the class
# - AfpEvScreen
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        10 Apr. 2019 - integrate all dervired flavour classes into one deck - Andreas.Knoblauch@afptech.de
#        25 Oct 2018 - corrections due to database changes in 'Event' modul- Andreas.Knoblauch@afptech.de
#        15 May 2018 - integrated into 'Event' modul - Andreas.Knoblauch@afptech.de
#        15 Jan. 2016 - inital code of 'Tourist' modul generated - Andreas.Knoblauch@afptech.de

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

from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile
from AfpBase.AfpDatabase.AfpSQL import AfpSQL
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import Afp_archivName, Afp_startFile
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Selection, AfpReq_Question, AfpReq_Text
from AfpBase.AfpBaseDialogCommon import AfpDialog_Auswahl, Afp_autoEingabe
from AfpBase.AfpBaseScreen import AfpScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_DiAdEin_fromSb
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

from AfpEvent.AfpEvScreen import AfpEvScreen
from AfpEvent.AfpEvRoutines import *
from AfpEvent.AfpEvDialog import AfpEvent_copy, AfpDialog_EventEdit, AfpDialog_EvClientEdit

## dialog for selection of tour data \n
# selects an entry from the EVENT table
class AfpDialog_EvAwTour(AfpDialog_Auswahl):
    ## initialise dialog
    def __init__(self):
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.typ = "Reiseauswahl"
        self.datei = "EVENT"
        self.modul = "Event"
        
    ## get the definition of the selection grid content \n
    # overwritten for "Event" use
    def get_grid_felder(self): 
        Felder = [["Beginn.EVENT",15], 
                            ["Ende.EVENT", 15], 
                            ["Bez.EVENT",50], 
                            ["Kennung.EVENT",15], 
                            ["Anmeldungen.EVENT",5], 
                            ["EventNr.EVENT",None]] # Ident column
        return Felder
    ## invoke the dialog for a new entry \n
    # overwritten for "Event" use
    def invoke_neu_dialog(self, globals, eingabe, filter):
        data = AfpEvTour(globals)
        return AfpLoad_EvTourEdit(data, "Tourist")      
 
## loader routine for event selection dialog 
# @param globals - global variables including database connection
# @param index - column which should give the order
# @param value -  if given,initial value to be searched
# @param where - if given, filter for search in table
# @param ask - flag if it should be asked for a string before filling dialog
def AfpLoad_EvAwTour(globals, index, value = "", where = None, ask = False):
    result = None
    Ok = True
    if ask:
        sort_list = AfpEvClient_getOrderlistOfTable(globals.get_mysql(), index)        
        value, index, Ok = Afp_autoEingabe(value, index, sort_list, "Reise")
    if Ok:
        DiAusw = AfpDialog_EvAwTour()   
        DiAusw.initialize(globals, index, value, where, "Bitte Reise auswählen:")
        DiAusw.ShowModal()
        result = DiAusw.get_result()
        DiAusw.Destroy()
    elif Ok is None:
        # flag for direct selection
        result = Afp_selectGetValue(globals.get_mysql(), "EVENT", "EventNr", index, value)
    return result      

## baseclass for tour handling         
class AfpEvTour(AfpEvent):
    ## initialize AfpEvent class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param EventNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either EventNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
    def  __init__(self, globals, EventNr = None, sb = None, debug = None, complete = False):
        AfpEvent.__init__(self, globals, EventNr, sb, debug, complete)
        self.listname = "Tour"
        if not self.get_value("AgentNr") and sb:
            KNr = sb.get_value("KundenNr.ADRESSE")
            Name = sb.get_value("Name.ADRESSE")
            self.set_value("AgentNr.EVENT", KNr)
            self.set_value("AgentName.EVENT", Name)
        self.selects["Verein"] = [ "ADRESATT","KundenNr = AgentNr.EVENT AND Attribut = \"Verein\""] 
        if complete: self.create_selections()
        if self.debug: print("AfpVerein Konstruktor, EventNr:", self.mainvalue)

    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpEvent
    def get_identification_string(self):
        return "Reise am "  +  self.get_string_value("Beginn") + " nach " + self.get_string_value("Bez")
    ## create client data
    # overwritten from AfpEvent
    # @param ANr - data will be retrieved for this database entry
    def get_client(self, ANr):
        return AfpEvTourist(self.globals, ANr)


## baseclass for Tourist handling         
class AfpEvTourist(AfpEvClient):
    ## initialize AfpEvTourist class, derivate from AfpEvClient
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param AnmeldNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
    # \n
    # either AnmeldNr or sb (superbase) has to be given for initialisation,otherwise a new, clean object is created
    def  __init__(self, globals, AnmeldNr = None, sb = None, debug = None, complete = False):
        AfpEvClient.__init__(self, globals, AnmeldNr, sb, debug, complete)
        self.listname = "Tourist"
        #  self.selects[name of selection]  [tablename,, select criteria, optional: unique fieldname]
        self.selects["TORT"] = [ "TORT","OrtsNr = Ab.ANMELD"] 
        self.selects["EINSATZ"] = [ "EINSATZ","EventNr = EventNr.ANMELD"] 
        if complete: self.create_selections()
        if self.debug: print("AfpEvTourist Konstruktor, AnmeldNr:", self.mainvalue)

    ## generate Event object for this client
    # overwritten from AfpEvClient
    def get_event(self):
        ENr = self.get_value("EventNr.EVENT")
        return AfpEvTour(self.get_globals(), ENr)
    ## return the translated listname to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_listname_translation(self):
        return "Teilnehmer"
    ## return specific identification string to be used in dialogs \n
    # - overwritten from AfpSelectionList
    def get_identification_string(self):
        return "Anmeldung für Reise am "  +  self.get_string_value("Beginn.EVENT") + " nach " + self.get_string_value("Bez.EVENT")
# end of class AfpEvTourist

## Class AfpEvScreen_Tourist shows 'Tourist' screen and handles interactions
class AfpEvScreen_Tourist(AfpEvScreen):
    ## initialize AfpEvScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        self.einsatz = None # to invoke import of 'Einsatz' modules in 'init_database'
        AfpEvScreen.__init__(self, debug)
        self.flavour = "Tourist"
        self.grid_row_selected = True
        self.SetTitle("Afp Tourist")
        if self.debug: print("AfpEvScreen_Tourist Konstruktor")
    
    ## initialize widgets
    # overwritten from AfpEvScreen
    def InitWx(self):
        self.custs_rows = 8
        self.grid_rows["Customers"] = self.custs_rows
        self.grid_cols["Customers"] = 7
        panel = self.panel
        # BUTTON
        self.button_Auswahl = wx.Button(panel, -1, label="Aus&wahl", pos=(692,50), size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Ausw, self.button_Auswahl)
        #self.button_Adresse = wx.Button(panel, -1, label="A&dresse", pos=(692,110), size=(77,50), name="BAdresse")
        #self.Bind(wx.EVT_BUTTON, self.On_Adresse_aendern, self.button_Adresse)      
        self.button_Anfrage = wx.Button(panel, -1, label="An&frage", pos=(692,110), size=(77,50), name="BAnfrage")
        self.Bind(wx.EVT_BUTTON, self.On_Anfrage, self.button_Anfrage)      
        self.button_Reise = wx.Button(panel, -1, label="&Reise", pos=(692,170), size=(77,50), name="Reise")
        self.Bind(wx.EVT_BUTTON, self.On_modify, self.button_Reise)
        self.button_Anmeldung = wx.Button(panel, -1, label="&Anmeldung", pos=(692,230), size=(77,50), name="BAnmeldung")
        self.Bind(wx.EVT_BUTTON, self.On_Anmeldung, self.button_Anmeldung)
        self.button_Zahlung = wx.Button(panel, -1, label="&Zahlung", pos=(692,290), size=(77,50), name="BZahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahlung)
        self.button_Dokumente = wx.Button(panel, -1, label="&Dokumente", pos=(692,350), size=(77,50), name="BDokumente")
        self.Bind(wx.EVT_BUTTON, self.On_Documents, self.button_Dokumente)
        self.button_Einsatz = wx.Button(panel, -1, label="Ein&satz", pos=(692,410), size=(77,50), name="BEinsatz")
        self.Bind(wx.EVT_BUTTON, self.On_VehicleOperation, self.button_Einsatz)               
        self.button_Ende = wx.Button(panel, -1, label="Be&enden", pos=(692,470), size=(77,50), name="BEnde")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Ende)
      
        # COMBOBOX
        self.combo_Filter = wx.ComboBox(panel, -1, value="Eigen-Anmeldungen", pos=(509,16), size=(164,20), choices=["Eigen-Anmeldungen","Eigen-Stornierungen","Eigen-Reservierungen","Fremd-Buchungen","Fremd-Anfragen","Fremd-Anmeldungen","Fremd-Stornierungen"], style=wx.CB_DROPDOWN, name="Filter")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        self.filtermap = {"Eigen-Anmeldungen":"Eigen-Anmeldung","Eigen-Stornierungen":"Eigen-Storno","Eigen-Reservierungen":"Eigen-Reserv","Fremd-Buchungen":"Fremd-","Fremd-Anfragen":"Fremd-Anfrage","Fremd-Anmeldungen":"Fremd-Anmeldung","Fremd-Stornierungen":"Fremd-Storno"}
        self.combo_Sortierung = wx.ComboBox(panel, -1, value="Kennung", pos=(689,16), size=(80,20), choices=["Kennung","Ort","Beginn","Anmeldung"], style=wx.CB_DROPDOWN, name="Sortierung")
        self.Bind(wx.EVT_COMBOBOX, self.On_Index, self.combo_Sortierung)
        self.indexmap = {"Kennung":"Kennung","Ort":"Bez","Beginn":"Beginn","Anmeldung":"RechNr"}
        self.combo_Jahr = wx.ComboBox(panel, -1, value="Aktuell", pos=(420,16), size=(84,20), style=wx.CB_DROPDOWN, name="Jahr")
        self.Bind(wx.EVT_COMBOBOX, self.On_Jahr_Filter, self.combo_Jahr)
        self.Bind(wx.EVT_TEXT_ENTER, self.On_Jahr_Filter, self.combo_Jahr)
      
        # LABEL
        self.label_Reise = wx.StaticText(panel, -1, label="Reise:", pos=(32,51), size=(95,18), name="LReise")
        self.label_Bem = wx.StaticText(panel, -1, label="Bemerkung:", pos=(32,260), size=(95,18), name="LBem")
        self.label_AZusatz = wx.StaticText(panel, -1, label="Zusatz:", pos=(32,285), size=(95,18), name="LAZusatz")
        self.label_Teilnehmer = wx.StaticText(panel, -1,  label="Teilnehmer:", pos=(32,98), size=(95,18), name="LTeilnehmer")
        self.label_Route = wx.StaticText(panel, -1,  label="Route:", pos=(196,98), size=(47,18), name="LRoute")
        self.label_RZusatz = wx.StaticText(panel, -1, label="Zusatz:", pos=(32,126), size=(95,18), name="LRZusatz")
        self.label_Anmeldung = wx.StaticText(panel, -1, label="Anmeldung:", pos=(32,166), size=(95,18), name="LAnmeldung")
        self.label_Adresse = wx.StaticText(panel, -1, label="Adresse:", pos=(32,191), size=(96,18), name="LAdresse")
        self.label_Leistung = wx.StaticText(panel, -1,label="Leistungen:", pos=(430,166), size=(80,18), name="LLeistung")
        #self.label_Transfer = wx.StaticText(panel, -1,label="Transfer:", pos=(433,187), size=(75,19), name="LTransfer")
        self.label_Label8 = wx.StaticText(panel, -1, label="vom", pos=(302,167), size=(26,16), name="Label8")
        self.label_Label2 = wx.StaticText(panel, -1, label="vom", pos=(138,75), size=(30,15), name="Label2")
        self.label_Label3 = wx.StaticText(panel, -1, label="bis zum", pos=(240,75), size=(51,15), name="Label3")
        self.label_Preis = wx.StaticText(panel, -1, label="Preis:", pos=(550,271), size=(50,18), name="LPreis")
        self.label_Zahlung = wx.StaticText(panel, -1, label="Zahlung:", pos=(550,293), size=(50,18), name="LZahlung")
      
        # TEXTBOX
        #Adresse
        self.text_Vorname = wx.TextCtrl(panel, -1, value="", pos=(135,184), size=(140,20), style=wx.TE_READONLY, name="Vorname_Tr")
        self.textmap["Vorname_Tr"] = "Vorname.ADRESSE"
        self.text_Name = wx.TextCtrl(panel, -1, value="", pos=(135,203), size=(224,20), style=wx.TE_READONLY, name="Name_Tr")
        self.textmap["Name_Tr"] = "Name.ADRESSE"
        self.text_Strasse = wx.TextCtrl(panel, -1, value="", pos=(135,222), size=(224,20), style=wx.TE_READONLY, name="Strasse_Tr")
        self.textmap["Strasse_Tr"] = "Strasse.ADRESSE"
        self.text_Plz = wx.TextCtrl(panel, -1, value="", pos=(135,241), size=(50,20), style=wx.TE_READONLY, name="Plz_Tr")
        self.textmap["Plz_Tr"] = "Plz.ADRESSE"
        self.text_Ort = wx.TextCtrl(panel, -1, value="", pos=(185,241), size=(175,20), style=wx.TE_READONLY, name="AdOrt")
        self.textmap["AdOrt"] = "Ort.ADRESSE"
        self.text_Telefon = wx.TextCtrl(panel, -1, value="", pos=(367,222), size=(139,20), style=wx.TE_READONLY, name="Telefon_Tr")
        self.textmap["Telefon_Tr"] = "Telefon.ADRESSE"
        self.text_Tel2 = wx.TextCtrl(panel, -1, value="", pos=(367,241), size=(139,20), style=wx.TE_READONLY, name="Tel2_Tr")
        self.textmap["Tel2_Tr"] = "Tel2.ADRESSE"
        self.text_Mail = wx.TextCtrl(panel, -1, value="", pos=(367,203), size=(139,20), style=0, name="Mail_Tr")
        self.textmap["Mail_Tr"] = "Mail.ADRESSE"

        # Event
        self.text_Bez = wx.TextCtrl(panel, -1, value="", pos=(138,51), size=(230,20), style=wx.TE_READONLY, name="Bez")
        self.textmap["Bez"] = "Bez.EVENT"
        self.text_Beginn = wx.TextCtrl(panel, -1, value="", pos=(168,75), size=(60,20), style=wx.TE_READONLY, name="Beginn")
        self.textmap["Beginn"] = "Beginn.EVENT"
        self.text_Ende = wx.TextCtrl(panel, -1, value="", pos=(308,75), size=(60,20), style=wx.TE_READONLY, name="Ende")
        self.textmap["Ende"] = "Ende.EVENT"
        self.text_Kennung = wx.TextCtrl(panel, -1, value="", pos=(35,75), size=(100,20), style=wx.TE_READONLY, name="Kennung")
        self.textmap["Kennung"] = "Kennung.EVENT"
        self.text_Route = wx.TextCtrl(panel, -1, value="", pos=(240,96), size=(128,20), style=wx.TE_READONLY, name="Route")
        self.textmap["Route"] = "Name.TNAME"
        self.text_Personen = wx.TextCtrl(panel, -1, value="", pos=(135,98), size=(25,20), style=wx.TE_READONLY, name="Personen")
        self.textmap["Personen"] = "Personen.EVENT"
        self.text_Anmeldungen = wx.TextCtrl(panel, -1, value="", pos=(168,98), size=(25,20), style=wx.TE_READONLY, name="Anmeldungen")
        self.textmap["Anmeldungen"] = "Anmeldungen.EVENT"
        self.text_Bem= wx.TextCtrl(panel, -1, value="", pos=(135,123), size=(370,35), style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="ReiseBem")
        self.textmap["ReiseBem"] = "Bem.EVENT"
        self.text_Verst = wx.TextCtrl(panel, -1, value="", pos=(377,51), size=(126,20), style=wx.TE_READONLY, name="Verst")
        self.textmap["Verst"] = "AgentName.EVENT"
        self.text_IntText = wx.TextCtrl(panel, -1, value="", pos=(509,50), size=(164,101), style=wx.TE_MULTILINE, name="IntText")
        self.extmap["IntText"] = "IntText.EVENT"

        # Client
        self.text_Zustand = wx.TextCtrl(panel, -1, value="", pos=(135,163), size=(87,20), style=wx.TE_READONLY, name="Zustand")
        self.textmap["Zustand"] = "Zustand.ANMELD"
        self.text_Anmeldung = wx.TextCtrl(panel, -1, value="", pos=(332,163), size=(60,20), style=wx.TE_READONLY, name="Anmeldung")
        self.textmap["Anmeldung"] = "Anmeldung.ANMELD"
        self.text_RechNr = wx.TextCtrl(panel, -1, value="", pos=(231,163), size=(64,20), style=wx.TE_READONLY, name="RechNr")
        self.textmap["RechNr"] = "RechNr.ANMELD"
        self.text_Agent = wx.TextCtrl(panel, -1, value="", pos=(285,184), size=(143,20), style=wx.TE_READONLY, name="Agent")
        self.textmap["Agent"] = "AgentName.ANMELD"
        self.text_Bem = wx.TextCtrl(panel, -1, value="", pos=(135,260), size=(370,20), style=wx.TE_READONLY, name="Bem_Tr")
        self.textmap["Bem_Tr"] = "Bem.ANMELD"
        self.text_ExtText = wx.TextCtrl(panel, -1, value="", pos=(135,280), size=(370,30), style=0, name="ExtText")
        self.textmap["ExtText"] = "ExtText.ANMELD"
        self.text_Preis= wx.TextCtrl(panel, -1, value="", pos=(600,269), size=(71,20), style=wx.TE_READONLY, name="Preis")
        self.textmap["Preis"] = "Preis.ANMELD"
        self.text_Zahlung = wx.TextCtrl(panel, -1, value="", pos=(600,291), size=(71,20), style=wx.TE_READONLY, name="Zahlung")
        self.textmap["Zahlung"] = "Zahlung.ANMELD"
        
        #ListBox
        self.list_service= wx.ListBox(panel, -1, pos=(512,163) , size=(160, 100), name="service")
        #self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Archiv, self.list_service)
        self.listmap.append("service")
        
        # GRID
       # self.grid_custs = wx.grid.Grid(panel, -1, pos=(23,256) , size=(653, 264), name="Customers")
        self.grid_custs = wx.grid.Grid(panel, -1, pos=(23,315) , size=(653, 204), name="Customers")
        self.grid_custs.CreateGrid(self.custs_rows, 7)
        self.grid_custs.SetRowLabelSize(3)
        self.grid_custs.SetColLabelSize(18)
        self.grid_custs.EnableEditing(0)
        self.grid_custs.EnableDragColSize(0)
        self.grid_custs.EnableDragRowSize(0)
        self.grid_custs.EnableDragGridSize(0)
        self.grid_custs.SetSelectionMode(wx.grid.Grid.GridSelectRows)
        self.grid_custs.SetColLabelValue(0, "Vorname")
        self.grid_custs.SetColSize(0, 130)
        self.grid_custs.SetColLabelValue(1, "Name")
        self.grid_custs.SetColSize(1, 130)
        self.grid_custs.SetColLabelValue(2, "RechNr")
        self.grid_custs.SetColSize(2, 75)
        self.grid_custs.SetColLabelValue(3, "Ab")
        self.grid_custs.SetColSize(3, 35)
        self.grid_custs.SetColLabelValue(4, "Zahlung")
        self.grid_custs.SetColSize(4, 90)
        self.grid_custs.SetColLabelValue(5, "Preis")
        self.grid_custs.SetColSize(5, 90)
        self.grid_custs.SetColLabelValue(6, "Info")
        self.grid_custs.SetColSize(6, 110)
        for row in range(0,self.custs_rows):
            for col in range(0,7):
                self.grid_custs.SetReadOnly(row, col)
        self.gridmap.append("Customers")
        self.grid_minrows["Customers"] = self.grid_custs.GetNumberRows()
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick_Custs, self.grid_custs)
        self.setup_date_filter()

        
    ## execution routine for client (tourist) filter
    # overwritten from AfpEvScreen
    def set_client_filter(self):
        value = self.combo_Filter.GetValue()
        if self.debug: print("AfpEvScreen_Tourist.set_client_filter:", value)      
        s_key = self.sb.get_value()
        value = self.filtermap[value]
        filter = value.split("-")
        re_filter = "Art LIKE \"Reise\""
        if filter[0] == "Fremd":
            re_filter += " AND AgentNr > 0"
        else:
            re_filter += " AND NOT AgentNr > 0"
        if filter[1]: an_filter = "Zustand LIKE \"" + filter[1] + "\""
        else: an_filter = ""
        if self.sb_date_filter:
            if self.sb_master == "ANMELD":
                if an_filter: an_filter += " AND "
                an_filter += self.get_minor_date_filter()
            else:
                re_filter += " AND " + self.sb_date_filter
        if re_filter != self.sb_re_filter:
            self.sb_re_filter = re_filter
            self.sb.select_where(self.sb_re_filter, None, "EVENT")        
        if an_filter != self.sb_an_filter:
            if not filter[1]:
                self.sb.select_where("", None, "ANMELD")
                self.sb_an_filter = "" 
            else:
                self.sb_an_filter = an_filter
                self.sb.select_where(self.sb_an_filter, None, "ANMELD")   
        #print "AfpEvScreen_Tourist.set_client_filter EVENT:", self.sb_re_filter,"ANMELD:", self.sb_an_filter, "CURRENT RECORD:", self.sb.get_value()

    ## populate text widgets
    # overwritten from AfpBaseScreen to handle dependant tourist display
    def Pop_text(self):
        no_slave =  not self.slave_exists()
        for entry in self.textmap:
            TextBox = self.FindWindowByName(entry)
            if no_slave and self.is_slave(self.textmap[entry]):
                value = ""
            elif self.data:
                value = self.data.get_tagged_value(self.textmap[entry])
            else:
                value = self.sb.get_string_value(self.textmap[entry])
            #print ("AfpEvScreen_Tourist.Pop_text:", no_slave, entry, value, self.is_slave(self.textmap[entry]))
            TextBox.SetValue(value)

    ## Eventhandler BUTTON, MENU - tour operation
    def On_VehicleOperation(self,event):
        if self.debug: print("AfpEvScreen_Tourist Event handler `On_VehicleOperation'")
        Event = self.get_data(True)
        if not Event.is_new() and Event.is_own_tour():
            needed = AfpEvClient_checkVehicle(self.globals.get_mysql(), Event.get_string_value("Route"))
            #print "AfpEvScreen.On_VehicleOperation needed:", needed
            if needed and self.einsatz:
                selection = Event.get_selection("EINSATZ")
                ENr = None
                #print "AfpEvScreen.On_VehicleOperation Einsatz:", self.einsatz
                #print "AfpEvScreen.On_VehicleOperation:", selection.get_data_length(), selection, Event.selections
                New = False
                if selection.get_data_length() == 0:
                    New = AfpReq_Question("Kein Einsatz für diese Reise vorhanden,","neuen Einsatz erstellen?","Einsatz?")
                    if New:
                        Einsatz = self.einsatz[1].AfpEinsatz(Event.get_globals(), None, None, Event.get_value("EventNr"), None, None)  
                        Einsatz.store()                    
                        #print "AfpEvScreen.On_VehicleOperation neuer Einsatz:", Einsatz
                        selection.reload_data()
                if selection.get_data_length() > 0: 
                    if selection.get_data_length() > 1:
                        liste = selection.get_value_lines("StellDatum,StellZeit,StellOrt,Bus")
                        ident = selection.get_values("EinsatzNr")
                        #print "Liste:", liste
                        #print ident
                        Ort = Event.get_string_value("Beginn") + " nach " +Event.get_string_value("Ort") 
                        ENr, Ok = AfpReq_Selection("Bitte Einsatz für Reise am " , Ort + " auswäAfpDialog_EventEdithlen.", liste, "Einsatzauswahl", ident)
                        ENr = ENr[0]
                    else:
                        ENr = selection.get_value("EinsatzNr")
                        Ok = True
                    if Ok: 
                        #print "AfpEvScreen.On_VehicleOperation EinsatzNr:", ENr
                        Einsatz = self.einsatz[1].AfpEinsatz(Event.get_globals(), ENr)
                        Ok = self.einsatz[0].AfpLoad_DiEinsatz(Einsatz, New)
            else:
                AfpReq_Info("Für eine eigene Reise mit dieser Route" , "ist kein Einsatz nötig!")
        else:
            AfpReq_Info("Für diese Veranstaltung" , "ist kein Einsatz möglich!")
        event.Skip()

              
    ## Eventhandler ListBox - double click ListBox 'Archiv'
    def On_DClick_Archiv(self, event):
        if self.debug: print("AfpEvScreen_Tourist Event handler `On_DClick_Archiv'", event)
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
                        print("WARNING in AfpEvScreen_Tourist: External file", filename, "does not exist, look in 'antiquedir'.") 
                        filename = Afp_addRootpath(self.globals.get_value("antiquedir"), file)
                    if Afp_existsFile(filename):
                        Afp_startFile(filename, self.globals, self.debug, True)
                    else:
                        print("WARNING in AfpEvScreen_Tourist: External file", filename, "does not exist!") 
        event.Skip()
        
    ## Eventhandler Grid - double click Grid 'Customers'
    def On_DClick_Custs(self, event):
        if self.debug: print("AfpEvScreen_Tourist Event handler `On_DClick_Custs'", event)
        index = event.GetRow()
        ANr = Afp_fromString(self.grid_id["Customers"][index])
        if ANr:
            #col = event.GetColumn(), Spalte extrahieren, evtl. Selectionsmethode in der Deklaration ändern
            col =event.GetCol()
            self.load_direct(0, ANr)
            self.Reload()
            if col == 6:
                #print "AfpEvScreen.On_DClick_Custs last column selected"
                #text_g = self.grid_custs.getCellValue(index, col)
                name = AfpAdresse(self.globals, self.sb.get_value("KundenNr.ANMELD")).get_name()
                text = self.sb.get_value("Info.ANMELD")
                if not text: text = ""
                text, Ok = AfpReq_Text("Bitte Information für Anmeldung",  name+ " eingeben.", text, "Info")
                if Ok:
                    data = AfpEvClient(self.globals, ANr)
                    data.set_value("Info", text)
                    data.store()
                    self.Reload()
        event.Skip()
    
    # routines overwritten from grandparent class
    ## load global veriables for this afp-module
    # (overwritten from AfpScreen) 
    def load_additional_globals(self):
        self.globals.set_value(None, None, "Einsatz")
        
    ## set database to show indicated tour
    # @param ENr - number of event 
    # @param ANr - if given, will overwrite ENr, number of tourist entry (AnmeldNummer)
    def load_direct(self, ENr, ANr = None):
        index = self.combo_Sortierung.GetValue()  
        if ANr:
            #self.sb.set_debug()
            self.sb_master = "ANMELD"
            self.sb.CurrentIndexName("AnmeldNr","ANMELD")
            self.sb.select_key(ANr,"AnmeldNr","ANMELD") 
            #print "AfpEvScreen_Tourist.load_direct select key:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD")
            ENr = self.sb.get_value("EventNr.ANMELD")
            if self.combo_Sortierung.FindString("Anmeldung"):
                self.combo_Sortierung.SetValue("Anmeldung")
        elif self.combo_Sortierung.GetValue() == "Anmeldung":
            self.combo_Sortierung.SetSelection(0)
        self.sb.select_key(ENr,"EventNr","EVENT")
        #print "AfpEvScreen_Tourist.load_direct:", ANr, ENr
        self.On_Index()
        #print "AfpEvScreen_Tourist.load_direct Index set:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD")
        self.set_current_record()
        #print "AfpEvScreen_Tourist.load_direct current record:", self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("EventNr.ANMELD")

    def set_current_record(self):
        #self.data = self.get_data() 
        #return
        FNr = self.sb.get_value("EventNr")
        #print "AfpEvScreen_Tourist.set_current_record initial:", FNr, self.sb.get_value("AnmeldNr.ANMELD"), self.sb.get_value("RechNr.ANMELD")
        if self.sb_master == "ANMELD": slave = "EVENT"
        else: slave = "ANMELD"
        self.sb.select_key(FNr,"EventNr",slave)
        ANr = self.sb.get_value("AnmeldNr.ANMELD")    
        #print "AfpEvScreen_Tourist.set_current_record ANr:", ANr, FNr, slave
        KNr = self.sb.get_value("KundenNr.ANMELD")      
        TNr = self.sb.get_value("Route.EVENT")      
        PNr = self.sb.get_value("PreisNr.ANMELD") 
        PNr = PNr - 100*(int(PNr/100))
        self.sb.select_key(KNr,"KundenNr","ADRESSE")        
        self.sb.select_key(TNr,"TourNr","TNAME")        
        self.sb.select_key(FNr,"EventNr","PREISE")
        nr = self.sb.get_value("PreisNr.PREISE")
        fnr = FNr
        while self.sb.neof("EventNr","PREISE") and nr != PNr and fnr == FNr:
            self.sb.select_next("EventNr","PREISE")
            nr = self.sb.get_value("PreisNr.PREISE")
            fnr = self.sb.get_value("EventNr.PREISE")
        if fnr != FNr: self.sb.select_key(FNr,"EventNr","PREISE")
        #print "AfpEvScreen_Tourist.set_current_record Fahrt:", FNr,"Anmeld:",ANr,"Kunde:",KNr,"Tour:",TNr,"Preis:",PNr,nr
        return 
        
    ## get names of database tables to be opened for this screen
    # (overwritten from AfpScreen)
    def get_dateinamen(self):
        return ["EVENT","ANMELD","PREISE","ANMELDEX","ADRESSE","TORT", "TNAME"]

   ## get rows to populate lists \n
    # default - empty, to be overwritten if grids are to be displayed on screen \n
    # possible selection criterias have to be separated by a "None" value
    # @param typ - name of list to be populated 
    def get_list_rows(self, typ):
        rows = []
        ANr =  self.sb.get_value("AnmeldNr.ANMELD")     
        select = ( "AnmeldNr = %d")% ANr
        if typ == "service" and self.slave_exists():
            bez = self.sb.get_string_value("Bezeichnung.PREISE")  
            preis = self.sb.get_string_value("Preis.PREISE")  
            if not bez: bez = "Grundpreis"
            if not preis: preis = self.sb.get_string_value("Preis.EVENT")  
            #rows.append(bez + "  " + preis)
            rows.append(preis + "  " + bez)
            transfer = self.sb.get_value("Transfer.ANMELD")  
            if transfer:
                ort = self.sb.get_string_value("Ort.TORT") 
                #rows.append(ort + "  " + Afp_toString(transfer)) 
                rows.append(Afp_toString(transfer) + "  " + ort) 
            extra = self.sb.get_value("Extra.ANMELD") 
            if extra:
                ex_row = self.mysql.select_strings("Bezeichnung,Preis",select,"ANMELDEX")
                for row in ex_row:
                    #rows.append(row[0] + "  " + row[1])
                    rows.append(row[1] + "  " + Afp_toString(row[0]))
        return rows

    ## get grid rows to populate grids \n
    # (overwritten from AfpEvScreen - to allow depricatesd use of superbase) 
    # @param typ - name of grid to be populated
    def get_grid_rows(self, typ):
        rows = []
        EventNr =  self.sb.get_value("EventNr")     
        select = ( "EventNr = %d")% EventNr
        if typ == "Customers" and self.sb.neof():
            select = ( "EventNr = %d")% EventNr
            if self.sb_an_filter: select = "(" + select +") and (" + self.sb_an_filter + ")"
            tmps = []
            tmps = self.mysql.select_strings("RechNr,Zahlung,Preis,Info,AnmeldNr,Ab,KundenNr",select,"ANMELD")
            #print "AfpEvScreen_Tourist.get_grid_rows tmps:", tmps
            for tmp in tmps:
                select =  "KundenNr = " + tmp[-1]
                name = self.mysql.select_strings("Vorname,Name", select,"ADRESSE")
                if not name: name = [["",""]]
                if not tmp[-2]: tmp[-2] = "0"
                select =  "OrtsNr = " + tmp[-2]
                ort = self.mysql.select_strings("Kennung", select,"TORT")
                if not ort: ort = [["--"]]
                #print "AfpEvScreen_Tourist.get_grid_rows append:", name, ort, tmp
                rows.append([name[0][0], name[0][1], tmp[0], ort[0][0]] + tmp[1:-2])
        return rows
    #
    # methods overwrittenAfpEventScreen       
    #
    ## load event selection dialog (Ausw)
    # (overwritten from AfpEvScreen)     
    # @param index - column which should give the order
    # @param value -  initial value to be searched
    # @param where - filter for search in table
    def load_event_ausw(self,  index, value, where):
        return AfpLoad_EvAwTour(self.globals, index, value, where, True)    
    ## generate the dedicated event
    # @param ENr - if given:True - new event; Number - EventNr of event
    def get_event(self, ENr = None):
        if ENr == True: return AfpEvTour(self.globals)
        elif ENr:  return  AfpEvTour(self.globals, ENr)
        return  AfpEvTour(self.globals, None, self.sb)
    ## load event edit dialog
    # @param data - data to be edited
    def load_event_edit(self, data):
        return AfpLoad_EvTourEdit(data, self.flavour)
    ## generate the dedicated event client
    # @param ANr - if given:True - new client; Number - AnmeldNr of client
    def get_client(self, ANr = None):
        if ANr == True: return AfpEvTourist(self.globals)
        elif ANr:  return  AfpEvTourist(self.globals, ANr)
        return  AfpEvTourist(self.globals, None, self.sb)
    ## load client edit dialog
    # @param data - data to be edited
    def load_client_edit(self, data):
        return AfpLoad_EvTouristEdit(data)
    ## set current record to be displayed 
    # (overwritten from AfpEvScreen - to allow depricated use of superbase) 
# end of class AfpEvScreen_Tourist

## allows the display and manipulation of an event 
class AfpDialog_EvTourEdit(AfpDialog_EventEdit):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        super(AfpDialog_EvTourEdit, self).__init__(*args, **kw)
        self.SetTitle("Reise")
        self.modifyWx()
        if self.debug: print("AfpDialog_EvTourEdit.init")
        
    def modifyWx(self):
        self.text_Kenn.Bind(wx.EVT_KILL_FOCUS, self.On_setKst)
        self.label_T_Kst = wx.StaticText(self.panel, -1, label="&Konto:", pos=(280,42), size=(60,18), name="T_Kst")
        self.text_Kst = wx.TextCtrl(self.panel, -1, value="", pos=(350,40), size=(80,22), style=0, name="Kst")
        self.textmap["Kst"] = "Kostenst.EVENT"
        self.text_Kst.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_TZeit.SetLabel("&Ende")
        self.vtextmap["Zeit"] = "Ende.EVENT"
        self.choicemap["COrt"] = "Name.TName"
        
    ## complete data if plain dialog has been started 
    # overwritten from AfpDialog_EventEdit
    # @param data - SelectionList where data has to be completed
    def complete_data(self, data):
        if not "Art" in data: data["Art"] = self.flavour
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
        AfpDialog_EventEdit.complete_data(self, data)
        return data
    
    ## fill in available route data
    # overwritten from AfpDialog_EventEdit
    def get_route_data(self):
        routes, routenr = AfpEvClient_getRouteNames(self.data.globals.get_mysql())
        routetext = " --- Neue Transferroute --- "
        return routes, routenr, routetext
  
    ## handle dialog to get new route name
    # overwritten from AfpDialog_EventEdit
    def get_new_route_name(self):
        rname = ""
        rname, Ok = AfpReq_Text("Neue Transferroute wird erstellt,", "bitte Bezeichnung der neuen Route eingeben.", rname, "Neue Route")
        if Ok and rname and rname in self.routes:
            AfpReq_Info("Bezeichnung schon in Routenliste enthalten!","Bitte dort auswählen.","Warnung")
            Ok = False
        return Ok, rname, 0

     
## loader routine for dialog EventEdit flavour 'Tour'
# @param data - AfpEvent data to be loaded
# @param flavour - if given, flavour (certain type) of dialog 
# @param edit - if given, flag if dialog should open in edit modus
def AfpLoad_EvTourEdit(data, flavour = None, edit = False):
    DiTour = AfpDialog_EvTourEdit(flavour)
    new = data.is_new()
    DiTour.attach_data(data, new, edit)
    DiTour.ShowModal()
    Ok = DiTour.get_Ok()
    DiTour.Destroy()
    return Ok    

## allows the display and manipulation of a EvClient data, flavour 'Tourist' 
class AfpDialog_EvTouristEdit(AfpDialog_EvClientEdit):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        #print("AfpDialog_EvTouristEdit._init_:", args, kw, super(AfpDialog_EvTouristEdit, self))
        super().__init__(*args, **kw)
        self.modifyWx()
        
    ##  modify Wx objects defined in parent class
    def modifyWx(self):
        self.combo_Ort.Show(True)
        self.combomap["Ort"] = "Ort.TORT"
        self.label_TAb.Show(True)
        self.label_TAb.SetLabel("Abfahrts&ort:")
        self.label_Transfer.Show(True)
        self.label_TTransfer.Show(True)    
        self.label_TGrund.SetLabel("Reisepreis:")
        self.button_Agent.SetLabel("&Reisebüro")
    ## attaches data to this dialog overwritten from AfpDialog
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        routenr = data.get_value("Route.EVENT")
        self.route = AfpEvRoute(data.get_globals(), routenr, None, self.debug, True)
        print("AfpDialog_EvTouristEdit.attach_data:", new, editable)
        super(AfpDialog_EvTouristEdit, self).attach_data(data, new, editable)
    ## complete data before storing
    # @param data - data to be completed
    def complete_data(self, data):
        if not self.data.get_value("IdNr"):
            IdNr= self.data.generate_IdNr() 
            data["IdNr"] = IdNr
        super(AfpDialog_EvTouristEdit, self).complete_data(data)
        return data
    
    ##  get a client object with given identnumber
    # overwritten from AfpDialog_EvEventEdit
    # @parm ANr - if given, identifier
    # -                     if = True new empty client is delivered
    def get_client(self, ANr = None):
        if ANr == True: return AfpEvTourist(self.data.globals)
        if ANr is None: ANr = self.data.get_value()
        return  AfpEvTourist(self.data.globals, ANr)
    ##  get text to be dispalyed in agent selection dialog and attribut value
    # overwritten from AfpDialog_EvEventEdit
    def get_agent_text(self):
         return  "Bitte Reisebüro auswählen:", "\"Reisebüro\""

        
## loader routine for dialog EvTouristEdit
# @param data - data to be proceeded
# @param edit - if given, flag if dialog should open in edit modus
# @param onlyOk - flag if only the Ok exit is possible to leave dialog, used for 'Umbuchung'
def AfpLoad_EvTouristEdit(data, edit = False, onlyOk = None):
    if data:
        DiEvTourist = AfpDialog_EvTouristEdit()
        new = data.is_new()
        DiEvTourist.attach_data(data, new, edit)
        if onlyOk: DiEvTourist.set_onlyOk()
        DiEvTourist.ShowModal()
        Ok = DiEvTourist.get_Ok()
        if onlyOk: Ok = DiEvTourist.get_RechNr()
        DiEvTourist.Destroy()
        return Ok
    else: return False
    
## load tourist edit dialog only by given id (needed for address screen)
# @param globals - global variabloes given, including mysql connection
# @param ANr - identifiers of this member
def AfpLoad_EvTouristEdit_fromANr(globals, ANr):
    data = AfpEvTourist(globals, ANr)
    Ok = AfpLoad_EvTouristEdit(data)
    return Ok

