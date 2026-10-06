import json
from google.protobuf import json_format
import sys
import glob
from collections.abc import MutableMapping

from app.app_io_pb2 import Result, ExperimentResultPart


def flatten(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if "uration" in new_key:
            v = float(v.replace("s", ""))
        if isinstance(v, MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


if __name__ == "__main__":
    results_part = []
    for dir in sys.argv[1:]:
        for res in glob.glob(dir + "/result-*-*.binary_proto"):
            part = ExperimentResultPart()
            f = open(res, "rb")
            part.ParseFromString(f.read())
            f.close()
            results_part += [
                flatten(json_format.MessageToDict(p)) for p in part.results
            ]
    print(json.dumps(results_part))
