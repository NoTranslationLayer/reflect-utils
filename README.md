# reflect-utils
Utilities for processing and analysis of Reflect data

## Installation

```python
pip install .
```

## JSON to CSV Converter

This script parses a JSON file of reflections into separate CSV files.

Each reflection in the JSON file will be parsed into a separate CSV file, with each reflection instance being a row and each metric being a column in the CSV file.

### Usage

Here's how to use the script:

```bash
python json_to_csv.py path_to_json_file output_directory
```

To filter only specific reflections by reflection name:

```bash
python json_to_csv.py path_to_json_file output_directory -r reflection_name1 reflection_name2 ...
```