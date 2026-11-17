"""One-off: save every page of the old Solo Build It site into source/pages/ (untouched copies).

Starts from the old sitemap and follows internal .html links, so pages missing from the sitemap are found too.
Usage:  python3 tools/crawl.py
"""
import html, os, re, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'source', 'pages')
BASE = 'https://www.essential-music-theory.com'
SITEMAP = BASE + '/eCzjMO2d.xml'
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130 Safari/537.36'}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()


def main():
    os.makedirs(OUT, exist_ok=True)
    sm = get(SITEMAP)
    open(os.path.join(ROOT, 'source', 'sitemap-original.xml'), 'wb').write(sm)
    todo = [urllib.parse.urlparse(u).path or '/' for u in re.findall(r'<loc>([^<]+)</loc>', sm.decode('utf-8', 'ignore'))]
    seen, failed = set(), []
    while todo:
        path = todo.pop(0)
        if path in seen:
            continue
        seen.add(path)
        name = 'index.html' if path == '/' else path.lstrip('/')
        if '/' in name or not name.endswith('.html'):
            continue
        dest = os.path.join(OUT, name)
        if not os.path.exists(dest):
            try:
                open(dest, 'wb').write(get(BASE + urllib.parse.quote(path)))
                time.sleep(0.3)
            except Exception as ex:
                failed.append((path, str(ex)))
                continue
        raw = open(dest, errors='ignore').read()
        for href in re.findall(r'href="([^"#?]+)', raw):
            href = html.unescape(href).strip()
            m = re.match(r'(?:https?:)?//(?:www\.)?essential-music-theory\.com(/[^/]*\.html)$', href)
            p = m.group(1) if m else href if re.match(r'/[^/]+\.html$', href) else None
            if p and p not in seen:
                todo.append(p)
    print('saved %d pages' % len(os.listdir(OUT)))
    for f in failed:
        print('FAILED', f)


if __name__ == '__main__':
    main()
