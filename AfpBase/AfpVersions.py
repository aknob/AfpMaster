#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package BusAfp
# \n
#   History: \n
#        25 Feb. 2026 - inital version generated - Andreas.Knoblauch@afptech.de
#
#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#   Copyright© 1989 - 2026 afptech.de (Andreas Knoblauch)
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

def AfpVersions():
    versions = {}
    versions["Base"] = "10.2.1"
    versions["AfpCash"] = "1.0.0"
    versions["AfpMotor"] = "2.0.2"
    versions["AfpFaktura"] = versions["AfpMotor"]
    versions["AfpVerein"] = "0.9.1" 
    versions["AfpEvent"] = versions["AfpVerein"] + " strict"  
    versions["BusAfp"] = "6.1.1 beta"
    return versions
