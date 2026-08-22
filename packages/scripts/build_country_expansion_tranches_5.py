from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'apps/web/src/data'
COLS=['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
VERIFIED='Live source HTTP 200 · verified 2026-08-22'
FREE='Free public web resource'

# (country, slug, track, topic_tags, priority, source_type, source_title, source_url, resource_title, resource_url, resource_class, language, notes)
R=[
 ('Egypt','egypt','GA','Thanaweya Amma;secondary;mathematics exam','A','Egypt Ministry of Education (Wayback capture)','Thanaweya Amma mathematics exams (official)','https://web.archive.org/web/20201019234601/http://moe.gov.eg/','2020 Thanaweya Amma algebra and solid geometry (English section)','https://web.archive.org/web/20201019234601/http://moe.gov.eg/booklet_new/last_years_Exams/2020/math/AlgebraSolidGeometry_E_3sec_C_2020.pdf','Exam','Arabic/English','Official Egyptian secondary-certificate mathematics examination (algebra and solid geometry) captured in the Wayback Machine, with English section.'),
 ('Egypt','egypt','GA','Thanaweya Amma;practice exam;English','A','Egypt Ministry of Education (Wayback capture)','June 2021 mathematics practice exam in English (official)','https://web.archive.org/web/20210624080527/https://moe.gov.eg/','2021 mathematics practice exam (English)','https://web.archive.org/web/20210624080527/https://moe.gov.eg/media/brodrbax/math-english-june21-practice.pdf','Exam','English','Official Egyptian secondary-education practice examination in English captured via the Wayback Machine.'),
 ('Egypt','egypt','GA','Thanaweya Amma;answer key;English','A','Egypt Ministry of Education (Wayback capture)','June 2021 mathematics answer key in English (official)','https://web.archive.org/web/20210624080514/https://moe.gov.eg/','2021 mathematics practice exam answer key (English)','https://web.archive.org/web/20210624080514/https://moe.gov.eg/media/0fjelwwg/answer-math-english-june21.pdf','Solutions','English','Official answer key for the English mathematics practice examination, captured via the Wayback Machine.'),
 ('Egypt','egypt','GA','dynamics;answer key;English','A','Egypt Ministry of Education (Wayback capture)','Dynamics 2021 practice answers in English (official)','https://web.archive.org/web/20210627100252/https://moe.gov.eg/','2021 dynamics practice answers (English)','https://web.archive.org/web/20210627100252/https://moe.gov.eg/media/2pngiixo/dynamics-english-session1-2021-prac-answers.pdf','Solutions','English','Official dynamics mathematics solutions for the 2021 practice examination in English, captured via the Wayback Machine.'),
 ('Egypt','egypt','GA','differentiation;integration;exam','A','Egypt Ministry of Education (Wayback capture)','2020 Thanaweya Amma differentiation and integration','https://web.archive.org/web/20201020003922/http://moe.gov.eg/','2020 Thanaweya Amma differentiation and integration exam','https://web.archive.org/web/20201020003922/http://moe.gov.eg/booklet_new/last_years_Exams/2020/math/Diff-Integr_A_3sec_C_2020.pdf','Exam','Arabic','Official Egyptian secondary-certificate mathematics examination covering differentiation and integration, captured via the Wayback Machine.'),
 ('Honduras','honduras','GA','OHM;olympiad;problems and solutions','A','Revista de Matematicas Aleph','Olimpiada Hondurena de Matematicas 2018-2021 (official)','https://matematicasaleph.com/2023/11/20/olimpiada-hondurena-de-matematicas-2018-2021/','OHM XVI-XIX problems and solutions compendium','https://matematicasaleph.com/wp-content/uploads/2025/06/compendio-soluciones.pdf','Problem set','Spanish','Full Honduran mathematics olympiad problems and solutions compendium for editions XVI-XIX hosted by the Aleph mathematics journal.'),
 ('Honduras','honduras','GA','OHM;national exams','A','Revista de Matematicas Aleph','OHM national examinations','https://matematicasaleph.com/examenes-de-la-ohm/','OHM national examination papers','https://matematicasaleph.com/wp-content/uploads/2025/06/2021-ohm.pdf','Exam','Spanish','Actual Honduran mathematics olympiad national examination papers across editions, hosted by the Aleph journal.'),
 ('Honduras','honduras','GA','OHM;national exam solutions','A','Revista de Matematicas Aleph','OHM national examination solutions','https://matematicasaleph.com/soluciones-de-los-examenes-de-la-ohm/','OHM national examination solutions','https://matematicasaleph.com/soluciones-de-los-examenes-de-la-ohm/','Solutions','Spanish','Solutions to the Honduran mathematics olympiad national examinations for recent editions, hosted by the Aleph journal.'),
 ('Honduras','honduras','GA','OHM;departmental rounds','A','Revista de Matematicas Aleph','OHM departmental round examinations','https://matematicasaleph.com/examenes-departamentales/','OHM departmental round papers','https://matematicasaleph.com/wp-content/uploads/2026/08/2024-I-Ronda.pdf','Exam','Spanish','Honduran mathematics olympiad departmental-round papers with first, second, and third round PDFs by year.'),
 ('Cuba','cuba','GA','Olimpiada Nacional;temarios;solutions','B','EDUNIV digital library','Olimpiadas Nacionales de Matematica de Cuba 2023','http://repositorio.eduniv.cu/','National olympiad problems and solutions compilations','https://web.archive.org/web/20250318174148/http://repositorio.eduniv.cu/files/original/d03f9520295eca05e454c04475e357b0.pdf','Exam','Spanish','Cuban national mathematics olympiad problem compilations with solutions for secondary-basic and pre-university levels, captured via the Wayback Machine.'),
 ('Dominican Republic','dominican_republic','GA','olympiad practice;problems;solutions','C','Educando (SEE)','Problemas matematicos anteriores','https://web.archive.org/web/20070711204929/http://www.educando.edu.do/','Mathematical problems with solutions (categories A-D)','https://web.archive.org/web/20070711204929/http://www.educando.edu.do/EducanDo/Administracion/Recursos/Curriculares/problemas+matematicos+anteriores.htm','Problem set','Spanish','Official education-portal mathematics problems with solutions across graded categories, captured via the Wayback Machine.'),
 ('Syria','syria','GA','APMO;regional olympiad;problems','B','Asian Pacific Mathematical Olympiad','APMO problems (official)','https://www.apmo-official.org/problems','APMO 2023 problems (Syria participant)','https://www.apmo-official.org/static/problems/apmo2023_prb.pdf','Problem set','English','Official Asian Pacific Mathematical Olympiad problems; Syria is an active participant in the regional competition.'),
 ('Tajikistan','tajikistan','GA','APMO;regional olympiad;problems','B','Asian Pacific Mathematical Olympiad','APMO problems (official)','https://www.apmo-official.org/problems','APMO 2022 problems (Tajikistan participant)','https://www.apmo-official.org/static/problems/apmo2022_prb.pdf','Problem set','English','Official Asian Pacific Mathematical Olympiad problems; Tajikistan is an active participant in the regional competition.'),
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
