from html.parser import HTMLParser
from datetime import datetime

class NatureParser(HTMLParser):
    def __init__(self):
        super(NatureParser, self).__init__()
        self.data_type = None #used temporarily to hold type of data being read
        self.data_subtype = None
        self.section_type = None
        self.n = -1 #index of article being read
        self.issue_date = None
        self.titles = []
        self.authors = []
        self.descriptions = []
        self.links = []
        self.article_types = []
        self.warnings = ""

    def feed(self, data):
        super(NatureParser, self).feed(data)
        self.quality_check()

    def quality_check(self):
        #if not type(self.issue_date) is type(datetime(1,1,1).date()):
        #    raise NoDateError('No date for Nature')
        if len(self.titles) < 8:
            self.warnings += "Warning: found too few articles in Nature"
        if sum([x == [] for x in self.authors]) > len(self.titles)/2:
            self.warnings += "Warning: found many articles with no authors in Nature"
        if sum([x == '' for x in self.descriptions]) > len(self.titles)/2:
            self.warnings += "Warning: found many articles with no description in Nature"
        if sum([x == '' for x in self.links]) > 0:
            self.warnings += "Warning: could not find links to all articles in Nature"
        if len(set(self.article_types)) < 2:
                self.article_types = [None for x in self.article_types]

    def handle_starttag(self, tag, attrs):
        if self.data_type == "ignore":
            #look for signal to stop ignoring if there is ever content after ignore signal
            return None
        if (tag == "h1"
            and len(attrs)>0
            and (
                attrs[0] == ("class", "primary-heading")
                or attrs[0] == ("class", "secondary-heading")
            )):
            self.data_type = "section"
        if (tag == "span" 
            and len(attrs)>0 
            and attrs[0] == ("class", "more")
            ):
            self.data_type = "date"
        if (tag == "article" and not self.data_type == "ignore"
            ):
            self.n += 1
            self.titles.append('')
            self.authors.append([])
            self.descriptions.append('')
            self.links.append('')
            self.article_types.append(self.section_type)
            self.data_type = "article"
        if (self.data_type == "article"
            and tag == "h1"
            ):
            self.data_subtype = "title"
        if (self.data_type == "article"
            and self.data_subtype == "title"
            and tag == "a"
            and len(attrs)>0
            and attrs[0][0] == "href"
            ):
            link = attrs[0][1]
            if not link.startswith('http://www.nature.com/'):
                link = 'http://www.nature.com/' + link
            self.links[self.n] = link
        if (self.data_type == "article"
            and tag == "p"
            ):
            self.data_subtype = "description"
        if (self.data_type == "article"
            and tag == "ul"
            and len(attrs)>0
            and attrs[0] == ("class", "authors limited")
            ):
            self.data_subtype = "authors"
        if (tag == "div"
            and len(attrs)>0
            and attrs[0] == ("id", "extranav")
            ):
            self.data_type = "ignore"
            self.data_subtype = None

    def handle_endtag(self, tag):
        if tag == "article" and self.data_type == "article":
            self.data_type = None
        if tag == "span" and self.data_type == "date":
            self.data_type = None
            self.data_subtype = None
        if tag == "p" and self.data_subtype == "description":
            self.data_subtype = None
        if tag == "a" and self.data_subtype == "title":
            self.data_subtype = None
        if tag == "ul" and self.data_subtype == "authors":
            self.data_subtype = None
        if tag == "h1" and self.data_type == "section":
            self.data_type = None
     
    def handle_data(self, data):
        if self.data_type == "date":
            self.issue_date = datetime.strptime(data, '%d %B %Y').date()
            self.data_type = None
        if self.data_type == "article":
            if self.data_subtype == "title":
                self.titles[self.n] += data.replace("\n", "").replace("\t", "").strip() + " "
            if self.data_subtype == "description":
                self.descriptions[self.n] += data.replace("\n", "").replace("\t", "").strip() + " "
            if self.data_subtype == "authors":
                self.authors[self.n].append(data.strip())
        if self.data_type == "section":
            self.section_type = data
