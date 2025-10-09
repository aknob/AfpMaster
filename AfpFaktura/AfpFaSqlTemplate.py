#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpFaktura.AfpFaSqlTemplate
# AfpFaSqlTemplate provides routines to implement mysql database tables for faktura handling,
#
#   History: \n
#        01 Okt. 2025 - inital code generated - Andreas.Knoblauch@afptech.de \n

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2025  afptech.de (Andreas Knoblauch)
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
def AfpFaktura_getSqlTables(flavour = None):
    required = {}
    # address table
    required["ADMEMO"] = """CREATE TABLE `ADMEMO` (
  `MemoNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `Datum` date NOT NULL,
  `Memo` text CHARACTER SET latin1 COLLATE latin1_german2_ci NOT NULL,
  `Zustand` char(10) DEFAULT NULL,
  `Typ` char(10) DEFAULT NULL,
  `TypNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  PRIMARY KEY (`MemoNr`),
  UNIQUE KEY `MemoNr_UNIQUE` (`MemoNr`),
  KEY `KundenNr` (`KundenNr`),
  KEY `Memo` (`Memo`(50)),
  KEY `Zustand` (`Zustand`),
  KEY `TypNr` (`TypNr`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
   # article buying discount table
    required["ARTDIS"] = """CREATE TABLE `ARTDIS` (
  `HersNr` smallint NOT NULL,
  `PreisGrp` char(5) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL,
  `LieferantNr` smallint NOT NULL,
  `Rabatt` float(3,1) NOT NULL,
  KEY `LieferantNr` (`LieferantNr`),
  KEY `HersNr` (`HersNr`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # article manufacturer  table
    required["ARTHERS"] = """CREATE TABLE `ARTHERS` (
  `HersNr` smallint NOT NULL AUTO_INCREMENT,
  `Hersteller` varchar(20) NOT NULL,
  `KundenNr` smallint NOT NULL,
  `Kennung` char(3) NOT NULL,
  `Datei` varchar(45) NOT NULL,
  PRIMARY KEY (`HersNr`),
  UNIQUE KEY `HersNr_UNIQUE` (`HersNr`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
   # article table
    required["ARTIKEL"] = """CREATE TABLE `ARTIKEL` (
  `ArtikelNr` tinytext CHARACTER SET latin1 COLLATE latin1_german2_ci NOT NULL,
  `Bezeichnung` tinytext CHARACTER SET latin1 COLLATE latin1_german2_ci NOT NULL,
  `Bestand` float(6,1) DEFAULT '0.0',
  `Mindestbestand` float(4,0) DEFAULT '0',
  `Einkaufspreis` float(9,2) NOT NULL,
  `Eingang` date DEFAULT NULL,
  `Rabatt` tinyint DEFAULT NULL,
  `Handelsspanne` tinyint DEFAULT NULL,
  `Listenpreis` float(9,2) NOT NULL,
  `Nettopreis` float(9,2) NOT NULL,
  `Sonderpreis` float(9,2) DEFAULT NULL,
  `PreisGrp` char(5) CHARACTER SET latin1 COLLATE latin1_german2_ci NOT NULL,
  `HersNr` smallint DEFAULT NULL,
  `Lagerort` char(15) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL,
  `EAN` char(13) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL,
  `Code39` char(6) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL,
  `Label` char(6) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL,
  KEY `ArtikelNr` (`ArtikelNr`(50)),
  KEY `Bezeichnung` (`Bezeichnung`(50)),
  KEY `EAN` (`EAN`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
   # article selling surcharge table
    required["ARTSUR"] = """CREATE TABLE `ARTSUR` (
  `HersNr` smallint NOT NULL,
  `PreisGrp` char(5) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL,
  `Handelsspanne` smallint NOT NULL,
  KEY `HersNr` (`HersNr`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
   # order table
    required["BESTELL"] = """CREATE TABLE `BESTELL` (
  `RechNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `Datum` date NOT NULL,
  `Bem` text,
  `Pos` smallint DEFAULT NULL,
  `Ust` char(1) DEFAULT NULL,
  `Netto` float(7,2) NOT NULL,
  `Betrag` float(7,2) NOT NULL,
  `ZahlDat` date DEFAULT NULL,
  `Zahlung` float(7,2) NOT NULL,
  `Zustand` char(7) NOT NULL,
  `Typ` char(7) DEFAULT NULL,
  `TypNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  PRIMARY KEY (`RechNr`),
  KEY `RechNr` (`RechNr`),
  KEY `KundenNr` (`KundenNr`),
  KEY `Datum` (`Datum`),
  KEY `TypNr` (`TypNr`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
  # order content table
    required["BESTIN"] = """CREATE TABLE `BESTIN` (
  `RechNr` mediumint NOT NULL,
  `PosNr` tinyint NOT NULL,
  `ErsatzteilNr` char(15) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL,
  `Bezeichnung` text CHARACTER SET latin1 COLLATE latin1_german2_ci,
  `Anzahl` float(5,1) DEFAULT NULL,
  `Einzelpreis` float(8,2) DEFAULT NULL,
  `Gesamtpreis` float(9,2) DEFAULT NULL,
  `Lieferung` float(5,1) DEFAULT NULL,
  `Datum` date DEFAULT NULL,
  `Hsp` smallint DEFAULT NULL,
  `Rabatt` smallint DEFAULT NULL,
  `Nr` tinyint DEFAULT NULL,
  `Zeile` tinytext CHARACTER SET latin1 COLLATE latin1_german2_ci,
  KEY `RechNr` (`RechNr`),
  KEY `ErsatzteilNr` (`ErsatzteilNr`),
  KEY `Bezeichnung` (`Bezeichnung`(50))
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
  # offer table
    required["KVA"] = """CREATE TABLE `KVA` (
  `RechNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `AttNr` smallint(5) unsigned zerofill DEFAULT NULL,
  `Datum` date NOT NULL,
  `Bem` text,
  `Pos` smallint DEFAULT NULL,
  `Ust` char(1) DEFAULT NULL,
  `Netto` float(7,2) NOT NULL,
  `Betrag` float(7,2) NOT NULL,
  `Kontierung` mediumint(8) unsigned zerofill NOT NULL,
  `Zustand` char(10) NOT NULL,
  `Gewinn` float(7,2) DEFAULT NULL,
  `Typ` char(7) DEFAULT NULL,
  `TypNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Ausgabe` char(10) DEFAULT NULL,
  `BerichtNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  PRIMARY KEY (`RechNr`),
  KEY `RechNr` (`RechNr`),
  KEY `KundenNr` (`KundenNr`),
  KEY `Datum` (`Datum`),
  KEY `Zustand` (`Zustand`),
  KEY `TypNr` (`TypNr`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
  # offer content table
    required["KVAIN"] = """CREATE TABLE `KVAIN` (
  `RechNr` mediumint NOT NULL,
  `PosNr` tinyint NOT NULL,
  `ErsatzteilNr` char(15) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL,
  `Bezeichnung` text CHARACTER SET latin1 COLLATE latin1_german2_ci,
  `Anzahl` float(5,1) DEFAULT NULL,
  `Einzelpreis` float(8,2) DEFAULT NULL,
  `Gesamtpreis` float(9,2) DEFAULT NULL,
  `KundenRabatt` float(2,0) DEFAULT NULL,
  `Gewinn` float(9,2) DEFAULT NULL,
  `Nr` tinyint DEFAULT NULL,
  `Zeile` tinytext CHARACTER SET latin1 COLLATE latin1_german2_ci,
  KEY `RechNr` (`RechNr`),
  KEY `ErsatzteilNr` (`ErsatzteilNr`),
  KEY `Bezeichnung` (`Bezeichnung`(50))
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
  # invoice content table
    required["RECHIN"] = """CREATE TABLE `RECHIN` (
  `RechNr` mediumint NOT NULL,
  `PosNr` tinyint NOT NULL,
  `ErsatzteilNr` char(15) CHARACTER SET latin1 COLLATE latin1_german2_ci DEFAULT NULL,
  `Bezeichnung` text CHARACTER SET latin1 COLLATE latin1_german2_ci,
  `Anzahl` float(5,1) DEFAULT NULL,
  `Einzelpreis` float(8,2) DEFAULT NULL,
  `Gesamtpreis` float(9,2) DEFAULT NULL,
  `KundenRabatt` float(2,0) DEFAULT NULL,
  `Gewinn` float(9,2) DEFAULT NULL,
  `Nr` tinyint DEFAULT NULL,
  `Zeile` tinytext CHARACTER SET latin1 COLLATE latin1_german2_ci,
  KEY `ErsatzteilNr` (`ErsatzteilNr`),
  KEY `Bezeichnung` (`Bezeichnung`(50)),
  KEY `RechNr` (`RechNr`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
   # fill 'no address' value into table 'Adresse'
   # required["ADRESSE"] += """INSERT INTO `ADRESSE` VALUES 
   #(00000000, '', 'keine Adresse', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, NULL, NULL, NULL, NULL, NULL, 'n', '', NULL);
   # UPDATE `ADRESSE` SET `KundenNr`='00000000' WHERE `KundenNr`='00000001';
   #ALTER TABLE `ADRESSE` AUTO_INCREMENT = 1;"""
   # return values
    return required

