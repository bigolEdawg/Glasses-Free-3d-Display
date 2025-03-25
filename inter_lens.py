import numpy as np
import cv2
import matplotlib.pyplot as plt
import random

# Define interlacing options.
lenticular = {
    'width': 2.54,          # width of each lens (mm)
    'offset': 0.5           # offset (number of lenses from left-hand side of screen)
}

# Define screen parameters.
screen = {
    'dpi': 25.4 / 0.258,    # screen resolution (pixels per inch)
    'res': [1050, 1680]     # screen dimensions [height, width] (pixels)
}

# Define light field.
lf = {
    'name': 'numbers',                      # light field
    'generalDir': './images/spheres/',      # base directory (only for 'general' case)
    'generalBase': 'spheres',                # base file name (only for 'general' case)
    'generalCount': '%0.2d',                 # counter format (only for 'general' case)
    'generalExt': 'png'                      # file format (only for 'general' case)
}

# Define input interlacing options.
pattern = {
    'upsample': 10                           # upsampling factor for interlaced pattern
}

# Display status
print('[lenticular sheet interlacer]')
print('> Evaluating resampling parameters...')


# Evaluate physical position of the center of each screen pixel.
screen['dpmm'] = (1 / 25.4) * screen['dpi']
screen['dim'] = (1 / screen['dpmm']) * np.array(screen['res'])
screen['x'] = (1 / (pattern['upsample'] * screen['dpmm'])) * \
              (np.arange(pattern['upsample'] * screen['res'][1]) + 0.5)

# Evaluate physical position of the center of each lens.
lenticular['x'] = lenticular['width'] * (np.arange(int(np.floor(screen['dim'][1] / lenticular['width']))) + 0.5) + \
                  lenticular['offset']

# Determine light field resolution.
lf['nSpatial'] = [screen['res'][0], int(np.floor(screen['dim'][1] / lenticular['width']))]
lf['nAngular'] = [1, int(np.round(screen['dpmm'] * lenticular['width']))]

# Determine light field sampling indices.
screen['u'] = np.floor((screen['x'] - lenticular['width'] * lenticular['offset']) / lenticular['width']) + 1
screen['s'] = -(lf['nAngular'][1] / lenticular['width']) * \
              ((screen['x'] - lenticular['width'] * lenticular['offset']) - (lenticular['width'] * screen['u']) +
               (lenticular['width'] / 2))
screen['s'] = screen['s'] + (lf['nAngular'][1] + 1) / 2

# Load the light field.
lf['image'] = []
print('> Loading the light field...')
for i in range(lf['nAngular'][1]):
    print(f'  - Loading frame {i + 1} of {lf["nAngular"][1]}...')
    if lf['name'] == 'calibration':
        img = 255 * (i == int((lf['nAngular'][1] + 1) / 2)) * np.ones((lf['nSpatial'][0], lf['nSpatial'][1], 3))
    elif lf['name'] == 'numbers':
        img = np.zeros((lf['nSpatial'][0], lf['nSpatial'][1], 3), dtype=np.uint8)
        for j in range(3):
            img[:, :, j] = (i + 1) * (j + 1) * (j + 1)
     #  case 'numbers'
     # lf.image{i} = imread(['./images/numbers/',int2str(i),'.jpg']);
     # %color = round(rand(1,3));
     # color = [1 1 1];
     # if all(color==0)
     #    color(ceil(3*rand)) = 1;
     # end
     # for j = 1:3
     #    lf.image{i}(:,:,j) = color(j)*lf.image{i}(:,:,j);
     # end

    elif lf['name'] == 'flip':
        filename = './images/flip/'
        img = cv2.imread(filename)

    elif lf['name'] == 'general':
        filename = lf['generalDir'] + lf['generalBase'] + (lf['generalCount'] % (i + 1)) + '.' + lf['generalExt']
        img = cv2.imread(filename)
    lf['image'].append(img)
    



# Evaluate and save the interlaced pattern.
print('> Calculating the interlaced pattern...')
pattern['image'] = np.zeros((screen['res'][0], pattern['upsample'] * screen['res'][1], 3), dtype=np.uint8)
for i in range(len(lf['image'])):
    valid_idx = np.where((screen['u'] >= 1) & (screen['u'] <= lf['nSpatial'][1]) & (np.round(screen['s']) == i))
    pattern['image'][:, valid_idx[0], :] = lf['image'][i][:, screen['u'][valid_idx[0]].astype(int) - 1, :]

if pattern['upsample'] > 1:
    I = np.zeros((screen['res'][0], screen['res'][1], 3), dtype=np.float32)
    for i in range(pattern['upsample']):
        I += pattern['image'][:, i::pattern['upsample'], :]
    pattern['image'] = (I / pattern['upsample']).astype(np.uint8)

pattern['filename'] = f'./patterns/{lf["generalBase"]}.png' if lf['name'] == 'general' \
    else f'./patterns/{lf["name"]}.png'
cv2.imwrite(pattern['filename'], pattern['image'])

# Display interlaced pattern.
plt.figure(1)
plt.imshow(pattern['image'])
plt.axis('image')
plt.title('Interlaced Pattern')

# Display the light field.
plt.figure(2)
lfmosaic = np.concatenate(lf['image'], axis=1)
plt.imshow(lfmosaic)
plt.gca().set_aspect('auto')
plt.axis('tight')
plt.gca().set_position([0, 0, 1, 1])
plt.title('Light Field')
plt.show()
