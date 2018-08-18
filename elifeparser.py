
from html.parser import HTMLParser
from datetime import datetime

class ELifeParser(HTMLParser):
    def __init__(self):
        super(ELifeParser, self).__init__()
        self.data_type = None #used temporarily to hold type of data being read
        self.data_subtype = None
        self.section_type = None
        self.n = -1 #index of article being read
        self.issue_date = None
        self.article_types = []
        self.titles = []
        self.authors = []
        self.descriptions = []
        self.links = []
        self.warnings = ""

    def feed(self, data):
        super(ELifeParser, self).feed(data)
        self.quality_check()

    def quality_check(self):
        #if not type(self.issue_date) is type(datetime(1,1,1).date()):
        #    raise NoDateError('No date for Neuron')
        if len(self.titles) < 4:
            self.warnings += "Warning: found too few articles in ELife"
        if sum([x == [] for x in self.authors]) > 4:
            self.warnings += "Warning: found many articles with no authors in ELife"
        if sum([x == '' for x in self.descriptions]) > 4:
            self.warnings += "Warning: found many articles with no description in ELife"
        if sum([x == '' for x in self.links]) > 0:
            self.warnings += "Warning: could not find links to all articles in ELife"
        if len(set(self.article_types)) < 2:
            self.article_types = ["Article" for x in self.article_types]

    def handle_starttag(self, tag, attrs):

        if (tag == "h4" 
            and len(attrs)>0
            and attrs[0] == ("class", "teaser__header_text")):
            self.n += 1
            self.titles.append('')
            self.authors.append([])
            self.descriptions.append('')
            self.article_types.append(self.section_type)
            self.links.append('')
            self.data_type = "article"
            self.data_subtype = "title"
        
        if (tag == "ol" 
            and len(attrs)>0
            and attrs[0] == ("class", "teaser__context_label_list")):
            self.section_type = None
            self.data_type = "section"

        if (self.data_subtype == "title"
            and tag == "a"
            and len(attrs) > 0
            ):
            self.links[self.n] = 'www.elifesciences.org/' + attrs[0][1]

        if (self.data_type == "article"
            and tag == "div"
            and len(attrs) > 0
            and attrs[0][1] == "teaser__secondary_info"
            ):
            self.data_subtype = "authors"
        
        if (self.data_type == "article"
            and tag == "div"
            and len(attrs) > 0
            and attrs[0][1] == "teaser__body"
            ):
            self.data_subtype = "description"

        if (self.data_type == "article"
            and tag == "footer"
            ):
            self.data_type = None
            self.data_subtype = None

    def handle_endtag(self, tag):

        if (self.data_subtype == "title" 
            and tag == "a"):
            self.data_subtype = None

        if (self.data_subtype == "description" 
            and tag == "div"):
            self.data_subtype = None

        if (self.data_subtype == "authors" 
            and tag == "div"):
            self.data_subtype = None
        
        if (self.data_type == "section"
            and tag == "ol"):
            self.data_type = None

######################
    def handle_data(self, data):

        if self.data_subtype == "title":
            self.titles[self.n] +=  data
            self.titles[self.n] = self.titles[self.n].strip()

        if self.data_subtype == "description":
            self.descriptions[self.n] += data.replace("\xa0", " ").strip()

        if self.data_subtype == "authors":
            self.authors[self.n].append(data.strip())
            self.data_subtype = None

        if self.data_type == "section":
            if self.section_type is None or self.section_type == "":
                self.section_type = data.replace(",", "").strip()
            elif not data.strip() == "": 
                self.section_type += (", " + data.replace(",", "").strip())