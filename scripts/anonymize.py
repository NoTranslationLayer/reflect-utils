import json
import random
import argparse
from nltk.corpus import words, wordnet
from pathlib import Path

# Generate a list of nouns and adjectives
nouns = {x.name().split(".", 1)[0] for x in wordnet.all_synsets("n")}
adjectives = {x.name().split(".", 1)[0] for x in wordnet.all_synsets("a")}
words_list = list(nouns | adjectives)


def generate_random_word():
    word = random.choice(words_list)
    return " ".join(part.capitalize() for part in word.split("_"))


def update_values(data, word_map):
    if isinstance(data, list):
        for i in range(len(data)):
            if isinstance(data[i], str):
                if data[i] not in word_map:
                    word_map[data[i]] = generate_random_word()
                data[i] = word_map[data[i]]
            else:
                update_values(data[i], word_map)
    elif isinstance(data, dict):
        for key, value in data.items():
            if key in ["name", "group"] and value != "":
                if value not in word_map:
                    word_map[value] = generate_random_word()
                data[key] = word_map[value]
            elif key == "choices" and isinstance(value, list):
                data[key] = [generate_random_word() for _ in value]
            else:
                update_values(value, word_map)
    return data


def main(input_file, output_file):
    # Load the JSON file
    with open(input_file) as f:
        data = json.load(f)

    group_map = {}
    # Update the values
    updated_data = update_values(data, group_map)

    # Write to the new JSON file
    with open(output_file, "w") as f:
        json.dump(updated_data, f, indent=4)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="The path of the input JSON file")
    parser.add_argument(
        "-o", "--output_file", help="The path of the output JSON file"
    )

    args = parser.parse_args()

    if args.output_file is None:
        # If no output file is provided, use the input file name with '_anonymized' appended
        input_path = Path(args.input_file)
        args.output_file = input_path.stem + "_anonymized" + input_path.suffix

    main(args.input_file, args.output_file)
