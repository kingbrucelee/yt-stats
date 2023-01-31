import pandas as pd
from googleapiclient.discovery import build
import datetime
from tqdm import tqdm

# Set up the API client
api_key = "YOUR_API_KEY"
youtube = build("youtube", "v3", developerKey=api_key)

# Define the playlist ID
playlist_id = "PLXXXXXXXXXXXXXXXXXXXXXXXX"

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
    for item in response["items"]:
        video_likes = item["statistics"].get("likeCount", 0)
        video_views = item["statistics"]["viewCount"]
        video_duration = item["contentDetails"]["duration"]
        video_comments = item["statistics"].get("commentCount", 0)
        video_link = f"https://www.youtube.com/watch?v={item['id']}"
        video_data.append((videos[i][1], datetime.datetime.strptime(videos[i][2][:10], "%Y-%m-%d"), video_likes, video_views, video_duration, video_link, video_comments))
        i += 1

# Convert the video data to a pandas DataFrame
df = pd.DataFrame(video_data, columns=["Title", "Date", "Likes", "Views", "Duration", "Link", "Comments"])

# Write the DataFrame to an Excel spreadsheet
df.to_excel("y.xlsx", index=False)
