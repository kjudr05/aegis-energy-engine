# backend/core_math/router.py
import networkx as nx
from typing import List, Dict, Tuple

class HybridRouter:
    def __init__(self, base_data: Dict):
        """
        Initializes the deterministic physical network map using NetworkX
        from our ingested base data.
        """
        self.graph = nx.DiGraph()  # Directed graph since shipping lanes have distinct directional paths
        self.load_network(base_data)

    def load_network(self, base_data: Dict):
        """Populates the nodes and edges from our mock configuration file."""
        # Add nodes with their physical metadata properties
        for node in base_data["shipping_network"]["nodes"]:
            self.graph.add_node(
                node["id"], 
                type=node["type"], 
                country=node.get("country"),
                base_risk=node.get("base_risk", 0.0)
            )
        
        # Add edges with physical distance data
        for edge in base_data["shipping_network"]["edges"]:
            self.graph.add_edge(
                edge["source"], 
                edge["target"], 
                distance_miles=edge["distance_miles"],
                dynamic_risk_multiplier=1.0  # Base state: no additional risk modifier
            )

    def calculate_edge_weight(self, source: str, target: str, d: dict) -> float:
        """
        Calculates the true operational 'cost' of an edge by combining
        deterministic physical distance with dynamic, nondeterministic risk ratings.
        """
        edge_data = self.graph[source][target]
        distance = edge_data["distance_miles"]
        risk_multiplier = edge_data["dynamic_risk_multiplier"]
        
        # Core Formula: Weight = Physical Distance * Dynamic Risk Multiplier
        return distance * risk_multiplier

    def apply_dynamic_risk(self, chokepoint_id: str, risk_multiplier: float):
        """
        Applies a risk penalty to all shipping pathways intersecting a threatened chokepoint.
        """
        for u, v in self.graph.edges():
            if u == chokepoint_id or v == chokepoint_id:
                self.graph[u][v]["dynamic_risk_multiplier"] = risk_multiplier

    def reset_risks(self):
        """Resets all dynamic risk penalties back to their baseline state."""
        for u, v in self.graph.edges():
            self.graph[u][v]["dynamic_risk_multiplier"] = 1.0

    def find_optimal_route(self, origin: str, destination: str) -> Tuple[List[str], float]:
        """
        Executes a deterministic shortest-path algorithm (Dijkstra) over 
        the risk-penalized network graph.
        """
        try:
            path = nx.shortest_path(
                self.graph, 
                source=origin, 
                target=destination, 
                weight=self.calculate_edge_weight
            )
            
            # Calculate total computed travel cost metric along the derived route
            total_cost = nx.shortest_path_length(
                self.graph, 
                source=origin, 
                target=destination, 
                weight=self.calculate_edge_weight
            )
            return path, total_cost
        except nx.NetworkXNoPath:
            return [], float('inf')