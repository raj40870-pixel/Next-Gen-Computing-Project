"""
Hydrogeological Graph Builder Module
Constructs spatial adjacency matrices and graph representations for 15 districts
across Punjab and Haryana using geographical coordinates, aquifer connectivity,
and Gaussian distance thresholding.
"""

import json
import os
import numpy as np
import torch
from typing import Dict, Any, Tuple, List

DEFAULT_GEO_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "geo", "punjab_haryana_districts.json")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two geographic coordinates in kilometers.
    """
    R = 6371.0  # Earth's radius in km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (
        np.sin(dlat / 2.0) ** 2
        + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return float(R * c)


class HydrogeologicalGraph:
    """
    Constructs and maintains the spatial aquifer graph for the 15 monitoring districts.
    """
    def __init__(
        self,
        geo_path: str = DEFAULT_GEO_PATH,
        dist_threshold_km: float = 140.0,
        sigma_km: float = 65.0,
        epsilon: float = 0.05
    ):
        self.geo_path = geo_path
        self.dist_threshold_km = dist_threshold_km
        self.sigma_km = sigma_km
        self.epsilon = epsilon
        self.districts = self._load_districts()
        self.num_nodes = len(self.districts)
        
        self.dist_matrix = self._compute_distance_matrix()
        self.adj_matrix = self._compute_adjacency_matrix()
        self.normalized_adj = self._compute_normalized_laplacian()

    def _load_districts(self) -> List[Dict[str, Any]]:
        with open(self.geo_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _compute_distance_matrix(self) -> np.ndarray:
        """Computes pairwise distance matrix (km) between all district centroids."""
        N = self.num_nodes
        D = np.zeros((N, N), dtype=np.float32)
        for i in range(N):
            for j in range(N):
                if i != j:
                    d = haversine_distance(
                        self.districts[i]["lat"], self.districts[i]["lon"],
                        self.districts[j]["lat"], self.districts[j]["lon"]
                    )
                    D[i, j] = d
        return D

    def _compute_adjacency_matrix(self) -> np.ndarray:
        """
        Builds spatial adjacency matrix using Gaussian distance kernel with thresholding:
        W_ij = exp(-d(i,j)^2 / sigma^2) if d(i,j) <= threshold and W_ij >= epsilon, else 0.
        """
        N = self.num_nodes
        W = np.zeros((N, N), dtype=np.float32)
        for i in range(N):
            for j in range(N):
                if i == j:
                    W[i, j] = 1.0  # self connection
                else:
                    d = self.dist_matrix[i, j]
                    if d <= self.dist_threshold_km:
                        weight = np.exp(- (d ** 2) / (self.sigma_km ** 2))
                        if weight >= self.epsilon:
                            W[i, j] = weight
        return W

    def _compute_normalized_laplacian(self) -> np.ndarray:
        """
        Computes symmetric normalized adjacency: D^(-1/2) * A * D^(-1/2)
        with self-loops added.
        """
        A = self.adj_matrix.copy()
        # Add self-loops if not fully 1.0
        np.fill_diagonal(A, 1.0)
        degree = np.sum(A, axis=1)
        deg_inv_sqrt = np.zeros_like(degree, dtype=np.float32)
        nonzero_mask = degree > 0
        deg_inv_sqrt[nonzero_mask] = 1.0 / np.sqrt(degree[nonzero_mask])
        D_inv = np.diag(deg_inv_sqrt)
        norm_adj = D_inv @ A @ D_inv
        return norm_adj.astype(np.float32)

    def get_torch_graph(self, device: torch.device = None) -> Dict[str, torch.Tensor]:
        """
        Returns graph representation ready for PyTorch neural network execution:
        - normalized_adj: [N, N] tensor
        - edge_index: [2, num_edges]
        - edge_weight: [num_edges]
        """
        adj_t = torch.tensor(self.normalized_adj, dtype=torch.float32)
        if device is not None:
            adj_t = adj_t.to(device)

        # Extract edge list for graph convolutions
        edge_indices = []
        edge_weights = []
        N = self.num_nodes
        for i in range(N):
            for j in range(N):
                if self.adj_matrix[i, j] > 0:
                    edge_indices.append([i, j])
                    edge_weights.append(self.adj_matrix[i, j])

        edge_index_t = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_weight_t = torch.tensor(edge_weights, dtype=torch.float32)

        if device is not None:
            edge_index_t = edge_index_t.to(device)
            edge_weight_t = edge_weight_t.to(device)

        return {
            "adj": adj_t,
            "edge_index": edge_index_t,
            "edge_weight": edge_weight_t,
            "raw_dist_matrix": self.dist_matrix,
            "num_nodes": self.num_nodes,
            "node_names": [d["name"] for d in self.districts],
            "coords": [[d["lat"], d["lon"]] for d in self.districts]
        }


if __name__ == "__main__":
    print("Testing HydrogeologicalGraph builder...")
    graph = HydrogeologicalGraph()
    t_graph = graph.get_torch_graph()
    print("Graph built successfully!")
    print(f"Num Nodes: {t_graph['num_nodes']}")
    print(f"Adjacency matrix shape: {t_graph['adj'].shape}")
    print(f"Edge index shape: {t_graph['edge_index'].shape}")
    print(f"Average degree: {t_graph['adj'].sum().item() / t_graph['num_nodes']:.2f}")
