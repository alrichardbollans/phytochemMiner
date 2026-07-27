import json
import os
import sys

from phytochemMiner import TaxaData

if sys.version_info >= (3, 9):
    from importlib.resources import files
else:
    from importlib_resources import files

_inputs_path = str(files('phytochemMiner').joinpath('inputs'))


def filter_classes(extractions: TaxaData):
    classes_to_remove = get_classes()

    for taxon in extractions.taxa:
        if hasattr(taxon, 'compounds'):
            new_list = []
            for compound in taxon.compounds:
                if compound.lower() not in classes_to_remove:
                    new_list.append(compound)
            taxon.compounds = new_list
        if hasattr(taxon, 'inchi_keys'):
            new_dict = {}
            for compound in taxon.inchi_keys:
                if compound.lower() not in classes_to_remove:
                    new_dict[compound] = taxon.inchi_keys[compound]
            taxon.inchi_keys = new_dict

        if hasattr(taxon, 'inchi_key_simps'):
            new_dict = {}
            for compound in taxon.inchi_key_simps:
                if compound.lower() not in classes_to_remove:
                    new_dict[compound] = taxon.inchi_key_simps[compound]
            taxon.inchi_key_simps = new_dict


def get_classes() -> list[str]:
    class_json = json.load(open(os.path.join(_inputs_path, 'index_v1.json')))
    classes = set(class_json['Class'].keys())
    superclasses = set(class_json['Superclass'].keys())
    pathways = set(class_json['Pathway'].keys())

    all_classes = classes | superclasses | pathways

    ## Add some classes manually based on those found in cololmbia paper
    all_classes.add('saponins')
    all_classes.add('tannins')
    all_classes.add('flavonoids')
    all_classes.add('steroids')
    all_classes.add('non-reducing sugars')
    all_classes.add('hemolytic saponins')
    all_classes.add('organic acids')
    all_classes.add('catechins')
    all_classes.add('depsides and depsidones')
    all_classes.add('double olefins')
    all_classes.add('reducing sugars')
    all_classes.add('resins')
    all_classes.add('sesquiterpenolactones')
    all_classes.add('phenols')
    all_classes.add('purines')
    all_classes.add('polyphenols')
    all_classes.add('triterpenes')

    all_classes_lower = []

    # lower case everything in all classes
    for class_ in all_classes:
        all_classes_lower.append(class_.lower())

    assert 'alkaloids' in all_classes_lower
    assert 'saponins' in all_classes_lower

    return all_classes_lower
