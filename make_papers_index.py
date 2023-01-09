#!/usr/bin/env python3

# Mark Fawcett
# fawcettm@parliament.uk
# Bugs should be expected and should be reported
# Ideas for improvement are welcome

# python standard library imports
from datetime import datetime, date, timedelta
from pathlib import Path
import re
import sys
from typing import cast
import os
from cache_to_disk import cache_to_disk
import requests

import click
from lxml import etree
from lxml.etree import _Element
from lxml.etree import iselement


OUTPUT_XML_NAME = "papers_for_indesign11.xml"

NS_MAP = {"xsi": "http://www.w3.org/2001/XMLSchema-instance"}


class Paper:
    def __init__(self, paper_element: _Element):
        self.side_title = paper_element.findtext("SideTitle", default="").strip()
        self.title = paper_element.findtext("Title", default="").strip()
        self.is_draft = paper_element.findtext("Draft", default="").strip()
        # replace any hyphens in the year with the en-dash as that is typographically correct
        self.year = (
            paper_element.findtext("Year", default="").strip().replace("-", "\u2013")
        )
        # papers don't always have a subject heading.
        self.subject_heading = paper_element.findtext(
            "SubjectHeading", default=""
        ).strip()

        self._input_date_laid: str = paper_element.findtext(
            "DateLaidCommons", default=""
        ).strip()
        self._input_date_withdrawn: str = paper_element.findtext(
            "DateWithdrawn", default=""
        ).strip()

        self.date_laid, self.date_withdrawn = self.__process_dates()

        if self.subject_heading:
            self.title = self.subject_heading.replace("  ", " ")

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
        return f"{self.title}, {self.date_laid} {self.date_withdrawn}".strip(", ")

    def __eq__(self, other):
        return self.index_entry == other.index_entry

    # for sorting
    @property
    def _sort_str(self):
        return self.index_entry.upper().removeprefix("THE ")

    def __lt__(self, other):
        return self._sort_str < other._sort_str

    def __gt__(self, other):
        # we only really need less than but hey
        return self._sort_str > other._sort_str

    def __str__(self):
        return self.index_entry


Side_Title = str
Group = str
Papers_Structure = dict[Side_Title, dict[Group, list[Paper]]]

PAPERS_GROUPING = [
    # the order here matters
    {
        "pattern": re.compile(r"Regulations ? ?\d?\d?\d?\d?$", flags=re.IGNORECASE),
        "base_key": "Regulations: ",
    },
    # {'pattern': re.compile(r'Regulations\(Northern Ireland\)$', flags=re.IGNORECASE),
    #     'base_key': 'Regulations (Northern Ireland): '},
    {
        "pattern": re.compile(r"^Report of the Law Commission ", flags=re.IGNORECASE),
        "base_key": "Report of the Law Commission: ",
    },
    {
        "pattern": re.compile(r"Order ? ?\d?\d?\d?\d?$", flags=re.IGNORECASE),
        "base_key": "Order: ",
    },
    {
        "pattern": re.compile(
            r"Order of Council ? ?\d?\d?\d?\d?$", flags=re.IGNORECASE
        ),
        "base_key": "Order of Council: ",
    },
    {
        "pattern": re.compile(r"^Report and Accounts of ", flags=re.IGNORECASE),
        "base_key": "Reports and Accounts, ",
    },
    {
        "pattern": re.compile(r"Rules ? ?\d?\d?\d?\d?$", flags=re.IGNORECASE),
        "base_key": "Rules: ",
    },
    {
        "pattern": re.compile(r"^Accounts of ", flags=re.IGNORECASE),
        "base_key": "Accounts, ",
    },
    {"pattern": re.compile(r"^Account ", flags=re.IGNORECASE), "base_key": "Account, "},
    {
        "pattern": re.compile(
            r"^Report of the Independent Chief Inspector of Borders and Immigration: ",
            flags=re.IGNORECASE,
        ),
        "base_key": "Report of the Independent Chief Inspector of Borders and Immigration: ",
    },
    {
        "pattern": re.compile(
            r"^Report by the Comptroller and Auditor General on ", flags=re.IGNORECASE
        ),
        "base_key": "Report by the Comptroller and Auditor General: ",
    },
]

PLURALS = (
    ("^Draft Order: ", "Draft Orders: "),
    ("^Order: ", "Orders: "),
    ("^Order of Council", "Orders of Council"),
)


def main(
    session: str | None = None,
    local_input_file_Path: Path | None = None,
    save_raw: bool = True,
) -> int:

    # args = cli()

    # if args.process_local:
    #     papers_xml_tree = etree.parse(args.process_local.name)
    #     papers_xml = papers_xml_tree.getroot()
    # elif args.session:
    #     try:
    #         session_start, session_end = get_dates_from_session(args.session)
    #     except Exception as e:
    #         print(e)
    #         return os.EX_UNAVAILABLE
    #     response = request_papers_data(session_start, session_end)
    #     if args.save_raw:
    #         as_downloaded_file_name = f"as_downloaded_papers_{args.session}.xml"
    #         with open(as_downloaded_file_name, "wb") as f:
    #             f.write(response.content)
    #     papers_xml = etree.fromstring(response.content)
    # else:
    #     print("Error: Must have either an XML file or a session.")
    #     return os.EX_USAGE

    if local_input_file_Path is not None:
        papers_xml_tree = etree.parse(local_input_file_Path)
        papers_xml = papers_xml_tree.getroot()

    elif session is not None:
        try:
            session_start, session_end = get_dates_from_session(session)
        except Exception as e:
            print(e)
            return os.EX_UNAVAILABLE
        try:
            response = request_papers_data(session_start, session_end)
        except Exception as e:
            print(e)
            print(
                "Could not get XML from the papers laid API. Check that you are connected to the parliament network."
            )
            return os.EX_UNAVAILABLE
        if save_raw:
            as_downloaded_file_name = f"as_downloaded_papers_{session}.xml"
            with open(as_downloaded_file_name, "wb") as f:
                f.write(response.content)
        papers_xml = etree.fromstring(response.content)
    else:
        print("Error: Must have either an XML file or a session.")
        return os.EX_USAGE

    filtered_papers = filter_papers(papers_xml)

    print(f"There are {len(filtered_papers)} papers once filtered.")

    papers_data = populate_papers_data(filtered_papers)

    sorted_papers_data = sort_papers(papers_data)

    output_xml = convert_to_xml(sorted_papers_data)

    write_xml(output_xml)

    return 0


# -------------------- Begin comand line interface ------------------- #


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
def from_file(input_path: Path):
    """Create papers index XML from a raw XML file already on your computer.

    if you do not already have a raw XML file containing papers data,
    use the from-api subcomand instead.
    """
    main(local_input_file_Path=input_path, save_raw=False)


@cli.command()
@click.argument("session")
@click.option(
    "--discard-raw-xml",
    default=False,
    help="Use this option to suppress saving the raw XML downloaded from the API",
)
def from_api(session: str, discard_raw_xml: bool):
    """For a given session, create papers index XML (to be typeset in InDesign)
    from data downloaded from the papers laid API.

    SESSION is a parliamentary session and should entered in the form YYYY-YY.
    E.g. 2017-19.

    By default the XML downloaded frompapers laid will be saved alongside the
    output. You can stop this behaviour with the --discard-raw-xml flag.

    \b
    You will need to be connected to the parliament network.
    For a list of parliamentary sessions check:
    https://whatson-api.parliament.uk/calendar/sessions/list.json
    """
    main(session=session, save_raw=not (discard_raw_xml))


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


def filter_papers(papers_xml: _Element | list[_Element]) -> list[_Element]:
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


def get_dates_from_session(session_code: str) -> tuple[datetime, datetime]:
    """Return a tuple of start and end dates (as strings) of a session of parliament"""

    # session code e.g. '2015-16'

    # Get the dates from API
    url = "http://service.calendar.parliament.uk/calendar/sessions/list.json"
    response = requests.get(url)

    session_json = response.json()

    for session_obj in session_json:
        if session_obj["CommonsDescription"] == session_code:
            start_date_str = session_obj["StartDate"]
            end_date_str = session_obj["EndDate"]

            start_date = datetime.strptime(start_date_str[:10], "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str[:10], "%Y-%m-%d")

            return start_date, end_date

    raise ValueError(
        f"Dates for session, {session_code} could not be found.\nCheck {url}"
    )


def request_papers_data(date_from: datetime, date_to: datetime) -> requests.Response:
    """Query the papers laid API for papers laid in the date range"""

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
                if len(value) > 1:
                    key = fix_plurals(key)
                etree.SubElement(
                    output_root, "Paper"
                ).text = f'{key}{"; ".join(paper.index_entry for paper in value)}.'
                # entries_under_side_title.append(f'{key}{"; ".join(value)}.')
                # entries_under_side_title.append(f'{key}{"; ".join(value)}')

        # add all the entries to the XML
        # for paper in entries_under_side_title:
        # for paper in sorted(entries_under_side_title, key=lambda item_str: item_str.removeprefix('The ')):
        #     etree.SubElement(output_root, 'Paper').text = paper

    # for every element in output_root add a new line after
    for ele in output_root:
        ele.tail = "\n"

    return output_root


def write_xml(xml_root: _Element, parent_directory: str | Path | None = None):
    if parent_directory:
        xml_file_Path = Path(parent_directory, OUTPUT_XML_NAME)
    else:
        xml_file_Path = Path(OUTPUT_XML_NAME)
    outputTree = etree.ElementTree(xml_root)
    outputTree.write(str(xml_file_Path), encoding="UTF-8", xml_declaration=True)


def fix_plurals(possible_plural: str) -> str:
    for plural in PLURALS:
        if re.search(plural[0], possible_plural):
            return re.sub(plural[0], plural[1], possible_plural)
    return possible_plural


def populate_papers_data(papers_of_interest: list[_Element]) -> Papers_Structure:

    papers_data: Papers_Structure = {}

    for p in papers_of_interest:
        paper = Paper(p)

        # paper_obj.setdefault(side_title, []).append()
        if paper.side_title not in papers_data:
            # PAPERS_DATA[side_title] = deepcopy(default_side_title_obj)
            papers_data[paper.side_title] = {}

        key = "[other papers]"  # key for ungrouped paper
        for group_obj in PAPERS_GROUPING:

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

            # if the above matched we do not need to check anymore so break
            break

        # if subject_heading.startswith(title) and subject_heading != title:
        #     # sometimes the subject heading includes info that we want that
        #     # does not appear in the title.
        #     title = subject_heading

        # journal_title = title
        # if year:
        #     journal_title = f'{title} for {year}'

        papers_data[paper.side_title].setdefault(key, []).append(paper)

    return papers_data


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
    # sys.exit(main())
    cli()
