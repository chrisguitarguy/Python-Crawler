# -*- coding: utf-8 -*-
from Queue import Queue

class URLQueue(Queue):
    def __init__(self):
        Queue.__init__(self)
        self.urls = set()
    
    def add_url(self, url):
        if url not in self.urls:
            self.put(url)
            self.urls.add(url)
            return True
        else:
            return False
