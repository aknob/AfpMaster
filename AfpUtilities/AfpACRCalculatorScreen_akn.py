#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import wx

import AfpACRCalculator
from AfpACRCalculator import *
import AfpBase
from AfpBase.AfpBaseScreen import AfpScreen


def Afp_getGridData(cols, rows):
    data = []
    for i in range(rows):
        row = []
        for j in range(cols):
            row.append("Reihe " + str(i) + ", Spalte " + str(j))
        data.append(row)
    return data
def Afp_getPercents():
    return  [10, 20, 30, 25, 15]
def Afp_getLables():
    return   ["1", "2", "3", "4", "5"]

## Class_Adresse shows Window Adresse and handles interactions
class AfpACRScreen(AfpScreen):
    ## initialize AfpAdScreen, graphic objects are created here
    # @param debug - flag for debug info
    def __init__(self, debug = None):
        AfpScreen.__init__(self,None, -1, "")
        self.typ = "ACR"
        self.archiv_rows = 10
        self.colnames = ["Name","Family","OTE","FTE","CLǴ", "DAIT","Position", "Performance", "%", "Increase"]
        self.colwidth = [20 ,15, 15, 5, 5, 5, 5, 5, 10, 15]
        # self properties
        self.SetTitle("AFP ACR-Calculator")
        self.SetSize((800, 600))
        self.SetBackgroundColour(wx.Colour(192, 192, 192))
        self.SetForegroundColour(wx.Colour(20, 19, 18))
        self.SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, "DejaVu Sans"))

      # values from call
        self.sizer = None
        self.config = None
        self.ranges = None
        self.people = None
        self.calculator = None
        # inital values      
        self.rows = 7
        #self.rows = int(1.5*self.rows)
        self.new_rows = self.rows
        self.fixed_width = 70
        self.fixed_height = 110
        self.grid_width = None
        self.grid_data = None
        # for internal use
        self.used_modul = None
        self.col_labels = ["Name","Family","OTE","FTE","CLG", "DAIT","-0+", "P&DC", "Promo", "%", "Increase"]
        self.col_percents =  [20 ,15, 10, 5, 5, 5, 5, 5, 5, 10, 15]
        self.cols = len(self.col_labels)
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
        #self.SetSize((560,315))
        height = self.GetSize()[1] - self.fixed_height
        self.row_height = height/self.rows 
        print "New:", self.GetSize(), height, self.grid_width, self.row_height, self.rows, self.new_rows
        #self.Pop_grid()
        self.Bind(wx.EVT_SIZE, self.On_ReSize)

    ## set up dialog widgets      
    def InitWx(self):
        self.label_Auswahl = wx.StaticText(self, 1, label="-- Bitte Datensatz auswählen --", name="Auswahl")
        
        self.button_First = wx.Button(self, -1, label="|<", size=(30,28), name="First")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_First, self.button_First)
        self.button_PPage = wx.Button(self, -1, label="&<<", size=(30,28), name="PPage")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_PPage, self.button_PPage)
        self.button_Minus = wx.Button(self, -1, label="&<", size=(30,28), name="Minus")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_Prev, self.button_Minus)
        self.button_Plus = wx.Button(self, -1, label="&>", size=(30,28), name="Plus")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_Next, self.button_Plus)
        self.button_NPage = wx.Button(self, -1, label="&>>", size=(30,28), name="NPage")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_NPage, self.button_NPage)
        self.button_Last = wx.Button(self, -1, label=">|", size=(30,28), name="Last")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_Last, self.button_Last)
        box = wx.StaticBox(self, size=(40, 212))
        self.right_sizer =wx.StaticBoxSizer(box, wx.VERTICAL)
        #self.right_sizer =wx.BoxSizer(wx.VERTICAL)
        self.right_sizer.AddStretchSpacer(1)      
        self.right_sizer.Add(self.button_First,0,wx.EXPAND)        
        self.right_sizer.Add(self.button_PPage,0,wx.EXPAND)        
        self.right_sizer.Add(self.button_Minus,0,wx.EXPAND)        
        self.right_sizer.Add(self.button_Plus,0,wx.EXPAND)        
        self.right_sizer.Add(self.button_NPage,0,wx.EXPAND)        
        self.right_sizer.Add(self.button_Last,0,wx.EXPAND)        
        self.right_sizer.AddStretchSpacer(1) 
        
        self.grid_auswahl = wx.grid.Grid(self, -1, style=wx.FULL_REPAINT_ON_RESIZE | wx.ALWAYS_SHOW_SB, name="Auswahl")
        self.grid_auswahl.CreateGrid(self.rows, self.cols)
        self.grid_auswahl.SetRowLabelSize(0)
        self.grid_auswahl.SetColLabelSize(18)
        self.grid_auswahl.EnableEditing(0)
        #self.grid_auswahl.EnableDragColSize(0)
        self.grid_auswahl.EnableDragRowSize(0)
        self.grid_auswahl.EnableDragGridSize(0)
        self.grid_auswahl.SetSelectionMode(wx.grid.Grid.wxGridSelectRows)   
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid_auswahl.SetReadOnly(row, col)

        self.left_sizer =wx.BoxSizer(wx.HORIZONTAL)
        #self.left_sizer.AddStretchSpacer(1)
        self.left_sizer.Add(self.grid_auswahl,10,wx.EXPAND)        
        #self.left_sizer.AddStretchSpacer(1)
        
        self.button_Suchen = wx.Button(self, -1, label="&Suchen", name="Suchen")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_Suchen, self.button_Suchen)
        self.button_Neu = wx.Button(self, -1, label="&Neu", name="Neu")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_Neu, self.button_Neu)
        self.button_Abbruch = wx.Button(self, -1, label="&Abbruch", name="Abbruch")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_Abbruch, self.button_Abbruch)
        self.button_Okay = wx.Button(self, -1, label="&OK", name="Okay")
        #self.Bind(wx.EVT_BUTTON, self.On_Ausw_Ok, self.button_Okay)
        self.lower_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lower_sizer.AddStretchSpacer(1)
        self.lower_sizer.Add(self.button_Suchen,0,wx.EXPAND)
        self.lower_sizer.AddStretchSpacer(1)
        self.lower_sizer.Add(self.button_Neu,0,wx.EXPAND)
        self.lower_sizer.AddStretchSpacer(4)
        self.lower_sizer.Add(self.button_Abbruch,0,wx.EXPAND)
        self.lower_sizer.AddStretchSpacer(1)
        self.lower_sizer.Add(self.button_Okay,0,wx.EXPAND)
        self.lower_sizer.AddStretchSpacer(1)
        # compose sizers
        self.mid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mid_sizer.Add(self.left_sizer,1,wx.EXPAND)        
        self.mid_sizer.AddSpacer(10)
        self.mid_sizer.Add(self.right_sizer,0,wx.EXPAND)
        self.mid_sizer.AddSpacer(10)
        self.sizer = wx.BoxSizer(wx.VERTICAL)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.label_Auswahl,0,wx.EXPAND)        
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
            print "Add:", self.new_rows - self.rows, self.grid_auswahl.GetNumberRows()
            self.rows = self.new_rows       
            for row in range(self.rows, self.new_rows):
                for col in range(self.cols):
                    self.grid_auswahl.SetReadOnly(row, col)
        elif self.new_rows < self.rows:
            for i in range(self.rows - self.new_rows):
                self.grid_auswahl.DeleteRows(1)
            print "Del:", self.rows - self.new_rows, self.grid_auswahl.GetNumberRows()
            self.rows = self.new_rows
        ColSize = []
        for per in self.col_percents:
            ColSize.append(per*self.grid_width/100)
        for col in range(self.cols):  
            self.grid_auswahl.SetColLabelValue(col,self.col_labels[col])
            if col < len(self.col_percents):
                self.grid_auswahl.SetColSize(col,self.col_percents[col]*self.grid_width/100)
    ## generate initial data for screen
    # @param config - dictionary holding configuration data
    def generate_data(self, config):
        self.config = config
        print "AfpACRScreen.generate_data:", config
        if self.config["DATA_FILE_NAME"] and self.config["RANGE_FILE_NAME"]:
            data = Afp_importCSVLines(self.config["DATA_FILE_NAME"])
            range_lines = Afp_importCSVLines(self.config["RANGE_FILE_NAME"])
            if self.debug: print "AfpACRScreen.generate_data:: data", len(data), "lines and ranges",len(range_lines)," lines read!"
            self.ranges = AfpACRRanges(range_lines, self.config["RANGE_COLUMN_MAP"], self.debug)
            self.people = AfpACRPeopleManager(data, self.config["DATA_COLUMN_MAP"], self.debug)
            self.people.set_positioning(self.ranges)
            self.people.set_performance(self.config["DATA_PERFORMANCE_MAP"])
            self.people.set_promotion(self.config["DATA_PROMOTION_LIST"])
            if not self.people.are_valid():
                print "AfpACRScreen.generate_data WARNING Not all data supplied for each person!"
                
            self.calculator = AfpACRCalculator(self.people, self.config["BUDGET_PERCENTAGE"], self.debug)
            self.calculator.set_spreadmap(self.config["MATRIX_SPREAD_MAP"])
            self.calculator.set_manager(self.config["MATRIX_MANAGER_MAP"])
        print "AfpACRScreen.generate_data:", self.ranges, self.people, self.calculator
        self.Pop_grid()
          
    def Pop_grid(self):
        if self.grid_data is None or len(self.grid_data) != self.rows:
            self.grid_data = self.people.get_grid_data()
        if self.grid_data: rows = self.grid_data
        lgh = len(rows)
        self.ident = []
        print "AfpACRScreen.Pop_grid lgh:", lgh
        for row in range(0, self.rows):
            print "AfpACRScreen.Pop_grid row:", rows[row]
            for col in range(0,self.cols):
                print "AfpACRScreen.Pop_grid grid:", row, col
                print "AfpACRScreen.Pop_grid grid:", rows[row][col]
                if row < lgh:
                    #self.grid_auswahl.SetCellValue(row, col,  Afp_toString(rows[row][col]))
                    self.grid_auswahl.SetCellValue(row, col,  rows[row][col])
                else:
                    self.grid_auswahl.SetCellValue(row, col,  "")
            #if row < lgh:
            #self.ident.append(rows[row][self.cols])   
    def On_ReSize(self, event):
        size = self.GetSize()
        self.grid_width = size[0] - self.fixed_width
        height = size[1] - self.fixed_height
        self.new_rows = int(height/self.row_height)
        #print "Resize:", size, height, self.grid_width, self.row_height, self.rows, self.new_rows
        self.adjust_grid_rows()
        self.Pop_grid()
        event.Skip()   
        
 # Main   
if __name__ == "__main__":
    config = None
    debug = None
    if len(sys.argv) > 1:
        config = Afp_ReadConfig(sys.argv[-1])
        if len(sys.argv) > 2 and sys.argv[1] == "-v":
            debug = true
    ex = wx.App()
    ACRScreen = AfpACRScreen(debug)
    ACRScreen.generate_data(config)
    ACRScreen.Show(True)
    #example.add_data(data)
    ex.MainLoop()    


