#!/usr/bin/env python3
"""
awesh - Main entry point for the AI-aware interactive shell
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

try:
    from .shell import AweshShell
    from .config import Config
except ImportError:
    from shell import AweshShell
    from config import Config


def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        prog='awesh',
        description='AI-aware interactive shell - "AI by default, Bash when I mean Bash"'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='~/.aweshrc',
        help='Path to configuration file (default: ~/.aweshrc)'
    )
    
    parser.add_argument(
        '--no-stream',
        action='store_true',
        help='Disable streaming output from AI responses'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Override model specified in config'
    )
    
    parser.add_argument(
        '--dry-run-tools',
        action='store_true',
        help='Enable dry-run mode for MCP tool calls'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    return parser


def main():
    """Main entry point for awesh"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_path = Path(args.config).expanduser()
        config = Config.load(config_path)
        
        # Apply command line overrides
        if args.no_stream:
            config.streaming = False
        if args.model:
            config.model = args.model
        if args.dry_run_tools:
            config.dry_run_tools = True
            
        # Initialize and run the shell
        shell = AweshShell(config)
        try:
            shell.run()
        finally:
            # Cleanup if needed
            if hasattr(shell, 'cleanup'):
                asyncio.run(shell.cleanup())
        
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cli_main():
    """Entry point for setuptools console script"""
    main()


if __name__ == '__main__':
    cli_main()
