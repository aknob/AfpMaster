#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFinance.AfpFiDialog
# AfpFiDialog module provides classes and routines needed for user interaction of finance handling and accounting,\n
#
#   History: \n
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
from AfpBase.AfpBaseAdRoutines import AfpAdresse
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