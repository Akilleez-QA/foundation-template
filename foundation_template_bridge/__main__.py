import importlib
import sys

sys.dont_write_bytecode = True
raise SystemExit(importlib.import_module(".server", __package__).main())
