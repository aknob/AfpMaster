#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFaktura.AfpFaScreen
# AfpFaScreen module provides the graphic screen to access all data of the Afp-'Faktura' modul 
# it holds the class
# - AfpFaScreen
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        22 Nov. 2016 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
#    Copyright (C) 1989 - 2025  afptech.de (Andreas Knoblauch)
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

from AfpBase.AfpUtilities.AfpStringUtilities import AfpSelectEnrich_dbname, Afp_ArraytoString, Afp_fromString, Afp_toString, Afp_isString, Afp_intString, Afp_floatString, Afp_addRootpath
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile, Afp_isNumeric, Afp_isInteger
from AfpBase.AfpDatabase.AfpSQL import AfpSQL
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase
from AfpBase.AfpBaseRoutines import AfpMailSender, Afp_archivName, Afp_startFile
from AfpBase.AfpBaseDialog import AfpReq_Info, AfpReq_Question, AfpReq_Text, AfpReq_EditText, AfpReq_MultiLine
from AfpBase.AfpBaseDialogCommon import  AfpReq_Information, Afp_editMail, AfpLoad_DiReport
from AfpBase.AfpBaseScreen import AfpEditScreen
from AfpBase.AfpBaseAdRoutines import AfpAdresse_StatusMap, AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_DiAdEin_fromKNr, AfpLoad_AdAusw, AfpAdresse_indirectAttributFromKNr
from AfpBase.AfpBaseFiDialog import AfpLoad_DiFiZahl

from AfpFaktura.AfpFaRoutines import AfpFa_FilterList, AfpInvoice, AfpOffer, AfpOrder, AfpFa_inFilterList, AfpFa_changeKind, AfpFa_possibleKinds, AfpFa_colonFloat, AfpFa_colonInt
from AfpFaktura.AfpFaDialog import AfpLoad_FaAusw, AfpLoad_FaCustomSelect, AfpLoad_FaLine, AfpLoad_FaArtikelAusw, AfpReq_FaSelectedRow

class AfpFaScreen_EditLinePlugIn(object):
    ## initialize AfpFaScreen_EditLinePlugIn class
    # @param grid - grid where row edit mode should be invoked - this input is mandatory
    # @param rowNr - index of row where row editing should happen
    # @param sb - AfpSuperbase to allow selection from different sorted tables, current data file and data index is used 
    # @param process - list of processes, the following entries per process are possible:
    # - ["choose", "value1, value2, ..."] - keyword "choose", values to be read from choosing-table
    # - ["set", "value1, value2, ..."] - keyword "set", values to be set to initial data row
    # - [integer,"postprocess-routinename","update desriptions, separated by ','"]
    # @param debug - flag for debug information
        def  __init__(self, grid, rowNr, sb, process, debug = False):
            self.grid = grid
            self.row = rowNr
            if self.row is None:
                self.row = grid.GetNumberRows() - 1
            self.cols = grid.GetNumberCols()
            self.sb = sb
            self.process = process
            self.debug = debug
            self.process_step_index = -1
            self.selectlinecolor = grid.GetCellBackgroundColour(self.row, 0)
            self.editcolcolor = (192, 252, 192)
            self.editlinecolor = (192, 220, 192)
            
            self.initial_row = None
            self.edit_col = None
            self.edit_value = ""
            self.choose = None
            self.postprocess = None
            self.update = None
            self.columns = None
            self.select_row()
            if self.debug: print("AfpFaScreen_EditLinePlugIn Konstruktor")
            self.next_process_step()
            self.initial_row = self.read_columns()
        ## destructor
        def __del__(self):    
            if self.debug: 
                print("AfpFaScreen_EditLinePlugIn Destruktor")
                #traceback.print_stack()

        ## mark indicates row for row edit mode
        # @param release - reset original color
        def select_row(self, release = False):
            attrSel = wx.grid.GridCellAttr()
            if release:
                attrSel.SetBackgroundColour(self.selectlinecolor)
            else:
                attrSel.SetBackgroundColour(self.editlinecolor)
            print("AfpFaScreen_EditLinePlugIn.select_row:", self.row, self.cols, attrSel)
            for col in range(0,self.cols):
                self.grid.SetAttr(self.row, col, attrSel)
                attrSel.IncRef()
        ## mark indicates row for row edit mode
        # @param release - reset original color
        def select_col(self, release = False):
            print("AfpFaScreen_EditLinePlugIn.select_col:", self.edit_col)
            if self.edit_col:
                attrSel = wx.grid.GridCellAttr()
                if release:
                    attrSel.SetBackgroundColour(self.editlinecolor)
                else:
                    attrSel.SetBackgroundColour(self.editcolcolor)
                print("AfpFaScreen_EditLinePlugIn.select_col:", self.row, self.edit_col, attrSel)
                self.grid.SetAttr(self.row, self.edit_col, attrSel)
        ## handle keydown events, supplied from AfpEditScreen
        # @param event - that initiated this catch
        def catch_keydown(self, event):
            keycode = event.GetKeyCode()
            caught = False
            if self.edit_col is None:
                if  keycode == wx.WXK_RETURN:
                    done = self.next_process_step()
                    if not done: caught = True
                elif  keycode == wx.WXK_ESCAPE:
                    self.clear_process_step()
                    #caught = True
                elif keycode == wx.WXK_LEFT:
                    self.select_previous_row_data()
                    caught = True
                elif keycode == wx.WXK_RIGHT: 
                    self.select_following_row_data()
                    caught = True
                print("AfpFaScreen_EditLinePlugIn.catch_keydown:", keycode, caught)
            else:
                if keycode != wx.WXK_SHIFT:
                    if  keycode == wx.WXK_RETURN:
                        done = self.next_process_step()
                        if not done: caught = True
                    elif keycode == wx.WXK_BACK:
                        if self.edit_value:
                            self.edit_value = self.edit_value[:-1]
                            self.grid.SetCellValue(self.row, self.edit_col, self.edit_value.encode("UTF-8"))
                    else:
                        upcase = event.ShiftDown()
                        char = self.get_char(keycode, upcase)
                        print("AfpFaScreen_EditLinePlugIn.catch_keydown Edit:", keycode, upcase, char)
                        self.edit_value += char
                        self.grid.SetCellValue(self.row, self.edit_col, self.edit_value.encode("UTF-8"))
            if self.debug: print("AfpFaScreen_EditLinePlugIn.catch_keydown:", keycode, caught)
            return caught
        ## get char from keycode and shift flag
        # @param keycode - code of pushed key
        # @param shift - flag if shift key has been pushed meanwhile
        def get_char(self, keycode, shift):
            if keycode == wx.WXK_NUMPAD0:
                char = "0"
            elif keycode == wx.WXK_NUMPAD1:
                char = "1"
            elif keycode == wx.WXK_NUMPAD2:
                char = "2"
            elif keycode == wx.WXK_NUMPAD3:
                char = "3"
            elif keycode == wx.WXK_NUMPAD4:
                char = "4"
            elif keycode == wx.WXK_NUMPAD5:
                char = "5"
            elif keycode == wx.WXK_NUMPAD6:
                char = "6"
            elif keycode == wx.WXK_NUMPAD7:
                char = "7"
            elif keycode == wx.WXK_NUMPAD8:
                char = "8"
            elif keycode == wx.WXK_NUMPAD9:
                char = "9"
            elif keycode == wx.WXK_DECIMAL:
                char = "."
            elif keycode == wx.WXK_SEPARATOR:
                char = "."
            else:
                char = chr(keycode).lower()
            #ch = chr(keycode)
            #key = str(keycode)
            if shift:
                char = char.upper()
            return char
        ## clear process step data for row editing
        def clear_process_step(self):
            self.choose = False
            self.columns = None
            self.edit_col = None
            self.edit_value = ""
            self.postprocess = None
            self.update = None
            self.process_step_index = None
            self.initial_row = None
        ## complete actuel step and invoke the next process step for row editing
        def next_process_step(self):
            #print "AfpFaScreen_EditLinePlugIn.next_process_step last index:", self.process_step_index
            done = False
            # postprocess last step
            if self.process_step_index is None:
                self.process_step_index = -1
            elif self.process_step_index >= 0:
                #print "AfpFaScreen_EditLinePlugIn.next_process_step post:", self.postprocess, self.edit_value, self.update
                if self.postprocess and self.edit_value:
                    pyBefehl = "value = " + self.postprocess + "(\"" + self.edit_value + "\")"
                    funct = {"Afp_intString": Afp_intString, "Afp_floatString": Afp_floatString, "AfpFa_colonFloat": AfpFa_colonFloat,  "AfpFa_colonInt": AfpFa_colonInt}
                    local = locals()
                    #print ("AfpFaScreen_EditLinePlugIn.next_process_step post exe:", pyBefehl, funct, local)
                    exec(pyBefehl, funct, local)
                    value = local["value"]
                    string = Afp_toString(value)
                    self.set_initial_row([self.edit_col, string])
                    #self.initial_row[self.edit_col] = string
                    self.grid.SetCellValue(self.row, self.edit_col, string)
                    if self.update:
                        updates = self.update.split(",")
                        for update in updates:
                            ups = update.split()
                            pyBefehl = ""
                            ucol = None
                            for up in ups:
                                if "$" == up[0]:
                                    col = int(up[1:])
                                    if pyBefehl == "":
                                        ucol = col
                                        pyBefehl = "value"
                                    else:
                                        #print "AfpFaScreen_EditLinePlugIn.next_process_step update col:", self.initial_row, col
                                        pyBefehl += " " + self.initial_row[col]
                                else:
                                    pyBefehl += " " + up
                            #print ("AfpFaScreen_EditLinePlugIn.next_process_step update exe:", pyBefehl)
                            exec(pyBefehl, {}, local) 
                            value = local["value"]
                            #print ("AfpFaScreen_EditLinePlugIn.next_process_step update res:", value, ucol)
                            if not ucol is None:
                                self.set_initial_row([ucol, Afp_toString(value)])
                                #self.initial_row[ucol] = Afp_toString(value)
                                if ucol < self.cols:
                                    self.grid.SetCellValue(self.row, ucol, self.initial_row[ucol])
                if not self.edit_col is None:
                    self.select_col(True)
            loop = True
            while loop:
                loop = False
                # clear variables
                self.choose = False
                self.columns = None
                self.edit_col = None
                self.edit_value = ""
                self.postprocess = None
                self.update = None
                # invoke next step
                self.process_step_index += 1
                print("AfpFaScreen_EditLinePlugIn.next_process_step cleard next:",  self.process_step_index, len(self.process))
                if self.process_step_index < len(self.process):
                    process = self.process[self.process_step_index]
                    print("AfpFaScreen_EditLinePlugIn.next_process:", process)
                    if process[0] == "choose":
                    # process = ["choose",",ArtikelNr,Bezeichnung,,Nettopreis,Nettopreis"]
                        self.choose = True
                        self.columns = process[1].split(",")
                    elif process[0] == "set":
                        self.set_initial_row(process[1])
                        self.display_row()
                        loop = True
                    elif type(process[0]) == int:
                    # process = [3,"Afp_intString","$5 = $5 * $3"]
                        self.edit_col = process[0]
                        if len(process) > 1:
                            self.postprocess = process[1]
                            if len(process) > 2:
                                self.update = process[2]
                        self.select_col()
                        if self.initial_row and self.initial_row[self.edit_col]:
                            self.edit_value = self.initial_row[self.edit_col]
                    #print "AfpFaScreen_EditLinePlugIn.next_process_step executed:", self.choose, self.columns, self.edit_col, self.postprocess, self.update
                else:
                    print("AfpFaScreen_EditLinePlugIn.next_process_step: ENDED")
                    done = True
            self.grid.Refresh()
            return done
        ## display row entries in selected grid row
        # @param row - if given, list of row entries to be displayed, otherwise initial row is displayed
        def display_row(self, row = None):
            if row is None:
                row = self.initial_row
            if row:
                for col in range(self.cols):
                    value = row[col]
                    if value is None: value = ""
                    self.grid.SetCellValue(self.row, col, value)
                self.grid.Refresh()
       ## select data for gridrow due to the 'left arrow' key
        def select_previous_row_data(self):
            if self.choose:
                self.get_previous_row_data()
                self.display_row()
       ## select data for gridrow due to the 'right arrow' key
        def select_following_row_data(self):
            if self.choose:
                self.get_following_row_data()
                self.display_row()
        ## routine to set the initial row data manually
        def set_initial_row(self, row):
            if Afp_isString(row):
                self.initial_row = row.split(",")
            else:
                ind = row[0]
                if self.initial_row is None:
                    lgh = self.cols
                    if ind >= lgh: lgh = ind + 1
                    self.initial_row = [None]*lgh
                lgh = len(self.initial_row)
                if lgh <= ind:
                    for i in range(lgh,ind+1):
                        self.initial_row.append(None)
                self.initial_row[ind] = row[1]
            #print "AfpFaScreen_EditLinePlugIn.set_initial_row:", self. initial_row
          ## routine to retrieve the result of row editing
        def get_row_edit_result(self):
            return self.initial_row
            #row = []
            #for col in range(self.cols):
               # row.append(self.grid.GetCellValue(self.row, col))
            #return row
        ## read values from database (superbase style)
        def read_columns(self):
            # ToDo: daten aus grid laden, wenn row == None
            row = self.initial_row
            if self.columns:
                row = []
                for col in self.columns:
                    if col:
                        value = self.sb.get_string_value(col)
                    else:
                        value = ""
                    row.append(value)
            return row
            
        ## get data for gridrow due to the 'left arrow' key
        # to be overwritten in devired class
        def get_previous_row_data(self):
            print("AfpFaScreen_EditLinePlugIn.get_previous_row")
            self.sb.select_previous()
            self.initial_row = self.read_columns()
            return self.initial_row 
        ## get data for gridrow due to the 'right arrow' key
        # to be overwritten in devired class
        def get_following_row_data(self):
            print("AfpFaScreen_EditLinePlugIn.get_following_row")
            self.sb.select_next()
            self.initial_row  = self.read_columns()
            return self.initial_row 
        ## process row edit result
        # to be overwritten in devired class
        def process_row_edit_result(self):
            print("AfpFaScreen_EditLinePlugIn.process_row_edit_result")
            return

## Class Faktura shows Window for Invoices and handles interactions
class AfpFaScreen(AfpEditScreen):
    ## initialize AfpAdScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None, use_labels = True):
        AfpEditScreen.__init__(self)
        self.typ = "Faktura"
        self.direct_sale_name = "Barverkauf"
        self.sb_master = "RECHNG"
        self.sb_filter = ""
        self.use_labels = use_labels
        self.use_RETURN = False
        self.use_custom_selection = False
        self.custom_index = None
        self.automated_selection = False
        self.first_content_change = None
        self.grid_rows["Content"] = 10 
        self.grid_cols["Content"] = 6
        self.grid_row_selected = False
        self.grid_col_labels =[["Datum", "Beleg", "Soll", "Haben", "Betrag", "Bezeichnung", "Name"], ["Datum", "Nr", "Pos", "Konto", "Betrag", "Bezeichnung", "Name"], ["Datum", "Nr", "Ext", "Konto", "Betrag", "Bezeichnung", "Name"]]
        self.dynamic_grid_name = "Bookings"
        self.dynamic_grid_col_percents = [12, 8, 10, 10, 10, 30, 20]
        self.dynamic_grid_col_labels = self.grid_col_labels[0]

        self.content_colname = ["Pos","ErsatzteilNr","Bezeichnung","Anzahl","Einzel","Gesamt"]
        self.selected_row = None
        self.index = None
        self.index_nr = None
        self.edit_typ = None
        self.active = False
        self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
        # self properties
        self.SetTitle("Afp-Fakturierung und Warenwirtschaft")
        #self.readonlycolor = (239, 235, 222)
        #self.readonlycolor = (212, 212, 212)
        self.changecolor = (220, 192, 192)
        self.SetSize((800, 600))
        #self.SetBackgroundColour(self.readonlycolor)
        self.SetForegroundColour(wx.Colour(20, 19, 18))
        self.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "DejaVu Sans"))
        self.InitWx()

    ## initialize widgets
    def InitWx(self):
        self.InitWx_static()
        
    ## initialize static widgets on panel
    def InitWx_static(self):
        panel = self.panel
      
        # BUTTON
        self.button_Auswahl = wx.Button(panel, -1, label="Aus&wahl", pos=(692,50), size=(77,50), name="BAuswahl")
        self.Bind(wx.EVT_BUTTON, self.On_Faktura_Ausw, self.button_Auswahl)
        self.button_Adresse = wx.Button(panel, -1, label="&Adresse", pos=(692,110), size=(77,50), name="BAdresse")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse, self.button_Adresse)
        self.button_Bar = wx.Button(panel, -1, label="B&ar", pos=(692,170), size=(77,25), name="BBar")
        self.Bind(wx.EVT_BUTTON, self.On_Bar, self.button_Bar)
        self.button_Neu = wx.Button(panel, -1, label="&Neu", pos=(692,195), size=(77,25), name="BNeu")
        self.Bind(wx.EVT_BUTTON, self.On_Neu, self.button_Neu)
      
        self.button_Dokument = wx.Button(panel, -1, label="&Dokument", pos=(692,256), size=(77,50), name="BDokument")
        self.Bind(wx.EVT_BUTTON, self.On_Dokument, self.button_Dokument)
        self.button_Zahlung = wx.Button(panel, -1, label="&Zahlung", pos=(692,338), size=(77,50), name="BZahlung")
        self.Bind(wx.EVT_BUTTON, self.On_Zahlung, self.button_Zahlung)
        self.button_Edit = wx.Button(panel, -1, label="&Bearbeiten", pos=(692,405), size=(77,50), name="Edit")
        self.Bind(wx.EVT_BUTTON, self.On_Edit, self.button_Edit)
        self.button_Ende = wx.Button(panel, -1, label="Be&enden", pos=(692,470), size=(77,50), name="Ende")
        self.Bind(wx.EVT_BUTTON, self.On_Ende, self.button_Ende)

        # COMBOBOX
        self.combo_Filter = wx.ComboBox(panel, -1, value="Rechnung", pos=(526,16), size=(150,20), choices=AfpFa_FilterList(), style=wx.CB_READONLY, name="Filter_Zustand")
        self.Bind(wx.EVT_COMBOBOX, self.On_Filter, self.combo_Filter)
        self.combo_Filter.SetSelection(AfpFa_inFilterList("Rechnung"))
        #self.filtermap = {"Alle":"","Kostenvoranschläge":"KVA","Angebote":"Angebot","Aufträge":"Auftrag","Rechnungen":"Rechnung","Mahnungen":"Mahnung","Stornierungen":"Storno %"}
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
        
        self.label_ZahlDat = wx.StaticText(panel, -1, label="Datum:", pos=(290,475), size=(50,18), name="LZahlDat")
        self.label_Zahlung = wx.StaticText(panel, -1, label="Zahlung:", pos=(290,495), size=(50,18), name="LZahlung")
        self.label_Mwst = wx.StaticText(panel, -1, label="Mwst:", pos=(425,475), size=(45,18), name="LMwst")
        self.label_Brutto = wx.StaticText(panel, -1, label="Brutto:", pos=(425,495), size=(47,18), name="LBrutto")
        self.label_Netto = wx.StaticText(panel, -1, label="Summe:", pos=(550,475), size=(45,18), name="LNetto")
        self.label_Betrag = wx.StaticText(panel, -1, label="Betrag:", pos=(550,495), size=(45,18), name="LBetrag")
       
        # address as LABEL
        if self.use_labels:
            self.label_Vorname = wx.StaticText(panel, -1, "", pos=(35,50), size=(200,23), name="Vorname")
            self.labelmap["Vorname"] = "Vorname.ADRESSE"
            self.label_Name = wx.StaticText(panel, -1,label="", pos=(35,75), size=(200,23), name="Name")
            self.labelmap["Name"] = "Name.ADRESSE"
            
            self.label_Strasse = wx.StaticText(panel, -1,label="", pos=(35,100), size=(200,23), name="Strasse")
            self.labelmap["Strasse"] = "Strasse.ADRESSE"
            
            self.label_Plz = wx.StaticText(panel, -1,label="", pos=(35,125), size=(40,23), name="Plz")
            self.labelmap["Plz"] = "Plz.ADRESSE"
            self.label_Ort = wx.StaticText(panel, -1,label="", pos=(75,125), size=(160,23), name="Ort")
            self.labelmap["Ort"] = "Ort.ADRESSE"
            
            self.label_Telefon = wx.StaticText(panel, -1,label="", pos=(88,150), size=(147,23), name="Telefon")
            self.labelmap["Telefon"] = "Telefon.ADRESSE"
            self.label_Mail = wx.StaticText(panel, -1,label="", pos=(88,175), size=(147,23), style=0, name="Mail")
            self.labelmap["Mail"] = "Mail.ADRESSE"
            
            self.label_Att = wx.StaticText(panel, -1, label="", pos=(240,100), size=(80,18), name="Att")               
            self.labelmap["Att"] = "Attribut.ADRESATT"
            self.label_AttT = wx.StaticText(panel, -1, label="", pos=(320,100), size=(175,18), name="AttT")               
            self.labelmap["AttT"] = "AttText.ADRESATT"
            self.label_Tag1 = wx.StaticText(panel, -1, label="", pos=(240,125), size=(80,18), name="Tag1")               
            self.labelmap["Tag1"] = "Tag#1.ADRESATT"
            self.label_Tag2 = wx.StaticText(panel, -1, label="", pos=(320,125), size=(80,18), name="Tag2")               
            self.labelmap["Tag2"] = "Tag#2.ADRESATT"
            self.label_Tag3 = wx.StaticText(panel, -1, label="", pos=(400,125), size=(95,18), name="Tag3")               
            self.labelmap["Tag3"] = "Tag#3.ADRESATT"
            self.label_Tag4= wx.StaticText(panel, -1, label="", pos=(320,150), size=(175,18), name="Tag4")               
            self.labelmap["Tag4"] = "Tag#4.ADRESATT"
            self.label_Tag5 = wx.StaticText(panel, -1, label="", pos=(240,175), size=(80,18), name="Tag5")               
            self.labelmap["Tag5"] = "Tag#5.ADRESATT"
            self.label_Tag6 = wx.StaticText(panel, -1, label="", pos=(320,175), size=(80,18), name="Tag6")               
            self.labelmap["Tag6"] = "Tag#6.ADRESATT"
            self.label_Tag7 = wx.StaticText(panel, -1, label="", pos=(400,175), size=(95,18), name="Tag7")               
            self.labelmap["Tag7"] = "Tag#7.ADRESATT"
        else:
            # address as TEXTBOX
            self.text_Vorname = wx.TextCtrl(panel, -1, "", pos=(35,50), size=(200,23), style=wx.TE_READONLY, name="Vorname")
            self.textmap["Vorname"] = "Vorname.ADRESSE"
            self.text_Name = wx.TextCtrl(panel, -1,value="", pos=(35,75), size=(200,23), style=wx.TE_READONLY, name="Name")
            self.textmap["Name"] = "Name.ADRESSE"
            
            self.text_Strasse = wx.TextCtrl(panel, -1,value="", pos=(35,100), size=(200,23), style=wx.TE_READONLY, name="Strasse")
            self.textmap["Strasse"] = "Strasse.ADRESSE"
            
            self.text_Plz = wx.TextCtrl(panel, -1,value="", pos=(35,125), size=(53,23), style=wx.TE_READONLY, name="Plz")
            self.textmap["Plz"] = "Plz.ADRESSE"
            self.text_Ort = wx.TextCtrl(panel, -1,value="", pos=(88,125), size=(147,23), style=wx.TE_READONLY, name="Ort")
            self.textmap["Ort"] = "Ort.ADRESSE"
            
            self.text_Telefon = wx.TextCtrl(panel, -1,value="", pos=(88,150), size=(232,23), style=wx.TE_READONLY, name="Telefon")
            self.textmap["Telefon"] = "Telefon.ADRESSE"
            self.text_Mail = wx.TextCtrl(panel, -1,value="", pos=(88,175), size=(147,23), style=0, name="Mail")
            self.textmap["Mail"] = "Mail.ADRESSE"
            
            self.text_Att = wx.TextCtrl(panel, -1, value="", pos=(240,100), size=(80,23), style=wx.TE_READONLY, name="Att")               
            self.textmap["Att"] = "Attribut.ADRESATT"
            self.text_AttT = wx.TextCtrl(panel, -1, value="", pos=(320,100), size=(175,23), style=wx.TE_READONLY, name="AttT")               
            self.textmap["AttT"] = "AttText.ADRESATT"
            self.text_Tag1 = wx.TextCtrl(panel, -1, value="", pos=(240,125), size=(80,23), style=wx.TE_READONLY, name="Tag1")               
            self.textmap["Tag1"] = "Tag#1.ADRESATT"
            self.text_Tag2 = wx.TextCtrl(panel, -1, value="", pos=(320,125), size=(80,23), style=wx.TE_READONLY, name="Tag2")               
            self.textmap["Tag2"] = "Tag#2.ADRESATT"
            self.text_Tag3 = wx.TextCtrl(panel, -1, value="", pos=(400,125), size=(95,23), style=wx.TE_READONLY, name="Tag3")               
            self.textmap["Tag3"] = "Tag#3.ADRESATT"
            self.text_Tag4= wx.TextCtrl(panel, -1, value="", pos=(320,150), size=(175,23), style=wx.TE_READONLY, name="Tag4")               
            self.textmap["Tag4"] = "Tag#4.ADRESATT"
            self.text_Tag5 = wx.TextCtrl(panel, -1, value="", pos=(240,175), size=(80,23), style=wx.TE_READONLY, name="Tag5")               
            self.textmap["Tag5"] = "Tag#5.ADRESATT"
            self.text_Tag6 = wx.TextCtrl(panel, -1, value="", pos=(320,175), size=(80,23), style=wx.TE_READONLY, name="Tag6")               
            self.textmap["Tag6"] = "Tag#6.ADRESATT"
            self.text_Tag7 = wx.TextCtrl(panel, -1, value="", pos=(400,175), size=(95,23), style=wx.TE_READONLY, name="Tag7")               
            self.textmap["Tag7"] = "Tag#7.ADRESATT"
        
        # TEXTBOX
        self.text_Datum = wx.TextCtrl(panel, -1,value="", pos=(449,50), size=(77,23), style=wx.TE_READONLY, name="Datum")
        self.textmap["Datum"] = "Datum.Main"
        self.text_RechNr = wx.TextCtrl(panel, -1,value="", pos=(599,50), size=(77,23), style=wx.TE_READONLY, name="RechNr")
        self.textmap["RechNr"] = "RechNr.Main"
        
        self.text_ZahlDat = wx.TextCtrl(panel, -1,value="", pos=(335,475), size=(77,18), style=wx.TE_READONLY, name="ZahlDat")
        self.textmap["ZahlDat"] = "ZahlDat.Main"  
        self.text_Zahlung = wx.TextCtrl(panel, -1,value="", pos=(335,495), size=(77,18), style=wx.TE_READONLY, name="Zahlung")
        self.textmap["Zahlung"] = "Zahlung.Main"  
        self.text_Mwst = wx.TextCtrl(panel, -1,value="", pos=(470,475), size=(77,18), style=wx.TE_READONLY, name="Mwst")
        self.textmap["Mwst"] = "Mwst.Main"  
        self.text_Betrag = wx.TextCtrl(panel, -1,value="", pos=(470,495), size=(77,18), style=wx.TE_READONLY, name="Betrag")
        self.textmap["Betrag"] = "Betrag.Main"  
        self.text_Netto = wx.TextCtrl(panel, -1,value="", pos=(599,475), size=(77,18), style=wx.TE_READONLY, name="Netto")
        self.textmap["Netto"] = "Netto.Main"  
        self.text_ZahlBetrag = wx.TextCtrl(panel, -1,value="", pos=(599,495), size=(77,18), style=wx.TE_READONLY, name="ZahlBetrag")
        self.textmap["ZahlBetrag"] = "ZahlBetrag.Main"  

        #ListBox - Archiv
        self.list_archiv = wx.ListBox(panel, -1, pos=(500,100) , size=(176, 100), name="ListArchiv")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Archiv, self.list_archiv)
        self.listmap.append("ListArchiv")

        # OPTIONBUTTON
        self.choice_Status = wx.Choice(panel, -1, pos=(240,50), size=(76,25), choices=["Passiv", "Aktiv", "Neutral", "Markiert", "Inaktiv"],  name="RStatus")
        self.choice_Status.SetSelection(0)
        #self.choice_Status.Enable(False)
        self.Bind(wx.EVT_CHOICE, self.On_CStatus, self.choice_Status)
        self.choicemap = AfpAdresse_StatusMap()
        
        # GRID
        self.grid_content = self.grid_editable = wx.grid.Grid(panel, -1, pos=(23,206) , size=(653, 264), name="Content")
        self.grid_content.CreateGrid(self.grid_rows["Content"] , self.grid_cols["Content"] )
        self.grid_content.SetRowLabelSize(3)
        self.grid_content.SetColLabelSize(18)
        self.grid_content.EnableEditing(0)
        self.grid_content.EnableDragColSize(0)
        self.grid_content.EnableDragRowSize(0)
        self.grid_content.EnableDragGridSize(0)
        self.grid_content.SetSelectionMode(wx.grid.Grid.SelectRows)
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
        for row in range(0,self.grid_rows["Content"] ):
            for col in range(0,self.grid_cols["Content"] ):
                self.grid_content.SetReadOnly(row, col)
        self.gridmap.append("Content")
        self.grid_minrows["Content"] = self.grid_content.GetNumberRows()
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick_EditGrid, self.grid_content)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_CLICK, self.On_LClick_EditGrid, self.grid_content)

    ## compose address specific menu parts
    def create_specific_menu(self):
        # setup address menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Anfrage", "")
        self.Bind(wx.EVT_MENU, self.On_MAnfrage, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Suchen", "")
        self.Bind(wx.EVT_MENU, self.On_Faktura_Ausw, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Bearbeiten", "")
        self.Bind(wx.EVT_MENU, self.On_Faktura_Test, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&E-Mail versenden", "")
        self.Bind(wx.EVT_MENU, self.On_MEMail, mmenu)
        tmp_menu.Append(mmenu)
        self.menubar.Append(tmp_menu, "Adresse")
        # setup address menu
        #tmp_menu = wx.Menu() 
        #mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "&Suche", "")
        #self.Bind(wx.EVT_MENU, self.On_MAddress_search, mmenu)
        #tmp_menu.Append(mmenu)
        #mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Be&arbeiten", "")
        #self.Bind(wx.EVT_MENU, self.On_Adresse_aendern, mmenu)
        #tmp_menu.Append(mmenu)
        #self.menubar.Append(tmp_menu, "Adresse")
        return

    ## Eventhandler on activation of screen
    # set flags from globals, possibly invoke selection
    def On_Activate(self,event):
        if not self.active:
            self.active = True
            self.use_RETURN = self.globals.get_value("use-RETURN","Faktura")
            self.use_custom_selection = self.globals.get_value("use-custom-selection","Faktura")
            self.automated_selection = self.globals.get_value("automated-selection","Faktura")
            if self.automated_selection:
                self.automated_row_selection = self.automated_selection
                self.invoke_selection()
            self.panel.SetFocus()
    ## Eventhandler MENU; BUTTON - select other invoice, either direkt or via attribut
    def On_Faktura_Ausw(self,event):
        if self.debug: print("Event handler `On_Faktura_Ausw'!")
        #self.sb.set_debug()
        self.invoke_selection()
        #self.sb.unset_debug()
        event.Skip()
    ## Eventhandler BUTTON - manipulate address data
    def On_Adresse(self,event = None):
        if self.debug: print("Event handler `On_Adresse'")
        changed = AfpLoad_DiAdEin_fromKNr(self.globals, self.data.get_value("KundenNr"))
        if changed: self.Reload()
        if event: event.Skip()
    ## Eventhandler BUTTON - create new record
    def On_Neu(self,event = None):
        if self.debug: print("Event handler `On_Neu'")
        typ = self.combo_Filter.GetValue()
        KNr = None
        GNr = None
        if self.data.get_value("KundenNr"):
            res = AfpReq_MultiLine("Welche Daten sollen übernommen werden?", "Bitte die entsprechend Daten auswählen.", "Check",["Adresse","Gerät"], "Daten übernehmen?")
            if res:
                if res[0]: 
                    KNr = self.data.get_value("KundenNr")
                    if res[1]: GNr = self.data.get_value("AttNr")
        self.generate_new_data(typ, KNr, GNr)
        if event: event.Skip()
    ## Eventhandler BUTTON - invoke cash sale
    def On_Bar(self,event = None):
        if self.debug: print("Event handler `On_Bar'")
        self.generate_new_data()
        if event: event.Skip()
    ## Eventhandler BUTTON -  invoke payment- not implemented yet!
    def On_Zahlung(self,event = None):
        if self.debug: print("Event handler `On_Zahlung'")
        self.invoke_Zahlung(self.data)   
        if event: event.Skip()
    ## handle payment dialog
    # @param data - data to be handled
    def invoke_Zahlung(self, data):
        if data.is_payable():
            Ok, newdata = AfpLoad_DiFiZahl(data)
            if Ok: 
                #newdata.view() # for debug
                newdata.store()
                self.data = newdata
                self.Reload()
    ## handle payment dialog with selection
    def select_Zahlung(self):
        datei, ident = AfpReq_FaSelectedRow(self.globals.get_mysql(),"Rechnung", "Bitte offene Rechnung auswählen!", self.debug)
        if datei and ident:
            data = AfpInvoice(self.globals, ident)
            self.invoke_Zahlung(data)   
    ## Eventhandler MENU, BUTTON - invoke special select dialog - for testing only
    def On_Faktura_Test(self,event):
        if self.debug: print("AfpAdScreen Event handler `On_Faktura_Test'")
        #self.invoke_custom_select()
        Ok = AfpLoad_FaLine()
        event.Skip()
    ## Eventhandler BUTTON - invoke dokument generation 
    def On_Dokument(self,event):
        if self.debug and event: print("Event handler `On_Dokument'")
        Faktura = self.get_data()
        zustand = Faktura.get_string_value("Zustand").strip()
        header = Faktura.get_listname() + " " + zustand
        prefix = "Faktura_" + header
        AfpLoad_DiReport(Faktura, self.globals, None, header, prefix, zustand)
        if event:
            self.Reload()
            event.Skip()
        event.Skip()
        
    ## Eventhandler BUTTON -  invoke arrival (of goods)- not implemented yet!
    def On_Ware(self,event = None):
        print("Event handler `On_Ware' not implemented!")
        if event: event.Skip()
    ## Eventhandler BUTTON -  invoke cash office - not implemented yet!
    def On_Kasse(self,event = None):
        print("Event handler `On_Kasse' not implemented!")
        if event: event.Skip()
    ## Eventhandler BUTTON -  invoke additional functionallity - not implemented yet!
    def On_Extra(self,event = None):
        print("Event handler `On_Extra' not implemented!")
        if event: event.Skip()
        
    ## Eventhandler COMBOBOX - allow filter due to attributes, change master table
    def On_Filter(self,event = None): 
        value = self.combo_Filter.GetValue()
        if self.debug: print("AfpFaScreen Event handler `On_Filter'", value)
        if self.is_editable():
            filter, orig = AfpFa_changeKind(value, self.data.get_kind())
            self.combo_Filter.SetValue(filter)
            if orig:
                self.text_Datum.SetValue(self.data.get_string_value("Datum"))
                self.text_RechNr.SetValue(self.data.get_string_value("RechNr"))
                self.set_changecolor("RechNr", True)
            else:
                self.text_Datum.SetValue(self.globals.today_string())
                self.text_RechNr.SetValue("")
                self.set_changecolor("RechNr")
            self.Refresh()
            return
        datei, filter = AfpFa_possibleKinds(value)
        reset = False
        print("AfpFaScreen.On_Filter:", datei, filter, self.sb_master)
        if not datei: 
            datei = self.sb_master
            reset = True
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
                self.sb.select_current()
            self.CurrentData()
        if reset:
            self.combo_Filter.SetSelection(self.get_filter_index(self.sb_master))
        if event: event.Skip()
    ## Eventhandler COMBOBOX - sort index
    def On_Sortierung(self,event = None):
        value = self.combo_Sortierung.GetValue()
        index = self.indexmap[value]
        if self.debug: print("Event handler `On_Sortierung'",self.index, index)
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
        print("Event handler `On_CStatus' only implemented to reset selection!")
        event.Skip()
        
    ## Eventhandler MENU - add an enquirery - not yet implemented! \n
    def On_MAnfrage(self, event):
        print("Event handler `On_MAnfrage' not implemented!")
        event.Skip()
    ## Eventhandler MENU - send an e-mail - not yet implemented! 
    def On_MEMail(self, event):
        if self.debug: print("Event handler `On_MEMail'")
        mail = AfpMailSender(self.globals, self.debug)
        an = self.data.get_value("Mail.ADRESSE")
        if an: mail.add_recipient(an)
        mail, send = Afp_editMail(mail)
        if send: mail.send_mail()
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
                        print("WARNING in AfpFaScreen: External file", filename, "does not exist, look in 'antiquedir'.") 
                        filename = Afp_addRootpath(self.globals.get_value("antiquedir"), file)
                    if Afp_existsFile(filename):
                        Afp_startFile(filename, self.globals, self.debug, True)
                    else:
                        print("WARNING in AfpFaScreen: External file", filename, "does not exist!") 
        event.Skip()
    ## special routine to update content grid and all dependent fields
    def Pop_content(self):
        self.Pop_grid("Content")
        self.Pop_special()
    ## set right status-choice for this address
    def Pop_choice_status(self):
        stat = self.data.get_value("Kennung.ADRESSE")
        if not stat: stat = 0
        choice = self.choicemap[stat]
        self.choice_Status.SetSelection(choice)
        if self.debug: print("AfpFaScreen.Pop_choice_status:", choice)
    ## population routine for special treatment - overwritten from AfpScreen
    def Pop_special(self):
        brutto = self.data.get_value("Betrag")
        zahlbetrag = self.data.get_value("ZahlBetrag")
        netto = self.data.get_value("Netto")
        gewinn = self.data.get_value("Gewinn")
        print("AfpFaScreen.Pop_special:", brutto, netto, gewinn, zahlbetrag)
        if self.is_editable():
            if not gewinn is None:
                if netto:
                    pro = Afp_toString(int(100*gewinn/netto))
                else:
                    pro = "0"
                label = Afp_toString(gewinn)
                label = pro + "00" + label[:-3].strip() + label[-2:]
                self.label_Gew.SetLabel(label)
            self.text_Netto.SetValue(Afp_toString(netto)) 
            self.text_Betrag.SetValue(Afp_toString(brutto)) 
            self.set_changecolor("Preis")
        else:
            self.label_Gew.SetLabel("")
        if zahlbetrag is None: zahlbetrag = brutto
        self.text_ZahlBetrag.SetValue(Afp_toString(zahlbetrag)) 
        if brutto is None or netto is None:
            Mwst = ""
        else:
            Mwst = brutto - netto
        self.text_Mwst.SetValue(Afp_toString(Mwst)) 
        if not self.data.get_value("KundenNr"):
            self.label_Name.SetLabel(self.direct_sale_name)
            self.label_Tel.Enable(False)
            self.label_Mail.Enable(False)
        else:
            self.label_Tel.Enable(True)
            self.label_Mail.Enable(True)
    ## postprocessing of text editing, insert textrows into data
    # @param textrange - [text, [startrow, endrow]] which has been changed, 
    #               start- and endrow indicate the original rows, where text has been read from before it was changed
    def edit_text_postprocess(self, textrange):
        textrows = textrange[0].split('\n')
        empty = 0
        for row in reversed(textrows):
            if row:
                break
            else:
                empty += 1
        lgh = len(textrows) - empty 
        rows = []
        for i in range(lgh):
            rows.append([textrows[i]])
        #print "AfpFaScreen.edit_text_postprocess:", textrows, lgh, empty, rows
        self.data.replace_content_rows(textrange[1], ["Zeile"], rows)   
        self.Pop_content()
    ## postprocessing of data editing
    # @param row - changed row data to be proceeded
    # @param rowNr - index of changed row
    # @param delete - if given, flag if row should be deleted
    def edit_data_postprocess(self, row, rowNr, delete = False):
        if delete:
            self.data.change_content_row(rowNr, None)
        else:
            lgh = self.data.get_content_length()
            self.data.change_content_row(rowNr, row)
            if rowNr is None or lgh < self.data.get_content_length():
                rowNr = self.data.get_content_length()
        self.Pop_content()
        self.select_row(rowNr)
    ## edit a grid line
    # @param typ - typ of line editing, valid types: None - choose, free - free artcle entry, stock - enter stock receipt
    # @param value - value(s) to be inserted
    # @param index - sortindex in database table
    # @param rowNr - number of row to be edited
    def edit_line(self, typ, value, index, rowNr):
        print("AfpFaScreen.edit_line:", value, index, rowNr)
        if typ is None:
            #self.sb.set_debug()
            self.sb.CurrentIndexName(index, "ARTIKEL")
            self.sb.select_key(value)
            param = None
        else:
            param = value
        #process = [ ["choose",",ArtikelNr,Bezeichnung,,Nettopreis,Nettopreis,Einkaufspreis,Zeile"], [3,"Afp_intString","$5 = $5 * $3,$6 =( $4 - $6 )* $3"]] 
        process = self.data.get_grid_lineprocessing(typ, param)
        if rowNr is None:
            rowNr = self.data.get_content_length()
        self.catch_keydown = EditLine = AfpFaScreen_EditLinePlugIn( self.grid_editable, rowNr, self.sb, process, self.debug)
        self.postprocess_keydown = self.get_edit_line_result
        print("AfpFaScreen.edit_line catch:",  self.catch_keydown, self.postprocess_keydown)
        EditLine.display_row()
        #self.sb.unset_debug()
    ## get edit line results from plugin
    def get_edit_line_result(self):
        EditLine = self.catch_keydown
        EditLine.select_row(True)
        newrow = EditLine.get_row_edit_result()
        self.edit_data_postprocess(newrow, self.selected_row )
    ## edit a text line
    # @param textrange - [text, [startrow, endrow]] to be edited
    def edit_text(self, textrange):
        #line, Ok = AfpReq_Text("Bitte Text eingeben.","",text)
        text = textrange[0]
        if text is None: text = ""
        print("AfpFaScreen.edit_text:", text)
        newtext, Ok = AfpReq_EditText(text, "TextEditor","Bitte Text eingeben.", None, None, True)
        if Ok: 
            textrange[0] = newtext
        else: 
            textrange = None
        return textrange
    ## invoke selection
    def invoke_selection(self):
        if self.use_custom_selection:
            print("AfpFaScreen.invoke_selection: invoke custom selection")
            self.invoke_custom_select()
        else:    
            index = self.index
            where = AfpSelectEnrich_dbname(self.sb.identify_index().get_where(), self.sb_master)
            value = self.sb.identify_index().get_indexwert()
            if index == "KundenNr":
                value = self.data.get_value("Name.ADRESSE")
            self.invoke_regular_selection(self.sb_master, value, where)
    ## regularpart of selections, use common 'Auswahl' mechanismn
    # @param table - tablename to be used for selection 
    # @param value - value to be looked for 
    # @param where - filter to be used 
    def invoke_regular_selection(self, table, value = "", where = ""):
        #print "On_Faktura_Ausw Ind:",index, "VAL:",values,"Where:", where
        #print "On_Faktura_Ausw Merkmal:", self.combo_Filter.GetValue()
        #self.sb.set_debug()
        auswahl = AfpLoad_FaAusw(self.globals, table, self.index, Afp_toString(value), where, True)
        #self.sb.unset_debug()
        if not auswahl is None:
            RNr = int(auswahl)
            if self.sb_filter: self.sb.select_where(self.sb_filter, "RechNr", self.sb_master)
            self.sb.select_key(RNr, "RechNr", self.sb_master)
            if self.sb_filter: self.sb.select_where("", "RechNr", self.sb_master)
            self.sb.set_index(self.index, self.sb_master, "RechNr")   
            self.sb.CurrentFileName(self.sb_master)
            self.set_current_record()
            if self.index == "KundenNr":
                self.sb.select_key(self.data.get_value("KundenNr"),"KundenNr","ADRESSE")
                self.sb.set_index("Name","ADRESSE","KundenNr")
            self.Populate()
        #self.sb.unset_debug()
    ## invoke the custom select dialog, behaves as follows 
    # - Ok == True: data becomes current data of screen
    # - Ok = string, (optional: data = string): Ok triggers routine, data triggers databasetable
    def invoke_custom_select(self):
        Ok, data, self.custom_index = AfpLoad_FaCustomSelect(self.globals, self.custom_index)
        print("AfpFaScreen.invoke_custom_select:", Ok, data)
        # fork to the different tasks, standard way Ok == True
        if Ok and data:
            if Ok == True:
                self.set_direct_data(data)
            elif Afp_isString(Ok):
                if data == "KVA": data = "Kostenvoranschlag"
                if Ok == "Suchen":
                    table, filter = AfpFa_possibleKinds(data)
                    where = None
                    if table == "KVA": where = "Zustand = \"" + filter + "\""
                    print("AfpFaScreen.invoke_custom_select Suchen:", table, where)
                    if table:
                        self.sb_master = table
                        self.invoke_regular_selection(table, "", where)
                        self.combo_Filter.SetValue(data)
                        #self.On_Filter()
                elif Ok == "Neu":
                    print("AfpFaScreen.invoke_custom_select Neu:", data)
                    if data: self.generate_new_data(data, None)
        elif Ok:
            if Ok == "Bar":
                self.On_Bar()
            elif Ok == "Zahlung":
                self.select_Zahlung()
            elif Ok == "Ware":
                self.On_Ware()
            elif Ok == "Kasse":
                self.On_Kasse()
            elif Ok == "Mehr":
                self.On_Extra()
    ## generate a new data record
    # @param typ - if given, typ of incident to be created, default: "Rechnung" (Invoice)
    # @param KNr - identifier of address fornthis new incident,
    # - 0: direct invoice without address; cash sale (default) 
    # - None: address has to be selected                      
    def generate_new_data(self, typ = "Rechnung", KNr = 0, GNr = None):
        table, subtyp = AfpFa_possibleKinds(typ)
        if KNr is None:
            GNr = None
            name = self.data.get_value("Name.ADRESSE")
            if not name:
                name, ok = AfpReq_Text("Bitte Namen für Auftraggeber eingeben!","","","Namenseingabe")
            text = "Bitte Auftraggeber für " + typ + " auswählen:"
            KNr = AfpLoad_AdAusw(self.globals,"ADRESSE","NamSort",name, None, text)
        if not KNr is None:
            print("AfpFaScreen.generate_new_data invoked for", typ, subtyp, KNr)
            if table == "KVA":
                data = AfpOffer(self.globals)
            elif table == "BESTELL":
                data = AfpOrder(self.globals)
            else:
                data = AfpInvoice(self.globals)
            data.set_new(subtyp, KNr)
            if GNr is None and KNr: 
                GNr = AfpAdresse_indirectAttributFromKNr(self.globals, KNr,"Gerät oder PKW")
            #print "AfpFaScreen.generate_new_data set AttNr:", GNr
            if GNr:
                data.set_value("AttNr",GNr)
            #print "AfpFaScreen.generate_new_data read AttNr:", data.get_value("AttNr")
            self.loaded_data = self.data
            self.data = data
            self.Populate()
            self.Set_Editable(True)
            print("AfpFaScreen.generate_new_data 'edit_data' invoked") 
            self.edit_data(0)
            print("AfpFaScreen.generate_new_data 'edit_data' ended") 
        
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
    ## direct selection of record via tablename and identifier
    # @param data -  SelectionList to be current on screen
    def set_direct_data(self, data):
        self.index = data.get_mainindex()
        self.sb_master = data.get_maintable()
        ReNr = data.get_value(self.index)
        if ReNr:
            filter = data.get_value("Zustand")
            name, index = AfpFa_possibleKinds(None, self.sb_master, filter)
            if not len(name): name = self.sb_master
            self.sb.CurrentIndexName("RechNr", self.sb_master)
            self.sb.select_key(ReNr)
            self.combo_Filter.SetSelection(self.get_filter_index(name))
            self.On_Sortierung()
        self.data = data
        self.Populate()
      
    ## extract price difference from row
    # @param newrow - new row values
    # @param oldrow - old row values
    def get_price_diff(self, newrow, oldrow):
        index = 5
        diff = 0.0
        if newrow[index]:
            diff += Afp_floatString(newrow[index])
        if oldrow[index]:
            diff -= Afp_floatString(oldrow[index])
        return diff
    ## extract appropriate index in filter list
    # @param name - name of list entry
    def get_filter_index(self, name):
        index = AfpFa_inFilterList(name)
        if index is None:
            if name == "RECHNG": index = AfpFa_inFilterList("Rechnung")
            elif name == "KVA": index = AfpFa_inFilterList("KVA")
            elif name == "BESTELL": index = AfpFa_inFilterList("Bestellung")
            else: index = 0
        return index
    # set and unset changecolor on different textfield
    # @param typ - defines which fields should be changed
    # - = "RechNr": 'Datum' and 'RechNr'  are changed
    # - = "Preis": 'Netto', 'Betrag' and 'Mwst'  are changed at second call
    # - = "all": all above fields are changed appropriate
    # @param unset - flag to remove changecolor
    def set_changecolor(self, typ = "all", unset = False):
        if unset:
            if typ == "all" or typ == "Preis":
                self.text_Netto.SetBackgroundColour(self.editcolor)
                self.text_Betrag.SetBackgroundColour(self.editcolor)
                self.text_Mwst.SetBackgroundColour(self.editcolor)
                self.first_content_change = None
            if typ == "all" or typ == "RechNr":
                self.text_Datum.SetBackgroundColour(self.editcolor)
                self.text_RechNr.SetBackgroundColour(self.editcolor)
        else:
            if typ == "all" or typ == "Preis":
                if self.first_content_change == True:
                    self.text_Netto.SetBackgroundColour(self.changecolor)
                    self.text_Betrag.SetBackgroundColour(self.changecolor)
                    self.text_Mwst.SetBackgroundColour(self.changecolor)
                    self.first_change = False
                elif self.first_content_change is None:
                    self.first_content_change = True
            if typ == "all" or typ == "RechNr":
                self.text_Datum.SetBackgroundColour(self.changecolor)
                self.text_RechNr.SetBackgroundColour(self.changecolor)
    # routines to be overwritten in explicit class
    ## set or unset editable mode - overwritten from AfpEditScreen
    # @param ed_flag - flag to turn editing on or off
    # @param lock_data - flag if invoking of editable mode needs a lock on the database
    def Set_Editable(self, ed_flag, lock_data = None):
        if ed_flag:
            self.edit_typ = None
            if self.data and self.data.is_processable():
                if self.data.get_listname() == "Bestellung":
                    #if self.data.is_editable():
                        #Ok = AfpReq_Question(text, "Sollen die Daten so gespeichert werden?", "Daten speichern?")
                    self.edit_typ = "stock"
        AfpEditScreen.Set_Editable(self, ed_flag, lock_data)
        if not ed_flag:  
            if self.text_Datum.GetBackgroundColour() == self.changecolor:
                self.combo_Filter.SetSelection(AfpFa_inFilterList(self.sb_master, self.data.get_value("Zustand")))
            self.set_changecolor("all", True)
        self.Pop_special()
    ## edit content data -  overwritten from AfpEditScreen
    # @param rowNr - if given, index of row to be changed
    def edit_data(self, rowNr = None):
        print("AfpFaScreen.edit_data invoked", rowNr)
        ident = None
        name = ""
        text = [None, None]
        row = None
        delete = False
        edit_next = True
        direct = self.edit_typ
        if not rowNr is None and rowNr < self.data.get_content_length():
            ident, name, text, anz = self.get_content_indicators(rowNr)
        else:
            if direct: edit_next = False
        print("AfpFaScreen.edit_data while outside:", ident, name, text, edit_next, self.debug)
        while edit_next:
            edit_next = False
            edit_text = False
            if self.use_custom_selection:
                Ok = False
                action = None
                if direct == "stock":
                    if anz[0]:
                        action = [direct, anz]
                        Ok = True
                elif Afp_isString(ident) or (ident is None and not text[0]):
                    Ok, action = AfpLoad_FaLine(ident, name, self.debug)
                if not Ok is None:
                    if Ok:
                        if action[1] == "frei":
                            print("AfpFaScreen.edit_data frei:", action)
                            self.edit_line("free", action[0], None, rowNr)
                        else:
                            self.edit_line(None, action[0], action[1], rowNr)
                    else:
                        edit_text = True
            else:
                if text:
                    edit_text = True
                else:
                    if not ident: ask = True
                    else: ask = False
                    res = AfpLoad_FaArtikelAusw(self.globals, "ArtikelNr", ident, None, ask)
                    print("AfpFaScreen.edit_data:", res)
                    # ToDo: res has to be expanded to row
            if edit_text:
                newtext = self.edit_text(text)
                print("AfpFaScreen.edit_data text:", newtext)
                if not newtext is None: 
                    if newtext[1] is None: lastrow = self.data.get_content_length()
                    else: lastrow = newtext[1][1]
                    if self.automated_selection and lastrow  == self.data.get_content_length():
                        edit_next = True
                    self.edit_text_postprocess(newtext)
            elif row or delete:
                self.edit_data_postprocess(row, rowNr, delete)
                if not delete and self.automated_selection and self.selected_row  == self.data.get_content_length():
                    edit_next = True
                row = None
                delete = False
            print("AfpFaScreen.edit_data while inside", edit_next, self.catch_keydown, self.edit_data_postprocess)
    ## check if data should or has to be stored - overwritten from AfpEditScreen \n
   # three return values are possible:
   # - None: no data to be saved
   # - False: user selects not to save data
   # - True: data has to be saved
    def check_data(self):
        value = self.combo_Filter.GetValue()
        datei, filter = AfpFa_possibleKinds(value)
        Ok = None
        if self.data.has_changed():
            Ok = True
        if not self.globals.get_value("instant-save","Faktura"):
            text = ""
            if datei != self.sb_master:
                orig = self.data.get_kind()
                text = "\"" + orig + "\" wird in \""  + value + "\" umgewandelt!"
            if Ok:
                if text:
                    text += "\n"
                text += "Der Inhalt hat sich verändert!"
            if text:
                #Ok = AfpReq_Question(text, "Sollen die Daten so gespeichert werden?", "Daten speichern?", False)
                Ok = AfpReq_Question(text, "Sollen die Daten so gespeichert werden?", "Daten speichern?")
        return Ok
   ## store data - overwritten from AfpEditScreen
    def store_data(self):
        # ToDo: add data from widgets (combo box)
        value = self.combo_Filter.GetValue()
        datei, filter = AfpFa_possibleKinds(value)
        if datei != self.sb_master:
            # conversion necessary
            selnames = ["ADRESSE","ADRESATT","Content"]
            faktura = self.data.get_converted_faktura(datei, filter)
            faktura.cannibalise(self.data, selnames)
            self.data = faktura
        elif filter != self.sb_filter:
            # kind changed
            self.data.set_value("Zustand", filter)
        if self.data.has_changed():
            self.data.store()    
    
    ## expand data to complete row. depending on input
    # @param value - value to be looked for, if dateifeld = None: line in grid data, else: identifier in database table
    # @param dateifield - column.table where identifier is selected from
    def expand_to_row(self, value, dateifeld = None):
        print("AfpFaScreen.expand_to_row", value, dateifeld)
        self.sb.CurrentIndex(dateifeld)
        self.sb.select_key(value)
        
        # ToDo:
    ## extract content definition from row
    # @param rowNr - index of row from where data is extracted
    def get_content_indicators(self, rowNr):
        ident = None
        name = None
        text = None
        trange = None
        anz = None
        lief = None
        value = self.data.get_value_rows("Content", "ErsatzteilNr", rowNr)[0][0]
        if value and not Afp_isInteger(value):
            ident = Afp_fromString(value)
        if not ident:
            anz = self.data.get_value_rows("Content", "Anzahl", rowNr)[0][0]
            if anz:
                name = Afp_toString(self.data.get_value_rows("Content", "Bezeichnung", rowNr)[0][0])
                lief  = self.data.get_value_rows("Content", "Lieferung", rowNr)[0][0]
                #name = Afp_fromString(self.data.get_value_rows("Content", "Bezeichnung", rowNr)[0][0])
            else:
                text = ""
                start = rowNr
                ende = rowNr + 1
                ranges = self.data.get_content_range("Anzahl","False")
                print("AfpFaScreen.get_content_indicators Ranges:", ranges)                
                for rang in ranges:
                    if rowNr >= rang[0] and rowNr <= rang[1]:
                        start = rang[0]
                        ende = rang[1] + 1
                for row in range(start, ende):
                    text += self.grid_content.GetCellValue(row, 1)
                    if text: text += '\n'
                trange = [start, ende-1]
        print("AfpFaScreen.get_content_indicators:", rowNr, ident, name, [text, trange], [anz, lief])
        return ident, name, [text, trange], [anz, lief]

    ## insert row in content data -  overwritten from AfpEditScreen
    # @param rowNr - if given, index of row to be changed
    def insert_row(self, rowNr = None):
        print("AfpFaScreen.insert_row invoked", rowNr)
        if rowNr is None:
            rowNr = self.data.get_content_length()
        if rowNr >  self.data.get_content_length():
            self.data.content.add_data_row() 
        else:
            self.data.content.insert_data_row(rowNr)
        self.Pop_content()
    ## delete row from content data -  overwritten from AfpEditScreen
    # @param rowNr - if given, index of row to be changed
    def delete_row(self, rowNr = None):
        print("AfpFaScreen.delete_row invoked", rowNr)
        if rowNr is None:
            rowNr = self.data.get_content_length()
        self.data.content.delete_row(rowNr)
        self.data.update_fields()
        self.Pop_content()
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
            #self.sb.select_key(11658) # for tests
            #self.sb.select_key(21167) # for tests
            self.sb.select_last() # for tests
        else:
            self.sb.CurrentIndexName("RechNr","RECHNG")
            self.sb.select_key(ReNr)
        self.index = "RechNr"
        self.set_current_record() # needed?
        return
    ## get identifier of graphical objects, 
    # where the keydown event should not be catched
    # (overwritten from AfpScreen)
    def get_no_keydown(self):
        return ["Bem","BemExt","MerkT_Archiv","Content"]
    ## get names of database tables to be opened for this screen
    # (overwritten from AfpScreen)
    def get_dateinamen(self):
        return  ["RECHNG","KVA","BESTELL","ADRESSE","ARTIKEL"]
    ## get rows to populate lists \n
    # possible selection criterias have to be separated by a "None" value
    # @param typ - name of list to be populated 
    def get_list_rows(self, typ):
        rows = []
        if self.debug: print("AfpFaScreen.get_list_rows:", typ)
        if typ == "Archiv" and self.data:
            rawrow = self.data.get_string_rows("ARCHIV", "Datum,Gruppe,Bem,Extern")
            for row in rawrow:
                rows.append(row[0] + " " + row[1] + " " + row[2])
            rows.append(None)
            for row in rawrow:
                rows.append(row[3])
        return rows
    ## get grid rows to populate grids \n
    # (overwritten from AfpScreen) 
    # @param name - name of grid to be populated
    def get_grid_rows(self, name):
        rows = []
        if self.debug: print("AfpFaScreen.get_grid_rows Population routine", name)
        if name == "Content" and self.data:
            id_col = 5      
            self.content_colname = self.data.get_grid_colnames()
            rows = self.data.get_grid_rows()
            for col in range(0,self.grid_cols["Content"] ):
                self.grid_content.SetColLabelValue(col, self.content_colname[col])
            self.editable_rows = len(rows)
            #print "AfpFaScreen.get_grid_rows rows:", self.editable_rows
        #print "AfpFaScreen.get_grid_rows:", rows
        return rows
    ## set current screen data - overwritten from AfpScreen for indirect Inedx handling
    # @param plus - indicator to step forwards, backwards or stay
    def CurrentData(self, plus = 0):
        if self.debug: print("AfpFaScreen.CurrentData", plus)
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
    # End of AfpFaScreen
