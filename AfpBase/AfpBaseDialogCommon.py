#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseDialogCommon
# AfpBaseDialogCommon module provides common used dialogs.
# it holds the calsses
# - AfpDialog_DiReport - common output dialog
# - AfpDialog_DiAusw - common selection dialog for unlimited choices
#
#   History: \n
#        26 Feb. 2015 - split from AfpBaseDialog - Andreas.Knoblauch@afptech.de \n

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

import AfpUtilities.AfpBaseUtilities
from AfpUtilities.AfpBaseUtilities import Afp_existsFile, Afp_copyFile, Afp_readFileNames, Afp_genHomeDir, Afp_addPath
import AfpUtilities.AfpStringUtilities
from AfpUtilities.AfpStringUtilities import Afp_addRootpath, Afp_ArraytoLine, Afp_toString, Afp_ArraytoString

import AfpDatabase.AfpSQL
from AfpDatabase.AfpSQL import AfpSQLTableSelection

import AfpBaseRoutines
from AfpBaseRoutines import Afp_archivName, Afp_startFile, Afp_printSelectionListDataInfo, AfpMailSender, Afp_readExtraInfo
import AfpBaseDialog
from AfpBaseDialog import *
import AfpAusgabe
from AfpAusgabe import AfpAusgabe

    
# Common dialog routines to be used in different modules
## Displays Info dialog of product
# @param globals - global variables to hold information data \n
# used values are - name, version, description, copyright, website, license, developer
def AfpReq_Information(globals):
    imagefile = Afp_addRootpath(globals.get_value("start-path"), globals.get_value("picture"))
    info = wx.AboutDialogInfo()
    info.SetIcon(wx.Icon(imagefile, wx.BITMAP_TYPE_PNG))
    info.SetName(globals.get_string_value("name"))
    info.SetVersion(globals.get_string_value("version"))
    info.SetDescription(globals.get_string_value("description"))
    info.SetCopyright(globals.get_string_value("copyright"))
    info.SetWebSite(globals.get_string_value("website"))
    info.SetLicence(globals.get_string_value("license")) 
    info.AddDeveloper(globals.get_string_value("developer"))
    docwriter = globals.get_string_value("docwriter")
    if docwriter: info.AddDocWriter(docwriter)
    artist = globals.get_string_value("artist")
    if artist: info.AddDocWriter(artist)
    translator = globals.get_string_value("translator")
    if translator: info.AddDocWriter(translator)
    wx.AboutBox(info)   
## show version information
# @param globals - global variables holding information or delivering methods to extract information
def AfpReq_Version(globals):
    afpmainversion = globals.get_string_value("name") + " " + globals.get_string_value("version")
    baseversion = globals.get_string_value("baseversion")
    pversion = globals.get_value("python-version").split("(")[0]
    myversion = globals.mysql.version.split("-")[0]
    wxversion = wx.version().split("(")[0]
    version = afpmainversion + '\n' + "AfpBase: " + baseversion+ '\n' + "python: " + pversion + '\n' + " wx: " + wxversion + '\n' + " mysql: " + myversion + '\n'
    versions = globals.get_modul_infos()
    AfpReq_Info(version, versions, "Versions Information")
## select extra programs from directory
# @param path - directory where to look
# @param modulname - name of modul program is designed for
def AfpReq_extraProgram(path, modulname):
    fname = None
    ok = False
    names = Afp_readFileNames(path, "*.py")
    liste = []
    fnames = []
    for name in names:
        modul, text = Afp_readExtraInfo(name)
        text = Afp_toString(text)
        if modul: text += " (" + modul +")"
        if modul is None or modul == modulname:
            liste.append(text)
            fnames.append(name)
    #print "AfpReq_extraProgram:", names, liste, fnames
    if liste:
        fname, ok = AfpReq_Selection("Bitte Zusatzprogramm auswählen, dass gestartet werden soll.".decode("UTF-8"), "", liste, "Zusatzprogramme", fnames)
    else:
        AfpReq_Info("Keine Zusatzprogramme vorhanden!","")
    return fname, ok
    
## common routine to invoke text editing \n
#  depending on input the text is edited directly or loaded from an external file
# @param input_text - text to be edited or relativ path to file
# @param globals - global variable to hold path-delimiter and path to archiv
def Afp_editExternText(input_text, globals=None):
    if globals:
        delimiter = globals.get_value("path-delimiter")
        file= Afp_archivName(input_text, delimiter)
        if file:
            file = globals.get_value("antiquedir") + file
            if Afp_existsFile(file): 
                with open(file,"r") as inputfile:
                    input_text = inputfile.read().decode('iso8859_15')
    return AfpReq_EditText(input_text,"Texteingabe")

## allow editing of configuration files \n
# write changed text to actuel configuration file
# @param modul - modul where configuration is changed
def Afp_editConfiguration(modul):
    home = Afp_genHomeDir()
    configuration = Afp_addPath(home, "Afp" + modul + ".cfg")
    input_text = ""
    if Afp_existsFile(configuration):
        with open(configuration,"r") as inputfile:
            input_text = inputfile.read().decode('iso8859_15')
    text, ok =AfpReq_EditText(input_text, "Afp '" + modul + "' Modul Configuration","Geladene Datei: " + configuration,"Aktivieren der Einstellungen durch entfernen des '#' Zeichens am Anfang der Zeile!", "Zum Bearbeiten der Konfigurationsdatei bitte 'Ändern' auswählen.".decode('UTF-8'), False, (800, 500))
    if ok:
        with open(configuration,"w") as outputfile:
            outputfile.write(text)
    return ok

## invoke a simple dialog to compose an e-mail \n
# return mail-sender and flag if mail could and should be sent
# @param mail - mail-sender to be edited
def Afp_editMail(mail):
    von = ""
    an = ""
    text = ""
    if mail.sender:
        von = "Von: " + mail.sender
    else:
        text += "Von: \n"
    if mail.recipients:
        an = "An: " + Afp_ArraytoLine(mail.recipients,", ")
    else:
        text += "An: \n"
    text += "Betreff: "
    if mail.subject:
        text += mail.subject
    if mail.message:
        text += "\n" + mail.message
    attachs = "Anhang: " + mail.get_attachment_names()
    text, ok = AfpReq_EditText(text,"E-Mail Versand", von, an, attachs, True)
    if ok:
        start = 0
        subject = None
        sender = None
        recipients = []
        attachs = []
        lines = text.split("\n")
        for line in lines:
            if ":" in line: 
                start += len(line) + 1
                if "Betreff:" in line:
                    subject = line[8:].strip()
                elif "An:" in line:
                    recipients = line[3:].split(",")
                elif "Von:" in line:
                    sender = line[4:].strip()
                elif "Anhang:" in line:
                    attachs = line[7:].split(",")
            else:
                break
        message = text[start:].strip()
        if message:
            mail.set_message(subject, message)
        if sender:
            mail.set_addresses(sender, None)
        if recipients:
            for recipient in recipients:
                mail.add_recipient(recipient)
        if attachs:
            for attach in attachs:
                mail.add_attachment(attach)
        ok = mail.is_ready()
    return mail, ok

##  handles automatic and manual sort cirterium selection for data search
#  @param value - initial value for search
#  @param index - initial sort criterium
#  @param sort_list - dictionary of possible sort criteria, with automatic selection format in the values
#  @param name - name of purpose of this selection
#  @param text - if given, text to be displayed for this selection
def Afp_autoEingabe(value, index, sort_list, name, text = None):
    name = name.decode("UTF-8")
    if text is None: text = "Bitte Auswahlkriteium für die ".decode("UTF-8") + name + "auswahl eingeben:"
    value, format, Ok = AfpReq_Eingabe(text, "", value, name +"auswahl")
    #print "Afp_autoEingabe:", Ok, value, format, sort_list
    if Ok:
        #print sort_list
        if format[0] == "!":
            liste = sort_list.keys()
            res,Ok = AfpReq_Selection("Bitte Sortierkriterium für die ".decode("UTF-8") + name + "auswahl auswählen.".decode("UTF-8"),"",liste,"Sortierung")
            #print Ok, res
            if Ok:
                index = res
        else:
            for entry in sort_list:
                if sort_list[entry] and sort_list[entry] == format:
                    index = entry
        #print "Afp_autoEingabe index:", index, value
        if sort_list[index] is None:
            Ok = None
    return value, index, Ok
     
## common dialog to create output documents
class AfpDialog_DiReport(wx.Dialog):
    ## constructor
    def __init__(self, *args, **kw):
        super(AfpDialog_DiReport, self).__init__(*args, **kw) 
        self.Ok = False
        self.debug = False
        self.data = None     # data where output should be created for
        self.datas = None   # in case more then one output has to be created, datas are attached here and sucessively assigned to data
        self.datasindex = None # current index in datas of actuel assigned data
        self.variables = None # given variables used globally in output
        self.globals = None
        self.major_type = None
        self.mail = None
        self.prefix = ""
        self.postfix = ""
        self.textmap = {}
        self.labelmap = {}
        self.choicevalues = {}
        self.changelist = []
        self.reportname = []
        self.reportlist = []
        self.reportflag = []
        self.reportdel = []
        self.readonlycolor = self.GetBackgroundColour()
        self.editcolor = (255,255,255)

        self.InitWx()
        #self.SetSize((428,138))
        self.SetSize((428,200))
        self.SetTitle("Dokumentenausgabe")

    ## set up dialog widgets
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.list_Report = wx.ListBox(panel, -1, pos=(10,10), size=(310,120), name="Report")
        #self.Bind(wx.EVT_LISTBOX_SCLICK, self.On_Rep_Click, self.list_Report)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Rep_DClick, self.list_Report)
        self.choice_Bearbeiten = wx.Choice(panel, -1,  pos=(325,10), size=(93,30),  choices=["Vorlage ...", "Ändern".decode("UTF-8"),"Kopie","Info", "Löschen".decode("UTF-8")], name="CBearbeiten")      
        self.choice_Bearbeiten.SetSelection(0)
        self.Bind(wx.EVT_CHOICE, self.On_Rep_Bearbeiten, self.choice_Bearbeiten)
        #self.button_Info = wx.Button(panel, -1, label="&Info", pos=(340,46), size=(78,30), name="Info")
        #self.Bind(wx.EVT_BUTTON, self.On_Rep_Info, self.button_Info)
        self.check_Archiv = wx.CheckBox(panel, -1, label="Archiv:", pos=(10,141), size=(70,20), name="Archiv")
        self.label_Ablage= wx.StaticText(panel, -1, label="", pos=(80,144), size=(70,18), name="Ablage")  
        self.text_Bem= wx.TextCtrl(panel, -1, value="", pos=(150,141), size=(170,20), style=0, name="Bem")        
        self.check_EMail = wx.CheckBox(panel, -1, label="per EMail", pos=(325,74), size=(93,20), name="check_EMail")
        self.button_Abbr = wx.Button(panel, -1, label="&Abbruch", pos=(325,100), size=(93,30), name="Abbruch")
        self.Bind(wx.EVT_BUTTON, self.On_Rep_Abbr, self.button_Abbr)
        self.button_Okay = wx.Button(panel, -1, label="&Ok", pos=(325,136), size=(93,30), name="Okay")
        self.Bind(wx.EVT_BUTTON, self.On_Rep_Ok, self.button_Okay)

    ## attach to database and populate widgets
    # @param selectionlist - SelectionList or list of SelectionLists to be used for output
    # @param globals - global variables to hold path values for output, including prefix of typ
    # @param variables - if given, dictionary of possible variable values used for output
    # @param header - if given, header to be display in the dialogs top ribbon
    # @param prepostfix - if given prefix and postfix of resultfile separated by a space
    def attach_data(self, data, globals, variables = None, header = None, prepostfix = None):
        if header: 
            self.SetTitle(self.GetTitle() + ": " + header)
            self.label_Ablage.SetLabel(header)      
        if type(data) == list:
            self.data = data.pop()
            self.datas = data
        else:
            self.data = data
        self.debug = self.data.debug
        self.globals = globals
        self.major_type = globals.get_value("name")
        if prepostfix:
            split = prepostfix.split()
            self.prefix = split[0]
            if len(split) > 1:
                self.postfix = split[1]
        else:
            self.prefix = self.globals.get_value("prefix", data.typ)
        if not self.datas: 
            self.check_Archiv.SetValue(True)
            self.check_Archiv.Enable(False)
            self.label_Ablage.Enable(False)
        if variables:
            self.variables = variables
        mail = AfpMailSender(self.globals, self.debug)
        if mail.is_possible():
            self.mail = mail
        else:
            self.check_EMail.SetValue(False)
            self.check_EMail.Enable(False)
        self.Populate()
    ## common population routines for dialog and widgets
    def Populate(self):
        self.Pop_text()
        self.Pop_label()
        self.Pop_list()
    ## return ok flag to caller
    def get_Ok(self):
        return self.Ok  
    ## specific population routine for textboxes 
    def Pop_text(self):
        for entry in self.textmap:
            TextBox = self.FindWindowByName(entry)
            value = self.data.get_string_value(self.textmap[entry])
            TextBox.SetValue(value)
    ## specific population routine for lables
    def Pop_label(self):
        for entry in self.labelmap:
            Label = self.FindWindowByName(entry)
            value = self.data.get_string_value(self.labelmap[entry])
            Label.SetValue(value)
    ## specific population routine for lists
    def Pop_list(self):
        rows = self.data.get_string_rows("AUSGABE", "Bez,Datei,BerichtNr")
        self.reportname = []
        self.reportlist = []
        self.reportflag = []
        self.reportdel = []
        for row in rows:
            self.reportname.append(row[0])
            if row[1]: 
                self.reportlist.append(row[1])
                self.reportdel.append(False)
            else: 
                self.reportlist.append(row[2])
                self.reportdel.append(True)
            self.reportflag.append(True)
        rows = self.data.get_string_rows("ARCHIV", "Datum,Gruppe,Typ,Bem,Extern,Art")
        if rows:
            for row in rows:
                if row[5] == self.globals.get_value("name"):
                    self.reportname.append(row[0] + " " + row[1] + " " + row[2] + " " + row[3])
                    self.reportlist.append(Afp_archivName(row[4], self.globals.get_value("path-delimiter")))
                    self.reportflag.append(False)
                    self.reportdel.append(False)
        self.list_Report.Clear()
        if self.reportname:
            self.list_Report.InsertItems(self.reportname, 0)
        return None
    ## fille preset value into archiv description
    # @param text - text to be displayed
    def preset_text_bem(self, text):
        self.text_Bem.SetValue(text)
    ## common Eventhandler TEXTBOX - when leaving the textbox
    # @param event - event which initiated this action
    def On_KillFocus(self,event):
        object = event.GetEventObject()
        name = object.GetName()
        if not name in self.changelist: self.changelist.append(name)
    ## initiate generation of names of template- and resultfiles
    def generate_names(self):
        fname = self.get_template_name()
        fresult = self.get_result_name()
        return fname, fresult
    ## initiate document generation
    def generate_Ausgabe(self):
        empty = Afp_addRootpath(self.globals.get_value("templatedir"), "empty.odt")
        fname, fresult = self.generate_names()
        #print "AfpDialog_DiReport.generate_Ausgabe:", fname, fresult
        if fresult:
            out = AfpAusgabe(self.debug, self.data)
            if self.variables:
                out.set_variables(self.variables)
            out.inflate(fname)
            out.write_resultfile(fresult, empty)
        else:
            fresult = fname
        if fresult:
            self.execute_Ausgabe(fresult)
            self.add_to_archiv()
            if self.check_EMail.IsChecked()  and self.mail:
                self.send_mail(fresult)
    ## send document per mail
    def send_mail(self, fresult):
        an = self.data.get_value("Mail.ADRESSE")
        fpdf = fresult[:-4] + ".pdf"
        if Afp_existsFile(fpdf):
            attach = fpdf
        else:
            attach = fresult
        self.mail.add_attachment(attach)
        if an: self.mail.add_recipient(an)
        self.mail, send = Afp_editMail(self.mail)
        if send: self.mail.send_mail()
    ## generate template filename due to list selection
    def get_template_name(self):
        template = None
        index = self.get_list_Report_index()
        if index >= 0:
            template = self.reportlist[index] 
            if not "." in template:
                template = self.major_type + "_template_" + template + ".fodt"
                template = Afp_addRootpath(self.globals.get_value("templatedir"), template)
            else:
                if template[:6] == "Archiv":
                    template = template[7:]
                    template = Afp_addRootpath(self.globals.get_value("antiquedir"), template)
                else:
                    template = Afp_addRootpath(self.globals.get_value("archivdir"), template)
            #print "AfpDialog_DiReport.get_template_name:", template, self.major_type, self.reportlist[index]
        return template
    ## generate result filename due to list selection
    def get_result_name(self):
        fresult = None  
        index = self.get_list_Report_index()
        archiv = self.check_Archiv.IsChecked() 
        if index >= 0 and self.reportflag[index]:
            if archiv:
                max = 0
                #print "AfpDialog_DiReport.get_result_name:", self.reportlist
                for entry in self.reportlist:
                    if entry and "." in entry:
                        split = entry.split(".")
                        nb = int(split[0][-2:]) 
                        if nb > max: max = nb
                max += 1
                if self.datasindex: max += self.datasindex
                if max < 10:  null = "0"
                else:  null = ""
                if self.postfix:
                    fresult = self.prefix  + "_" + self.data.get_string_value() + "_" + self.postfix + "_" + null + str(max) + ".odt"
                else:
                    fresult = self.prefix  + "_" + self.data.get_string_value() + "_" + null + str(max) + ".odt"
                self.archivname = fresult
                fresult = Afp_addRootpath(self.globals.get_value("archivdir"), fresult)
            else:
                if self.datasindex:
                    fresult = Afp_addRootpath(self.globals.get_value("tempdir"), self.major_type + "_textausgabe" + str(self.datasindex) + ".fodt")
                else:
                    fresult = Afp_addRootpath(self.globals.get_value("tempdir"), self.major_type + "_textausgabe.fodt")
        #print "get_result_name:", fresult   
        return  fresult
    ## return selected list index
    def get_list_Report_index(self):
        sel = self.list_Report.GetSelections()
        if sel: index = sel[0]
        else: index = -1
        return index
    ## return selected list index name
    def get_list_Report_name(self):
        name = None
        index = self.get_list_Report_index()
        if index >= 0:
            name = self.reportname[index]
        return Afp_toString(name)
    ## start editing of generated document in extern editor
    # @param fresult - result filename
    def execute_Ausgabe(self, fresult):
        Afp_startFile(fresult, self.globals, self.debug)
    ## gernerate entry in archieve
    def add_to_archiv(self):
        if not self.archivname: return
        new_data = {}
        new_data["Typ"] = self.label_Ablage.GetLabel()
        new_data["Gruppe"] = self.get_list_Report_name()
        new_data["Bem"] = self.text_Bem.GetValue()
        new_data["Extern"] = self.archivname
        self.data.add_to_Archiv(new_data)
   
    # Event Handlers 
    ## Eventhandler left mouse click in list selection
    # @param event - event which initiated this action
    def On_Rep_Click(self,event):
        print "AfpDialog_DiReport Event handler `On_Rep_Click' not implemented!"
        event.Skip()
    ## Eventhandler left mouse doubleclick in list selection
    # @param event - event which initiated this action
    def On_Rep_DClick(self,event):
        if self.debug: print "AfpDialog_DiReport Event handler `On_Rep_DClick'"
        self.On_Rep_Ok()
        event.Skip()
    ## Eventhandler BUTTON - Edit button pushed
    # @param event - event which initiated this action
    def On_Rep_Bearbeiten(self,event):
        if self.debug: print "AfpDialog_DiReport Event handler `On_Rep_Bearbeiten'"      
        template = self.get_template_name()
        choice = self.choice_Bearbeiten.GetStringSelection()
        list_Report_index = self.list_Report.GetSelection()
        if list_Report_index < 0: list_Report_index = 0
        if (template and template[-5:] == ".fodt") or choice == "Info":
            noWait = False
            filename = ""
            if choice == "Ändern".decode("UTF-8"):
                filename = template
            elif choice == "Kopie":
                filename = Afp_addRootpath(self.globals.get_value("tempdir"), self.major_type + "_template.fodt")
                Afp_copyFile(template, filename)
            elif choice == "Info":
                filename = Afp_addRootpath(self.globals.get_value("tempdir") , "DataInfo.txt")
                Afp_printSelectionListDataInfo(self.data, filename) 
                noWait = True
            elif choice == "Löschen".decode("UTF-8"):
                rname = self.list_Report.GetStringSelection()
                if self.reportdel[list_Report_index]:
                    ok = AfpReq_Question("Vorlage '" + rname + "' wirklich löschen?".decode("UTF-8") ,"", "Vorlage löschen".decode("UTF-8"))
                    if ok:
                        self.data.delete_row("AUSGABE",list_Report_index)
                        self.data.get_selection("AUSGABE").store()
                        self.Pop_list()
            if filename:
                Afp_startFile( filename, self.globals, self.debug, noWait) 
                if choice == "Kopie":
                    rows = self.data.get_value_rows("AUSGABE","Art,Typ,Bez",list_Report_index)
                    name = rows[0][2]
                    ok = True
                    neu = ""
                    while ok and name in self.reportname:
                        name, ok = AfpReq_Text("Bitte " + neu + "Namen eingeben unter dem die neue Vorlage","für '".decode("UTF-8") + rows[0][0] + " " + rows[0][1] + "' abgelegt werden soll!",rows[0][2], "Vorlagenbezeichnung")
                        neu = "NEUEN "
                    if ok:
                        data = {"Modul":self.globals.get_name(),"Art": rows[0][0], "Typ": rows[0][1], "Bez": name, "Datei": ""}
                        ausgabe = AfpSQLTableSelection(self.data.get_mysql(), "AUSGABE", self.debug, "BerichtNr", self.data.get_selection("AUSGABE").get_feldnamen())
                        ausgabe.new_data()
                        ausgabe.set_data_values(data)
                        ausgabe.store()
                        BNr = ausgabe.get_string_value("BerichtNr")
                        destination = self.globals.get_value("templatedir") + self.major_type + "_template_" + BNr + ".fodt"
                        Afp_copyFile(filename, destination)
                        ind = list_Report_index + 1
                        self.reportname.insert(ind, name)
                        self.reportlist.insert(ind, BNr)
                        self.reportflag.insert(ind, True)
                        self.reportdel.insert(ind, True)
                        self.list_Report.Clear()
                        self.list_Report.InsertItems(self.reportname, 0)
        self.choice_Bearbeiten.SetSelection(0)
        event.Skip()  
    ## Eventhandler BUTTON - Cancel button pushed
    # @param event - event which initiated this action
    def On_Rep_Abbr(self,event):
        if self.debug: print "AfpDialog_DiReport Event handler `On_Rep_Abbr'"
        self.EndModal(wx.ID_CANCEL)
        event.Skip()
    ## Eventhandler BUTTON - Ok button pushed
    # @param event - event which initiated this action
    def On_Rep_Ok(self,event=None):
        if self.debug: print "AfpDialog_DiReport Event handler `On_Rep_Ok'"
        self.archivname = None
        self.generate_Ausgabe()
        if self.datas:
            for data in self.datas:
                self.datasindex = self.datas.index(data)
                self.data = data
                self.generate_Ausgabe()
        if self.archivname:
            select = self.data.get_selection("ARCHIV")
            if select: select.store()
        if event: event.Skip()
        self.EndModal(wx.ID_OK)

## loader routine for dialog DiReport \n
# for multiple output use 'datalist' as input for a list of 'AfpSelectionList's
# @param selectionlist - SelectionList or list of SelectionLists to be used for output
# @param globals - global variables to hold path values for output
# @param variables - dictionary of possible variable values used for output
# @param header - if given, text displayed in header of dialog
# @param prefix - if given, prefix for output name creation and archiv entry
# @param archivtext - if given, preset text for archiv entry
# @param datalist - if given, list of SelectionLists, entries are filled consecutively into  'selectionlist' for multiple output
def AfpLoad_DiReport(selectionlist, globals, variables = None, header = "", prefix = "", archivtext = None):
    DiReport = AfpDialog_DiReport(None)
    DiReport.attach_data(selectionlist, globals, variables, header, prefix)
    if archivtext: DiReport.preset_text_bem(archivtext)
    DiReport.ShowModal()
    DiReport.Destroy()
 
## dialog for archiv editing
class AfpDialog_editArchiv(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        AfpDialog.__init__(self,None, -1, "")
        self.lock_data = True
        self.reload = ["ARCHIV"]
        self.changed = False
        self.fnames = []
        self.added = []
        self.SetTitle("Archiv")
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        self.SetSize((350,300))
        
    ## initialise graphic elements
    def InitWx(self):
        self.label_text_1 = wx.StaticText(self, 1, name="label1")        
        self.label_text_2 = wx.StaticText(self, 2, name="label2")
        self.label_lower = wx.StaticText(self, 2, name="label_lower")
        self.list_Archiv = wx.ListBox(self, -1, name="Archiv")      
        self.listmap.append("Archiv")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Archiv_edit, self.list_Archiv)
        self.button_Add = wx.Button(self, -1, label="&Hinzufügen".decode("UTF-8"), name="Add")
        self.Bind(wx.EVT_BUTTON, self.On_Button_Add, self.button_Add)
        self.lower_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lower_sizer.AddStretchSpacer(1)
        self.lower_sizer.Add(self.button_Add,3,wx.EXPAND)
        self.setWx(self.lower_sizer,[1, 3, 1], [0, 3, 1]) 
        self.inner_sizer=wx.BoxSizer(wx.VERTICAL)
        self.inner_sizer.Add(self.label_text_1,0,wx.EXPAND)
        self.inner_sizer.Add(self.label_text_2,0,wx.EXPAND)
        self.inner_sizer.Add(self.list_Archiv,1,wx.EXPAND)
        self.inner_sizer.Add(self.label_lower,0,wx.EXPAND)
        self.inner_sizer.Add(self.lower_sizer,0,wx.EXPAND)
        self.inner_sizer.AddSpacer(10)
        self.sizer=wx.BoxSizer(wx.HORIZONTAL)  
        self.sizer.AddSpacer(10)     
        self.sizer.Add(self.inner_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)    
        
    ## execution in case the OK button ist hit - to be overwritten in derived class
    def execute_Ok(self):
        self.Ok = True
        if self.added:
            max = 0
            for entry in self.fnames:
                if entry and "." in entry:
                    split = entry.split(".")
                    nb = int(split[0][-2:]) 
                    if nb > max: max = nb
            max += 1
            for entry in self.added:
                if len(entry) >= 5:
                    fname = entry[5]
                    if Afp_existsFile(fname):
                        ext = fname.split(".")[-1]
                        if max < 10:  null = "0"
                        else:  null = ""
                        if entry[3]:
                            postfix = entry[3]
                        else:
                            postfix = entry[1]
                        fresult = entry[2]  + "_" + self.data.get_string_value() + "_" + postfix + "_" + null + str(max) + "." + ext 
                        fpath = Afp_addRootpath(self.data.get_globals().get_value("archivdir"), fresult)
                        if self.debug: print "AfpDialog_editArchiv.execute_Ok copy file:", fname, "to",  fpath
                        #print "AfpDialog_editArchiv.execute_Ok copy file:", fname, "to",  fpath
                        Afp_copyFile(fname, fpath)
                        added = {"Datum": entry[0], "Art": entry[1], "Typ": entry[2], "Gruppe": entry[3], "Bem": entry[4], "Extern": fresult}
                        added["KundenNr"] = self.data.get_value("KundenNr")
                        added["Tab"] = self.data.get_mainselection()
                        added["TabNr"] = self.data.get_value()
                        self.data.set_data_values(added, "ARCHIV", -1)
                        max += 1
        self.data.store()
        #self.data.view()
 
    ## attach data and labels to dialog
    # @param data - SelectionList to be used for this dialog
    # @param label1 - first row of text to be displayed
    # @param label2 - second row of text to be displayed
    # @param editable - flag if dialog should be editable when it pops off
    def attach_data(self, data, label1, label2, editable = False):
        self.data = data
        self.debug = data.is_debug()
        self.major_type = data.get_globals().get_value("name")
        if label1: self.label_text_1.SetLabel(label1)
        if label2: self.label_text_2.SetLabel(label2)
        self.Populate()
        if editable:
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        else:
            self.Set_Editable(False)
    ## populate the 'Extra' list, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_Archiv(self): 
        liste = [] 
        self.fnames = []      
        if self.data and self.data.exists_selection("ARCHIV", True):
            rows = self.data.get_value_rows("ARCHIV","Datum,Art,Typ,Gruppe,Bem,Extern")
            for row in rows:
                liste.append(Afp_ArraytoLine(row, " ", 5))
                self.fnames.append(row[5])
        if self.added:
            for row in self.added:
                liste.append(Afp_ArraytoLine(row, " ", 5))
        self.list_Archiv.Clear()
        if liste: self.list_Archiv.InsertItems(liste, 0)
    ## overwritten routine for reloading data into display, \n
    # additional rows are deleted
    def re_load(self):
        self.added = []        
        super(AfpDialog_editArchiv, self).re_load()
    ## check if archiv is active for input data
    def active(self):
        if self.data and self.data.exists_selection("ARCHIV", True):
            return True
        else:
            return False
    ## Eventhandler DCLICK - list entry dselected
    # @param event - event which initiated this action
    def On_Archiv_edit(self, event):
        if self.debug: print "AfpDialog_editArchiv Event handler `On_Archiv_edit'"
        index = self.list_Archiv.GetSelections()[0] 
        row = self.data.get_value_rows("ARCHIV","Art,Typ,Gruppe,Bem", index)[0]
        row = Afp_ArraytoString(row)
        if row[0] == self.major_type or row[0] =="SEPA-DD":
            #liste = [["Art:", row[0]], ["Ablage:", row[1]], ["Fach:", row[2]], ["Bemerkung:", row[3]]]
            liste = [["Fach:", row[2]], ["Bemerkung:", row[3]]]
            text2 = "Art: " + row[0] + ", Ablage: " + row[1]
        else:
            liste = [["Ablage:", row[1]], ["Fach:", row[2]], ["Bemerkung:", row[3]]]
            text2 = "Art: " + row[0] 
        result = AfpReq_MultiLine("Bitte Archiveintrag ändern:".decode("UTF-8"), text2, "Text", liste, "Archiveintrag", 300, "")
        if result:
            for i in range(len(result)):
                if result[i] != liste[i][1]:
                    changed = True
            if changed:
                self.changed = True
                values = {}
                value_types = ["Typ", "Gruppe","Bem"]
                for res in reversed(result):
                    values[value_types.pop()] = res
                self.data.set_data_values(values, "ARCHIV", index)
        elif result is None:
            self.changed = True
            self.data.delete_row("ARCHIV", index)
        if self.changed: self.Populate()
        event.Skip()
    ## Eventhandler BUTTON - Add button pushed
    # @param event - event which initiated this action
    def On_Button_Add(self,event ):
        if self.debug: print "AfpDialog_editArchiv Event handler `On_Button_Add'"
        self.result = None
        dir = ""
        fname, ok = AfpReq_FileName(dir, "", "", True)
        #print fname, ok
        liste = [["Art:", "Extern"], ["Ablage:", self.data.get_listname()], ["Fach:", ""], ["Bemerkung:",""]]
        result = AfpReq_MultiLine("Neuen Archiveintrag erzeugen, für die Datei".decode("UTF-8"), fname.decode("UTF-8"), "Text", liste, "Archiveintrag", 300)
        #print result
        if result:
            self.added.append([self.data.get_globals().today(), result[0], result[1], result[2], result[3], fname])
            self.Pop_Archiv()
        event.Skip()

## loader routine for dialog editArchiv \n
# @param data - given SelectionList, where archiv should be manipulated
# @param label1 - text to be displayed in first line
# @param label2 - text to be displayed in second line
def AfpLoad_editArchiv(data, label1, label2):
    dialog = AfpDialog_editArchiv(None)
    dialog.attach_data(data, label1, label2)
    Ok = None
    if dialog.active():
        dialog.ShowModal()
        Ok = dialog.get_Ok()
    else:
        AfpReq_Info("Archiv für aktuelle Daten nicht aktiv".decode("UTF-8"),"oder keine Archiveinträge vorhanden!".decode("UTF-8"),"Archiv")
    dialog.Destroy()
    return Ok  