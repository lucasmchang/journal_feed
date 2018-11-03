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

        if (tag == "title"
            and self.n == -1
            ):
            self.data_type = "date"

        if (tag == "span"
            and len(attrs) > 0
            and attrs[0] == ("data-test", "article.type")
            and self.data_type == "article"
            ):
            self.data_subtype = "section"

        if (tag == "article"):
            self.n += 1
            self.titles.append('')
            self.authors.append([])
            self.descriptions.append('')
            self.links.append('')
            self.article_types.append('')
            self.data_type = "article"
        
    
        if (self.data_type == "article"
            and tag == "a"
            and len(attrs)>0
            and attrs[0][0] == "href"
            ):
            link = attrs[0][1]
            if not link.startswith('http://www.nature.com/'):
                link = 'http://www.nature.com/' + link
            self.links[self.n] = link
            self.data_subtype = "title"

        if (self.data_type == "article"
            and tag == "div"
            and len(attrs) > 1
            and attrs[1][1] == "description"
            ):
            self.data_subtype = "description"
        
        if (self.data_type == "article"
            and tag == "ul"
            and len(attrs)>0
            and attrs[0] == ("data-test", "author-list")
            ):
            self.data_subtype = "authors"

    def handle_endtag(self, tag):
        if tag == "article" and self.data_type == "article":
            self.data_type = None
        if tag == "title" and self.data_type == "date":
            self.data_type = None
            self.data_subtype = None
        if tag == "p" and self.data_subtype == "description":
            self.data_subtype = None
        if tag == "a" and self.data_subtype == "title":
            self.data_subtype = None
        if tag == "ul" and self.data_subtype == "authors":
            self.data_subtype = None
        if tag == "span" and self.data_type == "section":
            self.data_type = None
     
    def handle_data(self, data):
        if self.data_type == "date":
            date_str = data.split(",")[1].strip()
            self.issue_date = datetime.strptime(date_str, '%d %B %Y').date()
            self.data_type = None
        if self.data_type == "article":
            if self.data_subtype == "title":
                if len(self.titles[self.n]) > 1:
                    self.titles[self.n] += " "
                self.titles[self.n] += data.replace("\n", "").replace("\t", "").strip()
            if self.data_subtype == "description":
                if len(self.descriptions[self.n]) > 1:
                    self.descriptions[self.n] += " "
                self.descriptions[self.n] += data.replace("\n", "").replace("\t", "").strip()
            if self.data_subtype == "authors" and len(data) >= 2: 
                self.authors[self.n].append(data.strip())
            if self.data_type == "section":
                self.article_types[self.n] = data
