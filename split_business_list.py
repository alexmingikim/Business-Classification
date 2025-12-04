import os
import csv
import argparse

# ---- ARGUMENT PARSING ----
parser = argparse.ArgumentParser(
    description=(
        "Split a CSV file containing business names into multiple CSV files "
        "with 20 rows each, saved as raw_business_names/businesses_{i:04d}.csv"
    )
)
parser.add_argument(
    "--input-file",
    type=str,
    required=True,
    help="Path to the input CSV file.",
)
parser.add_argument(
    "--column-name",
    type=str,
    default=None,
    help=(
        "Name of the column containing business names. "
        "If not provided, the script will use the only column if exactly one exists; "
        "otherwise it will raise an error."
    ),
)
parser.add_argument(
    "--chunk-size",
    type=int,
    default=20,
    help="Number of business names per output file (default: 20).",
)
args = parser.parse_args()

input_file = args.input_file
column_name = args.column_name
chunk_size = args.chunk_size

# ---- OUTPUT DIRECTORY ----
output_dir = "raw_business_names"
os.makedirs(output_dir, exist_ok=True)

# ---- READ BUSINESS NAMES FROM INPUT ----
business_names = []

with open(input_file, "r", newline="", encoding="utf-8") as f:
    # column name provided
    if column_name:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError("Input file appears to be empty or missing a header row.")

        if column_name not in reader.fieldnames:
            raise ValueError(
                f'Column "{column_name}" not found in input file. '
                f"Available columns: {reader.fieldnames}"
            )

        for row in reader:
            name = (row.get(column_name) or "").strip()
            if name:
                business_names.append(name)
    else:
        # no column name provided: infer behavior based on number of columns
        reader = csv.reader(f)
        header = next(reader, None)

        if header is None:
            print("Input file is empty. Exiting.")
            exit(0)

        if len(header) == 1:
            # single-column CSV: treat the only column as the business name column
            for row in reader:
                if not row:
                    continue
                name = (row[0] or "").strip()
                if name:
                    business_names.append(name)
        else:
            # multiple columns but no column name specified -> ask user to specify
            raise ValueError(
                "Input file has multiple columns but no --column-name was provided. "
                f"Available columns: {header}"
            )

if not business_names:
    print("No business names found in input file. Exiting.")
    exit(0)

# ---- SPLIT INTO CHUNKS AND WRITE OUTPUT FILES ----
file_index = 1
for start_idx in range(0, len(business_names), chunk_size):
    chunk = business_names[start_idx:start_idx + chunk_size]

    output_path = os.path.join(
        output_dir,
        f"businesses_{file_index:04d}.csv"
    )

    with open(output_path, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.writer(out_f)
        # write rows
        for name in chunk:
            writer.writerow([name])

    file_index += 1

print(f"Done. Generated {file_index - 1} file(s) in '{output_dir}'.")
