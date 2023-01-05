from lxml import etree
from lxml.etree import Element

import process_xml
from process_xml import Papers_Structure

# test the group sort (i.e. groups within side title groups)
# all elements must have same side title

draft_order_paper = etree.fromstring("""<Paper>
    <Id>35040</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Double Taxation Relief (Guernsey) Order</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Draft Double Taxation Relief (Guernsey) Order 2016</SubjectHeading>
    <Draft>true</Draft>
</Paper>""")

order_of_council = etree.fromstring("""<Paper>
    <Id>35262</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Health and Care Professions Council (Miscellaneous Amendments) Rules Order of Council</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Health and Care Professions Council (Miscellaneous Amendments) Rules Order of Council 2016</SubjectHeading>
    <Draft>false</Draft>
</Paper>""")

order = etree.fromstring("""<Paper>
    <Id>35047</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Civil Enforcement of Parking Contraventions Designation Order</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Civil Enforcement of Parking Contraventions Designation Order 2016</SubjectHeading>
    <Draft>false</Draft>
</Paper>""")

draft_regulation = etree.fromstring("""<Paper>
    <Id>35059</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Statutory Auditors and Third Country Auditors Regulations</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Draft Statutory Auditors and Third Country Auditors Regulations 2016</SubjectHeading>
    <Draft>true</Draft>
</Paper>""")

regs_ni = etree.fromstring("""<Paper>
    <Id>35107</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Social Security (Disability Living Allowance and Personal Independence Payment) (Amendment) Regulations (Northern Ireland)</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Social Security (Disability Living Allowance and Personal Independence Payment) (Amendment) Regulations (Northern Ireland) 2016</SubjectHeading>
    <Draft>false</Draft>
</Paper>""")

regulation = etree.fromstring("""<Paper>
    <Id>35056</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Control of Electromagnetic Fields at Work Regulations</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Control of Electromagnetic Fields at Work Regulations 2016</SubjectHeading>
    <Draft>false</Draft>
</Paper>""")

rules = etree.fromstring("""<Paper>
    <Id>35399</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Justices of the Peace Rules</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Justices of the Peace Rules 2016</SubjectHeading>
    <Draft>false</Draft>
</Paper>""")

accounts = etree.fromstring("""<Paper>
    <Id>35045</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Accounts of the Crown's Nominee</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Accounts of the Crown's Nominee 2015-16</SubjectHeading>
    <Draft>false</Draft>
</Paper>""")

report_and_account = etree.fromstring("""<Paper>
    <Id>35037</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Report and Accounts of the Construction Industry Training Board</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Report and Accounts of the Construction Industry Training Board 2015</SubjectHeading>
    <Draft>false</Draft>
</Paper>""")

not_grouped = etree.fromstring("""<Paper>
    <Id>36208</Id>
    <DateLaidCommons>2016-05-19T00:00:00</DateLaidCommons>
    <Title>Report on the British Wool Marketing Board Agricultural Marketing Scheme</Title>
    <SideTitle>Corporation Tax</SideTitle>
    <Year>2016</Year>
    <SubjectHeading>Report on the British Wool Marketing Board Agricultural Marketing Scheme 2015-16</SubjectHeading>
    <Draft>false</Draft>
</Paper>""")

papers_in_wrong_order = [
    accounts, order, regs_ni, report_and_account, draft_order_paper, not_grouped, draft_regulation, order_of_council, rules, regulation,
]

correctly_ordred_xml = """<PapersIndex><SideTitle>Corporation Tax</SideTitle>
<Paper>Draft Order: 2016: Draft Double Taxation Relief (Guernsey), 19 May 2016.</Paper>
<Paper>Order: 2016: Civil Enforcement of Parking Contraventions Designation, 19 May 2016.</Paper>
<Paper>Order of Council: 2016: Health and Care Professions Council (Miscellaneous Amendments) Rules, 19 May 2016.</Paper>
<Paper>Draft Regulations: 2016: Draft Statutory Auditors and Third Country Auditors, 19 May 2016.</Paper>
<Paper>Regulations: 2016: Control of Electromagnetic Fields at Work, 19 May 2016.</Paper>
<Paper>Regulations (Northern Ireland): 2016: Social Security (Disability Living Allowance and Personal Independence Payment) (Amendment), 19 May 2016.</Paper>
<Paper>Rules: 2016: Justices of the Peace, 19 May 2016.</Paper>
<Paper>Accounts, 2016: the Crown's Nominee 2015-16, 19 May 2016.</Paper>
<Paper>Reports and Accounts, 2016: the Construction Industry Training Board 2015, 19 May 2016.</Paper>
<Paper>Report on the British Wool Marketing Board Agricultural Marketing Scheme 2015-16, 19 May 2016.</Paper>
</PapersIndex>"""


output_senior_courts_xml = """<PapersIndex><SideTitle>Senior Courts of England and Wales</SideTitle>
<Paper>Rules: 2016: Civil Procedure (Amendment No. 2), 7 Jul 2016; Civil Procedure (Amendment No. 3), 21 Jul 2016; Criminal Procedure (Amendment No. 2), 7 Jul 2016; Non-Contentious Probate (Amendment), 10 Oct 2016.</Paper>
<Paper>Rules: 2017: Civil Procedure (Amendment), 3 Feb 2017; Criminal Procedure (Amendment No. 2), 13 Mar 2017; Criminal Procedure (Amendment), 20 Feb 2017.</Paper>
<Paper>Explanatory Memorandum to the Civil Procedure (Amendment) Rules 2017 (S.I., 2017, No. 95) (laid 3 February), 27 Feb 2017.</Paper>
<Paper>Explanatory Memorandum to the Civil Procedure (Amendment) Rules 2017 (S.I., 2017, No. 95), 3 Feb 2017 [withdrawn, 27 Feb 2017].</Paper>
</PapersIndex>"""

output_regs_NI_xml = """<PapersIndex><SideTitle>Social Security</SideTitle>
<Paper>Regulations (Northern Ireland): 2016: Benefit Cap (Housing Benefit and Universal Credit) (Amendment), 17 Oct 2016; Employment and Support Allowance (Sanctions) (Amendment), 13 Jun 2016; Housing Benefit (Amendment No. 2), 13 Sep 2016; Housing Benefit (Amendment), 4 Jul 2016; Industrial Injuries Benefit (Employment Training Schemes and Courses), 13 Jun 2016; Industrial Injuries Benefit (Injuries arising before 5th July 1948), 13 Jun 2016; Jobseeker’s Allowance (Sanctions) (Amendment), 13 Jun 2016; Social Security (Disability Living Allowance and Personal Independence Payment) (Amendment), 6 Jun 2016; Social Security (Expenses of Paying Sums in Relation to Vehicle Hire), 17 Oct 2016; Social Security (Miscellaneous Amendments), 19 Dec 2016; Universal Credit (Consequential, Supplementary, Incidental and Miscellaneous Provisions), 13 Jun 2016.</Paper>
<Paper>Regulations (Northern Ireland): 2017: Employment and Support Allowance (Consequential Amendments and Transitional and Savings Provisions), 14 Mar 2017; Employment and Support Allowance (Exempt Work &amp; Hardship Amounts) (Amendment), 14 Mar 2017; Housing Benefit and Universal Credit (Size Criteria) (Miscellaneous Amendments), 30 Mar 2017; Income Support (Work-Related Activity) and Miscellaneous Amendments, 20 Jan 2017; Personal Independence Payment (Amendment), 30 Mar 2017; Social Security (Restrictions on Amounts for Children and Qualifying Young Persons) (Amendment), 20 Apr 2017.</Paper>
</PapersIndex>"""


output_orders_in_council = """<PapersIndex><SideTitle>Health Care and Associated Professions</SideTitle>
<Paper>Orders of Council: 2016: General Dental Council (Fitness to Practise) (Amendment) Rules, 13 Sep 2016; Health and Care Professions Council (Miscellaneous Amendments) Rules, 1 Jul 2016.</Paper>
</PapersIndex>"""


output_account_singular = """<PapersIndex><SideTitle>National Loans</SideTitle>
<Paper>Account, 2015–16: of the Consolidated Fund 2015-16, 7 Jul 2016; of the National Loans Fund 2015-16, 7 Jul 2016.</Paper>
</PapersIndex>"""

output_law_commission = """<PapersIndex><SideTitle>Law Commissions</SideTitle>
<Paper>Report of the Law Commission: on A New Sentencing Code for England and Wales: Transition—Final Report and Recommendations, 19 May 2016; on Bills of Sale, 12 Sep 2016; on Consumer Prepayments on Retailer Insolvency, 13 Jul 2016; on Criminal Records Disclosure: Non-Filterable Offences, 31 Jan 2017; on Enforcement of Family Financial Orders, 14 Dec 2016; on Event Fees in Retirement Properties, 30 Mar 2017; on Form and Accessibility of the Law Applicable in Wales, 13 Oct 2016; on Form and Accessibility of the Law Applicable in Wales, 29 Jun 2016 [withdrawn, 13 Oct 2016]; on Mental Capacity and Deprivation of Liberty, 13 Mar 2017.</Paper>
</PapersIndex>"""

output_borders = """<PapersIndex><SideTitle>UK Borders</SideTitle>
<Paper>Report of the Independent Chief Inspector of Borders and Immigration: A re-inspection of Border Force operations at Heathrow Airport: May 2016, 8 Sep 2016; A re-inspection of the handling of Tier 4 sponsor licence compliance for July 2016, 13 Oct 2016; A short-notice inspection of the Home Office response to 'lorry drops', 21 Jul 2016; An inspection into failed right of abode applications and referral for enforcement action, 13 Oct 2016; An inspection into the extent to which the police are identifying and flagging arrested foreign nationals to the Home Office and checking their status, 13 Oct 2016; An inspection of Border Force operations at Coventry and Langley postal hubs for March-July 2016, 13 Oct 2016; An inspection of Border Force's Identification and Treatment of Potential Victims of Modern Slavery for July-October 2016, 2 Feb 2017; An Inspection of Country of Origin Information: May 2016, 21 Jul 2016; An inspection of family reunion applications, 14 Sep 2016; An inspection of the 'hostile environment' measures relating to driving licences and bank accounts for January-July 2016, 13 Oct 2016; An inspection of the Administrative Review processes introduced following the 2014 Immigration Act, 26 May 2016; An inspection of the General Register Office for England and Wales, with particular emphasis on birth records for March-June 2016, 13 Oct 2016; An Inspection of the Intelligence Functions of Border Force and Immigration Enforcement, 21 Jul 2016; The implementation of the 2014 'hostile environment' provisions for tackling sham marriage, 15 Dec 2016; Inspection of Country of Origin Information, 3 Feb 2017.</Paper>
</PapersIndex>"""

"""<PapersIndex><SideTitle>Law Commissions</SideTitle>
<Paper>Report of the Law Commission: on A New Sentencing Code for England and Wales: Transition—Final Report and Recommendations, 19 May 2016; on Bills of Sale, 12 Sep 2016; on Consumer Prepayments on Retailer Insolvency, 13 Jul 2016; on Criminal Records Disclosure: Non-Filterable Offences, 31 Jan 2017; on Enforcement of Family Financial Orders, 14 Dec 2016; on Event Fees in Retirement Properties, 30 Mar 2017; on Form and Accessibility of the Law Applicable in Wales, 13 Oct 2016; on Form and Accessibility of the Law Applicable in Wales, 29 Jun 2016 [withdrawn, 13 Oct 2016]; on Mental Capacity and Deprivation of Liberty, 13 Mar 2017.</Paper>
<Paper>Withdrawal letter for the Report of the Law Commission on Form and Accessibility of the Law Applicable in Wales, 13 Oct 2016.</Paper>
</PapersIndex>"""

# Section 6 in the word document
# Alphabetical Order – problems
output_alphabetical_side_title_sort = """<PapersIndex><SideTitle>Health and Safety</SideTitle>
<Paper>Regulations: 2016: Blood Safety and Quality (Amendment), 6 Jun 2016; Control of Electromagnetic Fields at Work, 23 May 2016; Dangerous Goods in Harbour Areas, 11 Jul 2016; Equipment and Protective Systems Intended for Use in Potentially Explosive Atmospheres, 16 Nov 2016; Simple Pressure Vessels (Safety), 16 Nov 2016.</Paper>
<Paper>Regulations: 2017: Freight Containers (Safety Convention), 13 Mar 2017; Health and Safety (Miscellaneous Amendments and Revocation), 9 Mar 2017; Health and Safety (Miscellaneous Amendments), 2 Mar 2017.</Paper>
<Paper>Explanatory Memorandum to the Blood Safety and Quality (Amendment) Regulations 2016 (S.I., 2016, No. 604) (laid 27 May), 29 Jun 2016.</Paper>
<Paper>Explanatory Memorandum to the Blood Safety and Quality (Amendment) Regulations 2016 (S.I., 2016, No. 604), 6 Jun 2016 [withdrawn, 29 Jun 2016].</Paper>
<SideTitle>Health and Safety at Work</SideTitle>
<Paper>Reports and Accounts, 2015–16: the Health and Safety Executive 2015-16, 7 Jul 2016.</Paper>
<SideTitle>Health and Social Care</SideTitle>
<Paper>Reports and Accounts, 2015–16: the Care Quality Commission 2015-16, 21 Jul 2016; the Health and Social Care Information Centre 2015-16, 21 Jul 2016; Monitor 2015-16, 21 Jul 2016; the National Institute for Health and Care Excellence 2015-16, 21 Jul 2016.</Paper>
<Paper>Consolidated Accounts of NHS Foundation Trusts 2015-16, 21 Jul 2016.</Paper>
<Paper>Report by the Care Quality Commission: The state of health care and adult social care in England 2015-16, 12 Oct 2016.</Paper>
<Paper>Report of Healthwatch England 2015-16, 17 Oct 2016.</Paper>
<SideTitle>Health and Social Work Professions</SideTitle>
<Paper>Reports and Accounts, 2015–16: the Health and Care Professions Council 2015-16, 20 Jul 2016.</Paper>
<SideTitle>Health Care and Associated Professions</SideTitle>
<Paper>Draft Orders: 2017: Draft Nursing and Midwifery (Amendment), 12 Jan 2017 [withdrawn, 25 Jan 2017]; Draft Nursing and Midwifery (Amendment), 25 Jan 2017.</Paper>
<Paper>Orders of Council: 2016: General Dental Council (Fitness to Practise) (Amendment) Rules, 13 Sep 2016; Health and Care Professions Council (Miscellaneous Amendments) Rules, 1 Jul 2016.</Paper>
<Paper>Regulations: 2016: European Qualifications (Health and Social Care Professions), 28 Oct 2016.</Paper>
<Paper>Withdrawal letter to the draft Nursing and Midwifery (Amendment) Order 2017 (laid 12 January), 25 Jan 2017.</Paper>
<SideTitle>Health Service Commissioners</SideTitle>
<Paper>Learning from Mistakes: Report by the Parliamentary and Health Service Ombudsman on an investigation into how the NHS failed to properly investigate the death of a three-year old child, 18 Jul 2016.</Paper>
<SideTitle>Healthcare and Associated Professions</SideTitle>
<Paper>Order of Council: 2016: General Pharmaceutical Council (Amendment of Miscellaneous Provisions) Rules, 21 Oct 2016.</Paper>
<SideTitle>High Speed Rail (London-West Midlands)</SideTitle>
<Paper>Promoter's Response to the Special Report from the House of Lords Select Committee on the High Speed Rail (London-West Midlands) Bill, Session 2016–17, on the High Speed Rail (London-West Midlands) Bill, 17 Jan 2017.</Paper>
</PapersIndex>"""

# section 7 sorting the word `the`
output_sorting_word_the = """<PapersIndex><SideTitle>National Health Service</SideTitle>
<Paper>Reports and Accounts, Barnsley Hospital NHS Foundation Trust, 27 Jun 2016.</Paper>
<Paper>Reports and Accounts, 2015–16: 2gether NHS Foundation Trust 2015-16, 13 Jul 2016; 5 Boroughs Partnership NHS Foundation Trust 2015-16, 20 Jun 2016; Aintree University Hospital NHS Foundation Trust 2015-16, 13 Jul 2016; Airedale NHS Foundation Trust 2015-16, 27 Jun 2016; Alder Hey Children's NHS Foundation Trust 2015-16, 4 Jul 2016; Ashford and St Peter's Hospitals NHS Foundation Trust 2015-16, 28 Jun 2016; Basildon and Thurrock University Hospitals NHS Foundation Trust 2015-16, 6 Jun 2016; Berkshire Healthcare NHS Foundation Trust 2015-16, 13 Jun 2016; Birmingham and Solihull Mental Health NHS Foundation Trust 2015-16, 13 Jun 2016; Birmingham Children's Hospital NHS Foundation Trust 2015-16, 5 Jul 2016; Birmingham Women's NHS Foundation Trust 2015-16, 11 Jul 2016; Black Country Partnership NHS Foundation Trust 2015-16, 13 Jul 2016; Blackpool Teaching Hospitals NHS Foundation Trust 2015-16, 4 Jul 2016; Bolton NHS Foundation Trust 2015-16, 6 Jun 2016; Bradford District Care NHS Foundation Trust 2015-16, 11 Jul 2016; Bradford Teaching Hospitals NHS Foundation Trust 2015-16, 29 Jun 2016; Bridgewater Community Healthcare NHS Foundation Trust 2015-16, 30 Jun 2016; Burton Hospitals NHS Foundation Trust 2015-16, 6 Jul 2016; Calderdale and Huddersfield NHS Foundation Trust 2015-16, 12 Jul 2016; Calderstones Partnership NHS Foundation Trust 2015-16, 6 Jun 2016; Cambridge University Hospitals NHS Foundation Trust 2015-16, 12 Jul 2016; Cambridgeshire and Peterborough NHS Foundation Trust 2015-16, 14 Jul 2016; Camden and Islington NHS Foundation Trust 2015-16, 6 Jul 2016; Central and North West London NHS Foundation Trust 2015-16, 6 Jul 2016; Central Manchester University Hospitals NHS Foundation Trust 2015-16, 4 Jul 2016; Chelsea and Westminster Hospital NHS Foundation Trust 2015-16, 13 Jul 2016; Cheshire and Wirral Partnership NHS Foundation Trust 2015-16, 14 Jul 2016; Chesterfield Royal Hospital NHS Foundation Trust 2015-16, 5 Jul 2016; The Christie NHS Foundation Trust 2015-16, 13 Jul 2016; City Hospitals Sunderland NHS Foundation Trust 2015-16, 20 Jun 2016; The Clatterbridge Cancer Centre NHS Foundation Trust 2015-16, 13 Jul 2016; Colchester Hospital University NHS Foundation Trust 2015-16, 6 Jul 2016; Cornwall Partnership NHS Foundation Trust 2015-16, 28 Jun 2016; Countess of Chester NHS Foundation Trust 2015-16, 6 Jul 2016; County Durham and Darlington NHS Foundation Trust 2015-16, 7 Jul 2016; Cumbria Partnership NHS Foundation Trust 2015-16, 20 Jun 2016; Derby Teaching Hospitals NHS Foundation Trust 2015-16, 5 Jul 2016; Derbyshire Community Health Services NHS Foundation Trust 2015-16, 14 Jul 2016; Derbyshire Healthcare NHS Foundation Trust 2015-16, 11 Jul 2016; Doncaster and Bassetlaw Hospitals NHS Foundation Trust 2015-16, 29 Jun 2016; Dorset County Hospital NHS Foundation Trust 2015-16, 25 May 2016; Dorset HealthCare University NHS Foundation Trust 2015-16, 13 Jul 2016; The Dudley Group NHS Foundation Trust 2015-16, 4 Jul 2016; East Kent Hospitals University NHS Foundation Trust 2015-16, 4 Jul 2016; East London NHS Foundation Trust 2015-16, 27 Jun 2016; Frimley Health NHS Foundation Trust 2015-16, 30 Jun 2016; Gateshead Health NHS Foundation Trust 2015-16, 11 Jul 2016; Gloucestershire Hospitals NHS Foundation Trust 2015-16, 27 Jun 2016; Great Ormond Street Hospital for Children NHS Foundation Trust 2015-16, 13 Jul 2016; Great Western Hospitals NHS Foundation Trust 2015-16, 5 Jul 2016; Greater Manchester West Mental Health NHS Foundation Trust 2015-16, 11 Jul 2016; Guy's and St Thomas' NHS Foundation Trust 2015-16, 5 Jul 2016; Hampshire Hospitals NHS Foundation Trust 2015-16, 27 Jun 2016; Harrogate and District NHS Foundation Trust 2015-16, 14 Jul 2016; Heart of England NHS Foundation Trust 2015-16, 12 Jul 2016; Hertfordshire Partnership University NHS Foundation Trust 2015-16, 29 Jun 2016; the Hillingdon Hospitals NHS Foundation Trust 2015-16, 28 Jun 2016; Homerton University Hospital NHS Foundation Trust 2015-16, 11 Jul 2016; Humber NHS Foundation Trust 2015-16, 14 Jun 2016; James Paget University Hospitals NHS Foundation Trust 2015-16, 6 Jun 2016; Kent Community Health NHS Foundation Trust 2015-16, 30 Jun 2016; Kettering General Hospital NHS Foundation Trust 2015-16, 13 Jun 2016; King's College Hospital NHS Foundation Trust 2015-16, 14 Jul 2016; Kingston Hospital NHS Foundation Trust 2015-16, 27 Jun 2016; Lancashire Care NHS Foundation Trust 2015-16, 14 Jun 2016; Lancashire Teaching Hospitals NHS Foundation Trust 2015-16, 6 Jul 2016; Leeds and York Partnership NHS Foundation Trust 2015-16, 14 Jul 2016; Lincolnshire Partnership NHS Foundation Trust 2015-16, 5 Jul 2016; Liverpool Heart and Chest Hospital NHS Foundation Trust 2015-16, 13 Jun 2016; Liverpool Women's NHS Foundation Trust 2015-16, 5 Jul 2016; Luton and Dunstable University Hospital NHS Foundation Trust 2015-16, 28 Jun 2016; Medway NHS Foundation Trust 2015-16, 4 Jul 2016; Mid Cheshire Hospitals NHS Foundation Trust 2015-16, 27 Jun 2016; Mid Staffordshire NHS Foundation Trust 2015-16, 13 Jun 2016; Milton Keynes University Hospital NHS Foundation Trust 2015-16, 12 Jul 2016; Moorfields Eye Hospital NHS Foundation Trust 2015-16, 12 Jul 2016; The Newcastle upon Tyne Hospitals NHS Foundation Trust 2015-16, 6 Jul 2016; NHS Blood and Transplant 2015-16, 7 Jul 2016; the NHS Business Service Authority 2015-16, 6 Jul 2016; the NHS Commissioning Board 2015-16, 21 Jul 2016; the NHS Litigation Authority 2015-16, 21 Jul 2016; the NHS Trust Development Authority 2015-16, 21 Jul 2016; Norfolk and Norwich University Hospitals NHS Foundation Trust 2015-16, 14 Jun 2016; Norfolk and Suffolk NHS Foundation Trust 2015-16, 7 Jul 2016; North East Ambulance Service NHS Foundation Trust 2015-16, 20 Jun 2016; North East London NHS Foundation Trust 2015-16, 11 Jul 2016; North Essex Partnership NHS Foundation Trust 2015-16, 11 Jul 2016; North Tees and Hartlepool NHS Foundation Trust 2015-16, 27 Jun 2016; Northamptonshire Healthcare NHS Foundation Trust 2015-16, 13 Jul 2016 [withdrawn, 18 Jul 2016]; Northamptonshire Healthcare NHS Foundation Trust 2015-16, 18 Jul 2016; Northern Lincolnshire and Goole NHS Foundation Trust 2015-16, 30 Jun 2016; Northumberland, Tyne and Wear NHS Foundation Trust 2015-16, 7 Jul 2016; Northumbria Healthcare NHS Foundation Trust 2015-16, 30 Jun 2016; Nottinghamshire Healthcare NHS Foundation Trust 2015-16, 13 Jul 2016; Oxford Health NHS Foundation Trust 2015-16, 30 Jun 2016; Oxford University Hospitals NHS Foundation Trust 2015-16, 14 Jul 2016; Oxleas NHS Foundation Trust 2015-16, 4 Jul 2016; Papworth Hospital NHS Foundation Trust 2015-16, 7 Jul 2016; Pennine Care NHS Foundation Trust 2015-16, 12 Jul 2016; Peterborough and Stamford Hospitals NHS Foundation Trust 2015-16, 4 Jul 2016 [withdrawn, 5 Sep 2016]; Peterborough and Stamford Hospitals NHS Foundation Trust 2015-16, 5 Sep 2016; Poole Hospital NHS Foundation Trust 2015-16, 4 Jul 2016; the Queen Elizabeth Hospital King's Lynn NHS Foundation Trust 2015-16, 14 Jul 2016; Queen Victoria Hospital NHS Foundation Trust 2015-16, 12 Jul 2016 [withdrawn, 5 Sep 2016]; Queen Victoria Hospital NHS Foundation Trust 2015-16, 5 Sep 2016; The Robert Jones and Agnes Hunt Orthopaedic Hospital NHS Foundation Trust 2015-16, 6 Jun 2016; Rotherham Doncaster and South Humber NHS Foundation Trust 2015-16, 7 Jul 2016; the Rotherham NHS Foundation Trust 2015-16, 12 Jul 2016; Royal Berkshire NHS Foundation Trust 2015-16, 14 Jun 2016; The Royal Bournemouth and Christchurch Hospitals NHS Foundation Trust 2015-16, 13 Jun 2016; Royal Brompton and Harefield NHS Foundation Trust 2015-16, 5 Jul 2016; Royal Devon and Exeter NHS Foundation Trust 2015-16, 11 Jul 2016; Royal Free London NHS Foundation Trust 2015-16, 6 Jul 2016; the Royal Marsden NHS Foundation Trust 2015-16, 28 Jun 2016; the Royal Orthopaedic Hospital NHS Foundation Trust 2015-16, 7 Jul 2016; Royal Surrey County Hospital NHS Foundation Trust 2015-16, 12 Jul 2016; Royal United Hospitals Bath NHS Foundation Trust 2015-16, 12 Jul 2016; Salford Royal NHS Foundation Trust 2015-16, 7 Jul 2016; Salisbury NHS Foundation Trust 2015-16, 20 Jun 2016; Sheffield Children's NHS Foundation Trust 2015-16, 11 Jul 2016; Sheffield Health and Social Care NHS Foundation Trust 2015-16, 7 Jul 2016; Sheffield Teaching Hospitals NHS Foundation Trust 2015-16, 5 Jul 2016; Sherwood Forest Hospitals NHS Foundation Trust 2015-16, 6 Jul 2016; Somerset Partnership NHS Foundation Trust 2015-16, 13 Jun 2016; South Central Ambulance Service NHS Foundation Trust 2015-16, 28 Jun 2016; South East Coast Ambulance Service NHS Foundation Trust 2015-16, 7 Jul 2016; South Essex Partnership University NHS Foundation Trust 2015-16, 13 Jul 2016; South London and Maudsley NHS Foundation Trust 2015-16, 12 Jul 2016; South Staffordshire and Shropshire Healthcare NHS Foundation Trust 2015-16, 14 Jul 2016; South Tees Hospitals NHS Foundation Trust 2015-16, 29 Jun 2016; South Tyneside NHS Foundation Trust 2015-16, 15 Jun 2016; South Warwickshire NHS Foundation Trust 2015-16, 20 Jun 2016; South West Yorkshire Partnership NHS Foundation Trust 2015-16, 20 Jun 2016; South Western Ambulance Service NHS Foundation Trust 2015-16, 13 Jul 2016; Southend University Hospital NHS Foundation Trust 2015-16, 11 Jul 2016; Southern Health NHS Foundation Trust 2015-16, 14 Jun 2016; St George's University Hospitals NHS Foundation Trust 2015-16, 30 Jun 2016; Stockport NHS Foundation Trust 2015-16, 13 Jun 2016; Surrey and Borders Partnership NHS Foundation Trust 2015-16, 13 Jul 2016; Sussex Partnership NHS Foundation Trust 2015-16, 5 Jul 2016; Tameside Hospital NHS Foundation Trust 2015-16, 7 Jul 2016; Taunton and Somerset NHS Foundation Trust 2015-16, 8 Jun 2016; The Tavistock and Portman NHS Foundation Trust 2015-16, 4 Jul 2016; Tees, Esk and Wear Valleys NHS Foundation Trust 2015-16, 30 Jun 2016; Torbay and South Devon NHS Foundation Trust 2015-16, 14 Jul 2016; University College London Hospitals NHS Foundation Trust 2015-16, 13 Jun 2016; University College London Hospitals NHS Foundation Trust 2015-16, 8 Jun 2016 [withdrawn, 13 Jun 2016]; University Hospital of South Manchester NHS Foundation Trust 2015-16, 28 Jun 2016; University Hospital Southampton NHS Foundation Trust 2015-16, 28 Jun 2016; University Hospitals Birmingham NHS Foundation Trust 2015-16, 12 Jul 2016; University Hospitals Bristol NHS Foundation Trust 2015-16, 14 Jul 2016; University Hospitals of Morecambe Bay NHS Foundation Trust 2015-16, 12 Jul 2016; The Walton Centre NHS Foundation Trust 2015-16, 15 Jun 2016; Warrington and Halton Hospitals NHS Foundation Trust 2015-16, 15 Jun 2016; West Midlands Ambulance Service NHS Foundation Trust 2015-16, 20 Jun 2016; West Suffolk NHS Foundation Trust 2015-16, 12 Jul 2016; Western Sussex Hospitals NHS Foundation Trust 2015-16, 6 Jul 2016; Wirral University Teaching Hospital NHS Foundation Trust 2015-16, 29 Jun 2016; Wrightington, Wigan and Leigh NHS Foundation Trust 2015-16, 6 Jun 2016; Yeovil District Hospital NHS Foundation Trust 2015-16, 29 Jun 2016; York Teaching Hospital NHS Foundation Trust 2015-16, 29 Jun 2016.</Paper>
</PapersIndex>"""