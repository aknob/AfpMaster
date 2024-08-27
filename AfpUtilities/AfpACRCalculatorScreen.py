#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AfpACRCalculatorScreen provides the graphic interface for calculation 
# and simulation for the ACR process of the Dassult Systèmes Deutschland GmbH
# it holds the classes:
#   AfpACRScreen
#
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de 
#        02 Mar. 2020 - add fixed budget surcharge - Andreas.Knoblauch@afptech.de
#        29 May 2018 - add result processing - Andreas.Knoblauch@afptech.de
#        07 Feb. 2018 - inital code generated - Andreas.Knoblauch@afptech.de
#
#
# This file is an extract of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2022 afptech.de (Andreas Knoblauch)
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

import sys
import wx
import wx.grid as gridlib

import AfpACRCalculator
from AfpACRCalculator import *
import AfpBase
from AfpBase.AfpBaseScreen import AfpScreen
from AfpBase.AfpBaseDialog import AfpReq_FileName, AfpReq_MultiLine
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_extractPath, Afp_getArrayfromDict, Afp_extractColumns, Afp_sortSimultan 
from AfpBase.AfpUtilities.AfpStringUtilities import Afp_fromString, Afp_toString, Afp_toFloatString

## Class AfpACRScreen shows Window and handles interactions
class AfpACRScreen(AfpScreen):
    ## initialize AfpACRScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        AfpScreen.__init__(self,None, -1, "")
        self.typ = "ACR"
        self.dynamic_rows = False
        # self properties
        self.SetTitle("AFP ACR-Calculator")
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.Colour(222, 222, 222))
        self.SetForegroundColour(wx.Colour(20, 19, 18))
        self.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "DejaVu Sans"))

        # values from call
        self.debug = debug
        self.sizer = None
        self.confname = None
        self.config = None
        self.ranges = None
        self.people = None
        self.calculator = None
        # inital values      
        self.rows = 7
        #self.rows = int(1.5*self.rows)
        self.new_rows = self.rows
        self.fixed_width = 30
        self.fixed_height = 210
        self.grid_width = None
        self.grid_data = None
        #self.grid_sort_background = wx.Colour(222, 222, 222)
        self.grid_sort_col = None
        self.grid_sort_desc = None
        # for internal use
        self.used_modul = None
        self.col_percents =  [20 ,15, 10, 5, 5, 5, 5, 5, 5, 10, 15]
        self.col_labels = ["Name","Family","OTE","FTE","CLG", "DAIT","-=+", "MyC", "Boost", "%", "Increase"]
        self.cols = len(self.col_labels)
        #self.matrix_types = ["ACR - Result", "Referenzvalues","Focalvalues","PROMO - Focalvalues","Spread","PROMO","Managerrange", "OTE - Distribution","Persons - Count","Persons - Percent","OTE - Average", "ACR - Distribution", "ACR - Average","ACR - Given"]
        self.matrix_types = ["ACR - Result", "Referenzvalues","Focalvalues","Spread", "Managerrange", "OTE - Distribution","Persons - Count","Persons - Percent","OTE - Average", "ACR - Distribution", "ACR - Average","ACR - Given"]
        self.matrix_typ = None
        self.matrix_rows = 5
        self.matrix_cols = 5
        self.matrix_row_labels = None
        self.matrix_col_labels = None
        self.dateien = ""
        self.textmap = []
        self.sortname = ""
        self.valuecol = -1 
        self.link = None  
        self.ident = [None]
        self.offset = 0
        # for the result
        self.result_index = -1
        self.result = None
        self.grid_width = self.GetSize()[0] - self.fixed_width

        self.InitWx()
        self.SetSize((1000,500))
        height = self.GetSize()[1] - self.fixed_height
        self.row_height = height/self.rows 
        if self.debug: print("AfpACRScreen.init New:", self.GetSize(), height, self.grid_width, self.row_height, self.rows, self.new_rows)
        self.Bind(wx.EVT_SIZE, self.On_ReSize)

    ## set up dialog widgets      
    def InitWx(self):
        self.label_config= wx.StaticText(self, 1, label="", name="LConfigFile")
        self.upper_left_lineF1_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.upper_left_lineF1_sizer.AddStretchSpacer(1)
        self.upper_left_lineF1_sizer.Add(self.label_config,0,wx.EXPAND)
        self.upper_left_lineF1_sizer.AddStretchSpacer(1)
        self.label_data= wx.StaticText(self, 1, label="", name="LDataFile")
        self.upper_left_lineF2_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.upper_left_lineF2_sizer.AddStretchSpacer(1)
        self.upper_left_lineF2_sizer.Add(self.label_data,0,wx.EXPAND)
        self.upper_left_lineF2_sizer.AddStretchSpacer(1)
        self.label_ranges= wx.StaticText(self, 1, label="", name="LRangesFile")
        self.upper_left_lineF3_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.upper_left_lineF3_sizer.AddStretchSpacer(1)
        self.upper_left_lineF3_sizer.Add(self.label_ranges,0,wx.EXPAND)
        self.upper_left_lineF3_sizer.AddStretchSpacer(1)

        self.label_BudPer= wx.StaticText(self, 1, label="Budget in %:", size = (100,18), name="LBudPer")
        self.text_Budget = wx.TextCtrl(self, -1, value="", style=wx.TE_PROCESS_ENTER, name="Budget")
        self.Bind(wx.EVT_TEXT_ENTER, self.On_Budget, self.text_Budget)
        self.label_LOteSum= wx.StaticText(self, 1, label="OTE Sum:", size = (70,18), name="LOteSum")
        self.label_OteSum= wx.StaticText(self, 1, name="OteSum")
        self.label_LBudget= wx.StaticText(self, 1, label="Budget:", size = (70,18), name="LBudget")
        self.label_Budget= wx.StaticText(self, 1, name="Budget")
        self.upper_left_line1_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.upper_left_line1_sizer.AddStretchSpacer(1)
        self.upper_left_line1_sizer.Add(self.label_BudPer,0,wx.EXPAND) 
        self.upper_left_line1_sizer.Add(self.text_Budget,10,wx.EXPAND) 
        self.upper_left_line1_sizer.AddStretchSpacer(1)
        self.upper_left_line1_sizer.Add(self.label_LOteSum,0,wx.EXPAND) 
        self.upper_left_line1_sizer.Add(self.label_OteSum,10,wx.EXPAND) 
        self.upper_left_line1_sizer.AddStretchSpacer(1)
        self.upper_left_line1_sizer.Add(self.label_LBudget,0,wx.EXPAND) 
        self.upper_left_line1_sizer.Add(self.label_Budget,10,wx.EXPAND) 
        self.upper_left_line1_sizer.AddStretchSpacer(1)
        
        self.label_RefPer= wx.StaticText(self, 1, label="Reference in %:", size = (100,18), name="LRefPer")
        self.text_Ref = wx.TextCtrl(self, -1, value="", style=wx.TE_PROCESS_ENTER, name="Reference")
        self.Bind(wx.EVT_TEXT_ENTER, self.On_Ref, self.text_Ref)
        self.label_label1_line2= wx.StaticText(self, 1, label="ELIGIBLE:", size = (70,18), name="l1l2")
        self.label_text1_line2= wx.StaticText(self, 1, name="t1l2")
        self.label_label2_line2= wx.StaticText(self, 1, label="Increase:", size = (70,18), name="l2l2")
        self.label_text2_line2= wx.StaticText(self, 1, name="t2l2")
        self.upper_left_line2_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.upper_left_line2_sizer.AddStretchSpacer(1)
        self.upper_left_line2_sizer.Add(self.label_RefPer,0,wx.EXPAND) 
        self.upper_left_line2_sizer.Add(self.text_Ref,10,wx.EXPAND) 
        self.upper_left_line2_sizer.AddStretchSpacer(1)
        self.upper_left_line2_sizer.Add(self.label_label1_line2,0,wx.EXPAND) 
        self.upper_left_line2_sizer.Add(self.label_text1_line2,10,wx.EXPAND) 
        self.upper_left_line2_sizer.AddStretchSpacer(1)
        self.upper_left_line2_sizer.Add(self.label_label2_line2,0,wx.EXPAND) 
        self.upper_left_line2_sizer.Add(self.label_text2_line2,10,wx.EXPAND) 
        self.upper_left_line2_sizer.AddStretchSpacer(1)
       
        self.label_FocPer= wx.StaticText(self, 1, label="Focal in %:", size = (100,18), name="LFocPer")
        self.text_Focal = wx.TextCtrl(self, -1, value="", style=wx.TE_PROCESS_ENTER, name="Focal")
        self.Bind(wx.EVT_TEXT_ENTER, self.On_Focal, self.text_Focal)
        self.label_label1_line3= wx.StaticText(self, 1, label="ACR Inc:", size = (70,18), name="l1l3")
        self.label_text1_line3= wx.StaticText(self, 1, name="t1l3")
        self.label_label2_line3= wx.StaticText(self, 1, label="Diff:", size = (70,18), name="l2l3")
        self.label_text2_line3= wx.StaticText(self, 1, name="t2l3")
        self.upper_left_line3_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.upper_left_line3_sizer.AddStretchSpacer(1)
        self.upper_left_line3_sizer.Add(self.label_FocPer,0,wx.EXPAND) 
        self.upper_left_line3_sizer.Add(self.text_Focal,10,wx.EXPAND) 
        self.upper_left_line3_sizer.AddStretchSpacer(1)
        self.upper_left_line3_sizer.Add(self.label_label1_line3,0,wx.EXPAND) 
        self.upper_left_line3_sizer.Add(self.label_text1_line3,10,wx.EXPAND) 
        self.upper_left_line3_sizer.AddStretchSpacer(1)
        self.upper_left_line3_sizer.Add(self.label_label2_line3,0,wx.EXPAND) 
        self.upper_left_line3_sizer.Add(self.label_text2_line3,10,wx.EXPAND) 
        self.upper_left_line3_sizer.AddStretchSpacer(1)

        self.upper_left_sizer =wx.BoxSizer(wx.VERTICAL)
        self.upper_left_sizer.AddStretchSpacer(1)
        self.upper_left_sizer.Add(self.upper_left_lineF1_sizer,0,wx.EXPAND) 
        self.upper_left_sizer.Add(self.upper_left_lineF2_sizer,0,wx.EXPAND) 
        self.upper_left_sizer.Add(self.upper_left_lineF3_sizer,0,wx.EXPAND) 
        self.upper_left_sizer.AddStretchSpacer(1)
        self.upper_left_sizer.Add(self.upper_left_line1_sizer,0,wx.EXPAND) 
        self.upper_left_sizer.Add(self.upper_left_line2_sizer,0,wx.EXPAND) 
        self.upper_left_sizer.Add(self.upper_left_line3_sizer,0,wx.EXPAND) 
        self.upper_left_sizer.AddStretchSpacer(1)
       
        self.combo_matrix = wx.ComboBox(self, -1, choices=self.matrix_types, style=wx.CB_DROPDOWN, name="CMatrix")
        self.combo_matrix.SetSelection(0)
        self.Bind(wx.EVT_COMBOBOX, self.On_Combo, self.combo_matrix)
        self.matrix_grid = wx.grid.Grid(self, -1, style=wx.FULL_REPAINT_ON_RESIZE, name="Matrix")
        self.matrix_grid.CreateGrid(self.matrix_rows, self.matrix_cols)
        self.matrix_grid.SetRowLabelSize(140)
        self.matrix_grid.SetColLabelSize(18)
        self.matrix_grid.EnableEditing(0)
        self.matrix_grid.EnableDragColSize(0)
        self.matrix_grid.EnableDragRowSize(0)
        self.matrix_grid.EnableDragGridSize(0)
        self.matrix_grid.SetSelectionMode(wx.grid.Grid.GridSelectRows)   
        self.matrix_grid.SetSize((200, 200))   
        for row in range(self.matrix_rows):
            for col in range(self.matrix_cols):
                self.matrix_grid.SetReadOnly(row, col)
        mbox = wx.StaticBox(self, size=(300, 300), label="Matrices")
        self.upper_right_sizer = wx.StaticBoxSizer(mbox, wx.VERTICAL)      
        self.upper_right_sizer.AddStretchSpacer(1)
        self.upper_right_sizer.Add(self.combo_matrix,4,wx.EXPAND)   
        self.upper_right_sizer.AddStretchSpacer(1)
        self.upper_right_sizer.Add(self.matrix_grid,20,wx.EXPAND)   
        #self.upper_right_sizer.AddStretchSpacer(1)

        self.upper_sizer =wx.BoxSizer(wx.HORIZONTAL)
        self.upper_sizer.Add(self.upper_left_sizer,1,wx.EXPAND)   
        self.upper_sizer.Add(self.upper_right_sizer,0,wx.EXPAND)   
        
        self.grid_auswahl = wx.grid.Grid(self, -1, style=wx.FULL_REPAINT_ON_RESIZE, name="Auswahl")
        self.grid_auswahl.CreateGrid(self.rows, self.cols)
        self.grid_auswahl.SetRowLabelSize(0)
        self.grid_auswahl.SetColLabelSize(18)
        self.grid_auswahl.EnableEditing(0)
        #self.grid_auswahl.EnableDragColSize(0)
        self.grid_auswahl.EnableDragRowSize(0)
        self.grid_auswahl.EnableDragGridSize(0)
        self.grid_auswahl.SetSelectionMode(wx.grid.Grid.GridSelectRows)   
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid_auswahl.SetReadOnly(row, col)
        #self.grid_auswahl.Bind(gridlib.EVT_GRID_COL_SORT, self.On_GridSort)
        self.grid_auswahl.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.On_GridSort)

        self.left_sizer =wx.BoxSizer(wx.HORIZONTAL)
        #self.left_sizer.AddStretchSpacer(1)
        self.left_sizer.Add(self.grid_auswahl,10,wx.EXPAND)        
        #self.left_sizer.AddStretchSpacer(1)
        
        self.label_Rep= wx.StaticText(self, 1, label="Report:", size = (70,18), name="lReport")
        self.text_Rep = wx.TextCtrl(self, -1, value="", style=wx.TE_PROCESS_ENTER, name="Report")
        self.Bind(wx.EVT_TEXT_ENTER, self.On_Report, self.text_Rep)
        self.button_calc = wx.Button(self, -1, label="&Calculate", name="Calc")
        self.Bind(wx.EVT_BUTTON, self.On_Calculate, self.button_calc)
        self.button_sim = wx.Button(self, -1, label="&Simulate", name="Sim")
        self.Bind(wx.EVT_BUTTON, self.On_Simulate, self.button_sim)
        self.button_open = wx.Button(self, -1, label="&Open", name="Open")
        self.Bind(wx.EVT_BUTTON, self.On_Open, self.button_open)
        self.button_quit = wx.Button(self, -1, label="&Quit", name="Quit")
        self.Bind(wx.EVT_BUTTON, self.On_Quit, self.button_quit)
        self.lower_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lower_sizer.AddStretchSpacer(1)
        self.lower_sizer.Add(self.button_open,0,wx.EXPAND)
        self.lower_sizer.AddStretchSpacer(1)
        self.lower_sizer.Add(self.label_Rep,0,wx.EXPAND)
        self.lower_sizer.Add(self.text_Rep,4,wx.EXPAND)
        self.lower_sizer.AddStretchSpacer(2)
        self.lower_sizer.Add(self.button_sim,0,wx.EXPAND)
        self.lower_sizer.AddStretchSpacer(1)
        self.lower_sizer.Add(self.button_calc,0,wx.EXPAND)
        self.lower_sizer.AddStretchSpacer(1)
        self.lower_sizer.Add(self.button_quit,0,wx.EXPAND)
        self.lower_sizer.AddStretchSpacer(1)
        # compose sizers
        self.mid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mid_sizer.AddSpacer(10)        
        self.mid_sizer.Add(self.left_sizer,1,wx.EXPAND)        
        self.mid_sizer.AddSpacer(10)
        #self.mid_sizer.Add(self.right_sizer,0,wx.EXPAND)
        #self.mid_sizer.AddSpacer(10)
        self.sizer = wx.BoxSizer(wx.VERTICAL)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.upper_sizer,0,wx.EXPAND)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.mid_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.lower_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        
        self.adjust_grid_rows()
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)
                
    def adjust_grid_rows(self):
        if self.new_rows > self.rows:
            self.grid_auswahl.AppendRows(self.new_rows - self.rows)
            self.rows = self.new_rows       
            for row in range(self.rows, self.new_rows):
                for col in range(self.cols):
                    self.grid_auswahl.SetReadOnly(row, col)
        elif self.new_rows < self.rows:
            for i in range(self.rows - self.new_rows):
                self.grid_auswahl.DeleteRows(1)
            self.rows = self.new_rows
        for col in range(self.cols):  
            self.grid_auswahl.SetColLabelValue(col,self.col_labels[col])
            if col < len(self.col_percents):
                self.grid_auswahl.SetColSize(col,self.col_percents[col]*self.grid_width/100)
    ## adjust matrix sizes
    # @param rows - new number of rows
    # @param cols - new number of columns
    def adjust_matrix(self, rows, cols):
        if rows > self.matrix_rows:
            self.matrix_grid.AppendRows(rows - self.matrix_rows)    
        elif rows < self.matrix_rows:
            for i in range(self.matrix_rows - rows):
                self.matrix_grid.DeleteRows(1)
        if cols > self.matrix_cols:
            self.matrix_grid.AppendCols(cols - self.matrix_cols)    
        elif cols < self.matrix_cols:
            for i in range(self.matrix_cols - cols):
                self.matrix_grid.DeleteCols(1)
        for row in range(rows):
            for col in range(cols):
                self.matrix_grid.SetReadOnly(row, col)
        self.matrix_rows = rows
        self.matrix_cols = cols
        if self.matrix_row_labels:
            for row in range(self.matrix_rows):  
                if self.matrix_row_labels[row]:
                    self.matrix_grid.SetRowLabelValue(row,self.matrix_row_labels[row])
                else:
                    self.matrix_grid.SetRowLabelValue(row,"Not Applicable")
        if self.matrix_col_labels:
            for col in range(self.matrix_cols):  
                if self.matrix_col_labels[col]: 
                    self.matrix_grid.SetColLabelValue(col,self.matrix_col_labels[col])
                else:
                    self.matrix_grid.SetColLabelValue(col,"n/a")
    ## change color of a grid column
    # @param index - index of column to be marked
    def mark_grid_column(self, index):
        if self.grid_sort_col == index: return
        if not self.grid_sort_col is None:
            for row in range(self.rows):            
                attr =  wx.grid.GridCellAttr()
                attr.SetBackgroundColour(wx.Colour(255, 255, 255))
                self.grid_auswahl.SetAttr(row, self.grid_sort_col, attr)
        for row in range(self.rows):
            attr =  wx.grid.GridCellAttr()
            attr.SetBackgroundColour(self.grid_auswahl.GetBackgroundColour())
            self.grid_auswahl.SetAttr(row, index, attr)
    ## generate initial data for screen
    # @param confname - name of config file
    def read_config(self, confname):
        self.confname = confname
        config = Afp_ReadConfig(confname)
        if self.debug: print("AfpACRScreen.read_config:", config)
        if config:
            if config["DATA_FILE_NAME"] and config["RANGE_FILE_NAME"]:
                self.activate_config(config)
    ## activate config data
    # @param config - dictionary holding configuration data
    def activate_config(self, config):
            if self.config is None:
                self.config = config
            else:
                for conf in config:
                    self.config[conf] = config[conf]
            if self.debug: print("AfpACRScreen.activate_config:", self.config)
            new = False
            if "RANGE_FILE_NAME" in self.config and self.config["RANGE_FILE_NAME"]:
                range_lines = Afp_importCSVLines(self.config["RANGE_FILE_NAME"])
                if self.debug: print("AfpACRScreen.activate_config: ranges",len(range_lines)," lines read!")
                self.ranges = AfpACRRanges(range_lines, self.config["RANGE_COLUMN_MAP"], self.debug)
                new = True
            if "DATA_FILE_NAME" in self.config and self.config["DATA_FILE_NAME"]:
                data = Afp_importCSVLines(self.config["DATA_FILE_NAME"])
                if self.debug: print("AfpACRScreen.activate_config: data", len(data), "lines read!")
                if self.people:
                    self.people.set_persons(data, self.config["DATA_COLUMN_MAP"])
                else:
                    self.people = AfpACRPeopleManager(data, self.config["DATA_COLUMN_MAP"], self.debug)
                new = True
            boosters = None
            if new and self.ranges:
                self.people.set_positioning(self.ranges)
                self.people.set_performance(self.config["DATA_PERFORMANCE_MAP"])
                if "DATA_PROMOTION_LIST" in self.config:
                    print("AfpACRScreen.activate_config: DATA_PROMOTION_LIST deprecated, please use DATA_BOOSTER_MAP!")   
                if "DATA_BOOSTER_MAP" in self.config:
                    boosters = Afp_getBoostersFromConfig(self.config["DATA_BOOSTER_MAP"], debug)
                    self.people.set_boosters(boosters)
                if "DATA_INVALID_LIST" in self.config or "ELIGIBLE_RELATIV_OTE_FACTOR" in self.config or "ELIGIBLE_OTE_MAXIMUM" in self.config or "SKIP_PERFORMANCE_INDICATOR" in self.config: 
                    data_list = None
                    ote_factor = None
                    ote_max = None
                    skip_perf = None
                    if "DATA_INVALID_LIST" in self.config: data_list = self.config["DATA_INVALID_LIST"]
                    if "ELIGIBLE_RELATIV_OTE_FACTOR" in self.config: ote_factor = self.config["ELIGIBLE_RELATIV_OTE_FACTOR"]
                    if "ELIGIBLE_OTE_MAXIMUM" in self.config: ote_max = self.config["ELIGIBLE_OTE_MAXIMUM"]
                    if "SKIP_PERFORMANCE_INDICATOR" in self.config: skip_perf = self.config["SKIP_PERFORMANCE_INDICATOR"]
                    self.people.set_eligibillity(data_list, skip_perf, ote_factor, ote_max)
                if not self.people.are_valid():
                    print("AfpACRScreen.activate_config WARNING Not all data supplied for each person!")
            if new and self.people:
                fixum = None
                if "BUDGET_FIXUM" in self.config and self.config["BUDGET_FIXUM"]:
                    fixum =  self.config["BUDGET_FIXUM"]
                self.calculator = AfpACRCalculator(self.people, self.config["BUDGET_PERCENTAGE"], fixum, self.debug)
                self.calculator.set_spreadmap(self.config["MATRIX_SPREAD_MAP"])
                if "MATRIX_MANAGER_MAP" in self.config:
                    self.calculator.set_manager(self.config["MATRIX_MANAGER_FOCAL"], self.config["MATRIX_MANAGER_FACTOR"], self.config["MATRIX_MANAGER_MAP"])
                else:
                    self.calculator.set_manager(self.config["MATRIX_MANAGER_FOCAL"], self.config["MATRIX_MANAGER_FACTOR"])
                self.calculator.set_calcflags(self.config["CALC_USE_FOCAL_FOR_RANGE"], self.config["CALC_SKIP_SPREAD_ZEROS"])
                self.calculator.set_boostermaps(boosters)
                if "MATRIX_ACR" in self.config:
                    self.calculator.set_acr_matrix(self.config["MATRIX_ACR"])
                rows = self.people.get_matrix_length(1)
                cols = self.people.get_matrix_length(0)
                self.matrix_row_labels = self.people.get_performance_indicators()[::-1]  # reverse a list via slicing [::-1]
                self.matrix_col_labels = []
                for i in range(int(cols/2)):
                    self.matrix_col_labels.append("+")
                    for j in range(i):
                        self.matrix_col_labels[j] += "+"
                self.matrix_col_labels.append("=")
                for i in range(int(cols/2)):
                    self.matrix_col_labels.append("-"*(i+1))
                self.adjust_matrix(rows, cols)
                self.On_Calculate()
    ## open different files
    # @param typ - typ of file to be opened, currently used: None, config, data, ranges
    def open_file(self, typ=None):
        config = {}
        if typ is None:
            liste = [["Configuration File", False], ["Data File", False], ["Market Range File", False]]
            res = AfpReq_MultiLine("Please select which file should be (re)selected!","", "Check", liste, "File Selection")
            if res:
                typ = ""
                if res[0]: 
                    typ += " config"
                else:
                    if res[1]: typ += " data"
                    if res[2]: typ += " ranges"
            else:
                return config
        dir = ""
        if  self.config: # assuming all files in same directory
            if  "DATA_FILE_NAME" in self.config: 
                dir = Afp_extractPath(self.config[ "DATA_FILE_NAME"])
            elif  "RANGE_FILE_NAME" in self.config: 
                dir = Afp_extractPath(self.config[ "RANGE_FILE_NAME"])
        if typ is None or "config" in typ:
            name, ok = AfpReq_FileName(dir,"Open Configuration File","*.cfg",True)
            if ok:
                self.config = None
                self.confname = name
                config = Afp_ReadConfig(name)
        if ((typ is None or "config" in typ) and not "DATA_FILE_NAME" in config) or  "data" in typ:
            #dir = "/home/daten/Afp/pyAfp/Import"
            print("AfpACRScreen.open_file data dir:", dir)
            name, ok = AfpReq_FileName(dir,"Open People Data File","*.csv",True)
            if ok: 
                config ["DATA_FILE_NAME"] = name
                active = False
                if active and self.config and "DATA_COLUMN_MAP" in self.config:
                    line = Afp_toString(Afp_importCSVLines(name, True)[0])
                    #line = line.encode('iso8859_15')
                    print("AfpACRScreen.open_file data line:", line[:-1], "&" in line)
                    liste = Afp_getArrayfromDict(self.config["DATA_COLUMN_MAP"])
                    vals = AfpReq_MultiLine("Please select columns where entries should be read from!",line,"Text", liste, "Column Selection")
                    print("AfpACRScreen.open_file columns:", vals)
                    # hier weiter -> Spalten zuordnen - ist zur Zeit nicht nötig, da Topologie der Daten immer gleich bleibt
        if (typ is None and not "RANGE_FILE_NAME" in config) or "ranges" in typ:
            print("AfpACRScreen.open_file ranges dir:", dir)
            name, ok = AfpReq_FileName(dir,"Open Market Ranges File","*.csv",True)
            if ok: 
                config ["RANGE_FILE_NAME"] = name
                # hier weiter -> Spalten zuordnen - ist zur Zeit nicht nötig, da Topologie der Daten immer gleich bleibt
        if self.debug: print("AfpACRScreen.open_file:", config)
        return config
    ## populate complete screen      
    def populate(self):
        self.Pop_grid()
        self.Pop_info()
        self.Pop_matrix()
    ## populate grid      
    def Pop_grid(self):
        rows = None
        if self.grid_data is None or len(self.grid_data) != self.rows:
            self.grid_data = self.people.get_grid_data()
        if self.grid_data: rows = self.grid_data
        if not rows: return
        lgh = len(rows)
        self.ident = []
        if not self.dynamic_rows:
            self.new_rows = lgh
            self.adjust_grid_rows()
        if self.debug: print("AfpACRScreen.Pop_grid lgh:", lgh, self.rows)
        for row in range(0, self.rows):
            #print "AfpACRScreen.Pop_grid row:", rows[row]
            for col in range(0,self.cols):
                #print "AfpACRScreen.Pop_grid grid:", row, col, rows[row][col]
                if row < lgh:
                    self.grid_auswahl.SetCellValue(row, col,  Afp_toString(rows[row][col]))
                else:
                    self.grid_auswahl.SetCellValue(row, col,  "")
    ## populate matrix grid
    # @param sel - matrix typ identifier from combo box
    def Pop_matrix(self, sel=None):
        if self.debug: print("AfpACRScreen.Pop_matrix:", sel)
        if sel is None:
            sel = self.combo_matrix.GetValue()
        if sel and self.calculator:
            self.matrix_typ = sel
            matrix = self.calculator.get_matrix(sel)
            for i in range(self.matrix_rows):
                ii = self.matrix_rows - i - 1
                for j in range(self.matrix_cols):
                    if Afp_validMatrixField(ii, j, matrix):
                        self.matrix_grid.SetCellValue(i, j,  Afp_toString(matrix[ii][j]))
                    else:
                        self.matrix_grid.SetCellValue(i, j, "")
    ## populate info area
    def Pop_info(self):
        if self.debug: print("AfpACRScreen.Pop_info:", self.confname)
        if self.confname:
            self.label_config.SetLabel(self.confname)
        if self.config:
            if "DATA_FILE_NAME" in self.config:
                self.label_data.SetLabel(self.config["DATA_FILE_NAME"])
            if "RANGE_FILE_NAME" in self.config:
                self.label_ranges.SetLabel(self.config["RANGE_FILE_NAME"])
        if self.calculator:
            values = self.calculator.get_info_values()
            ote = self.people.get_ote_sum()
            fte = self.people.get_ote_sum(True, False, False)
            inc = self.people.get_increase_sum()
            acr = self.people.get_acr_increase_sum()
            self.text_Budget.SetValue(Afp_toString(values["BudCnt"]).strip())
            self.label_OteSum.SetLabel(Afp_toString(ote))
            self.label_Budget.SetLabel(Afp_toString(values["Budget"]))
            self.text_Ref.SetValue(Afp_toFloatString(values["Ref"],False,"8.4f"))
            self.label_text1_line2.SetLabel(Afp_toString(fte))
            self.label_text2_line2.SetLabel(Afp_toString(inc))
            self.text_Focal.SetValue(Afp_toFloatString(values["Focal"],False,"8.4f"))
            if acr:
                self.label_text1_line3.SetLabel(Afp_toString(acr))
                diff = inc - acr
            else:
                self.label_label1_line3.SetLabel("Variance:")
                var1, var2 = self.calculator.get_variance_risk()
                var1 = int(var1/1000)
                var2= int(var2/1000)
                label = "-" + Afp_toString(var1) + "k, +"  + Afp_toString(var2) + "k"
                self.label_text1_line3.SetLabel(label)
                diff = values["Budget"]-inc
            self.label_text2_line3.SetLabel(Afp_toString(diff))
            if diff < 0:
                self.label_text2_line3.SetForegroundColour(wx.RED)
            else:
                self.label_text2_line3.SetForegroundColour(wx.BLUE)
    ## sort grid rows due to one column
    # @param index - index of column to trigger sort
    # @param desc - if given , flag if order should be descending
    def sort_grid_data(self, index, desc=None):
        rows = self.grid_data
        col = Afp_extractColumns(index, rows)
        for i in range(len(col)):
            col[i] = Afp_fromString(col[i])
        col, rows = Afp_sortSimultan(col, rows)
        if desc: rows.reverse()
        self.grid_data = rows
        self.Pop_grid()
    ## handle grid sort even (pressed on column header)
    def On_GridSort(self, event):
        index = event.GetCol()
        desc = None
        if index == self.grid_sort_col:
            desc = not self.grid_sort_desc
        self.mark_grid_column(index)
        self.grid_sort_col = index
        self.grid_sort_desc = desc
        self.sort_grid_data(index, desc)
    ## handle budget text enter event
    def On_Budget(self, event = None):
        value = Afp_fromString(self.text_Budget.GetValue())
        if self.debug: print("AfpACRScreen.On_Budget:", value)
        if self.calculator:
            self.calculator.set_budget(value)
            self.On_Calculate()
        if event: event.Skip()
    ## handle reference text enter event
    def On_Ref(self, event = None):
        value = Afp_fromString(self.text_Ref.GetValue())
        if self.debug: print("AfpACRScreen.On_Ref:", value)
        if self.calculator:
            self.calculator.simulate(value)
            self.grid_data = self.calculator.get_people_data()
            self.populate()
        if event: event.Skip()
    ## handle report text enter event
    def On_Report(self, event = None):
        value = Afp_fromString(self.text_Rep.GetValue())
        if self.debug: print("AfpACRScreen.On_Report:", value)
        if self.calculator:
            self.calculator.view(value)
        if event: event.Skip()
    ## handle focal text enter event
    def On_Focal(self, event = None):
        value = Afp_fromString(self.text_Focal.GetValue())
        if self.debug: print("AfpACRScreen.On_Focal:", value)
        if self.calculator:
            self.calculator.simulate(None, value)
            self.grid_data = self.calculator.get_people_data()
            self.populate()
        if event: event.Skip()
    ## handle combo selection event
    def On_Combo(self, event = None):
        select = self.combo_matrix.GetValue()
        if select != self.matrix_typ:
            self.Pop_matrix(select)
        if event: event.Skip()
    ## handle resize events
    def On_ReSize(self, event = None):
        size = self.GetSize()
        self.grid_width = size[0] - self.fixed_width
        height = size[1] - self.fixed_height
        if self.dynamic_rows:
            self.new_rows = int(height/self.row_height)
        self.adjust_grid_rows()        
        if self.new_rows != self.rows:
            self.Pop_grid()
        self.Refresh()        
        if event: event.Skip() 
    # handle Button events
    ## handle Calculate button event
    def On_Calculate(self, event = None):
        if self.calculator:
            self.calculator.calculate_focal_matrix()
            self.calculator.generate_reference_matrix()
            self.calculator.simulate()
            self.grid_data = self.calculator.get_people_data()
            self.populate()
        if event: event.Skip()
    ## handle Simulate button event
    def On_Simulate(self, event = None):
        if self.calculator:
            value = Afp_fromString(self.text_Ref.GetValue())
            self.calculator.simulate(value)
            self.grid_data = self.calculator.get_people_data()
            self.populate()
        if event: event.Skip()
    ## handle Calculate button event
    def On_Open(self, event = None):
        config = self.open_file()
        if config: 
            self.activate_config(config)
            self.On_ReSize() 
        if event: event.Skip()
    ## Eventhandler BUTTON - quit
    def On_Quit(self,event):
        self.Close()
        event.Skip()
        
 # Main   
if __name__ == "__main__":
    config = None
    debug = None
    if len(sys.argv) > 1:
        config = sys.argv[-1]
        if len(sys.argv) > 2 and sys.argv[1] == "-v":
            debug = True
    ex = wx.App()
    ACRScreen = AfpACRScreen(debug)
    if debug: print("AfpACRCalculatorScreen main, Screen loaded:", debug)
    ACRScreen.read_config(config)
    if debug: print("AfpACRCalculatorScreen main, config loaded:", config)
    ACRScreen.Show(True)
    if debug: print("AfpACRCalculatorScreen main, Screen shown")
    #example.add_data(data)
    ex.MainLoop()    

