from datetime import datetime
import csv
import subprocess
import os
os.chdir(os.path.expanduser('~/Dropbox/Active/Other_stuff/IndependentProjects/journal_feed'))
from customweb import scrape
from cellparser import CellParser
from natureneuroparser import NatureNeuroParser
from pnasparser import PNASParser
from natureparser import NatureParser
from jneurosciparser import JNeurosciParser
import pandas as pd
from datetime import timedelta


recipients = [r[0] for r in csv.reader(open('recipients.csv', 'r'))]

site_urls = [
    'https://www.nature.com/nature/current_issue.html',
    'http://www.nature.com/nature/research',
    'https://www.nature.com/neuro/current-issue',
    'https://www.nature.com/neuro/research',
    'http://www.cell.com/neuron/current',
    'http://www.cell.com/neuron/newarticles',
    'http://www.cell.com/current-biology/current',
    'http://www.cell.com/current-biology/newarticles',
    'http://www.pnas.org/content/current',
    'http://www.jneurosci.org/content/current',
    'http://www.jneurosci.org/content/early/recent'
]

parsers = [
    NatureParser(),
    NatureNeuroParser(),
    NatureNeuroParser(),
    NatureNeuroParser(),
    CellParser(),
    CellParser(),
    CellParser(),
    CellParser(),
    PNASParser(),
    JNeurosciParser(),
    JNeurosciParser()
]

journal_names = [
    'Nature',
    'Nature',
    'Nature Neuroscience',
    'Nature Neuroscience',
    'Neuron',
    'Neuron',
    'Current Biology',
    'Current Biology',
    'PNAS',
    'Journal of Neuroscience',
    'Journal of Neuroscience'
]

error_report = ""

#parse each url and record any errors or warnings
for (url, parser) in zip(site_urls, parsers):
    try:
        source = scrape(url)
    except:
        error_report += url + " could not be reached\n"
    try:
        parser.feed(source)
    except:
        error_report += url + " could not be parsed\n"
        parser.issue_date = None
    finally:
        error_report += parser.warnings

###process the results of scraping the journals

#get list of articles
journal = []
article_type = []
title = []
authors = []
description = []
link = []
date = []

for (p, j) in zip(parsers, journal_names):
    n = len(p.titles)
    title += p.titles
    authors += [(', '.join(a) if type(a) == list else a) for a in p.authors]
    description += p.descriptions
    link += p.links
    article_type += p.article_types
    journal += [j for i in range(n)]
    date += [datetime.strftime(datetime.now().date(), "%d %B %Y") for i in range(n)]
articles = pd.DataFrame(
    {"journal": journal,
    "article_type": article_type,
    "title": title,
    "authors": authors,
    "description": description,
    "link": link,
    "date": date
    })

#get cached list
cache = pd.read_csv('cached_articles.csv').fillna('')

#drop articles with the same title and authors as cached articles
known_papers = [(
    t, 
    a.split(",")[0].split('and')[0].strip(), #first author
    l
    ) for t, a, l in zip(cache['title'], cache['authors'], cache['link'])]

drop_at = pd.Series([
    (t,a.split(",")[0].split('and')[0].strip()) in [(k[0], k[1]) for k in known_papers]
    or (t, l) in [(k[0], k[2]) for k in known_papers]
    for (t, a, l) in zip(articles['title'], articles['authors'], articles['link'])]).values
new_articles = articles[~drop_at]

#cache new articles
new_cache = pd.concat([new_articles, cache])
#drop old articles from cache
drop_at = pd.Series(
    [datetime.strptime(adate, "%d %B %Y").date() < datetime.now().date()-timedelta(days=40) for adate in new_cache['date']]
    ).values
new_cache = new_cache[~drop_at]

#write the new cache to csv
new_cache.to_csv('cached_articles.csv', index = False)

#get list of keyword-recipient pairs
keywords =[(r[0],recipients[int(r[1])]) for r in csv.reader(open('key_words.csv', 'r'))]
#{keyword,recipient_email}

def add_article_to_digest(digest, line, previous_journal):
    if not line['journal'] == previous_journal:
        digest += "\n\n" + line['journal'] + "\n\n"
    if line['article_type'] is not None:
        digest += '[' + line['article_type'].strip() + ']' + "\n"
        digest += line['title'] + "\n"
    if line['authors'] is not None and len(line['authors'].strip()) > 1:
        digest += line['authors'] + "\n"
    if line['description'] is not None and len(line['description'].strip()) > 1:
        digest += line['description'] + "\n"
    digest += line['link'] + "\n\n"
    previous_journal = line['journal']
    return digest, previous_journal

for email_address in recipients:
    #move new articles with keywords in watchlist to top
    watchlist = [r[0] for r in keywords if r[1] == email_address]
    title_in_watchlist = [any([w in t for w in watchlist]) for t in new_articles['title']] 
    description_in_watchlist = [any([w in t for w in watchlist]) for t in new_articles['description']] 
    author_in_watchlist = [any([w in t for w in watchlist]) for t in new_articles['authors']] 
    in_watchlist = [
        title_in_watchlist[i]
        or description_in_watchlist[i]
        or author_in_watchlist[i]
        for i in range(len(new_articles))
    ]
    num_flagged_articles = sum(in_watchlist)
    flagged_articles = new_articles[in_watchlist]
    #generate the digest from new articles
    contents = ""
    if num_flagged_articles:
        contents += "Articles containing your tracked keywords:" 
        previous_journal = None
        for index, line in flagged_articles.iterrows():
            contents, previous_journal = add_article_to_digest(
                contents, line, previous_journal
                )
        contents += "All articles:"
    previous_journal = None
    for index, line in new_articles.iterrows():
        contents, previous_journal = add_article_to_digest(
            contents, line, previous_journal
            )

    #send the email
    #don't send if no new articles today
    if contents == "":
        break
    #send the email
    mail_input = subprocess.Popen(('echo', contents), stdout=subprocess.PIPE)
    display_date = datetime.strftime(datetime.now().date(), "%d %B %Y")
    subprocess.check_output([
        'mail',
        '-s',
        'New articles for' + ' ' + display_date,
        email_address],
        stdin = mail_input.stdout)

#send the success report or warnings to Lucas
mail_input = subprocess.Popen(('echo', error_report), stdout=subprocess.PIPE)
subprocess.check_output([
    'mail',
    '-s',
    ("Journal Scraper Error Report" if len(error_report) > 0 else "Journal Scraper Success"),
    'lumochang@gmail.com'],
    stdin = mail_input.stdout)