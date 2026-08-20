from pathlib import Path
import sys
import cv2

path=Path(sys.argv[1])
image=cv2.imread(str(path))
if image is None:
    raise SystemExit(f'Cannot read {path}')
detector=cv2.QRCodeDetector()
text, points, _ = detector.detectAndDecode(image)
print(text or 'NO_QR_DECODED')
