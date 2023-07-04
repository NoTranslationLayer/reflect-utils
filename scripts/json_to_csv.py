import argparse
from reflect import conversions as conv


def main():
    """
    Parses a JSON file of reflections into separate CSV files.

    Each reflection in the JSON file will be parsed into a separate CSV file.
    The CSV files will be saved in the specified output directory.
    An optional list of reflection names can be provided to filter which
    reflections to save. Additionally, parsing options can be loaded from a
    YAML file.

    Command-line arguments:
    - json_path: Path to the JSON reflections file.
    - output_dir: Output directory for CSV files.
    - reflections: Optional list of reflection names to save. If not provided,
        all reflections will be saved.
    - options_file: Optional YAML file with parsing options.
    """
    parser = argparse.ArgumentParser(
        description="Parse JSON reflections and save to CSV."
    )
    parser.add_argument(
        "json_path", type=str, help="Path to the JSON reflections file."
    )
    parser.add_argument(
        "output_dir", type=str, help="Output directory for CSV files."
    )
    parser.add_argument(
        "-r",
        "--reflections",
        nargs="*",
        help="Optional list of reflection names to save.",
    )
    parser.add_argument(
        "-o",
        "--options_file",
        type=str,
        default=None,
        help="YAML file with parsing options.",
    )
    parser.add_argument(
        "-a",
        "--anonymize",
        action="store_true",
        help="Anonymize output CSV files",
    )
    parser.add_argument(
        "-n",
        "--nan",
        action="store_true",
        help="Write all values of CSV to NaN when anonymizing",
    )

    args = parser.parse_args()

    with open(args.json_path, "r") as f:
        json_string = f.read()

    if args.options_file:
        with open(args.options_file, "r") as f:
            options_yaml = f.read()
        options = conv.load_parsing_options_from_yaml(options_yaml)
    else:
        options = conv.ParsingOptions()

    reflections_map = conv.parse_json(json_string, options)
    conv.save_dataframes_to_csv(
        reflections_map,
        args.output_dir,
        do_anonymize=args.anonymize,
        set_all_nan=args.nan,
        filter_list=args.reflections,
    )


if __name__ == "__main__":
    main()
