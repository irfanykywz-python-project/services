from root_app.utils.file import readFile

from adbutils import adb
from uiautomator2 import Direction

import uiautomator2 as u2
import random, os
import time


class UIAUTOMATOR:

    SHOPEE_PACKAGE_NAME = "com.shopee.id"
    DEFAULT_TIMEOUT = 10

    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, attr):
        return getattr(self.parent, attr)

    def connect(self):
        try:
            print('connecting to device')
            self.status_bar.emit('connecting to device')
            self.d = u2.connect(self.payload['device'])
            self.d.implicitly_wait(self.DEFAULT_TIMEOUT)
        except Exception as e:
            print(e)

    def run(self):
        # connect uiautomator
        self.connect()

        # do upload
        self.upload(self.payload['media'])

    def screen(self):
        print('screen on')
        if not self.d.info.get('screenOn'):
            self.d.screen_on()
            # self.d.swipe_ext(Direction.FORWARD)

    def open(self):
        print(f'open {self.SHOPEE_PACKAGE_NAME}')
        self.status_bar.emit(f'open {self.SHOPEE_PACKAGE_NAME}')

        self.d.app_start(self.SHOPEE_PACKAGE_NAME, use_monkey=True)
        # wait until opened
        self.d.app_wait(self.SHOPEE_PACKAGE_NAME, front=True)
        time.sleep(5)

    def close(self):
        print(f'close {self.SHOPEE_PACKAGE_NAME}')
        self.status_bar.emit(f'close {self.SHOPEE_PACKAGE_NAME}')

        self.d.app_stop(self.SHOPEE_PACKAGE_NAME)
        time.sleep(5)

    def upload(self, medias):

        for media in medias:

            self.close()
            self.open()

            # move media to device
            print('push media to device')
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

            print('click video nav bottom')
            self.status.emit({
                'row': media['row'],
                'message': f'click video nav bottom'
            })
            self.d.xpath(
                '//*[@resource-id="com.shopee.id:id/sp_bottom_tab_layout"]/android.widget.FrameLayout[4]/android.widget.FrameLayout[1]').click_exists()

            print('wait until create video button exist')
            while True:
                print(self.d.exists(description="click top right create icon"))
                if self.d.exists(description="click top right create icon"):
                    print('click create video button')
                    self.status.emit({
                        'row': media['row'],
                        'message': f'click create video button'
                    })
                    self.d(description="click top right create icon").click_gone(maxretry=5)
                    break
                time.sleep(0.50)

            print('wait until galery button exist, need extra time...')
            while True:
                print(self.d.exists(resourceId="com.shopee.id:id/tv_gallery_entrance"))
                if self.d.exists(resourceId="com.shopee.id:id/tv_gallery_entrance"):
                    break
                time.sleep(0.50)

            print('click galery')
            self.status.emit({
                'row': media['row'],
                'message': f'click galery'
            })
            self.d(resourceId="com.shopee.id:id/tv_gallery_entrance").click_gone()
            time.sleep(3)

            print('click video tab')
            self.status.emit({
                'row': media['row'],
                'message': f'click video tab'
            })
            self.d(text="Video").click_exists()
            time.sleep(3)

            print('select first video')
            self.status.emit({
                'row': media['row'],
                'message': f'select first video'
            })
            self.d.xpath(
                '//*[@resource-id="com.shopee.id:id/rv_gallery"]/android.widget.RelativeLayout[1]/android.widget.ImageView[1]').click_exists()
            time.sleep(3)

            print('click lanjutkan preview page')
            self.status.emit({
                'row': media['row'],
                'message': f'click lanjutkan preview page'
            })
            print(self.d(text="Lanjutkan"))
            self.d(text="Lanjutkan").wait()
            self.d(text="Lanjutkan").click_exists()
            time.sleep(3)

            print('click lanjutkan edit page')
            self.status.emit({
                'row': media['row'],
                'message': f'click lanjutkan edit page'
            })
            self.d(resourceId="com.shopee.id:id/tv_compress").wait()
            self.d(resourceId="com.shopee.id:id/tv_compress").click_exists()
            time.sleep(3)

            caption = readFile(media['file_caption'])
            print(caption)
            if caption:
                print('isi caption')
                self.status.emit({
                    'row': media['row'],
                    'message': f'isi caption'
                })

                self.d.xpath('//*[contains(@resource-id, "/ll_caption")]').click_exists()
                self.d.set_fastinput_ime(True)
                self.d.send_keys(caption)
                time.sleep(2)
                # hide keyboard
                self.d.press("back")
                # click ok
                self.d.xpath('//*[contains(@resource-id, "/tv_right")]').click()
                time.sleep(3)

            product = readFile(media['file_product'])
            print(product)
            if product:
                self.status.emit({
                    'row': media['row'],
                    'message': f'add product'
                })

                print('add product')
                self.d.xpath('//*[contains(@resource-id, "/iv_product_symbol")]').click()
                time.sleep(3)

                print('click tab semua')
                self.d(text="Semua").wait()
                self.d(text="Semua").click_exists()
                time.sleep(3)

                self.d(text="Cari Produk").click_exists()
                self.d.set_fastinput_ime(True)
                self.d.send_keys(product)

                print('wait until product exist')
                while True:
                    print(self.d.xpath('//android.widget.ScrollView/android.view.ViewGroup[1]/android.view.ViewGroup[2]/android.view.ViewGroup[1]/android.view.ViewGroup[2]').exists)
                    if self.d.xpath('//android.widget.ScrollView/android.view.ViewGroup[1]/android.view.ViewGroup[2]/android.view.ViewGroup[1]/android.view.ViewGroup[2]').exists:
                        # hide keyboard
                        time.sleep(5)
                        self.d.press("back")
                        break
                    time.sleep(0.50)

                while True:
                    print('click tambah produk')
                    self.d.xpath('//android.widget.ScrollView/android.view.ViewGroup[1]/android.view.ViewGroup[2]/android.view.ViewGroup[1]/android.view.ViewGroup[last()]/android.widget.TextView[1]').click()
                    time.sleep(3)

                    print('check popup product showed')
                    print(self.d.xpath('//*[@resource-id="android:id/content"]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.ViewGroup[2]/android.view.ViewGroup[1]/android.widget.ImageView[1]').exists)
                    if self.d.xpath('//*[@resource-id="android:id/content"]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.ViewGroup[2]/android.view.ViewGroup[1]/android.widget.ImageView[1]').exists:
                        break

                    time.sleep(0.50)

                print('click selesai button')
                self.d.xpath('//*[@resource-id="android:id/content"]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.view.ViewGroup[1]/android.view.ViewGroup[1]/android.view.ViewGroup[2]/android.view.ViewGroup[2]').click_exists()
                time.sleep(3)

            print('click posting button')
            self.status.emit({
                'row': media['row'],
                'message': f'click posting button'
            })
            # self.d(resourceId="com.shopee.id.dfpluginshopee16:id/btn_post").click_exists()

            # wait until element exist..
            # TODO

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

            print('delay dont like a robot')
            time.sleep(15) # dont act like a bot !