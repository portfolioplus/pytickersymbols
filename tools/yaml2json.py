import yaml
import json
import os

# convert yaml file to json
input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          '..', 'stocks.yaml')
output_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '..', 'src', 'pytickersymbols', 'data', 'stocks.json')

os.makedirs(os.path.dirname(os.path.realpath(output_path)), exist_ok=True)

with open(output_path, 'w') as out_file:
    with open(input_path, 'r') as in_file:
        stock = yaml.safe_load(in_file)
        for idx, company in enumerate(stock["companies"]):
            while True:
                stop = True
                for idy, symbol in enumerate(company["symbols"]):
                    if "skip" in symbol and symbol["skip"]:
                        stock["companies"][idx]["symbols"].pop(idy)
                        stop = False
                        break
                if stop:
                    break
        json.dump(stock, out_file, ensure_ascii=False)
