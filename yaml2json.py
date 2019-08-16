import yaml
import json
import os

# convert yaml file to json
input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          'stocks.yaml')
output_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           'src', 'pytickersymbols', 'data', 'stocks.json')

os.makedirs(os.path.dirname(os.path.realpath(output_path)), exist_ok=True)

with open(output_path, 'w') as out_file:
    with open(input_path, 'r') as in_file:
        out_file.write(json.dumps(yaml.safe_load(in_file)))
