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
THREAD_COUNT = 20    #how many threads to use
ORIGINAL_SCALE = 0.9 #scale the image down to this size before converting to minecraft items

WHITELIST_BLOCK = ["wool","concrete","stained_glass","terracotta","ore","cobble","log","planks","grass_block_top","sand","obsidian","emerald","diamond","gold","iron","redstone_block","lapis","chiseled_quartz_bloc"]
BLACKLIST_BLOCK= ["stripped","pane_top","_dust","camp","nether_quartz_ore","nether_gold_ore"]
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
                name = file.split('\\')[-1].lower().split('.png')[0]
                if not any(x in name for x in BLACKLIST_BLOCK) and any(x in name for x in WHITELIST_BLOCK):
                    minecraft.append(os.path.join(dir, file))
    ending = {}
    for i in range(len(minecraft)):
        im = Image.open(minecraft[i])
        if im.size[0] != im.size[1]:
            im = im.crop((0, 0, min(im.size), min(im.size)))
        im = im.resize((1, 1))
        color = pixel_to_int(im.getpixel((0, 0)))
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
w_, h_ = im.size
w_, h_ = w_ * SCALE_BY, h_ * SCALE_BY
out_im = Image.new('RGBA', (w_,h_))
stats = {"time":{},"pixel_count":0}
pixeldata = im.getdata()
final_pixel_data = [""]*len(pixeldata)

def convert_pixel_to_nearest(pixel):
    global ending
    nearest = ending[get_nearest_color(pixel_to_int(pixel))][0]
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
    time.sleep(0.1)
#wait for all threads to finish
print(f"[+] Started {THREAD_COUNT} threads")
while threading.active_count() > 1:
    perc = round(stats["pixel_count"]/(im.size[0]*im.size[1])*100,2)
    avg = stats["time"].values()
    for i in range(len(avg_progress)):
        avg_progress[i].config(text=f"Thread {i} tpp: {round(list(avg)[i],4)}s")
    progress.config(text=f"[*] {perc}% active: {threading.active_count()-1}")
    window.update()
    time.sleep(0.1)
#create the final image
for i in range(len(final_pixel_data)):
    try:
        out_im.paste(final_pixel_data[i],(i%im.size[0]*SCALE_BY,i//im.size[0]*SCALE_BY))
    except:
        pass
window.destroy()
print(f"[+] Finished in {round(time.time()-t1,2)}s")
out_im.save('output.png')
im.close()
print(f"[+] Saved output.png")
