"""One-off: download every image and PDF the old SBI pages reference into static/."""
import re, os, html, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST = 'essential-music-theory.com'
BASE = 'https://www.' + HOST
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/130 Safari/537.36'}


def unpagespeed(path):
    # /images/xNAME.jpg.pagespeed.ic.HASH.jpg -> /images/NAME.jpg ; also WxH prefix form
    m = re.match(r'^(.*/)(?:\d+x\d+)?x([^/]+?)\.pagespeed\.[a-z]{2}\.[^/]+$', path)
    return m.group(1) + m.group(2) if m else path


imgs, pdfs = set(), set()
for f in os.listdir(os.path.join(ROOT, 'source/pages')):
    s = open(os.path.join(ROOT, 'source/pages', f), errors='ignore').read()
    # data-pin-media holds the real address when src is an inlined placeholder
    for v in re.findall(r'<img[^>]*?\b(?:src|data-pin-media)="([^"]+)"', s, re.I) + re.findall(r'data-pin-media="([^"]+)"', s, re.I):
        v = html.unescape(v)
        if v.startswith('data:') or 'cgi-bin' in v:
            continue
        if v.startswith('//'):
            v = 'https:' + v
        if v.startswith('/'):
            v = BASE + v
        if HOST not in v:
            continue
        p = urllib.parse.urlparse(v).path
        if p.startswith(('/images/', '/image-files/')):
            imgs.add(unpagespeed(p))
    for v in re.findall(r'href="([^"]+\.pdf)/?"', s, re.I):
        p = urllib.parse.urlparse(html.unescape(v)).path
        if p.startswith('/support-files/'):
            pdfs.add(p)
imgs.add('/favicon.ico')


def get(path, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return 'have'
    try:
        r = urllib.request.urlopen(urllib.request.Request(BASE + urllib.parse.quote(path), headers=UA), timeout=30)
        data = r.read()
        open(dest, 'wb').write(data)
        return len(data)
    except Exception as e:
        return 'FAIL %s' % e


for p in sorted(imgs):
    dest = os.path.join(ROOT, 'static', 'favicon.ico') if p == '/favicon.ico' else os.path.join(ROOT, 'static/images', os.path.basename(p))
    print(get(p, dest), p)
for p in sorted(pdfs):
    print(get(p, os.path.join(ROOT, 'static/support-files', os.path.basename(p))), p)
