import csv
import time
import json
from openai import OpenAI

client = OpenAI()

# ---- BIC CODE INPUT FILE ----
bic_file = "bic_codes.csv"

# ---- STEP 1: Load BIC descriptions and codes (once) ----
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
2. A list of industries with their respective BIC codes.

Your task:
- Match the company to the most appropriate industry (primary industry classification).
- You MUST select one industry from the provided list.
- If classification cannot be made, set code to "Could not be classified".
- If company descriptions are duplicated, then return the same codes.

Rules:
- Use business model description only to make classification.
- The code must only come from the provided lists.
- Do NOT guess outside the list.

Output format (VERY IMPORTANT):
Return ONLY a single JSON object, nothing else, with exactly these keys:

{
  "primary_bic_code": "....",
}
"""

# ---- Loop over multiple files ----
for i in range(2, 6):  # 0001 → 0005
    company_file = f"out_business_description/business_descriptions_{i:04d}.csv"
    output_file = f"out_classification/bic_classification_{i:04d}.csv"

    print(f"\n=== Processing {company_file} ===")
    start_time = time.time()

    # ---- STEP 3: Load companies and descriptions ----
    companies = []
    with open(company_file, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header row
        for row in reader:
            if row:
                companies.append({
                    "name": row[0],
                    "description": row[1]
                })

    # ---- STEP 4: Classify companies ----
    print("Classifying companies (this may take a moment)...")

    rows = []

    # simple cache for duplicate descriptions ⇒ same code
    desc_to_code = {}

    for c in companies:
        name = c["name"]
        desc = c["description"]

        # If description is blank → cannot classify
        if not desc or not desc.strip():
            primary_bic_code = "Could not be classified"
        else:
            # reuse code for duplicate descriptions
            if desc in desc_to_code:
                primary_bic_code = desc_to_code[desc]
            else:
                prompt = (
                    instruction +
                    "\n\nCompany Description:\n" + desc +
                    "\n\nAvailable BIC Industries:\n" + bic_text
                )

                response = client.responses.create(
                    model="gpt-5-nano",  # nano is best for this task
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
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Company Name",
            "Company Description",
            "BIC Code",
            "BIC Description"
        ])
        writer.writerows(rows)

    # ---- END TIMER ----
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = round(elapsed % 60, 2)

    print("Done. Output saved to:", output_file)
    print(f"Execution time: {minutes} min {seconds} sec")
