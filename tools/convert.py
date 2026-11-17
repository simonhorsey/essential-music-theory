"""One-off converter: source/pages/*.html (old SBI pages) -> content/*.html

Each output file is a small front-matter header plus the cleaned article HTML.
Strips the SBI wrapper, ads, social widgets, forms, tracking attributes and dead links.

Existing content files are NOT overwritten unless you pass --force, so hand edits are safe.
Usage:  python3 tools/convert.py [--force]
"""
import html, json, os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source', 'pages')
OUT = os.path.join(ROOT, 'content')
SITE = json.load(open(os.path.join(ROOT, 'site.json')))
REDIRECTS = SITE['redirects']
HOST = 'essential-music-theory.com'
FORCE = '--force' in sys.argv

# Pages written by hand in content/ (never generated from the old page).
HAND_WRITTEN = {'index', 'essential-music-theory', 'music-theory-blog', 'music-theory-questions', 'getintouch',
                'privacy-policy', 'music-theory-workbook'}
NOT_MIGRATED = set()

SECTION = {
    'reading': 'learn-to-read-music music-staff music-clef treble-clef bass-clef grand-staff learn-piano',
    'rhythm': 'music-note rhythm-tree dotted-note dotted-eighth-note dotted-whole-note double-dotted-note',
    'keys': 'key-signatures key-signature minor-key-signature',
    'intervals': 'music-intervals music-interval inverted-intervals',
    'resources': 'blank-manuscript-paper music-theory-workbook',
}
SLUG_SECTION = {slug: sec for sec, slugs in SECTION.items() for slug in slugs.split()}

# Visitor questions arrived with whatever title the visitor typed. These read better in a list.
QUESTION_TITLES = {}
if os.path.exists(os.path.join(ROOT, 'tools', 'question-titles.json')):
    QUESTION_TITLES = json.load(open(os.path.join(ROOT, 'tools', 'question-titles.json'), encoding='utf-8'))

# Outbound links that are dead or not worth keeping: keep the text, drop the link.
DEAD_HOSTS = ('sitesell.com', 'clickbank.net', 'amazon-adsystem.com', 'pinterest.com/pin', 'linkmaker.itunes.apple.com',
              'es.abrsm.org')
DEAD_AMAZON = ()
AFFILIATE = ('amazon.', 'amzn.to', 'shareasale.com', 'itunes.apple.com', 'books.apple.com')
DEAD_INTERNAL = ('/ledger-lines.html', '/how-to-read-music.html', '/inverting-intervals.html', '/onclick=')
BOOK_URL = SITE['offers']['book']['buy_url']

lastmod = {}
sm = open(os.path.join(ROOT, 'source', 'sitemap-original.xml'), errors='ignore').read()
for loc, lm in re.findall(r'<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>', sm):
    lastmod[loc.rstrip('/').split('/')[-1].replace('.html', '') or 'index'] = lm[:10]
lastmod['www.essential-music-theory.com'] = lastmod.get('index', '')

IMAGES = set(os.listdir(os.path.join(ROOT, 'static', 'images')))


def fix_href(href):
    """Return a cleaned href, or None to unwrap the link (keep its text)."""
    href = html.unescape(href).strip().replace('www,essential', 'www.essential')
    if href == 'http://www.essential-music-practice.com/clefs.html':  # a slip on the old site
        return '/music-clef.html'
    if href.startswith('//'):
        href = 'https:' + href
    if 'itunes.apple.com' in href and '920182047' in href:
        return BOOK_URL
    m = re.match(r'https?://(?:www\.)?' + re.escape(HOST) + r'(/.*)?$', href)
    if m:
        href = m.group(1) or '/'
    if href.startswith('/') or not re.match(r'[a-z]+:', href):
        if not href.startswith(('/', '#')):
            href = '/' + href
        path, _, frag = href.partition('#')
        if frag in ('INV', 'SOUND') or path.endswith('-comment-form.html'):
            return None
        path = re.sub(r'(\.pdf)/$', r'\1', path)
        if path in DEAD_INTERNAL and path in REDIRECTS:
            path = REDIRECTS[path]
        elif path in DEAD_INTERNAL or path.startswith('/%E2%80%9D'):
            return None
        path = REDIRECTS.get(path, path)
        return path + ('#' + frag if frag else '')
    if any(d in href for d in DEAD_HOSTS) or any(d in href for d in DEAD_AMAZON):
        return None
    return href


KEEP = {'p', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'a', 'img', 'strong', 'em', 'blockquote', 'br', 'hr',
        'table', 'thead', 'tbody', 'tr', 'td', 'th', 'figure', 'aside', 'sup', 'sub'}
RENAME = {'b': 'strong', 'i': 'em', 'h1': 'h2'}
VOID = {'br', 'hr', 'img'}


class Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.h1 = None
        self._in_h1 = False
        self._h1buf = []
        self.divs = []      # closing tag to emit for each open <div>
        self.links = []     # True if the open <a> was emitted

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'h1' and self.h1 is None:
            self._in_h1 = True
            return
        if self._in_h1:
            if tag == 'br':
                self._h1buf.append(' ')
            return
        if tag == 'div':
            cls = a.get('class', '') or ''
            if 'ImageBlock' in cls:
                side = 'right' if 'Right' in cls else 'left' if 'Left' in cls else 'center'
                self.out.append('<figure class="img-%s">' % side)
                self.divs.append('</figure>')
            elif 'CalloutBox' in cls:
                self.out.append('<aside class="callout">')
                self.divs.append('</aside>')
            else:
                self.divs.append('')
            return
        tag = RENAME.get(tag, tag)
        if tag not in KEEP:
            return
        if tag == 'p' and 'center' in (a.get('style') or '').replace(' ', ''):
            self.out.append('<p class="center">')
            return
        if tag == 'a':
            href = fix_href(a['href']) if a.get('href') else None
            if href is None:
                self.links.append(False)
                return
            self.links.append(True)
            extra = ''
            if re.match(r'https?:', href):
                rel = 'sponsored nofollow noopener' if any(x in href for x in AFFILIATE) else 'noopener'
                extra = ' rel="%s" target="_blank"' % rel
            self.out.append('<a href="%s"%s>' % (html.escape(href, quote=True), extra))
            return
        if tag == 'img':
            src = html.unescape(a.get('src', ''))
            if src.startswith('data:'):  # inlined placeholder: the real address is in data-pin-media
                src = html.unescape(a.get('data-pin-media') or '')
            if 'pagespeed' in src:
                m = re.match(r'^(.*/)(?:\d+x\d+)?x([^/]+?)\.pagespeed\.[a-z]{2}\.[^/]+$', src)
                src = m.group(1) + m.group(2) if m else src
            name = src.rsplit('/', 1)[-1]
            if HOST in src or src.startswith('/'):
                if name not in IMAGES:
                    return
                src = '/images/' + name
            elif 'amazon' in src or 'cgi-bin' in src or not src:
                return
            dims = ''
            for k in ('width', 'height'):
                v = (a.get(k) or '').split('.')[0]
                if v.isdigit():
                    dims += ' %s="%s"' % (k, v)
            self.out.append('<img src="%s" alt="%s"%s loading="lazy">' % (
                html.escape(src, quote=True), html.escape(a.get('alt') or '', quote=True), dims))
            return
        self.out.append('<%s>' % tag)

    def handle_endtag(self, tag):
        if tag == 'h1' and self._in_h1:
            self._in_h1 = False
            self.h1 = ' '.join(''.join(self._h1buf).split())
            return
        if self._in_h1:
            return
        if tag == 'div':
            if self.divs:
                self.out.append(self.divs.pop())
            return
        tag = RENAME.get(tag, tag)
        if tag == 'a':
            if self.links and self.links.pop():
                self.out.append('</a>')
            return
        if tag in KEEP and tag not in VOID:
            self.out.append('</%s>' % tag)

    def handle_data(self, data):
        if self._in_h1:
            self._h1buf.append(data)
        else:
            self.out.append(html.escape(data, quote=False))


def clean(raw):
    a = raw.find('id="ContentColumn"')
    b = raw.find('id="FooterWrapper"')
    if a < 0:
        return None, ''
    c = raw[raw.find('>', a) + 1:b]
    prev = None
    while prev != c:  # site-wide SBI blocks (promo box, what's new, forms, visitor submissions)
        prev = c
        c = re.sub(r'<!-- start: ((?:shared|tool)_blocks\.[^ ]+) -->.*?<!-- end: \1 -->', '', c, flags=re.S)
    c = re.sub(r'<!--.*?-->', '', c, flags=re.S)
    c = re.sub(r'<iframe[^>]*src="[^"]*youtube\.com/embed/([\w-]+)[^"]*"[^>]*>\s*</iframe>', r'<p>[[youtube:\1]]</p>', c, flags=re.S | re.I)
    c = re.sub(r'<(script|style|form|ins|noscript|iframe|select|textarea)\b.*?</\1>', '', c, flags=re.S | re.I)
    c = re.sub(r'<div class="pinit".*?</div>', '', c, flags=re.S)
    p = Cleaner()
    p.feed(c)
    out = ''.join(p.out)
    out = out.replace('\xa0', ' ')
    out = re.sub(r'\(\s*(?:This|this)?\s*(?:page |link )?opens? in a new window[^)]*\)', '', out)
    out = re.sub(r'<a [^>]*>(?:\s|<br>|<strong>|<em>)*(?:Return|Go back|Back) (?:to|from)\b(?:(?!</a>).)*</a>', '', out, flags=re.I | re.S)
    # the third-party quiz service the old pages linked to has closed: drop the invitations to take a quiz
    out = re.sub(r'<p(?: class="center")?>(?:(?!</p>).)*quiz\.cosmicsoft\.net(?:(?!</p>).)*</p>', '', out, flags=re.S)
    out = re.sub(r'<p>\s*\[\[youtube:([\w-]+)\]\]\s*</p>', r'<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/\1?rel=0" title="Video lesson" loading="lazy" allowfullscreen></iframe></div>', out)
    out = re.sub(r'<a [^>]*>\s*</a>', '', out)
    out = re.sub(r'(<br>\s*){2,}', '<br>', out)
    out = re.sub(r'<(h[234])>\s*(?:<strong>)?\s*(?:<br>)?\s*(.*?)\s*(?:<br>)?\s*(?:</strong>)?\s*</\1>', r'<\1>\2</\1>', out, flags=re.S)
    for _ in range(4):
        out = re.sub(r'<(p|strong|em|h2|h3|h4|li|figure|aside|blockquote|span)(?: class="center")?>(\s|<br>)*</\1>', '', out)
    out = re.sub(r'<(p|a [^>]*|strong)>\s*<br>\s*', r'<\1>', out)
    out = re.sub(r'\s*<br>\s*</(a|strong|h2|h3|li)>', r'</\1>', out)
    out = re.sub(r'(</(?:p|h2|h3|h4|ul|ol|figure|aside|table|div)>|<hr>)\s*(?:<br>\s*)+', r'\1\n', out)
    out = re.sub(r'(?:<br>\s*)+(<(?:p|h2|h3|h4|ul|ol|figure|aside|table|hr|div)\b)', r'\1', out)
    out = re.sub(r'\s*<br>\s*</p>', '</p>', out)
    out = re.sub(r'(<hr>\s*)+', '<hr>\n', out)
    out = re.sub(r'(\s*<hr>\s*)+$', '', out.strip())
    out = re.sub(r'[ \t]+', ' ', out)
    out = re.sub(r'\s*\n\s*', '\n', out)
    out = re.sub(r'</(p|h2|h3|h4|ul|ol|figure|aside|table|blockquote)>', r'</\1>\n', out)
    out = re.sub(r'<p>\s*(?=<(?:p|h2|h3|h4|ul|ol|figure|aside|table|hr|blockquote)\b)', '', out)
    out = re.sub(r'(</(?:p|h2|h3|h4|ul|ol|figure|aside|table|blockquote)>)\s*</p>', r'\1', out)
    out = re.sub(r'<p>\s*</p>', '', out)
    out = re.sub(r'\n{2,}', '\n', out).strip()
    for _ in range(3):  # a heading left with nothing under it (its quiz link or "return to" link was removed)
        out = re.sub(r'<(h[234])>(?:(?!</\1>).)*</\1>\s*(?:<hr>\s*)*(?=<h[23]>|$)', '', out, flags=re.S).strip()
        out = re.sub(r'(\s*<hr>\s*)+$', '', out)
    return p.h1, out


def paras(text):
    """Plain visitor text with <br> line breaks -> escaped paragraphs."""
    text = re.sub(r'<br\s*/?>', '\n', text)
    text = re.sub(r'<(/?)(?:b|strong)>', lambda m: '\ue000%sstrong\ue001' % m.group(1), text)
    text = re.sub(r'<(/?)(?:i|em)>', lambda m: '\ue000%sem\ue001' % m.group(1), text)
    text = html.unescape(re.sub(r'<[^>]+>', '', text)).replace('\xa0', ' ')
    out = []
    for block in re.split(r'\n\s*\n', text):
        lines = [' '.join(l.split()) for l in block.splitlines() if l.strip()]
        if lines:
            out.append('<p>%s</p>' % '<br>'.join(html.escape(l, quote=False) for l in lines))
    return '\n'.join(out).replace('\ue000', '<').replace('\ue001', '>')


def question(raw):
    """A visitor question page: the question, then every reply in date order."""
    m = re.search(r'<div id="submission_\d+"[^>]*>(.*?)(?:<table id="comments"|<!-- Music Theory Questions -->|<!-- Book Reviews -->)', raw, re.S)
    if not m:
        return None
    q = re.sub(r'<(script|style)\b.*?</\1>', '', m.group(1), flags=re.S)
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', q, re.S)
    title = ' '.join(html.unescape(re.sub(r'<[^>]+>', '', h1.group(1))).split()) if h1 else ''
    q = q[h1.end():] if h1 else q
    figures = []
    for src in re.findall(r'<img src="(?!data:)([^"]+)"', q):
        name = html.unescape(src).rsplit('/', 1)[-1]
        pm = re.match(r'^(?:\d+x\d+)?x(.+?)\.pagespeed\.[a-z]{2}\.[^/]+$', name)
        name = pm.group(1) if pm else name
        if name in IMAGES and name not in figures:
            figures.append(name)
    q = re.sub(r'<table id="thumbs">.*?</table>', '', q, flags=re.S)
    by = re.search(r'<p style="text-align:center;">\s*by\s+(.*?)</p>', q, re.S)
    asked = ''
    if by:
        asked = ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', by.group(1))).split())
        q = q.replace(by.group(0), '')
    body = ['<div class="question">', paras(re.sub(r'<img[^>]*>', '', q))]
    if asked:
        body.append('<p class="question__by">Asked by %s</p>' % html.escape(asked, quote=False))
    body += ['<figure class="img-center"><img src="/images/%s" alt="" loading="lazy"></figure>' % f for f in figures]
    body.append('</div>')
    replies = []
    for c in re.findall(r'<div id="comment_\d+">(.*?)<hr>', raw, re.S):
        date = re.search(r'class="date">\s*([A-Z][a-z]{2} \d{1,2}, \d{4})', c)
        head = re.search(r'<td valign="top" style="text-align:left;">\s*<strong>(.*?)</strong>', c, re.S)
        who = re.search(r'class="author"[^>]*><strong>by:\s*(.*?)</strong>', c, re.S)
        text = re.search(r'<span class="subBodyText">(.*?)</span>\s*</td>', c, re.S)
        who = ' '.join(html.unescape(who.group(1)).split()) if who else 'Anonymous'
        replies.append((date.group(1) if date else '', ' '.join(html.unescape(re.sub(r'<[^>]+>', '', head.group(1))).split()) if head else '',
                        who, paras(text.group(1)) if text else ''))
    replies.reverse()  # the old page listed newest first
    if replies:
        body.append('<h2>Answers</h2>')
    for date, head, who, text in replies:
        simon = who.lower() == 'simon'
        body.append('<article class="answer%s"><p class="answer__meta">%s%s</p>%s%s</article>' % (
            ' answer--simon' if simon else '', 'Simon Horsey' if simon else html.escape(who, quote=False),
            ' · ' + date if date else '', '<h3>%s</h3>' % html.escape(head, quote=False) if head else '', text))
    return title, '\n'.join(b for b in body if b), len(replies)


def meta(raw, name):
    m = re.search(r'<meta\s+name="%s"\s+content="(.*?)"' % name, raw, re.S | re.I)
    if not m:
        return ''
    return ' '.join(re.sub(r'<[^>]+>', '', html.unescape(html.unescape(m.group(1)))).split())


def main():
    os.makedirs(OUT, exist_ok=True)
    made = skipped = dropped = 0
    for f in sorted(os.listdir(SRC)):
        slug = f[:-5]
        if slug in HAND_WRITTEN or slug in NOT_MIGRATED or '/' + f in REDIRECTS:
            dropped += 1
            continue
        dest = os.path.join(OUT, f)
        if os.path.exists(dest) and not FORCE:
            skipped += 1
            continue
        raw = open(os.path.join(SRC, f), errors='ignore').read()
        asked = question(raw)
        if asked:
            title, body, n = asked
            if not n:
                print('question with no answers, not written (add a redirect):', f)
                continue
            title = QUESTION_TITLES.get(slug, title)
            desc = ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', body.split('</div>')[0].split('<p class="question__by">')[0])).split())
            desc = desc if len(desc) <= 155 else desc[:152].rsplit(' ', 1)[0] + '...'
            fm = ['---', 'title: ' + title, 'description: ' + desc, 'section: questions', 'updated: ' + lastmod.get(slug, ''), '---', '']
            open(dest, 'w').write('\n'.join(fm) + body + '\n')
            made += 1
            continue
        h1, body = clean(raw)
        if h1 is None and not body:
            print('no content column, skipped:', f)
            continue
        t = re.search(r'<title>(.*?)</title>', raw, re.S | re.I)
        title = ' '.join(re.sub(r'<[^>]+>', '', html.unescape(t.group(1))).split()) if t else slug
        fm = ['---', 'title: ' + (h1 or title), 'description: ' + meta(raw, 'description'),
              'section: ' + SLUG_SECTION.get(slug, 'page'), 'updated: ' + lastmod.get(slug, ''), '---', '']
        open(dest, 'w').write('\n'.join(fm) + body + '\n')
        made += 1
    print('written %d, kept existing %d, not migrated (redirected or hand-written) %d' % (made, skipped, dropped))


if __name__ == '__main__':
    main()
