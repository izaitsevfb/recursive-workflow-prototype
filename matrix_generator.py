#!/usr/bin/env python3

import json
import os
import sys

def generate_matrix(depth):
    # Get current recursion depth from environment variable or use provided argument
    current_depth = depth
    
    # Base case - if we've reached our limit, return empty matrix
    if current_depth >= 3:
        return {"include": []}
    
    # For depth 0 and 1, return 2 elements, for depth 2 return 1 element
    elements = 2 if current_depth < 2 else 1
    
    # Generate matrix
    matrix = {
        "include": [
            {"depth": current_depth + 1, "id": f"job-{current_depth}-{i}"} 
            for i in range(elements)
        ]
    }
    
    return matrix

if __name__ == "__main__":
    # Get depth from command line argument or default to 0
    depth = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    
    # Generate and print matrix as JSON
    result = generate_matrix(depth)
    print(json.dumps(result))
