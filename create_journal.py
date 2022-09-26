#!/usr/bin/env python3

# std library imports
from datetime import datetime as Datetime
import datetime
from copy import deepcopy
import json
from json import JSONDecodeError
from os import path
import re  # regex
import ssl
from socket import timeout
from typing import List
import urllib.request
from urllib.error import HTTPError, URLError


# stuff needed for parsing and manipulating XML
# this moduel does not come with python and needs to be installed with pip
from lxml import etree  # type: ignore
from lxml.etree import QName, Element, SubElement, iselement  # type: ignore
from lxml import html as lhtml

# local imports
try:
    import Python_Resources.tables as tables
except ModuleNotFoundError:
    from . import tables  # type: ignore

CONTEXT = ssl._create_unverified_context()

FILEEXTENSION = ".xml"

BASE_URL = "http://services.vnp.parliament.uk/voteitems"

# xml namespaces used
AID = "http://ns.adobe.com/AdobeInDesign/4.0/"
AID5 = "http://ns.adobe.com/AdobeInDesign/5.0/"

NS_ADOBE = {"aid": AID, "aid5": AID5}

ns2 = "http://www.w3.org/2001/XMLSchema-instance"
# ns1 = 'http://www.w3.org/2001/XMLSchema'

# Text before the following should get the speaker style
chair_titles = ("SPEAKER", "CHAIRMAN OF WAYS AND MEANS", "SPEAKER ELECT")


def main():
    # 2019 session
    # sitting_dates = get_sitting_dates_in_range(Datetime(2019, 10, 14), Datetime(2019, 11, 14))
    # 2020 session
    sitting_dates = get_sitting_dates_in_range(
        Datetime(2017, 9, 17), Datetime(2019, 10, 8)
    )
    sitting_dates = list(dict.fromkeys(sitting_dates))
    print(sitting_dates)

    # transform and combine a bunch of files.

    output_root = Element("root", nsmap=NS_ADOBE)

    for date in sitting_dates:
        # parse and build up a tree for the input file

        file_name = f'{date.strftime("%Y-%m-%d")}.xml'
        input_root = etree.parse(
            file_name
        ).getroot()  # LXML element object for the root

        temp_output_root = Element(
            "day", nsmap=NS_ADOBE, attrib={"date": date.strftime("%Y-%m-%d")}
        )

        # get all the VoteItemViewModel elements
        VoteItems = input_root.xpath(".//VoteItemViewModel")

        # put the vote number as an attribute into the root element
        # e.g. <root VnPNumber="No. 184">
        # input_root.find finds the first match. (The number is always first)
        first_VoteEntry = input_root.find("VoteItemViewModel/VoteEntry")
        if first_VoteEntry is not None and first_VoteEntry.text:
            # case insensitive search
            m = re.search(r"No\. ?[0-9]+", first_VoteEntry.text, flags=re.I)
            if m:
                temp_output_root.set("VnPNumber", m.group(0))

                DayLine = SubElement(temp_output_root, "DayLine")
                DayLine.tail = "\n"

                # delete this element so it wont go into the usual InDesign flow
                # first_VoteEntry.getparent().remove(first_VoteEntry)
                # actually keep it
                first_VoteEntry.text = f"[{m.group(0)}]"
                first_VoteEntry.tag = "NormalCentred"
                first_VoteEntry.tail = "\n"
                temp_output_root.append(first_VoteEntry)

            # insert date element
            date_ele = SubElement(temp_output_root, "VotesDate")
            date_ele.text = date.strftime("%A") + " "
            date_for_header = SubElement(date_ele, "DateForHeader")
            date_for_header.text = date.strftime("%d %B %Y").lstrip("0")
            date_ele.tail = "\n"

        # variable to contain the section
        last_section = "CHAMBER"
        restart_numbers = (
            False  # used to help tell if numbering should restart in InDesign
        )

        for vote_item in VoteItems:

            # If the section changes we need a new heading. There is not section heading needed for the chamber
            section_text = vote_item.findtext("Section")
            if section_text:
                section_text = section_text.strip()
                section_text_upper = section_text.upper()
                # There is also no heading needed for Certificates and Corrections
                if section_text_upper not in (
                    last_section,
                    "CERTIFICATES AND CORRECTIONS",
                ):
                    SubElement(temp_output_root, "OPHeading1").text = (
                        section_text + "\n"
                    )
                    last_section = section_text_upper
                    # The numbering is also supposed to restart after new sections
                    # unless section is other proceedings
                    if section_text_upper != "OTHER PROCEEDINGS":
                        restart_numbers = True

            # add a line to InDesign XML if vote Entry is 'FullLine'
            if vote_item.findtext("VoteEntryType") == "FullLine":
                SubElement(temp_output_root, "FullLine").text = " \n"
                continue

            # get the vote entry text
            vote_entry_text = vote_item.findtext("VoteEntry", default="")
            # convert vote entry text back to html and replace breaks with InDesign forced line breaks
            vote_entry_text = (
                vote_entry_text.replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
                .replace("<br />", "&#8232;")
            )
            # also remove any divs
            vote_entry_text = vote_entry_text.replace("<div>", "").replace("</div>", "")

            if len(vote_entry_text) > 0 and vote_entry_text[0] != "<":
                vote_entry_text = "<p>" + vote_entry_text + "</p>"
            cleaned_html_elements = lhtml.fromstring(
                "<div>" + vote_entry_text + "</div>"
            )

            for i, item in enumerate(cleaned_html_elements):
                next_item = item.getnext()  # returns the next element or None

                next_item_tag = ""
                next_item_text = ""
                if iselement(next_item):
                    next_item_tag = next_item.tag
                    if next_item.text:
                        next_item_text = next_item.text.strip()

                item_text = ""
                if item.text:
                    item_text = item.text.strip()

                # remove multiple new paragraphs, this sometimes happens after tables
                if (
                    item.tag == "p"
                    and next_item_tag == "p"
                    and item_text == "\u00A0"
                    and next_item_text == "\u00A0"
                ):
                    continue

                # if the element is an html tabe...
                if item.tag == "table":
                    # temp_output_root.append(convert_table(item))
                    indesign_table = tables.html_table_to_indesign(
                        item, tablestyle="Table Style 2", max_table_width=540
                    )
                    TableContainerPara = SubElement(
                        temp_output_root, "TableContainerPara"
                    )
                    TableContainerPara.append(indesign_table)
                    # if a tables first row has all cell have the <em> element then promote to header
                    try:
                        cols = int(indesign_table.get(QName(AID, "tcols")))

                        cells_that_should_be_headers = indesign_table.xpath(
                            f"Cell[position() <= {cols}][em]"
                        )
                        if len(cells_that_should_be_headers) == cols:
                            for cell in cells_that_should_be_headers:
                                cell.set(QName(AID, "theader"), "")
                    except ValueError:
                        pass

                    continue

                # get the style attribute if it exists
                item_style = item.get("style", "").rstrip(
                    ";"
                )  # somewitmes there is an unwadted `;`

                # decide what tag we need to give it
                number_ele = vote_item.find("Number")
                vote_entry_type = vote_item.find("VoteEntryType")
                if i == 0 and number_ele.text:
                    item.tag = "BusinessItemHeadingNumbered"
                    if restart_numbers is True:
                        item.tag = "BusinessItemHeadingNumberedRestart"
                        restart_numbers = False

                elif item.get("class", "") == "HalfLine":
                    item.tag = "HalfLine"

                # apply the special style to the speaker or chairs name
                elif (
                    item_style == "text-align: right"
                    and next_item_text.upper() in chair_titles
                ):
                    continue
                    # item.getparent().remove(item)
                    # item.tag = 'SpeakerName'

                # some elements are headings and take particular styles
                elif iselement(vote_entry_type) and vote_entry_type.text == "Heading":
                    item.tag = "OPHeading2"
                    if item_text.upper() in chair_titles:
                        continue
                        # item.getparent().remove(item)
                        # item.tag = 'RightAlign'
                    # put The House met at in the center
                    if re.search(r"^The House met at", item_text) is not None:
                        item.tag = "NormalCentred"
                    if item_text.upper() == "PRAYERS":
                        item.tag = "MotionText"

                elif item_style == "text-align: center":
                    item.tag = "NormalCentred"
                elif item_style == "text-align: right":
                    item.tag = "RightAlign"
                elif item_style == "padding-left: 30px":
                    item.tag = "Indent1"
                elif item_style == "padding-left: 60px":
                    item.tag = "Indent2"
                elif item_style == "padding-left: 90px":
                    item.tag = "Indent3"
                elif item_style == "padding-left: 120px":
                    item.tag = "Indent4"
                elif item_style == "padding-left: 150px":
                    item.tag = "Indent5"
                else:
                    item.tag = "MotionText"
                item.tail = "\n"
                temp_output_root.append(deepcopy(item))

            output_root.append(temp_output_root)

    # write out the file
    filename = "for_inDesign_Journal_XML"

    et = etree.ElementTree(output_root)

    et.write(
        filename + FILEEXTENSION, encoding="utf-8", xml_declaration=True
    )  # ,pretty_print=True
    print(
        "\nTransformed XML (for InDesign) is at:\n{}".format(
            path.abspath(filename + FILEEXTENSION)
        )
    )


def json_from_uri(uri: str, default=None, showerror=True):
    headers = {"Content-Type": "application/json"}
    request = urllib.request.Request(uri, headers=headers)
    try:
        response = urllib.request.urlopen(request, context=CONTEXT, timeout=30)
        json_obj = json.load(response)
    except (HTTPError, URLError, timeout, JSONDecodeError) as e:
        if showerror:
            print(f"Error getting data from:\n{uri}\n{e}")
        return default
    else:
        return json_obj


def get_sitting_dates_in_range(
    from_date: Datetime, to_date: Datetime
) -> List[Datetime]:
    """get return a list of sitting days"""

    # date
    cal_api_url_template = "http://service.calendar.parliament.uk/calendar/proceduraldates/commons/nextsittingdate.json?dateToCheck={}"

    # the calendar api gives you the next sitting day so we need to start form the day before
    start_date = from_date - datetime.timedelta(days=1)

    current_date = start_date
    dates = []
    count = 0
    while current_date < to_date:
        current_date = start_date + datetime.timedelta(days=count)
        dates.append(current_date)
        count += 1

    sitting_dates = []
    for date in dates:

        next_sitting_date_str = json_from_uri(
            cal_api_url_template.format(date.strftime("%Y-%m-%d"))
        )
        next_sitting_date = Datetime.strptime(next_sitting_date_str[:10], "%Y-%m-%d")
        sitting_dates.append(next_sitting_date)

    return sitting_dates


if __name__ == "__main__":
    main()
