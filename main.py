from structure.TumblrClass import tumblrClass
'''
Main page:
    - https://www.tumblr.com/{BLOG}
    - Autorizzazione: API_TOKEN
Info:
    - https://www.tumblr.com/api/v2/blog/{BLOG}/info?fields%5Bblogs%5D=%3Ftotal_posts,%3Fcreated,%3Fask_page_title,%3Favatar,%3Ftheme,%3Ftitle,%3Ftop_tags,%3Fuuid,%3Flinked_accounts
    - Autorizzazione
Posts:
    - https://www.tumblr.com/api/v2/blog/{BLOG}/posts?fields%5Bblogs%5D=name&page_number={PAGE_NUMBER}
    - Autorizzazione
'''

blogName = ""
checkNotes = False

def main():
    tumblr = tumblrClass(blogName, checkNotes)
    if not tumblr.prepareRunning():
        return
    tumblr.getInformations()
    tumblr.getOutput()


if __name__ == "__main__":
    main()
