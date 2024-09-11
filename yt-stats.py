import pandas as pd
from googleapiclient.discovery import build
import datetime
from tqdm import tqdm
import time
import requests
import isodate # Important for parsing IS0 8601 format of storing time
# Set up the API client
api_key = "YOUR_API_KEY"
youtube = build("youtube", "v3", developerKey=api_key)

# Define the playlist ID
playlist_id = "PLAYLIST_ID"

# Get all videos from the playlist
videos = []
next_page_token = None
while True:
    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=50,
        pageToken=next_page_token,
        playlistId=playlist_id
    )
    response = request.execute()

    # Get the video IDs and metadata from the response
    for item in response["items"]:
        video_id = item["snippet"]["resourceId"]["videoId"]
        video_title = item["snippet"]["title"]
        video_date = item["snippet"]["publishedAt"]
        videos.append((video_id, video_title, video_date))

    # Get the next page token
    next_page_token = response.get("nextPageToken")

    # If there are no more pages, break out of the loop
    if next_page_token is None:
        break

# Get the video statistics and details for all videos
video_data = []
for i in tqdm(range(0, len(videos), 50), desc="Getting video data"):
    video_ids = ",".join([video[0] for video in videos[i:i+50]])
    request = youtube.videos().list(
        part="statistics, contentDetails",
        id=video_ids
    )
    response = request.execute()
    # Get the data for each video
    # Attempt to make a clever way of handling API limits of 100 requests per minute
    #t0 = time.perf_counter()
    for item in response["items"]:
        video_likes = item["statistics"].get("likeCount", 0)
        video_views = item["statistics"]["viewCount"]
        video_duration = isodate.parse_duration(item["contentDetails"]["duration"]).seconds
        video_comments = item["statistics"].get("commentCount", 0)
        video_link = f"https://www.youtube.com/watch?v={item['id']}"
        time.sleep(0.4) 
        r = requests.get(f"https://returnyoutubedislikeapi.com/votes?videoId={item['id']}").json()
        video_data.append((videos[i][1], isodate.parse_datetime(videos[i][2]).date(), isodate.parse_datetime(videos[i][2]).time(), video_likes, video_views, video_duration // 60, video_duration % 60, video_link, video_comments, r['likes'], r['dislikes'], r['rawLikes'], r['rawDislikes'], r['rating']))
        i += 1
    #t1 = time.perf_counter()
    #print(t1-t0)
    #if t1-t0 < 35:
    #    time.sleep(35-(t1-t0))

# Convert the video data to a pandas DataFrame
# TODO Currently films over 1 hour will have more than 60 in "minutes". In other words there's no Duration_Hours field 
df = pd.DataFrame(video_data, columns=["Title", "Date", "Time", "Likes", "Views", "Duration_Minutes", "Duration_Seconds", "Link", "Comments", 'RD_Current_Likes', 'RD_Extrapolated_Dislikes','RD_Recorded_Likes','RD_Recorded_Dislikes', 'RD_Rating'])

# Write the DataFrame to an Excel spreadsheet
df.to_excel("file_name.xlsx", index=False)
