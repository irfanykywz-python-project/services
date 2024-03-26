
from root_app.utils.pyppeteer import PuppeteerHelper
from root_app.utils.string import find_between
from root_app.utils.file import readFile

from ichrome import ChromeDaemon
from pyppeteer import launcher
from pyppeteer_stealth import stealth

from bs4 import BeautifulSoup

import os.path
import asyncio
import autoit

class Puppeter(PuppeteerHelper):
    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, attr):
        return getattr(self.parent, attr)

    def launcher(self, payload):
        initLauncher = launcher.Launcher(
            headless=False,
            handleSIGINT=False,
            handleSIGTERM=False,
            handleSIGHUP=False,
            ignoreHTTPSErrors=True,
            executablePath=ChromeDaemon.get_chrome_path(),
            userDataDir=payload['chrome_dir'] + f"chrome_{payload['chrome_port']}",
            devtools=False,
            defaultViewport=False,
            ignoreDefaultArgs=self.ignoreArgs,
            args=self.args + [
                '--mute-audio',
                '--disable-crash-reporter',
                '--enable-features=NativeFileSystemAPI',
                f'--remote-debugging-port={payload["chrome_port"]}'  # for stopping process
            ]
        )
        initLauncher.port = payload['chrome_port']
        initLauncher.url = f'http://127.0.0.1:{initLauncher.port}'
        return initLauncher

    """
    FETCH PROCESS
    """

    async def fetchProfile(self):
        launcher = self.launcher(self.payload['chrome'])
        browser = await launcher.launch()
        page = await browser.newPage()
        await page.setViewport({'width':1280, 'height':768})
        await stealth(page)

        self.process.emit(f'fetch accountscenter...')

        await page.goto('https://accountscenter.facebook.com/?entry_point=app_settings', options={'waitUntil': 'domcontentloaded'})

        self.process.emit(f'wait selector')
        await page.waitForSelector('a[role=link][href*="/profiles/"]', options={'visible':True})
        # await page.screenshot({'path': 'example.png'})

        # get profile list
        self.process.emit(f'get content')
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        self.process.emit(f'parsing')
        links = soup.select('a[role=link][href*="/profiles/"]:not([aria-current])')
        profile = []
        for link in links:
            uid = link['href'].replace('/profiles/', '').replace('/', '')
            name = link.get_text().replace('Facebook', '')
            profile.append({
                'id': uid,
                'name': name
            })
        # print(profile)

        # save
        self.saveTarget(profile)

        # while True:
        #     await asyncio.sleep(1)
        await browser.close()

    async def fetchFanspage(self):
        launcher = self.launcher(self.payload['chrome'])
        browser = await launcher.launch()
        page = await browser.newPage()
        await page.setViewport({'width':1280, 'height':768})
        await stealth(page)

        await page.goto('https://www.facebook.com/pages/?category=your_pages', waitUntil='domcontentloaded')

        await page.waitForSelector('div[role=main]:not([aria-label])', visible=True)

        html = await page.content()
        soup = BeautifulSoup(html, 'html.parser')

        cards = soup.select('div[role=main]:not([aria-label]) div[style*=--card-corner-radius]')

        fanspage = []
        for card in cards:
            link = card.select_one('a:has(svg)')
            inbox_link = card.select_one('a[href*=latest]')
            # print(link['aria-label'])
            # print(inbox_link['href'])
            uid = find_between(inbox_link['href'], '/latest/inbox/all?asset_id=', '&')
            name = link['aria-label']
            fanspage.append({
                'id': uid,
                'name': name
            })
        # print(fanspage)

        # save
        self.saveTarget(fanspage)

        # while True:
        #     await asyncio.sleep(1)
        await browser.close()

    """
    UPLOAD TYPE
    """

    async def uploadProfile(self):
        launcher = self.launcher(self.payload['chrome'])
        browser = await launcher.launch()
        page = await browser.newPage()
        await stealth(page)

        # TODO change profile...

        await self.uploadReels(page)

    async def uploadFanspage(self):
        self.statusBar.emit('open browser')
        launcher = self.launcher(self.payload['chrome'])
        browser = await launcher.launch()
        page = await browser.newPage()
        await stealth(page)

        self.statusBar.emit(self.payload['upload']['type'])
        if self.payload['upload']['type'] == 'reels':
            await self.uploadReels(page)
        elif self.payload['upload']['type'] == 'video':
            await self.uploadVideo(page)
        if self.payload['upload']['type'] == 'reels_meta':
            await self.uploadReelsMeta(page)

        # while True:
        #     await asyncio.sleep(1)
        await browser.close()

    async def switchProfile(self):
        pass
        # # change profile
        # await page.goto('https://www.facebook.com/')
        #
        # # open menu
        # await page.waitForSelector("div[aria-label*=Settings] > span div[role=button]", options={'visible': True})
        # await page.click("div[aria-label*=Settings] > span div[role=button]")
        #
        # # see all profile
        # await page.waitForSelector(
        #     "div[aria-label*=profile][role=dialog] div[style*=BasePulseEffect_containerScaleXFactor] div[role=button]",
        #     options={'visible': True})
        # await page.click(
        #     "div[aria-label*=profile][role=dialog] div[style*=BasePulseEffect_containerScaleXFactor] div[role=button]")
        #
        # # select profile
        #
        # while True:
        #     asyncio.sleep(1)
        #
        # await browser.close()

    async def switchFanspage(self, page):
        # switch to fanspage first
        self.statusBar.emit('goto fanspage')
        await page.goto(f'https://www.facebook.com/{self.payload["target"]["id"]}', waitUntil='domcontentloaded')

        # check first before switch
        self.statusBar.emit('check switch page')
        # print(await page.querySelector('div[aria-label=Switch]'))
        # while True:
        #     await asyncio.sleep(1)
        if await page.querySelector('div[aria-label=Switch]'):

            # click switch button
            self.statusBar.emit('click switch')
            await page.waitForSelector('div[aria-label=Switch]', visible=True)
            await page.click('div[aria-label=Switch]')

            # click switch on dialog
            self.statusBar.emit('click switch dialog')
            await page.waitForSelector('div[role=dialog] div[aria-label=Switch]', visible=True)
            await page.click('div[role=dialog] div[aria-label=Switch]')

            # wait switch loading
            self.statusBar.emit('wait switch')
            await page.waitForNavigation()

    async def uploadReels(self, page):

        await self.switchFanspage(page)

        print('do upload reels')
        for media in self.payload['media']:

            self.status.emit({
                'row': media['row'],
                'message': f'upload started'
            })

            # sync status has uploaded
            if 'yes' in media['uploaded']:
                self.status.emit({
                    'row': media['row'],
                    'message': f'skip, has uploaded'
                })
                continue

            # do action upload
            await page.goto('https://www.facebook.com/reels/create')

            # wait loading
            await page.waitForSelector('input[type=file]')

            self.status.emit({
                'row': media['row'],
                'message': f'fill video'
            })
            file = await page.querySelector('input[type=file]')
            await file.uploadFile(media['file_output'] if os.path.exists(media['file_output']) else media['file'])

            await asyncio.sleep(2)

            await page.click('div[aria-label=Next]')

            await asyncio.sleep(2)

            await page.click('div[aria-label=Next]:not([aria-disabled])')

            await asyncio.sleep(2)

            # fill caption
            caption = readFile(media['file_caption'])
            # print(caption)
            if caption:
                self.status.emit({
                    'row': media['row'],
                    'message': f'fill caption'
                })
                await page.waitForSelector('div[contenteditable=true]', visible=True)
                await page.type('div[contenteditable=true]', caption)

            await asyncio.sleep(2)

            # publish
            self.status.emit({
                'row': media['row'],
                'message': f'click publish'
            })
            await page.waitForSelector('div[aria-label=Publish]:not([aria-disabled])', options={'visible': True})
            await page.click('div[aria-label=Publish]:not([aria-disabled])')

            # wait publish
            await page.waitForNavigation()

            # wait url
            while True:
                print(page.url)
                if 'reel_composer' in page.url:
                    break
                await asyncio.sleep(1)

            self.status.emit({
                'row': media['row'],
                'message': f'upload finished'
            })

            # save to log
            self.saveLog(media['name'])

            # update uploaded status
            self.uploaded.emit({
                'row': media['row'],
                'uploaded': 'yes'
            })

    async def uploadVideo(self, page):

        await self.switchFanspage(page)

        print('do upload video')
        for media in self.payload['media']:

            self.status.emit({
                'row': media['row'],
                'message': f'upload started'
            })

            # sync status has uploaded
            if 'yes' in media['uploaded']:
                self.status.emit({
                    'row': media['row'],
                    'message': f'skip, has uploaded'
                })
                continue

            # do action upload
            await page.goto(f'https://www.facebook.com/{self.payload["target"]["id"]}', waitUntil='networkidle2')
            await asyncio.sleep(2)

            # wait loading status card
            await page.waitForSelector('div[data-pagelet=ProfileComposer] div[role=button]:nth-of-type(2)', visible=True)
            await page.click('div[data-pagelet=ProfileComposer] div[role=button]:nth-of-type(2)')
            await asyncio.sleep(2)

            # fill caption
            caption = readFile(media['file_caption'])
            print(caption)
            if caption:
                await page.waitForSelector('div[role=dialog] form div[contenteditable=true]', visible=True)
                await page.type('div[role=dialog] form div[contenteditable=true]', caption)
                await asyncio.sleep(2)
            # return None

            self.status.emit({
                'row': media['row'],
                'message': f'fill video'
            })
            await page.waitForSelector('input[type=file][multiple][accept*=mp4]')
            file = await page.querySelector('input[type=file][multiple][accept*=mp4]')
            await file.uploadFile(media['file_output'] if os.path.exists(media['file_output']) else media['file'])

            self.status.emit({
                'row': media['row'],
                'message': f'wait video uploaded'
            })
            await page.waitForSelector('div[role=dialog] form div[style="width: 100%;"]', visible=True)

            await page.waitForSelector('form div[aria-label=Post][role=button]'),
            await page.click('form div[aria-label=Post][role=button]')

            await page.waitForSelector('div[role=dialog] form', hidden=True)
            self.status.emit({
                'row': media['row'],
                'message': f'video uploaded'
            })

            # save to log
            self.saveLog(media['name'])

            # update uploaded status
            self.uploaded.emit({
                'row': media['row'],
                'uploaded': 'yes'
            })

    """
    PROCESS META BUSINESS
    """

    async def switchFanspageMeta(self, page):
        # switch fanspage
        await page.goto(f'https://business.facebook.com/latest/home?asset_id={self.payload["target"]["id"]}', waitUntil='domcontentloaded')

    async def uploadReelsMeta(self, page):

        print('goto')
        await self.switchFanspageMeta(page)

        for media in self.payload['media']:
            self.status.emit({
                'row': media['row'],
                'message': f'upload started'
            })

            # sync status has uploaded
            if 'yes' in media['uploaded']:
                self.status.emit({
                    'row': media['row'],
                    'message': f'skip, has uploaded'
                })
                continue

            # goto reels page
            await page.goto('https://business.facebook.com/latest/reels_composer?ref=biz_web_home_create_reel&context_ref=HOME', waitUntil='domcontentloaded')

            # await page.evaluateHandle("""HTMLInputElement.prototype.click = function() {
            #         if(this.type !== 'file') HTMLElement.prototype.click.call(this)
            # }""")

            self.status.emit({
                'row': media['row'],
                'message': f'fill video'
            })
            await page.waitForXPath("//div[contains(text(), 'Add Video')]", visible=True)
            addVideoButton = await page.xpath("//div[contains(text(), 'Add Video')]")
            await addVideoButton[0].click()

            # set file on dialog
            file = media['file_output'] if os.path.exists(media['file_output']) else media['file']
            file = file.replace('/', '\\')
            autoit.win_wait_active("Open", 10)
            if autoit.win_exists('Open'):
                await asyncio.sleep(5)
                autoit.control_set_text('Open', 'Edit1', file)
                autoit.control_send('Open', 'Edit1', '{ENTER}')

            # wait file upload
            self.status.emit({
                'row': media['row'],
                'message': f'wait video loaded'
            })
            while True:
                print(await page.querySelector('div[aria-valuenow="100"][role=progressbar]'))
                if await page.querySelector('div[aria-valuenow="100"][role=progressbar]'):
                    self.status.emit({
                        'row': media['row'],
                        'message': f'video loaded'
                    })
                    break
                await asyncio.sleep(1)

            # fill caption
            caption = readFile(media['file_caption'])
            # print(caption)
            if caption:
                self.status.emit({
                    'row': media['row'],
                    'message': f'fill caption'
                })
                await page.type('div[contenteditable=true]', caption)

            # fill colab
            # await page.type('input[placeholder*=collaborator]', 'https://testcoolab')

            # goto share tab
            shareTab = await page.xpath("//div[contains(text(), 'Share')]")
            await shareTab[0].click()

            # # click next
            # next = await page.xpath("//div[@class='uiContextualLayerParent']//div[contains(text(), 'Next')][last()]")
            # await next[0].click()
            #
            # next = await page.xpath("//div[@class='uiContextualLayerParent']//div[contains(text(), 'Next')][last()]")
            # await next[0].click()

            # schedule
            if 'schedule' in media:
                self.status.emit({
                    'row': media['row'],
                    'message': f'schedule setting'
                })
                await page.waitForXPath("//div[contains(text(), 'Schedule')]", visible=True)
                schedule = await page.xpath("//div[contains(text(), 'Schedule')]")
                await schedule[0].click()

                # fill date
                dateInput = await page.querySelector('input[placeholder="mm/dd/yyyy"]')
                await dateInput.click(clickCount=3)
                await page.keyboard.press('Backspace')
                await page.type('input[placeholder="mm/dd/yyyy"]', '3/26/2024')

                # fill time
                await page.type('input[aria-label=hours]', '7') # value max 12
                await page.type('input[aria-label=minutes]', '50') # value max 59
                await page.type('input[aria-label=meridiem]', 'PM') # value AM / PM

                # publish schedule
                schedule = await page.xpath("//div[contains(text(), 'Schedule')]")
                await schedule[1].click()

                # wait until url change
                while True:
                    print(page.url)
                    if 'latest/posts/scheduled_posts' in page.url:
                        break
                    await asyncio.sleep(1)

            else:
                # publish now
                share = await page.xpath("//div[text() = 'Share']")
                await share[1].click()

                # wait until url change
                while True:
                    print(page.url)
                    if 'latest/posts/published_posts' in page.url:
                        break
                    await asyncio.sleep(1)

            self.status.emit({
                'row': media['row'],
                'message': f'video uploaded'
            })

            # save to log
            self.saveLog(media['name'])

            # update uploaded status
            self.uploaded.emit({
                'row': media['row'],
                'uploaded': 'yes'
            })

        # while True:
        #     await asyncio.sleep(1)