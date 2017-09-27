# fundamentals_crawler
A python and R based EDGAR (SEC), and Thomson-Reuters crawler that retrieves fundamental
stock data. EDGAR Crawler retrieves xml links (links to financial statements stored on sec.gov),
which are subsequently used as inputs in 'statement_parser.R'. TR_Crawler focuses on retreiving
headlines from 'https://www.reuters.com'

## Note:
When running these scripts you may have to change the filepath to your 'Downloads'
folder. Further note that we only store example links and statements in the obj folder
due to the size of files. Don't hesitate to get in touch if you experience any problems,
or if you want to contribute
