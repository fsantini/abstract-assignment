import json
import csv

with open('abstracts_merged.json', 'r', encoding='utf-8') as f:
    abstracts = json.load(f)

output_list = []
for abstract in abstracts:
    if not abstract['program_number']:
        continue
    if abstract['general_audience_pitch']:
        output_list.append({
            'program_number': abstract['program_number'],
            'reference': abstract['reference'],
            'submitter': abstract['submitter'],
            'submitter_email': abstract['submitter_email'],
            'authors': ', '.join([a[0] for a in abstract['authors']]),
            'title': abstract['title'],
        })

with open('gap_list.csv', 'w', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['program_number', 'reference', 'submitter', 'submitter_email', 'authors', 'title'])
    writer.writeheader()
    for row in output_list:
        writer.writerow(row)