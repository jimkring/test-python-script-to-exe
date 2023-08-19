import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import easyocr
import string
import concurrent.futures
import tkinter as tk
import threading
from pathlib import Path
from PIL import Image
import numpy as np

def make_address():
    json_data = {
        'city': '',
        'path': '/cn-address',
        'method': 'refresh',
    }

    response = requests.post('https://www.meiguodizhi.com/api/v1/dz', json=json_data)

    data = response.json()
    # print(data)
    street = data['address']['Address']
    city = data['address']['City']
    province = data['address']['State']
    area = data['address']['xian']
    name = data['address']['Full_Name']
    phone = data['address']['Telephone'][4:]

    # print(province, city, area, street, name, phone)
    return province, city, area, street, name, phone


province, city, area, street, name, phone = make_address()


def ocr(name):
    reader = easyocr.Reader(['ch_sim'])
    image = np.array(Image.open(name))
    results = reader.readtext(image)
    captcha_text = results[0][1] if results else "未能识别"

    print("识别结果:", captcha_text)

    # 判断识别结果中是否同时含有数字和其他字符
    if any(char.isdigit() for char in captcha_text) and any(not char.isdigit() for char in captcha_text):
        # 提取识别结果中的数字字符
        numbers = [char for char in captcha_text if char.isdigit()]

        # 判断是否有足够的数字字符进行计算
        if len(numbers) >= 4:
            # 使用字符串切片操作提取前两位数字和后两位数字
            first_two_digits = int(''.join(numbers[:2]))
            last_two_digits = int(''.join(numbers[-2:]))

            # 计算前两位数字和后两位数字的和
            captcha_text = first_two_digits + last_two_digits

            print(f"前两位数字和后两位数字的和为: {captcha_text}")
    else:
        print("识别结果不含数字")
    return captcha_text


# 生成代理
def get_proxy():
    # url = 'https://bapi.51daili.com/getapi2?linePoolIndex=1&packid=2&unkey=&tid=&qty=1&time=1&port=1&format=txt&ss=1&css=&pro=&city=&dt=3&ct=1&service=1&usertype=17&accessName=soar&accessPassword=08298D06FB363A0C471AE4CAE18A0435'
    url = 'https://bapi.51daili.com/getapi2?linePoolIndex=1&packid=2&unkey=&tid=&qty=1&time=1&port=1&format=txt&ss=1&css=&pro=&city=&dt=3&ct=0&service=1&usertype=17'
    resp = requests.get(url=url)
    proxy = resp.text
    print(proxy)
    return proxy


# 生成随机名字
def generate_random_name():
    letters = string.ascii_lowercase
    name = ''.join(random.choice(letters) for _ in range(8)) + '.png'
    return name


# 删除图片
def delete_image(name):
    path = Path(name)
    if path.exists():
        path.unlink()
        print(f"删除图片: {name}")
    else:
        print(f"图片 {name} 不存在")


def calculate_window_position(window_size, col_num, row_num):
    x = col_num * window_size[0]
    y = row_num * window_size[1]
    return x, y


def job(thread_num):
    # 代理设置

    max_retries = 3  # 最大重试次数
    retries = 0

    while retries < max_retries:
        PROXY = get_proxy()
        if PROXY:
            break
        else:
            retries += 1
            print(f"第{retries}次获取代理失败，等待5秒后重试...")
            time.sleep(5)

    options = webdriver.ChromeOptions()
    options.add_experimental_option('detach', True)
    # options.add_argument('--headless')  # 启用无头模式
    options.add_argument('--proxy-server=%s' % PROXY)
    driver = webdriver.Chrome(options=options)
    try:
        col_num = thread_num % 3  # 每行3个窗口
        row_num = thread_num // 3
        window_position = calculate_window_position(window_size, col_num, row_num)
        driver.set_window_position(*window_position)
        driver.set_window_size(*window_size)

        # 打开网站
        driver.get("http://buy.tjjntw.org.cn/wfdata/item/f8ed5d21a44b0e58.html")

        # 设置最长等待时间
        wait_time = 5

        # 使用WebDriverWait等待验证码加载，超时时间为wait_time秒
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.ID, 'wfvcode'))
        )

        # 选择产品
        products = ['wfproduct1', 'wfproduct2', 'wfproduct3']
        selected_product = random.choice(products)
        product_radio = driver.find_element(By.ID, selected_product)
        product_radio.click()

        # 填写信息
        province, city, area, street, name, phone = make_address()

        driver.find_element(By.NAME, "wfname").send_keys(name)
        driver.find_element(By.NAME, "wfmob").send_keys(phone)
        driver.find_element(By.ID, "wfprovince").send_keys(province)
        driver.find_element(By.ID, "wfcity").send_keys(city)
        driver.find_element(By.ID, "wfarea").send_keys(area)
        driver.find_element(By.NAME, "wfaddress").send_keys(street)

        name = generate_random_name()
        # 找到要截图的元素并进行截图
        element = driver.find_element(By.ID, 'wfvcode')
        element.screenshot(name)

        captcha_text = ocr(name)
        if not captcha_text:
            return
        driver.find_element(By.NAME, "wfvcode").send_keys(captcha_text)
        delete_image(name)

        # 点击提交
        button = driver.find_element(By.ID, 'wfsubmit')
        driver.execute_script("arguments[0].click();", button)
        time.sleep(5)
        print('*' * 10, driver.title, '*' * 10)

        # time.sleep(30)
        driver.quit()


    except Exception as e:
        print(e)
    finally:
        if driver:
            driver.quit()


window_size = (800, 600)
# 全局变量，用于控制任务执行状态
running = False


def start_jobs():
    global running
    running = True
    num_tasks = int(num_tasks_entry.get())  # 获取文本框中的任务数量
    interval = float(interval_entry.get())  # 获取文本框中的间隔时间
    while running:
        thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=num_tasks)
        futures = [thread_pool.submit(job, i) for i in range(num_tasks)]
        concurrent.futures.wait(futures)
        time.sleep(interval)  # 在每次执行之后等待指定的间隔时间


def stop_jobs():
    global running
    running = False


def start_jobs_in_thread():
    thread = threading.Thread(target=start_jobs)
    thread.start()


# 创建主窗口
root = tk.Tk()
root.title("Job Executor")

# 添加任务数量输入框和标签
num_tasks_label = tk.Label(root, text="Enter the number of tasks:")
num_tasks_label.pack(pady=10)

num_tasks_entry = tk.Entry(root)
num_tasks_entry.pack(pady=5)

# 添加间隔时间输入框和标签
interval_label = tk.Label(root, text="Enter the interval time (seconds):")
interval_label.pack(pady=10)

interval_entry = tk.Entry(root)
interval_entry.pack(pady=5)

# 创建开始按钮
start_button = tk.Button(root, text="Start Jobs", command=start_jobs_in_thread)
start_button.pack(pady=10)

# 创建停止按钮
stop_button = tk.Button(root, text="Stop Jobs", command=stop_jobs)
stop_button.pack(pady=5)

# 启动主事件循环
root.mainloop()
