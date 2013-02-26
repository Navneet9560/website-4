# Copyright 2011 Daniel James
# Distributed under the Boost Software License, Version 1.0.  (See accompanying
# file LICENSE_1_0.txt or http://www.boost.org/LICENSE_1_0.txt)

import re
import boost_site.site_tools

#
# Upgrades
#

def upgrade1():
    pages = boost_site.site_tools.load_pages()
    for qbk_file in pages.pages:
        page = pages.pages[qbk_file]
        if re.match('users/(download|history)', page.location) and \
                page.pub_date != 'In Progress':
            page.flags.add('released')
    pages.save()
    return True

def upgrade2():
    pages = boost_site.site_tools.load_pages()
    for qbk_file in pages.pages:
        page = pages.pages[qbk_file]
        if re.match('users/(download|history)', page.location) and \
                page.pub_date != 'In Progress':
            page.type = 'release'
        else:
            page.type = 'page'
    pages.save()
    return True

def upgrade3():
    pages_raw = boost_site.state.load('generated/state/feed-pages.txt')
    for page in pages_raw:
        page_details = pages_raw[page]
        flags = page_details['flags']
        flags = set(page_details['flags'].split(','))
        if '' in flags:
            flags.remove('')
        type = page_details['type']
        if type == 'release':
            if 'released' in flags:
                page_details['release_status'] = 'released'
                flags.remove('released')
            elif 'beta' in flags:
                page_details['release_status'] = 'beta'
                flags.remove('beta')
            else:
                page_details['release_status'] = None
        if len(flags) != 0:
            raise Exception("Unexpected flags: " + str(flags))
        del page_details['flags']
    boost_site.state.save(pages_raw, 'generated/state/feed-pages.txt')
    return True

def upgrade4():
    """
        Save all the rss entries to a state file.
        Will remove the rss hashes soon, which should improve some the
        rss handling a bit.
    """
    import xml.dom.minidom
    from boost_site.settings import settings

    pages = boost_site.site_tools.load_pages()

    # Load RSS items from feeds.
    old_rss_items_doc = xml.dom.minidom.parseString('''<items></items>''')
    old_rss_items = {}
    for feed_file in settings['feeds']:
        old_rss_items.update(pages.load_rss(feed_file, old_rss_items_doc))

    # Convert items to text (TODO: Should I support XML in state files?)
    for file in old_rss_items:
        old_rss_items[file]['item'] = old_rss_items[file]['item'].toxml('utf-8').decode('utf-8')

    boost_site.state.save(old_rss_items, 'generated/state/rss-items.txt')
    return True

versions = [
        upgrade1,
        upgrade2,
        upgrade3,
        upgrade4
        ]

#
# Implementation
#

def upgrade():
    version = Version()

    if(version.version < len(versions)):
        print("Upgrading to new version.")

        for v in range(version.version, len(versions)):
            print("Upgrade " + str(v + 1))
            if not versions[v]():
                raise Exception("Error upgrading to version v")
            version.version = v + 1
            version.save()

class Version:
    def __init__(self):
        self.filename = 'generated/state/version.txt'
        self.load()

    def load(self):
        version_file = open(self.filename, "r")
        try:
            self.version = int(version_file.read())
        finally:
            version_file.close()

    def save(self):
        version_file = open(self.filename, "w")
        try:
            version_file.write(str(self.version))
        finally:
            version_file.close()
