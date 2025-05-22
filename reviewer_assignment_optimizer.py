import json
import numpy as np
import pulp
from tqdm import tqdm
from unidecode import unidecode
from collections import defaultdict

# configuration
TOPIC_MULTIPLIER = 1.2
MINIMUM_MATCH_SCORE = 10
MAX_ABSTRACTS_PER_REVIEWER = 30
MIN_ABSTRACTS_PER_REVIEWER = 10
REVIEWERS_PER_ABSTRACT = 3
EXPERIENCE_THRESHOLD = 10  # years of experience

def calculate_match(abstract, reviewer):
    """
    Calculate the match score between an abstract and a reviewer.
    The score is based on the number of matching categories and focus topics.
    """
    # Initialize match score
    match_score = 0

    # Check for conflicts of interest
    for author in abstract['authors']:
        if unidecode(reviewer['last_name']).lower() in unidecode(author).lower():
            return 0  # avoid COIs

    # Check for matching categories
    for category, score in abstract['category_scores'].items():
        cats = [c.lower() for c in reviewer['categories']]
        if category.lower() in cats:
            match_score += score

    # Apply focus topic multiplier
    if abstract['focus_topic'] in reviewer['focus_topic']:
        match_score *= TOPIC_MULTIPLIER

    match_score *= reviewer['experience']  # Scale by experience (0-10 years)

    return match_score

def prepare_data(abstracts_file, reviewers_file):
    """
    Load and prepare data for optimization.
    """
    print("Loading data...")
    with open(abstracts_file, 'r') as f:
        abstracts = json.load(f)

    with open(reviewers_file, 'r') as f:
        reviewers = json.load(f)

    # Create lookup dictionaries
    abstract_dict = {abstract['number']: abstract for abstract in abstracts}
    reviewer_dict = {}
    for reviewer in reviewers:
        reviewer_key = (reviewer['first_name'], reviewer['last_name'])
        if reviewer_key in reviewer_dict:
            print("Duplicate reviewer found:", reviewer_key)
        reviewer_dict[reviewer_key] = reviewer

    print(len(reviewer_dict))

    # Add indices for easier referencing
    for i, reviewer_key in enumerate(reviewer_dict.keys()):
        reviewer_dict[reviewer_key]['index'] = i
    
    # Calculate all valid matches
    print("Calculating matches...")
    matches = {}
    eligible_reviewers = {}
    
    for abstract_num, abstract in tqdm(abstract_dict.items()):
        abstract_matches = {}
        eligible_list = []
        
        for reviewer_key, reviewer in reviewer_dict.items():
            match_score = calculate_match(abstract, reviewer)
            if match_score > MINIMUM_MATCH_SCORE:
                reviewer_idx = reviewer['index']
                abstract_matches[reviewer_idx] = match_score
                eligible_list.append(reviewer_idx)
        
        matches[abstract_num] = abstract_matches
        eligible_reviewers[abstract_num] = eligible_list
        print(f"Abstract {abstract_num} has {len(eligible_list)} eligible reviewers")
    
    # Identify experienced reviewers (5+ years of experience)
    experienced_reviewers = []
    for reviewer_key, reviewer in reviewer_dict.items():
        if reviewer.get('experience', 0) >= EXPERIENCE_THRESHOLD:
            experienced_reviewers.append(reviewer['index'])
            print("Reviewer", reviewer_key, "is experienced")
    
    # Find experienced reviewers for each abstract
    experienced_per_abstract = {}
    for abstract_num, eligible in eligible_reviewers.items():
        experienced_per_abstract[abstract_num] = [r for r in eligible if r in experienced_reviewers]
    
    # Check for abstracts without experienced reviewers
    problematic_abstracts = [num for num, exp_list in experienced_per_abstract.items() if not exp_list]
    if problematic_abstracts:
        print(f"WARNING: {len(problematic_abstracts)} abstracts have no eligible experienced reviewers")
        for num in problematic_abstracts:
            print(f"  - Abstract {num}")
    
    return {
        'abstracts': abstract_dict,
        'reviewers': reviewer_dict,
        'matches': matches,
        'eligible_reviewers': eligible_reviewers,
        'experienced_reviewers': experienced_reviewers,
        'experienced_per_abstract': experienced_per_abstract,
        'problematic_abstracts': problematic_abstracts
    }

def optimize_assignments(data, reviewers_per_abstract=3, max_abstracts_per_reviewer=30, min_abstracts_per_reviewer=10):
    """
    Perform optimization to assign reviewers to abstracts.
    """
    abstracts = data['abstracts']
    eligible_reviewers = data['eligible_reviewers']
    matches = data['matches']
    experienced_per_abstract = data['experienced_per_abstract']
    
    n_reviewers = max([max(rev_list) for rev_list in eligible_reviewers.values() if rev_list]) + 1
    abstract_numbers = list(abstracts.keys())
    
    print(f"Setting up optimization problem with {len(abstract_numbers)} abstracts and {n_reviewers} reviewers...")
    
    # Create the model
    model = pulp.LpProblem("Abstract_Reviewer_Assignment", pulp.LpMaximize)
    
    # Create decision variables - only for eligible reviewer-abstract pairs
    x = {}
    for abstract_num in abstract_numbers:
        for reviewer_idx in eligible_reviewers[abstract_num]:
            x[reviewer_idx, abstract_num] = pulp.LpVariable(
                f"x_{reviewer_idx}_{abstract_num}", 
                cat=pulp.LpBinary
            )
    
    # Objective function: Maximize total match score
    model += pulp.lpSum(
        matches[abstract_num][reviewer_idx] * x[reviewer_idx, abstract_num]
        for abstract_num in abstract_numbers
        for reviewer_idx in eligible_reviewers[abstract_num]
    )
    
    # Constraint 1: Each abstract needs exactly 3 reviewers
    for abstract_num in abstract_numbers:
        if eligible_reviewers[abstract_num]:  # Only if there are eligible reviewers
            model += pulp.lpSum(
                x[reviewer_idx, abstract_num] 
                for reviewer_idx in eligible_reviewers[abstract_num]
            ) == reviewers_per_abstract
    
    # Constraint 2: No reviewer can be assigned more than N abstracts
    reviewer_indices = set()
    for abstract_num in abstract_numbers:
        reviewer_indices.update(eligible_reviewers[abstract_num])
    
    for reviewer_idx in reviewer_indices:
        relevant_abstracts = [
            abstract_num for abstract_num in abstract_numbers 
            if reviewer_idx in eligible_reviewers[abstract_num]
        ]
        model += pulp.lpSum(
            x[reviewer_idx, abstract_num] 
            for abstract_num in relevant_abstracts
        ) <= max_abstracts_per_reviewer
        model += pulp.lpSum(
            x[reviewer_idx, abstract_num]
            for abstract_num in relevant_abstracts
        ) >= min_abstracts_per_reviewer
    
    # Constraint 3: Each abstract needs at least one experienced reviewer
    for abstract_num in abstract_numbers:
        if experienced_per_abstract[abstract_num]:  # Only if there are experienced reviewers
            model += pulp.lpSum(
                x[reviewer_idx, abstract_num] 
                for reviewer_idx in experienced_per_abstract[abstract_num]
            ) >= 1
    
    # Solve the model with a time limit
    print("Solving the optimization problem...")
    solver = pulp.PULP_CBC_CMD(timeLimit=600, msg=True, threads=4)
    model.solve(solver)
    
    # Check solution status
    print(f"Solution status: {pulp.LpStatus[model.status]}")
    
    if model.status != pulp.LpStatusOptimal:
        print("WARNING: Optimal solution not found. Using best solution found so far.")
    
    # Extract the assignments
    assignments = {}
    for abstract_num in abstract_numbers:
        assignments[abstract_num] = []
        for reviewer_idx in eligible_reviewers[abstract_num]:
            if (reviewer_idx, abstract_num) in x and pulp.value(x[reviewer_idx, abstract_num]) == 1:
                assignments[abstract_num].append(reviewer_idx)
    
    return assignments

def validate_and_fix_assignments(assignments, data, reviewers_per_abstract=3, max_abstracts_per_reviewer=30):
    """
    Validate the assignments and fix any issues.
    """
    print("Validating assignments...")
    
    abstracts = data['abstracts']
    reviewer_dict = data['reviewers']
    experienced_reviewers = data['experienced_reviewers']
    experienced_per_abstract = data['experienced_per_abstract']
    
    # Check assignment completeness
    incomplete_abstracts = []
    for abstract_num, assigned_reviewers in assignments.items():
        if len(assigned_reviewers) != reviewers_per_abstract:
            incomplete_abstracts.append(abstract_num)
    
    if incomplete_abstracts:
        print(f"Found {len(incomplete_abstracts)} abstracts without exactly {reviewers_per_abstract} reviewers")
    
    # Check experienced reviewer constraint
    no_experienced = []
    for abstract_num, assigned_reviewers in assignments.items():
        has_experienced = any(r in experienced_reviewers for r in assigned_reviewers)
        if not has_experienced and experienced_per_abstract[abstract_num]:
            no_experienced.append(abstract_num)
    
    if no_experienced:
        print(f"Found {len(no_experienced)} abstracts without an experienced reviewer")
    
    # Check reviewer load
    reviewer_loads = defaultdict(int)
    for abstract_num, assigned_reviewers in assignments.items():
        for reviewer_idx in assigned_reviewers:
            reviewer_loads[reviewer_idx] += 1
    
    overloaded_reviewers = {r: load for r, load in reviewer_loads.items() 
                           if load > max_abstracts_per_reviewer}
    if overloaded_reviewers:
        print(f"Found {len(overloaded_reviewers)} overloaded reviewers")
    
    # Fix issues using a greedy approach if needed
    if incomplete_abstracts or no_experienced or overloaded_reviewers:
        print("Fixing assignment issues...")
        
        # Fix incomplete abstracts
        for abstract_num in incomplete_abstracts:
            current = assignments[abstract_num]
            needed = reviewers_per_abstract - len(current)
            
            # Get eligible reviewers not already assigned
            eligible = [r for r in data['eligible_reviewers'][abstract_num] 
                      if r not in current]
            
            # Sort by match score
            eligible_with_scores = [(r, data['matches'][abstract_num][r]) 
                                  for r in eligible 
                                  if reviewer_loads[r] < max_abstracts_per_reviewer]
            eligible_with_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Add best matches
            for reviewer_idx, _ in eligible_with_scores[:needed]:
                assignments[abstract_num].append(reviewer_idx)
                reviewer_loads[reviewer_idx] += 1
    
        # Fix missing experienced reviewers
        for abstract_num in no_experienced:
            if not experienced_per_abstract[abstract_num]:
                continue  # Skip if no experienced reviewers are eligible
                
            current = assignments[abstract_num]
            
            # Find an experienced reviewer not already assigned
            available_experienced = [r for r in experienced_per_abstract[abstract_num]
                                    if r not in current]
            
            if available_experienced:
                # Sort by match score
                available_with_scores = [(r, data['matches'][abstract_num][r]) 
                                       for r in available_experienced]
                available_with_scores.sort(key=lambda x: x[1], reverse=True)
                
                # Replace worst non-experienced reviewer with best experienced one
                non_experienced = [r for r in current if r not in experienced_reviewers]
                if non_experienced:
                    non_exp_with_scores = [(r, data['matches'][abstract_num][r]) 
                                         for r in non_experienced]
                    non_exp_with_scores.sort(key=lambda x: x[1])
                    
                    # Remove worst non-experienced
                    worst = non_exp_with_scores[0][0]
                    assignments[abstract_num].remove(worst)
                    reviewer_loads[worst] -= 1
                    
                    # Add best experienced
                    best_exp = available_with_scores[0][0]
                    assignments[abstract_num].append(best_exp)
                    reviewer_loads[best_exp] += 1
        
        # Fix overloaded reviewers
        for reviewer_idx, load in sorted(overloaded_reviewers.items(), 
                                         key=lambda x: x[1], reverse=True):
            excess = load - max_abstracts_per_reviewer
            
            # Find abstracts assigned to this reviewer
            assigned_abstracts = [abstract_num for abstract_num, reviewers 
                                in assignments.items() if reviewer_idx in reviewers]
            
            # Sort by match score (remove lowest matches first)
            abstract_scores = [(abstract_num, data['matches'][abstract_num][reviewer_idx]) 
                              for abstract_num in assigned_abstracts]
            abstract_scores.sort(key=lambda x: x[1])
            
            # Remove from lowest scoring abstracts first
            for i in range(excess):
                if i < len(abstract_scores):
                    abstract_num = abstract_scores[i][0]
                    
                    # Find replacement that doesn't exceed load
                    eligible = data['eligible_reviewers'][abstract_num]
                    replacements = [r for r in eligible 
                                  if r not in assignments[abstract_num]
                                  and reviewer_loads[r] < max_abstracts_per_reviewer]
                    
                    if replacements:
                        # Sort by match score
                        replacements_with_scores = [(r, data['matches'][abstract_num][r]) 
                                                 for r in replacements]
                        replacements_with_scores.sort(key=lambda x: x[1], reverse=True)
                        
                        # Replace with best match
                        best_replacement = replacements_with_scores[0][0]
                        
                        # Check if we need to maintain experienced reviewer constraint
                        exp_in_current = any(r in experienced_reviewers 
                                           for r in assignments[abstract_num] if r != reviewer_idx)
                        
                        if (reviewer_idx in experienced_reviewers 
                            and not exp_in_current 
                            and best_replacement not in experienced_reviewers):
                            # Need to find an experienced replacement
                            exp_replacements = [r for r in replacements 
                                             if r in experienced_reviewers]
                            
                            if exp_replacements:
                                exp_with_scores = [(r, data['matches'][abstract_num][r]) 
                                                for r in exp_replacements]
                                exp_with_scores.sort(key=lambda x: x[1], reverse=True)
                                best_replacement = exp_with_scores[0][0]
                            else:
                                # Can't maintain constraint, try next abstract
                                continue
                        
                        # Do the replacement
                        assignments[abstract_num].remove(reviewer_idx)
                        assignments[abstract_num].append(best_replacement)
                        reviewer_loads[reviewer_idx] -= 1
                        reviewer_loads[best_replacement] += 1
    
    # Final validation
    print("Final validation:")
    incomplete = sum(1 for assigned in assignments.values() 
                   if len(assigned) != reviewers_per_abstract)
    print(f"- Abstracts without exactly {reviewers_per_abstract} reviewers: {incomplete}")
    
    missing_exp = sum(1 for abstract_num, assigned in assignments.items()
                     if not any(r in experienced_reviewers for r in assigned)
                     and experienced_per_abstract[abstract_num])
    print(f"- Abstracts without an experienced reviewer: {missing_exp}")
    
    reviewer_loads = defaultdict(int)
    for assigned in assignments.values():
        for reviewer_idx in assigned:
            reviewer_loads[reviewer_idx] += 1
    
    overloaded = sum(1 for load in reviewer_loads.values() 
                    if load > max_abstracts_per_reviewer)
    print(f"- Overloaded reviewers: {overloaded}")
    
    return assignments

def report_statistics(assignments, data):
    """
    Generate statistics about the assignments.
    """
    print("\n--- Assignment Statistics ---")
    
    # Count assignments per reviewer
    reviewer_loads = defaultdict(int)
    for abstract_num, assigned_reviewers in assignments.items():
        for reviewer_idx in assigned_reviewers:
            reviewer_loads[reviewer_idx] += 1
    
    # Match score statistics
    match_scores = []
    for abstract_num, assigned_reviewers in assignments.items():
        for reviewer_idx in assigned_reviewers:
            score = data['matches'][abstract_num][reviewer_idx]
            match_scores.append(score)
    
    print(f"Number of reviewers used: {len(reviewer_loads)}")
    print(f"Average abstracts per reviewer: {sum(reviewer_loads.values()) / len(reviewer_loads):.2f}")
    print(f"Min abstracts per reviewer: {min(reviewer_loads.values())}")
    print(f"Max abstracts per reviewer: {max(reviewer_loads.values())}")
    print(f"Average match score: {sum(match_scores) / len(match_scores):.2f}")
    print(f"Min match score: {min(match_scores):.2f}")
    print(f"Max match score: {max(match_scores):.2f}")
    return reviewer_loads

def convert_to_output_format(assignments, data):
    """
    Convert assignments to a readable output format.
    """
    output = []
    
    # Create a reverse mapping from indices to reviewer names
    reviewer_names = {}
    for (first, last), reviewer in data['reviewers'].items():
        reviewer_names[reviewer['index']] = (first,last)
    
    # Format each abstract's assignments
    for abstract_num, assigned_reviewers in sorted(assignments.items()):
        abstract_data = data['abstracts'][abstract_num]
        
        assigned_data = []
        for reviewer_idx in assigned_reviewers:
            score = data['matches'][abstract_num][reviewer_idx]
            name = reviewer_names[reviewer_idx]
            is_experienced = reviewer_idx in data['experienced_reviewers']
            
            assigned_data.append({
                "reviewer_name": name,
                "match_score": score,
                "experienced": is_experienced
            })
        
        output.append({
            "abstract_number": abstract_num,
            "title": abstract_data['title'],
            "assigned_reviewers": assigned_data
        })
    
    return output

def main():
    """Main function to run the optimization."""
    # Files with your data
    abstracts_file = 'categorized_abstracts.json'
    reviewers_file = 'reviewers.json'

    
    # Prepare data
    data = prepare_data(abstracts_file, reviewers_file)
    
    # Run optimization
    print("\nRunning assignment optimization...")
    assignments = optimize_assignments(
        data, 
        reviewers_per_abstract=REVIEWERS_PER_ABSTRACT,
        max_abstracts_per_reviewer=MAX_ABSTRACTS_PER_REVIEWER,
        min_abstracts_per_reviewer=MIN_ABSTRACTS_PER_REVIEWER
    )
    
    # Validate and fix assignments if needed
    fixed_assignments = validate_and_fix_assignments(
        assignments, 
        data, 
        reviewers_per_abstract=REVIEWERS_PER_ABSTRACT,
        max_abstracts_per_reviewer=MAX_ABSTRACTS_PER_REVIEWER
    )
    
    # Report statistics
    reviewer_loads = report_statistics(fixed_assignments, data)

    reviewer_dict = data['reviewers']
    idle_reviewers = []
    assigned_reviewers = []
    for reviewer_key, reviewer in reviewer_dict.items():
        if reviewer['index'] in reviewer_loads:
            assigned_reviewers.append({
                'reviewer_key': reviewer_key,
                'load': reviewer_loads[reviewer['index']]
            })
        else:
            idle_reviewers.append(reviewer_key)

    # Convert to output format
    output_data = convert_to_output_format(fixed_assignments, data)
    
    # Save results
    with open('reviewer_assignments.json', 'w') as f:
        json.dump(output_data, f, indent=2)

    with open('reviewer_assignments_statistics.json', 'w') as f:
        json.dump({
            "assigned_reviewers": assigned_reviewers,
            "idle_reviewers": idle_reviewers
        }, f, indent=2)

    print("\nAssignments completed! Results saved to 'reviewer_assignments.json'")

if __name__ == "__main__":
    main()
