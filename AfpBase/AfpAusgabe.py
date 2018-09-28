#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpAusgabe
# AfpAusgabe module provides the capabillity to read and complete flavoured text files
# currently it work on flat (plain xml) odt files (.fodt)
# it holds the class
# - AfpAusgabe
#
#   History: \n
#        27 Jan. 2015 - correct condition evaluation- Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        17 Mar. 2013 - inital code generated - Andreas.Knoblauch@afptech.de
#
# The following regulations apply: \n
#
# {} and [] brackets are used to flavour text and must not be used otherwise in the textfiles \n
# {} are function brackets holding WHILE and IF,ELSE statements  \n
# []  are database-fields or variable brackets, values inside will be evaluated or retrieved and 
#      the result will be positioned in the file instead \n
#
# the following different possibilites are implemented: \n
# []: \n
# [Zielort.Reisen]  :  the entry 'Zielort' from the table 'Reisen' will be set at that position \n
# [Vorname.Adresse,Name.Adresse] : both entries will be retrieved from the database and set to this position, a blank between them \n
# [Summe+=Preis.Anmeld] : the entry 'Preis.Anmeld' will be retrieved an added to the variable 'Summe', 'Preis.Anmeld' will be displayed \n
#                                            works the same with '-=' \n
# [Summe] : the variable 'Summe' will be set at this position \n
# [(Summe-Anzahlung)] : the evaluated value of the variable 'Summe' and the variable 'Anzahlung' will be set at this position \n
#
# {}: \n
# {IF Transfer.Anmeld} : this  line will be added to output if 'Transfer.Anmeld'  evaluates to 'True' (holds a value either  != 0.0 or != "") \n
# {IF Preis.AnmeldEx &gt; 0.0} :  this line will be added to output if 'Preis.AnmeldEx > 0.0' evaluates to 'True' \n
#                                                    works the same with &lt; (<),  == and != \n
# {ELSE IF} in line following a line with IF : this line will be added to outout if previous IF evaluates to False and phrase following IF evaluates to 'True' \n
# {ELSE} in line following a line with  IF or ELSE IF : this line will be added to outout if previous IFs all evaluate to 'False' \n
#                                           

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

import StringIO
import zipfile

import AfpUtilities
from AfpUtilities import *
from AfpUtilities.AfpStringUtilities import *
from AfpUtilities.AfpBaseUtilities import *

import AfpBaseRoutines
from AfpBaseRoutines import *
  
## main class to handle document output   
class AfpAusgabe(object):
    ## Constructor
    # @param debug - flag for debug information
    # @param data - if given, AfpSelectionList holding data where output is created from
    def  __init__(self,  debug = False, data = None):
        self.data = data
        self.filecontent = None
        self.debug = debug
        self.tempfile = StringIO.StringIO()
        #self.tempfile = tempfile.NamedTemporaryFile('w')
        #self.tempfile = open("/tmp/AfpTemp.txt", 'w') 
        self.execute_else= None
        self.while_clauses = []
        self.line_stack = [[]]
        self.stack_index = 0
        self.index_stack = [0]
        self.variables = {}
        self.values = {}
        if self.debug: print "AfpAusgabe Konstruktor" 
    ## Destruktor      
    def __del__(self):
        if self.debug: print "AfpAusgabe Destruktor"
    ## attach file which holds data to be used to inflate the flavoured text-file, \n
    # this may be used if no direct access to a mysql database is possible, only works if no data is given (self.data is None)
    # (used by the -d option of the commandline call)
    # @param filename - path to file to be loaded
    def set_data(self, filename):
        if self.data is None: 
            fin = open(filename, 'r') 
            self.filecontent = fin.readlines()
    ## check if line is part of a 'while' statement \n
    # output:  0- no while, 1- start, 2- end
    # @param line - line to be analysed
    def is_while(self, line):
        while_flag = 0
        action, netto= Afp_between(line,"{","}")
        if len(action) == 1:
            if action[0][:5] == "WHILE":
                if action[0] == "WHILE END":
                    while_flag = 2
                else:
                    while_flag = 1
        #else:
            #print "is_while:",action, netto
        return while_flag
    ## main method for reading an analysing flavoured file,
    # inflate the given file with data \n
    # - the file is read here, WHILEs are handeled here 
    # - other options are delegated
    # @param filename - path to flavoured file
    def inflate(self, filename):
        if self.data is None:
            self.load_values_from_data()
        fin = open(filename, 'r') 
        #self.line_stack.append([])
        self.line_stack = [[]]
        for line in fin:
            if self.debug: print "AfpAusgabe.inflate:", line
            line = self.correct_line(line)
            is_while = self.is_while(line)
            if is_while == 1:
                # start of new while loop
                self.line_stack[self.index_stack[-1]].append(line)
                self.stack_index += 1
                self.index_stack.append(self.stack_index)
                self.line_stack.append([])
                #print line
            elif is_while == 2:
                # end of while loop
                #print line
                if self.index_stack[-1] > 0:
                    self.index_stack.pop()
                    if self.index_stack[-1] == 0:
                        # back to root, execute while stack
                        #print "AfpAusgabe.inflate 0:", len(self.line_stack), "1"
                        #print "AfpAusgabe.inflate:", self.line_stack
                        self.execute_while(self.line_stack[0][0], 1)
                        # whiles executed, clear stack
                        self.line_stack = [[]]
                        self.stack_index = 0
                        self.index_stack = [0]
            else:
                if self.index_stack[-1] > 0:
                    # in while loop, add line to stack
                    self.line_stack[self.index_stack[-1]].append(line)
                else:
                    # outside whiles, direct execution
                    self.execute_line(line)
        fin.close()
    ## correct line, no '<>' brackets in execution brackets '[]', '{}'
    # @paream line - line to be corrected
    def correct_line(self, line):
        if "[" in line:
            line = self.move_xml_tags(line, "[","]")
        if "{" in line:
            line = self.move_xml_tags(line, "{","}")
        return line
    ## move xml tags out of given brackets
    # @param line - line, where tags should be moved
    # @param start - open brackets identifier
    # @param end - close brackets identifier
    def move_xml_tags(self, line, start, end):
        insides, outsides = Afp_between(line, start, end)
        oplus = len(outsides) - len(insides)
        if oplus: newline = outsides[0]
        else: newline = ""
        for i in range(len(insides)):
            entry = insides[i]
            insi, inso = Afp_between(entry, "<", ">")
            if insi:
                inside = ""
                infront = ""
                behind = ""
                for ins in inso:
                    inside += ins
                for ins in insi:
                    if ins[0] == "/":
                        behind += "<" + ins + ">"
                    else:
                        infront += "<" + ins + ">"
                entry = infront + start + inside + end + behind
            else:
                entry = start + entry + end
            newline += entry + outsides[i+oplus]
        return newline
    ## execute lines except WHILE statements \n
    # {IF,ELSE statement} ... and proper lines will be handled \n
    # - IF,ELSE statements are handles here, \n
    # - line evaluation is deligated
    # @param line - line to be analysed
    def execute_line(self,line):
        action, netto= Afp_between(line,"{","}")
        #print "AfpAusgabe.execute_line:", action, netto
        if len(action) == 1:
            condition = False
            if action[0][0:2] == "IF":
                phrase = action[0][3:].strip()
                condition = self.evaluate_condition(phrase)
                if condition:
                    self.write_line(netto)
                else:
                    self.execute_else = True
            elif action[0][0:4] == "ELSE" and self.execute_else:
                if len(action[0]) > 6 and action[0][5:7] == "IF":
                    phrase = action[0][6:].strip()
                    condition = self.evaluate_condition(phrase)
                    if condition:
                        self.write_line(netto)
                else:
                    self.write_line (netto)
        else:
            self.write_line([line])
    ## handle proper line evaluation including []-phrases and write line to temporary file \n
    # input may be given as list, that is interpreted as one line
    # @param lines - parts of one line to be analysed
    def write_line(self, lines):
        self.execute_else = None
        if len(lines) == 1:
            line = lines[0]
        else:
            line = ""
            for ln in lines: line+= " " + ln.strip()
            line = line.strip()
        fields,netto = Afp_between(line, "[", "]")
        line = self.concat_line(fields, netto)
        #print line
        #self.tempfile.write(line.encode("UTF-8")  +'\n')
        self.tempfile.write(line.encode("UTF-8"))
    ## replace variables with datavalues and concatinate to one line \n
    # if len(netto) > len(fields), the first netto value is placed at the start of the line \n
    # line = [netto] + fields + netto + fields + ... + netto
    # @param fields - variables to be replaced by data-values
    # @param netto - plain text to be placed between data-values
    def concat_line(self, fields, netto):
        line = ""
        if len(netto) > len(fields): 
            for i in range(len(fields)):
                line += netto[i].decode("UTF-8")  + self.gen_value(fields[i])
            line += netto[-1].decode("UTF-8") 
        else:
            for f,n in fields,netto:
                line += self.gen_value(f) + n.decode("UTF-8") 
        return line
    ## generate the values stated in []-phrases \n
    # fields, variables, list of fields are handled here \n
    # function and fromula evaluation is deligated \n
    # value output is a string
    # @param fields - variables to be replaced by data-values
    def gen_value(self, fields):
        if "=" in fields:
            value = Afp_toString(self.gen_function(fields))
        elif "(" in fields and ")" in fields:
            form, netto = Afp_between(fields,"(",")")
            #print form
            value = Afp_toString(self.evaluate_formula(form[0]))
        else:
            split = fields.split(",")
            value = ""
            for field in split:
                #print  "AfpAusgabe.gen_value field:", field, self.values 
                #print  "AfpAusgabe.gen_value DATA:", self.data.view()
                if not field in self.values:
                    self.values[field] = self.retrieve_value(field)
                value += " " + Afp_toString(self.values[field])
        #print "AfpAusgabe.gen_value value:", fields, value
        return value.strip()
    ## handles different function evaluations \n
    # assignments (= , +=, -=) are handled here \n
    # fromula evaluation in ()-prarantheses is deligated
    # @param funct - function to be evaluated
    def gen_function(self, funct):
        if "+=" in funct : sign = "+="
        elif "-=" in funct : sign = "-="
        else: sign = "="
        split = funct.split(sign) 
        var = split[0]
        form, field = Afp_between(split[1],"(",")")
        #print form, field
        if len(form) > 0: value = self.evaluate_formula(form[0])
        else: value = self.get_value(field[0])
        value = Afp_toString(value)
        if not var in self.values:
            self.values[var] = 0.0
        pyBefehl = "self.values[var]" + sign + value
        exec pyBefehl      
        return value
    ## evaluates a written condtion and returns the appropriate boolean value
    # @param phrase - phrase which holds condition to be evaluated
    def evaluate_condition(self, phrase):
        condition = False
        phrase = phrase.replace("&gt;",">")
        phrase = phrase.replace("&lt;","<")
        phrase = phrase.replace("&apos;","\"")
        sign = ""
        if ">" in phrase: sign = ">"
        elif "<" in phrase: sign = "<"
        elif "!" in phrase: sign = "!"
        if "=" in phrase: 
            if "==" in phrase:sign = "=="
            else: sign += "="
        if sign: 
            split = phrase.split(sign)
            split[0] = split[0].strip()
            if self.in_values(split[0] ): phrase = Afp_toQuotedString(self.values[split[0]], True)
            else: phrase = split[0].decode("UTF-8")
            phrase += sign
            split[1] = split[1].strip() 
            if self.in_values(split[1] ): phrase += Afp_toQuotedString(self.values[split[1]], True)
            else: phrase += split[1].decode("UTF-8")
        else: 
            if self.in_values(phrase): phrase = Afp_toQuotedString(self.values[phrase], True)
            else: phrase = "None"
        pyBefehl = "condition = bool(" + phrase + ")"
        #print "AfpAusgabe.evaluate_condition pyBefehl:", pyBefehl
        exec pyBefehl
        if self.debug: print "AfpAusgabe.evaluate_condition:", pyBefehl, condition
        return condition
    ## evaluate formulas in ()-prantheses \n
    # all python evaluations are allowed, 
    # as the formula is evaluated via the 'exec' command
    # @param form - formula to be evaluated
    def evaluate_formula(self, form):
        vars, signs = Afp_splitFormula(form)
        #print "AfpAusgabe.evaluate_formula:", vars, signs, self.is_date_formula(vars)
        if self.is_date_formula(vars):
            # special handling for date formulas
            value = self.evaluate_date_formula(vars, signs[0])
            if self.debug: print "evaluate_formula:", form, value
        else:
            # handling for all other formulas
            for i in range(len(vars)):
                if not Afp_hasNumericValue(vars[i]):
                    vars[i] = Afp_toString(self.get_value(vars[i]))
                    if not vars[i]: vars[i] = "0"
            formula = ""
            for i in range(len(vars)-1):
                formula += vars[i] + signs[i]
            formula += vars[-1]
            if len(signs) == len(vars):
                formula += signs[-1]
            pyBefehl = "value = " + formula
            #print "AfpAusgabe.evaluate_formula Befehl:", form, pyBefehl, vars, self.values
            exec pyBefehl
            if self.debug: print "AfpAusgabe.evaluate_formula:", form, pyBefehl, value
        return value
    ## executes a while loop, may be called recursive for nested loops \n
    # @param while_line - holds the while conditions
    # @param stack_index - index of the lines in this while loop in self.line_stack
    # @param file_index - current index of the line in datafile
    def execute_while(self, while_line, stack_index, file_index = 0):  
        indices = None
        while_clause, feldnamen, dsnamen, function = self.while_input(while_line, stack_index)
        if self.data is None:
            rows, indices = self.extract_rows_from_file(feldnamen, while_clause, file_index)
        else:
            if while_clause:
                rows = self.data.mysql.select(feldnamen, while_clause, dsnamen) 
            else:
                rows = self.extract_rows_from_data(dsnamen, feldnamen)            
            #print "AfpAusgabe.execute_while rows:", len(rows), self.data, while_clause
            #print "AfpAusgabe.execute_while rows:", len(rows), "\n", rows
        felder = feldnamen.split(",")
        local_lines = self.line_stack[stack_index]
        if function:
            var, function = Afp_getFuncVar(function)
            if var is None:
                function = None
            elif not var in self.values:
                self.values[var] = 0.0
        lgh = len(rows)
        for i in range(lgh):
            row = rows[i]
            #print felder
            #print row
            for feld,wert in zip(felder,row):
                self.values[feld] = wert
            if function: self.values[var] = self.evaluate_formula(function)
            if self.debug: print "AfpAusgabe.execute_while WHILE:", stack_index,"Row:", i
            #print local_lines
            for line in local_lines:
                if self.debug: print "Linie", local_lines.index(line)
                #print line
                if self.is_while(line) == 1:
                    # start of new while loop
                    if self.debug: print "NEW WHILE:", stack_index + 1, "stack length",len(self.line_stack)
                    if indices is None:
                        self.execute_while(line, stack_index + 1)
                        if self.debug: print "END NEW WHILE"
                    else:
                        self.execute_while(line, stack_index + 1, indices[i])
                        if self.debug: print "END NEW WHILE"
                else:
                    if self.debug: print "execute linie", local_lines.index(line), "of WHILE", stack_index
                    self.execute_line(line)
    ## analyses the while_line, \n
    # extracts the while_clause, fields, tables and optional the function
    # @param while_line - holds the while conditions
    # @param stack_index - index of the lines in this while loop in self.line_stack
    def while_input(self, while_line, stack_index):
        #print "AfpAusgabe.while_input input:", while_line, stack_index, self.line_stack
        function = ""
        datsels = ""
        action, netto =  Afp_between(while_line,"{","}")
        if len(action) == 1 and action[0][:5] == "WHILE":
            split_func = action[0].split("FUNCTION")
            if len(split_func) == 2:
                # extract function
                funct, netto =  Afp_between(split_func[1],"(",")")
                #print split_func
                #print funct, netto
                function = funct[0]
            # extract where clause for database access
            clause = split_func[0][6:]
            if clause[:7] == "ROWS IN":
                clause = clause[8:]
                if "AS" in clause:
                    split = clause.split("AS")
                    datsels = split[0].strip()
                    clause = ""
            else:
                fields, netto = Afp_between(clause,"[","]")
                clause = self.concat_line(fields, netto)
                clause = clause.replace(":","and")
            # get needed fileds from lines 
            felder = []
            if function: felder += Afp_getWords(function,".")
            for line in self.line_stack[stack_index]:
                fields, netto =  Afp_between(line,"[","]")
                for field in fields: 
                    split = field.split(",")
                    if len(split) > 1:
                        for sp in split:
                            if not sp in felder: felder.append(sp)
                    elif "(" in field:
                        fld, netto =  Afp_between(line,"(",")")
                        split = Afp_split(fld[0],["+","-"])
                        for spl in split:
                            if not spl in felder: felder.append(spl)
                    elif "=" in field:
                        split = field.split("=")
                        if len(split) == 2:
                            if not split[1] in felder: felder.append(split[1])
                    else:
                        if not field in felder: felder.append(field)
            dats= []
            feldnamen = ""
            for feld in felder:
                split = feld.split(".")
                if  len(split) > 1:
                    if clause and not split[1] in dats:
                        dats.append(split[1])
                        datsels += ","+ split[1]
                feldnamen += "," + feld
            if len(feldnamen) > 1: feldnamen = feldnamen[1:]
            # extract possible tables from clause which are not included in feldnamen
            if clause:
                if len(datsels) > 1: datsels = datsels[1:]
                split = clause.split()
                for word in split:
                    if "." in word and Afp_floatString(word, None) is None:
                        sp = word.split(".")
                        if len(sp) > 1:
                            if not sp[1] in dats:
                                dats.append(sp[1])
                                datsels += "," + sp[1]
        #print "AfpAusgabe.while_input output:", clause, feldnamen, datsels, function
        if self.debug: print "AfpAusgabe.while_input CLAUSE:", clause, "FIELDS:", feldnamen, "TABLES:", datsels, "FUNCT:", function
        return clause, feldnamen, datsels, function
    ## retrieve value from cache, possibly load into cache first
    # @param fieldname - name of database column to be loaded
    def get_value(self, fieldname):
        if self.in_values(fieldname):
            return self.values[fieldname]
        else:
            return None
    ## check if value exists in cache, possibly load value into cache
    # @param fieldname - name of database column to be loaded
    def in_values(self, fieldname):
        #print "AfpAusgabe.in_values", fieldname
        if fieldname in self.values:
            return True
        else:
            wert = self.retrieve_value(fieldname)
            #print "AfpAusgabe.in_values retrieve", fieldname, wert
            if not wert is None: 
                self.values[fieldname] = wert
                return True
        return False
    ## retrieve value from database (values from file are loaded once at start)
    # @param fieldname - name of database column to be loaded
    def retrieve_value(self, fieldname):
        val = None
        if Afp_isPlainString(fieldname):
            if self.data is None:
                print "WARNING: value for", fieldname, "not delivered in datafile"
            else:
                val = self.data.get_ausgabe_value(fieldname)
        #print "AfpAusgabe.retrieve_value:", fieldname,":",val
        return val
    ## load values from input file into data cache
    def load_values_from_data(self):
        lgh = len(self.filecontent)
        i = 0
        line = self.filecontent[0]
        while i < lgh and not line[:3] == "   " and not line[:5] == "WHILE":
            name, value = self.get_feld_name_value(line)
            self.values[name] = value
            i += 1
            if i < lgh:
                line = self.filecontent[i]
    ## read block of rows from datafile
    # @param selname - names of selection where values to be extracted from
    # @param feldnamen - names of values to be extracted
    def extract_rows_from_data(self, selname, feldnamen):
        rows = []
        if self.data:
            rows = self.data.get_grid_rows(selname) 
        return rows
   ## read block of rows from datafile
    # @param feldnamen - names of values to be extracted
    # @param while_clause - possible while clause in this row
    # @param index - startindex of first row-block in data
    def extract_rows_from_file(self, feldnamen, while_clause, index):
        #print "extract", index, while_clause
        rows = []
        indices = []
        data_lgh = len(self.filecontent)
        line = self.filecontent[index].strip()
        # look for while-clause
        while not line[:5] == "WHILE" and not line[6:] == "\""+ while_clause + "\"":
            index += 1
            #print index, line
            line = self.filecontent[index].strip()
        # while clause found set index to next line
        index += 1
        line = self.filecontent[index]     
        spcnt = Afp_leftSpCnt(line)
        cnt = spcnt
        i = index
        values = {}
        skip = False
        newline = False
        while (cnt >= spcnt or newline) and i < data_lgh:
            #print i+1, newline, skip
            if newline and not skip and not i+1 == data_lgh:
                # end of block, fill in rows
                row = []
                felder = feldnamen.split(",")
                for feld in felder: 
                    row.append(values[feld])
                rows.append(row) 
                indices.append(index)   
                index = i + 1
            elif not (skip or newline):
                # fill values
                name, value = self.get_feld_name_value(line)
                #print name, value
                if not name is None: values[name] = value
            i += 1
            if i < data_lgh - 1:
                line = self.filecontent[i]
                newline = Afp_isNewline(line)
                if not newline:
                    cnt = Afp_leftSpCnt(line)
                    if cnt > spcnt: skip = True
                    elif cnt == spcnt: skip = False
        return rows, indices
    ## extract value names and values from line
    # @param line - line to be analysed
    def get_feld_name_value(self, line):
        name = None
        value = None
        valuestring = None
        #print line
        if "=" in line:
            split = line.split("=")
            #print split, len(split)
            if len(split) == 2:
                ssplit = split[0].split("\"")
                name = ssplit[1]
                if "\"" in split[1]:
                    ssplit = split[1].split("\"")
                    valuestring = ssplit[1].strip()
                else:
                    valuestring = split[1].strip()
                value = Afp_fromString(valuestring)
        return name,valuestring
    ## check if given variables represent a formual where dates are involved
    # @param vars - variables for formula
    def is_date_formula(self, vars):
        wert = self.get_value(vars[0])
        if Afp_isString(wert): wert = Afp_fromString(wert)
        if len(vars) == 2 and  Afp_isDate(wert) and Afp_hasNumericValue(vars[1]):
            return True
        else:
            return False
    ## evaluates a fromula where dates are involved
    # @param vars - variables for formula
    # @param sign - sign in formula (+. - implemeted)
    def evaluate_date_formula(self, vars, sign):
        wert = self.get_value(vars[0])
        if Afp_isString(wert): wert = Afp_fromString(wert)
        value = Afp_addDaysToDate(wert, int(vars[1]), sign)
        return value
    ## write result to file \n
    # currently only .fodt and .odt files are implemented
    # @param filename - name of file to be written
    # @param template - name of empty template file to be used for writing in output format
    def write_resultfile(self, filename, template = None):
        if filename[-5:] == ".fodt":
            # write fodt file
            fout = open(filename, 'w') 
            fout.write(self.tempfile.getvalue())
            fout.close()
        elif filename[-4:] == ".odt":
            # write odt file
            if template and template[-4:] == ".odt":
                Afp_copyFile(template, filename) 
                odt_file = zipfile.ZipFile(filename,'a')
                zip_info = 'content.xml'
                # get zip_info from original "content.xml" entry to write and compress tempfile data
                list = odt_file.infolist()
                for entry in list:
                    if entry.filename == 'content.xml':   zip_info = entry
                odt_file.writestr(zip_info, self.tempfile.getvalue())              
                odt_file.close()  

## Main  program to be called from the commandline \n
# call: AfpAusgabe.py -v -d /home/daten/Afp/pyAfp/Vorlagen/AnmeldungMehrfach_3_data.txt -t /home/daten/Afp/pyAfp/Vorlagen/empty.odt /home/daten/Afp/pyAfp/Vorlagen/AnmeldungMehrfach_3.fodt /tmp/AfpResult.odt \n
# call: AfpAusgabe.py -v -r /home/daten/Afp/pyAfp/Vorlagen/ -d AnmeldungMehrfach_3_data.txt -t empty.odt  AnmeldungMehrfach_3.fodt to /tmp/AfpResult.odt  \n
# call: AfpAusgabe.py -v -r K:\\Afp\\pyAfp\\Vorlagen\ -d AnmeldungMehrfach_3_data.txt -t empty.odt  AnmeldungMehrfach_3.fodt to C:\\temp\\AfpResult.odt \n \n
# usage: AfpAusgabe [option] file [to] outputfile \n
# use the -h or --help option to get full definition
def main(argv):
    fname = ""
    fdata = "AfpData.txt"
    ftemplate = None
    fresult = None
    rootdir = ""
    debug = False
    execute = True
    lgh = len(argv)
    for i in range(1,lgh):
        if argv[i] == "-h" or argv[i] == "--help": execute = False
        elif argv[i] == "-v" or argv[i] == "--verbose": debug = True
        elif argv[i] == "-d" or argv[i] == "--data": 
            if i < lgh-1 and not "-" in argv[i+1]: fdata = argv[i+1]
        elif argv[i] == "-t" or argv[i] == "--template": 
            if i < lgh-1 and not "-" in argv[i+1]: ftemplate= argv[i+1]
        elif argv[i] == "-r" or argv[i] == "--rootdir": 
            if i < lgh-1 and  not "-" in argv[i+1]: rootdir = argv[i+1]
    if (lgh == 2 or (lgh > 2 and not argv[-2] == "to")) and not "-" in argv[-1] and not "-" in argv[-2]: 
        fname = argv[-2]
        fresult = argv[-1]
    elif (lgh > 2 and argv[-2] == "to") and not "-" in argv[-1] and not "-" in argv[-3]: 
        fname = argv[-3]
        fresult = argv[-1]
    else:
        if execute:
            print "ERROR: No file to be processed or no outputfile supplied!"
            print "Please take care of the command syntax below!" 
        execute = False
    if execute:
        out = AfpAusgabe(debug)
        out.set_data(Afp_addRootpath(rootdir, fdata))
        out.inflate(Afp_addRootpath(rootdir, fname))
        out.write_resultfile(Afp_addRootpath(rootdir, fresult), Afp_addRootpath(rootdir, ftemplate))
    else:
        print "usage: AfpAusgabe [option] file [to] outputfile"
        print "Options and arguments:"
        print "-h,--help      display this text"
        print "-d,--data      name of datafile to be used during processing follows"
        print "               if this argument is omitted it is assumed data is provided in the file \"AfpData.txt\""
        print "-t,--template  name of templatefile to be used for packing result follows(actually only .odt files are supported)"
        print "               if this argument is omitted it is assumed the template is provided in the file \"empty.xxx\" if needed"
        print "-r,--rootdir   name of rootdir follows"
        print "               if this argument is given all pathes are interpreted relativ to rootdir,"
        print "               as long as they do not hold a root themselves"
        print "-v,--verbose   display comments on all actions (debug-information)"
        print "file           flavoured wordprocessing file to be processed (actually only .fodt files are supported)"
        print "to             may or may not be used to clarify syntax"
        print "outputfile     name of outputfile follows (actually only .fodt and .odt files are supported)"
 
 # direct execution from the commandline
if __name__ == "__main__":
    main(sys.argv)
