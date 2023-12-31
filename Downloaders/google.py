import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[logging.FileHandler("google_downloader.log"), logging.StreamHandler()],
)


import os, time, threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from saving_photos import (
    FolderFilesManagement,
    SavingPhotoFromURLToFolderWithName,
)

FOLDER_PATH = os.path.join(os.getcwd(), "Images", "Google")


class GoogleDownloader:
    def __init__(self, searching_term):
        self.searching_term = searching_term
        self.setup_folder_path()

    def setup_folder_path(self):
        self.folder_path = os.path.join(FOLDER_PATH, self.searching_term)
        self.create_folder_if_not_exists()

    def create_folder_if_not_exists(self):
        folders = self.folder_path.split("/")
        for i in range(1, len(folders)):
            folder = "/".join(folders[: i + 1])
            if not os.path.isdir(folder):
                os.mkdir(folder)

    def start_download(self):
        self.create_driver()
        self.open_google()
        self.accept_cookies()
        self.switch_to_images()
        self.search_term()
        self.load_all_photos()
        self.download_images()
        self.driver.quit()

    def create_driver(self):
        self.driver = webdriver.Chrome()

    def open_google(self):
        self.driver.get("https://www.google.com/")

    def accept_cookies(self):
        try:
            accept_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="L2AGLb"]/div'))
            )
            accept_button.click()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            print("No cookies button")

    def switch_to_images(self):
        try:
            images_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="gb"]/div/div[1]/div/div[2]/a')
                )
            )
            images_button.click()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise Exception("Error - No images button")

    def search_term(self):
        try:
            search_bar = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="APjFqb"]'))
            )
            search_bar.send_keys(self.searching_term)
            search_bar.submit()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise Exception("Error - No search bar")

    def load_all_photos(self):
        self.scroll_down()
        while True:
            try:
                self.click_button_and_scroll_down()
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                break

    def click_button_and_scroll_down(self):
        try:
            button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.CLASS_NAME,
                        "LZ4I",
                    )
                )
            )
            button.click()
            self.scroll_down()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise Exception("Error - No button")

    def scroll_down(self):
        last_height = 0
        new_height = self.driver.execute_script("return document.body.scrollHeight")
        while last_height != new_height:
            last_height = new_height
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            self.wait_until_scroll_height_changes_or_timeout(last_height, 5)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

    def wait_until_scroll_height_changes_or_timeout(self, last_height, timeout):
        for i in range(timeout * 10):
            time.sleep(0.1)
            if (
                self.driver.execute_script("return document.body.scrollHeight")
                != last_height
            ):
                break

    def download_images(self, without_new_tab=False):
        self.click_first_div_with_img()
        while True:
            img_url = self.get_single_image()
            if not without_new_tab:
                self.download_more_imgs()
            if img_url:
                self.save_image(img_url)
            else:
                print("Error - No image")
            try:
                self.switch_to_next_img()
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                break

    def click_first_div_with_img(
        self,
    ):
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        try:
            self.img_div = self.driver.find_element(
                By.XPATH, '//*[@id="islrg"]/div[1]/div[1]'
            )
            self.img_div.click()
            time.sleep(0.5)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise Exception("Error - No divs")

    def switch_to_next_img(self):
        try:
            old_url = self.driver.current_url
            self.get_next_img_btn()
            self.next_img_btn.click()
            time.sleep(0.5)
            new_url = self.driver.current_url
            if old_url == new_url:
                raise Exception("Error - No next img btn")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise Exception("Error - No next img btn")

    def get_next_img_btn(self):
        try:
            self.next_img_btn = self.driver.find_element(
                By.XPATH,
                '//*[@id="Sva75c"]/div[2]/div[2]/div[2]/div[2]/c-wiz/div/div/div/div[1]/div/div[2]/div[1]/div/button[2]',
            )
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise Exception("Error - No next img btn")

    def get_single_image(self):
        try:
            img = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="Sva75c"]/div[2]/div[2]/div[2]/div[2]/c-wiz/div/div/div/div[3]/div[1]/a/img[1]',
                    )
                )
            )

            src = img.get_attribute("src")
            if src == None:
                src = img.get_attribute("data-src")
            return src
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            print("Error - No image")

    def download_more_imgs(self):
        self.open_more_imgs_in_new_tab_and_switch_tab()
        self.load_all_photos()
        self.download_images(without_new_tab=True)
        self.close_tab_and_switch_to_first_tab()

    def open_more_imgs_in_new_tab_and_switch_tab(self):
        try:
            more_imgs_url = self.get_more_imgs_url()
            self.driver.switch_to.new_window("tab")
            self.driver.get(more_imgs_url)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise Exception("Error - No more imgs url")

    def close_tab_and_switch_to_first_tab(self):
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    def get_more_imgs_url(self):
        try:
            more_imgs_btn = self.driver.find_element(
                By.XPATH,
                '//*[@id="Sva75c"]/div[2]/div[2]/div[2]/div[2]/c-wiz/div/div/div/c-wiz/div/div/div/div/div[1]/a',
            )
            more_imgs_url = more_imgs_btn.get_attribute("href")
            return more_imgs_url
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise Exception("Error - No more imgs btn")

    def save_image_threaded(self, img_url):
        try:
            img_name = self.get_converted_img_url_to_name_as_photo(img_url)
            photo = SavingPhotoFromURLToFolderWithName(
                img_url, self.folder_path, img_name
            )
            photo.save_photo()
        except Exception as e:
            logging.error(f"Unexpected error: {e}")

    def save_image(self, img_url):
        thread = threading.Thread(target=self.save_image_threaded, args=(img_url,))
        thread.start()

    def get_converted_img_url_to_name_as_photo(self, img_url):
        img_name = img_url.replace("https://", "")
        img_name = img_name.replace("http://", "")
        img_name = img_name.replace("/", "_")
        img_name = img_name.replace(":", "_")
        img_name = img_name.replace("?", "_")
        img_name = img_name.replace("=", "_")
        img_name = img_name.replace("&", "_")
        img_name = img_name.replace("%", "_")
        img_name = img_name.replace("+", "_")
        img_name = img_name.replace(".", "_")
        img_name = img_name.replace("-", "_")
        return img_name


if __name__ == "__main__":
    downloader = GoogleDownloader("dogs")
    downloader.start_download()
