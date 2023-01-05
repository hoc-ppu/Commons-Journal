from datetime import datetime
import os
import sys

from lxml import etree
from lxml.etree import _Element
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from process_xml import get_dates_from_session
from process_xml import filter_papers
from process_xml import populate_papers_data
from process_xml import sort_papers
from process_xml import convert_to_xml
from data_for_testing import output_senior_courts_xml
from data_for_testing import output_regs_NI_xml
from data_for_testing import output_orders_in_council
from data_for_testing import output_account_singular
from data_for_testing import output_law_commission
from data_for_testing import output_borders
from data_for_testing import output_alphabetical_side_title_sort
from data_for_testing import output_sorting_word_the
from data_for_testing import papers_in_wrong_order
from data_for_testing import correctly_ordred_xml


@pytest.fixture
def xml_test_root() -> _Element:
    papers_xml_tree = etree.parse("tests/raw_papers_data.xml")
    papers_xml_root = papers_xml_tree.getroot()
    return papers_xml_root


def test_get_dates_from_session() -> None:

    assert get_dates_from_session('2017-19') == (datetime(2017, 6, 21, 0, 0), datetime(2019, 10, 8, 0, 0))

    with pytest.raises(ValueError):
        get_dates_from_session('Junk')

def test_filter_papers():

    # test that indeed duplicates are removed and lords only is removed

    def elements_equal(e1, e2):
        if e1.tag != e2.tag: return False
        if e1.text != e2.text: return False
        if e1.tail != e2.tail: return False
        if e1.attrib != e2.attrib: return False
        if len(e1) != len(e2): return False
        return all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))

    root_ele = etree.parse("filtering_test_before_2.xml").getroot()

    papers_l = filter_papers(root_ele)

    papers_e = etree.Element('ExpectedPapers')
    papers_e.extend(papers_l)

    et = etree.parse('expected_after_filter.xml')
    expected_papers = et.getroot()

    assert elements_equal(papers_e, expected_papers) ==  True


# ---------------------------- Sort tests ---------------------------- #

def xml_section_from_xpath(xml_test_root: _Element, xpath: str) -> str:

    """Return XML with papers specifies in the xpath expresion"""

    results = xml_test_root.xpath(xpath)

    filtered_papers = filter_papers(results)
    p_structure = populate_papers_data(filtered_papers)

    sorted_senior_courts_structure = sort_papers(p_structure)

    xml = convert_to_xml(sorted_senior_courts_structure)

    xml_str = etree.tostring(xml, encoding='unicode')

    return xml_str


def test_senior_courts(xml_test_root):

    """Civil Procedure should be soreted as in section 3.a. in the word doc"""

    xpath = ('/*/*/*/Paper[SideTitle[contains(.,"Senior Courts of England and Wales")]]'
             '[SubjectHeading[contains(.,"Rules")]]')

    xml_str = xml_section_from_xpath(xml_test_root, xpath)

    assert xml_str == output_senior_courts_xml


def test_regs_ni(xml_test_root):

    """Regulations (Northern Ireland) should be grouped as in section 3.b. in
    the word doc"""

    xpath = ('/*/*/*/Paper[SideTitle[contains(.,"Social Security")]]'
             '[SubjectHeading[contains(.,"Regulations (Northern Ireland)")]]')

    xml_str = xml_section_from_xpath(xml_test_root, xpath)

    assert xml_str == output_regs_NI_xml


def test_orders_in_council(xml_test_root):

    """Orders in Council should be grouped as in section 3.c. in
    the word doc"""

    xpath = ('/*/*/*/Paper[SideTitle[contains(.,"Health Care and Associated Professions")]]'
             '[SubjectHeading[contains(.,"Order of Council")]]')

    xml_str = xml_section_from_xpath(xml_test_root, xpath)

    assert xml_str == output_orders_in_council


def test_account_singular(xml_test_root):

    """Account (singular) should be grouped as in section 3.d. in
    the word doc"""

    xpath = ('/*/*/*/Paper[SideTitle[contains(.,"National Loans")]]'
             '[SubjectHeading[contains(.,"Account of the")]]')

    xml_str = xml_section_from_xpath(xml_test_root, xpath)

    assert xml_str == output_account_singular


def test_law_commission(xml_test_root):

    """Reports of the Law Commission on particular subjects should be sorted as
    in section 3.e. of the word doc"""

    xpath = ('/*/*/*/Paper[SideTitle[contains(.,"Law Commission")]]'
             '[SubjectHeading[starts-with(.,"Report of the Law Commission")]]')

    xml_str = xml_section_from_xpath(xml_test_root, xpath)

    assert xml_str == output_law_commission


def test_borders(xml_test_root):

    """Reports of the Reports of the Independent Chief Inspector of Borders and
    Immigration should be sorted as in section 3.f. of the word doc"""

    xpath = ('/*/*/*/Paper[SideTitle[contains(.,"UK Borders")]]'
             '[SubjectHeading[starts-with(.,"Report of the Independent Chief Inspector of Borders and Immigration:")]]')

    xml_str = xml_section_from_xpath(xml_test_root, xpath)

    assert xml_str == output_borders


def test_alphabetical_side_title_sort(xml_test_root):

    """side titles should be sorted as in section 6 of word doc"""

    xpath = ('/*/*/*/Paper[SideTitle'
             '[normalize-space() = "Health and Safety" or'
             'normalize-space() = "Health and Safety at Work" or'
             'normalize-space() = "Health and Social Care" or '
             'normalize-space() = "Health and Social Work Professions" or '
             'normalize-space() = "Health Care and Associated Professions" or '
             'normalize-space() = "Health Service Commissioners" or '
             'normalize-space() = "Healthcare and Associated Professions" or '
             'normalize-space() = "High Speed Rail (London-West Midlands)"]]')

    xml_str = xml_section_from_xpath(xml_test_root, xpath)

    assert xml_str == output_alphabetical_side_title_sort


def test_sorting_titles_starting_with_the_word_the(xml_test_root):

    """`The` at the start of the name of some papers should not disrupt the
    alphabetical order. The most obvious example is the list of Reports and
    Accounts under NATIONAL HEALTH SERVICE, where Trusts beginning with `The`
    are indexed in a block under `T`, and Trusts beginning with `the` are
    indexed in a block at the very end of the list. They should all be indexed
    by their main title, e.g. `The Christie NHS Foundation Trust` should appear
    in the `C` section of the list.

    See section 7 of the word doc"""

    xpath = ('/*/*/*/Paper[SideTitle[normalize-space() = "National Health Service"]]'
             '[SubjectHeading[starts-with(.,"Report and Accounts of")]]')

    xml_str = xml_section_from_xpath(xml_test_root, xpath)
    print(xml_str)
    assert xml_str == output_sorting_word_the


def test_ordering_of_inner_sections(xml_test_root):

    """test the group sort (i.e. groups within side title groups) (in this
    contrived test all elements have same side title). Ordering is defined in
    the word doc."""

    structure_in_wrong_order = populate_papers_data(papers_in_wrong_order)
    sorted_papers = sort_papers(structure_in_wrong_order)

    xml = convert_to_xml(sorted_papers)

    xml_str = etree.tostring(xml, encoding='unicode')

    assert xml_str == correctly_ordred_xml


# -------------------------- End sort tests -------------------------- #


def test_the_big_one(xml_test_root):

    """Test with input raw_papers_data.xml we get output as expected in
    correct_papers_for_indesign_based_on_raw_data.xml. This is basically testing
    everything."""

    filtered_papers = filter_papers(xml_test_root)

    print(f'There are {len(filtered_papers)} papers once filtered.')

    papers_data = populate_papers_data(filtered_papers)

    sorted_papers_data = sort_papers(papers_data)

    output_xml = convert_to_xml(sorted_papers_data)

    xml_str = etree.tostring(output_xml, encoding='UTF-8', xml_declaration=True)  # bytes mode

    print(xml_str[:100])

    # read in the correct xml in bytes mode

    with open('tests/correct_papers_for_indesign_based_on_raw_data.xml', 'rb') as f:
        b_str = f.read()

    assert xml_str == b_str

