import os
import time
from utils.browser import Browser
from utils.captcha import get_captcha_code
from config import ACCOUNT, ALIVE_SECOND, INTERVAL_MINUTE, PASSWORD, PROXY, USER_AGENT, TARGETS
from nb_log import get_logger

logger = get_logger(__name__)


def key_alive(page):
    page.wait(3)
    pc_counts = len(page.eles(".desktopcom-item-main"))
    to_open_target = []
    # 默认全部打开
    if len(TARGETS) == 1 and TARGETS[0] == -1:
        to_open_target = [i for i in range(pc_counts)]
    # 只打开指定的云电脑
    else:
        to_open_target = [i for i in range(pc_counts) if i + 1 in TARGETS]

    for target in to_open_target:
        # 点击目标云电脑
        page.eles(".desktopcom-item-main")[target].click()
        if page.ele(".desktopcom-enter", timeout=10):
            logger.info(f"打开云电脑界面成功,开始保活第{target + 1}台云电脑...")
            page.ele(".desktopcom-enter").click()
            page.wait(ALIVE_SECOND)
            logger.info("第{}台云电脑保活完成！".format(target + 1))
        else:
            logger.error("打开云电脑界面失败,页面代码可能发生了变化！")
        # 返回云电脑列表页面
        page.back()
    return True


def login(page, account, proxy):
    if page.ele(".code", timeout=10):
        logger.info("检测到验证码！")
        code = get_captcha_code(account, proxy)
        page.ele(".code").input(code)
    page.listen.start('desk.ctyun.cn:8810/api/auth/client/login')
    page.ele(".:btn-submit-pc").click()
    response = page.listen.wait(timeout=5)
    login_info = response._raw_body
    logger.info(f"登录信息: {response._raw_body}")

    if "tenantName" in login_info:
        logger.info("登录成功！")
    elif "验证码错误" in login_info:
        logger.error("验证码错误！")
        return False
    elif "图形验证码错误" in login_info:
        logger.error("图形验证码错误")
        return False
    elif "请输入图形验证码" in login_info:
        logger.error("需要图形验证码")
        return False
    else:
        logger.error("登录失败！")
        return False

    return key_alive(page)


def main():
    account = ACCOUNT
    password = PASSWORD
    proxy = PROXY
    user_agent = USER_AGENT

    browser = Browser(proxy_server=proxy, user_agent=user_agent, data_path=os.path.join(os.getcwd(), "data"))
    page = browser.get_page()
    page.get("https://pc.ctyun.cn")

    if page.ele(".desktopcom-item-main", timeout=10):
        logger.info("已成功登陆！")
        key_alive(page)
    elif page.ele(".account", timeout=10):
        logger.info("页面打开成功！")
        page.ele(".account").click()
        page.ele(".account").input(account)
        page.ele(".password").input(password)
        for i in range(3):
            if login(page, account, proxy):
                break
    else:
        logger.error("页面打开失败,未检测到预期元素！")
    browser.quit()


if __name__ == "__main__":
    import schedule

    def job(retry=3):
        if retry <= 0:
            logger.error("保活任务运行失败！")
            return
        logger.info(f"开始保活任务，剩余重试次数: {retry}")
        try:
            main()
        except Exception as e:
            logger.exception(f"保活任务运行失败: {e}，剩余重试次数: {retry}")
            job(retry - 1)

    # 每45分钟运行一次
    schedule.every(INTERVAL_MINUTE).minutes.do(job)
    # 立即运行一次
    job()
    while True:
        schedule.run_pending()
        time.sleep(1)
