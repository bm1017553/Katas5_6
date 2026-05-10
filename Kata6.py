import pandas as pd
import os
import threading

# -----------------------------
# CONFIGURATION
# -----------------------------
INPUT_FILE = "large_dataset.csv"
OUTPUT_DIR = "filtered_output"
CHUNK_SIZE = 100_000

# Example category filters (edit as needed)
FILTERS = {
    "CONFIRMED": {"koi_disposition": "CONFIRMED"},
    "FALSE_POSITIVE": {"koi_disposition": "FALSE POSITIVE"},
    "CANDIDATE": {"koi_disposition": "CANDIDATE"},
}

# Thread lock for safe writing
write_lock = threading.Lock()


# -----------------------------
# ENSURE OUTPUT DIRECTORY EXISTS
# -----------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)


# -----------------------------
# FILTER FUNCTION
# -----------------------------
def apply_filters(df: pd.DataFrame, filter_conditions: dict):
    """
    Applies column-based filtering to a dataframe.
    filter_conditions example:
    {"koi_disposition": "CONFIRMED"}
    """
    for col, value in filter_conditions.items():
        if col in df.columns:
            df = df[df[col] == value]
    return df


# -----------------------------
# WRITE FUNCTION (THREAD SAFE)
# -----------------------------
def safe_write(df: pd.DataFrame, file_path: str, header: bool):
    with write_lock:
        df.to_csv(file_path, mode="a", index=False, header=header)


# -----------------------------
# MAIN PROCESSING FUNCTION
# -----------------------------
def process_dataset():
    print("Starting chunked processing...")

    # Track if header is written per output file
    header_written = {key: False for key in FILTERS.keys()}

    for chunk_number, chunk in enumerate(
        pd.read_csv(INPUT_FILE, chunksize=CHUNK_SIZE)
    ):
        print(f"Processing chunk {chunk_number + 1}")

        for label, conditions in FILTERS.items():
            filtered_chunk = apply_filters(chunk, conditions)

            if not filtered_chunk.empty:
                output_file = os.path.join(OUTPUT_DIR, f"{label}.csv")

                safe_write(
                    filtered_chunk,
                    output_file,
                    header=not header_written[label],
                )

                header_written[label] = True

    print("Processing complete.")


# -----------------------------
# ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    process_dataset()