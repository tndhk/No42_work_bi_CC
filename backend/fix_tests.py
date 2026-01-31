#!/usr/bin/env python3
"""Fix test files to properly unpack dynamodb_tables fixture."""
import re
from pathlib import Path

def fix_test_file(filepath: Path) -> None:
    """Fix a single test file."""
    content = filepath.read_text()

    # Pattern 1: table = dynamodb_tables['xxx'] -> tables, dynamodb = dynamodb_tables; table = tables['xxx']
    # This should be done at the beginning of each test function

    # Split into lines for easier processing
    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a line accessing dynamodb_tables dict directly
        if re.match(r'\s+table = dynamodb_tables\[', line):
            # Get indentation
            indent = re.match(r'(\s+)', line).group(1)

            # Insert unpacking line before this
            new_lines.append(f'{indent}tables, dynamodb = dynamodb_tables')
            # Modify current line
            new_line = line.replace('dynamodb_tables[', 'tables[')
            new_lines.append(new_line)
        elif 'with mock_aws():' in line:
            # Skip the with block opener
            i += 1
            # Skip the next line (dynamodb = boto3.resource...)
            i += 1
            # Unindent the following lines until we find dedent
            indent = re.match(r'(\s+)', line).group(1)
            inner_indent = indent + '    '

            # Continue until we find a line that's not indented with inner_indent
            while i < len(lines):
                next_line = lines[i]
                if next_line.startswith(inner_indent) and next_line.strip():
                    # Remove one level of indentation
                    dedented = next_line[4:]
                    new_lines.append(dedented)
                elif not next_line.strip():
                    # Empty line
                    new_lines.append(next_line)
                else:
                    # End of with block
                    i -= 1
                    break
                i += 1
        else:
            new_lines.append(line)

        i += 1

    # Write back
    filepath.write_text('\n'.join(new_lines))
    print(f'Fixed: {filepath}')

def main():
    """Fix all repository test files."""
    test_dir = Path(__file__).parent / 'tests' / 'repositories'

    for test_file in test_dir.glob('test_*.py'):
        fix_test_file(test_file)

    print('All files processed')

if __name__ == '__main__':
    main()
