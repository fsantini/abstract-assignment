import csv
import json
import re
from typing import List, Dict, Tuple
import anthropic

from unidecode import unidecode
from api_token import CLAUDE_API_KEY

ABSTRACT_EXPORT = 'Export_ESMRMB_2025_Abstract_20250520_141544.csv'

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

def create_parsing_prompt(text: str) -> str:
    """
    Create the prompt for Claude to parse the academic text.

    Args:
        text: The input text containing acknowledgments, data/code availability, and references

    Returns:
        Formatted prompt for Claude
    """
    prompt = f"""
Please parse the following academic text and extract three sections into a JSON structure. The text may contain acknowledgments, data and code availability statements, and references. Some sections might be missing or not clearly marked with headers.

Instructions:
1. Extract "Acknowledgments" - funding information, grants, institutional support
2. Extract "Data and Code Availability Statement" - information about data/code availability, access, repositories
3. Extract "References" as a list - each reference should be a separate item in the list
4. For references, remove any original numbering (like [1], 1., (1), etc.) and just include the reference text
5. If a section is not present, use null for that field
6. Do not modify or alter the original text - only organize it into the appropriate JSON fields
7. Infer section membership based on content when headers are unclear

Return ONLY valid JSON in this exact format:
{{
    "Acknowledgments": "text or null",
    "Data and Code Availability Statement": "text or null", 
    "References": ["reference1", "reference2", ...] or null
}}

Text to parse:
{text}
"""
    return prompt


def parse_refs(text: str):
    """
    Parse a single text using Claude API.

    Args:
        text: The academic text to parse

    Returns:
        Dictionary with parsed sections
    """
    try:
        prompt = create_parsing_prompt(text)

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=0,  # Use 0 for consistent parsing
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        response_text = message.content[0].text.strip()

        # Extract JSON from response (in case there's extra text)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        else:
            # Try to parse the entire response as JSON
            return json.loads(response_text)

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response was: {response_text}")
        return {
            "Acknowledgments": None,
            "Data and Code Availability Statement": None,
            "References": None,
            "error": f"JSON parsing failed: {str(e)}"
        }
    except Exception as e:
        print(f"API or other error: {e}")
        return {
            "Acknowledgments": None,
            "Data and Code Availability Statement": None,
            "References": None,
            "error": str(e)
        }


def parse_author_list(author_string: str) -> List[Tuple[str, str]]:
    """
    Parse an author list string into individual authors with their affiliations.

    Args:
        author_string: String containing authors with affiliations in parentheses

    Returns:
        List of tuples containing (author_name, affiliations)
    """
    authors = []

    # Pattern to match: Name (affiliations) followed by comma or end of string
    # This handles affiliations that may contain commas
    pattern = r'([^(,]+)\s*\(([^)]+)\)\s*(?:,\s*|$)'

    matches = re.findall(pattern, author_string)

    for name, affiliations in matches:
        # Clean up whitespace
        name = name.strip()
        affiliations = affiliations.strip()
        authors.append((name, affiliations))

    return authors


parentheses_re = re.compile(r'\([^)]*\)')

def remove_parentheses(line):
    return re.sub(parentheses_re, '', line)


# focus_topic, number, title, authors [list], keywords [list], general_audience_pitch [bool], text, primary_subcategory, secondary_subcategory

aff_cleanup_re = re.compile(r'^[0-9]+\.[\s,]*')
multispace_cleanup_re = re.compile(r'\s+')

with open(ABSTRACT_EXPORT, 'r', encoding='ISO-8859-15') as f:
    reader = csv.DictReader(f, delimiter=';', quotechar='"')
    abstracts = []
    row_number = 0
    for row in reader:
        if row_number > 10:
            break
        row_number += 1

        print(f"Processing row {row_number}: {row['Reference']} - {row['Titre']}")

        if row['Statut'] != 'Reviewing Pending':
            continue
        abstract = {}
        abstract['title'] = unidecode(row['Titre'])

        authors_line = re.sub(multispace_cleanup_re, ' ', unidecode(row['Auteurs']))
        authors_list = [unidecode(a.strip()) for a in authors_line.split(',')]
        abstract['authors'] = parse_author_list(authors_line)
        speaker = unidecode(row['Orateur nom'].strip())
        abstract['speaker'] = 0
        for i, (author_name, affiliations) in enumerate(abstract['authors']):
            if speaker.lower() in author_name.lower():
                abstract['speaker'] = i
                break

        affiliations = unidecode(row['Affiliations']).splitlines()
        # clean up affiliations
        abstract['affiliations'] = [re.sub(aff_cleanup_re, '', aff) for aff in affiliations if aff.strip()]


        abstract['introduction'] = unidecode(row['Résumé'])
        abstract['methods'] = unidecode(row['Methods'])
        abstract['results'] = unidecode(row['Results'])
        abstract['discussion'] = unidecode(row['Discussion'])
        abstract['conclusion'] = unidecode(row['Conclusion'])
        #refs = parse_refs(unidecode(row['Data and Code Availability Statement and References (Information not included in the word counting)']))
        refs = {}
        abstract['acknowledgments'] = refs.get('Acknowledgments', '')
        abstract['data_and_code_availability'] = refs.get('Data and Code Availability Statement', '')
        abstract['references'] = refs.get('References', [])
        abstracts.append(abstract)

        with open('abstracts_for_print.json', 'w', encoding='utf-8') as json_file:
            json.dump(abstracts, json_file, ensure_ascii=False, indent=4)