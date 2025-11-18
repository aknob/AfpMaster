#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpBaseAdRoutines
# AfpBaseAdRoutines module provides classes and routines needed for address handling,\n
# no display and user interaction in this modul.
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        24 Jan. 2015 - add order list- Andreas.Knoblauch@afptech.de \n
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

from AfpBase.AfpDatabase.AfpSQL import AfpSQLTableSelection
from AfpBase.AfpSelectionLists import AfpSelectionList
from AfpBase.AfpBaseRoutines import Afp_getOrderlistOfTable, Afp_getIndividualAccount
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_getMaxOfColumn
from AfpBase.AfpUtilities.AfpStringUtilities import Afp_toString

## return list of status string   
def AfpAdresse_StatusStrings():
    #return ["Passiv", "Aktiv", "keine Werbung", "Markiert", "Inaktiv"]
    return ["Passiv", "Aktiv", "Neutral", "Markiert", "Inaktiv"]
## return dictionary to map between status integers an choice entries on screen   
def AfpAdresse_StatusMap():
    return {-1:1,0:0,1:1,4:2,5:3,6:3,9:4}
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
    if attribut == "Reisebüro":
        list = ["Provision","Reisebürokontierung"]
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

## try to retrieve unique address from name
#  the address-identifier is only returnd if a uniqur result is found!
# @param mysql - connection to database
# @param name - name given in the format 'firstname' + " " + 'lastname', 'lastname' + " " + 'firstname' or 'lastname'
def AfpAdresse_getKNrFromSingleName(mysql, name):
    KNr = None
    if name:
        rows = mysql.execute("SELECT KundenNr FROM ADRESSE WHERE CONCAT(Vorname,\" \",Name) = \"" + name + "\";")
        #print "AfpAdresse_getKNrFromSingleName:", name, rows
        if rows and len(rows) == 1:
            KNr = rows[0][0]
        if KNr is None:
            rows = mysql.execute("SELECT KundenNr FROM ADRESSE WHERE CONCAT(Name,\" \",Vorname) = \"" + name + "\";")
            if rows and len(rows) == 1:
                KNr = rows[0][0]
        if KNr is None:
            rows = mysql.execute("SELECT KundenNr FROM ADRESSE WHERE CONCAT(Name,\", \",Vorname) = \"" + name + "\";")
            if rows and len(rows) == 1:
                KNr = rows[0][0]
        if KNr is None:
            rows = mysql.execute("SELECT KundenNr FROM ADRESSE WHERE Name = \"" + name + "\";")
            if rows and len(rows) == 1:
                KNr = rows[0][0]
    return KNr
## try to retrieve unique address from alias attribut of address
# @param mysql - connection to database
# @param alias - alias of name given for search
def AfpAdresse_getKNrFromAlias(mysql, alias):
    KNr = None
    if alias:
        rows = mysql.execute("SELECT KundenNr FROM ADRESATT WHERE Attribut = \"Alias\" AND AttText = \"" + alias + "\";")
        #print "AfpAdresse_getKNrFromSingleName:", name, rows
        if rows and len(rows) == 1:
            KNr = rows[0][0]
    return KNr
        
## get values of fields in given selection for an address with given identifier \n
# additionally the name is given, as it is commonly needed in following dial    ogs
# @param globals - globals variables, including mysql connection
# @param KNr - identifier for address to be searched
# @param selname - name of selection where fileds should be extracted from
# @param felder - name of fields to be extracted, separated by ,
# @param filter - if given, additional filter to be used to retrieve data
def AfpAdresse_getListOfTable(globals, KNr, selname, felder, filter = None):
    adresse = AfpAdresse(globals, KNr)
    if filter:
        sel = adresse.evaluate_selects(selname)[0] + " AND (" + filter + ")"
        print ("AfpAdresse_getListOfTable sel:", sel)
        adresse.get_selection(selname).load_data(sel)
    rows = adresse.get_value_rows(selname, felder)
    name = adresse.get_name()
    return rows, name
    
## get list of all entries having assigned the given attribut \n
# @param globals - globals variables, including mysql connection
# @param attribut - attribut looked for
def AfpAdresse_getListOfAttribut(globals, attribut):
    adresatt = AfpSQLTableSelection(globals.get_mysql(), "ADRESATT", globals.is_debug())
    adresatt.load_data("Attribut = \"" + attribut + "\" AND KundenNr > 0") 
    return adresatt.get_values()
## get the list of names (and addresses) of all entries having assigned the given attribut \n
# @param globals - globals variables, including mysql connection
# @param attribut - attribut looked for
def AfpAdresse_getAddresslistOfAttribut(globals, attribut):
    namen = []
    idents = []
    rows = AfpAdresse_getListOfAttribut(globals, attribut)
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
    # either KundenNr or sb (superbase) has to be given for initialisation, otherwise a new, clean object is created
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
        self.selects["ADRESATT"] = ["ADRESATT","KundenNr = KundenNr.ADRESSE"] 
        self.selects["ANFRAGE"] = ["ANFRAGE","KundenNr = KundenNr.ADRESSE"] 
        self.selects["Bez"] = []   
        self.selects["ARCHIV"] = ["ARCHIV","KundenNr = KundenNr.ADRESSE"] 
        self.selects["AUSGABE"] = ["AUSGABE","Modul = \"Adresse\""] 
        self.selects["BUCHUNG"] = ["BUCHUNG","KundenNr = KundenNr.ADRESSE"] 
        self.selects["FAHRTEN"] = ["FAHRTEN","KundenNr = KundenNr.ADRESSE"] 
        self.selects["FahrtKontakt"] = ["FAHRTEN","KontaktNr = KundenNr.ADRESSE"] 
        self.selects["FAHRTVOR"] = ["FAHRTVOR","KundenNr = KundenNr.ADRESSE"] 
        self.selects["FAHRER"] = ["FAHRER","FahrerNr = KundenNr.ADRESSE"] 
        self.selects["EINSATZ"] = ["EINSATZ","FremdNr = KundenNr.ADRESSE"] 
        self.selects["RECHNG"] = ["RECHNG","KundenNr = KundenNr.ADRESSE"] 
        self.selects["KVA"] = ["KVA","KundenNr = KundenNr.ADRESSE"] 
        self.selects["ANMELD"] = ["ANMELD","KundenNr = KundenNr.ADRESSE"] 
        self.selects["AnmeldAgent"] = ["ANMELD","AgentNr = KundenNr.ADRESSE"] 
        self.selects["EVENT"] = ["EVENT","AgentNr = KundenNr.ADRESSE"] 
        self.selects["VERBIND"] = ["VERBIND","KundenNr = KundenNr.ADRESSE"] 
        self.selects["SEPA"] = ["ARCHIV","KundenNr = KundenNr.ADRESSE AND Art = \"SEPA-DD\""] 
        if complete: self.create_selections()
        if self.debug: print(("AfpAdresse Konstruktor, KundenNr:", self.mainvalue))
    ## destructor
    def __del__(self):    
        if self.debug: print("AfpAdresse Destruktor")
    ## clear current SelectionList to behave as a newly created List 
    # @param KundenNr - if given, KundenNr address from where main data should be delivered   
    def set_new(self, KundenNr):
        self.new = True
        self._tmp = None
        if KundenNr and KundenNr != self.get_value("KundenNr"): 
            self.set_value("ParentNr._tmp", KundenNr)
        #print("AfpAdresse.set_new:", KundenNr, self._tmp) 
        data = {}
        keep = []
        self.clear_selections(keep)
        if KundenNr:
            Adresse = AfpAdresse(self.globals, KundenNr)
            data["Name"]  = Adresse.get_value("Name")
            data["Strasse"] =  Adresse.get_value("Strasse")
            data["Plz"]  = Adresse.get_value("Plz")
            data["Ort"]  = Adresse.get_value("Ort")
            data["Telefon"]  = Adresse.get_value("Telefon")
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
            #print ("AfpAdresse.spezial_selection:", self.selections["ADRESSE"].get_feldnamen())
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
                    while KNr !=  KundenNr and KNr != 0 and not KNr in self.spezial_bez:
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
            #print ("AfpAdresse.spezial_save data:", lgh, selection.data)
            if lgh > 0:
                KNr = int(self.mainvalue)
                bez_lgh = len(self.spezial_bez)
                for i in range(lgh):
                    KundenNr = KNr
                    index = -1
                    if KundenNr in self.spezial_bez: 
                        index = self.spezial_bez.index(KundenNr)
                        self.spezial_bez[index] = None
                    #print ("AfpAdresse.spezial_save KNr:", KundenNr, i, selection.get_values("KundenNr", i))
                    KN = selection.get_values("KundenNr", i)[0][0]
                    if KN:
                        KNr = int(KN)
                        self.mysql.write_update("ADRESSE", ["Bez"], [KNr], "KundenNr = " + Afp_toString(KundenNr), True)
                if KNr in self.spezial_bez: 
                    index = self.spezial_bez.index(KNr)
                    self.spezial_bez[index] = None
                self.mysql.write_update("ADRESSE", ["Bez"], [self.mainvalue], "KundenNr = " + Afp_toString(KNr))
            for KNr in self.spezial_bez:
                if KNr: self.mysql.write_update("ADRESSE", ["Bez"], ["0"], "KundenNr = " + Afp_toString(KNr))
    ## initialize data assumen to be not NULL\n
    def complete_data(self):
        if not self.get_value("Vorname"): self.set_value("Vorname","")
        if not self.get_value("Kennung"): self.set_value("Kennung",0)
        if not self.get_value("Geschlecht"): self.set_value("Geschlecht","n")
        if not self.get_value("Anrede"): self.set_value("Anrede","Sie")
    ## add a connection to "Bez" selection \n
    # @param KNr - address identifier for connection
    def add_connection(self, KNr):
        feldnamen = self.selections["ADRESSE"].get_feldnamen()
        Index = feldnamen.index("Bez")
        KNr = int(KNr)
        rows = self.get_mysql().select("*","KundenNr = " + Afp_toString(KNr), "ADRESSE") 
        mani = [None, rows[0]]       
        self.get_selection("Bez").manipulate_data([mani])
        # check for own connections of inserted address
        KundenNr = KNr
        KNr = int(rows[0][Index])
        if KNr:
            bez = []
            while KNr !=  KundenNr and KNr != 0 and not KNr in bez:
                if KNr < 0: KNr = - KNr
                rows = self.get_mysql().select("*","KundenNr = " + Afp_toString(KNr), "ADRESSE") 
                mani = [None, rows[0]]       
                self.get_selection("Bez").manipulate_data([mani])
                bez.append(KNr)
                KNr = int(rows[0][Index])   
        #print ("AfpAdresse.add_connection:", self.get_selection("Bez").data)
 
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
    ## return mayor type of this SelectionList,
    def get_mayor_type(self): 
        return "AfpAdresse"
    ## get short identifier of name \n
    # currently a trigram is used, first letter of surname plus first and second letter of lastname
    def get_short_name(self):
        vorname = self.get_string_value("Vorname")
        name = self.get_string_value("Name")
        return vorname[0].lower() + name[:2].lower()
    ## get attribut values of a given aatribut
    # @param attribut - if given name of extracted attributes
    def get_attributs(self, attribut=None):
        rows = self.get_selection("ADRESATT").get_values()
        if attribut:
            atts = []
            for row in rows:
                if row[2] == attribut:
                    atts.append(row)
            return atts
        else:
            return rows
    
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
            tables = victim.get_mysql().get_tables()
            # move through all selections and replace the values, if table is available in database
            for sel in selects:
                if victim.selects[sel] and victim.selects[sel][0] in tables and not (" AND " in victim.selects[sel][1]):
                    selection = victim.get_selection(sel)
                    target = victim.get_select_target(sel)
                    if selection and target:
                        selection.spread_value(target, KNr, True)
                        if sel in names:  selection.spread_value(names[sel], name, True)
                        if sel in debitors:  selection.spread_value(debitors[sel], debitor, True)
                        if sel in kreditors:  selection.spread_value(kreditors[sel], kreditor, True)
            # flag the address to be deleted
            victim.get_selection().delete_row()
            # write values to database
            if self.debug: print(("AfpAdresse.hostile_takeover:", victim.get_value(),"->", KNr))
            print("AfpAdresse.hostile_takeover:", victim.get_value(),"->", KNr)
            #victim.view()  
            victim.store()
    ## retrieve individual account from database
    # @param typ: defines which kind of account is selected \n
    # currently supported types are "Kreditor" and "Debitor"
    def get_account(self, typ = "Debitor"):
        account = Afp_getIndividualAccount(self.globals.get_mysql(), self.get_value("KundenNr"), typ)
        return account
    ## add a bank account to adresatt database
    # @param bic: BIC of bank account
    # @param iban: IBAN of bank account
    def add_bankaccount(self, bic, iban):
        found = False
        rows = self.get_value_rows("ADRESATT", "Attribut,Tag,Action")
        if rows:
            for row in rows:
                if row[0] == "Bankverbindung":
                    vals = row[1].split(",")
                    if vals[0] == iban: 
                        found = True
                        break
        #print("AfpAdresse.add_bankaccount:", iban, bic, found)
        if not found:
            values = {}
            values["KundenNr"] = self.get_value()
            values["Name"] = self.get_name()
            values["Attribut"] = "Bankverbindung"
            values["Tag"] = iban + "," + bic
            values["Aktion"] = "IBAN,BIC"
            self.set_data_values(values, "ADRESATT", -1)
    ## retrieve bank account(s) from database
    # @param typ: if given, defines which kind of account is selected \n
    # currently supported types are "SEPA" and "all"\n
    # return [[BIC, IBAN], ...] or []
    def get_bankaccounts(self, typ = None):
        accounts = []
        if typ == "SEPA" or typ == "all":
            # Gruppe = BIC, Bem = IBAN, Typ = Aktiv/Inaktiv
            rows = self.get_value_rows("SEPA", "Typ,Gruppe,Bem")
            if rows:
                for row in rows:
                    if row[0] == "Aktiv":
                        accounts.append([row[1], row[2]])
            if typ == "SEPA": return accounts
        rows = self.get_value_rows("ADRESATT", "Attribut,Tag,Action")
        if rows:
            for row in rows:
                if row[0] == "Bankverbindung":
                    vals = row[1].split(",")
                    names = row[2].split(",")
                    if len(vals) == len(names):
                        account = [None, None]
                        for name,val in names,vals:
                            if name == "IBAN":  account[1] = val
                            if name == "BIC":  account[0] = val
                        if typ == "all":   
                            accounts.append(account)
                        else:
                            return [account]
        return accounts
    ## add SEPA Direct Debit mandate 
    # @param fname - name of scan of mandat
    # @param datum - date when mandat has been signed
    # @param bic - BIC of client account for which mandat has been signed
    # @param iban - IBAN of client account for which mandat has been signed
    # @param client - if given, client data to be referenced
    def add_SEPA_mandat(self, fname, datum, bic, iban, client=None):
        if Afp_existsFile(fname) and client and datum and bic and iban:
            ext = fname.split(".")[-1]
            max = 1
            fpath = None
            if client:
                listname = client.get_listname()
                number = client.get_string_value() 
            else:
                listname = self.get_listname()
                number = selff.get_string_value() 
            while not fpath:
                if max < 10:  null = "0"
                else:  null = ""
                fresult = "SEPA" + "_" + listname + "_" + number + "_" + null + str(max) + "." + ext 
                fpath = Afp_addRootpath(client.get_globals().get_value("archivdir"), fresult)
                if Afp_existsFile(fpath):
                    max+= 1
                    fpath = None
            if self.debug: print("AfpAdresse.add_SEPA_mandat copy file:", fname, "to",  fpath)
            Afp_copyFile(fname, fpath)
            added = {}
            added["Art"] = "SEPA-DD"
            added["Typ"] = "Aktiv"
            added["Datum"] = datum
            added["Gruppe"] = bic
            added["Bem"] = iban
            added["Extern"] = fresult
            if client:
                added["Tab"] = client.get_tablename()
                added["TabNr"] = client.get_value()
                if client.get_value("AgentNr"):
                    added["KundenNr"] = client.get_value("AgentNr")
            added = self.set_archiv_data(added)
        else:
            print("WARNING: SEPA mandat not all data supplied:", fname, datum, bic, iban)

    ## deactivate  SEPA Mandat
    # it is assumed, that only one Mandat is active, 
    # otherwise all Mandats are deaktivated
    # @param store - flag if deactivation should be directly stored in the database
    def deactivate_SEPA(self, store=False): 
        newdata = {"Typ": "Inaktiv"}
        rows = self.get_value_rows("SEPA", "Typ,Gruppe,Bem")
        for i in range(len(rows)):
            if rows[i][0] == "Aktiv":
                self.set_data_values(newdata, "SEPA", i)
        if store:
            self.get_selection("SEPA").store()
            
    ## get values of active SEPA Mandat
    # return value, if no SEPA mandate is found: None
    # return value, if SEPA is found, but no active: {}
    def get_active_SEPA(self): 
        res = None
        rows = self.get_value_rows("SEPA", "Datum,Typ,Gruppe,Bem,Extern")
        if rows:
            res = {}
            for i in range(len(rows)):
                if rows[i][1] == "Aktiv":
                    res["Datum"] =  rows[i][0]
                    res["Gruppe"] =  rows[i][2]
                    res["Bem"] =  rows[i][3]
                    res["Extern"] =  rows[i][4]
                    break
        return res


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

