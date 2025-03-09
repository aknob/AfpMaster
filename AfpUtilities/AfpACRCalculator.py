#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AfpACRCalculator provides calculation and simulation for the ACR process
# of the Dassult Systèmes Deutschland GmbH
# it holds the classes:
#       AfpACRCalculator - class to control the compete calculation
#       AfpACRRanges - class to handle wage ranges for the different types
#       AfpACRPerson - class to handle all person specific data
#       AfpACRPeopleManager - class to handle all involved persons
#       AfpACRBooster - class to handle booster exceptions
#
#
#   History: \n
#        30 Dez. 2022 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        23 Feb. 2022 - add different booster and killer possibillities - Andreas.Knoblauch@afptech.de
#        17 Mar. 2021 - add exclusion criteria due to OTE - Andreas.Knoblauch@afptech.de
#        02 Mar. 2020 - add fixed budget surcharge - Andreas.Knoblauch@afptech.de
#        21 Jan   2019 - adaption for additionally file formats - Andreas.Knoblauch@afptech.de
#        29 May 2018 - add result processing - Andreas.Knoblauch@afptech.de
#        07 Feb. 2018 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is an extract of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2025 afptech.de (Andreas Knoblauch)
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
import os

import AfpBase
from AfpBase import *
from AfpBase.AfpUtilities import *
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_importFileLines,  Afp_isNumeric, Afp_existsFile, Afp_initMatrix, Afp_checkMatrix
from AfpBase.AfpUtilities.AfpStringUtilities import Afp_fromString, Afp_toString, Afp_splitMasked, Afp_isString, Afp_numericString

## main program to call AfpACRCalutlator from command line
# @param conffile - path and name to configuration file
# @param datafile - path and name to data file
# @param rangefile - path and name to salariy range file
# @param budget_str - string holding budget percentage of OTE to be distributed
# @param ref_str - string holding reference value for simulation
# @param focal_str - string holding focal value for simulation
# @param part - parttime flag - fte-factor should be used for calculation instead of full OTE
# @param check - flag if matrices check should be performed and displayed (to confirm calculation-path)
# @param display - different keywords to allow output of different aspects of the data and the calculation
# @param debug - flag for debug-modus
def AfpACRCalculator_main(conffile, datafile, rangefile, budget_str, ref_str, focal_str, part, check, display, debug):
    if debug: print("AfpACRCalculator.main called:", conffile, datafile, rangefile, budget_str, ref_str, focal_str, part, check, display)
    # define data for input
    if conffile: 
        config = Afp_ReadConfig(conffile)
    else: 
        config = {}
    if datafile: 
        config["DATA_FILE_NAME"] = datafile
    if rangefile: 
        config["RANGE_FILE_NAME"] = rangefile
    if budget_str:
        config["BUDGET_PERCENTAGE"] = Afp_fromString(budget_str)
    if debug: print("AfpACRCalculator.main configuration used:", config)
    fte_distribution = not part
    # start of executable code
    budget = config["BUDGET_PERCENTAGE"]
    fixum = config["BUDGET_FIXUM"]
    namecount = False
    data = range_lines = None
    if config["DATA_FILE_NAME"] and config["RANGE_FILE_NAME"]:
        data = Afp_importCSVLines(config["DATA_FILE_NAME"])
        range_lines = Afp_importCSVLines(config["RANGE_FILE_NAME"])
    boosters = None
    if data and range_lines:
        if debug: print("AfpACRCalculator_main: data", len(data), "lines and ranges",len(range_lines)," lines read!")
        ranges = AfpACRRanges(range_lines, config["RANGE_COLUMN_MAP"], debug)
        people = AfpACRPeopleManager(data, config["DATA_COLUMN_MAP"], debug)
        people.set_positioning(ranges)
        people.set_performance(config["DATA_PERFORMANCE_MAP"])
        if "DATA_PROMOTION_LIST" in config:
            print("AfpACRCalculator.main: DATA_PROMOTION_LIST deprecated, please use DATA_BOOSTER_MAP!")
        if "DATA_BOOSTER_MAP" in config:
            boosters = Afp_getBoostersFromConfig(config["DATA_BOOSTER_MAP"], debug)
            people.set_boosters(boosters)
        if "DATA_INVALID_LIST" in config or "ELIGIBLE_RELATIV_OTE_FACTOR" in config or "ELIGIBLE_OTE_MAXIMUM" in config or "SKIP_PERFORMANCE_INDICATOR" in config: 
            data_list = None
            ote_factor = None
            ote_max = None
            skip_perf = None
            if "DATA_INVALID_LIST" in config: data_list = config["DATA_INVALID_LIST"]
            if "ELIGIBLE_RELATIV_OTE_FACTOR" in config: ote_factor = config["ELIGIBLE_RELATIV_OTE_FACTOR"]
            if "ELIGIBLE_OTE_MAXIMUM" in config: ote_max = config["ELIGIBLE_OTE_MAXIMUM"]
            if "SKIP_PERFORMANCE_INDICATOR" in config: skip_perf = config["SKIP_PERFORMANCE_INDICATOR"]
            people.set_eligibillity(data_list, skip_perf, ote_factor, ote_max)
        if not people.are_valid():
            print("AfpACRCalculator_main WARNING Not all data supplied for each person!")
        if debug: print("AfpACRCalculator.main: Calculator creation beginning")           
        Calculator = AfpACRCalculator(people, budget, fixum, debug)
        Calculator.set_spreadmap(config["MATRIX_SPREAD_MAP"])
        if "MATRIX_MANAGER_MAP" in config:
            Calculator.set_manager(config["MATRIX_MANAGER_FOCAL"], config["MATRIX_MANAGER_FACTOR"], config["MATRIX_MANAGER_MAP"])
        else:
            Calculator.set_manager(config["MATRIX_MANAGER_FOCAL"], config["MATRIX_MANAGER_FACTOR"])
        Calculator.set_boostermaps(boosters)
        Calculator.set_calcflags(config["CALC_USE_FOCAL_FOR_RANGE"], config["CALC_SKIP_SPREAD_ZEROS"])
        if "MATRIX_ACR" in config:
            Calculator.set_acr_matrix(config["MATRIX_ACR"])
        if ref_str:
            ref = Afp_fromString(ref_str)
            Calculator.simulate(ref)        
        elif focal_str:
            ref = Afp_fromString(focal_str)
            Calculator.simulate(None, ref)
        else:
            Calculator.calculate_focal_matrix(fte_distribution, check)
            Calculator.generate_reference_matrix()
            Calculator.simulate()
            if check: Calculator.check_increase()
        if debug: print("AfpACRCalculator_main show:", display)
        Calculator.view(display)
    else:
        print("AfpACRCalculator not sufficent data available!")
## read configuration data from file 
# @param string - string holding values
def Afp_getConfigValue(string):
    value = None
    string = string.strip()
    if string[0] == "[" or string[0] == "{":  # list or dictionary
        #befehl = "value = " + string
        #exec(befehl)
        value = eval(string)
    else:
        value = Afp_fromString(string)
    return value
## read configuration data from file 
# @param filename - path and name of file to be read
def Afp_ReadConfig(filename):
    config = {}
    #print "Afp_ReadConfig:", Afp_existsFile(filename)
    data = Afp_importFileLines(filename)
    for line in data:
        if line.strip() and line.strip()[0] == "#": continue
        if "=" in line:
            name, value = line.split("=")
            config[name.strip()] = Afp_getConfigValue(value)
    if data: 
        config["CONFIG_FILE_NAME"] = filename
    return config
 
## generate dictionary of AfpACRMatrixBooster objects from config dictionary
# @param string - string to be converted
def Afp_getBoostersFromConfig(config, debug = False):
    boosters = {}
    for name in config:
        conf = config[name]
        if "Matrix" in conf:
            boosters[name] = AfpACRMatrixBooster(conf["Typ"], conf["Value"], conf["List"], conf["Matrix"], debug)
        else:
            boosters[name] = AfpACRMatrixBooster(conf["Typ"], conf["Value"], conf["List"], None, debug)
    if boosters: return boosters
    else: return None
## convert string to int, omit points
# @param string - string to be converted
def Afp_toInt(string):
    if string:
        string = string.split()[0] # remove everything behind a space (e.g. €)
        split = string.split(".")
        string = ""
        for sp in split:
            string += sp
        if "," in string: string = string.split(",")[0]
    if string and string.isdigit():
        return int(string)
    else:
        return 0
## returns positioning string
# @param pos - integer indication positioning
def Afp_toPos(pos):
    pos = int(pos)
    string = ""
    if not pos is None:
        if pos < 0:
            string = "-"*(-pos)
        elif pos == 0:
            string = "="
        else:
            string = "+"*pos
    return string
## checks if a valid entry at position i,j exists in matrix
# @param first - first index in matrix 
# @param second - second index in matrix 
# @param matrix - entry to be checked 
def Afp_validMatrixField(first, second, matrix):
    valid = False
    if matrix and not Afp_isNumeric(matrix):
        if len(matrix) > first:
            if len(matrix[first]) > second:
                if not matrix[first][second] is None: valid = True
    return valid
## import lines of extern file and return it \n
# allow backslash-n in fields (enclosed by ")
# @param fname - name of file
# @param only_first - read and return only first line
def Afp_importCSVLines(fname, only_first=False):
    lines = []
    if Afp_existsFile(fname):
        fin = open(fname , 'r', encoding='latin-1') 
        oldline = ""
        for line in fin:
            cnt = line.count("\"")
            if cnt%2 == 0:
                if oldline: 
                    oldline += line
                else:
                    lines.append(line)
                    if only_first: break
            else:
                if oldline:
                    lines.append(oldline + line)
                    oldline = ""
                    if only_first: break
                else:
                    oldline = line
        if oldline: 
            lines.append(oldline)
        fin.close()
    return lines
## convert matrix column identifier to index
# @param ident - identifier to be mapped
def Afp_colToInd(ident):
    if Afp_isNumeric(ident):
        return int(ident)
    else:
        index = 0
        potenz = len(ident)-1
        for letter in ident:
            asci = ord(letter)
            if asci > 96: asci -= 96 # lower case latters
            elif asci > 64: asci -= 64 # upper case letters
            factor = 26**potenz
            index += asci*factor
            potenz -= 1
        return index - 1

## check if al list is filled with other values than 'None'
# @param list - list to be checked
def Afp_isFilled(list):
    filled = True
    for entry in list:
        if entry is None: filled = False
    return filled
## check if values hold information
# @param values - dictonary to be checked
def Afp_holdsValues(values):
    check = False
    for val in values:
        if values[val]:
            check= True
            break
    return check
    
## get difference string from string with two given values
# @param string - given string
def Afp_getDiff(string):
    split = string.split(" ")
    val1 = Afp_fromString(split[0])
    val2 = Afp_fromString(split[-1])
    return val2 - val1

 ## class to handle the calculations of the whole ACR process
class AfpACRCalculator(object):
    ## initialize AfpACRCalculator class
    # @param people - AfpACRPeopleManager object holding all involved persons
    # @param percent - percents of ote-sum building budget
    # @param fixum - if given, fixed sum to be added to budget
    # @param debug - flag for debug information
    def  __init__(self, people, percent, fixum = None, debug = False):
        self.debug = debug
        self.check_acr = False
        self.people = people
        self.budgetfactor = percent/100.0
        self.budgetfixum = fixum
        self.mrange = 0.1
        self.mfact = 0.1
        self.mcalc = 0.75
        self.spread = 2.0
        self.spread_threshold = 0.0
        self.boosters = {"PROMO": AfpACRMatrixBooster("+", 2.0, ["True"])}
        self.use_focal_as_base = False
        self.skip_spread_zeros = False
        self.acr_matrix = None
        self.acr_display = None
        # data to be computed
        ## check_matrix only to check internal consistancy
        self.check_matrix = None
        ## complete budget
        self.budget = None
        ## spread matrix with factors of reference value
        self.spreadmap = None
        ##  matrix with factors of value for manager ranges
        self.rangemap = None
        ## reference matrix holding the midpoints of the ranges
        self.reference_matrix = None
        ## reference value (mid value of matrix)
        self.reference_value = None
        ## if wanted relativ correction of reference value
        self.reference_correction = None
        ## matrix of ote for each distribution field (position/perormance)
        self.ote_matrix = None
        ## ote sum for persons not proper aligned
        self.ote_leftover = None
        ## matrix of persons for each distribution field (position/perormance)
        self.person_counts= None
        ## count of persons not proper aligned
        self.person_leftover = None
        ## reference matrix holding the focal points of the ranges - used for simulation
        self.focal_matrix = None
        ## focal value (mid value of matrix)
        self.focal_value = None
        ## holding the different booster matrices - used for calculation and simulation
        self.booster_matrices = None
        ## result matrix, holding manager ranges in each field
        self.matrix = None
        ## result over all increase
        self.increase = None
        self.set_budget()
    ## set spreadmap
    # @param spread - map for relativ spread of dstribution matrix
    # @param threshold - threshold below which absolut values will be set to 0
    def set_spreadmap(self, spread = None, threshold = None):
        if not spread is None:
            self.spread = spread
        if not threshold is None:
            self.spread_threshold = threshold
        n = self.people.get_matrix_length(0)
        m = self.people.get_matrix_length(1)
        matrix = Afp_initMatrix(n, m, 1.0)
        if Afp_isNumeric(self.spread):
            n2 = n/2
            m2 = m/2
            step_u = (self.spread - 1.0)/(n2 + m2)
            step_l = 1.0/(n2 + m2)
            print("AfpACRCalculator.set_spreadmap step:", self.spread, n2+m2, step_u, step_l)
            for i in range(len(matrix)):
                f = i - m2
                if f < 0:
                    matrix[i][n2] = 1.0 + f*step_l 
                elif f > 0:
                    matrix[i][n2] =  1.0 + f*step_u
                for j in range(len(matrix[i])):
                    f = j - n2
                    if i < m2:
                        matrix[i][j] = matrix[i][n2] + f*step_l
                    else:
                        matrix[i][j] = matrix[i][n2] + f*step_u
        elif Afp_checkMatrix(self.spread, n, m):
            matrix = self.spread
        # check threshold
        for i in range(len(matrix)):
            for j in range(len(matrix[i])):
                if matrix[i][j] < self.spread_threshold:
                    matrix[i][j] = 0.0
        self.spreadmap = matrix
    ## set manager values
    # @param calcpoint - percentage which point of range is used for simulation
    # @param rule - factor for manager range, where no mapvalues are delivered
    # @param matrix - map for manager range
    def set_manager(self, calcpoint, rule = None, matrix = None):
        if Afp_isNumeric(rule):
            self.mfact = rule
        if not matrix is None:
            self.mrange = matrix
        if not calcpoint is None:
            self.mcalc = calcpoint/100.0
    ## set booster values
    # @param boosters - dictionary holding all values to create all boostermatrices
    def set_boostermaps(self, boosters):
        self.boosters = boosters
    ## set calculation flags
    # @param use_focal - flag,if focal value should be used to generate manager ranges
    # @param skip_zeros - flag, if zero fields in matrix should be skipped in calculation
    def set_calcflags(self, use_focal = None, skip_zeros = None):
        if use_focal:
            self.use_focal_as_base = True
        if skip_zeros:
            self.skip_spread_zeros = True
        #print "AfpACRCalculator.set_calc flags:",  self.use_focal_as_base,  self.skip_spread_zeros 
    ## set acr result matrix
    # @param matrix -  ACR-Matrix 
    def set_acr_matrix(self, matrix ):
        self.acr_matrix = matrix
        self.check_acr = True
        #print "AfpACRCalculator.set_acr_matrix:", self.acr_matrix
        n = len(matrix)
        m = len(matrix[0])
        mat= Afp_initMatrix(n, m, 0.0)
        for i in range(m):
            for j in range(n):
                mat[i][j] = Afp_toString(matrix[i][j][0]).strip() + " - " + Afp_toString(matrix[i][j][1]).strip()
        self.acr_display = mat
    ## calculate focal matrix by distributing the budget to the ote matrix \n
    # if spreadmap and budget are given generate focal matrix from people ote data. \n
    #  focal value - f, ote portion in matrix field - ote[i], spread of matix field i - s[i] budget = b \n
    #            f = 100 * b / sum ( s[i]*ote[i] )
    # @param fte - flag if if full time equivalent data should be used for distribution calculation
    # @param debug - flag if debug output should be generated, even when global flag is not set
    def calculate_focal_matrix(self, fte = True, debug = False):
        debug = debug or self.debug
        if not  fte:
            self.ote_leftover , self.ote_matrix = self.people.get_matrix_sums(False)
        else:
            self.ote_leftover , self.ote_matrix = self.people.get_matrix_sums()
        promo_sum = self.gen_boosted_sum()
        if debug: 
            print("AfpACRCalculator.calculate_focal_matrix ote matrix:", self.ote_leftover, self.ote_matrix)
            print("AfpACRCalculator.calculate_focal_matrix spreadmap:", self.spreadmap, "PROMO:", promo_sum)
        if self.spreadmap and self.budget:
            n = self.people.get_matrix_length(0)
            m = self.people.get_matrix_length(1)
            cmatrix = Afp_initMatrix(n, m, 0.0)
            #sum = self.ote_leftover
            sum = 0.0
            reduce = promo_sum
            all = not self.skip_spread_zeros
            for i in range(m):
                for j in range(n):
                    if self.spreadmap[i][j] > 0.0:
                        sum += self.spreadmap[i][j]*self.ote_matrix[i][j]
                        if debug: 
                            cmatrix[i][j] = self.spreadmap[i][j]*self.ote_matrix[i][j]
                            print("AfpACRCalculator.calculate_focal_matrix weighted matrix:", i, j, "value:", self.spreadmap[i][j],"*", self.ote_matrix[i][j], "=", cmatrix[i][j])
                    elif all and Afp_validMatrixField(i, j, self.mrange):
                            reduce += self.mcalc*self.mrange[i][j]*self.ote_matrix[i][j]/100
                            if debug: 
                                print("AfpACRCalculator.calculate_focal_matrix fixed matrix:", i, j, "value:", self.mcalc*self.mrange[i][j], "*", self.ote_matrix[i][j], "/ 100 =", self.mcalc*self.mrange[i][j]*self.ote_matrix[i][j])
                                cmatrix[i][j] = self.mcalc*self.mrange[i][j]*self.ote_matrix[i][j]/100
            self.focal_value = 100*(self.budget - reduce)/sum
            if debug: 
                self.check_matrix = cmatrix
                print("AfpACRCalculator.calculate_focal_matrix (100*(budget - reduce)/sum):", self.focal_value, "= 100 * (", self.budget, "-", reduce, ") /", sum)
                checksum = 0.0
                for i in range(m):
                    for j in range(n):
                        if self.spreadmap[i][j] > 0.0:
                            checksum +=   (self.focal_value*self.spreadmap[i][j]*self.ote_matrix[i][j])/100
                print("AfpACRCalculator.calculate_focal_matrix checksum:", checksum, "+" , reduce, "=", checksum + reduce, self.budget)
            self.generate_focal_matrix()
    ## generate increase sum over all boosters (inclusive promotions)
    # @param fte - flag if if full time equivalent data should be used for ote  calculation
    def gen_boosted_sum(self, fte = True):
        sum = 0.0
        if self.boosters:
            for boost in self.boosters:
                sum += self.gen_booster_sum(boost, fte)
        return sum
    ## generate booster increase sum
    # @param boost - name of used booster
    # @param fte - flag if if full time equivalent data should be used for sum calculation
    def gen_booster_sum(self, boost, fte = True):
        sum = 0.0
        if boost in self.boosters:
            booster = self.boosters[boost]
            if booster.get_matrix():
                matrix = self.people.get_booster_matrix(fte)
                n = self.people.get_matrix_length(0)
                m = self.people.get_matrix_length(1)
                for i in range(m):
                    for j in range(n):
                        sum += matrix[i][j] * booster.get_matrix()[i][j]/100
            elif booster.get_value():
                sum += self.people.get_booster_sum(boost, fte)*booster.get_value()/100
        return sum
    ## generate one reference value from a focal value respecting manager range
    # @param focal - focal value
    # @param first - first index in matrix 
    # @param second - second index in matrix 
    #  reference value - r, focal value - f, manager range value in both directions - m, calcpoint = c \n
    #          r = f/(1-m+2cm)       if manager range is set by a factor on r (mrange given as value) or \n
    #          r =  f -2cm + m         if manager range is given by value (mrange given as matrix)
    def gen_ref_value(self, focal, first = None, second = None):
        if first is None: first = self.people.get_matrix_length(1)/2
        if second is None: second = self.people.get_matrix_length(0)/2
        if Afp_validMatrixField(first, second, self.mrange):
            if self.spreadmap[first][second] > 0.0:
                ref = focal - self.mcalc*self.mrange[first][second] + self.mrange[first][second]/2
            else:
                ref = 0.0
        else:
            ref = focal/(1-self.mfact + 2*self.mcalc*self.mfact)
        return ref
    ## generate focal value from a given reference value  respecting manager range
    # @param ref - reference value
    # @param first - first index in matrix 
    # @param second - second index in matrix 
    #  focal value - f, reference value - r, manager range value - m, calcpoint = c \n
    #          f = r*(1-m+2cm)       if manager range is set by a factor on r (mrange given as value) or \n
    #          f =  r +2cm - m         if manager range is given by value (mrange given as matrix)
    def gen_focal_value(self, ref, first = None, second = None):
        if first is None: first = self.people.get_matrix_length(1)/2
        if second is None: second = self.people.get_matrix_length(0)/2
        if Afp_validMatrixField(first, second, self.mrange):
            if self.spreadmap[first][second] > 0.0:
                focal = ref + self.mcalc*self.mrange[first][second] - self.mrange[first][second]/2
            else:
                ref = 0.0
        else:
            focal = ref*(1-self.mfact + 2*self.mcalc*self.mfact)
        return focal
    ## generate focal matrix from focal value and spreadmap
    def generate_focal_matrix(self):
        matrix = None
        all = not self.skip_spread_zeros
        if self.focal_value:
            n = self.people.get_matrix_length(0)
            m = self.people.get_matrix_length(1)
            matrix = Afp_initMatrix(n, m, 0.0)
            for i in range(m):
                for j in range(n):
                    if self.spreadmap[i][j] > 0.0:
                        matrix[i][j] = self.focal_value*self.spreadmap[i][j]
                    elif all and Afp_validMatrixField(i, j, self.mrange):
                        matrix[i][j] = self.mcalc*self.mrange[i][j]
                    else:
                        matrix[i][j] = 0.0
            #print "AfpACRCalculator.generate_focal_matrix:", self.focal_value, "\n", self.focal_matrix,"\n", matrix
            if self.debug: print("AfpACRCalculator.generate_focal_matrix:", self.focal_value, "\n old:", self.focal_matrix,"\n new:", matrix)
        self.focal_matrix = matrix
    ## generate distribution (reference) matrix from focal matrix\n
    # if focal matrix is given generate distribution matrix on which manager ranges are applied.
    def generate_reference_matrix(self):
        matrix = None
        if self.focal_matrix:
            n = self.people.get_matrix_length(0)
            m = self.people.get_matrix_length(1)
            matrix = Afp_initMatrix(n, m, 0.0)
            for i in range(len(matrix)):
                for j in range(len(matrix[i])):
                    matrix[i][j] = self.gen_ref_value(self.focal_matrix[i][j], i, j)
        if matrix:
            #print "AfpACRCalculator.generate_reference_matrix:", self.reference_value, matrix[m/2][n/2], "\n",self.reference_matrix,"\n", matrix
            if self.debug: print("AfpACRCalculator.generate_reference_matrix:", self.reference_value, matrix[int(m/2)][int(n/2)], "\n old:",self.reference_matrix,"\n new:", matrix)
            self.reference_matrix = matrix
            self.reference_value = matrix[int(m/2)][int(n/2)]    
    ## generate acr matrix from reference matrix\n
    def generate_acr_matrix(self):
        matrix = None
        if self.reference_matrix:
            n = self.people.get_matrix_length(0)
            m = self.people.get_matrix_length(1)
            matrix = Afp_initMatrix(n, m, 0.0)
            for i in range(m):
                for j in range(n):
                    if Afp_validMatrixField(i, j, self.mrange):
                        rang = self.mrange[i][j]/2
                    else:
                        rang = self.mfact*self.reference_matrix[i][j]
                    #print "AfpACRCalculator.simulate:", i, j, rang, self.reference_matrix[i][j], self.mfact
                    matrix[i][j] = Afp_toString(max(self.reference_matrix[i][j] - rang,0)).strip() + " - " + Afp_toString(max(self.reference_matrix[i][j] + rang, 2*rang)).strip()
        if matrix:
            if self.debug: print("AfpACRCalculator.generate_acr_matrix:\n old:", self.matrix,"\n new:", matrix)
            self.matrix = matrix
    ## generate booster matrices \n
    def generate_booster_matrices(self):
        if self.boosters:
            if self.use_focal_as_base:
                from_matrix = self.focal_matrix
            else:
                from_matrix = self.reference_matrix
            self.booster_matrices = {}
            for name in self.boosters:
                self.booster_matrices[name] = self.boosters[name].gen_boosted_matrix(from_matrix)
        if self.debug: print("AfpACRCalculator.generate_booster_matrices:", self.booster_matrices)
        #print "AfpACRCalculator.generate_booster_matrices from:", from_matrix
        #print "AfpACRCalculator.generate_booster_matrices:", self.booster_matrices
    ## simulate distribution for given reference or focal value \n
    # spreadmap will be used on focal value
    # @param ref - new reference value
    # @param focal - new focal value
    def simulate(self, ref = None, focal = None):
        if not self.spreadmap: return
        n = self.people.get_matrix_length(0)
        m = self.people.get_matrix_length(1)
        if ref or focal:
            if ref: focal = self.gen_focal_value(ref)
            self.focal_value = focal
        if focal or self.focal_matrix is None:
            self.generate_focal_matrix()
        if focal or self.reference_matrix is None is None or self.booster_matrices is None or self.matrix is None:
            if focal or self.reference_matrix is None:
                self.generate_reference_matrix()
            if focal or self.matrix is None:
                self.generate_acr_matrix()
            if focal or self.booster_matrices is None:
                self.generate_booster_matrices()
        # set ote proposals for all
        self.people.set_ote_proposals(self.focal_matrix, self.booster_matrices)    
    ## check increase   
    def check_increase(self):
        if self.check_matrix:
            sum, matrix = self.people.get_matrix_sums(True, "Inc")
            booster_matrices = self.generate_booster_matrices()
            intend_sum = 0.0
            check_sum = 0
            print()
            print("AfpACRCalculator.check_increase boosted values:", booster_matrices)
            print("AfpACRCalculator.check_increase OTE leftover:", self.ote_leftover, "   Increase not eligible:", sum)
            print("AfpACRCalculator.check_increase: i j check \t\tintend  \tmatrix  \tdiff")
            matrix_sum = sum
            diff_sum = 0.0
            booster_sum = 0.0
            for i in range(len(matrix)):
                for j in range(len(matrix[i])):
                    if Afp_validMatrixField(i, j, self.check_matrix):
                        check = self.check_matrix[i][j]*self.focal_value/100
                        for matrix in booster_matrices:
                            check += matrix[i][j]
                    else:
                        check = 0.0
                    intend = self.ote_matrix[i][j] *self.focal_matrix[i][j]/100
                    for matrix in booster_matrices:
                        intend += matrix[i][j]
                        booster_sum += matrix[i][j]
                    check_sum += check
                    intend_sum += intend
                    matrix_sum += matrix[i][j]
                    diff_sum += intend - matrix[i][j]
                    print("%s %i %i %f \t%f \t%f \t%f" % ("AfpACRCalculator.check_increase:", i, j, check, intend, matrix[i][j], intend -  matrix[i][j]))
            print("%s %f \t %f\t%f\t%f \t%f \tBugdet: %f" % ("AfpACRCalculator.check_increase sums:", check_sum, intend_sum, matrix_sum, diff_sum, booster_sum, self.budget))
            print("AfpACRCalculator.check_increase rounded:", self.people.round, self.people.rounded)
            print()
    ## set complete budget sum
    # @param percent - if given, percentage of ote to generate budget
    # @param fix - if given, fixvalue to be added to budget
    def set_budget(self, percent = None, fix = None):
        if percent:
            self.budgetfactor = percent/100.0
        if fix:
            self.budgetfixum = fix
        #ote = self.people.get_ote_sum(True, False)
        ote = self.people.get_ote_sum()
        self.budget = self.budgetfactor * ote
        if self.budgetfixum: 
            self.budget += self.budgetfixum
    ## retrieve reference value
    def get_ref_value(self):
        return self.reference_value
    ## retrieve the different matrix data
    def get_info_values(self):
        values = {}
        values["BudCnt"] =100*self.budgetfactor
        values["Budget"] = self.budget
        values["Ref"] = self.reference_value
        values["Focal"] = self.focal_value
        return values
    ## generate variance risk of matrix to extend budget
    def get_variance_risk(self):
        return self.get_variance()*self.mcalc, self.get_variance()*(1.0 - self.mcalc)
    ## generate variance of matrix due to manager range
    def get_variance(self):
        n = len(self.matrix)
        m = len(self.matrix[0])
        var = 0.0
        for i in range(n):
            for j in range(m):
                var += Afp_getDiff(self.matrix[i][j])*self.ote_matrix[i][j]/100
        return var
    ## retrieve  data from people
    def get_people_data(self):
        return self.people.get_grid_data()
    ## generate ACR average percentage for each matix cell
    def get_acr_average(self):
        average = self.get_ote_averages()
        total, counts = self.people.get_matrix_sums(True, "cnt")
        matrix = self.get_acr_distribution()
        n = len(matrix)
        m = len(matrix[0])
        mmatrix = Afp_initMatrix(m, n, "")
        for i in range(n):
            for j in range(m):
                mmatrix[i][j] =  100*matrix[i][j]/(average[i][j]*counts[i][j])
        return mmatrix
    ## generate ACR sum for each matix cell
    def get_acr_distribution(self):
        n = len(self.matrix)
        m = len(self.matrix[0])
        mmatrix = Afp_initMatrix(m, n, "")
        for i in range(n):
            for j in range(m):
                mmatrix[i][j] = self.ote_matrix[i][j]*self.focal_matrix[i][j]/100
        return mmatrix
    ## generate avererage OTE data for each matix cell
    def get_ote_averages(self):
        n = self.people.get_matrix_length(1)
        m = self.people.get_matrix_length(0)
        matrix = Afp_initMatrix(m, n, 0.0)
        leftover, counts = self.people.get_matrix_sums(True, "cnt")
        for i in range(n):
            for j in range(m):
                if counts[i][j]:
                    matrix[i][j] = self.ote_matrix[i][j]/counts[i][j]
        return matrix
    ## retrieve the different matrix data
    # @param ident - identifier which matrix has to be retrieved
    def get_matrix_typs(self):
        typs = ["ACR - Average", "Referenzvalues"]
        return typs
    ## retrieve the different matrix data
    # @param ident - identifier which matrix has to be retrieved
    def get_matrix(self, ident):
        if "ACR" in ident:
            if ident == "ACR - Average":
                return self.get_acr_average()
            elif ident == "ACR - Distribution":
                return self.get_acr_distribution()
            elif ident == "ACR - Given":
                return self.acr_display
            else: # "ACR - Result"
                return self.matrix
        elif "OTE" in ident:
            if ident == "OTE - Distribution":
                return self.ote_matrix
            elif ident == "OTE - Average":
                return self.get_ote_averages()
        elif "Persons" in ident:
            if ident == "Persons - Count":
                leftover, counts = self.people.get_matrix_sums(True, "cnt")
                return counts
            elif ident == "Persons - Percent":
                total, counts = self.people.get_matrix_sums(True, "cnt")
                for i in range(len(counts)):
                    for j in range(len(counts[i])):
                        total += counts[i][j]
                for i in range(len(counts)):
                    for j in range(len(counts[i])):
                        counts[i][j] = 100.0*counts[i][j]/total
                return counts
        elif ident == "Focalvalues":
            return self.focal_matrix
        elif ident == "Referenzvalues":
            return self.reference_matrix
        elif ident == "Spread":
            return self.spreadmap
        elif ident == "Managerrange":
            n = len(self.matrix)
            m = len(self.matrix[0])
            mmatrix = Afp_initMatrix(m, n, "")
            for i in range(n):
                for j in range(m):
                    mmatrix[i][j] = Afp_toString(Afp_getDiff(self.matrix[i][j]))
            return mmatrix
        return self.matrix
    ## display internal data
    def view(self, typ = None):
        if self.debug: print("AfpACRCalculator.view:",typ)
        if typ == "HELP" or typ == "help":
             print("Data output, possible types:")
             print("MATRIX: spreadmap, managermap, ote matrix, referencevalue, referencematrix, focalvalue, focalmatrix, booster matrices")
             print("MATRIX type: display matrix of 'type', possible types:")
             print("            'Focalvalues', 'Referenzvalues', 'Spread', 'Managerrange', 'ACR - Average,Distribution,Given', 'OTE - Average,Distribution', Persons - Count,Percent'")
             print("CHECK_RANGE: People outside manager range")
             print("RANGE_FACTOR: Factor of percentage in manager range")
        if typ is None or typ == "MATRIX":
            print("AfpACRCalculator.view spreadmap:", self.spreadmap)
            print("AfpACRCalculator.view managermap:", self.mfact, self.mrange)
            print("AfpACRCalculator.view ote matrix:", self.ote_matrix, self.ote_leftover)
            print("AfpACRCalculator.view referencevalue:", self.reference_value)
            print("AfpACRCalculator.view referencematrix:", self.reference_matrix)
            print("AfpACRCalculator.view focalvalue:", self.focal_value)
            print("AfpACRCalculator.view focalmatrix:", self.focal_matrix)
            print("AfpACRCalculator.view booster matrices:", self.gen_booster_matrices())
            OTE = self.people.get_ote_sum()
            ote = self.people.get_ote_sum(False)
            print("AfpACRCalculator.view ote sums:", OTE, ote, OTE - ote, (OTE - ote)*self.reference_value/100)
            INC = self.people.get_increase_sum()
            inc = self.people.get_increase_sum(False)
            print("AfpACRCalculator.view increase sums:", INC, inc, INC - inc)
            print("AfpACRCalculator.view increase matrix:", self.get_acr_distribution())
            OTE = self.people.get_ote_sum(True, True)
            ote = self.people.get_ote_sum(False, True)
            print("AfpACRCalculator.view new ote sums:", OTE, ote, OTE - ote)
            print("AfpACRCalculator.view matrix:", self.matrix)
            print("AfpACRCalculator.view budget:", self.budget, "Increase 100%:", INC, "Difference 100%:", self.budget - INC, "Increase payable:",inc, "Difference payable:", self.budget - inc)
        elif "MATRIX" == typ[:6]:
            ident = typ[7:].strip()
            matrix = self.get_matrix(ident)
            if not matrix: matrix = "not found!"
            print("AfpACRCalculator.view", typ + ":", matrix)
        elif "CHECK_RANGE" == typ[:11] or "RANGE_FACTOR" == typ[:12]:
            outside = True
            if "RANGE_FACTOR" == typ[:12]: outside = False
            add = None
            flag = False
            if len(typ) > 11:
                split = typ.split()
                if len(split) > 2 and split[2].strip() == "%":
                    flag = True
                if len(split) > 1:
                    add = Afp_fromString(split[1].strip())
            matrix = self.matrix
            if self.acr_display: matrix = self.acr_display
            self.people.acr_manager_range(matrix, outside, self.boosters, add, flag)
        else:
            self.people.view(typ)

    
 ## class to handle salarie ranges       
class AfpACRRanges(object):
    ## initialize AfpACRRanges class
    # @param range_lines - lines read from range file
    # @param colmap - dictionary for used column indices
    # @param debug - flag for debug information
    def  __init__(self, range_lines, colmap, debug = False):
        if debug: print("AfpACRRanges:", range_lines, colmap)
        #colmap = {"NAME":0, "MIN":3, "MAX":5, "CLG":1}
        for col in colmap:
            colmap[col] = Afp_colToInd(colmap[col])
        ranges = {}
        current_range = ""
        next_range = ""
        range_data = {}
        for line in range_lines:
            cols = Afp_splitMasked(line,",","\"")
            #print "AfpACRRanges line:", next_range, cols
            if cols[colmap["NAME"]]: 
                    next_range = cols[colmap["NAME"]].strip()
            if next_range:
                if current_range and not next_range == current_range:
                    ranges[current_range] = range_data 
                    range_data = {}
                current_range = next_range
            if current_range:
                #print "AfpACRRanges MinMax:", cols[colmap["MIN"]], cols[colmap["MAX"]]
                if len(cols) > colmap["MAX"] and cols[colmap["MIN"]] and cols[colmap["MAX"]]: 
                    range_values = []
                    for i in range(colmap["MIN"], colmap["MAX"] + 1):
                        range_values.append(Afp_toInt(cols[i].strip()))
                    range_data[Afp_fromString(cols[colmap["CLG"]])] = range_values
                    #print "AfpACRRanges Values:", cols[colmap["CLG"]], range_values, range_data
                else:
                    if range_data:
                        ranges[current_range] = range_data
                        current_range = ""
                        next_range = ""
                        range_data = {}
                    #print "AfpACRRanges Data:", range_data, next_range
            else:
                if cols[colmap["NAME"]]: 
                    next_range = cols[colmap["NAME"]].strip()
        self.ranges = ranges
        self.midindex = int((colmap["MAX"] - colmap["MIN"])/2)
        if debug: self.view()
    ## extract salary target range from ranges
    # @param family - family for range
    # @param clg - clg-level for range
    # @param dait - dait to define upper or lower interval
    def get_range_target(self, family, clg, dait):
        if family in self.ranges:
            ranges = self.ranges[family]
            if clg in ranges:
                rang = ranges[clg]
                if dait == "I" or dait =="T":
                    return rang[1:]
                else:
                    return rang[:-1]
            else:
                print("AfpACRRanges WARNING CLG \""+ Afp_toString(clg) + "\" not in Ranges of", family + "!")
        else:
            print("AfpACRRanges WARNING Family \"" + family + "\" not in Ranges!")
        return None
    ## get relativ positioning of salary to target \n
    # return integer 
    # - == 0: in target range
    # - < 0: steps below target range
    # - > 0: steps above target range
    # @param value - value to be checked
    # @param family - family for range
    # @param clg - clg-level for range
    # @param dait - dait to define upper or lower interval
    def get_relativ_to_target(self, value, family, clg, dait):
        intervals = self.get_range_target(family, clg, dait)
        #print ("AfpACRRanges.get_relativ_to_target:", intervals)
        ind = None
        if not intervals is None: 
            ind = len(intervals)
            half = int(ind/2)
            for val in intervals:
                if value and value < val:
                    ind = intervals.index(val)
                    break
            ind -= half
        #print ("AfpACRRanges.get_relativ_to_target:", value, intervals, ind,  half, type(intervals), type(half))
        return ind, intervals[half-1:half+1]
    ## show data
    def view(self):
        print("AfpACRRanges:",self.midindex)
        for rang in self.ranges:
            print("AfpACRRanges", rang + ":", self.ranges[rang])
        
## class to handle personal data of one person
class AfpACRPerson(object):
    ## initialize AfpACRPerson class
    # @param nr - number of entry
    # @param values - dictionary of input values 
    # - values["ID"] - identifcator number of person
    # - values["NAME"] - name of person
    # - values["FAMILY"] - family name to identify salary ranges
    # - values["OTE"] - actuel on target earning
    # - values["FTE"] - actuel full time equvalent
    # - values["CLG"]- actuel career level grade
    # - values["DAIT"] - actuel dait grade
    # - values["PERF"] - actuel performance grade
    # - values["ACR-OTE"] - result OTE value for  ACR, if given
    # - values["ACR"] - result increase value for  ACR, if given
    # other values needed for boosters or killers, p.e.:
    # - values["PROMO"] - promotion
    # - values["VALID"] - validation value, if given
    # @param debug - flag for debug information
    def  __init__(self, nr, values, debug = False):
        if debug: print("AfpACRPerson._init:", nr, values)
        self.debug = debug
        self.nr = nr 
        self.id = None
        if "ID" in values:
            self.id = Afp_toInt(values["ID"])
        if "NAME" in values and  values["NAME"]: 
            self.name = values["NAME"]
        else:
            self.name = Afp_toString(self.nr)
        self.family = values["FAMILY"].strip()
        self.OTE = Afp_toInt(values["OTE"])
        self.set_fte(values["FTE"])
        self.ote = self.OTE * self.fte
        self.clg = Afp_fromString(values["CLG"])
        self.set_dait(values["DAIT"])
        self.perf_indicator = values["PERF"]
        self.validation_indicator = None
        if "VALID" in values: self.validation_indicator = values["VALID"].strip()
        self.acr_ote = None
        if "ACR-OTE" in values: self.acr_ote = Afp_toInt(values["ACR-OTE"])
        self.acr = None 
        if "ACR" in values: self.acr = Afp_toInt(values["ACR"])
        #print "AfpACRPerson.init ACR:", self.acr, "ACR" in values, values["ACR"], Afp_toInt(values["ACR"])
        # look for other needed columns
        value_names = ["ID", "NAME", "FAMILY", "OTE", "FTE", "CLG", "DAIT", "PERF", "ACR-OTE", "ACR"]
        self.columns = {}
        for name in values:
            if not name in value_names:
                self.columns[name] = values[name]
        # generated values
        self.positioning = None
        self.range_target = None
        self.performance = None
        self.booster = None
        self.eligible = True
        # result values
        self.percentage = None
        self.increase = None
        self.boosted_increase = None
        self.OTE_increase = None
        self.new_ote = None
        self.new_OTE = None
        #print "AfpACRPerson.init columns:", self.columns
    ## return if person holds all data for a valid computation
    def is_valid(self):
        return self.OTE and self.ote and not self.positioning is None and not self.performance is None
        #if not valid: print "AfpACRPerson.is_valid FAILED:", self.nr, self.id, self.name, self.valid, self.OTE, self.ote, self.positioning, self.performance
        #return valid
    ## return if person is valid and has the eligibillity 
    def is_eligible(self):
        return self.is_valid() and self.eligible 
    ## return if person is valid and has been boosted
    def is_boosted(self):
        if self.is_valid() :
            return not (self.booster is None) 
        return False
    ## return if person has the CLG DAIT grade
    #@param clg - clg-part of grade to be checked
    #@param dait - dait-part of-grade to be checked
    def is_grade(self, clg, dait):
        if clg == self.clg:
            if dait == self.dait or ( "1" in dait and self.dait == "D") or ("2" in dait and self.dait == "A") or ("3" in dait and self.dait == "I") or ("4" in dait and self.dait == "T"):
                return True
        return False
    ## check if person meets the requirements
    #@param id - id to be checked
    #@param ote - ote to be checked
    #@param clg - clg-part of grade to be checked
    #@param dait - dait-part of-grade to be checked
    #@param job - job family to be checked
    def check(self, id, ote=None, clg=None, dait=None, job=None):
        check = True
        if id: check = check & (self.get_id() == id)
        if ote: check = check & (self.get_ote() == ote)
        if clg and dait: check = check & self.is_grade(clg, dait)
        if job: check = check & (self.family == job)
        return check

    ## set fte as factor if percentage is given
    # @param fte - string holding the fte value
    def set_fte(self, fte):
        if fte:
            if Afp_isString(fte):
                if fte[-1] == "%":
                    fte = Afp_fromString(fte[:-1].strip())
                if Afp_isNumeric(fte):
                    fte = float(fte)/100
            self.fte = fte
        else:
            self.fte = 1.0
    ## set dait to defined values
    # @param dait - string holding the dait value
    def set_dait(self, dait):
        if "2" in dait:
            self.dait = "A"
        elif "3" in dait:
            self.dait = "I"
        elif "4" in dait:
            self.dait = "T"
        else:
            self.dait = "D"
    ## set positioning relativ to ranges
    # @param ranges - object holding salarie ranges
    def set_positioning(self, ranges):
        self.positioning, self.range_target = ranges.get_relativ_to_target(self.OTE, self.family, self.clg, self.dait)
        #if self.positioning is None: print("AfpACRPerson.set_positioning:", self.name, self.OTE, self.family, self.clg, self.dait, self.positioning)
        return self.positioning
    ## set performance relativ to input
    # @param ranges - object holding salarie ranges
    def set_performance(self, perf_indicators):
        if self.perf_indicator in perf_indicators:
            self.performance = perf_indicators[self.perf_indicator]
        else:
            print("AfpACRPerson WARNING \"", self.perf_indicator, "\" not in given performance indicators for " + self.name + "!")
        return self.performance
    ## set booster name
    # @param boosters - dictionary of all possible booster objects to boost percentage
    def set_booster(self, boosters):
        if boosters:
            for boost in boosters:
                if boost in self.columns and boosters[boost].is_applicable(self.columns[boost]):
                    self.booster = boost
                    break
        #if self.id == 425:
        #   print("AfpPerson.set_booster:", self.booster, self.id, boost in self.columns, self.columns[boost], boosters[boost].is_applicable(self.columns[boost]))
        #print "AfpPerson.set_booster:", self.booster, boosters, boost in self.columns, self.columns[boost], boosters[boost].is_applicable(self.columns[boost])
    ## set validation flag
    # @param invalidlist - list holding entries which flag this person not eligible
    # @param max_skip_perf - if given, performances below and equal this indicator are not eligible
    # @param max_ote_factor - if given, maximal factor of salaryrange midpoint being eligible
    # @param max_ote - if given, maximum OTE beeing eligible for acr
    def set_eligibillity(self, invalidlist, skip_perf, max_ote_factor = None, max_ote = None):
        #if self.validation_indicator.strip(): 
        #    print ("AfpACRPerson.set_eligibillity:", self.id, self.name, self.validation_indicator.strip())
        #    print ("AfpACRPerson.set_eligibillity:", invalidlist, self.validation_indicator in invalidlist)
        if invalidlist and self.validation_indicator and self.validation_indicator in invalidlist:
            #print ("AfpACRPerson.set_eligibillity FALSE:", self.id, self.name, self.validation_indicator)
            self.eligible = False
        if max_ote_factor:
            mid = (self.range_target[0] + self.range_target[1])/2.0
            if self.OTE > max_ote_factor*mid:
                self.eligible = False
        if max_ote and self.OTE > max_ote:
            self.eligible = False
        # don't allow performance below indicated value
        if not skip_perf is None and self.get_performance() <= skip_perf:
            self.eligible = False
    ## set ote proposal
    # @param percent - proposed increase percentage
    # @param boost - if given, proposed increase percentage for promotion (boosting)
    def set_proposal(self, percent, boost = None):
        self.percentage = percent
        if boost: 
            self.percentage = boost
            self.boosted_increase =  self.OTE*(boost - percent)/100
        self.increase = self.ote*self.percentage/100
        self.OTE_increase = self.OTE*self.percentage/100
        self.new_ote = self.ote + self.increase
        self.new_OTE = self.OTE + self.OTE_increase
    ## set to 0.01 rounded values
    # @param round -list holding keywords which values should be rounded
    def set_rounded_proposals(self, round):
        initial_increase = self.increase
        initial_OTE_increase = self.OTE_increase
        if "percent" in round:
            self.percentage  = int(self.percentage *100 + 0.5)/100.0
            self.increase = self.ote*self.percentage/100
            self.OTE_increase = self.OTE*self.percentage/100
        if "ote" in round:
            #self.increase = int(self.increase*100 + 0.5)/100.0
            self.increase = int(self.increase + 0.5)
        if "OTE" in round:
            #self.OTE_increase = int(self.OTE_increase*100 + 0.5)/100.0
            self.OTE_increase = int(self.OTE_increase + 0.5)
        self.new_ote = self.ote + self.increase
        self.new_OTE = self.OTE + self.OTE_increase
        rnd = abs(self.increase - initial_increase)
        rnd_OTE = abs(self.OTE_increase - initial_OTE_increase)
        if rnd > rnd_OTE: return rnd
        else: return rnd_OTE
    ## get name
    def get_id(self):
        if self.id:
            return self.id
        else:
            return self.nr
    ## get name
    def get_name(self):
        return self.name
    ## get range target
    def get_range_target(self):
        return self.range_target
    ## get promotion
    def get_promotion(self):
        return self.promotion
    ## get booster
    def get_booster(self):
        return self.booster
    ## get positioning
    def get_positioning(self):
        return self.positioning
    ## get performance indicator
    def get_perf_indicator(self):
        return self.performance, self.perf_indicator
    ## get performance
    def get_performance(self):
        return self.performance
    ## get ote value
    # @param fte - flag if full time ote should be returned
    # @param new - flag if new ote should be returned
    def get_ote(self, fte = True, new = False):
        if new:
            if fte: ote = self.new_OTE
            else: ote = self.new_ote
        else:
            if fte: ote = self.OTE
            else: ote = self.ote
        if ote is None: ote = 0.0
        return ote
    ## get increase value
    # @param fte - flag if full time increase should be returned
    # @param boosted - flag if additional boosted increase should be returned
    def get_increase(self, fte = True, boosted = False):
        if boosted:  inc = self.boosted_increase
        elif fte:  inc = self.OTE_increase
        else:  inc = self.increase
        if inc is None: inc = 0.0
        return inc
    ## get result acr increase value
    # @param fte - flag if full time increase should be returned
    def get_acr_increase(self, fte = True):
        inc = None
        if self.acr:
            if fte: inc = self.acr
            else: inc = self.acr*self.fte
        elif self.acr_ote:
            if fte:  inc = float(self.acr_ote - self.OTE)
            else:  inc =  float(self.acr_ote - self.OTE)*self.fte
        if inc is None: inc = 0.0
        return inc
    ## get result acr increase percent value
    # @param fte - flag if full time increase should be returned
    # @param red - manual reduction of used invrease
    def get_acr_percent(self, fte = True, red = None):
        inc = self.get_acr_increase(fte)
        if red: inc -= red
        percent = 0.0
        if inc:
            if fte: percent = 100.0*inc/self.OTE
            else:  percent = 100.0*inc/(self.OTE*self.fte)
        return int(percent*100)/100.0
    ## get row data for grids
    def get_row(self):
        boosted = "No"
        if self.booster: boosted = self.booster
        percent = Afp_toString(self.percentage)
        increase = Afp_toString(self.OTE_increase)
        if self.acr:
            #print "AfpACRPerson.get_row acr:", self.acr, self.get_acr_increase()
            increase += "  " + Afp_toString(self.get_acr_increase())
            if self.ote:
                percent += "  " + Afp_toString(self.get_acr_percent())
        return [Afp_fromString(self.name), self.family, Afp_toString(self.OTE), Afp_toString(self.fte), Afp_toString(self.clg), self.dait, Afp_toPos(self.positioning), Afp_toString(self.performance), boosted, percent, increase]
    ## show data
    # @param typ - indicator what should be shown
    def view(self, typ = None):
        if self.debug:  print("AfpACRPerson.view:", typ)
        if typ == "HELP" or typ == "help":
            print("\nOutput per person, possible types:")
            print("None or ALL: Id, Name, Jobfamily, OTE, FTE-factor, CLG, DAIT, positioning, performance, boosting, percentage of increase, new OTE")
            print("ACR:         Id, Name, planned percentage of increase, planned OTE increase, planned new OTE, real percentage, real increase, real new OTE, difference of increase")
            print("OTE:         Id, Name, FTE-factor, fulltime OTE, parttime OTE, percentage of increase, new fultime OTE, new parttime OTE")
            print("increase:    Id, Name, increase, percentage of increase")
            print("position:    Id, Name, OTE, positioning, target range")
            print("performance: Id, Name, result of performance review, performance, booster")
            print("DIFF:        Id, Name, OTE, 'DIFF:', difference of given ACR-value to computed ACR-result")
        if typ == "performance":
            print("AfpACRPerson.view performance:", self.get_id(), self.name, self.perf_indicator, self.performance, "Booster:", self.booster)
        elif typ == "position":
            print("AfpACRPerson.view position:", self.get_id(), self.name, self.OTE, self.positioning, self.get_range_target())
        elif typ == "increase":
            print("AfpACRPerson.view increase:", self.get_id(), self.name, self.increase, self.percentage, Afp_toString(self.increase), Afp_toString(self.percentage))#, "FULLTIME:", self.OTE_increase, self.new_OTE, "PARTTIME:", self.increase, self.new_ote
        elif typ == "OTE":
            print("AfpACRPerson.view OTE increase:", self.get_id(), self.name, self.fte, self.OTE, self.ote, "PLANNED INCREASE:", self.percentage,  self.new_OTE, self.new_ote)
        elif typ == "ACR":
            inc = self.get_acr_increase()
            res = self.get_acr_percent()
            print("AfpACRPerson.view ACR result:", self.get_id(), self.name, self.OTE, "PLANNED:", Afp_toString(self.percentage), Afp_toString(self.OTE_increase), Afp_toString(self.new_OTE), "RESULT:", Afp_toString(res), Afp_toString(inc), Afp_toString(self.acr), "DIFF:", Afp_toString(inc - self.OTE_increase))
        elif typ[:4] == "DIFF":
            limit = None
            if len(typ) > 4:
                limit = Afp_toInt(typ[4:])
            inc = self.get_acr_increase()
            diff = inc - self.OTE_increase
            if limit is None or diff > limit or -diff > limit:
                print("AfpACRPerson.view ACR difference:", self.get_id(), self.name, self.OTE, "DIFF:", Afp_toString(diff))
        elif typ is None or typ == "ALL":
            print("AfpACRPerson.view:", self.get_id(), self.name, self.family, self.OTE, self.fte, self.clg, self.dait, self.positioning, self.performance, self.booster, self.new_OTE)

## class to handle different booster possibillities for each person
class AfpACRMatrixBooster(object):
    ## initialize AfpACRMatrixBooster class
    # @param typ - typ of booster, possible types are '+' and '*'
    # @param value - value of booster to be applied
    # @param list - list of column values to allow use of this booster
    # @param matrix - if given, matrix for different booster values
    # @param debug - flag for debug information
    def  __init__(self, typ, value, list, matrix = None, debug = False):
        self.typ = typ
        self.value = value
        self.list = list
        self.matrix = matrix
        self.debug = debug
        if self.debug: print("AfpACRMatrixBooster Konstruktor:", self.typ, self.value, self.list, self.matrix)
    ## get given typ
    def get_typ(self):
        return self.typ
    ## get given value
    def get_value(self):
        return self.value
    ## get given conditions
    def get_list(self):
        return self.list
    ## get given matrix
    def get_matrix(self):
        return self.matrix
    ## apply booster on given value
    # @param in_matrix - matrix to be manipulated
    def gen_boosted_matrix(self, in_matrix):
        n = len(in_matrix)
        m = len(in_matrix[0])
        matrix = Afp_initMatrix(m, n, 0.0)
        for i in range(n):
            for j in range(m):
                if Afp_validMatrixField(i, j, self.matrix):
                    if self.typ == "*":
                        matrix[i][j] = in_matrix[i][j]*self.matrix[i][j]
                    else:
                        matrix[i][j] = in_matrix[i][j]+self.matrix[i][j]
                else:
                    if self.typ == "*":
                        matrix[i][j] = in_matrix[i][j]*self.value
                    else:
                        matrix[i][j] = in_matrix[i][j]+self.value
        return matrix
    ## check if this booster is applicable for the given column enty
    # @param colval - value to be checked against booster list
    def is_applicable(self, colval):
        if self.list and colval.strip() in self.list:
            return True
        else:
            return False
## class to handle data of all involved persons
class AfpACRPeopleManager(object):
    ## initialize AfpACRPeopleManager class
    # @param data - lines read fro  for used column indices
    # @param debug - flag for debug information
    def  __init__(self, data, colmap, debug = False):
        self.debug = debug
        self.names_available = None
        self.matrix_range = [None, None]
        self.persons = None
        #self.round = ["percent"]
        #self.round = ["OTE"]
        self.round = ["percent", "ote", "OTE"]
        #self.round = None
        self.rounded = None
        self.set_persons(data, colmap)
    ## extract column data from row
    #@param row - row holding data
    #@param colmap - original mappig
    #@param colmap_data - indices of mapfields in row
    def extract_cols(self, row, colmap, colmap_data):
        cols = {}
        for col in colmap: 
            if col in colmap_data:
                #cols[col] = row[colmap_data[col]].decode('iso8859_15')
                cols[col] = row[colmap_data[col]]
            else:
                cols[col] = ""
        #print "AfpACRPeopleManager.extract_cols cols:", cols
        return cols
    ## set person values from read lines
    # @param data - lines read from data file
    # @param colmap - dictionary for used column indices
    def set_persons(self, data, colmap):
        datacols = data[0].split(",")
        datacols[-1] = datacols[-1].strip()
        if self.debug: print("AfpACRPeopleManager.set_persons datacols:", datacols, "used:", colmap)
        colmap_data = {}
        for col in colmap:
            colname = colmap[col]
            if colname in datacols:
                colmap_data[col] = datacols.index(colname)
        if self.debug: print("AfpACRPeopleManager.set_persons:", colmap_data)
        names_given = False
        if "NAME" in colmap_data: names_given = True 
        no_promo = True
        if "PROMO" in colmap_data: no_promo = False
        merge = False
        if not names_given and self.persons and  self.names_available:
            merge = True
        persons = []
        count = 2
        for i in range(1,len(data)):
            #print "AfpACRPeopleManager.set_persons row:", i, data[i]
            cols = self.extract_cols(Afp_splitMasked(data[i], ",", "\""), colmap, colmap_data)
            if merge: cols = self.add_data_for_entry(count, cols, no_promo)
            if Afp_holdsValues(cols):
                #print "AfpACRPeopleManager.set_persons cols:",i, cols
                person = AfpACRPerson(count, cols, self.debug)
                persons.append(person)
                count += 1
        self.persons = persons
        self.names_available = names_given or merge
    ## set range of distribution matrix, range has to be symmetric to 0
    # @param dir - direction of range, 0 - social (positioning), 1  - performance
    # @param min - minimal value in this direction
    # @param max - maximal value in this direction
    def set_matrix_range(self, dir, min, max):
        if -min > max: max =  -min
        if -min < max: min =  -max
        self.matrix_range[dir] = [min, max]
    ## display percentage of people with OTE above midpoint of range
    # @param fac -faktor to scale range midpoint
    # @param list -flag if all counted persons should be listed
    def ote_above_rangemid(self, fac=None, list=False):
        if fac is None: fac = 1.0
        count = 0
        cnt = 0
        noelig = 0
        for person in self.persons:
            if person.is_eligible():
                mid = (person.range_target[0] + person.range_target[1])/2
                if person.OTE > fac*mid: 
                    cnt += 1 
                    if list: print("AfpACRPeopleManager.ote_above_rangemid counted:", person.get_name(), person.get_ote(), person.clg, person.dait)
                count +=1
            else:
                noelig += 1
        percent = 100.0 *cnt/count
        ptotal = 100.0 *(cnt+noelig)/count
        print("AfpACRPeopleManager.ote_above_rangemid used faktor:", fac, "People above, nor eligible:", cnt, noelig, "Percentage above, above-below:", Afp_toString(percent), Afp_toString(ptotal))
    ## display all acr value given outside manager range
    # @param matrix - matrix holding actuel manager ranges
    # @param outside - flag, if values outside the range should be displayed
    # @param boosters - if given, possible increase boosters
    # @param add - if given, value that had been added to increase
    # @param precent_flag - if given, flag if value is givfen in percents
    def acr_manager_range(self, matrix, outside = True, boosters = None,  add = None, percent_flag = False):
        found = False
        sum = 0.0
        count = 0
        for person in self.persons:
            if not person.is_eligible(): continue
            count += 1
            i = self.get_matrix_index(1, person.get_performance())
            j = self.get_matrix_index(0, person.get_positioning())
            split = matrix[i][j].split("-")
            min = Afp_fromString(split[0].strip())
            max = Afp_fromString(split[1].strip()) 
            promo = 0
            if boosters and person.is_boosted():
                boost = person.get_booster()
                if boost in boosters:
                    bmat = boosters[boost].get_matrix()
                    if bmat:
                        promo = bmat[i][j]
                    else:
                        promo = boosters[boost].get_value()
                    min += promo
                    max += promo
            percent = 0
            if add:
                percent = add
                if not percent_flag:
                    percent = (add*100.0)/person.get_ote()
                min += percent
                max += percent
            acr = person.get_acr_percent()
            if outside:
                if acr < (min - 0.01) or acr > (max + 0.01):
                    found = True
                    if add:
                        print("AfpACRPeopleManager.acr_manager_range outside:", person.get_id(), person.get_name(), Afp_toString(add), Afp_toString(percent), Afp_toString(promo), Afp_toString(acr), "OUTSIDE RANGE ", Afp_toString(min),  Afp_toString(max))
                    else:
                        print("AfpACRPeopleManager.acr_manager_range outside:", person.get_id(), person.get_name(), Afp_toString(promo), Afp_toString(acr), "OUTSIDE RANGE ", Afp_toString(min),  Afp_toString(max))
            else:
                factor = (acr - min)/(max - min)
                sum += factor
                print("AfpACRPeopleManager.acr_manager_range factor:", person.get_id(), person.get_name(), Afp_toString(promo), Afp_toString(acr), "RANGE ", Afp_toString(min),  Afp_toString(max), "FACTOR ", Afp_toString(factor))
        if not outside:
            print("AfpACRPeopleManager.acr_manager_range average factor:", Afp_toString(sum/count))
        elif not found:
            print("AfpACRPeopleManager.acr_manager_range outside: no persons found outside range!")
   ## set positioning due to input ranges
    # @param ranges - object holding salarie ranges
    def set_positioning(self, ranges):
        min = max = 0
        for person in self.persons:
            p = person.set_positioning(ranges)
            if not p is None:
                if p < min: min = p
                elif p > max: max = p
        self.set_matrix_range(0, min, max)
    ## set performance due to input indicators
    # @param perf_indicators - dictionary holding all performance indicators
    def set_performance(self, perf_indicators):
        min = max = 0
        for person in self.persons:
            p = person.set_performance(perf_indicators)
            if p:
                if p < min: min = p
                elif p > max: max = p
        self.set_matrix_range(1, min, max)
    ## set booster name if applicable
    # @param boosters - dictionary holding all booster values
    def set_boosters(self, boosters):
        #print "ACRPeopleManager.set_boosters:", boosters
        for person in self.persons:
            person.set_booster(boosters)
    ## set invalid flag due to input indicators
    # @param  invalidlist - list holding entries which flag this person not eligible
    # @param max_skip_perf - if given, performances below and equal this indicator are not eligible
    # @param max_ote_factor - if given, maximal factor of salaryrange midpoint beeng eligible
    # @param max_ote - if given, maximum OTE beeing eligible for acr
    def set_eligibillity(self, invalidlist, skip_perf = None, max_ote_factor = None, max_ote = None):
        #print ("AfpACRPeopleManager.set_eligibillity:", invalidlist, max_ote_factor, max_ote)
        for person in self.persons:
            person.set_eligibillity(invalidlist, skip_perf, max_ote_factor, max_ote)
    ## set ote increase proposals
    # @param matrix - list holding all increase percentages
    # @param bmatrices - dictionary holding lists holding all increase percentage for the different boosters
    def set_ote_proposals(self, matrix, bmatrices = None):
        self.rounded = 0.0
        for person in self.persons:
            if person.is_eligible():
                i = self.get_matrix_index(1, person.get_performance())
                j = self.get_matrix_index(0, person.get_positioning())
                p = matrix[i][j]
                pp = None
                if bmatrices:
                    boost = person.get_booster()
                    if boost:
                        pp = bmatrices[boost][i][j]
            else:
                p = 0.0
                pp = None
            #print "AfpACRPeopleManager.set_ote_proposals:", i, j, person.get_name(),  person.is_eligible(), "PERF:",person.get_performance(), "POS:", person.get_positioning(), p, pp
            person.set_proposal(p, pp)
            if self.round: self.rounded += person.set_rounded_proposals(self.round)
    ## get ranges for distribution matrix
    def are_valid(self):
        valid = True
        for person in self.persons:
            valid = valid and person.is_valid()
        return valid
    ## get name from person given by other indicators
    # @param nr - number of line
    # @param cols - values to be set in this line
    # @param boost - flag if boosted information should also be transfered
    def add_data_for_entry(self, nr, cols, boost = False):
        id = nr
        if "ID" in cols:
            id = Afp_toInt(cols["ID"])
        ote = None
        clg = None
        dait = None
        job = None
        if "OTE" in cols and "CLG" in cols and "DAIT" in cols and "FAMILY" in cols:
            ote = Afp_toInt(cols["OTE"])
            clg = Afp_fromString(cols["CLG"])
            dait = Afp_fromString(cols["DAIT"])
            job = Afp_fromString(cols["FAMILY"])
        # if "ID" is not applicable also other values p.e. "OTE" may be used
        found = False
        for person in self.persons:
            #if person.check(id):
            if person.check(None, ote, clg, dait):
                cols["NAME"] = person.get_name()
                if boost and person.is_boosted():
                    cols["PROMO"] = "TRUE"
                found = True
                break
        if not found: print("AfpACRPerson WARNING:\"", id, ote, clg, dait, "\", name not found during merge!")
        return cols
    ## get ranges for distribution matrix
    def get_matrix_range(self):
        return self.matrix_range
    ## get lendth of wanted dimension of distribution matrix
    # @param dir - direction of range, 0 - social (positioning), 1  - performance
    def get_matrix_length(self, dir):
        return int(self.matrix_range[dir][1] - self.matrix_range[dir][0] + 1)
    ## get index of the position in range
    # @param dir - direction of range, 0 - social (positioning), 1  - performance
    # @param pos - position in range
    def get_matrix_index(self, dir, pos):
        # as a low positioning needs a higher increase and 0 equals '=', 
        # use the *-1 value to generate the matrix index
        if dir == 0: pos *= -1
        return int(pos - self.matrix_range[dir][0])
    ## get performance indicator dictionary
    def get_performance_indicators(self):
        perf_inds= [None]*self.get_matrix_length(1)
        stop = False
        for person in self.persons:
            perf, indicator = person.get_perf_indicator()
            ind = self.get_matrix_index(1, perf)
            if perf_inds[ind] is None: 
                perf_inds[ind] = indicator
                if Afp_isFilled(perf_inds): stop = True
                if stop: break
        return perf_inds
    ## generate booster ote sum
    # @param boost - name of booster to be respected
    # @param fte - flag if fulltime ote should be used
    # @param inc - flag if increase should be used instead of ote
    def get_booster_sum(self, boost, fte = True, inc = False):
        sum = 0.0
        for person in self.persons:
            if person.get_booster() == boost and person.is_eligible():
                if inc:
                    sum += person.get_increase(fte, True)
                else:
                    sum += person.get_ote(fte)
        return sum
   ## generate increase sum
    # @param fte - flag if fulltime increase should be used
    # @param all - flag if all persons should be counted or only valid persons count
    def get_increase_sum(self, fte = True, all = True):
        sum = 0.0
        for person in self.persons:
            if all or person.is_eligible():
                sum += person.get_increase(fte)
        return sum
   ## generate increase sum
    # @param fte - flag if fulltime increase should be used
    # @param all - flag if all persons should be counted or only valid persons count
    def get_acr_increase_sum(self, fte = True, all = True):
        sum = 0.0
        for person in self.persons:
            if all or person.is_eligible():
                sum += person.get_acr_increase(fte)
        return sum
    ## generate OTE sum
    # @param fte - flag if fulltime OTE should be used
    # @param new - flag if new OTE values should be used
    # @param all - flag if all OTE should be counted or only valid persons count
    def get_ote_sum(self, fte = True, new = False, all = True):
        sum = 0.0
        for person in self.persons:
            if all or person.is_eligible():
                sum += person.get_ote(fte, new)
        return sum
    ## generate matrix field sums, only valid persons can be counted
    # @param fte - flag if fulltime OTE should be used
    # @param type - type different sums than OTE, actuel "Inc" = Increase  and 'cnt' = count are supported
    # @param promo - flag if only promoted persons should be counted
    def get_matrix_sums(self, fte = True, type = None, promo = False):
        if type and type == "cnt": init = 0
        else: init = 0.0
        # generate empty array
        matrix = Afp_initMatrix(self.get_matrix_length(0), self.get_matrix_length(1), init)
        sum = init
        for person in self.persons: 
            valid = person.is_eligible()
            if promo: valid = valid and person.get_promotion()
            if valid:
                i = self.get_matrix_index(1, person.get_performance())
                j = self.get_matrix_index(0, person.get_positioning())
                #print "AfpACRPeopleManager.get_matrix_sums:", i, j, matrix, matrix[i]
                if type:
                    if type == "Inc": matrix[i][j] += person.get_increase(fte)
                    elif type == "cnt": matrix[i][j] += 1
                else: 
                    matrix[i][j] += person.get_ote(fte)
            else:
                if type:
                    if type == "Inc": sum += person.get_increase(fte)
                    elif type == "cnt": sum += 1
                else: sum += person.get_ote(fte)
        return sum, matrix
    ## get grid data
    def get_grid_data(self):
        data = []
        for person in self.persons:
            data.append(person.get_row())
        return data
    ## display data
    # @param typ -type of display
    def view(self, typ = None):
        if typ == "HELP" or typ == "help":
            print("PEOPLE ABOVE [ALL] factor:     number of people and percentage of people above range-midpoint*'factor'")
            if len(self.persons): 
                self.persons[0].view(typ)
            print("\nResult output after person output:")
            print("DIFF:        ACR difference SUMS: sum, absolut sum; Min/Max: minimum and maximum value; Average: average value of differences")   
            return
        else:
            print("AfpACRPeopleManager.view:", typ)
        if "PEOPLE" in typ:
            if typ[:12] == "PEOPLE ABOVE":
                fac = None
                list = False
                if typ[:16] == "PEOPLE ABOVE ALL":
                    list = True
                    fstrg = typ[17:]
                else:
                    fstrg = typ[13:]
                if fstrg:
                    fac = Afp_numericString(fstrg, None)
                self.ote_above_rangemid(fac, list)
        elif typ[:4] == "DIFF":
            sum = 0
            suma = 0
            cnt = 0
            maxa = 0
            min = 0
            max = 0
            for person in self.persons:
                person.view(typ)
                diff = person.get_acr_increase() - person.OTE_increase
                sum += diff
                if diff < 0: suma -= diff
                else: suma += diff
                cnt += 1
                if diff < min: min = diff
                if diff > max: max = diff
            aver = suma/cnt
            print("AfpACRPeopleHandler.view ACR difference SUMS:", sum, suma, "Min/Max:", min, max, "Average:", aver)
        else:
            for person in self.persons:
                person.view(typ)

# Main  executable program 
if __name__ == "__main__":
    execute = True
    check = False
    debug = False
    filename = None
    rangefile = None
    budget = None
    focal = None
    part = None
    ref = None
    display = None
    lgh = len(sys.argv)
    ev_indices = []
    for i in range(1,lgh):
        if sys.argv[i] == "-m" or sys.argv[i] == "--market": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": rangefile = sys.argv[i+1]
        if sys.argv[i] == "-d" or sys.argv[i] == "--data": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": filename = sys.argv[i+1] 
        if sys.argv[i] == "-b" or sys.argv[i] == "--budget": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": budget = sys.argv[i+1] 
        if sys.argv[i] == "-f" or sys.argv[i] == "--focal": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": focal = sys.argv[i+1] 
        if sys.argv[i] == "-r" or sys.argv[i] == "--refer": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": ref = sys.argv[i+1] 
        if sys.argv[i] == "-s" or sys.argv[i] == "--show": 
            ev_indices.append(i+1)
            if i < lgh-1 and sys.argv[i+1][0] != "-": display = sys.argv[i+1] 
        if sys.argv[i] == "-c" or sys.argv[i] == "--check": check = True
        if sys.argv[i] == "-p" or sys.argv[i] == "--part": part = True
        if sys.argv[i] == "-v" or sys.argv[i] == "--verbose": debug = True
        if sys.argv[i] == "-h" or sys.argv[i] == "--help": execute = False
    if execute:
        conffile = None
        if lgh > 1 and sys.argv[lgh-1][0] != "-"  and not lgh-1 in ev_indices:
            conffile = sys.argv[lgh-1]
        AfpACRCalculator_main(conffile, filename, rangefile, budget, ref, focal, part, check, display, debug) 
    else:
        print("usage: AfpACRCalculator [option] configuration")
        print("AfpACRCalculator calculates a complete ACR distribution from given data.")
        print("If a percentage or the -f option is given only a simulation with this values will be performed.")
        print("Options and arguments:")
        print("-h, --help     display this text")
        print("-b, --budget   budget in percent from OTE sum to be distributed")
        print("-c, --check    checks increase against budget, works for distribution calculation not for simulation only")
        print("-d, --data     name of data file to be loaded (only csv files are supported)")
        print("               a data file has to be supplied")
        print("-f, --focal    focal percentage to be used for simulation, if no reference is given")
        print("-m, --market   name of market salary range file (only csv files are supported)")
        print("               a salary range file has to be supplied")
        print("-p, --part     flag if part-time should be respected during distribution calculation")
        print("-r, --refer    reference percentage to be used for simulation")
        print("-s, --show     show generated people data, following types may follow: ")
        print("               - performance: name/number, performance, performance index, PROMO:, promotion, promotion flag")
        print("               - position: name/number, 100% OTE, positioning, applied range")
        print("               - OTE: name/number, FTE factor, 100% OTE, payable OTE, INCREASE:, increase percentage, new 100% OTE, new payable OTE")
        print("               - increase: name/number, 100% OTE, increase percentage")
        print("               - data: name/number, job family, 100% OTE, FTE factor, CLG, DAIT, positioning index, performance index, promotion flag, increase percentage, new 100% OTE")
        print("-v,--verbose   display comments on all actions (debug-information)")
        print("configuration  name of configuration file name, the entries in this file are: 'PARAMETRE_NAME = paramter value',")
        print("               this file may hold the following parameter:")
        print("        BUDGET section:")
        print("               BUDGET_PERCENTAGE, as option -b")
        print("               BUDGET_FIXUM, optional additional value to be added to the budget")
        print("          DATA section:")
        print("               DATA_FILE_NAME, as option -d")
        print("               DATA_COLUMN_MAP, mapping of the file columns to the following indicators:")
        print("                                NAME, FAMILY, OTE, FTE, CLG, DAIT, PERF, ACR-OTE, ACR, PROMO, VALID")
        print("                               p.e: 'DATA_COLUMN_MAP = {\"NAME\":\"Name\",\"OTE\":\"Gehalt\"}'")
        print("               DATA_PERFORMANCE_MAP, mapping of the PERF column values to the relativ matrix indices")
        print("                               p.e: 'DATA_PERFORMANCE_MAP = {\"Below\":-1, \"Achieved\":0, \"Exceed\":1}'")
        print("               DATA_PROMOTION_LIST, (deprecated use DATA_BOOSTER_MAP) list of the PROMO column values to indicate promotion")
        print("                               p.e: 'DATA_PROMOTION_LIST = [\"Promotion\",\"promoted\"]'")
        print("               DATA_BOOSTER_MAP, dictionary of booster data (replaces DATA_PROMOTION_LIST), CAUTION: key values must also occur in the DATA_COLUMN_MAP")
        print("                               p.e: 'DATA_BOOSTER_MAP = {\"PROMO\": {\"Typ\": \"+\", \"Value\": 2, \"List\": [\"x1\", ...], \"Matrix\": [[0, 0, 0], [2, 2, 2], [3, 3, 3]]}, ... }'")
        print("                                     Typ: + or *, Value or Matrix must be given, List: holding values in column to initiate this booster")
        print("   ELIGIBILITY section:") 
        print("               DATA_INVALID_LIST,  list of VALID column values to indicate this entry is NOT eligible")
        print("                               p.e: 'DATA_INVALID_LIST = [\"Termination\", \"Individual agreement\"]'")
        print("               ELIGIBLE_OTE_MAXIMUM,  maximal OTE beeing eligible for ACR")
        print("               ELIGIBLE_RELATIV_OTE_FACTOR,  maximal OTE beeing eligible for ACR, relativ to salary range midpoin")
        print("  salary RANGE section:") 
        print("               RANGE_FILE_NAME, as option -m")
        print("               RANGE_COLUMN_MAP, mapping of the file columns indices to the following indicators: NAME, CLG, MIN, MAX")
        print("                               p.e: 'RANDE_COLUMN_MAP = {\"NAME\":0, \"CLG\":1, \"MIN\":3, \"MAX\":5}'")
        print("                               p.e: 'RANDE_COLUMN_MAP = {\"NAME\":\"A\", \"CLG\":\"B\", \"MIN\":\"D\", \"MAX\":\"F\"}'")
        print("        MATRIX section:") 
        print("               MATRIX_SPREAD_MAP, map how spread is applied over the result matrix (p.e. for a 3x3 matrix)")
        print("                               p.e: 'MATRIX_SPREAD_MAP = [[0.8, 0.9, 1.0], [0.9, 1.0, 1.1], [1.0, 1.1, 1.2]]'")
        print("               MATRIX_MANAGER_FACTOR, manager range factor to be applied where no other value is available")
        print("               MATRIX_MANAGER_MAP, map how the manager range is applied over the result matrix (p.e. for a 3x3 matrix)")
        print("                               p.e: 'MATRIX_MANAGER_MAP = [[0.25, 0.25, 0.25], [None, None, None], [None, None, 1.0]]'")
        print("               MATRIX_MANAGER_FOCAL, percentage of manager range to generate focal values")
        print("               MATRIX_PROMOTION_PREMIUM, (deprecated, is included in DATA_BOOSTER_MAP) promotion premium percentage or matrix of promotion premium percentages")
        print("                               p.e: 'MATRIX_PROMOTION_PREMIUM = 2.0,'")
        print("                               p.e: 'MATRIX_PROMOTION_PREMIUM = [[2.0, 2.0, 2.0], [2.0, 2.0, 2.0], [2.0, 2.0, 2.0]]'")
        print("   CALCULATION section:") 
        print("               CALC_USE_FOCAL_FOR_RANGE  = 1, use focal value to calculate manager-range instead of reference value")
        print("               CALC_SKIP_SPREAD_ZEROS = 1, skip focal simulation/calculation for 0.0 fields in spreadmap (lower than plan column)")
        print()
