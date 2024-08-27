#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AfpAudioSetTagsFromHierarchy sets, as the name says, the tag of an audiofile 
# according to the values from the directory hierarchy
#
#
#   History: \n
#        29 May 2022 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is an extract of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2018  afptech.de (Andreas Knoblauch)
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






from mutagen.easyid3 import EasyID3

audio = EasyID3("example.mp3")
audio['title'] = u"Example Title"
audio['artist'] = u"Me"
audio['album'] = u"My album"
audio['composer'] = u"" # clear
audio.save()

