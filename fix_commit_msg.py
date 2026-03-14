import sys
import re

msg = sys.stdin.read()
# Remove leading number and dot (e.g., "1. ", "10. ")
new_msg = re.sub(r'^\d+\.\s+', '', msg)
print(new_msg, end='')
