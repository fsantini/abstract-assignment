import csv

with open('reviewers.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    categories = set()
    for row in reader:
        categories.update(row['Categories of interest'].split(','))

with open('categories.txt', 'w') as f:
    for category in categories:
        f.write(category.strip() + '\n')