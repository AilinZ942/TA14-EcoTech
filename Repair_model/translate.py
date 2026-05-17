import argparse
import csv
from pathlib import Path
import tempfile
from typing import Optional
from deep_translator import GoogleTranslator

def is_missing(value: Optional[str]) -> bool:
    return value is None or str(value).strip() == ""




def translate_text(text: str, translator: Optional[object]) -> str:
    cleaned = str(text).strip()
    if not cleaned:
        return cleaned

    translated = translator.translate(cleaned)  # type: ignore[attr-defined]
    translated_text = str(translated).strip()
    if not translated_text:
        raise ValueError("Translator returned an empty result.")

    return translated_text


def translate_problem_csv(file_path: str | Path, output_path: str | Path) -> None:
    input_path = Path(file_path)
    destination = Path(output_path)
    translator = GoogleTranslator(source="auto", target="en")

    with input_path.open("r", encoding="utf-8", newline="") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames
        if fieldnames is None:
            raise ValueError(f"No CSV header found in {input_path}.")

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            suffix=".csv",
            delete=False,
            dir=destination.parent,
        ) as tmp_file:
            temp_path = Path(tmp_file.name)
            writer = csv.DictWriter(tmp_file, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                if "problem" in row and not is_missing(row["problem"]):
                    row["problem"] = translate_text(row["problem"], translator)
                writer.writerow(row)

    temp_path.replace(destination)

    print(f"Done: {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate the 'problem' column in a CSV to English.")
    parser.add_argument("input_csv", help="Path to the source CSV file")
    parser.add_argument("output_csv", help="Path to the translated CSV file")
    args = parser.parse_args()
    translate_problem_csv(args.input_csv, args.output_csv)
