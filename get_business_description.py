import csv
import time
from openai import OpenAI

# ---- START TIMER ----
start_time = time.time() 

client = OpenAI()

# ---- STEP 1: Load CSV and extract company names ----
input_file = "fourth25companies.csv"  ### 
output_file = "out_business_description/business_descriptions_fourth25.csv" ###
company_names = []

with open(input_file, "r", newline="", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        if row:
            company_names.append(row[0])

# ---- STEP 2: Prompt template ----
print("Building AI prompt...")

instruction = """
You will receive a list of company names.
For each company, return a CSV with two columns:
1) Company Name

2) Business Model Description (short, factual, 3 sentences)
Do a web search to find accurate information on what the main business model is.
Consult multiple sources if needed.
Do not guess based on company name.
Leave empty if no information found.
If company names are duplicated, then return same description.

Output ONLY valid CSV. No extra text.
"""
##3) Flag True if company description was found, otherwise, flag False.

prompt = instruction + "\n\nCompanies:\n" + "\n".join(company_names)

# ---- STEP 3: Call the model ----
print("Sending request to AI model (this may take a moment)...")
response = client.responses.create(
    model="gpt-5-mini", ###
    tools=[{"type": "web_search"}],
    input=prompt
)

csv_output = response.output_text

# ---- STEP 4: Save output CSV ----
with open(output_file, "w", newline="", encoding="utf-8") as f:
    f.write(csv_output)

# ---- END TIMER ----
end_time = time.time()
elapsed = end_time - start_time

minutes = int(elapsed // 60)
seconds = round(elapsed % 60, 2)

print("Done. Output saved to:", output_file)
print(f"Total execution time: {minutes} min {seconds} sec")
