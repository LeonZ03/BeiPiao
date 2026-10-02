"""Run the unmodified Blender Lab MCP with Windows child-process isolation.

Blender background children must not inherit the MCP protocol input pipe or
attempt to attach to a console. This wrapper affects process launch only;
all MCP tools, schemas and Blender code execution remain the official package.
"""
import os
import subprocess
import sys

_run = subprocess.run

def _blender_run(args, *positional, **kwargs):
    if os.name == 'nt' and isinstance(args, (list, tuple)) and args and str(args[0]).lower().endswith('blender.exe'):
        kwargs.setdefault('stdin', subprocess.DEVNULL)
        kwargs['creationflags'] = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
        # Large room exports can exceed the official default 120 seconds.
        # Opt-in launch budget only; tools and execution remain official MCP.
        budget = os.environ.get('BLENDER_MCP_CLI_TIMEOUT_SECONDS')
        if budget:
            kwargs['timeout'] = max(float(kwargs.get('timeout', 120)), min(900, float(budget)))
    try:
        return _run(args, *positional, **kwargs)
    except subprocess.TimeoutExpired as error:
        if error.stdout:
            print('Blender startup diagnostic: ' + repr(error.stdout[-1500:]), file=sys.stderr)
        raise

subprocess.run = _blender_run
from blmcp import main
raise SystemExit(main())
