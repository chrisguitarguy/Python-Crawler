# -*- coding: utf-8 -*-
from threading import Thread
from Queue import Empty

import lxml.html as parser

from .functions import (fetch_element_att, fetch_element_text,
    fetch_links, fetch_url, parse_content, parse_headers)

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
        
