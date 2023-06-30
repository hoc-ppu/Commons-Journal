#!/usr/bin/env python3

# Mark Fawcett
# fawcettm@parliament.uk
# Bugs should be expected and should be reported
# Ideas for improvement are welcome

# python standard library imports
from datetime import datetime, date, timedelta
from functools import cached_property
from pathlib import Path
import re
import sys
from typing import cast, Union
import os
from cache_to_disk import cache_to_disk
import requests

import click
from lxml import etree
from lxml.etree import _Element
from lxml.etree import iselement

# 1st party imports
from package.utilities import get_dates_from_session


OUTPUT_XML_NAME = "for-id7.xml"

DEFAULT_RAW_XML_TEMPLATE = "as_downloaded_papers_{session}.xml"

NS_MAP = {"xsi": "http://www.w3.org/2001/XMLSchema-instance"}

WORD_FOR_PATTERN = re.compile(r"([12]\d\d\d(?:-\d\d)? ?(?:\([A-Za-z0-9 ]*\))?)$")
LAID_PATTERN = re.compile(r" ?\(laid \d\d? [A-Za-z]{3,11} ?[0-9]{0,5}\)")

# WITHDRAWAL_PREFIX = "[Withdrawal] "
# RELAY_PREFIX = "[Relay] "


class Paper:
    @staticmethod
    def clean(string: str) -> str:
        return re.sub(r" +", " ", string.strip())

    def __init__(self, element: _Element):
        self.side_title = self.clean(element.findtext("SideTitle", ""))
        self._raw_title = self.clean(element.findtext("Title", ""))
        self.is_draft = self.clean(element.findtext("Draft", ""))
        # we will replace any hyphens in the year with the en-dash later
        # as for now we need to keep hyphens
        self.year = self.clean(element.findtext("Year", "")).replace("\u2013", "-")
        # papers don't always have a subject heading.
        self.subject_heading = self.clean(element.findtext("SubjectHeading", ""))

        self._input_date_laid: str = self.clean(element.findtext("DateLaidCommons", ""))
        self._input_date_withdrawn: str = self.clean(
            element.findtext("DateWithdrawn", "")
        )

        self.date_laid, self.date_withdrawn = self.__process_dates()

        if self.subject_heading:
            self.title = self.subject_heading
        else:
            self.title = self._raw_title

    def __process_dates(self) -> tuple[str, str]:
        try:
            laid_sitting_date = get_sitting_date(
                datetime.strptime(self._input_date_laid[0:10], "%Y-%m-%d")
            )
            laid_sitting_date_str = format_date(laid_sitting_date)
        except Exception:
            laid_sitting_date_str = ""

        date_withdrawn = ""
        try:
            withdrawn_sitting_date = get_sitting_date(
                datetime.strptime(self._input_date_withdrawn[0:10], "%Y-%m-%d")
            )
            date_withdrawn = f"[withdrawn, {format_date(withdrawn_sitting_date)}]"
        except Exception:
            date_withdrawn = ""

        return laid_sitting_date_str, date_withdrawn

    @property
    def index_entry(self):
        entry = f"{self.title.strip()}, {self.date_laid} {self.date_withdrawn}".strip(
            ", "
        )
        return re.sub(r"(?<=\d)-(?=\d)", "\u2013", entry)


    # for sorting
    @cached_property
    def _sort_str(self) -> str:

        # some papers are withdrawn and then relayed and these two entries
        # should appear together see fix_relayed().

        title_no_laid = re.sub(LAID_PATTERN, "", self.title.casefold().strip())
        index_entry = (
            f"{title_no_laid}, {self._input_date_laid} {self.date_withdrawn}".strip(
                ", "
            )
        )

        # some things should not be included in the sort
        # (e.g. the word `the` at the beginning)
        index_entry = index_entry.removeprefix("the ")
        # index_entry = index_entry.removeprefix(WITHDRAWAL_PREFIX.casefold())
        # index_entry = index_entry.removeprefix(RELAY_PREFIX.casefold())

        return index_entry

    def __lt__(self, other):
        return self._sort_str < other._sort_str

    def __gt__(self, other):
        # we only really need less than but hey
        return self._sort_str > other._sort_str

    def __eq__(self, other):
        return self._sort_str == other._sort_str

    def __str__(self):
        return self.index_entry


Side_Title = str
Group = str
Papers_Structure = dict[Side_Title, dict[Group, list[Paper]]]

PAPERS_GROUPING = [
    # the order here matters
    {
        "pattern": re.compile(r"Regulations ? ?\d?\d?\d?\d?$", flags=re.I),
        "base_key": "Regulations: ",
    },
    # {'pattern': re.compile(r'Regulations\(Northern Ireland\)$', flags=re.I),
    #     'base_key': 'Regulations (Northern Ireland): '},
    {
        "pattern": re.compile(r"^Report of the Law Commission (on )?", flags=re.I),
        "base_key": "Report of the Law Commission: ",
    },
    {
        "pattern": re.compile(r"Order ? ?\d?\d?\d?\d?$", flags=re.I),
        "base_key": "Order: ",
    },
    {
        "pattern": re.compile(r"Order of Council ? ?\d?\d?\d?\d?$", flags=re.I),
        "base_key": "Order of Council: ",
    },
    {
        "pattern": re.compile(r"^Report and Accounts of ", flags=re.I),
        "base_key": "Reports and Accounts, ",
    },
    {
        # "pattern": re.compile(r"Rules ? ?\d?\d?\d?\d?$", flags=re.I),  too  loose
        "pattern": re.compile(r"Rules ? ?\d\d\d\d$", flags=re.I),
        "base_key": "Rules: ",
    },
    {
        "pattern": re.compile(r"^Accounts of ", flags=re.I),
        "base_key": "Accounts, ",
    },
    {
        "pattern": re.compile(r"^Account of (the)?", flags=re.I),
        "base_key": "Account, ",
    },
    {
        "pattern": re.compile(
            r"^Report of the Independent Chief Inspector of Borders and Immigration: ",
            flags=re.I,
        ),
        "base_key": "Report of the Independent Chief Inspector of Borders and Immigration: ",
    },
    {
        "pattern": re.compile(
            r"^Report by the Comptroller and Auditor General on ", flags=re.I
        ),
        "base_key": "Report by the Comptroller and Auditor General: ",
    },
]

PLURALS: list[tuple[str, str]] = [
    ("^Draft Order: ", "Draft Orders: "),
    ("^Order: ", "Orders: "),
    ("^Order of Council", "Orders of Council"),
    (
        "^Report of the Independent Chief Inspector of Borders and Immigration",
        "Reports of the Independent Chief Inspector of Borders and Immigration",
    ),
    (
        "^Report by the Comptroller and Auditor General",
        "Reports by the Comptroller and Auditor General",
    ),
    (
        "^Report of the Law Commission",
        "Reports of the Law Commission",
    ),
]


def main(
    session: Union[str, None] = None,
    local_input_file: Union[Path, None] = None,
    output_file_or_dir: Union[Path, None] = None,
    save_raw: bool = True,
) -> int:

    if local_input_file is not None:
        # use local file as input rather than querying API
        papers_xml_tree = etree.parse(str(local_input_file))
        papers_xml = papers_xml_tree.getroot()

    elif session is not None:
        # Query papers laid API. First use passed in session to work out what
        # dates should be queried

        try:
            # first get the dates for the session
            session_start, session_end = get_dates_from_session(session)
        except Exception as e:
            print(e)
            print("Could not get session data from whats on.")
            sys.exit(1)
        try:
            # Query papers laid API
            print("Getting data from papers laid")
            response = request_papers_data(session_start, session_end)
        except Exception as e:
            print(e)
            print(
                "\nCould not get XML from the papers laid API. "
                "Check that you are connected to the parliament network."
            )
            sys.exit(1)

        if save_raw:
            as_downloaded_file_name = DEFAULT_RAW_XML_TEMPLATE.format(session=session)
            if output_file_or_dir is None:
                output_path = Path(as_downloaded_file_name)
            elif output_file_or_dir.is_dir():
                output_path = Path(output_file_or_dir, as_downloaded_file_name)
            else:
                # assume file instead of dir
                output_path = Path(output_file_or_dir.parent, as_downloaded_file_name)
            with open(output_path, "wb") as f:
                f.write(response.content)
                print(f"Downloaded: {output_path.absolute()}")

        papers_xml = etree.fromstring(response.content)
    else:
        print("Error: Must have either an XML file or a session.")
        sys.exit(1)

    filtered_papers = filter_papers(papers_xml)

    print(f"After filtering, there are {len(filtered_papers)} papers.")

    papers_data = populate_papers_data(filtered_papers)

    # fix_relayed(papers_data)

    sorted_papers_data = sort_papers(papers_data)

    output_xml = convert_to_xml(sorted_papers_data)

    write_xml(output_xml, output_file_or_dir)

    return 0


# -------------------- Begin comand line interface ------------------- #


@click.group()
def cli():
    pass


@cli.command()
@click.argument(
    "input_path", type=click.Path(exists=True, dir_okay=False, path_type=Path)
)
@click.option(
    "--output",
    "-o",
    help="Optionally provide the directory or file path for the output XML",
    type=click.Path(writable=True, path_type=Path),
)
def from_file(input_path: Path, output: Union[Path, None] = None):
    """Create papers index XML from a raw XML file already on your computer.

    if you do not already have a raw XML file containing papers data,
    use the from-api subcomand instead.
    """
    return main(local_input_file=input_path, save_raw=False, output_file_or_dir=output)


@cli.command()
@click.argument("session")
@click.option(
    "--discard-raw-xml",
    is_flag=True,
    default=False,
    help="Use this option to suppress saving the raw XML downloaded from the API",
)
@click.option(
    "--output",
    "-o",
    help="Optionally provide the directory or file path for the output XML",
    type=click.Path(writable=True, path_type=Path),
)
def from_api(session: str, discard_raw_xml: bool, output: Union[Path, None] = None):
    """For a given SESSION, create papers index XML (to be typeset in InDesign)
    from data downloaded from the papers laid API.

    SESSION is a parliamentary session and should entered in the form YYYY-YY.
    E.g. 2017-19.

    By default the XML downloaded from papers laid will be saved alongside the
    output. You can stop this behaviour with the --discard-raw-xml flag.

    \b
    You will need to be connected to the parliament network.
    For a list of parliamentary sessions check:
    https://whatson-api.parliament.uk/calendar/sessions/list.json
    """
    return main(
        session=session, save_raw=not (discard_raw_xml), output_file_or_dir=output
    )


# --------------------- End comand line interface -------------------- #


def sort_papers(papers_data: Papers_Structure) -> Papers_Structure:
    sorted_papers_data: Papers_Structure = {}
    for side_title in sorted(papers_data.keys(), key=lambda item: item.upper()):
        sorted_papers_data[side_title] = {}
        for group in sorted(papers_data[side_title].keys(), key=group_sort):
            sorted_papers_data[side_title][group] = sorted(
                papers_data[side_title][group]
            )

    return sorted_papers_data


def group_sort(item: str) -> tuple[int, str]:
    """Helper to sort groups as specified"""

    if item.startswith("Draft Order"):
        return 1, item
    if item.startswith("Order of Council") or item.startswith("Orders of Council"):
        return 3, item
    if item.startswith("Order"):
        # note this comes before the above
        return 2, item
    if item.startswith("Draft Regulations"):
        return 4, item
    if item.startswith("Regulations (Northern Ireland)"):
        return 6, item
    if item.startswith("Regulations"):
        return 5, item
    if item.startswith("Rules"):
        return 7, item
    if item.startswith("Accounts"):
        return 8, item
    if item.startswith("Report and Accounts"):
        return 9, item
    else:
        # We want these at the back of each section
        return 100, item


def filter_papers(papers_xml: Union[_Element, list[_Element]]) -> list[_Element]:
    """Remove duplicates and any papers not laid in Commons"""

    if iselement(papers_xml):
        papers_xpath_result = papers_xml.xpath(
            # get all papers
            "/ArrayOfDailyPapers/DailyPapers/*/Paper"
            #  remove any not laid in the commons
            "[DateLaidCommons[text()]]",
            namespaces=NS_MAP,
        )
    else:
        papers_xpath_result = papers_xml
    papers_xpath_result = cast(list[_Element], papers_xpath_result)

    paper_ids = set()  # use a set to contain all the paper Ids.
    papers_of_interest = []
    for paper in reversed(papers_xpath_result):
        # get the papers Id, ** I am assuming that these are unique to each paper **
        paper_id = paper.findtext("Id")

        if paper_id not in paper_ids:
            paper_ids.add(paper_id)
            papers_of_interest.append(paper)

    return papers_of_interest



def request_papers_data(date_from: datetime, date_to: datetime) -> requests.Response:
    """Query the papers laid API for papers laid in the date range."""

    session_from_str = date_from.strftime("%Y-%m-%d")
    session_to_str = date_to.strftime("%Y-%m-%d")

    url = (
        "http://services.paperslaid.parliament.uk/papers/list/daily.xml"
        f"?fromDate={session_from_str}&toDate={session_to_str}&house=commons"
    )

    response = requests.get(url)

    return response


def convert_to_xml(papers_data: Papers_Structure) -> _Element:
    """create a lxml.etree._Element from Papers structure"""

    output_root = etree.Element("PapersIndex")

    for side_t in papers_data:
        etree.SubElement(output_root, "SideTitle").text = side_t

        # entries_under_side_title = []

        for key, value in papers_data[side_t].items():
            if key == "[other papers]":
                # paper that are not grouped
                # entries_under_side_title += value
                # entries_under_side_title += f'{value}.'
                for paper in value:
                    etree.SubElement(
                        output_root, "Paper"
                    ).text = f"{paper.index_entry}."
            elif len(value) > 0:
                key = re.sub(r"(?<=\d)-(?=\d)", "\u2013", key)
                if len(value) > 1:
                    key = fix_plurals(key)
                etree.SubElement(
                    output_root, "Paper"
                ).text = f'{key}{"; ".join(paper.index_entry for paper in value)}.'

    # for every element in output_root add a new line after
    for ele in output_root:
        ele.tail = "\n"

    return output_root


def write_xml(xml_root: _Element, output_file_or_dir: Union[Path, None] = None):

    """Write XML to file. If output_file_or_dir is not passed use global
    constant OUTPUT_XML_NAME instead"""

    if output_file_or_dir is None:
        xml_file_Path: Path = Path(OUTPUT_XML_NAME)
    elif output_file_or_dir.is_dir():
        xml_file_Path = Path(output_file_or_dir, OUTPUT_XML_NAME)
    else:
        xml_file_Path = output_file_or_dir

    outputTree = etree.ElementTree(xml_root)
    try:
        outputTree.write(str(xml_file_Path), encoding="UTF-8", xml_declaration=True)
    except Exception as e:
        print(e)
        print(
            f"Warning: Can't print to {xml_file_Path}. "
            f"Trying {OUTPUT_XML_NAME} instead."
        )
        xml_file_Path = Path(OUTPUT_XML_NAME)
        outputTree.write(str(xml_file_Path), encoding="UTF-8", xml_declaration=True)

    print(f"Created: {xml_file_Path.absolute()}")


def fix_plurals(possible_plural: str) -> str:
    for plural in PLURALS:
        if re.search(plural[0], possible_plural):
            return re.sub(plural[0], plural[1], possible_plural)
    return possible_plural


def populate_papers_data(
    papers_of_interest: Union[list[_Element], list[Paper]],
) -> Papers_Structure:

    papers_data: Papers_Structure = {}

    for p in papers_of_interest:
        if iselement(p):
            # p is an element
            paper = Paper(p)
        else:
            # p must already be a Paper instance
            paper = cast(Paper, p)

        # paper_obj.setdefault(side_title, []).append()
        if paper.side_title not in papers_data:
            # PAPERS_DATA[side_title] = deepcopy(default_side_title_obj)
            papers_data[paper.side_title] = {}

        key = "[other papers]"  # key for ungrouped paper
        for group_obj in PAPERS_GROUPING:

            # special cases for things not to be grouped
            if paper.title.startswith((
                "Explanatory Memorandum", "Impact Assessment")
            ):
                continue

            # Nortern Ireland Regulations are special
            NI_re = r"(Regulations \(Northern Ireland\)) ([12]\d\d\d)"
            match = re.search(NI_re, paper.title)
            if match:
                key = f"{match.group(1)}: {match.group(2)}: "
                paper.title = re.sub(NI_re, "", paper.title).strip()
                break

            if not re.search(group_obj["pattern"], paper.title):
                continue

            # set the key up
            key = group_obj["base_key"]
            if paper.is_draft == "true":
                key = "Draft " + key
            if paper.year:
                key = f"{key}{paper.year}: "  # key for special paper

            # amend the title
            paper.title = re.sub(group_obj["pattern"], "", paper.title).strip()

            # Remove the year from the paper title
            # (this is since we started using <SubjectHeading>)
            # needed for e.g.
            # <Paper>Accounts, 2015–16: the Parliamentary Contributory Pension Fund 2015-16, 3 Feb 2017.</Paper>
            # which should be:
            # <Paper>Accounts, 2015–16: the Parliamentary Contributory Pension Fund, 3 Feb 2017.</Paper>
            if paper.year and paper.title.endswith(paper.year):
                # remove the year from the end
                paper.title = paper.title[: -len(paper.year)]

            # if the above matched we do not need to check anymore so break
            break

        add_word_for(paper)
        papers_data[paper.side_title].setdefault(key, []).append(paper)

    return papers_data


# def fix_relayed(papers_data: Papers_Structure):
#     """Prepend [Withdrawal] or [Relay] to relevant paper titles"""

#     # Sometimes papers (usually Explanatory Memoranda or Impact Assessments)
#     # can be withdrawn are relaid. When this happens the following format is required
#     # [Withdrawal] Explanatory Memorandum to the Schools (Definition) Order 2017, 10 Jan 2017 [withdrawn, 20 Feb 2017].
#     # [Relay] Explanatory Memorandum to the Schools (Definition) Order 2017 (laid 10 January), 20 Feb 2017.

#     # Note care must be taken in the sort here as the [Withdrawal] should come
#     # before the [Relay]. See paper._sort_str

#     # Papers_Structure = dict[Side_Title, dict[Group, list[Paper]]]

#     for group in papers_data.values():

#         for papers_list in group.values():
#             # find withdrawns
#             withdrawns: list[Paper] = []
#             for paper in papers_list:
#                 if paper.date_withdrawn:
#                     withdrawns.append(paper)

#             # next find any matched papers
#             for r_paper in papers_list:
#                 relay_paper_title = re.sub(LAID_PATTERN, "", r_paper.title).strip()
#                 for w_paper in withdrawns:

#                     paper_withdrawn = bool(r_paper.date_withdrawn)
#                     titles_match = relay_paper_title == w_paper.title

#                     if paper_withdrawn or not titles_match:
#                         continue

#                     # found a matching pair
#                     w_paper.title = (
#                         WITHDRAWAL_PREFIX
#                         + w_paper.title.removeprefix(WITHDRAWAL_PREFIX).strip()
#                     )
#                     r_paper.title = (
#                         RELAY_PREFIX + r_paper.title.removeprefix(RELAY_PREFIX).strip()
#                     )
#                     break


def add_word_for(paper: Paper):
    """if appropriate add the word `for` towards the end of the paper.title"""

    # sometime we need to add the word `for` between the main part of the title
    # and the year/year range. This must also allow for adding `for` between the
    # main title and something like `2015–16 (laid 12 July)`... I'm going to
    # assume the main title is in the paper._raw_title filed. Otherwise we may
    # get false positives...

    if paper._raw_title != paper.subject_heading:

        match = re.search(WORD_FOR_PATTERN, paper.title)
        if match and match.group(0) not in paper._raw_title:
            # here we are guarding against the situation where the raw title has
            # the pattern in. I.e. where there are numbers in the raw_title
            paper.title = re.sub(WORD_FOR_PATTERN, r"for \1", paper.title)


def format_date(date_: date) -> str:
    """Convert a date object to a string formatted for the Journal."""

    return date_.strftime("%d %b %Y").lstrip("0")


@cache_to_disk(1)
def get_sitting_date(date_: datetime) -> datetime:
    """If input date is a sitting date return the input date
    else return the next sitting date"""

    url_template = "https://whatson-api.parliament.uk/calendar/proceduraldates/Commons/nextsittingdate.json?dateToCheck={}"

    one_day_ago = date_ - timedelta(days=1)

    url = url_template.format(one_day_ago.strftime("%Y-%m-%d"))

    response = requests.get(url)

    return datetime.strptime(response.json(), "%Y-%m-%dT%H:%M:%S")


if __name__ == "__main__":
    cli()
