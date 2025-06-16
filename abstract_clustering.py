import json
import csv
from matplotlib import pyplot as plt
from sklearn.cluster import KMeans

with open('categorized_abstracts.json', 'r') as f:
    abstracts = json.load(f)

abstract_vectors = []
n_categories = len(abstracts[0]['category_scores'])
categories = list(abstracts[0]['category_scores'].keys())

for a in abstracts:
    # Ensure all vectors are of the same length
    if len(a['category_scores']) != n_categories:
        print(f"Warning: Abstract {a['number']} has a different number of categories.")
        continue
    vector = [a['category_scores'].get(c, 0) for c in sorted(a['category_scores'].keys())]
    abstract_vectors.append(vector)
#
# inertias = []
# for k in range(1, 20):
#     kmeans = KMeans(n_clusters=k)
#     kmeans.fit(abstract_vectors)
#     inertias.append(kmeans.inertia_)
#
# plt.plot(inertias, marker='o')
# plt.show()

N_CLUSTERS = 10
kmeans = KMeans(n_clusters=N_CLUSTERS)
kmeans.fit(abstract_vectors)

centers = kmeans.cluster_centers_
labels = kmeans.labels_

cluster_infos = []
for cluster in range(N_CLUSTERS):
    cluster_info = {}
    for i, category in enumerate(categories):
        cluster_info[category] = centers[cluster][i]
    cluster_info['N'] = sum(labels == cluster)
    cluster_infos.append(cluster_info)

# save as csv
with open('clusters.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=cluster_infos[0].keys())
    writer.writeheader()
    for cluster_info in cluster_infos:
        writer.writerow(cluster_info)