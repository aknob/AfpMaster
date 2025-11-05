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
#    Copyright© 1989 - 2025  afptech.de (Andreas Knoblauch)
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
from AfpBase.AfpDatabase.AfpSQL import AfpSQLTableSelection
from AfpBase.AfpUtilities.AfpStringUtilities import Afp_isEAN
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpBaseDialog import *
from AfpBase.AfpBaseDialogCommon import *
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_DiAdEin_fromKNr
from AfpBase.AfpBaseAdRoutines import AfpAdresse, AfpAdresse_getListOfTable
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

#from AfpEvent.AfpEvRoutines import *
from AfpFaktura.AfpFaRoutines import *

## dialog for selection of manufacurer data \n
# @param globals - global data, inclsive mysql connection
# @param new - flag if additional line for creation of a new manufacturere should be included
# @param debug - if given, flag for debug-modus
def AfpFaktura_listManufacturer(globals, new = False, debug = False):
    hersteller = AfpSQLTableSelection(globals.get_mysql(), "ARTHERS", debug, "HersNr")
    hersteller.load_data("")
    if new:
        liste = ["--- Neuen Hersteller anlegen ---"]
        ident = [None]
    else:
        liste = []
        ident = []
    rows = hersteller.get_values("Kennung,Hersteller,HersNr,KundenNr")
    for row in rows:
        adresse = AfpAdresse(globals, row[3])
        liste.append(row[0] + "  " + row[1] + "   " + adresse.get_name(True) + " " + adresse.get_value("Ort"))
        ident.append(row[2])
    return liste, ident
## dialog for selection of manufacurer data \n
# @param globals - global data, inclsive mysql connection
# @param text - to be displayed in second line
# @param debug - if given, flag for debug-modus
def AfpFaktura_selectManufacturer(globals, text, debug = False):
    hersdat = None
    liste, ident =  AfpFaktura_listManufacturer(globals, True, debug)
    nr, ok = AfpReq_Selection("Bitte Hersteller oder Lieferanten auswählen,", text, liste, "Herstellerauswahl", ident)
    if ok and nr:
        hersdat = AfpManufact(globals, nr, None, debug)
    return hersdat, ok
            
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
        self.typ = AfpFaktura_getClearName(tablename) + "sauswahl"
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
    # overwritten for "Faktura" use
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
    kind = AfpFaktura_getClearName(table)
    if ask:
        sort_list = AfpFaktura_getOrderlistOfTable()        
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
        result = Afp_selectGetValue(globals.get_mysql(), table, "RechNr", index, value)
    #print("AfpLoad_FaAusw result:", result)
    return result      

## simple select requester for selection of a indicated typ
# @param mysql - database handle to retrieve data from
# @param typ - indicated typ, where rows should be retrieved
# @param text - text to be displayed in requester
# @param debug - flag if debug text should be written
def AfpReq_FaSelectedRow(mysql, typ, text, debug):
    datei, rows = AfpFaktura_getSelectedRows(mysql, typ, debug)
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
        self.datei = "ARTIKEL"
        self.modul = "Faktura"
    ## get the definition of the selection grid content \n
    # overwritten for "Faktura" use
    def get_grid_felder(self): 
        Felder = [["ArtikelNr.ARTIKEL",30], 
                            ["Bezeichnung.ARTIKEL",30], 
                            ["Hersteller.ARTHERS",15], 
                            ["Lagerort.ARTIKEL",10], 
                            ["Nettopreis.ARTIKEL",15], 
                            ["HersNr.ARTHERS = HersNr.ARTIKEL",None],
                            ["ArtikelNr.ARTIKEL",None]] # Ident column
        return Felder
    ## invoke the dialog for a new entry \n
    # overwritten for "Artikel" use
    def invoke_neu_dialog(self, globals, eingabe, filter):
        ken = AfpFaktura_getShortManu(globals, eingabe)
        if ken:
            hers = AfpManufact(globals, ken, "Kennung", self.debug)
            ok = True
            eingabe = "!" + eingabe[len(ken) + 1:]
        else:
            hers, ok = AfpFaktura_selectManufacturer(self.globals, "aus dessen Datei ein Artikel übenommen werden soll.", self.debug) 
            print ("AfpDialog_FaArtikelAusw.invoke_neu_dialog Hers:", hers, ok)
        if ok and not hers:
                ok, hers = AfpLoad_FaManufact(self.globals, None)
        if ok and hers:
            newarticle = AfpLoad_FaArtikelAusw(self.globals, "ArtikelNr", eingabe, hers.get_manufact_table(), filter, False, hers)
            if newarticle:
                ok = AfpLoad_FaArticle(newarticle, True)
                if ok:
                    newarticle.store()
                    return True
        return False
## dialog for selection of manufacturer content data \n
class AfpDialog_FaManufactArtikelAusw(AfpDialog_Auswahl):
    ## initialise dialog
    def __init__(self, datei):
        self.table = datei # needed, as get_grid_felder is used in 'AfpDialog_Auswahl.__init__'
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.typ = "Hersteller-Artikelauswahl"
        self.datei = datei
        self.modul = "Faktura"
        self.manu = None
        self.SetBackgroundColour(wx.Colour(212, 212, 212))
    ## get the definition of the selection grid content \n
    # overwritten for "Faktura" use
    def get_grid_felder(self): 
        Felder = [["ArtikelNr." + self.table,30], 
                            ["Bezeichnung." + self.table,40], 
                            ["PreisGrp." + self.table,10], 
                            ["Listenpreis." + self.table,20], 
                            ["ArtikelNr." + self.table,None]] # Ident column
        return Felder
    ## invoke the dialog for a new entry \n
    # overwritten for "Artikel" use
    def invoke_neu_dialog(self, globals, eingabe, filter):
        print("AfpDialog_FaManufactArtikelAusw.invoke_neu_dialog not implemented!")
        if self.manu:
            print("AfpDialog_FaManufactArtikelAusw.invoke_neu_dialog Artikeldialog für:", eingabe)
        return False
    ## return result
    # overwritten for row return
    def get_result(self):
        if self.result:
            if Afp_isString(self.result):
                if self.manu:
                    article = self.manu.get_articles(self.result)
                    print("AfpDialog_FaManufactArtikelAusw.get_result:", article)
                    if article: article.view()
                    return article
                else:
                    print("WARNING in AfpDialog_FaManufactArtikelAusw: Manufacturer not provided for function.")
            else:
                return self.result
        return None
    ## set manufacturer
    # @param manu - AfpManucaft SelectionList
    def set_manufacturer(self, manu):
        self.manu = manu

## loader routine for artikel selection dialog 
# @param globals - global variables including database connection
# @param index - column which should give the order
# @param value -  if given,initial value to be searched
# @param datei -  database table to be searched
# @param where - if given, filter for search in table
# @param ask - flag if it should be asked for a string before filling dialog
# @param manu - if datei is set, manufacturer data may be submitted here 
def AfpLoad_FaArtikelAusw(globals, index, value = "", datei = "ARTIKEL", where = None, ask = False, manu = None):
    result = None
    Ok = True
    direct = False
    #globals.mysql.set_debug()
    if ask:
        if not value: value = ""
        value, Ok = AfpReq_Text("Bitte Suchbegriff für Artikelauswahl eingeben:", "", value, "Artikelauswahl")
    else:
        if len(value) and value[0] == "!":
            value = value[1:]
            direct = True
    if Ok and value:
        if AfpFaktura_getShortManu(globals, value) or direct:
            index = "ArtikelNr"
            #Ok = None
        elif Afp_isEAN(value):
            index = "EAN"
            Ok = None
        else:
            index = "Bezeichnung"
    #print("AfpLoad_FaArtikelAusw index:", index, value, Ok)
    if Ok:
        if datei == "ARTIKEL" or datei == "Artikel":
            DiArtikel = AfpDialog_FaArtikelAusw()
            text = "Bitte Artikel auswählen:"
            DiArtikel.initialize(globals, index, value, where, text)
            DiArtikel.ShowModal()
            result = DiArtikel.get_result()
            #print("AfpLoad_FaArtikelAusw result:", result)
            DiArtikel.Destroy()
        else:
            DiArtikel = AfpDialog_FaManufactArtikelAusw(datei)
            if manu:
                text = "Bitte Artikel aus der Herstellerdatei '" + manu.get_value("Hersteller") + "' auswählen:"
                DiArtikel.set_manufacturer(manu)
            else:
                text = "Bitte Artikel aus Herstellerdatei auswählen:"
            DiArtikel.initialize(globals, index, value, where, text)
            DiArtikel.ShowModal()
            result = DiArtikel.get_result()
            #print("AfpLoad_FaArtikelAusw result:", result)
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
        self.col_percents = [25, 15, 10, 50]
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
 
        self.radio_Memo = wx.RadioButton(panel, -1,  label = "Memo", pos=(280,30), size=(80,20),  style=wx.RB_GROUP,  name="RMemo") 
        self.radio_KVA = wx.RadioButton(panel, -1,  label = "KVA", pos=(280,50), size=(80,20),  name="RKVA") 
        self.radio_Angebot = wx.RadioButton(panel, -1,  label = "Angebot", pos=(280,70), size=(80,20),  name="RAngebot") 
        self.radio_Auftrag = wx.RadioButton(panel, -1,  label = "Auftrag", pos=(280,90), size=(80,20),  name="RAuftrag") 
        self.radio_Rechnung = wx.RadioButton(panel, -1,  label = "Rechnung", pos=(280,110), size=(90,20),  name="RRechnung") 
        self.radio_Bestellung = wx.RadioButton(panel, -1,  label = "Bestellung", pos=(280,130), size=(90,20),  name="RBestellung") 
        
        self.choice_Art = wx.Choice(panel, -1,  pos=(175,150), size=(250,30),  choices=AfpFaktura_possibleOpenKinds(),  name="CArt")   
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
        self.datei, rows = AfpFaktura_getSelectedRows(self.globals.get_mysql(), typ, self.debug)
        lgh = len(rows)
        rows = Afp_MatrixJoinCol(reversed(rows))
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
        self.choice_Art.SetSelection(3)
        self.radio_Angebot.SetValue(True)
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
    ## return index of grid combo-box
    def get_grid_ind(self):
        return self.choice_Art.GetSelection()
    ## set index of grid combo-box
    # @param ind -index to be selected
    def set_grid_ind(self, ind):
       self.choice_Art.SetSelection(ind)
       self.Pop_Auswahl()
    ## Eventhandler Grid DBLClick - invoke direct selection of invoice
    # @param event - event which initiated this action   
    def On_DClick(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_DClick'")
        ind = event.GetRow()
        #print("Event handler `AfpDialog_FaCustomSelect.On_DClick'", ind, self.ident)
        event.Skip()        
        if ind < len(self.ident):
            RechNr = self.ident[ind]
            data = AfpFaktura_getSelectionList(self.globals, RechNr, self.datei)
            if self.datei == "ADMEMO":
                name = data.get_name()
                ok = AfpReq_Question("Soll das Memo von", name + " deaktiviert werden?", "Memo")
                if ok:
                    data.deactivate()
                    self.Pop_Auswahl()
            else:
                self.data = data
                self.Ok = True
                self.EndModal(wx.ID_OK)
    ## Eventhandler Grid RightClick - invoke memo edit
    # @param event - event which initiated this action   
    def On_RClick(self,event):
        if self.debug: print("Event handler `AfpDialog_FaCustomSelect.On_RClick'")
        ind = event.GetRow()
        print("Event handler `AfpDialog_FaCustomSelect.On_RClick' not implemented!", ind)
        if ind < len(self.ident):
            RechNr = self.ident[ind]
            data = AfpFaktura_getSelectionList(self.globals, RechNr, self.datei)
            name = data.get_name()
            if self.datei == "ADMEMO":
                field = "Memo"
                text = data.get_value(field)
                mtext,ok = AfpReq_Text("Bitte den Memotext für", name + " eigeben!", text, "Memoeingabe")
            else:
                field = "Bem"
                text = data.get_value(field)
                if self.datei == "KVA":
                    vorgang = data.get_value("Zustand")
                    if vorgang == "Angebot": vorgang = "das " +  vorgang
                    else: vorgang = "den " +  vorgang
                else:
                    vorgang = "die Rechnung"
                vorgang += " Nr. " + data.get_string_value()
                mtext,ok = AfpReq_Text("Bitte die Bemerkung für " + vorgang, "von " + name + " eigeben!", text, "Bemerkung")
            if mtext and ok:
                data.set_value(field, mtext)
                data.store()
                self.Pop_Auswahl()
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
            text = "Bitte Person auswählen, der das Memo zugeordnet werden soll:"
            knr = AfpLoad_AdAusw(self.globals,"ADRESSE","NamSort","", None, text, True)
            if knr:
                ad = AfpAdresse(self.globals, knr)
                name = ad.get_name()
                mtext,ok = AfpReq_Text("Bitte den Memotext für", name + " eigeben!", "", "Memoeingabe")
                if mtext and ok:
                    memo = AfpMemo(self.globals)
                    memo.initialize(knr, None, mtext)
                    memo.store()
                    self.Pop_Auswahl()
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
# @param globals - global variables given (including mysql-connection)
# @param inind - if given, initial grid index
# returns the values Ok and data:
# - if Ok = True: data is selected or generated the SelectionList
# - if Ok = False: no data is returned, dialog has been canceled
# - if Ok is a string, it hold the button label that has been pushed and data holds the selected radiobutton label
# returns also actind - actuel index of grid selection
def AfpLoad_FaCustomSelect(globals, inind = None):
    DiSelect = AfpDialog_FaCustomSelect(None)
    DiSelect.attach_globals(globals)
    if inind: DiSelect.set_grid_ind(inind)
    DiSelect.ShowModal()
    Ok = DiSelect.get_Ok()
    data = None
    actind = None
    if Ok:
        data = DiSelect.get_data()
        actind = DiSelect.get_grid_ind()
    DiSelect.Destroy()
    return Ok, data, actind 

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
        self.text = wx.TextCtrl(panel, -1, value="", pos=(10,30), size=(180,22), style=0, name="Text")
        
        self.radio_Artikel = wx.RadioButton(panel, -1,  label = "Artikel &Nr.", pos=(10,55), size=(120,20),  style=wx.RB_GROUP,  name="RArtikel") 
        self.radio_Bez = wx.RadioButton(panel, -1,  label = "&Bezeichnung", pos=(10,75), size=(120,20),  name="RBez") 
        self.radio_Ohne = wx.RadioButton(panel, -1,  label = "&ohne Artikelnummer", pos=(10,95), size=(180,20),  name="ROhne") 
        self.radio_Text = wx.RadioButton(panel, -1,  label = "&Text", pos=(10,115), size=(180,20),  name="RText") 
 
        self.button_Ausw= wx.Button(panel, -1, label="&Auswahl", pos=(200,10), size=(70,35), name="BAusw")
        self.Bind(wx.EVT_BUTTON, self.On_Ausw, self.button_Ausw)
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
        elif self.radio_Text.GetValue(): label = "Text"
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
    def On_Ausw(self,event):
        if self.debug: print("Event handler `On_Ausw'")
        self.action = self.text.GetValue()
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
        if action and not Afp_isString(action):
            Ok = True
        else:
            Ok = False
    EditLine.Destroy()
    #print("AfpLoad_FaLine destroy:",Ok, action, res)
    return Ok, action
## dialog to maintain articles
class AfpDialog_FaArticle(AfpDialog):
    def __init__(self, hersteller, idents):
        self.hers_liste = hersteller
        self.hers_idents = idents
        AfpDialog.__init__(self,None, -1, "")
        self.hersteller = None
        self.fix_hersteller = False
        self.readonly = ["PrsGrp_Artikel"]
        self.preset =  {}
        self.presetedit = []
        self.preseteditcolor = (245,245,220)
        self.changecolor = (220, 192, 192)
        self.SetTitle("Artikelpflege")

    ## set up dialog widgets - overwritten from AfpDialog
    def InitWx(self):
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.label_ArtikelNr = wx.StaticText(self, -1, label="Artikelnummer:", name="LArtikelNr")
        self.label_Bez = wx.StaticText(self, -1, label="Bezeichnung:", name="LBez")
        self.label_Bestand = wx.StaticText(self, -1, label="Bestand:", name="LBestand")
        self.label_Lager = wx.StaticText(self, -1, label="Lager:", name="LLager")
        self.text_ArtikelNr = wx.TextCtrl(self, -1, value="", style=0, name="ArtikelNr_Artikel")
        self.textmap["ArtikelNr_Artikel"] = "ArtikelNr.ARTIKEL"
        self.text_ArtikelNr.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.text_Bez = wx.TextCtrl(self, -1, value="", style=0, name="Bez_Artikel")
        self.textmap["Bez_Artikel"] = "Bezeichnung.ARTIKEL"
        self.text_Bez.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.text_Bestand = wx.TextCtrl(self, -1, value="", style=0, name="Bestand_Artikel")
        self.textmap["Bestand_Artikel"] = "Bestand.ARTIKEL"
        self.text_Bestand.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.text_Lager = wx.TextCtrl(self, -1, value="", style=0, name="Lager_Artikel")
        self.textmap["Lager_Artikel"] = "Lagerort.ARTIKEL"
        self.text_Lager.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.line1a_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line1a_sizer.Add(self.label_ArtikelNr,0,wx.EXPAND)
        self.line1a_sizer.Add(self.text_ArtikelNr,0,wx.EXPAND)
        self.line1b_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line1b_sizer.Add(self.label_Bez,0,wx.EXPAND)
        self.line1b_sizer.Add(self.text_Bez,0,wx.EXPAND)
        self.line1c_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line1c_sizer.Add(self.label_Bestand,0,wx.EXPAND)
        self.line1c_sizer.Add(self.text_Bestand,0,wx.EXPAND)
        self.line1d_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line1d_sizer.Add(self.label_Lager,0,wx.EXPAND)
        self.line1d_sizer.Add(self.text_Lager,0,wx.EXPAND)
        self.line1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.line1_sizer.AddSpacer(10)
        self.line1_sizer.Add(self.line1a_sizer,2,wx.EXPAND)
        self.line1_sizer.AddSpacer(10)
        self.line1_sizer.Add(self.line1b_sizer,2,wx.EXPAND)
        self.line1_sizer.AddSpacer(10)
        self.line1_sizer.Add(self.line1c_sizer,0,wx.EXPAND)
        self.line1_sizer.AddSpacer(10)
        self.line1_sizer.Add(self.line1d_sizer,1,wx.EXPAND) 
        self.line1_sizer.AddSpacer(10)

        self.label_Hers = wx.StaticText(self, -1, label="Hersteller:", name="LHers")
        self.label_PrsGrp = wx.StaticText(self, -1, label="Preisgruppe:", name="LPrsGrp")
        self.label_EAN = wx.StaticText(self, -1, label="EAN:", name="LEAN")
        self.label_Sonder = wx.StaticText(self, -1, label="Sonderpreis:", name="LSonder")
        self.combo_Hers = wx.ComboBox(self, -1, value="", choices=self.hers_liste, style=wx.CB_DROPDOWN, name="CHers") 
        self.Bind(wx.EVT_COMBOBOX, self.On_Hersteller, self.combo_Hers)
        self.text_PrsGrp = wx.TextCtrl(self, -1, value="", style=wx.TE_READONLY, name="PrsGrp_Artikel")
        self.textmap["PrsGrp_Artikel"] = "PreisGrp.ARTIKEL"
        self.text_PrsGrp.SetBackgroundColour(self.readonlycolor)
        self.text_EAN = wx.TextCtrl(self, -1, value="", style=0, name="EAN_Artikel")
        self.textmap["EAN_Artikel"] = "EAN.ARTIKEL"
        self.text_Sonder = wx.TextCtrl(self, -1, value="", style=0, name="Sonder_Artikel")
        self.textmap["Sonder_Artikel"] = "Sonderpreis.ARTIKEL"
        self.text_EAN.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.line2a_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line2a_sizer.Add(self.label_Hers,0,wx.EXPAND)
        self.line2a_sizer.Add(self.combo_Hers,0,wx.EXPAND)
        self.line2b_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line2b_sizer.Add(self.label_PrsGrp,0,wx.EXPAND)
        self.line2b_sizer.Add(self.text_PrsGrp,0,wx.EXPAND)
        self.line2c_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line2c_sizer.Add(self.label_EAN,0,wx.EXPAND)
        self.line2c_sizer.Add(self.text_EAN,0,wx.EXPAND)
        self.line2d_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line2d_sizer.Add(self.label_Sonder,0,wx.EXPAND)
        self.line2d_sizer.Add(self.text_Sonder,0,wx.EXPAND)
        self.line2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.line2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.line2_sizer.AddSpacer(10)
        self.line2_sizer.Add(self.line2a_sizer,2,wx.EXPAND)
        self.line2_sizer.AddSpacer(10)
        self.line2_sizer.Add(self.line2b_sizer,1,wx.EXPAND)
        self.line2_sizer.AddSpacer(10)
        self.line2_sizer.Add(self.line2c_sizer,2,wx.EXPAND)
        self.line2_sizer.AddSpacer(10)
        self.line2_sizer.Add(self.line2d_sizer,1,wx.EXPAND)
        self.line2_sizer.AddSpacer(10)

        self.label_Einkauf = wx.StaticText(self, -1, label="Einkaufspreis:", name="LEinkauf")
        self.label_Rabatt = wx.StaticText(self, -1, label="% Rabatt:", name="LRabatt")
        self.label_Liste = wx.StaticText(self, -1, label="Listenpreis:", name="LListe")
        self.label_Hsp = wx.StaticText(self, -1, label="% Hsp:", name="LHsp")
        self.label_Preis = wx.StaticText(self, -1, label="Preis:", name="LPreis")
        self.text_Einkauf = wx.TextCtrl(self, -1, value="", style=0, name="Einkauf_Artikel")
        self.textmap["Einkauf_Artikel"] = "Einkaufspreis.ARTIKEL"
        self.text_Einkauf.Bind(wx.EVT_KILL_FOCUS, self.On_handlePricing)
        self.text_Rabatt = wx.TextCtrl(self, -1, value="", style=0, name="Rabatt_Artikel")
        self.textmap["Rabatt_Artikel"] = "Rabatt.ARTIKEL"
        self.text_Rabatt.Bind(wx.EVT_KILL_FOCUS, self.On_handlePricing)
        self.text_Liste = wx.TextCtrl(self, -1, value="", style=0, name="Liste_Artikel")
        self.text_Liste.Bind(wx.EVT_KILL_FOCUS, self.On_handlePricing)
        self.textmap["Liste_Artikel"] = "Listenpreis.ARTIKEL"
        self.text_Hsp = wx.TextCtrl(self, -1, value="", style=0, name="Hsp_Artikel")
        self.textmap["Hsp_Artikel"] = "Handelsspanne.ARTIKEL"
        self.text_Hsp.Bind(wx.EVT_KILL_FOCUS, self.On_handlePricing)
        self.text_Preis = wx.TextCtrl(self, -1, value="", style=0, name="Preis_Artikel")
        self.textmap["Preis_Artikel"] = "Nettopreis.ARTIKEL"
        self.text_Preis.Bind(wx.EVT_KILL_FOCUS, self.On_handlePricing)
        self.line3a_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line3a_sizer.Add(self.label_Einkauf,0,wx.EXPAND)
        self.line3a_sizer.Add(self.text_Einkauf,0,wx.EXPAND)
        self.line3b_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line3b_sizer.Add(self.label_Rabatt,0,wx.EXPAND)
        self.line3b_sizer.Add(self.text_Rabatt,0,wx.EXPAND)
        self.line3c_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line3c_sizer.Add(self.label_Liste,0,wx.EXPAND)
        self.line3c_sizer.Add(self.text_Liste,0,wx.EXPAND)
        self.line3d_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line3d_sizer.Add(self.label_Hsp,0,wx.EXPAND)
        self.line3d_sizer.Add(self.text_Hsp,0,wx.EXPAND)
        self.line3e_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line3e_sizer.Add(self.label_Preis,0,wx.EXPAND)
        self.line3e_sizer.Add(self.text_Preis,0,wx.EXPAND)
        self.line3_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.line3_sizer.AddSpacer(10)
        self.line3_sizer.Add(self.line3a_sizer,2,wx.EXPAND)
        self.line3_sizer.AddSpacer(10)
        self.line3_sizer.Add(self.line3b_sizer,1,wx.EXPAND)
        self.line3_sizer.AddSpacer(10)
        self.line3_sizer.Add(self.line3c_sizer,2,wx.EXPAND)
        self.line3_sizer.AddSpacer(10)
        self.line3_sizer.Add(self.line3d_sizer,1,wx.EXPAND)
        self.line3_sizer.AddSpacer(10)
        self.line3_sizer.Add(self.line3e_sizer,2,wx.EXPAND)
        self.line3_sizer.AddSpacer(10)
       
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.line1_sizer,2,wx.EXPAND)
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.line2_sizer,2,wx.EXPAND)
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.line3_sizer,2,wx.EXPAND)
        self.left_sizer.AddSpacer(10)
        #self.left_sizer.Add(self.line4_sizer,1,wx.EXPAND)
        #self.left_sizer.AddSpacer(10)

        self.button_Neu = wx.Button(self, -1, label="&Neu", name="Neu_FaArticle")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)
        self.button_Ablage = wx.Button(self, -1, label="Ab&lage", name="Ablage")
        self.Bind(wx.EVT_BUTTON, self.On_Ablage, self.button_Ablage)
        self.button_sizer = wx.BoxSizer(wx.VERTICAL)
        self.button_sizer.AddSpacer(10)
        self.button_sizer.AddStretchSpacer(1)
        self.button_sizer.Add(self.button_Neu,0,wx.EXPAND)
        self.button_sizer.AddStretchSpacer(1)
        self.button_sizer.Add(self.button_Ablage,0,wx.EXPAND)
        self.setWx(self.button_sizer, [1, 0, 0], [1, 0, 1]) # set Edit and Ok widgets
        self.button_sizer.AddSpacer(10)
        
        #self.left_sizer.Add(self.button_sizer,2,wx.EXPAND)
        #self.left_sizer.AddSpacer(10)
      
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.left_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.button_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)   
        self.SetSizerAndFit(self.sizer)
        #self.SetAutoLayout(1)
        #self.sizer.Fit(self)
    ## set fixed manufacturer
    def set_fix_manufacturer(self):
        self.fix_hersteller = True
    ## update prices due to changed value
    # @param name - name of ui-object that has been changed
    def reset_prices(self, name):
        go = False
        if name == "Liste_Artikel" or name == "Rabatt_Artikel":
            lstp = Afp_fromString(self.text_Liste.GetValue())
            disc = Afp_fromString(self.text_Rabatt.GetValue())
            go = True
        if name == "Einkauf_Artikel" or name == "Hsp_Artikel" or go:
            if go:
                ek = int(100*((100.0 - disc)/100.0)*lstp)/100.0
                self.text_Einkauf.SetValue(Afp_toString(ek))
                if Afp_isEps(ek - self.data.get_value("Einkaufspreis")):
                    self.text_Einkauf.SetBackgroundColour(self.changecolor)
                else:
                    self.text_Einkauf.SetBackgroundColour(self.editcolor)
            else:
                ek = Afp_fromString(self.text_Einkauf.GetValue())
            sur = Afp_fromString(self.text_Hsp.GetValue())
            if name == "Einkauf_Artikel":
                lstp = Afp_fromString(self.text_Liste.GetValue())
                disc = 100 - int(100*ek/lstp)
                self.text_Rabatt.SetValue(Afp_toString(disc))
                if "Rabatt_Artikel" in self.preset and Afp_toString(disc) == self.preset["Rabatt_Artikel"]:
                    self.text_Rabatt.SetBackgroundColour(self.preseteditcolor)
                elif disc == self.data.get_value("Rabatt"):
                    self.text_Rabatt.SetBackgroundColour(self.editcolor)
                else:
                    self.text_Rabatt.SetBackgroundColour(self.changecolor)
            go = True
        if  name == "Preis_Artikel" or go:
            if go:
                prs = int(100*((100.0 + sur)/100.0)*ek)/100.0
                self.text_Preis.SetValue(Afp_toString(prs))
                if Afp_isEps(prs - self.data.get_value("Nettopreis")):
                    self.text_Preis.SetBackgroundColour(self.changecolor)
                else:
                    self.text_Preis.SetBackgroundColour(self.editcolor)
            elif name == "Preis_Artikel":
                ek = Afp_fromString(self.text_Einkauf.GetValue())
                prs = Afp_fromString(self.text_Preis.GetValue())
                sur = 100 - int(100*prs/ek)
                self.text_Hsp.SetValue(Afp_toString(sur))
                if "Hsp_Artikel" in self.preset and Afp_toString(sur) == self.preset["Hsp_Artikel"]:
                    self.text_Hsp.SetBackgroundColour(self.preseteditcolor)
                elif sur == self.data.get_value("Handelsspanne"):
                    self.text_Hsp.SetBackgroundColour(self.editcolor)
                else:
                    self.text_Hsp.SetBackgroundColour(self.changecolor)
  ## population routine for comboboxes
    # overwritten from AfpDialog
    def Pop_combo(self):
        hnr = self.data.get_value("HersNr")
        if hnr:
            ind = self.hers_idents.index(hnr)
            if ind:
                self.combo_Hers.SetValue(self.hers_liste[ind])
        if self.fix_hersteller:
             self.combo_Hers.SetBackgroundColour(self.readonlycolor)
   ## population routine for special values
    # overwritten from AfpDialog
    def Pop_intristic(self):
        if not self.hersteller:
            self.hersteller = AfpManufact(self.data.get_globals(), self.data.get_value("HersNr"))
        disc = self.text_Rabatt.GetValue()
        sur = self.text_Hsp.GetValue()
        #print("AfpDialog_FaArticle.Pop_intristic start:", disc, sur)
        if not disc or not Afp_isEps(Afp_fromString(disc)):
            prsg = self.text_PrsGrp.GetValue()
            disc = self.hersteller.get_discount(prsg)
            self.text_Rabatt.SetValue(Afp_toString(disc))
            self.text_Rabatt.SetBackgroundColour(self.preseteditcolor)
            if not "Rabatt_Artikel" in self.presetedit: self.presetedit.append("Rabatt_Artikel")
            if not "Rabatt_Artikel" in self.preset: self.preset["Rabatt_Artikel"] = Afp_toString(disc)
        if not sur or not Afp_isEps(Afp_fromString(sur)):
            prsg = self.text_PrsGrp.GetValue()
            lstp = Afp_fromString(self.text_Liste.GetValue())
            sur = self.hersteller.get_surcharge(prsg, lstp)
            self.text_Hsp.SetValue(Afp_toString(sur))
            self.text_Hsp.SetBackgroundColour(self.preseteditcolor)
            if not "Hsp_Artikel" in self.presetedit: self.presetedit.append("Hsp_Artikel")
            if not "Hsp_Artikel" in self.preset: self.preset["Hsp_Artikel"] = Afp_toString(sur)
        #print("AfpDialog_FaArticle.Pop_intristic end:", disc, sur, self.presetedit)
    ## dis- or enable editing of dialog widgets - overwritten from AfpDialog
    # @param ed_flag - flag to turn editing on or off
    # @param lock_data - flag if invoking of dialog needs a lock on the database
    def Set_Editable(self, ed_flag, lock_data = None):
        if lock_data is None: lock_data = self.lock_data
        #print("AfpDialog_FaArticle.Set_Editable:", self.presetedit)
        for entry in self.textmap:
            TextBox = self.FindWindowByName(entry)
            if entry in self.readonly: continue
            TextBox.SetEditable(ed_flag)
            if ed_flag:
                if entry in self.presetedit:
                    TextBox.SetBackgroundColour(self.preseteditcolor)
                else:
                    TextBox.SetBackgroundColour(self.editcolor)
            else: TextBox.SetBackgroundColour(self.readonlycolor)    
        if not self.fix_hersteller:
            self.combo_Hers.Enable(ed_flag)
            if ed_flag: self.combo_Hers.SetBackgroundColour(self.editcolor)
            else: self.combo_Hers.SetBackgroundColour(self.readonlycolor)    
        if ed_flag:
            if self.wx_edit_choice and self.choice_Edit.GetCurrentSelection() != 1: 
                self.choice_Edit.SetSelection(1)
        else:
            self.changelist = []
        if lock_data:
            if ed_flag:
                if not self.new: self.data.lock_data()
            else: 
                if not self.new: self.data.unlock_data()

    ## execution in case the OK button ist hit - overwritten from AfpDialog
    def execute_Ok(self):
        self.store_data()

   ## read values from dialog and invoke writing into database         
    def store_data(self):
        self.Ok = False
        data = {}
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        if data and (len(data) > 2 or not self.new):
            if self.new: data = self.complete_data(data)
            self.data.set_data_values(data)
            self.data.store()
            self.Ok = True
        self.changed_text = []   
        
    ## initialise new empty data with all necessary values \n
    # or the other way round, complete new data entries with all needed input
    # @param data - data to be completed
    def complete_data(self, data):
        return data
   # Event Handlers 
     ## common Eventhandler TEXTBOX - when leaving the textboxes - overwritten from AfpDialog
    # @param event - event which initiated this action
    def On_KillFocus(self,event):
        name = event.GetEventObject().GetName()
        AfpDialog.On_KillFocus(self, event)
        TextBox = self.FindWindowByName(name)
        #print("AfpDialog_FaArticle.On_KillFocus:", name, name in self.textmap,  name in self.preset, TextBox.GetValue(), self.data.get_string_value(self.textmap[name]), TextBox.GetValue() == self.data.get_string_value(self.textmap[name]))
        if name in self.textmap:
            if name in self.preset:
                if TextBox.GetValue() == self.preset[name]:
                    TextBox.SetBackgroundColour(self.preseteditcolor)
                    return
            val = self.data.get_value(self.textmap[name])
            breakpoint()
            if (Afp_isNumeric(val) and not Afp_isEps(Afp_fromString(TextBox.GetValue()) - val)) or (TextBox.GetValue() == Afp_toString(val)):
                TextBox.SetBackgroundColour(self.editcolor)
                return
        TextBox.SetBackgroundColour(self.changecolor)
    ##  Eventhandler killfocus of possiby presetted textboxes\n
    # @param event - event which initiated this action   
    def On_handlePricing(self,event):
        if self.debug: print("AfpDialog_FaArticle Event handler `On_PresetEdit'")
        name = event.GetEventObject().GetName()
        self.reset_prices(name)
        if name in self.preset:
            for i in range(len(self.presetedit)):
                if self.presetedit[i] == name:
                    self.presetedit.pop(i)
                    break
            #print("AfpDialog_FaArticle.On_handlePricing:", name, self.presetedit)
        self.Pop_intristic()
        self.On_KillFocus(event)
    ##  Eventhandler ComboBox  select manufacurer\n
    # @param event - event which initiated this action   
    def On_Hersteller(self,event):
        if self.debug: print("AfpDialog_FaArticle Event handler `On_Hersteller'")
        if self.fix_hersteller:
            self.Pop_combo()
        else:
            print("AfpDialog_FaArticle.On_Hersteller not yet implemented")
    ##  Eventhandler BUTTON  create new article entry\n
    # @param event - event which initiated this action   
    def On_Neu(self,event):
        if self.debug: print("AfpDialog_FaArticle Event handler `On_Neu'")
        print("AfpDialog_FaArticle.On_Neu not yet implemented")
    ##  Eventhandler BUTTON  create new article entry\n
    # @param event - event which initiated this action   
    def On_Ablage(self,event):
        if self.debug: print("AfpDialog_FaArticle Event handler `On_Ablage'")
        print("AfpDialog_FaArticle.On_Ablage' not yet implemented")

## loader routine for dialog for editing articles, returns Ok flag 
# @param article - AfpArtikel SelectionList to be edited
# @param fix_manu - flag if manufacturer is fix in dialog
def AfpLoad_FaArticle(article, fix_manu = False):
    hersteller, idents = AfpFaktura_listManufacturer(article.get_globals(), True, article.is_debug())
    EditArticle = AfpDialog_FaArticle(hersteller, idents)
    EditArticle.attach_data(article, True)
    if fix_manu: EditArticle.set_fix_manufacturer()
    res = EditArticle.ShowModal()
    if res == wx.ID_OK:
        Ok = True
    else:
        Ok = False
    EditArticle.Destroy()
    return Ok
## dialog to maintain manufacturers
class AfpDialog_FaManufact(AfpDialog):
    def __init__(self):
        AfpDialog.__init__(self,None, -1, "")
        self.changed = False
        self.preseteditcolor = (245,245,220)
        self.changecolor = (220, 192, 192)
        self.SetTitle("Hersteller")

    ## set up dialog widgets - overwritten from AfpDialog
    def InitWx(self):
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.label_Kennung = wx.StaticText(self, -1, label="Kennung:", name="LKennung")
        self.label_Name = wx.StaticText(self, -1, label="Hersteller:", name="LHersName")
        self.text_Kennung = wx.TextCtrl(self, -1, value="", style=0, name="Kennung_ArtHers")
        self.textmap["Kennung_ArtHers"] = "Kennung.ARTHERS"
        self.text_Kennung.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.text_Name = wx.TextCtrl(self, -1, value="", style=0, name="Hersteller_ArtHers")
        self.textmap["Hersteller_ArtHers"] = "Hersteller.ARTHERS"
        self.text_Name.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.line1a_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line1a_sizer.Add(self.label_Kennung,0,wx.EXPAND)
        self.line1a_sizer.Add(self.text_Kennung,0,wx.EXPAND)
        self.line1b_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line1b_sizer.Add(self.label_Name,0,wx.EXPAND)
        self.line1b_sizer.Add(self.text_Name,0,wx.EXPAND)
        self.line1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.line1_sizer.AddSpacer(10)
        self.line1_sizer.Add(self.line1a_sizer,2,wx.EXPAND)
        self.line1_sizer.AddSpacer(10)
        self.line1_sizer.Add(self.line1b_sizer,2,wx.EXPAND)
        self.line1_sizer.AddSpacer(10)

        self.label_AdName = wx.StaticText(self, -1, label="", name="LAdName")
        self.labelmap["LAdName"] = "Name.ADRESSE"
        self.label_AdVorname = wx.StaticText(self, -1, label="", name="LAdVorname")
        self.labelmap["LAdVorname"] = "Vorname.ADRESSE"
        self.label_AdOrt = wx.StaticText(self, -1, label="", name="LAdOrt")
        self.labelmap["LAdOrt"] = "Ort.ADRESSE"
        self.line2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.line2_sizer.AddSpacer(10)
        self.line2_sizer.Add(self.label_AdName,2,wx.EXPAND)
        self.line2_sizer.AddSpacer(10)
        self.line2_sizer.Add(self.label_AdVorname,1,wx.EXPAND)
        self.line2_sizer.AddSpacer(10)
        self.line2_sizer.Add(self.label_AdOrt,2,wx.EXPAND)
        self.line2_sizer.AddSpacer(10)

        self.label_Rabatt = wx.StaticText(self, -1, label="Einkaufsrabatte:", name="LRabatt")
        self.liste_Einkauf = wx.ListBox(self, -1, name="Liste_Einkauf")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick, self.liste_Einkauf)
        self.listmap.append("Liste_Einkauf")
        #self.keepeditable.append("Liste_Einkauf")       
        self.line3a_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line3a_sizer.Add(self.label_Rabatt,0,wx.EXPAND)
        self.line3a_sizer.Add(self.liste_Einkauf,1,wx.EXPAND)
        self.line3_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.line3_sizer.AddSpacer(10)
        self.line3_sizer.Add(self.line3a_sizer,1,wx.EXPAND)
        self.line3_sizer.AddSpacer(10)
        
        self.label_Hsp = wx.StaticText(self, -1, label="Verkaufsaufschläge:", name="LHsp")
        self.liste_Verkauf = wx.ListBox(self, -1, name="Liste_Verkauf")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick, self.liste_Verkauf)
        self.listmap.append("Liste_Verkauf")
        #self.keepeditable.append("Liste_Einkauf")       
        self.line4a_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line4a_sizer.Add(self.label_Hsp,0,wx.EXPAND)
        self.line4a_sizer.Add(self.liste_Verkauf,1,wx.EXPAND)
        self.line4_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.line4_sizer.AddSpacer(10)
        self.line4_sizer.Add(self.line4a_sizer,1,wx.EXPAND)
        self.line4_sizer.AddSpacer(10)
 
        self.label_Datei = wx.StaticText(self, -1, label="Importdatei:", name="LDatei")
        self.text_Datei = wx.TextCtrl(self, -1, value="", style=0, name="Datei_ArtHers")
        self.textmap["Datei_ArtHers"] = "Datei.ARTHERS"
        self.label_ImpDatum = wx.StaticText(self, -1, label="Letzter Import:", name="LLImpDatum")
        self.label_Datum = wx.StaticText(self, -1, name="LDatum_ArtHers")
        self.labelmap["LDatum_ArtHers"] = "Import.ARTHERS"
        
        self.line5a_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line5a_sizer.Add(self.label_Datei,0,wx.EXPAND)
        self.line5a_sizer.Add(self.text_Datei,0,wx.EXPAND)
        self.line5b_sizer = wx.BoxSizer(wx.VERTICAL)
        self.line5b_sizer.Add(self.label_ImpDatum,0,wx.EXPAND)
        self.line5b_sizer.Add(self.label_Datum,0,wx.EXPAND)
        self.line5_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.line5_sizer.AddSpacer(10)
        self.line5_sizer.Add(self.line5a_sizer,1,wx.EXPAND)
        self.line5_sizer.AddSpacer(10)
        self.line5_sizer.Add(self.line5b_sizer,1,wx.EXPAND)
        self.line5_sizer.AddSpacer(10)
        
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.line1_sizer,0,wx.EXPAND)
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.line2_sizer,0,wx.EXPAND)
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.line5_sizer,0,wx.EXPAND)
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.line3_sizer,1,wx.EXPAND)
        self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.line4_sizer,1,wx.EXPAND)
        self.left_sizer.AddSpacer(10)

        self.button_Neu = wx.Button(self, -1, label="&Neu", name="Neu_FaManu")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)
        self.button_Adresse = wx.Button(self, -1, label="&Adresse", name="Ad_FaManu")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse, self.button_Adresse)
        self.check_Import = wx.CheckBox(self, -1, label="Import", name="CImport")
        self.check_Update = wx.CheckBox(self, -1, label="Update", name="CUpdate")
        self.button_sizer = wx.BoxSizer(wx.VERTICAL)
        self.button_sizer.AddSpacer(30)
        self.button_sizer.Add(self.button_Neu,0,wx.EXPAND)
        self.button_sizer.AddSpacer(10)
        self.button_sizer.Add(self.button_Adresse,0,wx.EXPAND)
        self.button_sizer.AddStretchSpacer(1)
        self.button_sizer.Add(self.check_Import,0,wx.EXPAND)
        self.button_sizer.Add(self.check_Update,0,wx.EXPAND)
        self.setWx(self.button_sizer, [1, 0, 0], [0, 0, 0]) # set Edit and Ok widgets
        self.button_sizer.AddSpacer(10)
        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.left_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.button_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)   
        self.SetSizerAndFit(self.sizer)

    # population routines
    ## populate discount list
    def Pop_Liste_Einkauf(self):
        #print ("AfpDialog_FaManufact.Pop_Liste_Einkauf not implemented yet!")
        self.populate_list(self.liste_Einkauf, "ARTDIS")
    ## populate surcharge list
    def Pop_Liste_Verkauf(self):
        #print ("AfpDialog_FaManufact.Pop_Liste_Verkauf not implemented yet!")
        self.populate_list(self.liste_Verkauf, "ARTSUR")
    
    ## populate lists with discount or surcharge data
    # @param lst - dialog list object to be poulated
    # @param sel - name of selection holding the data for population 
    def populate_list(self, lst, sel):
        self.data.sort_price_addons(sel)
        data = self.data.get_value_rows(sel)
        liste = ["--- neuen Eintrag anfügen ---"]
        for i in range(self.data.get_value_length(sel)):
            if sel =="ARTDIS":
                row = self.data.get_value_rows(sel, "PreisGrp,Rabatt", i)[0]
            else:
                row = self.data.get_value_rows(sel, "PreisGrp,Handelsspanne,Value", i)[0]
            print ("AfpDialog_FaManufact.populate_list row:", row)
            if row[0]:
                if len(row) > 2 and not row[2] is None:
                    line = Afp_toIntString(int(row[1]), 2) +  "% für die Preisgruppe " + row[0] + " bei" + Afp_toString(row[2])
                else:
                    line = Afp_toIntString(int(row[1]), 2) +  "% für die Preisgruppe " + row[0]
            else:
                if len(row) > 2 and not row[2] is None:
                    line = Afp_toIntString(int(row[1]), 2)  + "% für den Hersteller bei"  + Afp_toString(row[2])
                else:
                    line = Afp_toIntString(int(row[1]), 2)  + "% für den Hersteller insgesamt"
            liste.append(line)
        lst.Clear()
        lst.InsertItems(liste, 0)
    
    ## retrievs manufacturere data
    def get_manu(self):
        if self.Ok:
            return self.data
        return None
    ## execution in case the OK button ist hit - overwritten from AfpDialog
    def execute_Ok(self):
        if self.new:
            if not "Kennung_ArtHers" in self.changed_text or not "Hersteller_ArtHers" in self.changed_text:
                AfpReq_Info("Die Felder 'Kennung' und 'Hersteller' müssen ausgefüllt werden.","Bitte Eintragung nachholen!")
                self.close_dialog = False
                return
        fname = None
        imp = self.check_Import.IsChecked()
        upd = self.check_Update.IsChecked()
        if imp:
            fname = self.get_importfile()
        self.store_data()
        if imp and fname:
            self.import_articles(fname)
        if upd:
            self.update_articles()
        self.close_dialog = True
   ## read values from dialog and invoke writing into database         
    def store_data(self):
        self.Ok = False
        data = {}
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        if data:
            self.data.set_data_values(data)
            self.changed = True
        if self.changed:
            self.data.store()
            self.Ok = True
        self.changed = False
        self.changed_text = []   
    ## get filename for article import
    def get_importfile(self):
        fname = self.data.get_value("Datei")
        hers = self.data.get_value("Hersteller")
        dir = self.data.get_globals().get_value("homedir")
        filename, ok = AfpReq_FileName(dir, "Artikelimport " + hers, fname + "*.csv") 
        print ("AfpDialog_FaManufact.get_importfile:", filename, ok)
        if ok:
            idat = Afp_dateString(filename)
            if idat:
                self.data.set_value("Import", idat)
                self.changed = True
        else:
            filename = None
        return filename
    ## import manufacturer articles
    # @ param fname - name of file to be imported
    def import_articles(self, fname):
        res = AfpFaktura_importArtikels(globals, self.data, fname, True)
        if not res:
             AfpReq_Info("Keine Importdaten des Herstellers '" + self.data.get_value("Hersteller") + "' vorhanden.", "Import kann nicht durchgeführt werden!", "Warnung")

    ## update manufacturer articles in main article database
    def update_articles(self):
        print ("AfpDialog_FaManufact.update_articles not implemented yet!")
        return None
    # click events
    ## double click on discount list
    def On_DClick(self, event):
        hsp = event.GetEventObject().GetName() == "Liste_Verkauf"
        if hsp:
            table = "ARTSUR"
            cols = "PreisGrp,Handelsspanne,Value"
            text = "   Handelsspannen"
            header = "Verkauf Handelsspanne"
        else:
            table = "ARTDIS"
            cols = "PreisGrp,Rabatt"
            text = "   Rabatt"
            header = "Hersteller Rabatt"
        ind = event.GetInt() -1 
        print ("AfpDialog_FaManufact.On_DClick ind:", ind, table, cols)
        if ind < 0:
            if hsp: row = ["", 0, ""]
            else: row = ["", 0]
        else:
            row = self.data.get_value_rows(table, cols, ind)[0]
        print ("AfpDialog_FaManufact.On_DClick entry:", row)
        liste = [["Preisgruppe", Afp_toString(row[0])]]
        if hsp:
            liste.append(["Handelsspanne", Afp_toString(int(row[1]))])
            liste.append(["Wert", Afp_toString(row[2])])
        else:
            liste.append(["Rabatt", Afp_toString(int(row[1]))])
        res = AfpReq_MultiLine( text + "eingabe für den Hersteller '" + self.data.get_value("Hersteller.ARTHERS") + "'.","   Eingaben ohne Preisgruppe gelten für den gesamten Hersteller." , "Text", liste, header, 250, "")
        print ("AfpDialog_FaManufact.On_DClick res:", res, self.changed)
        if res:
            newdata = {}
            if res[0] != row[0]:
                newdata["PreisGrp"]  = res[0]
            if Afp_isEps(row[1] - Afp_numericString(res[1])):
                if hsp: newdata["Handelsspanne"] = Afp_numericString(res[1])
                else: newdata["Rabatt"] = Afp_numericString(res[1])
            if hsp and res[2] and (not row[2] or Afp_isEps(row[2] - Afp_numericString(res[2]))):
                newdata["Value"] = Afp_numericString(res[2])
            if newdata:   
                print ("AfpDialog_FaManufact.On_DClick new:",  newdata)
                self.data.set_data_values(newdata, table, ind)
                self.changed = True
        elif res is None and ind > -1:
            self.data.delete_row(table, ind)
            self.changed = True
        if hsp: self.Pop_Liste_Verkauf()
        else: self.Pop_Liste_Einkauf()
    # Button events
    ## create new manufacturer
    def On_Neu(self, event):
        if self.debug: print ("AfpDialog_FaManufact.On_Neu")
        data = AfpManufact(self.data.get_globals())
        #print ("AfpDialog_FaManufact.On_Neu data:", data) 
        self.attach_data( data, True, True)
    ## attach address to this manzfacturer
    def On_Adresse(self, event):
        if self.debug: print ("AfpDialog_FaManufact.On_Adresse")
        name = self.data.get_name(True)
        if not name: name = self.data.get_value("Hersteller")
        text = "Bitte Adresse für den Hersteller '" + self.data.get_value("Hersteller") + "' auswählen:"
        KNr = AfpLoad_AdAusw(self.data.get_globals(),"ADRESSE","NamSort",name, None, text)
        if KNr:
            self.data.set_value("KundenNr", KNr)
            self.data.delete_selection("ADRESSE")
            self.changed = True
            self.Populate()

## loader routine for dialog for editing and maintaining manufacturers, returns Ok flag 
# @param globals - global values including the mysql connection - this input is mandatory
# @param ident - identifier for manufacturer or manufact selectionlist, if not given an new manufacturer is created
# @param edit - flag, if dialog should be opened in edit mode
def AfpLoad_FaManufact(globals, ident, edit = False):
    new = ident is None
    if new: edit = True
    manunew = None
    if new or Afp_isInteger(ident):
        manu = AfpManufact(globals, ident)
    else:
        manu = ident
    EditManu = AfpDialog_FaManufact()
    EditManu.attach_data(manu, new, edit)
    res = EditManu.ShowModal()
    if res == wx.ID_OK:
        Ok = True
        if new: manunew = EditManu.get_manu()
    else:
        Ok = False
    EditManu.Destroy()
    return Ok, manunew
