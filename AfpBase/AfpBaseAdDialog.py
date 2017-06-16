#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseAdDialog
# AfpBaseAdDialog module provides the dialogs and appropriate loader routines needed for adress handling
# it holds the calsses
# - AfpDialog_AdAusw
# - AfpDialog_AdAttAusw
#
#   History: \n
#        24 Jan. 2015 - add auto selection - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2015  afptech.de (Andreas Knoblauch)
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
from AfpBase import AfpBaseRoutines, AfpBaseDialog, AfpBaseDialogCommon, AfpBaseAdRoutines, AfpUtilities
from AfpBase.AfpUtilities import AfpStringUtilities
from AfpBase.AfpUtilities.AfpStringUtilities import Afp_ArraytoString
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpBaseDialog import *
from AfpBase.AfpBaseDialogCommon import *
from AfpBase.AfpBaseAdRoutines import *

## select adress attribut or enter new \n
# return row or 'None' in case nothing is selected
# @param Adresse - AfpSelectionList holding adress data
def AfpAdDi_selectAttributRow(Adresse):
    sel = Adresse.get_selection("ADRESATT")
    liste, rows = Afp_getListe_fromTableSelection( sel, "KundenNr = 0", "Attribut", "Attribut")
    if not liste[0]: liste[0] = "\"Neues Adressenmerkmal\""
    name = Adresse.get_name()
    liste = Afp_ArraytoString(liste)
    row, ok = AfpReq_Selection("Bitte Adressmerkmal für".decode("UTF-8") , name + " auswählen.".decode("UTF-8") , liste, "Merkmalauswahl", rows)
    #index = sel.get_feldindices("Attribut,Tag,AttText")
    index = sel.get_feldindices("Attribut,AttText,Tag,Aktion")
    if not row[index[0]] and ok:
        attribut, ok = AfpReq_Text("Bitte Bezeichnung für neues Adressenmerkmal eingeben.","Dieses Merkmal wird " + name + " zugeordnet.")
        if ok: row[index[0]] = attribut
    else:
        attribut = row[index[0]]
    if ok:
        AttText = row[index[1]]      
        Tag =  row[index[2]] 
        Aktion =  row[index[3]] 
        ok, AttText, Tag = AfpAdDi_spezialAttribut(name, attribut, AttText, Tag, Aktion, True)
        if ok:  
            row[index[1]] = AttText
            row[index[2]]  = Tag
    if ok: return row
    else: return None
   
## handling routine to set text and/or special values needed for an attribut \n
# @param name - name of address this attribut belongs to
# @param attribut - name of  attribut to be modified
# @param text - additional text string for this attribut
# @param tag - individual data string holding all values for this special attribut
# @param action - individual string holding names of values for this special attribut
# @param no_delete - flag if 'delete' button should be hidden
def AfpAdDi_spezialAttribut(name, attribut, text, tag, action, no_delete = False):
    Ok = None
    taglist= None
    list = []
    attribut = Afp_toString(attribut)
    #print "AfpAdDi_spezialAttribut:", attribut, type(attribut), tag, action, Ok
    if action:
        taglist = action.split(",")
    if not taglist or len(taglist) == 1:
        taglist = AfpAdresse_getAttributTagList(attribut)
    #print "AfpAdDi_spezialAttribut taglist:", tag, taglist
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
            if "sichtbar" in taglist[i]: 
                ind_text = i
                continue
            entry = [taglist[i] + ":"]
            if cnt < lspl: 
                entry.append(split[cnt])
                cnt += 1
            else: entry.append("")
            list.append(entry)
    if not text: text = ""
    if ind_text < 0: list.append(["(optional) Merkmaltext:", text])
    else: list.append([taglist[ind_text] + ":", text])
    #print "AfpAdDi_spezialAttribut MultiLine:", name, attribut, list
    result = AfpReq_MultiLine("Für '".decode("UTF-8") + name + "' werden die folgenden " + attribut +"-Daten benötigt:".decode("UTF-8"), "", "Text", list, attribut, 400 , no_delete)
    if not result is None: Ok = False
    if result:
        changed = False
        for i in range(len(taglist)):
            if not list[i][1] == result[i]:
                changed = True
        if changed: 
            tag = Afp_ArraytoLine(result, ",", len(result)-1)
            Ok = True
        if not list[-1][1] == result[-1]:
            text = result[-1]
            Ok = True
    return Ok, text, tag

## dialog for selection of adress data \n
# selects an entry from the adress table
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
        if search is None: search = "a"
        debug = True
        Adresse = AfpAdresse(globals, None, None, debug, False)
        Ok = AfpLoad_DiAdEin(Adresse, search)
        return Ok
## dialog for adress selection from attribut \n 
# selects an entry of the adress table by choosing from the attribut (AdresAtt) table   
class AfpDialog_AdAttAusw(AfpDialog_Auswahl):
    ## initialise class
    def __init__(self):
        AfpDialog_Auswahl.__init__(self,None, -1, "", style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.typ = "Adressenauswahl"
        self.datei = "ADRESATT"        
        self.modul = "Adresse"
        # remove 'Neu'-button from panel
        self.button_Neu.Destroy()
    ## get the definition of the selection grid content \n
    # overwritten for "Adressen-attribut" use
    def get_grid_felder(self):  
        Felder = [["Name.AdresAtt.Name",30], 
                            ["Vorname.Adresse.Name", 20], 
                            ["Strasse.Adresse",30], 
                            ["Ort.Adresse",20], 
                            ["KundenNr.AdresAtt = KundenNr.Adresse",None]] 
        return Felder

## loader routine for adress selection dialog
def AfpLoad_AdAusw(globals, Datei, index, value = "", where = None, attribut_text = None, ask = False):
    result = None
    Ok = True
    if ask:
        sort_list = AfpAdresse_getOrderlistOfTable(globals.get_mysql(), index, Datei)
        value, index, Ok = Afp_autoEingabe(value, index, sort_list, "Adressen","Bitte Namen eingeben:")
    if Ok:
        if Datei == "ADRESATT":
            DiAusw = AfpDialog_AdAttAusw()
        else:
            DiAusw = AfpDialog_AdAusw()
        #print "AfpLoad_AdAusw:", Datei, Index, value, where
        if attribut_text:
            if len(attribut_text) > 4 and attribut_text[:5] == "Bitte":
                text = attribut_text
            else:
                text = "Bitte " + attribut_text + "-Adresse auswählen:".decode("UTF-8")
        else:
            text = "Bitte Adresse auswählen:".decode("UTF-8")
        DiAusw.initialize(globals, index, value, where, text)        
        DiAusw.ShowModal()
        result = DiAusw.get_result()
        DiAusw.Destroy()
    elif Ok is None:
        # flag for direct selection
        result = Afp_selectGetValue(globals.get_mysql(), Datei, "KundenNr", index, value)
    return result
## loader routine to select adress data from attribut table
def AfpLoad_AdAttAusw(globals, attribut, value = ""):     
        Datei = "ADRESATT"
        Index = "Name"
        where = "Attribut.ADRESATT = \"" + attribut.decode("UTF-8") + "\" and KundenNr.ADRESATT > 0"
        if not value: value = "a"
        result = AfpLoad_AdAusw(globals, Datei, Index, value, where, attribut)
        return result

## Class AfpDialog_DiAdEin display dialog to show and manipulate address-data (Adresse) and handles interactions \n
class AfpDialog_DiAdEin(AfpDialog):
    def __init__(self, *args, **kw):
        self.change_data = False
        self.choicevalues = {}
        AfpDialog.__init__(self,None, -1, "")
        self.lock_data = True
        self.SetSize((452,447))
        self.SetTitle("Adresse")
      
    ## initialize wx widgets of dialog  \n
    # calls setWx to handle Edit and Ok widgets and events
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.label_T_Vorname_Adresse = wx.StaticText(panel, -1, label="&Vorname:", pos=(14,28), size=(62,18), name="T_Vorname_Adresse")
        self.text_Vorname_Adresse = wx.TextCtrl(panel, -1, value="", pos=(80,26), size=(260,56), style=wx.TE_MULTILINE|wx.TE_LINEWRAP, name="Vorname_Adresse")
        self.text_Vorname_Adresse.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Vorname_Adresse"] = "Vorname.ADRESSE"
        self.label_T_Name_Adresse = wx.StaticText(panel, -1, label="&Name:", pos=(32,90), size=(44,18), name="T_Name_Adresse")
        self.text_Name_Adresse = wx.TextCtrl(panel, -1, value="", pos=(80,88), size=(260,56), style=wx.TE_MULTILINE|wx.TE_LINEWRAP, name="Name_Adresse")
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
        self.text_Fax = wx.TextCtrl(panel, -1, value="", pos=(80,254), size=(260,22), style=0, name="Fax")
        self.text_Fax.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Fax"] = "Fax.ADRESSE"
        self.label_TMail = wx.StaticText(panel, -1, label="&E-Mail:", pos=(22,278), size=(54,18), name="TMail")
        self.text_Mail = wx.TextCtrl(panel, -1, value="", pos=(80,276), size=(260,22), style=0, name="Mail")
        self.text_Mail.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.textmap["Mail"] = "Mail.ADRESSE"
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
        self.choice_Geschlecht = wx.Choice(panel, -1,  pos=(290,5), size=(50,20),  choices=["W","N","M"],  name="CGeschlecht")
        self.choicemap["CGeschlecht"] = "Geschlecht.ADRESSE"
        self.Bind(wx.EVT_CHOICE, self.On_CGeschlecht, self.choice_Geschlecht)
        self.choice_Status = wx.Choice(panel, -1,  pos=(280,338), size=(154,20),  choices=["Passiv", "Aktiv", "Neutral", "Markiert", "Inaktiv"],  name="CStatus")
        self.choicemap["CStatus"] = "Kennung.ADRESSE"
        self.Bind(wx.EVT_CHOICE, self.On_CStatus, self.choice_Status)
        self.setWx(panel, [264, 370, 80, 36], [356, 370, 80, 36]) # set Edit and Ok widgets

    ## attach to database and populate widgets
    def attach_data(self, Adresse, name = None):
        self.new = Adresse.is_new()     
        if name: 
            self.text_Name_Adresse.SetValue(name)
            self.changed_text.append(self.text_Name_Adresse.GetName())
        AfpDialog.attach_data(self, Adresse, self.new)
    ## execution in case the OK button ist hit (overwritten from AfpDialog)
    def execute_Ok(self):
        self.store_database()
    ## local routine to execute database storage
    def store_database(self):
        self.Ok = False
        data = {}
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        for entry in self.choicevalues:
            name = entry.split(".")[0]
            data[name] = self.choicevalues[entry]
        if self.new and len(data) > 1:
            self.data.set_data_values(data)
            self.Ok = True
        elif data or self.change_data:
            if data: self.data.set_data_values(data)
            self.Ok = True
        if self.Ok:
            if self.data.get_value("Kennung") is None:
                print "AfpDialog_DiAdEin.store_database set default 'Kennung' -> passiv"
                self.data.set_value("Kennung",0)
            self.data.store()
            self.new = False               
        self.changed_text = []
    ## populate choice widgets ((overwritten from AfpDialog)
    def Pop_choice(self):
      for entry in self.choicemap:
            Choice= self.FindWindowByName(entry)
            if entry == "CStatus":         
                stat = self.data.get_value(self.choicemap[entry])
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
        if self.debug: print "Event handler `On_Adresse_Geb'"
        gtag = self.text_Geb_Adresse.GetValue()
        gtag =  Afp_ChDatum(gtag, True)
        self.text_Geb_Adresse.SetValue(gtag)
        self.On_KillFocus(event)
        event.Skip()
    ## Eventhandler BUTTON - invoke dialog to change attributes
    def On_Adresse_Merk(self,event):
        if self.debug: print "Event handler `On_Adresse_Merk'"
        #if len(self.changed_text): self.store_database()
        changed = AfpLoad_DiAdEin_SubMrk(self.data)
        if changed:      
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
        self.changes = {}
        self.changedlists = False
        AfpDialog.__init__(self,None, -1, "")
        self.SetSize((358,225))
        self.SetTitle("Adressenmerkmale")

    ## initialize wx widgets of dialog  \n
    # calls setWx to handle Edit and Ok widgets and events
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.list_attribut = wx.ListBox(panel, -1, pos=(8,2) , size=(170, 80), name="Attribut")
        self.listmap.append("Attribut")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Attribut, self.list_attribut)
        self.changes["Attribut"] = []
        self.button_Ad_Attribut = wx.Button(panel, -1, label="Mer&kmal", pos=(8,86), size=(100,32), name="Ad_Attribut")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Merkmal, self.button_Ad_Attribut)      
        self.list_verbindung = wx.ListBox(panel, -1, pos=(180,2) , size=(170, 80), name="Verbindung")
        self.listmap.append("Verbindung")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_DClick_Verbindung, self.list_verbindung)
        self.changes["Verbindung"] = []
        self.button_Ad_Attr_Verbind = wx.Button(panel, -1, label="&Verbindung", pos=(250,86), size=(100,32), name="Ad_Attr_Verbind")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Verbindung, self.button_Ad_Attr_Verbind)
        self.text_Ad_Attr_Bem = wx.TextCtrl(panel, -1, value="", pos=(8,126), size=(342,26), style=0, name="Ad_Attr_Bem")
        self.textmap["Ad_Attr_Bem"] = "Bem.ADRESSE"
        self.text_Ad_Attr_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.button_Ad_Attr_Bemerk = wx.Button(panel, -1, label="&Bemerkung", pos=(8,158), size=(100,32), name="Ad_Attr_Bemerk")
        self.Bind(wx.EVT_BUTTON, self.On_Ad_Bem, self.button_Ad_Attr_Bemerk)
        self.setWx(panel, [129, 158, 100, 32], [250, 158, 100, 32]) # set Edit and Ok widgets

    ## Population routine for attribut list
    def Pop_Attribut(self):
        rows = self.data.get_value_rows("ADRESATT", "Attribut,AttText")
        liste = []
        for row in rows:
            liste.append(Afp_toString(row[0]) + " " + Afp_toString(row[1]))
        liste = Afp_ArraytoString(liste)
        self.list_attribut.Clear()
        self.list_attribut.InsertItems(liste, 0)
    ## Population routine for connected adresses list
    def Pop_Verbindung(self):
        rows = self.data.get_value_rows("Bez", "Vorname,Name")
        liste = []
        for row in rows:
            liste.append(row[0] + " " + row[1])
        #print liste
        self.list_verbindung.Clear()
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

    ## Eventhandler LIST - double click in attribut list
    def On_DClick_Attribut(self,event):
        if self.debug: print "Event handler `On_DClick_Attribut'"
        index = self.list_attribut.GetSelections()[0]
        if self.is_editable() and index >= 0:
            name = self.data.get_name()
            selection = self.data.get_selection("ADRESATT")
            #attribut = Afp_toString(selection.get_values("Attribut", index)[0][0])
            row = selection.get_values("Attribut,AttText,Tag,Aktion", index)[0]
            print "AfpDialog_DiAdEin_SubMrk.On_DClick_Attribut:", row
            attribut = Afp_toString(row[0])
            text = Afp_toString(row[1])
            tag = Afp_toString(row[2])
            action = Afp_toString(row[3])

            Ok, text, tag = AfpAdDi_spezialAttribut(name, attribut, text, tag, action)
            if Ok is None:
                Ok = AfpReq_Question("Soll das Merkmal '" + attribut + "'", "für diese Adresse gelöscht werden?".decode("UTF-8"), "Löschen?".decode("UTF-8"))
                if Ok:
                    #mani = [index, None]
                    #selection.manipulate_data([mani])
                    selection.delete_row(index)
                    self.changes["Attribut"].append(index)
            elif Ok:
                selection.set_value("Tag", tag, index)
                selection.set_value("AttText", text, index)
                self.changes["Attribut"].append("Tag")
                self.changes["Attribut"].append("AttText")
            if Ok: self.Pop_Attribut()
        event.Skip()  
    ## Eventhandler LIST - double click in connected addresses list
    def On_DClick_Verbindung(self,event):
        if self.debug: print "Event handler `On_DClick_Verbindung'"
        index = self.list_verbindung.GetSelections()[0]
        if self.is_editable() and index >= 0:
            selection = self.data.get_selection("Bez")
            name = selection.get_values("Vorname", index) + " " + selection.get_values("Name", index)
            Ok = AfpReq_Question("Soll die Verbindung zu '" + name + "'", "für diese Adresse gelöscht werden?".decode("UTF-8"), "Löschen?".decode("UTF-8"))
            if Ok:
                #mani = [index, None]
                #selection.manipulate_data([mani])
                selection.delete_row(index)
                self.changes["Verbindung"].append(index)
                self.Pop_Verbindung()
        event.Skip()  
    ## Eventhandler BUTTON - add new entry to attribut list   
    def On_Ad_Merkmal(self,event):
        if self.debug: print "Event handler `On_Ad_Merkmal'!"
        row = AfpAdDi_selectAttributRow(self.data)
        #print "On_Ad_Merkmal:", row
        if row:
            if row[0] == 0: # here additional manipulation for new  dataset can be made
                row[0] = self.data.get_value("KundenNr")
                row[1] = self.data.get_name(True)
            #print "On_Ad_Merkmal add row:", row
            self.data.get_selection("ADRESATT").add_row(row)
            self.changes["Attribut"].append(row)
            self.Pop_Attribut()
        event.Skip()
    ## Eventhandler BUTTON - add new entry to connected addresses list   
    def On_Ad_Verbindung(self,event):
        if self.debug: print "Event handler `On_Ad_Verbindung'"
        name = self.data.get_value("Name")
        text = "Bitte Adresse auswählen die mit der aktuellen in verbunden werden soll."
        auswahl = AfpLoad_AdAusw(self.data.get_mysql(), "ADRESSE", "NamSort", text, name[0])
        if not auswahl is None:
            KNr = int(auswahl)
            rows = self.data.get_mysql().select("*","KundenNr = " + Afp_toString(KNr), "ADRESSE") 
            mani = [None, rows[0]]       
            self.data.get_selection("Bez").manipulate_data([mani])
            self.changes["Verbindung"].append(mani)
            self.Pop_Verbindung()
            # print KNr
        event.Skip()
    ## Eventhandler BUTTON - add extern file for remaks \n
    # not yet implemented! \n
    # Possibly not needed anymore, as textfields nowerdays can store a lot of information!
    def On_Ad_Bem(self,event):
        print "Event handler `On_Ad_Bem' not implemented!"
        event.Skip()

## loader routine for attribut sub-dialog
# @param Adresse - AfpAdresse object to hold the data to be displayed or modified
def AfpLoad_DiAdEin_SubMrk(Adresse):
    DiAdMrk = AfpDialog_DiAdEin_SubMrk(None)
    DiAdMrk.attach_data(Adresse)
    DiAdMrk.ShowModal()
    changed = DiAdMrk.has_changed()
    DiAdMrk.Destroy()
    return changed
   