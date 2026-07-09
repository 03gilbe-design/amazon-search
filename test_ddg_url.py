from duckduckgo_search import DDGS

with DDGS() as ddgs:
    results = [r for r in ddgs.text('amazon.it collare cervicale morbido', max_results=10)]
    for r in results:
        print(r)
