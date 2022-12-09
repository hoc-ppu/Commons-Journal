#!/usr/bin/env python3

# Mark Fawcett
# fawcettm@parliament.uk
# Bugs should be expected and should be reported
# Ideas for improvement are welcome

# python standard library imports
# from copy import deepcopy
import argparse
from datetime import datetime, date
from functools import lru_cache
from pathlib import Path
import re
import ssl
import sys
from typing import cast, Optional
from os import path

import requests

from lxml import etree
from lxml.etree import _Element

# import urllib.request


NS_MAP = {'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
          'aid': 'http://ns.adobe.com/AdobeInDesign/4.0/',
          'aid5': 'http://ns.adobe.com/AdobeInDesign/5.0/'}

OUTPUT_XML_NAME = 'papers_for_indesign3.xml'

PAPER_IDS = set()  # use a set to contain all the paper Ids.

PAPERS_DATA: dict[str, dict[str, list]] = {}

PAPERS_INFO = [
    {'pattern': re.compile(r'Regulations$', flags=re.IGNORECASE),
        'base_key': 'Regulations: '},
    # {'pattern': re.compile(r'Regulations\(Northern Ireland\)$', flags=re.IGNORECASE),
    #     'base_key': 'Regulations (Northern Ireland): '},
    {'pattern': re.compile(r'Report of the Law Commission ',  flags=re.IGNORECASE),
        'base_key': 'Report of the Law Commission: '},
    {'pattern': re.compile(r'Order$', flags=re.IGNORECASE),
        'base_key': 'Order: '},
    {'pattern': re.compile(r'Order of Council$', flags=re.IGNORECASE),
        'base_key': 'Order of Council: '},
    {'pattern': re.compile(r'^Report and Accounts of ', flags=re.IGNORECASE),
        'base_key': 'Reports and Accounts, '},
    {'pattern': re.compile(r'^Accounts of ', flags=re.IGNORECASE),
        'base_key': 'Accounts, '},
    {'pattern': re.compile(r'^Account ', flags=re.IGNORECASE),
        'base_key': 'Account, '}
]

PLURALS = (
    ('^Order: ', 'Orders: '),
    ('^Draft Order: ', 'Draft Orders: ')
)


def main():

    parser = argparse.ArgumentParser(
        description="Download and process XML from papers laid to create InDesign XML for the papers index."
    )

    parser.add_argument("session", help="e.g. 2017-19")

    parser.add_argument(
        "--save-raw",
        action="store_true",
        help="Also save the raw XML",
    )

    parser.add_argument(
        "--process-local",
        type=open,
        help="Pass in a local file to process (rather than downloading form papers laid)",
    )

    args = parser.parse_args(sys.argv[1:])

    local_file = None
    if args.process_local:
        local_file = Path(args.process_local.name)

    process_papers(local_xml=local_file, session=args.session, save_raw_xml=args.save_raw)


def filter_papers(papers: list[_Element]) -> list[_Element]:
    papers_of_interest = []
    for paper in reversed(papers):
        # get the papers Id, ** I am assuming that these are unique to each paper **
        paper_id = paper.findtext('Id')

        if paper_id not in PAPER_IDS:
            PAPER_IDS.add(paper_id)
            papers_of_interest.append(paper)
    return papers_of_interest


def get_dates_from_session(session_code):
    """Return a tuple of start and end dates (as strings) of a session of parliament"""

    # Get the dates from API
    url = 'http://service.calendar.parliament.uk/calendar/sessions/list.json'
    response = requests.get(url)

    session_json = response.json()

    for session_obj in session_json:
        if session_obj['CommonsDescription'] == session_code:
            start_date = session_obj['StartDate']
            end_date = session_obj['EndDate']

            return(start_date[:10], end_date[:10])


def xml_from_papers_laid(session_code: str):
    """get the xml from the papers laid API"""

    # session code e.g. '2015-16'

    # dates of session of parliament
    session_dates = get_dates_from_session(session_code)

    url = ('http://services.paperslaid.parliament.uk/papers/list/daily.xml'
        f'?fromDate={session_dates[0]}&toDate={session_dates[1]}&house=commons')

    response = requests.get(url)

    return response


def process_papers(
    local_xml: Optional[Path] = None,
    session: Optional[str] = None,
    save_raw_xml = False):

    path_to_dir = ''

    # assume we want to save the output next to the input so get the location
    if local_xml:
        path_to_dir = local_xml.parent.absolute()
        papers_xml_tree = etree.parse(str(local_xml))
        papers_xml_root = papers_xml_tree.getroot()

    elif not session:
        print('Must have either an XML file or a session')
        return
    else:
        # download the XML first
        response = xml_from_papers_laid(session)

        if save_raw_xml:
            as_downloaded_file_name = f'as_downloaded_papers_{session}.xml'
            with open(as_downloaded_file_name, 'wb') as f:
                f.write(response.content)

        papers_xml_root = etree.fromstring(response.content)

    papers_xpath_result = papers_xml_root.xpath(
        # get all papers
        '/ArrayOfDailyPapers/DailyPapers/*/Paper'
        #  remove any not laid in the commons
        '[DateLaidCommons[text()]]',
        namespaces=NS_MAP
    )
    papers_xpath_result = cast(list[_Element], papers_xpath_result)

    papers_of_interest = filter_papers(papers_xpath_result)

    print(f'There are {len(papers_of_interest)} papers.')

    # regulations_str = 'Regulations'
    populate_papers_data(papers_of_interest)

    # create a root element for output XML
    output_root = etree.Element('root')


    for side_t in sorted(PAPERS_DATA.keys()):
        etree.SubElement(output_root, 'SideTitle').text = side_t

        entries_under_side_title = []

        for key, value in PAPERS_DATA[side_t].items():
            if key == 'papers':
                # papers is a special case
                entries_under_side_title += value
            elif len(value) > 0:
                value.sort()
                if len(value) > 1:
                    for plural in PLURALS:
                        key = re.sub(plural[0], plural[1], key)
                entries_under_side_title.append(f'{key}{"; ".join(value)}')

        # add all the entries to the XML
        for paper in sorted(entries_under_side_title):
            etree.SubElement(output_root, 'Paper').text = paper

    # for every element in output_root add a new line after
    for ele in output_root:
        ele.tail = '\n'

    # xml_file_path = path.join(path_to_dir, 'papers_for_indesign.xml')
    xml_file_Path = Path(path_to_dir, OUTPUT_XML_NAME)
    outputTree = etree.ElementTree(output_root)
    outputTree.write(xml_file_Path, encoding='UTF-8', xml_declaration=True)

    print(
        f'After combining there are {len(output_root.xpath("//Paper"))} entries.')


def populate_papers_data(papers_of_interest: list[_Element]):

    for paper in papers_of_interest:
        side_title = paper.findtext('SideTitle', default='').strip()
        title = paper.findtext('Title', default='').strip()
        date_laid = paper.findtext('DateLaidCommons', default='').strip()
        is_draft = paper.findtext('Draft', default='').strip()
        year = paper.findtext('Year', default='').strip()
        date_withdrawn = paper.findtext('DateWithdrawn', default='').strip()
        # papers don't always have a subject heading.
        subject_heading = paper.findtext('SubjectHeading', default='').strip()

        date_laid = process_date(date_laid)
        # if date_withdrawn: print(date_withdrawn)
        date_withdrawn = process_date(date_withdrawn)
        if date_withdrawn:
            date_withdrawn = f'[withdrawn, {date_withdrawn}]'
            # print(date_withdrawn)

        # paper_obj.setdefault(side_title, []).append()
        if side_title not in PAPERS_DATA:
            # PAPERS_DATA[side_title] = deepcopy(default_side_title_obj)
            PAPERS_DATA[side_title] = {}

        key = 'papers'  # key for standard paper
        for obj in PAPERS_INFO:
            match = re.search(r'(Regulations \(Northern Ireland\)) ([12]\d\d\d)', subject_heading)
            if match:
                key = f'{match.group(1)}: {match.group(2)}: '
                title = re.sub(r'Regulations \(Northern Ireland\)', '', title)
                break

            if not re.search(obj['pattern'], title):
                continue
                # this is a special paper

            # set the key up
            key = obj['base_key']
            if is_draft == 'true':
                key = 'Draft ' + key
            if year:
                # replace any hyphens in the year with the en-dash as that is typographically correct
                year = year.replace('-', '\u2013')
                key = f'{key}{year}: '  # key for special paper

            # amend the title
            title = re.sub(obj['pattern'], '', title).strip()

            # if the above matched we do not need to check anymore so break
            break

        # journal_title = title
        # if year:
        #     journal_title = f'{title} for {year}'
        paper_entry = f'{title}, {date_laid} {date_withdrawn}'.strip(', ')
        PAPERS_DATA[side_title].setdefault(key, []).append(paper_entry)


def process_date(date):
    if date and len(date) > 9:
        return datetime.strptime(
            date[0:10], '%Y-%m-%d').strftime('%d %b %Y').lstrip('0')
    return ''

@lru_cache
def get_next_sitting_date(date_: datetime) -> datetime:
    """Get next sitting day from whatson api"""

    url_template = "https://whatson-api.parliament.uk/calendar/proceduraldates/Commons/nextsittingdate.json?dateToCheck={}"

    url = url_template.format(date_.strftime("%Y-%m-%d"))

    response = requests.get(url)

    return datetime.strptime(response.json(), "%Y-%m-%dT%H:%M:%S")


if __name__ == "__main__":
    main()
