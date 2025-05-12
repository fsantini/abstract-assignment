import csv
import json

reviewers = []

topic_translator = {
    'Cycle of Technology': 'emerging technologies',
    'Cycle of Translation': 'translation',
    'Cycle of Quality': 'quality, quantitation, and validation'
}

with open('reviewers.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        categories = set()
        categories.update(row['Categories of interest'].split(','))
        focus_topics = [topic_translator[f.strip()] for f in row['Are you interested in a particular focus topic?'].split(',')  if f.strip()]
        # First name,Last name,Email,Highest academic degree,Years of working experience in the MR field,Number of ESMRMB meetings attended,Categories of interest,Are you interested in a particular focus topic?
        reviewers.append({
            'first_name': row['First name'].strip(),
            'last_name': row['Last name'].strip(),
            'email': row['Email'].strip(),
            'degree': row['Highest academic degree'].strip(),
            'experience': int(float(row['Years of working experience in the MR field'])),
            'previous_meetings': int(row['Number of ESMRMB meetings attended']),
            'categories': [category.strip() for category in categories],
            'focus_topic': focus_topics
        })

with open('reviewers.json', 'w') as f:
    json.dump(reviewers, f, indent=4)