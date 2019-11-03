#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFinance.AfpFiDialog
# AfpFiDialog module provides classes and routines needed for user interaction of finance handling and accounting,\n
#
#   History: \n
#        10 July 2019 - add direct accounting dialog- Andreas.Knoblauch@afptech.de
#        08 May 2019 - inital code generated - Andreas.Knoblauch@afptech.de

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

import AfpBase
from AfpBase import AfpUtilities, AfpBaseDialog, AfpBaseDialogCommon, AfpBaseAdRoutines
from AfpBase.AfpUtilities import AfpStringUtilities
from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpBaseDialog import *
from AfpBase.AfpBaseDialogCommon import AfpLoad_editArchiv
from AfpBase.AfpBaseFiDialog import AfpFinance_getZahlVorgang
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw
import AfpFinance
from AfpFinance import AfpFiRoutines
from AfpFinance.AfpFiRoutines import *

## Routine to add SEPA direct debit mandat to sepa object
# @param sepa - sepa data where SEPA mandat should be used for
# @param client - client data where SEPA should be used for
def AfpFinance_addSEPA(sepa, client):
    dir = ""
    fname, ok = AfpReq_FileName(dir, "SEPA Einzugsermächtigung für ".decode("UTF-8") + client.get_name() ,"", True)
    #print fname, ok
    if ok:
        Afp_startFile(fname, sepa.get_globals(), sepa.is_debug(), True)
        date = Afp_dateString(fname)
        liste = [["Erteilungsdatum:", Afp_toString(date)],  ["BIC:",""], ["IBAN:",""]]
        result = AfpReq_MultiLine("Neues SEPA-Lastschriftmandat mit der folgenden Datei erzeugen:".decode("UTF-8"), fname.decode("UTF-8"), "Text", liste, "SEPA-Lastschriftmandat", 500)
        #print "AfpFinance_addSEPA:", result
        if result:
            datum = Afp_fromString(Afp_ChDatum(result[0]))
            sepa.add_mandat_data(client, fname, datum, result[1], result[2])
            return sepa
    return None

## allow direct accounting
class AfpDialog_FiBuchung(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        self.cols = 7
        self.rows = 10
        AfpDialog.__init__(self,None, -1, "")
        self.grid_ident = None
        self.col_percents = [13, 10, 10, 15, 10, 21, 21]
        self.col_labels = ["Datum","Soll","Haben","Betrag","Beleg", "Name", "Bem"]
        self.revenue_accounts = None
        self.expense_accounts = None
        self.internal_accounts = None
        self.bank = None
        self.transfer = None
        self.last_date = None
        self.values = {}
        self.KNr = None
        self.Table = None
        self.TabNr = None

        self.grid_row_selected = None
        self.fixed_width = 80
        self.fixed_height = 80
        self.SetSize((574,410))
        self.SetTitle("Direktbuchung")
        self.Bind(wx.EVT_SIZE, self.On_ReSize)
        #self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
        
    ## set up dialog widgets      
    def InitWx(self):
        self.label_Label = wx.StaticText(self, 1, label="Direktbuchungen für".decode("UTF-8"), name="LLabel")
        self.label_Name = wx.StaticText(self, 1, label="", name="Name")
        self.labelmap["Name"] = "Name.Mandant"
        self.label_Ausz = wx.StaticText(self, 1, label="Auszug:", style=wx.ALIGN_RIGHT, name="LAusz")
        self.label_AzDat = wx.StaticText(self, 1, label="", name="AzDat")
        self.labelmap["AzDat"] = "BuchDat.AUSZUG"
        self.label_AzSaldo = wx.StaticText(self, 1, label="", name="AzSaldo")
        self.labelmap["AzSaldo"] = "EndSaldo.AUSZUG"
        self.text_Auszug=  wx.TextCtrl(self, -1, value="", style=0, name="Auszug")
        self.text_Auszug.Bind(wx.EVT_KILL_FOCUS, self.On_Change_Auszug)
        self.top_line1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line1_sizer.Add(self.label_Label,0,wx.EXPAND)
        self.top_line1_sizer.AddSpacer(10)
        self.top_line1_sizer.Add(self.label_Name,0,wx.EXPAND)
        self.top_line1_sizer.AddSpacer(10)
        self.top_line1_sizer.Add(self.label_Ausz,1,wx.EXPAND)
        self.top_line1_sizer.Add(self.label_AzDat,1,wx.EXPAND)        
        self.top_line1_sizer.Add(self.label_AzSaldo,1,wx.EXPAND)        
        self.top_line1_sizer.Add(self.text_Auszug,1,wx.EXPAND)
        self.top_line1_sizer.AddSpacer(10)
        
        self.label_Datum = wx.StaticText(self, 1, label="Datum:", size=(70,20), name="LDatum")
        self.text_Datum=  wx.TextCtrl(self, -1, value="", style=0, name="Datum")
        self.text_Datum.Bind(wx.EVT_KILL_FOCUS, self.Check_Datum)
        self.label_BDat = wx.StaticText(self, 1, label="Beleg Datum:", size=(70,20), name="LBDat")
        self.text_BDatum=  wx.TextCtrl(self, -1, value="", style=0, name="BDatum")
        self.text_BDatum.Bind(wx.EVT_KILL_FOCUS, self.Check_Datum)
        self.label_Beleg = wx.StaticText(self, 1, label="BelegNr:", size=(70,20), name="LBeleg")
        self.text_Beleg =  wx.TextCtrl(self, -1, value="", style=0, name="Beleg")
        self.top_line2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line2_box1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line2_box1_sizer.Add(self.label_Datum,0,wx.EXPAND)
        self.top_line2_box1_sizer.Add(self.text_Datum,1,wx.EXPAND)
        self.top_line2_sizer.Add(self.top_line2_box1_sizer,1,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(10)
        self.top_line2_box3_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.top_line2_box3_sizer.Add(self.label_BDat,0,wx.EXPAND)
        self.top_line2_box3_sizer.Add(self.text_BDatum,1,wx.EXPAND)
        self.top_line2_sizer.Add(self.top_line2_box3_sizer,1,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(10)
        self.top_line2_box2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line2_box2_sizer.Add(self.label_Beleg,0,wx.EXPAND)
        self.top_line2_box2_sizer.Add(self.text_Beleg,1,wx.EXPAND)
        self.top_line2_sizer.Add(self.top_line2_box2_sizer,1,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(10)
         
        self.label_Soll = wx.StaticText(self, 1, label="Soll:", size=(70,20), name="LSoll")
        self.combo_Soll = wx.ComboBox(self, -1, value="", choices=[], style=wx.CB_DROPDOWN, name="Soll")
        self.Bind(wx.EVT_COMBOBOX, self.Check_Konten, self.combo_Soll)
        self.label_Haben = wx.StaticText(self, 1, label="Haben:", size=(70,20), name="LHaben")
        self.combo_Haben = wx.ComboBox(self, -1, value="", choices=[], style=wx.CB_DROPDOWN, name="Haben")
        self.Bind(wx.EVT_COMBOBOX, self.Check_Konten, self.combo_Haben)
        self.label_Betrag = wx.StaticText(self, 1, label="Betrag:", size=(70,20), name="LBetrag")
        self.text_Betrag=  wx.TextCtrl(self, -1, value="", style=0, name="Betrag")
        self.top_line3_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line3_box1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line3_box1_sizer.Add(self.label_Soll,0,wx.EXPAND)
        self.top_line3_box1_sizer.Add(self.combo_Soll,1,wx.EXPAND)
        self.top_line3_sizer.Add(self.top_line3_box1_sizer,1,wx.EXPAND)
        self.top_line3_sizer.AddSpacer(10)
        self.top_line3_box2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line3_box2_sizer.Add(self.label_Haben,0,wx.EXPAND)
        self.top_line3_box2_sizer.Add(self.combo_Haben,1,wx.EXPAND)
        self.top_line3_sizer.Add(self.top_line3_box2_sizer,1,wx.EXPAND)
        self.top_line3_sizer.AddSpacer(10)
        self.top_line3_box3_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.top_line3_box3_sizer.Add(self.label_Betrag,0,wx.EXPAND)
        self.top_line3_box3_sizer.Add(self.text_Betrag,1,wx.EXPAND)
        self.top_line3_sizer.Add(self.top_line3_box3_sizer,1,wx.EXPAND)
        self.top_line3_sizer.AddSpacer(10)
        
        self.label_Text = wx.StaticText(self, 1, label="Text:", size=(70,20), name="LText")
        self.text_Text=  wx.TextCtrl(self, -1, value="", style=0, name="Text")
        self.top_line4_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line4_sizer.Add(self.label_Text,0,wx.EXPAND)
        self.top_line4_sizer.Add(self.text_Text,1,wx.EXPAND)
        self.top_line4_sizer.AddSpacer(10)

        self.label_Vorgang = wx.StaticText(self, 1, label="Vorgang:", size=(70,20), name="LVorgang")
        self.combo_Vorgang = wx.ComboBox(self, -1, value="-automatisch-", choices=["-automatisch-","Zahlung","Zahlung intern","Intern"], style=wx.CB_DROPDOWN, name="Vorgang")
        #self.Bind(wx.EVT_COMBOBOX, self.On_Index, self.combo_Vorgang)
        self.label_Vortext = wx.StaticText(self, 1, label="", name="LVortext")       
        self.top_line5_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line5_sizer.Add(self.label_Vorgang,0,wx.EXPAND)
        self.top_line5_sizer.Add(self.combo_Vorgang,1,wx.EXPAND)
        self.top_line5_sizer.AddSpacer(10)
        self.top_line5_sizer.Add(self.label_Vortext,3,wx.EXPAND)
        self.top_line5_sizer.AddSpacer(10)

        self.top_text_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_text_sizer.Add(self.top_line1_sizer,0,wx.EXPAND)
        self.top_text_sizer.AddSpacer(10)
        self.top_text_sizer.Add(self.top_line2_sizer,0,wx.EXPAND)
        self.top_text_sizer.AddSpacer(10)
        self.top_text_sizer.Add(self.top_line3_sizer,0,wx.EXPAND)
        self.top_text_sizer.AddSpacer(10)
        self.top_text_sizer.Add(self.top_line4_sizer,0,wx.EXPAND)
        self.top_text_sizer.AddSpacer(10)
        self.top_text_sizer.Add(self.top_line5_sizer,0,wx.EXPAND)
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_sizer.AddSpacer(10)
        self.top_sizer.Add(self.top_text_sizer,1,wx.EXPAND)
        
        self.button_Minus = wx.Button(self, -1, label="&-", size=(50,50), name="Minus")
        self.Bind(wx.EVT_BUTTON, self.On_Delete, self.button_Minus)
        self.button_Change = wx.Button(self, -1, label="&<>", size=(50,50), name="Change")
        self.Bind(wx.EVT_BUTTON, self.On_Adopt, self.button_Change)
        self.button_Plus = wx.Button(self, -1, label="&+", size=(50,50), name="Plus")
        self.Bind(wx.EVT_BUTTON, self.On_Add, self.button_Plus)
        box = wx.StaticBox(self, label="Aktion", size=(60, 212))
        self.right_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.right_sizer.AddStretchSpacer(2)      
        self.right_sizer.Add(self.button_Plus,0,wx.EXPAND)        
        self.right_sizer.AddStretchSpacer(1) 
        self.right_sizer.Add(self.button_Change,0,wx.EXPAND)               
        self.right_sizer.AddStretchSpacer(1) 
        self.right_sizer.Add(self.button_Minus,0,wx.EXPAND)               
        self.right_sizer.AddStretchSpacer(2) 
        
        self.grid_buchung = wx.grid.Grid(self, -1, style=wx.FULL_REPAINT_ON_RESIZE, name="Buchung")
        self.gridmap.append("Buchung")
        self.grid_buchung.CreateGrid(self.rows, self.cols)
        self.grid_buchung.SetRowLabelSize(0)
        self.grid_buchung.SetColLabelSize(18)
        self.grid_buchung.EnableEditing(0)
        #self.grid_buchung.EnableDragColSize(0)
        self.grid_buchung.EnableDragRowSize(0)
        self.grid_buchung.EnableDragGridSize(0)
        self.grid_buchung.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)   
        self.grid_buchung.SetColLabelValue(0, "Datum")
        self.grid_buchung.SetColLabelValue(1, "Soll")
        self.grid_buchung.SetColLabelValue(2, "Haben")
        self.grid_buchung.SetColLabelValue(3, "Betrag")
        self.grid_buchung.SetColLabelValue(4, "Beleg")
        self.grid_buchung.SetColLabelValue(5, "Name")
        self.grid_buchung.SetColLabelValue(6, "Bem")
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid_buchung.SetReadOnly(row, col)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_CLICK, self.On_LClick, self.grid_buchung)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick, self.grid_buchung)
        #self.Bind(wx.grid.EVT_GRID_CMD_CELL_RIGHT_CLICK, self.On_RClick, self.grid_buchung)

        self.left_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_sizer.Add(self.grid_buchung,1,wx.EXPAND)        
        
        self.button_Load = wx.Button(self, -1, label="&Laden", name="BLoad")
        self.Bind(wx.EVT_BUTTON, self.On_Load, self.button_Load)
        self.button_Vor = wx.Button(self, -1, label="&Vorgang", name="BVor")
        self.Bind(wx.EVT_BUTTON, self.On_Vorgang, self.button_Vor)
        self.button_Adresse = wx.Button(self, -1, label="&Adresse", name="BAdresse")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse, self.button_Adresse)
        self.lower_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lower_sizer.AddStretchSpacer(2) 
        self.lower_sizer.Add(self.button_Load,5,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(2) 
        self.lower_sizer.Add(self.button_Vor,5,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(2) 
        self.lower_sizer.Add(self.button_Adresse,5,wx.EXPAND) 
        self.setWx(self.lower_sizer, [2, 5, 1], [1, 5, 2])
       
        # compose sizers
        self.mid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mid_sizer.AddSpacer(10)
        self.mid_sizer.Add(self.left_sizer,1,wx.EXPAND)        
        self.mid_sizer.AddSpacer(10)
        self.mid_sizer.Add(self.right_sizer,0,wx.EXPAND)
        self.mid_sizer.AddSpacer(10)
        self.sizer = wx.BoxSizer(wx.VERTICAL)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.top_sizer,0,wx.EXPAND)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.mid_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.lower_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    ## attaches data to this dialog, invokes population of widgets
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        #editable = True
        super(AfpDialog_FiBuchung, self).attach_data( data, new, editable)
        self.set_accounts()
        self.reset_first_line()
        BNr = data.gen_next_rcptnr()
        if BNr:
            self.text_Beleg.SetValue(Afp_toString(BNr))

    ## reset first line dependent from the data
    def reset_first_line(self):
        period = self.data.get_period()
        auszug = self.data.get_auszug()
        if period:
            self.label_Label.SetLabel(self.label_Label.GetLabel() + " '" + period + "':")
        if auszug:
            self.text_Auszug.SetValue(auszug)
            self.text_Auszug.Enable(False)
        
    ## set all available accouts
    def set_accounts(self):
        self.revenue_accounts = []
        self.expense_accounts = []
        self.bank_accounts = []
        revenue_accounts = []
        expense_accounts = []
        internal_accounts = []
        bank_accounts = []
        transfer = ""
        rows = self.data.get_value_rows("KTNR")
        if rows:
            for row in rows:
                if row[4] == "Kosten":
                    self.expense_accounts.append(row[1])
                    expense_accounts.append(Afp_toString(row[1])  + " " + Afp_toString(row[2]))         
                elif row[4] == "Ertrag":
                    self.revenue_accounts.append(row[1])
                    revenue_accounts.append(Afp_toString(row[1])  + " " + Afp_toString(row[2]))             
                elif row[4] == "Bank":
                    self.bank_accounts.append(row[1])
                    bank_accounts.append(Afp_toString(row[1])  + " " + Afp_toString(row[2]))             
                elif row[4] != "Debitor" and row[4] != "Kreditor":
                    internal_accounts.append(Afp_toString(row[1])  + " " + Afp_toString(row[2]))    
                    if row[0] == "ZTF": 
                        self.transfer = row[1]
                        transfer = internal_accounts[-1]
        self.bank = self.data.get_bank()
        if not self.bank:
            self.bank = bank_accounts[0]
        solllist = bank_accounts + [transfer] + expense_accounts
        self.combo_Soll.SetItems(solllist)
        habenlist = bank_accounts + [transfer] + revenue_accounts
        self.combo_Haben.SetItems(habenlist)

    ## population routine for statement of accouns
    def Pop_Auszug(self):
        if self.data.get_auszug():
            sum = self.data.gen_bank_sum()
            label = self.data.get_string_value("StartSaldo.Auszug")  + "\n" + Afp_toString(sum)
            self.label_AzSaldo.SetLabel(label)
     ## population routine for finanacial transaction grid \n
    def Pop_Buchung(self):
        rows = []
        raws = None
        raws = self.data.get_value_rows("BUCHUNG")
        if raws:
            for raw in raws:
                adresse = AfpAdresse(self.data.get_globals(), raw[8])
                row = [raw[1], raw[2], raw[4], raw[7], raw[6], adresse.get_name(True), raw[9], raw[0]]
                rows.append(row)
        if rows:
            lgh = len(rows)
            if lgh > self.rows:
                self.adjust_grid_rows(lgh)
                self.rows = lgh
            self.grid_ident = []
            for row in range(self.rows):
                for col in range(self.cols): 
                    #print "AfpDialog_FiBuchung.Pop_Mandate", row, col
                    if row < lgh:
                        self.grid_buchung.SetCellValue(row, col,  Afp_toString(rows[row][col]))
                    else:
                        self.grid_buchung.SetCellValue(row, col,  "")
                if row < lgh:
                    self.grid_ident.append(rows[row][-1])

    ## populate text an internal values if data has been loaded
    # @param values - dictionary of values to be written into textfields
    def Pop_entries(self, values):
        for entry in values:
            widget = self.FindWindowByName(entry) 
            print "AfpDialog_FiBuchung.Pop_entries widgets:", entry, widget
            if widget:
                if entry[0] == "L":
                    widget.SetLabel(Afp_toString(values[entry]))
                else:
                    widget.SetValue(Afp_toString(values[entry]))
            else:
                self.values[entry] = values[entry]
        print "AfpDialog_FiBuchung.Pop_entries:", self.values

    ## read account number from combo box
    def read_account(self, combo):
        accstr = combo.GetValue().strip().split(" ")[0]
        print "AfpDialog_FiBuchung.read_account:", combo.GetValue(), combo.GetValue().strip().split(" "), accstr
        return Afp_fromString(accstr)
        
    ## adjust grid rows and columns for dynamic resize of window  
    # @param new_rows - new number of rows needed    
    def adjust_grid_rows(self, new_rows = None):
        if not new_rows: new_rows = self.rows
        self.grid_resize(self.grid_buchung, new_rows)
        if self.col_percents:
            grid_width = self.GetSize()[0] - self.fixed_width
            for col in range(self.cols):  
                self.grid_buchung.SetColLabelValue(col, self.col_labels[col])
                if col < len(self.col_percents):
                    self.grid_buchung.SetColSize(col, self.col_percents[col]*grid_width/100)
    
    ## execution in case the OK button ist hit - overwritten ifrom AfpDialog
    def execute_Ok(self):
        #print "AfpDialog_FiBuchung.execute_Ok:", self.data.has_changed()
        if self.data.has_changed():
            clients = []
            rows = self.data.get_value_rows("BUCHUNG", "BuchungsNr,Datum,Konto,Gegenkonto,Betrag,Tab,TabNr")
            #print "AfpDialog_FiBuchung.execute_Ok rows:", rows
            for row in rows:
                if row[0] or not row[5] or not row[6]: continue
                client = self.data.get_client(row[6])
                if client.get_mainselection().lower() != row[5].lower():
                    client = None
                if client:
                    zahl = client.get_payment_values()[1]
                    betrag = None
                    if row[2] in self.bank_accounts or row[2] == self.transfer:
                        betrag = Afp_fromString(row[4])
                    elif row[3] in self.bank_accounts or row[3] == self.transfer:
                        betrag = -Afp_fromString(row[4])
                    if betrag:
                        #print "AfpDialog_FiBuchung.execute_Ok client.set_payment:", zahl, type(zahl), betrag, type(betrag), row[1], client.get_name()
                        client.set_payment_values(zahl + betrag, row[1])
                    clients.append(client)
            self.data.store()
            #print "AfpDialog_FiBuchung.execute_Ok clients:", len(clients) 
            if clients: 
                for client in clients:
                    client.store()

    ## execution in case the Quit button ist hit - overwritten ifrom AfpDialog
    def execute_Quit(self):
        print "AfpDialog_FiBuchung.execute_Quit:", self.data.has_changed()
        if self.data.has_changed(): 
            Ok  = AfpReq_Question("Beim Verlassen gehen die geänderten Daten verloren,".decode("UTF-8"), "sollen sie in einer XML-Datei zwischengespeichert werden?","Daten geändert".decode("UTF-8"))
            if Ok:
                dir = self.data.get_globals().get_value("homedir")
                filename, Ok = AfpReq_FileName(dir, "", "*.xml") 
                typ =  filename[-4:] 
                if not typ == ".xml" or typ == ".XML":  filename += ".xml"
                print "AfpDialog_FiBuchung.execute_Quit filename:", filename
                if Ok and filename:
                    Export = AfpExport(self.data.get_globals(), self.data, filename, self.debug)
                    Export.write_to_file(None, 4) 

    ## identify header of xml-file, 'Afp' and 'SEPA' xml-files are possible
    #@param header - header to be checked
    def identify_file_header(self, header):
        res = "Afp"
        if len(header) > 2:
            tag1 = None
            tag2 = None
            tag3 = None
            inside, outside = Afp_between(header[1],"<",">")
            if inside:
                split = inside[0].split(" ")
                tag1 = split[0]
                if len(split) > 1:
                    sp = split[1].split("=")
                    if len(sp) > 1:
                        tag2 = sp[1][1:-1]
            inside, outside = Afp_between(header[2],"<",">")
            if inside:
                tag3 = inside[0]
            #print "identify_header:", tag1, tag2, tag3
            if tag1 == "Document" and tag2 == "urn:iso:std:iso:20022:tech:xsd:pain.008.001.02" and tag3 == "CstmrDrctDbtInitn":
                res = "SEPA"
        return res
    ## return tags to be used to interpret SEPS files   
    def generate_sepa_tags(self):
        valid_tags = ["DrctDbtTxInf", "GrpHdr"]
        value_tags = ["EndToEndId", "InstdAmt", "MndtId", "DtOfSgntr", "BIC", "Nm", "IBAN", "Ustrd", "NbOfTxs", "CtrlSum"]
        interpreter = "AfpFinance.AfpFiRoutines.AfpFinance_SEPATagInterpreter"
        return valid_tags, value_tags, interpreter

    ## get status of account
    #@ param kt - accountnumber to be checked
    def get_acc_stat(self, kt):
        status = None
        if kt in self.bank_accounts:
            status = "bank"
        elif kt in self.expense_accounts:
            status = "ex"
        elif kt in self.revenue_accounts:
            status = "rv"
        elif kt == self.tranfer:
            status = "transfer"
        return status
        
    ## return selected row from grid
    def get_selected_row(self):
        selected = None
        if not self.grid_row_selected is None:
            selected = self.grid_row_selected
        else: 
            indices = self.grid_buchung.GetSelectedRows()
            if indices: selected = indices[0]
        if not selected is None:
            last = len(self.grid_ident)
            if selected >= last or selected >= self.rows:
                selected = None
        return selected
        
    ## generate storno transaction
    #@param index - index of selected row
    def gen_storno_transaction(self, index):
        sel = self.data.get_selection("BUCHUNG")
        row = Afp_copyArray(sel.get_values(None, index)[0])
        print "AfpDialog_FiBuchung.gen_storno_transaction: row",  row
        if not row[10] == "Storno":
            sel.set_value("Art", "Storno", index)
            row[0] = None
            row[7] = -row[7]
            row[9] = "Storno " + Afp_toString(row[9])
            row[10] = "Storno"
            row[17] = self.data.get_globals().today()
            sel.add_row(row)

    ## event handler for resizing window
    def On_ReSize(self, event):
        height = self.GetSize()[1] - self.fixed_height
        new_rows = int(height/self.grid_buchung.GetDefaultRowSize())
        #print "AfpDialog_FiBuchung..Resize:", size, height, self.row_height, self.rows, self.new_rows
        self.adjust_grid_rows(new_rows)
        #self.Pop_grid(True)
        event.Skip()   
    
    ## Event handler for checking accounts
    def Check_Konten(self, event):
        if self.debug: print "AfpDialog_FiBuchung Event handler `Check_Konten'"
        object = event.GetEventObject()
        name = object.GetName()
        value = self.read_account(object)
        #print "AfpDialog_FiBuchung.Check_Konten:", name, value
        if name == "Soll" and value:
            if value in self.expense_accounts:
                self.combo_Haben.SetSelection(0)
            else:
                self.combo_Haben.SetSelection(len(self.bank_accounts) + 1) 
        elif value:
            if value in self.revenue_accounts:
                self.combo_Soll.SetSelection(0)
            else:
                self.combo_Soll.SetSelection(len(self.bank_accounts) + 1) 
         
    ## Event handler for checking date
    def Check_Datum(self, event):
        if self.debug: print "AfpDialog_FiBuchung Event handler `Check_Datum'"
        object = event.GetEventObject()
        dat = object.GetValue()
        if object.GetName() == "Datum":
            if self.last_date:
                datum = Afp_ChDatum(dat, False, Afp_fromString(self.last_date))
            else:
                datum = Afp_ChDatum(dat)
            self.last_date = datum
        else:
            datum = Afp_ChDatum(dat)
        if datum:
            object.SetValue(datum)
    
    ## Event handler for changing statement of account
    def On_Change_Auszug(self, event):
        if self.debug: print "AfpDialog_FiBuchung Event handler `On_Change_Auszug'"
        print "AfpDialog_FiBuchung Event handler `On_Change_Auszug' not implemented!"
 
    ## Event handler to add financial transaction to SelectionList
    def On_Add(self, event):
        if self.debug: print "AfpDialog_FiBuchung Event handler `On_Add'"
        accdata = {}
        accdata["Datum"] = Afp_fromString(self.text_Datum.GetValue())
        beleg = self.text_Beleg.GetValue()
        accdata["Beleg"] = beleg
        beleg = Afp_fromString(beleg)
        accdata["BelegDatum"] = Afp_fromString(self.text_BDatum.GetValue())
        accdata["Reference"] = self.text_Auszug.GetValue()
        accdata["Konto"] = self.read_account(self.combo_Soll)
        accdata["Gegenkonto"] = self.read_account(self.combo_Haben)
        accdata["Betrag"] = Afp_fromString(self.text_Betrag.GetValue())
        accdata["Bem"] = self.text_Text.GetValue()
        accdata["Art"] = self.combo_Vorgang.GetValue()
        soll = self.get_acc_stat(accdata["Konto"] )
        haben = self.get_acc_stat(accdata["Gegenkonto"]) 
        if accdata["Art"] == "-automatisch-":
            if soll == "bank" or haben == "bank":
                 accdata["Art"] = "Zahlung"
            elif soll == "transfer" or haben == "transfer" or soll == haben:
                accdata["Art"] = "Zahlung intern"
            else:
                accdata["Art"] = "intern"
        if "TabNr" in self.values and "Tab" in self.values:
            accdata["Tab"] = self.values["Tab"]
            accdata["TabNr"] = self.values["TabNr"]
        if "KundenNr" in self.values:  accdata["KundenNr"] = self.values["KundenNr"]
        print "AfpDialog_FiBuchung.On_Add:", accdata
        selected = self.get_selected_row()
        Storno = False
        Change = False
        if not selected is None:
            if self.grid_ident[selected]:
                Storno = AfpReq_Question("Die ausgewählte Buchung ist schon eingetragen und kann nicht überschrieben werden!".decode("UTF-8"), "Soll eine Stornierungsbuchung mit einer neuen Buchung zusammen erstellt werden?".decode("UTF-8"), "Buchung überschreiben?".decode("UTF-8"))
            else:
                Change = AfpReq_Question("Es ist eine Buchung ausgewählt".decode("UTF-8"), "Soll diese überschrieben werden?".decode("UTF-8"), "Buchung überschreiben?".decode("UTF-8"))
        if accdata["Datum"]  and accdata["Konto"]  and accdata["Gegenkonto"]  and accdata["Betrag"]:
            if Storno: 
                self.gen_storno_transaction(selected)
            if Change:
                self.data.set_data_values(accdata, "BUCHUNG", selected)
            else:
                self.data.add_direct_transaction(accdata)
            self.Pop_Buchung()
            self.Pop_Auszug()
            self.text_Text.SetValue("")
            self.text_Betrag.SetValue("")
            self.values = {}
            self.label_Vortext.SetLabel("")
            if (soll == "bank" or haben == "bank") and (soll == "transfer" or haben == "transfer"):
                if soll == "transfer":
                    self.combo_Haben.SetValue(self.combo_Soll.GetValue())
                    self.combo_Soll.SetValue("")
                else:
                    self.combo_Soll.SetValue(self.combo_Haben.GetValue())
                    self.combo_Haben.SetValue("")
                beleg = None
            else:
                self.combo_Soll.SetValue("")
                self.combo_Haben.SetValue("")
            if accdata["Konto"] == self.transfer:
                beleg = None
            if beleg:
                self.text_Beleg.SetValue(Afp_toString(beleg + 1))
            if not self.is_editable():
                self.Set_Editable(True)
        else:
            AfpReq_Info("Datum, Soll-, Habenkonto und Betrag müssen zur Übernahme eingegeben werden!".decode("UTF-8"),"Bitte fehlende Einträge nachholen!".decode("UTF-8"))
        event.Skip()
             
    ## Event handler for filling data from row into entry fields
    def On_Adopt(self, event = None):
        if self.debug: print "AfpDialog_FiBuchung Event handler `On_Adopt'"
        index = self.get_selected_row()
        if not index is None:
            row = self.data.get_value_rows("Buchung", None, index)[0]
            print "AfpDialog_FiBuchung.On_Adopt:", row
            data = {}
            data["Datum"] = row[1]
            data["Soll"] = row[2]
            data["Haben"] = row[4]
            data["Beleg"] = row[6]
            data["Betrag"] = row[7]
            if row[8]:
                data["KundenNr"] = row[8]
            data["Text"] = row[9]
            data["Vorgang"] = row[10]
            data["BDatum"] = row[11]
            if row[12] and row[13]:
                data["Tab"] = row[12]
                data["TabNr"] = row[13]
                client = self.data.get_client(row[13])
                if client:
                    data["LVortext"] = Afp_stripSpaces(client.line())
            elif row[8]:
                adresse = AfpAdresse(self.data.get_globals(), row[8])
                data["LVortext"] = adresse.get_name(True)
            self.values = {}
            self.Pop_entries(data)
        if event: event.Skip()

   ## Event handler to remove account transaction
    def On_Delete(self, event):
        if self.debug: print "AfpDialog_FiBuchung Event handler `On_Delete'"
        index = self.get_selected_row()
        if not index is None:
            Storno = False
            if self.grid_ident[index]:
                Storno = AfpReq_Question("Buchung ist schon eingetragen und kann nicht mehr gelöscht werden!".decode("UTF-8"), "Soll eine Stornierungsbuchung erstellt werden?".decode("UTF-8"), "Buchung stornieren?")
            print "AfpDialog_FiBuchung.On_Delete: index", index, Storno
            if Storno:
                self.gen_storno_transaction(index)
                self.Pop_Buchung()
            else:
                self.data.delete_row("BUCHUNG", index)
                self.grid_buchung.DeleteRows(index)
                self.grid_ident.pop(index)
            self.Pop_Auszug()
            if not self.is_editable():
                self.Set_Editable(True)
        else: 
            AfpReq_Info("Aktion kann nicht durchgeführt werden,".decode("UTF-8"), "bitte die Buchung auswählen, die gelöscht werden soll!".decode("UTF-8"))
        if event: event.Skip()
        
    ## Event handler for left click on grid
    def On_LClick(self, event):
        if self.debug: print "AfpDialog_FiBuchung Event handler `On_LClick'"
        self.grid_row_selected = event.GetRow()
        event.Skip()

   ## Event handler for double click on grid
    def On_DClick(self, event):
        if self.debug: print "AfpDialog_FiBuchung Event handler `On_DClick'"
        self.grid_row_selected = event.GetRow()
        self.On_Adopt()
        event.Skip()
        
   ## Event handler to add payment data to financial transactions
    def On_Vorgang(self, event=None):
        if self.debug: print "AfpDialog_FiBuchung Event handler `On_Vorgang'"
        client = AfpFinance_getZahlVorgang(self.data.get_globals(), "EventNr", 1)
        print "AfpDialog_FiBuchung.On_Vorgang:", client
        if client:
            data = {}
            preis, zahlung, dat = client.get_payment_values()
            if zahlung:
                data["Betrag"] = preis - zahlung
            else:
                data["Betrag"]  = preis
            if client.is_cancelled(): 
                data["Betrag"] *= -1
            if self.read_account(self.combo_Soll) == self.transfer:
                soll = self.transfer
            else:
                soll = self.bank
            data["Soll"] = Afp_toString(soll)
            data["Haben"] = client.get_value("ErloesKt.EVENT")
            data["Vorgang"] = "Zahlung"
            data["LVortext"] = Afp_stripSpaces(client.line())
            selection = None
            agent = client.get_value("Agent")
            if agent:
                data["KundenNr"] = agent
                selection = "Agent"
            else:
                data["KundenNr"] = client.get_value("KundenNr")
            data["Text"] = "Zahlung: " + client.get_name(selection)
            data["Tab"] = client.get_mainselection()
            data["TabNr"] = client.get_value()
            self.Pop_entries(data)
        if event: event.Skip()
        
   ## Event handler to load data from file
    def On_Load(self, event=None):
        if self.debug: print "AfpDialog_FiBuchung Event handler `On_Load'"
        ok = False
        datum = self.text_Datum.GetValue()
        beleg = self.text_Beleg.GetValue()
        auszug = self.text_Auszug.GetValue() 
        if not (datum and beleg and auszug):
            AfpReq_Info("Bitte Buchungsdatum, Belegnummer und Auzug angeben!","Lesevorgang wird abgebrochen.", "Info")
        else: 
            globals = self.data.get_globals()
            dir = globals.get_value("archivdir")
            fname, ok = AfpReq_FileName(dir , "Bitte XML Importfile auswählen!".decode("UTF-8"), "*.xml", True)
            if ok and fname:
                imp = AfpImport(globals,fname, self.debug)
                header = imp.get_file_header()
                ident = self.identify_file_header(header)
                if ident == "SEPA":
                    valid_tags, value_tags, interpreter = self.generate_sepa_tags()
                    para = "\"" + datum + "\", " + Afp_toString(self.bank) + ", " + Afp_toString(self.transfer) + ", " + Afp_toString(self.revenue_accounts[0]) + ", " + beleg + ", \"" + auszug + "\", \"Verein\"" 
                    imp.customise(valid_tags, value_tags, interpreter, para)
        if ok:
            datas = imp.read_from_file()   
            self.data.data_absorber("BUCHUNG", datas[0] )
            self.Pop_Buchung()
            self.Pop_Auszug()
            beleg = Afp_fromString(self.text_Beleg.GetValue())
            if beleg:
                self.text_Beleg.SetValue(Afp_toString(beleg + 1))
            self.Set_Editable(True)
        #print "AfpDialog_FiBuchung.On_Load data:", self.data.view()
        if event: event.Skip()
        
   ## Event handler to get address for transaction
    def On_Adresse(self, event=None):
        if self.debug: print "AfpDialog_FiBuchung Event handler `On_Adresse'"
        KNr  = AfpLoad_AdAusw(self.data.get_globals(), "ADRESSE", "Name", "", None, None, True)
        if KNr:
            adresse = AfpAdresse(self.data.get_globals(), KNr)
            text = self.text_Text.GetValue()
            if text: text += " - "
            data = {"KundenNr": KNr, "Text": text + adresse.get_name(True), "LVortext": adresse.get_name(True)}
            self.Pop_entries(data)
        if event: event.Skip()
 
## loader routine for Finance dialog handling  \n
# @param globals - global values, including mysql connection
# @param parlist - if given, parameterlist for AfpFinance creation
# @param factory - if given, client factory for financial transactions
def AfpLoad_FiBuchung(globals, parlist = None, factory = None):
    data = AfpFinance(globals, parlist)
    data.set_key_generation(False)
    if factory:
        data.add_client_factory(factory)
    if globals.get_value("multiple-transaction-mandates","Finance"):
        print "AfpLoad_FiBuchung 'multiple-transaction-mandates': Selection of financial mandate is not yet implemented!"
        data.set_period(data.period + "xxmxx")
    data.debug = True
    DiFi= AfpDialog_FiBuchung(None)
    DiFi.attach_data(data)
    DiFi.ShowModal()
    Ok = DiFi.get_Ok()
    DiFi.Destroy()
    return Ok 
    
## allow SEPA Direct Debit handling
class AfpDialog_SEPADD(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        self.cols = 5
        self.rows = 10
        AfpDialog.__init__(self,None, -1, "")
        self.grid_ident = None
        self.col_percents = [25, 15, 25, 10, 25]
        self.col_labels = [["Name","BIC","IBAN","Datum","Datei"], ["Name","BIC","IBAN","Art","Betrag"]]
        self.col_label_index = 0
        self.xml_data_loaded = False
        self.grid_row_selected = None
        self.clients = None
        self.newclients = None
        #self.xml_background = wx.Colour(255,255,255)
        self.xml_background = wx.Colour(192, 220, 192)
        self.fixed_width = 80
        self.fixed_height = 80
        self.SetSize((574,410))
        self.SetTitle("SEPA Lastschrift")
        self.Bind(wx.EVT_SIZE, self.On_ReSize)
        #self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
        
    ## set up dialog widgets      
    def InitWx(self):
        self.label_Label = wx.StaticText(self, 1, label="Verwaltung des SEPA Lastschriftmandate für".decode("UTF-8"), name="LLabel")
        self.label_Vorname = wx.StaticText(self, 1, label="", name="Vorname")
        self.labelmap["Vorname"] = "Vorname.ADRESSE"
        self.label_Name = wx.StaticText(self, 1, label="", name="Name")
        self.labelmap["Name"] = "Name.ADRESSE"
        self.top_line1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line1_sizer.Add(self.label_Name,0,wx.EXPAND)
        self.top_line1_sizer.AddSpacer(10)
        self.top_line1_sizer.Add(self.label_Vorname,0,wx.EXPAND)        
        
        self.label_BIC = wx.StaticText(self, 1, label="BIC:", name="LBIC")
        self.text_BIC =  wx.TextCtrl(self, -1, value="", style=0, name="BIC")
        self.textmap["BIC"] = "Tag#2.Konto"
        self.label_IBAN = wx.StaticText(self, 1, label="IBAN:", name="LIBAN")
        self.text_IBAN =  wx.TextCtrl(self, -1, value="", style=0, name="IBAN")
        self.textmap["IBAN"] = "Tag#1.Konto"
        self.label_Anz = wx.StaticText(self, 1, label="Anz:", name="LAnz")
        self.text_Anz =  wx.TextCtrl(self, -1, value="1", style=0, name="Anz")
        self.textmap["Anz"] = "Tag#3.Konto"
        self.text_Anz.Bind(wx.EVT_KILL_FOCUS, self.On_Change)
        self.top_line2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line2_sizer.Add(self.label_BIC,0,wx.EXPAND)
        self.top_line2_sizer.Add(self.text_BIC,2,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(10)
        self.top_line2_sizer.Add(self.label_IBAN,0,wx.EXPAND)
        self.top_line2_sizer.Add(self.text_IBAN,4,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(10)
        self.top_line2_sizer.Add(self.label_Anz,0,wx.EXPAND)
        self.top_line2_sizer.Add(self.text_Anz,1,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(10)
         
        self.label_Erst = wx.StaticText(self, 1, label="", name="Erst")
        self.label_Folge = wx.StaticText(self, 1, label="Erteilte Lastschriftmandate:", name="Folge")

        self.top_text_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_text_sizer.Add(self.label_Label,0,wx.EXPAND)
        self.top_text_sizer.Add(self.top_line1_sizer,0,wx.EXPAND)
        self.top_text_sizer.Add(self.top_line2_sizer,0,wx.EXPAND)
        self.top_text_sizer.AddSpacer(10)
        self.top_text_sizer.Add(self.label_Erst,0,wx.EXPAND)
        self.top_text_sizer.Add(self.label_Folge,0,wx.EXPAND)
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_sizer.AddSpacer(10)
        self.top_sizer.Add(self.top_text_sizer,1,wx.EXPAND)
        
        self.button_Minus = wx.Button(self, -1, label="&-", size=(50,50), name="Minus")
        self.Bind(wx.EVT_BUTTON, self.On_Deaktivate, self.button_Minus)
        self.button_Plus = wx.Button(self, -1, label="&+", size=(50,50), name="Plus")
        self.Bind(wx.EVT_BUTTON, self.On_AddMandat, self.button_Plus)
        box = wx.StaticBox(self, label="Mandate", size=(60, 212))
        self.right_sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        self.right_sizer.AddStretchSpacer(2)      
        self.right_sizer.Add(self.button_Minus,0,wx.EXPAND)        
        self.right_sizer.AddStretchSpacer(1) 
        self.right_sizer.Add(self.button_Plus,0,wx.EXPAND)               
        self.right_sizer.AddStretchSpacer(2) 
        
        self.grid_mandate = wx.grid.Grid(self, -1, style=wx.FULL_REPAINT_ON_RESIZE, name="Mandate")
        self.gridmap.append("Mandate")
        self.grid_mandate.CreateGrid(self.rows, self.cols)
        self.grid_mandate.SetRowLabelSize(0)
        self.grid_mandate.SetColLabelSize(18)
        self.grid_mandate.EnableEditing(0)
        #self.grid_mandate.EnableDragColSize(0)
        self.grid_mandate.EnableDragRowSize(0)
        self.grid_mandate.EnableDragGridSize(0)
        self.grid_mandate.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)   
        self.grid_mandate.SetColLabelValue(0, "Name")
        self.grid_mandate.SetColLabelValue(1, "Datum")
        self.grid_mandate.SetColLabelValue(2, "BIC")
        self.grid_mandate.SetColLabelValue(3, "IBAN")
        self.grid_mandate.SetColLabelValue(4, "Datei")
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid_mandate.SetReadOnly(row, col)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_CLICK, self.On_LClick, self.grid_mandate)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick, self.grid_mandate)
        #self.Bind(wx.grid.EVT_GRID_CMD_CELL_RIGHT_CLICK, self.On_RClick, self.grid_mandate)

        self.left_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_sizer.Add(self.grid_mandate,1,wx.EXPAND)        
        
        self.button_Load = wx.Button(self, -1, label="&Laden", name="BLoad")
        self.Bind(wx.EVT_BUTTON, self.On_Load, self.button_Load)
        self.lower_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lower_sizer.AddStretchSpacer(2) 
        self.lower_sizer.Add(self.button_Load,5,wx.EXPAND) 
        self.setWx(self.lower_sizer, [2, 5, 1], [1, 5, 2])
       
        # compose sizers
        self.mid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mid_sizer.AddSpacer(10)
        self.mid_sizer.Add(self.left_sizer,1,wx.EXPAND)        
        self.mid_sizer.AddSpacer(10)
        self.mid_sizer.Add(self.right_sizer,0,wx.EXPAND)
        self.mid_sizer.AddSpacer(10)
        self.sizer = wx.BoxSizer(wx.VERTICAL)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.top_sizer,0,wx.EXPAND)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.mid_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.lower_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    ## population routine for mandat grids \n
    def Pop_Mandate(self):
        if self.text_Anz.GetValue() == "":
             self.text_Anz.SetValue("1") 
        rows = []
        raws = None
        if self.xml_data_loaded:
            rows = self.get_client_rows()
        else:
            raws = self.data.get_value_rows("Mandat")
            if raws:
                for raw in raws:
                    adresse = AfpAdresse(self.data.get_globals(), raw[0])
                    row = [adresse.get_name(True), raw[3], raw[4], raw[6], raw[5], raw[-1]]
                    rows.append(row)
        if rows:
            lgh = len(rows)
            if lgh > self.rows:
                self.adjust_grid_rows(lgh)
                self.rows = lgh
            self.grid_ident = []
            for row in range(self.rows):
                for col in range(self.cols): 
                    #print "AfpDialog_SEPADD.Pop_Mandate", row, col
                    if row < lgh:
                        self.grid_mandate.SetCellValue(row, col,  Afp_toString(rows[row][col]))
                    else:
                        self.grid_mandate.SetCellValue(row, col,  "")
                if row < lgh:
                    self.grid_ident.append(rows[row][-1])

    ## populate sum lables if xml data has been loaded
    def Pop_sums(self):
        if self.xml_data_loaded:
            newsum = 0.0
            sum = 0.0
            if self.newclients:
                for client in self.newclients:
                    newsum += client.get_value(self.client_value_field)
            if self.clients:
                for client in self.clients:
                    sum += client.get_value(self.client_value_field)
            newman = " Mandate, Summe "
            if len(self.newclients) == 1: newman = " Mandat, Summe "
            man = " Mandate, Summe "
            if len(self.clients) == 1: man = " Mandat, Summe "
            self.label_Erst.SetLabel("Erstlastschriften: " + Afp_toString(len(self.newclients)) + newman+ Afp_toString(newsum))
            self.label_Folge.SetLabel("Folgelastschriften: " + Afp_toString(len(self.clients)) + man + Afp_toString(sum))

    ## print client nalmes (for debug purpose only)
    def view_clients(self):
        print "AfpDialog_SEPADD.view_clients New:"
        if self.newclients:
            for client in self.newclients:
                print client.get_name()
        print "AfpDialog_SEPADD.view_clients Recur:"
        if self.clients:
            for client in self.clients:
                 print client.get_name()
      
    ## get grid data from clients
    def get_client_rows(self):
        rows = []
        for client in self.newclients:
           rows.append(self.get_client_row(client, True))
        for client in self.clients:
           rows.append(self.get_client_row(client, False))
        return rows
            
   ## get grid data from clients
    def get_client_row(self, client, first):
        KNr = client.get_value("AgentNr")
        if not KNr: KNr = client.get_value("KundenNr")
        bic = self.data.get_client_BIC(KNr)
        iban = self.data.get_client_IBAN(KNr)
        field = self.data.get_client_fieldname("actuel")
        print "AfpDialog_SEPADD.get_client_row:", field, client.get_value(field)
        if first: flag = "Erst"
        else: flag = "Folge"
        return [client.get_name(True), bic, iban, flag, client.get_value(field), client.get_value()]
        
    ## adjust grid rows and columns for dynamic resize of window  
    # @param new_rows - new number of rows needed    
    def adjust_grid_rows(self, new_rows = None):
        if not new_rows: new_rows = self.rows
        self.grid_resize(self.grid_mandate, new_rows)
        if self.col_percents:
            grid_width = self.GetSize()[0] - self.fixed_width
            for col in range(self.cols):  
                self.grid_mandate.SetColLabelValue(col, self.col_labels[self.col_label_index][col])
                if col < len(self.col_percents):
                    self.grid_mandate.SetColSize(col, self.col_percents[col]*grid_width/100)
    
    ## execution in case the OK button ist hit - overwritten ifrom AfpDialog
    def execute_Ok(self):
        if  self.xml_data_loaded:
            ok = AfpReq_Question("SEPA xml-Dateien werden erzeugt", "und entsprechend im Archiv abgelegt!","SEPA xml-Dateien erzeugen!")
            if ok: self.data.execute_xml()
        print "AfpDialog_SEPADD.execute_Ok:", self.xml_data_loaded
        self.data.store()

   
    ## event handler for resizing window
    def On_ReSize(self, event):
        height = self.GetSize()[1] - self.fixed_height
        new_rows = int(height/self.grid_mandate.GetDefaultRowSize())
        #print "AfpDialog_Auswahl.Resize:", size, height, self.row_height, self.rows, self.new_rows
        self.adjust_grid_rows(new_rows)
        #self.Pop_grid(True)
        event.Skip()   
    
    ## Event handler for changing kreditor values
    def On_Change(self, event):
        if self.debug: print "AfpDialog_SEPADD Event handler `On_Change'"
        anz = None
        iban = None
        bic = None
        name = event.GetEventObject().GetName()
        if name == "Anz":
            anz = Afp_fromString(self.text_Anz.GetValue())
        if name == "IBAN":
            iban = Afp_fromString(self.text_IBAN.GetValue())
        if name == "BIC":
            bic = Afp_fromString(self.text_BIC.GetValue())
        if anz or iban or bic:
            self. data.set_creditor_data(bic, iban, anz)
            if self.xml_data_loaded and anz:
                self.On_Load()
        event.Skip()
        
    ## Event handler for left click on grid
    def On_LClick(self, event):
        if self.debug: print "AfpDialog_SEPADD Event handler `On_LClick'"
        self.grid_row_selected = event.GetRow()
        print "AfpDialog_SEPADD.On_LClick:", self.grid_row_selected
        event.Skip()

   ## Event handler for double click on grid
    def On_DClick(self, event):
        if self.debug: print "AfpDialog_SEPADD Event handler `On_DClick'"
        if not self.grid_row_selected is None:
            chg = False
            if self.xml_data_loaded:
                lgh = 0
                if self.newclients: lgh = len(self.newclients)
                if self.grid_row_selected >= lgh:
                    client = self.clients[self.grid_row_selected - lgh]
                    first = False
                else:
                    client = self.newclients[self.grid_row_selected]
                    first = True
                liste = [["Erstlastschrift:", first],["Betrag:", client.get_string_value(self.client_value_field)]]
                typen = ["Check", "Text"]
                result = AfpReq_MultiLine( "Bitte Lastschrifteinzug für ".decode("UTF-8") + client.get_name() + " ändern:".decode("UTF-8"),"" , typen, liste, "Lastschrifteinzug", 300, None)
                if result:
                    if client.get_value(self.client_value_field) != Afp_fromString(result[1]):
                        client.set_value(self.client_value_field, Afp_fromString(result[1]))
                        chg = True
                        if first:
                            self.newclients[self.grid_row_selected] = client
                        else:
                            self.clients[self.grid_row_selected-lgh] = client
                    if first != result[0]:
                        #print "AfpDialog_SEPADD.On_DClick Erstlastschrift:", result[0], first
                        chg = True
                        if first:
                            self.newclients.pop(self.grid_row_selected)
                            self.clients.append(client)
                        else:
                            self.clients.pop(self.grid_row_selected - lgh)
                            self.newclients.append(client)
            else:
                row = self.data.get_value_rows("Mandat","Art,Typ,Gruppe,Bem,KundenNr,Extern",self.grid_row_selected)[0]
                #print "AfpDialog_SEPADD.On_DClick:", row
                text = "Art: " + row[0] + ", Status: " + row[1]
                liste = [["BIC:", row[2]], ["IBAN:", row[3]]]
                adresse = AfpAdresse(self.data.get_globals(), row[4])
                result = AfpReq_MultiLine( "Bitte SEPA-Eintrag für ".decode("UTF-8") + adresse.get_name() + " ändern:".decode("UTF-8"), text, "Text", liste, "SEPA-Eintrag", 300, "An&zeigen")
                if result is None: # extra button pushed
                    Afp_startFile(self.data.get_globals().get_value("archivdir") + row[5], self.data.get_globals(), self.debug)
                elif result:
                    #print "AfpDialog_SEPADD.On_DClick no xml result:", result
                    if result[0] != row[2]:
                        self.data.set_value("Gruppe.Mandat", row[2])
                        chg = True
                    if result[1] != row[3]:
                        self.data.set_value("Bem.Mandat", row[3])
                        chg = True
            if chg:
                self.Pop_Mandate()
                self.Pop_sums()
        event.Skip()

   ## Event handler to load data for SEPA xml file
    def On_Load(self, event=None):
        if self.debug: print "AfpDialog_SEPADD Event handler `On_Load'"
        ok = self.data.prepare_xml()
        if ok: self.clients, self.newclients = self.data.get_clients()
        #print "AfpDialog_SEPADD.On_Load:", ok, self.newclients, self.clients
        if self.clients or self.newclients:
            self.client_value_field = self.data.get_client_fieldname("actuel")
            self.xml_data_loaded = True
            self.SetBackgroundColour(self.xml_background)
            self.col_label_index = 1
            self.Pop_Mandate()
            self.Pop_sums()
            self.adjust_grid_rows()
            self.Set_Editable(True)
        if event: event.Skip()

    ## Event handler to add SEPA mandate
    def On_AddMandat(self, event):
        if self.debug: print "AfpDialog_SEPADD Event handler `On_AddMandat'"
        clients = self.data.get_possible_clients()
        liste = []
        ident = []
        cnt = 0
        for client in clients:
            liste.append(client.get_name())
            ident.append(cnt)
            cnt += 1
        index, Ok = AfpReq_Selection(clients[0].get_identification_string() + " auswählen,".decode("UTF-8"),"für die ein SEPA Lastschriftmandat erstellt weden soll.".decode("UTF-8"), liste, "Neue SEPA Lastschrift", ident)
        print  "AfpDialog_SEPADD.On_AddMandat:", clients[index].get_name()
        if Ok: 
            client = clients[index]
            if client.get_value("AgentNr"):
                name = client.get_name("False","Agent")
                Ok = AfpReq_Question("SEPA Lastschriftmandat für ".decode("UTF-8") + name + " erstellen?","","Neues SEPA Lastschriftmandat")
        if Ok:
            sepa = AfpFinance_addSEPA(self.data, client)
            if sepa:
                self.data = sepa
                self.Pop_Mandate()
                self.Set_Editable(True)
        event.Skip()
        
   ## Event handler to deaktivare SEPA mandate
    def On_Deaktivate(self, event):
        print "AfpDialog_SEPADD Event handler `On_Deaktivate'"
        indices = self.grid_mandate.GetSelectedRows()
        if not indices and not self.grid_row_selected is None:
            indices = [self.grid_row_selected]
        last = len(self.grid_ident)
        selected = True
        if last < self.rows:
            selected = False
            for ind in indices:
                if ind < last: selected = True
        if selected:
            self.Set_Editable(True)
            if self.xml_data_loaded:
                print "AfpDialog_SEPADD.On_Deaktivate: XML Data loaded:", self.grid_row_selected, self.grid_mandate.GetSelectedRows()
                lgh = 0
                if self.newclients: lgh = len(self.newclients)
                if self.grid_row_selected >= lgh:
                    self.clients.pop(self.grid_row_selected - lgh)
                else:
                    self.newclients.pop(self.grid_row_selected)
            else:
                indices.sort(reverse=True)
                print "AfpDialog_SEPADD.On_Deaktivate: indices", indices
                for ind in indices:
                    if ind < last:  
                        newdata = {"Typ": "Inaktiv"}
                        print "AfpDialog_SEPADD.On_Deaktivate set Inaktiv:", ind, newdata, self.data.is_debug()
                        self.data.set_data_values(newdata, "Mandat", ind)
                        self.grid_mandate.DeleteRows(ind)
                        self.grid_ident.pop(ind)
        else: 
            if self.xml_data_loaded: 
                AfpReq_Info("Aktion kann nicht durchgeführt werden,".decode("UTF-8"), "bitte den Eintrag auswählen, für den kein Einzug ausgeführt werden soll!".decode("UTF-8"))
            else: 
                AfpReq_Info("Aktion kann nicht durchgeführt werden,".decode("UTF-8"), "bitte das Mandat auswählen, dass deaktiviert werden soll!".decode("UTF-8"))
        event.Skip()

## loader routine for SEPA dialog handling  \n
# @param data - SelectionList data where sepa direct debit is handled for
# @param fields - dictionary with field names to be used to extract debits from clients
# - "regular" - field for regular payment per year
# - "extra" - field for extra payment for this year in first draw
# - "total" - field where total payment for this year  is hold
# - "actuel" - field where the payment amount is written to
# @param filename - name of xml-file in sourcedir to be used for output
def AfpLoad_SEPADD(data, fields = None, filename = None):
    DiSepa = AfpDialog_SEPADD(None)
    sepa = AfpSEPADD(data, fields, filename, data.is_debug())
    DiSepa.attach_data(sepa)
    DiSepa.ShowModal()
    Ok = DiSepa.get_Ok()
    DiSepa.Destroy()
    return Ok 