#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseAdRoutines
# AfpBaseAdRoutines module provides classes and routines needed for address handling,\n
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
#    Copyright© 1989 - 2020 afptech.de (Andreas Knoblauch)
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

## try to retrieve uniqu address from name
# @param mysql - connection to database
# @param name - name given in the format 'firstname' + " " + 'lastname'
def AfpAdresse_getKNrFromSingleName(mysql, name):
    KNr = None
    rows = mysql.execute("SELECT KundenNr FROM ADRESSE WHERE CONCAT(Vorname,\" \",Name) = \"" + name + "\";")
    #print "AfpAdresse_getKNrFromSingleName:", name, rows
    if rows and len(rows) == 1:
        KNr = rows[0][0]
    return KNr
        
 
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
    
## get the list of names (and addresses) of all entries having assigned the given attribut \n
# @param globals - globals variables, including mysql connection
# @param attribut - attribut looked for
# @param felder - name of address-fields to be extracted, separated by ,
def AfpAdresse_getAddresslistOfAttribut(globals, attribut):
    namen = []
    idents = []
    adresatt = AfpSQLTableSelection(globals.get_mysql(), "ADRESATT", globals.is_debug())
    adresatt.load_data("Attribut = \"" + attribut + "\" AND KundenNr > 0") 
    rows = adresatt.get_values()
    for row in rows:
        adresse = AfpAdresse(globals, row[0])
        #namen.append(adresse.get_address_line())
        namen.append(adresse.get_name())
        idents.append(adresse.get_value("KundenNr"))
    return namen, idents
    
### baseclass for address handling      
class AfpAdresse(AfpSelectionList):
    ## initialize AfpAdresse class
    # @param globals - global values including the mysql connection - this input is mandatory
    # @param KundenNr - if given and sb == None, data will be retrieved this database entry
    # @param sb - if given data will  be retrieved from the actuel AfpSuperbase data
    # @param debug - flag for debug information
    # @param complete - flag if data from all tables should be retrieved during initialisation \n
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
            if self.mainvalue:
                AdSelection = sb.gen_selection("ADRESSE", "KundenNr", debug)
                self.selections["ADRESSE"] = AdSelection
            else:
                self.new = True
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
        self.selects["EVENT"] = [ "EVENT","AgentNr = KundenNr.ADRESSE"] 
        self.selects["VERBIND"] = [ "VERBIND","KundenNr = KundenNr.ADRESSE"] 
        if complete: self.create_selections()
        if self.debug: print "AfpAdresse Konstruktor, KundenNr:", self.mainvalue
    ## destructor
    def __del__(self):    
        if self.debug: print "AfpAdresse Destruktor"
    ## clear current SelectionList to behave as a newly created List 
    # @param KundenNr - if given, KundenNr address from where main data should be delivered   
    def set_new(self, KundenNr):
        self.new = True
        data = {}
        keep = []
        self.clear_selections(keep)
        if KundenNr:
            Adresse = AfpAdresse(self.globals, KundenNr)
            data["Name"]  = Adresse.get_value("Name")
            data["Strasse"] =  Adresse.get_value("Strasse")
            data["Plz"]  = Adresse.get_value("Plz")
            data["Ort"]  = Adresse.get_value("Ort")
            self.set_data_values(data,"ADRESSE")   
        #print "AfpAdresse.set_new:", KundenNr 
        #self.view()
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
                    #print "AfpAdresse.spezial_save KNr:", selection.get_values("KundenNr", i)
                    KNr = int(selection.get_values("KundenNr", i)[0][0])
                    self.mysql.write_update("ADRESSE", ["Bez"], [KNr], "KundenNr = " + Afp_toString(KundenNr), True)
                if KNr in self.spezial_bez: 
                    index = self.spezial_bez.index(KNr)
                    self.spezial_bez[index] = None
                self.mysql.write_update("ADRESSE", ["Bez"], [self.mainvalue], "KundenNr = " + Afp_toString(KNr))
            for KNr in self.spezial_bez:
                if KNr: self.mysql.write_update("ADRESSE", ["Bez"], ["0"], "KundenNr = " + Afp_toString(KNr))
    ## get complete address of name in one line \n
    # @param no_firstname - flag is first name should be skipped for output
    def get_address_line(self, no_firstname = False):
        line = ""
        if not no_firstname:
            line += self.get_string_value("Vorname") + " "
        line += self.get_string_value("Name") + ", "
        line += self.get_string_value("Strasse") + ", "
        line += self.get_string_value("Plz") + " "
        line += self.get_string_value("Ort")
        return line
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
            names = {"ADRESATT": "Name","ANMELDER": "AgentName","EVENT":"AgentName", "VERBIND":"Name", "FAHRTEN":"Name","AnmeldAgent":"AgentName"}
            debitors = {"ANMELDER": "AgentDebitor", "RECHNG":"Debitor", "EVENT":"Debitor"}
            kreditors = {"VERBIND": "Kreditor","EVENT":"Kreditor"}
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

# database tables

## get dictionary with required database tables and mysql generation code
# @param flavour - if given flavour of modul
def AfpAdresse_getSqlTables(flavour = None):
    required = {}
    # address attribut table
    required["ADRESATT"] = """CREATE TABLE `ADRESATT` (
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL DEFAULT '00000000',
  `Name` tinytext CHARACTER SET latin1,
  `Attribut` char(20) CHARACTER SET latin1 NOT NULL,
  `AttNr` smallint(5) DEFAULT NULL,
  `AttText` tinytext CHARACTER SET latin1,
  `Tag` tinytext CHARACTER SET latin1,
  `Aktion` tinytext CHARACTER SET latin1,
  KEY `KundenNr` (`KundenNr`),
  KEY `Name` (`Name`(50)),
  KEY `AttKdNr` (`Attribut`,`KundenNr`),
  KEY `AttName` (`Attribut`,`Name`(50))
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # address table
    required["ADRESSE"] = """CREATE TABLE `ADRESSE` (
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `Vorname` tinytext CHARACTER SET latin1,
  `Name` tinytext CHARACTER SET latin1 COLLATE latin1_german1_ci NOT NULL,
  `Strasse` tinytext CHARACTER SET latin1,
  `Plz` char(5) CHARACTER SET latin1 DEFAULT NULL,
  `Ort` tinytext CHARACTER SET latin1,
  `Telefon` tinytext CHARACTER SET latin1,
  `Geburtstag` date DEFAULT NULL,
  `Reise` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Miet` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Kontakt` date DEFAULT NULL,
  `Bez` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Bem` tinytext CHARACTER SET latin1,
  `Kennung` smallint(6) NOT NULL,
  `NamSort` tinytext CHARACTER SET latin1,
  `Tel2` tinytext CHARACTER SET latin1,
  `Fax` tinytext CHARACTER SET latin1,
  `Mail` tinytext CHARACTER SET latin1,
  `BemExt` char(20) CHARACTER SET latin1 DEFAULT NULL,
  `Geschlecht` char(1) CHARACTER SET latin1 NOT NULL,
  `Anrede` char(3) CHARACTER SET latin1 NOT NULL,
  `SteuerNr` char(20) CHARACTER SET latin1 DEFAULT NULL,
  PRIMARY KEY (`KundenNr`),
  KEY `KundenNr` (`KundenNr`),
  KEY `Plz` (`Plz`),
  KEY `Ort` (`Ort`(50)),
  KEY `Bez` (`Bez`),
  KEY `NamSort` (`Name`(50),`Vorname`(20)),
  KEY `Name` (`Name`(50))
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # archiv table
    required["ARCHIV"] = """CREATE TABLE `ARCHIV` (
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `Art` char(20) CHARACTER SET latin1 NOT NULL,
  `Typ` char(20) CHARACTER SET latin1 NOT NULL,
  `Gruppe` char(20) CHARACTER SET latin1 NOT NULL,
  `Bem` tinytext CHARACTER SET latin1,
  `Extern` tinytext CHARACTER SET latin1 NOT NULL,
  `Datum` date NOT NULL,
  `Tab` varchar(10) CHARACTER SET latin1 DEFAULT NULL,
  `TabNr` mediumint(9) DEFAULT NULL,
  KEY `KundenNr` (`KundenNr`),
  KEY `Extern` (`Extern`(50)),
  KEY `Datum` (`Datum`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # registration revenue table
    required["ANFRAGE"] = """CREATE TABLE `ANFRAGE` (
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `Datum` date NOT NULL,
  `Info` tinytext CHARACTER SET latin1 NOT NULL,
  `Zustand` smallint(6) NOT NULL,
  `KdNrInfo` tinytext CHARACTER SET latin1 NOT NULL,
  KEY `KundenNr` (`KundenNr`),
  KEY `Datum` (`Datum`),
  KEY `Zustand` (`Zustand`),
  KEY `KdNrInfo` (`KundenNr`,`Info`(50))
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # return values
    return required

