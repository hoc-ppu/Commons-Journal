from copy import deepcopy
from typing import Optional

from lxml import etree  # type: ignore
from lxml.etree import QName  # type: ignore
from lxml.html.clean import Cleaner  # type: ignore


# xml namespaces used
AID = 'http://ns.adobe.com/AdobeInDesign/4.0/'
AID5 = 'http://ns.adobe.com/AdobeInDesign/5.0/'


cleaner = Cleaner(page_structure=False, links=False, remove_unknown_tags=False,
                  safe_attrs_only=False, inline_style=True,
                  remove_tags=['tr', 'thead', 'tbody', 'tfoot', 'caption'],
                  kill_tags=['colgroup', 'col'])


def html_table_to_indesign(html_table_element,
                           max_table_width: int = 466,  # this is measured in points
                           tablestyle: Optional[str] = None
                           ):
    """
    Convert an HTML table element into an InDesign XML table element.
    The html_table_element must not be an inner element of another table.
    Instread use the outer element. Tables within tables are supported.
    """

    # tables within tables should work but the only if the outermost table is given to the function
    # here is an xpath for getting only the outermost tables in an html doc
    # //table[not(ancestor::table)]

    # print(etree.tostring(html_table_element))

    # get all the table elements
    html_table_element = deepcopy(html_table_element)
    tables = html_table_element.xpath('.|.//table')

    # go through the tables backwards because there could be tables in tables...
    for table in reversed(tables):

        # is the table an inner table
        ancestor_tables = table.xpath('//ancestor-or-self::table')
        inner_table = False
        if len(ancestor_tables) > 1:
            # table is an inner table
            inner_table = True

        # convert the table element to InDesign style
        table.tag = 'Table'  # preferred tag
        table.set(QName(AID, 'table'), 'table')

        table_rows = table.xpath('tbody/tr|thead/tr|tfoot/tr|tr')

        # number of table rows
        table_rows_number = len(table_rows)
        table.set(QName(AID, 'trows'), str(table_rows_number))
        if tablestyle:
            table.set(QName(AID5, 'tablestyle'), tablestyle)

        if not table_rows:
            return table
        # find out hom many columns there are
        number_of_colls = 0
        first_row = table_rows[0].xpath('td|th')
        for cell in first_row:
            colspan = cell.get('colspan', '')
            try:
                number_of_colls += int(colspan)
            except ValueError:
                number_of_colls += 1
        table.set(QName(AID, 'tcols'), str(number_of_colls))

        for cell in first_row:
            # define col widths
            colspan = cell.get('colspan', '')
            try:
                col_width = max_table_width / number_of_colls * int(colspan)
            except ValueError:
                col_width = max_table_width / number_of_colls
            if not inner_table:
                cell.set(QName(AID, 'ccolwidth'), str(col_width))


        # convert cells to InDesign cells
        for cell in table.xpath('.//th|.//td'):

            # convert headers cells to indesign headers
            if cell.tag == 'th':  # th indicates header
                cell.set(QName(AID, 'theader'), '')
            cell.tag = 'Cell'  # preferred InDesign tag
            cell.set(QName(AID, 'table'), 'cell')

            # if spanning cols
            colspan = cell.attrib.pop('colspan', '')
            try:
                if int(colspan) > 1:
                    cell.set(QName(AID, 'ccols'), colspan)
            except ValueError:
                pass

            # if spanning rows
            rowspan = cell.attrib.pop('rowspan', '')
            try:
                if int(rowspan) > 1:
                    cell.set(QName(AID, 'crows'), rowspan)
            except ValueError:
                pass

            # remove any extra newlines frome the end
            if cell.text and cell.text[-1] == '\n':
                cell.text = cell.text[:-1]
            if cell.tail:
                cell.tail = cell.tail.strip()
            if len(cell):
                last_child = cell[-1]
                if last_child.tail:
                    last_child.tail = last_child.tail.strip()

        # delete all table rows but keep children
        for row in table_rows:
            if row.tail:
                row.tail = row.tail.strip()
            row.drop_tag()  # since we have en lxml.html element
            # drop_tag(row)

        if table.text:
            table.text = table.text.strip()

    return cleaner.clean_html(html_table_element)
    # return html_table_element


# def drop_tag(element):
    """
    Remove the tag, but not its children or text.  The children and text
    are merged into the parent.
    Example::
        >>> h = fragment_fromstring('<div>Hello <b>World!</b></div>')
        >>> h.find('.//b').drop_tag()
        >>> print(tostring(h, encoding='unicode'))
        <div>Hello World!</div>
    """
    # parent = element.getparent()
    # assert parent is not None
    # previous = element.getprevious()
    # if element.text and isinstance(element.tag, (str, bytes)):
    #     # not a Comment, etc.
    #     if previous is None:
    #         parent.text = (parent.text or '') + element.text
    #     else:
    #         previous.tail = (previous.tail or '') + element.text
    # if element.tail:
    #     if len(element):
    #         last = element[-1]
    #         last.tail = (last.tail or '') + element.tail
    #     elif previous is None:
    #         parent.text = (parent.text or '') + element.tail
    #     else:
    #         previous.tail = (previous.tail or '') + element.tail
    # index = parent.index(element)
    # parent[index:index+1] = element[:]
