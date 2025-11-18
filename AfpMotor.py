#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package BusAfp
# AfpMotor is part of the open source BusAfp project,
# it is a software to manage invoicing and other tasks in the motor related business \n
#    Copyright© 1989 - 2025  afptech.de (Andreas Knoblauch) \n
# \n
#   History: \n
#        16 Jan. 2017 - separate software specific code from parameter extraction - Andreas.Knoblauch@afptech.de \n
#        30 Nov. 2016 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    AfpMotor is a software to manage invoicing and other tasks in the motor related business
#    Copyright© 1989 - 2025  afptech.de (Andreas Knoblauch)
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
name = 'AfpMotor'     
version = "2.0.2 alpha"    
website = 'http://www.afpmotor.de'
description = """AfpMotor ist eine Verwaltungsprogramm für den Werkstatteinsatz 
für Motoristen und in der Kfz-Branche.
Es enthält eine mitgeführte Buchhaltung, Zahlungsverfolgung, Einsatzplanung
und diverse weiter nützliche Hilfsmittel."""
picture = "AfpMotor_relief.png"
moduls = ["Adresse","Faktura"]
AfpMotor = AfpBase.AfpStart.AfpSoftwareInformation(name, moduls, description, picture, website, version)
AfpBase.AfpStart.AfpStart(AfpMotor)
      
 

   