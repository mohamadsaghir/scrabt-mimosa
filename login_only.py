from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

ACTIVATION_URL = "https://start.mimosa.co/app/activation.html?jwt=YOUR_JWT_HERE&null#/"
FILE_PATH = r"C:\Users\moham\Desktop\m\serials1.txt"

USERNAME = "......"
PASSWORD = "....."

with open(FILE_PATH, "r", encoding="utf-8") as f:
    SERIALS = [
        s.strip().replace("–", "-").replace("—", "-")
        for s in f
        if s.strip() and s.count("-") == 2
    ]

print(f" Loaded {len(SERIALS)} serials")

options = webdriver.ChromeOptions()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9224")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 30)

print(" Connected to Chrome")


def ensure_logged_in():
    if "login" not in driver.current_url.lower():
        return

    print("🔐 Logging in...")
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))

    driver.execute_script("""
        const i = document.querySelectorAll("input");
        if (i.length >= 2) {
            i[0].value = arguments[0];
            i[0].dispatchEvent(new Event('input',{bubbles:true}));
            i[1].value = arguments[1];
            i[1].dispatchEvent(new Event('input',{bubbles:true}));
            document.querySelector("input.btn-submitWelcome")?.click();
        }
    """, USERNAME, PASSWORD)

    for _ in range(12):   # ~6 ثواني
        time.sleep(0.5)
        if "login" not in driver.current_url.lower():
            return

    print(" Login stuck → continue anyway")


def back_to_activation():
    driver.get(ACTIVATION_URL)
    time.sleep(1.5)
    ensure_logged_in()


def wait_serial():
    if "unlockcode" in driver.current_url.lower():
        back_to_activation()

    try:
        wait.until(EC.presence_of_element_located((By.NAME, "serialInput")))
        return True
    except TimeoutException:
        back_to_activation()
        return False


def inject_serial(serial):
    driver.execute_script("""
        const i = document.getElementsByName('serialInput')[0];
        if (i) {
            i.value = arguments[0];
            i.dispatchEvent(new Event('input',{bubbles:true}));
        }
    """, serial)

def submit_fast():
    driver.execute_script("""
        [...document.querySelectorAll("a")]
          .find(a => a.innerText.trim() === "Submit")?.click();
    """)


def remove_serial(serial):
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        for line in lines:
            if serial not in line:
                f.write(line)


def handle_result(serial):
    time.sleep(1.2)

    url = driver.current_url.lower()
    page = driver.page_source.lower()

    if "permission denied" in page:
        print(f"⚠️ DENIED → {serial}")
        back_to_activation()
        return

    if "unlockcode" in url:
        print(f"✅ VALID → {serial}")
        remove_serial(serial)
        back_to_activation()
        return

    print(f"❌ INVALID → {serial}")


driver.get(ACTIVATION_URL)
time.sleep(2)
ensure_logged_in()

for serial in SERIALS:
    print(f"[+] {serial}")

    if not wait_serial():
        print("⏭️ skip")
        continue

    inject_serial(serial)

    # PTP
    driver.execute_script("""
        const b = document.querySelector("a.dropdown-toggle");
        if (b && b.innerText.trim() !== "PTP") {
            b.click();
            setTimeout(() => {
                [...document.querySelectorAll("a")]
                    .find(a => a.innerText.trim() === "PTP")?.click();
            }, 150);
        }
    """)

    # checkboxes
    driver.execute_script("""
        document.querySelector("input[ng-model='licenseFlag']")?.click();
        document.querySelector("input[ng-model='EulaLicense']")?.click();
    """)

    submit_fast()
    handle_result(serial)

print("\n DONE — سريع، ثابت، ولا مرة بيعلق ")
