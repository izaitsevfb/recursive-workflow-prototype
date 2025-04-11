#!/usr/bin/env python3
import argparse
import json

# Hardcoded list of builds. Each has an 'id', 'os', 'compiler', 'group', etc.
ALL_BUILDS = [
    {
        "id": "linux-jammy-py3_9-gcc11",
        "os": "ubuntu-latest",
        "compiler": "gcc11",
        "python_version": "3.9",
        "cuda": False,
        "group": "pull",
    },
    {
        "id": "linux-jammy-py3-clang12-mobile",
        "os": "ubuntu-latest",
        "compiler": "clang12",
        "python_version": "3.9",
        "cuda": False,
        "mobile": True,
        "group": "pull",
    },
    {
        "id": "linux-jammy-py3-clang12-executorch",
        "os": "ubuntu-latest",
        "compiler": "clang12",
        "python_version": "3.9",
        "cuda": False,
        "group": "pull",
    },
    {
        "id": "linux-focal-cuda12.6-py3.10-gcc11-no-ops",
        "os": "ubuntu-latest",
        "compiler": "gcc11",
        "python_version": "3.10",
        "cuda": "12.6",
        "no_ops": True,
        "group": "trunk",
    },
    {
        "id": "win-vs2022-cuda12.6-py3",
        "os": "windows-latest",
        "compiler": "msvc2022",
        "python_version": "3.10",
        "cuda": "12.6",
        "group": "trunk",
    },
    {
        "id": "linux-focal-rocm-py3.10",
        "os": "ubuntu-latest",
        "compiler": "rocm",
        "python_version": "3.10",
        "cuda": False,
        "group": "periodic",
    },
]

def get_test_matrix_for(build):
    """
    Returns a list of test configurations (shards, etc.) for the given build.
    Modify or expand as needed.
    """
    # Example logic: if 'cuda' or 'rocm' is set, assume GPU, use 3 shards;
    # otherwise 2 shards for CPU.
    # We'll just do "debug" config for everything, but you can adapt to do
    # "distributed", "jit_legacy", "docs_test", etc.
    if build.get("cuda") or build.get("compiler") == "rocm":
        shard_count = 3
    else:
        shard_count = 2

    test_list = []
    for shard_index in range(1, shard_count + 1):
        test_list.append({
            "os": build["os"],
            "compiler": build["compiler"],
            "config": "debug",
            "shard": shard_index,
        })
    return test_list

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", help="Filter by group (pull, trunk, periodic)", default=None)
    # You could add additional filters here, e.g. --compiler, --os, etc.
    args = parser.parse_args()

    # Filter the builds by group, if specified
    if args.group:
        filtered_builds = [b for b in ALL_BUILDS if b.get("group") == args.group]
    else:
        filtered_builds = ALL_BUILDS

    # Construct the final array: each element has {"build": build, "test": [...]}
    output = []
    for b in filtered_builds:
        test_matrix = get_test_matrix_for(b)
        output.append({
            "build": b,
            "test": test_matrix,
        })

    # Print JSON to stdout so GitHub Actions can capture it
    print(json.dumps(output))

if __name__ == "__main__":
    main()
