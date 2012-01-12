# -*- coding: utf-8 -*-
from sqlalchemy import Integer, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

base = declarative_base()

class URL(base):
    __tablename__ = 'urls'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(255), unique=True)
    
    def __init__(self, url):
        self.url = url
    
    def __repr__(self):
        return '<URL {}>'.format(self.url)


class URLData(base):
    __tablename__ = 'url_data'
    
    id = Column(Integer, primary_key=True)
    url_id = Column(Integer, ForeignKey('urls.id'))
    data_key = Column(String(255))
    data_value = Column(Text)
    
    def __init__(self, url_id, key, value):
        self.url_id = url_id
        self.data_key = key
        self.data_value = value
    
    def __repr__(self):
        return '<URLData {}: {}>'.format(self.data_key, self.data_value)
