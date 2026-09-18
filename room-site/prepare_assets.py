from pathlib import Path
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True

site = Path(__file__).resolve().parent
source = site.parent / 'Ref/永旺家园'
dest = site / 'dist/assets'
# Historical photo preparation; originals are local-only. Playback uses committed assets.
photos = {
 'reference-window': '微信图片_20260916133315_18_97.jpg',
 'reference-desk': '微信图片_20260916133311_16_97.jpg',
 'reference-bed': '微信图片_20260916133317_19_97.jpg',
 'reference-entry': '微信图片_20260916133308_15_97.jpg',
 'reference-bath': '微信图片_20260916133305_14_97.jpg',
 'reference-bath-new': 'reference-bath-new.jpg',
 'reference-entry-new': 'reference-entry-new.jpg',
 'reference-headboard': 'reference-headboard.jpg',
 'reference-closet-new': '微信图片_20260916141729_29_97.jpg',
 'reference-window-new': '微信图片_20260916141726_27_97.jpg',
}
for name, filename in photos.items():
 im = ImageOps.exif_transpose(Image.open(source/filename))
 im.thumbnail((1400,1400))
 im.save(dest/(name+'.jpg'), quality=86, optimize=True)

def crop_tile(filename, box, name, size=512, brighten=1.0):
 im=ImageOps.exif_transpose(Image.open(source/filename))
 w,h=im.size
 im=im.crop(tuple(int(v*(w if i%2==0 else h)) for i,v in enumerate(box)))
 im=ImageEnhance.Brightness(im).enhance(brighten).resize((size//2,size//2))
 tile=Image.new('RGB',(size,size))
 tile.paste(im,(0,0));tile.paste(ImageOps.mirror(im),(size//2,0))
 tile.paste(ImageOps.flip(im),(0,size//2));tile.paste(ImageOps.flip(ImageOps.mirror(im)),(size//2,size//2))
 tile.save(dest/name,quality=91)

crop_tile(photos['reference-desk'],(.39,.045,.77,.13),'pink-plaster.jpg',512,1.03)
crop_tile(photos['reference-closet-new'],(.58,.78,.64,.92),'wood.jpg',512,1.12)
crop_tile(photos['reference-closet-new'],(.03,.27,.33,.64),'gray-wall.jpg',512,1.10)
crop_tile(photos['reference-bath-new'],(.48,.33,.65,.54),'bath-marble.jpg',512,1.10)
crop_tile(photos['reference-desk'],(.13,.86,.27,.9),'woven-cloth.jpg',512,1.07)
crop_tile(photos['reference-bed'],(.46,.78,.72,.90),'floral-quilt.jpg',1024,1.4)
crop_tile(photos['reference-entry'],(.52,.70,.66,.79),'floor.jpg',512,1.4)
