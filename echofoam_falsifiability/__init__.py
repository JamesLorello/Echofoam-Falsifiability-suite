import sys
from pathlib import Path

_src_pkg = Path(__file__).resolve().parent.parent / 'src' / 'echofoam_falsifiability'
if _src_pkg.exists():
    __path__ = [str(_src_pkg)]
    if str(_src_pkg) not in sys.path:
        sys.path.insert(0, str(_src_pkg))
else:
    __path__ = []
