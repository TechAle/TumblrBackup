import utils.requestsUtils as requestUtils
import json
from datetime import datetime

class tumblrClass:
    def __init__(self, blogName, checkNotes):
        self.nextPercentage = None
        self.API_TOKEN = ""
        self.posts = []
        self.links = {
            "mainPage": "https://www.tumblr.com/" + blogName,
            "info": f"https://www.tumblr.com/api/v2/blog/{blogName}/info?fields[blogs]=total_posts,created,description,ask_page_title,title,top_tags,uuid,?linked_accounts,avatar,theme",
            "notes": "https://www.tumblr.com/api/v2/blog/[ID_BLOG]/post/[ID_POST]/notes/timeline?mode=[MODE]&sort=asc&pin_preview_note=false&fields[blogs]=name", # replies, reblogs_with_comments
            "posts": f"https://www.tumblr.com/api/v2/blog/{blogName}/posts?fields%5Bblogs%5D=name" # &page_number={PAGE_NUMBER}
        }
        self.checkNotes = checkNotes
        self.blogName = blogName

    '''
        @:return true if we can start getting informations
    '''
    def prepareRunning(self) -> bool:
        mainPage = requestUtils.makeRequest(self.links["mainPage"])
        if 200 <= mainPage.status_code <= 299:
            self.nextPercentage = 0
            tempVar = mainPage.text
            tempVar = tempVar[tempVar.index("API_TOKEN") + "API_TOKEN':'".__len__():]
            self.API_TOKEN = tempVar[:tempVar.index('"')]
            return True
        return False

    '''
        This get every informations from the api
    '''
    def getInformations(self):
        self.getInfoBlog()
        self.getPosts()

    def getInfoBlog(self):
        info = requestUtils.makeRequest(
            url=self.links["info"],
            header={
                "Authorization": "Bearer " + self.API_TOKEN
            }
        )
        info = json.loads(info.content)["response"]["blog"]
        self.totalPosts = info["total_posts"]
        self.created = info["created"]
        self.description = info["description"]
        self.askPage = info["ask_page_title"]
        self.title = info["title"]
        self.tags = info["top_tags"]
        self.uuid = info["uuid"]
        self.links["notes"] = self.links["notes"].replace("[ID_BLOG]", self.uuid)
        self.linkedAccounts = info["linked_accounts"]
        self.avatar = info["avatar"][0]["url"]
        self.background = info["theme"]["header_image"]
        self.backColor = info["theme"]["background_color"]
        self.textColor = info["theme"]["title_color"]

    def getPosts(self, pageNumber = "", numIterations = 0):
        info = requestUtils.makeRequest(
            url=self.links["posts"] + ("" if pageNumber.__len__() == 0 else "&page_number=" + pageNumber),
            header={
                "Authorization": "Bearer " + self.API_TOKEN
            }
        )
        info = json.loads(info.content)["response"]

        for post in info["posts"]:
            if self.checkNotes:
                if post["reply_count"] > 0:
                    post["replies"] = json.loads(requestUtils.makeRequest(
                        url=self.links["notes"].replace("[ID_POST]", post["id"]).replace("[MODE]", "replies"),
                        header={
                            "Authorization": "Bearer " + self.API_TOKEN
                        }
                    ).text)["response"]["timeline"]
            self.posts.append(post)

        if numIterations / self.totalPosts * 100 > self.nextPercentage:
            print(f"{numIterations / self.totalPosts * 100}: {numIterations}/{self.totalPosts}")
            self.nextPercentage += self.totalPosts / 100

        if info.__contains__("_links"):
            self.getPosts(
                pageNumber=info["_links"]["next"]["query_params"]["page_number"],
                numIterations=numIterations+info["posts"].__len__()
            )

    def createMessage(self, content):
        toAdd = ""
        if content["type"] == "image":
            toAdd += f'<img src="{content["media"][0]["url"]}" class="tumblrImage"/>'
        elif content["type"] == "text":
            toAdd += f'<div>{content["text"]}</div>'
        elif content["type"] == "poll":
            toAdd += "<div>"
            toAdd += f"Domanda: {content['question']}"
            for answer in content["answers"]:
                toAdd += f'<button class="buttonResult">{answer["answer_text"]}</button>'
            toAdd += "</div>"
        elif content["type"] == "link":
            toAdd += f'<div><a href="{content["url"]}">{content["display_url"]}</a></div>'
        return toAdd

    '''
        Return somekind of output
    '''
    def getOutput(self):
        kindPost = {
            "image",
            "text",
            "poll",
            "link"
        }
        output = ""
        with open("template.html", "r") as f:
            output = f.read()
            f.close()

        totalLikes = 0
        totalReblogs = 0
        totalComments = 0
        body = ""
        for post in self.posts:
            toAdd = "<div class='post'>"
            totalLikes += post["like_count"]
            totalReblogs += post["reblog_count"]
            totalComments += post["reply_count"]
            for content in post["content"]:
                if not kindPost.__contains__(content["type"]):
                    kindPost.add(content["type"])
                toAdd += self.createMessage(content)
            toAdd += f"<div>Likes: {post['like_count']} Reblogs: {post['reblog_count']} Comments: {post['reply_count']}</div>"
            if post["reply_count"] > 0:
                if post.__contains__("replies"):
                    if post["replies"]["elements"].__len__() > 0:
                        toAdd += "<div>Replies:"
                        for reblog in post["replies"]["elements"]:
                            toAdd += f"<br>{reblog['blog']['name']}"
                            for content1 in reblog["content"]:
                                toAdd += self.createMessage(content1)
                        toAdd += "</div>"
            toAdd += f"<div>Tags: {post['tags']}</div>"
            toAdd += "</div>"
            body += toAdd

        output = self.replaceStaticValues(output, totalLikes, totalReblogs, totalComments, body)
        with open(f"{self.blogName}.html", "w") as f:
            f.write(output)
            f.close()

    '''
                    <div class="post">
                    <div class="pinnedPost">
                        Post fissati in alto
                    </div>
                    <div class="reblog">
                        Autore <span class="reblogSymbol"><-> Chi</span>
                    </div>
                    <div class="autore">
                        Nome autore
                    </div>
                    <img src="img/alt.jpg" class="tumblrImage"/>
                    <button class="buttonResult">test</button>
                </div>

    '''

    def replaceStaticValues(self, html, totalLikes, totalReblogs, totalComments, body) -> str:
        return html.replace("{TITLE}", self.title)\
                .replace("{BACK_COLOR}", self.backColor)\
                .replace("{TEXT_COLOR}", self.textColor)\
                .replace("{ASK}", self.askPage)\
                .replace("{BACK_IMAGE}", self.background)\
                .replace("{ALT_IMAGE}", self.avatar)\
                .replace("{TAGS}", self.tags.__str__())\
                .replace("{ACCOUNTS}", self.linkedAccounts.__str__())\
                .replace("{POSTS}", str(self.totalPosts))\
                .replace("{LIKES}", str(totalLikes))\
                .replace("{REBLOGS}", str(totalReblogs))\
                .replace("{COMMENTS}", str(totalComments))\
                .replace("{NOTES}", str(totalLikes + totalReblogs + totalComments))\
                .replace("{CREATED}", datetime.fromtimestamp(self.created).__str__())\
                .replace("{BODY_NOW}", body)\
                .replace("{DESCRIPTION}", self.description)
