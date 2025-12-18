from copy import deepcopy
from typing import Optional

from lxml import etree
from lxml.etree import QName
from lxml.html import HtmlElement

from journal.logger import logger

# xml namespaces used
AID = 'http://ns.adobe.com/AdobeInDesign/4.0/'
AID5 = 'http://ns.adobe.com/AdobeInDesign/5.0/'


def clean_table(html_table_element: HtmlElement):
    """
    Clean the table element. This is needed to remove any extra tags that
    are not needed in the final InDesign table and unnecessary style attributes.
    """

    # remove any style attributes
    etree.strip_attributes(html_table_element, 'style')

    tags_to_remove = ['tr', 'thead', 'tbody', 'tfoot', 'caption']
    tags_to_kill = ['colgroup', 'col']

    elements_to_drop_tag: list[HtmlElement] = []
    elements_to_drop_tree: list[HtmlElement] = []

    for element in html_table_element.iter():
        if element.tag in tags_to_remove:
            elements_to_drop_tag.append(element)
        if element.tag in tags_to_kill:
            elements_to_drop_tree.append(element)

    for element in elements_to_drop_tag:
        # this usually works even if the element is not in the tree
        try:
            element.drop_tag()
        except Exception as e:
            logger.error(f'Error while dropping tag: {e}')

    for element in elements_to_drop_tree:
        # this usually works even if the element is not in the tree
        try:
            element.drop_tree()
        except Exception as e:
            logger.error(f'Error while dropping tree: {e}')

    return html_table_element


def html_table_to_indesign(
    html_table_element,
    max_table_width: int = 233,  # this is measured in points
    tablestyle: Optional[str] = None,
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
                # print(f'{col_width=}')

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

            # Not sure about the below optional bit
            # optionally put all the cell content into a <TableBodyPara> element as
            # this is easier to style in InDesign
            if cell.text or cell.tail or len(cell):
                para = etree.Element(QName(AID, 'TableBodyPara'))
                para.text = cell.text or ''
                para.tail = cell.tail or ''
                # remove the text and tail from the cell
                cell.text = None
                cell.tail = None
                # add the para to the cell
                cell.append(para)
                # move the children of the cell to the para
                para.extend(list(cell))

        # delete all table rows but keep children
        for row in table_rows:
            if row.tail:
                row.tail = row.tail.strip()
            row.drop_tag()  # since we have en lxml.html element
            # drop_tag(row)

        if table.text:
            table.text = table.text.strip()

    return clean_table(html_table_element)

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
