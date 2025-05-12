import json
from unidecode import unidecode
import re

abstracts = []

STATUS_NEWABSTRACT = 1
STATUS_TITLE = 2
STATUS_POST_TITLE = 3
STATUS_PRE_AUTHORS = 4
STATUS_AUTHORS = 5
STATUS_POST_AUTHORS = 6
STATUS_TEXT = 7
current_abstract = None
status = None

parentheses_re = re.compile(r'\([^)]*\)')

def remove_parentheses(line):
    return re.sub(parentheses_re, '', line)

with (open('abstracts.md', 'r') as f):
    for line in f:
        line = line.strip()
        if line.startswith('FOCUS TOPIC: ') or line == 'OTHER':
            status = STATUS_NEWABSTRACT
            # close the previous abstract
            if current_abstract:
                abstracts.append(current_abstract)
                print(current_abstract)
            # create a new abstract
            current_abstract = {}
            if line == 'OTHER':
                current_abstract['focus_topic'] = 'other'
            else:
                current_abstract['focus_topic'] = line.split(': ')[1].lower()
                if current_abstract['focus_topic'] == 'quality, quantitation,':
                    current_abstract['focus_topic'] = 'quality, quantitation, and validation'
            continue
        if status == STATUS_TEXT:
            if line.startswith('Data and Code Availability'):
                # close the abstract
                abstracts.append(current_abstract)
                current_abstract = None
                status = None
                continue
            if line:
                current_abstract['text'] += unidecode(line + '\n')
            continue
        if status == STATUS_NEWABSTRACT:
            if not line.startswith('#'):
                # bogus lines
                continue
            current_abstract['number'] = line.split(' ')[0]
            current_abstract['title'] = unidecode(line[line.find(' : ') + len(' : '):].strip())
            status = STATUS_TITLE
            continue
        if status == STATUS_TITLE:
            if not line:
                status = STATUS_POST_TITLE
                continue
            current_abstract['title'] += unidecode(' ' + line)
        if status == STATUS_POST_TITLE:
            if line.startswith('Authors:'):
                status = STATUS_PRE_AUTHORS
                authors_line = ''
                continue
        if status == STATUS_PRE_AUTHORS:
            if line:
                authors_line += line + ' '
                status = STATUS_AUTHORS
                continue
        if status == STATUS_AUTHORS:
            if line:
                authors_line += line + ' '
                continue

            # process authors
            authors_line = remove_parentheses(authors_line)
            authors_list = [unidecode(a.strip()) for a in authors_line.split(',')]
            current_abstract['authors'] = authors_list
            status = STATUS_POST_AUTHORS
        if status == STATUS_POST_AUTHORS:
            if line.startswith('Keywords'):
                keyword_line = line[len('Keywords: '):]
                keyword_line = keyword_line.replace(';', ',')
                keywords = [unidecode(k.strip()) for k in keyword_line.split(',')]
                current_abstract['keywords'] = keywords
            if line.startswith('Primary Sub-Category: '):
                current_abstract['primary_subcategory'] = line[len('Primary Sub-Category: '):].strip()
            if line.startswith('Secondary Sub-Category: '):
                current_abstract['secondary_subcategory'] = line[len('Secondary Sub-Category: '):].strip()
            if line.startswith('>> http://esmrmb2025.org/general-audience-pitches/:'):
                if line[len('>> http://esmrmb2025.org/general-audience-pitches/: ')] == 'Y':
                    current_abstract['general_audience_pitch'] = True
                else:
                    current_abstract['general_audience_pitch'] = False
            if line.startswith('Introduction'):
                current_abstract['text'] = unidecode(line.strip() + '\n')
                status = STATUS_TEXT

with (open('abstracts.json', 'w') as f):
    json.dump(abstracts, f, indent=4)