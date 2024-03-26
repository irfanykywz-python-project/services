from root_app.utils.file import readFile

from adbutils import adb
from uiautomator2 import Direction

import random, os
import time


class UIAUTOMATOR:

    TIKTOK_PACKAGE = "com.zhiliaoapp.musically.go"

    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, attr):
        return getattr(self.parent, attr)

    def run(self):

        self.screen()
        self.close()
        self.open()

        if self.action['name'] == 'upload':
            self.upload(self.action['media'])
        if self.action['name'] == 'scroll':
            self.scroll(self.action['limit'])

    def screen(self):
        if not self.d.info.get('screenOn'):
            self.d.screen_on()
            # self.d.swipe_ext(Direction.FORWARD)

    def open(self):
        print('open tiktok')

        # open tiktok
        # self.d.app_stop_all()
        self.d.app_start(self.TIKTOK_PACKAGE, use_monkey=True)

        # wait until opened
        self.d.app_wait(self.TIKTOK_PACKAGE, front=True)

    def close(self):
        self.d.app_stop(self.TIKTOK_PACKAGE)

    def upload(self, medias):
        for media in medias:

            self.status.emit({
                'row': media['row'],
                'message': f'upload started'
            })

            # move media to device
            self.status.emit({
                'row': media['row'],
                'message': f'push media to device'
            })
            d = adb.device(serial=self.payload['serial'])
            d.sync.push(media['file'], f"/sdcard/DCIM/{media['file_rename']}")
            # refresh file system, fix read file on app
            d.shell(f'am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:/sdcard/DCIM/{media["file_rename"]}')
            time.sleep(2)
            # return None

            # click plus button
            self.status.emit({
                'row': media['row'],
                'message': f'click plus button'
            })            
            self.d.xpath('//*[@resource-id="com.zhiliaoapp.musically.go:id/a56"]/android.widget.ImageView[1]').click_exists(timeout=5)

            # click upload button
            self.status.emit({
                'row': media['row'],
                'message': f'click upload button'
            })                        
            self.d(text="Upload").click_exists(timeout=5)
            time.sleep(3)  # wait media loaded

            # click first media
            self.status.emit({
                'row': media['row'],
                'message': f'select first media'
            })    
            self.d.xpath('//*[@resource-id="com.zhiliaoapp.musically.go:id/aex"]/android.widget.FrameLayout[1]/android.widget.ImageView[1]').click_exists(timeout=5)

            # click next
            self.status.emit({
                'row': media['row'],
                'message': f'next'
            }) 
            self.d(resourceId="com.zhiliaoapp.musically.go:id/alv").click_exists(timeout=5)

            # fill caption
            caption = readFile(media['file_caption'])
            # print(caption)
            if caption:
                self.status.emit({
                    'row': media['row'],
                    'message': f'fill caption'
                })
                self.d(resourceId="com.zhiliaoapp.musically.go:id/abm").click_exists(timeout=5)
                self.d.set_fastinput_ime(True)  # 切换成FastInputIME输入法
                self.d.send_keys(caption + '\r\n')
                # self.d.set_fastinput_ime(False)
                # hide keyboard
                time.sleep(2)
                self.d.press("back")

                # check if hastag choseer exist
                if self.d.xpath('//*[@resource-id="com.zhiliaoapp.musically.go:id/yd"]/android.view.ViewGroup[1]').exists:
                   self.d.xpath('//*[@resource-id="com.zhiliaoapp.musically.go:id/yd"]/android.view.ViewGroup[1]').click_exists(timeout=5)

            # click post button
            self.status.emit({
                'row': media['row'],
                'message': f'click post button'
            }) 
            self.d(resourceId="com.zhiliaoapp.musically.go:id/alw").click_exists(timeout=5)

            # wait until upload percentage gone
            self.status.emit({
                'row': media['row'],
                'message': f'wait uploaded'
            }) 
            while True:
                print(self.d.exists(resourceId="com.zhiliaoapp.musically.go:id/agb"))
                if self.d.exists(resourceId="com.zhiliaoapp.musically.go:id/agb"):
                    break
                time.sleep(0.50)


            # delete media on device
            self.status.emit({
                'row': media['row'],
                'message': f'delete media on device'
            })
            d.shell(f'rm /sdcard/DCIM/{media["file_rename"]}')

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

            print('delay 1 minutes')
            time.sleep(60) # dont act like a bot !


    def scroll(self, limit):
        count = 0
        while True:
            print(self.payload)
            width = self.payload['display']['width']
            height = self.payload['display']['height']

            x1 = width * 0.5
            y1 = height * 0.85
            y2 = height * 0.25

            self.d.swipe(x1, y1, x1, y2, 0.1)
            # self.d.swipe_ext(Direction.FORWARD)
            # self.d.swipe_ext(Direction.FORWARD)
            # click love
            # self.d(resourceId="com.zhiliaoapp.musically.go:id/rk").click_exists(timeout=5)

            # watching
            time.sleep(10)


            if count >= limit:
                print('finish scroll')
                break
            count += 1