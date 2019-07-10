# -*- coding: utf-8 -*-

## @package AfpFinance.AfpFiSqlTemplate
# AfpFiSqlTemplate provides routines to implement mysql database tables for bookkeeping,
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
def AfpFinance_getSqlTables(flavour = None):
    required = {}
    # main table for accounting values
    required["BUCHUNG"] = """CREATE TABLE `BUCHUNG` (
  `BuchungsNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `Datum` date NOT NULL,
  `Konto` mediumint(8) unsigned zerofill NOT NULL,
  `KtName` char(20) DEFAULT NULL,
  `Gegenkonto` mediumint(8) unsigned zerofill NOT NULL,
  `GktName` char(20) DEFAULT NULL,
  `Beleg` char(10) NOT NULL,
  `Betrag` float(6,2) NOT NULL,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `Bem` tinytext NOT NULL,
  `Art` char(10) NOT NULL,
  `Von` tinytext NOT NULL,
  `VorgangsNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Reference` char(20) DEFAULT NULL,
  `Eintrag` date NOT NULL,
  `Expo` date DEFAULT NULL,
  PRIMARY KEY (`BuchungsNr`),
  KEY `BuchungsNr` (`BuchungsNr`),
  KEY `Datum` (`Datum`),
  KEY `Konto` (`Konto`),
  KEY `Gegenkonto` (`Gegenkonto`),
  KEY `KundenNr` (`KundenNr`),
  KEY `Von` (`Von`),
  KEY `VorgangsNr` (`VorgangsNr`),
  KEY `Eintrag` (`Eintrag`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1;"""


CREATE TABLE `BUCHUNG` (
  `BuchungsNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `Datum` date NOT NULL,
  `Konto` mediumint(8) unsigned zerofill NOT NULL,
  `Gegenkonto` mediumint(8) unsigned zerofill NOT NULL,
  `Beleg` char(10) NOT NULL,
  `Betrag` float(6,2) NOT NULL,
  `KtName` char(20) DEFAULT NULL,
  `GktName` char(20) DEFAULT NULL,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `KtDat` char(15) DEFAULT NULL,
  `GktDat` char(15) DEFAULT NULL,
  `Bem` tinytext NOT NULL,
  `Art` char(10) NOT NULL,
  `Von` char(20) NOT NULL,
  `VorgangsNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Expo` date DEFAULT NULL,
  `Eintrag` date NOT NULL,
  PRIMARY KEY (`BuchungsNr`),
  KEY `BuchungsNr` (`BuchungsNr`),
  KEY `Datum` (`Datum`),
  KEY `KtName` (`KtName`),
  KEY `GktName` (`GktName`),
  KEY `KundenNr` (`KundenNr`),
  KEY `KtDat` (`KtDat`),
  KEY `GktDat` (`GktDat`),
  KEY `Von` (`Von`),
  KEY `VorgangsNr` (`VorgangsNr`),
  KEY `Eintrag` (`Eintrag`)
) ENGINE=InnoDB AUTO_INCREMENT=54 DEFAULT CHARSET=latin1;


    required["KTNR"] = """CREATE TABLE `KTNR` (
  `KtName` char(5) CHARACTER SET latin1 NOT NULL,
  `KtNr` mediumint(8) unsigned zerofill NOT NULL,
  `Bezeichnung` char(20) CHARACTER SET latin1 NOT NULL,
  `KtStand` smallint(6) NOT NULL,
  `Typ` char(10) CHARACTER SET latin1 NOT NULL,
  KEY `KtName` (`KtName`),
  KEY `KtNr` (`KtNr`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # fill initial table data
    if flavour == "Tourist":
        required["KTNR"] += """INSERT INTO `KTNR` VALUES 
    ('BAR',00001600,'Barkasse',0,'Kasse'),
    ('VB',00001803,'Volksbank',0,'Bank'),
    ('ERL',00004000,'Erlöse',0,'System'),('ERL01',00004001,'Erlöse Januar',0,'Erlös'),('ERL02',00004002,'Erlöse Februar',0,'Erlös'),
    ('ERL03',00004003,'Erlöse März',0,'Erlös'),('ERL04',00004004,'Erlöse April',0,'Erlös'),('ERL05',00004005,'Erlöse Main',0,'Erlös'),
    ('ERL06',00004006,'Erlöse Juni',0,'Erlös'),('ERL07',00004007,'Erlöse Juli',0,'Erlös'),('ERL08',00004008,'Erlöse August',0,'Erlös'),
    ('ERL09',00004009,'Erlöse September',0,'Erlös'),('ERL10',00004010,'Erlöse Oktober',0,'Erlös'),('ERL11',00004011,'Erlöse November',0,'Erlös'),('ERL12',00004012,'Erlöse Dezember,0,'Erlös'),
    ('EMF',00004151,'Erlös Inland.',0,'System'),('EMFA',00004150,'Erlös Ausland',0,'System'),
    ('SKTO',00004731,'SkontoAufw',0,'System'),
    ('DIV.A',00010001,'Debitor',0,'Debitor'),('DIV.B',00010500,'Debitor',0,'Debitor'),('DIV.C',00011000,'Debitor',0,'Debitor'),
    ('DIV.D',00011500,'Debitor',0,'Debitor'),('DIV.E',00011800,'Debitor',0,'Debitor'),('DIV.F',00012000,'Debitor',0,'Debitor'),
    ('DIV.G',00012400,'Debitor',0,'Debitor'),('DIV.H',00013000,'Debitor',0,'Debitor'),('DIV.I',00013900,'Debitor',0,'Debitor'),
    ('DIV.J',00014000,'Debitor',0,'Debitor'),('DIV.K',00014200,'Debitor',0,'Debitor'),('DIV.L',00015100,'Debitor',0,'Debitor'),
    ('DIV.M',00015500,'Debitor',0,'Debitor'),('DIV.N',00016100,'Debitor',0,'Debitor'),('DIV.O',00016300,'Debitor',0,'Debitor'),
    ('DIV.P',00016500,'Debitor',0,'Debitor'),('DIV.Q',00016500,'Debitor',0,'Debitor'),('DIV.R',00016900,'Debitor',0,'Debitor'),
    ('DIV.S',00017500,'Debitor',0,'Debitor'),('DIV.T',00018900,'Debitor',0,'Debitor'),('DIV.U',00019100,'Debitor',0,'Debitor'),
    ('DIV.V',00019200,'Debitor',0,'Debitor'),('DIV.W',00019400,'Debitor',0,'Debitor'),('DIV.X',00019500,'Debitor',0,'Debitor'),
    ('DIV.Y',00019500,'Debitor',0,'Debitor'),('DIV.Z',00019500,'Debitor',0,'Debitor'),('DIVER',00019999,'Debitor',0,'System'),
    ('DIVER',00070000,'Kreditor',0,'Kreditor');""".decode("UTF-8")
    else:
        required["KTNR"] += """INSERT INTO `KTNR` VALUES 
    ('BAR',00001600,'Barkasse',0,'Kasse'),
    ('BK',00001610,'Bank',0,'Bank'),
    ('ERL',00008100,'Erlöse',0,'System'),
    ('SKTO',00004201,'SkontoAufw',0,'System'),
    ('DIVER',00010000,'Debitor',0,'Debitor'),
    ('DIVER',00070000,'Kreditor',0,'Kreditor');""".decode("UTF-8")
    # table for bank accunt reference
    required["AUSZUG"] = """ CREATE TABLE `AUSZUG` (
  `Auszug` char(11) CHARACTER SET latin1 NOT NULL,
  `BuchDat` date NOT NULL,
  `Datum` date NOT NULL,
  `AnfSaldo` float(7,2) DEFAULT NULL,
  `EndSaldo` float(7,2) DEFAULT NULL,
  `Auszug2` char(17) CHARACTER SET latin1 DEFAULT NULL,
  `Beleg` char(12) CHARACTER SET latin1 DEFAULT NULL,
  `KtNr` mediumint(8) unsigned zerofill NOT NULL,
  `KtDat` char(12) CHARACTER SET latin1 DEFAULT NULL,
  KEY `Auszug` (`Auszug`),
  KEY `Auszug2` (`Auszug2`),
  KEY `KtDat` (`KtDat`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    required["ADRESATT"] = """INSERT INTO `ADRESATT` VALUES 
    (0,NULL,'SEPA Kreditor ID',NULL,NULL,NULL,'Kreditor ID (anzeigen)'),
    (0,NULL,'Bankverbindung',NULL,NULL,NULL,'IBAN,BIC');"""
    # return data
    return required
    