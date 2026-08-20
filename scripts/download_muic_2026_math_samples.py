from pathlib import Path
import csv
import requests

FILES = {
    "muic_example_mathematics.pdf": "https://muic-www-assets.muic.io/example_of_mathematics_9b6942cb44.pdf",
    "muic_example_mathematics_part_i.pdf": "https://muic-www-assets.muic.io/Example_of_Mathematics_Part_I_095f91e877.pdf",
    "muic_example_mathematics_part_ii.pdf": "https://muic-www-assets.muic.io/Example_of_Mathematics_Part_II_79ebfeb35a.pdf",
    "muic_example_mathematics_part_iii.pdf": "https://muic-www-assets.muic.io/Example_of_Mathematics_Part_III_486634bfad.pdf",
    "muic_example_mathematics_part_iv.pdf": "https://muic-www-assets.muic.io/Example_of_Mathematics_Part_IV_f8f3930f24.pdf",
}
root = Path(__file__).resolve().parents[1] / "research" / "muic_2026_candidates"
root.mkdir(parents=True, exist_ok=True)
rows=[]
for name,url in FILES.items():
    path=root/name
    try:
        r=requests.get(url, timeout=30)
        path.write_bytes(r.content)
        rows.append({"file":name,"url":url,"status":r.status_code,"content_type":r.headers.get("content-type",""),"bytes":len(r.content),"final_url":r.url})
    except Exception as e:
        rows.append({"file":name,"url":url,"status":"ERROR","content_type":"","bytes":0,"final_url":str(e)})
with (root/"download_manifest.csv").open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
print(root)
