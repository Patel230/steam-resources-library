from pathlib import Path
import subprocess

base = Path('/home/ubuntu/ga-em-dm-resource-hub/research/zimbabwe_buse_candidates')
pdf = base / 'buse_mte1101_2024.pdf'
render = base / 'rendered'
render.mkdir(exist_ok=True)
subprocess.run(['pdftoppm', '-r', '220', '-png', str(pdf), str(render / 'page')], check=True)
out = []
for image in sorted(render.glob('page-*.png')):
    txt = image.with_suffix('.txt')
    subprocess.run(['tesseract', str(image), str(txt.with_suffix('')), '--psm', '6'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    text = txt.read_text(errors='ignore') if txt.exists() else ''
    out.append(f'===== {image.name} =====\n{text}')
(base / 'buse_mte1101_2024_ocr.txt').write_text('\n'.join(out))
print('pages', len(out), 'chars', sum(len(x) for x in out))
