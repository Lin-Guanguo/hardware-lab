"""Small lossless-atom S-expression reader/writer for closed KiCad candidates."""
import json
import re
from pathlib import Path


class Quoted(str):
    pass


def parse(text):
    stack = []
    root = None
    for token in re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text):
        if token == '(':
            node = []
            if stack:
                stack[-1].append(node)
            else:
                assert root is None, 'Multiple roots'
                root = node
            stack.append(node)
        elif token == ')':
            stack.pop()
        else:
            stack[-1].append(Quoted(json.loads(token, strict=False)) if token.startswith('"') else token)
    assert not stack and root is not None
    return root


def read(path):
    return parse(Path(path).read_text())


def dumps(node, depth=0):
    if not isinstance(node, list):
        return json.dumps(str(node), ensure_ascii=False) if isinstance(node, Quoted) else str(node)
    if not any(isinstance(x, list) for x in node):
        return '(' + ' '.join(dumps(x) for x in node) + ')'
    out = '(' + ' '.join(dumps(x) for x in node if not isinstance(x, list))
    for child in node:
        if isinstance(child, list):
            out += '\n' + '\t' * (depth + 1) + dumps(child, depth + 1)
    return out + '\n' + '\t' * depth + ')'


def write(path, node):
    Path(path).write_text(dumps(node) + '\n')


def children(node, tag):
    return [x for x in node if isinstance(x, list) and x and x[0] == tag]


def child(node, tag):
    return next(iter(children(node, tag)), None)


def walk(node, tag):
    for x in node:
        if isinstance(x, list):
            if x and x[0] == tag:
                yield x
            yield from walk(x, tag)


def prop(node, name):
    return next((p for p in children(node, 'property') if p[1] == name), None)


def set_child(node, tag, *values):
    old = child(node, tag)
    if old is None:
        node.append([tag, *values])
    else:
        old[:] = [tag, *values]


def remove(node, *tags):
    node[:] = [x for x in node if not (isinstance(x, list) and x and x[0] in tags)]
