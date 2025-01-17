import sys
import os
import math
import numpy as np

from sklearn.cluster import MiniBatchKMeans, AgglomerativeClustering


def k_means_cluster_atoms(points, num_clusters=10):
    """
    Cluster atoms using KMeans
    """
    k_means = MiniBatchKMeans(n_clusters=num_clusters, random_state=0, n_init="auto")
    k_means.fit(points)
    k_means_labels = k_means.labels_
    k_means_cluster_centers = k_means.cluster_centers_
    k_means_labels_unique = np.unique(k_means_labels)
    return k_means_labels, k_means_cluster_centers, k_means_labels_unique


def agglomerative_cluster_atoms(points, num_clusters=3):
    """
    Cluster atoms using AgglomerativeClustering
    """
    clustering = AgglomerativeClustering(n_clusters=num_clusters).fit(points)
    # create the counts of samples under each node
    counts = np.zeros(clustering.children_.shape[0])
    n_samples = len(clustering.labels_)
    for i, merge in enumerate(clustering.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1  # leaf node
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count
    return clustering.labels_, counts
