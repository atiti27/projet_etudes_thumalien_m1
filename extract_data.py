import re
import spacy
from clean_data import filter_by_language, filter_short_text, normalize_data, lemmatization_text


# Function to clean text
def clean_text(text):
    try:
        return text.encode('utf-8', 'ignore').decode('utf-8')
    except Exception as e:
        print(f"Error cleaning text: {e}")
        return text

def extract_data_from_post(post, client):
    uri = post.post.uri
    res_post = client.app.bsky.feed.get_post_thread({"uri": uri})
    post_details = res_post.thread.post
    record = post_details.record
    content = record.text.replace("\n", " ")
    isFrench = filter_by_language(content)
    if not isFrench:
        return None
    isLong = filter_short_text(content)
    if not isLong:
        return None
    normalize = normalize_data(content)
    clean_content = lemmatization_text(normalize)
    author = post_details.author.display_name
    publi_date = record.created_at
    comments = res_post.thread.replies

    # Extract hashtags using regex
    hashtags = re.findall(r"#\w+", content, re.UNICODE)
    hashtags = " ".join(hashtags) if hashtags else "None"

    # Retrieve post metrics
    nb_like = post_details.like_count
    nb_comment = post_details.reply_count
    nb_repost = post_details.repost_count
    title = record.embed.external.title if hasattr(record.embed, 'external') else "None"

    return {
        "title": title,
        "content": clean_content,
        "author": author,
        "publi_date": publi_date,
        "link": uri,
        "nbr_like": nb_like,
        "nbr_comment": nb_comment,
        "nbr_repost": nb_repost,
        "hashtags": hashtags,
        "comments": comments
    }

def extract_comment_from_post(comment):
    author = comment.post.author.display_name
    reply_record = comment.post.record
    reply = reply_record.text.replace("\n", " ")
    link = comment.post.uri
    publi_date = reply_record.created_at
    nbr_like = comment.post.like_count
    nbr_comment = comment.post.reply_count
    nbr_repost = comment.post.repost_count

    return {
        "content": reply,
        "author": author,
        "publi_date": publi_date,
        "link": link,
        "nbr_like": nbr_like,
        "nbr_comment": nbr_comment,
        "nbr_repost": nbr_repost
    }