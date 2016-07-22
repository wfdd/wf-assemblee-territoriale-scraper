
import itertools as it
import sqlite3
from urllib.request import Request, urlopen

from lxml.html import document_fromstring as parse_html

base_url = 'http://www.wallis-et-futuna.pref.gouv.fr/Services-de-l-Etat-et-du-Territoire/Les-services-de-l-Assemblee-Territoriale'


def gather_people(doc):
    members_by_area = it.chain.from_iterable(i.xpath('''\
.//p[starts-with(string(.), "Pour ")] |
.//p[starts-with(string(.), "Pour ")]/following-sibling::ul''')
        for i in doc.xpath('''\
//table[@class="renderedtable" and
        contains(string(.), "Mandature 2012 – 2017")]
/following-sibling::table[@class="renderedtable" and
                          position() = 1 or
                          position() = 2]'''))
    members_by_area = (tuple(i) for _, i in it.groupby(members_by_area,
                                                       key=lambda i: i.tag))
    members_by_area = ((a.text_content().replace('Pour', '').strip(),
                        i.text_content().strip())
                       for (a,), m in zip(*(members_by_area,) * 2)
                       for i in m)
    for area, member in members_by_area:
        title, _, name = member.partition(' ')
        parts = name.split()
        surnames = tuple(it.takewhile(str.isupper, parts))
        yield (name,
               name,
               ' '.join(surnames),
               ' '.join(parts[len(surnames):]),
               {'M.': 'male', 'Mme': 'female'}[title],
               '2012',
               area)


def main():
    with urlopen(Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})) as r, \
            sqlite3.connect('data.sqlite') as c:
        c.execute('''\
CREATE TABLE IF NOT EXISTS data
(name, sort_name, family_name, given_name, gender, term, area,
 UNIQUE (name, term, area))''')
        c.executemany('''\
INSERT OR REPLACE INTO data VALUES (?, ?, ?, ?, ?, ?, ?)''',
            gather_people(parse_html(r.read().decode())))

if __name__ == '__main__':
    main()
