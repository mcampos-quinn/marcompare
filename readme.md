# MARCompare

This is a Flask-based webapp to compare matching MARC bibliographic records coming from (at least?) two different sources. It uses simple comparisons to point to which source has more data, which records are more complete, etc.

~in progress~

## Use case

The immediate use case is the UC System Wide ILS (Integrated Library System) where records from all University of California campus libraries will be joined in a single catalog, using Alma from ExLibris. In some cases, bibliographic records from one campus may be more complete or more detailed than matching records from another campus (matching is done via OCLC number).

This tool is designed to help with the analysis of which records should be updated with more detailed versions from another campus post-migration.

## Processing/to do

MARC files are input as JSON files created by MARCEdit. Currently I have a limited set of files to test with, so I'll need to add better handling for different formats of MARC JSON soon (coming from XML in Alma versus for example, MARC files exported from Millennium).

To dos:

* add handling for different MARC JSON formats (i.e. how tags/subfieds are handled & labeled)
* add different OCLC number match points (019, 001) and maybe offer a checkbox for each uploaded file for the user to specify where to look for OCLC#?
