import webbrowser

class AutoUpdate:
    updateUrl = "https://github.com/neutree/PySerialAssistant/releases"
    def detectNewVersion(self):

        return False

    def OpenBrowser(self):
        webbrowser.open(self.updateUrl, new=0, autoraise=True)
        return