from PIL import Image
import os
import random
import json

SCALE_BY = 64
ALPHA = False

def pixel_to_int(p):
    if not isinstance(p, tuple):
        return p
    return sum([p[i] * 256 ** i for i in range(len(p))])
    
def int_to_pixel(i):
    if not ALPHA:
        return (i % 256, (i // 256) % 256, (i // 256 ** 2) % 256)
    alpha_p = (i // 256 ** 3) % 256
    return (i % 256, (i // 256) % 256, (i // 256 ** 2) % 256, alpha_p)

def get_distance_between_pixels(p1, p2):
    #get the distance between two pixels
    return sum([abs(p1[i] - p2[i]) for i in range(len(p1))])

def get_nearest_color(pixel_a):
    global ending
    temp = {}
    for i in ending:
        temp[get_distance_between_pixels(int_to_pixel(pixel_a),int_to_pixel(int(i)))] = i
    #find the minimum key and return the value
    return temp[min(temp.keys())]
        

#load the minecraft item colors
try:
    ending = json.load(open('minecraft_item_color.json', 'r'))
except:
    minecraft = []
    for dir, subdir, files in os.walk('minecraft'):
        for file in files:
            if file.endswith('.png') and not file in minecraft:
                minecraft.append(os.path.join(dir, file))
    ending = {}
    for i in range(len(minecraft)):
        im = Image.open(minecraft[i])
        im = im.resize((1, 1))
        color = pixel_to_int(im.getpixel((0, 0)))
        if not color in ending:
            ending[color] = []
        ending[color].append(minecraft[i])
    json.dump(ending, open('minecraft_item_color.json', 'w'))

#ask for an image, and then find the closest minecraft item for each pixel
im = Image.open(input('Image: '))
w_, h_ = im.size
w_, h_ = w_ * SCALE_BY, h_ * SCALE_BY
out_im = Image.new('RGBA', (w_,h_))
for x in range(im.size[0]):
    for y in range(im.size[1]):
        pixelint = pixel_to_int(im.getpixel((x, y)))
        closest = random.choice(ending[get_nearest_color(pixelint)])
        out_im.paste(Image.open(closest).resize((SCALE_BY, SCALE_BY)), (x*SCALE_BY, y*SCALE_BY))
out_im.save('output.png')
im.close()
