from playwright.sync_api import sync_playwright
from playwright.sync_api import ViewportSize, sync_playwright
import random
from PIL import Image
# Define the URL and the text you want to replace

W = 1920
H = 1080


reddit_object = {
    "thread_url": "https://www.quora.com/How-can-I-copy-a-whole-webpage-all-of-the-code",
    "thread_title": "外国人看中国",
    "thread_id": "abcdef",
    "is_nsfw": False,
    "comments": [
        {
            "comment_body": "韩国网友：火锅是我们发明的",
            "comment_body_en": "Hotpot is something we Koreans invented.",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/123456",
            "comment_id": "123456"
        },
        {
            "comment_body": "英国网友：这给我的感觉就是特别辣",
            "comment_body_en": "To me, this feels especially spicy.",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/234567",
            "comment_id": "234567"
        },
        {
            "comment_body": "预测式外呼针对任务中已分配名单进行外呼，并不针对未分配名单。",
            "comment_body_en": "Predictive dialing makes outbound calls to lists already assigned to tasks, not unassigned lists.",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/345678",
            "comment_id": "345678"
        },
        {
            "comment_body": "支持配置并发数量（业内大概是接通率30%的情况下,1坐席配2.5-3并发）",
            "comment_body_en": "Concurrency can be configured, with roughly 1 agent handling 2.5-3 concurrent calls at a 30% connection rate.",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/456789",
            "comment_id": "456789"
        },
        {
            "comment_body": "支持配置空闲时间，即当前通话结束后可设置",
            "comment_body_en": "Support for configuring idle time, allowing it to be set after the current call ends.",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/567890",
            "comment_id": "567890"
        },
        {
            "comment_body": "Keep up the good work, everyone!",
            "comment_body_en": "Great job, everyone!",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/678901",
            "comment_id": "678901"
        },
        {
            "comment_body": "Ray is the best!",
            "comment_body_en": "Ray is awesome!",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/789012",
            "comment_id": "789012"
        },
        {
            "comment_body": "I love participating in this community!",
            "comment_body_en": "I enjoy being part of this community!",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/890123",
            "comment_id": "890123"
        },
        {
            "comment_body": "Great thread, keep it up!",
            "comment_body_en": "This thread is fantastic, keep it going!",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/901234",
            "comment_id": "901234"
        },
        {
            "comment_body": "This thread deserves more upvotes!",
            "comment_body_en": "This thread deserves more upvotes!",
            "comment_url": "https://reddit.com/r/test/abcdef/comment/012345",
            "comment_id": "012345"
        }
    ]
}

def take_screenshot(reddit_object):
    # Define the URL and the text you want to replace
    url = reddit_object["thread_url"]
    replacement_text = reddit_object["thread_title"]

    # Launch the browser (Playwright supports multiple browsers)
    with sync_playwright() as p:
        dsf = 2

        browser = p.chromium.launch(
            # '/Users/macbook/Library/Application Support/Google/Chrome',
            headless=False
        ) 

        context = browser.new_context(
            locale="en-us",
            # color_scheme="dark",
            viewport=ViewportSize(width=W, height=H),
            device_scale_factor=dsf,
        )

        page = context.new_page()
        page.set_default_timeout(0)
        page.set_default_navigation_timeout(0)

        # Open the URL
        page.goto(url)
        page.set_viewport_size(ViewportSize(width=1920, height=1080))
        page.wait_for_load_state()
        page.wait_for_timeout(5000)  # 等待5秒

        # Replace the specified CSS selector with reddit_object['thread_title']
        page.evaluate(f"""
            const element = document.querySelector("#mainContent > div.q-box.qu-borderAll.qu-borderRadius--small.qu-borderColor--raised.qu-boxShadow--small.qu-bg--raised > div > div > span > span > div > div > div > span");
            element.innerText = '{reddit_object["thread_title"]}';
        """)

        print("now title screenshoting")

        # Take a screenshot of the specific element (title)
        element = page.query_selector("#mainContent > div.q-box.qu-borderAll.qu-borderRadius--small.qu-borderColor--raised.qu-boxShadow--small.qu-bg--raised > div")
        reddit_id = reddit_object["thread_id"]
        screenshot_path = f"assets/temp/{reddit_id}/png/title.png"
        element.screenshot(path=screenshot_path)



        # 为了加载更多内容，模拟滚动到页面底部
        # for _ in range(1):
        #     print("滚动到页面底部...")
        #     page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        #     print("等待5秒...")
        #     page.wait_for_timeout(15000)  # 等待5秒



        # 获取页面中所有包含 dom_annotate_question_answer_item_ 的元素
        container_elements = page.query_selector_all('[class*=dom_annotate_question_answer_item_]')
        print("找到的容器元素数量：", len(container_elements))

        # for container in container_elements:
        #     class_list = container.get_attribute('class').split()
        #     print("容器元素类名：", class_list)

        # 过滤只包含 .q-image 子元素的元素
        q_image_containers = [container for container in container_elements if container.query_selector(".q-image")]
        print("符合条件的容器元素数量：", len(q_image_containers))


        for idx, comment in enumerate(reddit_object["comments"]):
            print("正在截取评论 " )
            print(idx)
            comment_body_en = comment.get("comment_body_en", "")
            
            # 如果没有符合条件的容器元素，跳过该评论
            if not q_image_containers:
                print("没有符合条件的容器元素，跳过该评论")
                continue
            
            # 随机选择一个容器元素
            container_element = random.choice(q_image_containers)
            class_list = container_element.get_attribute('class').split()
            class_selector = '.' + ', .'.join(class_list)
            print("容器元素类名：", class_selector)

            # Assume you have a CSS class named "replaced-comment" defined in your external CSS file
            # with the desired styles for the replaced content
            # replaced_comment_class = 'replaced-comment'

            # page.evaluate(f"""
            #     const containerElement = document.querySelector("{class_selector}");
            #     if (containerElement) {{
            #         // Find the element containing the comment text
            #         const commentElement = containerElement.querySelector(".qu-userSelect--text");
            #         console.log(commentElement)
            #         if (commentElement) {{
            #             // Remove existing content
            #             commentElement.innerHTML = '{comment_body_en}';
            #         }}
            #     }}
            # """)

            page.evaluate(f"""
                const containerElement = document.querySelector("{class_selector}");
                if (containerElement) {{
                    // Find the element containing the comment text
                    const commentElement = containerElement.querySelector(".qu-wordBreak--break-word");
                    console.log(commentElement)
                    if (commentElement) {{
                        // Remove existing content
                        commentElement.innerHTML = ''; // Remove all children
                        // Create a new span element
                        const newSpan = document.createElement('span');
                        // Append the new span element to the comment element
                        commentElement.appendChild(newSpan);
                        // Now you can further manipulate the new span element as needed
                    }}
                }}
            """)




            page.wait_for_timeout(5000)  # 等待5秒
            # 截取容器元素的屏幕截图
            comment_screenshot_path = f"assets/temp/{reddit_id}/png/comment_title_{idx}.png"
            print("正在截取评论的屏幕截图...")
            container_element.query_selector(".spacing_log_answer_header").screenshot(path=comment_screenshot_path)


            print("now title screenshoting")

            # Take a screenshot of the specific element (title)
            element = page.query_selector("#mainContent > div.q-box.qu-borderAll.qu-borderRadius--small.qu-borderColor--raised.qu-boxShadow--small.qu-bg--raised > div")
            reddit_id = reddit_object["thread_id"]
            screenshot_path = f"assets/temp/{reddit_id}/png/comment_content_{idx}.png"
            element.screenshot(path=screenshot_path)
            



            # 打开两个截图文件
            image1 = Image.open(f"assets/temp/{reddit_id}/png/comment_title_{idx}.png")
            image2 = Image.open(f"assets/temp/{reddit_id}/png/comment_content_{idx}.png")

            # 获取两个图片的尺寸
            width1, height1 = image1.size
            width2, height2 = image2.size

            # 创建一个新的图片，宽度为两个图片宽度的最大值，高度为两个图片高度的总和
            new_width = max(width1, width2)
            new_height = height1 + height2
            new_image = Image.new("RGB", (new_width, new_height), color="white")

            # 将第一个图片粘贴到新图片的顶部
            new_image.paste(image1, (0, 0))

            # 将第二个图片粘贴到新图片的底部
            new_image.paste(image2, (0, height1))

            # 保存新图片
            new_image_path = f"assets/temp/{reddit_id}/png/comment_{idx}.png"
            new_image.save(new_image_path)

            print("合并后的图片已保存为:", new_image_path)


            print("完成！")




        
        # Close the browser
        browser.close()

take_screenshot(reddit_object)
