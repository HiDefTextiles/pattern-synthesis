"""Stack PNGs vertically with their file names as captions.
Usage: python3 scripts/contact_sheet.py OUT.png IN1.png IN2.png ..."""
import sys
from PIL import Image, ImageDraw

out, files = sys.argv[1], sys.argv[2:]
ims = [Image.open(f) for f in files]
pad = 30
sheet = Image.new("RGB", (max(i.width for i in ims), sum(i.height + pad for i in ims)), "white")
draw, y = ImageDraw.Draw(sheet), 0
for f, im in zip(files, ims):
    draw.text((6, y + 9), f.rsplit("/", 1)[-1].rsplit(".", 1)[0], fill="black")
    sheet.paste(im, (0, y + pad))
    y += im.height + pad
sheet.save(out)
