import numpy as np
import glob
import os
import read_lund_json as lund
#######################
dir_in = '/data1/hammad/OT/prepare_files/output_pythia/' # to bechanged for different processes
dir_out = './images/'
os.makedirs(dir_out, exist_ok=True)
files  = glob.glob(dir_in+'/*')
q = 0 
xval = [0,7]
yval = [-3,7]
Images=[]
for file in files:
    q +=1
    print(f'Processing Image:  {q+1}')
    os.system('./example < %s'%(file))
    if os.path.getsize('jets.json')==0:continue
    reader = lund.Reader('jets.json',100)
    reader.reset()
    img_generator = lund.LundImage(reader,1,50,xval,yval)
    images = img_generator.values()
    Images.append(np.array(images))
    os.remove('jets.json')
    
np.savez_compressed(dir_out+'Images_pythia_qcd',Images)    # to bechanged for different processes
