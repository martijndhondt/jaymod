#!/usr/bin/env python3
"""Minimal M4 template expander for the Jaymod build system.

Replaces: m4 -I <include_dir> <template.m4>
Usage:    python m4expand.py <m4_include_dir> <template.m4>

Handles the subset of M4 used by Jaymod templates:
  changequote / changecom / include directives
  define(<<__var>>, <<value>>)dnl  (parsed from project.m4)
  __varname substitution
  <<>>  concatenation marker
  dnl   comment-to-end-of-line
  ifelse(__var, value, then_text, <<else_text>>)dnl
"""

import os
import re
import sys


def load_definitions(m4_dir):
    """Parse project.m4 and return a dict of __varname -> value."""
    defs = {}
    path = os.path.join(m4_dir, 'project.m4')
    with open(path, 'r') as f:
        for line in f:
            m = re.match(r'define\(<<(__\w+)>>,\s*<<([^>]*)>>\)dnl', line)
            if m:
                defs[m.group(1)] = m.group(2)
    return defs


def substitute(text, defs):
    """Replace __varname (and __varname() call form) with their values."""
    for name, value in defs.items():
        text = text.replace(name + '()', value)
    for name, value in defs.items():
        text = text.replace(name, value)
    text = text.replace('<<>>', '')
    return text


def expand_ifelse(m, defs):
    """Evaluate ifelse(var, expected, then_text, <<else_text>>) and return result."""
    cond_var = m.group(1)
    expected  = m.group(2)
    then_text = m.group(3)
    else_text = m.group(4)

    actual = defs.get(cond_var, '')
    result = then_text if actual == expected else else_text

    # Strip a leading "dnl\n" that M4 would consume when outputting the block.
    result = re.sub(r'^dnl\n?', '', result)

    return substitute(result, defs)


def expand(template_path, m4_dir):
    """Return the expanded content of an M4 template."""
    defs = load_definitions(m4_dir)

    with open(template_path, 'r') as f:
        text = f.read()

    # Remove M4 control-directive lines (changequote / changecom / include).
    text = re.sub(r'^changequote\([^)]*\)dnl\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^changecom\([^)]*\)dnl\n?',   '', text, flags=re.MULTILINE)
    text = re.sub(r'^include\([^)]*\)dnl\n?',      '', text, flags=re.MULTILINE)

    # Expand ifelse(var, val, then, <<else>>)dnl blocks (may span lines).
    text = re.sub(
        r'ifelse\((__\w+),\s*(\w+),\s*(.*?),\s*<<(.*?)>>\)dnl\n?',
        lambda m: expand_ifelse(m, defs),
        text,
        flags=re.DOTALL,
    )

    # Remove standalone dnl lines.
    text = re.sub(r'^dnl[^\n]*\n?', '', text, flags=re.MULTILINE)

    # Strip inline dnl comments (dnl to end of line → keep the newline).
    text = re.sub(r'dnl[^\n]*', '', text)

    return substitute(text, defs)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f'Usage: {sys.argv[0]} <m4_include_dir> <template.m4>', file=sys.stderr)
        sys.exit(1)

    print(expand(sys.argv[2], sys.argv[1]), end='')
