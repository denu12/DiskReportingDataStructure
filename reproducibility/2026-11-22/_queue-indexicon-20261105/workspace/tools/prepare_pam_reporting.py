"""Generate explicit repairs to PAM's range-query example; retain upstream files."""
from pathlib import Path
import difflib
import shutil


def prepare(root, source):
    target=root/'build/pam-reporting'
    target.mkdir(parents=True,exist_ok=True)
    patches=[]
    changes={
        'range_utils.h': [('  data_type x, y;', '  c_type x, y;'),
                         ('  weight w;', '  w_type w;'),
                         ('  Point(data_type x, data_type y, weight w)', '  Point(c_type x, c_type y, w_type w)')],
        'range_tree.h': [('    int r;', '    size_t r;'),
                         ('  w_type query_count(', '  size_t query_count('),
                         ('r += (a.rank(y2) - a.rank(y1));', 'r += (a.rank(y2) - a.rank(y1) + size_t(a.contains(y2)));'),
                         ('point_y(e.first.second,e.first.second)', 'point_y(e.first.second,e.first.first)')],
    }
    for name, replacements in changes.items():
        original=(source/'examples/range_query'/name).read_text()
        text=original
        for old,new in replacements:
            if old not in text:raise RuntimeError('Unexpected PAM source: '+name)
            text=text.replace(old,new)
        (target/name).write_text(text)
        patches.extend(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='upstream/'+name,tofile='adapted/'+name))
    (target/'reporting.patch').write_text(''.join(patches))
    return target
