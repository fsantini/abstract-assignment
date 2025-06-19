import os
from unidecode import unidecode

IMAGE_FOLDER = '/media/bigboy2/ESMRMB2025/image/'

for filename in os.listdir(IMAGE_FOLDER):
    src = os.path.join(IMAGE_FOLDER, filename)
    if os.path.isfile(src):
        new_filename = unidecode(filename)
        dst = os.path.join(IMAGE_FOLDER, new_filename)
        if src != dst:
            os.rename(src, dst)
            print(f'Renamed: {filename} -> {new_filename}')