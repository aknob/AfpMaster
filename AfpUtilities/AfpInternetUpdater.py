#!/usr/bin/env python
# -*- coding: utf-8 -*-

# AfpInternetUpdater is a helper utility to update internet sites in an easy way
# it holds 3 classes:

# AfpSlideShowGenerator generates HTML Slideshow from given Layout and allows FTP-Upload to an Internet site.
# AfpCaldendarEntries      generates a javascript file holding given calendar entries
# AfpFTPConnector           handles the FTP connections

#
#   History: \n
#        20 Nov. 2024 - changes for python 3.12 - Andreas.Knoblauch@afptech.de 
#        30 Dez. 2021 - conversion to python 3 - Andreas.Knoblauch@afptech.de
#        16 Jul. 2021 - inital code generated - Andreas.Knoblauch@afptech.de

#
# This file is an extract of the  'Open Source' project "BusAfp" by 
#  AfpTechnologies (afptech.de)
#
#    BusAfp is a software to manage coach and travel acivities
#    Copyright (C) 1989 - 2025 afptech.de (Andreas Knoblauch)
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

import sys
import os
import ftplib
import glob
import io
import base64
import wx

import AfpBase
from AfpBase import AfpBaseDialog, AfpUtilities
from AfpBase.AfpBaseDialog import AfpDialog, AfpReq_Info, AfpReq_Question, AfpReq_Text, AfpReq_FileName, AfpReq_Calendar, AfpReq_MultiLine
from AfpBase.AfpUtilities import AfpBaseUtilities, AfpStringUtilities
from AfpBase.AfpUtilities.AfpBaseUtilities import Afp_existsFile, Afp_getGlobalVar, Afp_genHomeDir, Afp_readFileNames, Afp_copyFile, Afp_getToday
from AfpBase.AfpUtilities.AfpStringUtilities import Afp_pathname, Afp_isRootpath, Afp_addRootpath, Afp_fromString, Afp_toString, Afp_toIntString, Afp_getToLastChar, Afp_toDateString, Afp_ChDatum, Afp_readLinesFromFile


## main internet updater routine  \n
# @param config - path and name of configuration file
# @param debug - debug flag
def Afp_InternetUpdater(config, debug):
    settings = None
    path_deli = Afp_getGlobalVar("path-delimiter") 
    if config is None:
        config = Afp_pathname(Afp_genHomeDir(), path_deli) + "AfpInternetUpdater.cfg"
    if Afp_existsFile(config):
        settings = Afp_loadSettings(config,"cal,show", debug) 
        if debug: print("Afp_InternetUpdater settings:", settings)
        liste = []
        for set in sorted(settings.keys()):
            if "cal" == set[:3]:
                liste.append(set[4:])
            elif "show-slideshows" == set:
                liste.append("Slideshows")
            elif "show" == set[:4]:
                liste.append("Slides " + set[5:])
        ok = True
        while not ok == False:
            results = AfpReq_MultiLine( "Bitte Updatekonfiguration für das Internet auswählen.", "", "Button", liste, "Internet Update", 300)
            if results:
                result = ""
                for res in results:
                    if res: result = res
                ftp = AfpFTPConnector(config, debug)
                if "Slideshows" in result:
                    slide = AfpSlideShowGenerator(ftp, "Slideshows", config, debug)
                    Ok = AfpLoad_Slideshow(slide) 
                elif "Slides" in result:
                    slide = AfpSlideShowGenerator(ftp, result, config, debug)
                    Ok = AfpLoad_Slideshow(slide) 
                else:
                    cal = AfpCalendarEntries(ftp, result, config, debug)
                    Ok = AfpLoad_calEvents(cal) 
                if ftp: ftp.quit()
            else:
                ok = False
    else:
        AfpReq_Info("Kein Konfigurationsfile angegeben oder ermittelt!","Info siehe 'AfpInternetUpdater --help', Programm wird beendet!","Fehlende Konfiguration")
## get filenames from directory
# @param path - if given, directory from which files have to be listed, default: current directory
# @param ext - if given, list of file extensions to be used, defaut: all file extensions
def Afp_getDirContent(path=None, ext=None):
    filenames = []
    dirnames = []
    for root, dirs, files in os.walk(path):
        #print "Afp_getDirContent walk:", root, dirs, files
        for file in files:
            if ext:
                for ex in ext:
                    if file.endswith(ex):
                        filenames.append(os.path.join(root, file).replace("\\\\", "\\"))
            else:
                filenames.append(os.path.join(root, file).replace("\\\\", "\\"))
        for dir in dirs:
            dirnames.append(os.path.join(root, dir).replace("\\\\", "\\"))
            #print "Afp_getDirContent dirs:", dir, dirnames
        break
    return filenames, dirnames
## get filenames from directory
# @param dir - if given, directory from which files have to be listed, default: current directory
# @param ext - if given, list of file extensions to be used, defaut: all file extensions
def Afp_getFilenames(dir=None, ext=None):
    files, dirs = Afp_getDirContent(dir, ext)
    #if dir is None: dir = ""
    #if ext is None: ext = ["*"]
    #print "Afp_getFilenames:", dir, ext
    #files = []
    #[files.extend(glob.glob(dir + '*.' + e)) for e in ext] 
    #if files and "\\\\" in files[0]:
    #    for i in range(len(files)):
    #        files[i] = files[i].replace("\\\\", "\\")
    return sorted(files)
## get directorynames from directory
# @param dir - if given, directory from which directories have to be listed, default: current directory
# @param deli - if given, pathdelimiter, default: "/" is used
def Afp_getDirnames(dir=None, deli="/"):
    files, dirs = Afp_getDirContent(dir, None)
    #if dir is None: dir = ""
    #files = []
    #[files.extend(glob.glob(dir + '*' + deli))]
    #return sorted(files)
    return sorted(dirs)
## create a directory
# @param dir - full path of the directory to be created
def Afp_genDir(dir):
    if not dir is None: 
        os.makedirs(dir)

## routine to load settings from file
# @param config - path and name of configuration file
# @param idents - if given, strings to filter settings, separated by commas
# @param debug - if given, debug flag
def Afp_loadSettings(config, idents="", debug=False):
    settings = None
    if Afp_existsFile(config):
        if idents:
            filter = idents.split(",")
        else:
            filter = None
        settings = {}
        fin = open(config , 'r') 
        for line in fin:
            cline = line.split("#")
            sline = cline[0].split("=",1)
            if len(sline) > 1:
                name = sline[0].strip()
                if filter:
                    load = False
                    for f in filter:
                        if name[:len(f)] == f:
                            load = True
                            break
                else:
                    load = True
                if load:
                    if debug: print("Afp_loadSettings:", line[:-1])
                    settings[name] = Afp_fromString(sline[1].strip())
    return settings

## convert german 'Umlaute' from html-representation to UTF-8
# @param text - text to be converted
def Afp_fromHtml(text):
    text = text.replace("&auml;", "ä")
    text = text.replace("&ouml;", "ö")
    text = text.replace("&uuml;", "ü")
    text = text.replace("&Auml;", "Ä")
    text = text.replace("&Ouml;", "Ö")
    text = text.replace("&Uuml;", "Ü")
    text = text.replace("&szlig;", "ß")
    return text
## convert german 'Umlaute'  in UTF-8 to html-representation
# @param text - text to be converted
def Afp_toHtml(text):
    text = text.replace("ä", "&auml;")
    text = text.replace( "ö", "&ouml;")
    text = text.replace( "ü", "&uuml;")
    text = text.replace( "Ä", "&Auml;")
    text = text.replace( "Ö", "&Ouml;")
    text = text.replace( "Ü", "&Uuml;")
    text = text.replace( "ß", "&szlig;")
    return text

## class to generate silde shows
class AfpSlideShowGenerator(object):
    ## initialize AfpSlideShowGenerator class
   # @param ftpcon - AfpFTPConnector to be used for download and upload
    # @param type - type to identify the used files
    # @param config - path and name of configuration file
    # @param debug - if given, debug-flag
    def  __init__(self, ftpcon, type, config, debug = False):  
        self.ftpcon = ftpcon
        if type[:6] == "Slides" and type != "Slideshows":
            self.type = type[7:]
        else:
            self.type = type
        self.name = None
        self.new = False
        self.changed = False
        self.debug = debug
        self.collect_dir = None
        self.iwidth = 185
        self.iheight = 125
        self.source_list = wx.ImageList(self.iwidth, self.iheight)
        self.source_pathes = None
        self.show_list = wx.ImageList(self.iwidth, self.iheight)
        self.show_pathes = None
        self.show_index = None
        self.show_texts = None
        self.show_deleted = None
        self.local_file = None
        self.serial_show_tags = ["<div class=\"mySlides", "  </div>", "<span class=\"dot\" onclick", "<span class=\"dot\" onclick"]
        self.serial_index_tags = ["<div id=\"show-", "</div>", "<div id=\"showloop\">", "</div>"]
        self.datalist = None
        self.pathdelimiter = Afp_getGlobalVar("path-delimiter")
        if config:
            self.localdir = Afp_getToLastChar(config, self.pathdelimiter)
        else:
            self.localdir = Afp_pathname(Afp_genHomeDir(), self.pathdelimiter)  
            config = self.localdir + "AfpInternetUpdater.cfg"
        self.slide_template = self.localdir + "AfpInternetSlideShowGenerator.template"
        self.index_template = self.localdir + "AfpInternetSlideShowIndexInsert.js"
        self.localindex = "index.js"
        self.localroot = None
        self.localpath = None
        self.localname = None
        self.remotepath = None
        self.remotename = None
        self.max_thumbs_per_line = None
        self.settings = {}    
        self.settings = Afp_loadSettings(config, "show,local", self.debug)
        if "local-root" in self.settings: 
            self.localroot = Afp_pathname(self.settings["local-root"], self.pathdelimiter)
            self.localdir = self.localroot
        if "local-clientname" in self.settings: 
            self.name = self.settings["local-clientname"]
        if "local-max-thumbs-per-line" in self.settings: 
            self.max_thumbs_per_line = Afp_fromString(self.settings["local-max-thumbs-per-line"])
        #if self.ftpcon:
            #self.ftpcon.invoke_ftp() 
        self.set_locrem()
        #self.read_serial_tags()
        if self.debug: print("AfpSlideShowGenerator Konstruktor") 
     ## destructor
    def __del__(self):   
        if self.debug: print("AfpSlideShowGenerator Destruktor") 

    ## set local and remote filenames from settings entry
    def set_locrem(self):
        #print "AfpSlideShowGenerator.set_locrem:","show-" + self.type, self.settings
        names = None
        if "show-" + self.type in self.settings:
            names = self.settings["show-" + self.type]
        elif "show-slideshows"  in self.settings:
            names = self.settings["show-slideshows"]
        if names:
            split = names.split(",") 
            local = split[0]
            remote = None
            if len(split) > 1:
                remote = split[1]
            if remote is None: remote = local
            if Afp_isRootpath(local):
                localfile = Afp_pathname(dir, self.pathdelimiter, True)
            else:
                local = Afp_addRootpath(self.localroot, local)
                localfile = Afp_pathname(local, self.pathdelimiter, True)
            lsplit = localfile.split(self.pathdelimiter)
            self.localpath = self.pathdelimiter.join(lsplit[:-1]) + self.pathdelimiter
            self.localname = lsplit[-1]
            remotefile = Afp_pathname(remote, "/", True)
            rsplit = remotefile.split("/")
            self.remotepath = "/".join(rsplit[:-1]) + "/"
            self.remotename = rsplit[-1]
            if self.ftpcon:
                self.ftpcon.set_remotedir(self.remotepath)
                self.ftpcon.set_localdir(self.localpath)
        if self.debug: 
            print("AfpSlideShowGenerator.set_locrem local:" , self.localpath, self.localname, "remote:", self.remotepath, self.remotename)
    ## retrieve type of slideshow
    def get_type(self):
        return self.type
    ## retrieve name of client
    def get_name(self):
        return self.name
    ## check if show has changed
    def has_changed(self):
        return self.changed or self.new
    ## retrieve localname of slideshow
    # @param blanks - flag if underscores should be replaced by blanks
    def get_localname(self, blanks = False):
        if blanks:
            return self.localname.replace("_", " ")
        else:
            return self.localname
    ## retrieve complete path of slideshow
    # @param complete - flag if concatinated path is delivered
    def get_localpath(self, complete=True):
        if complete:
            return self.localpath + self.localname + self.pathdelimiter
        else:
            return self.localpath
    ## get ftp-handler
    def get_ftp(self):
        return self.ftpcon
    ## get background color for sildeshow html-file
    def get_bgColor(self): 
        if self.localname == "Homepage":
            color = "#8CC8EA"
        else:
            color = "#cb1beb"
        return color   
    ## get background image for sildeshow html-file
    def get_background(self):
        if self.localname == "Homepage":
            image = "../../../images/hg-mainframe.gif"
        else:
            image = "../images/hg-frame.gif"
        return image
    ## return if actuel slideshow exists on filesystem
    def show_exists(self):
        exists = False
        if self.localname in self.get_actuel_shows():
            exists = True
        return exists
    ## set new flag
    # @param new - value new flag should be set to
    def set_new(self, new):
        self.new = new
     ## set local path and name where slideshow should be taken from
    # @param path - new localpath for slideshow 
    def set_localshow(self, path):
        lsplit = path.split(self.pathdelimiter)
        self.set_localpath(self.pathdelimiter.join(lsplit[:-1]) + self.pathdelimiter)
        self.set_show(lsplit[-1])
        return lsplit[-1]
    ## set path where slideshow shoulö be written to
    # @param path - new localpath for slideshow to be written to
    def set_localpath(self, path):
        if not path[-1] == self.pathdelimiter:
            path += self.pathdelimiter
        self.localpath = path
    ## set slidesshow with given name
    # @param name - new localname of slideshow to be loaded
    def set_show(self, name):
        name = name.replace(" ", "_")
        self.localname = name
        self.changed = False
        if name in self.get_actuel_shows():
            self.new = False
        else:
            self.new = True
    ## set attched text of images in show list
    # @param index - index of image in list
    # @param text - text to be attached
    def set_image_text(self,  index, text):
        if not self.show_texts:
            self.show_texts = [None] * self.get_image_len()
        if index >=0 and index < len(self.show_texts):
            self.show_texts[index] = text
            self.changed = True
        #print "AfpSlideShowGenerator.set_image_text:", index, self.show_texts, self.changed
    ## get imageLists
    # @param typ - typ of list to be retrieved
    def get_image_list(self, typ="show"):
        if typ == "source":
            return self.source_list
        else:
            return self.show_list
    ## get text attached to images from list
    # @param index - index of image in list, where name has to be extracted for
    # @param typ - typ of list to be retrieved
    def get_image_text(self,  index=0, typ="show"):
        text = ""
        if typ == "source":
            text = self.get_source_filename(index)
        else:
            if index >=0 and index < len(self.show_texts):
                text = self.show_texts[index]
        #return  Afp_toString(index+1) + " " + text
        return  text
    ## get length of imageLists
    # @param typ - typ of list to be retrieved
    def get_image_index(self, index, typ="show"):
        if typ == "show" and len(self.show_index) > index:
            return self.show_index[index]
        return index
   ## get length of imageLists
    # @param typ - typ of list to be retrieved
    def get_image_len(self, typ="show"):
        return self.get_image_list(typ).GetImageCount()
    ## generate list of source directory
    # param dir - path to directory to load, if a filename is given, the including directory will be taken
    def gen_source_list(self, dir):
        #print "AfpSlideShowGenerator.gen_source_list:", dir
        split = dir.split(self.pathdelimiter)
        if "." in split[-1]:
            dir = self.pathdelimiter.join(split[:-1])
        self.source_pathes = self.get_filenames(dir)
        if self.debug: print("AfpSlideShowGenerator.gen_source_list:", self.source_pathes)
        #print "AfpSlideShowGenerator.gen_source_list:", self.source_pathes
        for file in self.source_pathes:
            img = wx.Image(file, wx.BITMAP_TYPE_ANY).Rescale(self.iwidth,self.iheight).ConvertToBitmap()
            self.source_list.Add(img)
    ## generate list of show directory
    # param dir - if given, path to directory to load
    def gen_show_list(self, dir=None):
        self.show_pathes = self.get_filenames(dir)
        if self.debug: print("AfpSlideShowGenerator.get_show_list:", self.show_pathes)
        self.show_list.RemoveAll()
        if self.show_pathes:
            for file in self.show_pathes:
                img = wx.Image(file, wx.BITMAP_TYPE_ANY).Rescale(self.iwidth,self.iheight).ConvertToBitmap()
                self.show_list.Add(img)
        self.extract_imagedata(dir)
    ## get filename from path list
    # @param index - index of path in pathlist, where name has to be extracted from
    def get_source_filename(self, index=0):
        if index >= 0 and index < len(self.source_pathes):
            return self.source_pathes[index].split(self.pathdelimiter)[-1]
        else:
            return self.source_pathes[index]
            
    ## add source image to show list
    # @param index - index of file in source pathes
    # @param show - index in show-list where image is inserted in front of
    # @param text - text to be attached to image
    def add_source_to_show(self, index, show, text):
        if index >=0 and index < len(self.source_pathes):
            path = self.source_pathes[index]
            img = wx.Image(path, wx.BITMAP_TYPE_ANY).Rescale(self.iwidth,self.iheight).ConvertToBitmap()
            self.show_list.Add(img)
            self.insert_imagedata(show, self.show_list.GetImageCount()-1, text, path)
            self.changed = True
    ## delete image from show list
    # @param show - index in show-list of image to be deleted
    def delete_from_show(self, show):
        if self.show_deleted is None: self.show_deleted = []
        index = self.show_index.pop(show)
        for i in range(len(self.show_index)):
            if self.show_index[i] > index: self.show_index[i] -= 1
        self.show_list.Remove(index)
        self.show_texts.pop(show)
        self.show_deleted.append(self.show_pathes.pop(show))
        self.changed = True
    ## move image up one position
    # @param show - index in show-list of image to be moved
    # @param down - flag to move image down
    def move_image(self, show, down=False):
        swap = None
        if down:
            if show > 0:
                swap = show - 1
        else:
            if show < len(self.show_index) - 1:
                swap = show + 1
        #print "AfpSlideShowGenerator.move_image:", swap, show, len(self.show_index)
        if not swap is None and show < len(self.show_index):
            val = self.show_index[show]
            self.show_index[show] = self.show_index[swap]
            self.show_index[swap] = val
            val = self.show_texts[show]
            self.show_texts[show] = self.show_texts[swap]
            self.show_texts[swap] = val
            self.changed = True
         
    ## extract serial tags from template file
    def read_serial_tags(self):
        if self.template and Afp_existsFile(self.template):
         fin = open(fnamself.template , 'r') 
         for line in fin:
             if "div class=\"mySlides " in line:
                self.serial_show_tags = [line.strip(), "</div>", 1]
                break
         fin.close()
         
    ## get image text and order from html-file
    # @param dir - if given, directory where images are found
    def extract_imagedata(self, dir=None):
        self.show_texts = []
        self.show_index = []
        files = []
        if dir is None:
            dir = self.localpath + self.localname + self.pathdelimiter
        #print "AfpSlideShowGenerator.extract_imagedata dir:", dir
        split = dir.split(self.pathdelimiter)
        name = split[-2]
        path = self.pathdelimiter.join(split[:-2]) + self.pathdelimiter
        fname = path + name + ".html"
        #print "AfpSlideShowGenerator.extract_imagedata file:", fname, Afp_existsFile(fname)
        if Afp_existsFile(fname):
            fin = open(fname, "r")
            skip = True
            cnt = 0
            text = None
            filename = None
            for line in fin:
                if self.serial_show_tags[0] in line:
                    skip = False
                    cnt = 0
                    continue
                if skip: continue 
                cnt += 1
                if cnt == 1: continue
                elif cnt == 2:
                    split = line.split()
                    for sp in split:
                        if "src=" in sp:
                            filename = sp[5:-1]
                elif cnt == 3:
                    line = line.strip()
                    if len(line) > 24 and "<div class=\"text\">"  == line[:18]:
                        text = line[18:-6]
                elif cnt > 3 or self.serial_show_tags[1] in line:
                    self.show_texts.append(Afp_fromHtml(text))
                    files.append(filename.split("/")[-1]) 
                    skip = True
            fin.close()
        show_files = []
        for path in self.show_pathes:
            show_files.append(path.split(self.pathdelimiter)[-1])
        for file in files:
            for i in range(len(show_files)):
                show = show_files[i]
                if file == show:
                    self.show_index.append(i)   
                    break
        if self.debug: print("AfpSlideShowGenerator.extract_imagedata:", self.show_texts, self.show_index)
        #print "AfpSlideShowGenerator.extract_imagedata: \n", self.show_texts, "\n",self.show_index, "\n", self.show_pathes
    ## insert imagedata at given index into appropriate lists
    # @param index - index where value has to be inserted, original vlaues will be shifted to index+1
    # @param image_index - index of image in image-list
    # @param path - complete filename of inserted image
    def insert_imagedata(self, index, image_index, text, path):
        self.show_index = self.insert_into_list(self.show_index, index, image_index)
        self.show_texts = self.insert_into_list(self.show_texts, index, text)
        self.show_pathes = self.insert_into_list(self.show_pathes, image_index, path)
        #print "AfpSlideShowGenerator.insert_imagedata:", index, image_index, text, path
        #print "AfpSlideShowGenerator.insert_imagedata:", self.show_index, self.show_texts, self.show_pathes

    ## get all actuel possible slidehows
    # @param blanks - flag if underscores should be replaced by blanks
    def get_actuel_shows(self, blanks = False):
        files = self.get_filenames(self.localpath, ["html","HTML"])
        dirs = self.get_dirnames(self.localpath)
        #print "AfpSlideShowGenerator.get_actuel_shows 1:", files, dirs
        names = []
        for file in files:
            #print "AfpSlideShowGenerator.get_actuel_shows 2:", file[:-5], dirs, file[:-5] in dirs
            if file[:-5] in dirs:
                name = file.split(self.pathdelimiter)[-1]
                if blanks: name = name.replace("_"," ")
                names.append(name[:-5])
        return names
    ## get name of file where thumbs of slideshows are shown
    def get_index_filename(self):
        pathlst = self.localpath.split(self.pathdelimiter)
        if pathlst[-1] == "": pathlst = pathlst[:-1]
        rellst = self.localindex.split(self.pathdelimiter)
        for rel in rellst:
            if rel == "..": 
                pathlst = pathlst[:-1]
            elif rel != ".":
                pathlst.append(rel)
        return self.pathdelimiter.join(pathlst)
    ## get image filenames from directory
    # @param dir - if given, directory where images are found
    # @param ext - if given, list of file extensions to be used, defaut: image file extensions
    def get_filenames(self, dir=None, ext=None):
        if dir is None:
            dir = self.localpath + self.localname + self.pathdelimiter
        if not dir[-1] == self.pathdelimiter: dir += self.pathdelimiter
        if ext is None:
            ext = ['png', 'PNG', 'jpg', 'JPG', 'gif', 'GIF']    # Add image formats here
        files = Afp_getFilenames(dir, ext)
        if self.debug: print("AfpSlideShowGenerator.get_filenames:", dir, files)
        #print "AfpSlideShowGenerator.get_filenames:", dir, files
        return files
    ## get directorynames from directory
    # @param dir - if given, directory where directries should be searched
    def get_dirnames(self, dir=None):
        if dir is None:
            dir = self.localpath + self.localname + self.pathdelimiter
        subdirs = Afp_getDirnames(dir, self.pathdelimiter)
        if self.debug: print("AfpSlideShowGenerator.get_dirnames:", dir, subdirs)
        return subdirs
    ## secure old files of a given filename
    # @param fname - nameof the file to be secured
    def secure_file(self, fname):
        if Afp_existsFile(fname):
            oldname = fname
            newname = fname
            ext = "." + fname.split(".")[-1]
            oldname = fname[:-len(ext)]
            cnt = 0
            while Afp_existsFile(newname):
                cnt += 1
                newname = oldname + "_" + Afp_toIntString(cnt) + ext
            #print "AfpSlideShowGenerator.secure_file:", fname, "->", newname
            Afp_copyFile(fname, newname)    
        
    ## insert a value into alist at given index
    # @param index - index of path in self.show_pathes
    # @param small - flag if path should point into 'small' directory
    def relativ_index_path(self, index):
        path = "slides" + self.pathdelimiter + self.relativ_show_path(index, True)
        pathlst = self.localpath.split(self.pathdelimiter)
        if pathlst[-1] == "": pathlst = pathlst[:-1]
        rellst = self.localindex.split(self.pathdelimiter)
        for rel in rellst:
            if rel == "..": 
                path = pathlst.pop(-1) + self.pathdelimiter + path
        return path
    ## insert a value into alist at given index
    # @param index - index of path in self.show_pathes
    # @param small - flag if path should point into 'small' directory
    def relativ_show_path(self, index, small = False):
        ind = self.get_image_index(index)
        name = self.show_pathes[ind].split(self.pathdelimiter)[-1]
        sdir = ""
        if small: 
            sdir = "small" + self.pathdelimiter
            name = name.split(".")[0] + ".png"
        path = self.localname + self.pathdelimiter + sdir + name
        return path
    ## insert a value into alist at given index
    # @param index - index where value has to be inserted, original vlaue will be shifted to index+1
    # @param value - value to be inserted
    def insert_into_list(self, liste, index, value):
        if index < 0 or index > len(liste)-1:
            liste.append(value)
        else:
            liste.append(liste[-1])
            #print "AfpSlideShowGenerator.insert_into_list  in:", liste, index, value
            lgh = len(liste) - 3
            if lgh > index:
                for i in range(lgh,index-1,-1):
                    #print "AfpSlideShowGenerator.insert_into_list i:", i, i+1
                    liste[i+1] = liste[i]
            liste[index] = value
            #print "AfpSlideShowGenerator.insert_into_list out:", liste, index, value
        return liste
            
    ## store images to filesystem
    def store_show_images(self):
        locdir = self.localpath
        if not locdir[-1] == self.pathdelimiter: locdir += self.pathdelimiter
        dirs = self.get_dirnames(locdir)
        # look for slideshow directory
        gen = True
        for dir in dirs:
            if dir.split(self.pathdelimiter)[-1] == self.localname: gen = False
        #print "AfpSlideShowGenerator.store_show_images:", self.localname, dirs, gen 
        if gen:
            Afp_genDir(self.localpath + self.localname)
        locdir = self.localpath + self.localname + self.pathdelimiter 
        #print "AfpSlideShowGenerator.store_show_images locdir:", locdir
        dirs = self.get_dirnames(locdir)
        #look for thumbnail directory
        gen = True
        for dir in dirs:
            if dir.split(self.pathdelimiter)[-1] == "small": gen = False
        #print "AfpSlideShowGenerator.store_show_images small:", dirs, gen 
        if gen:
            Afp_genDir(locdir + "small")
        files = self.get_filenames()
        for i in range(len(self.show_pathes)):
            file = self.show_pathes[i]
            name = file.split(self.pathdelimiter)[-1]
            ext = "." + name.split(".")[-1]
            # write files
            if not file in files:
                to_file = locdir + name
                #print "AfpSlideShowGenerator.store_show_images copy file:",file, "->", to_file
                Afp_copyFile(file, to_file)
            to_file = locdir + "small" + self.pathdelimiter + name[:-len(ext)] + ".png"
            # write thumbnails
            if not Afp_existsFile(to_file):
                bit = self.show_list.GetBitmap(i)
                img = wx.ImageFromBitmap(bit)
                #print "AfpSlideShowGenerator.store_show_images write thumb:", i, "->", to_file
                img.SaveFile(to_file, wx.BITMAP_TYPE_PNG)
                
    ## generate html output index file with the list of available slideshows
    def generate_index_html(self):
        # write html file
        fname = self.get_index_filename() 
        fin = Afp_readLinesFromFile(fname)
        floop = open(self.index_template, "r")
        tmpfile = io.StringIO()
        ShowDir = self.get_localname()
        ShowName = self.get_localname(True)
        showstring = "show-" + self.get_localname()
        is_new = True
        for line in fin:
            if showstring in line:
                is_new = False
                break
        Path = self.relativ_index_path(0)
        skip = False
        for zeile in fin:
            if self.serial_index_tags[0] in zeile:
                show = zeile.split(self.serial_index_tags[0])[1]
                if "\">" in show: show = show.split("\">")[0]
                #print "AfpSlideShowGenerator.generate_index_html show:", show, self.get_localname(), is_new
                if show == self.get_localname() or (show != "Homepage" and is_new):
                    if show == self.get_localname(): 
                        skip = True
                    else:
                        is_new = False
                    looping = False
                    for line in floop:
                        if self.serial_index_tags[2] in line:
                            #tmpfile.write(line) # don't write loop tags
                            loop = []
                            looping = True
                        elif looping:
                            if self.serial_index_tags[3] in line:
                                looping = False
                                Anzahl = self.get_image_len()
                                #print "AfpSlideShowGenerator.generate_index_html stop:",looping, loop, 
                                if self.max_thumbs_per_line and Anzahl > self.max_thumbs_per_line:   
                                    step = float(Anzahl)/self.max_thumbs_per_line
                                else: 
                                    step = 1
                                value = step
                                for i in range(1, Anzahl):
                                    if i > 1 and i != int(value) and i < Anzahl-1: continue # assure only designated number of thumbs in a line
                                    value += step
                                    Path = self.relativ_index_path(i)
                                    for lop in loop:
                                        if "[i]" in lop:
                                            lop = lop.replace("[i]", Afp_toString(i+1))
                                        if "[Path]" in lop:
                                            lop = lop.replace("[Path]", Afp_toString(Path))
                                        if "[ShowDir]" in lop:
                                            lop = lop.replace("[ShowDir]", ShowDir)
                                        tmpfile.write(lop)  
                                #tmpfile.write(line) # don't write loop tags
                            else:
                                loop.append(line)
                        else:
                            if "[ShowDir]" in line: line = line.replace("[ShowDir]", ShowDir)
                            if "[ShowName]" in line: line = line.replace("[ShowName]", ShowName)
                            if "[Path]" in line: line = line.replace("[Path]", Path)
                            tmpfile.write(line)
                            #print "AfpSlideShowGenerator.generate_index_html outside:", line[:-1]
                    if not skip: tmpfile.write(zeile) # write entry line, if part should not be skipped
                else:
                    tmpfile.write(zeile)            
            else:
                if  skip:
                    #print "AfpSlideShowGenerator.generate_index_html skipped:", zeile[:-1]
                    if self.serial_index_tags[1] in zeile: skip = False
                else:
                    tmpfile.write(zeile)
        floop.close()
        #print "AfpSlideShowGenerator.generate_index_html tmpfile:", tmpfile, tmpfile.getvalue()
        self.secure_file(fname) # secure previous generated files
        #fname = fname[:-5] + "_akn.html"
        fout = open(fname, 'w') 
        fout.write(tmpfile.getvalue())
        fout.close()

    ## generate slideshow html output file
    def generate_slide_html(self):
        fname = self.localpath + self.localname + ".html"
        self.secure_file(fname) # secure previous generated files
        #print "AfpSlideShowGenerator.generate_slide_html files:", fname, self.slide_template
        #print "AfpSlideShowGenerator.generate_slide_html input:",  self.show_pathes, self.show_index, self.show_texts
        fin = open(self.slide_template, "r")
        fout = open(fname, "w")
        looping = False
        loop = []
        for line in fin:
            #print "AfpSlideShowGenerator.generate_slide_html:", line[:-1], looping, loop
            if self.serial_show_tags[0] in line or self.serial_show_tags[2] in line:
                loop = []
                looping = True
            if looping:
                if self.serial_show_tags[1] in line or self.serial_show_tags[3] in line: 
                    loop.append(line)
                    looping = False
                    Anzahl = self.get_image_len()
                    #print "AfpSlideShowGenerator.generate_slide_html stop:",looping, loop, self.show_pathes, self.show_index, self.show_texts
                    for i in range(Anzahl):
                        Path = self.relativ_show_path(i)
                        Text = Afp_toHtml(self.get_image_text(i))
                        # copy image to targetdiretory and to smalldiretory
                        for lop in loop:
                            if "[i]" in lop:
                                lop = lop.replace("[i]", Afp_toString(i+1))
                            if "[Anzahl]" in lop:
                                lop = lop.replace("[Anzahl]", Afp_toString(Anzahl))
                            if "[Path]" in lop:
                                lop = lop.replace("[Path]", Afp_toString(Path))
                            if "[Text]" in lop:
                                lop = lop.replace("[Text]", Text)
                            fout.write(lop) 
                            #print "AfpSlideShowGenerator.generate_slide_html loop:", lop[:-1]
                else:
                    loop.append(line)
            else:
                if "[BGCOLOR]" in line: line = line.replace("[BGCOLOR]", self.get_bgColor())
                if "[BACKGROUND]" in line: line = line.replace("[BACKGROUND]", self.get_background())
                fout.write(line) 
                #print "AfpSlideShowGenerator.generate_slide_html:", line[:-1]
        fout.close()
        fin.close()
        
    ## save images to disk and write appropriate file
    def save_slideshow(self):
        self.store_show_images()
        self.generate_slide_html()
        self.generate_index_html()
    ## publish slideshow data on ftp-server
    def publish_slideshow(self):
        if self.ftpcon:
            if not self.ftpcon.is_connected():
                self.ftpcon.invoke_ftp()
            print("AfpSlideShowGenerator.publish_slideshow:", self.localname, self.localindex)
            self.ftpcon.send_ftp_dir(self.localname)
            self.ftpcon.send_ftp_file(self.localname + ".html")
            self.ftpcon.send_ftp_file(self.localindex)
    ## download slideshow data on ftp-server
    def get_slideshow(self):
        if self.ftpcon:
            if not self.ftpcon.is_connected():
                self.ftpcon.invoke_ftp()
            self.ftpcon.get_ftp_dir(self.localname)
            self.ftpcon.get_ftp_file(self.localname + ".html")
            self.ftpcon.get_ftp_file(self.localindex)
    ## download all slideshow data from ftp-server
    def get_all_slideshows(self):
        if self.ftpcon:
            if not self.ftpcon.is_connected():
                self.ftpcon.invoke_ftp()
            self.ftpcon.get_ftp_dir(None)
            self.set_locrem()
            
## class to handle internet pages showing dates from a singe javascript file
class AfpCalendarEntries(object):
    ## initialize AfpCalendarEntries generator class
    # @param ftpcon - AfpFTPConnector to be used for download and upload
    # @param type - type to identify the used files
    # @param config - path and name of configuration file
    # @param debug - if given, debug-flag
    def  __init__(self, ftpcon, type, config, debug = False):
        self.ftpcon = ftpcon
        self.type = type
        self.name = None
        self.debug = debug
        self.data_separator = "|"
        self.pathdelimiter = Afp_getGlobalVar("path-delimiter")        
        if config:
            self.localdir = Afp_getToLastChar(config, self.pathdelimiter)
        else:
            self.localdir = Afp_pathname(Afp_genHomeDir(), self.pathdelimiter)  
            config = self.localdir + "AfpInternetUpdater.cfg"
        self.templatefile = self.localdir + "AfpInternetCalendarEntries.template"
        self.entries = {}
        self.localroot = None
        self.localpath = None
        self.localname = None
        self.remotepath = None
        self.remotename = None
        self.settings = {}    
        self.settings = Afp_loadSettings(config, "cal,local", self.debug)
        if "local-root" in self.settings: 
            self.localroot = Afp_pathname(self.settings["local-root"], self.pathdelimiter)
            self.localdir = self.localroot
        if "local-clientname" in self.settings: 
            self.name = self.settings["local-clientname"]
        #if self.ftpcon:
            #self.ftpcon.invoke_ftp() 
        self.set_locrem()
        self.load()
        if self.debug: print("AfpCalendarEntries Konstruktor") 

     ## destructor
    def __del__(self):   
        if self.debug: print("AfpCalendarEntries Destruktor") 
        
## set local and remote filenames from settings entry
    def set_locrem(self):
        if "cal-" + self.type in self.settings:
            names = self.settings["cal-" + self.type]
            split = names.split(",")
            local = split[0]
            remote = None
            if len(split) > 1:
                remote = split[1]
            if remote is None: remote = local
            if Afp_isRootpath(local):
                localfile = Afp_pathname(dir, self.pathdelimiter, True)
            else:
                local = Afp_addRootpath(self.localroot, local)
                localfile = Afp_pathname(local, self.pathdelimiter, True)
            lsplit = localfile.split(self.pathdelimiter)
            self.localpath = self.pathdelimiter.join(lsplit[:-1]) + self.pathdelimiter
            self.localname = lsplit[-1]
            remotefile = Afp_pathname(remote, "/", True)
            rsplit = remotefile.split("/")
            self.remotepath = "/".join(rsplit[:-1]) + "/"
            self.remotename = rsplit[-1]
            if self.ftpcon:
                self.ftpcon.set_remotedir(self.remotepath)
                self.ftpcon.set_localdir(self.localpath)
        if self.debug: print("AfpCalendarEntries.set_locrem  local:" , self.localpath, self.localname, "remote:", self.remotepath, self.remotename)
    
    ## check if line is a date-line
    # @param line - line to be checked
    def is_date(self, line):
        if self.data_separator in line: return True
        return False
        
    ## retrieve type of events
    def get_type(self):
        return self.type
   ## retrieve name of client
    def get_name(self):
        return self.name
    ## get ftp-handler
    def get_ftp(self):
        return self.ftpcon
    ## get globals
    # needed to set up dialogs
    def get_globals(self):
        return None
    ## extrat date values from line
    # @param line - line where data should be extracted
    def get_date(self, line):
        words = line.split("\"")
        if len(words) > 1:
            if self.data_separator in words[1]:
                split = words[1].split(self.data_separator)
                datum = Afp_fromString(split[0])
                text = Afp_fromHtml(split[1])
                return datum, text
        return None, None
        
    ## get event rows to populate grid
    def get_events(self):
        #print "AfpCalendarEntries.get_events entries:" , len(self.entries), self.entries
        #print "AfpCalendarEntries.get_events keys:" ,self.entries.keys()
        rows = []
        for entry in sorted(self.entries.keys()):
            rows.append([Afp_toString(entry), Afp_toString(self.entries[entry])])
        return rows
    ## retrieve remote file
    def get_remote_file(self):
        if self.ftpcon:
            if not self.ftpcon.is_connected():
                self.ftpcon.invoke_ftp()
            self.ftpcon.get_ftp_file(self.remotename, self.localname)
    ## publish local file
    def publish_local_file(self):
        if self.ftpcon:
            if not self.ftpcon.is_connected():
                self.ftpcon.invoke_ftp()
            self.ftpcon.send_ftp_file( self.localname, self.remotename)
    
    ## set and add date to entries
    # @param datum - date of calendar entry
    # @param text - text for calendar entry
    def set_date(self, datum, text):
        if self.debug: print("AfpCalendarEntries.set_date:", datum, text)
        self.entries[datum] = text
    ## delete date from entries
    # @param datum - date of calendar entry
    def del_date(self, datum):
        if self.debug: print("AfpCalendarEntries.del_date:", datum)
        self.entries.pop(datum)
    ## clear all entries
    # @param datum - date of calendar entry
    def clear(self):
        if self.debug: print("AfpCalendarEntries.clear")
        self.entries = {}
    ## load entries from local file
    # @param fname - if given, name of file to be opend
    def load(self, fname=None):
        if fname is None: 
            fname = self.localpath + self.localname
        #print "AfpCalendarEntries.load:", fname
        fin = open(fname, "r")
        self.clear()
        for line in fin:
            if self.is_date(line):
                datum, text = self.get_date(line)
                #print "AfpCalendarEntries.load:", datum, text, line[:-1]
                if datum:
                    self.entries[datum] = text
        fin.close()
                    
    ## write entries to local file
    # @param fname - if given, name of file to be written
    def write(self, fname=None):
        if fname is None: 
            fname = self.localpath + self.localname
        fin = open(self.templatefile, "r")
        fout = open(fname, "w")
        for line in fin:
            if "[Name]" in line:
                line = line.replace("[Name]", Afp_toString(self.type))
            if "[Anzahl]" in line:
                line = line.replace("[Anzahl]", Afp_toString(len(self.entries)-1))
            if "[i]" in line and "[Datum]" and "[Text]" in line:
                cnt = 0
                for entry in sorted(self.entries.keys()):
                    local = line.replace("[i]", Afp_toString(cnt))
                    local = local.replace("[Datum]", Afp_toDateString(entry, "dd.mm.yyyy"))
                    local = local.replace("[Text]", Afp_toHtml(Afp_toString(self.entries[entry])))
                    fout.write(local)  
                    #print "AfpCalendarEntries.write loop:", local[:-1]
                    cnt += 1
            else:
                fout.write(line) 
                #print "AfpCalendarEntries.write:", line[:-1]
        fout.close()
        fin.close()
    
            
## class to handle FTP connection and interactions
class AfpFTPConnector(object):
    ## initialize AfpFTPConnector class
    # @param config - path and name of configuration file
    # @param debug - if given, debug flag
    # @param server - if given, server name or IP
    # @param port - if given, server port, default: 21
    def  __init__(self, config, debug=False, server=None, port = None):
        self.debug = debug
        self.FTP = ftplib.FTP()
        self.connected = False
        self.server = server
        self.server_port = 21
        if port: self.server_port = port
        #self.server_port = 990 #for ftps
        self.pathdelimiter = Afp_getGlobalVar("path-delimiter")
        self.localdir = Afp_pathname(Afp_genHomeDir(), self.pathdelimiter)
        if config is None: config = self.localdir + "AfpInternetUpdater.cfg"
        self.settings = Afp_loadSettings(config, "ftp,local", self.debug)
        if self.server is None and "ftp-server" in self.settings:
            self.server = self.settings["ftp-server"]
        if "local-root" in self.settings: 
            self.localroot = Afp_pathname(self.settings["local-root"], self.pathdelimiter)
            self.localdir = self.localroot
        self.remotedir = None
    # possible  ftp-commands:
    # dir() - ls
    # nlst() - ls, python list as output
    # mkd(name) - make directory 'name'
    # cwd(name) - change actuel directory to 'name'
    # rmd(name) - remove directory 'name'
    # delete(name) - delete file 'name'
    # rename(name1, name2) - rename file 'name1' to 'name2'
    ## destructor
    def __del__(self):  
        res = None
        if self.connected: 
            res = self.FTP.close() 
        if self.debug: print("AfpFTPConnector Destruktor, send 'close' to ftp connection:", res)
            
    ## check if FTP-connection is established
    def is_connected(self):
        return self.connected
    ## set remote directory name
    #@param dir - new directory path
    def set_remotedir(self, dir):
        if dir and not dir[0] == "/": dir = "/" + dir
        self.remotedir = dir
        if self.debug: print("AfpFTPConnector.set_remotedir:", self.remotedir)
    ## set local directory
    #@param dir - if given, new directory path, otherwise localroot is returned
    def set_localdir(self, dir=None):
        if dir and Afp_isRootpath(dir):
            self.localdir = Afp_pathname(dir, self.pathdelimiter)
        else: 
            dir = Afp_addRootpath(self.localroot, dir)
            self.localdir = Afp_pathname(dir, self.pathdelimiter)
        if self.debug: print("AfpFTPConnector.set_localdir:", self.localdir)
     ## completes local filename
    def complete_filename(self, name):
        fname = name
        if not Afp_isRootpath(name):
            fname = Afp_addRootpath(self.localdir, name)
        return Afp_pathname(fname, self.pathdelimiter, True)
    ## extract filename from path    
    # @param path - complete filepath where name should be extracted   
    def ext_from_path(self, path):
        split = path.split(self.pathdelimiter)
        return split[-1]
    
    ## invoke ftp connection
    # @param user - ftp-user for login on remote site    
    # @param word - password for ftp-user (encoded)  
    def invoke_ftp(self, user=None, word=None):
        if user is None and "ftp-user" in self.settings:
            user = self.settings["ftp-user"]
        if word is None and "ftp-word" in self.settings:
            word = base64.b64decode(self.settings["ftp-word"].encode("ascii"))
        if self.FTP and  user and word:
            r1 = self.FTP.connect(self.server, self.server_port)
            r2 = self.FTP.login(user,base64.b64decode(word).decode("UTF-8"))
            self.connected = True
            if self.remotedir:
                self.FTP.cwd(self.remotedir)
            if self.debug: 
                print("AfpFTPConnector.invoke_ftp: FTP connection established to server", self.server, "on port", self.server_port, "Return value:", r1)
                print("AfpFTPConnector.invoke_ftp: FTP user logged in", user, "Return value:", r2)
                
   ## check if a directory exists, check is performed in 'remotedir'
    # @ param name - name of directory to be checked
    def dir_exists(self, name):
        exists = False
        if self.connected:
            if name in self.FTP.nlst():
                exists = True
        if self.debug: print("AfpFTPConnector.dir_exists:", name, exists)
        return exists
    ## change directory on remote site
    # @param path - path to which current remote directory has to be changed to
    def chdir(self, path):
        res = None
        if self.connected: 
            res = self.FTP.cwd(path)
        if self.debug: 
            print("AfpFTPConnector.chdir:", path, "Return value:", res, "Actuel path:", self.actdir())
    ## create a directory on remote site
    # @param name - name of directory to be created
    def mkdir(self, name):
        res = None
        if self.connected: 
            res = self.FTP.mkd(name)
        if self.debug: 
            print("AfpFTPConnector.mkdir:", name, "Return value:", res)
    ## show actuel directory on remote site
    def actdir(self):
        if self.connected:
            return self.FTP.pwd()
        else:
            return None
        
    ## get file via ftp from server
    # @param remote - name of file to be retrieved
    # @param local - if given, name file is retrieved to, default: filename of 'remote' path, file will be written into 'localdir'
    def get_ftp_file(self, remote, local = None):        
        if self.debug: print("AfpFTPConnector.get_ftp_file:", remote, "to", local)
        if local is None: local = Afp_addRootpath(self.localdir, self.ext_from_path(remote))
        local = self.complete_filename(local)
        if self.connected: 
            print("FTP get: invoking tranfer of", remote, "to", local)
            fout = open(local,"wb")
            self.FTP.retrbinary('RETR '+ remote, fout.write)
            fout.close()
            print("FTP get: transfer of", remote, "to", local, "completed")
    ## upload file onto server
    # remote directory has to be set to the position, where file should be written
    # @param local - local name of file to be send
    # @param remote - if given name of file on remote site, default: filename of 'local' path
    def send_ftp_file(self, local, remote = None):
        if self.debug: print("AfpFTPConnector.send_ftp_file:", local, "to", remote)
        local = self.complete_filename(local)
        if remote is None: remote = self.ext_from_path(local)
        if self.connected and Afp_existsFile(local):
            print("FTP send: invoking tranfer of", local, "to", remote)
            fin = open(local, "rb") 
            self.FTP.storbinary('STOR ' + remote, fin)
            fin.close()
            print("FTP send: transfer of", local, "to", remote, "completed")
    ## download complete directory from the server
    # lokal directory has to be set to parent directory, if copied directory does not exist locally, it will be created
    # @param remote - name of directory on remote site, if == None: actuel directory
    # @param local - if given, local name of directory to be downloaded, default: name of remote directory, res. actuel directory
    def get_ftp_dir(self, remote, local = None):
        if self.debug: print("AfpFTPConnector.get_ftp_dir:", remote, "to", local)
        olddir = None
        if remote:
            if local is None: local = remote
            olddir = self.localdir
            locdir = self.complete_filename(local)
            #if Afp_existsFile(local) and self.connected:
            if not Afp_existsFile(locdir):
                Afp_genDir(locdir)
            self.set_localdir(locdir)
            self.chdir(remote)
        ls = []
        if self.connected:
            ls = self.FTP.nlst()
        #print "AfpFTPConnector.get_ftp_dir files:", ls
        for fname in ls:
            if fname[0] == ".": continue 
            if not "." in fname: continue # skip directories
            self.get_ftp_file(fname)
        # recursive for all directories
        for dir in ls:
            if "." in dir: continue # skip files
            dname = self.ext_from_path(dir)
            self.get_ftp_dir(dname)
        if olddir: self.set_localdir(olddir)
        if remote and remote[0] == "/":
            self.chdir(self.remotedir)
        else:
            self.chdir("..")
            if remote:
                for char in remote:
                    if char == "/":  self.chdir("..")
    ## upload complete directory onto the server
    # remote directory has to be set to parent directory, if copied directory does not exist on server, it will be created
    # @param local - local name of directory to be send
    # @param remote - if given name of file on remote site, default: filename of 'local' path
    def send_ftp_dir(self, local, remote = None):
        if self.debug: print("AfpFTPConnector.send_ftp_dir:", local, "to", remote)
        if remote is None: remote = local
        local = self.complete_filename(local)
        #if Afp_existsFile(local) and self.connected:
        if Afp_existsFile(local):
            locdir = self.localdir
            self.set_localdir(local)
            if not self.dir_exists(remote):
                self.mkdir(remote)
            self.chdir(remote)
            ls = Afp_readFileNames(self.localdir) 
            #print "AfpFTPConnector.send_ftp_dir files:", ls
            for fname in ls:
                lname = Afp_pathname(fname, self.pathdelimiter, True)
                rname = self.ext_from_path(fname)
                if not "." in rname: continue
                self.send_ftp_file(lname, rname)
            # recursive for all directories
            lsd = Afp_getDirnames(self.localdir)
            #print "AfpFTPConnector.send_ftp_dir dirs:", lsd
            for dir in lsd:
                dname = self.ext_from_path(dir)
                if "." in dname: continue
                self.set_localdir(local)
                self.send_ftp_dir(dname)
            self.set_localdir(locdir)
            if remote[0] == "/":
                self.chdir(self.remotedir)
            else:
                self.chdir("..")
                for char in remote:
                    if char == "/":  self.chdir("..")
    ## leave actuel ftp-session
    def quit(self):
        res = None
        if self.connected: 
            res = self.FTP.quit()
            self.connected = False
        if self.debug: print("AfpFTPConnector.quit: send 'quit' to ftp connection:", res)


## Dialog to handle calendar entries \n
class AfpDialog_calEvents(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):   
        self.cols = 2
        self.rows = 10
        self.filled_rows = 0
        AfpDialog.__init__(self,None, -1, "")
        self.grid_ident = None
        self.col_percents = [15, 85]
        self.col_labels = ["Datum","Text"]
        self.grid_row_selected = None
        #self.xml_background = wx.Colour(255,255,255)
        self.xml_background = wx.Colour(192, 220, 192)
        self.fixed_width = 80
        self.fixed_height = 80
        self.SetSize((574,410))
        self.SetTitle("Termineinträge")
        self.Bind(wx.EVT_SIZE, self.On_ReSize)
        #self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
        
    ## set up dialog widgets      
    def InitWx(self):
        self.label_Label = wx.StaticText(self, 1, label="Verwaltung der Termineinträge für", name="LLabel")
        self.label_Name = wx.StaticText(self, 1, label="", name="Name")
        self.top_line1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line1_sizer.Add(self.label_Label,0,wx.EXPAND)
        self.top_line1_sizer.AddSpacer(5)
        self.top_line1_sizer.Add(self.label_Name,0,wx.EXPAND)
         
        self.button_Datum = wx.Button(self, -1, label="&Datum:", name="BDatum")
        self.Bind(wx.EVT_BUTTON, self.On_Datum, self.button_Datum)
        self.text_Datum =  wx.TextCtrl(self, -1, value="", style=0, name="Datum")
        self.text_Datum.Bind(wx.EVT_KILL_FOCUS, self.On_ChDatum)
        self.label_Text = wx.StaticText(self, 1, label="Text:", name="LText")
        self.text_Text =  wx.TextCtrl(self, -1, value="", style=0, name="Text")
        self.check_fix = wx.CheckBox(self, -1, label="", name="Fix")
        self.top_line2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line2_sizer.Add(self.button_Datum,0,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(5)
        self.top_line2_sizer.Add(self.text_Datum,2,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(10)
        self.top_line2_sizer.Add(self.label_Text,0,wx.EXPAND)
        self.top_line2_sizer.Add(self.text_Text,8,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(20)
        self.top_line2_sizer.Add(self.check_fix,0,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(30)
          
        self.top_text_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_text_sizer.Add(self.top_line1_sizer,0,wx.EXPAND)
        self.top_text_sizer.AddSpacer(10)
        self.top_text_sizer.Add(self.top_line2_sizer,0,wx.EXPAND)
        self.top_text_sizer.AddSpacer(10)
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_sizer.AddSpacer(10)
        self.top_sizer.Add(self.top_text_sizer,1,wx.EXPAND)
        
        self.button_Minus = wx.Button(self, -1, label="&-", size=(50,50), name="Minus")
        self.Bind(wx.EVT_BUTTON, self.On_delete, self.button_Minus)
        self.button_Plus = wx.Button(self, -1, label="&+", size=(50,50), name="Plus")
        self.Bind(wx.EVT_BUTTON, self.On_add, self.button_Plus)
        self.sizer_box = wx.StaticBox(self, label="Events", size=(60, 212))
        self.right_sizer = wx.StaticBoxSizer(self.sizer_box, wx.VERTICAL)
        self.right_sizer.AddStretchSpacer(2)      
        self.right_sizer.Add(self.button_Minus,0,wx.EXPAND)        
        self.right_sizer.AddStretchSpacer(1) 
        self.right_sizer.Add(self.button_Plus,0,wx.EXPAND)               
        self.right_sizer.AddStretchSpacer(2) 
        
        self.grid_events = wx.grid.Grid(self, -1, style=wx.FULL_REPAINT_ON_RESIZE, name="Mandate")
        self.gridmap.append("Events")
        self.grid_events.CreateGrid(self.rows, self.cols)
        self.grid_events.SetRowLabelSize(0)
        self.grid_events.SetColLabelSize(18)
        self.grid_events.EnableEditing(0)
        #self.grid_events.EnableDragColSize(0)
        self.grid_events.EnableDragRowSize(0)
        self.grid_events.EnableDragGridSize(0)
        self.grid_events.SetSelectionMode(wx.grid.Grid.GridSelectRows)   
        self.grid_events.SetColLabelValue(0, "Datum")
        self.grid_events.SetColLabelValue(1, "Text")
        for row in range(self.rows):
            for col in range(self.cols):
                self.grid_events.SetReadOnly(row, col)
        self.Bind(wx.grid.EVT_GRID_CMD_CELL_LEFT_DCLICK, self.On_DClick, self.grid_events)
        #self.Bind(wx.grid.EVT_GRID_CMD_CELL_RIGHT_CLICK, self.On_RClick, self.grid_events)

        self.left_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_sizer.Add(self.grid_events,1,wx.EXPAND)        
        
        self.button_Get = wx.Button(self, -1, label="&Holen", name="BGet")
        self.Bind(wx.EVT_BUTTON, self.On_Get, self.button_Get)
        self.button_Load = wx.Button(self, -1, label="&Laden", name="BLoad")
        self.Bind(wx.EVT_BUTTON, self.On_Load, self.button_Load)
        self.button_Save = wx.Button(self, -1, label="S&peichern", name="BSave")
        self.Bind(wx.EVT_BUTTON, self.On_Save, self.button_Save)
        self.button_Send = wx.Button(self, -1, label="&Senden", name="BSend")
        self.Bind(wx.EVT_BUTTON, self.On_Send, self.button_Send)
        self.button_End= wx.Button(self, -1, label="Be&enden", name="BEnd")
        self.Bind(wx.EVT_BUTTON, self.On_End, self.button_End)
        self.lower_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_Get,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_Load,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_Save,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_Send,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_End,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
       
        # compose sizers
        self.mid_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.mid_sizer.AddSpacer(10)
        self.mid_sizer.Add(self.left_sizer,1,wx.EXPAND)        
        self.mid_sizer.AddSpacer(10)
        self.mid_sizer.Add(self.right_sizer,0,wx.EXPAND)
        self.mid_sizer.AddSpacer(10)
        self.sizer = wx.BoxSizer(wx.VERTICAL)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.top_sizer,0,wx.EXPAND)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.mid_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.lower_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    ## attaches data to this dialog, invokes population of widgets
    # overwritten from AfpDialog
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        super(AfpDialog_calEvents, self).attach_data(data, new, True)
        self.SetTitle(data.get_type())
        self.label_Name.SetLabel(data.get_name())
        if self.data.get_ftp() is None:
            self.button_Get.Enable(False)
            self.button_Send.Enable(False)
        #else:
            #self.button_Get.SetBackgroundColour(wx.Colour(192, 220, 192))
            #self.button_Send.SetBackgroundColour(wx.Colour(192, 220, 192))
        self.Pop_Events()
        
    ## population routine for events grids \n
    def Pop_Events(self):
        rows = self.data.get_events()
        lgh = len(rows)
        self.adjust_grid_rows(lgh)
        self.rows = lgh
        self.filled_rows = lgh
        for row in range(self.rows):
            for col in range(self.cols): 
                if row < lgh:
                    self.grid_events.SetCellValue(row, col,  Afp_toString(rows[row][col]))
                else:
                    self.grid_events.SetCellValue(row, col,  "")
        
    ## adjust grid rows and columns for dynamic resize of window  
    # @param new_rows - new number of rows needed    
    def adjust_grid_rows(self, new_rows = None):
        if not new_rows: new_rows = self.rows
        #print "AfpDialog_SEPA.adjust_grid_rows:", new_rows
        self.grid_resize(self.grid_events, new_rows)
        if self.col_percents:
            grid_width = self.GetSize()[0] - self.fixed_width
            for col in range(self.cols):  
                self.grid_events.SetColLabelValue(col, self.col_labels[col])
                if col < len(self.col_percents):
                    self.grid_events.SetColSize(col, int(self.col_percents[col]*grid_width/100))
    ## deselect all selected grid rows
    def grid_deselect(self):
        indices = self.grid_events.GetSelectedRows()
        if indices:
            for ind in indices:
                self.grid_events.DeselectRow(ind)
    
    ## event handler for resizing window
    def On_ReSize(self, event):
        height = self.GetSize()[1] - self.fixed_height
        new_rows = int(height/self.grid_events.GetDefaultRowSize())
        if new_rows >= self.filled_rows:
            self.adjust_grid_rows(new_rows)
        event.Skip()   
    
    ## Event handler for changing of date
    def On_ChDatum(self, event):
        if self.debug: print("AfpDialog_calEvents Event handler `On_ChDatum'")
        datum = self.text_Datum.GetValue()
        datum = Afp_ChDatum(datum)
        self.text_Datum.SetValue(datum)
        
   ## Event handler for calendar dialog
    def On_Datum(self, event):
        if self.debug: print("AfpDialog_calEvents Event handler `On_Datum'")
        x, y = self.button_Datum.ScreenPosition
        datum = self.text_Datum.GetValue()
        dates = AfpReq_Calendar((x, y), datum)
        if dates:
            self.text_Datum.SetValue(dates[0])
        event.Skip()
        
   ## Event handler for double click on grid
    def On_DClick(self, event):
        if self.debug: print("AfpDialog_calEvents Event handler `On_DClick'")        
        indices = self.grid_events.GetSelectedRows()
        if indices:
            ind = indices[0]
            datum = self.grid_events.GetCellValue(ind, 0)
            text = self.grid_events.GetCellValue(ind, 1)
            self.text_Datum.SetValue(datum)
            self.text_Text.SetValue(text)
            self.grid_deselect()
        event.Skip()

    ## Event handler to add events
    def On_add(self, event):
        if self.debug: print("AfpDialog_calEvents Event handler `On_Add'")
        datum = self.text_Datum.GetValue()
        text = self.text_Text.GetValue()
        self.data.set_date(Afp_fromString(datum), text)
        if not self.check_fix.GetValue():
            self.text_Text.SetValue("")
        self.Pop_Events()
        event.Skip()
   ## Event handler to delete events
    def On_delete(self, event):
        if self.debug: print("AfpDialog_calEvents Event handler `On_delete'")
        indices = self.grid_events.GetSelectedRows()
        if indices:
            for ind in indices:
                datum = self.grid_events.GetCellValue(ind, 0)
                print("AfpDialog_calEvents.On_delete:", datum)
                self.data.del_date(Afp_fromString(datum))
            self.grid_deselect()
            self.Pop_Events()   
        else: 
            ok = AfpReq_Question("Keine Termine ausgewählt,", "soll die gesamte Liste gelöscht werden?", "Löschung")
            if ok:
                self.data.clear()
                self.Pop_Events()   
        event.Skip()

    ## Button handlers
   ## Get file from remote site and load data
    def On_Get(self, event):
        if self.debug: print("AfpDialog_calEvents Event handler `On_Get'")
        self.data.get_remote_file()
        self.data.load()
        self.Pop_Events()
        event.Skip()
   ## Load data from selected file
    def On_Load(self, event):
        if self.debug: print("AfpDialog_calEvents Event handler `On_Load'")
        dir = self.data.localpath
        #print "AfpDialog_calEvents.On_Load dir:", dir 
        filename, Ok = AfpReq_FileName(dir,"Termindatei öffnen", "*.js", True)
        if Ok:
            self.data.load(filename)
            self.Pop_Events()
        event.Skip()
   ## Save dialog entries to local file
    def On_Save(self, event):
        if self.debug: print("AfpDialog_calEvents Event handler `On_Save'")
        dir = self.data.localpath
        filename, Ok = AfpReq_FileName(dir,"Termindatei speichern", "*.js")
        if Ok:
            self.data.write(filename)
        event.Skip()
   ## Save dialog entries to local file and send file to remote site
    def On_Send(self, event):
        if self.debug: print("AfpDialog_calEvents Event handler `On_Send'")
        self.data.write()
        self.data.publish_local_file()
        event.Skip()
   ## Event handler for Quit Button
    def On_End(self, event=None):
        if self.debug: print("AfpDialog_calEvents Event handler `On_End'")
        self.execute_Quit()
        if event: event.Skip()
        self.EndModal(wx.ID_CANCEL)

## loader routine for calendar events handling  \n
# @param data - SelectionList data where holding or generation events for
def AfpLoad_calEvents(data):
    DiEv = AfpDialog_calEvents(None)
    DiEv.attach_data(data)
    DiEv.ShowModal()
    Ok = DiEv.get_Ok()
    DiEv.Destroy()
    return Ok 
    
## Dialog to generate a slideshow from directory \n
class AfpDialog_Sildeshow(AfpDialog):
    ## initialise dialog
    def __init__(self, *args, **kw):    
        AfpDialog.__init__(self,None, -1, "")
        self.SetSize((574,410))
        self.SetTitle("Slideshow")
        self.Bind(wx.EVT_SIZE, self.On_ReSize)
        #self.Bind(wx.EVT_ACTIVATE, self.On_Activate)
        
    ## set up dialog widgets      
    def InitWx(self):
        self.label_Label = wx.StaticText(self, 1, label="Erzeugung einer Slideshow für", name="LLabel")
        self.label_Name = wx.StaticText(self, 1, label="", name="Name")
        self.top_line1_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line1_sizer.Add(self.label_Label,0,wx.EXPAND)
        self.top_line1_sizer.AddSpacer(5)
        self.top_line1_sizer.Add(self.label_Name,0,wx.EXPAND)
         
        self.label_Text = wx.StaticText(self, 1, label="Maximale Anzahl der Bilder:", name="LText")
        self.text_Text =  wx.TextCtrl(self, -1, value="", style=0, name="Text")
        self.combo_Shows = wx.ComboBox(self, -1, value="", choices=[], style=wx.CB_DROPDOWN | wx.CB_READONLY, name="Shows")
        self.Bind(wx.EVT_COMBOBOX, self.On_Change, self.combo_Shows)
        self.top_line2_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_line2_sizer.AddSpacer(10)
        self.top_line2_sizer.Add(self.label_Text,0,wx.EXPAND)
        self.top_line2_sizer.Add(self.text_Text,1,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(30)
        self.top_line2_sizer.Add(self.combo_Shows,4,wx.EXPAND)
        self.top_line2_sizer.AddSpacer(10)
          
        self.top_text_sizer = wx.BoxSizer(wx.VERTICAL)
        self.top_text_sizer.Add(self.top_line1_sizer,0,wx.EXPAND)
        self.top_text_sizer.AddSpacer(10)
        self.top_text_sizer.Add(self.top_line2_sizer,0,wx.EXPAND)
        self.top_text_sizer.AddSpacer(10)
        self.top_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.top_sizer.AddSpacer(10)
        self.top_sizer.Add(self.top_text_sizer,1,wx.EXPAND)
        
        self.button_Add = wx.Button(self, -1, label="&>>", size=(50,50), name="Plus")
        self.Bind(wx.EVT_BUTTON, self.On_Add, self.button_Add)
        self.button_Minus = wx.Button(self, -1, label="&-", size=(50,50), name="Minus")
        self.Bind(wx.EVT_BUTTON, self.On_Minus, self.button_Minus)
        self.button_Plus = wx.Button(self, -1, label="&+", size=(50,50), name="Plus")
        self.Bind(wx.EVT_BUTTON, self.On_Plus, self.button_Plus)
        self.button_Delete = wx.Button(self, -1, label="&<<", size=(50,50), name="Minus")
        self.Bind(wx.EVT_BUTTON, self.On_Delete, self.button_Delete)
        self.sizer_box = wx.StaticBox(self, label="  >>> ", size=(60, 212))
        self.mid_sizer = wx.StaticBoxSizer(self.sizer_box, wx.VERTICAL)
        self.mid_sizer.AddStretchSpacer(5)      
        self.mid_sizer.Add(self.button_Add,0,wx.EXPAND)        
        self.mid_sizer.AddStretchSpacer(1) 
        self.mid_sizer.Add(self.button_Minus,0,wx.EXPAND)        
        self.mid_sizer.AddStretchSpacer(1) 
        self.mid_sizer.Add(self.button_Plus,0,wx.EXPAND)               
        self.mid_sizer.AddStretchSpacer(1) 
        self.mid_sizer.Add(self.button_Delete,0,wx.EXPAND)               
        self.mid_sizer.AddStretchSpacer(5) 

        #self.label_Source = wx.StaticText(self, 1, label="", style=wx.ST_ELLIPSIZE_START, name="LSource")        
        self.list_Source = wx.ListCtrl(self,-1 ,size=(185,398), style=wx.LC_REPORT | wx.LC_HRULES )
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.On_DClick_Source, self.list_Source)
        self.left_sizer = wx.BoxSizer(wx.VERTICAL)
        #self.left_sizer.Add(self.label_Source,0,wx.EXPAND)
        #self.left_sizer.AddSpacer(10)
        self.left_sizer.Add(self.list_Source,1,wx.EXPAND)
        
        #self.label_Show = wx.StaticText(self, 1, label="", name="LShow")        
        self.list_Show = wx.ListCtrl(self,-1 ,size=(185,398),style=wx.LC_REPORT | wx.LC_HRULES )
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.On_DClick_Show, self.list_Show)
        self.right_sizer = wx.BoxSizer(wx.VERTICAL)
        #self.right_sizer.Add(self.label_Show,0,wx.EXPAND)
        #self.right_sizer.AddSpacer(10)
        self.right_sizer.Add(self.list_Show,1,wx.EXPAND)

        self.middle_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.middle_sizer.AddSpacer(10)        
        self.middle_sizer.Add(self.left_sizer,1,wx.EXPAND)    
        self.middle_sizer.AddSpacer(10)        
        self.middle_sizer.Add(self.mid_sizer,0,wx.EXPAND)   
        self.middle_sizer.AddSpacer(10)        
        self.middle_sizer.Add(self.right_sizer,1,wx.EXPAND)        
        self.middle_sizer.AddSpacer(10)        
        
        self.button_Get = wx.Button(self, -1, label="&Holen", name="BGet")
        self.Bind(wx.EVT_BUTTON, self.On_Get, self.button_Get)
        self.button_Load = wx.Button(self, -1, label="&Laden", name="BLoad")
        self.Bind(wx.EVT_BUTTON, self.On_Load, self.button_Load)
        self.button_Save = wx.Button(self, -1, label="S&peichern", name="BSave")
        self.Bind(wx.EVT_BUTTON, self.On_Save, self.button_Save)
        self.button_Send = wx.Button(self, -1, label="&Senden", name="BSend")
        self.Bind(wx.EVT_BUTTON, self.On_Send, self.button_Send)
        self.button_End= wx.Button(self, -1, label="Be&enden", name="BEnd")
        self.Bind(wx.EVT_BUTTON, self.On_End, self.button_End)
        self.lower_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_Get,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_Load,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_Save,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_Send,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
        self.lower_sizer.Add(self.button_End,6,wx.EXPAND) 
        self.lower_sizer.AddStretchSpacer(1) 
       
        # compose sizers
        self.sizer = wx.BoxSizer(wx.VERTICAL)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.top_sizer,0,wx.EXPAND)        
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.middle_sizer,1,wx.EXPAND)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.lower_sizer,0,wx.EXPAND)
        self.sizer.AddSpacer(10)
        
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
        self.sizer.Fit(self)

    ## attaches data to this dialog, invokes population of widgets
    # overwritten from AfpDialog
    # @param data - AfpSelectionList which holds data to be filled into dialog wodgets 
    # @param new - flag if new database entry has to be created 
    # @param editable - flag if dialogentries are editable when dialog pops up
    def attach_data(self, data, new = False, editable = False):
        super(AfpDialog_Sildeshow, self).attach_data(data, new, True)
        self.SetTitle(data.get_type())
        self.label_Name.SetLabel(data.get_name())
        self.list_Source.SetImageList(self.data.get_image_list("source"), wx.IMAGE_LIST_SMALL)
        self.list_Source.InsertColumn(0,"Quellverzeichnis",wx.LIST_FORMAT_LEFT, self.list_Source.Size[0])
        self.list_Show.SetImageList(self.data.get_image_list("show"), wx.IMAGE_LIST_SMALL)
        self.list_Show.InsertColumn(0,"Slideshow",wx.LIST_FORMAT_LEFT, self.list_Show.Size[0])
        self.fill_show_list()
        self.fill_show_combo()
        if "local-maximages" in data.settings:
            self.text_Text.SetValue(Afp_toString(self.data.settings["local-maximages"]))
        if self.data.get_ftp() is None:
            self.button_Get.Enable(False)
            self.button_Send.Enable(False)
        
    ## fill show combobox to select available sildeshow directly
    def fill_show_combo(self):
        shows = ["- Neu -"] + self.data.get_actuel_shows(True)
        if shows:
            self.combo_Shows.SetItems(shows)
            if self.data.get_localname(True) in shows:
                self.combo_Shows.SetValue(self.data.get_localname(True))
    ## fill 'source' list-control with images from a directory 
    # param dir - if given, path to directory to load
    def fill_source_list(self, dir = None):
        self.list_Source.DeleteAllItems()
        self.data.gen_source_list(dir)
        for i in range(self.data.get_image_len("source")):
            self.list_Source.InsertImageStringItem(i,self.data.get_image_text(i, "source"), self.data.get_image_index(i, "source"))
        #self.label_Source.SetLabel(Afp_toString(dir))
        #print "AfpDialog_Sildeshow.fill_source_list:",  self.list_Source,  self.list_Source.GetItemCount()
    ## fill 'show' list-control with images from a directory 
    def fill_show_list(self):
        self.list_Show.DeleteAllItems()
        self.data.gen_show_list() 
        for i in range(self.data.get_image_len("show")):
            self.list_Show.InsertImageStringItem(i,self.data.get_image_text(i, "show"), self.data.get_image_index(i, "show"))
        #self.label_Show.SetLabel(Afp_toString(dir))
        #print "AfpDialog_Sildeshow.fill_show_list:",  self.list_Show,  self.list_Show.GetItemCount()
    ## repaint modified 'show' list-control with images from a directory 
    def repaint_show_list(self):
        self.list_Show.DeleteAllItems()
        self.list_Show.SetImageList(self.data.get_image_list("show"), wx.IMAGE_LIST_SMALL)
        for i in range(self.data.get_image_len("show")):
            self.list_Show.InsertImageStringItem(i,self.data.get_image_text(i, "show"), self.data.get_image_index(i, "show"))
        #print "AfpDialog_Sildeshow.repaint_show_list:", self.list_Show.GetItemCount()
        
    ## store data to disk
    def write_data(self):
        slidename = self.data.get_localname()
        ok = self.data.has_changed()
        if ok and self.data.show_exists():
            ok = AfpReq_Question("Die Slideshow '" + slidename + "' existiert schon!", "Soll diese Slideshow überschrieben werden?", "Speichern")
            if not ok:
                pathname, ok = AfpReq_FileName(self.data.get_localpath(False),"Bitte Verzeichnis auswählen, in das gespeichert werden soll.", None)
                if ok and pathname:
                    self.data.set_localpath(pathname)
        elif not ok:
            AfpReq_Info("Die Slideshow '" + slidename + "' ist nicht geändert worden,", "Sie wird nicht gespeichert!")
        if ok:
            self.data.save_slideshow()
            #ok = AfpReq_Question("Die Slideshow '" + slidename + "' wurde gespeichert!", "Soll diese Slideshow in die Präsentation eingehängt werden?", "Speichern")
            #if ok:
                #self.data.generate_index_html()
        return ok
        
    ## event handler for resizing window
    def On_ReSize(self, event):
        self.list_Source.SetColumnWidth(0, self.list_Source.Size[0])
        self.list_Show.SetColumnWidth(0, self.list_Show.Size[0])
        event.Skip()   
    ## event handler for loading other slideshow
    def On_Change(self, event):
        show = self.combo_Shows.GetValue()
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_change'", show)  
        if show == "- Neu -":
            print("AfpDialog_Sildeshow.On_change:", show)
            show = ""
            show, Ok = AfpReq_Text("Bitte die Bezeichnung (Name oder Ort) für die neue Slideshow eingeben.", "Wenn die beiden letzten Zeichen nicht die aktuelle Jahreszahl darstellen,\n wird das aktuelle Jahr angehängt (_20xx).", show)
            if show and Ok:
                show = show.replace(" ","_")
                jahr = Afp_getToday().year
                j = Afp_toString(jahr)[-2:]
                vj = Afp_toString(jahr-1)[-2:]
                if not (show[-2:] == j or show[-2:] == vj):
                    show += "_" + Afp_toString(jahr)
                shows =  self.combo_Shows.GetStrings()
                shows.append(show.replace("_"," "))
                self.combo_Shows.SetItems(shows)
                self.combo_Shows.SetValue(shows[-1])
        if show:
            self.data.set_show(show)
            self.fill_show_list()
        event.Skip()   
        
   ## Event handler for double click Source Listcontrol
    def On_DClick_Source(self, event=None):
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_DClick_Source'")        
        self.On_Add()
        if event: event.Skip()
   ## Event handler for double click Show Listcontrol
    def On_DClick_Show(self, event=None):
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_DClick_Show'")        
        row = self.list_Show.GetFirstSelected()
        text = self.list_Show.GetItemText(row)
        text, Ok = AfpReq_Text("", "Bitte Text für das ausgewählte Bild eingeben:", text)
        if Ok:
            self.list_Show.SetItemText(row, text)
            self.data.set_image_text(row, text)
        else:
            self.On_Delete()
        if event: event.Skip()

    ## Event handler to move images in the slideshow backwards
    def On_Plus(self, event=None):
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_plus'")        
        row = self.list_Show.GetFirstSelected()
        self.data.move_image(row)
        self.repaint_show_list()
    ## Event handler to move images in the slideshow forewards
    def On_Minus(self, event=None):
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_minus'")        
        row = self.list_Show.GetFirstSelected()
        self.data.move_image(row, True)
        self.repaint_show_list()
    ## Event handler to add images from source to slideshow
    def On_Add(self, event=None):
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_add'")        
        row = self.list_Source.GetFirstSelected()
        max = self.text_Text.GetValue()
        if max:
            max = Afp_fromString(max)
            if self.data.get_image_len() >= max: 
                AfpReq_Info("Maximale Anzahl von Bildern in der Slideschow erreicht,", "bitte ein Bild löschen bevor ein weiteres hinzugefügt werden kann.")
                row = -1
        if row >= 0:
            sel = self.list_Show.GetFirstSelected()
            #print "AfpDialog_Sildeshow.On_add:", row, sel
            if sel >= 0:
                label = "Bild vor der ausgewählten Position(" + Afp_toString(sel+1) + ") in die Slideshow anfügen?"
            else:
                label = "Bild am Ende der Slideshow anfügen?"
            text = ""
            text, Ok = AfpReq_Text(label, "Bitte Text für das ausgewählte Bild eingeben:", text)
            if Ok:
                self.data.add_source_to_show(row, sel, text)
                self.repaint_show_list()
        if event: event.Skip()   
    ## Event handler to delete images from slideshow
    def On_Delete(self, event=None):
        if self.debug: print("AfpDialog_calEvents Event handler `On_delete'")
        sel = self.list_Show.GetFirstSelected()
        if sel >= 0:
            ok = AfpReq_Question("Ausgewähltes Bild", "aus der Slideshow löschen?", "Löschung")
            if ok:
                self.data.delete_from_show(sel)
                self.repaint_show_list()
        if event: event.Skip()

    ## Get file from remote site and load data
    def On_Get(self, event):
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_Get'")
        liste = [self.data.get_localname(True), "Alle Slideshows"]
        results = AfpReq_MultiLine( "Bitte auswählen was vom Server heruntergeladen werden soll!", "Dafür bitte den ensprechenden Knopf drücken.", "Button", liste, "Vom Server holen", 300)
        if results:
            result = ""
            for res in results:
                if res: result = res
            if result == "Alle Slideshows": 
                self.data.get_all_slideshows()
                self.fill_show_combo()
            else:
                self.data.get_slideshow()
            self.fill_show_list()
        event.Skip()
   ## Load data from selected file
    def On_Load(self, event):
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_Load'")
        liste = ["Quellverzeichnis","Slideshow"]
        results = AfpReq_MultiLine( "Auswählen was neu geladen werden soll!", "Bitte den ensprechenden Knopf drücken.", "Button", liste, "Laden", 300)
        if results:
            result = ""
            for res in results:
                if res: result = res
            if result == "Slideshow":
                dir = self.data.get_localpath()
                pathname, Ok = AfpReq_FileName(dir,"Bitte Slideshow auswählen, die geladen werden soll.", None)
                if pathname[-5:] == ".html":
                    pathname = pathname[:-5] 
                #print "AfpDialog_Sildeshow.On_Load:", pathname, Ok
                if Ok and pathname:
                    locpath = self.data.get_localpath(False)
                    show = self.data.set_localshow(pathname).replace("_"," ")
                    shows =  self.combo_Shows.GetStrings()
                    if not show in shows:
                        shows.append(show)
                        self.combo_Shows.SetItems(shows)
                        self.data.set_new(True)
                    else:
                        self.data.set_new(False)
                    self.combo_Shows.SetValue(show)
                    self.fill_show_list()
                    self.data.set_localpath(locpath)
            else:
                dir = self.data.get_localpath(False)
                pathname, Ok = AfpReq_FileName(dir,"Bitte Verzeichnis auswählen, das geladen werden soll.", None)
                #print "AfpDialog_Sildeshow.On_Load:", pathname, Ok
                if Ok and pathname:
                    self.fill_source_list(pathname)
        event.Skip()
   ## Save dialog entries to local file
    def On_Save(self, event):
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_Save'")
        self.write_data()
        event.Skip()
   ## Save dialog entries to local file and send file to remote site
    def On_Send(self, event):
        if self.debug: print("AfpDialog_Sildeshow Event handler `On_Send'")
        if self.data.has_changed():
            ok = self.write_data()
        else:
            ok =True
        if ok:
            slidename = self.data.get_localname()
            ok = AfpReq_Question("Die Slideshow '" + slidename + "' lokal gesichert,", "soll diese Slideshow auf den Internet-Server übetragen werden?", "FTP-Upload")
            if ok: self.data.publish_slideshow()
        event.Skip()
   ## Event handler for Quit Button
    def On_End(self, event=None):
        if self.debug: print("AfpDialog_calEvents Event handler `On_End'")
        self.execute_Quit()
        if event: event.Skip()
        self.EndModal(wx.ID_CANCEL)

## loader routine for calendar events handling  \n
# @param data - SelectionList data where holding or generation events for
def AfpLoad_Slideshow(data):
    DiSlide = AfpDialog_Sildeshow(None)
    DiSlide.attach_data(data)
    DiSlide.ShowModal()
    Ok = DiSlide.get_Ok()
    DiSlide.Destroy()
    return Ok 


# Main  executable program 
if __name__ == "__main__": 
    lgh = len(sys.argv)
    config = None
    debug = False
    execute = True
    if lgh > 1:
        if sys.argv[1] == "-h" or  sys.argv[1] == "--help":
            print("usage: AfpInternetUpdater [option] configuration")
            print("AfpInternetUpdater allows update of internet pages holding events or slied shows.")
            print("The configuration is")
            print("Options and arguments:")
            print("-h, --help     display this text")
            print("-v,--verbose   display comments on all actions (debug-information)")
            print("configuration  name of configuration file name, the entries in this file are: 'PARAMETRE_NAME=paramter value',")
            print("   FTP section:")
            print("   ftp-server  name or IP of ftpserver")
            print("   ftp-user    name user on ftpserver")
            print("   ftp-word    encrypted word for user")
            print("   LOCAL section:")
            print("   local-clientname  name of client to be displayed in dilaog")
            print("   local-root        local directory where data could be found")
            print("   local-maximages   maximum number of slides to be inserted into slideshow - only for slideshows")
            print("   local-max-thumbs-per-line   maximal number of thumbs in a line of slideshow index file - only for slideshows")
            print("   CALENDAR section:")
            print("   cal-[Name]        relativ_path_to_'local-root'_for_file_holding_eventdata,relativ_path_to_file_on_ftp-site_holding_eventdata")
            print("       [Name]        type of events delivered in file, will be displayed on button")
            print("     Example:        'cal-Feiertage=mainframes/impressionen/feiertage.js,feiertage.js'")
            print("   SLIDESHOW section:")
            print("   show-[Name]       relativ_path_to_'local-root'_for_html-file_and_directory_holding_slidedata,relativ_path_to_html-file_and_directory_on_ftp-site_holding_slidedata")
            print("        [Name]       name of slideshow, will be displayed as 'Slide Name' on button")
            print("      Example:       'show-Fuhse=mainframes/impressionen/slides/Fuhse_2021,slides/Fuhse_2021'")
            print("                     a slideshow consists of a html-file and a directory with the same name holding the images")
            print("                     in this directory another directory named 'small' will hold the thumbnails of the images")
            print("   show-slideshows   same as 'show-Hompage' uses same entries (see above)")
            print()
            execute = False
        elif sys.argv[1] == "-v" or  sys.argv[1] == "--verbose":
            debug = True
            if lgh > 2:
                config = sys.argv[2] 
        else:
            config = sys.argv[1] 
    if debug: print("AfpInternetUpdater main:", sys.argv) 
    if execute:
        ex = wx.App(redirect=False)
        Afp_InternetUpdater(config, debug)
    if debug: print("AfpInternetUpdater main: dialog closed")
