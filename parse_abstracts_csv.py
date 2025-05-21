import csv
import json
import re
from unidecode import unidecode

ABSTRACT_EXPORT = 'Export_ESMRMB_2025_Abstract_20250520_141544.csv'

FT_MAP = {
    '##Focus Topic: Emerging technologies||Focus Topic: Emerging technologies##': 'emerging technologies',
    '##Focus Topic: Translation||Focus Topic: Translation##': 'translation',
    '##Focus Topic: Quality, Quantitation, and Validation||Focus Topic: Quality, Quantitation, and Validation##': 'quality, quantitation, and validation',
    '##Other||Other##': 'other'
}

parentheses_re = re.compile(r'\([^)]*\)')

def remove_parentheses(line):
    return re.sub(parentheses_re, '', line)


# focus_topic, number, title, authors [list], keywords [list], general_audience_pitch [bool], text, primary_subcategory, secondary_subcategory



with open(ABSTRACT_EXPORT, 'r', encoding='ISO-8859-15') as f:
    reader = csv.DictReader(f, delimiter=';', quotechar='"')
    abstracts = []
    for row in reader:
        if row['Statut'] != 'Reviewing Pending':
            continue
        abstract = {}
        abstract['focus_topic'] = FT_MAP[row['Theme']]
        abstract['number'] = '#' + row['Reference']
        abstract['title'] = unidecode(row['Titre'])
        abstract['general_audience_pitch'] = row['?\xa0COMPETITION: I would like to participate in the General Audience Pitches Competition and, if accepted, I will submit a short video >> https://esmrmb2025.org/general-audience-pitches/'][0] == 'Y'
        authors_line = remove_parentheses(row['Auteurs'])
        authors_list = [unidecode(a.strip()) for a in authors_line.split(',')]
        abstract['authors'] = authors_list
        keywords_line = row['Mots-clefs']
        keywords_line = keywords_line.replace(';', ',')
        keywords = [unidecode(k.strip()) for k in keywords_line.split(',')]
        abstract['keywords'] = keywords
        abstract['primary_subcategory'] = unidecode(row['Primary Sub-Category'])
        abstract['secondary_subcategory'] = unidecode(row['Secondary Sub-Category'])
        abstract['text'] = 'Introduction\n' + unidecode(row['Résumé']) + \
                            '\n\nMethods\n' + unidecode(row['Methods']) + \
                            '\n\nResults\n' + unidecode(row['Results']) + \
                            '\n\nDiscussion\n' + unidecode(row['Discussion']) + \
                            '\n\nConclusion\n' + unidecode(row['Conclusion'])
        abstracts.append(abstract)

print('Number of abstracts:', len(abstracts))

# Save the abstracts to a JSON file
with open('abstracts.json', 'w', encoding='utf-8') as json_file:
    json.dump(abstracts, json_file, ensure_ascii=False, indent=4)