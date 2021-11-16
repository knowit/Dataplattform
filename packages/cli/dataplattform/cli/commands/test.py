from pathlib import Path
import subprocess
import os 
from argparse import Namespace, ArgumentParser

def test_all():
    test_dirs = [p.resolve().parent for p in Path().glob("**/tox.ini")]
    for test_dir in test_dirs:
        os.chdir(test_dir)
        subprocess.run(["tox", "-r"])

def init(parser: ArgumentParser):
    pass

def run(args: Namespace, _):
    test_all()