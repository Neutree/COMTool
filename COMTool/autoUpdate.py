try:
    import version
    import parameters
except ImportError:
    from COMTool import version, parameters

log = parameters.log

class AutoUpdate:
    updateUrl = "https://github.com/Neutree/COMTool/releases"
    releaseApiUrl = "https://api.github.com/repos/Neutree/COMTool/releases"
    releaseApiUrl2 = "https://neucrack.com/comtool_update"
    def detectNewVersion(self):
        need, v = self.checkUpdate_neucrack() # github api may change, but this will not
        if not v:
            log.i("get version info from neucrack fail, now get from github")
            need , v = self.checkUpdate_github()
        return need, v
    
    def checkUpdate_github(self):
        import requests, json
        latest = version.Version()
        try:
            page = requests.get(self.releaseApiUrl)
            if page.status_code != 200:
                log.i("request {} fail, check update fail!".format(self.releaseApiUrl))
                return False, None
            releases = json.loads(page.content)
            releasesInfo = []
            for release in releases:
                if release["prerelease"] or release["draft"]:
                    continue
                tag = release["tag_name"]
                name = release["name"]
                body = release["body"]
                ver = self.decodeTag(tag, name, body)
                releasesInfo.append([ver, ver.major * 100 + ver.minor * 10 + ver.dev])
            releasesInfo = sorted(releasesInfo, key=lambda x:x[1], reverse=True)
            latest = releasesInfo[0][0]
            if self.needUpdate(latest):
                return True, latest
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, None
        log.i("Already latest version!")
        return False, latest

    def checkUpdate_neucrack(self):
        import requests, json
        latest = version.Version()
        try:
            page = requests.post(self.releaseApiUrl2)
            if page.status_code != 200:
                log.i("request {} fail, check update fail!".format(self.releaseApiUrl))
                return False, None
            release = json.loads(page.content)
            latest.load_dict(release)
            if self.needUpdate(latest):
                return True, latest
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, None
        log.i("Already latest version!")
        return False, latest

    def decodeTag(self, tag, name, body):
        # v1.7.9
        tag = tag[1:].split(".")
        return version.Version(int(tag[0]), int(tag[1]), int(tag[2]) if len(tag) > 2 else 0, name, body)

    def needUpdate(self, ver):
        if ver.major * 10 + ver.minor > version.major * 10 + version.minor:
            return True
        return False

    def OpenBrowser(self):
        import webbrowser
        webbrowser.open(self.updateUrl, new=0, autoraise=True)
        return

if __name__ == "__main__":
    update = AutoUpdate()
    needUpdate, latest = update.detectNewVersion()
    print(needUpdate, latest)
