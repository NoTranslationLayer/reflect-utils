# reflect-utils
Utilities for processing and analysis of Reflect data

## Installation

```python
pip install .
```

For installing in editable mode, allowing to test changes without reinstalling the package:

```python
pip install -e .
```

## JSON to CSV Converter

This script parses a JSON reflection history into separate CSV files.

Each reflection type in the JSON file will be parsed into a separate CSV file. This corresponds to a separate CSV file for each defined reflection template. Each reflection instance is a row and each metric in the reflection is a column in the resulting CSV file.

### Usage

Here's how to use the script:

```bash
python json_to_csv.py path_to_json_file output_directory
```

To filter only specific reflections by reflection name:

```bash
python json_to_csv.py path_to_json_file output_directory -r reflection_name1 reflection_name2 ...
```