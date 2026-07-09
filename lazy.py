import re
path = r'C:\Users\Gilberto Bizzo\amazon_search\.claude\worktrees\amazon-improvements\webui\templates\categorize.html'
text = open(path, 'r', encoding='utf-8').read()

text = re.sub(r'<img (?![^>]*loading="lazy")', '<img loading="lazy" ', text)
text = text.replace("const img = document.createElement('img');", "const img = document.createElement('img');\n      img.loading = 'lazy';")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Replaced')
