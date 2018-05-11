#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseAdRoutines
# AfpBaseAdRoutines module provides classes and routines needed for adress handling,\n
# no display and user interaction in this modul.
#
#   History: \n
#        24 Jan. 2015 - add order list- Andreas.Knoblauch@afptech.de \n
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

import AfpBase
from AfpBase import AfpDatabase, AfpBaseRoutines, AfpUtilities
from AfpBase.AfpDatabase import AfpSQL
from AfpBase.AfpDatabase.AfpSQL import AfpSQLTableSelection
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_getMaxOfColumn

## return dictionary to map between status integers an choice entries on screen   
def AfpAdresse_StatusMap():
    return {-1:1,0:0,1:1,5:2,6:3,9:4}
## mapping in other direction \n
# return status flag indicated by input \n
# @param ind - index in screen choice selection
def AfpAdresse_StatusReMap(ind):
    dict = AfpAdresse_StatusMap()
    for key in dict:
        if dict[key] == ind: return key
    return None
## return names of textfields needed for special attribut dialogs
# @param attribut - name of attribut to define the special dialog
def AfpAdresse_getAttributTagList(attribut):
    list = []
    attribut = Afp_toString(attribut)
    if attribut == "Reisebüro".decode("UTF-8"):
        list = ["Provision","Reisebürokontierung".decode("UTF-8")]
    elif attribut == "Reiseveranstalter":
        list = ["Verrechungskonto", "Veranstalter (Debitor)","Veranstalter (Kreditor)","Reisekennung"]
    return list
 
##  get the list of indecies of address table,
# @param mysql - database where values are retrieved from
# @param index  -  name sort criterium initially selected
# @param datei  -  name table to be used as primary
def AfpAdresse_getOrderlistOfTable(mysql, index, datei = "ADRESSE"):
    if datei == "ADRESATT":
        keep = ["Name","KundenNr"]
        indirect = None
    else: 
        keep = ["NamSort","KundenNr"]
        indirect = ["Name","Plz","Ort"]
    liste = Afp_getOrderlistOfTable(mysql, datei, keep, indirect)
    return liste
 
## get values of fields in given selection for an address with given identifier \n
# additionally the name is given, as it is commonly needed in following dialogs
# @param globals - globals variables, including mysql connection
# @param KNr - identifier for address to be searched
# @param selname - name of selection where fileds should be extracted from
# @param felder - name of fields to be extracted, separated by ,
def AfpAdresse_getListOfTable(globals, KNr, selname, felder):
    adresse = AfpAdresse(globals, KNr)
    rows = adresse.get_value_rows(selname, felder)
    name = adresse.get_name()
    return rows, name

## baseclass for address handling      
class AfpAdresse(AfpSelectionList):
    ## initialize AfpAdresse class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param KundenNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved durin initialisation \n
    # \n
    # either KundenNr or sb (superbase) has to be given for initialisation,otherwise a new, clean object is created
    def  __init__(self, globals, KundenNr = None, sb = None, debug = False, complete = False):
        # either KundenNr or sb (superbase) has to be given for initialisation,
        # otherwise a new, clean object is created
        AfpSelectionList.__init__(self, globals, "ADRESSE", debug)
        self.debug = debug
        self.new = False
        self.mainindex = "KundenNr"
        self.mainvalue = ""
        self.spezial_bez = []
        if sb:
            self.mainvalue = sb.get_string_value("KundenNr.ADRESSE")
            AdSelection = sb.gen_selection("ADRESSE", "KundenNr", debug)
            self.selections["ADRESSE"] = AdSelection
        else:
            if KundenNr:
                self.mainvalue = Afp_toString(KundenNr)
            else:
                self.new = True
        self.mainselection = "ADRESSE"
        self.set_main_selects_entry()
        if not self.mainselection in self.selections:
            self.create_selection(self.mainselection)
        self.selects["ADRESATT"] = [ "ADRESATT","KundenNr = KundenNr.ADRESSE"] 
        self.selects["ANFRAGE"] = [ "ANFRAGE","KundenNr = KundenNr.ADRESSE"] 
        self.selects["Bez"] = []   
        self.selects["ARCHIV"] = [ "ARCHIV","KundenNr = KundenNr.ADRESSE"] 
        self.selects["BUCHUNG"] = [ "BUCHUNG","KundenNr = KundenNr.ADRESSE"] 
        self.selects["FAHRTEN"] = [ "FAHRTEN","KundenNr = KundenNr.ADRESSE"] 
        self.selects["FahrtKontakt"] = [ "FAHRTEN","KontaktNr = KundenNr.ADRESSE"] 
        self.selects["FAHRTVOR"] = [ "FAHRTVOR","KundenNr = KundenNr.ADRESSE"] 
        self.selects["FAHRER"] = [ "FAHRER","FahrerNr = KundenNr.ADRESSE"] 
        self.selects["EINSATZ"] = [ "EINSATZ","FremdNr = KundenNr.ADRESSE"] 
        self.selects["RECHNG"] = [ "RECHNG","KundenNr = KundenNr.ADRESSE"] 
        self.selects["ANMELD"] = [ "ANMELD","KundenNr = KundenNr.ADRESSE"] 
        self.selects["AnmeldAgent"] = [ "ANMELD","AgentNr = KundenNr.ADRESSE"] 
        self.selects["REISEN"] = [ "REISEN","AgentNr = KundenNr.ADRESSE"] 
        self.selects["VERBIND"] = [ "VERBIND","KundenNr = KundenNr.ADRESSE"] 
        if complete: self.create_selections()
        if self.debug: print "AfpAdresse Konstruktor, KundenNr:", self.mainvalue
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpAdresse Destruktor"
    ## special selection (overwritten from AfpSelectionList) \n
    # to handle the selection 'Bez' (Beziehung) which attach different address entries via a single connected list in the datafield 'Bez'
    # @param selname - name of selection (in our case 'Bez' is implemented)
    # @param new - flag if a new empty list has to be created
    def spezial_selection(self, selname, new = False):
        AdSelection = None
        if selname == "Bez":
            #print  self.selections["ADRESSE"].get_feldnamen()
            feldnamen = self.selections["ADRESSE"].get_feldnamen()
            if new:
                 AdSelection = AfpSQLTableSelection(self.mysql, "ADRESSE", self.debug, None, feldnamen) 
                 AdSelection.new_data()
            else: 
                AdSelection = AfpSQLTableSelection(self.mysql, "ADRESSE", self.debug, None, feldnamen) 
                KNr = self.selections["ADRESSE"].get_value("Bez")
                if not KNr: KNr = 0
                data = []
                self.spezial_bez = []
                if KNr != 0:
                    Index = feldnamen.index("Bez")
                    KundenNr = int(self.mainvalue)
                    while KNr !=  KundenNr and KNr != 0 :
                        if KNr < 0: KNr = - KNr
                        row = self.mysql.select("*","KundenNr = " + Afp_toString(KNr), "ADRESSE")
                        self.spezial_bez.append(KNr)
                        KNr = int(row[0][Index])
                        data.append(row[0])
                    AdSelection.set_data(data)
        return AdSelection
    ## special save (overwritten from AfpSelectionList) \n
    # store the special selection 'Bez'
    # @param selname - name of selection (in oru case 'Bez' is implemented)
    def spezial_save(self, selname):
        if selname == "Bez": 
            selection = self.selections[selname]
            lgh = selection.get_data_length()
            if lgh > 0:
                KNr = int(self.mainvalue)
                bez_lgh = len(self.spezial_bez)
                for i in range(lgh):
                    KundenNr = KNr
                    index = -1
                    if KundenNr in self.spezial_bez: 
                        index = self.spezial_bez.index(KundenNr)
                        self.spezial_bez[index] = None
                    KNr = int(selection.get_values("KundenNr", i))
                    self.mysql.write_update("ADRESSE", ["Bez"], [KNr], "KundenNr = " + Afp_toString(KundenNr), True)
                if KNr in self.spezial_bez: 
                    index = self.spezial_bez.index(KNr)
                    self.spezial_bez[index] = None
                self.mysql.write_update("ADRESSE", ["Bez"], [self.mainvalue], "KundenNr = " + Afp_toString(KNr))
            for KNr in self.spezial_bez:
                if KNr: self.mysql.write_update("ADRESSE", ["Bez"], ["0"], "KundenNr = " + Afp_toString(KNr))
    ## get short identifier of name \n
    # currently a trigram is used, first letter of surname plus first and second letter of lastname
    def get_short_name(self):
        vorname = self.get_string_value("Vorname")
        name = self.get_string_value("Name")
        return vorname[0].lower() + name[:2].lower()
    ## return next attribut number for the actuel adress
    def next_attribut_number(self):
        rows = self.get_selection("ADRESATT").get_values()
        max = Afp_getMaxOfColumn(rows)
        if max is None: max = 1 
        else: max += 1
        return max
    ##  merge given address into this address, all dependent data is taken over by replacing the address identification number \n
    # the given address is deleted, address dependent data (like name or accountnumbers) is replaced by values of this address
    # @param victim - 'Adresse' selecion list, which should be merged and deleted
    def hostile_takeover(self, victim):
        if self.get_listname() == victim.get_listname():
            KNr = self.get_value("KundenNr")
            name = self.get_name(True)
            debitor = self.get_account("Debitor")
            kreditor = self.get_account("Kreditor")
            selects = self.get_selection_names()
            names = {"ADRESATT": "Name","ANMELDER": "AgentName","REISEN":"AgentName", "VERBIND":"Name", "FAHRTEN":"Name","AnmeldAgent":"AgentName"}
            debitors = {"ANMELDER": "AgentDebitor", "RECHNG":"Debitor", "REISEN":"Debitor"}
            kreditors = {"VERBIND": "Kreditor","REISEN":"Kreditor"}
            # move through all selections and replave the values
            for sel in selects:
                selection = victim.get_selection(sel)
                target = victim.get_select_target(sel)
                if selection and target:
                    selection.spread_value(target, KNr)
                    if sel in names:  selection.spread_value(names[sel], name)
                    if sel in debitors:  selection.spread_value(debitors[sel], debitor)
                    if sel in kreditors:  selection.spread_value(kreditors[sel], kreditor)
            # flag the address to be deleted
            victim.get_selection().delete_row()
            # write values to database
            if self.debug: print "AfpAdresse.hostile_takeover:", auswahl,"->", KdNr
            print "AfpAdresse.hostile_takeover:", auswahl,"->", KdNr
            #victim.view()  
            victim.store()
    ## retrieve individual account from database
    # @param typ: defines which kind of account is selected \n
    # currently supported types are "Kreditor" and "Debitor"
    def get_account(self, typ = "Debitor"):
        account = Afp_getIndividualAccount(self.globals.get_mysql(), self.get_value("KundenNr"), typ)
        return account

      