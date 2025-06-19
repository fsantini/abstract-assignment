import os
import json
from unidecode import unidecode

with open('abstracts_for_print.json', 'r', encoding='utf-8') as f:
    abstracts = json.load(f)

IMAGE_FOLDER = '/media/bigboy2/ESMRMB2025/image/'

for abstract in abstracts:
    if abstract['figure_files']:
        for f_num, figure in enumerate(abstract['figure_files']):
            figure = unidecode(figure.replace('?', ''))
            path = os.path.join(IMAGE_FOLDER, figure)
            if not os.path.exists(path):
                print(f"Warning: Image file {figure} for abstract {abstract['reference']} does not exist at {path}.")
