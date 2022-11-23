import yaml
import os

# convert yaml file to json
input_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                          '..', 'stocks.yaml')
output_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '..', 'stocks_akas.yaml')

os.makedirs(os.path.dirname(os.path.realpath(output_path)), exist_ok=True)

with open(output_path, 'w') as out_file:
    with open(input_path, 'r') as in_file:
        stock = yaml.safe_load(in_file)
        for idx, company in enumerate(stock["companies"]):
            if "akas" not in stock["companies"][idx]:
                stock["companies"][idx]["akas"] = []
        yaml.dump(stock, out_file, default_flow_style=False, sort_keys=False, allow_unicode=True)
