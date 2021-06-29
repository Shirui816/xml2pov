from io import StringIO
from xml.etree import cElementTree

import pandas as pd


class Box(object):
    def __init__(self):
        return

    def update(self, dic):
        self.__dict__.update(dic)


class Xml(object):
    def __init__(self, filename, needed=None, skip=None):
        tree = cElementTree.ElementTree(file=filename)
        root = tree.getroot()
        self.box = Box()
        self.meta = {}
        self.contents = {}
        needed = [] if needed is None else needed
        skip = [] if skip is None else skip
        for key in root[0].attrib:
            self.meta[key] = int(root[0].attrib[key])
        for element in root[0]:
            if element.tag == 'box':
                self.box.update(element.attrib)
                continue
            if (len(needed) > 0) and (element.tag not in needed):
                continue
            if (len(skip) > 0) and (element.tag in skip):
                continue
            self.contents[element.tag] = pd.read_csv(StringIO(element.text),
                                                     delim_whitespace=True,
                                                     squeeze=1,
                                                     header=None,
                                                     ).values
