import yaml
import unittest
class TestStringMethods(unittest.TestCase):

    def test_yaml(self):
        with open('stocks.yaml') as f:
            data = yaml.safe_load(f)
            assert data
            assert data['companies']


if __name__ == '__main__':
    unittest.main()