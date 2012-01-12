# -*- coding: utf-8 -*-
from tempfile import NamedTemporaryFile

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
import wx
import wx.grid

from events import ID_NEW_URL, ID_NEW_DATA, ID_NEW_NOTE
from grids import URLGrid
from menus import MainMenu
from models import URL, URLData, base
from threads import Dispatcher


class Main(wx.Frame):
    """
    The main application view
    """
    
    def __init__(self, parent=None, title='Python Crawler'):
        wx.Frame.__init__(self, parent=parent, title=title)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.panel = wx.Panel(self, wx.ID_ANY)
        self.panel.SetSizer(sizer)
        self.urls = {}
        self.counter = 0;
        self.CreateStatusBar()
        
        # set up menus
        self.menu = MainMenu()
        self.SetMenuBar(self.menu)
        
        # set up the grid
        self.grid = URLGrid(sizer, self.panel)
        
        # Bind menu events
        self.Bind(wx.EVT_MENU, self.menu_exit, self.menu.file_menu.exit)
        
        # Bind events from worker thread
        self.Connect(-1, -1, ID_NEW_URL, self.event_url)
        self.Connect(-1, -1, ID_NEW_DATA, self.event_data)
        self.Connect(-1, -1, ID_NEW_NOTE, self.event_note)
        
        ## lame stuff for testing.  To be removed.
        urls = ['http://www.classicalguitar.org/about', 'http://www.classicalguitar.org']
        d = Dispatcher(base='http://www.classicalguitar.org/', gui=self)
        d.signal_queue.put(('add_urls', urls))
        d.start()
        
        self.Show()
        
    def menu_exit(self, event):
        self.Close(True)
    
    def event_url(self, event):
        self.urls[event.url] = self.counter
        self.grid.AppendRows(1)
        self.grid.SetCellValue(self.counter, 0, event.url)
        self.counter += 1
    
    def event_data(self, event):
        row = self.urls.get(event.url)
        if row is None:
            return # probably should do something here?
        for key, value in event.data.items():
            col = self.grid.get_col_data(key)
            if col is None:
                continue
            if isinstance(value, basestring):
                value = value.encode('ascii', 'ignore')
            else:
                value = str(value)
            self.grid.SetCellValue(row, col[0], value)
    
    def event_note(self, event):
        row = self.urls.get(event.url)
        if row is None:
            return
        col = self.grid.get_col_data('notes')
        self.grid.SetCellValue(row, col[0], event.note)
        
    def setup_db(self):
        self.tempdb = NamedTemporaryFile(prefix='pycrawlcli-temp-', suffix='.db')
        self.engine = create_engine('sqlite:///{}'.format(self.tempdb.name))
        self.maker = sessionmaker(bind=self.engine)
    
    @classmethod
    def get_cols(cls):
        return cls.column_map
    
    @classmethod
    def get_col_info(cls, col):
        return cls.column_map.get(col)


class CheckSingleDialog(wx.Dialog):
    pass

class CrawlDialog(wx.Dialog):
    pass
