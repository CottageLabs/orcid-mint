orcid-mint
==========

A tool for creating (minting) ORCIDs.

# Usage

## Test

    ./create_orcid.py test 1.2_rc3 es ../[dir]/[csv input] ES ../cadiz.json

Emails will be replaced by ```orcid-test-[num]@mailinator.com``` where [num] is ```orcid_test_email_number``` as defined at the top of create_orcid.py, and incremented by 1 for each successive record.

## Live

    ./create_orcid.py live 1.2_rc3 es ../[dir]/[csv input] ES ../cadiz.json > ../[dir]/live_run.log 2>&1
