import unittest
from PySerialAssistant import PySerialAssistant
import urllib.request
from bs4 import BeautifulSoup

class UTest(unittest.TestCase):

    def setUp(self):
        print("setup")

    def tearDown(self):
        print("teardown")

    def test_1(self):
        print("test")
        # self.jd("https://github.com/Neutree/PandaTvDanMu/releases")
        # os.system('start devmgmt.msc')
        PySerialAssistant.main()

    def jd(self,url):
        page = urllib.request.urlopen(url)
        html_doc = page.read().decode()
        soup = BeautifulSoup(html_doc,"html.parser")
        for v in soup.select('.release-timeline .label-latest .css-truncate-target'):
            print(v.get_text()[1:].split("."))


if __name__=="__main__":
    unittest.main() #执行用例#