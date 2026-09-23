import sys

# Windows AppLocker policy blocks pyarrow._compute DLL in this environment.
# Setting pyarrow in sys.modules to None informs pandas and other libraries
# that pyarrow is unavailable so they cleanly use pure Python/NumPy fallbacks
# without triggering DLL load failures.
sys.modules['pyarrow'] = None
sys.modules['pyarrow.compute'] = None
