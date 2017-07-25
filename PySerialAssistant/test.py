import unittest
from PySerialAssistant import Main

class UTest(unittest.TestCase):

    def setUp(self):
        print("setup")

    def tearDown(self):
        print("teardown")

    def test_1(self):
        print("test")



if __name__=="__main__":
    # unittest.main() #执行用例#
    Main.main()