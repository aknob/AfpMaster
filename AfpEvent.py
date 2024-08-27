#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package BusAfp
# AfpEvent is part of the open source BusAfp project,
# it is a software to manage invoicing and other tasks in the motor related business \n
#    Copyright© 1989 - 2019 afptech.de (Andreas Knoblauch) \n
# \n
#   History: \n
#        17 May 2018 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    AfpEvent is a software to manage events
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

# only needed if code is compiled with py2exe
#import AfpAdresse.AfpAdScreen
#import AfpEvent.AfpEvScreen
# if database has to be created
#import AfpAdresse.AfpAdSqlTemplate
#import AfpEvent.AfpEvSqlTemplate


# main program
name = 'AfpEvent'     
#version = "0.9.1 beta"    
version = "0.9.1 strict beta"    
website = 'http://www.busafp.de'
description = """AfpEvent ist eine Verwaltungsprogramm für Veranstaltungen.
Es enthält Anmeldungs- und Stornierungsverwaltung, sowie eine mitgeführte Buchhaltung, Zahlungsverfolgung
und diverse weiter nützliche Hilfsmittel."""
picture = "AfpEvent_relief.png"
moduls = ["Adresse","Event"]
AfpEvent = AfpBase.AfpStart.AfpSoftwareInformation(name, moduls, description, picture, website, version)
AfpBase.AfpStart.AfpStart(AfpEvent)
      
 

   