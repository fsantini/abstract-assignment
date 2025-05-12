import json
from unidecode import unidecode

TOPIC_MULTIPLIER = 1.2
MINIMUM_MATCH_SCORE = 10

def calculate_match(abstract, reviewer):
    """
    Calculate the match score between an abstract and a reviewer.
    The score is based on the number of matching categories and focus topics.
    """
    # Initialize match score
    match_score = 0

    for author in abstract['authors']:
        if unidecode(reviewer['last_name']).lower() in unidecode(author).lower():
            return 0 # avoid COIs

    # Check for matching categories
    for category, score in abstract['category_scores'].items():
        if category in reviewer['categories']:
            match_score += score

    if abstract['focus_topic'] in reviewer['focus_topic']:
        match_score *= TOPIC_MULTIPLIER

    return match_score

with open('categorized_abstracts.json', 'r') as f:
    abstracts = json.load(f)

with open('reviewers.json', 'r') as f:
    reviewers = json.load(f)

reviewer_dict = {
    (reviewer['first_name'], reviewer['last_name']): reviewer for reviewer in reviewers
}

for abstract in abstracts:
    matches = {}
    for reviewer_key, reviewer in reviewer_dict.items():
        match_score = calculate_match(abstract, reviewer)
        if match_score > MINIMUM_MATCH_SCORE:
            matches[reviewer_key] = match_score
    abstract['matches'] = matches
    print(f"Abstract {abstract['number']} matches: {len(matches)}")

