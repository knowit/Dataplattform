from pathlib import Path
import subprocess
import os
from argparse import Namespace, ArgumentParser


def test_all():
    test_dirs = [p.resolve().parent for p in Path().glob("**/tox.ini")]
    for test_dir in test_dirs:
        run_test(test_dir)


def run_test(test_dir: Path):
    os.chdir(test_dir)
    subprocess.run(["tox", "-r"])


def init(parser: ArgumentParser):
    parser.add_argument('-s', '--services', required=False, type=str, nargs='*')


def run(args: Namespace, _):
    if args.services:
        for service in args.services:
            path = Path(service).resolve()
            run_test(path)
    else:
        test_all()
