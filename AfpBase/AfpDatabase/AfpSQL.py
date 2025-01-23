#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpDatabase.AfpSQL
# AfpSQL module provides the connection to the MySql Interface,
# it holds the calsses
# - AfpSQL
# - AfpSQLTableSelection
#
#   History: \n
#        23 Jan. 2025 - AfpSQLTableSelection: allow reload with different order - Andreas.Knoblauch@afptech.de \n
#        29 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        04 Nov. 2018 - AfpSQL: add free execution of sql-statements - Andreas.Knoblauch@afptech.de \n
#        28 Mar. 2016 - AfpSQLTableSelection: add afterburner - Andreas.Knoblauch@afptech.de \n
#        14 Apr. 2015 - AfpSQLTableSelection: keep original values in modification - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de

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

import sys
import MySQLdb
import datetime
import base64

from AfpBase.AfpUtilities.AfpBaseUtilities import *
from AfpBase.AfpUtilities.AfpStringUtilities import *

##   provides a low level interface to MySql \n
# mostly not used directly, interaction takes place through the AfpSQLTableSelection objects
class AfpSQL(object):
    ## constructor
    # @param dbhost - host for database 
    # @param dbuser - user for connection
    # @param dbword - password for connection
    # @param dbname - name of database
    # @param debug - flag for debug output
    def  __init__(self, dbhost, dbuser, dbword, dbname, debug):
        self.dbname = dbname
        self.create_db = False
        #self.debug = True
        self.debug = debug
        self.db_connection = None
        self.db_cursor = None      
        self.db_connection = self.connect(dbhost,dbuser,dbword, self.dbname)
        self.db_cursor = self.db_connection.cursor()
        self.db_lastrowid = 0
        self.select_clause= None
        self.version = self.get_version()
        if self.debug: print("AfpSQL Konstruktor")
        if self.create_db: 
            try:
                self.execute("CREATE DATABASE " + self.dbname + ";")
                self.execute("USE " + self.dbname + ";")
                print("WARNING: AfpSQL database created:", self.dbname)
            except  MySQLdb.Error as e:
                print("ERROR %d in MySQL connection: %s" % (e.args[0], e.args[1]))
                if e.args[0] == 1044:
                    print("ERROR: MySQL-User has not the right privileges to create database! Please restart with administrative MySQL-User.")
                sys.exit (1)
    ## destructor
    def __del__(self):
        if self.db_cursor: self.db_cursor.close ()
        if self.db_connection: self.db_connection.close ()
        if self.debug: print("AfpSQL Destruktor")
    ## switch debug on
    def set_debug(self):
        #print "AfpSQL.set_debug()"
        self.debug = True
    ## turn debug off
    def unset_debug(self):
        #print "AfpSQL.unset_debug()"
        self.debug = False
    ## create connection to mysql database 
    # @param sql_host - host for database 
    # @param sql_user - user for connection
    # @param sql_word - password for connection
    # @param sql_db - name of database
    def connect(self, sql_host, sql_user, sql_word, sql_db):
        # connect to the MySQL server
        try:
            connection = MySQLdb.connect (host = sql_host,
                                          user = sql_user,
                                          passwd = base64.b64decode(sql_word).decode("UTF-8"),
                                          db = sql_db)
            if self.debug: print("AfpSQL connect:", sql_host, sql_user, sql_db)
        except MySQLdb.Error as e:
            print("ERROR %d in MySQL connection: %s" % (e.args[0], e.args[1]))
            if e.args[0] == 1049: 
                # unknown database, connect without database name, set flag for later creation
                try:
                    connection = MySQLdb.connect (host = sql_host,
                                                  user = sql_user,
                                                  passwd = base64.b64decode(sql_word).decode("UTF-8"))
                    print("WARNING: AfpSQL connect without database:", sql_host, sql_user)
                    self.create_db = True
                except MySQLdb.Error as e: 
                    print("ERROR %d in MySQL connection: %s" % (e.args[0], e.args[1]))
                    sys.exit (1)
            else:
                sys.exit (1)
        return connection 
    ## return debug flag
    def get_debug(self):
        return self.debug
    ## return database name
    def get_dbname(self):
        return self.dbname
    ## return database cursor
    def get_cursor(self):
        return self.db_cursor   
    ## return last used mysql select clause
    def get_select_clause(self):
        return self.select_clause
    ## return database version
    def get_version(self):
        Befehl = "SELECT VERSION()"
        if self.debug: print("AfpSQL.get_version:", Befehl)
        self.db_cursor.execute (Befehl)     
        rows = self.db_cursor.fetchall()
        return rows[0][0]
    ## return tables available in this database
    def get_tables(self):
        Befehl = "SHOW TABLES"
        if self.debug: print("AfpSQL.get_tables:", Befehl)
        self.db_cursor.execute (Befehl)     
        rows = self.db_cursor.fetchall()
        return Afp_extractColumns(0, rows)
    ## return information of database table
    # @param datei - name of table
    # @param typ - type of information ('fields' and 'index' implemented)
    # @param col_array - if given, array of colum indices to be extracted
    def get_info(self, datei, typ = "fields", col_array = None):
        if typ == "index":
            Befehl = "SHOW INDEX FROM " + datei
        else:
            Befehl = "SHOW FIELDS FROM " + datei
        if self.debug: print("AfpSQL.get_info:", Befehl)
        self.db_cursor.execute (Befehl)     
        rows = self.db_cursor.fetchall ()
        result = []
        if col_array:
            for col in col_array:
                result.append([])
                for row in rows:
                    if col >= 0 and col < len(row):
                        result[-1].append(row[col])
                    else:
                        result[-1].append(None)
        else:
            result = rows
        return result
    ## check if database has been created
    def database_created(self):
        return self.create_db
    ## extract different parts of the mysql select clause for  database access \n
    # returns a list holding:
    # - feld_clause: part of the clause indicating the desired columns of the tables
    # - dat_clause: part of the clause indicatindg the involved tables
    # - where_clause: part of the clause indicating the needed filter on the tables
    # - order_clause: part of the clause indicating the wanted order
    # - limit_clause: part of the clause setting the range of the query
    # @param feldnamen -  "*" for all fields or "field.table[.alias][, ...]" alias - of the concatination of fields
    # @param select         -  "field.table (>,<,>=,<=,==) value"
    # @param dateinamen  - "table[,...]" 
    # @param order          - "[column]" name of column
    # @param limit           - "[offset,number]" offset to select root, maximal number of rows extracted
    # @param  where         -  "[field1.table1 (>,<,>=,<=,==) (field2.table2,value)[(and,or) ...]]"
    # @param link            - "[field1.table1 == field2.table2 [and ...]]"
    def extract_clauses(self, feldnamen, select, dateinamen, order = None, limit = None, where=None, link=None):
        #print "AfpSQL.extract_clause:", feldnamen,'\n', select,'\n', dateinamen,'\n', order,'\n', limit,'\n',where,'\n',link
        if  feldnamen.strip() == "*": all_fields = True
        else: all_fields = False
        limit_clause = ""
        if not limit is None: limit_clause = limit
        dat_clause = ""
        if " " in dateinamen:
            dateien = dateinamen.split()
        else:
            dateien = dateinamen.split(",")
        lgh = len(dateien)
        if lgh == 1 and all_fields: no_indicator = True
        else: no_indicator = False
        for i in range(0,lgh):
            if dat_clause == "": komma = ""
            else: komma = ","
            if no_indicator:
                dat_clause += komma +  self.dbname + "." + dateien[i].upper() 
            else:
                dat_clause += komma +  self.dbname + "." + dateien[i].upper() + " D" + str(i)

        if all_fields:
            feld_clause = "*"
        else:
            feld_clause = ""      
            felder = feldnamen.split(",")
            concat = ""
            for feld in felder:
                if feld_clause == "": komma = ""
                else: komma = ", "
                if concat: komma = ",\" \", " 
                fld = feld.split(".")
                i = -1
                dat = ""
                cons = ""
                cone = ""
                connew = ""
                if len(fld) > 1 and not Afp_isFloatString(feld): 
                    if fld[1] in dateien: i = dateien.index(fld[1])
                    else: i = dateien.index(fld[1].upper())
                    if i > -1: dat = "D" + str(i) + "."
                    if len(fld) > 2: connew = fld[2]
                if not connew == concat:
                    if concat:
                        cone = ") AS " + concat
                        komma = ", "
                    if connew:
                        cons = "CONCAT("
                    concat = connew
                feld_clause += cone + komma + cons + dat + "`" + fld[0] + "`"
        order_clause = ""
        if not order is None:
            order_clause = Afp_SbToDbName(order, dateien)
        where_clause = ""
        if not select is None: 
            where_clause = Afp_SbToDbName(select, dateien)
        if not where is None: 
            where_clause += " and (" + Afp_SbToDbName(where, dateien) + ")"
        if not link is None: 
            where_clause += " and (" + Afp_SbToDbName(link, dateien) + ")"
        return [feld_clause, dat_clause, where_clause, order_clause, limit_clause]
    ## selects entries from the database \n
    # returns the selected value rows converted in strings
    # @param feldnamen -  "*" for all fields or "field.table[.alias][, ...]" alias - of the concatination of fields
    # @param select         -  "field.table (>,<,>=,<=,==) value"
    # @param dateinamen  - "table[,...]" 
    # @param order          - "[column]" name of column
    # @param limit           - "[offset,number]" offset to select root, maximal number of rows extracted
    # @param  where         -  "[field1.table1 (>,<,>=,<=,==) (field2.table2,value)[(and,or) ...]]"
    # @param link            - "[field1.table1 == field2.table2 [and ...]]"
    def select_strings(self, feldnamen, select, dateinamen, order = None, limit = None, where=None, link=None):
        rows = self.select( feldnamen, select, dateinamen, order, limit, where, link)
        string_rows = Afp_ArraytoString(rows)
        return string_rows
    ## selects entries from the database \n
    # returns the selected value rows.
    # @param feldnamen -  "*" for all fields or "field.table[.alias][, ...]" alias - of the concatination of fields
    # @param select         -  "field.table (>,<,>=,<=,=) value"
    # @param dateinamen  - "table[,...]" 
    # @param order          - "[column]" name of column
    # @param limit           - "[offset,number]" offset to select root, maximal number of rows extracted
    # @param  where         -  "[field1.table1 (>,<,>=,<=,=) (field2.table2,value)[(and,or) ...]]"
    # @param link            - "[field1.table1 == field2.table2 [and ...]]"
    def select(self, feldnamen, select, dateinamen, order = None, limit = None, where=None, link=None):      
        #if self.debug: print "AfpSQL.select:", feldnamen, select, dateinamen, order, limit, where, link
        clauses = self.extract_clauses(feldnamen, select, dateinamen, order, limit, where, link)
        Befehl = "SELECT "+ clauses[0] + " FROM " + clauses[1]  # feld_clause, dat_clause
        if not clauses[2] == "": Befehl += " WHERE "+ clauses[2]# where_clause 
        if not clauses[3] == "": Befehl += " ORDER BY "+ clauses[3] # order_clause 
        if not clauses[4] == "": Befehl += " LIMIT "+ clauses[4] # limit_clause 
        if self.debug: print("AfpSQL.select:",Befehl)
        #print ("AfpSQL.select:",Befehl)
        self.db_cursor.execute (Befehl)     
        rows = self.db_cursor.fetchall ()
        if self.debug: print("AfpSQL.select result:",rows)
        self.select_clause= Befehl
        return rows
    ## set a lock on the database table
    # @param datei - name of the table
    # @param select - select clause for locked database entries
    def lock(self, datei, select):
        Befehl = "SELECT * FROM "  + self.dbname + "." + datei + " WHERE "  + select + " LOCK IN SHARE MODE;"
        if self.debug: print("AfpSQL.lock:",Befehl)
        self.db_cursor.execute(Befehl)
    ## remove the lock from the table, rollback to database status befor the lock was set
    def unlock(self):
        Befehl = "ROLLBACK;"
        if self.debug: print("AfpSQL.unlock:", Befehl)
        self.db_cursor.execute(Befehl)
    ## return the las inserted database id
    def get_last_inserted_id(self):
        return self.db_lastrowid
    ## write data to database, if select is set use 'update' \n
    # for tables with a primary key
    # @param datei - name of table
    # @param felder - list of column names in table, where data is written to 
    # @param data - list of data rows, each written to the columns indicated above (nomally one row is delivered)
    # @param select - select clause for database entries to be updated (normally points to a unique entry)
    def write_unique(self, datei, felder, data, select):
        if select is None:
            self.write_insert(datei, felder, data)
        else:
            self.write_update(datei, felder, data, select)
    ## insert data into database
    # @param select_clause - select clause for database entries 
    # @param felder - list of column names in table, where data is written to 
    # @param data - list of data rows, each written to the columns indicated above (nomally one row is delivered)
    def write_no_unique(self, select_clause, felder, data):
        split_clause = select_clause.split(" FROM ")
        if len(split_clause) == 2:
            self.write_delete(select_clause)
            split_dat = split_clause[1].split(" WHERE ")
            dateien = split_dat[0].split(",")
            if len(dateien) > 1 : print("WARNING: AfpSQL.write_no_unique: multiple tables not yet possible!")
            datei = dateien[0].split(" ")[0]
            self.write_insert(datei, felder, data)
    ## delete data from database
    # @param select_clause - select clause for database entries to be deleted \n
    # "SELECT * FROM database.table WHERE ..."
    def write_delete(self, select_clause):
        split_clause = select_clause.split(" FROM ")
        if len(split_clause) == 2:
          # delete data from database
            Befehl = "DELETE FROM " + split_clause[1]
            if self.debug:  print("AfpSQL.write_delete Command:", Befehl)
            res = self.db_cursor.execute (Befehl)     
            self.db_cursor.execute("COMMIT;")
            if self.debug: print("AfpSQL.write_delete Deleted Rows:",res)
    ## update data in database, \n
    # for tables with a primary key
    # @param datei - name of table
    # @param felder - list of column names in table, where data is written to 
    # @param data - list of data rows, each written to the columns indicated above (nomally one row is delivered)
    # @param select - select clause for database entries to be updated (normally points to a unique entry)
    # @param no_commit - omit COMMIT statement at the end of this routine (if more database interactions should be done in one step)
    def write_update(self, datei, felder, data, select, no_commit= False):
        Befehl = None
        flen = len(felder)
        if len(data) == flen:
            set_clause =    (" SET %(set)s WHERE ") %   {"set"  : ",".join( [str(i)+"=%s" for i in felder] ) }
            Befehl =  "UPDATE " + self.dbname + "." + datei +  set_clause + select +";" 
        else:
            print("WARNING: AfpSQL.write_update: length data does not match number of fields (", flen, ",", len(data), ")") 
        if not Befehl is None:
            if self.debug: print("AfpSQL.write_update:", Befehl, "DATA:", data)
            self.db_cursor.execute (Befehl, data)
            if not no_commit: self.db_cursor.execute("COMMIT;")      
    ## insert data in database, 
    # @param datei - name of table
    # @param felder - list of column names in table, where data is written to 
    # @param data - list of data rows, each written to the columns indicated above
    def write_insert(self, datei, felder, data):
        Befehl = None      
        flen = len(felder)   
        if not "." in datei: datei = self.dbname + "." + datei
        for datarow in data:
            if len(datarow) == flen:
                value_clause =  (" ( %(items)s ) VALUES ( %(values)s );") %  {"items" : ",".join(felder), "values" : ",".join( ["%s"]*flen ) }
                Befehl = "INSERT INTO "  +  datei + value_clause 
                if self.debug: print("AfpSQL.write_insert:", Befehl, datarow)
                #print("AfpSQL.write_insert:", Befehl, datarow)
                self.db_cursor.execute (Befehl, datarow)
                self.db_lastrowid = self.db_cursor.lastrowid
            else:
                print("WARNING: AfpSQL.write_insert: length data does not match number of fields (", flen, ",", len(datarow), ")") 
        if not Befehl is None:
            self.db_cursor.execute("COMMIT;")
    ## direct execution of given mysql commands, retuns the returnvalue of the last command
    # @ param commands - given commands
    def execute(self, commands):
        retval = None
        if commands:
            befehle = commands.split(";")
            for befehl in befehle:
                if befehl:
                    if self.debug: print("AfpSQL.execute:", befehl + ";")
                    #print("AfpSQL.execute:", befehl + ";")
                    retval = self.db_cursor.execute(befehl + ";") 
                    if retval: retval = self.db_cursor.fetchall ()
                    #print "AfpSQL.execute:", befehl, retval
            #if not befehle is None:
                #self.db_cursor.execute("COMMIT;")
        return retval
        
## handles SQL-selections for one table
class AfpSQLTableSelection(object):
    ## initializes the object 
    # @param mysql - AfpSql object to handle database actions
    # @param tablename - name of table this is responsible for
    # @param debug - flag for debug output
    # @param unique_feldname - name of identifying column, if primary key exsists, otherwise None
    # @param feldnamen - names of columns, if not given they will be retrieved from database
    def  __init__(self, mysql, tablename, debug = False, unique_feldname = None, feldnamen = None):
        self.dbg = False # hardcode switch for storage logging
        #if tablename == "PREISE": debug = True
        if debug: 
            print("AfpSQLTableSelection Konstruktor dbg On:", tablename)
            print("AfpSQLTableSelection Konstruktor input:", tablename, debug, unique_feldname, feldnamen)
            self.dbg = True # hardcoded switch for storage logging, for debug purpose during programming
            #mysql.debug = True
        self.mysql = mysql      
        self.tablename = tablename
        self.feldnamen = feldnamen
        self.unique_feldname = unique_feldname 
        self.last_inserted_id = None
        self.select = None
        self.select_clause = None
        self.debug = debug
        self.new = False
        self.last_manipulation = None
        self.manipulation = []
        self.data = []
        self.afterburner = None
        if self.debug: print("AfpSQLTableSelection Konstruktor", self, self.tablename)
        if self.feldnamen is None:
            self.feldnamen = []
            db_cursor = self.mysql.get_cursor()
            db_cursor.execute ("SHOW FIELDS FROM " + self.tablename)
            rows = db_cursor.fetchall ()
            for row in rows:
                self.feldnamen.append(row[0])
    ## destructor
    def __del__(self):
        if self.debug: print("AfpSQLTableSelection Destruktor", self, self.tablename)
    ## return an initialized copy of this TableSelection
    #@param  unique_fieldname, if given, unique fieldname differring from the original TableSelection
    def create_initialized_copy(self, unique_fieldname=None):
        if self.debug: print("AfpSQLTableSelection.create_initialized_copy:",  unique_fieldname)
        if unique_fieldname is None: unique_fieldname = self.unique_feldname
        return AfpSQLTableSelection(self.mysql, self.tablename, self.debug, unique_fieldname, self.feldnamen)
   ## return an complete copy of this TableSelection
   # @param data - flag if data should be copied, default: True
   # @param mani - flag if manipulation data should be copied, default: False
    def create_complete_copy(self, data = True, mani = False):
        copy = self.create_initialized_copy()
        copy.select = self.select
        copy.select_clause = self.select_clause
        copy.new = self.new
        if mani:
            if self.last_manipulation:
                copy.last_manipulation = Afp_copyArray(self.last_manipulation)
            copy.manipulation = Afp_copyArray(self.manipulation)
        if data:
            copy.data = Afp_copyArray(self.data)
        return copy
    ## returns if data of this TableSelection has been deleted after last load or write
    # @param row - if given, index of row which should be checked
    def has_been_deleted(self, row = None):
        deleted = False
        if self.manipulation:
            for mani in self.manipulation:
                if mani[0] == "delete":
                    if row is None or row == mani[1]:
                        deleted = True
        return deleted
    ## returns if this TableSelection has been altered since last load or write
    # @param feld - if given it will be checked if this column has been changed
    # @param last - flag if manipulations before last storage should be checked
    def has_changed(self, feld = None, last = False):
        changed = False
        if last:
            manipulation = self.last_manipulation
        else:
            manipulation = self.manipulation
        if manipulation:
            changed = self.mani_has_changed(manipulation, feld)
        elif self.new: changed = True
        return changed
    ## returns if table selection holds no data
    def is_empty(self):
        empty = True
        if self.data:
            for row in self.data:
                for entry in row:
                    if entry:
                        empty = False
                        break
        return empty
    ## returns if given column has been set to last inserted id
    # @param feldname - name of column
    def is_last_inserted_id(self, feldname):
        flag = False
        if feldname in self.feldnamen:
            index = self.feldnamen.index(feldname)
            if self.last_inserted_id and self.data[0][index] == self.last_inserted_id:
                flag = True
        return flag
    ## sets given column  to last inserted id
    # @param feldname - name of column
    # @param row - index of row in this TableSelection
    def set_last_inserted_id(self, feldname, row = 0):
        if self.last_inserted_id and feldname in self.feldnamen:
            index = self.feldnamen.index(feldname)
            self.data[row][index] = self.last_inserted_id
            if self.dbg: print("AfpSQLTableSelection.set_last_inserted_id:", self.last_inserted_id, self.data[row][index], self.data)
    ## sets the data column in last row to indicated select criteria
    def set_select_criteria(self):
        # feld [<>=] integer
        if self.select:
            split = self.select.split(" ")
            feldname = split[0]
            if Afp_isNumeric(split[2]):
                value = int(split[2])
                last_index = self.get_data_length() - 1
                self.set_value(feldname, value, last_index)
    ## resets select criterium from last row
    def reset_select(self): 
        if self.debug: print("AfpSQLTableSelection.reset_select:", self.select)
        if self.select:
            split = self.select.split(" ")
            last_index = self.get_data_length() - 1
            self.select = "" 
            #print "AfpSQLTableSelection.reset_select split:", split
            for i in range(0, len(split), 4):
                if i: self.select += " " + split[i-1] + " "
                feldname = split[i]
                values = self.get_values(feldname, last_index)
                #print "AfpSQLTableSelection.reset_select value:", i, feldname, last_index,  values
                if split[i+1] == "=" and values:
                    value = Afp_toQuotedString(values[0][0], None)
                    self.select += feldname + " = " + value
                else:
                    self.select += split[i] +  " " + split[i+1] +  " " + split[i+2] 
        if self.dbg: print("AfpSQLTableSelection.reset_select out:", self.select)
    ## load data into TableSelection according to given select clause
    # @param select - select clause to identify desired data
    # @param order - if given desired order of output rows
    # @param limit - if given limitation of number of rows selected
    def load_data(self, select, order = None, limit = None):
        self.select = select  
        if self.dbg: print("AfpSQLTableSelection.load_data select:", self.tablename, self.select)
        #self.data = map(list, self.mysql.select("*",self.select, self.tablename, order)) # py2
        self.data = list(map(list, self.mysql.select("*",self.select, self.tablename, order, limit)))
        if self.dbg: print("AfpSQLTableSelection.load_data:", self.select, self.tablename, order, self.data)
        self.select_clause = self.mysql.get_select_clause()
        self.manipulation = []  
    ## reload data from database according to last load
    # @param order - if given desired order of output rows
    def reload_data(self, order = None):
        if self.dbg: print("AfpSQLTableSelection.reload_data:", self.select)
        if self.select: self.load_data(self.select, order)
    ## load data from given AfpSbDatei
    # @param datei - name of table
    # @param select - select clause for this  AfpSbDatei entry
    def load_datei_data(self, datei, select):  
        self.select = select
        if self.dbg: print("AfpSQLTableSelection.load_datei_data select:", self.select)
        values = datei.get_values()
        if values:
            self.data = list(map(list, [datei.get_values()]))
        else:
            self.data = [values]
        self.manipulation = []    
    ## attach input to data property
    # @param data - data to be attached
    # @param select - select clause for this  data
    def set_data(self, data, select=None):
        if self.dbg: print("AfpSQLTableSelection.set_data:", self.select, data, select)
        if select: self.select = select
        if data is None:
            self.data = None
        else:
            #self.data = map(list, data) # py2
            self.data = list(map(list, data)) 
    ## attach empty data
    # @param empty - flag if data should be comletely empty (true) or if one empty row should be inserted (false)
    # @param no_criteria - flag if selection criteria should be spread into new row (false) or not (true)
    def new_data(self, empty = False, no_criteria = False):
        self.new = True
        self.data = []
        if not empty: self.add_data_row(no_criteria)
    ## insert empy data row into data at given index
    # @param index - index where row should be inserted, if == None data will be added at the end
    # @param no_criteria - flag if selection criteria should be spread into new row (false) or not (true)
    def insert_data_row(self, index, no_criteria = False):
        data = []
        for feld in self.feldnamen:
            data.append(None)
        self.insert_row(index, data)
        if not no_criteria: self.set_select_criteria()
        if index is None: index = self.get_data_length() - 1
        return index
    ## add indicated data in a new row
    # @param index - index where data should be inserted, if == None data will be added at the end
    # @param row - data to be inserted
    def insert_row(self, index, row):
        if index is None:
            mani = [None, row]
        else:
            mani = [-index-1, row]
        #print "AfpSQLTableSelection.insert_row:", index, mani
        self.manipulate_data([mani])
    ## add empy data row to data
    # @param no_criteria - flag if selection criteria should be spread into new row (false) or not (true)
    def add_data_row(self, no_criteria = False):
        return self.insert_data_row(None, no_criteria)
    ## add indicated data in a new row
    # @param row - data to be inserted
    def add_row(self, row):
        self.insert_row(None, row)
  ## delete indicated row
    # @param row - index of row to be deleted
    def delete_row(self, row = 0):        
        #print "AfpSQLTableSelection.delete_row:", row, self.get_data_length()
        if row >= 0 and row < self.get_data_length():
            mani = [row, None]
            self.manipulate_data([mani])
    ## log manipulation of data
    # @param changes - indicator of changes made \n
    # \n
    # changes = [rowindex, values]: \n
    # - delete:  values  = None
    # - replace: values = {feld1: value1, ... }
    # - replace: values = [value1, value2, ...] , len == len(self.feldnamen)
    # - append: rowindex  == None and  values = [value1, value2, ...] , len == len(self.feldnamen)
    # - insert: rowindex  < 0 and  values = [value1, value2, ...] , len == len(self.feldnamen), rowindexrow will be mapped to index = -1 - rowindex
    def manipulate_data(self, changes):
        for entry in changes:
            if self.dbg: print("AfpSQLTableSelection.manipulate_data:", entry, type(entry[1]))
            index = entry[0]
            values = entry[1]
            originals = None
            typ = ""
            if type(values) == dict: typ = "dict"
            elif type(values) == list or  type(values) == tuple: typ = "list"
            action = "replace"
            if index is None:
                action = "append"
            elif index < 0:
                action = "insert" # type(values) == list
                index = -1 - index
            elif values is None:
                action = "delete"
            #if self.unique_feldname: index = 0
            if action == "delete":  # fill row into values to allow postprocessing, delete data row
                originals = self.data[index]
                del self.data[index]
                #print("AfpSQLTableSelection.manipulate_data deleted:", index, originals)
            elif action == "replace" and typ == "dict":
                originals = {}
                for key in values:
                    originals[key] = self.get_value(key, index)
                    self.set_value(key, values[key], index)
            elif action == "replace" and typ == "list" and len(values) == len(self.feldnamen):
                originals = self.data[index]
                self.data[index] = values
            elif action == "append"  and typ == "list" and len(values) == len(self.feldnamen):
                    self.data.append(values)
                    self.set_select_criteria()
            elif action == "insert"  and typ == "list" and len(values) == len(self.feldnamen):
                    self.data.insert(index, values)
                    self.set_select_criteria()
            else:
                print("ERROR: AfpSQLTableSelection.manipulate_data incorrect values:", action, typ)
            self.manipulation.append([action, index, originals, values])
    ## returns the original or the new value of the column in the actuel manipulation data, 
    # if no actuel manipulation data is present, the last manipulation data is schecked 
    # @param feld - it will be checked if this column has been changed
    # @param orig - flag if original or new value should be retrieved
    # @param row - if given, only look in this row
    def manipulation_get_value(self, feld, orig = False, row = None):
        manipulation = self.mani_get()
        if row is None:
            original, new = self.mani_get_values(manipulation, feld)
        else:
            original, new = self.mani_get_from_row(manipulation, feld, row)
        if orig:
            return original
        else:
            return new
    ## return actuel indices of manipulated rows
    def manipulation_get_indices(self):
        indices = []
        manipulation = self.mani_get()
        for mani in manipulation:
            if mani[0] == "delete":
                index = mani[1]
                for i in range(len(indices)):
                    if indices[i] > index:
                        indices[i] -= 1
                    elif indices[i] == index:
                        indices[i] = None
                indices.append(None)
            else:
                indices.append(mani[1])
        return indices
    ## return appropriate manipulation data,
    # if no actuel manipulation is available, the manipulation 
    # before last storage will be returned
    def mani_get(self):
        if self.last_manipulation and not self.manipulation:
            return self.last_manipulation
        else:
            return self.manipulation        
    ## returns the original and the changed value of the column in this  manipulation data \n
    # only used internally!
    # @param manipulation - manipulation data to be checked 
    # @param feld - it will be checked if this column has been changed
    # @param row - index of row from where values should be extracted
    def mani_get_from_row(self, manipulation, feld, row):
        index = None
        if feld in self.feldnamen:
            index = self.feldnamen.index(feld)
        entry = manipulation[row]
        original, value = self.mani_get_value_from_entry(entry, feld, index) 
        return original, value
    ## returns the original and the changed value of the column in this  manipulation data \n
    # only used internally!
    # @param manipulation - manipulation data to be checked 
    # @param feld - it will be checked if this column has been changed
    def mani_get_values(self, manipulation, feld):
        value = None
        original = None
        index = None
        if feld in self.feldnamen:
            index = self.feldnamen.index(feld)
        for entry in manipulation: 
            orig, value = self.mani_get_value_from_entry(entry, feld, index) 
            if original is None: original = orig
        return original, value
    ## returns the original and the changed value of one manipulation entry \n
    # only used internally!
    # @param entry - manipulation entry to be checked 
    # @param feld - name of field to be checked
    # @param index - index of field to be checked
    def mani_get_value_from_entry(self, entry, feld, index):
        original = None
        value = None
        values = entry[3]
        originals = entry[2]
        if type(values) == list:
            if not index is None:
                if values: value = values[index]
                if originals: original = originals[index]
        elif type(values) == dict:
            if feld in values: 
                value = values[feld]  
            if feld in originals:
                original = originals[feld]  
        return original, value
    ## returns if the given manipulation data holds changed entries \n
    # only used internally!
    # @param manipulation - manipulation data to be checked 
    # @param feld - if given it will be checked if this column has been changed
    def mani_has_changed(self, manipulation, feld = None):
        changed = False
        if manipulation:
            if feld is None:
                changed = True
            else:
                for entry in manipulation: 
                    values = entry[3]
                    if values is None or type(values) == list:
                        changed = True
                    elif type(values) == dict:
                        if feld in values: changed = True
        return changed
    ## return length of data list
    def get_data_length(self):
        return len(self.data)
    ## convinient methog for export
    def get_listname(self):
        return self.get_tablename()
    ## return name of responsible table
    def get_tablename(self):
        return self.tablename
    ## return list of column names
    def get_feldnamen(self):
        return self.feldnamen  
    ## return indices of given entries in the column name list
    # @param felder - column names separates by a colon (,)
    def get_feldindices(self, felder):
        split = felder.split(",")
        indices = []
        for feld in split:
            if feld in self.feldnamen:
                indices.append(self.feldnamen.index(feld))
            else:
                indices.append(None)
        return indices
    ## retrieve values of indicated columns
    # @param felder - if a colon separated list is given, the appropriate values are returned. None - all values are returned
    # @param row - index of row where values are extracted from. row < 0 values are extract from all rows
    def get_values(self, felder = None, row = -1):
        # felder == None: complete data, resp. row
        # felder == 'Name1, Name2, ...': data of columns Name1, Name2, ..., resp. only indicated row
        result = []
        if self.data:
            if felder is None:
                if row < 0:
                    result = self.data
                elif row < len(self.data):
                    result.append(self.data[row])
            else:
                split = felder.split(",")
                index = []
                for feld in split:
                    if feld.strip() in self.feldnamen: index.append(self.feldnamen.index(feld.strip()))
                    else: index.append(None)
                if self.data:
                    #print "AfpSQLTableSelection.get_values:",felder, split, index
                    #print "AfpSQLTableSelection.get_values:",self.data, self.feldnamen
                    #print "AfpSQLTableSelection.get_values feldnamen:", self.feldnamen
                    if row < 0:
                        for data in self.data:
                            result.append(Afp_extractPureValues(index,data))
                    elif row < len(self.data):
                        result.append(Afp_extractPureValues(index,self.data[row]))
        #print ("AfpSQLTableSelection.get_values result:",result)
        return result
    ## retrieve value of indicated column
    # @param feld - column name of indicated column
    def get_value(self, feld):
        wert = None
        rows = self.get_values(feld)
        #print "get_value", rows, type(rows)      
        if type(rows) == list:
            if len(rows) > 0 :
                row = rows[0] 
                if type(row) == list:
                    if len(row) > 0 : wert = row[0]
                else:
                    wert = row
        else:
            wert = rows
        return wert
    ## retrieve string representation of value of indicated column
    # @param feld - column name of indicated column
    def get_string_value(self, feld):
        string = Afp_toString(self.get_value(feld))
        return string
    ## retrieve one string (line) for each row
    # @param felder - colon separated list of column names
    def get_value_lines(self,  felder):
        lines = []
        rows = self.get_values(felder)
        for row in rows:
            lines.append(Afp_ArraytoLine(row))
        return lines
    ## retrieve complete data of this table selection
    def get_data(self):
        return self.data
    ## spread values of given column to column holding indicators for all rows
    # @param feldname - column name from where to get the value
    # @param indicator - column name where indeicators are found
    def spread_collection_indicators(self, feldname, indicator):
        lgh = self.get_data_length()
        cache = {}
        print ("AfpSQLTableSelection.spread_collection_indcators input:", feldname, indicator, lgh)
        for row in range(0,lgh):
            ind = self.get_values(indicator, row)[0][0] 
            if ind:
                if ind in cache:
                    value = cache[ind]
                else:
                    value = self.get_values(feldname, row)[0][0] 
                    cache[ind] = value
                print ("AfpSQLTableSelection.spread_collection_indcators:", row, ind, value, cache)
                if ind != value:
                    self.set_value(indicator, value, row)
    ## spread value of indicated column to all rows
    # @param feldname - indicated column name
    # @param value -  value to be filled in indicated column
    # @param replace -  if given, flag if value should be replaced, default: False
    def spread_value(self, feldname, value, replace = False):
        keep = not replace
        lgh = self.get_data_length()
        #print ("AfpSQLTableSelection.spread_value:", self.tablename, feldname, value, lgh)
        for row in range(0,lgh):
            #print ("AfpSQLTableSelection.spread_value row:", feldname, row, self.get_values(feldname, row))
            if keep and self.get_values(feldname, row)[0][0]: continue
            #print ("AfpSQLTableSelection.spread_value set:", feldname, row, "->", value)
            self.set_value(feldname, value, row)
        if self.select is None:
            #self.select =  feldname + " = " + Afp_toString(value)
            self.select =  feldname + " = " + Afp_toQuotedString(value, None)
    ## get index of first row with given value in column
    # @param value -  value to be found in indicated column
    # @param feldname - indicated column name
    def find_value_row(self, value, feldname):
        index = None
        feld = feldname.strip()
        if feld in self.feldnamen:  index = self.feldnamen.index(feld) 
        #print("AfpSQLTableSelection.find_value_row:", value, feldname, feld, index)
        if not index is None:
            for row in self.data: 
                #print("AfpSQLTableSelection.find_value_row row:", value, type(value), index, row[index], type(row[index]), value == row[index], row)
                if value == row[index]:
                    return row
                    break
        return None
    ## set indicated column to a given value
    # @param feldname - indicated column name
    # @param value -  value to be filled in indicated column
    # @param row -  index of row where value has to be inserted \n
    # if row points behind last datarow, a new datarow is attached and the value is inserted there
    def set_value(self, feldname, value, row = 0):
        if self.dbg: print("AfpSQLTableSelection.set_value:", feldname, value, type(value))#, self.feldnamen
        if row >= self.get_data_length() or (row == 0 and self.data[0] is None):
            row = self.add_data_row()
        if feldname in self.feldnamen:
            index = self.feldnamen.index(feldname)
            self.set_manipulation(feldname, row, value)
            self.data[row][index] = value
    ## set data values from given dictionary
    # @param changed_data - dictionary holding appropriate value in entry [column name]
    # @param row -  index of row where values have to be inserted 
    def set_data_values(self, changed_data, row = 0):
        if self.dbg: print("AfpSQLTableSelection.set_data_values:", changed_data, row)
        for data in changed_data:
            self.set_value(data, changed_data[data], row)
    ## add a row with data values from given dictionary
    # @param changed_data - dictionary holding appropriate value in entry [column name]
    def add_data_values(self, changed_data):
        row = self.add_data_row(True)
        self.set_data_values(changed_data, row)
    ## set or if already set, reset manipulation entry
    # @param feldname - name of column
    # @param row - index of row
    # @param value - value to be set
    def set_manipulation(self, feldname, row, value):
        add = True
        for mani in self.manipulation:
            if mani[0] == "replace" and mani[1] == row:
                mani[3][feldname] = value
                add = False
                break
        if add:
            original = self.get_values(feldname, row) 
            if original[0]:
                original = original[0][0]
            else:
                original = ""
            self.manipulation.append(["replace", row, {feldname: original}, {feldname: value}])
    ## set a lock on database table according to actuel select clause
    def lock_data(self):
        self.mysql.lock(self.tablename,  self.select)
    ## unlock database table and rollback
    def unlock_data(self):
        self.mysql.unlock()
    ## add formula to afterburner, to be executed after storage
    # @param form - formula to be evaluated after storage
    def add_afterburner(self, form):
        if form: 
            if self.afterburner is None:
                self.afterburner = [form]
            else:
                self.afterburner.append(form)
     ## execute formulas of afterburner
    def execute_afterburner(self):
        if self.afterburner:
            for form in self.afterburner:
                if "=" in form:
                    split = form.split("=")
                    vars, signs = Afp_splitFormula(split[1])
                    #print "execute_afterburner:", form, vars, signs
                    vals = []
                    for var in vars:
                        vals.append(var)
                    for row in range(self.get_data_length()):
                        for i in range(len(vars)):
                            if not Afp_hasNumericValue(vars[i]):
                                vals[i] = Afp_toString(self.get_values(vars[i], row)[0][0])
                        #print "execute_afterburner vals:", vals, signs
                        formula = ""
                        for i in range(len(vals)-1):
                            formula += vals[i] + signs[i]
                        formula += vals[-1]
                        if len(signs) == len(vals):
                            formula += signs[-1]
                        #pyBefehl = "value = " + formula
                        #exec(pyBefehl)
                        value = eval(formula)
                        self.set_value(split[0].strip(), value, row),
                        if self.dbg: print("AfpSQLTableSelection.execute_afterburner:", formula, "       Row:", row, split[0], "=", value)
                        #print "execute_afterburner:", pyBefehl, "\nRow:", row, split[0], "=", value,  type(value) 
                else:
                    pyBefehl = form
                    exec(pyBefehl)
                    if self.dbg: print("AfpSQLTableSelection.execute_afterburner:", pyBefehl)
            self.afterburner = None
    ## write attached data to database
    def store(self):
        # writes data hold directly in this SelectionTable
        if self.dbg: print("AfpSQLTableSelection.store:",self.tablename, self.unique_feldname)
        if self.unique_feldname:
            for row in range(self.get_data_length()):
                unique_value = self.get_values(self.unique_feldname, row)[0][0]
                if not unique_value:
                    if self.dbg: print("AfpSQLTableSelection.store unique new value:", self.last_inserted_id, self.get_values(None, row)[0])
                    #print "AfpSQLTableSelection.store unique new value:", self.last_inserted_id, self.get_values(None, row)[0]
                    self.mysql.write_insert( self.tablename, self.feldnamen, self.get_values(None, row))
                    self.last_inserted_id = self.mysql.get_last_inserted_id() 
                    if self.dbg: print("AfpSQLTableSelection.store unique last_inserted_id:",  self.last_inserted_id)
                    self.set_last_inserted_id(self.unique_feldname, row)
                else:
                    select = self.unique_feldname + " = " + Afp_toQuotedString(unique_value)
                    if self.dbg: print("AfpSQLTableSelection.store unique value already set:", select, self.get_values(None, row)[0])
                    self.mysql.write_unique( self.tablename,  self.feldnamen, self.get_values(None, row)[0], select)  
            if self.get_data_length() == 0:
                # check if data has been deleted
                if self.has_been_deleted():
                    if self.dbg: print("AfpSQLTableSelection.store delete unique:", self.select_clause)
                    self.mysql.write_delete(self.select_clause)
        else:
            new = False 
            if self.select_clause is None: 
                new = True
            else:
                if self.dbg: print("AfpSQLTableSelection.store manipulation:", self.manipulation)
                if self.dbg: print("AfpSQLTableSelection.store data:", self.data)
                #if self.manipulation:
                    #new = True
                    #for mani in self.manipulation:
                        #if not mani[0] == "insert": new = False
            if self.dbg: print("AfpSQLTableSelection.store new:", new, self.new)
            if new or self.new:
                if self.dbg: print("AfpSQLTableSelection.store insert:", self.get_values())
                self.mysql.write_insert( self.tablename, self.feldnamen, self.get_values())
            else:
                if self.dbg: print("AfpSQLTableSelection.store no_unique:", self.select_clause, self.get_values())            
                self.mysql.write_no_unique(self.select_clause, self.feldnamen, self.get_values())
            self.reset_select()
            self.reload_data()
        self.new = False
        self.last_manipulation = self.manipulation
        self.manipulation = []
        if self.afterburner: 
            self.execute_afterburner()
            if self.select_clause is None and self.select:
                self.select_clause = "SELECT * FROM " + self.tablename + " WHERE " + self.select
            if self.dbg: print("AfpSQLTableSelection.store afterburner:", self.manipulation, self.select, self.select_clause)
    
    # end of AfpSQL
      
