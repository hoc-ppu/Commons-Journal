#!/usr/local/bin/python3

# Mark Fawcett
# fawcettm@parliament.uk
# Bugs should be expected and should be reported
# Ideas for improvement are welcome

# python standard library imports
# from copy import deepcopy
import datetime
import re
import ssl
import sys
from os import path

from lxml import etree
from openpyxl import Workbook

# import urllib.request


NS_MAP = {'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
          'aid': 'http://ns.adobe.com/AdobeInDesign/4.0/',
          'aid5': 'http://ns.adobe.com/AdobeInDesign/5.0/'}


def main():
    if len(sys.argv) < 2:
        print('This script takes one argument. The path to the xml file (downloaded from papers laid) that you wish to process')
        exit()

    # pass the script's first argument to the function
    process_papers(sys.argv[1])


def process_papers(papers_xml):

    # assume we want to save the output next to the input so get the location
    path_to_dir = path.dirname(path.abspath(papers_xml))

    papers_xml_tree = etree.parse(papers_xml)
    papers_xml = papers_xml_tree.getroot()

    papers_xpath_result = papers_xml.xpath(
        # get all papers
        '/ArrayOfDailyPapers/DailyPapers/*/Paper'
        #  remove any not laid in the commons
        '[DateLaidCommons[text()]]',
        namespaces=NS_MAP
    )

    # use a set to contain all the paper Ids. Sets are as in maths -- unique members
    paper_ids = set()
    papers_of_intrest = []

    # need to reverse the list of papers as we are more interested in the most recent papers
    for paper in reversed(papers_xpath_result):

        # get the papers Id, ** I am assuming that these are unique to each paper **
        paper_id = paper.findtext('Id')

        if paper_id not in paper_ids:
            paper_ids.add(paper_id)
            papers_of_intrest.append(paper)

    print(f'There are {len(papers_of_intrest)} papers.')

    # regulations_str = 'Regulations'

    papers_obj = {}

    papers_info = [
        {'pattern': re.compile(r'Regulations$', flags=re.IGNORECASE),
         'base_key': 'Regulations: '},
        {'pattern': re.compile(r'Order$', flags=re.IGNORECASE),
         'base_key': 'Order: '},
        {'pattern': re.compile(r'^Report and Accounts of ', flags=re.IGNORECASE),
         'base_key': 'Reports and Accounts, '},
        {'pattern': re.compile(r'^Accounts of ', flags=re.IGNORECASE),
         'base_key': 'Accounts, '}
    ]

    plurals = (
        ('^Order: ', 'Orders: '),
        ('^Draft Order: ', 'Draft Orders: ')
    )

    for paper in papers_of_intrest:
        side_title = paper.findtext('SideTitle').strip()
        title = paper.findtext('Title').strip()
        date_laid = paper.findtext('DateLaidCommons')
        is_draft = paper.findtext('Draft')
        year = paper.findtext('Year')
        # some papers are withdrawn
        date_withdrawn = paper.findtext('DateWithdrawn')

        date_laid = process_date(date_laid)
        # if date_withdrawn: print(date_withdrawn)
        date_withdrawn = process_date(date_withdrawn)
        if date_withdrawn:
            date_withdrawn = f'[withdrawn, {date_withdrawn}]'
            # print(date_withdrawn)

        # paper_obj.setdefault(side_title, []).append()
        if side_title not in papers_obj:
            # papers_obj[side_title] = deepcopy(default_side_title_obj)
            papers_obj[side_title] = {}

        special_paper = False
        for obj in papers_info:
            if re.search(obj['pattern'], title):
                # this is a special paper
                special_paper = True

                # set the key up
                key = obj['base_key']
                if is_draft == 'true':
                    key = 'Draft ' + key
                if year:
                    # replace any hypens in the year with the en-dash as that is typographically correct
                    key = key + year.replace('-', '\u2013') + ': '

                # ammend the title
                title = re.sub(obj['pattern'], '', title).strip()

                # if the above matched we do not need to check anymore so break
                break
        if not special_paper:
            # must be a standard paper
            key = 'papers'

        paper_entry = f'{title}, {date_laid} {date_withdrawn}'.strip(', ')
        papers_obj[side_title].setdefault(key, []).append(paper_entry)

    # create a root element for output XML
    output_root = etree.Element('root')

    # create a new excel workbook
    wb = Workbook()
    ws = wb.active
    ws.append(['Entry', 'Side Title'])

    for side_t in sorted(papers_obj.keys()):
        etree.SubElement(output_root, 'SideTitle').text = side_t

        entries_under_side_title = []

        for key, value in papers_obj[side_t].items():
            if key == 'papers':
                # papers is a special case
                entries_under_side_title += value
            elif len(value) > 0:
                value.sort()
                if len(value) > 1:
                    for plural in plurals:
                        key = re.sub(plural[0], plural[1], key)
                entries_under_side_title.append(f'{key}{"; ".join(value)}')

        # add all the entries to the XML
        for paper in sorted(entries_under_side_title):
            etree.SubElement(output_root, 'Paper').text = paper
            # also add all the entries to excel
            ws.append([paper, side_t])

    # for every element in output_root add a new line after
    for ele in output_root:
        ele.tail = '\n'

    xml_file_path = path.join(path_to_dir, 'papers_for_indesign.xml')
    outputTree = etree.ElementTree(output_root)
    outputTree.write(xml_file_path, encoding='UTF-8', xml_declaration=True)

    # save the workbook
    excel_file_path = path.join(path_to_dir, 'processed_papers_data.xlsx')
    wb.save(filename=excel_file_path)
    print(f'Excel file saved at: {excel_file_path}')

    print(
        f'After combining there are {len(output_root.xpath("//Paper"))} entires.')


def process_date(date):
    if date and len(date) > 9:
        return datetime.datetime.strptime(
            date[0:10], '%Y-%m-%d').strftime('%d %b %Y').lstrip('0')
    return ''


if __name__ == "__main__":
    main()
