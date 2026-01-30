import time
import logging
import threading
import queue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FacebookBot:
    def __init__(self, headless=False):
        self.headless = headless
        self.options = Options()
        if self.headless:
            self.options.add_argument("--headless")

        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-notifications")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--start-maximized")
        # To avoid being detected as a bot easily
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = None

    def start_browser(self):
        """Starts the browser instance."""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            self.driver.set_page_load_timeout(60)
            return True
        except Exception as e:
            logging.error(f"Failed to start browser: {e}")
            return False

    def close_driver(self):
        """Closes the browser instance."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

    def process_number(self, phone_number, log_callback=None):
        """Processes a single number using the existing driver."""
        url = "https://www.facebook.com/login/identify/?ctx=recover&ars=facebook_login&from_login_screen=0"
        
        try:
            if log_callback: log_callback(f"Processing: {phone_number}...")
            self.driver.get(url)
            
            wait = WebDriverWait(self.driver, 20)
            
            # --- STEP 1: FIND INPUT FIELDS ---
            # User wants to avoid top bar input. We target the specific central input.
            # Central input often has id="identify_email" or placeholder="Email address or mobile number"
            email_input = None
            selectors = [
                 # Specific ID for the recovery box input
                 (By.ID, "identify_email"),
                 # Exact placeholder from user screenshot
                 (By.XPATH, "//input[@placeholder='Email address or mobile number']"),
                 # Fallback but excluding the top login bar (often has name='email' too but is inside a different form)
                 (By.CSS_SELECTOR, "div[role='main'] input[name='email']"),
                 # Generic fallback if the above fail
                 (By.CSS_SELECTOR, "input[name='email']") 
            ]
            
            for by, val in selectors:
                try:
                    # We ensure the element is not just present but visible to avoid hidden inputs
                    element = wait.until(EC.visibility_of_element_located((by, val)))
                    
                    # Double check: ensure it's NOT the small top-right input
                    # The central input is usually wider. Or we can check if it's inside the 'blue' header
                    # Simplest check: The placeholder text.
                    placeholder = element.get_attribute("placeholder")
                    if placeholder and "Email or phone" in placeholder: 
                        # This matches the top bar in English, ignore it if possible unless it's the only one
                        continue
                        
                    email_input = element
                    break
                except:
                    continue
            
            if not email_input:
                if log_callback: log_callback(f"Error: Could not find input field for {phone_number}")
                return "INPUT_NOT_FOUND"

            email_input.clear()
            email_input.send_keys(phone_number)
            time.sleep(0.5)
            
            # --- STEP 2: CLICK SEARCH ---
            search_btn = None
            # The search button is also distinct from the "Log In" button
            btn_selectors = [
                 (By.ID, "did_submit"),
                 (By.NAME, "did_submit"),
                 (By.XPATH, "//button[contains(text(), 'Search')]"),
                 (By.CSS_SELECTOR, "button[type='submit']")
            ]
            
            for by, val in btn_selectors:
                try:
                    search_btn = wait.until(EC.element_to_be_clickable((by, val)))
                    if search_btn:
                        break
                except:
                    continue
                    
            if not search_btn:
                if log_callback: log_callback(f"Error: Could not find Search button for {phone_number}")
                return "BTN_NOT_FOUND"
                
            search_btn.click()
            
            # --- STEP 3: ANALYZE RESULT ---
            
            found_account = False
            start_time = time.time()
            
            while time.time() - start_time < 15:
                src = self.driver.page_source
                
                # Case A: Not Found
                if "No search results" in src or "No account found" in src:
                    if log_callback: log_callback(f"Not Found: {phone_number}")
                    return "NOT_FOUND"
                
                # Case A.2: User screenshot shows "Please fill in at least one field" which happens if top bar was used or empty
                # If we see this, we failed step 1. But for now we treat as not found or retry? 
                # We will treat as Error/Not Found.
                if "Please fill in at least one field" in src:
                     if log_callback: log_callback(f"Error: Input failed (Empty?) for {phone_number}")
                     return "INPUT_ERROR"

                # Case B: Found - "Reset Your Password" screen
                if "Reset Your Password" in src or "Send code via SMS" in src:
                    found_account = True
                    break
                    
                # Case C: Already sent OTP
                if "Enter code" in src or "We sent" in src:
                    found_account = True
                    if log_callback: log_callback(f"OTP/Code Screen Reached: {phone_number}")
                    time.sleep(2)
                    return "OTP_SENT"
                    
                time.sleep(0.5)
            
            if found_account:
                if log_callback: log_callback(f"FOUND: {phone_number} - Clicking Continue...")
                
                # 1. Select SMS if available
                try:
                    sms_radio = self.driver.find_element(By.XPATH, "//input[@type='radio' and (following-sibling::div[contains(., 'SMS')] or ../following-sibling::div[contains(., 'SMS')] or parent::*/following-sibling::*[contains(., 'SMS')])]")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", sms_radio)
                    sms_radio.click()
                    time.sleep(0.5)
                except:
                    pass
                    
                # 2. Click Continue
                clicked_continue = False
                continue_selectors = [
                    (By.XPATH, "//button[text()='Continue']"),
                    (By.XPATH, "//button[contains(text(), 'Continue')]"),
                    (By.CSS_SELECTOR, "button[name='reset_action']")
                ]
                
                for by, val in continue_selectors:
                    try:
                        btn = self.driver.find_element(by, val)
                        if btn.is_displayed() and btn.is_enabled():
                            btn.click()
                            clicked_continue = True
                            if log_callback: log_callback(f"Clicked Continue for {phone_number}")
                            break
                    except:
                        continue
                
                if clicked_continue:
                    time.sleep(2)
                    if "Enter code" in self.driver.page_source or "We sent" in self.driver.page_source:
                         if log_callback: log_callback(f"SUCCESS: OTP Sent to {phone_number}")
                         time.sleep(2)
                         return "OTP_SENT"
                    else:
                         if log_callback: log_callback(f"Processed: {phone_number}")
                         return "OTP_SENT"
                else:
                    if log_callback: log_callback(f"FOUND: {phone_number} (Could not click Continue)")
                    return "FOUND_Wait"
            else:
                 if log_callback: log_callback(f"Timeout: {phone_number}")
                 return "TIMEOUT"

        except Exception as e:
            if log_callback: log_callback(f"Error processing {phone_number}: {str(e)}")
            return "ERROR"

def worker_loop(number_queue, log_queue, headless):
    """
    Continuous worker loop.
    """
    bot = FacebookBot(headless=headless)
    
    if not bot.start_browser():
        log_queue.put("Worker failed to start browser.")
        return

    log_queue.put("Worker started. Browser ready.")

    while True:
        try:
            phone_number = number_queue.get(timeout=1)
        except queue.Empty:
            break
        
        try:
            bot.process_number(phone_number, lambda msg: log_queue.put(msg))
        except Exception as e:
            log_queue.put(f"Worker critical error on {phone_number}: {e}")
        finally:
            number_queue.task_done()
            
    bot.close_driver()
    log_queue.put("Worker finished. Browser closed.")
