import unittest

from train_models import _sex


class AustinFeatureTests(unittest.TestCase):
    def test_sex_upon_intake_distinguishes_female_from_male_substring(self):
        self.assertEqual(_sex("Spayed Female"), "female")
        self.assertEqual(_sex("Intact Female"), "female")
        self.assertEqual(_sex("Neutered Male"), "male")
        self.assertEqual(_sex("Unknown"), "unknown")


if __name__ == "__main__":
    unittest.main()
