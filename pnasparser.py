from html.parser import HTMLParser
from datetime import datetime

class PNASParser(HTMLParser):
        def __init__(self):
            super(PNASParser, self).__init__()
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
            super(PNASParser, self).feed(data)
            self.quality_check()

        def quality_check(self):
            #if not type(self.issue_date) is type(datetime(1,1,1).date()):
            #    raise NoDateError('No date for PNAS')
            if len(self.titles) < 8:
                self.warnings += "Warning: found too few articles in PNAS" + '\n'
            if sum([x == [] for x in self.authors]) > len(self.titles)/2:
                self.warnings += "Warning: found many articles with no authors in PNAS" + '\n'
            #if sum([x == '' for x in self.descriptions]) > 6:
            #    self.warnings += "Warning: found many articles with no description in PNAS"  + '\n'
            if sum([x == '' for x in self.links]) > 0:
                self.warnings += "Warning: could not find links to all articles in PNAS"  + '\n'
            if len(set(self.article_types)) < 2:
                self.article_types = ["Article" for x in self.article_types]

        def handle_starttag(self, tag, attrs):
            if (tag == "span" 
                and len(attrs)>0 
                and attrs[0][1] == "highwire-cite-metadata-pub-date highwire-cite-metadata"
                ):
                self.data_type = "date"

            if (tag == "div" 
                and len(attrs)>0
                and attrs[0] == ("class", "highwire-cite-access")):
                self.n += 1
                self.titles.append('')
                self.authors.append([])
                self.descriptions.append('')
                self.links.append('')
                self.article_types.append(self.section_type)
                self.data_type = "article"
            
            if (self.data_type == "article"
                and tag == "a"
                and len(attrs) >1
                and attrs[1][1] == "highwire-cite-linked-title"
                ):
                self.links[self.n] = "www.pnas.org" + attrs[0][1]

            if (self.data_type == "article"
                and tag == "span"
                and len(attrs) > 0
                and attrs[0][1] == "highwire-cite-title"
                ):
                self.data_subtype = "title"
    
            if (self.data_type == "article"
                and tag == "span"
                and len(attrs) > 0
                and attrs[0][1] == "highwire-citation-authors"
                ):
                self.data_subtype = "author"

            if (tag == "h2"):
                self.data_type = "section"

        def handle_endtag(self, tag):
            if (self.data_subtype == "title" 
                and tag == "a"):
                self.data_subtype = None

            if (self.data_subtype == "author"
                and tag == "div"):
                self.authors[self.n] = ''.join(self.authors[self.n])
                self.data_subtype = None

        def handle_data(self, data):
            if self.data_type == "date":
                self.issue_date =  datetime.strptime(data.split(";")[0].strip(), '%B %d, %Y').date()
                self.data_type = None

            if self.data_subtype == "title":
                self.titles[self.n] = (self.titles[self.n] + ' ' + data).strip()
                self.titles[self.n] = self.titles[self.n].strip()

            if self.data_subtype == "author":
                self.authors[self.n].append(data)   

            if self.data_type == "section":
                self.section_type = data
                self.data_type = None