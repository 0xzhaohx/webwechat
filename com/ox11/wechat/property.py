#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-

import re
import os
import tempfile
import sys

reload(sys)

sys.setdefaultencoding('utf8')

class Properties:

    def __init__(self, pfile):
        self.pfile = pfile
        self.properties = {}
        with open(self.pfile, 'r') as fopen:
            for line in fopen:
                line = line.strip()
                if line.find('=') > 0 and not line.startswith('#'):
                    strs = line.split('=')
                    self.properties[strs[0].strip()] = strs[1].strip()
                    
    def has_key(self, key):
        return key in self.properties

    def get(self, key, default_value=''):
        if key in self.properties:
            return self.properties[key]
        return default_value

    def put(self, key, value):
        self.properties[key] = value
        replace_property(self.file_name, key + '=.*', key + '=' + value, True)


def parse(pfile):
    return Properties(pfile)


def replace_property(pfile, from_regex, to_str, append_on_not_exists=True):
    tmpfile = tempfile.TemporaryFile()

    if os.path.exists(pfile):
        r_open = open(pfile, 'r')
        pattern = re.compile(r'' + from_regex)
        found = None
        for line in r_open:
            if pattern.search(line) and not line.strip().startswith('#'):
                found = True
                line = re.sub(from_regex, to_str, line)
            tmpfile.write(line)
        if not found and append_on_not_exists:
            tmpfile.write('\n' + to_str)
        r_open.close()
        tmpfile.seek(0)

        content = tmpfile.read()

        if os.path.exists(pfile):
            os.remove(pfile)

        w_open = open(pfile, 'w')
        w_open.write(content)
        w_open.close()

        tmpfile.close()
    else:
        print "properties file %s not found" % pfile
        