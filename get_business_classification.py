import os
import csv
import time
import argparse
import json
from openai import OpenAI

client = OpenAI()

# ---- ARGUMENT PARSING (number of files to process) ----
parser = argparse.ArgumentParser()
parser.add_argument(
    "--num-files",
    type=int,
    required=True,
    help="Number of input CSV files to process (e.g. 900 for companies_0001–companies_0900.csv)",
)
args = parser.parse_args()

# ---- BIC CODE INPUT FILE ----
bic_file = "bic_codes.csv"

# ---- STEP 1: Load BIC descriptions and codes ----
bic_industries = []
bic_description_lookup = {}   # for looking up industry description by code

with open(bic_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        if row:
            bic_industries.append({
                "BIC_CODE": row[0],
                "BIC_DESC": row[1]
            })
            bic_description_lookup[row[0]] = row[1]

bic_text = "\n".join([f"{i['BIC_CODE']} --- {i['BIC_DESC']}" for i in bic_industries])

# ---- STEP 2: Classification prompt ----
instruction = """
You will receive:
1. A company's business model description.
2. A list of BIC codes and the industry classifications they present.

Your task:
- Consider all BIC codes and match the company to the most appropriate BIC code based on the business model description.
- You MUST select one BIC code from the provided list.
- If classification cannot be made, set code to "Could not be classified".
- If company descriptions are duplicated, then return the same codes.

Rules:
- Interpret the entire business model description as a whole to make the classification.
- The code must only come from the provided lists.
- Do NOT guess outside the list.

Output format (VERY IMPORTANT):
Return ONLY a single JSON object, nothing else, with exactly these keys:

{
  "primary_bic_code": "....",
}
"""

for i in range(1, args.num_files+1):
    os.makedirs("out_classifications", exist_ok=True)
    business_file = f"out_business_descriptions/business_descriptions_{i:04d}.csv"
    output_file = f"out_classifications/bic_classification_{i:04d}.csv"

    print(f"\n=== Processing {business_file} ===")

    # ---- START TIMER ----
    start_time = time.time()

    # ---- STEP 3: Load business names and descriptions ----
    businesses = []
    with open(business_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header row
        for row in reader:
            if row:
                businesses.append({
                    "name": row[0],
                    "description": row[1]
                })

    # ---- STEP 4: Classify businesses ----
    print("Classifying businesses (this may take a moment)...")

    rows = []

    # simple cache for duplicate descriptions ⇒ same code
    desc_to_code = {}

    for business in businesses:
        name = business["name"]
        desc = business["description"]

        # if description is blank → cannot classify
        if not desc or not desc.strip():
            primary_bic_code = "Could not be classified"
        else:
            # reuse code for duplicate descriptions
            if desc in desc_to_code:
                primary_bic_code = desc_to_code[desc]
            else:
                prompt = (
                    instruction +
                    "\n\nBusiness Description:\n" + desc +
                    "\n\nAvailable BIC Industries:\n" + bic_text
                )

                response = client.responses.create(
                    model="gpt-5-mini",  # changed to mini
                    input=prompt
                )

                raw = response.output_text.strip()

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    # if model output is malformed, fall back to "Could not be classified"
                    data = {
                        "primary_bic_code": "Could not be classified",
                    }

                primary_bic_code = data.get("primary_bic_code") or "Could not be classified"
                desc_to_code[desc] = primary_bic_code

        # lookup descriptions for codes
        def get_bic_desc(code):
            if not code or code == "Could not be classified":
                return "Could not be classified"
            return bic_description_lookup.get(code, "Could not be classified")

        primary_bic_desc = get_bic_desc(primary_bic_code)

        rows.append([
            name,
            desc,
            primary_bic_code,
            primary_bic_desc
        ])

    # ---- STEP 5: Save output CSV ----
    # Column 1: Business Name
    # Column 2: Business Description
    # Column 3: BIC Code
    # Column 4: BIC Description
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "BUSINESS_NAME",
            "BUSINESS_DESCRIPTION",
            "BIC_CODE",
            "BIC_DESCRIPTION"
        ])
        writer.writerows(rows)

    # ---- END TIMER ----
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = round(elapsed % 60, 2)

    print("Done. Output saved to:", output_file)
    print(f"Execution time: {minutes} min {seconds} sec")
