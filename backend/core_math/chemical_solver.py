# backend/core_math/chemical_solver.py
from ortools.linear_solver import pywraplp
from typing import Dict, Any, List

class ChemicalCompatibilitySolver:
    @staticmethod
    def validate_blend(refinery_constraints: Dict[str, Any], supplier_capabilities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy validation logic preserved to maintain downstream graph state compatibility.
        """
        s_sulfur = supplier_capabilities.get("sulfur_content", 0.0)
        s_api = supplier_capabilities.get("api_gravity", 0.0)
        
        r_sulfur_max = refinery_constraints.get("max_sulfur_threshold", 1.5)
        r_api_min = refinery_constraints.get("min_api_gravity", 28.0)
        
        compatible = (s_sulfur <= r_sulfur_max) and (s_api >= r_api_min)
        return {"compatible": compatible}

    @staticmethod
    def optimize_global_allocation(refinery_constraints: Dict[str, Any], alternative_suppliers: List[Dict[str, Any]], required_volume: float = 10000.0) -> Dict[str, Any]:
        """
        Advanced MILP Optimization Model.
        Selects the mathematically optimal supplier mix using binary activation states (0 or 1),
        minimizing both fixed contract activation overhead and variable volume costs.
        """
        # 1. Create the local SCIP solver (Standard Mixed-Integer Programming Engine)
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if not solver:
            return {"status": "Solver Unavailable", "allocation": {}, "total_minimized_cost": 0.0}

        infinity = solver.infinity()
        
        # Operational parameters
        max_sulfur_allowed = refinery_constraints.get("max_sulfur_threshold", 1.5)
        min_api_required = refinery_constraints.get("min_api_gravity", 28.0)

        # Decision Variables Matrices
        volume_vars = {}      # Continuous variables: Volume allocated to supplier i (x_i >= 0)
        activation_vars = {}  # Integer/Binary variables: Is supplier i active (y_i in {0, 1})

        for i, supplier in enumerate(alternative_suppliers):
            s_name = supplier["name"]
            max_capacity = supplier.get("max_capacity_barrels", 15000.0)
            
            # Define variables
            volume_vars[s_name] = solver.NumVar(0.0, max_capacity, f"vol_{s_name}")
            activation_vars[s_name] = solver.IntVar(0, 1, f"active_{s_name}")

            # Constraint: If supplier is inactive (0), volume must be 0. If active (1), vol <= max_capacity
            solver.Add(volume_vars[s_name] <= activation_vars[s_name] * max_capacity)

        # ─── GLOBAL CONSTRAINTS ────────────────────────────────────────────────
        
        # Constraint 1: Target demand volume allocation met exactly
        solver.Add(solver.Sum([volume_vars[s["name"]] for s in alternative_suppliers]) == required_volume)

        # Constraint 2: Total weighted sulfur profile constraint lower or equal to threshold
        total_sulfur_expr = solver.Sum([volume_vars[s["name"]] * s.get("sulfur_content", 0.0) for s in alternative_suppliers])
        solver.Add(total_sulfur_expr <= max_sulfur_allowed * required_volume)

        # ─── OBJECTIVE FUNCTION ───────────────────────────────────────────────
        # Objective: Minimize (Variable Cost per Barrel * Volume) + (Fixed Contract Penalty * Activation State)
        objective_terms = []
        for s in alternative_suppliers:
            s_name = s["name"]
            var_cost = s.get("cost_per_barrel", 75.0)
            fixed_cost = s.get("fixed_contract_activation_fee", 50000.0) # Fixed penalty
            
            objective_terms.append(volume_vars[s_name] * var_cost + activation_vars[s_name] * fixed_cost)

        solver.Minimize(solver.Sum(objective_terms))

        # Run optimization
        status = solver.Solve()
        
        if status == pywraplp.Solver.OPTIMAL:
            allocation_results = {}
            total_cost = solver.Objective().Value()
            
            for s in alternative_suppliers:
                s_name = s["name"]
                allocated_vol = volume_vars[s_name].solution_value()
                is_active = activation_vars[s_name].solution_value()
                
                if is_active > 0.5 and allocated_vol > 0:
                    allocation_results[s_name] = {
                        "allocated_volume_barrels": round(allocated_vol, 2),
                        "fixed_contract_triggered": True
                    }
                    
            return {
                "status": "MILP_OPTIMAL",
                "allocation": allocation_results,
                "total_minimized_cost": round(total_cost, 2)
            }
        
        return {"status": "INFEASIBLE_CONSTRAINTS", "allocation": {}, "total_minimized_cost": 0.0}