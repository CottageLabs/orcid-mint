#!/usr/bin/python
import sys
import requests
import json

ORCID_SANDBOX_API = 'https://api.sandbox.orcid.org'
ORCID_LIVE_API = 'https://api.orcid.org'
endpoints = {}
endpoints['profile'] = 'orcid-profile'
CREATE_URL_TEMPLATE = '{orcid_api}/v{schema_version}/{endpoint}'

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

def main(argv=sys.argv):
    if len(argv) < 4:
        fail(
'''
Usage: {script} test|live orcid_schema_version filename.xml
E.g.: {script} test 1.2_rc3 test.xml
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
    fn = argv[3]

    create_url = CREATE_URL_TEMPLATE.format(orcid_api=ORCID_API, schema_version=orcid_schema_version, endpoint=endpoints['profile'])

    if test:
        credentials = load_json('../sandbox_oauth_creds.json')
    else:
        credentials = load_json('../production_oauth_creds.json')

    headers = {}
    headers['Authorization'] = credentials['token_type'].capitalize() + ' ' + credentials['access_token']
    headers['Content-Type'] = 'application/vdn.orcid+xml'
    headers['Accept'] = 'application/xml'

    rec_xml = load(fn)
    r = requests.post(create_url, data=rec_xml, headers=headers)
    if r.status_code != 201:
        fail(
'''ORCID Error:
HTTP Status code: {code}
HTTP Headers:
{headers}

HTTP Body:
{body}
'''.format(code=r.status_code, headers=r.headers, body=r.text)
    )

    theorcid = r.headers['location'].split('/')[3]
    print '{env} ORCID created, status 201. ID: {orcid}'.format(env=orcid_env, orcid=theorcid)
    print "HTTP Headers: \n{headers}".format(headers=r.headers)
    print "HTTP Body: \n{body}".format(body=r.text)
    save(fn + '.orcid.txt', theorcid)

if __name__ == '__main__':
    main()
