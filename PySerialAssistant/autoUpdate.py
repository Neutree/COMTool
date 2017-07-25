import webbrowser
import urllib.request
from bs4 import BeautifulSoup
from PySerialAssistant import helpAbout,parameters

class AutoUpdate:
    updateUrl = "https://github.com/Neutree/PyserialAssistant/releases"
    def detectNewVersion(self):
        try:
            page = urllib.request.urlopen(self.updateUrl)
            html_doc = page.read().decode()
            soup = BeautifulSoup(html_doc,"html.parser")
            for v in soup.select('.release-timeline .label-latest .css-truncate-target'):
                versionStr = v.get_text()
                version = list(map(int, versionStr[1:].split(".")))
                if version[0]*10+version[1] > helpAbout.versionMajor*10+helpAbout.versionMinor:
                    return True
                print("no new version,the newest is %s, now:V%d.%d" %(versionStr,helpAbout.versionMajor,helpAbout.versionMinor))
                return False
        except Exception as e:
            print("error:",e)
            return False
        print("Already latest version!")
        return False

    def OpenBrowser(self):
        webbrowser.open(self.updateUrl, new=0, autoraise=True)
        return