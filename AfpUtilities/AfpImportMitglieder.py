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
 
## mapping for different Inputs
# @param typ: which mapping data should be returned
def Afp_getMapKt(typ):
    #0                                           1                              2                              3                                      4                     5                       6                                          7                                          8                                                           9                     10                            11        12                13                                14                15            16                    17                    18
    #Bezeichnung Auftragskonto	IBAN Auftragskonto	BIC Auftragskonto	Bankname Auftragskonto	Buchungstag	Valutadatum	Name Zahlungsbeteiligter	IBAN Zahlungsbeteiligter	BIC (SWIFT-Code) Zahlungsbeteiligter	Buchungstext	Verwendungszweck	Betrag	Waehrung	Saldo nach Buchung	Bemerkung	Kategorie	Steuerrelevant	Glaeubiger ID	Mandatsreferenz
    if typ == "vb":
        map = {"Datum":5, "Name": 6, "Typ":9, "Text":10, "Betrag":11, "Summe":13}
    return map
## mapping for different Inputs
def Afp_getTransactionMap():
    map = {"Member":{"Gegenkonto":"ErloesKt.EVENT","Bem":"RechNr Bez.EVENT" },"Rechnung":{"Gegenkonto":"Kontierung","Bem":"RechNr Zustand Bem" }, "Verbindlichkeit":{"Konto":"Kontierung","Bem":"ExternNr Bem" }}
    return map
## get accountnumber and for transaction, add result to newdata
# @param globals: global values holding mysql connection
# @param ktnr: accountnumber of bankaccount
# @param knr: addressidentifier of person
# @param typ: typ of transaction
# @param text: text of transaction
# @param out: flag if amount has been payed from account by this transaction
def Afp_qualifyTransaction(globals, ktnr, knr, typ, text, out):
    adresse = AfpAdresse(globals, knr)
    #print("AfpImportMitglieder.Afp_qualifyTransaction Oblig in:",knr, typ, text, out)
    if out:
        # outgoing Retoure
        if "Retoure SEPA" in text or "Beitrag" in text:
            sel = adresse.get_selection("ANMELD")
            for i in range(sel.get_data_length()):
                val = sel.get_values("AnmeldNr,RechNr,Zustand", i)[0]
                #print("AfpImportMitglieder.Afp_qualifyTransaction Anmeld Retoure SEPA val:",val, text)
                if val[2] == "Anmeldung" or val[2] == "PreStorno":
                    return AfpEvMember(globals, val[0])
        else:
            # outgoing: obligation
            sel = adresse.get_selection("VERBIND")
            for i in range(sel.get_data_length()):
                val = sel.get_values("ExternNr,Bem,Kontierung,Zustand,RechNr", i)[0]
                #print("AfpImportMitglieder.Afp_qualifyTransaction Oblig val:",val, not val[0] or val[0] in text, text)
                if val[3] == "Static" or val[3] == "Open":
                    if not val[0] or val[0] in text:
                        return AfpObligation(globals, val[4])
    else:
        # incoming: prices or invoice
        if "Beitrag" in text or "beitrag" in text or "Beotrag" in text or "BEITRAG" in text:
            sel = adresse.get_selection("AnmeldAgent")
            for i in range(sel.get_data_length()):
                val = sel.get_values("AnmeldNr,KundenNr,RechNr,Zustand", i)[0]
                #print("AfpImportMitglieder.Afp_qualifyTransaction Agent val:",val)
                if val[3] == "Anmeldung" or val[3] == "PreStorno":
                    adresse = AfpAdresse(globals, val[1])
                    found = False
                    if adresse.get_value("Vorname").strip() in text: 
                        found = True
                    else:
                        rows = adresse.get_attributs("Alias")
                        #print("AfpImportMitglieder.Afp_qualifyTransaction Agent attributs:",rows)
                        if rows:
                            for row in rows:
                                if row[4] in text:
                                    found = True
                                    break
                    if found:
                        return AfpEvMember(globals, val[0])
            sel = adresse.get_selection("ANMELD")
            for i in range(sel.get_data_length()):
                val = sel.get_values("AnmeldNr,RechNr,Zustand", i)[0]
                #print("AfpImportMitglieder.Afp_qualifyTransaction Anmeld val:",val)
                if val[2] == "Anmeldung" or val[2] == "PreStorno":
                    return AfpEvMember(globals, val[0])
        else:
            sel = adresse.get_selection("RECHNG")
            for i in range(sel.get_data_length()):
                val = sel.get_values("RechNr,Bem,Zustand", i)[0]
                #print("AfpImportMitglieder.Afp_qualifyTransaction Invoice RECHNG:",val, text)
                if val[2] == "Static" or val[2] == "Open":
                    fval = val[1].split("\n")
                    if not fval or not fval[0] or fval[0] in text:
                        if len(fval) > 1:
                            if "Beitrag:" in fval[1]: # look if member could be found by name
                                name = fval[1][8:].strip()
                                if name:
                                    KNr = AfpAdresse_getKNrFromSingleName(globals.get_mysql(), name)
                                    if KNr is None:
                                        KNr = AfpAdresse_getKNrFromAlias(globals.get_mysql(), name) 
                                    if KNr:
                                        sel = AfpAdresse(globals, KNr).get_selection("ANMELD")
                                        for i in range(sel.get_data_length()):
                                            val = sel.get_values("AnmeldNr,RechNr,Zustand", i)[0]
                                            if val[2] == "Anmeldung" or val[2] == "PreStorno":
                                                return AfpEvMember(globals, val[0])
                        #print("AfpImportMitglieder.Afp_qualifyTransaction Invoice RECHNG fval:",fval, not fval or fval in text, text)
                        return AfpCommonInvoice(globals, val[0])
    return None
## mapping for different Inputs
# @param typ: which mapping data should be returned
# @param table: for which table mapping data should be returned
def Afp_getMapMember(typ, table):
    # [0]=AnmeldNr, [2]=Vorname, [3]=Name, [4]=Email, [5]=Telefon, [6]=Geburtstag, [7]=Aktiv/Passiv, [9]=Mitgliedschaft-Beginn
    # [10]=M-Ende, [11]=Erstellungsdatum, [12]=Sparten, [13]=Junior/Senior, [14]=Spartenabteilung, [15]=Funktion, [16]=Beitragskategorien,
    # [17]=IBAN, [18]=BIC, [19]=Notiz
    #                      
    #             0       1      2                              3              4                  5                             6          7      8     9           10             11        12                13               14         15                       16                     17                18                19            20         21              22                            23                        24        25    26            27        28                    29        30
    #230418:Nr.	Typ	Name (vollständig)	Vorname	Nachname	Ansprechpartner	Straße	PLZ	Ort	E-Mail	Telefon	Mobil	Geburtstag	Geschlecht	Status	Benutzerstatus	Mitglied seit	Mitglied bis	Erstellt am	Sparten	Alter	Abteilung	Position im Verein	Mitgliedsbeitrag	IBAN	BIC	Anrede	Titel	2. Adresszeile	Land	Notiz
    #             0       1      2                                 3              4                  5                            6             7      8     9           10        11        12                13        14                15                16                    17         18                   19                    20                21                22            23         24           25                             26                        27              28        29    30        31        32                33        34        35        36                         37                        38                39                             40                  41 
    #230605:Nr.	Typ	Name (vollständig)	Vorname	Nachname	Ansprechpartner	Straße	PLZ	Ort	E-Mail	Telefon	Mobil	Geburtstag	Alter	Alter (wird)	Geschlecht	Familienstand	Status	Benutzerstatus	Mitglied seit	Mitglied bis	Erstellt am	Sparten	Alter	Abteilung	Position im Verein	Mitgliedsbeitrag	Zahlungsart	IBAN	BIC	Anrede	Titel	2. Adresszeile	Land	Notiz	Zahler	Mandatsreferenz	Art des Mandats	Erteilt am	Letzte Verwendung	G�ltig bis	Benutzer-Rollen

    map = None
    if typ == "wiso":
        if table == "Adresse":
            #map = {"Vorname":2, "Name":3, "Mail":4, "Telefon":5, "Geburtstag":6}
            #map = {"Vorname":3, "Name":4, "Strasse":6, "Plz":7, "Ort":8, "Mail":9, "Telefon":10, "Tel2":11, "Geburtstag":12, "Geschlecht":13} # 230418
            map = {"Vorname":3, "Name":4, "Strasse":6, "Plz":7, "Ort":8, "Mail":9, "Telefon":10, "Tel2":11, "Geburtstag":12, "Geschlecht":15} # 230605
        elif table == "Anmeld":
            #map = {"Anmeldung":16, "Bem":19} # 230418
            map = {"Anmeldung":19, "Bem":24,  "InfoDat":20,  "ExtText":34} # 230605
        elif table == "Preise":
            #map = {"Aktiv":14, "Sparten": 19, "Alter":20, "Beitrag": 23} # 230418
            map = {"Aktiv":17, "Sparten": 22, "Alter":23, "Beitrag": 26, "Zahler":35} # 230605
        elif table == "Bank":
            #map = {"IBAN":24, "BIC":25} # 230418
            map = {"IBAN":28, "BIC":29, "Date": 38} # 230605
    return map
## calculated needed prices from input data
# @param Preise: TableSelection holding all possible prices
# @param aktivpassiv: Aktiv/Passiv flag
# @param age: age for seniority
# @param sparten_string: line holding names of Sparten
# @param beitrag_string: line holding categories of prices
# @param zahler: if given: name of person which pays
def Afp_getPreise(Preise, aktivpassiv, age, sparten_string, beitrag_string, zahler=None): 
    #print ("AfpImportMitglieder.Afp_getPreise input:", aktivpassiv, age, sparten_string, beitrag_string, Preise.data) 
    # has to be filled with life
    #return [[1, "Standardpreis", 200.00,0]]
    wiso = {"Abteilungsbeitrag Tischtennis Jugend":63.00, "Alleinerziehend mit 2 Kinder Turnen":63.00, "Betreuung GS Lichtenberg":18.00, "Ehrenmitglied":0.00, \
                "Familienbeitrag":63.00, "Familienbeitrag + 1 Kind":68.00, "Familienbeitrag + 2 Kinder":72.00, "Familienbeitrag +Tennis+Gymnastik":138.00, "Familienbeitrag 2 Erwachsene + 1 Kind Turnen & Gymnastik":85.50, "Familienbeitrag Tennis Blonski":156.00, "Familienbeitrag+ Tennis Sen. + Tennis Jun.+ Zumba Sen.":115.50, "Familienbetrag +2 Kinder Fussball /Tennis /Ski":148.50, \
                "Fussball Abteilungsbeitrag Herren":16.50, "Fussball Erwachsener":52.50, "Fussball Rentner":46.50, "Fussball Schueler":28.50, "Grundbeitrag Leichtathletik Junioren":18.00, "Jahresbeitrag":144.00,  \
                "Mout / Ski / Bo / Lei":36.00, "Mout / Ski / Bo / Leicht / Rentner":30.00, "Passiv":18.00, "Ski Abteilungsbeitrag":0.00, "T & G /TT/ Rentner": 39.00, "TTennis Abteilungsbeitrag Jugend":4.50, \
                "Tennis / T&G Senioren /Netsch":67.50, "Tennis Erwachsener":58.50, "Tennis Familien +1 Kind":63.00, "Tennis Familienbeitrag":45.00, "Tennis Familienbeitrag +1 Kind":117.00, "Tennis Familienbeitrag Komplett":108.00, "Tennis Jugend":39.00, "Tennis Rentner":52.50, \
                "Tu / TT/  Schueler":22.50, "Tu/TT Erwachsen":45.00, "Tu/TT/ TE /Schueler Rentner":39.00, "Turnen Abteilungsbeitrag":9.00}
    
    data = Preise.data
    ehre = "Ehrenmitglied" in beitrag_string
    if ehre:  
        passiv = False
        rentner = False
    else: 
        passiv = aktivpassiv == "Passiv"
        if not passiv and "Passiv" in beitrag_string: passiv = True
        if passiv:
            rentner = False
        else: 
            rentner = age > 66
            #rentner = not jugend and "Rentner" in beitrag_string
    if beitrag_string and "Schueler" in Afp_replaceUml(beitrag_string):
        jugend = True
    else:
        jugend = age < 23
    #mitglied = beitrag_string == ""
    if zahler is None: 
       mitglied = beitrag_string == ""
    else:
       mitglied = True
    allein = "Alleinerziehend" in beitrag_string
    familie= not allein and "Familie" in beitrag_string and not "Familienm" in beitrag_string
    beitrag = [None]
    sparten = sparten_string.split(",")
    for i in range(len(sparten)):
        sparte = sparten[i].strip()
        if sparte == "Turnen u. Gymnastik": sparte = "Turnen und Gymnastik"
        if sparte == "Grundschule Lichteberg": sparte = "Grundschule Lichtenberg"
        if sparte == "Ski -Abteilung": sparte = "Ski" 
        sparten[i] = sparte
    #print ("AfpImportMitglieder.Afp_getPreise Ehrenmitglied:", ehre, "Passiv:", passiv, "Jugend:", jugend, "Familienmitglied:", mitglied,  "Rentner:",rentner, "Allein:", allein, "Familie:", familie, "Sparten:", sparten, (jugend and not mitglied)) 
    found = []
    for row in data: 
        #print ("AfpImportMitglieder.Afp_getPreise row:", row, beitrag)
        if row[0] == 1:
            if not beitrag[0] is None: continue
            if ehre and "Ehrenmitglied" in row[2] or \
               passiv and "Passiv" in row[2] or \
               (jugend and not mitglied) and "Jugend" in row[2] or \
               rentner and "Rentner" in row[2] or \
               allein and "Allein" in row[2] or \
               familie and ("Familie" in row[2]  and not "Familienm" in row[2]) or \
               mitglied and "Familienmitglied" in row[2] or \
               (not (ehre or passiv or jugend or rentner or allein or familie or mitglied) and row[2] == "Beitrag"):            
                beitrag[0] = [row[1],row[2],row[5],row[8]]
        else:
            for sparte in sparten:
                if sparte in row[2]:
                    if sparte in found: continue
                    if sparte == "Tennis" or sparte == "Fussball" or sparte == "Tischtennis" or sparte == "Turnen und Gymnastik" or sparte == "Volleyball":
                        if sparte == "Tennis":
                            if (passiv or ehre) and "Passiv" in row[2] or \
                               (jugend and not mitglied) and "Jugend" in row[2] or \
                               familie and  ("Familie" in row[2]  and not "Familienm" in row[2]) or \
                               mitglied and "Familienmitglied" in row[2] or \
                               (not (ehre or passiv or familie or jugend or mitglied) and row[2] == "Sparte Tennis"):
                                beitrag.append([row[1],row[2],row[5],row[8]])
                                found.append(sparte)
                                #print ("AfpImportMitglieder.Afp_getPreise append Tennis:", sparte, (passiv and "Passiv" in row[2] or jugend and "Jugend" in row[2]), row[2])
                        else:
                            if (passiv or ehre) and "Passiv" in row[2] or \
                               jugend and "Jugend" in row[2]:
                                beitrag.append([row[1],row[2],row[5],row[8]])
                                found.append(sparte)
                                #print ("AfpImportMitglieder.Afp_getPreise append Jugend/passiv:", sparte, (passiv and "Passiv" in row[2] or jugend and "Jugend" in row[2]), row[2])
                            elif not (ehre or passiv or  jugend):
                                beitrag.append([row[1],row[2],row[5],row[8]])
                                found.append(sparte)
                                #print ("AfpImportMitglieder.Afp_getPreise append Jugend/passiv:", sparte, not(passiv or jugend), row[2])
                    else:
                        beitrag.append([row[1],row[2],row[5],row[8]])
                        found.append(sparte)
                        #print ("AfpImportMitglieder.Afp_getPreise append Else:", sparte, not(passiv or jugend), row[2])
    altbeitrag = 0.0
    alte = beitrag_string
    if beitrag_string:
        alte = beitrag_string.split(",") 
        #print ("AfpImportMitglieder.Afp_getPreise wiso:", alte)
        for alt in alte:
            neu = Afp_replaceUml(alt).strip()
            if neu in wiso:
                altbeitrag += wiso[neu]
            else:
                print ("WARNING:", neu, "not found in Wiso!")
    altbeitrag *= 4
    return beitrag, altbeitrag, alte
    
## add transaction value to balance. compare sums
# @param bal: balance where value has to be added
# @param KtNr: number of balance-account
# @param newdata: data to be added to account transactions
# @param debug: id given, debug flag
def Afp_addTransVal(bal, KtNr, newdata, debug=None):
    if newdata["Konto"] == KtNr:
        bal += newdata["Betrag"]
    elif newdata["Gegenkonto"] == KtNr:
        bal -= newdata["Betrag"]
    if debug: 
        print ("AfpImportMitglieder.Afp_addTransVal balance:", bal, newdata["Summe"], bal - newdata["Summe"], KtNr)
    if Afp_isEps(bal - newdata["Summe"]):
        print ("ERROR! Balance not in line:", bal,  bal - newdata["Summe"], KtNr, newdata)
        test = test # error, end program
    return bal
    
## connect family members by using same RechNr, move prices to main member
# @param globals - global variables
# @param debug - debug flag
def Afp_Familie(globals, debug):
    mysql = globals.get_mysql()
    mains = mysql.select("AnmeldNr,KundenNr,RechNr", "PreisNr = 4 OR PreisNr = 5","ANMELD")
    clients = mysql.select("AnmeldNr,KundenNr,AgentNr", "PreisNr = 7","ANMELD") 
    print ("AfpImportMitglieder.Afp_Familie mains:", mains)
    namen = []
    nrs = []
    for client in clients:
        namen.append(AfpAdresse(globals, client[1]).get_value("Name"))
    print ("AfpImportMitglieder.Afp_Familie clients:", clients)
    print ("AfpImportMitglieder.Afp_Familie namen:", namen)
    for main in mains:
        main_anmeld= AfpEvMember(globals, main[0])
        main_name= main_anmeld.get_value("Name.ADRESSE")
        main_anmeldex = main_anmeld.get_selection("ANMELDEX")
        print ("\nAfpImportMitglieder.Afp_Familie check main:", main_name, main_anmeld.get_name())
        personen = 0
        tennis = 0
        for i in range(len(namen)): 
            if clients[i][2] == main[1]: agent = True
            else: agent = False
            #if namen[i] == main_name and not main[0] == clients[i][0]:
            if not main[0] == clients[i][0] and (namen[i] == main_name or agent) :
                anmeld = AfpEvMember(globals, clients[i][0])
                anmeld.set_value("RechNr", main[2])
                personen += 1
                if anmeld.pricename_holds("Tennis"):
                    tennis += 1
                if agent: anmeld.set_value("AgentNr", None)
                print ("AfpImportMitglieder.Afp_Familie same name:", main[2], main_name, anmeld.get_name(), agent)
                preis = 0.0
                if anmeld.get_value("Preis"): # move price to main member
                    preis = anmeld.get_value("Preis")
                    anex = anmeld.get_selection("ANMELDEX")
                    for i in range(len(anex.data)):
                        if anex.data[i][3]:
                            row = anex.data[i]
                            mrow = [main[0], None, anex.data[i][2] +" " +  anmeld.get_name() + " " + Afp_toString(anex.data[i][1]), anex.data[i][3], 0, None]
                            main_anmeldex.add_row(mrow)
                            #anex.data[i][3] = 0.0
                            anex.set_value("Preis", 0.0, i) 
                            print ("AfpImportMitglieder.Afp_Familie anex:", anex.data[i])
                    anmeld.set_value("Preis", 0.0)
                    anmeld.set_value("Extra", 0.0)
                    anmeld.set_value("ProvPreis", 0.0)
                    main_anmeld.set_value("Preis", main_anmeld.get_value("Preis") + preis)
                    main_anmeld.set_value("Extra", main_anmeld.get_value("Extra") + preis)
                    main_anmeld.set_value("ProvPreis", main_anmeld.get_value("ProvPreis") + preis)
                    print ("AfpImportMitglieder.Afp_Familie price:", main_name, preis, anmeld.get_value("Vorname.ADRESSE"), "to", main_anmeld.get_value("Vorname.ADRESSE"))
                anmeld.store()
                print ("AfpImportMitglieder.Afp_Familie ANMELDEX:", anmeld.get_selection("ANMELDEX").data)
                if debug: print ("AfpImportMitglieder.Afp_Familie Found:", clients[i][0], main[2], main_name)
                print ("AfpImportMitglieder.Afp_Familie Found:", clients[i][0], main[2], anmeld.get_name(), preis)
        # add additional persons bookings
        if personen < 0:
        #if personen > 2:
            plus = 0.0
            for i in range(3, personen+1):
                mrow = [main[0], 8, "je Kind (Kind " + Afp_toString(i-1) + ")", 60.0, 0, None]
                main_anmeldex.add_row(mrow)
                plus += 60.0
            if tennis > 2:
                for i in range(3, tennis+1):
                    mrow = [main[0], 15, "Sparte Tennis je Kind (Kind " + Afp_toString(i-1) + ")", 18.0, 0, None]
                    main_anmeldex.add_row(mrow)
                    plus += 18.0
            if Afp_isEps(plus):
                main_anmeld.set_value("Preis", main_anmeld.get_value("Preis") + plus)
                main_anmeld.set_value("Extra", main_anmeld.get_value("Extra") + plus)
                main_anmeld.set_value("ProvPreis", main_anmeld.get_value("ProvPreis") + plus)
                print ("AfpImportMitglieder.Afp_Familie Kinder:",  personen, tennis, plus, main_anmeld.get_value("Preis"))
        #if main_anmeld.has_changed():
            #print ("AfpImportMitglieder.Afp_Familie main:")
            #main_anmeld.view()
        main_anmeld.store()
## import data from csv-file in Wiso-Format
# @param input - AfpEvVerein SelectionList
# @param debug - debug flag
def Afp_CheckWiso(globals, wiso, debug):
    alle = False
    csv_o = True
    count = 0
    ecount = 0
    sum = 0.0
    wsum = 0.0
    einzug = 0.0
    weinzug = 0.0
    if wiso:
        for nr in wiso:
            row = wiso[nr]
            anmeld= AfpEvMember(globals, nr)
            preis = anmeld.get_value("Preis")
            sum += preis
            wsum += row[0]
            diff = preis - row[0]
            if Afp_isEps(diff) and preis:
                if diff - row[1]:
                    if csv_o:
                        print (anmeld.get_name(True), ";Beitrag:;", preis, ";Wiso Beitrag:;", row[0], ";Differenz:;", diff,  ";   Sparten:;", row[2], ";Wiso Eintrag:;", row[3], ";alte Differenz:;", row[1] )
                    else:
                        print ( "Beitrag:", preis, "Wiso Beitrag:", row[0], "Differenz:", diff, anmeld.get_name(True),  "   Sparten:", row[2], "Wiso Eintrag:", row[3], "alte Differenz:", row[1] )
                else:
                    if csv_o:
                        print (anmeld.get_name(True),  ";Beitrag:;", preis, ";Wiso Beitrag:;", row[0], ";Differenz:;", diff, ";   Sparten:;", row[2], ";Wiso Eintrag:;", row[3] )
                    else:
                        print ( "Beitrag:", preis, "Wiso Beitrag:", row[0], "Differenz:", diff, anmeld.get_name(True),  "   Sparten:", row[2], "Wiso Eintrag:", row[3])
            elif  alle and preis:
                print ( "Beitrag:", preis, "Wiso Beitrag:", row[0], "Differenz:", diff, anmeld.get_name(True), "   OK!")
            elif alle:
                print ( "Beitrag:", preis, "Wiso Beitrag:", row[0], "Differenz:", diff, anmeld.get_name(True), "   Familienmitglied!")
            count += 1
            if anmeld.get_value("Datum.SEPA"):
                ecount += 1
                einzug += preis
                weinzug += row[0]
    print ("AfpImportMitglieder.Afp_CheckWiso Summen:", count, "Mitglieder, Beitragssumme:", sum, "Beiträge Wiso:", wsum, "Differenz: ", sum - wsum)
    print ("AfpImportMitglieder.Afp_CheckWiso Einzug:", ecount, "Mitglieder, Beitragssumme:", einzug, "Beiträge Wiso:", weinzug, "Differenz: ", einzug - weinzug)

## import data from csv-file in Wiso-Format
# @param globals - global data including mysql connection
# @param input - AfpEvVerein SelectionList
# @param imp - format of import files
# @param debug - debug flag
def AfpImport_Member(globals, input, imp,  debug):
    #store = False
    store = True
    alle = False
    #alle = True
    dir = globals.get_value("docdir")
    filename, Ok = AfpReq_FileName(dir,"Importdatei selektieren", "*.csv", True)
    print ("AfpImportMitglieder.AfpImport_Member File:", Afp_getNow(), Ok, filename) 
    sum = 0.0
    altsum = 0.0
    count = 0
    Adress_map = Afp_getMapMember(imp, "Adresse")
    Anmeld_map = Afp_getMapMember(imp, "Anmeld") 
    Pmap = Afp_getMapMember(imp, "Preise")
    Bank_map = Afp_getMapMember(imp, "Bank")
    print ("AfpImportMitglieder.AfpImport_Member maps:", Adress_map, Anmeld_map, Pmap, Bank_map) 
    wiso = None
    if Ok and filename:
        #Verein = AfpEvVerein(globals, 1)
        Verein = input
        all_prices = Verein.get_selection("Sparten")
        lines = Afp_readLinesFromFile(filename)
        maxnr = 0
        wiso = {}
        for line in lines:
            data = line.split(";")
            #print ("AfpImportMitglieder.AfpImport_Member data:", len(data), data) 
            nr = Afp_fromString(data[0])
            if Afp_isString(nr): continue
            if nr:
                if nr > maxnr: maxnr = nr
                # import Adressdata
                newdata = {}
                newdata["Anrede"] = "Du"
                newdata["Kennung"] = 1
                for entry in Adress_map:
                    value = data[Adress_map[entry]].strip()
                    if value == "-": value = ""
                    if value: newdata[entry] = value 
                    #print ("AfpImportMitglieder.AfpImport_Member adress:", entry, "=", value) 
                if "Geschlecht" in newdata: 
                    newdata["Geschlecht"] = newdata["Geschlecht"].strip()[0] 
                else:
                    newdata["Geschlecht"] = "n"
                #print ("AfpImportMitglieder.AfpImport_Member newdata:", newdata) 
                # age needed for Anmeldung has to be calculated here, as Geburtstag data is available now!
                age = 25
                if data[Pmap["Alter"]] == "Junioren": age = 6
                if "Geburtstag" in newdata and newdata ["Geburtstag"]: 
                    geb = Afp_fromString(newdata["Geburtstag"])
                    newdata ["Geburtstag"] =  Afp_toInternDateString(geb)
                    age = Afp_getToday().year - geb.year
                # check if address already exists
                if "Vorname" in newdata:
                    name = newdata["Vorname"] + " " + newdata["Name"]
                else:
                    name = newdata["Name"]
                KNr = AfpAdresse_getKNrFromSingleName(globals.get_mysql(), name)
                if KNr is None:
                    KNr = AfpAdresse_getKNrFromAlias(globals.get_mysql(), name)
                if KNr:
                    Adresse = AfpAdresse(globals, KNr)
                else:
                    Adresse = AfpAdresse(globals)
                Adresse.set_data_values(newdata)
                if store: Adresse.store()                
                KNr = Adresse.get_value("KundenNr")
                # Mitgliedschaft
                Anmeldung = AfpEvMember(globals)
                newdata = {}
                #newdata ["AnmeldNr"] = nr
                newdata ["KundenNr"] = KNr
                newdata ["EventNr"] = 1
                newdata ["IdNr"] = nr
                newdata ["RechNr"] = "mtv-" + Afp_toIntString(nr,4)
                for entry in Anmeld_map:
                    value = data[Anmeld_map[entry]].strip()
                    if value == "-": value = ""
                    if value: newdata[entry] = value
                newdata["Zustand"] = "Anmeldung"
                sepa_typ = "Aktiv"
                if newdata ["Anmeldung"]:  newdata ["Anmeldung"] =  Afp_toInternDateString(Afp_fromString(newdata["Anmeldung"]))
                if "InfoDat" in newdata and newdata ["InfoDat"]:  
                    newdata["Info"] = newdata["InfoDat"] + " Abmeldung"
                    newdata ["InfoDat"] =  Afp_toInternDateString(Afp_fromString(newdata["InfoDat"]))
                    newdata["Zustand"] = "Storno"
                    sepa_typ = "Inaktiv"
                AgentNr = None
                agent = None
                if "Zahler" in Pmap:
                    zahler = data[Pmap["Zahler"]].strip()
                    if zahler and not zahler == "-": agent = zahler
                    if agent:
                        AgentNr = AfpAdresse_getKNrFromSingleName(globals.get_mysql(), agent)
                        if AgentNr:
                            rows = globals.get_mysql().select("AnmeldNr", "KundenNr = " + Afp_toString(AgentNr),"ANMELD")
                            if not AfpEvMember(globals, rows[0][0]).pricename_holds("Familie"): agent = None
                if agent:
                    Preise, Altpreis, Altbez = Afp_getPreise(all_prices, data[Pmap["Aktiv"]], age, data[Pmap["Sparten"]], data[Pmap["Beitrag"]], agent) 
                else:
                    Preise, Altpreis, Altbez = Afp_getPreise(all_prices, data[Pmap["Aktiv"]], age, data[Pmap["Sparten"]], data[Pmap["Beitrag"]]) 
                #print ("AfpImportMitglieder.AfpImport_Member Preise:", age, Preise, Altpreis, Altbez) 
                if AgentNr:  newdata ["AgentNr"] = AgentNr
                newdata ["PreisNr"] = Preise[0][0]
                newdata ["Preis"] = Preise[0][2]
                newdata ["Zahlung"] = 0.0
                Anmeldung.set_data_values(newdata)
                if store: Anmeldung.store()
                newdata = {}
                ANr = Anmeldung.get_value()
                # bankdata in ADRESATT and SEPA (AnmeldNr is needed)
                Iban = data[Bank_map["IBAN"]].strip()
                Bic = data[Bank_map["BIC"]].strip() 
                dat = data[Bank_map["Date"]] 
                if Iban == "-": Iban = "" 
                if Bic == "-": Bic = "" 
                if dat: dat = Afp_toInternDateString(Afp_fromString(dat))
                if Iban:
                    newdata = {"KundenNr":KNr, "Name":Adresse.get_value("Name"), "Attribut":"Bankverbindung", "Tag": Iban + ","  + Bic, "Aktion":"IBAN,BIC"}
                    Adresse.set_data_values(newdata, "ADRESATT", -1)
                    if dat:
                        newdata = {"KundenNr":KNr, "Art":"SEPA-DD", "Typ":sepa_typ, "Gruppe":Bic, "Bem":Iban, "Extern":"No-Scan.txt", "Datum":dat, "Tab":"ANMELD", "TabNr":ANr }
                        Adresse.set_data_values(newdata, "SEPA", -1)
                if store: Adresse.store()
                newdata = {}
                gesamt = None
                if len(Preise) > 1:
                    AnmeldEx = Anmeldung.get_selection("AnmeldEx")
                    #print ("AfpImportMitglieder.AfpImport_Member AnmeldEx empty:", AnmeldEx.data)
                    #row = [ANr, 0, "",  0.0, 0, None]
                    first = True
                    for preis in Preise:
                        if gesamt is None:
                            gesamt = preis[2]
                        else:
                            if first:
                                AnmeldEx.set_value("AnmeldNr", ANr)
                                AnmeldEx.set_value("Kennung", preis[0])
                                AnmeldEx.set_value("Bezeichnung", preis[1])
                                AnmeldEx.set_value("Preis", preis[2])
                                AnmeldEx.set_value("NoPrv", preis[3])
                                first = False
                            else:
                                row = [ANr] + preis + [None]
                                AnmeldEx.add_row(row)
                            gesamt += preis[2]
                    #print ("AfpImportMitglieder.AfpImport_Member AnmeldEx filled:", AnmeldEx.data)
                else:
                    gesamt = Preise[0][2]
                newdata ["Preis"] = gesamt
                newdata ["ProvPreis"] = gesamt
                newdata ["Extra"] = gesamt - Preise[0][2]
                Anmeldung.set_data_values(newdata)
                if store: Anmeldung.store()
                diff = gesamt - Altpreis
                if alle or Afp_isEps(diff):
                    #print ("AfpImportMitglieder.AfpImport_Member Preis:",gesamt, Altpreis, diff, Adresse.get_name(), Preise, Altbez)
                    print ( "Beitrag:", gesamt, "Wiso Beitrag:", Altpreis, "Differenz:", diff, Adresse.get_name(True),  age, "   Sparten:", Preise, "Wiso Eintrag:", Altbez)
                else:
                    #print ("AfpImportMitglieder.AfpImport_Member Preis:",gesamt, Altpreis, diff, Adresse.get_name())
                    print ( "Beitrag:", gesamt, "Wiso Beitrag:", Altpreis, "Differenz:", diff, Adresse.get_name(True), "   OK!")
                wiso[ANr] = [Altpreis, diff, Preise, Altbez]
                sum += gesamt
                altsum += Altpreis
                count += 1
        Verein.set_value("RechNr", maxnr)
        Verein.set_value("Anmeldungen", count)
        Verein.store()
    print ("AfpImportMitglieder.AfpImport_Member Summen:", count, "Mitglieder, Beitragssumme:", sum, "Beiträge Wiso:", altsum, "Differenz: ", sum - altsum)
    return wiso
## import accountdata from csv-file and return AfpFinance and a list of selectionlists
# @param globals - global data including mysql connection
# @param typ - import data typ
# @param debug - debug flag
def AfpImport_Konto(globals, typ, debug):
    dir = globals.get_value("docdir")
    filename, Ok = AfpReq_FileName(dir,"Importdatei der Kontodaten selektieren", "*.csv", True)
    print ("AfpImportMitglieder.AfpImport_Konto File:", Afp_getNow(), Ok, filename) 
    if not Ok: return None, None
    skip_intern = False
    Konto = "1610"
    Auszug = "VB"
    today = Afp_getToday()
    period = Afp_toString(today.year)
    #Konto, res = AfpReq_Text("Kontodaten werden aus der Datei: " + filename + " importiert,","bitte Kontonummer angeben, der diese Daten zugeordnet werden sollen.",Konto)
    kosten = 4200
    ertrag = 8900
    Types = ["Text", "Check", "Text", "Text", "Text"]
    Liste = [["Auzug:", Auszug], ["interne Buchungen ignorieren:", False], ["Default-Kosten:",Afp_toString(kosten)], ["Default-Ertrag:",Afp_toString(ertrag)], ["Periode:",period]]
    res = AfpReq_MultiLine("Kontodaten werden aus der Datei: " + filename.split(globals.get_value("path-delimiter"))[-1] + " importiert,","bitte Werte angeben, die diesen Daten zugeordnet werden sollen.",Types, Liste, "Finanzwerte")
    if not res: return None, None
    Auszug = res[0]
    Konto = Afp_getSpecialAccount(globals.get_mysql(), Afp_getStartLetters(Auszug))
    skip_intern = res[1]
    kosten = Afp_fromString(res[2])
    ertrag = Afp_fromString(res[3])
    period = res[4]
    balance= None
    count = 0
    KtNr = Afp_fromString(Konto)
    Transfer = 1690
    Kasse = 1600
    BelegNr = 1
    select = "SELECT MAX(CONVERT(Beleg,UNSIGNED)) FROM BUCHUNG WHERE Period = \"" + period + "\""
    res = globals.get_mysql().execute(select)
    print ("AfpImportMitglieder.AfpImport_Konto BelegNr:", res, res[0][0])
    if res and res[0][0]:
        BelegNr = Afp_fromString(res[0][0]) + 1
    selection_lists = []
    finanz = None
    ktmap = Afp_getMapKt(typ)
    newdata_map = Afp_getTransactionMap()
    print ("AfpImportMitglieder.AfpImport_Konto maps:", ktmap, newdata_map) 
    if Ok and filename:
        lines = Afp_readLinesFromFile(filename) 
        lines.reverse()
        #print ("AfpImportMitglieder.AfpImport_Konto lines:", type(lines), lines) 
        maxnr = 0
        #finanz = AfpFinanceTransactions(globals, None, "BuchungsNr", period)
        data =  lines[0].split(";")
        #print ("AfpImportMitglieder.AfpImport_Konto data:", data, ktmap["Summe"], ktmap["Betrag"]) 
        balance = Afp_fromString(data[ktmap["Summe"]]) - Afp_fromString(data[ktmap["Betrag"]]) 
        parlist = {}
        #parlist["Auszug"] = Afp_extractBase(filename)[:11]
        parlist["Auszug"] = Auszug
        data =  lines[-2].split(";")
        value = data[ktmap["Datum"]]
        if value[:5] == "30.02": value = "28.02" + value[5:]
        parlist["Datum"] = Afp_fromString(value)
        #parlist["Saldo"] = Afp_fromString(data[ktmap["Summe"]]) - Afp_fromString(data[ktmap["Betrag"]])  
        parlist["Saldo"] = balance
        print ("AfpImportMitglieder.AfpImport_Konto parlist:", parlist)
        finanz = AfpFinance(globals, period, parlist)
        buchung = finanz.get_selection()
        for line in lines:
            newdata = {}
            data = line.split(";")
            if "Bezeichnung" in data[0] : continue
            for entry in ktmap:
                value = data[ktmap[entry]].strip()
                if value[:5] == "30.02": value = "28.02" + value[5:]
                if value: newdata[entry] = Afp_fromString(value)
            if newdata["Betrag"] < 0.0: ausgabe = True
            else: ausgabe = False
            typ = newdata.pop("Typ")
            if "Text" in newdata:
                text = newdata.pop("Text")
            else:
                text = ""
            if "€" in text:
                split = text.split("€")
                text = ""
                for sp in split:
                    text += sp + "EURO"
                text = text[:-4]
            name = ""
            if "Name" in newdata: name = newdata.pop("Name")
            print ("AfpImportMitglieder.AfpImport_Konto Name:", name)
            KNr = None
            if typ == "Auszahlung girocard":
                newdata["Konto"] = Kasse
                newdata["Gegenkonto"] = KtNr
            elif typ == "Bareinzahlung":
                newdata["Konto"] = KtNr
                newdata["Gegenkonto"] = Kasse
                print ("AfpImportMitglieder.AfpImport_Konto Bareinzahlung:", typ, name)
            if name:
                KNr = AfpAdresse_getKNrFromSingleName(globals.get_mysql(), name)
                if KNr is None:
                    KNr = AfpAdresse_getKNrFromAlias(globals.get_mysql(), name)
                if KNr: 
                    if KNr == 1 and skip_intern: continue
                    newdata["KundenNr"] = KNr
                    sel = None
                    payback = ("Retoure" in text or "Rueckweisung" in text or ("rstattung" in text and "Beitrag" in text)) and newdata["Betrag"] < 0.0
                    if not "Konto" in newdata and not "Gegenkonto" in newdata:
                        sel = Afp_qualifyTransaction(globals, KtNr, KNr, typ, text, newdata["Betrag"] < 0.0)
                        if not sel and KNr == 3 and newdata["Betrag"] > 0.0 : # try other direction for paybacks of WEVG
                            sel = Afp_qualifyTransaction(globals, KtNr, KNr, typ, text, True)
                            payback = True
                    if sel:
                        selection_lists.append(sel)
                        map = newdata_map[sel.get_listname()]
                        for entry in map:
                            words = map[entry].split(" ")
                            value = ""
                            for word in words:
                                value += sel.get_string_value(word) + " "
                            value = value.strip()
                            # spezial handling as account is handled via short name
                            if map[entry] == "ErloesKt.EVENT":
                                value = Afp_getSpecialAccount(globals.get_mysql(), value)
                            newdata[entry] = value
                        if  payback:
                            if "Gegenkonto" in newdata: 
                                newdata["Konto"] = newdata["Gegenkonto"]
                                newdata.pop("Gegenkonto")
                            else:
                                newdata["Gegenkonto"] = newdata["Konto"]
                                newdata.pop("Konto")
                        if "Konto" in newdata: 
                            newdata["Gegenkonto"] = KtNr
                        else: 
                            newdata["Konto"]  = KtNr
                        newdata["Period"] = period
                        newdata["Eintrag"] = Afp_toInternDateString(today)
                        if not "Art" in newdata: newdata["Art"] = "Zahlung"
                        newdata["Tab"] = sel.get_mainselection()
                        newdata["TabNr"] = sel.get_value()
                        betrag = newdata["Betrag"]
                        if newdata["Betrag"] < 0.0: newdata["Betrag"] = - newdata["Betrag"] 
                        splitting = sel.get_splitting_values(newdata["Betrag"])
                        newdata["Beleg"] = BelegNr
                        BelegNr += 1 
                        bem = newdata["Bem"]
                        newdata["Bem"] = bem + " - " + text[:250]
                        newdata["Art"] = newdata["Art"][:20]
                        if splitting: 
                            #print ("AfpImportMitglieder.AfpImport_Konto splitting:", splitting)
                            if newdata["Konto"]  == KtNr:
                                newdata["Gegenkonto"]  = Transfer
                            else:
                                newdata["Konto"]  = Transfer
                            #print ("AfpImportMitglieder.AfpImport_Konto split init:", newdata)   
                            balance = Afp_addTransVal(balance, KtNr, newdata, debug)
                            finanz.add_direct_transaction(newdata)
                            if newdata["Konto"]  == KtNr:
                                newdata["Konto"]  = Transfer
                                if "GktName" in newdata: newdata["KtName"]  = newdata["GktName"]
                                konto = "Gegenkonto"
                                ktname = "GktName"
                            else:
                                newdata["Gegenkonto"]  = Transfer
                                if "KtName" in newdata: newdata["GktName"]  = newdata["KtName"]
                                konto = "Konto"
                                ktname = "KtName"
                            for split in splitting:
                                newdata[konto] = split[0]
                                newdata[ktname] = ""
                                newdata["Betrag"] = split[1]
                                if split[2]: newdata["Bem"] = Afp_toString(split[2]) + " " + bem[:250]
                                else: newdata["Bem"] = bem
                                if newdata["Art"] == "Zahlung": newdata["Art"] = "Zahlung intern"
                                #print ("AfpImportMitglieder.AfpImport_Konto split:", newdata)
                                finanz.add_direct_transaction(newdata)
                        else:
                            if not skip_intern:
                                balance = Afp_addTransVal(balance, KtNr, newdata, debug)
                            finanz.add_direct_transaction(newdata)
                        dum1, zahl, dum2 = sel.get_payment_values()
                        betrag += zahl 
                        dat = today
                        if "Datum" in newdata:
                            dat = newdata["Datum"]
                        sel.set_payment_values(betrag, dat) 
                        newdata = {}
                else:
                    print ("WARNING! Adressidentifier for", "\""+ name + "\"", "not found! If the address exists, create the appropriate 'Alias' address attribut.")
                if newdata and not "Konto" in newdata and not "Gegenkonto" in newdata:
                    if  newdata["Betrag"] < 0.0: 
                        if "SEPA" in text or "Retoure" in text or "Rueckweisung" in text or ("rstattung" in text and "Beitrag" in text) :
                            newdata["Konto"] = 8100
                            newdata["Gegenkonto"] = KtNr
                    elif "Beitrag" in text or "Mitgliedsnummer" in text or "Quartal" in text:
                        newdata["Konto"] = KtNr
                        newdata["Gegenkonto"] = 8210
            else:
                if text[:4] == "SEPA":
                    KNr = 1
                    newdata["KundenNr"] = KNr
                    newdata["Bem"] = text
                    if "lastschrift" in typ:
                        newdata["Konto"] = KtNr
                        newdata["Gegenkonto"] = 8100
                    else:
                        newdata["Konto"] = 4200
                        newdata["Gegenkonto"] = KtNr
                elif not "Konto" in newdata or not "Gegenkonto" in newdata:
                    KNr = 4 #"Bankaccount"
                    newdata["Konto"] = 4209
                    newdata["Gegenkonto"] = KtNr
                    newdata["KundenNr"] = KNr
                    newdata["Bem"] = typ + ": Gebühr "+ text
            if newdata: 
                # Kosten: 4200, Ertrag: 8900
                if not "Konto" in newdata and not "Gegenkonto" in newdata: 
                    print ("WARNING! Transaction not classified: ", "\""+ name + "\"",  typ, text, newdata["Betrag"])
                if newdata["Betrag"] < 0.0:
                    if not "Konto" in newdata: newdata["Konto"] = kosten
                    if not "KundenNr" in newdata: newdata["KtName"] = name
                    if not "Gegenkonto" in newdata: newdata["Gegenkonto"] = KtNr
                    newdata["Betrag"] = - newdata["Betrag"] 
                else:
                    if not "Konto" in newdata: newdata["Konto"] = KtNr
                    if not "Gegenkonto" in newdata: newdata["Gegenkonto"] = ertrag
                    if not "KundenNr" in newdata: newdata["GktName"] = name
                newdata["Period"] = period
                newdata["Eintrag"] = Afp_toInternDateString(today)
                if not "Bem" in newdata: newdata["Bem"] = text                                
                if not "Art" in newdata: newdata["Art"] = typ                                
                newdata["Beleg"] = BelegNr
                BelegNr += 1 
                newdata["Bem"] = newdata["Bem"][:250]
                newdata["Art"] = newdata["Art"][:20]
                if not skip_intern:
                    balance = Afp_addTransVal(balance, KtNr, newdata, debug)
                finanz.add_direct_transaction(newdata)
    return finanz, selection_lists

## import accountdata from csv-file and save it to database
# @param globals - global data including mysql connection
# @param input - AfpEvVerein SelectionList
# @param typ - import data typ
# @param debug - debug flag
def AfpImport_KontoStore(globals, input, typ, debug):
        finanz, selection_lists = AfpImport_Konto(globals, typ, debug)
        if finanz: finanz.store()
        if selection_lists:
            for sel in selection_lists:
                #sel.view()
                sel.store()
## import data from csv-file in Wiso-Format
# @param globals - global data including mysql connection
# @param input - AfpEvVerein SelectionList
# @param imp - format of import files
# @param debug - debug flag
def AfpImport_Club(globals, input, imp, debug):
    wiso = AfpImport_Member(globals, input, imp, debug)
    if wiso: 
        Afp_Familie(globals, debug)
        print("")
        Afp_CheckWiso(globals, wiso, debug)
    return

# Main   
if __name__ == "__main__": 
    lgh = len(sys.argv)
    imp = "wiso"
    debug = False
    execute = True
    for i in range(1, lgh):
        if sys.argv[i] == "-h" or  sys.argv[i] == "--help":
            print("usage: AfpImportMitglieder [option]")
            print("AfpImportMitglieder allows imports members of a club from a certain cvs-file.")
            print("Options and arguments:")
            print("-h, --help     display this text")
            print("-v,--verbose   display comments on all actions (debug-information)")
            print("-W,--wiso      menmber import from 'wiso' cvs-file format")
            print("-V,--volksbank account import from 'Volksbank' cvs-file format")
            print()
            execute = False
            break
        elif sys.argv[i] == "-v" or  sys.argv[i] == "--verbose":
            debug = True
        elif sys.argv[i] == "-W" or  sys.argv[i] == "--wiso":
            imp = "wiso"
        elif sys.argv[i] == "-V" or  sys.argv[i] == "--volksbank":
            imp = "vb"
    if debug: print("AfpImportMitglieder main:", sys.argv) 
    if execute:
        set = AfpSettings(debug)
        set.set("graphic-moduls", ["Adresse","Verein"])
        set.read_config("/home/akn/AfpVerein.cfg")
        mysql = AfpSQL(set.get("database-host"), set.get("database-user"), "YnVzc2U=","AfpVerein", set.is_debug())
        globals = AfpGlobal("test", mysql, set)
        ex = wx.App()
        verein = AfpEvVerein(globals,1)
        if imp == "vb":
            AfpImport_KontoStore(globals, verein, imp, debug)
        else:
            AfpImport_Club(globals, verein, imp, debug)
    if debug: print("AfpImportMitglieder main: dialog closed")
