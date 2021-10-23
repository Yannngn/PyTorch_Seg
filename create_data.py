import os
import numpy as np
import random
from PIL import Image
from shutil import copyfile, rmtree

PATH = "C:/Users/Yann/Documents/GitHub/LesionInserter-data/"
OUT = "data/"

# IMG_PATH = OUT + "submission/input/phantom/"
# MSK_PATH = OUT + "submission/input/mask/"

IMG_PATH = OUT + "phantom/"
MSK_PATH = OUT + "mask/"
TRAIN = OUT + "train/"
VAL = OUT + "val/"

FILES = ["null_9_0000_00_00",
         "sphere_0_4285_50_02",
         "spiculated_1_4285_50_02",
         "spiculated_2_4285_50_02"]

FILES = ['calc_4_5000_30_42']

def main(path = PATH, files = FILES, img_path = IMG_PATH, mask_path = MSK_PATH, get_slice = False, crop = False, delete = False, shuffle = False):
    if delete:
        clear_data(img_path)
        clear_data(mask_path)
        clear_data(TRAIN)
        clear_data(VAL)
    
    for file in files:
        if get_slice:
            get_slices(path + file + '/', file, img_path, mask_path)
            
        if crop:
            cropper(img_path, mask_path)

    if shuffle:
        shuffle_train_val(OUT, TRAIN, VAL)
                                
def get_slices(path, name, img_path = IMG_PATH, mask_path = MSK_PATH):
    a, j, r, s = 0, 0, 0, 0
    for _, dirs, _ in os.walk(path):
        for folder in dirs:
            if folder[-4:] == "crop":
                family = folder.split('_')[0]

                if family == 'Alvarado':
                    image = f'_{a:03}'
                    a += 1
                elif family == 'Jhones':
                    image = f'_{j:03}'
                    j += 1
                elif family == 'Richards':
                    image = f'_{r:03}'
                    r += 1
                elif family == 'Stark':
                    image = f'_{s:03}'
                    s += 1
                else:
                    raise ValueError('error, unknown family', family)
                
                copyfile(path + folder + "/_recon_slice_317.tiff", img_path + '_'.join(name.split('_')[:2]) + "_" + family + "_" + '_'.join(name.split('_')[2:]) + image + "-crop.tiff")

                copyfile(path + folder[:-5] + "_mask/_317.png", mask_path + '_'.join(name.split('_')[:2]) + "_" + family + "_" + '_'.join(name.split('_')[2:]) + image + "_mask.png")
      
def cropper(img, masks):
    phant = Image.open(img + os.listdir(img)[0])
    img_height = phant.size[1]

    for _, _, files in os.walk(masks):
        for file in files:
            if file[-4:] == ".png":
                mask = Image.open(masks + file)
                w, h = mask.size
                mask.crop((0, h - img_height, w, h)).save(masks + file)

def clear_data(path):
    if os.path.isdir(path):
        try:
            rmtree(path)
        except OSError as e:
            raise ValueError("Error: %s : %s" % (path, e.strerror))
        
        os.makedirs(path)

    elif os.path.isdir(path) is False:
        try:
            os.makedirs(path)
        except OSError as e:
            raise ValueError("Error: %s : %s" % (path, e.strerror))
                               
def shuffle_train_val(path, train_dir, val_dir):
    phantom_orig = path + 'phantom/'
    mask_orig = path + 'mask/'
    phantom_train = train_dir + 'phantom/'
    mask_train = train_dir + 'mask/'
    phantom_val = val_dir + 'phantom/'
    mask_val = val_dir + 'mask/'

    os.makedirs(phantom_train)
    os.makedirs(mask_train)
    os.makedirs(phantom_val)
    os.makedirs(mask_val)

    img_files = [os.path.join(path, file) for file in os.listdir(phantom_orig) if file.endswith('.tiff')]
    img_names = [filepath_to_name(img) for img in img_files]
    
    lesions = np.unique(['_'.join(name.split('_')[:2]) for name in img_names])
    
    names_per_lesion = []
    
    for lesion in lesions:
        names = [img for img in img_names if '_'.join(img.split('_')[:2]) == lesion]
        names_per_lesion.append(names)

    val_names = set(random.choices(names_per_lesion[0], k=5)+
                    random.choices(names_per_lesion[1], k=2)+
                    random.choices(names_per_lesion[2], k=2)+
                    random.choices(names_per_lesion[3], k=2))

    train_names = set(img_names) - val_names
   
    for file in val_names:
        copyfile(phantom_orig + file + '.tiff', phantom_val + file + '.tiff')
        copyfile(mask_orig + file[:-5] + '_mask.png', mask_val + file[:-5] + '_mask.png')

    for file in train_names:
        copyfile(phantom_orig + file + '.tiff', phantom_train + file + '.tiff')
        copyfile(mask_orig + file[:-5] + '_mask.png', mask_train + file[:-5] + '_mask.png')

def filepath_to_name(full_name):
    file_name = os.path.basename(full_name)
    file_name = os.path.splitext(file_name)[0]
    return file_name

if __name__ == "__main__":
    main(get_slice = True, crop = True, delete = True, shuffle = True)
    # main(get_slice = True, crop = True)