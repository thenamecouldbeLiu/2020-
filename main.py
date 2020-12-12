import pandas as pd
import numpy as np
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
#from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException
import time


class IndividualScraperResult(object):
    def __init__(self, **kwargs):
        self.individual_result ={}

        for k,v in kwargs.items():
            self.individual_result[k] = v


    def getResult(self):
        return self.individual_result

class YoutubeScraper(object):

    def __init__(self, target_pages = ["https://www.youtube.com/watch?v=C4Z9BtKIu0w"], infinite_scroll =0, num_of_post =10):
        self.target_pages = target_pages
        self.email = ""
        self.pwd = ""
        self.result ={}
        self.num_of_post = num_of_post
        self.final_DF = pd.DataFrame()

        options = webdriver.ChromeOptions()
        prefs = {
            "profile.default_content_setting_values":
                {
                    "notificaitons": 2
                }
        }
        options.add_experimental_option("prefs", prefs)
        options.add_argument("disable-infobars")
        options.add_argument("--mute-audio")
        options.add_argument('--headless')  # 啟動無頭模式
        options.add_argument('--disable-gpu')  # windowsd必須加入此行
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(5)

    def loginInfo(self, file = "credentials.txt"):
        with open(file) as info:
            temp_list = info.readlines()
        #去掉換行字元
        for i in range(len(temp_list)):
            temp_list[i] = temp_list[i].strip("\n")
        self.email = temp_list[0]
        self.pwd = temp_list[1]

    def targetFileReader(self, file = "target.txt"):
        #開目標檔案
        with open(file) as pages:
            self.target_pages = pages.readlines()
        #去掉換行字元
        for i in range(len(self.target_pages)):
            self.target_pages[i] = self.target_pages[i].strip("\n")


    def goVideoPage(self, page):
        self.driver.get(page)

    def getUsefulClassName(self, class_name):
        return class_name.replace(" ", ".")

    def getNumberInString(self, s):
        return re.findall("\d+", s)


    def getDataFrame(self, data):

        data_DF = pd.DataFrame.from_dict(data)
        if len(self.final_DF):
            self.final_DF = pd.concat([self.final_DF,data_DF])
        else:
            self.final_DF = data_DF


    def getContent(self):
        video_class_xpath = "//*[@id='container']/h1/yt-formatted-string"
        view_class_xpath = "//*[@id='count']/yt-view-count-renderer/span[1]"
        time_class_xpath = "//*[@id='date']/yt-formatted-string"
        likedislike_class = "#text.style-scope.ytd-toggle-button-renderer.style-text"
        #respond_class = "#content-text.style-scope.ytd-comment-renderer"

        url = self.driver.current_url
        video_name = self.driver.find_element_by_xpath(video_class_xpath).text
        view_num = self.getNumberInString(self.driver.find_element_by_xpath(view_class_xpath).text)
        view_num = "".join(view_num)
        time_stamp = self.getNumberInString(self.driver.find_element_by_xpath(time_class_xpath).text)
        time_stamp = "/".join(time_stamp)
        like_dislike = self.driver.find_elements_by_css_selector(likedislike_class)
        dislike = like_dislike[1].get_attribute("aria-label")[:-4]
        like = like_dislike[0].get_attribute("aria-label")[:-4]

        print(video_name, view_num, time_stamp, dislike, like, url)

        wait = WebDriverWait(self.driver,15)
        body = self.driver.find_element_by_css_selector('body')
        body.send_keys(Keys.PAGE_DOWN)

        data = []
        keep_scroll = True
        while keep_scroll:
            cur_height = self.driver.execute_script("return document.documentElement.scrollHeight;")
            #print("cur:", cur_height)
            wait.until(EC.visibility_of_element_located((By.TAG_NAME, "body"))).send_keys(Keys.END)
            time.sleep(10)
            check_height = self.driver.execute_script("return document.documentElement.scrollHeight;")
            #print("check:", check_height)
            if cur_height == check_height:
                break

        print("finish scrolling")

        more_comment_class = "//ytd-button-renderer[@id='more-replies']/a/paper-button[@id='button']"

        #"#text.style-scope.ytd-button-renderer"
        all_more_comment_button = self.driver.find_elements_by_xpath(more_comment_class)
        #打開每個更多回應
        for button in all_more_comment_button:
            try:
                webdriver.ActionChains(self.driver).move_to_element(button).click(button).perform()
            except:
                pass
        counter =1
        all_comments = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#content-text")))
        for comment in all_comments:

            print(counter,"/", len(all_comments))
            counter +=1
            print(comment.text)
            data.append(comment.text)
        """
        res_dict = {
            "video_name" : video_name,
            "url" : url,
            "view": view_num,
            "like": like,
            "dislike": dislike,
            "timestamp":time_stamp,
            "reply": data

        }"""


        res = IndividualScraperResult(video_name = video_name, url =url, view_num = view_num, like = like,
                                      dislike = dislike, time_stamp = time_stamp, reply =data)
        self.getDataFrame(res.getResult())

    def getFinalResult(self):

        for col in self.final_DF.columns:
            print(self.final_DF.loc[:,col].head())
        self.final_DF.to_excel("youtube_scraper_result.xlsx")




    def run(self):
        self.targetFileReader()
        while len(self.target_pages):
            cur_page = self.target_pages.pop()
            self.goVideoPage(cur_page)
            self.getContent()

        self.driver.quit()
        self.getFinalResult()
"""            
        except Exception as e:
            import sys
            import traceback
            #    print(e)
            error_class = e.__class__.__name__  # 取得錯誤類型
            detail = e.args[0]  # 取得詳細內容
            cl, exc, tb = sys.exc_info()  # 取得Call Stack
            lastCallStack = traceback.extract_tb(tb)[-1]  # 取得Call Stack的最後一筆資料
            fileName = lastCallStack[0]  # 取得發生的檔案名稱
            lineNum = lastCallStack[1]  # 取得發生的行號
            funcName = lastCallStack[2]  # 取得發生的函數名稱
            errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
            print(errMsg)"""



if __name__ == "__main__":

    new_scraper = YoutubeScraper()
    new_scraper.run()