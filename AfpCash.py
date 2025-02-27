#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package BusAfp
# AfpVerein is part of the open source BusAfp project,
# it is a software to manage invoicing and other tasks in the motor related business \n
#    Copyright© 1989 - 2025 afptech.de (Andreas Knoblauch) \n
# \n
#   History: \n
#        10 Jan 2019 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    AfpEvent is a software to manage events
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


import AfpBase
from AfpBase import AfpStart

# only needed if code is compiled with py2exe
#import AfpAdresse.AfpAdScreen
#import AfpEvent.AfpEvScreen

# main program
name = 'AfpCash (Barkasse)'     
version = "1.0.0 beta"    
website = 'http://www.afptech.de'
description = """AfpCash ist eine Barkasse."""
picture = "AfpCash_relief.png"
moduls = ["Finance:Cash"]
AfpCash = AfpBase.AfpStart.AfpSoftwareInformation(name, moduls, description, picture, website, version)
AfpBase.AfpStart.AfpStart(AfpCash)
      
 

   
