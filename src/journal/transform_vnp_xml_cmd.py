#!/usr/local/bin/python3

# std library imports
from datetime import datetime
from copy import deepcopy
import html
from os import path
import re  # regex
import sys
from typing import List


# stuff needed for parsing and manipulating XML
# this moduel does not come with python and needs to be installed with pip
from lxml import etree  # type: ignore
from lxml.etree import QName, Element, SubElement, iselement  # type: ignore
from lxml import html as lhtml

# local imports
try:
    import tables
except ModuleNotFoundError:
    from . import tables

# some variables used throughout
FILEEXTENSION = '.xml'

BASE_URL = 'http://services.vnp.parliament.uk/voteitems'

# xml namespaces used
AID = 'http://ns.adobe.com/AdobeInDesign/4.0/'
AID5 = 'http://ns.adobe.com/AdobeInDesign/5.0/'

NS_ADOBE = {'aid': AID, 'aid5': AID5}

ns2 = 'http://www.w3.org/2001/XMLSchema-instance'
# ns1 = 'http://www.w3.org/2001/XMLSchema'

# Text before the following should get the speaker style
chair_titles = ('SPEAKER', 'CHAIRMAN OF WAYS AND MEANS', 'SPEAKER ELECT')


def transform_xml_from_dates(dates: List[datetime], working_folder=None, sitting_date=None):

    urls: List[str] = []
    for date in dates:
        urls.append(f'{BASE_URL}/{date.strftime("%Y-%m-%d")}')

    # create an output root element
    output_root = Element('root', nsmap=NS_ADOBE)

    for url in urls:
        # parse and build up a tree for the input file
        input_root = etree.parse(url).getroot()  # LXML element object for the root

        temp_output_root = Element('day', nsmap=NS_ADOBE)
        # get all the VoteItemViewModel elements
        VoteItems = input_root.xpath('.//VoteItemViewModel')

        # put the vote number as an attribute into the root element
        # e.g. <root VnPNumber="No. 184">
        # input_root.find finds the first match. (The number is always first)
        first_VoteEntry = input_root.find('VoteItemViewModel/VoteEntry')
        if first_VoteEntry is not None and first_VoteEntry.text:
            # case insensitive search
            m = re.search(r'No\. ?[0-9]+', first_VoteEntry.text, flags=re.I)
            if m:
                temp_output_root.set('VnPNumber', m.group(0))
                # delete this element so it wont go into the usual InDesign flow
                first_VoteEntry.getparent().remove(first_VoteEntry)

        # variable to contain the section
        last_section = 'CHAMBER'
        restart_numbers = False  # used to help tell if numbering should restart in InDesign

        for vote_item in VoteItems:

            # If the section changes we need a new heading. There is not section heading needed for the chamber
            section_text = vote_item.findtext('Section')
            if section_text:
                section_text = section_text.strip()
                section_text_upper = section_text.upper()
                # There is also no heading needed for Certificates and Corrections
                if section_text_upper not in (last_section, 'CERTIFICATES AND CORRECTIONS'):
                    SubElement(temp_output_root, 'OPHeading1').text = section_text + '\n'
                    last_section = section_text_upper
                    # The numbering is also supposed to restart after new sections
                    # unless section is other proceedings
                    if section_text_upper != 'OTHER PROCEEDINGS':
                        restart_numbers = True

            # add a line to InDesign XML if vote Entry is 'FullLine'
            if vote_item.findtext('VoteEntryType') == 'FullLine':
                SubElement(temp_output_root, 'FullLine').text = ' \n'
                continue

            # get the vote entry text
            vote_entry_text = vote_item.findtext('VoteEntry', default='')
            # convert vote entry text back to html and replace breaks with InDesign forced line breaks
            vote_entry_text = vote_entry_text.replace('&lt;', '<').replace(
                '&gt;', '>').replace('&amp;', '&').replace('<br />', '&#8232;')
            # also remove any divs
            vote_entry_text = vote_entry_text.replace('<div>', '').replace('</div>', '')

            if len(vote_entry_text) > 0 and vote_entry_text[0] != '<':
                vote_entry_text = '<p>' + vote_entry_text + '</p>'
            cleaned_html_elements = lhtml.fromstring('<div>' + vote_entry_text + '</div>')

            for i, item in enumerate(cleaned_html_elements):
                next_item = item.getnext()  # returns the next element or None

                next_item_tag = ''
                next_item_text = ''
                if iselement(next_item):
                    next_item_tag = next_item.tag
                    if next_item.text:
                        next_item_text = next_item.text.strip()

                item_text = ''
                if item.text:
                    item_text = item.text.strip()

                # remove multiple new paragraphs, this sometimes happens after tables
                if item.tag == 'p' and next_item_tag == 'p' and item_text == "\u00A0" and next_item_text == "\u00A0":
                    continue

                # if the element is an html tabe...
                if item.tag == 'table':
                    # temp_output_root.append(convert_table(item))
                    indesign_table = tables.html_table_to_indesign(item, tablestyle='StandardTable',
                                                                   max_table_width=420)
                    temp_output_root.append(indesign_table)
                    continue

                # get the style attribute if it exists
                item_style = item.get('style', '').rstrip(';')  # somewitmes there is an unwadted `;`

                # decide what tag we need to give it
                number_ele = vote_item.find('Number')
                vote_entry_type = vote_item.find('VoteEntryType')
                if i == 0 and number_ele.text:
                    item.tag = 'BusinessItemHeadingNumbered'
                    if restart_numbers is True:
                        item.tag = 'BusinessItemHeadingNumberedRestart'
                        restart_numbers = False

                elif item.get('class', '') == 'HalfLine':
                    item.tag = 'HalfLine'

                # apply the special style to the speaker or chairs name
                elif item_style == 'text-align: right' and next_item_text.upper() in chair_titles:
                    item.tag = 'SpeakerName'

                # some elements are headings and take particular styles
                elif iselement(vote_entry_type) and vote_entry_type.text == 'Heading':
                    item.tag = 'OPHeading2'
                    if item_text.upper() in chair_titles:
                        item.tag = 'RightAlign'
                    # put The House met at in the center
                    if re.search(r'^The House met at', item_text) is not None:
                        item.tag = 'NormalCentred'
                    if item_text.upper() == 'PRAYERS':
                        item.tag = 'MotionText'

                elif item_style == 'text-align: center': item.tag = 'NormalCentred'
                elif item_style == 'text-align: right':  item.tag = 'RightAlign'
                elif item_style == 'padding-left: 30px': item.tag = 'Indent1'
                elif item_style == 'padding-left: 60px': item.tag = 'Indent2'
                elif item_style == 'padding-left: 90px': item.tag = 'Indent3'
                elif item_style == 'padding-left: 120px': item.tag = 'Indent4'
                elif item_style == 'padding-left: 150px': item.tag = 'Indent5'
                else: item.tag = 'MotionText'
                item.tail = '\n'
                temp_output_root.append(deepcopy(item))

            output_root.append(temp_output_root)




    # write out the file
    if sitting_date is not None:
        filename = 'for_inDesign_VnP_XML_{}'.format(sitting_date)
    else:
        filename = 'for_inDesign_VnP_XML'

    et = etree.ElementTree(output_root)

    et.write(filename + FILEEXTENSION, encoding='utf-8', xml_declaration=True)  # , pretty_print=True
    print('\nTransformed XML (for InDesign) is at:\n{}'.format(path.abspath(filename + FILEEXTENSION)))
    # outputfile = open(filepath, 'w')



def main():
    if len(sys.argv) != 2:
        print("\nThis script takes 1 argument. The path to the file you wish to process.\n",)
        exit()

    infilename = sys.argv[1]
    try:
        print('\nInput file is located at: ' + path.abspath(infilename))
    except:
        print('Input: ' + infilename)
    transform_xml(infilename)
    print('\nAll Done Chum!')


if __name__ == "__main__": main()
