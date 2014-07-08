#!/usr/bin/python
from collections import OrderedDict
import sys
reload(sys)  # Reload does the trick!
sys.setdefaultencoding('UTF8')
import requests
import json
import csv
import string

ORCID_SANDBOX_API = 'https://api.sandbox.orcid.org'
ORCID_LIVE_API = 'https://api.orcid.org'
endpoints = {}
endpoints['profile'] = 'orcid-profile'
CREATE_URL_TEMPLATE = '{orcid_api}/v{schema_version}/{endpoint}'
orcid_test_email_number = 280

def load(filename):
    with open(filename, 'rb') as f:
        content = f.read()
    return content

def save(filename, content):
    with open(filename, 'wb') as f:
        f.write(content)

def load_json(fn):
    return json.loads(load(fn))

def fail(msg):
    print msg
    sys.exit(1)

class OrcidError(Exception):
    pass

def orcid_from_xml(orcid_env, rec_xml, fn, create_url, headers):
    r = requests.post(create_url, data=rec_xml, headers=headers)
    if r.status_code != 201:
        print \
'''ORCID Error:
HTTP Status code: {code}
HTTP Headers:
{headers}

HTTP Body:
{body}
'''.format(code=r.status_code, headers=r.headers, body=r.text)
        raise OrcidError('Error occurred, see above.')

    theorcid = r.headers['location'].split('/')[3]
    print '{env} ORCID created, status 201. ID: {orcid}'.format(env=orcid_env, orcid=theorcid)
    print "HTTP Headers: \n{headers}".format(headers=r.headers)
    print "HTTP Body: \n{body}".format(body=r.text)
    save(fn + '.orcid.txt', theorcid)
    return theorcid


def create_xml(schema_version, locale, given_names, family_name,
               other_names=[], biography='', email='', country='', keywords=[],
               department='', role_title='', scopus_id='', researcher_id='',
               org_name='', org_addr_city='', org_addr_region='', org_addr_country='', org_ringgold_id='',
               orcid_env='test'):

    global orcid_test_email_number

    xml = OrderedDict()
    xml['START'] = """<?xml version="1.0" encoding="UTF-8"?>
<orcid-message xmlns="http://www.orcid.org/ns/orcid"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.orcid.org/ns/orcid https://raw.github.com/ORCID/ORCID-Source/master/orcid-model/src/main/resources/orcid-message-{schema_version}.xsd">
<message-version>{schema_version}</message-version>
<orcid-profile>
""".format(schema_version=schema_version)

    xml['PREFERENCES'] = """<orcid-preferences>
    <locale>{locale}</locale>
</orcid-preferences>
""".format(locale=locale.lower())

    xml['BIO_START'] = '<orcid-bio>' + "\n"
    xml['BIO_PERSONAL_START'] = '<personal-details>' + "\n"
    if given_names: xml['BIO_GIVEN_NAMES'] = '<given-names>{given_names}</given-names>'.format(given_names=given_names) + "\n"
    if family_name: xml['BIO_FAMILY_NAME'] = '<family-name>{family_name}</family-name>'.format(family_name=family_name) + "\n"
    if other_names:
        xml['BIO_OTHER_NAMES_START'] = '<other-names visibility="public">' + "\n"
        other_names_xml = ''
        for name in other_names:
            other_names_xml += "<other-name>{name}</other-name>".format(name=name) + "\n"
        xml['BIO_OTHER_NAMES_CONTENT'] = other_names_xml
        xml['BIO_OTHER_NAMES_END'] = '</other-names>' + "\n"
    xml['BIO_PERSONAL_END'] = '</personal-details>' + "\n"
    if scopus_id or researcher_id:
        xml['BIO_EXT_IDS_START'] = '<external-identifiers>' + "\n"
        if scopus_id:
            xml['BIO_EXT_IDS_SCOPUS_START'] = '<external-identifier>' + "\n"
            xml['BIO_EXT_IDS_SCOPUS_CN'] = '<external-id-common-name>Scopus Author ID</external-id-common-name>' + "\n"
            xml['BIO_EXT_IDS_SCOPUS_REF'] = '<external-id-reference>{scopus_id}</external-id-reference>'.format(scopus_id=scopus_id) + "\n"
            xml['BIO_EXT_IDS_SCOPUS_URL'] = '<external-id-url>http://www.scopus.com/authid/detail.url?authorId={scopus_id}#</external-id-url>'.format(scopus_id=scopus_id) + "\n"
            xml['BIO_EXT_IDS_SCOPUS_END'] = '</external-identifier>' + "\n"
        if researcher_id:
            xml['BIO_EXT_IDS_RESEARCHER_ID_START'] = '<external-identifier>' + "\n"
            xml['BIO_EXT_IDS_RESEARCHER_ID_CN'] = '<external-id-common-name>ResearcherID</external-id-common-name>' + "\n"
            xml['BIO_EXT_IDS_RESEARCHER_ID_REF'] = '<external-id-reference>{researcher_id}</external-id-reference>'.format(researcher_id=researcher_id) + "\n"
            xml['BIO_EXT_IDS_RESEARCHER_ID_URL'] = '<external-id-url>http://www.researcherid.com/rid/{researcher_id}</external-id-url>'.format(researcher_id=researcher_id) + "\n"
            xml['BIO_EXT_IDS_RESEARCHER_ID_END'] = '</external-identifier>' + "\n"
        xml['BIO_EXT_IDS_END'] = '</external-identifiers>' + "\n"
    if biography: xml['BIO_BIOGRAPHY'] = '<biography visibility="public">{biography}</biography>'.format(biography=biography) + "\n"
    if email or country:
        xml['BIO_CONTACT_START'] = '<contact-details>' + "\n"
        if orcid_env == 'test':
            orcid_test_email_number += 1
            email = 'orcid-test-{0}@mailinator.com'.format(orcid_test_email_number)
        if email: xml['BIO_CONTACT_EMAIL'] = '<email primary="true" visibility="limited">{email}</email>'.format(email=email) + "\n"
        if country:
            xml['BIO_CONTACT_ADDRESS_START'] = '<address>' + "\n"
            xml['BIO_CONTACT_ADDRESS_COUNTRY'] = '<country visibility="public">{country}</country>'.format(country=country.upper()) + "\n"
            xml['BIO_CONTACT_ADDRESS_END'] = '</address>' + "\n"
        xml['BIO_CONTACT_END'] = '</contact-details>' + "\n"
    if keywords:
        xml['BIO_KEYWORDS_START'] = '<keywords visibility="public">' + "\n"
        keywords_xml = ''
        for k in keywords:
            keywords_xml += '<keyword>{keyword}</keyword>'.format(keyword=k) + "\n"
        xml['BIO_KEYWORDS_CONTENT'] = keywords_xml
        xml['BIO_KEYWORDS_END'] = '</keywords>' + "\n"
    xml['BIO_END'] = '</orcid-bio>' + "\n"

    xml['ACT_START'] = '<orcid-activities>' + "\n"
    xml['AFFILIATIONS_START'] = '<affiliations>' + "\n"
    xml['AFFILIATION_START'] = '<affiliation>' + "\n"
    xml['AFFILIATION_TYPE'] = '<type>education</type>' + "\n"
    if department: xml['AFFILIATION_DEPT'] = '<department-name>{department}</department-name>'.format(department=department) + "\n"
    if role_title: xml['AFFILIATION_ROLE'] = '<role-title>{role_title}</role-title>'.format(role_title=role_title) + "\n"
    if org_name:
        xml['AFFILIATION_ORG_START'] = '<organization>' + "\n"
        xml['AFFILIATION_ORG_NAME'] = '<name>{org_name}</name>'.format(org_name=org_name) + "\n"
        if org_addr_city or org_addr_region or org_addr_country:
            xml['AFFILIATION_ORG_ADDR_START'] = '<address>' + "\n"
            if org_addr_city: xml['AFFILIATION_ORG_ADDR_CITY'] = '<city>{org_addr_city}</city>'.format(org_addr_city=org_addr_city) + "\n"
            if org_addr_region: xml['AFFILIATION_ORG_ADDR_REGION'] = '<region>{org_addr_region}</region>'.format(org_addr_region=org_addr_region) + "\n"
            if org_addr_country: xml['AFFILIATION_ORG_ADDR_COUNTRY'] = '<country>{org_addr_country}</country>'.format(org_addr_country=org_addr_country) + "\n"
            xml['AFFILIATION_ORG_ADDR_END'] = '</address>' + "\n"
        if org_ringgold_id:
            xml['AFFILIATION_ORG_ID'] = \
'''<disambiguated-organization>
    <disambiguated-organization-identifier>{org_ringgold_id}</disambiguated-organization-identifier>
    <disambiguation-source>RINGGOLD</disambiguation-source>
</disambiguated-organization>
'''.format(org_ringgold_id=org_ringgold_id)

        xml['AFFILIATION_ORG_END'] = '</organization>' + "\n"
    xml['AFFILIATION_END'] = '</affiliation>' + "\n"
    xml['AFFILIATIONS_END'] = '</affiliations>' + "\n"
    xml['ACT_END'] = '</orcid-activities>' + "\n"

    xml['END'] = \
'''</orcid-profile>
</orcid-message>'''

    xmlstr = ''
    for k,v in xml.iteritems():
        xmlstr += v

    return xmlstr



def ingest_csv(orcid_env, fn, create_url, headers, schema_version, locale, country='', org_data={}):
    columns = OrderedDict()
    columns['orcid'] = 0
    columns['given-names'] = 1
    columns['family-name'] = 2
    columns['credit-name'] = 3
    columns['department'] = 4
    columns['role-title'] = 5
    columns['biography'] = 6
    columns['email'] = 7
    columns['keywords'] = 8  # both in the csv and in the processed record
    columns['scopus_id'] = 9
    columns['researcher_id'] = 10
    columns['other-names'] = 11  # not part of the CSVs, just how 11-16 get interpreted
    columns['other-name-1'] = 11
    columns['other-name-2'] = 12
    columns['other-name-3'] = 13
    columns['other-name-4'] = 14
    columns['other-name-5'] = 15
    columns['other-name-6'] = 16

    # 1. load the csv
    data = []
    with open(fn, 'rb') as i:
        csvreader = csv.reader(i)
        for row in csvreader:
            data.append(row)

    csv_header = data.pop(0)  # delete the header
    records = data[:]
    # 2. process the csv into records
    current_biography = ''
    current_biography_row = 0
    for row_n, row in enumerate(records):
        # concatenate biography rows together
        if (row[columns['orcid']] or row[columns['given-names']]
            or row[columns['family-name']] or row[columns['credit-name']]):

            if row_n > 0:
                # save the biography so far into the right record
                records[row_n - current_biography_row][columns['biography']] = current_biography

            current_biography = row[columns['biography']]
            current_biography_row = 1
            
        else:
            current_biography += row[columns['biography']] + "\n\n"
            current_biography_row += 1
        

        # clean up and make keywords into a list
        keywords = row[columns['keywords']]
        if keywords:
            keywords = keywords.lower()
            for c in string.punctuation:
                if c != ',':
                    keywords = keywords.replace(c, '')
            keywords = clean_list(keywords.split(','))
            row[columns['keywords']] = keywords
            
        other_names = []
        if row[columns['other-name-1']]: other_names.append(row[columns['other-name-1']])
        if row[columns['other-name-2']]: other_names.append(row[columns['other-name-2']])
        if row[columns['other-name-3']]: other_names.append(row[columns['other-name-3']])
        if row[columns['other-name-4']]: other_names.append(row[columns['other-name-4']])
        if row[columns['other-name-5']]: other_names.append(row[columns['other-name-5']])
        if row[columns['other-name-6']]: other_names.append(row[columns['other-name-6']])
        row[columns['other-names']] = clean_list(other_names)


    for row in records[:]:
        if (not row[columns['orcid']] and not row[columns['given-names']]
            and not row[columns['family-name']] and not row[columns['credit-name']]):

            records.remove(row)

    # 3. process each record into an XML file in memory
    count = 0
    results = [['ORCID', 'Family name', 'Given names', 'Email']]
    for rec in records:
        if not rec[columns['orcid']].strip():
            count += 1
            rec_xml = create_xml(
                schema_version=schema_version,
                locale=locale,
                family_name=rec[columns['family-name']],
                given_names=rec[columns['given-names']],
                other_names=rec[columns['other-names']],
                biography=rec[columns['biography']],
                email=rec[columns['email']],
                country=country,
                keywords=rec[columns['keywords']],
                department=rec[columns['department']],
                role_title=rec[columns['role-title']],
                org_name=org_data.get('name'),
                org_addr_city=org_data.get('address', {}).get('city'),
                org_addr_region=org_data.get('address', {}).get('region'),
                org_addr_country=org_data.get('address', {}).get('country'),
                org_ringgold_id=org_data.get('ringgold_id'),
                scopus_id=rec[columns['scopus_id']],
                researcher_id=rec[columns['researcher_id']],
                orcid_env=orcid_env
            )

            #print rec_xml
            #print
            #print
            #print
            try:
                rec[columns['orcid']] = 'http://orcid.org/' + orcid_from_xml(orcid_env=orcid_env, rec_xml=rec_xml, fn=rec[columns['email']], create_url=create_url, headers=headers)
            except OrcidError:
                pass
        results.append([rec[columns['orcid']], rec[columns['family-name']], rec[columns['given-names']], rec[columns['email']]])

    with open(fn + '_' + orcid_env + '_results.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(results)

    print 'Read {0} records'.format(len(records))
    print 'Created {0} ORCIDs'.format(count)



def main(argv=sys.argv):
    if len(argv) < 5:
        fail(
'''
Usage: {script} <test|live> <orcid_schema_version> <locale> <filename.xml|filename.csv> [country code] [file with organisation details.json]
Parameters in [] are optional, but if you specify any of them, you have to specify all of them. Until I upgrade this to use argparse.

E.g.: {script} test 1.2_rc3 en test.xml GB ../nottingham.json

or

{script} test 1.2_rc3 es list_of_researchers.csv ES ../cadiz.json
'''.format(script=argv[0])
)

    orcid_env = argv[1]
    if orcid_env == 'live':
        ORCID_API = ORCID_LIVE_API
        test = False
    elif orcid_env == 'test':
        ORCID_API = ORCID_SANDBOX_API
        test = True
    else:
        fail('First argument can only be "test" or "live". That is how you select whether to really create the record in production or not.')
    orcid_schema_version = argv[2]
    locale = argv[3]
    fn = argv[4]
    if len(argv) > 5:
        country = argv[5]
        if len(country) > 2:
            fail('The <country> has to be a 2-char ISO code. Like GB for the United Kingdom, or ES for Spain.')
        org_data_fn = argv[6]
    else:
        country = ''
        org_data_fn = ''


    create_url = CREATE_URL_TEMPLATE.format(orcid_api=ORCID_API, schema_version=orcid_schema_version, endpoint=endpoints['profile'])

    if test:
        credentials = load_json('../sandbox_oauth_creds.json')
    else:
        credentials = load_json('../production_oauth_creds.json')

    headers = {}
    headers['Authorization'] = credentials['token_type'].capitalize() + ' ' + credentials['access_token']
    headers['Content-Type'] = 'application/vdn.orcid+xml'
    headers['Accept'] = 'application/xml'

    if fn.endswith('.xml'):
        rec_xml = load(fn)
        orcid_from_xml(orcid_env=orcid_env, rec_xml=rec_xml, fn=fn, create_url=create_url, headers=headers)

    if fn.endswith('.csv'):
        if org_data_fn:
            org_data = load_json(org_data_fn)
        else:
            org_data = {}
        ingest_csv(orcid_env=orcid_env, fn=fn, create_url=create_url, headers=headers, schema_version=orcid_schema_version, locale=locale, country=country, org_data=org_data)


def clean_list(list):
    '''Clean up a list. Returns a list.
    Returns an empty list if given an empty list.

    How to use: clist = clean_list(your_list)

    Example: you have a list of tags. This is coming in from an HTML form
    as a single string: e.g. "tag1, tag2, ".
    You do tag_list = request.values.get("tags",'').split(",")
    Now you have the following list: ["tag1"," tag2", ""]
    You want to both trim the whitespace from list[1] and remove the empty
    element - list[2]. clean_list(tag_list) will do it.

    What it does (a.k.a. algorithm):
    1. Trim whitespace on both ends of individual strings
    2. Remove empty strings
    3. Only check for empty strings AFTER splitting and trimming the
    individual strings (in order to remove empty list elements).
    '''
    return [clean_item for clean_item in [item.strip() for item in list] if clean_item]

if __name__ == '__main__':
    main()
