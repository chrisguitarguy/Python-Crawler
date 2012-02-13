from collections import OrderedDict

import wx.grid

class URLGrid(wx.grid.Grid):
    """
    The grid object (table) for displaying all the data about the URLs.
    This is here so the init method of the our main frame doesn't get
    cluttered up with grid crap.
    """
    
    # (col number, label, width)
    column_map = OrderedDict([
        ('url', (0, 'URL', 400)),
        ('status', (1, 'Status Code', 150)),
        ('server', (2, 'Server', 150)),
        ('content_type', (3, 'Content Type', 200)),
        ('size', (4, 'Size', 150)),
        ('title', (5, 'Title', 250)),
        ('desc', (6, 'Meta Description', 350)),
        ('kw', (7, 'Meta Keywords', 350)),
        ('canonical', (8, 'Rel Canonical', 300)),
        ('h1', (9, 'H1', 300)),
        ('h2', (10, 'H2', 300)),
        ('x_robots', (11, 'X-Robots-Tag Header', 300)),
        ('notes', (12, 'Notes', 300))
    ])
    
    def __init__(self, sizer, *args, **kwargs):
        wx.grid.Grid.__init__(self, *args, **kwargs)
        
        self.CreateGrid(0, len(self.get_cols()))
        self.SetDefaultColSize(50)
        self.EnableEditing(False)
        self.DefaultCellOverflow = False
        
        sizer.Add(self, 1, wx.EXPAND)
        
        self.DefaultColumnLabelSize = 14
        self.SetRowLabelSize(0)
        for key, data in self.get_cols().items():
            self.SetColLabelValue(data[0], data[1])
            self.SetColSize(data[0], data[2])
    
    @classmethod
    def get_cols(cls):
        return cls.column_map
    
    @classmethod
    def get_col_data(cls, col):
        return cls.column_map.get(col)
