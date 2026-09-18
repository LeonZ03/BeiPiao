"""Call Blender Lab's official MCP server via its standard STDIO transport.

Useful before Codex reloads its MCP tool list; this is an MCP client, not a
replacement Blender bridge. Prefer directly exposed MCP tools when available.
"""
import argparse
import asyncio
import datetime
import json
import os
import pathlib
import shutil
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = pathlib.Path(__file__).resolve().parent

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--tool')
    parser.add_argument('--args-file', type=pathlib.Path)
    parser.add_argument('--output', type=pathlib.Path)
    args = parser.parse_args()
    env = dict(os.environ)
    blender = env.get('BLENDER_PATH') or shutil.which('blender')
    if not blender:
        program_files = pathlib.Path(env.get('ProgramFiles', 'C:/Program Files'))
        candidates = list((program_files / 'Blender Foundation').glob('Blender */blender.exe'))
        candidates += [program_files / 'Steam/steamapps/common/Blender/blender.exe']
        blender = next((str(p) for p in sorted(candidates, reverse=True) if p.is_file()), None)
    if not blender:
        parser.error('Set BLENDER_PATH to your Blender executable, or put Blender on PATH. Website playback does not need Blender.')
    env.update(BLENDER_PATH=blender, PYTHONUTF8='1')
    env.setdefault('BLENDER_MCP_HOST', '127.0.0.1')
    env.setdefault('BLENDER_MCP_PORT', '9876')
    env.setdefault('BEIPIAO_ROOT', str(ROOT.parent))
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / 'run-official-blender-mcp.py')], env=env)
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=datetime.timedelta(seconds=300)) as client:
            await client.initialize()
            if args.list:
                result = await client.list_tools()
            else:
                if not args.tool:
                    parser.error('--tool or --list is required')
                arguments = json.loads(args.args_file.read_text(encoding='utf-8')) if args.args_file else {}
                result = await client.call_tool(args.tool, arguments)
            serialized = result.model_dump(mode='json', exclude_none=True)
            output = json.dumps(serialized, ensure_ascii=False, indent=2)
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(output, encoding='utf-8')
            print(output)
            if getattr(result, 'isError', False):
                raise RuntimeError('The official Blender MCP tool returned an error')

asyncio.run(main())
