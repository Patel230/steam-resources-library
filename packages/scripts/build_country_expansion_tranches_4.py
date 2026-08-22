from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'apps/web/src/data'
COLS=['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
VERIFIED='Live source HTTP 200 · verified 2026-08-22'
FREE='Free public web resource'

# (country, slug, track, topic_tags, priority, source_type, source_title, source_url, resource_title, resource_url, resource_class, language, notes)
R=[
 ('Switzerland','switzerland','GA','SMO;olympiad;problems','A','Swiss Mathematical Olympiad','SMO problems archive (official)','https://github.com/imosuisse/imosuisse.github.io','Swiss Mathematical Olympiad problems in English','https://imosuisse.github.io/problems/','Problem set','English','Official Swiss Mathematical Olympiad archive of 666 English problems filterable by topic and round, with original LaTeX sources spanning 1997-2019.'),
 ('Switzerland','switzerland','EM','ETH;analysis;lecture notes','B','ETH Zurich course notes','ETHZ Analysis I and II notes','https://github.com/moll-re/analysis','Analysis I and II course notes PDF','https://github.com/moll-re/analysis','Textbook','German','Full ETH Zurich Analysis I and II course notes compiled as a PDF; substantive university calculus content with exercises.'),
 ('Switzerland','switzerland','DM','informatics olympiad;contest problems','C','Swiss Olympiad in Informatics','SOI contest problems','https://github.com/paul-linked/Soi','Swiss Olympiad in Informatics problems 2021/22','https://github.com/paul-linked/Soi','Problem set','English','Swiss Olympiad in Informatics contest problems; computational and discrete-mathematics oriented.'),
 ('Ukraine','ukraine','GA','UMO;olympiad;problems and solutions','B','Ukrainian Mathematical Olympiad catalog','UMO problems archive','https://github.com/amrzv/olymp','Ukrainian Mathematical Olympiad problems with solutions','https://github.com/amrzv/olymp','Problem set','Ukrainian','Ukrainian Mathematical Olympiad problems for grades 6-11 across regional and national rounds with full solutions.'),
 ('Mozambique','mozambique','GA','national exams;mathematics','C','MozEstuda','Mozambican national mathematics exams','https://www.mozestuda.com','Matematica exams for classes 6, 9, 10, 12','https://www.mozestuda.com/todos-exames-de-matematica-da-10a-classe/','Exam archive','Portuguese','Free portal with downloadable Mozambican national mathematics examination papers across grades with problems.'),
 ('Mozambique','mozambique','EM','university admission;exams;solutions','C','Exames MozEstuda','Mozambican university admission exams','https://exames.mozestuda.com','UP/UEM/ISPG university admission mathematics exams with solutions','https://exames.mozestuda.com','Exam archive','Portuguese','Substantive university admission mathematics examinations with enunciados and resolutions for UP, UEM, and other institutions.'),
 ('Mozambique','mozambique','GA','national exams;catalogue','C','Internet Archive catalogue','Mozambique grade 10 mathematics exams index','https://archive.org/details/baixar-todos-exames-de-matematica-da-10a-classe-mocamique','Grade 10 mathematics exams catalogue','https://archive.org/details/baixar-todos-exames-de-matematica-da-10a-classe-mocamique','Exam archive','Portuguese','Internet Archive catalogue pointing to the collection of Mozambican grade 10 mathematics examinations.'),
 ('Democratic Republic of the Congo','democratic_republic_of_the_congo','GA','Exetat;national exam;maths','C','Internet Archive Exetat collection','Exetat mathematics items','https://archive.org/details/items-exetat-2017-pedagogie-math-physique-s-1-suite-code-m-10','Exetat pedagogie maths/physics paper','https://archive.org/details/items-exetat-2017-pedagogie-math-physique-s-1-suite-code-m-10','Exam','French','French-language national Exetat examination item covering mathematics and physics from the DR Congo state examination.'),
]


def main()->None:
    known=set()
    for p in DATA.glob('*.csv'):
        with p.open(newline='',encoding='utf-8') as h:
            for r in csv.DictReader(h):
                if r.get('resource_url'): known.add(r['resource_url'].strip().lower())
    counts={}; skipped=set()
    for row in R:
        url=row[9].strip().lower()
        if url in known: skipped.add(row[9]); continue
        out=DATA/f'{row[1]}_expansion_verified_resources.csv'
        rows=[]
        if out.exists():
            with out.open(newline='',encoding='utf-8') as h: rows=list(csv.DictReader(h))
            known.add(url)
        rec={'country':row[0],'track':row[2],'topic_tags':row[3],'priority':row[4],'source_type':row[5],'source_title':row[6],'source_url':row[7],'resource_title':row[8],'resource_url':row[9],'resource_class':row[10],'language':row[11],'notes':row[12],'access_model':FREE,'verification_status':VERIFIED,'free_resource':'Yes'}
        rows.append(rec)
        with out.open('w',newline='',encoding='utf-8') as h:
            w=csv.DictWriter(h,fieldnames=COLS); w.writeheader(); w.writerows(rows)
        counts[row[1]]=len(rows)
    print(f'Wrote tranches: {counts} ({sum(counts.values())} rows total)')
    if skipped: print('SKIPPED duplicates:',skipped)


if __name__=='__main__': main()
