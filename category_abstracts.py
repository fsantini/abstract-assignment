import json
import csv
import os
import shutil

ABSTRACTS_FOLDER = '/media/bigboy2/ESMRMB2025/abstracts/pdf/'
ABSTRACTS_BASE_OUTPUT = '/media/bigboy2/ESMRMB2025/'

## GLIMR configuration
#LIST_NAME = 'glimr'
#LIST_NAME = 'microstructure'
LIST_NAME = 'mritogether'

if LIST_NAME == 'glimr':
    CATEGORIES_OF_INTEREST = [
        'Brain tumors: Data and MR technology driving innovation',
        'Aligning Clinical Expectations with imaging Research in Neuro-Oncology',
        'brain tumors'
    ]

    KEYWORDS_OF_INTEREST = []
    SUBCATEGORIES_OF_INTEREST = []

elif LIST_NAME == 'microstructure':
    CATEGORIES_OF_INTEREST = [
        "diffusion",
        "brain physiology (modifiers)",
        "brain function",
    ]

    KEYWORDS_OF_INTEREST = [
        'diffusion',
        'microstructure',
        'relaxation',
        'glymphatic',
        'BBB',
        'blood-brain',
        'water exchange',
        'tractography',
        'connectivity',
        'white matter',
        'grey matter',
    ]
    SUBCATEGORIES_OF_INTEREST = []

elif LIST_NAME == 'mritogether':
    CATEGORIES_OF_INTEREST = [
        'open science',
        'reproducibility and validation',
    ]

    KEYWORDS_OF_INTEREST = []
    SUBCATEGORIES_OF_INTEREST = CATEGORIES_OF_INTEREST

PDF_OUTPUT_FOLDER = os.path.join(ABSTRACTS_BASE_OUTPUT, LIST_NAME)
os.makedirs(PDF_OUTPUT_FOLDER, exist_ok=True)

with open('abstracts_merged.json', 'r', encoding='utf-8') as f:
    abstracts = json.load(f)


CATEGORY_THRESHOLD = 6

output_list = []
for abstract in abstracts:
    if not abstract['program_number']:
        continue
    to_include = False
    for category in CATEGORIES_OF_INTEREST:
        if abstract['category_scores'].get(category, 0) >= CATEGORY_THRESHOLD:
            to_include = True
            break
    for keyword_of_interest in KEYWORDS_OF_INTEREST:
        for keyword_in_abstract in abstract['keywords']:
            if keyword_of_interest.lower() in keyword_in_abstract.lower():
                to_include = True
                break
        if keyword_of_interest.lower() in abstract['title'].lower():
            to_include = True
            break
    for subcategory_of_interest in SUBCATEGORIES_OF_INTEREST:
        if subcategory_of_interest.lower() in abstract['primary_subcategory'].lower() or \
           subcategory_of_interest.lower() in abstract['secondary_subcategory'].lower():
            to_include = True
            break

    if not to_include:
        continue

    abstract_to_include = {
        'program_number': abstract['program_number'],
        'reference': abstract['reference'],
        'submitter': abstract['submitter'],
        'submitter_email': abstract['submitter_email'],
        'authors': ', '.join([a[0] for a in abstract['authors']]),
        'title': abstract['title'],
        'presentation_type': abstract['presentation_type'],
        'keywords': ', '.join(abstract['keywords']),
        'primary_subcategory': abstract['primary_subcategory'],
        'secondary_subcategory': abstract['secondary_subcategory']
    }
    for category in CATEGORIES_OF_INTEREST:
        abstract_to_include[category] = abstract['category_scores'].get(category, 0)
    print(f'Including abstract {abstract["reference"]}: {abstract["title"]}')
    output_list.append(abstract_to_include)
    shutil.copy(os.path.join(ABSTRACTS_FOLDER, abstract['reference'][1:] + '.pdf'), PDF_OUTPUT_FOLDER)

with open(os.path.join(PDF_OUTPUT_FOLDER, LIST_NAME + '.csv'), 'w', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=list(output_list[0].keys()))
    writer.writeheader()
    for row in output_list:
        writer.writerow(row)