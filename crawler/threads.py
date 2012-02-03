# -*- coding: utf-8 -*-
from threading import Thread, Event
from Queue import Empty, Queue

import lxml.html as parser
import requests
import wx

from queues import URLQueue
from events import NewUrlEvent, NewURLDataEvent, NewNoteEvent, send_event

HEADERS = {'User-Agent': 'PyCrawl 0.1'}

class Dispatcher(Thread):
    """
    Sends and receives signals from all the other threads in the application.
    """
    name = 'dispatcher'
    daemon = True
    
    def __init__(self, timeout=600.0, fetchers=2, base=None, gui=None):
        Thread.__init__(self)
        
        self.killer = Event()
        self.base_url = base
        self.timeout = timeout
        self.fetchers = fetchers
        self.gui = gui
        
        # queues
        self.url_queue = URLQueue()
        self.content_queue = Queue()
        self.signal_queue = Queue()
        
        # other threads
        for i in xrange(0, self.fetchers):
            setattr(self, 'fetcher{}'.format(i), 
                Fetcher(self.url_queue, self.signal_queue, self.killer))  
        self.parser = Parser(self.content_queue, self.signal_queue, 
                                             self.base_url, self.killer)
        
    def run(self):
        for i in xrange(0, self.fetchers):
            getattr(self, 'fetcher{}'.format(i)).start()
        self.parser.start()
        
        while not self.killer.is_set():
            try:
                action, val = self.signal_queue.get(True, self.timeout)
            except Empty:
                self.killer.set()
                continue
            else:
                self.handle_signal(action, val)
                self.signal_queue.task_done()
        
        while 1:
            try:
                action, val = self.signal_queue.get(True, 10)
            except Empty:
                break
            else:
                self.handle_signal(action, val)
                self.signal_queue.task_done()
    
    def handle_signal(self, action, val):
        if 'add_urls' == action:
            for url in val:
                new = self.url_queue.add_url(url)
                if new:
                    send_event(self.gui, NewUrlEvent(url))
        elif 'add_content' == action:
            self.content_queue.put(val)
        elif 'fetch_error' == action:
            url, e = val
            send_event(self.gui, NewNoteEvent(url, e))
        elif 'url_meta' == action:
            url, dict_ = val
            send_event(self.gui, NewURLDataEvent(url, dict_))
        elif 'stop' == action:
            self.killer.set()
        else:
            pass # nothin'


class Fetcher(Thread):
    """
    Fetches URLs and sends an event to the application with their status 
    codes.  Also places the responses body into a Queue for further processing
    by ParserThread
    """
    name = 'fetcher'
    daemon = True
    
    def __init__(self, url_queue, signal_queue, killer):
        Thread.__init__(self)
        
        self.urls = url_queue
        self.signal = signal_queue
        self.killer = killer
        self.headers = HEADERS
    
    def run(self):
        while not self.killer.is_set():
            try:
                url = self.urls.get_nowait()
            except Empty:
                continue
            else:
                self.fetch_url(url)
                self.urls.task_done()
        
        while 1:
            try:
                url = self.urls.get(True, 10)
            except Empty:
                break
            else:
                self.fetch_url(url)
                self.urls.task_done()
    
    def fetch_url(self, url):
        try:
            resp = requests.get(url, headers=self.headers, 
                                          allow_redirects=False)
        except Exception, e:
            self.signal.put(('fetch_error', (url, e)))
        else:
            out = {}
            out['server'] = resp.headers.get('server', 'unknown')
            content_type = resp.headers.get('content-type')
            if content_type is not None:
                out['content_type'] = content_type.split(';', 1)[0]
            else:
                out['content_type'] = 'unknown'
            out['size'] = resp.headers.get('content-length', '-1')
            out['status'] = resp.status_code
            
            self.signal.put(('url_meta', (url, out)))
            if 'text/html' == out['content_type']:
                self.signal.put(('add_content', (url, resp.content)))
                    

class Parser(Thread):
    """
    Parses the HTML sent from FetcherThread. Finds the title, meta description
    meta keywords, and rel canonical
    """
    name = 'parser'
    daemon = True
    
    def __init__(self, content_queue, signal_queue, base_url, killer):
        Thread.__init__(self)
        
        self.content = content_queue
        self.signal = signal_queue
        self.url = base_url
        self.killer = killer
    
    def run(self):
        while not self.killer.is_set():
            try:
                url, to_parse = self.content.get_nowait()
            except Empty:
                continue
            else:
                self.parse_content(url, to_parse)
                self.content.task_done()
        
        while 1:
            try:
                url, to_parse = self.content.get(True, 10)
            except Empty:
                break
            else:
                self.parse_content(url, to_parse)
                self.content.task_done()
    
    def parse_content(self, url, to_parse):
        try:
            parsed = parser.document_fromstring(to_parse)
        except Exception, e:
            self.signal.put(('parsing_error', (url, e)))
        else:
            parsed.make_links_absolute(self.url)
            
            if not self.killer.is_set():
                links = parsed.cssselect('a')
                out_links = set()
                for l in links:
                    href = l.get('href')
                    if href is not None and href.startswith(self.url):
                        out_links.add(href)
                self.signal.put(('add_urls', out_links))
            
            out = {}
            
            ## todo: maybe too much repeating myself here?
            ## could `out` be an object of some sort with a 
            ## set_value method to abstract away this len(x) crap?
            title = parsed.cssselect('title')
            if len(title) > 1:
                out['title'] = ';'.join([t.text_content() for t in title])
            elif len(title) == 1:
                out['title'] = title[0].text_content()
            else:
                out['title'] = 'n/a'
            
            desc = parsed.cssselect('meta[name=description]')
            if len(desc) > 1:
                out['desc'] = ';'.join([d.get('content') for d in desc])
            elif len(desc) == 1:
                out['desc'] = desc[0].get('content')
            else:
                out['desc'] = 'n/a'
            
            kw = parsed.cssselect('meta[name=keywords]')
            if len(kw) > 1:
                out['kw'] = ';'.join([k.get('content') for k in kw])
            elif len(kw) == 1:
                out['kw'] = kw[0].get('content')
            else:
                out['kw'] = 'n/a'
            
            canonical = parsed.cssselect('link[rel=canonical]')
            if len(canonical) > 1:
                out['canonical'] = ';'.join([c.get('href') 
                                            for c in canonical])
            elif len(canonical) == 1:
                out['canonical'] = canonical[0].get('href')
            else:
                out['canonical'] = 'n/a'
                
            h1 = parsed.cssselect('h1')
            if len(h1) > 1:
                out['h1'] = ';'.join([h.text_content().strip() 
                                  for h in h1 if h is not None])
            elif len(h1) == 1:
                out['h1'] = h1[0].text_content().strip()
            else:
                out['h1'] = 'n/a'
            
            h2 = parsed.cssselect('h2')
            if len(h2) > 1:
                out['h2'] = ';'.join([h.text_content().strip() 
                                  for h in h2 if h is not None])
            elif len(h2) == 1:
                out['h2'] = h2[0].text_content().strip()
            else:
                out['h2'] = 'n/a'
            self.signal.put(('url_meta', (url, out)))

if __name__ == '__main__':
    urls = ['http://www.classicalguitar.org/about', 'http://www.classicalguitar.org']
    d = Dispatcher(base='http://www.classicalguitar.org/')
    d.signal_queue.put(('add_urls', urls))
    d.start()
        
