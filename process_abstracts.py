import json
from typing import Dict, List, Any
import anthropic

from api_token import CLAUDE_API_KEY

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)


def load_data(categories_file: str, abstracts_file: str):
    """Load categories and abstracts from files."""
    # Load categories
    with open(categories_file, 'r') as f:
        categories = [line.strip() for line in f if line.strip()]

    # Load abstracts
    with open(abstracts_file, 'r') as f:
        abstracts = json.load(f)

    return categories, abstracts


def categorize_abstract(abstract: Dict[str, Any], categories: List[str]) -> Dict[str, int]:
    """Use Claude API to categorize an abstract."""

    # Prepare the prompt for Claude
    prompt = f"""
    I'm going to provide you with an academic abstract. Please analyze it and rate how well it fits into each of the following categories on a scale of 0-10.

    0 means no relevance at all
    5 means moderate relevance
    10 means extremely relevant/perfect fit

    Abstract Title: {abstract.get('title', '')}
    Abstract Keywords: {', '.join(abstract.get('keywords', []))}
    Abstract Text: {abstract.get('text', '')}

    Categories to rate (return ONLY these exact categories with their numerical scores):
    {', '.join(categories)}

    Please return your response as a JSON object with categories as keys and integer scores (0-10) as values. 
    No explanations, just the JSON object.
    """

    # Call the Claude API
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4000,
        temperature=0,
        system="You are a scientific categorization assistant. You analyze academic abstracts and rate how well they fit into given categories. Return ONLY a JSON object with categories as keys and scores (0-10) as values.",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract the JSON from the response
    response_text = response.content[0].text

    # Try to parse the JSON response
    try:
        # Clean up the response if it contains markdown code block markers
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        return json.loads(json_str)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON response: {response_text}")
        return {}


def process_abstracts(categories_file: str, abstracts_file: str, output_file: str = "categorized_abstracts.json"):
    """Process all abstracts and save results."""
    categories, abstracts = load_data(categories_file, abstracts_file)

    results = []

    for i, abstract in enumerate(abstracts):
        print(f"Processing abstract {i + 1}/{len(abstracts)}: {abstract.get('title', '')}")

        # Get category scores
        category_scores = categorize_abstract(abstract, categories)

        # Add scores to the abstract
        abstract_result = abstract.copy()
        abstract_result["category_scores"] = category_scores

        results.append(abstract_result)

        # Save intermediate results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Saved results for {i + 1}/{len(abstracts)} abstracts")

    return results


def main():
    """Main function to run the script."""
    categories_file = "categories.txt"
    abstracts_file = "abstracts.json"

    results = process_abstracts(categories_file, abstracts_file)

    print("Processing complete!")

    # Print example of categorization for the first abstract
    if results:
        title = results[0].get('title', '')
        print(f"\nExample categorization for abstract: {title}")
        for category, score in results[0].get('category_scores', {}).items():
            if score >= 5:  # Only show categories with moderate or high relevance
                print(f"{category}: {score}")


if __name__ == "__main__":
    main()