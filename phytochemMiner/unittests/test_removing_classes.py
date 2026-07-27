# extraction\methods\unittests\test_get_agreements_and_disagreements.py
import unittest
from copy import deepcopy

from phytochemMiner import Taxon, TaxaData, filter_classes


class TestExamples(unittest.TestCase):
    def test_no_duplicates(self):
        taxa = [
            Taxon(scientific_name="Ficus religiosa", compounds=["alkaloids"], inchi_key_simps={'alkaloids':'HHH'}, accepted_name='a'),
            Taxon(scientific_name="Mangifera indica", compounds=["compound2", 'steroids'], inchi_key_simps={'steroids':'HHH', "compound2":'YYY'}, accepted_name='a')
        ]
        taxadat = TaxaData(taxa=deepcopy(taxa))
        filter_classes(taxadat)
        expected_taxa = [
            Taxon(scientific_name="Ficus religiosa", compounds=[], inchi_key_simps={}, accepted_name='a'),
            Taxon(scientific_name="Mangifera indica", compounds=["compound2"], inchi_key_simps={"compound2":'YYY'}, accepted_name='a')
        ]
        self.assertEqual(len(expected_taxa), len(taxadat.taxa))
        for i, taxon in enumerate(taxadat.taxa):
            self.assertEqual(expected_taxa[i].scientific_name, taxon.scientific_name)
            self.assertEqual(expected_taxa[i].compounds, taxon.compounds)
            self.assertEqual(expected_taxa[i].inchi_key_simps, taxon.inchi_key_simps)




if __name__ == '__main__':
    unittest.main()
