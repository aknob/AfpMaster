#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseScreen
# AfpBaseScreen module provides the base class of all Afp-screens and the global screen loader routine
# it holds the calsses
# - AfpScreen - screen base class
#
#   History: \n
#        05 Mar. 2015 - move screen base class to separate file - Andreas.Knoblauch@afptech.de \n
#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright© 1989 - 2015  afptech.de (Andreas Knoblauch)
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

import AfpUtilities.AfpBaseUtilities
from AfpUtilities.AfpBaseUtilities import Afp_existsFile
import AfpDatabase.AfpSuperbase
from AfpDatabase.AfpSuperbase import AfpSuperbase

import AfpBaseRoutines
from AfpBaseRoutines import Afp_importPyModul, Afp_importAfpModul, Afp_ModulNames, Afp_archivName, Afp_startExtraProgram
import AfpBaseDialogCommon
from AfpBaseDialogCommon import AfpLoad_editArchiv, AfpReq_Information, AfpReq_Version, AfpReq_extraProgram
import AfpGlobal
from AfpGlobal import *

## base class for Screens
class AfpScreen(wx.Frame):
    ## constructor
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.typ = None
        self.debug = False
        self.globals = None
        self.mysql = None
        self.setting = None
        self.sb = None
        self.sb_filter = ""
        self.data = None
        self.menu_items = {}
        self.labelmap = {}
        self.textmap = {}
        self.choicemap = {}
        self.extmap = {}
        self.listmap =[]
        self.list_id = {}
        self.gridmap = []
        self.grid_id = {}
        self.grid_minrows = {}
        self.filtermap = {}
        self.indexmap = {}
        self.no_keydown = []     
        self.buttoncolor = (230,230,230)
        self.actuelbuttoncolor = (255,255,255)
        self.readonlycolor = self.GetBackgroundColour()
        self.editcolor = (255,255,255)
        self.editable = False
        self.panel = wx.Panel(self, -1, style = wx.WANTS_CHARS) 
        
    ## connect to database and populate widgets
    # @param globals - global variables, including database connection
    # @param sb - AfpSuperbase database object , if supplied, otherwise it is created
    # @param origin - string from where to get data for initial record, 
    # to allow syncronised display of screens (only works if 'sb' is given)
    def init_database(self, globals, sb, origin):
        self.globals = globals
        self.create_menubar()
        self.create_modul_buttons()
        # set header
        self.SetTitle(globals.get_host_header())
        # shortcuts for convienence
        self.mysql = self.globals.get_mysql()
        self.debug = self.globals.is_debug()
        #self.debug = True
        self.globals.set_value(None, None, self.typ)
        self.load_additional_globals()
        # add 'Einsatz' moduls if desired
        if hasattr(self,'einsatz'):
            self.einsatz = Afp_importAfpModul("Einsatz", globals)
        else:
            self.einsatz = None
        print "AfpScreen.init_database Einsatz:", self.einsatz
        # Keyboard Binding
        self.no_keydown = self.get_no_keydown()
        self.panel.Bind(wx.EVT_KEY_DOWN, self.On_KeyDown)
        self.panel.SetFocus()
        children = self.panel.GetChildren()
        for child in children:
            if not child.GetName() in self.no_keydown:
                child.Bind(wx.EVT_KEY_DOWN, self.On_KeyDown)
        # generate Superbase
        setting = self.globals.get_setting(self.typ)
        if not self.debug and not setting is None: 
            if setting.exists_key("debug"):
                self.debug = setting.get("debug")
        if sb:
            self.sb = sb
        else:
            self.sb = AfpSuperbase(self.globals, self.debug)
        dateien = self.get_dateinamen()
        for datei in dateien:
            self.sb.open_datei(datei)
        self.set_initial_record(origin)
        self.set_current_record()
        self.Populate()
    
    ## create menubar and add common items \n
    # menubar implementation has only be done to this point, specific Afp-modul menues are not yet implemented
    def create_menubar(self):
        self.menubar = wx.MenuBar()
        # setup screen menu
        tmp_menu = wx.Menu()
        modules = Afp_ModulNames(self.globals)
        for mod in modules:
            new_id = wx.NewId()
            self.menu_items[new_id] = wx.MenuItem(tmp_menu, new_id, mod, "", wx.ITEM_CHECK)
            tmp_menu.AppendItem(self.menu_items[new_id])
            self.Bind(wx.EVT_MENU, self.On_Screenitem, self.menu_items[new_id])
            if self.menu_items[new_id].GetText() == self.typ: self.menu_items[new_id].Check(True)
        new_id = wx.NewId()
        self.menu_items[new_id] = wx.MenuItem(tmp_menu, new_id, "Beenden", "")
        tmp_menu.AppendItem(self.menu_items[new_id])
        self.Bind(wx.EVT_MENU, self.On_Screenitem, self.menu_items[new_id])
        self.menubar.Append(tmp_menu, "Bildschirm")
        # setup modul specific menu parts
        self.create_specific_menu()
        # setup extra menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Archiv", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenArchiv, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Zusatzprogramme", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenZusatz, mmenu)
        tmp_menu.AppendItem(mmenu)
        self.menubar.Append(tmp_menu, "Extra")
       # setup info menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Version", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenVersion, mmenu)
        tmp_menu.AppendItem(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Info", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenInfo, mmenu)
        tmp_menu.AppendItem(mmenu)
        self.menubar.Append(tmp_menu, "?")
        self.SetMenuBar(self.menubar)
    ## setup typ specific menu \n
    # to be overwritten in devired class
    def create_specific_menu(self):
        return
   
    ## create buttons to switch modules 
    def create_modul_buttons(self):
        modules = Afp_ModulNames(self.globals)
        panel = self.panel
        cnt = 0
        self.button_modules = {}
        for mod in modules:
            self.button_modules[mod] = wx.Button(panel, -1, label=mod, pos=(35 + cnt*80,10), size=(75,30), name="B"+ mod)
            self.Bind(wx.EVT_BUTTON, self.On_ScreenButton, self.button_modules[mod])
            cnt += 1
            if mod == self.typ:
                self.button_modules[mod] .SetBackgroundColour(self.actuelbuttoncolor)
            else:
                self.button_modules[mod] .SetBackgroundColour(self.buttoncolor)

    ## resize grid rows
    # @param name - name of grid
    # @param grid - the grid object
    # @param new_lgh - new number of rows to be populated
    def grid_resize(self, name, grid, new_lgh):
        if new_lgh < self.grid_minrows[name]:
            new_lgh =  self.grid_minrows[name]
        old_lgh = grid.GetNumberRows()
        if new_lgh > old_lgh:
            grid.AppendRows(new_lgh - old_lgh)
        elif  new_lgh < old_lgh:
            for i in range(new_lgh, old_lgh):
                grid.DeleteRows(1)
                
    ## central routine which returns if screen is in editable mode
    def is_editable(self):
        #editable = False
        #if self.panel.GetBackgroundColour() == self.editcolor: editable = True
        #return editable
        return self.editable
    
    ## Eventhandler Menu - show version information
    def On_ScreenVersion(self, event):
        if self.debug: print "AfpScreen Event handler `On_ScreenVersion'!"
        AfpReq_Version(self.globals)
    ## Eventhandler Menu - show info dialog box
    def On_ScreenInfo(self, event):
        if self.debug: print "AfpScreen Event handler `On_ScreenInfo'!"
        AfpReq_Information(self.globals)
   ## Eventhandler Menu - add or delete files in archiv
    def On_ScreenArchiv(self, event):
        if self.debug: print "AfpScreen Event handler `On_ScreenArchiv'!"
        data = self.get_data()
        ok = AfpLoad_editArchiv(data,  "Archiv von " + data.get_name() , data.get_identification_string())
        if ok: self.Reload()
   ## Eventhandler Menu - select and start additional programs
    def On_ScreenZusatz(self, event):
        if self.debug: print "AfpScreen Event handler `On_ScreenZusatz'!"
        print "AfpScreen Event handler `On_ScreenZusatz' not implemented!"
        fname, ok = AfpReq_extraProgram(self.globals.get_value("extradir"), self.typ)
        if ok and fname:
            Afp_startExtraProgram(fname, self.globals, self.debug)
      
    ## Eventhandler Menu - switch between screen
    def On_Screenitem(self, event):
        if self.debug: print "AfpScreen Event handler `On_Screenitem'!"
        id = event.GetId()
        item = self.menu_items[id]
        text = item.GetText() 
        #print id, text
        if text == self.typ:
            item.Check(True)
        elif text == "Beenden":
            self.On_Ende(event)
        else:
            # Afp_writeTarget(self.globals, text, self.typ)
            Afp_loadScreen(self.globals, text, self.sb, self.typ)
            self.Close()
        #event.Skip() #invokes eventhandler twice on windows

    ## Enventhandler BUTTON - switch modules
    def On_ScreenButton(self,event):
        if self.debug: print "AfpScreen Event handler `On_ScreenButton'!"
        object = event.GetEventObject()
        name = object.GetName()
        text = name[1:]
        if not text == self.typ:
            Afp_loadScreen(self.globals, text, self.sb, self.typ)
            self.Close()
        #event.Skip() #invokes eventhandler twice on windows
      
 ## Eventhandler BUTTON - quit
    def On_Ende(self,event):
        if self.debug: print "AfpScreen Event handler `On_Ende'!"
        self.Close()
        event.Skip()

    ## Eventhandler Keyboard - handle key-down events
    def On_KeyDown(self, event):
        keycode = event.GetKeyCode()        
        if self.debug: print "AfpScreen Event handler `On_KeyDown'", keycode
        #print "AfpScreen Event handler `On_KeyDown'", keycode
        caught = 0
        if keycode == wx.WXK_LEFT: caught = -1
        if keycode == wx.WXK_RIGHT: caught = 1
        if self.editable: caught = 0
        #print "AfpScreen Event handler `On_KeyDown'", keycode, self.editable, next
        if caught: 
            self.CurrentData(caught)
        else: 
            caught = self.invoke_special_keydown(keycode)
            if not caught: event.Skip()

     
    ## Population routines for form and widgets
    def Populate(self):
        self.Pop_label()
        self.Pop_text()
        self.Pop_ext()
        self.Pop_grid()
        self.Pop_list()
        self.Pop_special()
    ## populate label widgets
    def Pop_label(self):
        for entry in self.labelmap:
            Label = self.FindWindowByName(entry)
            if self.data:
                value = self.data.get_string_value(self.labelmap[entry])
            else:
                value = self.sb.get_string_value(self.labelmap[entry])
            Label.SetLabel(value)
    ## populate text widgets
    def Pop_text(self):
        for entry in self.textmap:
            TextBox = self.FindWindowByName(entry)
            if self.data:
                value = self.data.get_string_value(self.textmap[entry])
            else:
                value = self.sb.get_string_value(self.textmap[entry])
            TextBox.SetValue(value)
    ## populate external file textboxes
    def Pop_ext(self):
        delimiter = self.globals.get_value("path-delimiter")
        for entry in self.extmap:
            filename = ""
            TextBox = self.FindWindowByName(entry) 
            if self.data:
                text = self.data.get_string_value(self.extmap[entry])
            else:
                text = self.sb.get_string_value(self.extmap[entry])
            file= Afp_archivName(text, delimiter)
            if file:
                filename = self.globals.get_value("antiquedir") + file
                if not Afp_existsFile(filename): 
                    #if self.debug: 
                    print "WARNING in AfpScreen: External file", filename, "does not exist!"
                    filename = ""
            if filename:
                #print "AfpScreen LoadFile", self.extmap[entry], filename
                TextBox.LoadFile(filename)
            else:
                TextBox.Clear()
                if text: TextBox.SetValue(text)
    ## populate lists
    def Pop_list(self):
        for entry in self.listmap:
            rows = self.get_list_rows(entry)
            list = self.FindWindowByName(entry)
            if None in rows:
                ind = rows.index(None)
                self.list_id[entry] = rows[ind+1:]
                rows = rows[:ind]
            list.Clear()
            if rows:
                list.InsertItems(rows, 0)
    ## populate grids
    # @param name - if given ,name of grid to be populated 
    def Pop_grid(self, name = None):
        for typ in self.gridmap:
            if not name or typ == name:
                rows = self.get_grid_rows(typ)
                grid = self.FindWindowByName(typ)
                self.grid_resize(typ, grid, len(rows))
                self.grid_id[typ] = []
                row_lgh = len(rows)
                max_col_lgh = grid.GetNumberCols()
                if rows: act_col_lgh = len(rows[0]) - 1
                for row in range(0,row_lgh):
                    for col in range(0,max_col_lgh):
                        if col >= act_col_lgh:
                            grid.SetCellValue(row, col, "")
                        else:
                            grid.SetCellValue(row, col, rows[row][col])
                    self.grid_id[typ].append(rows[row][act_col_lgh])
                if row_lgh < self.grid_minrows[typ]:
                    for row in range(row_lgh, self.grid_minrows[typ]):
                        for col in range(0,max_col_lgh):
                            grid.SetCellValue(row, col,"")
    ## population routine for special treatment - to be overwritten in derived class
    def Pop_special(self):
        return
 
    ## set or unset editable mode
    # @param ed_flag - flag to turn editing on or off
    # @param lock_data - flag if invoking of editable mode needs a lock on the database
    def Set_Editable(self, ed_flag, lock_data = None):
        self.editable = ed_flag
        if ed_flag:
            self.panel.SetBackgroundColour(self.editcolor)
        else:
            self.panel.SetBackgroundColour(self.readonlycolor)
        self.panel.Refresh()
        if lock_data and self.data:
            if ed_flag:
                if not self.data.new: self.data.lock_data()
            else: 
                if not self.data.new: self.data.unlock_data()
  
    ## reload current data to screen
    def Reload(self):
        self.sb.select_current()
        self.CurrentData()
         
    ## set current screen data
    # @param plus - indicator to step forwards, backwards or stay
    def CurrentData(self, plus = 0):
        if self.debug: print "AfpScreen.CurrentData", plus
        #self.sb.set_debug()
        if plus == 1:
            self.sb.select_next()
        elif plus == -1:
            self.sb.select_previous()
        self.set_current_record()
        #self.sb.unset_debug()
        self.Populate()

    # routines to be overwritten in explicit class
    ## load additional global data for this Afp-modul
    # default - empty, to be overwritten if needed
    def load_additional_globals(self): # only needed if globals for additonal moduls have to be loaded
        return
    ## generate explicit data class object from the present screen
    # @param complete - flag if all TableSelections should be generated
    def get_data(self, complete = False):
        return  None
    ## set current record to be displayed 
    # default - empty, to be overwritten if changes have to be diffused to other the main database table
    def set_current_record(self): 
        return   
    ## set initial record to be shown, when screen opens the first time
    # default - empty, should be overwritten to assure consistant data on frist screen
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        return
    ## get identifier of graphical objects, 
    # where the keydown event should not be catched
    # default - empty, to be overwritten if needed
    def get_no_keydown(self):
        return []
    ## get names of database tables to be opened for the screen
    # default - empty, has to be overwritten
    def get_dateinamen(self):
        return []
    ## get rows to populate lists \n
    # default - empty, to be overwritten if grids are to be displayed on screen \n
    # possible selection criterias have to be separated by a "None" value
    # @param typ - name of list to be populated 
    def get_list_rows(self, typ):
        return [] 
    ## get grid rows to populate grids \n
    # default - empty, to be overwritten if grids are to be displayed on screen
    # @param typ - name of grid to be populated
    # - REMARK: last column will not be shown, but stored for identifiction
    def get_grid_rows(self, typ):
        return []   
    ## invoke special keydown handling, additional to scrolling forward and backward\n
    # default - don't do anything, to be overwritten if special key handling is desired \n
    # return flag if key has been caught
    def invoke_special_keydown(self, keycode):
        return False
# End of class AfpScreen

## loader roution for Screens
# @param globals - global variables, holding mysql access
# @param modulname - name of modul this screen belongs to, the appropriate modulfile will be imported
# @param sb - AfpSuperbase object which holds the current settings on the mysql tables
# @param origin - value which identifies mysql tableentry to be displayed
# the parameter 'sb' and 'origin' may only be used aternatively
def Afp_loadScreen(globals, modulname, sb = None, origin = None):
    Modul = None
    moduls = Afp_ModulNames(globals)
    if modulname in moduls:
        screen = "Afp" + modulname[:2] + "Screen" 
        modname = "Afp" + modulname + "." + screen 
        print "Afp_loadScreen:", modname
        pyModul =  Afp_importPyModul(modname, globals)
        #print "Afp_loadScreen:", pyModul
        pyBefehl = "Modul = pyModul." + screen + "()"
        #print "Afp_loadScreen:", pyBefehl
        exec pyBefehl
    if Modul:
        Modul.init_database(globals, sb, origin)
        Modul.Show()
        return Modul
    else:
        return None
        