#!/usr/bin/env python
# -*- coding: utf-8 -*-

## @package AfpCalendar.AfpCalRoutines
# AfpCalRoutines module provides classes and routines needed for calendar interaction.\n
# no display and user interaction in this modul.
#
#   History: \n
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de \n
#        09 April 2015 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is part of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel activities
#    Copyright© 1989 - 2023 afptech.de (Andreas Knoblauch)
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
import icalendar
from icalendar import Calendar, Event
from icalendar import vCalAddress, vText

from AfpBase.AfpBaseRoutines import *
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_getNow

 ## class to handle calendar interactions 
class AfpCalConnector (object):
    ## initialize AfpCalConnector class
    # @param globals - globals variables possibly holding smtp-server data
    # @param destination - string holding destination value
    # @param name - name of product, to be used in .ics header
    # @param version - version of product, to be used in .ics header
    # @param debug - flag for debug information
    def  __init__(self, globals, destination, name, version, debug = False):
        self.globals = globals
        self.debug = debug
        self.destination = None
        self.connector_name = name
        self.connector_version = version
        self.action = None
        self.target = None
        self.events = []
        self.event_index = None
        self.check_new = False
        self.content = None
        self.set_destination(destination)
        if self.debug: print("AfpCalConnector Konstruktor")
    ## set event-collection of one target to be processed
    # @param events - AfpCalEvents to be processed
    def set_events(self, events):
        print("AfpCalConnector.set_events:", events)
        self.events = events
        self.set_global_action()
    ##set destination string,perform check 
    # to be overwritten in devired class    
    def set_destination(self, destination):
        self.destination = None
        if destination:
            self.destination = self.check_destination(destination)
    ## perform check on destination string, return 'None' if check is not passed,  
    # to be overwritten in devired class    
    def check_destination(self, destination):
        return None
    ## return if all necessary requirements are available to perform action,  
    # to be overwritten in devired class    
    def is_available(self):
        return False
    ## execution routine, 
    # to be overwritten in devired class    
    def perform_action(self):
       return
    ## return if all necessary requirements are available and connector is ready to perform action,  
    def is_ready(self):
        return self.is_available() and not self.destination is None
    ## extract action needed from events
    def set_global_action(self):
        self.action = None
        for event in self.events:
            action = event.get_type()
            if self.action:
                if not action == self.action:
                    self.action = "modify"
            else:
                self.action = action
    ## generate calendar with one or all inserted events 
    def generate_ics_content(self):
        print("AfpCalConnector.generate_ics_content:", self.events)
        if self.events:
            calendar = Calendar()
            calendar.add('prodid', "-//" + self.connector_name + " calendar connector//afptech.de//")
            calendar .add('version', self.connector_version)
            if self.action == 'delete':
                calendar .add('method', 'CANCEL')
            added = False
            if self.event_index:
                calendar.add_component(self.events[self.event_index].get_event())
                added = True               
            else:
                for event in self.events:
                    calendar.add_component(event.get_event())
                    added = True 
            print("AfpCalConnector.generate_ics_content:", added, calendar)
            if added:
                self.content  = calendar
    ## write calendar into a ics-file
    # @param filepath - path to destination ics-file
    def write_to_ics_file(self, filepath):
        print("AfpCalConnector.write_to_ics_file:", self.content, filepath)
        if self.content :
            file = open(filepath, 'wb')
            file.write(self.content.to_ical())
            file.close()
            
## class to handle calendar writing to file
class AfpCalFileConnector (AfpCalConnector):
    ## perform check on destination string, return 'None' if check is not passed,  
    # overwrittenfrom AfpCalConnector 
    def check_destination(self, filename):
        #print "AfpCalFileConnector:", filename,  filename[-4:] == ".ics"
        if filename and filename[-4:] == ".ics":
            return filename
        else:
            return self.globals.get_value("tempdir") + "icalendar.ics"
    ## return if all necessary requirements are available to perform action,  
    # always return 'True' in this case, overwritten from AfpCalConnector  
    def is_available(self):
        return True    
    ## execution routine, 
    # overwritten from AfpCalConnector 
    def perform_action(self):
        if not self.destination:
            self.destination = self.globals.get_value("tempdir") + "icalendar.ics"
        self.generate_ics_content()
        self.write_to_ics_file(self.destination)
              
## class to handle calendar sending per e-mail
class AfpCalMailConnector (AfpCalConnector):
    ## initialize AfpCalConnector class
    # @param globals - globals variables possibly holding smtp-server data
    # @param recipient - string holding email address
    # @param name - name of product, to be used in .ics header
    # @param version - version of product, to be used in .ics header
    # @param debug - flag for debug information
    def  __init__(self, globals, recipient, name, version, debug = False):
        AfpCalConnector.__init__(self, globals, recipient, name, version, debug)
        self.send = True
        self.mailsender = None
        mailsender = AfpMailSender(globals, debug)
        if mailsender.is_possible():
            self.mailsender = mailsender
        if self.debug: print("AfpCalMailConnector Konstruktor")
    ## send mail directly (default)
    # @param flag - flag to switch 'keep mail' on and off
    def set_send_mail(self, flag = True):
        self.send = flag
    ## perform check on destination string, return 'None' if check is not passed,  
    # overwrittenfrom AfpCalConnector 
    def check_destination(self, destination):
        recipients = []
        split = destination.split(",")
        for recipient in split:
            if Afp_isMailAddress(recipient):
                recipients.append(recipient)
        if recipients:
            return recipients
        else:
            return None
    ## return if all necessary requirements are available to perform action,  
    # overwritten from AfpCalConnector  
    def is_available(self):
        return not self.mailsender is None 
    ## fill all necessary entries in mailsender
    def prepare_action(self):
        print("AfpCalMailConnector.prepare_action:", self.is_available())
        if self.is_available():
            filename = self.globals.get_value("tempdir") + "icalendar.ics"
            Afp_deleteFile(filename)
            self.generate_ics_content()
            self.write_to_ics_file(filename)
            print("AfpCalMailConnector.prepare_action file:", filename)
            if Afp_existsFile(filename):
                print("AfpCalMailConnector.prepare_action, file exists")
                self.mailsender.clear()
                for recipient in self.destination:
                    self.mailsender.add_recipient(recipient)
                self.mailsender.set_message(self.events[0].summary, self.events[0].description)
                self.mailsender.add_attachment(filename)
    ## execution routine, 
    # overwritten from AfpCalConnector 
    def perform_action(self):
        self.prepare_action()
        if self.send: self.mailsender.send_mail()
    ## retrieve mailsender, used for manuel mail-sending dialog
    def get_mailsender(self):
        return self.mailsender

## class to handle direct calendar connection via caldav 
class AfpCalCalConnector (AfpCalConnector):
    ## initialize AfpCalConnector class
    # @param globals - globals variables possibly holding smtp-server data
    # @param calname - string holding calendar name
    # @param name - name of product, to be used in .ics header
    # @param version - version of product, to be used in .ics header
    # @param debug - flag for debug information
    def  __init__(self, globals, calname, name, version, debug = False):
        AfpCalConnector.__init__(self, globals, calname, name, version, debug)
        self.delete_all = False
        self.check_new = False
        self.caldav_modul = None
        self.url = self.globals.get_value("caldav-url")
        if self.url:
            #path = self.globals.get_value("python-path") + self.globals.get_value("path-delimiter") + "caldav"
            #self.caldav_modul = AfpPy_Import("davclient", path)
            if AfpPy_checkModule('caldav'):
                self.caldav_modul = AfpPy_Import("caldav")
            print("AfpCalCalConnector Caldav Modul:", self.caldav_modul)
            if self.debug: print("AfpCalCalConnector Caldav Modul:", self.caldav_modul)
    ## set flag to remove events marked 'delete' from all possible calendars
    # @param flag - flag to switch *'delete all' on and off
    def set_delete_all(self, flag = False):
        self.delete_all = flag
    ## perform check on destination string, return 'None' if check is not passed,  
    # overwrittenfrom AfpCalConnector 
    def check_destination(self, calname):
        if calname:
            return  calname
        else:
            return None
    ## return if all necessary requirements are available to perform action,  
    # overwritten from AfpCalConnector  
    def is_available(self):
        return not self.caldav_modul is None
    ## execution routine,  overwritten from AfpCalConnector \
    def perform_action(self):
        if self.delete_all:
            self.delete_from_all_calendars()
        else:
            self.perform_single_calendar_action()
    ## execution routine, or a single calendar \n
    # events are processed individually
    def perform_single_calendar_action(self):
        print("AfpCalCalConnector.perform_action available:", self.is_available())
        if self.is_available():
            #calendars = self.caldav_modul.DAVClient(self.url, ssl_verify_cert = False).principal().calendars()
            calendars = self.caldav_modul.davclient.DAVClient(self.url, ssl_verify_cert = False).principal().calendars()
            calendar = None
            for cal in calendars:
                #print "AfpCalCalConnector.perform_action Calendar URLs:", cal.url 
                if self.url + self.destination + "/"  == cal.url:
                    calendar = cal
            if calendar:
                for self.event_index in range(len(self.events)):
                    self.generate_ics_content()
                    event = None
                    action = self.events[self.event_index].get_type() 
                    print("AfpCalCalConnector.perform_action:", self.destination, "\n", self.action , self.check_new, "\n", self.content.to_ical())
                    if action == "modify" or action == "delete" or (self.check_new and action == "new"):
                        uid = self.events[self.event_index].get_uid()
                        event =self.get_event_from_uid(calendar, uid)
                        print("AfpCalCalConnector.perform_action event found:", self.destination, "\n", event)
                    if event and (action == "modify" or action == "new"):
                        event.set_data(self.content.to_ical())
                        event.save()  
                        print("AfpCalCalConnector.perform_action event modified:", self.destination, "\n", event)  
                    if event is None and self.action == "new":
                        event = calendar.add_event(self.content.to_ical())
                        print("AfpCalCalConnector.perform_action event created:", self.destination, "\n", event)
                    if event and self.action == "delete":
                        event.delete()
                        print("AfpCalCalConnector.perform_action event deleted:", self.destination, "\n", event)
            else:
                print("ERROR: AfpCalCalConnector.perform_action calendar", self. destination, "not found!!")
    ## delete events with type 'delete' from all possible calendars
    def delete_from_all_calendars(self):
        if self.is_available():
            calendars = self.caldav_modul.davclient.DAVClient(self.url, ssl_verify_cert = False).principal().calendars()
            for afpvent in self.events:
                uid = afpvent.get_uid()
                print("AfpCalCalConnector.delete_from_all_calendars delete event:", uid)
                if uid and afpvent.get_type() == "delete":
                    for calendar in calendars:
                        event = self.get_event_from_uid(calendar, uid)
                        if event:
                            event.delete()
                            print("AfpCalCalConnector.delete_from_all_calendars event deleted from", calendar)
    ## retrieve event with given uid
    # @param cal - calendar where event should be extracted from
    # @param uid - uniform identification of event
    def get_event_from_uid(self, calendar, uid): 
        eventurl = str(calendar.url)  + uid + ".ics"
        try:
            event = calendar.event_by_url(eventurl)
        except:
            event = None
        return event
                
## class to handle calendar events 
class AfpCalEventTarget(object):
    ## initialize AfpCalEventTarget class, the destination inputs (calname, email, filename) are used
    # each collection is used to be targeted to one destination. If different destinations are given, they are used in the following order:
    # - calname - name of calendar if manipulation via direct calendar connection is desired and present
    # - email - email-address of recipient if sending ics-file via email is desired and present
    # - filename - name of file, if writing to different files is desired \n
    # - 'None' - all entries will be sampled into one calendar \n
    # even if the appropriate manipulation methods (calendar connection, email) are not present the events 
    # will be grouped by the hirarchially higher property!
    # @param debug - flag for debug information    
    # @param calname - name of destination calendar (for direct access)
    # @param email - email address this event is destinated to
    # @param filename - name for output file,      
    def  __init__(self, debug = False, calname = None, email = None, filename = None):
        self.globals = globals
        self.debug = debug
        self.calendar = calname
        self.email = email
        self.filename = filename
        self.events = []
        if self.debug: print("AfpCalEventTarget Konstruktor")
    ## return if at least one event has been added
    def is_valid(self):
        return len(self.events) > 0
    ## add an AfpCalEvent to the collection
    # @param event - AfpCalEvent to be added
    def add_event(self, event):
        self.events.append(event)
    ## retrieve events from collectioin
    def get_events(self):
        return self.events
        
## class to hold calendar event data
class AfpCalEvent(object):
    ## initialize AfpCalEvent event data class
    # @param globals - globals variables holding host data
    # @param debug - flag for debug information    
    # @param typ - type of modification for this event, possible values:
    # - new - creation of an new event, if the check_new flag is set, works as 'modify' for existing events
    # - modify - modification of an existing event
    # - delete - deletation of an existing event
    def  __init__(self, globals, debug = False, typ = "new"):
        self.globals = globals
        self.debug = debug
        self.type = typ
        self.starttime = None
        self.endtime = None
        self.uid = None
        self.summary = None
        self.description = None
        self.location = None
        self.organizer = None
        self.attendees = []
        self.attachments = []
        self.ical_event = None
        if self.debug: print("AfpCalEvent Konstruktor")
    ## set begin and end to event
    # @param start - datetime for begin of event
    # @param end - datetime for end of event
    def set_times(self, start, end):
        self.starttime = Afp_toTzDatetime(start)
        self.endtime = Afp_toTzDatetime(end)
    ## set unique ID
    # @param uid - if given unique ID to be used, otherwise hostconfiguration and timestamp is used
    def set_uid(self, uid = None):
        if uid:
            self.uid = uid
        else:
            self.uid = self.globals.get_value("user") + "@" 
            self.uid += self.globals.get_value("net-name") + "." 
            self.uid +=  self.globals.get_value("name") + "."
            self.uid +=  self.globals.get_value("database-host") + ":" 
            self.uid +=  Afp_toString(Afp_getNow(True))
    ## returns the uid, generates it if necessary
    def get_uid(self):
        if self.uid is None:
            self.set_uid()
        return self.uid
    ## set text-portions of event
    # @param sum - summary of event
    # @param desc - description of event
    def set_text(self, sum, desc = None):
        if sum: self.summary = sum
        if desc: self.description = desc
    ## add attendee to list
    # @param name - name of attendee
    # @param mail - mail address of attendee
    def add_attendee(self, name, mail):
        self.attendee.append([mail, name])
    ## add attattachment to list
    # @param url - url of attachment \n
    # possible values are par example:
    # - http://webadress
    # - file://path_to_file
    # - afpp://direct_afp_execution_address
    def add_attachment(self, url):
        self.attachments.append(url)
    ## set organistion values
    # @param name - name of organizer
    # @param mail - mail address of organizer
    # @param loc - location for event
    def set_organize(self, name, mail, loc):
        orga = []
        if mail: orga.append(mail)
        else: orga.append("")
        if name: orga.append(name)
        else: orga.append("")
        if orga: self.organizer = orga
        if loc: self.location = loc
    ## set complete event in one shot
    # @param start - datetime for begin of event
    # @param end - datetime for end of event
    # @param summary - summary of event    
    # @param uid - if given unique ID to be used
    # @param description - if given, description of event    
    # @param attendees - if given, attendees of event, given as [[mail, name], ...]   
    # @param organizer - if given, organizer of event, given as [mail, name]   
    # @param location - if given, location for event
    def set_event(self, start, end, summary, uid = None, description = None, attendees = None, attachments = None, organizer = None, location = None):
        self.set_times(start, end)
        self.set_text(summary, description)
        self.set_uid(uid)
        if attendees: self.attendees = attendees
        if attachments: self.attachments = attachments
        if organizer: self.organizer = organizer
        if location: self.location = location
    ## return modification type of this event
    def get_type(self):
        return self.type
    ## check if the minimum entries are given, to build a proper event
    def is_ready(self):
        return (self.starttime and self.endtime and self.summary) or (self.type == 'delete'and self.uid)
    ## generates ical event entries
    def generate_ical_event(self):
        if self.is_ready():
            event = Event()
            if self.type == 'delete':
                event.add('dtstamp', Afp_getNow(True))
                event['uid'] = self.get_uid()
                event['status'] =  vText('CANCELLED')
            else:
                event.add('summary', self.summary)
                event.add('dtstart', self.starttime)
                event.add('dtend', self.endtime)
                event.add('dtstamp', Afp_getNow(True))
                event['uid'] = self.get_uid()
                #event.add('priority', 5)
                if self.description: event.add('description', self.description)
                if self.organizer:
                    organizer = vCalAddress("MAILTO:" + self.organizer[1])
                    organizer.params['cn'] = vText(self.organizer[0])
                    event['organizer'] = organizer
                if self.location: event['location'] = vText(self.location)
                if self.attendees:
                    for attend in self.attendees:
                        attendee = vCalAddress("MAILTO:"+ attend[1])
                        attendee.params['cn'] = vText(attend[0])
                        attendee.params['ROLE'] = vText('REQ-PARTICIPANT')
                        event.add('attendee', attendee, encode=0)                
                if self.attachments:
                    for attach in self.attachments:
                        print("AfpCalEvent.generate_ical_event attach:", attach)
                        event.add("attach", attach)
            self.ical_event = event
    ## get ical event data
    def get_event(self):
        if self.ical_event is None and self.is_ready():
            self.generate_ical_event()
        return self.ical_event
        
## class to handle calendar interactions 
class AfpCalendar (object):
    ## initialize AfpCalendar class
    # @param globals - globals variables possibly holding caldav-server and smtp-server data
    # @param debug - flag for debug information
    # @param use_calendar - flag if direct calendar connection should be used, if available
    # @param use_email - flag if .ics data should sent via email, if available
    # @param use_file - flag if .ics data should be written to disc, if no other method is available
    def  __init__(self, globals, debug = False, use_calendar = True, use_email = True,  use_file = True):
        self.globals = globals
        self.debug = debug
        self.name = globals.get_string_value("name")
        self.version = globals.get_string_value("version")
        self.cal_connector = None
        self.email_connector = None
        self.file_connector = None
        self.allow_no_filename = use_file
        self.keep_mails = False
        self.mailsenders = []
        connector = AfpCalCalConnector(globals, None, self.name, self.version, debug)
        print("AfpCalendar.init CalConnector:", connector.is_available())
        if connector.is_available() and use_calendar:
            self.cal_connector = connector
        connector = AfpCalMailConnector(globals, None, self.name, self.version, debug)
        if connector.is_available() and use_email:
            self.email_connector = connector
        self.file_connector = AfpCalFileConnector(globals, None, self.name, self.version, debug)
        self.target = None
        self.targets = []
        if self.debug: print("AfpCalendar Konstruktor Calendar connection:", self.cal_connector, "E-Mail:", self.email_connector) 
    ## add target collection to targets
    # @param target - valid AfpCalEventTarget collection to be added
    def add_target(self, target):
        if target.is_valid():
            self.targets.append(target)
    ## generate new target for direct input of events
    # @param calname - name of destination calendar (for direct access)
    # @param email - email address this target is destinated to, different mail addresses may be separated by a ','
    # @param filename - name for output file,      
    def gen_new_target(self, calname, email, filename = None):
        if self.target and self.target.is_valid():
            self.targets.append(self.target)
        self.target = AfpCalEventTarget(self.debug, calname, email, filename)
    ## generate filname if calendarname or email is given
    # @param calname - name of destination calendar (for direct access)
    # @param email - email address this target is destinated to, if different mail addresses are separated by a ',', the first address is used
    def gen_target_filename(self, calname, email):
        fname = None
        dir = self.globals.get_value("caldir")
        if not dir: dir = self.globals.get_value("tempdir")
        if  calname:
            fname = dir + "calendar_" + calname + ".ics"
        elif email: 
            split = email.split(",")
            fname = dir + split[0].strip() + ".ics"
        else:
            fname =  dir + "icalendar.ics"
        return fname
    ## clear targets and mailsenders cache
    def clear_targets(self):
        self.target = None
        self.targets = [] 
    ## clear mailsenders
    def clear_senders(self):
        self.mailsenders = []
    ## add a new event to the actuel target collection \n
    # convenience method to avoid explicit AfpCalEvent and AfpCalEventTarget construction (not all parameters possible)
    # @param typ - type of modification for this event, possible values:
    # - new - creation of an new event, if the check_new flag is set, works as 'modify' for existing events
    # - modify - modification of an existing event
    # - delete - deletation of an existing event
    # @param start - datetime for begin of event
    # @param end - datetime for end of event
    # @param summary - summary of event    
    # @param uid - if given unique ID to be used
    # @param description - if given, description of event    
    # @param location - if given, location for event
    def add_event_to_target(self, typ, start, end, summary, uid = None, description = None, attachment = None, location = None):
        if self.target:
            event = AfpCalEvent(self.globals, self.debug, typ)
            if typ == "delete":
                event.set_uid(uid)
            elif start and end:
                orgamail = self.globals.get_value("mail-sender")
                if orgamail is None: orgamail = ""
                organizer =  [self.name, orgamail]
                attach = None
                if attachment: attach = [attachment]
                event.set_event(start, end, summary, uid, description, None,  attach, organizer, location)
            if event.is_ready():
                self.target.add_event(event)
            elif self.debug:
                print("WARNING: AfpCalendar.add_event_to_target: event data not complete!")
        elif self.debug:
            print("WARNING: AfpCalendar.add_event_to_target: target collection not present!")
    ## perform event syncronisation (drop events on targets)
    # @param typ - types used, the following possibillities are implemented:
    # - None - use file-creation as fallback
    # - not None - FileConnector: strict fileusage, don't generate filename if not given
    # - 'keep_mails' - MailConnector: mails are not send, but mailsenders cached for later use
    # - 'delete_all' - CalConnector: try to delete event from all possible calendars
    def drop_on_targets(self, typ = None):
        if self.target and self.target.is_valid():
            self.targets.append(self.target)
        self.target = None
        print("AfpCalendar.drop_on_targets:", self.targets)
        if self.targets:
            for target in self.targets: 
                print("AfpCalendar.drop_on_targets Calendar:", target.calendar, self.cal_connector)
                print("AfpCalendar.drop_on_targets EMail:", target.email, self.email_connector)
                print("AfpCalendar.drop_on_targets File:", target.filename, self.file_connector)
                email_kept = False
                connector = None
                if target.calendar and self.cal_connector:
                    connector = self.cal_connector
                    destination = target.calendar
                    if typ == "delete_all":
                        connector.set_delete_all(True)
                    else:
                        connector.set_delete_all()
                elif target.email and self.email_connector:
                    connector = self.email_connector
                    destination = target.email  
                    if typ == "keep_mails": 
                        connector.set_send_mail(False)
                        email_kept = True
                    else:
                        connector.set_send_mail()
                elif target.filename or type is None:
                    connector = self.file_connector
                    if target.filename is None:
                        destination = self.gen_target_filename(target.calendar, target.email)
                    else:
                        destination = target.filename                         
                if connector:
                    connector.set_destination(destination)
                    connector.set_events(target.get_events()) 
                    connector.perform_action()
                    if email_kept: 
                        self.mailsenders.append(connector.get_mailsender())
                else:
                    print("WARNING: AfpCalendar.drop_on_targets no connector available!", target.calendar, target.email, target.filename)
    ## get mailsenders
    def get_mailsenders(self):
        return self.mailsenders
    ## read ics-file and print component names
    # @param filepath - path to source ics-file   
    def read_ics_components(self, filepath):
        file = open(filepath,'rb')
        gcal = Calendar.from_ical(file.read())
        for component in gcal.walk():
            print(component.name)
        file.close()
    ## read ics-file and print events
    # @param filepath - path to source ics-file 
    def read_ics_events(self, filepath):
        file = open(filepath,'rb')
        gcal = Calendar.from_ical(file.read())
        for component in gcal.walk():
            if component.name == "VEVENT":
                print(list(component.keys()))
                for key in list(component.keys()):
                    if type(component.get(key)) == list:
                        print(key,":", type(component.get(key)), component.get(key))
                    else:
                        print(key,":", type(component.get(key)), vars(component.get(key)), component.get(key))
        file.close()
        
