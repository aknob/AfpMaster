#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpFinance.AfpFiDialog
# AfpFiDialog module provides classes and routines needed for user interaction of finance handling and accounting,\n
#
#   History: \n
#        20 Jan. 2025  - enhancement for multi-use of AfpDialog_FiBuchung - Andreas.Knoblauch@afptech.de 
#        20 Nov. 2024 - changes for python 3.12 - Andreas.Knoblauch@afptech.de 
#        19 Okt. 2024 - direct use of purpose in AfpDialog_SEPA - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        13 June 2020 - add incoming and outgoing invoice dialog- Andreas.Knoblauch@afptech.de
#        10 July 2019 - add direct accounting dialog- Andreas.Knoblauch@afptech.de
#        08 May 2019 - inital code generated - Andreas.Knoblauch@afptech.de

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

import AfpBase
from AfpBase import AfpUtilities, AfpBaseDialog, AfpBaseDialogCommon, AfpBaseAdRoutines
from AfpBase.AfpUtilities import AfpStringUtilities
from AfpBase.AfpUtilities.AfpStringUtilities import *
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_sortSimultan
from AfpBase.AfpBaseDialog import *
from AfpBase.AfpBaseDialogCommon import AfpLoad_editArchiv
from AfpBase.AfpBaseFiDialog import AfpFinance_getZahlVorgang, AfpFinance_get_ZahlSelectors, AfpLoad_DiFiZahl
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAusw, AfpLoad_AdAttAusw
import AfpFinance
from AfpFinance import AfpFiRoutines
from AfpFinance.AfpFiRoutines import *

## Routine to add SEPA direct debit mandat to client or sepa object
# @param client - client data where SEPA should be used for
# @param fname - if given, name of file to be added
# @param sepa - if given, sepa data where SEPA mandat should be used for
def AfpFinance_addSEPAdd(client, fname = None, sepa = None ):
    result = False
    if fname is None:
        dir = client.get_globals().get_value("docdir")
        fname, ok = AfpReq_FileName(dir, "SEPA Einzugsermächtigung für " + client.get_name() ,"", True)
        #print ("AfpFinance_addSEPAdd:", fname, ok)
        if ok:
            Afp_startFile(fname, client.get_globals(), client.is_debug(), True)
        else:
            ok = AfpReq_Question("Keine Datei ausgewählt,", "SEPA Mandat trotzdem erzeugen?")
            if ok:
                fname = "No-Scan.txt"
            else:
                fname = None
    if fname:
        date = Afp_dateString(fname)
        liste = [["Erteilungsdatum:", Afp_toString(date)],  ["BIC:",""], ["IBAN:",""]]
        check = False
        while not check :
            result = AfpReq_MultiLine("Neues SEPA-Lastschriftmandat mit der folgenden Datei erzeugen:", fname, "Text", liste, "SEPA-Lastschriftmandat", 500)
            if result:
                check_bic = Afp_checkBIC(result[1])
                check_iban = Afp_checkIBAN(result[2])
                check = check_bic and check_iban
                if not check :
                    liste[0][1] = result[0]
                    liste[1][1] = result[1]
                    liste[2][1] = result[2]
            else:
                check = True
        if result:
            datum = Afp_fromString(Afp_ChDatum(result[0]))
            if sepa:
                sepa.add_mandat_data(client, fname, datum, result[1], result[2].replace(" ",""))
                return sepa
            else:
                client.add_sepa_data(fname, datum, result[1], result[2].replace(" ",""))
                return client
    return None
    
## Routine to get SEPA creditor transfer data
# @param KNr - address identifier for client
# @param input - dictionary for already set values: {"Name": , "IBAN": , "BIC": , "Betrag": , "Zweck": } 
def AfpFinance_getSEPAct(globals, KNr, input = None):
    check_iban = False
    check_bic = False
    if input is None or not "Name" in input or not "IBAN" in input or not "BIC" in input:
        if input is None: input = {}
        adresse = AfpAdresse(globals, KNr)
        if not "Name" in input: input["Name"] = adresse.get_name()
        if not "IBAN" in input or not "BIC" in input:
            adresse.selects["ADRESATT"][1] = "Attribut = \"Bankverbindung\" AND KundenNr = KundenNr.ADRESSE"
            rows = adresse.get_value_rows("ADRESATT","Tag")
            #print "AfpFinance_getSEPAct bankaccounts:", rows
            bank = ","
            if len(rows) > 1:
                if "IBAN" in input and not "BIC" in input:
                    for row in rows:
                        if input["IBAN"] in row:
                            bank = row
                else:
                    bank = rows[1][0]
            elif len(rows) == 1:
                bank = rows[0][0]
            iban,bic = bank.split(",")
            if not "IBAN" in input: input["IBAN"] = iban
            if not "BIC" in input: input["BIC"] = bic
            if bank == ",": check_bank = True
        #if not "Zweck" in input: input["Zweck"] = adresse.get_name(True)
    if not "Betrag" in input: input["Betrag"] = ""
    if not "Zweck" in input: input["Zweck"] = ""
    if  input["IBAN"] == "": check_iban = True
    if  input["BIC"] == "": check_bic = True
    liste = [["Name:", input["Name"]], ["IBAN:", input["IBAN"]], ["BIC:", input["BIC"]], ["Betrag:", input["Betrag"]], ["Zweck:", input["Zweck"]]]
    client = None
    result = None
    while result is None: 
        result = AfpReq_MultiLine( "Neue Überweisung, bitte Daten eingeben:", "", "Text", liste, "Überweisung", 350, "Vorgang")
        #print ("AfpFinance_getSEPAct result:", result)
        if result is None: # Vorgang button pressed
            selectors = AfpFinance_get_ZahlSelectors(globals, False)  
            #print "AfpFinance_getSEPAct selectors:", selectors
            selector = None
            if len(selectors) > 1:
                sellist = []
                for sel in selectors:
                    sellist.append(selectors[sel].get_label())
                value = AfpReq_MultiLine("Bitte wählen sie die Adresse", "oder den Vorgang für die Überweisung aus.", "Button", sellist, "Auswahl für Überweisung")
                if len(value) > 1:
                    selector = None
                    for i in range(len(value)):
                        if selector: break
                        for sel in selectors:
                            #print("AfpFinance_getSEPAct:", value[i],  sel, selectors[sel].get_label())
                            if selectors[sel].get_label() == value[i]:
                                selector = selectors[sel]
                                break
            else:
                selector = selectors[list(selectors.keys())[0]]
            if selector:
                client= selector.select_client_by_KNr(KNr)
                if client:
                    preis, zahlung, dummy = client.get_payment_values()
                    print("AfpFinance_getSEPAct pay:", preis, zahlung, dummy)
                    liste[3][1] = Afp_toString(preis - zahlung)
                    #liste[4][1] = client.get_string_value("Zustand") + ": " + client.get_string_value("TabNr") + ", " + adresse.get_name(True)
                    liste[4][1] = client.get_payment_text()
                else:
                    result = False
        elif result and (check_iban or check_bic): 
            ok = True
            if check_iban: 
                ok = Afp_checkIBAN(result[1])
            if check_bic:
                ok = ok and Afp_checkBIC(result[2])
            if not ok:
                for i in range(len(result)):
                    liste[i][1] = result[i]
                result = None
            
    #print "AfpFinance_getSEPAct Überweisung:", result, client
    return result, client        

## Handle statements of bank accounts
# @param period - actuel finance period
# @param globals - global value, including mysql connection
# @param data - data in which context this handling takes place
# @param statsel - flag if  statement selection should be used, default: True
def AfpFinance_handleStatements(globals, data, statsel = True):
    res = None
    sdat = None
    konto = None
    wok = True
    period = globals.get_string_value("actuel-transaction-period","Finance")
    if not period:
        period = Afp_toString(globals.today().year)
    if statsel:
        sel = "Typ = \"Bank\" OR Typ = \"Kasse\""
        #print ("AfpFinance_handleStatements sel:", sel) 
        kts = list(map(list, (globals.get_mysql().select("*", sel, "KTNR", "KtNr"))))
        liste = []
        for kt in kts:
            liste.append(Afp_toString(kt[1]) + " " + Afp_toString(kt[0]) + " " + Afp_toString(kt[2]))
        val, ok = AfpReq_Selection("  Bitte Konto auswählen für das ein Auszug bearbeitet werden soll", "", liste)
        if ok and val:
            konto = val.split()[0]
            ktname = Afp_fromString(val.split()[1])
        else:
            wok = False
        while not wok == False:
            #ok, val = AfpFinance_selectStatement(globals.get_mysql(), period)
            wok, val, sdat = AfpFinance_selectStatement(globals.get_mysql(), period, konto, ktname)
            dat = ""
            #print ("AfpFinance_handleStatements:", ok, val, sdat)
            parlist = None
            if wok:
                parlist =  {"Auszug": val}
            elif wok is None:
                if val:
                    auszug = val[0]
                    saldo = Afp_toString(val[1])
                else:
                    auszug = ""
                    saldo = ""
                parlist = AfpFinance_modifyStatement(period, konto, ktname, auszug, saldo, dat)
                if parlist:
                    if "Period" in parlist: period = parlist["Period"]
                    if sdat:
                        fname, ok = AfpReq_FileName(globals.get_value("docdir"), "Importdatei wählen", "*.csv", True)
                        if wok and fname:
                            parlist["Importfile"] = fname
                            parlist["Importstart"] = sdat
                    else:
                        wok = False
            if parlist:
                no_strict = globals.get_value("no_strict_accounting","Finance")
                if no_strict: 
                    parlist["disable"] = "strict_accounting"
                res = AfpLoad_FiBuchung(globals, period, parlist)
    else:
        parlist = {"Period":period} 
        disable = "display_stat"
        no_strict = globals.get_value("no_strict_accounting","Finance")
        if no_strict: 
            disable += ",strict_accounting"
        parlist["disable"] = disable
        res = AfpLoad_FiBuchung(globals, period, parlist)
    return  res

## Routine to add SEPA direct debit mandat to sepa object
# @param mysql - sql connection to database
# @param period - period where statements should be selected for
# @param konto - account for which statement should be selected
# @param ktname - name of account for which statement should be selected
# @param new - flag if line for new statement should be added
def AfpFinance_selectStatement(mysql, period, konto , ktname , new = False):
    period = Afp_toString(period)
    sel = "Period = \"" + period + "\""
    if konto:
        where = "KtNr = " + konto + " AND NOT Auszug = \"SALDO\"" 
        text = " für das Konto " + konto + " " + ktname
    else:
        where = "NOT Auszug = \"SALDO\"" 
        ktname = "BAR"
        text = ""
    lgh = len(ktname)
    #print ("AfpFinance_selectStatement sel:", sel, where) 
    raws = list(map(list, mysql.select("*", sel, "AUSZUG", "Auszug", None, where)))
    #print ("AfpFinance_selectStatement raws:", raws)
    rows = []
    saldo = 0.0
    dat = None
    anr = 0
    if raws:
        for raw in raws:
            if raw[0] != "SALDO":
                rows.append(raw[0] + " " + Afp_toString(raw[1]) + " Anfangssaldo: " + Afp_toString(raw[3]) + " Endsaldo: " + Afp_toString(raw[4]))
                saldo = raw[4]
                dat = raw[1]
                nr = Afp_fromString(raw[0][lgh:])
                if nr > anr: anr = nr
    if not new is None: 
        if new: rows.append("--- Neuen Auszug einlesen ---")
        rows.append("--- Neuen Auszug anlegen ---")
    rows.reverse()
    val, ok = AfpReq_Selection("Bitte Auszug" + text  + " für die Finanzperiode '" + period + "' auswählen:", "", rows)
    #print "AfpFinance_selectStatement select:",  ok, val
    if ok and val[:16] == "--- Neuen Auszug":
        if val == "--- Neuen Auszug einlesen ---":
            if dat is None:
                text,ok = AfpReq_Date("Bitte Datum für Importstart eingeben:","")
                if ok and text:
                    dat = Afp_fromString(text)
            return None, saldo, dat
        else:
            auszug = ktname + Afp_toIntString(anr + 1, 5 - lgh)
            return None, [auszug, saldo], None
    else:
        return ok, val.split()[0], None
## modify statement data
# all entries are 'strings' please
# @param period - period where statements should be selected for
# @param konto - account for statement
# @param ktname - name of account for statement
# @param auszug - suggested name of statement
# @param saldo - balance at startdate of the statement
# @param dat - date when statement has benn drawn
def AfpFinance_modifyStatement(period, konto, ktname, auszug, saldo, dat):
    liste = [["Auszug:",auszug], ["Anfangssaldo:", saldo], ["Datum:", dat]]
    if period: liste = [["Periode:", period]] + liste
    result = AfpReq_MultiLine( "  Buchungseingabe für das Konto " + konto + " " + ktname + ".","  Bitte folgende Auszugdaten eigeben:", "Text", liste, "Auszug", 300)
    parlist = None
    if result:
        parlist = {}
        plus = 0
        if period: 
            plus = 1
            if result[0]:
                parlist["Period"] = result[0]
        if result[plus]:
            parlist["Auszug"] = Afp_fromString(result[plus])
        if result[plus + 1]:
            parlist["Saldo"] = Afp_fromString(result[plus + 1])
        if result[plus + 2]:
            parlist["Datum"] = Afp_fromString(Afp_ChDatum(result[plus + 2]))
    return parlist
    
## allow direct accounting
class AfpDialog_FiBuchung(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        self.cols = 7
        self.rows = 10
        self.col_percents = [13, 10, 10, 15, 10, 21, 21]
        self.col_labels = ["Datum","Soll","Haben","Betrag","Beleg", "Name", "Bem"]
        AfpDialog.__init__(self,None, -1, "")
        self.active = False
        self.grid_ident = None
        self.grid_indices = None
        self.disabled = None
        self.client_factories = None
        self.revenue_accounts = None
        self.expense_accounts = None
        self.internal_accounts = None
        self.bank = None
        self.bank_selection = 0
        self.transfer =  None
        self.soll_default = None
        self.haben_default  = None
        self.last_date = None
        self.import_line = None
        self.keep_import_line = None
        self.adopt_data = None
        self.values = {}
        self.KNr = None
        self.Table = None
        self.TabNr = None
        self.sequence = None

        self.grid_row_selected = None
        self.fixed_width = 80
        self.fixed_height = 80
        self.SetSize((574,410))
        self.SetTitle("Direktbuchung")
        self.Bind(wx.EVT_SIZE, self.On_ReSize)
        self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
        
    ## set up dialog widgets      
    def InitWx(self):
        self.label_Label = wx.StaticText(self, 1, label="Direktbuchungen für", name="LLabel")
        self.label_Name = wx.StaticText(self, 1, label="", name="Name")
        self.labelmap["Name"] = "Name.Mandant"
        self.label_Ausz = wx.StaticText(self, 1, label="Auszug:", style=wx.ALIGN_RIGHT, name="LAusz")
        self.label_AzDat = wx.StaticText(self, 1, label="", name="AzDat")
        self.labelmap["AzDat"] = "BuchDat.AUSZUG"
        self.label_AzSaldo = wx.StaticText(self, 1, label="", name="AzSaldo")
        self.labelmap["AzSaldo"] = "EndSaldo.AUSZUG"
        self.label_Import = wx.StaticText(self, 1, label="     ", name="Import")
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
        self.top_line1_sizer.Add(self.label_Import,1,wx.EXPAND)        
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
        self.text_Beleg.Bind(wx.EVT_KILL_FOCUS, self.Changes)
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
        self.text_Betrag.Bind(wx.EVT_KILL_FOCUS, self.Changes)        
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
        self.text_Text=  wx.TextCtrl(self, -1, value="", style=0, name="Text_Dlg")
        self.text_Text.Bind(wx.EVT_KILL_FOCUS, self.Changes)
        self.top_line4_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line4_sizer.Add(self.label_Text,0,wx.EXPAND)
        self.top_line4_sizer.Add(self.text_Text,1,wx.EXPAND)
        self.top_line4_sizer.AddSpacer(10)

        self.label_Vorgang = wx.StaticText(self, 1, label="Vorgang:", size=(70,20), name="LVorgang")
        self.combo_Vorgang = wx.ComboBox(self, -1, value="-automatisch-", choices=["-automatisch-","Zahlung","Zahlung intern","Intern"], style=wx.CB_DROPDOWN, name="Vorgang")
        self.Bind(wx.EVT_COMBOBOX, self.Changes, self.combo_Vorgang)
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
        self.grid_buchung.SetSelectionMode(wx.grid.Grid.GridSelectRows) 
        for col in range(self.cols):
            self.grid_buchung.SetColLabelValue(col, self.col_labels[col])
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
    # @param data - AfpSelectionList which holds data to be filled into dialog widgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        #editable = True
        super(AfpDialog_FiBuchung, self).attach_data( data, new, editable)
        #print ("AfpDialog_FiBuchung.attach_data:", data.auszug)
        self.set_accounts()
        self.set_possible_factories()
        self.reset_first_line()
        BNr = data.gen_next_rcptnr()
        if BNr:
            self.text_Beleg.SetValue(Afp_toNumericString(BNr))

    ## start data import on dialog activation
    def On_Activate(self, event):
        if not self.active:
            if self.data and self.data.has_import_queued():
                self.set_entries_from_import()
            if self.is_disabled("strict_accounting") and self.has_grid_entries():
                self.grid_buchung.SelectRow(0)
                self.On_Adopt()
            if self.is_disabled("display_stat"):
                self.label_Ausz.SetLabel("")
                self.label_AzDat.SetLabel("")
                self.label_AzSaldo.SetLabel("0,00")
                self.labelmap.pop("AzDat")
                self.labelmap.pop("AzSaldo")
            if self.is_disabled("load"):
                self.button_Load.Enable(False)
            if self.is_disabled("transaction"):
                self.button_Vor.Enable(False)
        self.active = True
        event.Skip()

    ## return if gridrows are present
    def has_grid_entries(self):
        entries = False
        if self.data.get_value("Betrag") or self.data.get_value("Betrag") == 0.00:
            entries = True
        return entries
    ## disable certain feature of the dialog
    # @param valnames - comma separated list of names to be disabled
    # at the moment the following entries are supported: 
    # strict_accounting - disable strict accounting
    # display_stat - disable display of statement values in dialig
    # load - disable Load-button ("Laden") 
    # transaction - disable Transaction ("Vorgang") button
    def set_disabled(self, valnames):
        split = valnames.split(",")
        if not self.disabled: self.disabled = []
        for sp in split:
            self.disabled.append(sp)
    ## return if values have been disabled
    # @param valname - name of the value to be checked
    def is_disabled(self, valname):
        disable = False
        if self.disabled:
            if valname in self.disabled:
                disable = True
        return disable
    ## return if value is not disabled
    # @param valname - name of the value to be checked
    def is_enabled(self, valname):
        return not self.is_disabled(valname)
    ## reset first line dependent from the data
    def reset_first_line(self):
        period = self.data.get_period()
        auszug = self.data.get_auszug()[0]
        batch = self.data.get_batch()
        main = self.data.get_mainindex()
        if period:
            self.label_Label.SetLabel(self.label_Label.GetLabel() + " '" + period + "':")
        if auszug:
            self.text_Auszug.SetValue(auszug)
            self.text_Auszug.Enable(False)
        elif batch: 
            self.text_Auszug.SetValue(batch)
        if main == "Konto" or main == "Gegenkonto":
            self.label_Ausz.SetLabel("Konto " + self.data.get_value() + "  ")
        elif main == "KundenNr":
            self.label_Ausz.SetLabel(self.data.get_name())
        elif main == "Beleg":
            self.label_Ausz.SetLabel("Beleg " + self.data.get_value() + "  ")
        else:
            self.label_Ausz.SetLabel("Auszug " + self.data.get_string_value("KtNr.AUSZUG") + "  ")
           
        
    ## set all possible clients
    def set_possible_factories(self):
        clients = AfpFinance_get_ZahlSelectors(self.data.get_globals())
        self.client_factories = {}
        for client in clients:
            if clients[client].get_name() != "Storno":
                self.client_factories[clients[client].get_tablename()] = clients[client]
    ## set all available accouts
    def set_accounts(self):
        self.revenue_accounts = self.data.get_accounts("Ertrag")
        self.expense_accounts =self.data.get_accounts("Kosten")
        self.bank_accounts = self.data.get_accounts("Cash")
        self.internal_accounts = self.data.get_accounts("Other")
        self.bank = self.data.get_bank()
        if not self.bank:
            self.bank = self.bank_accounts[0]
        self.bank_selection = self.bank_accounts.index(self.bank)
        self.transfer = self.data.get_transfer()
        solllist = self.data.get_account_lines("Cash,Internal,Kosten")
        habenlist = self.data.get_account_lines("Cash,Internal,Ertrag")
        self.combo_Soll.SetItems(solllist)
        self.combo_Haben.SetItems(habenlist)

    ## set booking from import data
    def set_entries_from_import(self):
        if self.import_line is None:
            self.import_line = self.data.get_import_line()
            if self.import_line:            
                nr, total = self.data.get_import_status()
                self.label_Import.SetLabel("Datenimport: " + Afp_toString(nr) + "/" + Afp_toString(total) )            
                self.adopt_row(self.import_line)
            else:
                self.data.delete_import_data()
                self.label_Import.SetLabel("")
        self.keep_import_line = False

    ## population routine for statement of accouns
    def Pop_Auszug(self):
        print("AfpDialog_FiBuchung.Pop_Auszug:", self.data.get_auszug())
        if self.data.get_auszug()[0]:
            sum = self.data.gen_bank_sum()
            label = self.data.get_string_value("StartSaldo.Auszug")  + "\n" + Afp_toString(sum)
            self.label_AzSaldo.SetLabel(label)
    ## population routine for finanacial transaction grid \n
    def Pop_Buchung(self):
        rows = []
        dates = []
        raws = None
        raws = self.data.get_value_rows("BUCHUNG")
        #print ("AfpDialog_FiBuchung.Pop_Buchung raws:", raws)
        if raws:
            for raw in raws:
                adresse = AfpAdresse(self.data.get_globals(), raw[8])
                row = [raw[1], raw[2], raw[4], raw[7], raw[6], adresse.get_name(True), raw[9], raw[0]]
                rows.append(row)
                #dates.append(raw[1])
                dates.append(Afp_toInternDateString(raw[1]) + Afp_toIntString(raw[6], 5))
            self.grid_indices, rows = Afp_sortSimultan(dates, rows, True)
        #print ("AfpDialog_FiBuchung.Pop_Buchung rows:", rows, len(rows), self.rows)
        #self.data.view()
        if rows:
            lgh = len(rows)
            if lgh > self.rows or lgh > self.grid_buchung.GetNumberRows():
                self.adjust_grid_rows(lgh)
                self.rows = lgh
            self.grid_ident = []
            for row in range(self.rows):
                #print "AfpDialog_FiBuchung.Pop_Buchung matrix:", row, self.rows
                for col in range(self.cols): 
                    #print "AfpDialog_FiBuchung.Pop_Buchung matrix:", row, col, self.grid_buchung.GetNumberRows()
                    if row < lgh:
                        if col == 4:
                            self.grid_buchung.SetCellValue(row, col,  Afp_toNumericString(rows[row][col]))
                        else:
                            self.grid_buchung.SetCellValue(row, col,  Afp_toString(rows[row][col]))
                    else:
                        self.grid_buchung.SetCellValue(row, col,  "")
                if row < lgh:
                    self.grid_ident.append(rows[row][-1])
        #print ("AfpDialog_FiBuchung.Pop_Buchung ident:",  self.grid_ident, self.grid_indices)

    ## populate text an internal values if data has been loaded
    # @param values - dictionary of values to be written into textfields
    def Pop_entries(self, values):
        for entry in values:
            widget = self.FindWindowByName(entry) 
            #print ("AfpDialog_FiBuchung.Pop_entries widgets:", entry, widget, values[entry])
            if widget:
                if entry[0] == "L":
                    widget.SetLabel(Afp_toString(values[entry]))
                else:
                    widget.SetValue(Afp_toString(values[entry]))
            else:
                self.values[entry] = values[entry]
        #print ("AfpDialog_FiBuchung.Pop_entries:", self.values)

    ## read account number from combo box
    def read_account(self, combo):
        accstr = combo.GetValue().strip().split(" ")[0]
        #print "AfpDialog_FiBuchung.read_account:", combo.GetValue(), combo.GetValue().strip().split(" "), accstr
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
                    self.grid_buchung.SetColSize(col, int(self.col_percents[col]*grid_width/100))
    
   ## check if changes are grave for this accounting entry
    def changes_are_grave(self):
        grave = False
        if "Datum" in self.changed_text: grave = True
        #elif "BDatum" in self.changed_text: grave = True
        elif "Soll" in self.changed_text: grave = True
        elif "Haben" in self.changed_text: grave = True
        elif "Betrag" in self.changed_text: grave = True
        #print ("AfpDialog_FiBuchung.changes_are_grave:", grave, self.changed_text)
        return grave
    ## scale the splitting values to given amount
    # @param amount - value to which splitting values should be scaled
    # @param splitting - list of rows, holding splitting values with the value at position [1]
    def scale_splitting(self, amount, splitting):
        sum = 0.0
        for row in splitting:
            sum += row[1]
        csum = 0.0
        for row in splitting:
            value = amount*(row[1]/sum)
            row[1] = float(int(value*100)/100)
            csum += row[1]
        if not csum == amount:
            splitting[0][1] += amount - csum
        return splitting       
    ## generate splitting data depending of accounting information, if necessary
    # @param accdata - dictionary of accountind data possibly to be splitted
    def gen_splitting(self, accdata):
        splitting = None
        sequence = None
        soll = self.get_acc_stat(accdata["Konto"] )
        haben = self.get_acc_stat(accdata["Gegenkonto"]) 
        text = None
        deduct = None
        if "xxx-Deduct" in self.values:
            deduct = self.values["xxx-Deduct"]
        if  "xxx-Split" in self.values:
            splitting = self.values["xxx-Split"]
        if deduct and not splitting:
            if soll == "bank":
                splitting =  [[accdata["Gegenkonto"], accdata["Betrag"], "", "extra"]]
            else:
                splitting =  [[accdata["Konto"], accdata["Betrag"], "", "extra"]]
        #print("AfpDialog_FiBuchung.On_Add splitting:", splitting, self.values)
        if  splitting:
            betrag = accdata["Betrag"]
            if deduct: betrag -= deduct[1]
            splitting = self.scale_splitting(betrag, splitting)
            if deduct: splitting = [deduct] + splitting
        if soll == "bank" and haben == "bank" and soll != "transfer" and haben != "transfer":
            # internal use of transfer to separate receipt-cycles
            text = "Diese Buchung berührt 2 Geldkonten, soll diese Buchung in 2 Buchungen aufgesplittet werden?"
            if accdata["Konto"] == self.bank: 
                haben = "intern"
                splitting = [[accdata["Gegenkonto"], accdata["Betrag"], None ]]
            else:
                soll = "intern"
                splitting = [[accdata["Konto"], accdata["Betrag"], None ]]
            sequence = self.get_next_sequence()
        elif not (soll == "bank" or haben == "bank"):
            if soll == "transfer" or haben == "transfer":
                splitting = None
            else:
                # internal use of direct transfer accounting
                text = "Dies ist eine interne Verrechungsbuchung, soll diese Buchung über das Transferkonto erfolgen?"
                #haben = "intern"
                #splitting = [[accdata["Gegenkonto"], accdata["Betrag"], None ]]
                soll = "intern"
                splitting = [[accdata["Konto"], accdata["Betrag"], None ]]
                sequence = self.get_next_sequence()       
        return splitting, sequence, soll, haben, text       
    
    ## execution in case the OK button ist hit - overwritten from AfpDialog
    def execute_Ok(self):
        if self.debug: print("AfpDialog_FiBuchung.execute_Ok:", self.data.has_changed())
        self.Ok = False
        #print ("AfpDialog_FiBuchung.execute_Ok:", self.grid_ident, self.data.has_changed(), self.data.get_value_length(), self.has_grid_entries())
        if self.has_grid_entries() and self.data.has_changed():
            text1 = "Auszug/Buchungsstapel wurde geändert,"
            text2 = "sollen die Daten in die Buchhaltung übernommen werden?"
            self.Ok  = AfpReq_Question(text1, text2,"Daten übernehmen?")
        if self.Ok:
            if self.is_enabled("strict_accounting") and self.data.get_globals().get_value("additional-transaction-file","Finance"):
                self.execute_Quit(True)
            clients = []
            rows = self.data.get_value_rows("BUCHUNG", "BuchungsNr,Datum,Konto,Gegenkonto,Betrag,Tab,TabNr,Art")
            #print ("AfpDialog_FiBuchung.execute_Ok rows:", rows)
            for row in rows:
                #if row[0] or not row[5] or not row[6]: continue
                if  (row[0] and  self.is_enabled("strict_accounting")) or not row[5] or not row[6]: continue
                #if (row[2] in self.bank_accounts or row[2] == self.tranfer) and (row[3] in self.bank_accounts or row[3] == self.tranfer) continue
                client = None
                new = False
                if clients:
                    for cl in clients:
                        if Afp_fromString(cl.get_value()) == Afp_fromString(row[6]) and cl.get_mainselection().upper() == row[5].upper():
                            client = cl
                            break
                if not client:
                    client = self.get_client(row[5].upper(), row[6])
                    new = True
                if client and client.get_mainselection().upper() != row[5].upper():
                    client = None
                if client and not "extra" in row[7]:
                    #ToDo: client.adapt_payment(row[1], row[2], row[3], row[4]) # the client has to decide whether the payment fits
                    zahl = client.get_payment_values()[1]
                    betrag = None
                    # this is mainly working if only one payment client could be found, ToDo: see above!
                    if row[2] in self.expense_accounts or row[3] in self.revenue_accounts:
                        betrag = Afp_fromString(row[4])
                    elif row[2] in self.revenue_accounts or row[3] in self.expense_accounts:
                        betrag = -Afp_fromString(row[4])
                    #print ("AfpDialog_FiBuchung.execute_Ok Betrag:", new, zahl, betrag, row[1], row[2], row[2] in self.expense_accounts, row[3], row[3] in self.revenue_accounts, row[7], "extra" in row[7] , client.get_name())
                    if betrag:
                        client.set_payment_values(zahl + betrag, row[1])
                if client and new:
                    clients.append(client)
            if self.data.get_batch():
                self.data.update_sums()
            if self.sequence:
                self.data.add_afterburner("BUCHUNG", "self.spread_collection_indicators('BuchungsNr', 'VorgangsNr')")
            self.data.store()
            #print ("AfpDialog_FiBuchung.execute_Ok clients:", len(clients)) 
            if clients: 
                for client in clients:
                    client.store()

    ## execution in case the Quit button ist hit - overwritten from AfpDialog
    # @param store - flag if text for storing should be dispayed in dialog
    def execute_Quit(self, store=False):
        if self.debug: print ("AfpDialog_FiBuchung.execute_Quit:", self.data.has_changed())
        if self.has_grid_entries() and self.data.has_changed(): 
            if store:
                text1 = "Die Daten werden gespeichert,"
                text2 = "sollen sie zusätzlich in einer XML-Datei abgelegt werden?"
            else:
                text1 = "Beim Verlassen gehen die geänderten Daten verloren,"
                text2 = "sollen sie in einer XML-Datei zwischengespeichert werden?"
            Ok  = AfpReq_Question(text1, text2,"Daten geändert")
            if Ok:
                dir = self.data.get_globals().get_value("homedir")
                filename, Ok = AfpReq_FileName(dir, "", "*.xml") 
                typ =  filename[-4:] 
                if not typ == ".xml" or typ == ".XML":  filename += ".xml"
                #print "AfpDialog_FiBuchung.execute_Quit filename:", filename
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
            #print ("AfpDialog_FiBuchung.identify_header:", tag1, tag2, tag3)
            if tag1 == "Document":
                if tag2 == "urn:iso:std:iso:20022:tech:xsd:pain.008.001.02" and tag3 == "CstmrDrctDbtInitn":
                    res = "SEPA-DD"
                if tag2 == "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03" and tag3 == "CstmrCdtTrfInitn":
                    res = "SEPA-CT"
        return res
    ## return tags to be used to interpret SEPA files   
    # @param typ - SEPA typ where tags are created for, possible types: SEPA-DD (default), SEPA-CT
    def generate_sepa_tags(self, typ="SEPA-DD"):
        if typ == "SEPA-CT":
            valid_tags = ["CdtTrfTxInf", "GrpHdr"]
            value_tags = ["EndToEndId", "InstdAmt", "BIC", "Nm", "IBAN", "Ustrd", "NbOfTxs", "CtrlSum"]
            interpreter = "AfpFinance.AfpFiRoutines.AfpFinance_SEPActTagInterpreter"
        else:
            valid_tags = ["DrctDbtTxInf", "GrpHdr"]
            #value_tags = ["EndToEndId", "InstdAmt", "MndtId", "DtOfSgntr", "BIC", "Nm", "IBAN", "Ustrd", "NbOfTxs", "CtrlSum"]
            value_tags = ["EndToEndId", "InstdAmt", "MndtId", "BIC", "Nm", "IBAN", "Ustrd", "NbOfTxs", "CtrlSum"]
            interpreter = "AfpFinance.AfpFiRoutines.AfpFinance_SEPAddTagInterpreter"
        return valid_tags, value_tags, interpreter

    ## get client, if possible
    #@ param table - indicator which clientfactory shoud be used (i.e. tablename)
    #@ param idnr - identificationnumber, which client should be retrieved
    def get_client(self, table, idnr):
        #print ("AfpDialog_FiBuchung.get_client:", self.client_factories, table, idnr)
        if self.client_factories and table in self.client_factories:
            return self.client_factories[table].get_client(idnr)
        else:
            return None
    ## get reference of a given bakaccount
    # @param date - date of entry, this reference if generated for
    # @param ktnr - number of bank account for which the reference has to be delivered
    def get_reference(self, date, ktnr): 
        ktstrg =  Afp_toString(ktnr)  
        ref = Afp_getSpecialAccount(self.data.get_mysql(), ktstrg, "KtNr", "KtName")
        if ref:
            if ktnr != self.data.get_main_bankaccount():
                typ = Afp_getSpecialAccount(self.data.get_mysql(), ktstrg, "KtNr", "Typ")
                if typ == "Cash":
                    intervall = self.data.get_globals().get_value("cash-statement-period", "Finance")
                    if not intervall: intervall = 1
                else:
                    intervall = self.data.get_globals().get_value("bank-statement-period", "Finance")
                    if not intervall: intervall = 3
                ref += Afp_toIntString(Afp_genPeriodExtension(date, intervall), 5-len(ref))
            else:
                row = self.data.get_mysql().execute("SELECT MAX(Auszug) FROM AUSZUG WHERE Period = " + self.data.get_period() + " AND KtNr = " + self.data.get_main_bankaccount() + " AND NOT (AUSZUG = 'SALDO')")
                print ("AfpDialog_FiBuchung.get_reference main:", row)
                ref += Afp_toIntString(Afp_getEndNumber(row) + 1, 5-len(ref))
        return ref
    ## get next sequence number
    # to avoid conflicts with low numbers, 
    # start of sequence is set to 2000, 
    # if already used booking numbers are lower 1000
    def get_next_sequence(self):
        if self.sequence is None:
            if self.data.gen_next_rcptnr() < 1000:
                self.sequence = 2000
            else:
                self.sequence = 0
        self.sequence += 1
        return self.sequence
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
        elif kt == self.transfer:
            status = "transfer"
        return status
        
    ## return selected row from grid
    def get_selected_row(self):
        selected = None
        indices = self.grid_buchung.GetSelectedRows()
        if indices: selected = indices[0]
        if not selected is None:
            if self.grid_ident:
                last = len(self.grid_ident)
            else:
                last = 0
            if selected >= last or selected >= self.rows:
                selected = None
        return selected
        
    ## generate storno transaction
    #@param index - index of selected row
    def gen_storno_transaction(self, index):
        sel = self.data.get_selection("BUCHUNG")
        row = Afp_copyArray(sel.get_values(None, index)[0])
        print("AfpDialog_FiBuchung.gen_storno_transaction: row",  row)
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
        #print "AfpDialog_FiBuchung.Resize:", size, height, self.row_height, self.rows, self.new_rows
        if new_rows > self.rows:
            self.adjust_grid_rows(new_rows)
        else:
            self.adjust_grid_rows()
        event.Skip()   
    
    ## event handler to keep track of changes
    def Changes(self, event):
        object = event.GetEventObject()
        name = object.GetName()
        if not name in self.changed_text:
            check = False
            cat = event.GetEventCategory()
            if cat == 1:
                value = None
                if self.adopt_data: 
                    if name in self.adopt_data: value = self.adopt_data[name]
                    #print ("AfpDialog_FiBuchung.Changes:", value, value, object.GetValue(), Afp_toString(value).strip() == object.GetValue().strip())
                    if (not value and object.GetValue()) or (Afp_toString(value) != object.GetValue()):
                        check = True
            else:
                check = True
            #print ("AfpDialog_FiBuchung.Changes:", name, cat, check)
            if check: self.changed_text.append(name) 
        
    ## Event handler for checking accounts
    def Check_Konten(self, event):
        if self.debug: print("AfpDialog_FiBuchung Event handler `Check_Konten'")
        object = event.GetEventObject()
        name = object.GetName()
        value = self.read_account(object)
        #print ("AfpDialog_FiBuchung.Check_Konten:", name, value)
        #wx.CallAfter(object.SetValue, Afp_toString(value))
        if self.data.get_main_bankaccount() != self.data.get_bank() and not self.data.is_cash():
            if name == "Soll" and value and self.soll_default is None:
                ok = AfpReq_Question("Soll das Konto " + Afp_toString(value) ,"als Standardeintrag im Feld 'Soll' übernommen werden?", "Standardwert")
                if ok: self.soll_default = value
                else:
                    ok = AfpReq_Question("Kein Standardeintrag im Feld 'Soll'" ,"für diese Eingabesequenz?", "Standardwert")
                    if ok: self.soll_default = False
            elif name == "Haben" and value and self.haben_default is None:
                ok = AfpReq_Question("Soll das Konto " + Afp_toString(value) ,"als Standardeintrag im Feld 'Haben' übernommen werden?", "Standardwert")
                if ok: self.haben_default = value
                else:
                    ok = AfpReq_Question("Kein Standardeintrag im Feld 'Haben'" ,"für diese Eingabesequenz?", "Standardwert")
                    if ok: self.haben_default = False
        if not (value == self.transfer) or len(self.bank_accounts) > 1:
            if name == "Soll" and value:
                if not self.read_account(self.combo_Haben) in self.internal_accounts:
                    if value in self.expense_accounts:
                        self.combo_Haben.SetSelection(self.bank_selection)
                    else: 
                        if self.haben_default:
                            self.combo_Haben.SetValue(Afp_toString(self.haben_default))
                        else:
                            self.combo_Haben.SetSelection(len(self.bank_accounts) + len(self.internal_accounts)) 
            elif value:
                if not self.read_account(self.combo_Soll) in self.internal_accounts:
                    if value in self.revenue_accounts:
                        self.combo_Soll.SetSelection(self.bank_selection)
                    else:
                        if self.soll_default:
                            self.combo_Soll.SetValue(Afp_toString(self.soll_default))
                        else:
                            self.combo_Soll.SetSelection(len(self.bank_accounts) + len(self.internal_accounts)) 
        self.Changes(event  )
         
    ## Event handler for checking date
    def Check_Datum(self, event):
        if self.debug: print("AfpDialog_FiBuchung Event handler `Check_Datum'")
        object = event.GetEventObject()
        dat = object.GetValue()
        name = object.GetName() 
        if name == "Datum":
            if self.last_date:
                datum = Afp_ChDatum(dat, False, Afp_fromString(self.last_date))
            else:
                datum = Afp_ChDatum(dat)
            self.last_date = datum
        else:
            datum = Afp_ChDatum(dat)
        if datum:
            object.SetValue(datum) 
            if name == "Datum":
                self.text_BDatum.SetValue(datum)
        self.Changes(event)
    ## filling data from row into entry fields
    # @param row - row fromvalues to be adopted and fillet into the data fields
    def adopt_row(self, row):
        #print ("AfpDialog_FiBuchung.adopt_row row:", row)
        data = {}
        data["Datum"] = row[1]
        data["Soll"] = row[2]
        data["Haben"] = row[4]
        if row[6]: data["Beleg"] = row[6]
        if row[7]: data["Betrag"] = float(row[7])
        if row[8]:
            data["KundenNr"] = row[8]
        data["Text_Dlg"] = row[9]
        if row[10]: data["Vorgang"] = row[10]
        else: data["Vorgang"] = "-automatisch-"
        data["BDatum"] = row[11]
        if row[12] and row[13]:
            client = None
            data["Tab"] = row[12]
            data["TabNr"] = row[13]
            if row[12] in self.client_factories:
                client = self.client_factories[row[12]].get_client(row[13])
            if client:
                data["LVortext"] = client.get_listname()[:4]  + ":" + client.line()
        elif row[8]:
            adresse = AfpAdresse(self.data.get_globals(), row[8])
            data["LVortext"] = adresse.get_name(True)
        if self.text_Auszug.IsEnabled() and row[15] and not "X" in row[15]:
            data["Auszug"] = row[15]
        # no booking data given, apply standard values
        if "Betrag" in data and not (data["Soll"] or data["Haben"]):
            if data["Betrag"] < 0.0:
                if self.soll_default: data["Soll"] = self.soll_default
                else: data["Soll"] = self.data.get_accounts("Kosten")[0]
                data["Haben"] = Afp_toString(self.bank)
                data["Betrag"] *= -1
            else:
                data["Soll"] = Afp_toString(self.bank)
                if self.haben_default: data["Haben"] = self.haben_default
                else: data["Haben"] = self.data.get_accounts("Ertrag")[0]
        self.values = {}
        #print ("AfpDialog_FiBuchung.adopt_row data:", data)
        self.adopt_data = data
        self.Pop_entries(data)
    
    ## Event handler for changing statement of account
    def On_Change_Auszug(self, event):
        if self.debug: print("AfpDialog_FiBuchung Event handler `On_Change_Auszug'")
        auszug = self.text_Auszug.GetValue()
        if auszug:
            konto = self.data.get_bank()
            saldo = ""
            row = self.data.find_value_row(auszug, "Auszug.Auszuege")
            if not row:
                ken = Afp_getStartLetters(auszug)
                nr = Afp_getEndNumber(auszug)
                if nr > 1:
                    old = ken + Afp_toIntString(nr-1,5-len(ken))
                    row = self.data.find_value_row(old, "Auszug.Auszuege")
                    if row:
                        saldo = row[4]
                        konto = row[6]
                #print("AfpDialog_FiBuchung.On_Change_Auszug Mod:", konto, ken, auszug, saldo)
                parlist = AfpFinance_modifyStatement(None, Afp_toString(konto), ken, auszug, Afp_toString(saldo), "")
                if parlist: self.data.set_auszug(parlist["Auszug"], parlist["Datum"], parlist["Saldo"])
            self.Changes(event)
                
    ## Event handler to add financial transaction to SelectionList
    def On_Add(self, event):
        if self.debug: print("AfpDialog_FiBuchung Event handler `On_Add'")
        text = None
        #print("AfpDialog_FiBuchung.On_Add IN:", self.values)
        accdata = {}
        accdata["Datum"] = Afp_fromString(self.text_Datum.GetValue())
        beleg = self.text_Beleg.GetValue()
        accdata["Beleg"] = beleg
        beleg = Afp_fromString(beleg)
        accdata["BelegDatum"] = Afp_fromString(self.text_BDatum.GetValue())
        if not accdata["BelegDatum"]: accdata["BelegDatum"]  = None
        accdata["Reference"] = self.text_Auszug.GetValue()
        accdata["Konto"] = self.read_account(self.combo_Soll)
        accdata["Gegenkonto"] = self.read_account(self.combo_Haben)
        accdata["Betrag"] = Afp_fromString(self.text_Betrag.GetValue())
        accdata["Bem"] = self.text_Text.GetValue()[:250]
        accdata["Art"] = self.combo_Vorgang.GetValue()
        if not (accdata["Datum"]  and accdata["Konto"]  and accdata["Gegenkonto"]  and accdata["Betrag"]):
            AfpReq_Info("Datum, Soll-, Habenkonto und Betrag müssen zur Übernahme eingegeben werden!","Bitte fehlende Einträge nachholen!")
            self.Pop_Buchung()
            return
        # generate possible splitting data, if necessary. All values are initialized    
        splitting, sequence, soll, haben, text = self.gen_splitting(accdata)
        
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
        if "KundenNr" in self.values:  
            accdata["KundenNr"] = self.values["KundenNr"]
        else:
            accdata["KundenNr"] = 0
        #print("AfpDialog_FiBuchung.On_Add splitting:", splitting)
        if  splitting: 
            if not text:
                text = "Der ausgewählte Vorgang enthält eine Splitbuchung, soll diese so durchgeführt werden?"
            text2 = ""
            sum = 0.0
            for sp in splitting:
                text2 += "\n"  + Afp_ArraytoLine(sp)
                sum += sp[1]
            text2 += "\n Gesamtsumme: " + Afp_toString(sum)
            if sum != Afp_fromString(self.text_Betrag.GetValue()):
                text2 += "WARNING: Summe " + Afp_toString(sum) + " entspricht nicht den eingegeben Wert " + self.text_Betrag.GetValue() + "!"
            split = AfpReq_Question(text, text2, "Splitbuchung durchführen?")
            if split:
                if soll == "bank":
                    accdata["Gegenkonto"]  = self.transfer
                else:
                    accdata["Konto"]  = self.transfer
            else:
                splitting = None
        if self.debug: print("AfpDialog_FiBuchung.On_Add:", accdata)
        selected = self.get_selected_row()
        Storno = False
        Change = False
        if  not selected is None: 
            if self.grid_ident[selected]:
                if self.is_enabled("strict_accounting") and self.changes_are_grave():
                    Storno = AfpReq_Question("Die ausgewählte Buchung ist schon eingetragen und kann nicht überschrieben werden!", "Soll eine Stornierungsbuchung mit einer neuen Buchung zusammen erstellt werden?", "Buchung überschreiben?")
                    if not Storno: Change = None
                elif splitting:
                    Change = AfpReq_Question("Die ausgewählte Buchung ist schon eingetragen!", "Soll diese als Eingangsbuchung der Splitbuchung überschrieben werden?", "Buchung überschreiben?")                 
                else:
                    Change = True
            else:
                Change = AfpReq_Question("Es ist eine Buchung ausgewählt", "Soll diese überschrieben werden?", "Buchung überschreiben?")
        #print("AfpDialog_FiBuchung.On_Add Change:", Change, Storno, self.is_enabled("strict_accounting"), selected, self.grid_indices, beleg)
        #print("AfpDialog_FiBuchung.On_Add Change:", Change, accdata)
        #if Change is None or (accdata["Datum"]  and accdata["Konto"]  and accdata["Gegenkonto"]  and accdata["Betrag"]):
        if splitting and sequence:
            accdata["VorgangsNr"] = sequence
        if Storno: 
            self.gen_storno_transaction(self.grid_indices[selected])
        if Change:
            self.data.set_data_values(accdata, "BUCHUNG", self.grid_indices[selected])
        else:
            self.data.add_direct_transaction(accdata)
        if splitting:
            gesamt = accdata["Betrag"]
            bem = accdata["Bem"]
            if soll == "bank":
                accdata["Konto"]  = self.transfer
                if "GktName" in accdata: accdata["KtName"]  = accdata["GktName"]
                konto = "Gegenkonto"
                ktname = "GktName"
            else:
                accdata["Gegenkonto"]  = self.transfer
                if "KtName" in accdata: accdata["GktName"]  = accdata["KtName"]
                konto = "Konto"
                ktname = "KtName"
            if sequence: 
                #print ("AfpDialog_FiBuchung.On_Add sequence:", sequence, accdata, splitting)
                accdata["Reference"] = self.get_reference(Afp_fromString(accdata["Datum"]), splitting[0][0])
                if not accdata["Reference"] : accdata.pop("Reference")
                accdata.pop("Beleg")
            for split in splitting:
                accdata[konto] = split[0]
                accdata[ktname] = ""
                accdata["Betrag"] = split[1]
                if split[2]: accdata["Bem"] = (Afp_toString(split[2]) + " " + bem)[:250]
                else: accdata["Bem"] = bem
                if len(split) > 3: accdata["Art"] = "Zahlung " + split[3]
                else: accdata["Art"] = "Zahlung intern"
                if self.debug:  print ("AfpDialog_FiBuchung.On_Add split:", accdata)
                #print ("AfpDialog_FiBuchung.On_Add split:", accdata, split)
                if Change:
                    cnt = splitting.index(split) + 1
                    self.grid_indices.insert(selected + cnt,  self.grid_indices[selected] + cnt)
                    print ("AfpDialog_FiBuchung.On_Add insert:", accdata, self.grid_indices[selected + cnt] )
                    #self.data.insert_direct_transaction(accdata, self.grid_indices[selected + cnt])
                else:
                    self.data.add_direct_transaction(accdata)
        self.Pop_Buchung()
        self.Pop_Auszug()
        self.text_Text.SetValue("")
        self.text_Betrag.SetValue("")
        self.combo_Vorgang.SetValue("-automatisch-")
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
        if self.data.has_import_queued():
            if not self.keep_import_line:
                self.import_line = None
            self.set_entries_from_import()
        if not splitting and accdata["Konto"] == self.transfer:
            beleg = None
        #if beleg and self.is_enabled("strict_accounting"):
        if beleg:
            beleg = self.data.gen_next_rcptnr()
            self.text_Beleg.SetValue(Afp_toNumericString(beleg))
        if not self.is_editable():
            self.Set_Editable(True)
        event.Skip()
             
    ## Event handler for filling data from row into entry fields
    def On_Adopt(self, event = None):
        if self.debug: print("AfpDialog_FiBuchung Event handler `On_Adopt'")
        index = self.get_selected_row()
        if index is None:
            if self.data.has_import_queued():
                res = AfpReq_MultiLine("   < vorherige Zeile", "   > nächste Zeile", "Button", ["<",">"], "Datenimport Direktwahl")
                #print ("AfpDialog_FiBuchung.On_Adopt:", res)
                if res:
                    self.import_line = None
                    if res[0]: self.data.set_previous_import_line()
                    self.set_entries_from_import()
        else:
            #print ("AfpDialog_FiBuchung.On_Adopt Index:", index, self.grid_indices[index], self.data.get_value_length("Buchung"))
            row = self.data.get_value_rows("Buchung", None, self.grid_indices[index])[0]
            self.adopt_row(row)
            if not self.keep_import_line is None:
                self.keep_import_line = True
        if event: event.Skip()

   ## Event handler to remove account transaction
    def On_Delete(self, event):
        if self.debug: print("AfpDialog_FiBuchung Event handler `On_Delete'")
        index = self.get_selected_row()
        if not index is None:
            Storno = None
            if self.grid_ident[index]:
                Storno = AfpReq_Question("Buchung ist schon eingetragen und kann nicht mehr gelöscht werden!", "Soll eine Stornierungsbuchung erstellt werden?", "Buchung stornieren?")
            #print("AfpDialog_FiBuchung.On_Delete index:", index, Storno)
            if Storno:
                self.gen_storno_transaction(index)
                self.Pop_Buchung()
            elif Storno is None:
                self.data.delete_row("BUCHUNG", self.grid_indices[index])
                self.grid_buchung.DeleteRows(index)
                self.grid_ident.pop(index)
                self.rows -= 1
                #print "AfpDialog_FiBuchung.On_Delete data:", self.data.get_selection("BUCHUNG").data
            self.Pop_Auszug()
            if not self.is_editable():
                self.Set_Editable(True)
        else: 
            AfpReq_Info("Aktion kann nicht durchgeführt werden,", "bitte die Buchung auswählen, die gelöscht werden soll!")
        if event: event.Skip()
        
    ## Event handler for left click on grid
    def On_LClick(self, event):
        if self.debug: print("AfpDialog_FiBuchung Event handler `On_LClick'")
        #self.grid_row_selected = event.GetRow()
        event.Skip()

   ## Event handler for double click on grid
    def On_DClick(self, event):
        if self.debug: print("AfpDialog_FiBuchung Event handler `On_DClick'")
        #self.grid_row_selected = event.GetRow()
        self.On_Adopt()
        event.Skip()
        
   ## Event handler to add payment data to financial transactions
    def On_Vorgang(self, event=None):
        if self.debug: print("AfpDialog_FiBuchung Event handler `On_Vorgang'")
        client = AfpFinance_getZahlVorgang(self.data.get_globals(), "EventNr", 1)
        if client:
            data = {}
            if client.get_listname() == "Member" and client.is_outgoing():
                client.payment_text = "Retoure: "
                val = ""
                val, ok = AfpReq_Text("Ist eine Bankgebühr für diese Retoure fällig?","Bitte Höhe der Gebühr eingeben:", val, "Gebühreneingabe")
                if ok and val:
                    val = Afp_fromString(val)
                    if Afp_isNumeric(val) and val > 0.0:
                        data["xxx-Deduct"] = [4712, val, "Gebühr","extra"] 
                        #print ("AfpDialog_FiBuchung.On_Vorgang:", data["xxx-Deduct"])
            selected = self.get_selected_row()
            if not (selected is None):
                preis = self.data.get_value_rows("Buchung", "Betrag", selected)[0][0]
                zahlung = 0.0
            else:
                preis = Afp_fromString(self.text_Betrag.GetValue())
                zahlung = 0.0
                if not preis:
                    preis, zahlung, dat = client.get_payment_values()
            if zahlung:
                data["Betrag"] = preis - zahlung
            else:
                data["Betrag"]  = preis
            splitting =  client.get_splitting_values()
            if splitting: data["xxx-Split"] = splitting
            #print("AfpDialog_FiBuchung.On_Vorgang splitting:", splitting)
            if client.is_canceled(): 
                data["Betrag"] *= -1
            if self.read_account(self.combo_Soll) == self.transfer:
                soll = self.transfer
            else:
                soll = self.bank
            if client.is_outgoing():
                data["Soll"] = client.get_account()
                data["Haben"] = Afp_toString(soll)
            else:
                data["Soll"] = Afp_toString(soll)
                data["Haben"] = client.get_account()
            data["Vorgang"] = "Zahlung"
            data["LVortext"] = client.get_listname()[:4]  + ":" + client.line()
            data["KundenNr"] = client.get_payer()
            data["Text_Dlg"] = client.get_payment_text() 
            data["Tab"] = client.get_mainselection()
            data["TabNr"] = client.get_value()
            # = [[KtNr, Betrag, Zusatz], ...]  
            #print ("AfpDialog_FiBuchung.On_Vorgang:", data)
            if self.text_Betrag.GetValue():
                data.pop("Betrag")
            if self.text_Text.GetValue():
                data["Text_Dlg"] = data["Text_Dlg"] + " "  + self.text_Text.GetValue()[:250]
            self.Pop_entries(data)
        if event: event.Skip()
        
   ## Event handler to load data from file
    def On_Load(self, event=None):
        if self.debug: print("AfpDialog_FiBuchung Event handler `On_Load'")
        ok = False
        datum = self.text_Datum.GetValue()
        beleg = self.text_Beleg.GetValue()
        auszug = self.text_Auszug.GetValue() 
        globals = self.data.get_globals()
        dir = globals.get_value("archivdir")
        fname, ok = AfpReq_FileName(dir , "Bitte XML Importfile auswählen!", "*.xml;*.csv", True)
        print("AfpDialog_FiBuchung.On_Load File:", ok, fname)
        if ok and fname and (fname[-4:] == ".csv" or fname[-4:] == ".CSV"):
            toDat = self.data.get_value("BuchDat.AUSZUG")
            if datum: fromDat = Afp_fromString(datum)
            else: fromDat = None
            self.data.import_from_file(fname, toDat, fromDat)
            self.set_entries_from_import()
            return
        elif ok and fname:
            imp = AfpImport(globals, fname, None, self.debug)
            header = imp.get_file_header()
            ident = self.identify_file_header(header)
            split_data = False
            #print("AfpDialog_FiBuchung.On_Load SEPA:", fname, header, ident)
            if "SEPA" in ident:
                if not (datum and beleg and auszug):
                    AfpReq_Info(ident + " Datei gewählt, bitte Buchungsdatum, Belegnummer und Auzug angeben!","Lesevorgang wird abgebrochen.", "Info")
                    ok = False
                else: 
                    valid_tags, value_tags, interpreter = self.generate_sepa_tags(ident)
                    if ident == "SEPA-CT":
                        exp = self.read_account(self.combo_Soll)
                        if not exp:  exp = self.expense_accounts[0]
                        para = "\"" + datum + "\", " + Afp_toString(self.bank) + ", " + Afp_toString(self.transfer) + ", " + Afp_toString(exp) + ", " + beleg + ", \"" + auszug + "\", \"Verein\"" 
                    else:
                        para = "\"" + datum + "\", " + Afp_toString(self.bank) + ", " + Afp_toString(self.transfer) + ", " + Afp_toString(self.revenue_accounts[0]) + ", " + beleg + ", \"" + auszug + "\", \"Verein\"" 
                    imp.customise_xml(valid_tags, value_tags, interpreter, para)
                split_data = True
                if "ANMELD" in self.client_factories:
                    self.data.add_client_factory(self.client_factories["ANMELD"])
        if ok:
            datas = imp.read_from_file()   
            #print ("AfpDialog_FiBuchung.On_Load Datas:") 
            #datas[0].view()
            if self.data.has_import_queued():
                dlg_value = Afp_fromString(self.text_Betrag.GetValue())
                if dlg_value and Afp_fromString(datas[0].get_value("Betrag")) == dlg_value: 
                    datas[0].set_value("Bem", self.text_Text.GetValue()[:250])
                    datas[0].set_value("Art", self.combo_Vorgang.GetValue())
                    self.import_line = None
                    self.set_entries_from_import()
            self.data.booking_absorber(datas[0], split_data)
            self.Pop_Buchung()
            self.Pop_Auszug()
            BNr = self.data.gen_next_rcptnr()
            if BNr:
                self.text_Beleg.SetValue(Afp_toNumericString(BNr))
            date = self.data.get_highest_value("Datum")
            if date: 
                self.text_Datum.SetValue(Afp_toString(date))
            self.Set_Editable(True)
        #print "AfpDialog_FiBuchung.On_Load data:", self.data.view()
        if event: event.Skip()
        
   ## Event handler to get address for transaction
    def On_Adresse(self, event=None):
        if self.debug: print("AfpDialog_FiBuchung Event handler `On_Adresse'")
        KNr  = AfpLoad_AdAusw(self.data.get_globals(), "ADRESSE", "Name", "", None, None, True)
        if KNr:
            adresse = AfpAdresse(self.data.get_globals(), KNr)
            text = self.text_Text.GetValue()
            if text: text += " - "
            data = {"KundenNr": KNr, "Text_Dlg": text + adresse.get_name(True), "LVortext": adresse.get_name(True)}
            #print("AfpDialog_FiBuchung.On_Adresse:", data)
            self.Pop_entries(data)            
        if event: event.Skip()
 
## loader routine for Finance dialog handling  \n
# @param globals - global values, including mysql connection
# @param period - if given ,period marker for transactions in AfpFinance
# @param parlist - if given, parameterlist for AfpFinance creation
def AfpLoad_FiBuchung(globals, period = None, parlist = None):
    data = AfpFinance(globals, period, parlist)
    data.set_key_generation(False)
    if globals.get_value("multiple-transaction-mandates","Finance"):
        print("AfpLoad_FiBuchung 'multiple-transaction-mandates': Selection of financial mandate is not yet implemented!")
        data.set_period(data.period + "xxmxx")
    #data.debug = True
    DiFi= AfpDialog_FiBuchung(None)
    DiFi.attach_data(data)
    if parlist: 
        if "disable"  in parlist:
            DiFi.set_disabled(parlist["disable"])
    DiFi.ShowModal()
    Ok = DiFi.get_Ok()
    DiFi.Destroy()
    return Ok 
## loader routine for Finance dialog handling direct from data \n
# @param globals - global values, including mysql connection
# @param data - AfpFinance data to be handled
# @param unset - flag, if strict accounting should be unset
def AfpLoad_FiBuchung_fromData(globals, data, unset = False):
    data.set_key_generation(False)
    if globals.get_value("multiple-transaction-mandates","Finance"):
        print("AfpLoad_FiBuchung 'multiple-transaction-mandates': Selection of financial mandate is not yet implemented!")
        data.set_period(data.period + "xxmxx")
    #data.debug = True
    DiFi= AfpDialog_FiBuchung(None)
    DiFi.attach_data(data)
    if unset:
        DiFi.unset_strict_accounting()
    DiFi.ShowModal()
    Ok = DiFi.get_Ok()
    DiFi.Destroy()   
## loader routine for Finance dialog handling wtith additional data to be integrated \n
# @param globals - global values, including mysql connection
# @param finance - AfpFinance data to be handled
def AfpLoad_FiBuchung_withData(globals, finance):
    period = finance.get_period()
    auszug, dat, sald = finance.get_auszug()
    parlist = None
    if auszug:
        parlist = {"Auszug": auszug, "Datum": dat, "Saldo": sald}
    data = AfpFinance(globals, period, parlist)
    data.set_key_generation(False)
    data.import_direct(finance)
    if globals.get_value("multiple-transaction-mandates","Finance"):
        print("AfpLoad_FiBuchung 'multiple-transaction-mandates': Selection of financial mandate is not yet implemented!")
        data.set_period(data.period + "xxmxx")
    #data.debug = True
    DiFi= AfpDialog_FiBuchung(None)
    DiFi.attach_data(data)
    #if parlist and "no_strict_accounting" in parlist:
        #DiFi.unset_strict_accounting()
    DiFi.ShowModal()
    Ok = DiFi.get_Ok()
    DiFi.Destroy()
    return Ok    
## Dialog to allow all SEPA handlings, per default 'SEPA Direct Debit' will be handeled \n
# use the 'set_creditor_transfer' method to switch to 'SEPA Creditor Transfer' handling \n
# 'SEPA Direct Debit' will allow two states, first Direct Debit mandates will be handled,
# second the xml-file can be created (switched background colour) \n
# 'SEPA Creditor Transfer' will allow only one state - xml-file can be created (also switched background colour)
class AfpDialog_SEPA(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        self.cols = 5
        self.rows = 10
        self.filled_rows = 0
        AfpDialog.__init__(self,None, -1, "")
        self.grid_ident = None
        self.col_percents = [25, 15, 25, 10, 25]
        self.col_labels = [["Name","BIC","IBAN","Datum","Datei"], ["Name","BIC","IBAN","Art","Betrag"], ["Name","BIC","IBAN","Betrag","Grund"]]
        self.col_label_index = 0
        self.xml_data_loaded = False
        self.xml_sepa_type = "SEPA-DD"
        self.grid_row_selected = None
        self.sort_rows = None
        self.clients = None
        self.newclients = None
        self.sort_clients = None
        self.sort_newclients = None
        self.purpose = None
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
        self.label_Label = wx.StaticText(self, 1, label="Verwaltung des SEPA Lastschriftmandate für", name="LLabel")
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
        self.text_BIC.Bind(wx.EVT_KILL_FOCUS, self.On_Change)
        self.label_IBAN = wx.StaticText(self, 1, label="IBAN:", name="LIBAN")
        self.text_IBAN =  wx.TextCtrl(self, -1, value="", style=0, name="IBAN")
        self.textmap["IBAN"] = "Tag#1.Konto"
        self.text_IBAN.Bind(wx.EVT_KILL_FOCUS, self.On_Change)
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
        self.sizer_box = wx.StaticBox(self, label="Mandate", size=(60, 212))
        self.right_sizer = wx.StaticBoxSizer(self.sizer_box, wx.VERTICAL)
        self.right_sizer.AddStretchSpacer(2)      
        self.right_sizer.Add(self.button_Plus,0,wx.EXPAND)               
        self.right_sizer.AddStretchSpacer(1) 
        self.right_sizer.Add(self.button_Minus,0,wx.EXPAND)        
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
        self.grid_mandate.SetSelectionMode(wx.grid.Grid.GridSelectRows)   
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

    ## switch to creditor transfer mode
    def set_creditor_transfer(self):
        self.xml_data_loaded = True
        self.xml_sepa_type = "SEPA-CT"
        self.SetTitle("SEPA Überweisungen")
        self.label_Label.SetLabel("Erstellung von SEPA Überweisungen für") 
        self.textmap.pop("BIC")
        self.textmap.pop("IBAN")
        self.textmap.pop("Anz")
        #self.button_Load.Enable(False)
        self.label_Anz.SetLabel("")
        self.label_Folge.SetLabel("Summe:")
        self.sizer_box.SetLabel("Zahlung")
        self.SetBackgroundColour(self.xml_background)
        self.col_label_index = 2
        self.Pop_sums()
        self.adjust_grid_rows()
        self.Set_Editable(True)
        self.text_Anz.SetValue("")
        self.text_Anz.SetEditable(False)
    ## set SEPA Creditor Transfer bankaccount debitor data, select from different accounts if necessary
    def set_debit_data(self):
        index = None
        rows = self.data.get_bankaccounts()
        lgh = 0
        if rows: lgh = len(rows)
        if lgh > 1:
            index, ok = AfpReq_Selection("Bitte Bankverbindung auswählen,", "für die die Sammelüberweisung erstellt werden soll.", rows)
            print("AfpDialog_SEPA.set_debit_data:", index)
            if not index is None:
                split = rows[index].split(",")
                self.data.set_debit_data(split[0], split[1])
        self.Pop_Mandate()
    ## population routine for mandat grids \n
    def Pop_Mandate(self):
        if self.xml_sepa_type == "SEPA-DD" and self.text_Anz.GetValue() == "":
             self.text_Anz.SetValue("1") 
        if self.xml_sepa_type == "SEPA-CT":
            #print "AfpDialog_SEPA.Pop_Mandate SEPA-CT:", self.data.debit_IBAN, self.data.debit_BIC
            if self.data.debit_IBAN:
                self.text_IBAN.SetValue(self.data.debit_IBAN)
            if self.data.debit_BIC:
                self.text_BIC.SetValue(self.data.debit_BIC)
        rows = []
        raws = None
        if self.xml_data_loaded:
            if self.xml_sepa_type == "SEPA-CT":
                rows = self.data.get_transaction_rows()
            else:
                rows = self.get_client_rows()
        else:
            raws = self.data.get_value_rows("Mandat")
            if raws:
                sort = []
                for raw in raws:
                    adresse = AfpAdresse(self.data.get_globals(), raw[0])
                    row = [adresse.get_name(True), raw[3], raw[4], raw[6], raw[5], raw[-1]]
                    rows.append(row)
                    sort.append(rows[-1][0])
                self.sort_rows, rows = Afp_sortSimultan(sort, rows,  True)
        if rows:
            lgh = len(rows)
            #print "AfpDialog_SEPA.Pop_Mandate rows:", lgh, self.rows, rows
            if lgh > self.rows:
                self.adjust_grid_rows(lgh)
                self.rows = lgh
                self.filled_rows = lgh
            self.grid_ident = []
            #print ("AfpDialog_SEPA.Pop_Mandate lgh:", lgh, self.rows)
            for row in range(self.rows):
                for col in range(self.cols): 
                    if row < lgh:
                        self.grid_mandate.SetCellValue(row, col,  Afp_toString(rows[row][col]))
                    else:
                        self.grid_mandate.SetCellValue(row, col,  "")
                if row < lgh:
                    self.grid_ident.append(rows[row][-1])

    ## populate sum lables if xml data has been loaded
    def Pop_sums(self):
        if self.xml_data_loaded and self.xml_sepa_type == "SEPA-DD":
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
        elif self.xml_sepa_type == "SEPA-CT":
            if self.data:
                sum = self.data.get_sum()
            else:
                sum = 0.0
            self.label_Folge.SetLabel("Summe: " +  Afp_toString(sum))
            
    ## print client names (for debug purpose only)
    def view_clients(self):
        print("AfpDialog_SEPA.view_clients New:")
        if self.newclients:
            for client in self.newclients:
                print(client.get_name())
        print("AfpDialog_SEPA.view_clients Recur:")
        if self.clients:
            for client in self.clients:
                 print(client.get_name())
      
    ## get grid data from clients
    def get_client_rows(self):
        rows = []
        sort = []
        newrows = []
        for client in self.newclients:
            rows.append(self.get_client_row(client, True))
            sort.append(rows[-1][0])
        if sort: self.sort_newclients, newrows = Afp_sortSimultan(sort, rows, True)
        rows = []
        sort = []
        for client in self.clients:
            rows.append(self.get_client_row(client, False))
            sort.append(rows[-1][0])    
        if sort: self.sort_clients, rows = Afp_sortSimultan(sort, rows, True)            
        return newrows + rows
            
   ## get grid data from clients
    def get_client_row(self, client, first):
        KNr = client.get_value("AgentNr")
        if not KNr: KNr = client.get_value("KundenNr")
        bic = self.data.get_client_BIC(KNr)
        iban = self.data.get_client_IBAN(KNr)
        field = self.data.get_client_fieldname("actuel")
        #print ("AfpDialog_SEPA.get_client_row:", KNr, client.get_name(True), bic, iban, field, client.get_value(field))
        if first: flag = "Erst"
        else: flag = "Folge"
        return [client.get_name(True), bic, iban, flag, client.get_value(field), client.get_value()]
        
    ## adjust grid rows and columns for dynamic resize of window  
    # @param new_rows - new number of rows needed    
    def adjust_grid_rows(self, new_rows = None):
        if not new_rows: new_rows = self.rows
        #print "AfpDialog_SEPA.adjust_grid_rows:", new_rows
        self.grid_resize(self.grid_mandate, new_rows)
        if self.col_percents:
            grid_width = self.GetSize()[0] - self.fixed_width
            for col in range(self.cols):  
                self.grid_mandate.SetColLabelValue(col, self.col_labels[self.col_label_index][col])
                if col < len(self.col_percents):
                    self.grid_mandate.SetColSize(col, int(self.col_percents[col]*grid_width/100))
    
    ## execution in case the OK button ist hit - overwritten from AfpDialog
    def execute_Ok(self):
        #print ("AfpDialog_SEPA.execute_Ok:", self.xml_data_loaded, self.clients, self.newclients, self.xml_sepa_type, self.data.has_changed())
        if  self.xml_data_loaded:
            if self.purpose:
                bem = self.purpose
                ok = True
            else:
                #ok = AfpReq_Question("SEPA xml-Dateien werden erzeugt", "und entsprechend im Archiv abgelegt!","SEPA xml-Dateien erzeugen!")
                bem, ok = AfpReq_Text("SEPA xml-Dateien werden erzeugt und entsprechend im Archiv abgelegt!", "Bitte Bezeichnung eingeben (kann auch leer bleiben).", "", "SEPA xml-Dateien erzeugen!")
            if ok:
                if self.clients or self.newclients: 
                    self.data.set_clients(self.clients, self.newclients)
                self.data.execute_xml(bem)
        self.data.store()
        if  self.xml_data_loaded:
            pathes = self.data.get_filepathes()
            if pathes:
                split = pathes.split()
                text1 = "Die folgende SEPA xml-Dateien wurde erzeugt:\n" + split[0] 
                text2 = "Bitte unverzüglich bei der Bank abgeben!\nSoll Dateipfad in die Zwischenablage übernommen werden?"
                if len(split) == 2:
                    text1 +=  "\n" + split[1]
                ok = AfpReq_Question(text1, text2,"Pfade in Zwischenablage?")
                if ok:
                    Afp_toClipboard(pathes)
    ## execution in case the Quit button ist hit -  overwritten from AfpDialog
    def execute_Quit(self):
        if self.debug: print ("AfpDialog_SEPA.execute_Quit:", self.data.has_changed())
        #print ("AfpDialog_SEPA.execute_Quit:", self.data.has_changed(), self.xml_sepa_type, self.filled_rows, self.grid_ident)
        #self.data.view()
        #self.data.transactions[0].view()
        self.Ok = False
        if self.xml_sepa_type == "SEPA-CT" and self.grid_ident: 
            text1 = "Beim Verlassen gehen die geänderten Daten verloren,"
            text2 = "sollen sie in einer XML-Datei zwischengespeichert werden?"
            Ok  = AfpReq_Question(text1, text2,"Daten geändert")
            if Ok:
                dir = self.data.get_globals().get_value("homedir")
                filename, Ok = AfpReq_FileName(dir, "", "*.xml") 
                typ =  filename[-4:] 
                if not typ == ".xml" or typ == ".XML":  filename += ".xml"
                #print "AfpDialog_FiBuchung.execute_Quit filename:", filename
                if Ok and filename:
                    Export = AfpExport(self.data.get_globals(), self.data, filename, self.debug)
                    Export.write_to_file(None, 4) 
  
    ## event handler for resizing window
    def On_ReSize(self, event):
        height = self.GetSize()[1] - self.fixed_height
        new_rows = int(height/self.grid_mandate.GetDefaultRowSize())
        #print "AfpDialog_SEPA.On_ReSize:", height, self.filled_rows, new_rows
        if new_rows >= self.filled_rows:
            self.adjust_grid_rows(new_rows)
        #self.Pop_grid(True)
        event.Skip()   
    
    ## Event handler for changing kreditor values
    def On_Change(self, event):
        if self.debug: print("AfpDialog_SEPA Event handler `On_Change'")
        anz = None
        act = None
        iban = None
        bic = None
        name = event.GetEventObject().GetName()
        if name == "Anz":
            text = self.text_Anz.GetValue()
            if "/" in text:
                split = text.split("/")
                act = Afp_fromString(split[0])
                anz = Afp_fromString(split[1])
            else:
                anz = Afp_fromString(text)
        if name == "IBAN":
            iban = Afp_fromString(self.text_IBAN.GetValue())
            if not Afp_checkIBAN(iban):
                iban = None
        if name == "BIC":
            bic = Afp_fromString(self.text_BIC.GetValue())
            if not Afp_checkBIC(bic):
                bic = None
        if anz or act or iban or bic:
            if self.xml_sepa_type == "SEPA-DD":
                self.data.set_creditor_data(iban, bic, anz, act)
            else:
                self.data.set_debit_data(iban, bic)
            if self.xml_data_loaded and (anz or act):
                self.On_Load()
        event.Skip()
        
    ## Event handler for left click on grid
    def On_LClick(self, event):
        if self.debug: print("AfpDialog_SEPA Event handler `On_LClick'")
        self.grid_row_selected = event.GetRow()
        #print "AfpDialog_SEPA.On_LClick:", self.grid_row_selected
        event.Skip()

   ## Event handler for double click on grid
    def On_DClick(self, event):
        if self.debug: print("AfpDialog_SEPA Event handler `On_DClick'")
        if not self.grid_row_selected is None:
            chg = False
            if self.xml_sepa_type == "SEPA-CT":
                row = self.data.get_transaction_row(self.grid_row_selected)
                liste = {"Name": self.grid_mandate.GetCellValue(self.grid_row_selected, 0), "IBAN": row[3], "BIC": row[4], "Betrag": Afp_toFloatString(row[1]), "Zweck": row[2]}
                KNr = row[0]
                #print "AfpDialog_SEPA.On_DClick:", KNr, liste
                row, client = AfpFinance_getSEPAct(self.data.get_globals(), KNr, liste)
                if row:
                    if client:
                        tab = client.get_selection().get_tablename()
                        tabNr = client.get_value()
                    else:
                        tab = None,
                        tabNr = None
                    self.data.set_transfer_data(self.grid_row_selected, KNr, row[1], row[2], Afp_fromString(row[3]), row[4], tab, tabNr)
                    self.Pop_Mandate()
                    self.Pop_sums()
            elif self.xml_data_loaded:
                lgh = 0
                if self.newclients: lgh = len(self.newclients)
                if self.grid_row_selected >= lgh:
                    #client = self.clients[self.grid_row_selected - lgh]
                    client = self.clients[self.sort_clients[self.grid_row_selected - lgh]]
                    first = False
                else:
                    #client = self.newclients[self.grid_row_selected]
                    client = self.newclients[self.sort_newclients[self.grid_row_selected]]
                    first = True
                liste = [["Erstlastschrift:", first],["Betrag:", client.get_string_value(self.client_value_field)]]
                typen = ["Check", "Text"]
                result = AfpReq_MultiLine( "Bitte Lastschrifteinzug für " + client.get_name() + " ändern:","" , typen, liste, "Lastschrifteinzug", 300, None)
                if result:
                    if client.get_value(self.client_value_field) != Afp_fromString(result[1]):
                        client.set_value(self.client_value_field, Afp_fromString(result[1]))
                        chg = True
                        if first:
                            self.newclients[self.sort_newclients[self.grid_row_selected]] = client
                        else:
                            self.clients[self.sort_clients[self.grid_row_selected - lgh]] = client
                    if first != result[0]:
                        #print "AfpDialog_SEPA.On_DClick Erstlastschrift:", result[0], first
                        chg = True
                        if first:
                            self.newclients.pop(self.sort_newclients[self.grid_row_selected])
                            self.clients.append(client)
                        else:
                            self.clients.pop(self.sort_clients[self.grid_row_selected - lgh])
                            self.newclients.append(client)
            else:
                row = self.data.get_value_rows("Mandat","Art,Typ,Gruppe,Bem,KundenNr,Extern",self.sort_rows[self.grid_row_selected])[0]
                #print "AfpDialog_SEPA.On_DClick:", row
                text = "Art: " + row[0] + ", Status: " + row[1]
                liste = [["BIC:", row[2]], ["IBAN:", row[3]]]
                adresse = AfpAdresse(self.data.get_globals(), row[4])
                result = AfpReq_MultiLine( "Bitte SEPA-Eintrag für " + adresse.get_name() + " ändern:", text, "Text", liste, "SEPA-Eintrag", 300, "An&zeigen")
                if result is None: # extra button pushed
                    Afp_startFile(self.data.get_globals().get_value("archivdir") + row[5], self.data.get_globals(), self.debug)
                elif result:
                    #print "AfpDialog_SEPA.On_DClick no xml result:", result
                    if result[0] != row[2]:
                        new_values = {"Gruppe": result[0]}
                        self.data.set_data_values(new_values, "Mandat", self.sort_rows[self.grid_row_selected])
                        chg = True
                    if result[1] != row[3]:
                        new_values = {"Bem": result[1]}
                        self.data.set_data_values(new_values, "Mandat", self.sort_rows[self.grid_row_selected])
                        chg = True
            if chg:
                self.Pop_Mandate()
                self.Pop_sums()
        event.Skip()

   ## Event handler to generate and load data for SEPA xml file into dialog
    def On_Load(self, event=None):
        if self.debug: print("AfpDialog_SEPA Event handler `On_Load'") 
        refresh = False
        if self.xml_sepa_type == "SEPA-CT":
            print ("AfpDialog_SEPA.On_load type: SEPA-CT")
            # add here xml-import from saved file        
            dir = self.data.get_globals().get_value("homedir")
            fname, ok = AfpReq_FileName(dir , "Bitte XML Importfile auswählen!", "*.xml", True)
            if ok and fname:
                imp = AfpImport(self.data.get_globals(), fname, None, self.debug)
                datas = imp.read_from_file()            
                self.data.booking_absorber(datas[0], False)
                refresh = True
        else:
            ok = self.data.prepare_xml()
            if ok: self.clients, self.newclients = self.data.get_clients()
            #print ("AfpDialog_SEPA.On_Load:", ok, self.newclients, self.clients)
            if self.clients or self.newclients:
                self.client_value_field = self.data.get_client_fieldname("actuel")
                self.xml_data_loaded = True
                self.SetBackgroundColour(self.xml_background)
                refresh = True
        if refresh:
            self.col_label_index = 1
            self.Pop_Mandate()
            self.Pop_sums()
            self.adjust_grid_rows()
            self.Set_Editable(True)
        if event: event.Skip()

    ## Event handler to add SEPA mandate
    def On_AddMandat(self, event):
        if self.debug: print("AfpDialog_SEPA Event handler `On_AddMandat'")
        if self.xml_sepa_type == "SEPA-DD":
            clients = self.data.get_possible_clients()
            liste = []
            ident = []
            cnt = 0
            for client in clients:
                liste.append(client.get_name())
                ident.append(cnt)
                cnt += 1
            index, Ok = AfpReq_Selection(clients[0].get_identification_string() + " auswählen,","für die ein SEPA Lastschriftmandat erstellt weden soll.", liste, "Neue SEPA Lastschrift", ident)
            #print  "AfpDialog_SEPA.On_AddMandat:", clients[index].get_name()
            if Ok: 
                client = clients[index]
                if client.get_value("AgentNr"):
                    name = client.get_name(False,"Agent")
                    Ok = AfpReq_Question("SEPA Lastschriftmandat für " + name + " erstellen?","","Neues SEPA Lastschriftmandat")
            if Ok:
                sepa = AfpFinance_addSEPAdd(client, None, self.data)
                if sepa:
                    self.data = sepa
                    self.Pop_Mandate()
                    self.Set_Editable(True)
        elif self.xml_sepa_type == "SEPA-CT":
            row = None
            name,ok = AfpReq_Text("Bitte Namen eingeben,", "nach dem gesucht werden soll:","", "Namenssuche")
            if not name: name = ""
            KNr = AfpLoad_AdAttAusw(self.data.get_globals(), "Bankverbindung", name)
            if not KNr:
                KNr = AfpLoad_AdAusw(self.data.get_globals(), "ADRESSE", "Name", name)
            if KNr:
                purpose = None
                if self.purpose: purpose = {"Zweck": self.purpose}
                row, client = AfpFinance_getSEPAct(self.data.get_globals(), KNr, purpose)
                if row:
                    if client:
                        tab = client.get_selection().get_tablename()
                        tabNr = client.get_value()
                    else:
                        tab = None
                        tabNr = None
                    #print ("AfpDialog_SEPA.On_AddMandat:",KNr, row[1], row[2], row[3], row[4], tab, tabNr)
                    if self.purpose is None:
                        ok = AfpReq_Question("Zweck der Sammelüberweisung auf '"+ row[4] + "' festlegen?","Zweck wir für alle Einträge als Vorschlag übernommen!","Zweck der Überweisungen")
                        if ok:
                            self.purpose = row[4]
                        else:
                            self.purpose = False
                    self.data.add_transfer_data(KNr, row[1], row[2], Afp_fromString(row[3]), row[4], tab, tabNr)
                    self.Pop_Mandate()
                    self.Pop_sums()
        event.Skip()
        
   ## Event handler to deaktivate SEPA mandate
    def On_Deaktivate(self, event):
        if self.debug: print("AfpDialog_SEPA Event handler `On_Deaktivate'")
        indices = self.grid_mandate.GetSelectedRows()
        if not indices and not self.grid_row_selected is None:
            indices = [self.grid_row_selected]
        if self.grid_ident:
            last = len(self.grid_ident)
        else:
            last = self.rows
        selected = False
        if indices: selected = True
        if last < self.rows:
            selected = False
            for ind in indices:
                if ind < last: selected = True
        if selected:
            self.Set_Editable(True)  
            if self.xml_sepa_type == "SEPA-DD":
                if self.xml_data_loaded:
                    #print ("AfpDialog_SEPA.On_Deaktivate: XML Data loaded:", self.grid_row_selected, indices)
                    lgh = 0
                    if self.newclients: lgh = len(self.newclients)
                    Ok = False
                    if len(indices) > 1:
                        Ok  = AfpReq_Question( Afp_toString(len(indices)) + " Einträge selektiert,", "sollen alle gelöscht werden werden?","Einzüge löschen")
                    if Ok:
                        indices.reverse()
                    else:
                        indices = [self.grid_row_selected]
                    for index in indices:
                        if index >= lgh: 
                            ind = self.sort_clients[index - lgh] 
                            #print ("AfpDialog_SEPA.On_Deaktivate Client:", ind, index, lgh, self.clients[ind].get_name())
                            self.clients.pop(ind)
                            for i in range(len(self.sort_clients)):
                                if self.sort_clients[i] > ind:  self.sort_clients[i]  -= 1
                            self.sort_clients.pop(index - lgh)
                        else:
                            ind = self.sort_newclients[index]
                            #print ("AfpDialog_SEPA.On_Deaktivate Newclient:", ind, index, self.newclients[ind].get_name())
                            self.newclients.pop(ind)
                            for i in range(len(self.sort_newclients)):
                                if self.sort_newclients[i] > ind:  self.sort_newclients[i]  -= 1
                            self.sort_newclients.pop(index)
                            lgh -= 1
                else:
                    indices.sort(reverse=True)
                    #print ("AfpDialog_SEPA.On_Deaktivate: indices", indices)
                    for index in indices:
                        if index < last:  
                            ind = self.sort_rows[index]
                            newdata = {"Typ": "Inaktiv"}
                            #print ("AfpDialog_SEPA.On_Deaktivate set Inaktiv:", ind, newdata, self.grid_ident)
                            self.data.set_data_values(newdata, "Mandat", ind)
                            self.grid_mandate.DeleteRows(index)
                            self.grid_ident.pop(index)
                            KNr = self.data.get_value_rows("Mandat","KundenNr", ind)[0] [0]
                            client = AfpAdresse(self.data.get_globals(), KNr)
                            Ok  = AfpReq_Question("SEPA Lastschriftmandat für " + client.get_name() + " ist deaktiviert,", "soll ein neues Mandat erstellt werden?","SEPA Lastschrift")
                            if Ok:
                                sepa = AfpFinance_addSEPAdd(client, None, self.data)
                                if sepa:
                                    self.data = sepa
                                    self.Set_Editable(True)
            elif self.xml_sepa_type == "SEPA-CT":
                #print("AfpDialog_SEPA.On_Deaktivate:", self.xml_sepa_type, self.grid_row_selected)
                if not self.grid_row_selected is None:
                    self.data.delete_transfer_data(self.grid_row_selected)
            self.Pop_Mandate()   
            self.Pop_sums()    
        else: 
            if self.xml_data_loaded: 
                AfpReq_Info("Aktion kann nicht durchgeführt werden,", "bitte den Eintrag auswählen, für den kein Einzug ausgeführt werden soll!")
            else: 
                AfpReq_Info("Aktion kann nicht durchgeführt werden,", "bitte das Mandat auswählen, dass deaktiviert werden soll!")
        event.Skip()

## loader routine for SEPA Direct Debit dialog handling  \n
# @param data - SelectionList data where sepa direct debit is handled for
# @param fields - dictionary with field names to be used to extract debits from clients
# - "regular" - field for regular payment per year
# - "extra" - field for extra payment for this year in first draw
# - "total" - field where total payment for this year  is hold
# - "actuel" - field where the payment amount is written to
# @param filename - name of xml-file in sourcedir to be used for output
def AfpLoad_SEPAdd(data, fields = None, filename = None):
    DiSepa = AfpDialog_SEPA(None)
    sepa = AfpSEPAdd(data, fields, filename, data.is_debug())
    DiSepa.attach_data(sepa)
    DiSepa.ShowModal()
    Ok = DiSepa.get_Ok()
    DiSepa.Destroy()
    return Ok 
## loader routine for SEPA Creditor Transfer dialog handling  \n
# @param data - SelectionList data where sepa direct debit is handled for
# @param mandator - address identifier for mandator to be used
# @param filename - name of xml-file in sourcedir to be used for output
def AfpLoad_SEPAct(data, mandator = None, filename = None):
    DiSepa = AfpDialog_SEPA(None)
    sepa = AfpSEPAct(data, mandator, filename, data.is_debug())
    DiSepa.set_creditor_transfer()
    DiSepa.attach_data(sepa)
    DiSepa.set_debit_data()
    DiSepa.ShowModal()
    Ok = DiSepa.get_Ok()
    DiSepa.Destroy()
    return Ok 

  
