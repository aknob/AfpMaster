#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseScreen
# AfpBaseScreen module provides the base class of all Afp-screens and the global screen loader routine
# it holds the calsses
# - AfpScreen - screen base class
#
#   History: \n
#        31 Jan. 2025 - add readonly flag and color - Andreas.Knoblauch@afptech.de \n
#        26 Nov. 2024 - add set_initial_gridrow - Andreas.Knoblauch@afptech.de \n
#        24 Okt. 2024 - adaption to python 3.12 - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        20 Okt. 2019 - enable grid sort mechnismn - Andreas.Knoblauch@afptech.de \n
#        31 Jan. 2018 - enable tagged value evaluation for textfields - Andreas.Knoblauch@afptech.de \n
#        05 Mar. 2015 - move screen base class to separate file - Andreas.Knoblauch@afptech.de \n
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

from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile
from AfpBase.AfpDatabase.AfpSuperbase import AfpSuperbase

from AfpBase.AfpBaseRoutines import Afp_importPyModul, Afp_importAfpModul, Afp_ModulNames, Afp_getModulShortName, Afp_getModulFlavour, Afp_inModuls, Afp_archivName, Afp_startExtraProgram
from AfpBase.AfpBaseDialog import AfpReq_Question
from AfpBase.AfpBaseDialogCommon import AfpLoad_editArchiv, AfpReq_Information, AfpReq_Version, AfpReq_extraProgram
from AfpBase.AfpBaseFiDialog import Afp_handleCommonInvoice, Afp_handleObligation
from AfpBase.AfpGlobal import *

## base class for Screens
class AfpScreen(wx.Frame):
    ## constructor
    def __init__(self, *args, **kwds):
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.typ = None
        self.debug = False
        self.globals = None
        self.sizer = None
        self.modul_button_sizer = None
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
        # common grid handling
        self.gridmap = []
        self.grid_rows = {}
        self.grid_minrows = {}
        self.grid_cols = {}
        self.grid_id = {}
        # sorting grids
        self.grid_sort_col = {}
        self.grid_sort_desc = {}
        self.grid_sort_rows = None # sorting turned off by default
        #self.grid_sort_rows = {}  # use this line in devired screen to turn it on
        # dynamic grid handling during resizing
        self.dynamic_grid_name= None
        self.dynamic_grid_col_percents = None
        self.dynamic_grid_col_labels = None
        # control settings for database selections
        self.filtermap = {}
        self.indexmap = {}
        self.no_keydown = []
        self.readonly = None
        self.windowsbackgroundcolor = (239, 235, 222)
        #self.readonlycolor = wx.Colour(192, 220, 192)
        self.readonlycolor = wx.Colour(220, 192, 192)
        #self.buttoncolor = (230,230,230)
        self.buttoncolor = (220,220,220)
        self.actuelbuttoncolor = (255,255,255)
        #self.panel = wx.Panel(self, -1, style = wx.WANTS_CHARS) 
        self.panel = self
        self.font = None
        self.no_data_shown = None
        if not hasattr(self,'flavour'): self.flavour = None
        
    ## connect to database and populate widgets
    # @param globals - global variables, including database connection
    # @param sb - AfpSuperbase database object , if supplied, otherwise it is created
    # @param origin - string from where to get data for initial record, 
    # to allow syncronised display of screens (only works if 'sb' is given)
    def init_database(self, globals, sb, origin):
        self.globals = globals
        self.create_menubar()
        self.create_modul_buttons()
        self.initialize_sizer()
        # set header
        self.SetTitle(globals.get_host_header())
        # shortcuts for convienence
        self.mysql = self.globals.get_mysql()
        self.debug = self.globals.is_debug()
        if self.readonly is None: 
            self.readonly = self.globals.get_value("readonly")
        #self.debug = True
        self.globals.set_value(None, None, self.typ)
        self.load_additional_globals()
        setting = self.globals.get_setting(self.typ)
        if not self.debug and not setting is None: 
            if setting.exists_key("debug"):
                self.debug = setting.get("debug")
        # add 'Einsatz' moduls if desired
        if hasattr(self,'einsatz'):
            self.einsatz = Afp_importAfpModul("Einsatz", globals)
        else:
            self.einsatz = None
        if self.debug: print("AfpScreen.init_database Einsatz:", self.einsatz)
        # generate Superbase
        if sb:
            self.sb = sb
        else:
            self.sb = AfpSuperbase(self.globals, self.debug)
        dateien = self.get_dateinamen()
        for datei in dateien:
            self.sb.open_datei(datei)
        self.set_initial_record(origin)
        #self.set_current_record() # if needed, to be integrated into set_initial_record
        self.Populate()
        self.set_initial_gridrow()
        # Keyboard Binding
        self.no_keydown = self.get_no_keydown()
        self.Bind(wx.EVT_KEY_DOWN, self.On_KeyDown)
        self.panel.Bind(wx.EVT_KEY_DOWN, self.On_KeyDown)
        children = self.panel.GetChildren()
        for child in children:
            if not child.GetName() in self.no_keydown:
                child.Bind(wx.EVT_KEY_DOWN, self.On_KeyDown)
        # set background and readonly flag for database, if necessary
        if self.readonly:
            self.SetBackgroundColour(self.readonlycolor)
            self.mysql.set_readonly()
        if self.globals.os_is_windows():
            if not self.readonly: self.SetBackgroundColour(self.windowsbackgroundcolor)
            #print "AfpScreen.init_database Windows Background set:", self.windowsbackgroundcolor
            for entry in self.grid_minrows:
                self.grid_minrows[entry] =  int(1.4 * self.grid_minrows[entry])
                
    ## set focus to panel
    def set_focus(self):
        self.panel.SetFocus()
    
    ## create menubar and add common items \n
    # menubar implementation has only be done to this point, specific Afp-modul menues are not yet implemented
    def create_menubar(self):
        self.menubar = wx.MenuBar()
        # setup screen menu
        tmp_menu = wx.Menu()
        modules = Afp_ModulNames(self.globals, True)
        if modules:
            for mod in modules:
                new_id = wx.NewId()
                self.menu_items[new_id] = wx.MenuItem(tmp_menu, new_id, mod, "", wx.ITEM_CHECK)
                tmp_menu.Append(self.menu_items[new_id])
                self.Bind(wx.EVT_MENU, self.On_Screenitem, self.menu_items[new_id])
                if self.menu_items[new_id].GetItemLabelText() == self.typ or self.menu_items[new_id].GetItemLabelText() == self.flavour: self.menu_items[new_id].Check(True)
        new_id = wx.NewId()
        self.menu_items[new_id] = wx.MenuItem(tmp_menu, new_id, "Beenden", "")
        tmp_menu.Append(self.menu_items[new_id])
        self.Bind(wx.EVT_MENU, self.On_Screenitem, self.menu_items[new_id])
        self.menubar.Append(tmp_menu, "Bildschirm")
        # setup modul specific menu parts
        self.create_specific_menu()
        # setup extra menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Archiv", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenArchiv, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Ausgangsrechnung", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenInvoice, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Eingangsrechnung", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenObligation, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Zusatzprogramme", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenZusatz, mmenu)
        tmp_menu.Append(mmenu)
        self.menubar.Append(tmp_menu, "Extra")
       # setup info menu
        tmp_menu = wx.Menu() 
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Version", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenVersion, mmenu)
        tmp_menu.Append(mmenu)
        mmenu =  wx.MenuItem(tmp_menu, wx.NewId(), "Info", "")
        self.Bind(wx.EVT_MENU, self.On_ScreenInfo, mmenu)
        tmp_menu.Append(mmenu)
        self.menubar.Append(tmp_menu, "?")
        self.SetMenuBar(self.menubar)
    ## setup typ specific menu \n
    # to be overwritten in devired class
    def create_specific_menu(self):
        return
   
    ## create buttons to switch modules 
    def create_modul_buttons(self):
        modules = Afp_ModulNames(self.globals, True)
        self.button_modules = {}
        if self.sizer: # use sizer
            if self.modul_button_sizer: 
                if modules:
                    for mod in modules:
                        self.button_modules[mod] = wx.Button(self, -1, label=mod, size=(75,30), name="B"+ mod)
                        self.Bind(wx.EVT_BUTTON, self.On_ScreenButton, self.button_modules[mod])
                        #print "AfpBaseScreen.create_modul_buttons:", mod, self.typ, self.flavour
                        if mod == self.typ or mod == self.flavour:
                            self.button_modules[mod].SetBackgroundColour(self.actuelbuttoncolor)
                        else:
                            self.button_modules[mod].SetBackgroundColour(self.buttoncolor)
                        self.modul_button_sizer.AddSpacer(10)
                        self.modul_button_sizer.Add(self.button_modules[mod] ,0,wx.EXPAND)
        else: # use direct postioning on the panel
            if modules:
                cnt = 0               
                for mod in modules:
                    self.button_modules[mod] = wx.Button(self.panel, -1, label=mod, pos=(35 + cnt*80,10), size=(75,30), name="B"+ mod)
                    self.Bind(wx.EVT_BUTTON, self.On_ScreenButton, self.button_modules[mod])
                    cnt += 1
                    #print "AfpBaseScreen.create_modul_buttons:", mod, self.typ, self.flavour
                    if mod == self.typ or mod == self.flavour:
                        self.button_modules[mod].SetBackgroundColour(self.actuelbuttoncolor)
                    else:
                        self.button_modules[mod].SetBackgroundColour(self.buttoncolor)
    ## fit sizer into screen
    def initialize_sizer(self):
        if self.sizer:
            #self.SetSizerAndFit(self.sizer)
            self.SetSizer(self.sizer)
            #self.SetAutoLayout(1)
            self.sizer.Fit(self)
      
   ## dump database with available 'Extra'-program
    def dump_database(self):
        prog = self.globals.get_value("extradir") + self.globals.get_value("auto-dump-sql-tables")
        if Afp_existsFile(prog):
            Afp_startExtraProgram(prog, self.globals, None, self.debug)
        
   ## scroll all grids to first row
    # necessary to avoid slow scrollback when changing grid input
    def grid_scrollback(self):
        for typ in self.gridmap:
            grid = self.FindWindowByName(typ)
            grid.Scroll(0,0)
    ## resize grid rows - only needed, if grid should be exactly filled up with rows
    # @param name - name of grid
    # @param grid - grid to be resized
    # @param new_lgh - new number of rows to be populated
    def grid_resize(self, name, grid, new_lgh):
        grid = self.FindWindowByName(name)
        #print ("AfpScreen.grid_resize:", name, grid)
        if new_lgh < self.grid_minrows[name]:
            new_lgh =  self.grid_minrows[name]
        old_lgh = grid.GetNumberRows()
        #print ("AfpScreen.grid_resize:", name, old_lgh, new_lgh, self.grid_cols)
        if new_lgh > old_lgh:
            grid.AppendRows(new_lgh - old_lgh)
            for row in range(old_lgh, new_lgh):
                for col in range(self.grid_cols[name]):
                    grid.SetReadOnly(row, col)
        elif  new_lgh < old_lgh:
            for i in range(old_lgh-1, new_lgh-1, -1):
                grid.DeleteRows(i)
        self.grid_rows[name] = new_lgh
    ## retun percentr values of grid col width
    # @param grid - grid object, where col percents should be extracted from
    # @param cols - number of columns in grid
    def get_grid_col_percents(self, grid, cols):
        if self.dynamic_grid_col_percents:
            percents = self.dynamic_grid_col_percents
        else:
            percents = []
            width = 0
            array = []
            for col in range(cols):
                array.append(grid.GetColSize(col))
                width += array[-1]
            for col in range(cols):
                percents.append(int(100.0*array[col]/width + 0.5))
            #print "AfpScreen.get_grid_col_percents:", percents
        return percents
        
    ## adjust grid row to new size of  screen
    # @param name - identifier of grid to be used
    def adjust_grid_rows(self, name):
        grid = self.FindWindowByName(name)
        width, height = grid.GetSize()
        if width and height:
            row_height = grid.GetRowSize(0)
            new_rows = int(height/row_height) - 1
            #print "AfpScreen.adjust_grid_rows:", self.grid_rows[name] , new_rows
            if new_rows > self.grid_rows[name] :
                self.grid_resize(name, grid, new_rows)
                self.grid_rows[name] = new_rows  
            percents = self.get_grid_col_percents(grid, self.grid_cols[name])
            if self.dynamic_grid_col_labels or percents:
                for col in range(self.grid_cols[name]):  
                    if self.dynamic_grid_col_labels:
                        grid.SetColLabelValue(col, self.dynamic_grid_col_labels[col])
                    if percents and col < len(percents):
                        grid.SetColSize(col, int(percents[col]*width/100))
    ## change color of a grid column or reset marked color
    # @param name - name of grid
    # @param index - if given, index of column to be marked
    def mark_grid_column(self, name, index=None):
        #print  "AfpScreen.mark_grid_column attr:", name, index, self.grid_sort_col
        grid = self.FindWindowByName(name)
        if name in self.grid_sort_col:
            for row in range(grid.GetNumberRows()):            
                attr =  wx.grid.GridCellAttr()
                attr.SetBackgroundColour(self.actuelbuttoncolor)
                #print "AfpScreen.mark_grid_column normal attr:", attr, attr.GetFont()
                grid.SetAttr(row, self.grid_sort_col[name], attr)
            if not index: self.grid_sort_col.pop(name)
        if index:
            for row in range(grid.GetNumberRows()):
                attr =  wx.grid.GridCellAttr()
                attr.SetBackgroundColour(self.buttoncolor)
                #print "AfpScreen.mark_grid_column attr:", attr, attr.GetFont()
                grid.SetAttr(row, index, attr)
            self.grid_sort_col[name] = index

    ## sort grid rows due to one column
    # @param name - name of grid
    # @param index - index of column to trigger sort
    # @param desc - if given , flag if order should be descending
    def sort_grid_rows(self, name, index, desc=None):
        rows = self.grid_sort_rows[name]
        col = Afp_extractColumns(index, rows)
        for i in range(len(col)):
            col[i] = Afp_fromString(col[i]) 
        col, rows = Afp_sortSimultan(col, rows)
        if desc: rows.reverse()
        self.grid_sort_rows[name]= rows
        self.Pop_grid(name)

    ## Eventhandler Menu - show version information
    def On_ScreenVersion(self, event):
        if self.debug: print("AfpScreen Event handler `On_ScreenVersion'!")
        AfpReq_Version(self.globals)
    ## Eventhandler Menu - show info dialog box
    def On_ScreenInfo(self, event):
        if self.debug: print("AfpScreen Event handler `On_ScreenInfo'!")
        AfpReq_Information(self.globals)
   ## Eventhandler Menu - add or delete files in archiv
    def On_ScreenArchiv(self, event):
        if self.debug: print("AfpScreen Event handler `On_ScreenArchiv'!")
        data = self.get_data()
        ok = AfpLoad_editArchiv(data,  "Archiv von " + data.get_name() , data.get_identification_string())
        if ok: self.Reload()
   ## Eventhandler Menu - handle outgoing common invoices
    def On_ScreenInvoice(self, event):
        if self.debug: print("AfpScreen Event handler `On_ScreenInvoicecc'!")
        ok = Afp_handleCommonInvoice(self.globals)
        if ok: self.Reload()
   ## Eventhandler Menu - handle incoming obligations
    def On_ScreenObligation(self, event):
        if self.debug: print("AfpScreen Event handler `On_ScreenObligation'!")
        ok = Afp_handleObligation(self.globals)
        if ok: self.Reload()
    ## Eventhandler Menu - select and start additional programs
    # @param data - optional input of data for indirect use
    def On_ScreenZusatz(self, event, data = None):
        if self.debug: print("AfpScreen Event handler `On_ScreenZusatz'!")
        typ = self.typ
        if self.flavour: typ = self.flavour
        if not data: data = self.data
        fname, ok = AfpReq_extraProgram(self.globals.get_value("extradir"), typ)
        if ok and fname:
            Afp_startExtraProgram(fname, self.globals, data, self.debug)
      
    ## Eventhandler Menu - switch between screen
    def On_Screenitem(self, event):
        if self.debug: print("AfpScreen Event handler `On_Screenitem'!")
        id = event.GetId()
        item = self.menu_items[id]
        text = item.GetItemLabelText() 
        if text == self.typ:
            item.Check(True)
        elif text == "Beenden":
            self.On_Ende(event)
        else:
            self.SwitchModulScreen(text)
        #event.Skip() #invokes eventhandler twice on windows
    ## Enventhandler BUTTON - switch modules
    def On_ScreenButton(self,event):
        if self.debug: print("AfpScreen Event handler `On_ScreenButton'!")
        object = event.GetEventObject()
        name = object.GetName()
        text = name[1:]
        if not text == self.typ:
            self.SwitchModulScreen(text)
        #event.Skip() #invokes eventhandler twice on windows
    ## switch to other modul screen
    # @param modul - name of modul to switch to
    def SwitchModulScreen(self, modul):
        pos = self.GetPosition().Get()
        Afp_loadScreen(self.globals, modul, self.sb, self.typ, pos)
        self.Close()
      
    ## Eventhandler BUTTON - quit
    def On_Ende(self,event):
        if self.debug: print("AfpScreen Event handler `On_Ende'!")
        if self.globals.get_value("auto-dump-sql-tables"): self.dump_database()
        self.Close()
        event.Skip()

    ## Eventhandler Keyboard - handle key-down events
    def On_KeyDown(self, event):
        keycode = event.GetKeyCode()        
        if self.debug: print("AfpScreen Event handler `On_KeyDown'", keycode)
        #print "AfpScreen Event handler `On_KeyDown'", keycode
        next = 0
        if keycode == wx.WXK_LEFT: next = -1
        if keycode == wx.WXK_RIGHT: next = 1
        if next: self.grid_scrollback()
        self.CurrentData(next)
        #event.Skip()) #invokes eventhandler twice on windows
    
    ## handle grid sort event (pressed on column header)
    def On_GridSort(self, event):
        if not self.grid_sort_rows is None:
            index = event.GetCol()
            name = event.GetEventObject().GetName()
            desc = None
            if name in self.grid_sort_col and index == self.grid_sort_col[name]:
                if name in self.grid_sort_desc: desc = not self.grid_sort_desc[name]
            self.mark_grid_column(name, index)
            self.grid_sort_desc[name] = desc
            self.sort_grid_rows(name, index, desc)

    ## Eventhandler resize event
    def On_ReSize(self, event):
        if self.dynamic_grid_name:
            self.adjust_grid_rows(self.dynamic_grid_name)
            self.Pop_grid(True)
        event.Skip()   
     
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
                value = self.data.get_tagged_value(self.labelmap[entry])
            else:
                value = self.sb.get_string_value(self.labelmap[entry])
            #print ("AfpScreen.Pop_label:", entry,"=", value)
            Label.SetLabel(value)
    ## populate text widgets
    def Pop_text(self):
        for entry in self.textmap:
            TextBox = self.FindWindowByName(entry)
            if self.data:
                value = self.data.get_tagged_value(self.textmap[entry])
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
                    print("WARNING in AfpScreen: External file", filename, "does not exist!")
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
                if not self.grid_sort_rows is None and typ == name and typ in self.grid_sort_rows:
                    rows = self.grid_sort_rows[typ]
                else:
                    #self.mark_grid_column(typ)                    
                    rows = self.get_grid_rows(typ)
                    if not self.grid_sort_rows is None and rows and typ in self.grid_sort_col:
                        self.grid_sort_rows[typ] = rows
                        self.sort_grid_rows(typ, self.grid_sort_col[typ], self.grid_sort_desc[typ])
                        rows = self.grid_sort_rows[typ]
                row_lgh = len(rows)
                grid = self.FindWindowByName(typ)
                self.grid_resize(typ, grid, row_lgh)
                self.grid_id[typ] = []
                max_col_lgh = grid.GetNumberCols()
                if rows: act_col_lgh = len(rows[0]) - 1
                for row in range(0,row_lgh):
                    for col in range(0,max_col_lgh):
                        if col >= act_col_lgh:
                            if self.font: grid.SetCellFont(row, col, self.font)
                            grid.SetCellValue(row, col, "")
                        else:
                            if self.font: grid.SetCellFont(row, col, self.font)
                            grid.SetCellValue(row, col, rows[row][col])
                    self.grid_id[typ].append(rows[row][act_col_lgh])
                if row_lgh < self.grid_minrows[typ]:
                    for row in range(row_lgh, self.grid_minrows[typ]):
                        for col in range(0,max_col_lgh):
                            if self.font: grid.SetCellFont(row, col, self.font)
                            grid.SetCellValue(row, col,"")
                if not self.grid_sort_rows is None: 
                    self.grid_sort_rows[typ]= rows
    ## population routine for special treatment - to be overwritten in derived class
    def Pop_special(self):
        return
 
    ## reload current data to screen
    def Reload(self):
        self.sb.select_current()
        self.CurrentData()
         
    ## set current screen data
    # @param plus - indicator to step forwards, backwards or stay
    def CurrentData(self, plus = 0):
        if self.debug: print("AfpScreen.CurrentData:", plus)
        #self.sb.set_debug()
        if plus == 1:
            self.sb.select_next()
        elif plus == -1:
            self.sb.select_previous()
        self.no_data_shown = self.sb.eof() 
        #print ("AfpScreen.CurrentData:", plus, self.sb.eof())
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
    # default - empty, to be overwritten if changes have to be diffused to other then the main database table
    def set_current_record(self): 
        return   
    ## set initial record to be shown, when screen opens the first time
    # default - empty, should be overwritten to assure consistant data on frist screen when the program is called
    # may be used to initialise the empty database, when the program is called the first time
    # @param origin - string where to find initial data
    def set_initial_record(self, origin = None):
        return
    ## set initial gridrow to be selected, when screen opens the first time
    # needed to assure cross-screen selection (origin in set_initial_record)
    # default - empty, should be overwritten to assure consistant data on frist screen when the program is called
    def set_initial_gridrow(self):
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
# End of class AfpScreen

## loader roution for Screens
# @param globals - global variables, holding mysql access
# @param modulname - name of modul this screen belongs to, the appropriate modulfile will be imported
# @param sb - AfpSuperbase object which holds the current settings on the mysql tables
# @param origin - value which identifies mysql tableentry to be displayed
# the parameter 'sb' and 'origin' may only be used alternatively
# @param pos - position tuple where screen should be placed
def Afp_loadScreen(globals, modulname, sb = None, origin = None, pos = None):
    Modul = None
    if Afp_inModuls(modulname, globals):
        name, flavour = Afp_getModulFlavour(modulname)
        #print("Afp_loadScreen name:", modulname, name, flavour)
        screen = "Afp" + Afp_getModulShortName(name) + "Screen" 
        if flavour: flavour = "_" + flavour
        modname = "Afp" + name + "." + screen + flavour
        #print("Afp_loadScreen modname:", modname)
        pyModul =  Afp_importPyModul(modname, globals)
        pyBefehl = "Modul = pyModul." + screen + flavour + "()"
        local = locals()
        #print("Afp_loadScreen exec:", pyBefehl, local)
        exec(pyBefehl, {}, local)
        Modul = local["Modul"]
        #print("Afp_loadScreen Modul:", Modul, local)
    if Modul:
        if pos:
            Modul.SetPosition(pos)
        Modul.init_database(globals, sb, origin)
        Modul.set_focus()
        Modul.Show()
        return Modul
    else:
        return None
        
## Class of screen with interactive edit possibillity \n \n
# - the grid to be edited has to be assigned to the property 'self.grid_editable'
# - for this grid the event 'EVT_GRID_CMD_CELL_LEFT_CLICK' has to be connected to the method 'self.On_LClick_EditGrid'
#   self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick_EditGrid, self.grid_editable)
# - for this grid the event 'EVT_GRID_CMD_CELL_LEFT_DCLICK' has to be connected to the method 'self.On_DClick_EditGrid'
#   self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_CLICK, self.On_LClick_EditGrid, self.grid_editable)
# - a button to switch to editable modus may be assigned to 'self.button_Edit', the event has to be assigned to the method 'self.On_Edit'
#   self.Bind(wx.EVT_BUTTON, self.On_Edit, self.button_Edit)
# - 'self.editable_rows' has to be set tu number of grid rows in self.get_grid_rows in devired class
class AfpEditScreen(AfpScreen):
    ## initialize AfpEditScreen
    def __init__(self):
        AfpScreen.__init__(self,None, -1, "")
        self.editable = False
        self.readonlycolor = None
        self.editcolor = (255,255,255)
        self.editcellcolor = (192, 192, 192)
        # set if keyboard entries should be deviated to the plugin
        # the plugin must supply the method 'catch_keydown(keycode)'
        self.catch_keydown = None
        # postprocess keydown function, when enter key is not catched
        self.postprocess_keydown = None
        # editable grid has to be assigned here
        # the events EVT_GRID_CMD_CELL_LEFT_CLICK and EVT_GRID_CMD_CELL_LEFT_DCLICK have to be assigened properly
        self.grid_editable = None  
        # button to switch to edit modus has to be assigned here
        # the event EVT_BUTTON has to be assigned to self.On_Edit
        self.button_Edit = None
        # to get full functionallity self.editable_rows has to be set to number of grid rows in self.get_grid_rows
        self.editable_rows = None
        self.editable_cols = None
        # index of row actually selected
        self.selected_row = None
        # data to be proceeded
        self.data = None
        
        # use_RETURN may be set in devired screen during activation
        self.use_RETURN = None
        # automated_row_selection may be set to invoke edit_data automatically when last rowis selected
        self.automated_row_selection = None

    ## connect to database and populate widgets
    # overwritten from AfpScreen
    # @param globals - global variables, including database connection
    # @param sb - AfpSuperbase database object , if supplied, otherwise it is created
    # @param origin - string from where to get data for initial record, 
    # to allow syncronised display of screens (only works if 'sb' is given)
    def init_database(self, globals, sb, origin):
        AfpScreen.init_database(self, globals, sb, origin)
        self.readonlycolor = self.GetBackgroundColour()
        
    ## set or unset editable mode
    # @param ed_flag - flag to turn editing on or off
    # @param lock_data - flag if invoking of editable mode needs a lock on the database
    def Set_Editable(self, ed_flag, lock_data = None):
        self.editable = ed_flag
        if ed_flag:
            self.panel.SetBackgroundColour(self.editcolor)
            if self.grid_editable:
                if self.editable_cols is None:
                    self.editable_cols = self.grid_editable.GetNumberCols()
                if self.editable_rows is None:
                    self.editable_rows = self.grid_editable.GetNumberRows()
            if self.button_Edit:
                self.button_Edit.SetLabel("&Speichern")
        else:
            self.panel.SetBackgroundColour(self.readonlycolor)
            if self.button_Edit:
                self.button_Edit.SetLabel("&Bearbeiten")
        self.panel.Refresh()
        if lock_data and self.data:
            if ed_flag:
                self.data.lock_data()
            else: 
                self.data.unlock_data()
   ## central routine which returns if screen is in editable mode
    def is_editable(self):
        return self.editable
    ## leave editable modus of screen
    # @param store - flag if data should be stored during leaving the modus, default: True
    def leave_editmodus(self, store=True):
        if  self.is_editable() :
            if self.debug: print("AfpEditScreen.leave_editmodus ReadOnly:", self.is_editable(), store)
            checked = None
            if store:
                checked = self.check_data()
                if checked:
                    self.store_data()            
            if checked is None:
                self.data.unlock_data()
                self.data = None
            self.CurrentData()
            self.select_row(-1)
            self.Set_Editable(False)
            self.panel.Refresh()
    ## enter editable modus of screen
    def invoke_editmodus(self):
        if self.data.is_editable() and not self.is_editable():
            self.Set_Editable(True)
            if self.editable_rows:
                self.select_row(self.editable_rows)
            self.panel.Refresh()
            if self.debug: print("AfpEditScreen.invoke_editmodus Edit:", self.is_editable())
            self.data.lock_data()
            self.edit_data()
    ## resize grid rows - overwritten from AfpScreen
    # @param name - name of grid
    # @param grid - the grid object
    # @param new_lgh - new number of rows to be populated
    def grid_resize(self, name, grid, new_lgh):
        if self.is_editable() and new_lgh >= self.grid_minrows[name]:
            new_lgh += 1
        super().grid_resize(name, grid, new_lgh)
    ## mark indicates row of content grid as selected
    # @param row - index of gridrow to be marked \n
    # - if row < 0: only marked row will be unmarked
    def select_row(self, row):
        #print "AfpEditScreen.select_row invoked", row
        if self.grid_editable and row <= self.editable_rows:
            if not self.selected_row is None and self.selected_row != row :
                attrRO = wx.grid.GridCellAttr()
                for col in range(0,self.editable_cols):
                    #print "AfpEditScreen.On_LClick_Content RO:", self.selected_row, col, attrRO
                    self.grid_editable.SetAttr(self.selected_row, col, attrRO)
            if row > -1:
                attrSel = wx.grid.GridCellAttr()
                attrSel.SetBackgroundColour(self.editcellcolor)
                for col in range(0,self.editable_cols):
                    #print "AfpEditScreen.On_LClick_Content Select:", row, col, attrSel
                    self.grid_editable.SetAttr(row, col, attrSel)
                self.selected_row = row
            else:
                self.selected_row = None
            self.panel.Refresh()
 
    ## Eventhandler Keyboard - handle key-down events
    def On_KeyDown(self, event):
        keycode = event.GetKeyCode()        
        if self.debug: print("AfpEditScreen Event handler `On_KeyDown'", keycode)
        #print "AfpEditScreen Event handler `On_KeyDown'", keycode
        caught = 0
        if keycode == wx.WXK_LEFT: caught = -1
        if keycode == wx.WXK_RIGHT: caught = 1
        if self.editable: caught = 0
        if caught: 
            self.CurrentData(caught)
        else: 
            if self.catch_keydown:
                caught = self.catch_keydown.catch_keydown(event)
                if self.postprocess_keydown and not caught and (keycode == wx.WXK_RETURN or  keycode == wx.WXK_ESCAPE):
                    if self.debug: print("AfpEditScreen postprocess keydown, remove catcher")
                    if keycode == wx.WXK_RETURN:
                        self.postprocess_keydown()
                    else:
                        self.Pop_grid()
                        self.select_row(self.selected_row)
                    self.catch_keydown = None
                    self.postprocess_keydown = None
                    caught = True
                    # invoke next selection, if last line is selected
                    if self.automated_row_selection and self.selected_row  == self.data.get_content_length():
                        if self.debug: print("AfpEditScreen postprocess keydown: 'edit_data' invoked") 
                        self.edit_data()
            else:
                caught = self.editable_keydown(keycode)
            if not caught: event.Skip()
    ## invoke special keydown handling, additional to scrolling forward and backward \n
    # @param keycode - code of pushed key
    def editable_keydown(self, keycode):
        caught = False
        if keycode == wx.WXK_SPACE:
            if self.is_editable():
                if not self.selected_row is None:
                    if self.debug: print("AfpEditScreen.editable_keydown deselect row")
                    self.select_row(-1)
                else:
                    #self.data.lock_data()
                    if self.debug: print("AfpEditScreen.editable_keydown lock edit")
                    self.edit_data()
            else:
                if self.debug: print("AfpEditScreen.editable_keydown invoke editmodus")
                self.invoke_editmodus()
            caught = True
        elif keycode == wx.WXK_ESCAPE:
            if self.is_editable():
                if self.debug: print("AfpEditScreen.editable_keydown unlock editmodus")
                self.leave_editmodus(False)
            caught = True
        elif keycode == wx.WXK_RETURN:
            if self.is_editable() and not self.selected_row is None:
                if self.debug: print("AfpEditScreen.editable_keydown edit row:", self.selected_row)
                self.edit_data(self.selected_row)
            elif self.use_RETURN:
                if self.is_editable():
                    if self.debug: print("AfpEditScreen.editable_keydown leave editmodus")
                    self.leave_editmodus()
                else:
                    if self.debug: print("AfpEditScreen.editable_keydown invoke editmodus")
                    self.invoke_editmodus()
            caught = True
        elif keycode == wx.WXK_DELETE:
            if self.debug: print("AfpEditScreen.editable_keydown DELETE")
            self.delete_row(self.selected_row)
            self.select_row(self.selected_row)
        elif keycode == wx.WXK_INSERT:
            if self.debug: print("AfpEditScreen.editable_keydown INSERT")
            self.insert_row(self.selected_row)
            self.select_row(self.selected_row)
        elif self.is_editable():
            if keycode == wx.WXK_DOWN: 
                if not self.selected_row is None and self.selected_row < self.editable_rows: 
                    if self.debug: print("AfpEditScreen.editable_keydown rows:", self.selected_row +1, self.editable_rows)
                    self.select_row(self.selected_row + 1)
                caught = True
            elif keycode == wx.WXK_UP: 
                if self.selected_row: 
                    if self.debug: print("AfpEditScreen.editable_keydown rows:", self.selected_row - 1, self.editable_rows)
                    self.select_row(self.selected_row - 1)
                caught = True
        if self.debug: print("AfpEditScreen.editable_keydown:", keycode, caught)
        return caught
             
    ## Eventhandler Grid - left click editable grid \n
    # has to be attached to editable grid in devired class
    def On_LClick_EditGrid(self, event):
        if self.is_editable():
            row = event.GetRow()
            if self.debug: print("AfpEditScreen Event handler `On_LClick_EditGrid' invoked", row)
            self.select_row(row)
        else:
            if self.debug: print("AfpEditScreen Event handler `On_LClick_EditGrid'")
    ## Eventhandler Grid - double click editable grid \n
    # has to be attached to editable grid in devired class
    def On_DClick_EditGrid(self, event):
        if self.is_editable():
            if self.debug: print("AfpEditScreen Event handler `On_LClick_EditGrid' invoked")
            row = event.GetRow()
            if row <= self.editable_rows:
                self.edit_data(row)
        else:
            if self.debug: print("AfpEditScreen Event handler `On_LClick_EditGrid'")
            
    ## Eventhandler BUTTON - swap editable modus \n
    # has to be attached to button_Edit if button is present
    # - lock data if editable modus is started
    # - store data if editable modus is ended
    def On_Edit(self,event):
        if self.editable:
            self.leave_editmodus()
        else:
            self.invoke_editmodus()
        event.Skip()
  
    # routines that may be overwritten in devired class
    # 
   ## check if data should or has to be stored \n
   # three return values are possible:
   # - None: no data to be saved
   # - False: user selects not to save data
   # - True: data has to be saved
    def check_data(self):
        #print "AfpEditScreen.check_data invoked" 
        Ok = AfpReq_Question("Sollen die Daten so gespeichert werden?", "", "Daten speichern?")
        return Ok
    ## store data
    def store_data(self):
        #print "AfpEditScreen.store_data invoked" 
        self.data.store()    
    # routines to be overwritten in devired class
    #
    ## edit data
    # @param rowNr - row index to be edited
    # to be overwritten in devired class
    def edit_data(self, rowNr = None):
        return
    ## insert row
    # @param rowNr - row index to be edited
    # to be overwritten in devired class
    def insert_row(self, rowNr = None):
        return
    ## delete row
    # @param rowNr - row index to be edited
    # to be overwritten in devired class
    def delete_row(self, rowNr = None):
        return
             
# end of class AfpEditScreen

