import os
import csv
import re
from atproto_client import Client
import dotenv

dotenv.load_dotenv()

user_name = os.getenv("USER")
password = os.getenv("PASSWORD")
did = os.getenv("DID")

client = Client()
client.login(user_name, password)

record_key_france = "aaafczzvnktbe"

# Construct public feed URI
public_feed_uri = f'at://{did}/app.bsky.feed.generator/{record_key_france}'
print(f"Public feed URI for French press: {public_feed_uri}")

# Function to clean text
def clean_text(text):
    try:
        return text.encode('utf-8', 'ignore').decode('utf-8')
    except Exception as e:
        print(f"Error cleaning text: {e}")
        return text

try:
    # Retrieve posts from the public feed
    response = client.app.bsky.feed.get_feed({
        "feed": public_feed_uri,
        "limit": 10
    })

    feed = response.feed
    print(f"Number of posts retrieved: {len(feed)}")

    # Open CSV file for writing
    with open("tweets.csv", "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Title", "Content", "Author", "Date", "Link", "Comments", "Likes", "Retweets", "Hashtags"])

        for post in feed:
            uri = post.post.uri

            # Fetch post details
            res = client.app.bsky.feed.get_post_thread({"uri": uri})
            post_details = res.thread.post
            author = clean_text(post_details.author.display_name)
            record = post_details.record
            publi_date = clean_text(record.created_at)
            text = clean_text(record.text.replace("\n", " "))

            # Extract hashtags using regex
            hashtags = re.findall(r"#\w+", text, re.UNICODE)
            hashtags = " ".join(hashtags) if hashtags else "None"

            # Retrieve post metrics
            try:
                stats = post_details.stats
                nbr_commentaire = getattr(stats, 'replies', 'Unavailable')
                nbr_like = getattr(stats, 'likes', 'Unavailable')
                nbr_retweet = getattr(stats, 'reposts', 'Unavailable')
            except AttributeError:
                nbr_commentaire = nbr_like = nbr_retweet = "Unavailable"

            # Check for an external link to retrieve title
            title = ""
            if hasattr(record, "embed") and hasattr(record.embed, "external"):
                title = clean_text(record.embed.external.title)

            # Save post details in CSV
            try:
                writer.writerow([title, text, author, publi_date, uri, nbr_commentaire, nbr_like, nbr_retweet, hashtags])
            except UnicodeEncodeError as e:
                print(f"Encoding error for post {uri}: {e}. Skipping...")

    print("✅ Tweets successfully saved in tweets.csv")

except Exception as e:
    print(f"Error retrieving feed: {e}")