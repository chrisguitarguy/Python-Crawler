# -*- coding: utf-8 -*-
import re

import wx

from .events import send_event, StartEvent

class CheckSingleDialog(wx.Dialog):
    pass # todo


class CrawlDialog(wx.Dialog):
    """
    The dialog to start a crawl and adjust all the settings, etc.
    """
    def __init__(self, *args, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        fb_panel = wx.Panel(self)
        fetcher_box = wx.StaticBox(fb_panel, label='Fetcher Threads')
        fb_sizer = wx.StaticBoxSizer(fetcher_box, orient=wx.VERTICAL)
        self.fetcher_1 = wx.RadioButton(fb_panel, label='1')
        self.fetcher_2 = wx.RadioButton(fb_panel, label='2')
        self.fetcher_3 = wx.RadioButton(fb_panel, label='3')
        self.fetcher_4 = wx.RadioButton(fb_panel, label='4')
        self.fetcher_5 = wx.RadioButton(fb_panel, label='5')
        fb_sizer.Add(self.fetcher_1)
        fb_sizer.Add(self.fetcher_2)
        fb_sizer.Add(self.fetcher_3)
        fb_sizer.Add(self.fetcher_4)
        fb_sizer.Add(self.fetcher_5)
        fb_panel.SetSizer(fb_sizer)
        
        ub_panel = wx.Panel(self)
        url_box = wx.StaticBox(ub_panel, label='Start URL')
        ub_sizer = wx.StaticBoxSizer(url_box, orient=wx.VERTICAL)
        self.url_field = wx.TextCtrl(ub_panel, size=(378, 30,))
        ub_sizer.Add(self.url_field)
        ub_panel.SetSizer(ub_sizer)
        
        ok_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.okay = wx.Button(self, wx.ID_OK, label='Crawl')
        self.cancel = wx.Button(self, wx.ID_CANCEL, label='Cancel')
        ok_sizer.Add(self.okay)
        ok_sizer.Add(self.cancel, flag=wx.LEFT, border=5)
        
        vbox.Add(ub_panel, proportion=1, flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(fb_panel, proportion=2, flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(ok_sizer, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)
        
        self.SetSizer(vbox)
        
        # Bind Events
        self.okay.Bind(wx.EVT_BUTTON, self.on_okay)
        self.cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.Bind(wx.EVT_RADIOBUTTON, self.set_fetcher_1, self.fetcher_1)
        self.Bind(wx.EVT_RADIOBUTTON, self.set_fetcher_2, self.fetcher_2)
        self.Bind(wx.EVT_RADIOBUTTON, self.set_fetcher_3, self.fetcher_3)
        self.Bind(wx.EVT_RADIOBUTTON, self.set_fetcher_4, self.fetcher_4)
        self.Bind(wx.EVT_RADIOBUTTON, self.set_fetcher_5, self.fetcher_5)
        self.num_fetcher = 2
        
    
    def on_okay(self, event):
        url = self.url_field.GetValue()
        # kinda lame...
        match = re.match(r'^https?://(.*?)$', url)
        if match is None:
            wx.MessageBox('Invalid URL', 'Error', wx.OK | wx.ICON_ERROR)
        else:
            send_event(self.GetParent(), StartEvent(url, self.num_fetcher))
            self.Destroy()
        
    def on_cancel(self, event):
        self.Destroy()
    
    def set_fetcher_1(self, event):
        self.num_fetcher = 1
    
    def set_fetcher_2(self, event):
        self.num_fetcher = 2
    
    def set_fetcher_3(self, event):
        self.num_fetcher = 3
    
    def set_fetcher_4(self, event):
        self.num_fetcher = 4
    
    def set_fetcher_5(self, event):
        self.num_fetcher = 5
