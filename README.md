# abstract-assignment
Automatic abstract assignment for ESMRMB

## Procedure

Place your Claude API key in api_token.py in a variable called CLAUDE_API_KEY

Extract categories from reviewers with extract_categories.py
Create reviewer json file with reviewers2json.py
Convert abstract pdf to markdown with markitdown
Convert abstract markdown to json with parse_abstracts.py
Parse abstract json to categories with process_abstracts.py using Claude AI
Assign reviewers with assign_abstracts.py