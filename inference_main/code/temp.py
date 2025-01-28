
import os
import shutil
from fuzzywuzzy import fuzz

def get_eval_kwargs_geolayoutlm_vie(geo_clsses_path):
    print(geo_clsses_path)
    class_names = get_class_names(geo_clsses_path)
    bio_class_names = ["O"]
    for class_name in class_names:
        if not class_name.startswith('O'):
            bio_class_names.extend([f"B-{class_name}", f"I-{class_name}"])
    eval_kwargs = {
        "bio_class_names": bio_class_names,
    }
    return eval_kwargs

def get_class_names(dataset_root_path):
    class_names_file = os.path.join(dataset_root_path)#, "class_names.txt")
    class_names = (
        open(class_names_file, "r", encoding="utf-8").read().strip().split("\n")
    )
    print(class_names)
    return class_names

ot = get_eval_kwargs_geolayoutlm_vie('class_names_temp.txt')
print(ot)
exit('OK')



from fuzzywuzzy import fuzz

str1 = "a b a c"
str2 = "a b c"

similarity_score = fuzz.token_sort_ratio(str1, str2)
print(similarity_score)  # This should also output a high score, typically 100, as it treats them as the same ordered set.




import torch
import torch.nn.functional as F

# Example logits for classification
logits = torch.tensor([[1.0, 2.0, 3.0], [1.5, 2.5, 3.5]])

# Apply softmax along the last dimension (-1)
probs = F.softmax(logits, dim=-1)

print("Logits:", logits)
print("Probabilities:", probs)

# output a high score (e.g., 100), indicating a strong match.
exit('OK')



def clean_text(text):
    # Remove leading and trailing '/', '-', or ':'
    token_to_strip = "/-:._'^"
    return text.strip(token_to_strip)

value1 = 'V NDIA ENGINEERING ANDCONSTRUCTION PVT LTD wr 11 .I000-'
value1 = 'to , grasim industries ltd binaga , karwar 581307 . -/'
value2 = 'v ndia engineering andconstruction pvt ltd'
value2 = 'To, GRASIM INDUSTRIES LTD BINAGA, KARWAR - 581307.'
value1 = value1.replace(" ", "")
value2 = value2.replace(" ", "")
# if field_name in ['purchase_order_number', 'pan_number', 'vendor_name']:
value1 = clean_text(value1)
value2 = clean_text(value2)
print('value1', value1)
print('value2', value2)
print(fuzz.ratio(value1, value2))
print(fuzz.ratio(value2.lower(), value1.lower()))
print(fuzz.ratio(value1.lower(), value2.lower()))
exit('OK')


    