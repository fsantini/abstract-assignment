import json
import csv
from abstract_csv_to_json_print import parse_author_list

def find_abstract_by_reference(abstracts, reference):
    for abstract in abstracts:
        if abstract['number'] == reference:
            return abstract
    return None

with open('abstracts_for_print_fixed.json', 'r') as f:
    abstracts_for_print = json.load(f)

with open('categorized_abstracts_clean.json', 'r') as f:
    categorized_abstracts = json.load(f)

original_exported_abstracts = {}
with open('Export_ESMRMB_2025_Abstract_20250621_093641_utf8.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';', quotechar='"')
    for row in reader:
        original_exported_abstracts['#' + row['Reference']] = row

session_assignments = {}
with open('assigned_sessions_final_cleaned.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter=';', quotechar='"')
    for row in reader:
        session_assignments['#' + row['Id']] = row

for abstract in abstracts_for_print:
    reference = abstract['reference']
    abstract_categorized = find_abstract_by_reference(categorized_abstracts, reference)
    abstract['general_audience_pitch'] = abstract_categorized['general_audience_pitch']
    abstract['category_scores'] = abstract_categorized['category_scores']
    abstract['keywords'] = abstract_categorized['keywords']
    abstract['primary_subcategory'] = abstract_categorized['primary_subcategory']
    abstract['secondary_subcategory'] = abstract_categorized['secondary_subcategory']

    exported_row = original_exported_abstracts[reference]
    abstract['submitter'] = exported_row['Soumissionaire prénom'] + ' ' + exported_row['Soumissionaire nom']
    abstract['submitter_email'] = exported_row['Soumissionaire Email']

    assignment_row = session_assignments[reference]
    abstract['program_number'] = assignment_row['Program number']
    abstract['presentation_type'] = assignment_row['Presentation type']
    abstract['focus_topic'] = assignment_row['Focus topic']
    abstract['session_number'] = assignment_row['Session number']
    abstract['session_title'] = assignment_row['Session title']
    abstract['order_in_session'] = assignment_row['Order in Session']
    authors_new = parse_author_list(exported_row['Auteurs'])
    separated_authors = []
    for (author, aff) in authors_new:
        author = author.strip()
        first_last = author.split('  ')
        if len(first_last) == 2:
            separated_authors.append((first_last[0], first_last[1]))
        else:
            separated_authors.append(('', author))
    abstract['authors_separated'] = separated_authors



with open('abstracts_merged.json', 'w', encoding='utf-8') as f:
    json.dump(abstracts_for_print, f, indent=4, ensure_ascii=False)
