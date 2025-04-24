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
    
    # Determine additional components for the job name
    cuda_part = ""
    if build.get("cuda"):
        cuda_part = f"cuda{build.get('cuda')}-"
    elif build.get("rocm"):
        cuda_part = f"rocm{build.get('rocm')}-"
    
    compiler = build.get("compiler", "")
    
    # Build the job name
    build_job_name = f"{platform}-{distro}-{cuda_part}{py_version}-{compiler}"
    return build_job_name

def generate_test_job_name(build, test_config):
    """Generate a human-readable job name for the test job."""
    # Format: test (distributed, 1, 3, lf.ephemeral.linux.g4dn.12xlarge.nvidia.gpu)
    
    # Determine test config type based on build properties
    if build.get("mobile"):
        config = "mobile"
    elif "executorch" in build.get("id", ""):
        config = "executorch"
    elif build.get("no_ops"):
        config = "no_ops"
    elif build.get("cuda") or build.get("rocm"):
        config = "distributed"  # Assume distributed for GPU builds
    else:
        config = "default"
        
    shard = test_config.get("shard", 1)
    
    # Total shards - use custom value if specified in the build, otherwise follow standard logic
    if build.get("shard_count"):
        total_shards = build.get("shard_count")
    else:
        total_shards = 4 if build.get("cuda") or build.get("compiler") == "rocm" else 3
    
    # Instance type based on build configuration
    prefix = "lf.ephemeral."
    if "id" in build and "linux-focal-cuda12.6-py3.10-gcc11" in build["id"] and not build.get("no_ops"):
        instance = f"{prefix}linux.g4dn.12xlarge.nvidia.gpu"
    elif "rocm5.4" in build.get("id", ""):
        instance = f"{prefix}linux.g4dn.12xlarge.amd.gpu"
    elif "windows" in build.get("os", ""):
        instance = f"{prefix}windows.g4dn.12xlarge"
    elif build.get("cuda"):
        instance = f"{prefix}linux.g4dn.12xlarge.nvidia.gpu"
    elif build.get("compiler") == "rocm":
        instance = f"{prefix}linux.g4dn.12xlarge.amd.gpu"
    else:
        instance = f"{prefix}linux.2xlarge"
    
    # Generate the test job name in PyTorch format
    test_job_name = f"test ({config}, {shard}, {total_shards}, {instance})"
    return test_job_name

def get_test_matrix_for(build):
    """
    Returns a list of test configurations (shards, etc.) for the given build.
    Modify or expand as needed.
    """
    # Determine config type based on build properties
    if build.get("mobile"):
        config_type = "mobile"
    elif "executorch" in build.get("id", ""):
        config_type = "executorch"
    elif build.get("no_ops"):
        config_type = "no_ops"
    elif build.get("cuda") or build.get("rocm"):
        config_type = "distributed"  # Assume distributed for GPU builds
    else:
        config_type = "default"
    
    # Determine shard count
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
            "config": config_type,
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

    # Construct the final array with build info and test matrix
    output = []
    for b in filtered_builds:
        test_matrix = get_test_matrix_for(b)
        b["job_name"] = generate_build_job_name(b)  # Add job_name to the build object
        
        # Create an entry with build and test matrix
        entry = {
            "build": b,
            "test": test_matrix,
        }
        output.append(entry)

    # Print JSON to stdout so GitHub Actions can capture it
    print(json.dumps(output))

if __name__ == "__main__":
    main()
