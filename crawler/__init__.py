#! /usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
from Queue import Queue
import signal
import sys
from threading import Event

from .threads import Fetcher, Parser
from .queues import URLQueue

class main(object):
    
    def __init__(self):
        self.num_fetchers = 3
        self.base_url = None
        self.parser = None
        self.killer = Event()
        self.abrupt = Event()
        self.url_queue = URLQueue()
        self.content_queue = Queue()
        self.signal_queue = Queue()
        
    
    def __call__(self):
        parser = argparse.ArgumentParser(description="SEO web scraping")
        parser.add_argument('-s', '--start', dest='start_url',
                                 help='The URI where the crawl starts.')
        parser.add_argument('-f', '--fetchers', dest='fetchers', 
                                   help='The number of fetcher threads')
        args = parser.parse_args()
        if args.start_url is None:
            print ('Usage: {} -s <start_url> '
                        '[-f <number of fetchers>]'.format(sys.argv[0]))
            sys.exit(1)
        if args.fetchers is not None:
            try:
                self.num_fetchers = int(args.fetchers)
            except ValueError:
                pass # leave it at three fetcher threads
        self.connect_signals()
        self.set_fetchers()
        self.set_parser()
        self.parser.start()
        for i in range(0, self.num_fetchers):
            getattr(self, 'fetcher{}'.format(i)).start()
        
        while 1:
            try:
                pass
            except KeyboardInterrupt:
                pass
    
    def set_fetchers(self):
        for i in xrange(0, self.num_fetchers):
            setattr(self, 'fetcher{}'.format(i), 
                Fetcher(self.url_queue, self.signal_queue, 
                    self.killer, self.abrupt))
    
    def set_parser(self):
         self.parser = Parser(self.content_queue, self.signal_queue, 
                                self.base_url, self.killer, self.abrupt)
    
    def stop_fetchers(self):
        # this seems really bad?
        for i in xrange(0, self.num_fetchers):
            while getattr(self, 'fetcher{}'.format(i)).is_alive():
                getattr(self, 'fetcher{}'.format(i)).join()
    
    def stop_parsers(self):
        while self.parser.is_alive():
            self.parser.join()
    
    def empty_queues(self):
        with self.url_queue.mutex:
            self.url_queue.queue.clear()
        with self.content_queue.mutex:
            self.content_queue.queue.clear()
        with self.signal_queue.mutex:
            self.signal_queue.queue.clear()
    
    def connect_signals(self):
        signal.signal(signal.SIGINT, self.catch_cancel)
    
    def catch_cancel(self, signal, frame):
        print 'stopping threads'
        self.killer.set()
        self.abrupt.set()
        self.stop_fetchers()
        self.stop_parsers()
        sys.exit(0)
