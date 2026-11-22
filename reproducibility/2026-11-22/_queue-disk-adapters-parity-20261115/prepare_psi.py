"""Allow the pinned PSI traversals to take an exact disk predicate."""

from pathlib import Path
import re
import shutil
import sys


def patch(root, file, transform):
    path = root / file
    before = path.read_text()
    after = transform(before)
    if after == before:
        raise ValueError(f"PSI source differs from the pinned version: {file}")
    path.write_text(after)


def base_declarations(text):
    start = text.index("/* range query stuffs */")
    end = text.index(" * utility", start)
    part = text[start:end].replace("typename Range>", "typename Range, typename QueryShape>")
    return text[:start] + part.replace("box_type const &query_box", "QueryShape const &query_box") + text[end:]


def base_queries(text):
    start = text.index("/* orthogonal range query in leaf */")
    end = text.index(" * Convenience range_query:", start)
    part = text[start:end].replace("typename Range>", "typename Range, typename QueryShape>")
    part = part.replace("box_type const &query_box", "QueryShape const &query_box")
    part = part.replace("within_box(tl->pts[0], query_box)", "psi_disk_point<Traits>(tl->pts[0], query_box)")
    part = part.replace("within_box(tl->pts[i], query_box)", "psi_disk_point<Traits>(tl->pts[i], query_box)")
    part = part.replace("within_box(p, query_box)", "psi_disk_point<Traits>(p, query_box)")
    part = part.replace("box_intersect_box(box, query_box)", "psi_disk_intersects<Traits>(box, query_box)")
    part = part.replace("within_box(box, query_box)", "psi_disk_covers<Traits>(box, query_box)")
    return text[:start] + part + text[end:]


def tree_override(text, tree):
    pattern = rf"(template <typename Range>\s+auto {tree}<Traits>::range_query\()[\s\S]+?(?=\ntemplate <typename Traits>)"

    def replace(match):
        part = match[0].replace("typename Range>", "typename Range, typename QueryShape>", 1)
        part = part.replace("box_type const &query_box", "QueryShape const &query_box", 1)
        return part.replace("base_type::box_is_empty(query_box)", "psi_disk_empty<base_type>(query_box)")

    return re.sub(pattern, replace, text, count=1)


def main():
    source, dest = map(Path, sys.argv[1:])
    root = dest / "psi"
    shutil.copytree(source / "psi", root, dirs_exist_ok=True)
    patch(root, "base_tree.h", base_declarations)
    patch(root, "base_tree_impl/range_query.hpp", base_queries)
    for tree, stem in (("kd_tree", "kd"), ("orth_tree", "orth"), ("p_tree", "p")):
        def declaration(text):
            return re.sub(r"template <typename Range>\s+auto range_query\(box_type const &query_box,",
                          "template <typename Range, typename QueryShape>\n\tauto range_query(QueryShape const &query_box,",
                          text, count=1)
        patch(root, tree + ".h", declaration)
        patch(root, f"{tree}_impl/{stem}_override.hpp", lambda text: tree_override(text, tree))
    def cpam(text):
        for old, new in (
            ("base_type::box_intersect_box(node_box, query_box)", "psi_disk_intersects<base_type>(node_box, query_box)"),
            ("base_type::within_box(node_box, query_box)", "psi_disk_covers<base_type>(node_box, query_box)"),
            ("base_type::within_box(et, query_box)", "psi_disk_point<base_type>(et, query_box)"),
            ("base_type::within_box(rb->entry.first, query_box)", "psi_disk_point<base_type>(rb->entry.first, query_box)"),
        ):
            text = text.replace(old, new)
        return text
    patch(root, "dependence/cpam/augmented_ops.h", cpam)


if __name__ == "__main__":
    main()
