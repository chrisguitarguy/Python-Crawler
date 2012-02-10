import logging

import lxml.html as parser
import requests
from requests.exceptions import ConnectionError, RequestException, \
    Timeout, SSLError

def fetch_url(url):
    """
    Fetch a url! this is a simple wrapper around request.get that grabs
    whatever url is thrown at it and returns the content, headers, status
    and whatever notes we may have.
    """
    content = None
    headers = None
    notes = None
    status = None
    headers = {'User-Agent': 'PyCrawl 0.1'}
    try:
        resp = requests.get(url, headers=headers)
    except ValueError as e:
        logging.error('Invalid url on {} - {}'.format(url, e))
        note = 'invalid url'
    except ConnectionError as e:
        logging.error('Could not connect to {}: {}'.format(url, e))
        note = 'Could not connect'
    except SSLError as e:
        # this should ever happen.
        logging.error("Couldn't verify SSL cert for {}: {}".format(url, e))
        note = 'SSL error: could not verify'
    except Timeout as e:
        logging.error('{} timed out: {}'.format(url, e))
        note = 'Request timed out'
    except (RequestException, Exception) as e:
        logging.error('General error on {}: {}'.format(url, e))
        note = 'Something when horribly wrong'
    else:
        if url != resp.url:
            notes = 'Redirected to: {}'.format(url)
        if 'text/html' in resp.headers.get('content-type', ''):
            content = resp.content
        headers = resp.headers
        status = resp.status_code
    finally:
        return content, headers, status, notes


def parse_headers(headers):
    """
    Get the relevant items out of a dict of resp headers.
    """
    out = {
        'server': headers.get('server', 'unknown'),
        'size': headers.get('content-length', '-1'),
    }
    content_type = headers.get('content-type')
    if content_type is not None:
        out['content_type'] = content_type.split(';', 1)[0]
    else:
        out['content_type'] = 'unknown'
    return out


def parse_content(content, base_href=None):
    """
    Turn a big string of HTML into a lxml object with which we can fetch
    the elements we need.
    """
    rv = None
    try:
        rv = parser.document_fromstring(content)
    except Exception as e:
        # todo: what exceptions can this throw?
        logging.error('Could not parse content')
    else:
        if base_href is not None:
            rv.make_links_absolute(base_href)
    return rv


def fetch_element_text(html, css):
    """
    Fetch the given elements specified by the css from html 
    (an `Element` from lxml). Used for things like h1's, h2's, titles:
    anything that we need text content from.
    """
    rv = None
    elements = html.cssselect(css)
    if len(elements) == 1:
        rv = elements[0].text_content()
    elif len(elements) > 1:
        rv = ';'.join([e.text_content().strip() 
                                    for e in elements if e is not None])
    return rv


def fetch_element_att(html, css, attr):
    """
    Fetch the given elements specifed by the css selector from html
    (an `Element` from lxml) and return the attribute (attr) of each.
    """
    rv = None
    elements = html.cssselect(css)
    if len(elements) == 1:
        rv = elements[0].get(attr)
    elif len(elements) > 1:
        rv = ';'.join([e.get(attr) for e in elements])
    return rv

def fetch_links(html):
    """
    Fetch all links on a given page and return their hrefs in a list
    """
    elements = html.cssselect('a')
    return [e.get('href') for e in elements if e.get('href') is not None]
    
        
