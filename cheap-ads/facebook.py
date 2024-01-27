from root_app.utils.file import storeFile, readFile, readDir
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, urlsplit, urlunsplit

import asyncio, re, json, pyotp, random, spintax

class Facebook:

    baseUrlDesktop = 'https://www.facebook.com/'
    baseUrlMobile = 'https://m.facebook.com/'
    baseUrlMbasic = 'https://mbasic.facebook.com/'
    baseUrlTouch = 'https://touch.facebook.com/'

    userAgentApp = 'Mozilla/5.0 (Linux; Android 6.0.1; LG-K240 Build/MXB48T; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/55.0.2883.91 Mobile Safari/537.36 [FB_IAB/FB4A;FBAV/396.0.0.21.104;]'

    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, attr):
        return getattr(self.parent, attr)

    async def run(self):

        # auth first
        if not self.payload['action'] == 'open':
            await self._auth()
            await self._setLanguage()

        # do action
        if self.payload['action'] == 'check_group':
            await self.checkGroup()
        if self.payload['action'] == 'check_inbox':
            await self.checkInbox()
        if self.payload['action'] == 'export_group':
            await self.exportGroup()
        if self.payload['action'] == 'collect':
            await self.collect()
        if self.payload['action'] == 'rawat':
            await self.rawat()
        if self.payload['action'] == 'open':
            await self.open()
        if self.payload['action'] == 'join':
            await self.joinGroup()
        if self.payload['action'] == 'delete':
            await self.deletePost()
        if self.payload['action'] == 'sundul':
            await self.sundulPost()
        if self.payload['action'] == 'post_group':
            await self.postGroup()

    async def _auth(self):
        async def _hasLogin():
            soup = BeautifulSoup(await self.tab.html, "html.parser")
            if soup.select('#m_login_email'):
                print('form input found')
                return None
            elif soup.select('a[href*="login.php"]'):
                print('account need login')
                return None

            return True

        async def _hasA2F():
            print('check by url')
            if '/checkpoint/' in await self.tab.url:
                print(' check again, if content have form with id #approvals_code')
                html = BeautifulSoup(await self.tab.html, "html.parser")
                if html.find_all("input", {"id": "approvals_code"}):
                    print("input otp Found #1")
                    return True

            print('otp not found')
            return None

        async def _handleA2F():
            print('check user have a2f key')
            if self.payload['a2f'] is None:
                self.error.emit({
                    'row': self.payload['row'],
                    'type': '_collect',
                    'message': 'a2f key not found'
                })
                await asyncio.sleep(5)
                await self.tab.crash()

            print('generate otp')
            totp = pyotp.TOTP(self.payload['a2f'])
            otp = totp.now()
            print(self.payload['a2f'])

            print('focus to #approvals_code')
            await self.tab.js_code(self.scrollTo('#approvals_code'))
            await asyncio.sleep(2)

            print('click & fill input #approvals_code')
            await self.tab.mouse_click_element_rect("#approvals_code")
            await self.tab.keyboard_send(string=otp, timeout=5)
            await asyncio.sleep(2)

            print('focus & click to #checkpointSubmitButton-actual-button')
            await self.tab.js_code(self.scrollTo('#checkpointSubmitButton-actual-button'))
            # dont use click from ichrome, use javascript because have popup password !!!
            await self.tab.wait_tag_click('#checkpointSubmitButton-actual-button')
            await self.tab.mouse_click_element_rect("#checkpointSubmitButton-actual-button")

            print('wait form submited')
            await self.tab.wait_loading(5)

            # after submit otp default is show save browser
            # but if not show save browser its a checkpoint
            # handle until button not exist
            await _handleCheckPoint()

        async def _handleCheckPoint():
            # after login
            # facebook will check account login/checkpoint/
            print('check if url have path login/checkpoint/')
            url = await self.tab.url
            if 'login/checkpoint/' in url:
                print('found it, handle process')

                print('focus & click to #checkpointSubmitButton-actual-button')
                await self.tab.js_code(self.scrollTo('#checkpointSubmitButton-actual-button'))
                await self.tab.mouse_click_element_rect("#checkpointSubmitButton-actual-button")

                print('wait page loaded')
                await self.tab.wait_loading(5)

                # check again until url login/checkpoint/ not exist
                await _handleCheckPoint()

        self.messages.emit({
            'row': self.payload['row'],
            'message': 'check login...'
        })

        # goto settings account > for trigget view app
        await self.tab.goto(self.baseUrlMobile + 'settings/account/')
        await self.tab.wait_includes('</body>')
        await asyncio.sleep(4)

        if not await _hasLogin():

            self.messages.emit({
                'row': self.payload['row'],
                'message': 'login akun...'
            })

            # process login
            await self.tab.wait_tag_click('a[href*="login.php"]')
            await self.tab.wait_includes('</body>')

            # check url if have login/?next
            # its a choice account select new account
            soup = BeautifulSoup(await self.tab.html, "html.parser")
            if soup.select('a[href*="login/?next"]'):
                print('choice account, click new loign')
                await self.tab.wait_tag_click('a[href*="login/?next"]')
                await self.tab.wait_tag('#m_login_email', timeout=2)
                await asyncio.sleep(2)

            # fill email
            print('fill username')
            await self.tab.mouse_click_element_rect('#m_login_email')
            await self.tab.keyboard_send(string=self.payload['identity'])
            await asyncio.sleep(2)

            # fill password
            print('fill password')
            await self.tab.mouse_click_element_rect('#m_login_password')
            await self.tab.keyboard_send(string=self.payload['password'])
            await asyncio.sleep(2)

            # submit
            print('submit')
            await self.tab.wait_tag_click('button[name=login]')
            await self.tab.wait_loading(5)

            # check a2f
            if await _hasA2F():
                await _handleA2F()

            # validate login again
            if await _hasLogin():

                self.messages.emit({
                    'row': self.payload['row'],
                    'message': 'akun berhasil login'
                })

                # save cookie
                self.cookies.emit({
                    'row': self.payload['row'],
                    'cookies': await self.tab.get_cookies()
                })


            else:

                self.messages.emit({
                    'row': self.payload['row'],
                    'message': 'akun tidak bisa login, cek'
                })

                self.error.emit({
                    'row': self.payload['row'],
                    'type': '',
                    'message': 'akun tidak bisa login, cek username / passwordnya'
                })

        else:

            self.messages.emit({
                'row': self.payload['row'],
                'message': 'akun masih login'
            })

            # save cookie
            self.cookies.emit({
                'row': self.payload['row'],
                'cookies': await self.tab.get_cookies()
            })

    async def _setLanguage(self):

        # before setting check first language if not id
        soup = BeautifulSoup(await self.tab.html, "html.parser")
        html = soup.select_one('html')
        if 'id' in html['lang']:
            print('skip, language has id')
            return None

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'sedang setting bahasa'
        })
        await self.tab.goto(self.baseUrlMobile + 'language/')
        await self.tab.wait_includes('</body>')
        await asyncio.sleep(4)
        await self.tab.wait_tag_click("span[value=id_ID]", timeout=5)
        await self.tab.wait_loading(timeout=5)
        self.messages.emit({
            'row': self.payload['row'],
            'message': f'setting bahasa selesai'
        })

    """
    open
    ====
    """
    async def open(self):
        print(self.baseUrlDesktop)
        await asyncio.sleep(3)
        await self.tab.goto(self.baseUrlDesktop)

    """
    check group
    ===========
    """
    async def checkGroup(self):

        readBadGroup = readFile(self.payload['userDirectory'] + 'link-bad-group.txt')
        listBadGroup = readBadGroup.split('\n') if readBadGroup else []
        readGoodGroup = readFile(self.payload['userDirectory'] + 'link-good-group.txt')
        listGoodGroup = readGoodGroup.split('\n') if readGoodGroup else []
        for index, url in enumerate(self.payload['groupList']):

            self.messages.emit({
                'row': self.payload['row'],
                'message': f'check group [{index + 1}/{len(self.payload["groupList"])}]'
            })

            # goto group
            if validateUrl(url):
                if '/' not in url[-1]:
                    url = url + '/'
                # print(url)
                await self.tab.goto(convertUrlToMobile(url) + 'madminpanel/pending/')
            else:
                print('url invalid, skip')
                continue

            await asyncio.sleep(random.randrange(5,10))

            # check article
            soup = BeautifulSoup(await self.tab.html, "html.parser")
            if soup.select('section > article'):
                # arcile found > this is pending post dump url for save
                listBadGroup.append(url)
                # remove duplicate
                listBadGroup = list(set(listBadGroup))
                # save
                storeFile(self.payload['userDirectory'] + 'link-bad-group.txt', "\n".join(listBadGroup))

            else:
                # this is not found article, dump url for save
                listGoodGroup.append(url)
                # remove duplicate
                listGoodGroup = list(set(listGoodGroup))
                # save
                storeFile(self.payload['userDirectory'] + 'link-good-group.txt', "\n".join(listGoodGroup))

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'check group selesai'
        })

    """
    check inbox
    ===========
    """

    async def checkInbox(self):

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'check pesan'
        })

        # click message navigation
        await self.tab.click('a[href*="messages/?entrypoint"]')
        await asyncio.sleep(10)

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'check pesan hidden'
        })

        # click hidden message
        await self.tab.click('a[href*="messages/?folder=pending"]')
        await asyncio.sleep(10)

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'check pesan spam'
        })

        # click spam message
        await self.tab.click('a[href*="messages/?folder=spam"]')

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'check pesan selesai'
        })

    """
    export group
    ===========
    """

    async def exportGroup(self):
        def parse(html):
            soup = BeautifulSoup(html, "html.parser")
            groupListTag = soup.select('#root a[href*="/groups/"]')
            groupList = []
            for group in groupListTag:
                groupUrl = group['href']
                if groupUrl[0] == '/':
                    if '?ref' in groupUrl:
                        groupUrl = groupUrl.split('?ref')[0]
                    groupUrl = self.baseUrlMbasic + groupUrl[1:]
                # print(groupUrl)
                groupList.append(groupUrl)
            return groupList

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'memulai export group'
        })

        # goto group with app view version
        await self.tab.goto(self.baseUrlMobile + 'groups_browse/your_groups/')
        await self.tab.wait_tag('#root a[href*="/groups/"]')

        while True:
            await self.tab.js("""
             window.scrollTo(0, document.body.scrollHeight);
             """)
            await asyncio.sleep(2)

            """
            save url when looping, prevent waiting if have many group
            """
            # then parse the group
            groupListAll = parse(await self.tab.html)

            # remove duplicate
            groupListAll = list(set(groupListAll))
            # print("all group")
            # print(groupListAll)

            # save list group
            storeFile(self.payload['userDirectory'] + 'Export Group.txt', "\n".join(groupListAll))

            self.messages.emit({
                'row': self.payload['row'],
                'message': f'{len(groupListAll)} group tersimpan'
            })

            # check loader class exist ?
            # if not exist reach the bottom of page and loaded all group
            soup = BeautifulSoup(await self.tab.html, "html.parser")
            if not soup.select_one('._lmw'):
                break

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'export group selesai'
        })

    """
    collect
    ===========
    """

    async def collect(self):
        async def insertStatus(text):
            # await self.tab.wait_tag('textarea[class~="composerInput"]')
            # await self.tab.mouse_click_element_rect('textarea[class~="composerInput"]')
            # await self.tab.keyboard_send(string=status, timeout=5)
            # await asyncio.sleep(2)
            # use javascript
            await self.tab.js_code("""
            document.querySelector('.mentions-placeholder').style.display = 'none';
            document.querySelector('input[name=status]').value = '%s';
            document.querySelector('textarea[class~="composerInput"]').value = '%s';
            """ % (text, text))
            await asyncio.sleep(2)

        async def insertPhoto(photoList):
            # upload file
            print('set file using cdp command')
            cdpRoot = await self.tab.send('DOM.getDocument')
            await asyncio.sleep(2)

            cdpSelector = await self.tab.send(
                    "DOM.querySelector",
                    nodeId=cdpRoot['result']['root']['nodeId'],
                    selector='input#photo_input[type="file"]',
                    timeout=10,
            )
            await asyncio.sleep(2)

            await self.tab.send(
                    "DOM.setFileInputFiles",
                    files=photoList,
                    nodeId=cdpSelector['result']['nodeId'],
                    timeout=5,
            )
            await self.tab.wait_tag_click('div._5cqb')
            await asyncio.sleep(2)

        # build payload
        statusText = readFile(self.payload['userDirectory'] + 'Collect.txt')
        dirPhoto = self.payload['userDirectory'] + 'Photo Status/'
        photoList = []
        for file in readDir(dirPhoto):
            photoList.append(dirPhoto + file)
        print(photoList)
        # validation
        if len(photoList) < 1:
            self.error.emit({
                'row': self.payload['row'],
                'type': '_collect',
                'message': 'collect photo not found'
            })
            await self.tab.close()
            return None

        self.messages.emit({
            'row': self.payload['row'],
            'message': 'start collect'
        })

        # click home navigation
        await self.tab.click('a[href*="/home"]')
        await self.tab.wait_tag('#m_home_notice')

        await self.tab.wait_tag_click("div[role=button][onclick*='bgUploadInlineComposerCallback']")
        await asyncio.sleep(2)

        # insert status
        statusSpin = spintax.spin(statusText)
        await insertStatus(statusSpin)

        # insert photo
        if photoList:
            await insertPhoto(photoList)

        # submit
        await self.tab.wait_tag_click("#composer-async-content button[data-sigil=submit_composer]")

        # handle dialog if exist
        async def cb(rs):
            # print(rs)
            await self.tab.handle_dialog(
                    accept=True,
                    promptText=None,
                    timeout=5
            )
        await self.tab.wait_event('Page.javascriptDialogOpening',timeout=1, callback_function=cb)

        # view post
        # wait progress show
        # div[data-sigil=bg-upload-progress-root][style*='(0%)']
        # wait post success show
        # div[data-sigil=bg-upload-progress-root][style*='(0%)'] div:nth-child(3) a
        await self.tab.wait_tag_click("div[data-sigil=bg-upload-progress-root][style*='(0%)'] div:nth-child(3) a")
        await asyncio.sleep(5)

        self.messages.emit({
            'row': self.payload['row'],
            'message': 'collect selesai'
        })

    """
    rawat
    ===========
    """
    async def rawat(self):

        async def likeAndComment(commentText):

            async def _scroll():
                lastIndex = 0
                stopWhenIndex = random.randrange(5, 10)
                while True:
                    # first detect count article with bs
                    soup = BeautifulSoup(await self.tab.html, "html.parser")
                    articleSelector = soup.select('article > footer > div > div:last-child a[data-uri]')
                    countArticle = len(articleSelector)

                    print(lastIndex)
                    if lastIndex > stopWhenIndex:
                        break

                    for scrollIndex in range(countArticle - lastIndex):
                        # start by lastIndex
                        lastIndex = lastIndex + 1
                        await self.tab.js_code(f'document.querySelectorAll("article > footer > div > div:last-child a[data-uri]")[{lastIndex}].scrollIntoView();')
                        await asyncio.sleep(random.randrange(3, 5))

                    # dont scroll like a robot
                    await asyncio.sleep(random.randrange(3, 5))
                return lastIndex


            # click home navigation
            await self.tab.click('a[href*="/home"]')
            await self.tab.wait_tag('#m_home_notice', timeout=5)
            await self.tab.wait_tag('article', timeout=5)

            # first we scroll
            countIndex = await _scroll()

            # then we get random index
            randomIndex = random.randrange(0, countIndex)
            print(randomIndex)

            # go to post page
            # header a:has(abbr)
            await self.tab.js_code(f'document.querySelectorAll("header a:has(abbr)")[{randomIndex}].click();')
            await self.tab.wait_tag('footer a[data-uri]', timeout=5)

            # before like, we check status
            # if has liked maybe this post has processed, must skip it and try other post
            soup = BeautifulSoup(await self.tab.html, "html.parser")
            if soup.select('footer a[data-uri][data-sigil*="unlike"]'):
                print('this post has liked, go search other post')
                return await likeAndComment()

            # go like
            print('do like')
            await self.tab.js_code('document.querySelector("footer a[data-uri]").click();')
            await self.tab.wait_tag('footer a[data-uri][data-sigil*="unlike"]', timeout=5)

            # go comment
            if commentText:
                print('do comment')

                # check first form comment exist or not
                soup = BeautifulSoup(await self.tab.html, "html.parser")
                if not soup.select('input[name=comment_text]'):
                    print('comment form not exist')
                    return None

                mess = spintax.spin(commentText)
                await self.tab.js_code("""
                document.querySelector('.mentions-placeholder').style.display = 'none';
                document.querySelector('input[name=comment_text]').value = '%s';
                var textarea = document.querySelector('#composerInput');
                textarea.value = '%s'
                textarea.scrollIntoView()
                """ % (mess, mess))
                await asyncio.sleep(2)

                # click send
                await self.tab.js_code("""
                var submitBtn = document.querySelector('form[action*="comment"] button[type=submit]');
                submitBtn.disabled = false;
                submitBtn.click()
                """)
                await asyncio.sleep(2)

                await self.tab.wait_tag('div[data-sigil*="m-photo-composer"] > div[data-uniqueid]', timeout=5)
                print('comment success')

        async def postStatus(text):

            # click home navigation
            await self.tab.click('a[href*="/home"]')
            await self.tab.wait_tag('#m_home_notice', timeout=5)

            await self.tab.wait_tag_click("div[role=button][onclick*='bgUploadInlineComposerCallback']", timeout=5)
            await self.tab.wait_tag('textarea[class~="composerInput"]', timeout=5)
            await asyncio.sleep(2)

            # insert status
            await self.tab.js_code("""
            document.querySelector('.mentions-placeholder').style.display = 'none';
            document.querySelector('input[name=status]').value = '%s';
            document.querySelector('textarea[class~="composerInput"]').value = '%s';
            """ % (text, text))
            await asyncio.sleep(2)

            # submit
            await self.tab.wait_tag_click("#composer-async-content button[data-sigil=submit_composer]", timeout=5)

            # handle dialog if exist
            async def cb(rs):
                # print(rs)
                await self.tab.handle_dialog(
                    accept=True,
                    promptText=None,
                    timeout=5
                )

            await self.tab.wait_event('Page.javascriptDialogOpening', timeout=1, callback_function=cb)

            # view post
            await self.tab.wait_tag_click("div[data-sigil=bg-upload-progress-root][style*='(0%)'] div:nth-child(3) a", timeout=5)
            await asyncio.sleep(5)

        async def sendMessage(profileUrl, messageText):

            await self.tab.set_ua(self.userAgentApp)
            await self.tab.goto(profileUrl)

            # click message button
            await self.tab.wait_tag_click('a[href*="messages/thread/"]', timeout=5)
            await self.tab.wait_tag('form[action*="messages/send"]', timeout=5)

            async def sendNewThread(mess):
                # set message
                await self.tab.js_code("""
                var textarea = document.querySelector('textarea[name=body]');
                textarea.value = '%s'
                textarea.scrollIntoView()
                """ % (mess))
                await asyncio.sleep(2)

                # click send
                await self.tab.js_code("""
                var submitBtn = document.querySelector('form button[type=submit]:nth-of-type(1)');
                submitBtn.disabled = false;
                submitBtn.click()
                """)
                await asyncio.sleep(2)

            async def sendExistThread(mess):
                # set message

                await self.tab.js_code("""
                var textarea = document.querySelector('#composerInput');
                textarea.value = '%s'
                textarea.scrollIntoView()
                """ % (mess))
                await asyncio.sleep(2)

                # click send
                await self.tab.js_code("""
                var submitBtn = document.querySelector('form button[type=submit]:nth-of-type(1)');
                submitBtn.disabled = false;
                submitBtn.click()
                """)
                await asyncio.sleep(2)

            soup = BeautifulSoup(await self.tab.html, "html.parser")
            mess = spintax.spin(messageText)
            if soup.select('form#composer_form'):
                print('new message thread')
                await sendNewThread(mess)
            elif soup.select('div#message-reply-composer'):
                print('exist message thread')
                await sendExistThread(mess)


        # prepare payload
        readStatusTxt = readFile(self.payload['userDirectory'] + 'Status.txt')
        statusList = readStatusTxt.split('\n')  if readStatusTxt else []
        readKomentarTxt = readFile(self.payload['userDirectory'] + 'Komen.txt')
        commentList = readKomentarTxt.split('\n') if readKomentarTxt else []
        readPesanTxt = readFile(self.payload['userDirectory'] + 'Pesan.txt')
        messageList = readPesanTxt.split('\n')  if readPesanTxt else []
        readTemanTxt = readFile(self.payload['userDirectory'] + 'Teman.txt')
        profileUrl = readTemanTxt.split('\n')  if readTemanTxt else []

        index = 0
        while True:

            # post status
            if index <= len(statusList) - 1:
                if len(statusList[index]) > 0:
                    print(statusList[index])
                    print('create status')
                    await postStatus(statusList[index])
                    # dont like a robot
                    await asyncio.sleep(random.randrange(10, 30))

            # like and comment
            if index <= len(commentList) - 1:
                if len(commentList[index]) > 0:
                    print('like and comment')
                    await likeAndComment(commentText=random.choice(commentList))
                    await asyncio.sleep(random.randrange(10, 30))
                else:
                    print('like only')
                    await likeAndComment(commentText=None)
                    print('sleep')
                    await asyncio.sleep(random.randrange(10, 30))
            else:
                print('like only')
                await likeAndComment(commentText=None)
                print('sleep')
                await asyncio.sleep(random.randrange(10, 30))

            if index <= len(profileUrl) - 1 and len(messageList) > 0:
                # validate profileUrl
                if validateUrl(profileUrl[index]):
                    print('url valid')
                    url = convertUrlToMobile(profileUrl[index])
                    print(url)
                    # validate length Message
                    if index <= len(messageList) - 1:
                        # use message by Index
                        message = messageList[index]
                        print('use index message')
                        print(message)
                    else:
                        # use message by random
                        message = random.choice(messageList)
                        print('use random message')
                        print(message)

                    if len(message) > 0:
                        # activity found set status live
                        loopKeepAlive = True
                        print('send message')
                        await sendMessage(url, message)

            index += 1
            await asyncio.sleep(30)

    """
    join
    ===========
    """
    async def joinGroup(self):
        # prepare payload
        readWawancaraTxt = readFile(self.payload['userDirectory'] + 'Wawancara.txt')
        answerText = readWawancaraTxt.split('\n')  if readWawancaraTxt else None
        readGroup = readFile(self.payload['userDirectory'] + 'Auto-Join.txt')
        if not readGroup:
            self.error.emit({
                'row': self.payload['row'],
                'type': '',
                'message': 'auto-join.txt masih kosong'
            })
            return None
        else:
            groupList = readGroup.split('\n')

        for index, url in enumerate(groupList):

            self.messages.emit({
                'row': self.payload['row'],
                'message': f'join group [{index + 1}/{len(groupList)}]'
            })

            # goto group
            if validateUrl(url):
                if '/' not in url[-1]:
                    url = url + '/'
                # print(url)
                await self.tab.goto(convertUrlToMobile(url))
                await self.tab.wait_loading(timeout=5)
                await self.tab.wait_tag('h1[dir]', timeout=5)
                await asyncio.sleep(5)
            else:
                print('url invalid, skip')
                continue

            # check join
            soup = BeautifulSoup(await self.tab.html, "html.parser")
            if not soup.select("div[aria-label*='Gabung']"):
                print('tidak ditemukan tombol gabung, kemungkinan sudah bergabung')
                continue

            # do join
            await self.tab.wait_tag_click("div[aria-label*='Gabung']", timeout=5)
            await self.tab.wait_loading(timeout=5)
            await asyncio.sleep(5)

            # check question
            soup = BeautifulSoup(await self.tab.html, "html.parser")
            if soup.select("div[aria-label*='Pertanyaan']"):
                print('question exist answer...')

                # textarea
                if textarea := soup.select("div[aria-label*='Pertanyaan'] textarea"):
                    print('textarea found, handle it')
                    for index, input in enumerate(textarea):
                        await self.tab.js_code(self.scrollTo("div[aria-label*='Pertanyaan'] textarea"))
                        await self.tab.mouse_click_element_rect("div[aria-label*='Pertanyaan'] textarea")
                        await self.tab.keyboard_send(string=random.choice(answerText))
                        await asyncio.sleep(2)

                # checkbox
                if checkbox := soup.select("div[aria-label*='Pertanyaan'] input[type=checkbox]"):
                    print('checkbox found, handle it')
                    for index, input in enumerate(checkbox):
                        await self.tab.js_code(f"""
                        document.querySelectorAll("div[aria-label*='Pertanyaan'] input[type=checkbox]")[{index}].click()
                        """)
                        await asyncio.sleep(2)

                # radio
                if radio := soup.select("div[aria-label*='Pertanyaan'] input[type=checkbox]"):
                    print('text area input found, handle it')
                    await self.tab.js_code(self.scrollTo("div[aria-label*='Pertanyaan'] input[type=radio]"))
                    await self.tab.js_code("""
                    document.querySelectorAll("div[aria-label*='Pertanyaan'] input[type=radio]")[0].click()
                    """)
                    await asyncio.sleep(2)


                # submit
                await self.tab.js_code(self.scrollTo("div[aria-label*='Pertanyaan'] div[aria-label*='Kirim'][role=button]:not([aria-disabled]"))
                await self.tab.wait_tag_click("div[aria-label*='Pertanyaan'] div[aria-label*='Kirim'][role=button]:not([aria-disabled]", timeout=5)
                await self.tab.wait_loading(timeout=5)
                await asyncio.sleep(5)

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'join group selesai'
        })

    """
    delete
    ===========
    """
    async def deletePost(self):
        while True:

            self.messages.emit({
                'row': self.payload['row'],
                'message': 'memulai menghapus post'
            })

            await self.tab.goto(self.baseUrlMbasic + 'allactivity/?category_key=groupposts')
            await self.tab.wait_includes('</body>')

            # check
            soup = BeautifulSoup(await self.tab.html, "html.parser")
            links = soup.select('header a[href*="confirm_dialog"]')

            # break
            if not links:
                self.messages.emit({
                    'row': self.payload['row'],
                    'message': 'menghapus post selesai'
                })
                break

            # do delete
            for index, link in enumerate(links):

                self.messages.emit({
                    'row': self.payload['row'],
                    'message': f'proses menghapus post [{index + 1}/{len(links)}]'
                })

                print(link['href'])
                await self.tab.js_code(f'window.location.href = "{link["href"]}"')
                await self.tab.wait_includes('</body>')
                await asyncio.sleep(2)

                await self.tab.wait_tag_click("a[href*='delete']")
                await self.tab.wait_includes('</body>')
                await asyncio.sleep(random.randrange(3, 10))

    """
    sundul
    ===========
    """
    async def sundulPost(self):

        # prepare payload
        readSundulTxt = readFile(self.payload['userDirectory'] + 'Sundul.txt')
        commentText = readSundulTxt.split('\n')  if readSundulTxt else None

        # validation
        if len(commentText) < 1:
            self.error.emit({
                'row': self.payload['row'],
                'type': '',
                'message': 'Sundul.txt masih kosong'
            })
            await self.tab.close()
            return None

        self.messages.emit({
            'row': self.payload['row'],
            'message': 'memulai sundul post'
        })

        await self.tab.goto(self.baseUrlMbasic + 'allactivity/?category_key=groupposts')
        await self.tab.wait_includes('</body>')

        # check
        soup = BeautifulSoup(await self.tab.html, "html.parser")
        links = soup.select('section header h3 a')

        for link in links:

            if 'memposting' in link.text:
                print(link['href'])
                await self.tab.js_code(f'window.location.href = "{link["href"]}"')
                await self.tab.wait_includes('</body>')
                await asyncio.sleep(2)

                await self.tab.js_code("""
                document.querySelector('textarea[name=comment_text]').value = `%s`;
                """ % (spintax.spin(random.choice(commentText))))
                await asyncio.sleep(2)

                # submit
                await self.tab.wait_tag_click("form[action*='comment'] table input[type=submit]")
                await self.tab.wait_includes('</body>')
                await asyncio.sleep(random.randrange(3, 10))


        self.messages.emit({
            'row': self.payload['row'],
            'message': 'sundul post selesai'
        })

    """
    post
    ===========
    """
    async def postGroup(self):
        async def insertStatus():
            # await self.tab.wait_tag('textarea[class~="composerInput"]')
            # await self.tab.mouse_click_element_rect('textarea[class~="composerInput"]')
            # await self.tab.keyboard_send(string=status.replace('\n', '\r') + '✅', timeout=5)
            # await asyncio.sleep(2)
            # use javascript
            await self.tab.js_code("""
            document.querySelector('textarea[name=xc_message]').value = `%s`;
            """ % (spintax.spin(self.payload['caption'])))
            await asyncio.sleep(2)

        async def insertPhoto():
            # click photo
            await self.tab.wait_tag_click('input[name=view_photo]')
            await self.tab.wait_tag('input[accept*="image"]')

            # upload file
            print('set file using cdp command')
            cdpRoot = await self.tab.send('DOM.getDocument')
            await asyncio.sleep(2)

            files = self.payload['image']
            print(files)

            numb = 1
            for file in files:
                print(f'input[name=file{str(numb)}]')
                cdpSelector = await self.tab.send(
                        "DOM.querySelector",
                        nodeId=cdpRoot['result']['root']['nodeId'],
                        selector=f'input[name=file{str(numb)}]',
                        timeout=10,
                )
                await asyncio.sleep(2)

                await self.tab.send(
                        "DOM.setFileInputFiles",
                        files=[file],
                        nodeId=cdpSelector['result']['nodeId'],
                        timeout=5,
                )

                numb += 1
            await self.tab.wait_tag_click('input[name=add_photo_done]')
            await self.tab.wait_tag('input[name=view_photo]')

        # send message
        self.messages.emit({
            'row': self.payload['row'],
            'message': 'memulai post'
        })

        hasPost = 0
        for index, url in enumerate(self.payload['groupList']):

            # send message
            self.messages.emit({
                'row': self.payload['row'],
                'message': f'proses post [{index + 1}/{len(self.payload["groupList"])}]'
            })

            if validateUrl(url):
                if '/' not in url[-1]:
                    url = url + '/'
                print(url)
                await self.tab.goto(convertUrlToMbasic(url))
                await self.tab.wait_loading(5)
            else:
                print('url invalid, skip')
                continue

            # # before click post button check first exist or not
            # # if not exist maybe you can't post to this group or you has banned !
            # soup = BeautifulSoup(await self.tab.html, "html.parser")
            # if not soup.select('div[role=button][onclick*="bgUploadInlineComposerCallback"]'):
            #     print(f'tidak bisa menemukan input status pada group {url}')
            #     continue
            #
            # await self.tab.wait_tag_click('div[role=button][onclick*="bgUploadInlineComposerCallback"]')
            # await asyncio.sleep(2)

            # insert status
            await insertStatus()

            # insert photo
            if self.payload['image']:
                await insertPhoto()

            # test
            # await asyncio.sleep(10)
            # continue

            # submit
            await self.tab.wait_tag_click("input[name=view_post]")
            await self.tab.wait_tag('article')

            await asyncio.sleep(5)

            hasPost += 1

            # safe post
            print(self.payload['safePost'])
            print(hasPost)
            if self.payload['safePost'] and hasPost >= 2:
                print('long sleep')
                for i in reversed(range(60*30)): # 30 minutes
                    self.messages.emit({
                        'row': self.payload['row'],
                        'message': f'delay in {i}'
                    })
                    await asyncio.sleep(1)
            else:

                print('short sleep')
                for i in reversed(range(10)): # 10 seconds
                    self.messages.emit({
                        'row': self.payload['row'],
                        'message': f'delay in {i}'
                    })
                    await asyncio.sleep(1)

        self.messages.emit({
            'row': self.payload['row'],
            'message': f'post selesai'
        })

def validateUrl(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def convertUrlToMobile(url):
    parse = list(urlsplit(url))
    parse[1] = "m.facebook.com"
    return urlunsplit(parse)

def convertUrlToMbasic(url):
    parse = list(urlsplit(url))
    parse[1] = "mbasic.facebook.com"
    return urlunsplit(parse)

def getGroupID(url):
    try:
        parse = re.search('\\/((\\d+))\\/', url)
        return parse.group(1)
    except:
        return None