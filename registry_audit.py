"""
Phase 3.1: Ingredient Registry Audit

Analyzes normalized-ingredients.json to identify:
1. All ingredients that have been resolved (have ingredient_id)
2. All ingredients that are unresolved (ingredient_id is null)
3. Current registry status and gaps

Output: audit_report.json with detailed findings
"""

import json
import sys
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple


def load_normalized_ingredients(file_path: str) -> List[Dict]:
    """Load normalized ingredients from file."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_ingredient_registry(file_path: str) -> Dict:
    """Load current ingredient registry."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"Warning: Registry file not found: {file_path}")
        return {}
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            registry_list = json.load(f)
            # Convert list to dict by ingredient_id
            return {item['ingredient_id']: item for item in registry_list}
    except:
        return {}


def audit_ingredients(normalized_ingredients: List[Dict]) -> Dict:
    """
    Audit all ingredients to find resolved and unresolved.
    
    Returns:
        Dict with:
        - resolved: Dict of ingredient_id -> list of raw ingredient strings
        - unresolved: List of raw ingredient strings
        - stats: Summary statistics
    """
    resolved = defaultdict(list)
    unresolved = []
    raw_ingredient_count = 0
    
    for recipe_data in normalized_ingredients:
        recipe_id = recipe_data.get("recipe_id")
        title = recipe_data.get("title", "Unknown")
        ingredients = recipe_data.get("ingredients", [])
        
        for ing_data in ingredients:
            raw_ingredient_count += 1
            display_text = ing_data.get("display_text", "")
            ingredient_id = ing_data.get("ingredient_id")
            
            if ingredient_id and ingredient_id != "null":
                resolved[ingredient_id].append({
                    "raw": display_text,
                    "recipe_id": recipe_id,
                    "recipe_title": title
                })
            else:
                unresolved.append({
                    "raw": display_text,
                    "recipe_id": recipe_id,
                    "recipe_title": title
                })
    
    # Get unique unresolved ingredients
    unique_unresolved = {}
    for item in unresolved:
        raw = item["raw"]
        if raw not in unique_unresolved:
            unique_unresolved[raw] = []
        unique_unresolved[raw].append(item)
    
    return {
        "resolved": dict(resolved),
        "unresolved": unique_unresolved,
        "stats": {
            "total_ingredient_instances": raw_ingredient_count,
            "unique_resolved_ids": len(resolved),
            "unique_unresolved": len(unique_unresolved),
            "resolved_instances": sum(len(v) for v in resolved.values()),
            "unresolved_instances": len(unresolved)
        }
    }


def generate_audit_report(audit: Dict, registry: Dict) -> Dict:
    """
    Generate comprehensive audit report.
    
    Returns:
        Audit report with actionable recommendations
    """
    report = {
        "audit_date": str(Path(__file__).stat().st_mtime),
        "registry_status": {
            "total_items_in_registry": len(registry),
            "target_size": 300,
            "progress_percent": round((len(registry) / 300) * 100, 2)
        },
        "data_statistics": audit["stats"],
        "unresolved_ingredients": {},
        "priority_tiers": {
            "tier_1_critical": [],
            "tier_2_high": [],
            "tier_3_medium": []
        },
        "recommendations": []
    }
    
    # Prioritize unresolved ingredients by frequency
    unresolved_by_frequency = sorted(
        audit["unresolved"].items(),
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    for ingredient_str, occurrences in unresolved_by_frequency:
        count = len(occurrences)
        sample_recipe = occurrences[0]["recipe_title"] if occurrences else "Unknown"
        
        report["unresolved_ingredients"][ingredient_str] = {
            "occurrences": count,
            "sample_recipes": list(set(o["recipe_title"] for o in occurrences))[:3]
        }
        
        # Prioritize by frequency
        if count >= 3:
            report["priority_tiers"]["tier_1_critical"].append({
                "ingredient": ingredient_str,
                "occurrences": count
            })
        elif count >= 2:
            report["priority_tiers"]["tier_2_high"].append({
                "ingredient": ingredient_str,
                "occurrences": count
            })
        else:
            report["priority_tiers"]["tier_3_medium"].append({
                "ingredient": ingredient_str,
                "occurrences": count
            })
    
    # Generate recommendations
    tier_1_count = len(report["priority_tiers"]["tier_1_critical"])
    tier_2_count = len(report["priority_tiers"]["tier_2_high"])
    
    if tier_1_count > 0:
        report["recommendations"].append(
            f"PRIORITY: Resolve {tier_1_count} Tier 1 critical ingredients "
            f"({report['data_statistics']['unresolved_instances']} instances)"
        )
    
    if tier_2_count > 0:
        report["recommendations"].append(
            f"HIGH: Resolve {tier_2_count} Tier 2 high-priority ingredients"
        )
    
    target_expansion = max(
        50,  # At least expand by 50 items for Tier 1 & 2
        report["registry_status"]["target_size"] - len(registry)
    )
    
    report["recommendations"].append(
        f"PHASE 3 Goal: Expand registry from {len(registry)} → "
        f"{len(registry) + target_expansion} items"
    )
    
    report["recommendations"].append(
        "Use registry_population_template.py to create entries for top priority ingredients"
    )
    
    return report


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("PHASE 3.1: INGREDIENT REGISTRY AUDIT")
    print("="*70 + "\n")
    
    # Load data
    print("Loading normalized ingredients...")
    normalized_ings = load_normalized_ingredients("source/normalized-ingredients.json")
    print(f"  Loaded {len(normalized_ings)} recipes")
    
    print("Loading current registry...")
    registry = load_ingredient_registry("normalizer/ingredient_registry.json")
    print(f"  Loaded {len(registry)} registry items")
    
    # Run audit
    print("Running audit...")
    audit = audit_ingredients(normalized_ings)
    
    print(f"\nAudit Results:")
    print(f"  Total ingredient instances: {audit['stats']['total_ingredient_instances']}")
    print(f"  Unique resolved IDs: {audit['stats']['unique_resolved_ids']}")
    print(f"  Unique unresolved: {audit['stats']['unique_unresolved']}")
    print(f"  Resolved instances: {audit['stats']['resolved_instances']}")
    print(f"  Unresolved instances: {audit['stats']['unresolved_instances']}")
    
    # Generate report
    report = generate_audit_report(audit, registry)
    
    # Save report
    with open("AUDIT_REPORT.json", "w", encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n{'='*70}")
    print("AUDIT REPORT SUMMARY")
    print(f"{'='*70}")
    print(f"\nRegistry Status:")
    for key, value in report["registry_status"].items():
        print(f"  {key}: {value}")
    
    print(f"\nUnresolved Ingredients (Top 10 by frequency):")
    for i, (ing, data) in enumerate(list(report["unresolved_ingredients"].items())[:10], 1):
        print(f"  {i}. {ing} ({data['occurrences']} instances)")
        print(f"     Sample recipes: {', '.join(data['sample_recipes'])}")
    
    print(f"\nPriority Tiers:")
    print(f"  Tier 1 (≥3 occurrences): {len(report['priority_tiers']['tier_1_critical'])} ingredients")
    print(f"  Tier 2 (2 occurrences): {len(report['priority_tiers']['tier_2_high'])} ingredients")
    print(f"  Tier 3 (1 occurrence): {len(report['priority_tiers']['tier_3_medium'])} ingredients")
    
    print(f"\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  • {rec}")
    
    print(f"\n{'='*70}")
    print("✓ Audit complete. See AUDIT_REPORT.json for full details.")
    print(f"{'='*70}\n")
