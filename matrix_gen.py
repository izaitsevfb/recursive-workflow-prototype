#!/usr/bin/env python3
import argparse
import json

# Hardcoded list of builds. Each has an 'id', 'os', 'compiler', 'group', etc.
ALL_BUILDS = [
    # Original builds
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
    # New CUDA build in pull group
    {
        "id": "linux-focal-cuda12.6-py3.10-gcc11",
        "os": "ubuntu-latest",
        "compiler": "gcc11",
        "python_version": "3.10",
        "cuda": "12.6",
        "group": "pull",
        # Specifying custom shard count
        "shard_count": 5,
    },
    # Original trunk and periodic builds
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
    # New ROCm build in pull group
    {
        "id": "linux-focal-rocm5.4-py3.9",
        "os": "ubuntu-latest",
        "compiler": "rocm",
        "python_version": "3.9",
        "cuda": False,
        "rocm": "5.4",
        "group": "pull",
        "shard_count": 4,
    },
]

def generate_build_job_name(build):
    """Generate a human-readable job name for the build job."""
    name = build["id"]
    platform = "linux"

    # Determine distro
    distro = ""
    if "jammy" in name:
        distro = "jammy"
    elif "focal" in name:
        distro = "focal"
    
    # Determine architecture
    arch = "amd64"  # default
    if "windows" in build.get("os", ""):
        platform = "win"
        arch = "x86_64"
    
    # Determine Python version with the format py3.10
    py_version = f"py{build['python_version']}"
    
    # Build the job name
    build_job_name = f"{platform}-{distro}-{arch}-{py_version}"
    return build_job_name

def generate_test_job_name(build, test_config):
    """Generate a human-readable job name for the test job."""
    # Format: test (default, 1, 4, linux.arm64.2xlarge)
    config = test_config.get("config", "default")
    shard = test_config.get("shard", 1)
    
    # Total shards - use custom value if specified in the build, otherwise follow standard logic
    if build.get("shard_count"):
        total_shards = build.get("shard_count")
    else:
        total_shards = 4 if build.get("cuda") or build.get("compiler") == "rocm" else 3
    
    # Instance type based on build configuration
    if "id" in build and "linux-focal-cuda12.6-py3.10-gcc11" in build["id"] and not build.get("no_ops"):
        instance = "linux.4xlarge.nvidia.gpu"
    elif "rocm5.4" in build.get("id", ""):
        instance = "linux.4xlarge.amd.gpu"
    elif "windows" in build.get("os", ""):
        instance = "windows.4xlarge"
    elif build.get("cuda"):
        instance = "linux.gpu.nvidia.4xlarge"
    elif build.get("compiler") == "rocm":
        instance = "linux.gpu.amd.4xlarge"
    else:
        instance = "linux.amd64.2xlarge"
    
    # Generate the test job name in PyTorch format
    test_job_name = f"({config}, {shard}, {total_shards}, {instance})"
    return test_job_name

def get_test_matrix_for(build):
    """
    Returns a list of test configurations (shards, etc.) for the given build.
    Modify or expand as needed.
    """
    # Example logic: if 'cuda' or 'rocm' is set, assume GPU, use 3 shards;
    # otherwise 2 shards for CPU.
    # We'll just do "debug" config for everything, but you can adapt to do
    # "distributed", "jit_legacy", "docs_test", etc.
    if build.get("shard_count"):
        shard_count = build.get("shard_count")
    elif build.get("cuda") or build.get("compiler") == "rocm":
        shard_count = 3
    else:
        shard_count = 2

    test_list = []
    for shard_index in range(1, shard_count + 1):
        test_config = {
            "os": build["os"],
            "compiler": build["compiler"],
            "config": "debug",
            "shard": shard_index,
        }
        # Add human-readable job name
        test_config["job_name"] = generate_test_job_name(build, test_config)
        test_list.append(test_config)
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

    # Construct the final array: each element has {"build": build, "test": [...], "job_name": "..."}
    output = []
    for b in filtered_builds:
        test_matrix = get_test_matrix_for(b)
        job_name = generate_build_job_name(b)
        output.append({
            "build": b,
            "test": test_matrix,
            "job_name": job_name,
        })

    # Print JSON to stdout so GitHub Actions can capture it
    print(json.dumps(output))

if __name__ == "__main__":
    main()
