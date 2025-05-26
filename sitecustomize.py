import sys
from pathlib import Path
root = Path(__file__).resolve().parent
src_pkg = root / 'src' / 'echofoam_falsifiability'
if str(root) not in sys.path:
    sys.path.insert(0, str(root))
if src_pkg.exists() and str(src_pkg) not in sys.path:
    sys.path.insert(0, str(src_pkg))
