from api_token import CLAUDE_API_KEY
import anthropic
import json

from abstract_csv_to_json_print import parse_refs

with open('abstracts_for_print.json', 'r') as f:
    abstracts = json.load(f)

for abstract in abstracts:
    if abstract['acknowledgments'] == "PARSE FAILED":
        print(f"Re-parsing abstract {abstract['reference']} due to failed acknowledgment parsing.")
        parsed_refs = parse_refs(abstract['original_availability'])
        abstract['acknowledgments'] = parsed_refs.get('Acknowledgments', '')
        abstract['data_and_code_availability'] = parsed_refs.get('Data and Code Availability Statement', '')
        abstract['references'] = parsed_refs.get('References', [])

with open('abstracts_for_print.json', 'w', encoding='utf-8') as f:
    json.dump(abstracts, f, indent=4, ensure_ascii=False)
