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
def AfpFinance_getSqlTables(flavour = None):
    required = {}
    # main table for accounting values
    required["BUCHUNG"] = """CREATE TABLE `BUCHUNG` (
  `BuchungsNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `Datum` date NOT NULL,
  `Konto` mediumint(8) unsigned zerofill NOT NULL,
  `KtName` tinytext DEFAULT NULL,
  `Gegenkonto` mediumint(8) unsigned zerofill NOT NULL,
  `GktName` tinytext DEFAULT NULL,
  `Beleg` char(10) DEFAULT NULL,
  `Betrag` float(6,2) NOT NULL,
  `KundenNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Bem` tinytext NOT NULL,
  `Art` char(20) NOT NULL,
  `BelegDatum` date DEFAULT NULL,
  `Tab` varchar(10) DEFAULT NULL,
  `TabNr` mediumint(9) DEFAULT NULL,
  `VorgangsNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Reference` char(20) DEFAULT NULL,
  `Period` char(12) DEFAULT NULL,
  `Eintrag` date NOT NULL,
  `Expo` date DEFAULT NULL,
  PRIMARY KEY (`BuchungsNr`),
  KEY `BuchungsNr` (`BuchungsNr`),
  KEY `Datum` (`Datum`),
  KEY `Konto` (`Konto`),
  KEY `Gegenkonto` (`Gegenkonto`),
  KEY `KundenNr` (`KundenNr`),
  KEY `VorgangsNr` (`VorgangsNr`),
  KEY `Eintrag` (`Eintrag`),
  KEY `Period` (`Period`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;"""
    required["KTNR"] = """CREATE TABLE `KTNR` (
  `KtName` char(5) CHARACTER SET latin1 NOT NULL,
  `KtNr` mediumint(8) unsigned zerofill NOT NULL,
  `Bezeichnung` varchar(45) CHARACTER SET latin1 NOT NULL,
  `KtStand` smallint(6) NOT NULL,
  `Typ` char(10) CHARACTER SET latin1 NOT NULL,
  KEY `KtName` (`KtName`),
  KEY `KtNr` (`KtNr`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # fill initial table data
    if flavour == "Tourist":
        required["KTNR"] += """INSERT INTO `KTNR` VALUES 
    ('SALDO',00001000,'Finanzfluss',0,'Kasse,Bank'),
    ('BAR',00001600,'Barkasse',0,'Kasse'),
    ('VB',00001803,'Volksbank',0,'Bank'),    
    ('SALDO',00004000,'Einnahmen',0,'Ertrag'),
    ('ERL',00004100,'Erlöse',0,'Ertrag'),('ERL01',00004001,'Erlöse Januar',0,'Ertrag'),('ERL02',00004002,'Erlöse Februar',0,'Ertrag'),
    ('ERL03',00004003,'Erlöse März',0,'Ertrag'),('ERL04',00004004,'Erlöse April',0,'Ertrag'),('ERL05',00004005,'Erlöse Main',0,'Ertrag'),
    ('ERL06',00004006,'Erlöse Juni',0,'Ertrag'),('ERL07',00004007,'Erlöse Juli',0,'Ertrag'),('ERL08',00004008,'Erlöse August',0,'Ertrag'),
    ('ERL09',00004009,'Erlöse September',0,'Ertrag'),('ERL10',00004010,'Erlöse Oktober',0,'Ertrag'),('ERL11',00004011,'Erlöse November',0,'Ertrag'),('ERL12',00004012,'Erlöse Dezember,0,'Ertrag'),
    ('EMF',00004151,'Erlös Inland.',0,'Ertrag'),('EMFA',00004150,'Erlös Ausland',0,'Ertrag'),   
    ('SALDO',00008000,'Ausgaben,0,'kosten'),
    ('SKTO',00008731,'SkontoAufw',0,'Kosten'), 
    ('DIV.A',00010001,'Debitor',0,'Debitor'),('DIV.B',00010500,'Debitor',0,'Debitor'),('DIV.C',00011000,'Debitor',0,'Debitor'),
    ('DIV.D',00011500,'Debitor',0,'Debitor'),('DIV.E',00011800,'Debitor',0,'Debitor'),('DIV.F',00012000,'Debitor',0,'Debitor'),
    ('DIV.G',00012400,'Debitor',0,'Debitor'),('DIV.H',00013000,'Debitor',0,'Debitor'),('DIV.I',00013900,'Debitor',0,'Debitor'),
    ('DIV.J',00014000,'Debitor',0,'Debitor'),('DIV.K',00014200,'Debitor',0,'Debitor'),('DIV.L',00015100,'Debitor',0,'Debitor'),
    ('DIV.M',00015500,'Debitor',0,'Debitor'),('DIV.N',00016100,'Debitor',0,'Debitor'),('DIV.O',00016300,'Debitor',0,'Debitor'),
    ('DIV.P',00016500,'Debitor',0,'Debitor'),('DIV.Q',00016500,'Debitor',0,'Debitor'),('DIV.R',00016900,'Debitor',0,'Debitor'),
    ('DIV.S',00017500,'Debitor',0,'Debitor'),('DIV.T',00018900,'Debitor',0,'Debitor'),('DIV.U',00019100,'Debitor',0,'Debitor'),
    ('DIV.V',00019200,'Debitor',0,'Debitor'),('DIV.W',00019400,'Debitor',0,'Debitor'),('DIV.X',00019500,'Debitor',0,'Debitor'),
    ('DIV.Y',00019500,'Debitor',0,'Debitor'),('DIV.Z',00019500,'Debitor',0,'Debitor'),('DIVER',00019999,'Debitor',0,'System'),
    ('DIVER',00070000,'Kreditor',0,'Kreditor');"""
    elif flavour == "Verein":
        required["KTNR"] += """INSERT INTO `KTNR` VALUES 
    ('SALDO',00001000,'Finanzfluss',0,'Kasse,Bank'),
    ('BAR',00001600,'Barkasse',0,'Kasse'),
    ('BLS',00001610,'Bank Girokonto',0,'Bank'),
    ('ZTF',00001690,'Geldtransit',0,'System'),
    ('SALDO',00004000,'Ausgaben',0,'Kosten'),
    ('AB',00004200,'Ausgaben laufender Betrieb',0,'Kosten'),
    ('SKTO',00004201,'Skonto Aufwand',0,'Kosten'),
    ('VS',00004205,'Versicherungen',0,'Kosten'),
    ('BG',00004209,'Bankgebühren',0,'Kosten'),
    ('AB',00004210,'Abgaben, Steuern',0,'Kosten'),
    ('REP',00004300,'Reparaturen, Unterhalt',0,'Kosten'),
    ('EN',00004310,'Unterhalt - Energiekosten',0,'Kosten'),
    ('UM',00004320,'Neu-  und Umbauprojekte',0,'Kosten'),
    ('BO',00004350,'Boote, Zubehör',0,'Kosten'),
    ('VA',00004400,'Veranstaltungen',0,'Kosten'),
    ('SP',00004410,'Sportbetrieb',0,'Kosten'),
    ('VE',00004810,'Verbände',0,'Kosten'),
    ('SALDO',00008000,'Einnahmen',0,'Ertrag'),
    ('EBT',00008100,'Mitgliedsbeiträge',0,'Ertrag'),
    ('EBF',00008109,'Mitgliedsbeiträge Folgejahr',0,'Ertrag'),
    ('ESP',00008200,'Spenden natürliche Person',0,'Ertrag'),
    ('ESA',00008210,'Spenden anonym',0,'Ertrag'),
    ('GAU',00008300,'Aufnahmegebühr',0,'Ertrag'),
    ('GBP',00008410,'Gebühr Bootsliegeplatz',0,'Ertrag'),
    ('GNA',00008420,'Gebühr nicht geleistete Arbeitsstunden',0,'Ertrag'),
    ('GA',00008430,'Gebühr Nutzung Sportanalage, Dusche, WC',0,'Ertrag'),
    ('GE',00008440,'Gebühr Einlagerung',0,'Ertrag'),
    ('ZU',00008800,'Zuschüsse allgemein',0,'Ertrag'),
    ('DIVER',00010000,'Debitor',0,'Debitor'),
    ('DIVER',00070000,'Kreditor',0,'Kreditor');"""
    else:
        required["KTNR"] += """INSERT INTO `KTNR` VALUES 
    ('SALDO',00001000,'Finanzfluss',0,'Kasse,Bank'), 
    ('BAR',00001600,'Barkasse',0,'Kasse'),
    ('BK',00001610,'Bank',0,'Bank'),
    ('ZTF',00001690,'Geldtransit',0,'System'),   
    ('SALDO',00004000,'Ausgaben',0,'Kosten'),
    ('AW',00004200,'Aufwände',0,'Kosten'),
    ('SKTO',00004201,'SkontoAufw',0,'Kosten'),    
    ('SALDO',00008000,'Einnahmen,0,'Ertrag'),
    ('ERL',00008100,'Erlöse',0,'Ertrag'),
    ('DIVER',00010000,'Debitor',0,'Debitor'),
    ('DIVER',00070000,'Kreditor',0,'Kreditor');"""
    # table for bank account reference
    required["AUSZUG"] = """ CREATE TABLE `AUSZUG` (
  `Auszug` char(11) CHARACTER SET latin1 NOT NULL,
  `BuchDat` date NOT NULL,
  `Datum` date NOT NULL,
  `StartSaldo` float(7,2) DEFAULT NULL,
  `EndSaldo` float(7,2) DEFAULT NULL,
  `Period` varchar(12) NOT NULL,
  `KtNr` mediumint(8) unsigned zerofill NOT NULL,
  KEY `Auszug` (`Auszug`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    required["ADRESATT"] = """INSERT INTO `ADRESATT` VALUES 
    (0,NULL,'SEPA Kreditor ID',NULL,NULL,NULL,'Kreditor ID (anzeigen)'),
    (0,NULL,'Bankverbindung',NULL,NULL,NULL,'IBAN,BIC');"""
    # return data
    return required
    