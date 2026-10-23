"""Generate a small, reviewable PGM reporting patch; keep upstream untouched."""
from pathlib import Path
import difflib
import shutil


def prepare(root):
    source=root/'src/third_party/pgm-index/include'
    target=root/'build/pgm-reporting/include'
    shutil.copytree(source,target,dirs_exist_ok=True)
    path=target/'pgm/pgm_index_variants.hpp'
    original=path.read_text();text=original
    changes=[
        ('            if (*it > zmax)\n', '            if (it != super->data.end() && *it > zmax)\n'),
        ('                    it = std::upper_bound(super->data.begin() + range.lo, super->data.begin() + range.hi, bmin);\n                    --it;',
         '                    it = std::lower_bound(super->data.begin() + range.lo, super->data.begin() + range.hi, bmin);\n                    continue;'),
        ('            auto range = super->pgm.search(zmin);',
         '            if (super->data.empty()) { this->it = super->data.end(); return; }\n            auto range = super->pgm.search(zmin);'),
        ('        reference operator*() const { return p; }',
         '        size_t source_position() const { return it - super->data.begin(); }\n        reference operator*() const { return p; }'),
    ]
    for old,new in changes:
        if text.count(old)!=1:raise RuntimeError('PGM source differs from pinned reporting patch')
        text=text.replace(old,new)
    path.write_text(text)
    (root/'build/pgm-reporting/reporting.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='upstream/pgm_index_variants.hpp',tofile='adapted/pgm_index_variants.hpp')))
    return target
