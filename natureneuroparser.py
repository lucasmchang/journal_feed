#This can parse Nature Neuroscience issues,
#and both Nature and Nature Neuroscience latest pre-print publications

from html.parser import HTMLParser
from datetime import datetime

class NatureNeuroParser(HTMLParser):
        def __init__(self):
            super(NatureNeuroParser, self).__init__()
            self.data_type = None #used temporarily to hold type of data being read
            self.data_subtype = None
            self.n = -1 #index of article being read
            self.issue_date = None
            self.titles = []
            self.authors = []
            self.descriptions = []
            self.links = []
            self.article_types = []
            self.warnings = ""

        def feed(self, data):
            super(NatureNeuroParser, self).feed(data)
            self.quality_check()

        def quality_check(self):
            #if not type(self.issue_date) is type(datetime(1,1,1).date()):
            #    raise NoDateError('No date for Nature Neuroscience')
            if len(self.titles) < 12:
                self.warnings += "Warning: found too few articles in Nature Neuroscience"
            if sum([x == [] for x in self.authors]) > len(self.titles)/2:
                self.warnings += "Warning: found many articles with no authors in Nature Neuroscience"
            if sum([x == '' for x in self.descriptions]) > len(self.titles)/2:
                self.warnings += "Warning: found many articles with no description in Nature Neuroscience"
            if sum([x == '' for x in self.links]) > 0:
                self.warnings += "Warning: could not find links to all articles in Nature Neuroscience"
            if len(set(self.article_types)) < 2:
                self.article_types = ["Article" for x in self.article_types]

        def handle_starttag(self, tag, attrs):
            if (tag == "h2" 
                and len(attrs)>0 
                and attrs[0] == ("class", "extra-tight-line-height")
                ):
                self.data_type = "date"

            if (tag == "article"):
                self.n += 1
                self.titles.append('')
                self.authors.append([])
                self.descriptions.append('')
                self.links.append('')
                self.data_type = "article"
                self.article_types.append(None)
            
            if (self.data_type == "article"
                and tag == "p"
                ):
                self.data_subtype = "description"

            if (self.data_type == "article"
                and tag == "a"
                and len(attrs) > 0
                ):
                self.links[self.n] = 'www.nature.com' + attrs[0][1]
                self.data_subtype = "title"
            
            if (self.data_type == "article"
                and tag == "span"
                and len(attrs) > 0
                and attrs[0][1] == "name"
                ):
                self.data_subtype = "author"

            if (self.data_type == "article"
                and tag == "span"
                and len(attrs) > 0
                and attrs[0] == ("data-test", "article.type")):
                self.data_subtype = "article_type"

        def handle_endtag(self, tag):
            if tag == "article":
                self.data_type = None
                self.data_subtype = None

            if (self.data_subtype == "title" 
                and tag == "a"):
                self.data_subtype = None

        def handle_data(self, data):
            if self.data_type == "date":
                self.issue_date =  datetime.strptime(data.split(',')[1].strip(), '%B %Y').date()
                self.data_type = None

            if self.data_subtype == "title":
                self.titles[self.n] +=  data
                self.titles[self.n] = self.titles[self.n].strip()

            if self.data_subtype == "description":
                self.descriptions[self.n] =  data
                self.data_subtype = None

            if self.data_subtype == "author":
                self.authors[self.n].append(data)
                self.data_subtype = None
            
            if self.data_subtype == "article_type":
                self.article_types[self.n] = data
                self.data_subtype = None