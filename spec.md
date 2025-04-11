Here's a concise spec in Markdown:

---

## High-Level Overview

We want a GitHub Actions workflow system with the following conceptual “stages”:

1. **Trigger** (e.g., pull, schedule, push, etc.)
2. **Build** (one or many build jobs, each with a job matrix)
3. **Test** (one or many test jobs, depending on each build job's matrix)

We’ll have a Python script to generate these job matrices (both build and test), along with any other configuration values. This should be reusable from multiple workflows.

---

## Architecture

1. **Python Script** (e.g. `matrix_gen.py`)
    - Takes inputs such as: event type, configs, shard counts, runner types, etc.
    - Outputs JSON for each “stage”:
        - A matrix for build jobs (one or more build environments/config combos).
        - A matrix for test jobs (with shard splitting, runner assignment, etc.).
    - Possibly also includes “logical filters” or “label filters” to figure out which jobs actually need to run.

2. **Pull Workflow** (`pull.yml` or similar)
    - Runs on `pull_request`, `push`, or `workflow_dispatch`.
    - **Step**: Calls the Python script (or a reusable workflow that does so) to generate the config for which jobs should run.
    - **Step**: Invokes the **Build** stage via a reusable workflow (passing in that JSON).
    - **Step**: The Build workflow outputs both the Docker image name (if relevant) and a test matrix.
    - **Step**: Invokes the **Test** stage via another reusable workflow, passing the test matrix from build.

3. **Reusable Workflows**
    - **`build.yml`**: Takes an input (JSON) describing which builds to perform.
        - Spawns one or more build jobs using the job matrix.
        - Outputs any artifacts (docker images, logs) plus a second matrix for test jobs.
    - **`test.yml`**: Takes the test matrix from the build.
        - Spawns one or many test jobs (sharded, different configs, etc.) based on that matrix.
        - Possibly calls into more specialized workflows if needed.

---

## Proposed Flow

1. **trigger** → _pull workflow_
2. _pull workflow_ calls **matrix_gen.py** → obtains `build_matrix`, `test_matrix`, or more complex JSON.
3. _pull workflow_ then calls a reusable **Build** workflow (`build.yml`), passing `build_matrix` (and any parent filters / environment variables).
    - The Build workflow runs parallel jobs for each build config.
    - If the build is successful, it outputs a `test_matrix` (which might be the same or a subset of the original).
4. _pull workflow_ then calls a reusable **Test** workflow (`test.yml`), passing that `test_matrix`.
    - The Test workflow splits out the test shards, environment variables, or concurrency settings, and executes them in parallel.

---

## Implementation Details

1. **`matrix_gen.py`**
    - Command-line arguments: e.g. `--event-type pull_request --config-file config.json --stage build --out build_matrix.json`.
    - Could parse labels or environment variables for dynamic decisions.
    - Each stage returns a JSON matrix structure.

2. **`pull.yml`** (the main workflow)
    - Trigger on `pull_request`, `push`, etc.
    - Jobs:
        1. **Generate Filters** (optionally a script or job that checks labels, commit messages, etc.).
        2. **Matrix Generation**: run `matrix_gen.py` with the appropriate stage = "build".
        3. **Invoke Reusable Build**: pass the matrix output as an `input` to the reusable workflow.
        4. **Invoke Reusable Test**: pass the build’s test matrix to the test workflow.

3. **Reusable `build.yml`**
    - Inputs:
        - `build_matrix` (JSON)
        - Possibly other config info or environment variables.
    - Jobs:
        - A “dynamic” job using `strategy.matrix` from the `build_matrix`.
        - Outputs: `test_matrix` (to be used in test stage) and possibly build artifacts.

4. **Reusable `test.yml`**
    - Inputs:
        - `test_matrix` (JSON), which includes test shards, runner assignment, etc.
    - Jobs:
        - A dynamic `strategy.matrix` job for each config+shard.

---

## Example Usage

```yaml
name: pull

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  generate-build-matrix:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Generate Build Matrix
        run: |
          python matrix_gen.py --stage build --event-type ${{ github.event_name }} --out build_matrix.json
      - name: Upload Build Matrix
        uses: actions/upload-artifact@v3
        with:
          name: build_matrix
          path: build_matrix.json

  build:
    needs: generate-build-matrix
    uses: ./.github/workflows/build.yml
    with:
      build_matrix_artifact: build_matrix
    secrets: inherit

  test:
    needs: build
    uses: ./.github/workflows/test.yml
    with:
      test_matrix_artifact: ${{ needs.build.outputs.test_matrix_artifact }}
    secrets: inherit
```

_(Note: This snippet is just an illustration. The actual details can vary depending on how artifacts and outputs are passed around.)_

---

**That’s the gist!** We have a single Python script generating dynamic matrices for each stage, and a chain of workflows (the root workflow plus two reusable child workflows) that orchestrate builds and tests.