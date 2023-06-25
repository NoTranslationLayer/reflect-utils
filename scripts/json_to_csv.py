import argparse
from reflect import conversions as conv


def main():
    """
    Parses a JSON file of reflections into separate CSV files.

    Each reflection in the JSON file will be parsed into a separate CSV file.
    The CSV files will be saved in the specified output directory.
    An optional list of reflection names can be provided to filter which 
    reflections to save.

    Command-line arguments:
    - json_path: Path to the JSON reflections file.
    - output_dir: Output directory for CSV files.
    - reflections: Optional list of reflection names to save. If not provided, 
        all reflections will be saved.
    - default_value: Optional default value for unrecorded metrics.
    """
    parser = argparse.ArgumentParser(description='Parse JSON reflections and save to CSV.')
    parser.add_argument('json_path', type=str, help='Path to the JSON reflections file.')
    parser.add_argument('output_dir', type=str, help='Output directory for CSV files.')
    parser.add_argument('-r', '--reflections', nargs='*', help='Optional list of reflection names to save.')
    parser.add_argument('-d', '--default_value', type=str, default=None, help='Default value for unrecorded metrics.')

    args = parser.parse_args()

    with open(args.json_path, 'r') as f:
        json_string = f.read()

    reflections_map = conv.parse_json(json_string, default_value=args.default_value)
    conv.save_dataframes_to_csv(reflections_map, args.output_dir, args.reflections)

if __name__ == "__main__":
    main()
