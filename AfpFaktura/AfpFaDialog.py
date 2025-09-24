#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpInvoice.AfpInDialog
# AfpInDialog module provides the dialogs and appropriate loader routines needed for invoicehandling
#
#   History: \n
#        20 Nov. 2024 - changes for python 3.12 - Andreas.Knoblauch@afptech.de 
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        22 Nov. 2016 - inital code generated - Andreas.Knoblauch@afptech.de \n

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
#    Copyright© 1989 - 2023  afptech.de (Andreas Knoblauch)
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
from AfpBase.AfpBaseAdRoutines import AfpAdresse_getListOfTable
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

#from AfpEvent.AfpEvRoutines import *
from AfpFaktura.AfpFaRoutines import *

## dialog for selection of faktura data \n
# selects an entry from the different faktura tables
class AfpDialog_FaAusw(AfpDialog_Auswahl):
    ## initialise dialog
    def __init__(self):
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.typ = "Rechnungsauswahl"
        self.datei = "RECHNG"
        self.modul = "Faktura"
    ## set type (to be used before initialisation
    # @param tablename - name of table this search is used for 
    # (has to have certain columns defined)
    def set_type(self, tablename):
        self.datei = tablename
        self.typ = AfpFa_getClearName(tablename) + "sauswahl"
    ## get the definition of the selection grid content \n
    # overwritten for "Faktura" use
    def get_grid_felder(self): 
        Felder = [["RechNr.RECHNG",15], 
                            ["Datum.RECHNG", 15], 
                            ["Vorname.ADRESSE.Name",20],
                            ["Name.ADRESSE.Name",30], 
                            ["Pos.RECHNG",5], 
                            ["Betrag.RECHNG",15], 
                            ["KundenNr.ADRESSE = KundenNr.RECHNG",None],
                            ["RechNr.RECHNG",None]] # Ident column
        return Felder
    ## invoke the dialog for a new entry \n
    # overwritten for "Tourist" use
    def invoke_neu_dialog(self, globals, eingabe, filter):
        print("AfpDialog_FaAusw.invoke_neu_dialog not implemented!")
        return
        superbase = AfpSuperbase.AfpSuperbase(globals, debug)
        superbase.open_datei("RECHNG")
        superbase.CurrentIndexName("RechNr")
        superbase.select_key(eingabe)
        return AfpLoad_DiToEin_fromSb(globals, superbase, eingabe)      
 
## loader routine for faktura selection dialog 
# @param globals - global variables including database connection
# @param table - table which should be searched
# @param index - column which should give the order
# @param value -  if given,initial value to be searched
# @param where - if given, filter for search in table
# @param ask - flag if it should be asked for a string before filling dialog
def AfpLoad_FaAusw(globals, table, index, value = "", where = None, ask = False):
    result = None
    Ok = True
    print("AfpLoad_FaAusw input:", table, index, value, where, ask)
    kind = AfpFa_getClearName(table)
    if ask:
        sort_list = AfpFa_getOrderlistOfTable()        
        value, index, Ok = Afp_autoEingabe(value, index, sort_list, kind + "s")
        print("AfpLoad_FaAusw index:", index, value, Ok)
    if Ok:
        if index == "KundenNr":
            text = "Bitte Auftraggeber von " + kind + " auswählen:"
            KNr = AfpLoad_AdAusw(globals,"ADRESSE","NamSort",value, None, text)
            if KNr:
                text = "Bitte " + kind + " von dem folgenden Auftraggeber auswählen,"
                #rows, name = AfpAdresse_getListOfTable(globals, KNr, "RECHNG","RechNr,Datum,Pos,Betrag")
                fields = "RechNr,Datum,Pos,Betrag"
                filter = None
                if where: filter = where.split("=")
                if filter:
                    filter[0] = filter[0].strip()
                    filter[1] = filter[1].strip().replace("\"","")
                    fields += "," + filter[0]
                rows, name = AfpAdresse_getListOfTable(globals, KNr, table, fields)
                liste = []
                ident = []
                if rows:
                    for row in reversed(rows):
                        if filter and row[-1] != filter[1]: continue
                        ident.append(row[0])
                        liste.append(Afp_ArraytoLine(row[:4]))
                print("AfpLoad_FaAusw select:", text, name, liste, ident, rows)
                result, Ok = AfpReq_Selection(text, name, liste, "Auswahl", ident)
        else:
            DiAusw = AfpDialog_FaAusw()
            DiAusw.set_type(table)
            text = "Bitte " + kind + " auswählen:"        
            print("AfpLoad_FaAusw dialog:", index, value, where)
            DiAusw.initialize(globals, index, value, where, text)
            print("AfpLoad_FaAusw dialog ShowModal:")
            DiAusw.ShowModal()
            result = DiAusw.get_result()
            DiAusw.Destroy()
    elif Ok is None:
        # flag for direct selection
        result = Afp_selectGetValue(globals.get_mysql(), "RECHNG", "RechNr", index, value)
    print("AfpLoad_FaAusw result:", result)
    return result      

## simple select requester for selection of a indicated typ
# @param mysql - database handle to retrieve data from
# @param typ - indicated typ, where rows should be retrieved
# @param text - text to be displayed in requester
# @param debug - flag if debug text should be written
def AfpReq_FaSelectedRow(mysql, typ, text, debug):
    datei, rows = AfpFa_getSelectedRows(mysql, typ, debug)
    liste = []
    ident = []
    for row in rows:
        ident.append(row[3])
        line = [row[3],row[2],row[0],row[1],row[4]]
        liste.append(Afp_ArraytoLine(line))
    if not text: text = "Bitte " + typ + " auswählen!"
    select, Ok = AfpReq_Selection(text, "", liste, "Auswahl", ident)   
    if Ok:
        return datei, select
    else:
        return None, None

## dialog for selection of faktura content data \n
# selects an entry from the 'Artikel' table
class AfpDialog_FaArtikelAusw(AfpDialog_Auswahl):
    ## initialise dialog
    def __init__(self):
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.typ = "Artikelauswahl"
        self.datei = "Artikel"
        self.modul = "Faktura"
    ## get the definition of the selection grid content \n
    # overwritten for "Faktura" use
    def get_grid_felder(self): 
        Felder = [["ArtikelNr.ARTIKEL",30], 
                            ["Bezeichnung.ARTIKEL",30], 
                            ["Name.ADRESSE",15], 
                            ["Lagerort.ARTIKEL",10], 
                            ["Nettopreis.ARTIKEL",15], 
                            ["KundenNr.ADRESSE = HersNr.ARTIKEL",None],
                            ["ArtikelNr.ARTIKEL",None]] # Ident column
        return Felder
    ## invoke the dialog for a new entry \n
    # overwritten for "Artikel" use
    def invoke_neu_dialog(self, globals, eingabe, filter):
        print("AfpDialog_FaArtikelAusw.invoke_neu_dialog not implemented!")
        return
## loader routine for artikel selection dialog 
# @param globals - global variables including database connection
# @param index - column which should give the order
# @param value -  if given,initial value to be searched
# @param where - if given, filter for search in table
# @param ask - flag if it should be asked for a string before filling dialog
def AfpLoad_FaArtikelAusw(globals, index, value = "", where = None, ask = False):
    result = None
    Ok = True
    #globals.mysql.set_debug()
    if ask:
        value, Ok = AfpReq_Text("Bitte Suchbegriff für Artikelauswahl eingeben:", "", value, "Artikelauswahl")
        if Ok:
            if len(value) > 2 and value[2] == " ":
                index = "ArtikelNr"
                #Ok = None
            elif len(value) == 13:
                index = "EAN"
                Ok = None
            else:
                index = "Bezeichnung"
        print("AfpLoad_FaArtikelAusw index:", index, value, Ok)
    if Ok:
        DiArtikel = AfpDialog_FaArtikelAusw()
        print("AfpLoad_FaArtikelAusw dialog invoked:", index, value, where)
        text = "Bitte Artikel auswählen:"
        DiArtikel.initialize(globals, index, value, where, text)
        print("AfpLoad_FaArtikelAusw dialog initialised:", index, value, where, text)
        DiArtikel.ShowModal()
        result = DiArtikel.get_result()
        print("AfpLoad_FaArtikelAusw result:", result)
        DiArtikel.Destroy()
    elif Ok is None:
        # flag for direct selection
        result = Afp_selectGetValue(globals.get_mysql(), "ARTIKEL", "ArtikelNr", index, value)
        #print result
    #globals.mysql.unset_debug()
    return result      


## allow direct selection of different Faktura methods (AfpMotor-style)
class AfpDialog_FaCustomSelect(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):  
        self.globals = None
        self.rows = 7
        self.minrows = 7
        self.cols = 4
        self.col_percents = [30, 15, 20, 35]
        self.ident = []
        AfpDialog.__init__(self,None, -1, "")
        self.SetSize((650,415))
        self.SetTitle("Schnellauswahl")
        #self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
        
    ## set up dialog widgets - overwritten from AfpDialog
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.label_Direkt = wx.StaticText(panel, -1, label="Direktwahl", pos=(90,10), size=(80,20), name="LDirekt")
        self.label_Rechnung = wx.StaticText(panel, -1, label="Rechnungsverwaltung", pos=(303,10), size=(150,20), name="LRechnung")
        self.label_Zusatz = wx.StaticText(panel, -1, label="Zusatzfunktionen", pos=(518,10), size=(150,20), name="LZusatz")
        self.label_Auftrag= wx.StaticText(panel, -1, label="Auftragsverwaltung", pos=(15,160), size=(160,20), name="LAuftrag")
 
        self.radio_Memo = wx.RadioButton(panel, -1,  label = "Memo", pos=(280,30), size=(80,15),  style=wx.RB_GROUP,  name="RMemo") 
        self.radio_KVA = wx.RadioButton(panel, -1,  label = "KVA", pos=(280,55), size=(80,15),  name="RKVA") 
        self.radio_Angebot = wx.RadioButton(panel, -1,  label = "Angebot", pos=(280,70), size=(80,15),  name="RAngebot") 
        self.radio_Auftrag = wx.RadioButton(panel, -1,  label = "Auftrag", pos=(280,85), size=(80,15),  name="RAuftrag") 
        self.radio_Rechnung = wx.RadioButton(panel, -1,  label = "Rechnung", pos=(280,100), size=(90,15),  name="RRechnung") 
        self.radio_Bestellung = wx.RadioButton(panel, -1,  label = "Bestellung", pos=(280,125), size=(90,15),  name="RBestellung") 
        
        self.choice_Art = wx.Choice(panel, -1,  pos=(175,160), size=(250,20),  choices=AfpFa_possibleOpenKinds(),  name="CArt")   
        self.Bind(wx.EVT_CHOICE, self.On_CArt, self.choice_Art)
         
        self.button_Bar = wx.Button(panel, -1, label="&Bar", pos=(20,30), size=(100,50), name="Bar")
        self.Bind(wx.EVT_BUTTON, self.On_Bar, self.button_Bar)
        self.button_XXX = wx.Button(panel, -1, label="&XXX", pos=(20,90), size=(100,50), name="XXX")
        #self.Bind(wx.EVT_BUTTON, self.On_XXX, self.button_XXX)
        
        self.button_Zahl = wx.Button(panel, -1, label="&Zahlung", pos=(140,30), size=(100,50), name="Zahl")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahl)
        self.button_Ware = wx.Button(panel, -1, label="&Wareneingang", pos=(140,90), size=(100,50), name="Ware")
        self.Bind(wx.EVT_BUTTON, self.On_Ware, self.button_Ware)
        
        self.button_Neu = wx.Button(panel, -1, label="&Neu", pos=(400,30), size=(100,50), name="Neu")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)
        self.button_Suche = wx.Button(panel, -1, label="&Suchen", pos=(400,90), size=(100,50), name="Suche")
        self.Bind(wx.EVT_BUTTON, self.On_Suche, self.button_Suche)
        
        self.button_Adresse = wx.Button(panel, -1, label="&Adresse", pos=(520,30), size=(100,50), name="Adresse")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse, self.button_Adresse)
        self.button_Kasse = wx.Button(panel, -1, label="&Kasse", pos=(520,90), size=(100,50), name="Kasse")
        self.Bind(wx.EVT_BUTTON, self.On_Kasse, self.button_Kasse)
        self.check_Strich = wx.CheckBox(panel, -1, label="Strich&code", pos=(520,150), size=(120,20), name="Strich")
        self.button_Mehr = wx.Button(panel, -1, label="&Mehr", pos=(520,240), size=(100,50), name="Mehr")
        self.Bind(wx.EVT_BUTTON, self.On_Mehr, self.button_Mehr)
        self.button_Ende = wx.Button(panel, -1, label="Be&enden", pos=(520,300), size=(100,50), name="Ende")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Ende)
       
        #self.setWx(panel, [390, 220, 80, 30], [480, 220, 80, 30]) # set Edit and Ok widgets
        #self.grid_auswahl = wx.grid.Grid(panel, -1, pos=(15,182), size=(500,180), style=wx.ALWAYS_SHOW_SB, name="Auswahl")
        self.grid_auswahl = wx.grid.Grid(panel, -1, pos=(15,182), size=(500,180), name="Auswahl")
        self.grid_auswahl.CreateGrid(self.rows, self.cols)
        self.grid_auswahl.SetRowLabelSize(0)
        self.grid_auswahl.SetColLabelSize(0)
        self.grid_auswahl.EnableEditing(0)
        self.grid_auswahl.EnableDragColSize(0)
        self.grid_auswahl.EnableDragRowSize(0)
        self.grid_auswahl.EnableDragGridSize(0)
        self.grid_auswahl.SetSelectionMode(wx.grid.Grid.GridSelectRows)   
        for col in range(self.cols):
            self.grid_auswahl.SetColSize(col, int(self.col_percents[col]*4.9)) # 5 = 500/100
            for row in range(self.rows):
                self.grid_auswahl.SetReadOnly(row, col)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick, self.grid_auswahl)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_RIGHT_CLICK, self.On_RClick, self.grid_auswahl)
        self.gridmap.append("Auswahl")

    ## populate the 'Auswahl' grid, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_Auswahl(self):
        typ = self.choice_Art.GetStringSelection()
        self.datei, rows = AfpFa_getSelectedRows(self.globals.get_mysql(), typ, self.debug)
        lgh = len(rows)
        rows = Afp_MatrixJoinCol(rows)
        #print "AfpDialog_FaCustomSelect.Pop_Auswahl:", lgh, rows
        if lgh < self.minrows:
            self.grid_resize(self.grid_auswahl, self.minrows)
            self.rows = self.minrows
        else:
            self.grid_resize(self.grid_auswahl, lgh)
            self.rows = lgh
        self.ident = []
        for row in range(self.rows):
            for col in range(self.cols):
                if row < lgh:
                    self.grid_auswahl.SetCellValue(row, col,  rows[row][col])
                else:
                    self.grid_auswahl.SetCellValue(row, col,  "")
            if row < lgh:
                self.ident.append(rows[row][2])

    ## attach global data to dialog, populate
    # @param globals - globals to be attached
    def attach_globals(self, globals):
        self.globals = globals
        self.debug = globals.is_debug()
        if self.globals.os_is_windows():
            self.rows = int(1.4 * self.rows)
            self.minrows = int(1.4 * self.minrows)
        self.choice_Art.SetSelection(0)
        self.Populate()
        
    ## return label of selected radio button
    def get_selected_RadioButton(self):
        label = ""
        if self.radio_Memo.GetValue(): label = self.radio_Memo.GetLabel()
        elif self.radio_KVA.GetValue(): label = self.radio_KVA.GetLabel()
        elif self.radio_Angebot.GetValue(): label = self.radio_Angebot.GetLabel()
        elif self.radio_Auftrag.GetValue(): label = self.radio_Auftrag.GetLabel()
        elif self.radio_Rechnung.GetValue(): label = self.radio_Rechnung.GetLabel()
        elif self.radio_Bestellung.GetValue(): label = self.radio_Bestellung.GetLabel()
        return label
        
    ## Eventhandler Grid DBLClick - invoke direct selection of invoice
    # @param event - event which initiated this action   
    def On_DClick(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_DClick'")
        ind = event.GetRow()
        print("Event handler `AfpDialog_FaCustomSelect.On_DClick'", ind)
        event.Skip()        
        if ind < len(self.ident):
            RechNr = self.ident[ind]
            self.data = AfpFa_getSelectionList(self.globals, RechNr, self.datei)
            self.Ok = True
            self.EndModal(wx.ID_OK)
    ## Eventhandler Grid RightClick - invoke memo edit
    # @param event - event which initiated this action   
    def On_RClick(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_RClick'")
        print("Event handler `AfpDialog_FaCustomSelect.On_RClick' not implemented!", event.GetRow())
        event.Skip()

    ## Eventhandler CHOICE - invoke new choice display to grid
    # @param event - event which initiated this action   
    def On_CArt(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_CArt'")
        print("Event handler `AfpDialog_FaCustomSelect.On_CArt' not implemented!")
        self.Populate()
        event.Skip()

    ## Eventhandler BUTTON - invoke direct sale and payment
    # @param event - event which initiated this action   
    def On_Bar(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_Bar'")
        self.Ok = "Bar"
        print("Event handler `AfpDialog_FaCustomSelect.On_Bar:", self.Ok, self.data)
        self.EndModal(wx.ID_CANCEL)
        event.Skip()
        
   ## Eventhandler BUTTON - invoke payment
    # @param event - event which initiated this action   
    def On_Zahlung(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_Zahlung'")
        self.Ok = "Zahlung"
        print("Event handler `AfpDialog_FaCustomSelect.On_AZahlung:", self.Ok, self.data)
        self.EndModal(wx.ID_CANCEL)
        event.Skip()
        
    ## Eventhandler BUTTON - invoke delivery
    # @param event - event which initiated this action   
    def On_Ware(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_Ware'")
        self.Ok = "Ware"
        print("Event handler `AfpDialog_FaCustomSelect.On_Ware:", self.Ok, self.data)
        self.EndModal(wx.ID_CANCEL)
        event.Skip()

    ## Eventhandler BUTTON - generate new tour entrys
    # @param event - event which initiated this action   
    def On_Neu(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_Neu'")
        radio = self.get_selected_RadioButton()
        if radio == "Memo":
            print("AfpDialog_FaCustomSelect.On_Neu Memo!")
        else:
            self.Ok = "Neu"
            self.data = radio
            print("Event handler `AfpDialog_FaCustomSelect.On_Neu:", self.Ok, self.data)
            self.EndModal(wx.ID_CANCEL)
        event.Skip()        
    ## Eventhandler BUTTON - invoke address selection
    # @param event - event which initiated this action   
    def On_Adresse(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_Adresse'")
        self.Ok = "Adresse"
        print("Event handler `AfpDialog_FaCustomSelect.On_Adresse:", self.Ok, self.data)
        self.EndModal(wx.ID_CANCEL)
        event.Skip()

    ## Eventhandler BUTTON - invoke caisse
    # @param event - event which initiated this action   
    def On_Kasse(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_Kasse'")
        self.Ok = "Kasse"
        print("Event handler `AfpDialog_FaCustomSelect.On_Kasse:", self.Ok, self.data)
        self.EndModal(wx.ID_CANCEL)
        event.Skip()

   ## Eventhandler BUTTON - invoke additional functions
    # @param event - event which initiated this action   
    def On_Mehr(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_Mehr'")
        self.Ok = "Mehr"
        print("Event handler `AfpDialog_FaCustomSelect.On_Mehr:", self.Ok, self.data)
        self.EndModal(wx.ID_CANCEL)
        event.Skip()

    ## Eventhandler BUTTON - search for entry
    # @param event - event which initiated this action   
    def On_Suche(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_Suche'")
        radio = self.get_selected_RadioButton()
        if radio == "Memo":
            print("AfpDialog_FaCustomSelect.On_Suche Memo!")
        else:
            self.Ok = "Suchen"
            self.data = radio
            print("Event handler `AfpDialog_FaCustomSelect.On_Suche:", self.Ok, self.data)
            self.EndModal(wx.ID_CANCEL)
        event.Skip()

    ## Eventhandler BUTTON - leave dialog
    # @param event - event which initiated this action   
    def On_Ende(self,event):
        if self.debug: print("Event handler `On_Ende'")
        self.Ok = False
        self.EndModal(wx.ID_CANCEL)
        event.Skip()
       
    ## event handler when window is activated
    # @param event - event which initiated this action   
    def On_Activate(self,event):
        if not self.active:
            print("Event handler `On_Activate' not implemented")
     
# end of class AfpDialog_FaCustomSelect

## loader routine for custom Faktura selection
# returns the values Ok and data:
# - if Ok = True: data is selected or generated the SelectionList
# - if Ok = False: no data is returned, dialog has been canceled
# - if Ok is a string, it hold the button label that has been pushed and data holds the selected radiobutton label
def AfpLoad_FaCustomSelect(globals):
    DiSelect = AfpDialog_FaCustomSelect(None)
    DiSelect.attach_globals(globals)
    DiSelect.ShowModal()
    Ok = DiSelect.get_Ok()
    data = None
    if Ok:
        data = DiSelect.get_data()
    DiSelect.Destroy()
    return Ok, data

## allows the entry and modification of an invoice line
class AfpDialog_FaLine(AfpDialog):
    def __init__(self, *args, **kw):
        AfpDialog.__init__(self,None, -1, "")
        self.action = None
        self.SetSize((280,165))
        self.SetTitle("Rechnungszeile ändern")
        self.SetFocus()

    ## set up dialog widgets - overwritten from AfpDialog
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.label_TArtikelt = wx.StaticText(panel, -1, label="Artikelauswahl", pos=(10,10), size=(160,20), name="TArtikel")
        self.text = wx.TextCtrl(panel, -1, value="", pos=(10,40), size=(180,22), style=0, name="Text")
        
        self.radio_Artikel = wx.RadioButton(panel, -1,  label = "Artikel &Nr.", pos=(10,70), size=(120,15),  style=wx.RB_GROUP,  name="RArtikel") 
        self.radio_Bez = wx.RadioButton(panel, -1,  label = "&Bezeichnung", pos=(10,85), size=(120,15),  name="RBez") 
        self.radio_Ohne = wx.RadioButton(panel, -1,  label = "&ohne Artikelnummer", pos=(10,100), size=(180,15),  name="ROhne") 
 
        self.button_Text = wx.Button(panel, -1, label="&Text", pos=(200,10), size=(70,35), name="BText")
        self.Bind(wx.EVT_BUTTON, self.On_Text, self.button_Text)
        self.button_Abbr = wx.Button(panel, id=wx.ID_CANCEL, label="&Abbruch", pos=(200,50), size=(70,35), name="BEnde")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Abbr)
        self.button_Artikel = wx.Button(panel, id=wx.ID_OK, label="&Ok", pos=(200,90), size=(70,35), name="BArtikel")
        self.Bind(wx.EVT_BUTTON, self.On_Artikel, self.button_Artikel)
        self.button_Artikel.SetDefault()
        #self.setWx(panel, [400, 6, 75, 36], [400, 90, 75, 36]) # set Edit and Ok widgets

    ## attach data to dialog 
    # @param ident - identifier to be displayed and edited
    # @param name - if ident == None: name to be displayed and edited
    # @param debug - debug flag
    def set_data(self, ident, name, debug = False):
        text = ident
        if text is None:
            text = name
        if text: self.text.SetValue(text)
        if ident is None: 
            self.radio_Ohne.SetValue(True)
        self.debug = debug
    ## get radio selection 
    def get_radio_value(self):
        label = ""
        if self.radio_Artikel.GetValue(): label = "ArtikelNr"
        elif self.radio_Bez.GetValue(): label = "Bezeichnung"
        elif self.radio_Ohne.GetValue(): label = "frei"
        return label
    ## retrieve action set
    def get_action(self):
        return self.action
        
    # Event Handlers 
    ##  Eventhandler BUTTON  use thie entry in this dialog appropriate to settings
    # @param event - event which initiated this action   
    def On_Artikel(self,event):
        if self.debug: print("Event handler `On_Artikel'")
        self.action = [self.text.GetValue(), self.get_radio_value()]
        #event.Skip()
        self.EndModal(wx.ID_OK)
    ##  Eventhandler BUTTON  insert a plain text line into invoice
    # @param event - event which initiated this action   
    def On_Text(self,event):
        if self.debug: print("Event handler `On_Text'")
        event.Skip()
        self.EndModal(wx.ID_OK)
    ##  Eventhandler BUTTON  end invoice line editing modus
    # @param event - event which initiated this action   
    def On_Ende(self,event):
        if self.debug: print("Event handler `On_Ende'")
        event.Skip()
        self.EndModal(wx.ID_CANCEL)


## loader routine for dialog for invoice entries, returns Ok flag and action = [textvalue, radiovalue]
# @param ident - identifier to be displayed and edited
# @param name - if ident == None: name to be displayed and edited
# @param debug - debug flag
def AfpLoad_FaLine( ident = None, name = False,  debug = False):
    #print "AfpLoad_FaLine init:",ident, name, debug
    EditLine = AfpDialog_FaLine(None)
    if ident or name or debug: EditLine.set_data(ident, name, debug)
    res = EditLine.ShowModal()
    Ok = None
    action = None
    if res == wx.ID_OK:
        action = EditLine.get_action()
        if action:
            Ok = True
        else:
            Ok = False
    EditLine.Destroy()
    print("AfpLoad_FaLine destroy:",Ok, action, res)
    return Ok, action

