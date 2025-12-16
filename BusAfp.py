#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package BusAfp
# BusAfp is a software to manage coach and travel acivities \n
#    Copyright© 1989 - 2018  afptech.de (Andreas Knoblauch) \n
# \n
#   History: \n
#        16 Jan. 2017 - separate software spexcific code from parameter extraction - Andreas.Knoblauch@afptech.de \n
#        26 Aug. 2015 - change direct execution parameter to normal input, to be used via os - Andreas.Knoblauch@afptech.de \n
#        11 Jun. 2015 - enable direct routine execution via command line option - Andreas.Knoblauch@afptech.de \n
#        23 May 2015 - enable variable setting via command line option - Andreas.Knoblauch@afptech.de \n
#        19 Okt. 2014 - adapt package hierarchy - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2012 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright© 1989 - 2019 afptech.de (Andreas Knoblauch)
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
from AfpBase import AfpStart

# main program
name = "BusAfp"
version = "6.1.1 beta"
description = """BusAfp ist eine Verwaltungsprogramm für den Buseinsatz 
für Mietfahrten, sowie der Organisation von eigenen Reisen.
Es enthält eine mitgeführte Buchhaltung, Zahlungsverfolgung, Einsatzplanung
und diverse weiter nützliche Hilfsmittel."""
picture = "Bus_relief.png"
website = "http://www.busafp.de"
#moduls = ["Adresse","Charter","Tourist"]
moduls = ["Adresse","Charter","Event:Tourist"]
BusAfp = AfpBase.AfpStart.AfpSoftwareInformation(name, moduls, description, picture, website)
AfpBase.AfpStart.AfpStart(BusAfp)