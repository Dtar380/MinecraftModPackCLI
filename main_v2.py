from datetime import datetime, UTC
import hashlib
import json
from pathlib import Path
import requests  # type: ignore
import shutil
from typing import Union, Any

# ===============================================
# FILE DISCOVERY
# ===============================================
def get_mods(profile: str) -> list[Path]:
    instance_path = Path(
        f"C:\\Users\\dtar3\\AppData\\Roaming\\ModrinthApp\\profiles\\{profile}"
    )
    mods_path = instance_path / "mods"
    return list(mods_path.glob("*.jar"))

# ===============================================
# INDEX BUILDING
# ===============================================
def sha1(file_path: Path) -> str:
    h = hashlib.sha1()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def build_file_index(mods: list[Path]) -> dict[str, Path]:
    return {sha1(mod): mod for mod in mods}

# ===============================================
# MODRINTH API
# ===============================================
def resolve_mods(hashes: list[str]):
    return requests.post(
        "https://api.modrinth.com/v2/version_files",
        json={"hashes": hashes, "algorithm": "sha1"},
        timeout=10,
    ).json()


def get_project(project_id: str) -> Any:
    return requests.get(
        f"https://api.modrinth.com/v2/project/{project_id}", timeout=10
    ).json()


def is_library(project: Any) -> Any:
    categories = project.get("categories", [])
    return any(c in ["library", "api", "framework"] for c in categories)

# ===============================================
# DEPENDENCY RESOLVER
# ===============================================
def add_dependencies_with_map(seed_pack, all_mods):
    by_project = {m["project_id"]: m for m in all_mods}

    expanded = set(m["project_id"] for m in seed_pack)

    dependency_map = {m["project_id"]: set() for m in all_mods}

    changed = True
    while changed:
        changed = False

        for pid in list(expanded):
            mod = by_project.get(pid)
            if not mod:
                continue

            for dep in mod.get("dependencies", []):
                if dep["dependency_type"] != "required":
                    continue

                dep_id = dep["project_id"]
                if not dep_id:
                    continue

                dependency_map[pid].add(dep_id)

                if dep_id not in expanded:
                    expanded.add(dep_id)
                    changed = True

    full_pack = [by_project[pid] for pid in expanded if pid in by_project]

    return seed_pack, full_pack, dependency_map


def print_dependency_map(name, dep_map, mods):
    by_project = {m["project_id"]: m["name"] for m in mods}

    print(f"\n{name} DEPENDENCY MAP:\n")

    for mod_id, deps in dep_map.items():
        if not deps:
            continue

        print(f"- {by_project.get(mod_id, mod_id)}")
        for d in deps:
            print(f"    → {by_project.get(d, d)}")

# ===============================================
# EXPORTER
# ===============================================
def export_pack(pack, manifest, output_dir: str):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    mods_folder = output_path / "mods"
    mods_folder.mkdir(parents=True, exist_ok=True)

    for mod in pack:
        src = mod["file_path"]
        dst = mods_folder / src.name

        shutil.copy2(src, dst)

    save_manifest(manifest, output_path / "manifest.json")
    print(f"Exported {len(pack)} mods to {output_dir}")


def create_manifest(
    pack_name: str,
    minecraft_version: str,
    loader: str,
    seed_set: set,
    pack: list[dict]
) -> dict[str, Union[list, str]]:

    manifest: dict[str, Union[list, str]] = {
        "name": pack_name,
        "minecraft_version": minecraft_version,
        "loader": loader,
        "created_at": datetime.now(UTC).isoformat(),
        "mods": [],
    }

    by_project = {m["project_id"]: m for m in pack}

    for mod in pack:
        project_id = mod["project_id"]

        manifest["mods"].append(  # type: ignore
            {
                "name": mod["name"],
                "project_id": project_id,
                "version_id": mod["version_id"],
                "sha1": mod["sha1"],
                # classification
                "side": (
                    "server" if mod["server_side"] == "required" else "client"
                ),
                # seed vs dependency
                "source": "seed" if project_id in seed_set else "dependency",
                # explicit dependency list (resolved from Modrinth data)
                "dependencies": [
                    dep["project_id"]
                    for dep in mod.get("dependencies", [])
                    if dep.get("project_id") in by_project
                ],
            }
        )

    return manifest


def save_manifest(manifest, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

# ===============================================
# MAIN
# ===============================================
def main(
    name: str,
    minecraft_version: str,
    loader: str,
) -> None:
    # 1. Get mods
    mods = get_mods(name)
    print(f"Found {len(mods)} mods")

    # 2. Build hash index (MOST IMPORTANT FIX)
    file_index = build_file_index(mods)
    hashes = list(file_index.keys())

    # 3. Resolve via Modrinth
    result = resolve_mods(hashes)
    print("\nResolved mods:\n")

    mods_data = []

    # 3. Build structured mod objects
    counter = 1
    for file_hash, data in result.items():
        project_id = data["project_id"]
        version_id = data["id"]

        project = get_project(project_id)

        mods_data.append(
            {
                "name": project["title"],
                "project_id": project_id,
                "version_id": version_id,
                "client_side": project["client_side"],
                "server_side": project["server_side"],
                "file_path": file_index[file_hash],
                "sha1": file_hash,
                "dependencies": data.get("dependencies", []),
                "is_library": is_library(project),
            }
        )

        print(f"[{counter:03}] Fetched: {project['title']}")
        counter += 1

    # 4. Initial classification
    server_pack = []
    client_pack = []

    for mod in mods_data:

        # SERVER PACK RULE
        if mod.get("server_side", "optional") == "required" and not mod.get(
            "is_library", False
        ):
            server_pack.append(mod)

        # CLIENT PACK RULE
        if mod.get("client_side", "optional") != "unsupported" and not mod.get(
            "is_library", False
        ):
            client_pack.append(mod)

    # 5. Resolve dependencies
    server_seed, server_pack, server_map = add_dependencies_with_map(
        server_pack, mods_data
    )
    client_seed, client_pack, client_map = add_dependencies_with_map(
        client_pack, mods_data
    )

    server_seed_set = set([mod["project_id"] for mod in server_seed])
    client_seed_set = set([mod["project_id"] for mod in client_seed])

    # 6. Debbug lines
    print("\n--- FINAL PACK CHECK ---")

    all_ids = set(m["project_id"] for m in mods_data)
    server_ids = set(m["project_id"] for m in server_pack)
    client_ids = set(m["project_id"] for m in client_pack)

    lost = all_ids - (server_ids | client_ids)

    print(f"LOST MODS: {len(lost)}\n")

    for pid in lost:
        mod = next(m for m in mods_data if m["project_id"] == pid)
        print("-", mod["name"], mod["server_side"], mod["client_side"])

    # 7. Output
    print("\nSERVER PACK:")
    for i, m in enumerate(server_pack):
        print(f"[{i + 1:03}] {m["name"]}")
    print_dependency_map("SERVER", server_map, mods_data)

    print("\nCLIENT PACK:")
    for i, m in enumerate(client_pack):
        print(f"[{i + 1:03}] {m["name"]}")
    print_dependency_map("CLIENT", client_map, mods_data)

    server_manifest = create_manifest(
        name + " [server]",
        minecraft_version,
        loader,
        server_seed_set,
        server_pack,
    )
    client_manifest = create_manifest(
        name + " [client]",
        minecraft_version,
        loader,
        client_seed_set,
        client_pack,
    )

    export_pack(server_pack, server_manifest, "server")
    export_pack(client_pack, client_manifest, "client")

    print("\nFINISHED!")

if __name__ == "__main__":
    main(
        "AdventureCraft",
        "1.20.1",
        "Fabric"
    )
