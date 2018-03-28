from datetime import datetime
import csv
import subprocess
import os
import sys
sys.path.append(os.path.expanduser('~/Dropbox/Active/Other_stuff/IndependentProjects/journal_feed'))
from customweb import scrape
from neuronparser import NeuronParser
from natureneuroparser import NatureNeuroParser
from currentbioparser import CurrentBioParser
from pnasparser import PNASParser
from natureparser import NatureParser
from jneurosciparser import JNeurosciParser
from nodateerror import NoDateError

os.chdir(os.path.expanduser('~/Dropbox/Active/Other_stuff/IndependentProjects/journal_feed'))
recipients = [r[0] for r in csv.reader(open('recipients.csv', 'r'))]

site_urls = [
    'https://www.nature.com/nature/current_issue.html',
    'https://www.nature.com/neuro/current-issue',
    'http://www.cell.com/neuron/current',
    'http://www.cell.com/current-biology/current',
    'http://www.pnas.org/content/current',
    'http://www.jneurosci.org/content/current'
]
parsers = [
    NatureParser(),
    NatureNeuroParser(),
    NeuronParser(),
    CurrentBioParser(),
    PNASParser(),
    JNeurosciParser()
]

journal_names = [
    'Nature',
    'Nature Neuroscience',
    'Neuron',
    'Current Biology',
    'PNAS',
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
    except NoDateError:
        error_report += "Could not find date on " + url + "\n"
    except:
        error_report += url + " could not be parsed\n"
        parser.issue_date = None
    finally:
        error_report += parser.warnings

#check issue dates against known issues
known_dates = [
    datetime(int(r[1]), int(r[2]), int(r[3])).date() 
    for r in csv.reader(open('latest_issues.csv', 'r'))
    ]
scraped_dates = [p.issue_date for p in parsers]
new_issues = [s is not None and not k == s for k,s, in zip(known_dates, scraped_dates)]

#update issue dates
with open('latest_issues.csv', 'w') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    for p, n, k in zip(parsers, journal_names, known_dates):
        if p.issue_date is not None:
            writer.writerow([
                n,
                p.issue_date.year,
                p.issue_date.month,
                p.issue_date.day]
                )
        else:
            #couldn't find a date for this journal, so write date of last successful read
            writer.writerow([
                n,
                k.year,
                k.month,
                k.day]
                )

#generate the digest
for p, n, is_new in zip(parsers, journal_names, new_issues):
    if not is_new:
        continue
    contents = (
        n + ' '
        + datetime.strftime(p.issue_date, "%d %B %Y")
        + "\n\n"
    )
    for t, l, d, a in zip(p.titles, p.links, p.descriptions, p.authors):
        contents += t.strip().replace("\t", "") + ("\n" if len(t) > 0 else "")
        contents += (
            (', '.join(a) if type(a) == list else a) 
            + ("\n" if len(a) > 0 else ""))
        contents += d.strip().replace("\t", "") + ("\n" if len(d) > 0 else "")
        contents += l + ("\n" if len(l) > 0 else "")
        contents += "\n"

    #send the email
    for email_address in recipients:
        mail_input = subprocess.Popen(('echo', contents), stdout=subprocess.PIPE)
        if p.issue_date.day == 1 and datetime.now().day > 2 and p.issue_date.month == datetime.now().month:
            #we are using the 1st as a placeholder date, so send today's date instead
            display_date = datetime.strftime(datetime.now().date(), "%d %B %Y")
        else:
            display_date = datetime.strftime(p.issue_date, "%d %B %Y")
        subprocess.check_output([
            'mail',
            '-s',
            n + ' ' + display_date,
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