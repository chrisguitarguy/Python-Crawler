# -*- coding: utf-8 -*-
from threading import Thread, Event
from Queue import Empty, Queue

import lxml.html as parser

from .functions import fetch_element_att, fetch_element_text, \
    fetch_links, fetch_url, parse_content, parse_headers
from .events import NewUrlEvent, NewURLDataEvent, NewNoteEvent, send_event
from .queues import URLQueue

class Dispatcher(Thread):
    """
    Sends and receives signals from all the other threads in the application.
    """
    name = 'dispatcher'
    daemon = True
    
    def __init__(self, timeout=600.0, fetchers=2, base=None, gui=None):
        Thread.__init__(self)
        
        self.killer = Event()
        self.abrupt = Event()
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
                Fetcher(self.url_queue, self.signal_queue, 
                self.killer, self.abrupt))  
        self.parser = Parser(self.content_queue, self.signal_queue, 
                                self.base_url, self.killer, self.abrupt)
        
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
        
        while 1 and not self.abrupt.is_set():
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
        elif 'send_note' == action:
            url, e = val
            send_event(self.gui, NewNoteEvent(url, e))
        elif 'url_meta' == action:
            url, dict_ = val
            send_event(self.gui, NewURLDataEvent(url, dict_))
        elif 'stop' == action:
            self.killer.set()
        elif 'stop_now' == action:
            self.killer.set()
            self.empty_queues()
            self.abrupt.set()
            self.stop_fetchers()
            self.stop_parsers()
        else:
            pass # nothin'
    
    def empty_queues(self):
        with self.url_queue.mutex:
            self.url_queue.queue.clear()
        with self.content_queue.mutex:
            self.content_queue.queue.clear()
        with self.signal_queue.mutex:
            self.signal_queue.queue.clear()
    
    def stop_fetchers(self):
        # this seems really bad?
        for i in xrange(0, self.fetchers):
            while getattr(self, 'fetcher{}'.format(i)).is_alive():
                getattr(self, 'fetcher{}'.format(i)).join()

    def stop_parsers(self):
        while self.parser.is_alive():
            self.parser.join()


class Fetcher(Thread):
    """
    Fetches URLs and sends an event to the application with their status 
    codes.  Also places the responses body into a Queue for further processing
    by ParserThread
    """
    name = 'fetcher'
    daemon = True
    
    def __init__(self, url_queue, signal_queue, killer, abrupt):
        Thread.__init__(self)
        
        self.urls = url_queue
        self.signal = signal_queue
        self.killer = killer
        self.abrupt = abrupt
    
    def run(self):
        while not self.killer.is_set():
            try:
                url = self.urls.get_nowait()
            except Empty:
                continue
            else:
                self.handle_url(url)
                self.urls.task_done()
        
        while 1 and not self.abrupt.is_set():
            try:
                url = self.urls.get(True, 10)
            except Empty:
                break
            else:
                self.handle_url(url)
                self.urls.task_done()
    
    def handle_url(self, url):
        content, headers, status, notes = fetch_url(url)
        if status is None:
            self.signal.put(('send_note', (url, notes)))
            return
        if content is not None:
            self.signal.put(('add_content', (url, content)))
        if headers is not None:
            meta = parse_headers(headers)
            meta['status'] = status
            self.signal.put(('url_meta', (url, meta)))
        if notes is not None:
            self.signal.put(('send_note', (url, notes)))
                    

class Parser(Thread):
    """
    Parses the HTML sent from FetcherThread. Finds the title, meta description
    meta keywords, and rel canonical
    """
    name = 'parser'
    daemon = True
    
    def __init__(self, content_queue, signal_queue, base_url, killer, abrupt):
        Thread.__init__(self)
        self.content = content_queue
        self.signal = signal_queue
        self.url = base_url
        self.killer = killer
        self.abrupt = abrupt
    
    def run(self):
        while not self.killer.is_set():
            try:
                url, to_parse = self.content.get_nowait()
            except Empty:
                continue
            else:
                self.parse_content(url, to_parse)
                self.content.task_done()
        
        while 1 and not self.abrupt.is_set():
            try:
                url, to_parse = self.content.get(True, 10)
            except Empty:
                break
            else:
                self.parse_content(url, to_parse)
                self.content.task_done()
    
    def parse_content(self, url, to_parse):
        parsed = parse_content(to_parse)
        if parsed is None:
            self.signal.put(('send_note', (url, 'HTML parsing error')))
            return
        
        if not self.killer.is_set():
            links = fetch_links(parsed)
            if links is not None:
                out_links = set()
                for l in links:
                    if l.startswith(self.url):
                        out_links.add(l)
                self.signal.put(('add_urls', out_links))
        
        out = {
            'title': '--',
            'desc': '--',
            'kw': '--',
            'canonical': '--',
            'h1': '--',
            'h2': '--'
        }
        title = fetch_element_text(parsed, 'title')
        if title is not None:
            out['title'] = title
        desc = fetch_element_att(parsed, 'meta[name=description]', 'content')
        if desc is not None:
            out['desc'] = desc
        kw = fetch_element_att(parsed, 'meta[name=keywords]', 'content')
        if kw is not None:
            out['kw'] = kw
        canonical = fetch_element_att(parsed, 'link[rel=canonical]', 'href')
        if canonical is not None:
            out['canonical'] = canonical
        h1 = fetch_element_text(parsed, 'h1')
        if h1 is not None:
            out['h1'] = h1
        h2 = fetch_element_text(parsed, 'h2')
        if h2 is not None:
            out['h2'] = h2
        self.signal.put(('url_meta', (url, out)))
        
