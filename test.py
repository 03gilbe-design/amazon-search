from pathlib import Path
import re
text = open(rstr(Path.home() / "amazon_search", ".claude", "worktrees", "amazon-improvements", "webui", "templates", "categorize.html"), encoding='utf-8').read()
matches = re.findall(r'onclick=[\'"]([^\'"]+)[\'"]', text)
for m in set(matches):
    print(m)
