#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpAdresse.AfpAdSqlTemplate
# AfpAdSqlTemplate provides routines to implement mysql database tables for address handling,
#
#   History: \n
#        13 Nov. 2018 - inital code generated - Andreas.Knoblauch@afptech.de \n

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

## get dictionary with required database tables and mysql generation code
# @param flavour - if given flavour of modul
def AfpAdresse_getSqlTables(flavour = None):
    required = {}
    # address table
    required["ADRESSE"] = """CREATE TABLE `ADRESSE` (
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `Vorname` tinytext COLLATE latin1_german2_ci NOT NULL,
  `Name` tinytext COLLATE latin1_german2_ci NOT NULL,
  `Strasse` tinytext CHARACTER SET latin1,
  `Plz` char(5) CHARACTER SET latin1 DEFAULT NULL,
  `Ort` tinytext CHARACTER SET latin1,
  `Telefon` tinytext CHARACTER SET latin1,
  `Geburtstag` date DEFAULT NULL,
  `Reise` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Miet` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Kontakt` date DEFAULT NULL,
  `Bez` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Bem` tinytext CHARACTER SET latin1,
  `Kennung` smallint(6) NOT NULL,
  `NamSort` tinytext CHARACTER SET latin1,
  `Tel2` tinytext CHARACTER SET latin1,
  `Fax` tinytext CHARACTER SET latin1,
  `Mail` tinytext CHARACTER SET latin1,
  `BemExt` char(20) CHARACTER SET latin1 DEFAULT NULL,
  `Geschlecht` char(1) CHARACTER SET latin1 NOT NULL,
  `Anrede` char(3) CHARACTER SET latin1 NOT NULL,
  `SteuerNr` char(20) CHARACTER SET latin1 DEFAULT NULL,
  PRIMARY KEY (`KundenNr`),
  KEY `KundenNr` (`KundenNr`),
  KEY `Plz` (`Plz`),
  KEY `Ort` (`Ort`(50)),
  KEY `Bez` (`Bez`),
  KEY `NamSort` (`Name`(50),`Vorname`(20)),
  KEY `Name` (`Name`(50))
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # archiv table
    required["ARCHIV"] = """CREATE TABLE `ARCHIV` (
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `Art` char(25) CHARACTER SET latin1 NOT NULL,
  `Typ` char(25) CHARACTER SET latin1 NOT NULL,
  `Gruppe` char(50) CHARACTER SET latin1 NOT NULL,
  `Bem` tinytext CHARACTER SET latin1,
  `Extern` tinytext CHARACTER SET latin1 NOT NULL,
  `Datum` date NOT NULL,
  `Tab` varchar(10) CHARACTER SET latin1 DEFAULT NULL,
  `TabNr` mediumint(9) DEFAULT NULL,
  KEY `KundenNr` (`KundenNr`),
  KEY `Extern` (`Extern`(50)),
  KEY `Datum` (`Datum`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # address attribut table
    required["ADRESATT"] = """CREATE TABLE `ADRESATT` (
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL DEFAULT '00000000',
  `Name` tinytext CHARACTER SET latin1,
  `Attribut` char(20) CHARACTER SET latin1 NOT NULL,
  `AttNr` smallint(5) DEFAULT NULL,
  `AttText` tinytext CHARACTER SET latin1,
  `Tag` tinytext CHARACTER SET latin1,
  `Aktion` tinytext CHARACTER SET latin1,
  KEY `KundenNr` (`KundenNr`),
  KEY `Name` (`Name`(50)),
  KEY `AttKdNr` (`Attribut`,`KundenNr`),
  KEY `AttName` (`Attribut`,`Name`(50))
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    #  table
    required["ANFRAGE"] = """CREATE TABLE `ANFRAGE` (
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `Datum` date NOT NULL,
  `Info` tinytext CHARACTER SET latin1 NOT NULL,
  `Zustand` smallint(6) NOT NULL,
  `KdNrInfo` tinytext CHARACTER SET latin1 NOT NULL,
  KEY `KundenNr` (`KundenNr`),
  KEY `Datum` (`Datum`),
  KEY `Zustand` (`Zustand`),
  KEY `KdNrInfo` (`KundenNr`,`Info`(50))
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # fill 'no address' value into table 'Adresse'
    required["ADRESSE"] += """INSERT INTO `ADRESSE` VALUES 
    (00000000, '', 'keine Adresse', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 'n', '', NULL);
    UPDATE `ADRESSE` SET `KundenNr`='00000000' WHERE `KundenNr`='00000001';
    ALTER TABLE `ADRESSE` AUTO_INCREMENT = 1;"""
    # return values
    return required

