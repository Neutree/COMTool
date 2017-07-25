import unittest,sys
from COMTool import Main,helpAbout

class COMTest(unittest.TestCase):

    def setUp(self):
        print("setup")

    def tearDown(self):
        print("teardown")

    def test_1(self):
        print("test",helpAbout.strAbout)
        Main.main()



if __name__=="__main__":
    unittest.main() #执行用例#
