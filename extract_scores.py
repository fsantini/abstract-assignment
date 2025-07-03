import json
import csv
import re

SCORES_CSV = 'Export_ESMRMB_2025_Abstract_20250619_095047_review.csv'
CATEGORIZED_ABSTRACTS_JSON = 'categorized_abstracts_clean.json'

SCORE_NAMES = [
    'Relevance of the scientific question',
    'Methodological quality',
    'Impact of the results'
]

FT_MAP = {
    'emerging technologies' : 'Cycle of Technology',
    'translation': 'Cycle of Translation',
    'quality, quantitation, and validation': 'Cycle of Quality',
    'other': 'Other'
}

N_REVIEWERS = 3

def get_score(abstract_row, reviewer_index, score_name):
    score_key = f'{score_name} {reviewer_index + 1}'
    score = abstract_row.get(score_key, '-1.0')
    try:
        return float(score)
    except ValueError:
        return -1.0

# load categorized abstracts
with open(CATEGORIZED_ABSTRACTS_JSON, 'r', encoding='utf-8') as f:
    categorized_abstracts = json.load(f)

# load scores from CSV into a dictionary
scores_dict = {}
with open(SCORES_CSV, 'r', encoding='ISO-8859-15') as f:
    reader = csv.DictReader(f, delimiter=';', quotechar='"')
    for row in reader:
        reference = '#' + row['Reference']
        format = 'Oral' if row.get('Format souhaité', '').startswith('Oral') else 'Poster'
        comments = []
        scores = []
        n_reviewers = 0
        for i in range(N_REVIEWERS):
            reviewer_ok = False
            scores.append([])
            for score_index, score_name in enumerate(SCORE_NAMES):
                score = get_score(row, i, score_name)
                if score > 0:
                    reviewer_ok = True
                scores[i].append(score)
            if reviewer_ok:
                n_reviewers += 1
            comments.append(row.get(f'Commentaires {i + 1}', ''))
        if n_reviewers < 2:
            print(f'Warning: Abstract {reference} has less than 2 reviewers!')
        scores_dict[reference] = {
            'format': format,
            'scores': scores,
            'comments': comments
        }

# Creating output data structure
# Fields: ID, Title, Authors, Focus Topic, Main Categories, Preferred Presentation Type, ReviewerX ScoreY

multispace_cleanup_re = re.compile(r'\s+')

abstract_output = []
for abstract in categorized_abstracts:
    output_dict = {}
    reference = abstract['number']
    if reference not in scores_dict:
        print(f'Warning: No scores found for abstract {reference}')
        continue
    output_dict['ID'] = reference[1:]  # Remove the leading '#'
    output_dict['Title'] = abstract['title']
    output_dict['Authors'] = re.sub(multispace_cleanup_re, ' ', ', '.join(abstract['authors']))
    output_dict['Focus Topic'] = FT_MAP[abstract['focus_topic']]

    # find main categories
    sorted_cats = dict(sorted(abstract['category_scores'].items(), key=lambda x: x[1], reverse=True))
    main_categories = []
    max_categories = 4
    for category, score in sorted_cats.items():
        if category == 'Aligning Clinical Expectations with imaging Research in Neuro-Oncology':
            continue
        if category == 'Brain tumors: Data and MR technology driving innovation':
            continue
        if score >= 5:
            main_categories.append(category)
        if len(main_categories) >= max_categories:
            break

    output_dict['Main Categories'] = ', '.join(main_categories)
    output_dict['Preferred Presentation Type'] = scores_dict[reference]['format']
    for i in range(N_REVIEWERS):
        reviewer_scores = scores_dict[reference]['scores'][i]
        for j in range(len(SCORE_NAMES)):
            output_dict[f'Reviewer{i + 1} Score{j + 1}'] = reviewer_scores[j]
    abstract_output.append(output_dict)

# write output CSV
with open('abstract_scores_output.csv', 'w', encoding='utf-8') as csvfile:
    fieldnames = ['ID', 'Title', 'Authors', 'Focus Topic', 'Main Categories', 'Preferred Presentation Type'] + \
                 [f'Reviewer{i + 1} Score{j + 1}' for i in range(N_REVIEWERS) for j in range(len(SCORE_NAMES))]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for abstract in abstract_output:
        writer.writerow(abstract)
