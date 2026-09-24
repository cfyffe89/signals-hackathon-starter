#!/usr/bin/env python3
"""
Print the full, ref-resolved detail (parameters, requestBody, responses) for
ONE operation, without loading the whole spec file into context.

Usage:
    python3 scripts/lookup_endpoint.py --system <core|data-factory> <file.yaml> <METHOD> <path>
    python3 scripts/lookup_endpoint.py --system <core|data-factory> --grep <text>

Examples:
    python3 scripts/lookup_endpoint.py --system core entities.yaml GET /entities/{eid}
    python3 scripts/lookup_endpoint.py --system core --grep createSample
    python3 scripts/lookup_endpoint.py --system data-factory sdf-openapi.yaml POST /api/v2/maps
    python3 scripts/lookup_endpoint.py --system data-factory --grep publication

Look up the file/method/path in references/endpoint-index-<system>.md first
(or use --grep to search that index directly by any substring — path,
operationId, tag, or summary word).

All $ref pointers in both systems' specs are local to their own file
(#/components/...), so refs are resolved within the single spec file only —
no cross-file resolution needed. Resolution recurses but stops at a depth
limit to avoid runaway output on self-referential schemas.

core and data-factory are different product surfaces with different base
URLs, auth failure behavior, and conventions (see references/guide/core/ vs
references/guide/data-factory/) — always pass the correct --system.
"""
import argparse
import copy
import os
import sys

import yaml

ROOT = os.path.join(os.path.dirname(__file__), "..")
MAX_DEPTH = 6


def resolve_refs(node, doc, depth=0, seen=None):
    if seen is None:
        seen = set()
    if depth > MAX_DEPTH:
        return "... (max ref depth reached)"
    if isinstance(node, dict):
        if "$ref" in node and isinstance(node["$ref"], str) and node["$ref"].startswith("#/"):
            ref = node["$ref"]
            if ref in seen:
                return {"$ref": ref, "note": "circular reference, not expanded further"}
            target = doc
            for part in ref.lstrip("#/").split("/"):
                part = part.replace("~1", "/").replace("~0", "~")
                if not isinstance(target, dict) or part not in target:
                    return {"$ref": ref, "note": "unresolved"}
                target = target[part]
            resolved = resolve_refs(copy.deepcopy(target), doc, depth + 1, seen | {ref})
            extra = {k: v for k, v in node.items() if k != "$ref"}
            if extra and isinstance(resolved, dict):
                merged = dict(resolved)
                merged.update(extra)
                return merged
            return resolved
        return {k: resolve_refs(v, doc, depth, seen) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve_refs(v, doc, depth, seen) for v in node]
    return node


def grep_index(system, term):
    index_path = os.path.join(ROOT, "references", f"endpoint-index-{system}.md")
    if not os.path.exists(index_path):
        print(f"Index not found for system '{system}' — run scripts/build_index.py --system {system} first.", file=sys.stderr)
        sys.exit(1)
    term_lower = term.lower()
    with open(index_path, encoding="utf-8") as f:
        matches = [line for line in f if line.startswith("|") and term_lower in line.lower()]
    if not matches:
        print(f"No index rows matched '{term}' in system '{system}'.")
        return
    print(f"{len(matches)} match(es):\n")
    print("| File | Method | Path | operationId | Tags | Summary |")
    print("|---|---|---|---|---|---|")
    for m in matches:
        print(m.rstrip("\n"))


def lookup(system, fname, method, path):
    spec_dir = os.path.join(ROOT, "spec", system)
    fpath = os.path.join(spec_dir, fname)
    if not os.path.exists(fpath):
        print(f"No such spec file: {fname} in spec/{system}/", file=sys.stderr)
        sys.exit(1)
    doc = yaml.safe_load(open(fpath, encoding="utf-8"))
    paths = doc.get("paths", {})
    if path not in paths:
        candidates = [p for p in paths if p.lower() == path.lower()]
        if candidates:
            path = candidates[0]
        else:
            print(f"Path '{path}' not found in {fname}. Available paths in this file:", file=sys.stderr)
            for p in paths:
                print(f"  {p}", file=sys.stderr)
            sys.exit(1)
    item = paths[path]
    method_l = method.lower()
    if method_l not in item:
        print(f"Method {method} not found for {path}. Available methods: {list(item.keys())}", file=sys.stderr)
        sys.exit(1)
    op = resolve_refs(copy.deepcopy(item[method_l]), doc)
    print(yaml.dump({method.upper(): {path: op}}, sort_keys=False, allow_unicode=True, width=100))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--system", required=True, choices=["core", "data-factory"])
    ap.add_argument("--grep", help="search the endpoint index by substring instead of doing a direct lookup")
    ap.add_argument("file", nargs="?", help="spec yaml filename, e.g. entities.yaml or sdf-openapi.yaml")
    ap.add_argument("method", nargs="?", help="HTTP method, e.g. GET")
    ap.add_argument("path", nargs="?", help="path, e.g. /entities/{eid}")
    args = ap.parse_args()

    if args.grep:
        grep_index(args.system, args.grep)
        return

    if not (args.file and args.method and args.path):
        ap.print_help()
        sys.exit(1)

    lookup(args.system, args.file, args.method, args.path)


if __name__ == "__main__":
    main()
