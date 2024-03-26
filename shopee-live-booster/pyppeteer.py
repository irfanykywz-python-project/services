from root_app.utils.file import readFileJSON, storeFileJSON
from root_app.utils.path import get_temp_path
from root_app.utils.time import timeLog
from root_app.utils.ichrome import ChromeHelper

from pyppeteer import launch
from pyppeteer_stealth import stealth

from ichrome import ChromeDaemon

import json
import random
import re
import os
import asyncio

class Chrome(ChromeHelper):

    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, attr):
        return getattr(self.parent, attr)

    def _sendLog(self, val):
        if not self.parentBotView.logDisable.isChecked() and self.parentBotView.logEnable.isChecked():
            self.process.emit(timeLog(val))

    async def generate(self, payload):
        status = f'temp-{random.randrange(1, 9999999)}'
        browser = await launch(
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False,
            headless=True,
            executablePath=ChromeDaemon.get_chrome_path(),
            userDataDir=get_temp_path('profile'),
            devtools=False
        )
        page = await browser.newPage()
        await stealth(page)

        cdp = await page.target.createCDPSession()
        await cdp.send('Network.enable')

        async def response_url(data, status):
            data = data['response']['requestHeadersText']
            url = re.search('GET\s(.*=v2)', data)
            url = url.group(1)
            print(url)

            protocol = re.search('Sec-WebSocket-Protocol:\s(.*)\r', data)
            protocol = protocol.group(1)
            print(protocol)

            url_wss = [url, protocol]

            # save to file
            urls = readFileJSON(payload['filePath'])
            urls.append(url_wss)
            storeFileJSON(payload['filePath'], urls)

            # # send log
            self._sendLog(f"success generate websocket\n"
                          f"wss: {url_wss}")

            self._sendLog(f"total wss: {len(urls)}")

            print(status)
            with open(status, 'w') as f:
                pass

        cdp.on('Network.webSocketHandshakeResponseReceived', lambda res: asyncio.ensure_future(response_url(res, status)))

        url = f'https://live.shopee.co.id/share?from=live&session={payload["target"]}&in=1'
        self._sendLog(f"goto {url}")
        await page.goto(url)

        try:
            self._sendLog(f"wait video")
            await page.waitForSelector('div[class*=PlayHint__Wrapper] svg', {'visible': True, 'timeout': 60000})
            # await page.waitForSelector('video', {'visible': True, 'timeout': self.timeout})
            self._sendLog(f"play video")
            await page.click('div[class*=PlayHint__Wrapper] svg')
        except Exception as e:
            self._sendLog(str(e))
            return None

        self._sendLog(f"wait websocket")
        retry = 0
        while True:
            if os.path.exists(status):
                os.remove(status)
                break

            if retry >= self.timeout:
                self._sendLog(f"fail get websocket")
                break

            await asyncio.sleep(1)
            retry += 1

        await browser.close()