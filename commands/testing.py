tweet = {
    "data": {
        "attachments": {},
        "author_id": "15899943",
        "conversation_id": "1533075589841702912",
        "created_at": "2022-06-04T13:17:58.000Z",
        "entities": {},
        "geo": {},
        "id": "1533075589841702912",
        "lang": "et",
        "possibly_sensitive": False,
        "public_metrics": {
            "retweet_count": 0,
            "reply_count": 0,
            "like_count": 0,
            "quote_count": 0,
        },
        "reply_settings": "everyone",
        "source": "Twitter Web App",
        "text": "test test",
    },
    "includes": {
        "users": [
            {
                "created_at": "2008-08-19T03:09:46.000Z",
                "description": "GBR",
                "id": "15899943",
                "name": "Aaron",
                "profile_image_url": "https://pbs.twimg.com/profile_images/1206047447451086848/GEMbd3wB_normal.jpg",
                "protected": False,
                "public_metrics": {
                    "followers_count": 39,
                    "following_count": 563,
                    "tweet_count": 1157,
                    "listed_count": 0,
                },
                "url": "",
                "username": "ayy_gbr",
                "verified": False,
            }
        ]
    },
    "matching_rules": [{"id": "1532102238562402312", "tag": ""}],
}


class TweetUserData(object):
    def __init__(self, data):
        self.profile_image_url = None
        self.name = None
        self.username = None
        for key in data:
            setattr(self, key, data[key])


class MyTweet(object):
    def __init__(self, tweet_data):
        self.data = None
        self.includes = None
        self.matching_rules = None

        for key in tweet_data:
            setattr(self, key, tweet_data[key])


if __name__ == "__main__":
    test = MyTweet(tweet)

    author = None
    print(type(test.includes["users"]))
    for user in test.includes["users"]:
        if test.data["author_id"] == user["id"]:
            author: TweetUserData = TweetUserData(user)
            break

    print(author)
