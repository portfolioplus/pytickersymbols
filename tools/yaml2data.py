import yaml
import json
import os

# convert yaml and add to init file
input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          '..', 'stocks.yaml')
output_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '..', 'src', 'pytickersymbols', 'data.py')


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

        data = json.dumps(stock, ensure_ascii=False)
        out_file.write(f'__data__ = {data.replace("null", "None")}\n')