"""Add an exact point-disk traversal to copies of the pinned Indexicon headers."""

from pathlib import Path
import sys


METHODS = {
    "kdtree.hpp": (
        "    template <typename OutIter>\n    void query(const Region& queryBox",
        """    template<class Disk, class Out>
    void queryDisk(const Disk& disk, Out out) const {
        queryDiskNode(root, disk, out);
    }

    template<class Disk, class Out>
    void queryDiskNode(const unique_ptr<Node>& node, const Disk& disk, Out& out) const {
        if (!node) return;
        const auto& lo = node->region.low;
        const auto& hi = node->region.high;
        if (!disk.intersects(lo[0], lo[1], hi[0], hi[1])) return;
        if (disk.covers(lo[0], lo[1], hi[0], hi[1])) {
            queryDumpAll(node, out);
        } else if (node->isLeaf) {
            for (const auto& [point, value] : asLeaf(node.get())->data)
                if (disk.contains(point[0], point[1])) *out++ = value;
        } else {
            const auto* branch = asInternal(node.get());
            queryDiskNode(branch->left, disk, out);
            queryDiskNode(branch->right, disk, out);
        }
    }

""",
    ),
    "quadtree.hpp": (
        "    template <typename OutIter>\n    void query(const QBox",
        """    template<class Disk, class Out>
    void queryDisk(const Disk& disk, Out out) const {
        if (!disk.intersects(box[XLOW], box[YLOW], box[XHIGH], box[YHIGH])) return;
        if (disk.covers(box[XLOW], box[YLOW], box[XHIGH], box[YHIGH])) {
            queryDumpAll(out);
        } else if (isLeaf()) {
            for (const auto& point : data)
                if (disk.contains(point.pt[0], point.pt[1])) *out++ = point.id;
        } else {
            for (const auto* child : children) child->queryDisk(disk, out);
        }
    }

""",
    ),
    "mxcif_quadtree.hpp": (
        "    template <typename OutIter>\n    void query(const MXCIFBox",
        """    // This overload is for trees indexed by zero-area point boxes.
    template<class Disk, class Out>
    void queryDisk(const Disk& disk, Out out) {
        if (!disk.intersects(box[XLOW], box[YLOW], box[XHIGH], box[YHIGH])) return;
        if (disk.covers(box[XLOW], box[YLOW], box[XHIGH], box[YHIGH])) {
            queryDumpAll(out);
            return;
        }
        auto report = [&](const auto& items) {
            for (const auto& point : items)
                if (disk.contains(point.box[XLOW], point.box[YLOW])) *out++ = point.id;
        };
        report(xStraddle);
        report(yStraddle);
        if (isLeaf()) report(data);
        else for (auto* child : children) child->queryDisk(disk, out);
    }

""",
    ),
}


def main():
    upstream, patched = map(Path, sys.argv[1:])
    patched.mkdir(parents=True, exist_ok=True)
    for name, (marker, method) in METHODS.items():
        source = (upstream / name).read_text()
        if source.count(marker) != 1:
            raise ValueError(f"Indexicon source differs from the pinned version: {name}")
        (patched / name).write_text(source.replace(marker, method + marker))


if __name__ == "__main__":
    main()
