"""
Description:

This program takes the OCR data generated by the AWS textract, and also the 
already annotated data (in YOLO format). 

Primary goal here is to clean out wrong key-value pairs from textract OCR data, 
and also including the key-value paris that the textract failed to detect. 

Finally, the output is generated in FUNSD-like format and resultant data 
is dumped in this path -> preprocess/custom/custom_data/data_in_funsd_format 
"""

from copy import copy
import os
import json
from functools import cmp_to_key
from tqdm import tqdm
from PIL import Image, ImageDraw
import shutil
from typing import List, Dict
def denormalize(h, w, bbox, denom=2):
    """
    Get entire label coordinate region
    
    Parameters
    ----------
    h: int
       heigth of the image
    w: int
       width of the image
    bbox: list
        word coordinates obtained from ocr
    denom: int
        Denominator for denormalize operation

    Returns:
    x0, y0, x1, y1: tuple
        tuple of denormalized word coordinates
    """

    x_center = float(bbox[0]) * w
    y_center = float(bbox[1]) * h
    width = float(bbox[2]) * w
    height = int(float(bbox[3]) * h)
    x0 = int(x_center - (width / denom))
    x1 = int(x_center + (width / denom))
    y0 = int(y_center - (height / denom))
    y1 = int(y_center + (height / denom))

    return x0, y0, x1, y1

def calculate_iou(bbox1, bbox2):
    """
    Finds the percentage of intersection  with a smaller box. (what percernt of smaller box is in larger box)
    """
    # assert bbox1['x1'] < bbox1['x2']
    # assert bbox1['y1'] < bbox1['y2']
    # assert bbox2['x1'] < bbox2['x2']
    # assert bbox2['y1'] < bbox2['y2']

    # determine the coordinates of the intersection rectangle
    x_left = max(bbox1[0], bbox2[0])
    y_top = max(bbox1[1], bbox2[1])
    x_right = min(bbox1[2], bbox2[2])
    y_bottom = min(bbox1[3], bbox2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # The intersection of two axis-aligned bounding boxes is always an
    # axis-aligned bounding box
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # compute the area of both AABBs
    bbox1_area = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    bbox2_area = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    # min_area = min(bbox1_area,bbox2_area)
    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    intersection_percent = intersection_area / bbox2_area

    return intersection_percent

def contour_sort(a, b):
	if abs(a['y1'] - b['y1']) <= 15:
		return a['x1'] - b['x1']

	return a['y1'] - b['y1']

def get_area(bbox):
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])


def get_other_text(words):
    """
    1. Track the already covered words here
    2. Difference of all words and Covered words = Others 
    """
    pass


def findOtherCategory(word_box: List, key_box:List, value_box: List):
    print(f'word box: {word_box}')
    print(f'key box: {key_box}')
    print(f'value box: {value_box}')
    # exit('++++++++++++++++')
    overlapping_value=True
    for i in range(len(key_box)):
        iou1 = calculate_iou(key_box[i], word_box)
        if iou1>0.4:
            overlapping_value=False
    for i in range(len(value_box)):
        iou2 = calculate_iou(value_box[i], word_box)
        if  iou2> 0.4:
            overlapping_value= False
    return overlapping_value


def dataSegmentation():
    pass

def get_text(ocr_region, labelled_region, words_coords=None, words=None, all_words=None):
    if get_area(labelled_region) > get_area(ocr_region):
        print(f'area of labelled region: {get_area(labelled_region)}')
        print(f'area of ocr region : {get_area(ocr_region)}')
        # exit('+++++++++++')
        coords = []
        for idx, item in all_words.items():
            #if abs(item['bbox'][0] - labelled_region[0]) < 250:
                iou = calculate_iou(item['bbox'], labelled_region)
                if iou > 0.0:
                    coords.append({'bbox' : item['bbox'],
                                   'word': item['text']})
        # coords = sorted(coords, key=cmp_to_key(contour_sort))  
        # print(f"coords: {coords}")
        # exit('+++++++++++++++++')
        words = [item['word'] for item in coords]
        cords = [item['bbox'] for item in coords]
        assert len(words) == len(cords)
        return words, cords
    else:
        assert len(words_coords) == len(words)
        print('Else condition ++++++++++++++++++')
        print(f'area of labelled region: {get_area(labelled_region)}')
        print(f'area of ocr region : {get_area(ocr_region)}')
        res = []
        coords = []
        print(f'word corred: {words_coords}')
        print(f'words : {words}')
        # exit('+++++++++++++')
        for i in range(len(words_coords)):
            iou = calculate_iou(labelled_region, words_coords[i])
            #print(iou)
            if iou > 0.4:
                res.append(words[i])
                coords.append(words_coords[i])
        return res, coords


root_path = "/home/ntlpt-42/Documents/mani_projects/IDP/IDE/Geolayoutlm/CS_complete_data/new_data_prep"

ocr_path = os.path.join(root_path, "custom_data/key_val_sets")
all_words_path = os.path.join(root_path, "custom_data/all_words")

save_to = os.path.join(root_path, "data_in_funsd_format")
os.makedirs(os.path.join(save_to, 'images'), exist_ok=True)
os.makedirs(os.path.join(save_to, 'annotations'), exist_ok=True)

labels_path = os.path.join(root_path, 'Labels')
images_path = os.path.join(root_path, 'Images')

classes_path = os.path.join(root_path, "label.txt")
with open(classes_path, 'r') as f:
    classes = f.readlines()

classes = [item.replace('\n','').strip() for item in classes]

images_list = os.listdir(images_path)
labels_list = os.listdir(labels_path)

labels_list = [item for item in labels_list if item.replace('txt', 'png') in images_list]


for labels in tqdm(labels_list, desc="Preparing"):
    print(f'file name: {labels}')
    with open(os.path.join(labels_path, labels), 'r') as f:
        label_data  = f.readlines()
        for label in label_data:
            print(label.split(' ')[0])
            # exit('++++++++++++++')
            if int(label.split(' ')[0])==36:
                # print(label)
                # exit('+++++++++++++=')
                label_data.remove(label)
        print(label_data)
        # exit('+++++++++++++++')
    ocr_name = labels.replace('txt','json')
    with open(os.path.join(ocr_path, ocr_name) , 'r') as f:
        ocr_labels = json.load(f)
        # print(f'ocr labels: {ocr_labels}')
        # exit('+++++++++++++++++++++++=')
    with open(os.path.join(all_words_path, ocr_name), 'r')   as f:
        all_words = json.load(f)

    classes_enum = [int(item.split()[0]) for item in label_data]
    # value_to_remove = 36                       # remove document settlement instruction
    # classes_enum.remove(value_to_remove)
    print(classes_enum)
    print(max(classes_enum))
    print(len(classes))
    # exit('++++++++++++++')

    if max(classes_enum) > len(classes):
        continue

    
    
    label_data = [item.split()[1:] for item in label_data]
    print(label_data)
    # exit('+++++++++++++')
    label_data = [[float(item) for item in line ] for line in label_data]
    # print('++++++++++++++++++++++=====')
    print(label_data)
    # exit('+++++++++++')

    image_name = labels.replace('txt','png')
    image_loc = os.path.join(images_path, image_name)

    shutil.copy(image_loc, os.path.join(save_to,'images',image_name))

    image_org=Image.open(image_loc)
    image = Image.new('RGBA', image_org.size)
    image.paste(image_org)
    w, h = image_org.size

    denormalized_coords = [denormalize(h, w, coord) for coord in label_data]
    print(denormalized_coords)
    # exit('+++++++++++++=')

    draw=ImageDraw.Draw(image)

    
    #exit(s)
    for enum, coord in enumerate(denormalized_coords):
        draw.rectangle([coord[0], coord[1], coord[2], coord[3]], width=3 ,outline='blue') #, fill=(0, 0, 255, 125))
        draw.text((coord[0]+10, coord[1]-10), text=classes[classes_enum[enum]], fill='blue')
        
        
    #exit()
    ocr_labels_temp = copy(ocr_labels)
    labels_data_temp = copy(denormalized_coords)

    keep_coords = []

    id_counter = 0  


    value_cntr = 1000
    key_cntr = 0
    other_contr= len(ocr_labels)

    value_dict = {}
    key_dict = {}

    covered_keys = []
    val_box=[]
    key_box=[]

    print(f'ocr labels: {ocr_labels}')
    print(len(ocr_labels))
    # exit('+++++++++++++++=')

    for i, ocr_coord in enumerate(ocr_labels):
        val_bbox = [int(item) for item in ocr_coord['value_bbox']]
        key_bbox=  [int(item) for item in ocr_coord['key_bbox']]
        key_box.append(key_bbox)
        for j, label_coords in enumerate(labels_data_temp):
            if not len(val_bbox) == len(label_coords) == 0:
                # print(val_bbox, label_coords)
                # val_box.append(label_coords)
                iou = calculate_iou(val_bbox, label_coords)
                # print(iou, end='\n\n')
                if iou > 0:
                    overlapped_text, overlapped_coords = get_text(ocr_coord['value_bbox'],
                                               label_coords, 
                                               ocr_coord['value_text_bbox'], 
                                               ocr_coord['value_text'],
                                               all_words)
                
                    
                    # ocr_coord['key_text'] = [_ for item in ocr_coord['key_text'] if item in overlapped_text]
                    # if ocr_coord['key_text'] == []: 
                    #     key_text = None
                    # else: key_text = ocr_coord


                    """
                    # List to store all metadata
                    
                    keep_coords.append({
                        'id' : id_counter,
                        'key_bbox': ocr_coord['key_bbox'],
                        'key_text': ocr_coord['key_text'],
                        'key_text_bbox' : ocr_coord['key_text_bbox'],
                        'actual_key': classes[classes_enum[j]],
                        'actual_key_id': classes_enum[j],
                        'value_bbox': list(label_coords),
                        'value_text': overlapped_text,
                        'value_text_bbox': ocr_coord['value_text_bbox']
                    })

                    id_counter += 1
                    """
                    print(f'words : {overlapped_text}')
                    print(f'Coords: {overlapped_coords}')
                    print(ocr_coord['key_text'][0])
                    # exit('+++++++++++++++++')
                    key_text = ''
                    #for kt in ocr_coord['key_text']:
                        #print(kt, ' :::: ', overlapped_text)
                    if ocr_coord['key_text'][0] in overlapped_text:
                        key_text = None
                        break

                    if key_text != None:
                        if key_cntr != 0 and (' '.join(ocr_coord['key_text']) == key_dict[key_cntr - 1]['text']):
                            
                            key_dict[key_cntr - 1]['linking'].append([ key_cntr-1,value_cntr])
                            key_cntr -= 1
                        else:
                            key_dict.update({key_cntr : { 
                                    'id' : key_cntr ,
                                    'box': ocr_coord['key_bbox'],
                                    'label': 'other',
                                    'text': ' '.join(ocr_coord['key_text']),
                                    'words' : [{'text': ocr_coord['key_text'][i], 
                                                'box':ocr_coord['key_text_bbox'][i] }
                                                for i in range(len(ocr_coord['key_text']))],
                                    'linking': [[key_cntr, value_cntr]]}})
                            # key_box.append(ocr_coord['key_bbox'])
                        
                            
                    #if overlapped_text != []:
                    value_dict.update(
                        {
                            value_cntr : {
                                'id' : value_cntr,
                                'box': list(label_coords),
                                'label': classes[classes_enum[j]],
                                'text': ' '.join(overlapped_text),
                                'words' : [{'text': overlapped_text[i], 
                                            'box':overlapped_coords[i] }
                                            for i in range(len(overlapped_text))],
                                'linking': [[key_cntr, value_cntr]]
                        }}
                    )
                    covered_keys.append(classes_enum[j])

                    # print(value_dict[value_cntr], end='\n\n')

                    key_cntr += 1
                    value_cntr += 1
                        #key_cntr += 1
                    
        
        draw.rectangle([int(ocr_coord['key_bbox'][0]), 
                        int(ocr_coord['key_bbox'][1]), 
                        int(ocr_coord['key_bbox'][2]), 
                        int(ocr_coord['key_bbox'][3])], 
                        width=3,
                        outline='red')
        draw.rectangle([int(ocr_coord['value_bbox'][0]), 
                        int(ocr_coord['value_bbox'][1]), 
                        int(ocr_coord['value_bbox'][2]), 
                        int(ocr_coord['value_bbox'][3])], 
                        width=3,
                        outline='green')
    all_actual_keys = [item for item in classes_enum]
    #all_ocr_keys = [item['actual_key_id'] for item in keep_coords]
    print(f'acutal keys: {all_actual_keys}')
    print(f'covered keys: {covered_keys}')

    # exit('+++++++++++++')
    missed_keys = list(set(all_actual_keys) - set(covered_keys))
    print(f'missed keys: {missed_keys}')
    # exit('+++++++++++=')
    if missed_keys != []:
        for i, key in enumerate(missed_keys):
            missed_key_idx = [classes_enum.index(item) for item in missed_keys]
            #print(missed_key_idx)
            value_bbox = [int(item) for item in denormalized_coords[missed_key_idx[i]]]
            value_text, value_coords =  get_text(ocr_region= [0, 0, 0, 0],
                                    labelled_region= value_bbox, 
                                    all_words= all_words)
              
            value_dict.update(
                        {
                            value_cntr : {
                                'id' : value_cntr,
                                'box': value_bbox,
                                'label': classes[key],
                                'text': ' '.join(value_text),
                                'words' : [{'text': value_text[i], 
                                            'box':value_coords[i] }
                                            for i in range(len(value_text))],
                                'linking': []
                        }}
                    )
            value_cntr += 1
             
            """
            keep_coords.append({
                    'id' : id_counter,
                   'key_bbox' : None,
                    'key_text' : None,
                    'key_text_bbox': None,
                    'actual_key': classes[key],
                    'actual_key_id': key,
                    'value_bbox': value_bbox,
                    'value_text':value_text,
                    'value_text_bbox': value_coords
              })
            
            id_counter += 1
            """
    print(f'key box: {key_box}')
    print(len(key_box))
    val_box= [list(box) for box in labels_data_temp]
    print(f'value box: {val_box}')
    print(f'no. of keys: {len(val_box)}')
    # exit('++++++++++++++++=')

    for i, ocr_coord in enumerate(all_words):
            print(ocr_coord)
            print(all_words[ocr_coord])
            text = all_words[ocr_coord]['text']
            bbox = all_words[ocr_coord]['bbox']
            if (findOtherCategory(word_box=bbox, key_box=key_box, value_box= val_box)):
                print(f'text: {text}, box: {bbox}')
                key_dict.update({other_contr : { 
                                        'id' : other_contr,
                                        'box': all_words[ocr_coord]['bbox'],
                                        'label': 'other',
                                        'text': text,
                                        'words' : [{'text': all_words[ocr_coord]['text'],
                                                    'box':all_words[ocr_coord]['bbox']}],
                                        'linking': []
                                        }})
                other_contr+=1

    #final_data = copy(key_dict)
    key_dict.update(value_dict)
    
    final_data = [key_dict[item] for item in key_dict]
    # for item in final_data:
    #     print(item, end="\n\n")
    # break

    with open(os.path.join(save_to,'annotations' ,ocr_name), 'w') as f:
        json.dump({"form" : final_data}, f, indent=4)

