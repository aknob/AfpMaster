#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Afp Zusatzprogramm zum Import der MTV-Daten
#

import AfpBase
from AfpBase import *
from AfpBase.AfpUtilities import *
from AfpBase.AfpUtilities.AfpStringUtilities import Afp_toString, Afp_fromString, Afp_toIntString, Afp_toInternDateString,  Afp_ChDatum
from AfpBase.AfpAusgabe import AfpAusgabe
from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpBaseAdRoutines import AfpAdresse_getKNrFromSingleName, AfpAdresse_getKNrFromAlias
from AfpBase.AfpGlobal import *
from AfpBase.AfpBaseDialog import AfpReq_Question, AfpReq_MultiLine,  AfpReq_Selection
from AfpBase.AfpDatabase import AfpSQL

import AfpEvent
from AfpEvent import *
from AfpEvent.AfpEvRoutines import *
from  AfpEvent.AfpEvScreen_Verein import *

from AfpBase.AfpBaseFiRoutines import *
from AfpFinance.AfpFiRoutines import AfpFinanceTransactions, AfpFinance
 

def Afp_SetZahlArt(data):
    if data.get_listname() == "Verein":
        all_clients = data.get_clients(False, None)
        free = 0
        arge = 0
        sepa = 0
        rech = 0
        for client in all_clients:       
            print ("Verein_ZahlungsArt check client:", client.get_value())
            if "Storno" in client.get_value("Zustand"):
                client.set_value("Abmeldung", client.get_value("InfoDat"))
            extext = client.get_value("ExtText")
            if extext and ("ARGE" in extext or "Arge" in extext):
                client.set_value("ZahlArt", "ARGE")
                arge += 1
            elif client.get_value("Preis") < 0.01:
                #client.set_value("ZahlArt", "Familie")
                free += 1
            elif client.get_aktiv_sepa("Datum"):
                text =  "SEPA-Mandat " + Afp_toString(client.get_aktiv_sepa("Datum")[0]) 
                print ("Verein_ZahlungsArt check SEPA:", client.get_value(), text, len(text))
                client.set_value("ZahlArt", text)
                sepa += 1
            else:
                client.set_value("ZahlArt", "Rechnung")
                rech += 1
            client.store()
        print ("Verein_ZahlungsArt ARGE:", arge, "    SEPA:", sepa, "    Rechnung:", rech, "Beitragsfrei:", free)
        
# Main   
if __name__ == "__main__": 
    debug = False
    set = AfpSettings(debug)
    set.set("graphic-moduls", ["Adresse","Verein"])
    set.read_config("/home/akn/AfpWW.cfg")
    mysql = AfpSQL(set.get("database-host"), set.get("database-user"), "YnVzc2U=","AfpWW", set.is_debug())
    globals = AfpGlobal("test", mysql, set)
    verein = AfpEvVerein(globals,1)
    Afp_SetZahlArt(verein)
    print("AfpSetZahlArt main: THE END")
