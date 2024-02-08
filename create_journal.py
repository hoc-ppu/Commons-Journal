#!/usr/bin/env python3

# std library imports
import re  # regex
import ssl
import sys
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import date, datetime, timedelta
from os import path
from pathlib import Path
from socket import timeout
from typing import (Any, Dict, Iterable, List, Optional, Tuple, TypeVar, Union,
                    cast)

# 3rd party imports
import click
import requests
from lxml import etree
from lxml import html as lhtml
from lxml.etree import Element, QName, SubElement, _Element, iselement
from requests import Response

# 1st party imports
from package.utilities import get_dates_from_session

# local imports
try:
    import Python_Resources.tables as tables
except ModuleNotFoundError:
    from . import tables  # type: ignore

T = TypeVar("T")

CONTEXT = ssl._create_unverified_context()

DEFAULT_OUTPUT_FILENAME = "output.xml"
DEFAULT_RAW_XML_FOLDER = "datedJournalFragments"

BASE_URL = "http://services.vnp.parliament.uk/voteitems"

CAL_API_URL_TEMPLATE = "https://whatson-api.parliament.uk/calendar/proceduraldates/commons/nextsittingdate.json?dateToCheck={}&includeWeekendSittings=true"

# xml namespaces used
AID = "http://ns.adobe.com/AdobeInDesign/4.0/"
AID5 = "http://ns.adobe.com/AdobeInDesign/5.0/"

NS_ADOBE: Dict[str, str] = {"aid": AID, "aid5": AID5}

ns2 = "http://www.w3.org/2001/XMLSchema-instance"
# ns1 = 'http://www.w3.org/2001/XMLSchema'

# Text before the following should get the speaker style
chair_titles = ("SPEAKER", "CHAIRMAN OF WAYS AND MEANS", "SPEAKER ELECT")

speaker_certificates = ("speaker's certificate", "speaker’s certificate",
                        "speaker’s certificates", "speaker's certificates")



# -------------------- Begin comand line interface ------------------- #


@click.group()
def cli():
    """To get XML for the journal from the VnP API use from-api subcomand.
    If you have all the XML for each day in the Journal saved in a folder use
    the from-folder subcomand. You can get additional help by typing --help
    after the subcommands, e.g. create_journal.py from-api --help"""
    pass


@cli.command()
@click.argument(
    "input_path",
    type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path),
)
@click.option(
    "--output",
    "-o",
    help=(
        "Optionally provide the file path for the output XML (for InDesign)."
        f" default={DEFAULT_OUTPUT_FILENAME}"
    ),
    type=click.Path(writable=True, path_type=Path),
)
def from_folder(input_path: Path, output: Optional[Path] = None):
    """Create papers index XML from raw XML files stored in a folder INPUT_PATH
    already on your computer.

    INPUT_PATH is the file path to the folder containing the individual VnP XML
    files

    Each file within INPUT_PATH must contain one day of VnP data and must be
    named with the VnP date in the form YYY-MM-DD.
    If you have not already downloaded VnP XML files, use the from-api
    subcomand instead.
    """
    sys.exit(main(raw_xml_dir=input_path, save_raw=False, output_file=output))


@cli.command()
@click.argument("session")
@click.option(
    "--discard-raw-xml",
    is_flag=True,
    default=False,
    help="Use this option to suppress saving the raw XML downloaded from the API",
)
@click.option(
    "--raw-xml-folder",
    type=click.Path(writable=True, dir_okay=True, file_okay=False),
    help="Use this option to specify the folder for the raw XML to be saved in"
    f"default={DEFAULT_RAW_XML_FOLDER}",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(writable=True, path_type=Path),
    help="Use this option to specify the folder for the raw XML to be saved in"
    f" default={DEFAULT_RAW_XML_FOLDER}",
)
def from_api(
    session: str,
    discard_raw_xml: bool,
    raw_xml_folder: Optional[Path],
    output: Union[Path, None] = None,
):
    """For a given SESSION, create the body of the commons journal
    (to be typeset in InDesign) from data downloaded from the vnp API.

    SESSION is a parliamentary session and should entered in the form YYYY-YY.
    E.g. 2017-19.

    By default the XML downloaded from vnp will be saved alongside the
    output. You can stop this behaviour with the --discard-raw-xml flag.

    You will need to be connected to the parliament network.
    For a list of parliamentary sessions check:
    https://whatson-api.parliament.uk/calendar/sessions/list.json
    """
    sys.exit(
        main(
            session=session,
            save_raw=not (discard_raw_xml),
            raw_xml_dir=raw_xml_folder,
            output_file=output,
        )
    )


# --------------------- End comand line interface -------------------- #


def request_vnp_data(
    sitting_date: datetime,
    save_to_disk: bool = True,
    save_to_folder: Path = Path(DEFAULT_RAW_XML_FOLDER)
) -> Tuple[requests.Response, datetime]:

    """Query the VnP API for papers laid in the date range."""

    formatted_sitting_date = sitting_date.strftime("%Y-%m-%d")

    url = f'{BASE_URL}/{formatted_sitting_date}.xml'

    response = requests.get(url)

    if save_to_disk:
        file_path = save_to_folder.joinpath(f"{formatted_sitting_date}.xml")
        with open(file_path, "wb") as f:
            f.write(response.content)

    return response, sitting_date


def progress_bar(iterable: Iterable, total: int) -> list:
    output = []
    count = 0
    bar_len = 50
    for item in iterable:
        output.append(item)
        count += 1
        filled_len = int(round(bar_len * count / total))
        percents = round(100.0 * count / total, 1)
        bar = "#" * filled_len + "-" * (bar_len - filled_len)
        sys.stdout.write(f"[{bar}] {percents}%\r")
        sys.stdout.flush()

    return output


def xml_sort_helper(item):
    # item can either be a path or a tuple [Response, datetime]
    # in either cased we want to sort by date
    if isinstance(item, Path):
        return item.name
    else:
        return item[1].strftime('%Y-%m-%d')

def main(
    session: Optional[str] = None,
    save_raw: bool = True,
    raw_xml_dir: Optional[Path] = None,
    output_file: Optional[Path] = None,
) -> int:

    print("main")

    if raw_xml_dir is not None:
        # Do not query API
        # insted assume path is dir with vnp xml files.
        # Each filename should be the date

        glob = raw_xml_dir.glob("*.xml")
        files_or_responses: List[Union[Tuple[Response, datetime], Path]] = list(glob)

    elif session is not None:
        try:
            # first get the dates for the session
            print("Getting session data")

            session_start, session_end = get_dates_from_session(session)

            print(f"Session starts: {session_start.strftime('%y-%m-%d')}.")
            print(f"Session ends: {session_end.strftime('%y-%m-%d')}.")

            sitting_dates = get_sitting_dates_in_range(session_start, session_end)
            print(f"There are {len(sitting_dates)} sitting days this session.")

        except Exception as e:
            print(repr(e))
            print("Error: Could not get session data from whats on.")
            return 1
        try:
            # Query papers VnP API
            print("Getting data from VnP API.")
            # query concurrently to save time
            with ThreadPoolExecutor(max_workers=8) as pool:

                # create a progress bar and return a list
                files_or_responses = progress_bar(
                    pool.map(
                        lambda sitting_date: request_vnp_data(sitting_date, save_raw),
                        sitting_dates,
                    ),
                    len(sitting_dates),
                )
                print()  # newline after progress bar

        except Exception as e:
            print(e)
            print(
                "\nCould not get XML from the VnP API. "
                "Check that you are connected to the parliament network."
            )
            return 1

    else:
        return 1

    # transform and combine a bunch of files.

    output_root = Element("root", nsmap=NS_ADOBE)

    # sort the VnP XML by date
    files_or_responses.sort(key=xml_sort_helper)


    for i, item in enumerate(files_or_responses):
        # parse and build up a tree for the input file

        if isinstance(item, Path):
            date = datetime.strptime(item.name[:10], "%Y-%m-%d")
            tree = etree.parse(str(item))
            input_root = tree.getroot()
        else:
            # assume tuple
            date = item[1]
            response = item[0]
            input_root = etree.fromstring(response.content)
            tree = etree.ElementTree(input_root)

        temp_output_root = Element(
            "day", nsmap=NS_ADOBE, attrib={"date": date.strftime("%Y-%m-%d")}
        )

        # get all the VoteItemViewModel elements
        VoteItems = input_root.xpath(".//VoteItemViewModel")
        VoteItems = cast(List[_Element], VoteItems)

        # put the vote number as an attribute into the root element
        # e.g. <root VnPNumber="No. 184">
        # input_root.find finds the first match. (The number is always first)
        first_VoteEntry = input_root.find("VoteItemViewModel/VoteEntry")
        if first_VoteEntry is not None and first_VoteEntry.text:
            # case insensitive search
            m = re.search(r"No\. ?[0-9]+", first_VoteEntry.text, flags=re.I)
            if m:
                temp_output_root.set("VnPNumber", m.group(0))

                if i > 0:
                    # we want a line between days (bun not before the first day)
                    DayLine = SubElement(temp_output_root, "DayLine")
                    DayLine.tail = "\n"


                first_VoteEntry.text = f"[{m.group(0)}]"
                first_VoteEntry.tag = "DaySep"
                first_VoteEntry.tail = "\n"
                temp_output_root.append(first_VoteEntry)

            # insert date element
            date_ele = SubElement(temp_output_root, "VotesDate")
            date_ele.text = date.strftime("%A") + " "
            date_for_header = SubElement(date_ele, "DateForHeader")
            date_for_header.text = date.strftime("%d %B %Y").lstrip("0")
            date_ele.tail = "\n"

        # variable to contain the section
        last_section = "chamber"
        # used to help tell if numbering should restart in InDesign
        restart_numbers = True

        for vote_item in VoteItems:

            # If the section changes we need a new heading. There is not section heading needed for the chamber
            section_text = vote_item.findtext("Section")
            if section_text:
                section_text = section_text.strip()
                section_text_cf = section_text.casefold()
                # There is also no heading needed for Certificates and Corrections
                if section_text_cf not in (
                    last_section,
                    "certificates and corrections",
                ):
                    SubElement(temp_output_root, "OPHeading1").text = (
                        section_text + "\n"
                    )
                    last_section = section_text_cf
                    # The numbering is also supposed to restart after new sections
                    # unless section is other proceedings
                    if section_text_cf != "other proceedings":
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

                # if the element is an html table...
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
                )  # sometimes there is an unwanted `;`

                # decide what tag we need to give it
                number_ele = vote_item.find("Number")
                vote_entry_type = vote_item.find("VoteEntryType")
                if i == 0 and number_ele is not None and number_ele.text:
                    item.tag = "BusinessItemHeadingNumbered"
                    if restart_numbers is True:
                        item.tag = "BusinessItemHeadingNumberedRestart"
                        restart_numbers = False

                elif item.get("class", "") == "HalfLine":
                    item.tag = "HalfLine"

                elif (
                    item_style == "text-align: right"
                ):
                    # apply the special style to the speaker or chairs name
                    if next_item_text.upper().strip() in chair_titles:
                        # We need to remove the speakers signature as it is
                        # not needed for the journal
                        print(f"\n{etree.tostring(date_ele)}")
                        print(f"{next_item_text=}")
                        print(etree.tostring(item))
                        continue
                        # item.getparent().remove(item)
                        # item.tag = 'SpeakerName'
                    if item_text.upper().strip() in chair_titles:
                        continue

                    # other wise right align
                    item.tag = "RightAlign"

                # some elements are headings and take particular styles
                elif iselement(vote_entry_type) and vote_entry_type.text == "Heading":
                    item.tag = "OPHeading2"
                    if item_text.upper().strip() in chair_titles:
                        # print(f"{etree.tostring(vote_entry_type)}")
                        # print(f"{vote_entry_type.text=}")
                        # print(etree.tostring(item))
                        continue
                        # item.getparent().remove(item)
                        # item.tag = 'RightAlign'

                    # put The House met at in the center
                    if re.search(r"^The House met at", item_text) is not None:
                        item.tag = "NormalCentred"
                    if item_text.upper() == "PRAYERS":
                        item.tag = "MotionText"
                    if item_text.casefold().strip() in speaker_certificates:
                        item.tag = "SpeakersCertificates"

                elif item_style == "text-align: center":
                    item.tag = "NormalCentred"
                    if item.text and item.text.casefold().strip() in speaker_certificates:
                        item.tag = "SpeakersCertificates"

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


                # item.text = re.sub(r"[ \u00A0]+", " ", item.text.strip())

                item.tail = "\n"
                temp_output_root.append(deepcopy(item))

            output_root.append(temp_output_root)

    output_root = journal_mods(output_root)

    # write out the file
    if output_file is None:
        output_file = Path(DEFAULT_OUTPUT_FILENAME)

    et = etree.ElementTree(output_root)

    et.write(str(output_file), encoding="utf-8", xml_declaration=True)
    print(f"\nTransformed XML (for InDesign) is at:\n{output_file.resolve()}")
    return 0


def journal_mods(output_root: _Element) -> _Element:

    allowed_empty_paras = ("DaySep", "ThinLine", "TableContainerPara")

    for item in output_root.findall('./day/*'):

        if item.text:
            item.text = item.text.strip()

        # remove the bold on e.g. (2) the Prime Minister
        try:
            is_para = item.tag in ("MotionText", "Indent1")
            strong_child = item[0].tag == "strong"
            no_other_children = len(item) == 1
            starts_with_number = re.match(r'\(\d+\)\s', item[0].text.strip()) is not None

            if is_para and strong_child and no_other_children and starts_with_number:
                if item.text and item[0].text:
                    item.text += " " + item[0].text
                elif item[0].text:
                    item.text = item[0].text

                if item[0].tail:
                    item.text += ' ' + item[0].tail

        except Exception:
            pass

        # convert loads of underscores to a thin line
        if item.text and item.text.strip() == '_' * len(item.text.strip()):
            item.tag = 'ThinLine'
            item.text = ''

        # in the journal we use a thin line above to separate things and
        # but it needs to be a separate elements so that is is kept with
        # the last paragraph
        if item.tag == "OPHeading1":
            item.tag = "HeadingItalicAfterLine"
            thin_line = etree.Element("ThinLine")
            thin_line.tail = "\n"
            item.addprevious(thin_line)

        # TODO: members names in brackets keep with previous
        # TODO: remove none breaking spaces
        if item.text:
            item.text = item.text.replace("\u00A0", " ")


        # TODO: remove empty paragraphs
        if item.tag not in allowed_empty_paras and item.text and item.text.strip() == '' and len(item) == 0 and item.tail and item.tail.strip() == '':
            item.getparent().remove(item)
        # TODO: fix tables

        if item.tag == "FullLine" and item.getnext() is not None and item.getnext().tag == "SpeakersCertificates":
            item.getparent().remove(item)




    return output_root

def json_from_uri(
    uri: str, default: Optional[T] = None, showerror=True
) -> Union[T, Any]:
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.get(uri, headers=headers)
        json_obj = response.json()
    except Exception as e:
        if showerror:
            print(f"Error getting data from:\n{uri}\n{e}")
        return default
    else:
        return json_obj


def get_sitting_dates_in_range(
    from_date: datetime, to_date: datetime
) -> List[datetime]:
    """get return a list of sitting days"""

    # the calendar api gives you the next sitting day so we need to start form the day before
    start_date = from_date - timedelta(days=1)

    current_date = start_date
    dates = []
    count = 0
    while current_date < to_date:
        current_date = start_date + timedelta(days=count)
        dates.append(current_date)
        count += 1

    sitting_dates = []
    for d in dates:

        next_sitting_date_str = json_from_uri(
            CAL_API_URL_TEMPLATE.format(d.strftime("%Y-%m-%d"))
        )

        if not next_sitting_date_str:
            continue

        next_sitting_date = datetime.strptime(
            next_sitting_date_str[:10], "%Y-%m-%d"
        )

        if next_sitting_date not in sitting_dates:
            sitting_dates.append(next_sitting_date)

    print(f"{[sd.strftime('%y-%m-%d') for sd in sitting_dates]}")

    return sitting_dates


if __name__ == "__main__":
    cli()
