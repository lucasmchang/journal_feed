from html.parser import HTMLParser
from nodateerror import NoDateError
from datetime import datetime

class CurrentBioParser(HTMLParser):
        def __init__(self):
            super(CurrentBioParser, self).__init__()
            self.data_type = None #used temporarily to hold type of data being read
            self.data_subtype = None
            self.n = -1 #index of article being read
            self.issue_date = None
            self.titles = []
            self.authors = []
            self.descriptions = []
            self.links = []
            self.warnings = ""

        def feed(self, data):
            super(CurrentBioParser, self).feed(data)
            self.quality_check()

        def quality_check(self):
            if not type(self.issue_date) is type(datetime(1,1,1).date()):
                raise NoDateError('No date for Current Biology')
            if len(self.titles) < 12:
                self.warnings += "Warning: found too few articles in Current Biology"
            if sum([x == [] for x in self.authors]) > 6:
                self.warnings += "Warning: found many articles with no authors in Current Biology"
            if sum([x == '' for x in self.descriptions]) > 6:
                self.warnings += "Warning: found many articles with no description in Current Biology"
            if sum([x == '' for x in self.links]) > 0:
                self.warnings += "Warning: could not find links to all articles in Current Biology"

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
                self.links.append('')
                self.data_type = "article"
                self.data_subtype = "title"
            
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
