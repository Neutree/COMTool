import unittest
from PyCom import Main

class PyComTest(unittest.TestCase):

    def setUp(self):
        print("setup")

    def tearDown(self):
        print("teardown")

    def test_1(self):
        print("test")
        Main.main()



if __name__=="__main__":
    unittest.main() #执行用例#
