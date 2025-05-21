import csv

with open('reviewers.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    categories = set()
    for row in reader:
        categories.update([c.strip() for c in row['Categories of interest'].lower().split(',')])

extra_categories = {
    'Brain tumors: Data and MR technology driving innovation',
    'Aligning Clinical Expectations with imaging Research in Neuro-Oncology'
}

categories.update(extra_categories)

with open('categories.txt', 'w') as f:
    for category in categories:
        f.write(category.strip() + '\n')
