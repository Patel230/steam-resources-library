from __future__ import annotations

import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'apps/web/src/data'
COLS=['country','track','topic_tags','priority','source_type','source_title','source_url','resource_title','resource_url','resource_class','language','notes','access_model','verification_status','free_resource']
VERIFIED='Live source HTTP 200 · verified 2026-08-22'
FREE='Free public web resource'

# (country, slug, track, topic_tags, priority, source_type, source_title, source_url, resource_title, resource_url, resource_class, language, notes)
R=[
 ('Spain','spain','GA','OME;olympiad;problems','A','Real Sociedad Matematica Espanola','Olimpiada Matematica Espanola problems archive (official)','https://rsme.es/olimpiada-matematica-espanola/','OME national and local phase problems with solutions','https://rsme.es/olimpiada-matematica-espanola/problemas-propuestos-y-resultados-2/','Problem set','Spanish','First-party RSME archive of national-phase olympiad problems 1993-2025 plus local-phase problems, with solution PDFs.'),
 ('Portugal','portugal','GA','OPM;olympiad;past papers','A','Sociedade Portuguesa de Matematica','Olimpiadas Portuguesas de Matematica (official)','https://www.spm.pt/','OPM past papers with solutions','https://olimpiadas.spm.pt/','Exam archive','Portuguese','Official SPM olympiad site with past papers (enunciados and solucoes) for Junior, A, and B categories across editions.'),
 ('Portugal','portugal','EM','national exams;mathematics;archive','A','IAVE','National final exams archive (official)','https://iave.pt/','Matematica A national exam archive 1997-2025','https://iave.pt/provas-e-exames/arquivo/arquivo-provas-e-exames-finais-nacionais-es/','Exam archive','Portuguese','Official exam body archive of Portuguese national final examinations including Matematica A by year.'),
 ('Greece','greece','GA','HMS;olympiad;problems and solutions','A','Hellenic Mathematical Society','HMS competitions problems and solutions (official)','https://hms.gr/','Thales/Euclides/Archimedes problems and solutions','https://hms.gr/competitions/','Exam archive','Greek','First-party Hellenic Mathematical Society archive of contest problems and solutions for Thales, Euclides, and Archimedes.'),
 ('Hungary','hungary','GA','Komal;problems;journal','A','Komal MATFUND','Komal problems in English (official)','https://komal.hu/','Monthly problems by difficulty with English translations','https://komal.hu/feladat?a=honap&h=202605&t=mat&l=en','Problem set','English','Official MATFUND journal problems by difficulty with full English translations, including discrete and contest items.'),
 ('Romania','romania','GA','ONM;olympiad;problems and solutions','A','Societatea de Stiinte Matematice din Romania','Olimpiada Nationala de Matematica (official)','https://ssmr.ro/','ONM problems and solutions for grades 5-12','https://ssmr.ro/onm2026','Exam archive','Romanian','Official national olympiad problems with solutions and rubrics for grades 5-12, archives reaching back to 2012.'),
 ('Romania','romania','DM','Gazeta Matematica;problems journal','A','SSMR','Gazeta Matematica problems (official)','https://gmb.ssmr.ro/','Gazeta Matematica problem collection','https://gmb.ssmr.ro/resurse/probleme','Problem set','Romanian','Official monthly mathematics journal problem collection covering high-school, middle-school, and primary levels.'),
 ('Poland','poland','GA','Olimpiada Matematyczna;problems','A','Polish Mathematical Society','Olimpiada Matematyczna problems archive (official)','https://om.mimuw.edu.pl/','OM problems and solutions stages 1-3','https://om.mimuw.edu.pl/problems/','Exam archive','Polish','Official Polish Mathematical Olympiad archive of problems and solutions for stages 1-3 across editions 47-77.'),
 ('Czechia','czechia','GA','Matematicka olympiada;problems','A','Matematicka olympiada (JCMF/MU)','Matematicka olympiada archive (official)','https://matematickaolympiada.cz/','MO round problems and solutions by year','https://matematickaolympiada.cz/mo-pro-ss/rocnik','Exam archive','Czech','Official Czech Mathematical Olympiad archive of round problems and solutions by year with English toggle.'),
 ('Czechia','czechia','DM','M&M correspondence seminar;problems','C','M&M seminar MFF UK','M&M correspondence seminar archive','https://mam.mff.cuni.cz/','Math and informatics seminar problem archive','https://mam.mff.cuni.cz/archiv/rocniky/','Problem set','Czech','Free mathematics and informatics correspondence seminar with a CC-BY problem archive including discrete-material items.'),
 ('Belgium','belgium','GA','VWO;olympiad;past problems','A','Vlaamse Wiskunde Olympiade','VWO contest problems archive (official)','https://www.vwo.be/','JWO and VWO contest questions by year and round','https://www.vwo.be/vwo/wedstrijdvragen-per-jaargang-en-ronde/','Exam archive','Dutch','Official Flemish mathematics olympiad archive of 3000+ contest questions as PDFs spanning 1986-2026.'),
 ('Belarus','belarus','GA','olympiad;competitions portal','B','Academy of Education Belarus','National olympiad and tournament portal (official)','https://olimp.adu.by/','Olympiad and competition hub with links to materials','https://olimp.adu.by/','Official gateway','Russian','Official national educational-portal hub for olympiads and competitions with distance events and links to materials.'),
 ('Madagascar','madagascar','GA','Baccalaureat malgache;series D;corriges','A','Ministere de l Education Nationale Madagascar','EDUCMAD media library (official)','http://mediatheque.accesmad.org/educmad/','Baccalaureat maths series D papers with corriges','http://mediatheque.accesmad.org/educmad/course/view.php?id=816','Exam archive','French','First-party ministry digital library with official baccalaureat mathematics series D papers and corriges for 1999-2023.'),
 ('Madagascar','madagascar','GA','Bac/BEPC/CEPE;sujets','C','College Saint Joseph Mahamasina','CSJ Mahamasina sujets archive','https://csjmahamasina.com/sujets','Bac/BEPC/CEPE mathematics sujets','https://csjmahamasina.com/sujets','Exam archive','French','Supplementary archive of Malagasy baccalaureate, BEPC, and CEPE mathematics subjects from 1999-2019.'),
 ('Mali','mali','GA','Baccalaureat malien;epreuves;corrections','C','Sigmaths','Bac Malien mathematics sujets','https://www.sigmaths.net/bac2/Mali.php','Baccalaureat mathematics papers with corrections','https://www.sigmaths.net/bac2/Mali.php','Exam archive','French','Deep archive of Malian baccalaureate mathematics papers across all series from 1978-2023, most with corrections.'),
 ('Burkina Faso','burkina_faso','GA','Baccalaureat;BEPC;mathematics','C','Sigmaths','Bac Burkina Faso mathematics sujets','https://www.sigmaths.net/bac2/Burkina_faso.php','Baccalaureat and BEPC mathematics papers','https://www.sigmaths.net/bac2/Burkina_faso.php','Exam archive','French','Burkina Faso baccalaureate and BEPC mathematics papers across series from 2014-2023 with corrections.'),
 ('Côte d’Ivoire','cote_divoire','GA','Baccalaureat ivoirien;BEPC;mathematics','C','Sigmaths','Bac Ivoirien mathematics sujets','https://www.sigmaths.net/bac2/RCI.php','Baccalaureat and BEPC mathematics papers','https://www.sigmaths.net/bac2/RCI.php','Exam archive','French','Ivorian baccalaureate and BEPC mathematics papers across series from 1990-2023 with corrections.'),
 ('Niger','niger','GA','Baccalaureat nigerien;annales;mathematics','C','Sigmaths','Bac Niger documents and annales','https://www.sigmaths.net/docEtranger/documents.php?country=niger','Baccalaureate mathematics papers and annales','https://www.sigmaths.net/docEtranger/documents.php?country=niger','Exam archive','French','Niger baccalaureate mathematics subjects with corrections plus annotated mathematical annales.'),
 ('Togo','togo','GA','Baccalaureat togolais;BEPC;mathematics','C','Sigmaths','Bac Afrique Togo mathematics','https://www.sigmaths.net/bac2/bacAfrique.php','Togolese baccalaureate and BEPC mathematics papers','https://www.sigmaths.net/bac2/bacAfrique.php','Exam archive','French','Togolese baccalaureate series D mathematics papers with corrections plus BEPC material.'),
 ('Guinea','guinea','GA','terminal;mathematics exam','C','Sigmaths','Guinea mathematics exam documents','https://www.sigmaths.net/docEtranger/details.php?doc_id=97','Terminale mathematics exam document','https://www.sigmaths.net/docEtranger/details.php?doc_id=97','Exam','French','Single terminale mathematics examination document for Guinea; thin but freely accessible.'),
 ('Benin','benin','GA','BEPC;brevet;mathematics','C','Sunudaara','Benin BEPC mathematics paper 2025','https://www.sunudaara.com/mathematiques','BEPC mathematics paper session normale 2025','https://www.sunudaara.com/mathematiques/brevet-detudes-du-premier-cycle-session-normale-benin-2025','Exam','French','Benin BEPC mathematics paper with statistics, affine functions, and analytic geometry problems.'),
 ('Sierra Leone','sierra_leone','GA','WASSCE;mathematics;national exam','A','WAEC Sierra Leone','WASSCE examinations (official)','https://www.waecsierraleone.org/','WASSCE mathematics national examination page','https://www.waecsierraleone.org/examinations/wassce','Official gateway','English','Official WAEC Sierra Leone page for WASSCE and BECE mathematics; national examination programme with papers available through official channels.'),
 ('Afghanistan','afghanistan','GA','Kankor;university entrance;mathematics','B','Internet Archive item','Kankor Math 1 collection','https://archive.org/details/kankor-math-1','Kankor mathematics question collection with answer key','https://archive.org/download/kankor-math-1/Kankor%20Math%201.pdf','Exam','Dari/Persian','Free Internet Archive collection of 3000+ categorised Kankor university-entrance mathematics questions from forms 1390-1400 with an answer key.'),
 ('Cambodia','cambodia','GA','Bac II;olympiad;outstanding student','C','Math-Book Cambodia','Math-Book Cambodia Grade 12 collection','https://mathbookcambodia.blogspot.com/','Grade 12 and outstanding-student olympiad problems with solutions','https://mathbookcambodia.blogspot.com/search/label/Math%2012','Problem set','Khmer','Free Khmer-language collection of Grade 12 and national outstanding-student olympiad problems with worked solutions plus IMO material.'),
 ('Guatemala','guatemala','GA','Olimpiada de Mayo;problems','B','OMA Olimpiada de Mayo archive','Olimpiada de Mayo nivel 1 2024','https://www.oma.org.ar/enunciados/index.htm','Olimpiada de Mayo problem set 2024 level 1','https://www.oma.org.ar/contents/enunciados/pdf/mayo/2024/enunciados_MAYO_nivel1_2024.pdf','Problem set','Spanish','Olimpiada de Mayo problem set for the national node run in Guatemala by Universidad Galileo; genuine multi-level competition problems.'),
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
