import csv
import time
from openai import OpenAI

client = OpenAI()

# Loop through numbered CSVs
for i in range(61, 71):  # 0001 → 0005
    input_file = f"raw_company_names/companies_{i:04d}.csv"
    output_file = f"out_business_description/business_descriptions_{i:04d}.csv"

    print(f"\n=== Processing {input_file} ===")

    start_time = time.time()

    # ---- STEP 1: Load CSV and extract company names ----
    company_names = []
    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                company_names.append(row[0])

    # ---- STEP 2: Prompt ----
    instruction = """
    You will receive a list of company names.
    For each company, return a CSV with two columns:
    1) Company Name

    2) Business Model Description (short, factual, 3 sentences)
    Do a deep web search to find out what the main business model is, using only the given company name as the search term.
    First, focus on doing a web search for New Zealand companies then branch out to global sources.
    Consult multiple sources and business registries if needed.
    If company names are duplicated, then return same description.
    Based on web search, if more than one company exists with the same exact name given, then write: "Multiple companies with the same name exist" - no need to give the source.

    Do not guess based on company name.
    Leave empty if no information found for the given company name.

    Make sure to only output two columns.
    Output ONLY valid CSV. No extra text.
    """

    prompt = instruction + "\n\nCompanies:\n" + "\n".join(company_names)

    # ---- STEP 3: Call the model ----
    print("Sending request to AI model (this may take a moment)...")
    response = client.responses.create(
        model="gpt-5-mini",
        tools=[{"type": "web_search"}],
        input=prompt
    )

    csv_output = response.output_text

    # ---- STEP 4: Save output CSV ----
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        f.write(csv_output)

    # ---- END TIMER ----
    elapsed = time.time() - start_time
    m = int(elapsed // 60)
    s = round(elapsed % 60, 2)

    print(f"Done. Output saved to {output_file}")
    print(f"Execution time: {m} min {s} sec")
