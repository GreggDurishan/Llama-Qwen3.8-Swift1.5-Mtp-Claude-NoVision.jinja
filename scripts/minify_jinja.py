import re
import sys

def minify_jinja(content):
    # Remove single line jinja comments {# ... #} if any
    content = re.sub(r'\{#.*?#\}', '', content, flags=re.DOTALL)
    return content.replace('\n', '')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python minify_jinja.py <input.jinja> <output.txt>")
        sys.exit(1)
        
    with open(sys.argv[1], 'r') as f:
        content = f.read()

    with open(sys.argv[2], 'w') as f:
        f.write(minify_jinja(content))
