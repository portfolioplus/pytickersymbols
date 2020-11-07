import yaml
import os
import wptools
import re
import wikipedia
import multiprocessing
from collections import OrderedDict

represent_dict_order = lambda self, data: self.represent_mapping(
    'tag:yaml.org,2002:map', data.items()
)
yaml.add_representer(OrderedDict, represent_dict_order)


def get_page(page_search):
    lang_codes = ['en', 'de', 'es', 'fr']
    for lang in lang_codes:
        try:
            return wptools.page(page_search, lang=lang).get_parse()
        except LookupError:
            try:
                wikipedia.set_lang(lang)
                search = wikipedia.search(page_search)
                if search:
                    return wptools.page(search[0], lang=lang).get_parse()
            except LookupError:
                print(f'no wiki page found for {page_search} lang {lang}.')
    return None


def metadata(stock_name):
    so = get_page(stock_name)
    founded = 'unknown'
    employees = 'unknown'
    if so:
        infobox = so.data.get('infobox', None)
        if infobox:
            foundation_str = infobox.get('foundation', '')
            foundation = re.findall(r'\d{4}', foundation_str)
            employees_str = (
                infobox.get('num_employees', '')
                .replace(',', '')
                .replace('.', '')
            )
            employees_items = re.findall(r'\d+', employees_str)
            if employees_items:
                employees = int(employees_items[0])
            if foundation:
                founded = int(foundation[-1])
    return founded, employees, stock_name


# convert yaml file to json
input_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'stocks.yaml'
)
output_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'stockswithmetadata.yaml'
)

pool = multiprocessing.Pool(10)
with open(output_path, 'w', encoding='latin1') as out_file:
    with open(input_path, 'r') as in_file:
        stocksyaml = yaml.safe_load(in_file)
        founded_values, employee_values, stock_names = zip(
            *pool.map(
                metadata,
                map(lambda stock: stock['name'], stocksyaml['companies']),
            )
        )
        metadata_values = list(zip(founded_values, employee_values, stock_names))
        for founded, employees, stock_name in metadata_values:
            for stock in stocksyaml['companies']:
                if stock['name'] == stock_name:
                    stock['metadata'] = {
                        'founded': founded,
                        'employees': employees,
                    }
                    break
        yaml.dump(stocksyaml, out_file, sort_keys=False)
