#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseAdDialog
# AfpBaseAdDialog module provides the dialogs and appropriate loader routines needed for address handling
# it holds the calsses
# - AfpDialog_AdAusw
# - AfpDialog_AdAIndiAusw
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        06 Mai 2020 - add file to archiv dialog - Andreas.Knoblauch@afptech.de \n
#        24 Jan. 2015 - add auto selection - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
#    Copyright© 1989 - 2025 afptech.de (Andreas Knoblauch)
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

from AfpBase.AfpUtilities.AfpStringUtilities import Afp_ArraytoString, Afp_toQuotedString
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_getMaxOfColumn
from AfpBase.AfpBaseDialog import *
from AfpBase.AfpBaseDialogCommon import *
from AfpBase.AfpBaseRoutines import Afp_getListe_fromTableSelection
from AfpBase.AfpBaseAdRoutines import *

## Routine to select a file and add it into the archiv
# @param client - SelectionList where file should be added to archive
# @param text - text to be displayed in header and default for 'Gruppe' in archive 
# @param fixed - dictionary for fixed entries in archive 
# @param changeable - dictionary for changeable entries for archive
# - will be written from the back: last to 'Bem', second last to 'Gruppe', ..'Typ', .. 'Art';
# - if 'datum' is found in a entry, this one is written to 'Datum' 
# @param fname- if given, name of file to be integrated into archiv
def AfpAdresse_addFileToArchiv(client, text = "Archiveintrag", fixed = None, changeable = None, fname = None):
    if fname is None:
        no_name = True
        dir = client.get_globals().get_value("docdir")
        fname, ok = AfpReq_FileName(dir, text + " für " + client.get_name() ,"", True)
    else:
        no_name = False
        ok = True
    #print "AfpAdresse_addFileToArchiv:", fname, ok
    result = None
    if ok and changeable:
        if no_name: Afp_startFile(fname, client.get_globals(), client.is_debug(), True)
        if "Datum" in changeable:
            if changeable["Datum"]:
                datum = changeable["Datum"]
            else:
                datum = client.get_globals().today_string()
            liste = [["Datum", datum]]
        else:
            liste = []
        for chg in changeable:
            if not chg == "Datum":
                liste.append([chg, changeable[chg]])
        result = AfpReq_MultiLine(text + " mit der folgenden Datei erzeugen:", fname, "Text", liste, text, 500)
        #print "AfpAdresse_addFileToArchiv:", liste, result
    if ok and not result == False:
        entry = {}
        if fixed:
            for fix in fixed:
                entry[fix] = fixed[fix]
        if result:
            lgh = len(result)
            if "Datum" in liste[0][0] or "datum" in liste[0][0] :
                entry["Datum"] = Afp_fromString(result.pop(0))
                lgh -= 1
            entry["Bem"] = result[-1]
            if lgh > 1: entry["Gruppe"] = result[-2]
            if lgh > 2: entry["Typ"] = result[-3]
            if lgh > 3: entry["Art"] = result[-4]
        if not "Gruppe" in entry: entry["Gruppe"] = text
        entry["Extern"] = fname
        #print "AfpAdresse_addFileToArchiv entry:", entry
        client.add_to_Archiv(entry, True)
        client.last_selected_file = fname
        return client
    return None

## select address attribut of given address identifier or enter new \n
# return indirect attribut identifier or 'None' in case nothing is selected
# @param globals - global values holding mysql connection
# @param KNr - address identifier
# @param text - text for dialog
def AfpAdresse_indirectAttributFromKNr(globals, KNr, text = "Adressenmerkmal"):
    GNr = None
    Adresse = AfpAdresse(globals, KNr)
    row = AfpAdresse_selectAttribut(Adresse, text, False)
    if row:
        index = Adresse.get_selection("ADRESATT").get_feldindices("AttNr")[0]
        #print "AfpAdresse_indirectAttributFromKNr:", index, row
        if not index is None: GNr = row[index]
    return GNr
    
## select address attribut of given address identifier or enter new \n
# return row or 'None' in case nothing is selected
# @param Adresse - AfpSelectionList holding address data
# @param text - text for dialog
# @param direct - flag which kind of attributs should be selected
# - True: select only direct attributs 
# - False: select only indirect attributs (with unique identifier)
# - None: select all attributs 
def AfpAdresse_selectAttribut(Adresse, text = "Adressenmerkmal", direct = True):
    rows = Adresse.get_value_rows("ADRESATT")
    index = Adresse.get_selection("ADRESATT").get_feldindices("Attribut,AttText,Tag,AttNr")
    no_unique = False
    if index[3] is None: 
        direct = True
        no_unique = True
    unique = not index[3] is None
    liste = []
    ident = []
    liste.append("   ---   Neues " + text + " auswählen!  ---   ")
    for row in rows:
        if direct is None or (direct and (no_unique or not row[index[3]])) or (not direct and row[index[3]]):
            tag = ""
            if not direct and row[index[3]] and row[index[2]]:
                tag =  Afp_toString(row[index[2]]).replace(","," ")
            liste.append(Afp_toString(row[index[0]]) + " " + Afp_toString(row[index[1]]) + "  " + tag)
    row = None
    lisel, ok = AfpReq_Selection("Bitte " + text + " von", Adresse.get_name() + " auswählen." , liste, text, ident)
    #print "AfpAdresse_selectAttribut:", lisel, ok, liste
    if ok: 
        if lisel  == liste[0]:
            ok, row = AfpAdresse_selectAttributRow(Adresse, direct)
            if ok and row:
                row[0] = Adresse.get_value("KundenNr")
                Adresse.get_selection("ADRESATT").add_row(row)
                Adresse.store()
        else:
            for i in range(len(rows)):
                if liste[i+1] == lisel:
                    row = rows[i]
                    break
        return row
    else:
        return None
        
## select address attribut or enter new \n
# return row or 'None' in case nothing is selected
# @param Adresse - AfpSelectionList holding address data
# @param direct - flag which kind of attributs should be selected
# - True: select only direct attributs 
# - False: select only indirect attributs (with unique identifier)
# - None: select all attributs 
def AfpAdresse_selectAttributRow(Adresse, direct=True):
    sel = Adresse.get_selection("ADRESATT")
    next_nr = Adresse.next_attribut_number()
    index = sel.get_feldindices("Attribut,AttText,Tag,Aktion,AttNr")
    imax = 0
    for ind in index:
        if ind and ind > imax: imax = ind
    no_unique = False
    if index[4] is None: 
        direct = True
        no_unique = True
    # generate text and selection depending on 'direct'
    filter = "KundenNr = 0"
    if direct:
        filter += " AND AttNr IS NULL"
        input_line = "   ---   Neues Adressenmerkmal eingeben!   ---   "
        text = "Adressenmerkmal"
        text1 = "Bitte Bezeichnung für neues Adressenmerkmal eingeben."
    elif direct is None:
        input_line = "---   Neues Merkmal oder Vorlage eingeben!   ---   "
        text = "Merkmal oder Vorlage"
        text1 = "Bitte Bezeichnung für neues Merkmal oder neue Vorlage eingeben,\n Vorlagen bitte mit ' +' kennzeichnen."
    else:
        filter += " AND AttNr > 0"
        input_line = "   ---   Neue Merkmalvorlage eingeben!   ---   "
        text = "Vorlage"
        text1 = "Bitte Bezeichnung für neue Vorlage eingeben."

    liste, rows = Afp_getListe_fromTableSelection(sel, filter, "Attribut", "Attribut", "AttNr")
    #print ("AfpAdresse_selectAttributRow Liste:", filter, liste, rows, imax, sel, sel.data)
    liste = Afp_ArraytoString(liste)
    liste = [input_line] + liste
    row = [0]
    for i in range(imax):
        row.append(None)
    rows = [row] + rows
    name = Adresse.get_name()
    row, ok = AfpReq_Selection("Bitte " + text + " für" , name + " auswählen." , liste, text, rows)

    if not row[index[0]] and ok:
        attribut, ok = AfpReq_Text(text1,"Dieses Merkmal wird " + name + " zugeordnet.")
        if ok:
            indirect = False
            if attribut[-2:] == " +":
                attribut = attribut[:-2]
                indirect = True
            elif not direct is None and direct == False:
                indirect = True
            row[index[0]] = attribut
            if indirect: row[index[4]] = 1
            active, ok = AfpReq_Text("Falls zusätzliche Daten benötigt werden, die Bezeichnungen durch Komma getrennt hier eingeben.","Z.B. 'Kennzeichen(anzeigen),Typ,Identifikationsnummer'")
            if ok and active:
                row[index[3]] = active
            #print "AfpAdresse_selectAttributRow Store:", row
            sel.add_row(row)
            sel.store()
    else:
        attribut = row[index[0]]
    #print "AfpAdresse_selectAttributRow Select:", ok, row, index
    if ok:
        AttText = row[index[1]]      
        Tag =  row[index[2]] 
        Aktion =  row[index[3]] 
        ok, AttText, Tag = AfpAdresse_spezialAttribut(name, attribut, AttText, Tag, Aktion, None)
        #print "AfpAdresse_selectAttributRow Tag:", ok, AttText, Tag
        if ok:  
            row[index[1]] = AttText
            row[index[2]]  = Tag
            if row[0] == 0: # here additional manipulation for new  dataset can be made
                row[0] = Adresse.get_value("KundenNr")
                row[1] = Adresse.get_value("Name")
                if index[4] and row[index[4]]:
                    row[index[4]] = next_nr
    #print "AfpAdresse_selectAttributRow:", ok, row
    if ok: return ok, row
    else: return ok, None
   
## handling routine to set text and/or special values needed for an attribut \n
# @param name - name of address this attribut belongs to
# @param attribut - name of  attribut to be modified
# @param text - additional text string for this attribut
# @param tag - individual data string holding all values for this special attribut
# @param action - individual string holding names of values for this special attribut
# @param delete_button - flag if 'delete' button should be hidden; None - Hide, "" - Show , Text - Label
def AfpAdresse_spezialAttribut(name, attribut, text, tag, action, delete_button = None):
    if tag: new = False
    else: new = True
    Ok = None
    taglist= None
    new = True
    liste = []
    attribut = Afp_toString(attribut)
    #print "AfpAdresse_spezialAttribut:", attribut, type(attribut), tag, action, Ok
    if action:
        taglist = action.split(",")
    if not taglist or (len(taglist) == 1 and "Anmeld_" in taglist[0]):
        taglist = AfpAdresse_getAttributTagList(attribut)
    #print "AfpAdresse_spezialAttribut taglist:", tag, taglist
    ind_text = -1
    if taglist:
        split = ""
        if tag:
            split = tag.split(",")
            if tag and len(split) == 1:
                split = tag.split(" ")
        lspl = len(split)
        cnt = 0
        for i in range(len(taglist)):
            if "anzeigen" in taglist[i]: 
                ind_text = i
                continue
            entry = [taglist[i] + ":"]
            if cnt < lspl: 
                entry.append(split[cnt])
                cnt += 1
            else: entry.append("")
            liste.append(entry)
    if not text: text = ""
    if ind_text < 0: liste = [["(optional) Merkmaltext:", text]] + liste
    else: liste = [[taglist[ind_text] + ":", text]] + liste
    #print "AfpAdresse_spezialAttribut MultiLine:", name, attribut, liste, no_delete
    Ok = None
    while Ok is None:
        result = AfpReq_MultiLine("Für '" + name + "' werden die folgenden " + attribut +"-Daten benötigt:", "", "Text", liste, attribut, 400 , delete_button)
        #print ("AfpAdresse_spezialAttribut result", result)
        if not result is None:
            if type(result) == list: Ok = True
            else: Ok = False
        if result:
            changed = False
            lgh = len(taglist)  + 1
            if ind_text > -1: lgh -= 1
            for i in range(1, lgh):
                if not liste[i][1] == result[i] or new:
                    if not Ok is None: changed = True
                    if liste[i][0] == "IBAN:":
                        if not Afp_checkIBAN(result[i]):
                            changed = False
                            Ok = None
                    elif liste[i][0] == "BIC:":
                        if not Afp_checkBIC(result[i]):
                            changed = False
                            Ok = None
                    liste[i][1] = result[i]       # keep input for next loop                 
            if changed: 
                tag = Afp_ArraytoLine(result[1:], ",", len(result)-1)
                Ok = True
            if not liste[0][1] == result[0]:
                text = result[0]
                Ok = True
    #print ("AfpAdresse_spezialAttribut result:", Ok, text, tag)
    return Ok, text, tag
    
## select an address and add given attribut to it
# @param globals - global variables, holding mysql connection
# @param attribut - name of  attribut where an additional entry should be created
# @param sname - initial name for search
# @param text - text to be displayed during search
def AfpAdresse_addAttributToAdresse(globals, attribut, sname, text):
    Ok = False
    name = None
    KNr = AfpLoad_AdAusw(globals, "ADRESSE", "Name", sname, None, text, True)
    if KNr:
        adresse = AfpAdresse(globals, KNr, None, globals.is_debug())
        sel = adresse.get_selection("ADRESATT")
        values = sel.get_values("Attribut")
        actuel = []
        for value in values:
            actuel.append(value[0])
        #print "AfpAdresse_addAttributToAdresse actuel:",attribut, actuel, attribut in actuel
        if not attribut in actuel:
            filter = "KundenNr = 0"
            liste, rows = Afp_getListe_fromTableSelection(sel, filter, "Attribut", "Attribut", "AttNr")
            #print "AfpAdresse_addAttributToAdresse liste:",attribut, liste
            if attribut in liste:
                ok = AfpReq_Question( "Der Adresse '" + adresse.get_name() + "'", "wird das Merkmal '" + attribut + "' zugeordnet!", "Merkmalzuordnung") 
                if ok:
                    index = liste.index(attribut)
                    row = rows[index]
                    row[0] = adresse.get_value("KundenNr")
                    sel.add_row(row)
                    sel.store()
                    Ok = True
                    name = adresse.get_name()
            else:
                AfpReq_Info("Das Merkmal '" + attribut + "' existiert nicht,","keine Zuordnung möglich!", "Warnung")
        else: 
            AfpReq_Info("Das Merkmal '" + attribut + "'ist der Adresse", adresse.get_name() +"schon zugeordnet", "Info")
    return name, Ok
    
## dialog for selection of address data \n
# selects an entry from the address table
class AfpDialog_AdAusw(AfpDialog_Auswahl):
#class AfpDialog_AdAusw(AfpDialog_DiAusw):
    ## initialise class
    def __init__(self):
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        #AfpDialog_DiAusw.__init__(self,None, -1, "")
        self.typ = "Adressenauswahl"
        self.datei = "ADRESSE"
        self.modul = "Adresse"
    ## get the definition of the selection grid content \n
    # overwritten for "Adressen" use ! \n
    # Each line defines a column for the "Auswahl" dialog. \n
    # Felder = [[Field .Table .Alias,Width], ... , [Field1.Table1,None]]     
    def get_grid_felder(self):  
    #                   Field  Table    Alias  Width     
        Felder = [["Name.Adresse.Namen",30], 
                            ["Vorname.Adresse.Namen", 20], 
                            ["Strasse.Adresse",30], 
                            ["Ort.Adresse",20], 
                            ["KundenNr.Adresse",None]] # Ident column)  
        return Felder
    ## invoke the dialog for a new entry
    def invoke_neu_dialog(self, globals, search, where):
        #if search is None: search = "a"
        KNr = None
        Adresse = AfpAdresse(globals, None, None, globals.is_debug(), False)
        if self.result_index > -1:
            KNr = self.ident[self.result_index]
            Adresse.set_new(KNr)
            search = None
        #print "AfpDialog_AdAusw.invoke_neu_dialog:", search, self.result_index, KNr
        Ok = AfpLoad_DiAdEin(Adresse, search)
        return Ok
 
## dialog for indirect address selection \n 
# selects an entry of the address table by choosing from anothertable (currently used for  AdresAtt) 
class AfpDialog_AdIndiAusw(AfpDialog_Auswahl):
    ## initialise class
    def __init__(self, datei):
        self.grid_datei = datei       
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.typ = "Adressenauswahl"
        self.datei = datei
        self.modul = "Adresse"
        # remove 'Neu'-button from panel
        self.button_Neu.Destroy()
    ## get the definition of the selection grid content \n
    # overwritten for indirect "Adressen" use
    def get_grid_felder(self):  
        Felder = [["Name.Adresse.Name",30], 
                            ["Vorname.Adresse.Name", 20], 
                            ["Strasse.Adresse",30], 
                            ["Ort.Adresse",20], 
                            ["KundenNr." + self.grid_datei  + " = KundenNr.Adresse", None]] 
        return Felder
    
## loader routine for address selection dialog
# @param globals - global data holding mysql connection to database
# @param Datei - table name where data should be selected from
# @param index - name of index column in table
# @param value - name that should be searched
# @param where - filter for database search
# @param attribut_text - if given, attribut looked for in ADRESATT
# @param ask - flag if input dialog should be shown
def AfpLoad_AdAusw(globals, Datei, index, value = "", where = None, attribut_text = None, ask = False):
    result = None
    Ok = True
    if ask:
        sort_list = AfpAdresse_getOrderlistOfTable(globals.get_mysql(), index, Datei)
        value, index, Ok = Afp_autoEingabe(value, index, sort_list, "Adressen","Bitte Namen für Suche eingeben:")
    if Ok:
        if Datei == "ADRESSE":
            DiAusw = AfpDialog_AdAusw()
        else:
            DiAusw = AfpDialog_AdIndiAusw(Datei)
        #print "AfpLoad_AdAusw:", Datei, Index, value, where
        if attribut_text:
            if len(attribut_text) > 4 and attribut_text[:5] == "Bitte":
                text = attribut_text
            else:
                text = "Bitte " + attribut_text + "-Adresse auswählen:"
        else:
            text = "Bitte Adresse auswählen:"
        DiAusw.initialize(globals, index, value, where, text)        
        DiAusw.ShowModal()
        result = DiAusw.get_result()
        DiAusw.Destroy()
    elif Ok is None:
        # flag for direct selection
        result = Afp_selectGetValue(globals.get_mysql(), Datei, "KundenNr", index, value)
    return result
## loader routine to select address data from attribut table
# @param globals - global data holding mysql connection to database
# @param Datei - table name where data should be selected from
# @param attribut - attribut looked for in ADRESATT
# @param value - initial name to be looked for
def AfpLoad_AdAttAusw(globals, attribut, value = ""):     
        Datei = "ADRESATT"
        Index = "Name"
        where = "Attribut.ADRESATT = \"" + attribut + "\" and KundenNr.ADRESATT > 0"
        #if not value: value = "a"
        result = AfpLoad_AdAusw(globals, Datei, Index, value, where, attribut)
        return result
        
## loader routine to select address data indirectly from given table
# @param globals - global variables, includinmg database connection
# @param dateifeld - table.field name of connection field
# @param value - value of connection field, resp. values of connection field
# @param where - additional filter for selection
# @param name - initial name for search
# @param attribut - name for dialog display, or complete Question started by "Bitte"
def AfpLoad_AdIndiAusw(globals, dateifeld, value, name="", where=None, attribut = None):
        feld, datei = dateifeld.split(".")
        index = "Name.ADRESSE"
        if where: where += " and " 
        else: where = ""
        if type(value) == list:
            where += "("
            for val in value:
                where +=  dateifeld + " = " + Afp_toQuotedString(val) + " or "
            where = where[:-4] + ")"
        else:
            where += dateifeld + " = " + Afp_toQuotedString(value) 
        if not attribut: attribut = " individuelle "
        if not name: ask = True
        else: ask = False
        result = AfpLoad_AdAusw(globals, datei, index, name, where, attribut, ask)
        return result

## Class AfpDialog_DiAdEin display dialog to show and manipulate address-data (Adresse) and handles interactions \n
class AfpDialog_DiAdEin(AfpDialog):
    def __init__(self, *args, **kw):
        self.change_data = False
        self.choicevalues = {}
        AfpDialog.__init__(self,None, -1, "")
        self.lock_data = True
        self.bulk_nrs = None
        self.SetSize((452,447))
        self.SetTitle("Adresse")
      
    ## initialize wx widgets of dialog  \n
    # calls setWx to handle Edit and Ok widgets and events
    def InitWx(self):
        #self.InitWx_panel()
        self.InitWx_sizer()
    ## initialize wx widgets of dialog  using sizers\n
    # calls setWx to handle Edit and Ok widgets and events
    def InitWx_sizer(self):
        self.left_weight = 1
        self.right_weight = 7
        #self.right_weight = 2
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.line1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.label_Anrede = wx.StaticText(self, -1, label="Anre&de:", name="Anrede")
        self.choice_Anrede = wx.Choice(self, -1, choices=["Du", "Sie"],  name="CAnrede")
        self.choicemap["CAnrede"] = "Anrede.ADRESSE"
        self.Bind(wx.EVT_CHOICE, self.On_CAnrede, self.choice_Anrede)      
        self.label_Geschlecht = wx.StaticText(self, -1, label="&Geschlecht:", name="Geschlecht")      
        self.choice_Geschlecht = wx.Choice(self, -1,  choices=["w","n","m"],  name="CGeschlecht")
        self.choice_Geschlecht.SetSelection(1)
        self.choicemap["CGeschlecht"] = "Geschlecht.ADRESSE"
        self.Bind(wx.EVT_CHOICE, self.On_CGeschlecht, self.choice_Geschlecht)
        self.line1_sizer.AddSpacer(10)
        self.line1_sizer.Add(self.label_Anrede,self.left_weight,wx.EXPAND)
        self.line1_right = wx.BoxSizer(wx.HORIZONTAL)
        self.line1_right.Add(self.choice_Anrede,0,wx.EXPAND)
        self.line1_right.AddStretchSpacer(1) 
        self.line1_right.Add(self.label_Geschlecht,0,wx.EXPAND)
        self.line1_right.Add(self.choice_Geschlecht,0,wx.EXPAND)
        self.line1_sizer.AddSpacer(10) 
        self.line1_sizer.Add(self.line1_right,self.right_weight,wx.EXPAND)        
        self.line1_sizer.AddSpacer(10) 

        self.line2_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_T_Vorname_Adresse = wx.StaticText(self, -1, label="&Vorname:", name="T_Vorname_Adresse")
        self.text_Vorname_Adresse = wx.TextCtrl(self, -1, value="",  style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="Vorname_Adresse")
        self.text_Vorname_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Vorname_Adresse"] = "Vorname.ADRESSE"
        self.line2_sizer.AddSpacer(10)
        self.line2_sizer.Add(self.label_T_Vorname_Adresse,self.left_weight,wx.EXPAND)
        self.line2_sizer.AddSpacer(10) 
        self.line2_sizer.Add(self.text_Vorname_Adresse,self.right_weight,wx.EXPAND)
        self.line2_sizer.AddSpacer(10) 

        self.line3_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_T_Name_Adresse = wx.StaticText(self, -1, label="&Name:", name="T_Name_Adresse")
        self.text_Name_Adresse = wx.TextCtrl(self, -1, value="", style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="Name_Adresse")
        self.text_Name_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Name_Adresse"] = "Name.ADRESSE"
        self.line3_sizer.AddSpacer(10)
        self.line3_sizer.Add(self.label_T_Name_Adresse,self.left_weight,wx.EXPAND)
        self.line3_sizer.AddSpacer(10) 
        self.line3_sizer.Add(self.text_Name_Adresse,self.right_weight,wx.EXPAND)
        self.line3_sizer.AddSpacer(10) 
        
        self.line4_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_T_Strasse_Adresse = wx.StaticText(self, -1, label="Stra&sse:",  name="T_Strasse_Adresse")
        self.text_Strasse_Adresse = wx.TextCtrl(self, -1, value="", style=0, name="Strasse_Adresse")
        self.text_Strasse_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Strasse_Adresse"] = "Strasse.ADRESSE"
        self.line4_sizer.AddSpacer(10)
        self.line4_sizer.Add(self.label_T_Strasse_Adresse,self.left_weight,wx.EXPAND)
        self.line4_sizer.AddSpacer(10) 
        self.line4_sizer.Add(self.text_Strasse_Adresse,self.right_weight,wx.EXPAND)
        self.line4_sizer.AddSpacer(10) 
       
        self.line5_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_T_Plz_Adresse = wx.StaticText(self, -1, label="&Plz/Ort:", name="T_Plz_Adresse")
        self.text_Plz_Adresse = wx.TextCtrl(self, -1, value="",  style=0, name="Plz_Adresse")
        self.text_Plz_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Plz_Adresse"] = "Plz.ADRESSE"
        self.text_Ort_Adresse = wx.TextCtrl(self, -1, value="", style=0, name="Ort_Adresse")
        self.text_Ort_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Ort_Adresse"] = "Ort.ADRESSE" 
        self.line5_sizer.AddSpacer(10) 
        self.line5_sizer.Add(self.label_T_Plz_Adresse,self.left_weight,wx.EXPAND)
        self.line5_right = wx.BoxSizer(wx.HORIZONTAL)
        self.line5_right.Add(self.text_Plz_Adresse,1,wx.EXPAND)
        self.line5_right.AddSpacer(10) 
        self.line5_right.Add(self.text_Ort_Adresse,5,wx.EXPAND)
        self.line5_sizer.AddSpacer(10) 
        self.line5_sizer.Add(self.line5_right,self.right_weight,wx.EXPAND)
        self.line5_sizer.AddSpacer(10) 
        
        self.line6_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_T_Telefon_Adresse = wx.StaticText(self, -1, label="&Telefon:", name="T_Telefon_Adresse")
        self.text_Telefon_Adresse = wx.TextCtrl(self, -1, value="", style=0, name="Telefon_Adresse")
        self.text_Telefon_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Telefon_Adresse"] = "Telefon.ADRESSE"
        self.line6_sizer.AddSpacer(10)
        self.line6_sizer.Add(self.label_T_Telefon_Adresse,self.left_weight,wx.EXPAND)
        self.line6_sizer.AddSpacer(10) 
        self.line6_sizer.Add(self.text_Telefon_Adresse,self.right_weight,wx.EXPAND)
        self.line6_sizer.AddSpacer(10) 
         
        self.line7_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_T_Tel2 = wx.StaticText(self, -1, label="", name="T_Tel2")
        self.text_Tel2 = wx.TextCtrl(self, -1, value="",  style=0, name="Tel2")
        self.text_Tel2.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Tel2"] = "Tel2.ADRESSE"
        self.line7_sizer.AddSpacer(10)
        self.line7_sizer.Add(self.label_T_Tel2,self.left_weight,wx.EXPAND)
        self.line7_sizer.AddSpacer(10) 
        self.line7_sizer.Add(self.text_Tel2,self.right_weight,wx.EXPAND)
        self.line7_sizer.AddSpacer(10) 
         
        self.line8_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_TFax = wx.StaticText(self, -1, label="&Fax:", name="TFax")
        self.text_Fax = wx.TextCtrl(self, -1, value="", style=0, name="Fax_Adresse")
        self.text_Fax.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Fax_Adresse"] = "Fax.ADRESSE"
        self.line8_sizer.AddSpacer(10)
        self.line8_sizer.Add(self.label_TFax,self.left_weight,wx.EXPAND)
        self.line8_sizer.AddSpacer(10) 
        self.line8_sizer.Add(self.text_Fax,self.right_weight,wx.EXPAND)
        self.line8_sizer.AddSpacer(10) 
         
        self.line9_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_TMail = wx.StaticText(self, -1, label="&E-Mail:",  name="TMail")
        self.text_Mail = wx.TextCtrl(self, -1, value="", style=0, name="AdMail")
        self.text_Mail.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["AdMail"] = "Mail.ADRESSE"
        self.line9_sizer.AddSpacer(10)
        self.line9_sizer.Add(self.label_TMail,self.left_weight,wx.EXPAND)
        self.line9_sizer.AddSpacer(10) 
        self.line9_sizer.Add(self.text_Mail,self.right_weight,wx.EXPAND)
        self.line9_sizer.AddSpacer(10) 
        
        self.line10_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_T_StNr = wx.StaticText(self, -1, label="Ste&uerNr:", name="T_StNr")
        self.text_StNr = wx.TextCtrl(self, -1, value="", style=0, name="StNr")
        self.text_StNr.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["StNr"] = "SteuerNr.ADRESSE"
        self.line10_sizer.AddSpacer(10)
        self.line10_sizer.Add(self.label_T_StNr,self.left_weight,wx.EXPAND)
        self.line10_sizer.AddSpacer(10) 
        self.line10_sizer.Add(self.text_StNr,self.right_weight,wx.EXPAND)
        self.line10_sizer.AddSpacer(10) 
       
        self.line11_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.label_T_Geb_Adresse = wx.StaticText(self, -1, label="&Geb:", name="T_Geb_Adresse")
        self.text_Geb_Adresse = wx.TextCtrl(self, -1, value="", style=0, name="Geb_Adresse")
        self.text_Geb_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_Adresse_Geb)
        self.vtextmap["Geb_Adresse"] = "Geburtstag.ADRESSE"
        self.line11_sizer.AddSpacer(10)
        self.line11_sizer.Add(self.label_T_Geb_Adresse,self.left_weight,wx.EXPAND)
        self.line11_right = wx.BoxSizer(wx.HORIZONTAL)
        self.line11_right.Add(self.text_Geb_Adresse,1,wx.EXPAND)
        self.line11_right.AddStretchSpacer(5)        
        self.line11_sizer.AddSpacer(10) 
        self.line11_sizer.Add(self.line11_right,self.right_weight,wx.EXPAND)
        self.line11_sizer.AddSpacer(10) 
 
        self.line12_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        self.button_Merk = wx.Button(self, -1, label="Mer&kmale",  name="Merk")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_Merk, self.button_Merk)
        self.check_Mehrfach = wx.CheckBox(self, -1, label="&Mehrfach", name="Mehrfach", style=wx.ALIGN_RIGHT)
        self.line12_sizer.AddSpacer(10)
        self.line12_sizer.AddStretchSpacer(self.left_weight)
        self.line12_right = wx.BoxSizer(wx.HORIZONTAL)
        self.line12_right.Add(self.button_Merk,1,wx.EXPAND)
        self.line12_right.AddSpacer(10)
        self.line12_right.Add(self.check_Mehrfach,1,wx.EXPAND)
        self.setWx(self.line12_right, [3, 0, 0], [0, 0, 0])        
        self.line12_sizer.AddSpacer(10) 
        self.line12_sizer.Add(self.line12_right,self.right_weight,wx.EXPAND)
        self.line12_sizer.AddSpacer(10) 
 
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line1_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line2_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line3_sizer,2,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line4_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line5_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line6_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line7_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line8_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line9_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line10_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line11_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.line12_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
        #self.sizer.Fit(self)
        
    ## initialize wx widgets of dialog  using panel\n
    # calls setWx to handle Edit and Ok widgets and events
    def InitWx_panel(self):
        panel = wx.Panel(self, -1)
        self.label_T_Vorname_Adresse = wx.StaticText(panel, -1, label="&Vorname:", pos=(14,28), size=(62,18), name="T_Vorname_Adresse")
        self.text_Vorname_Adresse = wx.TextCtrl(panel, -1, value="", pos=(80,26), size=(260,56), style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="Vorname_Adresse")
        self.text_Vorname_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Vorname_Adresse"] = "Vorname.ADRESSE"
        self.label_T_Name_Adresse = wx.StaticText(panel, -1, label="&Name:", pos=(32,90), size=(44,18), name="T_Name_Adresse")
        self.text_Name_Adresse = wx.TextCtrl(panel, -1, value="", pos=(80,88), size=(260,56), style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="Name_Adresse")
        self.text_Name_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Name_Adresse"] = "Name.ADRESSE"
        self.label_T_Strasse_Adresse = wx.StaticText(panel, -1, label="Stra&sse:", pos=(28,152), size=(48,18), name="T_Strasse_Adresse")
        self.text_Strasse_Adresse = wx.TextCtrl(panel, -1, value="", pos=(80,150), size=(260,24), style=0, name="Strasse_Adresse")
        self.text_Strasse_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Strasse_Adresse"] = "Strasse.ADRESSE"
        self.label_T_Plz_Adresse = wx.StaticText(panel, -1, label="&Plz/", pos=(20,182), size=(32,18), name="T_Plz_Adresse")
        self.text_Plz_Adresse = wx.TextCtrl(panel, -1, value="", pos=(80,180), size=(52,24), style=0, name="Plz_Adresse")
        self.text_Plz_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Plz_Adresse"] = "Plz.ADRESSE"
        self.label_T_Ort_Adresse = wx.StaticText(panel, -1, label="O&rt:", pos=(52,182), size=(24,18), name="T_Ort_Adresse")
        self.text_Ort_Adresse = wx.TextCtrl(panel, -1, value="", pos=(132,180), size=(260,24), style=0, name="Ort_Adresse")
        self.text_Ort_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Ort_Adresse"] = "Ort.ADRESSE"
        self.label_T_Telefon_Adresse = wx.StaticText(panel, -1, label="&Telefon:", pos=(22,212), size=(54,18), name="T_Telefon_Adresse")
        self.text_Telefon_Adresse = wx.TextCtrl(panel, -1, value="", pos=(80,210), size=(260,22), style=0, name="Telefon_Adresse")
        self.text_Telefon_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Telefon_Adresse"] = "Telefon.ADRESSE"
        self.text_Tel2 = wx.TextCtrl(panel, -1, value="", pos=(80,232), size=(260,22), style=0, name="Tel2")
        self.text_Tel2.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Tel2"] = "Tel2.ADRESSE"
        self.label_TFax = wx.StaticText(panel, -1, label="&Fax:", pos=(22,256), size=(54,18), name="TFax")
        self.text_Fax = wx.TextCtrl(panel, -1, value="", pos=(80,254), size=(260,22), style=0, name="Fax_Adresse")
        self.text_Fax.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Fax_Adresse"] = "Fax.ADRESSE"
        self.label_TMail = wx.StaticText(panel, -1, label="&E-Mail:", pos=(22,278), size=(54,18), name="TMail")
        self.text_Mail = wx.TextCtrl(panel, -1, value="", pos=(80,276), size=(260,22), style=0, name="Mail_dlg")
        self.text_Mail.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Mail_dlg"] = "Mail.ADRESSE"
        self.label_T_StNr = wx.StaticText(panel, -1, label="Ste&uerNr:", pos=(10,308), size=(66,18), name="T_StNr")
        self.text_StNr = wx.TextCtrl(panel, -1, value="", pos=(80,306), size=(260,22), style=0, name="StNr")
        self.text_StNr.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["StNr"] = "SteuerNr.ADRESSE"
        self.label_T_Geb_Adresse = wx.StaticText(panel, -1, label="&Geb:", pos=(22,338), size=(54,18), name="T_Geb_Adresse")
        self.text_Geb_Adresse = wx.TextCtrl(panel, -1, value="", pos=(80,336), size=(78,22), style=0, name="Geb_Adresse")
        self.text_Geb_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_Adresse_Geb)
        self.vtextmap["Geb_Adresse"] = "Geburtstag.ADRESSE"

        self.button_Merk = wx.Button(panel, -1, label="Mer&kmale", pos=(78,370), size=(80,36), name="Merk")
        self.Bind(wx.EVT_BUTTON, self.On_Adresse_Merk, self.button_Merk)
        #self.button_Suchen = wx.Button(panel, -1, label="&Suchen", pos=(170,370), size=(80,36), name="Suchen")
        #self.Bind(wx.EVT_BUTTON, self.On_Adresse_Auswahl, self.button_Suchen)
      
        self.label_Anrede = wx.StaticText(panel, -1, label="Anre&de:", pos=(8,6), size=(62,18), name="Anrede")
        self.choice_Anrede = wx.Choice(panel, -1,  pos=(80,5), size=(60,20),  choices=["Du", "Sie"],  name="CAnrede")
        self.choicemap["CAnrede"] = "Anrede.ADRESSE"
        self.Bind(wx.EVT_CHOICE, self.On_CAnrede, self.choice_Anrede)      
        self.label_Geschlecht = wx.StaticText(panel, -1, label="&Geschlecht:", pos=(200,6), size=(80,18), name="Geschlecht")      
        self.choice_Geschlecht = wx.Choice(panel, -1,  pos=(290,5), size=(50,20),  choices=["w","n","m"],  name="CGeschlecht")
        self.choice_Geschlecht.SetSelection(1)
        self.choicemap["CGeschlecht"] = "Geschlecht.ADRESSE"
        self.Bind(wx.EVT_CHOICE, self.On_CGeschlecht, self.choice_Geschlecht)
        self.choice_Status = wx.Choice(panel, -1,  pos=(280,338), size=(154,20),  choices=["Passiv", "Aktiv", "Neutral", "Markiert", "Inaktiv"],  name="CStatus")
        self.choicemap["CStatus"] = "Kennung.ADRESSE"
        self.Bind(wx.EVT_CHOICE, self.On_CStatus, self.choice_Status)
        self.setWx(panel, [264, 370, 80, 36], [356, 370, 80, 36]) # set Edit and Ok widgets

    ## attach to database and populate widgets
    def attach_data(self, Adresse, name = None):
        self.new = Adresse.is_new()     
        AfpDialog.attach_data(self, Adresse, self.new)
        if name: 
            self.text_Name_Adresse.SetValue(name)
            self.changed_text.append(self.text_Name_Adresse.GetName())
    ## execution in case the OK button ist hit (overwritten from AfpDialog)
    def execute_Ok(self):
        loop = self.check_Mehrfach.GetValue()
        if loop:
            loop = AfpReq_Question("Einen weitere verbundene Adresse eingeben?","","Mehrfacheingabe Adresse?")
        if self.bulk_nrs and not loop:
            print("AfpDialog_DiAdEin.execute_Ok use bulk:", self.bulk_nrs) 
            for nr in self.bulk_nrs:
                self.data.add_connection(nr)
        self.store_database(loop)
        self.close_dialog = True
        if loop:
            print("AfpDialog_DiAdEin.execute_Ok looping") 
            self.new = True
            self.close_dialog = False
            KNr = self.data.get_value("KundenNr")
            if KNr:
                if self.bulk_nrs is None:
                    nr = self.data.get_value("ParentNr._tmp")
                    if nr:
                        self.bulk_nrs = [nr]
                    else:
                        self.bulk_nrs = []
                self.data.set_new(KNr)
                self.bulk_nrs.append(KNr)
                self.Populate()
            print("AfpDialog_DiAdEin.execute_Ok set bulk_nrs:" , self.bulk_nrs)
    ## local routine to execute database storage
    # @param loop - flag if parts of data should be kept for next loop
    def store_database(self, loop=False):
        self.Ok = False
        data = {}
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        for entry in self.choicevalues:
            name = entry.split(".")[0]
            data[name] = self.choicevalues[entry]
        if self.new: 
            data = self.complete_data(data)
            if len(data) > 1:
                self.data.set_data_values(data)
            self.Ok = True
        elif data or self.change_data:
            if data: self.data.set_data_values(data)
            self.Ok = True
        if self.Ok:
            self.data.store()
            self.new = False               
        if not loop: self.changed_text = []
    ## complete data if necessary
    # @param data - data dictionary to be completed to assure necessary datafields to be set
    def complete_data(self, data):
        if not "Vorname" in data:
            data["Vorname"] = ""
        if not "Kennung" in data:
            data["Kennung"] = 0
        if not "Geschlecht" in data:
            data["Geschlecht"] = self.choice_Geschlecht.GetStringSelection()
        if not "Anrede" in data:
            data["Anrede"] = self.choice_Anrede.GetStringSelection()
        return data
    ## populate choice widgets ((overwritten from AfpDialog)
    def Pop_choice(self):
      for entry in self.choicemap:
            Choice= self.FindWindowByName(entry)
            if entry == "CStatus":         
                stat = self.data.get_value(self.choicemap[entry])
                if not stat: stat = 0
                cset = AfpAdresse_StatusMap()[stat]
                Choice.SetSelection(cset) 
            else:
                value = self.data.get_string_value(self.choicemap[entry])
                Choice.SetStringSelection(value)
   
    ## Eventhandler CHOICE - change form of address 'anrede'
    def On_CAnrede(self,event = None):
        self.choicevalues["Anrede.ADRESSE"] = self.choice_Anrede.GetStringSelection()   
        if event: event.Skip()  
    ## Eventhandler CHOICE - change gender 'geschlecht'
    def On_CGeschlecht(self,event = None):
        self.choicevalues["Geschlecht.ADRESSE"] = self.choice_Geschlecht.GetStringSelection()   
        if event: event.Skip()  
    ## Eventhandler CHOICE - change internal status flag
    def On_CStatus(self,event= None ):
        self.choicevalues["Kennung.ADRESSE"] = AfpAdresse_StatusReMap(self.choice_Status.GetCurrentSelection())
        if event: event.Skip()  
    ## Eventhandler date TEXTBOX - change birthday
    def On_Adresse_Geb(self,event):
        if self.debug: print("Event handler `On_Adresse_Geb'")
        gtag = self.text_Geb_Adresse.GetValue()
        gtag =  Afp_ChDatum(gtag, True)
        self.text_Geb_Adresse.SetValue(gtag)
        self.On_KillFocus(event)
        event.Skip()
    ## Eventhandler BUTTON - invoke dialog to change attributes
    def On_Adresse_Merk(self,event):
        if self.debug: print("Event handler `On_Adresse_Merk'")
        if self.new: self.store_database()
        data = AfpLoad_DiAdEin_SubMrk(self.data)
        if data: 
            self.data = data
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
            self.change_data = True
        event.Skip()
  
## loader routines for dialog DiAdEin 
# @param Adresse - AfpAdresse holding data
# @param name - name to be set in dialog
def AfpLoad_DiAdEin(Adresse, name = None):
    DiAdEin = AfpDialog_DiAdEin(None)
    DiAdEin.attach_data(Adresse, name)
    DiAdEin.ShowModal()
    Ok = DiAdEin.get_Ok()
    DiAdEin.Destroy()
    return Ok   
## loader routines for dialog DiAdEin with AfpSuperbase input
# @param globals - global variables including database connection
# @param sb - AfpSuperbase object to extract actuel adressdata from
# @param name - name to be set in dialog
def AfpLoad_DiAdEin_fromSb(globals, sb, name = None):
    Adresse = AfpAdresse(globals, None, sb, sb.debug)
    return AfpLoad_DiAdEin(Adresse, name)
## loader routines for dialog DiAdEin with ident number (KundenNr) input
# @param globals - global variables including database connection
# @param KNr - address ident number (KundenNr)
def AfpLoad_DiAdEin_fromKNr(globals, KNr):
    Adresse = AfpAdresse(globals, KNr, None, globals.debug)
    return AfpLoad_DiAdEin(Adresse)
   
## Class for attribut sub-dialog , it displays dialog to show and manipulate attribut-data (AdresAtt) and handles interactions \n
class AfpDialog_DiAdEin_SubMrk(AfpDialog):
    def __init__(self, *args, **kw):
        self.changes = False
        self.changedlists = False
        AfpDialog.__init__(self,None, -1, "")
        self.SetSize((358,225))
        self.SetTitle("Adressenmerkmale")

    ## initialize wx widgets of dialog  \n
    # calls setWx to handle Edit and Ok widgets and events
    def InitWx(self):
        #self.InitWx_panel()
        self.InitWx_sizer()
        
    ## initialize wx widgets of dialog with panel\n
    # calls setWx to handle Edit and Ok widgets and events
    def InitWx_panel(self):
        panel = wx.Panel(self, -1)
        self.list_attribut = wx.ListBox(panel, -1, pos=(8,2) , size=(170, 80), name="Attribut")
        self.listmap.append("Attribut")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Attribut, self.list_attribut)
        self.button_Ad_Attribut = wx.Button(panel, -1, label="Mer&kmal", pos=(8,86), size=(100,32), name="Ad_Attribut")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Merkmal, self.button_Ad_Attribut)      
        self.list_verbindung = wx.ListBox(panel, -1, pos=(180,2) , size=(170, 80), name="Verbindung")
        self.listmap.append("Verbindung")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Verbindung, self.list_verbindung)
        self.button_Ad_Attr_Verbind = wx.Button(panel, -1, label="&Verbindung", pos=(250,86), size=(100,32), name="Ad_Attr_Verbind")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Verbindung, self.button_Ad_Attr_Verbind)
        self.choice_Status = wx.Choice(panel, -1, pos=(124,86), size=(100,32), choices=AfpAdresse_StatusStrings(),  name="CStatus")
        self.Bind(wx.EVT_CHOICE, self.On_CStatus, self.choice_Status)
        self.choicemap["CStatus"] = "Kennung.ADRESSE"
        self.text_Ad_Attr_Bem = wx.TextCtrl(panel, -1, value="", pos=(8,126), size=(342,26), style=0, name="Ad_Attr_Bem")
        self.textmap["Ad_Attr_Bem"] = "Bem.ADRESSE"
        self.text_Ad_Attr_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.button_Ad_Attr_Bemerk = wx.Button(panel, -1, label="&Bemerkung", pos=(8,158), size=(100,32), name="Ad_Attr_Bemerk")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Bem, self.button_Ad_Attr_Bemerk)
        self.setWx(panel, [129, 158, 100, 32], [250, 158, 100, 32]) # set Edit and Ok widgets

    def InitWx_sizer(self):
        self.list_attribut = wx.ListBox(self, -1, name="Attribut")
        self.listmap.append("Attribut")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Attribut, self.list_attribut)        
        self.list_verbindung = wx.ListBox(self, -1, name="Verbindung")
        self.listmap.append("Verbindung")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Verbindung, self.list_verbindung)  
        # sizer
        self.sizer_line1 = wx.BoxSizer(wx.HORIZONTAL)     
        self.sizer_line1.AddSpacer(10)        
        self.sizer_line1.Add(self.list_attribut,1,wx.EXPAND)
        self.sizer_line1.AddSpacer(10)
        self.sizer_line1.Add(self.list_verbindung,1,wx.EXPAND)
        self.sizer_line1.AddSpacer(10)
        
        self.button_Ad_Attribut = wx.Button(self, -1, label="Mer&kmal", name="Ad_Attribut")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Merkmal, self.button_Ad_Attribut)      
        self.choice_Status = wx.Choice(self, -1, choices=AfpAdresse_StatusStrings(),  name="CStatus")
        self.Bind(wx.EVT_CHOICE, self.On_CStatus, self.choice_Status)
        self.choicemap["CStatus"] = "Kennung.ADRESSE"
        self.button_Ad_Attr_Verbind = wx.Button(self, -1, label="&Verbindung", name="Ad_Attr_Verbind")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Verbindung, self.button_Ad_Attr_Verbind)
        # sizer
        self.sizer_line2 = wx.BoxSizer(wx.HORIZONTAL)        
        self.sizer_line2.AddStretchSpacer(1)
        self.sizer_line2.Add(self.button_Ad_Attribut,4,wx.EXPAND)
        self.sizer_line2.AddStretchSpacer(1)
        self.sizer_line2.Add(self.choice_Status,4,wx.EXPAND)
        self.sizer_line2.AddStretchSpacer(1)
        self.sizer_line2.Add(self.button_Ad_Attr_Verbind,4,wx.EXPAND)
        self.sizer_line2.AddStretchSpacer(1)
        
        self.text_Ad_Attr_Bem = wx.TextCtrl(self, -1, value="", style=0, name="Ad_Attr_Bem")
        self.textmap["Ad_Attr_Bem"] = "Bem.ADRESSE"
        self.text_Ad_Attr_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        # sizer
        self.sizer_line3 = wx.BoxSizer(wx.HORIZONTAL)     
        self.sizer_line3.AddSpacer(10)        
        self.sizer_line3.Add(self.text_Ad_Attr_Bem,1,wx.EXPAND)
        self.sizer_line3.AddSpacer(10)
        
        self.button_Ad_Attr_Bemerk = wx.Button(self, -1, label="&Bemerkung", name="Ad_Attr_Bemerk")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Bem, self.button_Ad_Attr_Bemerk)
        self.sizer_line4 = wx.BoxSizer(wx.HORIZONTAL) 
        self.sizer_line4.AddStretchSpacer(1)        
        self.sizer_line4.Add(self.button_Ad_Attr_Bemerk,4,wx.EXPAND)
        self.setWx(self.sizer_line4, [1, 4, 1], [0, 4, 1]) # set Edit and Ok widgets
        
        self.sizer = wx.BoxSizer(wx.VERTICAL) 
        self.sizer.AddSpacer(10)    
        self.sizer.Add(self.sizer_line1,2,wx.EXPAND)        
        self.sizer.AddSpacer(10)    
        self.sizer.Add(self.sizer_line2,0,wx.EXPAND)        
        self.sizer.AddSpacer(10)    
        self.sizer.Add(self.sizer_line3,1,wx.EXPAND)        
        self.sizer.AddSpacer(10)    
        self.sizer.Add(self.sizer_line4,0,wx.EXPAND)        
        self.sizer.AddSpacer(10)    
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)


    ## Population routine for status choice
    def Pop_choice(self):
        map = AfpAdresse_StatusMap()
        value = self.data.get_value("Kennung")
        index = map[value]
        self.choice_Status.SetSelection(index)
        #print "AfpDialog_DiAdEin_SubMrk.Pop_Choice:", self.choice_Status.GetString(index)
    ## Population routine for attribut list
    def Pop_Attribut(self):
        rows = self.data.get_value_rows("ADRESATT", "Attribut,AttText")
        liste = []
        for row in rows:
            liste.append(Afp_toString(row[0]) + " " + Afp_toString(row[1]))
        liste = Afp_ArraytoString(liste)
        self.list_attribut.Clear()
        if liste:
            self.list_attribut.InsertItems(liste, 0)
    ## Population routine for connected adresses list
    def Pop_Verbindung(self):
        rows = self.data.get_value_rows("Bez", "Vorname,Name")
        liste = []
        for row in rows:
            liste.append(Afp_toString(row[0] + " " + row[1]))
        #print "AfpDialog_DiAdEin_SubMrk.Pop_Verbindung:",  liste
        self.list_verbindung.Clear()
        if liste:
            self.list_verbindung.InsertItems(liste, 0)

    ## overwritten from AfpDialog, because also buttons are dis/enabled
    def Set_Editable(self, ed_flag, lock_data = None):
        AfpDialog.Set_Editable(self, ed_flag)
        self.button_Ad_Attribut.Enable(ed_flag)
        self.button_Ad_Attr_Verbind.Enable(ed_flag)
        self.button_Ad_Attr_Bemerk.Enable(ed_flag)
        self.use_changedlists = ed_flag
    ## return if content has changed
    def has_changed(self):
        if self.use_changedlists:
            return (self.changed_text or self.changes)
        else:
            return False
    ## return data if content has changed
    def get_changed_data(self):
        data = None
        if self.has_changed():
            return self.data
        else:
            return None
     

    ## Eventhandler LIST - double click in attribut list
    def On_DClick_Attribut(self,event):
        if self.debug: print("AfpDialog_DiAdEin_SubMrk Event handler `On_DClick_Attribut'")
        index = self.list_attribut.GetSelections()[0]
        if self.is_editable() and index >= 0:
            name = self.data.get_name()
            selection = self.data.get_selection("ADRESATT")
            #attribut = Afp_toString(selection.get_values("Attribut", index)[0][0])
            row = selection.get_values("Attribut,AttText,Tag,Aktion", index)[0]
            #print "AfpDialog_DiAdEin_SubMrk.On_DClick_Attribut:", row
            attribut = Afp_toString(row[0])
            text = Afp_toString(row[1])
            tag = Afp_toString(row[2])
            action = Afp_toString(row[3])

            Ok, text, tag = AfpAdresse_spezialAttribut(name, attribut, text, tag, action)
            #print "AfpDialog_DiAdEin_SubMrk.On_DClick_Attribut action:",Ok, text, tag
            if Ok is None:
                Ok = AfpReq_Question("Soll das Merkmal '" + attribut + "'", "für diese Adresse gelöscht werden?", "Löschen?")
                if Ok:
                    #mani = [index, None]
                    #selection.manipulate_data([mani])
                    selection.delete_row(index)
                    self.changes = True
            elif Ok:
                selection.set_value("Tag", tag, index)
                selection.set_value("AttText", text, index)
                self.changes = True
            #print "AfpDialog_DiAdEin_SubMrk.On_DClick_Attribut selection:",selection.data
            self.Pop_Attribut()
        event.Skip()  
    ## Eventhandler LIST - double click in connected addresses list
    def On_DClick_Verbindung(self,event):
        if self.debug: print("AfpDialog_DiAdEin_SubMrk Event  handler `On_DClick_Verbindung'")
        index = self.list_verbindung.GetSelections()[0]
        if self.is_editable() and index >= 0:
            selection = self.data.get_selection("Bez")
            name = selection.get_values("Vorname", index)[0][0] + " " + selection.get_values("Name", index)[0][0]
            Ok = AfpReq_Question("Soll die Verbindung zu '" + name + "'", "für diese Adresse gelöscht werden?", "Löschen?")
            if Ok:
                #mani = [index, None]
                #selection.manipulate_data([mani])
                selection.delete_row(index)
                self.changes = True
                self.Pop_Verbindung()
        event.Skip()  
    ## Eventhandler BUTTON - add new entry to attribut list   
    def On_CStatus(self,event):
        if self.debug: print("AfpDialog_DiAdEin_SubMrk Event  handler `On_CStatus'!")
        index = self.choice_Status.GetSelection()
        self.data.set_value("Kennung", AfpAdresse_StatusReMap(index))
        self.changes = True
        event.Skip()
     ## Eventhandler BUTTON - add new entry to attribut list   
    def On_Ad_Merkmal(self,event):
        if self.debug: print("AfpDialog_DiAdEin_SubMrk Event  handler `On_Ad_Merkmal'!")
        ok, row = AfpAdresse_selectAttributRow(self.data)
        #print "AfpDialog_DiAdEin_SubMrk.On_Ad_Merkmal:", row
        if ok and row:
            #self.data.view()
            self.data.get_selection("ADRESATT").add_row(row)
            self.changes = True
            self.Pop_Attribut()
        event.Skip()
    ## Eventhandler BUTTON - add new entry to connected addresses list   
    def On_Ad_Verbindung(self,event):
        if self.debug: print("AfpDialog_DiAdEin_SubMrk Event  handler `On_Ad_Verbindung'")
        name = self.data.get_value("Name")
        #text = "Bitte Adresse auswählen die mit der aktuellen in verbunden werden soll."
        auswahl = AfpLoad_AdAusw(self.data.get_globals(), "ADRESSE", "NamSort", name)
        if not auswahl is None:
            self.data.add_connection(auswahl)
            self.changes = True
            self.Pop_Verbindung()
            # print KNr
        event.Skip()
    ## Eventhandler BUTTON - add extern file for remaks \n
    # not yet implemented! \n
    # Possibly not needed anymore, as textfields nowerdays can store a lot of information!
    def On_Ad_Bem(self,event):
        print("AfpDialog_DiAdEin_SubMrk Event  handler `On_Ad_Bem' not implemented!")
        event.Skip()

## loader routine for attribut sub-dialog
# @param Adresse - AfpAdresse object to hold the data to be displayed or modified
def AfpLoad_DiAdEin_SubMrk(Adresse):
    DiAdMrk = AfpDialog_DiAdEin_SubMrk(None)
    DiAdMrk.attach_data(Adresse)
    DiAdMrk.ShowModal()
    data = DiAdMrk.get_changed_data()
    DiAdMrk.Destroy()
    return data
   
