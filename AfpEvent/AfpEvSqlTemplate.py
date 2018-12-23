#!/usr/bin/python
# -*- coding: utf-8 -*-

## @package AfpEvent.AfpEvSqlTemplate
# AfpEvSqlTemplate provides routines to implement mysql database tables for event handling,
#
#   History: \n
#        13 Nov. 2018 - inital code generated - Andreas.Knoblauch@afptech.de \n

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright© 1989 - 2016  afptech.de (Andreas Knoblauch)
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
# @param flavour - if given flavour of moduls
def AfpEvent_getSqlTables(flavour = None):
    required = {}
    # event table
    required["EVENT"] = """CREATE TABLE `EVENT` (
  `EventNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `Kostenst` mediumint(8) unsigned zerofill NOT NULL,
  `RechNr` smallint(6) NOT NULL,
  `Bez` tinytext NOT NULL,
  `Kennung` char(20) DEFAULT NULL,
  `Beginn` date NOT NULL,
  `Uhrzeit` time NULL,
  `Ende` date NULL,
  `Route` smallint(6) NOT NULL,
  `Personen` smallint(6) NOT NULL,
  `MaxPers` smallint(6) DEFAULT NULL,
  `Anmeldungen` smallint(6) NOT NULL,
  `Preis` float(8,2) DEFAULT NULL,
  `Menge` smallint(6) DEFAULT NULL,
  `Art` char(5) DEFAULT NULL,
  `Bem` tinytext,
  `IntText` text,
  `EventTyp` char(15) DEFAULT NULL,
  `TypNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `EinsatzNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `AgentNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `AgentName` tinytext,
  `Kreditor` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Debitor` mediumint(8) unsigned zerofill DEFAULT NULL,
  `ErloesKt` char(5) DEFAULT NULL,
  PRIMARY KEY (`EventNr`),
  KEY `FahrtNr` (`EventNr`),
  KEY `Bez` (`Bez`(50)),
  KEY `Beginn` (`Beginn`),
  KEY `Route` (`Route`),
  KEY `EinsatzNr` (`EinsatzNr`),
  KEY `TypNr` (`TypNr`),
  KEY `AgentNr` (`AgentNr`),
  KEY `Kennung` (`Kennung`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # event prices table
    required["PREISE"] = """CREATE TABLE `PREISE` (
  `EventNr` mediumint(8) unsigned zerofill NOT NULL,
  `PreisNr` smallint(6) NOT NULL,
  `Bezeichnung` tinytext NOT NULL,
  `Plaetze` smallint(6) DEFAULT NULL,
  `Anmeldungen` smallint(6) DEFAULT NULL,
  `Preis` float(7,2) NOT NULL,
  `Kennung` int(11) DEFAULT NULL,
  `Typ` char(20) DEFAULT NULL,
  `NoPrv` smallint(6) DEFAULT NULL,
  `ListKenn` char(3) DEFAULT NULL,
  KEY `FahrtNr` (`EventNr`),
  KEY `Kennung` (`Kennung`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # event registration table
    required["ANMELD"] = """CREATE TABLE `ANMELD` (
  `AnmeldNr` mediumint(8) unsigned zerofill NOT NULL AUTO_INCREMENT,
  `KundenNr` mediumint(8) unsigned zerofill NOT NULL,
  `EventNr` mediumint(8) unsigned zerofill NOT NULL,
  `AgentNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `RechNr` tinytext NOT NULL,
  `Anmeldung` date NOT NULL,
  `Ab` smallint(6) DEFAULT NULL,
  `PreisNr` mediumint(8) unsigned zerofill NOT NULL,
  `Preis` float(8,2) NOT NULL,
  `Extra` float(8,2) DEFAULT NULL,
  `Transfer` float(8,2) DEFAULT NULL,
  `Bem` tinytext,
  `ExtText` text,
  `Anzdatum` date DEFAULT NULL,
  `Zahlung` float(8,2) DEFAULT NULL,
  `ZahlDat` date DEFAULT NULL,
  `UmbEvent` mediumint(8) unsigned zerofill DEFAULT NULL,
  `UmbVon` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Info` tinytext,
  `InfoDat` date DEFAULT NULL,
  `BerichtNr` mediumint(8) unsigned zerofill DEFAULT NULL,
  `ExtDatei` char(20) DEFAULT NULL,
  `Zustand` char(12) NOT NULL,
  `ProvPreis` float(8,2) DEFAULT NULL,
  PRIMARY KEY (`AnmeldNr`),
  KEY `AnmeldNr` (`AnmeldNr`),
  KEY `KundenNr` (`KundenNr`),
  KEY `FahrtNr` (`EventNr`),
  KEY `AgentNr` (`AgentNr`),
  KEY `RechNr` (`RechNr`(50)),
  KEY `Anmeldung` (`Anmeldung`),
  KEY `Ab` (`Ab`),
  KEY `PreisNr` (`PreisNr`),
  KEY `Zustand` (`Zustand`)
) ENGINE=InnoDB AUTO_INCREMENT=0 DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # registration revenue table
    required["ANMELDER"] = """CREATE TABLE `ANMELDER` (
  `RechNr` tinytext NOT NULL,
  `ErloesKt` char(5) NOT NULL,
  `Erloes` float(5,2) NOT NULL,
  `ErloesKt2` char(5) NOT NULL,
  `Erloes2` float(5,2) NOT NULL,
  `ExtRechNr` tinytext NOT NULL,
  `AnmeldNr` mediumint(8) unsigned zerofill NOT NULL,
  `AgentNr` mediumint(8) unsigned zerofill NOT NULL,
  `ProvProz` float(2,1) NOT NULL,
  `Transfer` smallint(6) NOT NULL,
  `Umst` float(2,1) NOT NULL,
  `ProvPreis` float(5,2) NOT NULL,
  `Provision` float(5,2) NOT NULL,
  `BrtProv` float(5,2) NOT NULL,
  `AgentName` tinytext NOT NULL,
  `AgentDebitor` mediumint(8) unsigned zerofill NOT NULL,
  `GesamtPreis` float(5,2) NOT NULL,
  KEY `RechNr` (`RechNr`(50)),
  KEY `AnmeldNr` (`AnmeldNr`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # first contact table
    required["ANMELDEX"] = """CREATE TABLE `ANMELDEX` (
  `AnmeldNr` mediumint(8) unsigned zerofill NOT NULL,
  `Kennung` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Bezeichnung` tinytext NOT NULL,
  `Preis` float(5,2) NOT NULL,
  `NoPrv` smallint(6) DEFAULT NULL,
  `ListKenn` char(3) DEFAULT NULL,
  KEY `AnmeldNr` (`AnmeldNr`),
  KEY `Kennung` (`Kennung`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    # registration extra charge table
    required["ANMELDEX"] = """CREATE TABLE `ANMELDEX` (
  `AnmeldNr` mediumint(8) unsigned zerofill NOT NULL,
  `Kennung` mediumint(8) unsigned zerofill DEFAULT NULL,
  `Bezeichnung` tinytext NOT NULL,
  `Preis` float(5,2) NOT NULL,
  `NoPrv` smallint(6) DEFAULT NULL,
  `ListKenn` char(3) DEFAULT NULL,
  KEY `AnmeldNr` (`AnmeldNr`),
  KEY `Kennung` (`Kennung`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
    if flavour == "Tourist":
        # transfer route name table
        required["TNAME"] = """CREATE TABLE `TNAME` (
  `TourNr` smallint(6) NOT NULL,
  `Name` tinytext NOT NULL,
  `OhneBus` smallint(6) NOT NULL,
  KEY `TourNr` (`TourNr`),
  KEY `Name` (`Name`(50))
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
        # transfer route location table
        required["TORT"] = """CREATE TABLE `TORT` (
  `OrtsNr` smallint(6) NOT NULL,
  `Ort` tinytext NOT NULL,
  `Kennung` char(2) NOT NULL,
  PRIMARY KEY (`OrtsNr`),
  KEY `OrtsNr` (`OrtsNr`),
  KEY `Ort` (`Ort`(50))
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
        # transfer route, route data table
        required["TROUTE"] = """CREATE TABLE `TROUTE` (
  `KennNr` mediumint(8) unsigned zerofill NOT NULL,
  `Zeit` float(3,2) NOT NULL,
  `Preis` float(3,2) NOT NULL,
  `ZuAb` smallint(6) DEFAULT NULL,
  `ZuNach` smallint(6) DEFAULT NULL,
  KEY `KennNr` (`KennNr`),
  KEY `Zeit` (`Zeit`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german2_ci;"""
        # insert output possibillities for 'Tourist' flavour into 'AUSGABE' table
        required["AUSGABE"] = """INSERT INTO `AUSGABE` VALUES 
    (0,'Tourist','EigenReise','Anmeldung','Anbest','Anmeldebestätigung',''),
    (0,'Tourist','EigenReise','Storno','Stbest','Stornierungsbestätigung',''),
    (0,'Tourist','EigenReise','Anmeldung Verkauf','Anbere','Anmeldebestätigung Reisebüro',''),
    (0,'Tourist','EigenReise','Reservierung','Anresv','Reservieungsbestätigung',''),
    (0,'Tourist','EigenReise','Storno Verkauf','Stbere','Stornierungsbestätigung Reisebüro',''),
    (0,'Tourist','FremdReise','Anfrage','Fbanf','Anfrage Reiseveranstalter',''),
    (0,'Tourist','FremdReise','Anfrage','Fbanfb','Bestätigung Reiseteilnehmer',''),
    (0,'Tourist','FremdReise','Anmeldung','Fbbest','Anmeldebestätigung Femdbuchung',''),
    (0,'Tourist','FremdReise','Anmeldung','Fbbunt','Reiseunterlagen Femdbuchung',''),
    (0,'Tourist','FremdReise','Storno','Fbstrv','Stornierungbeim Reiseveranstalter',''),
    (0,'Tourist','FremdReise','Storno','Fbstbe','Stornierungsbestätigung für Kunden','');""".decode("UTF-8")
        # insert 'Agent' attribut template into 'ADRESATT' table
        required["ADRESATT"] = """INSERT INTO `ADRESATT` VALUES 
    (0,NULL,'Reisebüro',NULL,NULL,NULL,'Provision,Reisebürokontierung'),
    (0,NULL,'Reiseveranstalter',NULL,NULL,NULL,'Provision,Veranstalterkontierung');""".decode("UTF-8")
    else:
        # insert 'Event' output possibillities into 'AUSGABE' table
        required["AUSGABE"] = """INSERT INTO `AUSGABE` VALUES 
    (0,'Event','EigenEvent','Anmeldung','EvAnmeld','Anmeldebestätigung',''),
    (0,'Event','EigenEvent','Storno','EvStorno','Stornierungsbestätigung',''),
    (0,'Event','FremdEvent','Anmeldung','EvAnmeld','Anmeldebestätigung Fremdveranstaltung',''),
    (0,'Event','FremdEvent','Storno','EvStorno','Stornierungsbestätigung Fremdveranstaltung','');""".decode("UTF-8")
        # insert 'Agent' attribut template into 'ADRESATT' table
        required["ADRESATT"] = """INSERT INTO `ADRESATT` VALUES 
    (0,NULL,'Verkäufer',NULL,NULL,NULL,'Provision,Verkäuferkontierung'),
    (0,NULL,'Veranstalter',NULL,NULL,NULL,'Provision,Veranstalterkontierung'),
    (0,NULL,'Veranstaltungsort',NULL,NULL,NULL,NULL);""".decode("UTF-8")
    # return required tables
    return required