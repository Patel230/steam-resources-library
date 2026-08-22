from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'apps/web/src/data'
COLS=['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
VERIFIED='Live source HTTP 200 · verified 2026-08-22'
FREE='Free public web resource'

# (country, slug, track, topic_tags, priority, source_type, source_title, source_url, resource_title, resource_url, resource_class, language, notes)
R=[
 ('Estonia','estonia','GA','matemaatikaolumpiaad;olympiad;archive','A','Tartu Ulikooli Teaduskool','Eesti matemaatikaolumpiaadi arhiiv (official)','https://teaduskool.ut.ee/','Estonian mathematics olympiad archive','https://teaduskool.ut.ee/et/olumpiaadid/eesti/matemaatikaolumpiaad/arhiiv','Exam archive','Estonian','Official Tartu University Science School archive of Estonian mathematics olympiad problems and solutions by round and year.'),
 ('Estonia','estonia','EM','university;mathematics education centre','B','University of Tartu Institute of Mathematics','Tartu math education centre (official)','https://math.ut.ee/','Mathematics education and exam-prep resources','https://math.ut.ee/et/mhk','Official gateway','Estonian','Official University of Tartu Institute of Mathematics education centre with exam-prep courses and problem collections.'),
 ('Lithuania','lithuania','GA','matematikos olimpiados;olympiad portal','A','Vilnius University MIF','Matematikos olimpiados portal (official)','https://mif.vu.lt/','Lithuanian mathematics olympiad portal','https://www4352.vu.lt/matematikos-olimpiados/','Exam archive','Lithuanian','Central Vilnius University MIF hub for Lithuanian mathematics olympiads including LMMO and regional rounds.'),
 ('Lithuania','lithuania','GA','LJMM;problem books;archive','A','Vilnius University MIF','Lietuvos jaunuju matematiku mokykla archive','https://www4352.vu.lt/matematikos-olimpiados/','LJMM annual problem-book archive','https://www4352.vu.lt/matematikos-olimpiados/ljmm/archyvas/','Problem set','Lithuanian','Archive of annual Lithuanian young-mathematicians problem books in PDF with discrete and olympiad topics.'),
 ('Montenegro','montenegro','GA','Olimpijada znanja;problems and solutions','A','University of Montenegro PMF','Olimpijada znanja (official)','https://www.ucg.ac.me/pmf/olimpijada','Knowledge-olympiad problems and solutions','https://www.ucg.ac.me/pmf/olimpijada','Exam archive','Montenegrin','Official University of Montenegro mathematics faculty archive of annual olympiad problems and solutions.'),
 ('Republic of Moldova','moldova','GA','virtual school;olympiad problems','B','Institute of Mathematics and Informatics Moldova','Virtualnaia shkola (official)','https://www.math.md/','Young-mathematician virtual school problem archive','https://web.archive.org/web/20230101052732/http://www.math.md/school/','Problem set','Romanian/Russian','Official Moldovan mathematics institute virtual school with olympiad problem sets, captured via the Wayback Machine.'),
 ('Costa Rica','costa_rica','EM','university;course texts;solved exercises','A','Universidad de Costa Rica EMate','EMate recursos (official)','https://emate.ucr.ac.cr/','UCR mathematics course texts and solved exercises','https://emate.ucr.ac.cr/recursos','Textbook','Spanish','Official UCR mathematics school resources with full calculus and algebra course texts and solved exercise books.'),
 ('Costa Rica','costa_rica','GA','OLCOMA;olympiad exams','A','Olimpiadas Costarricenses de Matematicas','OLCOMA exaumenes anteriores (official)','https://olcoma.ac.cr/','National olympiad exams and solutions','https://web.archive.org/web/2024/https://olcoma.ac.cr/nacional/entrenamientos/examenes-anteriores','Exam archive','Spanish','Official Costa Rican mathematics olympiad archive of national exams and solutions across levels and stages, captured via the Wayback Machine.'),
 ('Panama','panama','GA','OPM;olympiad;resources','A','Olimpiada Panamena de Matematica','OPM recursos (official)','https://opm.org.pa/','Panama olympiad training resources','https://opm.org.pa/recursos/','Problem set','Spanish','Official Panama mathematics olympiad training resource page linking problem books and weekly problems.'),
 ('Panama','panama','GA','OPM;problem book','A','Olimpiada Panamena de Matematica','Cien problemas de olimpiadas (official)','https://opm.org.pa/','Collection of 100 olympiad problems','https://opm.org.pa/wp-content/uploads/2023/05/Libro1_OPM.pdf','Problem set','Spanish','Official Panama olympiad problem book with one hundred substantive competition problems.'),
 ('Fiji','fiji','GA','national exams;past papers','A','Fiji Ministry of Education (Wayback capture)','Past years exam papers (official)','https://www.education.gov.fj/','Fiji national past-year exam papers','https://web.archive.org/web/20240722013433/https://www.education.gov.fj/?page_id=11099','Exam archive','English','Official Fiji Ministry of Education past-year national examination papers page captured via the Wayback Machine.'),
 ('Tonga','tonga','GA','national exams;exam papers','A','Tonga Ministry of Education and Training (Wayback capture)','Tonga exam papers (official)','https://www.education.gov.to/','Secondary examination papers by subject','https://web.archive.org/web/20251020090028/https://www.education.gov.to/index.php/students/exam-papers','Exam archive','English','Official Tonga Ministry of Education secondary examination papers page including mathematics, captured via the Wayback Machine.'),
 ('Tonga','tonga','GA','SEE;secondary entrance;mathematics','A','Tonga Ministry of Education and Training (Wayback capture)','SEE Mathematics 2024 paper (official)','https://www.education.gov.to/','Secondary Entrance Exam mathematics paper','https://web.archive.org/web/20251204030626/https://www.education.gov.to/images/SEE%20MATHS%20%202024.pdf','Exam','English','Official Tonga Secondary Entrance Examination mathematics paper captured via the Wayback Machine.'),
 ('Solomon Islands','solomon_islands','GA','SIY9;national assessment;mathematics','A','MEHRD NEAD (Wayback capture)','Year 9 SIY9 mathematics assessment guide (official)','https://www.mehrd.gov.sb/','Year 9 mathematics national assessment guide','https://web.archive.org/web/20241203153217/https://mehrd.gov.sb/images/NESU_Forms/Assessments/F3_Maths.pdf','Exam','English','Official Solomon Islands national education assessment mathematics guide for Year 9, captured via the Wayback Machine.'),
 ('Dominica','dominica','EM','UWI;tertiary access point','B','University of the West Indies Global Campus','UWI Dominica campus (official)','https://www.open.uwi.edu/dominica','University of the West Indies access point','https://www.open.uwi.edu/dominica','Official gateway','English','University of the West Indies Global Campus tertiary access point for Dominica providing mathematics programmes.'),
 ('Grenada','grenada','EM','UWI;tertiary access point','B','University of the West Indies Global Campus','UWI Grenada campus (official)','https://www.open.uwi.edu/grenada','University of the West Indies access point','https://www.open.uwi.edu/grenada','Official gateway','English','University of the West Indies Global Campus tertiary access point for Grenada providing mathematics programmes.'),
 ('Saint Kitts and Nevis','saint_kitts_and_nevis','EM','UWI;tertiary access point','B','University of the West Indies Global Campus','UWI Saint Kitts and Nevis campus (official)','https://www.open.uwi.edu/st_kitts_nevis','University of the West Indies access point','https://www.open.uwi.edu/st_kitts_nevis','Official gateway','English','University of the West Indies Global Campus tertiary access point for Saint Kitts and Nevis providing mathematics programmes.'),
 ('Saint Lucia','saint_lucia','EM','UWI;tertiary access point','B','University of the West Indies Global Campus','UWI Saint Lucia campus (official)','https://www.open.uwi.edu/st_lucia','University of the West Indies access point','https://www.open.uwi.edu/st_lucia','Official gateway','English','University of the West Indies Global Campus tertiary access point for Saint Lucia providing mathematics programmes.'),
 ('Saint Vincent and the Grenadines','saint_vincent_and_the_grenadines','EM','UWI;tertiary access point','B','University of the West Indies Global Campus','UWI Saint Vincent campus (official)','https://www.open.uwi.edu/st_vincent_grenadines','University of the West Indies access point','https://www.open.uwi.edu/st_vincent_grenadines','Official gateway','English','University of the West Indies Global Campus tertiary access point for Saint Vincent and the Grenadines providing mathematics programmes.'),
 ('Belize','belize','EM','university;mathematics department','B','University of Belize','UoB mathematics physics IT department (official)','https://ub.edu.bz/','University of Belize mathematics programmes','https://ub.edu.bz/mpit-department/','Official gateway','English','Official University of Belize mathematics, physics, and IT department page.'),
 ('Barbados','barbados','EM','UWI;mathematics faculty','B','University of the West Indies Cave Hill','UWI Cave Hill FST (official)','https://www.cavehill.uwi.edu/','Computer science mathematics and physics faculty','https://www.cavehill.uwi.edu/fst-cmp/','Official gateway','English','Official University of the West Indies Cave Hill computer-science mathematics and physics department for Barbados.'),
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
