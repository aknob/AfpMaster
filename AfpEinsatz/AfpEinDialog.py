#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpEinsatz.AfpEinDialog
# AfpEinDialog module provides the dialogs and appropriate loader routines needed for vehicle operation \n
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        11 Mar. 2014 - inital code generated - Andreas.Knoblauch@afptech.de

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

from AfpBase.AfpBaseDialog import *
from AfpBase.AfpBaseDialogCommon import *
from AfpBase.AfpBaseAdRoutines import AfpAdresse
from AfpBase.AfpBaseAdDialog import AfpLoad_AdAttAusw

from AfpEinsatz.AfpEinRoutines import *

## create one line info of driver row
# @param datum - startdate of the vehicle oeration
# @param row - input row line is created from \n
# - row = [Kuerzel, Datum, Von, Bis, EndDatum, AbZeit, Abfahrt, AbOrt] 
def AfpEinsatz_setFahrerLineFromRow(datum, row):
    line = ""
    ADat = ""
    EDat = ""
    SDat = ""
    lgh = len(row)
    if lgh: line = Afp_toString(row[0])
    if lgh > 1 and row[1]:
        dat = Afp_fromString(row[1])
        if dat != datum:
            ADat = Afp_toShortDateString(dat)
    if lgh > 2 and row[2]:
        space = ""
        if ADat: space = " "
        ADat += space + Afp_toString(row[2])
    if lgh > 3 and row[3] :
        EDat = Afp_toString(row[3])
    if lgh > 4 and row[4]:
        dat = Afp_fromString(row[4])
        if dat != datum:
            space = ""
            if EDat: space = " "
            EDat += space + Afp_toShortDateString(dat)
    if lgh > 5 and row[5] :
        SDat = Afp_toString(row[5])
    if lgh > 6 and row[6]:
        dat = Afp_fromString(row[6])
        if dat != datum:
            space = ""
            if SDat: space = " "
            SDat += space + Afp_toShortDateString(dat)
    if lgh > 7 and row[7]:
        space = ""
        if SDat: space = " "
        SDat += space + Afp_toString(row[7])
    if ADat or EDat: 
        if ADat: line += " " + ADat
        line += " - "
        if EDat: line += EDat
    if SDat: 
        line += " > " + SDat
    return line

## display and manipulation of vehicle operations
class AfpDialog_DiEinsatz(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):
        AfpDialog.__init__(self,None, -1, "")
        self.choicevalues = {}
        self.times = {}
        self.fremd = None
        self.changed_data = False
        self.calling_modul = None
      
        self.SetSize((452,430))
        self.SetTitle("Einsatz")

    ## initialise graphic elements
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.label_Abfahrt = wx.StaticText(panel, -1, label="&Abfahrt:", pos=(178,92), size=(80,20), name="Abfahrt")
        self.text_AbDat = wx.TextCtrl(panel, -1, value="", pos=(178,112), size=(80,22), style=0, name="AbDat")
        self.vtextmap["AbDat"] = "Datum.EINSATZ"
        self.text_AbDat.Bind(wx.EVT_KILL_FOCUS, self.On_ChTime)
        self.text_AbZeit = wx.TextCtrl(panel, -1, value="", pos=(178,134), size=(80,22), style=0, name="AbZeit")
        self.vtextmap["AbZeit"] = "Zeit.EINSATZ"
        self.text_AbZeit.Bind(wx.EVT_KILL_FOCUS, self.On_ChTime)
        self.label_Stellung = wx.StaticText(panel, -1, label="&Stellung:", pos=(94,92), size=(80,20), name="Stellung")
        self.text_StellDat = wx.TextCtrl(panel, -1, value="", pos=(94,112), size=(80,22), style=0, name="StellDat")
        self.vtextmap["StellDat"] = "StellDatum.EINSATZ"
        self.text_StellDat.Bind(wx.EVT_KILL_FOCUS, self.On_ChTime)
        self.text_StellZeit = wx.TextCtrl(panel, -1, value="", pos=(94,134), size=(80,22), style=0, name="StellZeit")
        self.vtextmap["StellZeit"] = "StellZeit.EINSATZ"
        self.text_StellZeit.Bind(wx.EVT_KILL_FOCUS, self.On_ChTime)
        self.label_Beginn = wx.StaticText(panel, -1, label="&Beginn:", pos=(10,92), size=(80,20), name="Beginn")
        self.text_StartDat = wx.TextCtrl(panel, -1, value="", pos=(10,112), size=(80,22), style=0, name="StartDat")
        self.vtextmap["StartDat"] = "AbDatum.EINSATZ"
        self.text_StartDat.Bind(wx.EVT_KILL_FOCUS, self.On_ChTime)
        self.text_StartZeit = wx.TextCtrl(panel, -1, value="", pos=(10,134), size=(80,22), style=0, name="StartZeit")
        self.vtextmap["StartZeit"] = "AbZeit.EINSATZ"
        self.text_StartZeit.Bind(wx.EVT_KILL_FOCUS, self.On_ChTime)
        self.label_Ende = wx.StaticText(panel, -1, label="&Ende:", pos=(272,92), size=(80,20), name="Ende")
        self.text_EndDat = wx.TextCtrl(panel, -1, value="", pos=(272,112), size=(80,22), style=0, name="EndDat")
        self.vtextmap["EndDat"] = "EndDatum.EINSATZ"
        self.text_EndDat.Bind(wx.EVT_KILL_FOCUS, self.On_ChTime)
        self.text_EndZeit = wx.TextCtrl(panel, -1, value="", pos=(272,134), size=(80,22), style=0, name="EndZeit")
        self.vtextmap["EndZeit"] = "EndZeit.EINSATZ"
        self.text_EndZeit.Bind(wx.EVT_KILL_FOCUS, self.On_ChTime)
    #FOUND: DialogFrame "Wofür", conversion not implemented due to lack of syntax analysis!
        self.button_Typ = wx.Button(panel, -1, label="Einsatz", pos=(6,8), size=(100,24), name="Typ")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_Typ, self.button_Typ)
        self.label_EName = wx.StaticText(panel, -1, pos=(120,12), size=(220,20), name="EName")
        self.label_Start = wx.StaticText(panel, -1, pos=(10,38), size=(160,20), name="Nr")
        self.label_Ziel = wx.StaticText(panel, -1, pos=(180,38), size=(160,20), name="Ziel")
      
        self.label_TStellOrt = wx.StaticText(panel, -1, label="Stell&ort:", pos=(10,162), size=(80,20), name="TStellOrt")
        self.text_StellOrt = wx.TextCtrl(panel, -1, value="", pos=(94,160), size=(260,22), style=0, name="StellOrt")
        self.textmap["StellOrt"] = "StellOrt"
        self.text_StellOrt.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_TBem = wx.StaticText(panel, -1, label="Bes&chreibung:", pos=(8,188), size=(90,20), name="TBem")
        self.text_Bem = wx.TextCtrl(panel, -1, value="", pos=(94,186), size=(346,80), style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="Bem")
        self.textmap["Bem"] = "Bem"
        self.text_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        #self.label_Text = wx.StaticText(panel, -1, label="Ein_Text$", pos=(10,64), size=(330,20), name="Text")
        #self.text_Bem = wx.TextCtrl(panel, -1, value="", pos=(,), size=(,), style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="Bem")
        #self.textmap["Bem"] = "Ein_Bmk$"
        #self.text_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.button_BAdresse = wx.Button(panel, -1, label="&Fremd Adresse:", pos=(6,270), size=(120,24), name="BAdresse")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_AbAdresse, self.button_BAdresse)
        self.label_EAbName = wx.StaticText(panel, -1, pos=(10,300), size=(300,20), name="EAbName")
        self.labelmap["EAbName"] = "Name.FremdAdresse"
        self.label_EAbOrt = wx.StaticText(panel, -1, pos=(10,324), size=(150,20), name="EAbOrt")
        self.labelmap["EAbOrt"] = "Ort.FremdAdresse"
        self.label_EAbStr = wx.StaticText(panel, -1, label="Ein_AbStr$", pos=(176,324), size=(150,20), name="EAbStr")
        self.labelmap["EAbStr"] = "Strasse.FremdAdresse"
        self.label_EAbTel = wx.StaticText(panel, -1, label="Ein_AbTel$", pos=(10,348), size=(150,20), name="EAbTel")
        self.labelmap["EAbTel"] = "Telefon.FremdAdresse"
        self.label_EAbFax = wx.StaticText(panel, -1, label="Ein_AbFax$", pos=(10,372),size=(150,20), name="EAbFax")
        self.labelmap["EAbFax"] = "Fax.FremdAdresse" 
        self.label_TKontakt = wx.StaticText(panel, -1, label="&Kontakt:", pos=(176,348), size=(60,20), name="TKontakt")
        self.text_Kontakt = wx.TextCtrl(panel, -1, value="", pos=(238,346), size=(114,24), style=0, name="Kontakt")
        self.textmap["Kontakt"] = "FremdKontakt.EINSATZ"
        self.text_Kontakt.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_TPreis = wx.StaticText(panel, -1, label="&Preis:", pos=(176,372), size=(60,20), name="TPreis")
        self.text_Preis = wx.TextCtrl(panel, -1, value="", pos=(238,370), size=(114,24), style=0, name="Preis")
        self.vtextmap["Preis"] = "FremdPreis.EINSATZ"
        self.text_Preis.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
    #FOUND: DialogFrame "REin", conversion not implemented due to lack of syntax analysis!
        self.label_TBus = wx.StaticText(panel, -1, label="Bus:", pos=(220,272), size=(36,20), name="TBus")
        self.choice_Bus = wx.Choice(panel, -1,  pos=(250,270), size=(102,24),  choices=[],  name="CBus")      
        self.choicemap["CBus"] = "Bus.EINSATZ"
        self.Bind(wx.EVT_CHOICE, self.On_CBus, self.choice_Bus)
        self.button_BFahrer = wx.Button(panel, -1, label="&Fahrer:", pos=(6,270), size=(120,24), name="BFahrer")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_Fahrer, self.button_BFahrer)
        self.list_FahrList = wx.ListBox(panel, -1, pos=(6,296), size=(346,98), name="FahrList")
        self.listmap.append("FahrList")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Ein_FahrChg, self.list_FahrList)
        self.button_Neu = wx.Button(panel, -1, label="&Neu", pos=(360,30), size=(80,34), name="Neu")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_Neu, self.button_Neu)
        self.button_Loeschen = wx.Button(panel, -1, label="&Löschen", pos=(360,70), size=(80,34), name="Loeschen")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_Loeschen, self.button_Loeschen)
        self.button_Termin = wx.Button(panel, -1, label="&Termin", pos=(360,110), size=(80,34), name="Termin")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_Termin, self.button_Termin)
        self.button_Bem = wx.Button(panel, -1, label="Be&merkung", pos=(360,150), size=(80,34), name="BBem")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_Bem, self.button_Bem)
        self.button_Dokument = wx.Button(panel, -1, label="&Dokument", pos=(360,272), size=(80,34), name="Dokument")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_Dokument, self.button_Dokument)
        self.setWx(panel, [360, 330, 80, 24], [360, 360, 80, 34])

    ## population routine, AfpDialog population routines is called here
    def Populate(self):
        super(AfpDialog_DiEinsatz, self).Populate()
        self.switch_driver_external()
        typ = self.data.get_typ()
        if typ: 
            self.button_Typ.SetLabel(typ)
            name = ""
            start = ""
            ziel = ""
            if "Mietfahrt" in typ:
                name = self.data.get_name(False, "FahrtAdresse")
                start =  self.data.get_string_value("Abfahrtsort.FAHRTEN") 
                ziel =  self.data.get_string_value("Zielort.FAHRTEN") 
            elif "Reise" in typ:
                name = "Eigene Reise"
                start = self.data.get_string_value("Kostenst.REISEN") 
                ziel = "am " + self.data.get_string_value("Abfahrt.REISEN")
            self.label_EName.SetLabel(name)
            self.label_Start.SetLabel(start)
            self.label_Ziel.SetLabel(ziel)

    ## populate the driver list, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_FahrList(self):
        #print "akn 15.12 4:00 - 17:00 [16.12] > 7:00 [15.12] Stellort"
        rows = self.data.get_value_rows("FAHRER", "Kuerzel,Datum,Von,Bis,EndDatum,AbZeit,Abfahrt,AbOrt")
        liste = []
        for row in rows:
            liste.append(AfpEinsatz_setFahrerLineFromRow(self.data.get_value("Datum"),row))
        self.list_FahrList.Clear()
        if liste:
            self.list_FahrList.InsertItems(liste, 0)
    ## create one line info of driver row
    # @param row - input row line is created from \n
    # - row = [Kuerzel, Datum, Von, Bis, EndDatum, AbZeit, Abfahrt, AbOrt] 
    # - Einsatz:   AbDatum, AbZeit, EndZeit, EndDatum, Zeit, Datum, Stellort]
    def Set_FahrerLineFromRow(self, row):
        line = ""
        ADat = ""
        EDat = ""
        SDat = ""
        datum = self.data.get_value("Datum")
        lgh = len(row)
        if lgh: line = Afp_toString(row[0])
        if lgh > 1 and row[1]:
            dat = Afp_fromString(row[1])
            if dat != datum:
                ADat = Afp_toShortDateString(dat)
        if lgh > 2 and row[2]:
            space = ""
            if ADat: space = " "
            ADat += space + Afp_toString(row[2])
        if lgh > 3 and row[3] :
            EDat = Afp_toString(row[3])
        if lgh > 4 and row[4]:
            dat = Afp_fromString(row[4])
            if dat != datum:
                space = ""
                if EDat: space = " "
                EDat += space + Afp_toShortDateString(dat)
        if lgh > 5 and row[5] :
            SDat = Afp_toString(row[5])
        if lgh > 6 and row[6]:
            dat = Afp_fromString(row[6])
            if dat != datum:
                space = ""
                if SDat: space = " "
                SDat += space + Afp_toShortDateString(dat)
        if lgh > 7 and row[7]:
            space = ""
            if SDat: space = " "
            SDat += space + Afp_toString(row[7])
        if ADat or EDat: 
            if ADat: line += " " + ADat
            line += " - "
            if EDat: line += EDat
        if SDat: 
            line += " > " + SDat
        return line

    ## attaches data to this dialog, invokes population of widgets \n
    # - overwritten from parent
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        rows = data.get_mysql().select_strings("Name","","BUSSE")
        values = []
        values.append("")
        values.append("FREMD")
        for value in rows:
            values.append(value[0])
        self.choice_Bus.Appends(values)
        super(AfpDialog_DiEinsatz, self).attach_data(data, new, editable)
        if self.data.is_typ("Miet"):
            self.calling_modul = Afp_importPyModul("AfpCharter.AfpChDialog", data.get_globals())
        if self.typ_hasTime("Ab"):
            self.times["Ab"]  = self.get_typTime("Ab", True)
        if self.typ_hasTime("Stell"):
            self.times["Stell"] = self.get_typTime("Stell", True)
        if self.typ_hasTime("Start"):
            self.times["Start"] = self.get_typTime("Start", True)
        if self.data.no_calendar():
            self.button_Termin.Enable(False)
        if self.data_is_fremd():
            self.choice_Bus.SetSelection(1)
            self.switch_driver_external(True)
    ## execution in case the OK button ist hit - overwritten from parent     
    def execute_Ok(self):
        self.store_database()
    ## read values from dialog and invoke writing into database          
    def store_database(self):
        self.Ok = False
        data = {}
        #print "store_database()", self.changed_text
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
            #print name, wert
        for entry in self.choicevalues:
            name = entry.split(".")[0]
            data[name] = self.choicevalues[entry]
            print(entry, name, self.choicevalues[entry])
        if self.fremd:
            data["FremdNr"] = self.fremd.get_value("KundenNr")
            data["EAbName"] = self.fremd.get_value("Name")
            data["EAbOrt"] = self.fremd.get_value("Ort")
            data["EAbStr"] = self.fremd.get_value("Strasse")
            data["EAbTel"] = self.fremd.get_value("Telefon")
            data["EAbFax"] = self.fremd.get_value("Fax")
        #elif "Bus" in data and not data["Bus"] == "FREMD":
            #data["FremdNr"] = 0
        if data or self.changed_data:
            if data: 
                self.data.set_data_values(data)
            self.data.store()
            self.new = False          
            self.Ok = True              
        self.changed_text = []   
        self.choicevalues = {}

    ## return if operation stored in data is to be executed by an extern operator
    def data_is_fremd(self):
        flag = False
        if self.data.get_value("Bus.EINSATZ") == "FREMD":
            if self.data.get_value("FremdNr.EINSATZ"):
                flag = True
        return flag
    ## return if operation in dialog is to be executed by an extern operator
    def selection_is_fremd(self):
        fremd = False
        if self.choice_Bus.GetStringSelection() == "FREMD":
            fremd = True
        return fremd
    ## switch operation to be executed internal or by an extern operator
    # @param flag - flag if operation is to be executed by an extern operator \n
    # driver is show if flag  is set to False
    def switch_driver_external(self, flag = False):
        if flag:
            driver = False
            extern = True
        else:
            driver = True
            extern = False
            self.fremd = None
        # set flags for extern display
        self.button_BAdresse.Show(extern)
        self.label_EAbName.Show(extern)
        self.label_EAbOrt.Show(extern)
        self.label_EAbStr.Show(extern)
        self.label_EAbTel .Show(extern)
        self.label_EAbFax.Show(extern)
        self.label_TKontakt.Show(extern)
        self.text_Kontakt.Show(extern)
        self.label_TPreis.Show(extern)
        self.text_Preis.Show(extern)
        # set flags for driver display
        self.button_BFahrer.Show(driver)
        self.list_FahrList.Show(driver) 
   
    ## extract date and time from both widgets for different typ
    # @param typ - typ for which the widgets are read
    # @param end - flag if time has to be interpreted \n
    # relativ to midnight (24:00), otherwise 0:00 will be used
    # - convention: the appropriate widgets have to be called typ + "Dat" and typ + "Zeit"
    def get_typTime(self, typ, end = False):
        typDat = typ + "Dat"
        TextBox = self.FindWindowByName(typDat)
        datestring = Afp_ChDatum(TextBox.GetValue())
        typZeit = typ + "Zeit"       
        TextBox = self.FindWindowByName(typZeit)
        timestring, tage = Afp_ChZeit(TextBox.GetValue())
        if datestring and timestring:
            return Afp_datetimeString(datestring, timestring, end)
        else:
            return None
    ## write input time value to date and time widgets for different types
    # @param time - time value for which the widgets are written
    # @param typ - typ for which the widgets are written
    # - convention: the appropriate widgets have to be called typ + "Dat" and typ + "Zeit"
    def set_typTime(self, time, typ):
        typDat = typ + "Dat" 
        TextBox = self.FindWindowByName(typDat)
        TextBox.SetValue(Afp_toString(time.date())) 
        if not typDat in self.changed_text: self.changed_text.append(typDat)
        if time.time():
            typZeit = typ + "Zeit"      
            TextBox = self.FindWindowByName(typZeit)
            TextBox.SetValue(Afp_toString(time.time())) 
            self.times[typ] = time
            if not typZeit in self.changed_text: self.changed_text.append(typZeit)
    ## check if a time widgets exists for this typ
    # @param typ - typ for which widget has t be checked
    def typ_hasTime(self, typ):
        typZeit = typ + "Zeit"
        TextBox = self.FindWindowByName(typZeit)
        if TextBox.GetValue(): return True
        else: return False
    ## spread times into dialog according to given typ
    # @param typ - name of master timefields (Start, Stell, Ab, End)
    def spread_times(self, typ):
        dattime= None
        if typ == "End":
            dattime = self.get_typTime("End", True)
            if dattime: self.set_typTime(dattime, "End")
        if typ == "Ab":
            delta = None
            if typ in self.times and "Stell" in self.times:     
                delta = self.times[typ] - self.times["Stell"]
            dattime = self.get_typTime("Ab")
            if dattime: 
                self.set_typTime(dattime,"Ab")
                if delta:
                    dattime = dattime - delta
                else:
                    value = Afp_toTimedelta(self.data.globals.get_value("stell-difference","Einsatz"))
                    if not value is None: dattime = dattime -  value
            if self.typ_hasTime(typ):  typ = "Stell"      
        if typ == "Stell":
            delta = None
            if typ in self.times and "Start" in self.times:     
                delta = self.times[typ] - self.times["Start"]
            if not dattime: dattime = self.get_typTime("Stell") 
            if dattime: 
                self.set_typTime(dattime,"Stell")
                if delta:
                    dattime = dattime - delta
                else:
                    value = Afp_toTimedelta(self.data.globals.get_value("start-difference","Einsatz"))
                    if not value is None: dattime = dattime -  value
            if self.typ_hasTime(typ):  typ = "Start"
        if typ == "Start":
            if not dattime: dattime = self.get_typTime("Start")
            if dattime: self.set_typTime(dattime,"Start")
      
    # Event Handlers 
    ##  Eventhandler TEXT,  check if time entry has the correct format, \n
    # complete time-text if necessary 
    def On_ChTime(self,event):
        if self.debug: print("Event handler `On_ChTime'")
        if self.is_editable(): 
            object = event.GetEventObject()
            name = object.GetName()
            if not name in self.changed_text: self.changed_text.append(name)  
            if "Zeit" in name: typ = name[:-4]
            else: typ = name[:-3]
            #print "ENTER:", name, typ      
            self.spread_times(typ)
        event.Skip()
      
    ##Eventhandler CHOICE - handle vehicle choice changes
    def On_CBus(self, event):
        if self.debug: print("Event handler `On_CBus'")
        choice = self.choice_Bus.GetStringSelection()
        self.choicevalues["Bus.EINSATZ"] = choice
        self.switch_driver_external(choice == "FREMD")
        event.Skip()

    ##Eventhandler BUTTON - edit triggering incident
    def On_Ein_Typ(self,event):
        if self.debug: print("Event handler `On_Ein_Typ'")
        if self.calling_modul:
            if self.data.is_typ("Miet"):
                FahrtNr = self.data.get_value("MietNr")
                globals = self.data.get_globals()
                #print "AfpDialog_DiEinsatz.On_Ein_Typ:",FahrtNr
                self.calling_modul .AfpLoad_DiChEin_fromFNr(globals, FahrtNr)
        event.Skip()

    ##Eventhandler BUTTON - select address of extern operator
    def On_Ein_AbAdresse(self,event):
        if self.debug: print("Event handler `On_Ein_AbAdresse'")
        if self.selection_is_fremd():
            KNr = AfpLoad_AdAttAusw(self.data.get_globals(), "Busbetrieb")
            if KNr:  
                self.fremd = AfpAdresse(self.data.get_globals(), KNr, None, self.debug)
                self.label_EAbName.SetLabel(self.fremd.get_string_value("Name"))
                self.label_EAbOrt.SetLabel(self.fremd.get_string_value("Ort"))
                self.label_EAbStr.SetLabel(self.fremd.get_string_value("Strasse"))
                self.label_EAbTel.SetLabel(self.fremd.get_string_value("Telefon"))
                self.label_EAbFax.SetLabel(self.fremd.get_string_value("Fax"))
        event.Skip()

    ##Eventhandler BUTTON - select driver entry
    def On_Ein_Fahrer(self,event):
        if self.debug: print("Event handler `On_Ein_Fahrer'")
        Ok = False
        KNr = AfpLoad_AdAttAusw(self.data.get_globals(), "Fahrer")
        if KNr:
            index = None
            if self.calling_modul:
                if self.data.is_typ("Miet"):
                    index = self.calling_modul.AfpChInfo_selectEntry(self.data.get_selection("FAHRTI"))
            Ok = AfpLoad_DiFahrer(self.data, None, KNr, index)
        if Ok: 
            self.Pop_FahrList()
            self.changed_data = True
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()

    ##Eventhandler CLICK - edit driver entry
    def On_Ein_FahrChg(self,event):
        if self.debug: print("Event handler `On_Ein_FahrChg'")
        Ok = False
        index = self.list_FahrList.GetSelections()[0]
        if self.is_editable() and index >= 0:
            Ok = AfpLoad_DiFahrer(self.data, index)
        if Ok: 
            self.Pop_FahrList()
            self.changed_data = True  
        event.Skip()

    ##Eventhandler BUTTON - generate new vehicle operation
    def On_Ein_Neu(self,event):
        if self.debug: print("Event handler `On_Ein_Neu'")
        Ok = False
        index = None
        if self.calling_modul:
            if self.data.is_typ("Miet"):
                index = self.calling_modul.AfpChInfo_selectEntry(self.data.get_selection("FAHRTI"))
                print("AfpDialog_DiEinsatz.On_Ein_Neu:",index)
        if index is None:
            Ok = AfpReq_Question("Zusätzlichen Einsatz für diese Fahrt erstellen?","Einsatzdaten werden kopiert.","zusätzlicher Einsatz?")
        if Ok: 
            self.data.set_new(None, None, index)
            self.new = True
            self.Populate()
            self.choice_Edit.SetSelection(1)
            self.Set_Editable(True)
        event.Skip()

    ##Eventhandler BUTTON - edit triggering incident
    def On_Ein_Loeschen(self,event):
        print("Event handler `On_Ein_Loeschen' not implemented!")
        event.Skip()

    ##Eventhandler BUTTON - edit date entry
    # only needed if calendar-modul has been implemented
    def On_Ein_Termin(self,event):
        if self.debug: print("Event handler `On_Ein_Termin'")
        result = AfpLoad_DiTermin(self.data)
        event.Skip()

    ##Eventhandler BUTTON - edit extern file
    # not implemented yet - possibly not needed
    def On_Ein_Bem(self,event):
        print("Event handler `On_Ein_Bem' not implemented!")
        event.Skip()

    ##Eventhandler BUTTON - generate output documents \n
    # the dialog AfpDialog_DiReport is called
    def On_Ein_Dokument(self,event):
        if self.debug: print("Event handler `On_Ein_Dokument'")
        prefix = "Einsatz_" + self.data.get_string_value()
        header = "Einsatz"
        if self.selection_is_fremd():
            self.data.add_Ausgabe()
            AfpLoad_DiReport(self.data, self.data.globals, None, header, prefix)
        else:
            select = self.list_FahrList.GetSelections()
            if select: 
                datalist = self.data.create_FahrerList(select)
            else:
                datalist = self.data.create_FahrerList()
            if len(datalist) > 0:
                datalist[0].add_Ausgabe()
                AfpLoad_DiReport(datalist, self.data.globals, None, header, prefix)
        event.Skip()

## loader routine for dialog DiEinsatz \n
# @param data - SelectionList for which this vehicle operation is created
# @param direct - allow direct editing
def AfpLoad_DiEinsatz(data, direct = False):
    DiEin = AfpDialog_DiEinsatz(None)
    DiEin.attach_data(data)
    if direct: DiEin.Set_Editable(True)
    DiEin.ShowModal()
    Ok = DiEin.get_Ok()
    DiEin.Destroy()
    return Ok
## loader routines for dialog DiEinsatz with vehicle operation ident number (EinsatzNr) input
# @param globals - global variables including database connection
# @param ENr - verhicle operation ident number (EinsatzNr)
def AfpLoad_DiEinsatz_fromENr(globals, ENr):
    Einsatz = AfpEinsatz(globals, ENr, None, None, None, globals.debug)
    return AfpLoad_DiEinsatz(Einsatz)
    
## Dialog for driver mission
class AfpDialog_DiFahrer(AfpDialog):
    ## constructor
    def __init__(self, *args, **kw):
        self.localtextmap = {}      
        AfpDialog.__init__(self,None, -1, "")
        self.index = None
        self.selection = None
        self.selection_adresse = None

        self.SetSize((374,415))
        self.SetTitle("Fahrer Einsatz")
      
    ## initialise graphic elements  
    def InitWx(self):
        panel = wx.Panel(self, -1)
        self.label_Name = wx.StaticText(panel, -1, label="Name$", pos=(10,6), size=(272,20), name="Name")
        self.label_Kurz = wx.StaticText(panel, -1, pos=(290,6), size=(70,20), name="Kurz")
        self.labelmap["Kurz"] = "Kuerzel"
    #FOUND: DialogFrame "Rahmen", conversion not implemented due to lack of syntax analysis!
        #self.label_TStunden = wx.StaticText(panel, -1, label="&Stunden", pos=(280,60), size=(80,20), name="TStunden")
        self.label_TBeginn = wx.StaticText(panel, -1, label="&Beginn", pos=(10,60), size=(80,20), name="TBeginn")
        self.text_SDat = wx.TextCtrl(panel, -1, value="", pos=(10,84), size=(80,22), style=0, name="SDat")
        self.vtextmap["SDat"] = "Datum"
        self.text_SDat.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Datum)
        self.text_Von = wx.TextCtrl(panel, -1, value="", pos=(10,110), size=(80,22), style=0, name="Von")
        self.vtextmap["Von"] = "Von"
        self.text_Von.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Zeit)
        self.label_TEnde = wx.StaticText(panel, -1, label="&Ende", pos=(100,60), size=(80,20), name="TEnde")
        self.text_EDat = wx.TextCtrl(panel, -1, value="", pos=(100,84), size=(80,22), style=0, name="EDat")
        self.vtextmap["EDat"] = "EndDatum"
        self.text_EDat.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Datum)
        self.text_Bis = wx.TextCtrl(panel, -1, value="", pos=(100,110), size=(80,22), style=0, name="Bis")
        self.vtextmap["Bis"] = "Bis"
        self.text_Bis.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Zeit)
        self.button_Arbeit = wx.Button(panel, -1,  label="&Arbeitszeit", pos=(190,60), size=(80,20), name="BArbeit")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_Arbeit, self.button_Arbeit)
        self.text_Tage = wx.TextCtrl(panel, -1, value="", pos=(190,84), size=(80,22), style=0, name="Tage")
        self.localtextmap["Tage"] = "Tage"
        self.text_Tage.Bind(wx.EVT_KILL_FOCUS, self.On_Ein_calArbeit)
        self.text_ZeitA = wx.TextCtrl(panel, -1, value="", pos=(190,110), size=(40,22), style=0, name="ZeitA")
        self.localtextmap["ZeitA"] = "Std_Start"
        self.text_ZeitA.Bind(wx.EVT_KILL_FOCUS, self.On_Ein_calArbeit)
        self.text_ZeitE = wx.TextCtrl(panel, -1, value="", pos=(230,110), size=(40,22), style=0, name="ZeitE")
        self.localtextmap["ZeitE"] = "Std_Ende"
        self.text_ZeitE.Bind(wx.EVT_KILL_FOCUS, self.On_Ein_calArbeit)
        self.button_Spesen = wx.Button(panel, -1, label="&Spesen", pos=(280,60), size=(80,20), name="BSpesen")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_Spesen, self.button_Spesen)
        self.text_SpesenT = wx.TextCtrl(panel, -1, value="", pos=(280,84), size=(80,22), style=0, name="SpesenT")
        self.textmap["SpesenT"] = "Spesen"
        self.text_SpesenT.Bind(wx.EVT_KILL_FOCUS, self.On_Ein_calSpesen)
        self.text_SpesenSA = wx.TextCtrl(panel, -1, value="", pos=(280,110), size=(40,22), style=0, name="SpesenSA")
        self.textmap["SpesenSA"] = "Spesen_Start"
        self.text_SpesenSA.Bind(wx.EVT_KILL_FOCUS, self.On_Ein_calSpesen)
        self.text_SpesenSE = wx.TextCtrl(panel, -1, value="", pos=(320,110), size=(40,22), style=0, name="SpesenSE")
        self.textmap["SpesenSE"] = "Spesen_Ende"
        self.text_SpesenSE.Bind(wx.EVT_KILL_FOCUS, self.On_Ein_calSpesen)
        self.label_Gesamt = wx.StaticText(panel, -1, label="Gesamt:", pos=(10,134), size=(54,20), name="Gesamt")
        self.label_GTage = wx.StaticText(panel, -1, label="", pos=(65,134), size=(20,20), name="GTage")
        self.labelmap["GTage"] = "Gesamt_Tage"
        self.label_TGTage = wx.StaticText(panel, -1, label="Tage", pos=(90,134), size=(30,20), name="TGTage")
        self.label_GStd = wx.StaticText(panel, -1, label="", pos=(130,134), size=(20,20), name="GStd")
        self.labelmap["GStd"] = "Gesamt_Stunden"
        self.label_TGStd = wx.StaticText(panel, -1, label="Std.", pos=(160,134), size=(20,20), name="TGStd")
        self.label_TGSpesen = wx.StaticText(panel, -1, label="Spesen", pos=(270,134), size=(40,20), name="TGSpesen")
        self.label_GSpesen = wx.StaticText(panel, -1, label="GSpesen$", pos=(315,134), size=(50,20), name="GSpesen")
        self.labelmap["GSpesen"] = "Gesamt_Spesen"
    #FOUND: DialogOptionButton "OpEinsatz", conversion not implemented due to lack of syntax analysis!
    #FOUND: DialogOptionButton "OpArbeit", conversion not implemented due to lack of syntax analysis!
    #FOUND: DialogFrame "GRahmen", conversion not implemented due to lack of syntax analysis!
        self.label_TUebernahme = wx.StaticText(panel, -1, label="Busübernahme", pos=(10,164), size=(100,20), name="TUebernahme")
        self.label_TAbfahrt = wx.StaticText(panel, -1, label="&Datum", pos=(50,184), size=(40,20), name="TADatum")
        self.text_ADat = wx.TextCtrl(panel, -1, value="", pos=(100,182), size=(80,22), style=0, name="ADat")
        self.vtextmap["ADat"] = "Abfahrt"
        self.text_ADat.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Datum)
        self.label_TAbZeit= wx.StaticText(panel, -1, label="&Zeit", pos=(190,184), size=(30,20), name="TAZeit")
        self.text_Ab = wx.TextCtrl(panel, -1, value="", pos=(220,182), size=(80,22), style=0, name="Ab")
        self.vtextmap["Ab"] = "AbZeit"
        self.text_Ab.Bind(wx.EVT_KILL_FOCUS, self.On_Check_Zeit)
        self.label_TAOrt = wx.StaticText(panel, -1, label="&Ort", pos=(60,216), size=(30,20), name="TAOrt")
        self.text_AOrt = wx.TextCtrl(panel, -1, value="", pos=(100,214), size=(260,22), style=0, name="AOrt")
        self.textmap["AOrt"] = "AbOrt"
        self.text_AOrt.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.label_TBem = wx.StaticText(panel, -1, label="Bes&chreibung", pos=(6,240), size=(90,20), name="TBem")
        self.text_Bem = wx.TextCtrl(panel, -1, value="", pos=(100,240), size=(260,80), style=wx.TE_MULTILINE|wx.TE_BESTWRAP, name="Bem")
        self.textmap["Bem"] = "Bem"
        self.text_Bem.Bind(wx.EVT_KILL_FOCUS, self.On_KillFocus)
        self.button_loeschen = wx.Button(panel, -1, label="&Löschen", pos=(100,350), size=(75,30), name="loeschen")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_FahrLoesch, self.button_loeschen)
        self.button_ExText = wx.Button(panel, -1, label="Be&merkung", pos=(185,350), size=(90,30), name="ExText")
        self.Bind(wx.EVT_BUTTON, self.On_Ein_FahrExt, self.button_ExText)
        self.setWx(panel, [10, 350, 80, 20], [285, 350, 75, 30])
      
    ## attach data to dialog and invoke population of the graphic elements
    # @param data - AfpEinsatz for which this driver mission is created
    # @param index - if given, index of row of this driver mission is attached to
    # @param KundenNr - if given and index is None, address identifiction number of new driver this mission is created for
    # @param info - if given, additional info for this new driver mission
    def attach_data(self, data, index, KundenNr = None, info = None):
        self.data = data
        self.debug = self.data.debug
        self.index = index
        self.selection = data.get_selection_from_row("FAHRER", self.index)
        if index is None and KundenNr:
            self.new = True
            self.selection.set_value("EinsatzNr", self.data.get_value("EinsatzNr"))
            self.selection.set_value("FahrerNr", KundenNr)
            datum = self.data.get_value("AbDatum")
            zeit = self.data.get_value("Zeit")
            self.selection.set_value("Datum", datum)
            self.selection.set_value("EndDatum", self.data.get_value("EndDatum"))
            von = self.data.get_value("AbZeit")
            bis = self.data.get_value("EndZeit")
            if von: self.selection.set_value("Von", von)
            if bis: self.selection.set_value("Bis", bis)
            if not info is None:
                row = self.data.get_Fahrtinfo(info)
                #print info, row
                if row[0] and not row[0] == datum: self.selection.set_value("Abfahrt", row[0])
                if row[1] and not row[1] == zeit: self.selection.set_value("AbZeit",row[1])
                if row[2]: self.selection.set_value("AbOrt", row[2])
        else:
            KundenNr = self.selection.get_value("FahrerNr")
        self.selection_adresse = AfpAdresse(self.data.get_globals(), KundenNr)
        self.Populate()
        self.Set_Editable(self.new, True)
        if self.new:
            self.selection.set_value("Kuerzel", self.label_Kurz.GetLabel())
            self.choice_Edit.SetSelection(1)

    ## get value from textbox (needed for formating of dates) \n
    # overwritten from parent
    # @param entry - windowname of calling widget
    def Get_TextValue(self, entry):
        TextBox = self.FindWindowByName(entry)
        wert = TextBox.GetValue()
        if entry in self.vtextmap:
            name = self.vtextmap[entry].split(".")[0]
            wert = Afp_fromString(wert)
        elif entry in self.localtextmap:
            name = self.localtextmap[entry]
        else:
            name = self.textmap[entry]  
        return name, wert

  ## execution in case the OK button ist hit - overwritten from parent
    def execute_Ok(self):
        self.store_data()       
         
    ## read values from dialog and invoke writing into data         
    def store_data(self):
        self.Ok = False
        data = {}
        for entry in self.changed_text:
            name, wert = self.Get_TextValue(entry)
            data[name] = wert
        if data or self.new:
            if data: self.selection.set_data_values(data)
            if self.new:
                self.data.set_row_to_selection_values(self.selection)
            else:
                self.data.set_row_to_selection_values(self.selection, self.index)
            self.Ok = True
            print("set FAHRER:",self.data.selections["FAHRER"].data)
        self.changed_text = []   
        self.choicevalues = {}  
 
    ## dis- or enable editing of dialog widgets \n
    # overwritten from parten to handle 'localtextmap', AfpDialog.SetEditable routine is called here
    # @param ed_flag - flag to turn editing on or off
    # @param lock_data - flag if invoking of dialog needs a lock on the database
    def Set_Editable(self, ed_flag, lock_data = None):
        super(AfpDialog_DiFahrer, self).Set_Editable(ed_flag, lock_data)
        for entry in self.localtextmap:
            #print "Set_Editable", entry, ed_flag
            TextBox = self.FindWindowByName(entry)
            TextBox.SetEditable(ed_flag)
            if ed_flag: TextBox.SetBackgroundColour(self.editcolor)
            else: TextBox.SetBackgroundColour(self.readonlycolor) 
         
    ## population routine for dialog and widgets \n
    # overwritten from parent to handle localtextmap for floats and additional special handlings
    def Populate(self):
        self.Pop_text()
        self.Pop_label()
        vorname = self.selection_adresse.get_string_value("Vorname")
        name = self.selection_adresse.get_string_value("Name")
        self.label_Name.SetLabel(vorname + " " + name)
        kurz = self.selection_adresse.get_short_name()
        self.label_Kurz.SetLabel(kurz)
        for entry in self.localtextmap:
            TextBox = self.FindWindowByName(entry)
            value =self.selection.get_value(self.localtextmap[entry]) 
            string = Afp_toFloatString(value, False, "5.1f")
            #print self.localtextmap[entry], "=", value, "=",string
            TextBox.SetValue(string)
        #print "Populate selection:",self.selection.data
        #print "Populate data[EINSATZ]:",self.data.selections["EINSATZ"].data
        #print "Populate data[FAHRER]:",self.data.selections["FAHRER"].data

    ##  check if date entry in widget has the correct format \n
    # complete time-text if necessary 
    # @param name - name of widget
    def check_datum(self, name):
        TextBox = self.FindWindowByName(name)
        datestring = Afp_ChDatum(TextBox.GetValue())
        if datestring: 
            TextBox.SetValue(datestring)
            self.set_changed(name)
    ##  check if time entry in widget has the correct format \n
    # complete time-text if necessary 
    # @param name - name of widget
    def check_zeit(self, name):
        TextBox = self.FindWindowByName(name)
        timestring, days = Afp_ChZeit(TextBox.GetValue())
        if timestring: 
            TextBox.SetValue(timestring)
            self.set_changed(name)
    ## set if widget has been changed
    # @param name - name of widget
    # @param object - the widget itself
    def set_changed(self, name, object = None):
        if name is None and object:
            name = object.GetName()
        if not name in self.changed_text: self.changed_text.append(name)
    ## set time values for this driver mission
    # @param tage - full days of mission
    # @param abZeit - time on start day of mission
    # @param bisZeit - time on end day of mission
    def set_gesamt_zeit(self, tage, abZeit, bisZeit):
        if tage is None: tage = 0
        ab = Afp_toTimedelta(abZeit)
        bis = Afp_toTimedelta(bisZeit)
        plus, abrest = self.data.get_einsatztage(ab)
        tage += plus
        plus, bisrest = self.data.get_einsatztage(bis)
        tage += plus
        #print "set_gesamt_zeit",tage, type(tage), abrest, type(abrest), bisrest, type(bisrest)
        plus, rest = self.data.get_einsatztage(abrest +bisrest)
        self.label_GTage.SetLabel(Afp_toFloatString(tage+plus, False, "5.1f"))
        self.label_GStd.SetLabel(Afp_toFloatString(rest, False, "5.1f"))

    # Event Handlers 
    ##  Eventhandler BUTTON  allow entry of working dates and times
    def On_Ein_Arbeit(self,event):
        if self.debug: print("Evtent handler `On_Ein_Arbeit'")
        tage = None
        abDat = None
        bisDat = None
        abZeit = None
        bisZeit = None
        string = self.text_SDat.GetValue()
        if string: abDat = Afp_dateString(string)
        string = self.text_EDat.GetValue()
        if string: bisDat = Afp_dateString(string)
        if abDat: 
            if bisDat: tage = Afp_diffDays(abDat, bisDat) + 1
            else: tage = 1
        string = self.text_Von.GetValue()
        if string: abZeit = Afp_timeString(string)
        string = self.text_Bis.GetValue()
        if string: bisZeit = Afp_timeString(string, True)
        if not tage is None:
            if abZeit: tage -= 1
            if bisZeit: tage -= 1
            if tage < 0: tage = 0
            self.text_Tage.SetValue(Afp_toString(tage))
        else:
            self.text_Tage.SetValue("")
        if abZeit: 
            if bisZeit and abDat == bisDat:
                abZeit = Afp_toTimedelta(bisZeit) - Afp_toTimedelta(abZeit)
                bisZeit = None
            else:
                abZeit = Afp_toTimedelta(abZeit, True)
            #print abZeit, bisZeit
            self.text_ZeitA.SetValue(Afp_toString(abZeit))
        else:
            self.text_ZeitA.SetValue("")
        if bisZeit:
            self.text_ZeitE.SetValue(Afp_toString(bisZeit))
        else:
            self.text_ZeitE.SetValue("")
        self.set_gesamt_zeit(tage, abZeit, bisZeit)
        self.set_changed(None, self.text_Tage)
        self.set_changed(None, self.text_ZeitA)
        self.set_changed(None, self.text_ZeitE)
        event.Skip()
      
    ##  Eventhandler BUTTON  allow entries of expenses
    def On_Ein_Spesen(self,event):
        if self.debug: print("Event handler `On_Ein_Spesen'")
        tage = Afp_fromString(self.text_Tage.GetValue())
        stdA = Afp_fromString(self.text_ZeitA.GetValue())
        stdE = Afp_fromString(self.text_ZeitE.GetValue())
        if tage:
            spT = self.data.get_spesen(tage)
            self.text_SpesenT.SetValue(Afp_toString(spT))
        else:
            self.text_SpesenT.SetValue("")
        if stdA:
            spA = self.data.get_spesen(None, Afp_TimeToFloat(stdA))
            self.text_SpesenSA.SetValue(Afp_toString(spA).strip())
        else:
            self.text_SpesenSA.SetValue("")
        if stdE:
            spE = self.data.get_spesen(None, Afp_TimeToFloat(stdE))
            self.text_SpesenSE.SetValue(Afp_toString(spE).strip())
        else:
            self.text_SpesenSE.SetValue("")
        self.On_Ein_calSpesen()
        self.set_changed(None, self.text_SpesenT)
        self.set_changed(None, self.text_SpesenSA)
        self.set_changed(None, self.text_SpesenSE)
        event.Skip()

    ##  Eventhandler TEXT  set dependent date and time widgets\n
    def On_Ein_calArbeit(self,event):
        if self.debug: print("Event handler `On_Ein_calArbeit'")
        name = event.GetEventObject().GetName()
        if "Zeit" in name: self.check_zeit(name)
        tage = Afp_fromString(self.text_Tage.GetValue())
        abZeit = Afp_fromString(self.text_ZeitA.GetValue())
        bisZeit = Afp_fromString(self.text_ZeitE.GetValue())
        #print tage, type(tage), abZeit, type(abZeit), bisZeit, type(bisZeit)
        self.set_gesamt_zeit(tage, abZeit, bisZeit)
        self.On_KillFocus(event)
        event.Skip()  
      
    ##  Eventhandler TEXT  set dependent expense widgets\n
    def On_Ein_calSpesen(self,event = None):
        if self.debug: print("Event handler `On_Ein_calSpesen'")
        spesen = 0.0
        val= Afp_fromString(self.text_SpesenT.GetValue())
        if Afp_isNumeric(val): spesen += val
        val = Afp_fromString(self.text_SpesenSA.GetValue())
        if Afp_isNumeric(val): spesen += val
        val = Afp_fromString(self.text_SpesenSE.GetValue())
        if Afp_isNumeric(val): spesen += val
        self.label_GSpesen.SetLabel(Afp_toString(spesen))
        if event:
            self.On_KillFocus(event)
            event.Skip()

    ##  Eventhandler TEXT,  check if date entry has the correct format, \n
    # complete date-text if necessary 
    def On_Check_Datum(self,event):
        if self.debug: print("Event handler `On_Check_Datum'")
        self.check_datum(event.GetEventObject().GetName())
        self.On_KillFocus(event)
        event.Skip()

    ##  Eventhandler TEXT,  check if time entry has the correct format, \n
    # complete time-text if necessary 
    def On_Check_Zeit(self,event):
        if self.debug: print("Event handler `On_Check_Zeit'")    
        self.check_zeit(event.GetEventObject().GetName())
        self.On_KillFocus(event)
        event.Skip()
      
    ##  Eventhandler BUTTON,  delete this driver mission
    def On_Ein_FahrLoesch(self,event):
        if self.debug: print("Event handler `On_Ein_FahrLoesch'")
        name = self.label_Name.GetLabel()
        Ok = AfpReq_Question("Soll das Fahrereinsatz von '" +name + "'", "für diese Fahrt gelöscht werden?", "Löschen?")
        if Ok:
            self.data.delete_row("FAHRER", self.index)
            self.store_data()
            self.Ok = True
            self.EndModal(wx.ID_OK)
        event.Skip()

    ##  Eventhandler BUTTON,  edit extern textfile \n
    # not implemented yet - possibly not needed
    def On_Ein_FahrExt(self,event):
        print("Event handler `On_Ein_FahrExt' not implemented!")
        event.Skip()

## loader routine for dialog DiFahrer
# @param data - AfpEinsatz for which this driver mission is created
# @param index - if given, index of row of this driver mission is attached to
# @param KundenNr - if given and index is None, address identifiction number of new driver this mission is created for
# @param info - if given, additional info for this new driver mission
def AfpLoad_DiFahrer(data, index , KundenNr = None, info = None):
    DiFahr = AfpDialog_DiFahrer(None)
    print(index, KundenNr)
    DiFahr.attach_data(data, index, KundenNr, info)
    DiFahr.ShowModal()
    Ok = DiFahr.get_Ok()
    DiFahr.Destroy()
    return Ok

## dialog for editing of calendar entries and generating .ics files
class AfpDialog_DiTermin(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        AfpDialog.__init__(self,None, -1, "")
        self.changed = False
        self.SetTitle("Termine")
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
        #self.SetSize((350,350))
        self.SetSize((400,350))
        
    ## initialise graphic elements
    def InitWx(self):
        self.label_text_1= wx.StaticText(self, -1, name="text_1")        
        self.label_text_2= wx.StaticText(self, -1, name="text_2")        
        self.label_cal_url = wx.StaticText(self, -1, name="cal_url")        
        self.label_cal_name = wx.StaticText(self, -1, name="cal_name")
        self.label_mail_server = wx.StaticText(self, -1, name="mail_server")
        self.label_mail_address = wx.StaticText(self, -1, name="mail_address")
        self.text_filename = wx.TextCtrl(self, -1, name="filename")
        self.list_Events = wx.ListBox(self, -1, name="Events")      
        self.listmap.append("Events")
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.On_Set_Event, self.list_Events)
        self.button_delete = wx.Button(self, -1, label="&Löschen", name="delete")
        self.Bind(wx.EVT_BUTTON, self.On_Button_Delete, self.button_delete)
        self.button_insert = wx.Button(self, -1, label="&Eintragen", name="insert")
        self.Bind(wx.EVT_BUTTON, self.On_Button_Insert, self.button_insert)
        self.button_send = wx.Button(self, -1, label="&Versenden", name="send")
        self.Bind(wx.EVT_BUTTON, self.On_Button_Send, self.button_send)
        self.button_write = wx.Button(self, -1, label="&Schreiben", name="write")
        self.Bind(wx.EVT_BUTTON, self.On_Button_Write, self.button_write)
        self.cal_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cal_left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.cal_left_sizer.Add(self.label_cal_name,0,wx.EXPAND)
        self.cal_left_sizer.Add(self.label_cal_url,0,wx.EXPAND)        
        self.cal_right_sizer = wx.BoxSizer(wx.VERTICAL)
        self.cal_right_sizer.Add(self.button_delete,0,wx.EXPAND)
        self.cal_right_sizer.Add(self.button_insert,0,wx.EXPAND)        
        #self.cal_sizer.AddStretchSpacer(1)       
        self.cal_sizer.Add(self.cal_left_sizer,0,wx.EXPAND)        
        #self.cal_sizer.AddSpacer(10)           
        self.cal_sizer.AddStretchSpacer(1)                                 
        self.cal_sizer.Add(self.cal_right_sizer,0,wx.EXPAND)        
        self.mail_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mail_left_sizer = wx.BoxSizer(wx.VERTICAL)
        self.mail_left_sizer.Add(self.label_mail_address,0,wx.EXPAND)
        self.mail_left_sizer.Add(self.label_mail_server,0,wx.EXPAND)         
        #self.mail_sizer.AddStretchSpacer(1)              
        self.mail_sizer.Add(self.mail_left_sizer,0,wx.EXPAND)        
        #self.mail_sizer.AddSpacer(10)        
        self.mail_sizer.AddStretchSpacer(1)                            
        self.mail_sizer.Add(self.button_send,0,wx.EXPAND)        
        self.file_sizer = wx.BoxSizer(wx.HORIZONTAL)        
        #self.file_sizer.AddStretchSpacer(1)       
        self.file_sizer.Add(self.text_filename,1,wx.EXPAND)         
        self.file_sizer.AddSpacer(10)                     
        self.file_sizer.Add(self.button_write,0,wx.EXPAND)        
        self.lower_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.setWx(self.lower_sizer,[1, 3, 1], [0, 3, 1]) 
        self.inner_sizer=wx.BoxSizer(wx.VERTICAL)
        self.inner_sizer.Add(self.label_text_1,0,wx.EXPAND)
        self.inner_sizer.Add(self.label_text_2,0,wx.EXPAND)
        self.inner_sizer.AddSpacer(10)
        self.inner_sizer.Add(self.list_Events,1,wx.EXPAND)
        self.inner_sizer.AddSpacer(10)
        self.inner_sizer.Add(self.cal_sizer,0,wx.EXPAND)
        self.inner_sizer.AddSpacer(10)
        self.inner_sizer.Add(self.mail_sizer,0,wx.EXPAND)
        self.inner_sizer.AddSpacer(10)
        self.inner_sizer.Add(self.file_sizer,0,wx.EXPAND)
        self.inner_sizer.AddSpacer(10)
        self.inner_sizer.Add(self.lower_sizer,0,wx.EXPAND)
        self.inner_sizer.AddSpacer(10)
        self.sizer=wx.BoxSizer(wx.HORIZONTAL)  
        self.sizer.AddSpacer(10)     
        self.sizer.Add(self.inner_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)    
        
    ## attach data and labels to dialog
    # @param data - SelectionList to be used for this dialog
    def attach_data(self, data):
        self.cal = None
        self.mail = None
        self.data = data
        self.globals = data.get_globals()
        self.calendar = data.calendar
        self.debug = data.is_debug()
        self.Populate()
    ## overwritten population routine for labels 
    def Pop_label(self):
        bus = self.data.get_string_value("Bus") 
        globals = self.data.get_globals()
        label1 = "Einsatz " + bus + " nach " +  self.data.get_cal_summary() + "\n"
        label1 += "vom " +  self.data.get_string_value("AbDatum") + " bis zum "  + self.data.get_string_value("EndDatum") 
        #label1 = ("Einsatz %s nach %s") % self.data.get_string_value("Bus"),  self.data.get_cal_summary()
        #label1 = label1
        uid = self.data.get_string_value("Datei")
        if not uid: uid = "kein Termin erzeugt!"        
        label2 = "UID: " + uid
        #label2 = ("vom %s um %s bis zum %s um %s")% self.data.get_string_value("AbDatum"), self.data.get_string_value("AbZeit"),self.data.get_string_value("EndDatum"), self.data.get_string_value("EndZeit")
        #label2 = label2
        self.label_text_1.SetLabel(label1)
        self.label_text_2.SetLabel(label2)
        url = ""
        if self.calendar:
            url = self.globals.get_value("caldav-url")
        if not url: 
            url = "nicht aktiv!"
            self.enable_cal(False)
        self.cal = bus
        self.label_cal_name.SetLabel("Kalendername: " + bus)
        self.label_cal_url.SetLabel("Kalenderadresse:\n" + url)
        host = self.globals.get_value("smtp-host")
        self.mail = self.globals.get_value("mail-sender")
        if not host or not self.mail: 
            host = "nicht aktiv!"
            self.mail = ""
            self.enable_mail(False)
        self.label_mail_server.SetLabel("Mailserver: " + host)
        self.label_mail_address.SetLabel("EMail an: " + self.mail)
        temp = self.globals.get_value("tempdir")
        fname = temp + "icalendar.ics"
        if self.mail: fname = temp + self.mail + ".ics"
        if self.cal: fname = temp + self.cal + ".ics"
        self.text_filename.SetValue(fname) 
    ## enable calendar widgets
    # @param flag - flag if widget should be enabled or disabled
    def enable_cal(self, flag = True):
        self.label_cal_name.Enable(flag)
        self.label_cal_url.Enable(flag)
        self.button_delete.Enable(flag)
        self.button_insert.Enable(flag)
    ## enable email widgets
    # @param flag - flag if widget should be enabled or disabled
    def enable_mail(self, flag = True):
        self.label_mail_address.Enable(flag)
        self.label_mail_server.Enable(flag)
        self.button_send.Enable(flag)
    ## populate the 'Events' list, \n
    # this routine is called from the AfpDialog.Populate
    def Pop_Events(self): 
        liste = [] 
        if self.data:
            liste = self.data.get_selection().get_value_lines("Bus,StellDatum,StellZeit,EndZeit,EndDatum,Zeit,Datum,StellOrt")
            if self.data.exists_selection("FAHRER"):
                rows = self.data.get_value_rows("FAHRER", "Kuerzel,Datum,Von,Bis,EndDatum,AbZeit,Abfahrt,AbOrt")
                for row in rows:
                    liste.append(AfpEinsatz_setFahrerLineFromRow(self.data.get_value("Datum"),row))
        self.list_Events.Clear()
        self.list_Events.InsertItems(liste, 0)
    ## Eventhandler CLICK - list entry selected
    # @param event - event which initiated this action
    def On_Set_Event(self, event):
        if self.debug: print("Event handler `On_Set_Event'")
        index = self.list_Events.GetSelections()[0] 
        if index:
            Fahrer = AfpFahrer(self.globals, self.data, index-1, self.debug)
            uid = Fahrer.get_value("ExText")
            if not uid: uid =  "kein Fahrertermin erzeugt!"    
            self.mail = Fahrer.get_value("Mail.ADRESSE")
            self.cal = Fahrer.get_value("Kuerzel")
            name = Fahrer.get_name().replace(" ", "_")
            temp = self.globals.get_value("tempdir")
            self.label_text_2.SetLabel( "UID: " + uid)
            self.label_cal_name.SetLabel("Kalendername: " + self.cal)
            self.label_mail_address.SetLabel("EMail an: " + self.mail)
            self.text_filename.SetValue(temp + name + ",ics") 
        else:
            self.Pop_label()
        
    ## Eventhandler BUTTON - Delete button pushed
    # @param event - event which initiated this action
    def On_Button_Delete(self, event):
        if self.debug: print("Event handler `On_Button_Delete'")
        selects = self.list_Events.GetSelections()
        if selects: index = selects[0]
        else: index = 0
        if index:
            self.data.gen_driver_targetevent(index-1, self.cal, None, None, False, True)
        else:
            self.data.gen_vehicle_targetevent(None, self.cal, None)
        self.data.perform_calendar_action("delete_all")
    ## Eventhandler BUTTON - Insert button pushed
    # @param event - event which initiated this action
    def On_Button_Insert(self, event):
        if self.debug: print("Event handler `On_Button_Insert'")
        selects = self.list_Events.GetSelections()
        if selects: index = selects[0]
        else: index = 0
        if index:
            self.data.gen_driver_targetevent(index-1, self.cal, None)
        else:
            self.data.gen_vehicle_targetevent(True, self.cal, None)
        self.data.perform_calendar_action("strict")
    ## Eventhandler BUTTON - Send button pushed
    # @param event - event which initiated this action
    def On_Button_Send(self, event):
        if self.debug: print("Event handler `On_Button_Send'")
        selects = self.list_Events.GetSelections()
        if selects: index = selects[0]
        else: index = 0
        if index:
            self.data.gen_driver_targetevent(index-1, None, self.mail)
        else:
            self.data.gen_vehicle_targetevent(True, None, self.mail)
        self.data.perform_calendar_action("keep_mails")
        mailsenders = self.data.get_calendar_mailsenders()
        if mailsenders:
            for sender in mailsenders:
                mail, ok = Afp_editMail(sender)
                if ok: mail.send_mail()
    ## Eventhandler BUTTON - Write button pushed
    # @param event - event which initiated this action
    def On_Button_Write(self, event):
        if self.debug: print("Event handler `On_Button_Write'")
        fname = self.text_filename.GetValue()
        selects = self.list_Events.GetSelections()
        if selects: index = selects[0]
        else: index = 0
        if index:
            self.data.gen_driver_targetevent(index-1, None, None, fname)
        else:
            self.data.gen_vehicle_targetevent(True, None, None, fname)
        self.data.perform_calendar_action("strict")
 
## loader routine for dialog editArchiv \n
# @param data - given SelectionList, where archiv should be manipulated
def AfpLoad_DiTermin(data):
    dialog = AfpDialog_DiTermin(None)
    dialog.attach_data(data)
    Ok = None
    dialog.ShowModal()
    dialog.Destroy()
    return Ok  

