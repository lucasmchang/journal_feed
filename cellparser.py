#This can parse Neuron and Current Biology
#Both are published by Cell and have the same format

from html.parser import HTMLParser
from datetime import datetime

class CellParser(HTMLParser):
        def __init__(self):
            super(CellParser, self).__init__()
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
            super(CellParser, self).feed(data)
            self.quality_check()

        def quality_check(self):
            #if not type(self.issue_date) is type(datetime(1,1,1).date()):
            #    raise NoDateError('No date for Neuron')
            if len(self.titles) < 5:
                self.warnings += "Warning: found too few articles in Cell (Neuron/Current Bio)"
            if sum([x == [] for x in self.authors]) > 4:
                self.warnings += "Warning: found many articles with no authors in Cell (Neuron/Current Bio)"
            if sum([x == '' for x in self.descriptions]) > 4:
                self.warnings += "Warning: found many articles with no description in Cell (Neuron/Current Bio)"
            if sum([x == '' for x in self.links]) > 0:
                self.warnings += "Warning: could not find links to all articles in Cell (Neuron/Current Bio)"
            if len(set(self.article_types)) < 2:
                self.article_types = ["Article" for x in self.article_types]

        def handle_starttag(self, tag, attrs):
            if (tag == "span" 
                and len(attrs)>0 
                and attrs[0] == ("class", "date")
                ):
                self.data_type = "date"

            if (tag == "div" 
                and len(attrs)>0
                and attrs[0] == ("class", "article-details")):
                self.n += 1
                self.titles.append('')
                self.authors.append([])
                self.descriptions.append('')
                self.article_types.append(self.section_type)
                self.links.append('')
                self.data_type = "article"
                self.data_subtype = "title"
            
            if (tag == "h2" 
                and len(attrs)>0
                and attrs[0] == ("class", "heading")):
                self.data_type = "section"

            if (self.data_subtype == "title"
                and tag == "a"
                and len(attrs) > 0
                ):
                self.links[self.n] = 'www.cell.com' + attrs[0][1]

            if (self.data_type == "article"
                and tag == "span"
                and len(attrs) > 0
                and attrs[0][1] == "content"
                ):
                self.data_subtype = "description"
            
            if (self.data_type == "article"
                and tag == "div"
                and len(attrs) > 0
                and attrs[0][1] == "authors"
                ):
                self.data_subtype = "author"

        def handle_endtag(self, tag):
            if tag == "li":
                self.data_type = None
                self.data_subtype = None

            if (self.data_subtype == "title" 
                and tag == "a"):
                self.data_subtype = None

            if (self.data_subtype == "description" 
                and tag == "span"):
                self.data_subtype = None

        def handle_data(self, data):
            if self.data_type == "date":
                self.issue_date =  datetime.strptime(data.strip(), '%B %d, %Y').date()
                self.data_type = None

            if self.data_subtype == "title":
                self.titles[self.n] +=  data
                self.titles[self.n] = self.titles[self.n].strip()

            if self.data_subtype == "description":
                self.descriptions[self.n] += data.replace("\xa0", " ")

            if self.data_subtype == "author":
                self.authors[self.n].append(data)
                self.data_subtype = None

            if self.data_type == "section":
                self.section_type = data
                self.data_type = None