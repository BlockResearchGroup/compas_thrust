from compas.geometry import Point
import compas_rhino
import json

# Modify Parameters
title = 'sangelo_vault_top_final'
layers = ['Top_Vault::Extrapts', 'Top_Vault::Intrapts', 'Top_Vault::Fillpts']

# Create dictionary and save as .json
points_UB = []
points_LB = []
UBLB = ['UB', 'LB', 'FILL']
# data = {UBLB[0]:{}, UBLB[1]:{}}
data = {UBLB[0]:{}, UBLB[1]:{}, UBLB[2]:{}}

for j in range(len(layers)):
    i = 0
    for guid in compas_rhino.get_points(layer=layers[j]):
        point = compas_rhino.rs.PointCoordinates(guid)
        data[UBLB[j]][i] = list(point)
        i += 1
    print('Found {0} points in layer {1}'.format(i, layers[j]))


with open('/Users/mricardo/compas_dev/me/anagni/' + title + '.json', 'w') as outfile:
    json.dump(data, outfile)
    
print('Saved a .json to:', outfile)