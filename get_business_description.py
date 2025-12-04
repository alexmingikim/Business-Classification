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
    help="Number of input CSV files to process (e.g. 900 for businesses_0001–businesses_0900.csv)",
)
args = parser.parse_args()

for i in range(1, args.num_files+1):
    os.makedirs("out_business_descriptions", exist_ok=True)
    input_file = f"raw_business_names/businesses_{i:04d}.csv"
    output_file = f"out_business_descriptions/business_descriptions_{i:04d}.csv"

    print(f"\n=== Processing {input_file} ===")

    # ---- START TIMER ----
    start_time = time.time()

    # ---- STEP 1: Load CSV and extract business names ----
    business_names = []
    with open(input_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                business_names.append(row[0])

    # ---- STEP 2: Prompt to get a description of the business model ----
    # We ask the model for JSON with a list of descriptions.
    instruction = """
    You will receive a list of business names (one per line).

    For each name, you must:
    - Do web research to find the main business model for the business.
    - Focus on New Zealand businesses first, then branch out to global sources.
    - Write a short, factual business model description of up to 3 sentences.

    Special cases:
    - If more than one distinct business exists with the exact same name, return the string:
    "Multiple businesses with the same name exist"
    - If you cannot find any reliable information, return an empty string "".
    - Do not guess based only on the name.

    Return ONLY valid JSON in this exact structure:

    {
    "descriptions": [
        "<description for business 1>",
        "<description for business 2>",
        ...
    ]
    }

    Requirements for "descriptions":
    - It MUST have exactly the same number of items as the number of business names I give you.
    - Each item must correspond, in order, to the business at the same position in the input list.
    - Do NOT include business names in the descriptions array, only the descriptions themselves.
    - No extra keys, comments, or text outside of the JSON.
    """

    prompt = instruction + "\n\nBusiness names:\n" + "\n".join(business_names)

    # ---- STEP 3: Call the model ----
    print("Sending request to AI model (this may take a moment)...")
    response = client.responses.create(
        model="gpt-5-mini",
        tools=[{"type": "web_search"}],
        input=prompt
    )

    raw_json = response.output_text

    data = json.loads(raw_json)
    descriptions = data["descriptions"]

    # ---- STEP 4: Save output CSV ----
    # Column 1: Business Name (must match input exactly)
    # Column 2: Business Description (from model)
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["BUSINESS_NAME", "BUSINESS_DESCRIPTION"])
        for name, desc in zip(business_names, descriptions):
            writer.writerow([name, desc])

    # ---- END TIMER ----
    elapsed = time.time() - start_time
    m = int(elapsed // 60)
    s = round(elapsed % 60, 2)

    print(f"Done. Output saved to {output_file}")
    print(f"Execution time: {m} min {s} sec")
