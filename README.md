This downloader pulls all pdfs referenced in a csv file under the column
name url into an output directory using filenames derived from Title (Authors)
fields from the csv file.

Commands:

Install dependencies:
```bash 
make install
```
(Note: You can create a simple requirements.txt containing requests and browser_cookie3 for this target to pick up).

Run the script with default options:
```bash
make run
```
Run the script with custom parameters (e.g., overriding the default CSV file or specifying Firefox):

```bash
make run CSV_FILE=my_custom_links.csv BROWSER=firefox OUT_DIR=./my_files
```

Clean up downloaded files:
```bash
make clean
```