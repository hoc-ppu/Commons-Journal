#!/usr/bin/env python3

from copy import deepcopy
import re
from typing import List, Optional

from lxml import etree
from lxml import html
from lxml.etree import SubElement
from lxml.html import HtmlElement


HTML_SECTIONS: List[HtmlElement] = []


class Section:
    section_template = html.fromstring(
        '<section class="collapsible journalDay"></section>'
    )
    collapsible_header_template = html.fromstring(
        '<div class="collapsible-header"></div>'
    )
    collapsible_content_template = html.fromstring(
        '<div class="collapsible-content"></div>'
    )

    def __init__(self, heading_element: HtmlElement, junk_section: bool = False):
        self.junk_section = junk_section

        self.element = deepcopy(self.section_template)
        self.header = deepcopy(self.collapsible_header_template)
        self.content = deepcopy(self.collapsible_content_template)

        arrow = html.fromstring('<span class="arrow"> </span>')
        # heading_element.insert(0, arrow)
        arrow.tail = heading_element.text
        heading_element.text = ""
        heading_element.insert(0, arrow)

        self.header.append(heading_element)

        self.element.extend((self.header, self.content))

        if not junk_section:
            HTML_SECTIONS.append(self.element)

    def append(self, element: HtmlElement):
        self.content.append(element)

    def add_short_line(self):
        line_e = html.Element("hr")
        line_e.tail = "\n"
        line_e.classes.add("shortRule")
        self.content.append(line_e)

    def add_long_line(self):
        line_e = html.Element("hr")
        line_e.tail = "\n"
        line_e.classes.add("longRule")
        self.content.append(line_e)


def main():

    template_tree = html.parse("Journal_HTML_template.html")
    template_root = template_tree.getroot()
    content_container = template_root.find(".//*[@id='content-goes-here']")

    input_tree = html.parse("test-2016-17-Journal-Body_Part1.html")
    root = input_tree.getroot()

    # content_sections = []
    section = Section(
        html.fromstring(
            '<h3 style="color: red;">This heading should not be here!</h3>'
        ),
        junk_section=True,  # we do not want this adding to the output
    )

    day_number: Optional[str] = None

    first_section_found = False

    for element in root.xpath(".//div/*"):
        # remove lang attribute (inc. en_gb) from elements
        element.attrib.pop("lang", None)

        # BodyIndented is pretty much just the body copy
        # so the class can be removed and left as a <p>
        element.classes.discard("BodyIndented")

        if "Journal_DaySep" in element.classes:
            # make a note of the number as this will need to be added after
            # the date heading
            day_number = element.text_content().strip()
            continue

        if "Journal_VotesDate" in element.classes:
            # Journal_VotesDate represents a new section
            section = Section(element)
            if first_section_found:
                section.add_long_line()
            else:
                first_section_found = True

            element.tag = "h3"

            # first add the rule, then the heading and immediately after
            # add the day number
            if day_number:
                day_number_e = html.Element("p")
                day_number_e.classes.add("dayNumber")
                day_number_e.text = day_number
                section.append(day_number_e)
                day_number = None
            else:
                print(
                    f"Warning: no day number found for heading '{element.text_content()}'"
                )

            # must continue here as we don't want to add the element again
            continue

        if set(
            ("Journal_Vote-Item-Numbered", "Journal_Vote-Item-Numbered-Restart")
        ).intersection(element.classes):
            # element.classes.add('mt-5')  # no longer needed
            # numbered spans
            for span in element.xpath("span[contains(@class, '_idGenBNMarker')]"):
                span.classes.add("charBallotNumber")
                span.tag = "strong"

        elements_promoted_to_h4 = {"Journal_Line-Above", "Journal_Heading-Line-Before"}
        if elements_promoted_to_h4.intersection(element.classes):
            element.tag = "h4"

        # budget_resolutions
        budget_resolution_classes = {
            "Budget-Resolutions_outdent2",
            "Budget-Resolutions_outdent3",
            "Budget-Resolutions_outdent4",
            "Budget-Resolutions_outdent5",
        }
        if budget_resolution_classes.intersection(element.classes):
            if not element.text:
                print(
                    f"Warning: budget resolution has no text.\n{etree.tostring(element)}"
                )

            match = re.match(r"\t+.?\([A-Za-z0-9]+\)\t", element.text)
            if match:
                para_num_span = SubElement(element, "span")
                para_num_span.classes.add("para_num")
                para_num_span.text = match.group(0).strip()
                para_num_span.tail = element.text[len(match.group(0)) :].strip()
                element.text = ""

        short_line_classes = {
            "Journal_Line-Above",
            "Journal_Line-Below",
            "Journal_SpeakersCertificates",
            "Journal_Heading-Line-Before",
        }
        if short_line_classes.intersection(element.classes):
            # these headings need a line before
            section.add_short_line()

        # fix any spans
        section.append(element)

    for section in HTML_SECTIONS:
        section.append(html.fromstring(("<hr class='longRule'/>")))

    content_container.extend(HTML_SECTIONS)

    process_spans(content_container)
    fix_tables(content_container)

    template_tree.write("output.html", encoding="utf-8")
    print("done")


def process_spans(element: HtmlElement):
    # numbered spans
    for span in element.xpath(".//span|.//strong"):
        # if span.classes == set(("DateForHeader",)):
        if "DateForHeader" in span.classes:
            # if DateForHeader is the only class, remove tag,
            # keep text children and tail text
            span.drop_tag()

        # convert <span class="Bold"> to <strong>
        if "Bold" in span.classes:
            span.tag = "strong"
        if span.tag == "strong":
            span.classes.discard("Bold")

        # convert <span class="Italic"> to <em>
        if "Italic" in span.classes:
            span.tag = "em"
        if span.tag == "em":
            span.classes.discard("Italic")


def fix_tables(element: HtmlElement):
    # tables
    for table in element.xpath(".//table"):
        table.classes.add("table")
        table.classes.add("table-hover")
        for decentant in table.iterdescendants():
            # remove redundant classes
            decentant.classes -= table.classes
            # set(decentant.classes).difference(set(table.classes))


if __name__ == "__main__":
    main()
