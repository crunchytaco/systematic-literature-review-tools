import os
import csv
import argparse
import re
import requests
import browser_cookie3
from urllib.parse import urlparse

def validate_csv(csv_path):
    """Checks if the file exists and contains the required columns."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Error: The file '{csv_path}' does not exist.")

    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames

            if not fieldnames:
                raise ValueError(f"Error: The CSV file '{csv_path}' appears to be empty or improperly formatted.")

            # Check for the mandatory URL column (case-insensitive)
            url_field = next((field for field in fieldnames if field.strip().lower() == 'url'), None)
            if not url_field:
                raise ValueError(
                    f"Error: Could not find a required 'url' column in '{csv_path}'. "
                    f"Found columns: {list(fieldnames)}"
                )

            return url_field, fieldnames

    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        raise RuntimeError(f"Error reading CSV file '{csv_path}': {e}")

def download_files(csv_path, output_dir, browser_name="chrome"):
    # --- 1. PRE-FLIGHT CSV VALIDATION ---
    print(f"Validating CSV file: {csv_path}...")
    url_field, fieldnames = validate_csv(csv_path)
    print(f"CSV validation successful! Found URL column: '{url_field}'")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # --- 2. BROWSER COOKIES & SESSION SETUP ---
    print(f"Loading cookies from {browser_name}...")
    try:
        if browser_name.lower() == "firefox":
            cj = browser_cookie3.firefox()
        elif browser_name.lower() == "edge":
            cj = browser_cookie3.edge()
        elif browser_name.lower() == "safari":
            cj = browser_cookie3.safari()
        else:
            cj = browser_cookie3.chrome()
    except Exception as e:
        print(f"Warning: Could not load browser cookies automatically ({e}). Proceeding without them.")
        cj = None

    session = requests.Session()
    if cj:
        session.cookies = cj

    # Add realistic browser headers to bypass bot protection (418 / blocks)
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    })

    # --- 3. EXECUTE DOWNLOADS ---
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        success_count = 0
        error_count = 0

        for row_idx, row in enumerate(reader, start=1):
            raw_url = row.get(url_field, "").strip()
            if not raw_url:
                print(f"Row {row_idx}: Skipped (empty URL)")
                continue

            # Transform wrapper/landing page URLs into direct PDF download endpoints
            if "ieeexplore.ieee.org/stamp/stamp.jsp" in raw_url:
                arnumber_match = re.search(r'arnumber=(\d+)', raw_url)
                if arnumber_match:
                    pdf_url = f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber={arnumber_match.group(1)}"
                else:
                    pdf_url = raw_url
            elif "link.springer.com/article/" in raw_url:
                pdf_url = raw_url.replace("/article/", "/content/pdf/") + ".pdf"
            else:
                pdf_url = raw_url

            try:
                print(f"Downloading (Row {row_idx}): {pdf_url}")
                response = session.get(pdf_url, stream=True, timeout=30)
                response.raise_for_status()

                # Warn if server response is HTML instead of an actual PDF file
                content_type = response.headers.get("content-type", "").lower()
                if "pdf" not in content_type and "octet-stream" not in content_type:
                    print(f"⚠️ Warning: Row {row_idx} may not have returned a PDF (Content-Type: {content_type})")

                filename = None

                # 1. Try to get filename from Content-Disposition header (original file name)
                content_disposition = response.headers.get("content-disposition")
                if content_disposition and "filename=" in content_disposition:
                    fname_match = re.findall(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', content_disposition)
                    if fname_match:
                        filename = fname_match[0]

                # 2. Fallback: Document Title (Authors)
                if not filename or "stamp" in filename or filename.endswith(".jsp"):
                    title = row.get("Document Title", row.get("Item Title", row.get("Title", "")))
                    authors = row.get("Authors", row.get("Author", ""))

                    if title and authors:
                        fallback_str = f"{title} ({authors})"
                    elif title:
                        fallback_str = title
                    else:
                        fallback_str = f"file_{row_idx}"

                    # Clean up invalid filename characters (excluding colons)
                    safe_filename = "".join(c if c.isalnum() or c in (' ', '-', '_', '(', ')') else '_' for c in fallback_str)[:150].strip()
                    filename = f"{safe_filename}.pdf"

                file_path = os.path.join(output_dir, filename)

                # Write the file chunks to disk
                with open(file_path, "wb") as out_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            out_file.write(chunk)

                print(f"Saved: {file_path}")
                success_count += 1

            except Exception as e:
                print(f"Error downloading row {row_idx} ({raw_url}): {e}")
                error_count += 1

    print(f"\nDownload complete! Successfully downloaded: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download files from URLs in a CSV column using browser session cookies.")
    parser.add_argument("infile", help="Path to the input CSV file")
    parser.add_argument("outdir", help="Directory where files should be saved")
    parser.add_argument("--browser", default="chrome", help="Browser to pull cookies from (chrome, firefox, edge, safari)")

    args = parser.parse_args()
    download_files(args.infile, args.outdir, args.browser)