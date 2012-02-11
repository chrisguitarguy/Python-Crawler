# -*- coding: utf-8 -*-
import wx

ID_BUGS = wx.NewId()
ID_LIST = wx.NewId()
ID_DOCS = wx.NewId()
ID_UPDATES = wx.NewId()
ID_STOP_ABRUPT = wx.NewId()

class FileMenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)
        
        self.new_crawl = self.Append(wx.ID_NEW, '&New', 'New Crawl')
        #self.check_single = self.Append(wx.NewId(), 'Check Single', 
        #                                           'Check a single url')
        #self.check_list = self.Append(ID_LIST, 'Check List', 
        #                        'Check a list of URLs from a text file')
                                
        self.AppendSeparator()
        
        #self.save = self.Append(wx.ID_SAVE, '&Save', 
        #                                       'Save the current crawl')
        self.export = self.Append(wx.ID_SAVEAS, 'Export', 
                                            'Export to sql, csv or tsv')
        
        self.AppendSeparator()
        
        self.stop = self.Append(wx.ID_CANCEL, 'Stop Crawl (graceful)', 
            'Stop the current crawl, but finish up all the URLs in the queue.')
        self.stop_abrupt = self.Append(ID_STOP_ABRUPT, 'Stop Crawl (abrubt)',
            "Stop the current crawl abruptly -- don't finish the URLs in the queue")
        self.AppendSeparator()
        self.exit = self.Append(wx.ID_EXIT, 'E&xit', 'Quit this program')


class HelpMenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)
        
        self.about = self.Append(wx.ID_ABOUT, '&About', 'About this program')
        self.bugs = self.Append(ID_BUGS, 'Report Bugs', 'Report bugs and glitches')
        self.docs = self.Append(ID_DOCS, 'Documentation', 'Online documentation')
        #self.updates = self.Append(ID_UPDATES, 'Updates', 'Check for available updates')


class MainMenu(wx.MenuBar):
    def __init__(self):
        wx.MenuBar.__init__(self)
        self.file_menu = FileMenu()
        self.help_menu = HelpMenu()
        
        self.Append(self.file_menu, '&File')
        self.Append(self.help_menu, '&Help')
        
