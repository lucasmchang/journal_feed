from html.parser import HTMLParser
from datetime import datetime

class ScienceParser(HTMLParser):
    def __init__(self):
        super(ScienceParser, self).__init__()
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
        super(ScienceParser, self).feed(data)
        self.quality_check()

    def quality_check(self):
        #if not type(self.issue_date) is type(datetime(1,1,1).date()):
        #    raise NoDateError('No date for Neuron')
        if len(self.titles) < 4:
            self.warnings += "Warning: found too few articles in Science"
        if sum([x == [] for x in self.authors]) > 7:
            self.warnings += "Warning: found many articles with no authors in Science"
        if sum([x == '' for x in self.descriptions]) >= self.n - 2  and self.issue_date is not None:
            #no description is ok for early articles
            self.warnings += "Warning: found many articles with no description in Science"
        if sum([x == '' for x in self.links]) > 0:
            self.warnings += "Warning: could not find links to all articles in Science"
        if len(set(self.article_types)) < 2:
            self.article_types = ["Article" for x in self.article_types]

    def handle_starttag(self, tag, attrs):
        ####################################3
        if (tag == "div" 
            and len(attrs)>0 
            and attrs[0][1].startswith("beta section-title")
            ):
            self.data_type = "date"

        if (tag == "h3" 
            and len(attrs)>0
            and attrs[0][1].startswith("highwire-cite-title-wrapper")
            ):
            self.n += 1
            self.titles.append('')
            self.authors.append([])
            self.descriptions.append('')
            self.article_types.append(self.section_type)
            self.links.append('')
            self.data_type = "article"
            self.data_subtype = "link"
        
        if (tag == "h2" 
            and len(attrs)>1
            and attrs[1][1].startswith("toc-heading")
            ):
            self.data_type = "section"

        if (self.data_subtype == "link"
            and tag == "a"
            and len(attrs) > 0
            ):
            self.links[self.n] = 'science.sciencemag.org' + attrs[0][1]

        if (self.data_type == "article"
            and tag == "div"
            and len(attrs) > 0
            and (
                attrs[0][1].startswith("highwire-cite-title") or
                attrs[0][1].startswith("highwire-cite-subtitle")
                )
            ):
            self.data_subtype = "title"

        if (self.data_type == "article"
            and tag == "div"
            and len(attrs) > 0
            and attrs[0][1].startswith("highwire-cite-snippet")
            ):
            self.data_subtype = "description"
        
        if (self.data_type == "article"
            and tag == "span"
            and len(attrs) > 0
            and attrs[0][1].startswith("highwire-citation-author")
            ):
            self.data_subtype = "author"

    def handle_endtag(self, tag):
        if tag == "h2":
            self.data_type = None
            self.data_subtype = None

        if tag == "a":
            self.data_subtype = None

        if (self.data_subtype in ["author", "description"]
            and tag == "p"):
            self.data_subtype = None

    def handle_data(self, data):
        if self.data_type == "date":
            self.issue_date =  datetime.strptime(data.strip(), '%d %B %Y').date()
            self.data_type = None

        if self.data_subtype == "title":
            self.titles[self.n] +=  data.replace('"', '')

        if self.data_subtype == "description":
            if self.descriptions[self.n] == '':
                self.descriptions[self.n] = data.strip()
            else:
                self.descriptions[self.n] += ' ' + data

        if self.data_subtype == "author":
            self.authors[self.n].append(data)
            self.data_subtype = None

        if self.data_type == "section":
            if data.startswith("This Week"):
                data = "This Week in Science"
            self.section_type = data.strip()
            self.data_type = None