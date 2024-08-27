#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpCharter.AfpChSqlTemplate
# AfpChSqlTemplate provides routines to implement mysql database tables for event handling,
#
#   History: \n
#        13 Nov. 2018 - inital code generated - Andreas.Knoblauch@afptech.de \n

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2022 afptech.de (Andreas Knoblauch)
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

## get dictionary with required database tables and mysql generation code
# @param flavour - if given flavour of modul
def AfpCharter_getSqlTables(flavour = None):
    required = {}
    # charter tour table
    required["FAHRTEN"] = """CREATE TABLE `FAHRTEN` (
  `FahrtNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `Abfahrt` date NOT NULL,
  `Fahrtende` date DEFAULT NULL,
  `Abfahrtsort` tinytext CHARACTER SET latin1,
  `Zielort` tinytext CHARACTER SET latin1 NOT NULL,
  `Personen` smallint(6) DEFAULT NULL,
  `Art` char(10) CHARACTER SET latin1 NOT NULL,
  `Km` smallint(6) DEFAULT NULL,
  `Ausland` smallint(6) DEFAULT NULL,
  `Kostenst` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Preis` float(8,2) DEFAULT NULL,
  `AuftragPreis` float(8,2) DEFAULT NULL,
  `Datum` date NOT NULL,
  `Extra` float(8,2) DEFAULT NULL,
  `Brief` text CHARACTER SET latin1,
  `Vorgang` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Kontakt` tinytext CHARACTER SET latin1,
  `Zustand` char(16) CHARACTER SET latin1 NOT NULL,
  `Auftrag` date DEFAULT NULL,
  `Von` char(5) CHARACTER SET latin1 NOT NULL,
  `Nach` char(10) CHARACTER SET latin1 NOT NULL,
  `RechNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `SortNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Name` tinytext CHARACTER SET latin1,
  `Zahlung` float(8,2) DEFAULT NULL,
  `ZahlDat` date DEFAULT NULL,
  `ExAusl` float(8,2) DEFAULT NULL,
  `PersPreis` float(8,2) DEFAULT NULL,
  `EinsatzNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `BerichtNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `ExText` text CHARACTER SET latin1,
  `Ausstattung` tinytext CHARACTER SET latin1,
  `KontaktNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  PRIMARY KEY (`FahrtNr`),
  KEY `KundenNr` (`KundenNr`),
  KEY `Abfahrt` (`Abfahrt`),
  KEY `Zielort` (`Zielort`(50)),
  KEY `Vorgang` (`Vorgang`),
  KEY `RechNr` (`RechNr`),
  KEY `SortNr` (`SortNr`),
  KEY `Name` (`Name`(50)),
  KEY `EinsatzNr` (`EinsatzNr`),
  KEY `FahrtNr` (`FahrtNr`)
) ENGINE=InnoDB AUTO_INCREMENT=8386 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # charter tour extra prices table
    required["FAHRTEX"] = """CREATE TABLE `FAHRTEX` (
  `FahrtNr` mediumint(8) unsigned zerofill NOT NULL,
  `Extra` tinytext NOT NULL,
  `Preis` float(5,2) NOT NULL,
  `Info` char(2) NOT NULL,
  `Inland` char(1) NOT NULL,
  `noPausch` char(4) NOT NULL,
  KEY `FahrtNr` (`FahrtNr`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # charter tour information table
    required["FAHRTI"] = """CREATE TABLE `FAHRTI` (
  `FahrtNr` mediumint(8) unsigned zerofill NOT NULL,
  `Adresse1` tinytext NOT NULL,
  `Abfahrtszeit` time NOT NULL,
  `Adresse2` tinytext,
  `Ankunftszeit` float(5,0) DEFAULT NULL,
  `Datum` date NOT NULL,
  `Datum2` date DEFAULT NULL,
  KEY `FahrtNr` (`FahrtNr`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # charter tour sequence table
    required["FAHRTVOR"] = """CREATE TABLE `FAHRTVOR` (
  `VorgangsNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `Bez` tinytext NOT NULL,
  `SortBez` tinytext,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `Bez2` tinytext,
  PRIMARY KEY (`VorgangsNr`),
  KEY `VorgangsNr` (`VorgangsNr`),
  KEY `SortBez` (`KundenNr`,`Bez2`(2),`Bez`(20))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # insert 'Charter' output possibillities into 'AUSGABE' table
    required["AUSGABE"] = """INSERT INTO `AUSGABE` VALUES 
    (0,'Charter','KVA','','Kva','Kostenvoranschlag',''),
    (0,'Charter','KVA','','Kvap','Kostenvoranschlag (pro Person)',''),
    (0,'Charter','Angebot','','Angb','Angebot',''),
    (0,'Charter','Angebot','','Ange','Angebot (ohne Unterschrift)',''),
    (0,'Charter','Angebot','','Angp','Angebot (pro Person)',''),
    (0,'Charter','Auftrag','','Auft','Auftrag',''),
    (0,'Charter','Auftrag','','Aufp','Auftrag (pro Person)',''),
    (0,'Charter','Auftrag','Storno','Stauft','Auftragsstornierung',''),
    (0,'Charter','Rechnung','','Rech','Rechnung',''),
    (0,'Charter','Rechnung','Storno','Strech','Rechnungsstornierung',''),
    (0,'Charter','Mahnung','','Mahn','Mahnung','');"""



