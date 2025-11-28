import csv
import time
from openai import OpenAI

# ---- START TIMER ----
start_time = time.time()

client = OpenAI()

# ---- INPUT FILES ----
company_file = "out_business_description/business_descriptions_fourth25.csv" ###
industry_file = "anzsic_2006_class_codes.csv"
output_file = "out_classification/anzsic_classification_fourth25.csv"


# ---- STEP 1: Load companies and descriptions ----
companies = []
with open(company_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader, None) # skip header row
    for row in reader:
        if row:
            companies.append({
                "name": row[0],
                "description": row[1]
            })


# ---- STEP 2: Load industry descriptions and codes ----
industries = []
industry_description_lookup = {}   # for looking up industry description by code

with open(industry_file, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        if row:
            industries.append({
                "description": row[0],
                "code": row[1]
            })
            industry_description_lookup[row[1]] = row[0]

industry_text = "\n".join([f"{i['description']} --- {i['code']}" for i in industries])


# ---- STEP 3: Prompt template ----
print("Building AI prompt...")

instruction = """
You will receive:
1. A company's business model description.
2. A list of industries with their respective codes.

Your task:
- Match the company to the most appropriate industry.
- You MUST select one industry from the provided list.
- Return ONLY the ANZSIC code.
- If classification cannot be made, return the text: Could not be classified
- If company descriptions are duplicated, then return same code.

Rules:
- Use business model description only.
- Do NOT guess outside the list.
- Return only the ANZSIC code, no extra text.
"""


# ---- STEP 4: Make classifications ----
print("Classifying companies (this may take a moment)...")

rows = []

for c in companies:
    name = c["name"]
    desc = c["description"]

    # If description is blank → cannot classify
    if not desc.strip():
        anzsic_code = "Could not be classified"
        anzsic_description = "Could not be classified"
    else:
        prompt = (
            instruction +
            "\n\nCompany Description:\n" + desc +
            "\n\nAvailable Industries:\n" + industry_text +
            "\n\nReturn ANZSIC code only."
        )

        response = client.responses.create(
            model="gpt-5-nano", ###
            input=prompt
        )

        raw = response.output_text.strip()
        anzsic_code = raw

        # Lookup industry description
        if anzsic_code in industry_description_lookup:
            anzsic_description = industry_description_lookup[anzsic_code]
        else:
            anzsic_code = "Could not be classified"
            anzsic_description = "Could not be classified"

    # Save final row
    rows.append([name, desc, anzsic_code, anzsic_description])


# ---- STEP 5: Save output CSV ----
with open(output_file, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Company Name",
        "Business Model Description",
        "ANZSIC Code",
        "Industry Description"
    ])
    writer.writerows(rows)


# ---- END TIMER ----
end_time = time.time()
elapsed = end_time - start_time

minutes = int(elapsed // 60)
seconds = round(elapsed % 60, 2)

print("Done. Output saved to:", output_file)
print(f"Total execution time: {minutes} min {seconds} sec")
