import os
import time
from utils.browser import Browser
from utils.captcha import get_captcha_code
from config import ACCOUNT,PASSWORD,PROXY,USER_AGENT
from nb_log import get_logger
logger = get_logger(__name__)


def main():

    """
    如果你已经再手机APP登陆过，后续网页新设备登陆就需要短信验证码；
    那么请在这里允许一次登陆，将会把你的数据自动保存到data文件夹中，
    后续运行run.py时，会自动读取data文件夹中的数据，不会弹出验证码。
    """

    browser = Browser(data_path=os.path.join(os.getcwd(), "data"))
    page = browser.get_page()
    page.get("https://pc.ctyun.cn")
    page.listen.start('desk.ctyun.cn:8810/api/desktop/client/pageDesktop')
    response = page.listen.wait(timeout=300)
    login_info = response._raw_body
    logger.info(f"登录信息: {response._raw_body}")

    if "云电脑租户" in login_info:
        logger.info(f"登录成功！浏览器数据已经保存到:{os.path.join(os.getcwd(), 'data')}")
        # browser.save_data()
    else:
        logger.error("登录失败！")
        return False


if __name__ == "__main__":
    main()
