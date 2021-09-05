from selenium import webdriver
from selenium.webdriver.common import keys
from selenium.webdriver.common.keys import Keys
from webdriver_manager import driver
from webdriver_manager.chrome import ChromeDriver, ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup
import pandas as pd
import pafy

def convert_views(df):
    if 'K' in df["views"]:
        views = float(df["views"].split('K')[0]) * 1000
        return views

    elif 'M' in df["views"]:
        views = float(df["views"].split('M')[0]) * 1000000

    else:
        views = df["views"].split()[0]

    return views

def get_ychannel_info(curl,surl):
    channel_url = curl
    search_url = surl
    viedo_count = int(get_videos_count(search_url).replace(",","")) 

    # Open chrome in headless mode and scroll down videos page
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get(channel_url)

    # Scroll down
    scroll = viedo_count // 30 
    for _ in range (scroll):
        driver.find_element_by_tag_name("body").send_keys(Keys.END)
        time.sleep(1)

    # Get page source
    html = driver.page_source

    # Get channle title 
    youtube_title = driver.title

    # Use BeautifulSoup to extract the data
    soup = BeautifulSoup(html,"html.parser")
    videos = soup.find_all("div", {"id":"dismissible"})
    videos_lst = []
    for video in videos:
        video_dict = {}
        video_dict["title"] = video.find("a", {"id":"video-title"}).text
        video_dict["url"] = "https://www.youtube.com/" + video.find("a", {"id":"video-title"})["href"]
        meta_data = video.find("div", {"id":"metadata-line"}).find_all("span")
        video_dict["views"] = meta_data[0].text
        video_dict["age"] = meta_data[1].text
        videos_lst.append(video_dict)

    # Save videos list to data frame
    df = pd.DataFrame(videos_lst)

    # Get ecah video details
    videos_details = get_video_info(df)
  
    # zip [videos_lst] and [videos_details] list into [final_lst]
    final_lst = []
    for video, detail in zip(videos_lst, videos_details):
        final_ouput  = {**video, **detail}
        final_lst.append(final_ouput)
    
    # Save result to data frame
    df = pd.DataFrame(final_lst)
    

    # Add new row to the data farme [clean_views]
    df["clean_views"] = df.apply(convert_views, axis = 1)
    df["clean_views"] = df["clean_views"].astype(int)
    
    # Save DataFrame to csv file 
    df.to_csv (f"{youtube_title}.csv", index = False, encoding = "utf-8-sig")
   
    driver.quit()

def get_video_info (df):
    # opne eaech video url and extract data using pafy
    video_details = []
    for url in df["url"]:
        video_dict = {}
        print (url)
        # instant created
        video = pafy.new(url)
        # getting number of likes
        video_dict["likes"] = video.likes
        video_dict["dislikes"] = video.dislikes
        # showing likes
        video_details.append(video_dict)
        
    return video_details

def get_videos_count(url):
    # Open chrome in headless mode and get video count the channel 
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get(url)
    page = driver.page_source
    soup = BeautifulSoup(page,"html.parser")
    video_count = str(soup.find("span",{"id":"video-count"}).text.split()[0])
    driver.quit()
    return video_count


# Main 
channel_url = "https://www.youtube.com/c/MakeDataUseful/videos"
search_url = "https://www.youtube.com/results?search_query=Make+Data+Useful"
get_ychannel_info(channel_url, search_url)
print("Done!")

