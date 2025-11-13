#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpBase.AfpAusgabe
# AfpAusgabe module provides the capabillity to read and complete flavoured text files
# currently it work on flat (plain xml) odt files (.fodt)
# it holds the class
# - AfpAusgabe
#
#   History: \n
#        23 Jan. 2025 - allow direct evaluation output via () - Andreas.Knoblauch@afptech.de \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        24 Mar. 2019 - add serial letters- Andreas.Knoblauch@afptech.de \n
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
# [Afp_Function(Summe,Anz.Anmeld,1)] : the return value of the function 'Afp_Function' with the variable 'Summe', the datafield 'Anz.Anmeld' and the value '1'  as input will be set at this position \n
#
# {}: \n
# {IF Transfer.Anmeld} : this  line will be added to output if 'Transfer.Anmeld'  evaluates to 'True' (holds a value either  != 0.0 or != "") \n
# {IF Preis.AnmeldEx &gt; 0.0} :  this line will be added to output if 'Preis.AnmeldEx > 0.0' evaluates to 'True' \n
#                                                    works the same with &lt; (<),  == and != \n
# {ELSE IF} in line following a line with IF : this line will be added to outout if previous IF evaluates to False and phrase following IF evaluates to 'True' \n
# {ELSE} in line following a line with  IF or ELSE IF : this line will be added to outout if previous IFs all evaluate to 'False' \n
#
# {WHILE [AnmeldNr.Anmeld] = AnmeldNr.AnmeldEx}: while condition for following lines - use for direct database access
# {WHILE  ROWS IN Content AS C}: while condition for following lines - use for loop over rows in a given SelectionList using C as an alias
#
# {WHILE END}: end of lines for while condition
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

import io
import zipfile

from . import AfpUtilities
from .AfpUtilities import *
from .AfpUtilities.AfpStringUtilities import *
from .AfpUtilities.AfpBaseUtilities import *

from . import AfpBaseRoutines
from .AfpBaseRoutines import *
  
## main class to handle document output   
class AfpAusgabe(object):
    ## Constructor
    # @param debug - flag for debug information
    # @param data - if given, one or more AfpSelectionList's holding data where output is created from
    # @param serial_tags - if given and data is list, tags to drive serialisation
    # - serial_tags[0]:  tag to start serialised data sampling
    # - serial_tags[1]:  tag to end serialised text part and to start serialisation
    # - serial_tags[2]:  flag if lines holding the tags should be included into serialisation
    # - serial_tags[3]:  if given, number of skipping start tag (possibly needed for first row of table, etc.)
    def  __init__(self,  debug = False, data = None, serial_tags = None):
        self.serial_tag_start = "<office:text text:use-soft-page-breaks=\"true\">"  # tag to start serialised data sampling (libre office start of text part)
        self.serial_tag_end = "</office:text>" # tag to end serialised text part and to start serialisation (libre office end of text part)
        self.serial_tag_include = False # flag if lines hodling the tags should be included into serialisation
        self.serial_tag_start_skips = None # if given, number of start tag occurance before start of serialisation (needed to skip first line of table)
        if type(data) == list:
            self.serial_index = 0
            self.data = data[0]
            self.serial_data = data
            if serial_tags:
                lgh = len(serial_tags)
                if lgh: self.serial_tag_start = serial_tags[0]
                if lgh > 1: self.serial_tag_end = serial_tags[1]
                if lgh > 2 and serial_tags[2]: self.serial_tag_include = True
                if lgh > 3: self.serial_tag_start_skips = int(serial_tags[3])
        else:
            self.data = data
            self.serial_data = None
            self.serial_index = None
        self.datas_variables = None
        self.filecontent = None
        self.debug = debug
        self.tempfile = io.StringIO()
        #self.tempfile = tempfile.NamedTemporaryFile('w')
        #self.tempfile = open("/tmp/AfpTemp.txt", 'w') 
        self.serial_text = None
        self.serial_line_written = None
        self.execute_else= None
        self.while_clauses = []
        self.line_stack = [[]]
        self.stack_index = 0
        self.index_stack = [0]
        self.serialized_variables = []
        self.variables = {}
        self.dummies = []
        self.values = {}
        if self.debug: print("AfpAusgabe Konstruktor") 
    ## Destruktor      
    def __del__(self):
        if self.debug: print("AfpAusgabe Destruktor")
    ## attach file which holds data to be used to inflate the flavoured text-file, \n
    # this may be used if no direct access to a mysql database is possible, only works if no data is given (self.data is None)
    # (used by the -d option of the commandline call)
    # @param filename - path to file to be loaded
    def set_data(self, filename):
        if self.data is None: 
            fin = open(filename, 'r') 
            self.filecontent = fin.readlines()
    ## set list of variables diretcly, if list of datas is given
    # @param vars - list of dictionary holding variable values,
    # - should have same length as datas list
    def set_datas_variables(self, vars):
        self.datas_variables = vars
        for var in vars[0]:
            self.values[var] = vars[0][var]
    ## set list of variables diretcly, if list of datas is given
    def load_next_datas_variables(self):
        if len(self.datas_variables) > self.serial_index:
            vars = self.datas_variables[self.serial_index]
            for var in vars:
                self.values[var] = vars[var]
    ## set variables directly
    # @param vars - dictionary holding variable values
    def set_variables(self, vars):
        #print ("AfpAusgabe.set_variables:", vars)
        for var in vars:
            self.variables[var] = Afp_fromString(vars[var])
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
    ## check if all variables have been deliverd for a file
    # @param vars - dictionary holding variable values
    def check_variables(self, filename):
        needed = []
        fin = open(filename, 'r', encoding='cp850') 
        for line in fin:
            need = self.check_line(line)
            if need:
                for me in need:
                    if not me in needed: needed.append(me)
        fin.close()
        return needed
            
    ## main method for reading an analysing flavoured file,
    # inflate the given file with data \n
    # - the file is read here, WHILEs are handeled here 
    # - other options are delegated
    # @param filename - path to flavoured file
    def inflate(self, filename):
        if self.data is None:
            self.load_values_from_data()
        #fin = open(filename, 'r') 
        fin = open(filename, 'r', encoding="UTF-8") 
        #self.line_stack.append([])
        self.line_stack = [[]]
        for line in fin:
            #if self.debug: print "AfpAusgabe.inflate:", line
            line = self.correct_line(line)
            if self.serial_text and not self.serial_tag_include and self.serial_tag_end in line:
                # invoke serial text before the end-tag line is executed
                self.loop_serial_text()
            self.handle_line(line)
            if not self.serial_text is None:
                # append to serial text, if necessary
                self.serial_text.append(line)
            if self.serial_data:
                if self.serial_text is None:
                    if self.serial_tag_start in line :
                        if self.serial_tag_start_skips:
                            self.serial_tag_start_skips -= 1
                        else:
                            # start sampling of serialised text, either with or without the actuel line
                            if self.serial_tag_include: self.serial_text = [line]
                            else: self.serial_text = []
                elif self.serial_tag_include and self.serial_tag_end in line: 
                    # invoke serial text including end-tag line
                    self.loop_serial_text()
        fin.close()
    ## handle serial data
    def loop_serial_text(self):
        if self.debug: print("AfpAusgabe.loop_serial_text:", self.serial_text)
        while len(self.serial_data) > self.serial_index+1:
            self.serial_index += 1
            self.data = self.serial_data[self.serial_index]
            #print "AfpAusgabe.loop_serial_text serialized:", self.serialized_variables, self.variables, self.values
            for var in self.serialized_variables:
                if var in self.values:
                    if var[-4:] == "_Loc":
                        self.values[var] = 0.0
                    self.variables[var] = self.values[var]
            self.values = {}
            if self.datas_variables:
                self.load_next_datas_variables()
            for line in self.serial_text:
                self.handle_line(line)
    ## main method handeling a line
    # - WHILEs are handeled here directly 
    # - other options are delegated
    # @param line - line to be proceeded
    def handle_line(self, line):
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
    ## check if all variabel used inb line are present in self.variables
    # @param line - line to be checked
    def check_line(self, line):
        needed = []
        # hier weiter -> auch in die FUNCTION gucken und ggf. in dummies schreiben
        if "[" in line:
            ain, aout = Afp_between(line, "[", "]")
            for an in ain:
                bin, bout = Afp_between(an, "<", ">")
                var = ""
                for b in bout:
                    var += b
                #print "AfpAusgabe.check_line:", line, "AN:", an, "BOUT:", bout, "VAR:", var, var in self.variables
                if "=" in var:
                    var,dum = Afp_getFuncVar(var)
                    if not var in self.dummies: self.dummies.append(var)
                    #print "AfpAusgabe.check_line dummy:", var
                if not "." in var and not var in self.variables and not var in self.dummies and not(var[0] == "(" and var[-1] == ")"):
                    needed.append(var)
                    #print "AfpAusgabe.check_line needed:", var
        return needed
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
    ## replace special html-tag by unicode sign for formulas
    # @phrase - string where tags have to be replaced
    def replace_html_tags(self, phrase):
        phrase = phrase.replace("&gt;",">")
        phrase = phrase.replace("&lt;","<")
        phrase = phrase.replace("&apos;","\"")
        phrase = phrase.replace("&quot;","\"")
        return phrase
    ## execute lines except WHILE statements \n
    # {IF,ELSE statement} ... and proper lines will be handled \n
    # - IF,ELSE statements are handles here, \n
    # - line evaluation is deligated
    # @param line - line to be analysed
    def execute_line(self,line):
        action, netto= Afp_between(line,"{","}")
        #print "AfpAusgabe.execute_line:", action, netto
        if len(action) == 1:
            #print "AfpAusgabe.execute_line:", action, netto
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
            #for ln in lines: line+= " " + ln.strip()
            for ln in lines: line+= ln
            #line = line.strip()
        fields,netto = Afp_between(line, "[", "]")
        line = self.concat_line(fields, netto)
        #if self.debug: print "AfpAusgabe.write_line:", line
        #self.tempfile.write(line.encode("UTF-8"))
        self.tempfile.write(line)
    ## replace variables with datavalues and concatinate to one line \n
    # if len(netto) > len(fields), the first netto value is placed at the start of the line \n
    # line = [netto] + fields + netto + fields + ... + netto
    # @param fields - variables to be replaced by data-values
    # @param netto - plain text to be placed between data-values
    # @param quoted - flag, if quoted strings should be generated
    def concat_line(self, fields, netto, quoted = False):
        line = ""
        if len(netto) > len(fields): 
            for i in range(len(fields)):
                if quoted: line += netto[i]  + Afp_toQuotedString(self.gen_value(fields[i]), None)
                else: line += netto[i]  + self.gen_value(fields[i])
            line += netto[-1]
        else:
            for f,n in fields,netto:
                if quoted: line += Afp_toQuotedString(self.gen_value(f), None) + n
                else: line += self.gen_value(f) + n 
        #line = self.replace_html_tags(line)
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
            if netto and Afp_holdsValue(netto):
                value = Afp_toString(self.execute_function(fields))
            else:
                value = Afp_toString(self.evaluate_formula(form[0]))
        else:
            split = fields.split(",")
            value = ""
            for field in split:
                #print  "AfpAusgabe.gen_value field:", field, self.values, self.variables 
                #print  "AfpAusgabe.gen_value DATA:", self.data.view()
                if not field in self.values:
                    if field in self.variables:
                        self.values[field] = self.variables[field]
                    else:
                        self.values[field] = self.retrieve_value(field)
                value += " " + Afp_toString(self.values[field])
        #print "AfpAusgabe.gen_value value:", fields, value
        return value.strip()
    ## handles different function evaluations \n
    # assignments (= , +=, -=) are handled here \n
    # fromula evaluation in ()-parantheses is deligated
    # @param funct - function to be evaluated
    def gen_function(self, funct):
        direct = False
        int = False
        if funct[0] == "(" and funct[-1] == ")":
            funct = funct[1:-1]
            direct = True
        if "+=" in funct : sign = "+="
        elif "-=" in funct : sign = "-="
        else: sign = "="
        split = funct.split(sign) 
        var = split[0]
        form, field = Afp_between(split[1],"(",")")
        #print "AfpAusgabe.gen_function:", form, field
        if len(form) > 0: 
            if field and Afp_holdsValue(field):
                value = self.execute_function(split[1])
            else:
                value = self.evaluate_formula(form[0])
        elif Afp_isNumeric(Afp_fromString(field[0])):
            value = Afp_fromString(field[0])
            int = Afp_isInteger(value)
            direct = True
        else: 
            value = self.get_value(field[0])
        if Afp_isString(value): 
            value = Afp_fromString(value)
        if not var in self.values:
            if var in self.variables:
                self.values[var] = self.variables[var]
            else:
                if direct and int:
                    self.values[var] = 0
                else:
                    self.values[var] = 0.0
            if not var in self.serialized_variables: self.serialized_variables.append(var)
        if Afp_toString(value):
            #pyBefehl = "self.values[var]" + sign + value
            #exec(pyBefehl) 
            #print ("AfpAusgabe.gen_function var:", var, self.values[var], type(self.values[var]), value, type(value))
            if sign == "+=":
                self.values[var] += value
            elif sign == "-=":
                self.values[var] -= value
            else:
                self.values[var] = value
            if direct: value = self.values[var]
        return value
    ## evaluates a written condtion and returns the appropriate boolean value
    # @param inphrase - phrase which holds condition to be evaluated
    def evaluate_condition(self, inphrase):
        #print "AfpAusgabe.evaluate_condition in:", inphrase
        splitphrase = inphrase.split("FUNCTION")
        phrase = splitphrase[0]
        condition = False
        phrase = self.replace_html_tags(phrase)
        sign = ""
        if ">" in phrase: sign = ">"
        elif "<" in phrase: sign = "<"
        elif "!" in phrase: sign = "!"
        if "=" in phrase: 
            if "==" in phrase:sign = "=="
            else: sign += "="
        #print ("AfpAusgabe.evaluate_condition SIGN:", sign, "PHRASE:",phrase)
        if sign: 
            split = phrase.split(sign)
            #print ("AfpAusgabe.evaluate_condition split:", phrase, split, sign)
            split[0] = split[0].strip()
            if "(" in split[0] and ")" in split[0]: 
                phrase = Afp_toQuotedString(self.execute_function(split[0]))
            elif self.in_values(split[0]): 
                #print ("AfpAusgabe.evaluate_condition values 0:", split[0], self.values[split[0]], type(self.values[split[0]]))
                phrase = Afp_toQuotedString(Afp_fromString(self.values[split[0]]), True)
            else: 
                phrase = split[0]
            phrase += sign
            split[1] = split[1].strip() 
            #print "AfpAusgabe.evaluate_condition split1:", split[1][0] == "\"" and split[1][-1] == "\"", self.in_values(split[1]), "(" in split[1] and ")" in split[1]
            if (split[1][0] == "\"" and split[1][-1] == "\"") or Afp_isNumeric(Afp_fromString(split[1])):
                phrase += split[1]
            elif "(" in split[1] and ")" in split[1]: 
                phrase = Afp_toQuotedString(self.execute_function(split[1]))
            elif self.in_values(split[1] ): 
                #print "AfpAusgabe.evaluate_condition values 1:", split[1], self.values[split[1]], type(self.values[split[1]])
                phrase += Afp_toQuotedString(Afp_fromString(self.values[split[1]]), True)
            else: 
                phrase += split[1]
        else: 
            if "(" in phrase and ")" in phrase: 
                phrase = Afp_toQuotedString(self.execute_function(phrase))
            elif self.in_values(phrase): 
                phrase = Afp_toQuotedString(self.values[phrase], True)
            else: 
                phrase = "None"
        #pyBefehl = "condition = bool(" + phrase + ")"
        #local = locals()
       #print ("AfpAusgabe.evaluate_condition pyBefehl:", pyBefehl, local)
        #exec(pyBefehl, {}, local)
        #condition = local["condition"]
        #print ("AfpAusgabe.evaluate_condition phrase:", phrase)
        condition = eval("bool(" + phrase + ")")
        #if self.debug: print("AfpAusgabe.evaluate_condition:", pyBefehl, condition)
        if self.debug: print("AfpAusgabe.evaluate_condition:", condition, phrase)
        if condition and len(splitphrase) > 1:
            self.gen_function(splitphrase[1].strip())
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
            if self.debug: print("evaluate_formula:", form, value)
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
            #pyBefehl = "value = " + formula
            #print "AfpAusgabe.evaluate_formula Befehl:", form, pyBefehl, vars, self.values
            #exec(pyBefehl)
            value = eval(formula)
            if self.debug: print("AfpAusgabe.evaluate_formula:", form, formula, value)
        return value
    ## execute python function
    # @param func - funtion call to be executed
    def execute_function(self, func):
        parms, netto = Afp_between(func, "(",")") 
        #print ("AfpAusgabe.execute_function parms:", func, parms, netto)
        vars = parms[0].split(",")
        pyBefehl = "value = " + netto[0] + "("
        for i in range(len(vars)):
            vars[i] = vars[i].strip()
            if Afp_isNumeric(Afp_fromString(vars[i])) or (vars[i][0] == "\"" and vars[i][-1] == "\""):
                var = vars[i]
            else:
                var = Afp_toQuotedString(self.get_value(vars[i]))
            if not var: var = "0"
            pyBefehl += var + ","
        pyBefehl = pyBefehl[:-1] + ")"
        #print ("AfpAusgabe.execute_function Befehl:", pyBefehl, vars, self.values)
        #exec(pyBefehl)
        value = eval(pyBefehl[8:])
        if self.debug: print("AfpAusgabe.execute_function:", pyBefehl, "Result:", value)
        return value
       
    ## executes a while loop, may be called recursive for nested loops \n
    # @param while_line - holds the while conditions
    # @param stack_index - index of the lines in this while loop in self.line_stack
    # @param file_index - current index of the line in datafile
    def execute_while(self, while_line, stack_index, file_index = 0):  
        indices = None
        while_clause, feldnamen, dsnamen, function, order = self.while_input(while_line, stack_index)
        if self.data is None:
            rows, indices = self.extract_rows_from_file(feldnamen, while_clause, file_index)
        else:
            #print ("AfpAusgabe.execute_while select:", feldnamen, while_clause, dsnamen, order)
            if while_clause:
                rows = self.data.mysql.select(feldnamen, while_clause, dsnamen, order) 
            else:
                rows = self.extract_rows_from_data(feldnamen)            
            #print "AfpAusgabe.execute_while rows:", len(rows), "\n", rows
        felder = feldnamen.split(",")
        local_lines = self.line_stack[stack_index]
        if function:
            var, function = Afp_getFuncVar(function)
            if var is None:
                function = None
            elif not var in self.values:
                self.values[var] = 0.0
        if rows:
            lgh = len(rows)
            for i in range(lgh):
                row = rows[i]
                #print felder
                #print row
                for feld,wert in zip(felder,row):
                    self.values[feld] = wert
                if function: self.values[var] = self.evaluate_formula(function)
                if self.debug: print("AfpAusgabe.execute_while WHILE:", stack_index,"Row:", i)
                #print local_lines
                for line in local_lines:
                    if self.debug: print("AfpAusgabe.execute_while Linie", local_lines.index(line))
                    #print line
                    if self.is_while(line) == 1:
                        # start of new while loop
                        if self.debug: print("NEW WHILE:", stack_index + 1, "stack length",len(self.line_stack))
                        if indices is None:
                            self.execute_while(line, stack_index + 1)
                            if self.debug: print("END NEW WHILE")
                        else:
                            self.execute_while(line, stack_index + 1, indices[i])
                            if self.debug: print("END NEW WHILE")
                    else:
                        if self.debug: print("AfpAusgabe.execute_while execute linie", local_lines.index(line), "of WHILE", stack_index, "Linie:", line)
                        self.execute_line(line)
    ## analyses the while_line, \n
    # extracts the while_clause, fields, tables and optional the function
    # @param while_line - holds the while conditions
    # @param stack_index - index of the lines in this while loop in self.line_stack
    def while_input(self, while_line, stack_index):
        #print "AfpAusgabe.while_input input:", while_line, stack_index, self.line_stack
        function = ""
        datsels = ""
        order = None
        action, netto =  Afp_between(while_line,"{","}")
        if len(action) == 1 and action[0][:5] == "WHILE":
            split_func = action[0].split("FUNCTION")
            if len(split_func) == 2:
                # extract function
                function = split_func[1].strip()
                #funct, netto =  Afp_between(split_func[1],"(",")")
                #function = funct[0]
            # extract where clause for database access
            clause = split_func[0][6:]
            #print "AfpAusgabe.while_input split:", split_func, clause, "ORDER BY" in clause
            if "ORDER BY" in clause:
                split = clause.split("ORDER BY")
                order = split[1].strip()
                clause = split[0].strip()
            if clause[:7] == "ROWS IN":
                clause = clause[8:]
                if "AS" in clause:
                    split = clause.split("AS")
                    datsels = split[0].strip()
                clause = ""
            else:
                fields, netto = Afp_between(clause,"[","]")
                clause = self.concat_line(fields, netto, True)
                clause = clause.replace(":","and")
                clause = clause.replace("!","or")
            clause = self.replace_html_tags(clause)
            #print "AfpAusgabe.while_input clause:", clause
            # get needed fieds from lines 
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
                    spl = split[1].strip()
                    if clause and not spl in dats:
                        dats.append(spl)
                        datsels += ","+ spl
                else:
                    if feld in self.variables:
                        feld = ""
                if feld:
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
                            spl = sp[1].strip()
                            if not spl in dats:
                                dats.append(spl)
                                datsels += "," + spl
        #print "AfpAusgabe.while_input output CLAUSE:", clause, "FIELDS:", feldnamen, "TABLES:", datsels, "FUNCT:", function, "ORDER:", order
        if self.debug: print("AfpAusgabe.while_input CLAUSE:", clause, "FIELDS:", feldnamen, "TABLES:", datsels, "FUNCT:", function, "ORDER:", order)
        return clause, feldnamen, datsels, function, order
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
        #print ("AfpAusgabe.in_values", fieldname, fieldname in self.values,  fieldname in self.variables)
        if fieldname in self.values:
            return True
        elif fieldname in self.variables:
            self.values[fieldname] = self.variables[fieldname]
            return True
        else:
            wert = self.retrieve_value(fieldname)
            #print ("AfpAusgabe.in_values retrieve", fieldname, wert)
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
                print("WARNING: value for", fieldname, "not delivered in datafile")
            else:
                val = self.data.get_ausgabe_value(fieldname)
        #print ("AfpAusgabe.retrieve_value:", fieldname,":",val)
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
    # @param feldnamen - names of values to be extracted
    def extract_rows_from_data(self, feldnamen):
        fields = feldnamen.split(",")
        selname = ""
        felder = ""
        for field in fields:
            split = field.split(".")
            if split:
                felder += "," + split[0]
                if not selname and len(split) > 1:
                    selname = split[1]
        if felder: felder = felder[1:]            
        rows = []
        if self.data:
            #rows = self.data.get_grid_rows(selname) 
            rows = self.data.get_value_rows(selname, felder) 
            #print ("AfpAusgabe.extract_rows_from_data:", selname, felder, rows)
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
    ## check if given variables represent a formula where dates are involved
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
    # currently only .xml, .fodt and .odt files are implemented
    # @param filename - name of file to be written
    # @param template - name of empty template file to be used for writing in output format
    def write_resultfile(self, filename, template = None):
        if self.debug: print("AfpAusgabe.write_resultfile input:", filename, template)
        ext = None
        if filename[-5] == ".": 
            ext =  filename[-5:]
        elif filename[-4] == ".": 
            ext = filename[-4:]
        if ext == ".fodt" or ext == ".xml":
            # write plain file (fodt or xml)
            #fout = open(filename, 'w') 
            fout = open(filename, 'w', encoding='UTF-8') 
            fout.write(self.tempfile.getvalue())
            fout.close()
        elif filename[-4:] == ".odt":
            # write zipped odt file
            if template and template[-4:] == ".odt":
                #Afp_copyFile(template, filename) 
                tmpl_file = zipfile.ZipFile(template,'r')
                odt_file = zipfile.ZipFile(filename,'w')
                # get zipinfo list from templatefile, look for "content.xml" entry to write and compress tempfile data into it
                list = tmpl_file.infolist() 
                for entry in list: 
                    if entry.filename == 'content.xml': 
                       odt_file.writestr(entry, self.tempfile.getvalue()) 
                    else:
                        odt_file.writestr(entry, tmpl_file.read(entry.filename))
                odt_file.close()  
                tmpl_file.close()  

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
            print("ERROR: No file to be processed or no outputfile supplied!")
            print("Please take care of the command syntax below!") 
        execute = False
    if execute:
        out = AfpAusgabe(debug)
        out.set_data(Afp_addRootpath(rootdir, fdata))
        out.inflate(Afp_addRootpath(rootdir, fname))
        out.write_resultfile(Afp_addRootpath(rootdir, fresult), Afp_addRootpath(rootdir, ftemplate))
    else:
        print("usage: AfpAusgabe [option] file [to] outputfile")
        print("Options and arguments:")
        print("-h,--help      display this text")
        print("-d,--data      name of datafile to be used during processing follows")
        print("               if this argument is omitted it is assumed data is provided in the file \"AfpData.txt\"")
        print("-t,--template  name of templatefile to be used for packing result follows(actually only .odt files are supported)")
        print("               if this argument is omitted it is assumed the template is provided in the file \"empty.xxx\" if needed")
        print("-r,--rootdir   name of rootdir follows")
        print("               if this argument is given all pathes are interpreted relativ to rootdir,")
        print("               as long as they do not hold a root themselves")
        print("-v,--verbose   display comments on all actions (debug-information)")
        print("file           flavoured wordprocessing file to be processed (actually only .fodt files are supported)")
        print("to             may or may not be used to clarify syntax")
        print("outputfile     name of outputfile follows (actually only .fodt and .odt files are supported)")
 
 # direct execution from the commandline
if __name__ == "__main__":
    main(sys.argv)
