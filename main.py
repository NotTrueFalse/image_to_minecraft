#tpp = time per pixel
#this script will convert an image to minecraft items
#it will find the nearest minecraft item for each pixel
#it will then create a new image with the minecraft items
#it will also create a json file with the minecraft item colors
#this script will use multithreading to speed up the process
from PIL import Image
import os
import json
import time
import threading
import tkinter as tk

SCALE_BY = 32        #scale the image up by this much
ALPHA = True         #use alpha channel
THREAD_COUNT = 10    #how many threads to use
ORIGINAL_SCALE = 0.9 #scale the image down to this size before converting to minecraft items
NO_SLEEP = False

WHITELIST_BLOCK = ["wool","concrete","stained_glass","terracotta","ore","cobble","log","planks","grass_block_top","sand","coal_block","obsidian","emerald","diamond","gold","iron","redstone_block","lapis","chiseled_quartz_bloc","cauldron","bedrock","beacon","trapdoor"]
BLACKLIST_BLOCK= ["stripped","pane_top","_dust","camp","nether_quartz_ore","nether_gold_ore"]
def pixel_to_hex(pixel:tuple):
    if not ALPHA:return '%02x%02x%02x' % pixel
    else:return '%02x%02x%02x%02x' % pixel
    
def hex_to_pixel(hex:str):
    lst = (0, 2, 4, 6) if ALPHA else (0, 2, 4)
    return tuple(int(hex[i:i+2], 16) for i in lst)

def sqrt(x):
    return x**(1/2)

def get_distance_between_pixels(p1, pxs:list):
    #get the distance between two pixels
    diffs = []
    for icolor in pxs:
        if not ALPHA:
            cr,cg,cb = hex_to_pixel(icolor)
            diff = sqrt((cr-p1[0])**2+(cg-p1[1])**2+(cb-p1[2])**2)
        else:
            cr,cg,cb,ca = hex_to_pixel(icolor)
            diff = sqrt((cr-p1[0])**2+(cg-p1[1])**2+(cb-p1[2])**2+(ca-p1[3])**2)
        diffs.append((diff,icolor))
    return min(diffs)[1]


def get_nearest_color(pixel:tuple):
    global ending
    px = hex_to_pixel(pixel_to_hex(pixel))#double conversion to avoid errors
    return get_distance_between_pixels(px,list(ending.keys()))


#load the minecraft item colors
try:
    ending = json.load(open('minecraft_item_color.json', 'r'))
except:
    minecraft = []
    for dir, subdir, files in os.walk('minecraft'):
        for file in files:
            if file.endswith('.png') and not file in minecraft:
                name = file.split('\\')[-1].lower().split('.png')[0]
                if not any(x in name for x in BLACKLIST_BLOCK) and any(x in name for x in WHITELIST_BLOCK):
                    minecraft.append(os.path.join(dir, file))
    ending = {}
    for i in range(len(minecraft)):
        im = Image.open(minecraft[i])
        if im.size[0] != im.size[1]:
            im = im.crop((0, 0, min(im.size), min(im.size)))
        im = im.resize((1, 1))
        im = im.convert('RGBA'if ALPHA else 'RGB')
        im = im.getdata()[0]
        color = pixel_to_hex(im)
        if not color in ending:
            ending[color] = []
        ending[color].append(minecraft[i])
    json.dump(ending, open('minecraft_item_color.json', 'w'))
print(f"[+] loaded {len(ending)} minecraft blocs")
#ask for an image, and then find the closest minecraft item for each pixel
try:
    im = Image.open(input('Image: '))
except:
    print('Invalid image')
    exit()
im = im.resize((int(im.size[0]*ORIGINAL_SCALE),int(im.size[1]*ORIGINAL_SCALE)))
im = im.convert('RGBA'if ALPHA else 'RGB')
w_, h_ = im.size
w_, h_ = w_ * SCALE_BY, h_ * SCALE_BY
out_im = Image.new('RGBA', (w_,h_))
stats = {"time":{},"pixel_count":0}
pixeldata = im.getdata()
final_pixel_data = [""]*len(pixeldata)

def convert_pixel_to_nearest(pixel):
    global ending
    nearest = ending[get_nearest_color(pixel)][0]
    nearest = Image.open(nearest)
    nearest = nearest.resize((SCALE_BY,SCALE_BY))
    return nearest

def threader(data_sample:list,thread_id:int,glob_start:int):
    global stats
    global im
    if not thread_id in stats["time"]:
        stats["time"][thread_id] = 0
    #loop through each pixel in the image and find the nearest img then add it to final_pixel_data[start+i]
    for i in range(len(data_sample)):
        start = time.time()
        final_pixel_data[glob_start+i] = convert_pixel_to_nearest(data_sample[i])
        stats["time"][thread_id] = time.time()-start
        stats["pixel_count"] += 1
        if i == len(data_sample)-1:
            print(f"[+] Thread {thread_id} finished")

window = tk.Tk()
window.title("Progress")
window.geometry("300x400")
progress = tk.Label(window,text="Progress will be shown here")
progress.pack()
avg_progress = [tk.Label(window,text=f"Thread {i} avg time per pixel: 0s") for i in range(THREAD_COUNT)]
#create the number of threads
t1 = time.time()
for i in range(THREAD_COUNT):
    start,end = i*int(len(pixeldata)/THREAD_COUNT),(i+1)*int(len(pixeldata)/THREAD_COUNT)
    sample_data = list(pixeldata)[start:end]
    t = threading.Thread(target=threader, args=(sample_data,i,start))
    avg_progress[i].pack()
    t.daemon = True
    t.start()
    if not NO_SLEEP:time.sleep(0.1)
#wait for all threads to finish
print(f"[+] Started {THREAD_COUNT} threads")
while threading.active_count() > 1:
    perc = round(stats["pixel_count"]/(im.size[0]*im.size[1])*100,2)
    avg = stats["time"].values()
    for i in range(len(avg_progress)):
        avg_progress[i].config(text=f"Thread {i} tpp: {round(list(avg)[i],4)}s")
    progress.config(text=f"[*] {perc}% active: {threading.active_count()-1}")
    window.update()
    if not NO_SLEEP:time.sleep(0.1)
#create the final image
for i in range(len(final_pixel_data)):
    try:
        out_im.paste(final_pixel_data[i],(i%im.size[0]*SCALE_BY,i//im.size[0]*SCALE_BY))
    except:
        pass
window.destroy()
print(f"[+] Finished in {round(time.time()-t1,2)}s")
out_im.save('output.png')
out_im.show()
im.close()
print(f"[+] Saved output.png")
