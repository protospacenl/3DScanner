from pathlib import Path
import sys

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print("Usage: {0} imagesPath".format(sys.argv[0]))
		sys.exit(1)
		
	imagesPath = Path(sys.argv[1])

	for d in sorted(imagesPath.glob('**/')):
		if d.stem.lower() == 'recap':
			print("Skipping recap path: {0}".format(d))
			continue

		for f in sorted(d.glob('*.jpg')):
			try:
				fname = f.stem
				parts = fname.split('_')
				ip = parts[2].split('.')

				camera = int(ip[-1]) - 100

				print("{0} - {1} - {2} - {3}".format(fname, parts, ip[-1], camera))
				
				bracketPath = d / "br{0}".format(parts[0])
				bracketFile = bracketPath / "{0}.jpg".format(camera)
				
				print("moving {0} -> {1}".format(f, bracketFile))

				bracketPath.mkdir(exist_ok=True)
				f.replace(bracketFile)
			except:
				pass