#!/usr/bin/env python3
"""Fix Pipeline constructor calls in test files."""

import re


def fix_pipeline_tests():
    """Fix all Pipeline constructor calls in test_pipeline_coverage.py"""

    with open('tests/test_pipeline_coverage.py') as f:
        content = f.read()

    # Pattern 1: Pipeline(guards) -> Pipeline("test_pipeline", guards)
    content = re.sub(
        r'(\s+)pipeline = Pipeline\(guards\)',
        r'\1pipeline = Pipeline("test_pipeline", guards)',
        content
    )

    # Pattern 2: Pipeline(guards, param=value) -> Pipeline("test_pipeline", guards, param=value)
    content = re.sub(
        r'(\s+)pipeline = Pipeline\(guards, ([^)]+)\)',
        r'\1pipeline = Pipeline("test_pipeline", guards, \2)',
        content
    )

    # Fix validate calls to use keyword argument
    content = re.sub(
        r'\.validate\(([^,]+), ctx\)',
        r'.validate(\1, ctx=ctx)',
        content
    )

    # Fix validate calls with no context
    content = re.sub(
        r'\.validate\("([^"]+)"\)(?!\s*,)',
        r'.validate("\1", ctx=Context())',
        content
    )

    # Need to import Context if not already imported
    if 'from safellm.context import Context' not in content and 'from .context import Context' not in content:
        # Find imports section and add Context import
        import_lines = []
        other_lines = []
        in_imports = True

        for line in content.split('\n'):
            if line.startswith('import ') or line.startswith('from ') or line.strip() == '' or line.startswith('#'):
                if in_imports:
                    import_lines.append(line)
                else:
                    other_lines.append(line)
            else:
                in_imports = False
                other_lines.append(line)

        # Add Context import
        import_lines.append('from safellm.context import Context')
        content = '\n'.join(import_lines + other_lines)

    with open('tests/test_pipeline_coverage.py', 'w') as f:
        f.write(content)

    print("Fixed Pipeline constructor calls in test_pipeline_coverage.py")

if __name__ == '__main__':
    fix_pipeline_tests()
