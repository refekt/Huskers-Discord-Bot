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

test_2 = {
    "attachments": {},
    "author_id": "15899943",
    "context_annotations": [
        {
            "domain": {
                "id": "46",
                "name": "Brand Category",
                "description": "Categories within Brand Verticals that narrow down the scope of Brands",
            },
            "entity": {"id": "781974596752842752", "name": "Services"},
        },
        {
            "domain": {
                "id": "47",
                "name": "Brand",
                "description": "Brands and Companies",
            },
            "entity": {"id": "10045225402", "name": "Twitter"},
        },
    ],
    "conversation_id": "1533095338705289216",
    "created_at": "2022-06-04T14:36:26.000Z",
    "entities": {
        "urls": [
            {
                "start": 53,
                "end": 76,
                "url": "https://t.co/5csNvIlRFK",
                "expanded_url": "https://google.com",
                "display_url": "google.com",
                "status": 200,
                "title": "Google",
                "description": "Search the world's information, including webpages, images, videos and more. Google has many special features to help you find exactly what you're looking for.",
                "unwound_url": "https://www.google.com/",
            },
            {
                "start": 77,
                "end": 100,
                "url": "https://t.co/MVVdTA7Bvf",
                "expanded_url": "https://yahoo.com",
                "display_url": "yahoo.com",
                "images": [
                    {
                        "url": "https://pbs.twimg.com/news_img/1531799350120448000/jh2TO-QT?format=png&name=orig",
                        "width": 500,
                        "height": 500,
                    },
                    {
                        "url": "https://pbs.twimg.com/news_img/1531799350120448000/jh2TO-QT?format=png&name=150x150",
                        "width": 150,
                        "height": 150,
                    },
                ],
                "status": 200,
                "title": "Yahoo | Mail, Weather, Search, Politics, News, Finance, Sports & Videos",
                "description": "Latest news coverage, email, free stock quotes, live scores and video are just the beginning. Discover more every day at Yahoo!",
                "unwound_url": "https://www.yahoo.com/",
            },
            {
                "start": 101,
                "end": 124,
                "url": "https://t.co/70oQ1m6IsN",
                "expanded_url": "https://bing.com",
                "display_url": "bing.com",
                "status": 200,
                "title": "The beauty that lies below",
                "description": "Marovo Lagoon in the Solomon Islands is the larges",
                "unwound_url": "https://www.bing.com/?toWww=1&redig=17CEBFF75CE44970A26DED98D0DDA3D3",
            },
        ]
    },
    "geo": {},
    "id": "1533095338705289216",
    "lang": "tr",
    "possibly_sensitive": False,
    "public_metrics": {
        "retweet_count": 0,
        "reply_count": 0,
        "like_count": 0,
        "quote_count": 0,
    },
    "reply_settings": "everyone",
    "source": "Twitter Web App",
    "text": "asdfasf sfsadfsafjsd;lkf Test of a tweet with links. https://t.co/5csNvIlRFK https://t.co/MVVdTA7Bvf https://t.co/70oQ1m6IsN",
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
