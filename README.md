# Recursive GitHub Workflow Test

This repository tests if GitHub Actions supports recursive workflow calls.

## Components

1. **matrix_generator.py** - Python script that generates a job matrix based on the current recursion depth:
   - Depth 0 and 1: Returns 2 jobs
   - Depth 2: Returns 1 job
   - Depth 3+: Returns empty matrix (stopping condition)

2. **reusable-workflow.yml** - Reusable workflow that:
   - Takes a `recursion_depth` input parameter
   - Generates a matrix of jobs using the Python script
   - Creates jobs that call the same workflow with increased depth

3. **trigger-workflow.yml** - Main workflow with workflow_dispatch trigger to start the recursion

## Testing

Trigger the workflow manually with initial depth 0 to test with maximum depth 3:
- The workflow will create a tree-like structure of jobs
- Total jobs expected: 1 (depth 0) + 2 (depth 1) + 4 (depth 2) + 0 (depth 3) = 7

The workflow should stop at depth 3 per the logic in the Python script.