# coding: UTF-8
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 環境変数から設定を取得
ROUTER_IP = os.getenv('ROUTER_IP', '192.168.0.1')
ROUTER_USER = os.getenv('ROUTER_USER', 'admin')
ROUTER_PASS = os.getenv('ROUTER_PASS')

# デバッグフラグ
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'


# Setup Chrome options for Selenium standalone container
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-extensions")
options.add_argument("--disable-web-security")

# ChromeDriverサービス設定 (Seleniumコンテナの標準パス)
webdriver_service = Service("/usr/bin/chromedriver")

# Set the driver
driver = webdriver.Chrome(service=webdriver_service, options=options)

try:
    print("ルーター管理画面にアクセス中...")
    driver.get(f"http://{ROUTER_IP}")
    
    time.sleep(3)
    
    # ユーザー名の入力欄を探して入力
    username_field = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "Frm_Username"))
    )
    username_field.clear()
    username_field.send_keys(ROUTER_USER)
    
    # パスワードの入力欄を探して入力
    password_field = driver.find_element(By.ID, "Frm_Password")
    password_field.clear()
    password_field.send_keys(ROUTER_PASS)
    
    # ログインボタンをクリック
    login_button = driver.find_element(By.ID, "LoginId")
    login_button.click()
    
    print("ログイン完了")
    time.sleep(5)
    
    # メインナビゲーションが表示されるまで待機
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "mainNavigator"))
    )
    
    print("管理&診断メニューを探しています...")
    
    # ページが完全に読み込まれるまで待機
    WebDriverWait(driver, 10).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )
    
    # 管理&診断メニューをクリック
    try:
        admin_diag_menu = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "mgrAndDiag"))
        )
        admin_diag_menu.click()
        time.sleep(3)
        print("管理&診断ページに移動")
        
        # 管理&診断ページのHTMLを保存
        with open("/app/data/output/admin_diag_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # スクリーンショットを撮影
        driver.save_screenshot("/app/data/output/admin_diag_page.png")
        
        # リブートボタンを探してクリック
        print("リブートボタンを探しています...")
        try:
            reboot_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "Btn_restart"))
            )
            print("リブートボタンをクリック")
            reboot_button.click()
            time.sleep(2)
            
            # 確認ダイアログが表示されるまで待機
            print("確認ダイアログの表示を待機中...")
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.ID, "confirmLayer"))
            )
            
            # 確認ダイアログのスクリーンショットを撮影
            print("確認ダイアログのスクリーンショットを撮影")
            driver.save_screenshot("/app/data/output/reboot_confirm_dialog.png")
            
            # 確認ダイアログのHTMLを保存
            with open("/app/data/output/reboot_confirm_dialog.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            
            
            # DEBUGモードでない場合は最終確認ボタン（OK）を押す
            if DEBUG:
                print("\n(デバッグモード: 最終確認ボタン（OK）をスキップ)")
                print("処理完了: リブートボタンクリック、確認ダイアログ表示、スクリーンショット撮影完了")
                print("注意: 最終確認ボタン（OK）はまだ押していません")
            else:
                print("最終確認ボタン（OK）をクリックします...")
                try:
                    confirm_ok_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "confirmOK"))
                    )
                    confirm_ok_button.click()
                    print("最終確認ボタン（OK）をクリックしました - ルーターリブート開始")
                    
                    # リブート開始後の画面変化を待機・記録
                    time.sleep(3)
                    driver.save_screenshot("/app/data/output/reboot_started.png")
                    
                    print("\n処理完了: ルーターリブートを実行しました")
                    
                except Exception as ok_e:
                    print(f"最終確認ボタン（OK）のクリックでエラー: {ok_e}")
                    print("処理完了: 確認ダイアログまでは成功しましたが、OKボタンのクリックに失敗")
            
        except Exception as reboot_e:
            print(f"リブートボタンのクリックでエラーが発生: {reboot_e}")
            
            # 利用可能なボタンを確認
            print("利用可能なボタンを確認します...")
            try:
                buttons = driver.find_elements(By.TAG_NAME, "input")
                for button in buttons:
                    if button.get_attribute('type') == 'button':
                        button_id = button.get_attribute('id')
                        button_value = button.get_attribute('value')
                        button_class = button.get_attribute('class')
                        print(f"ボタン要素: ID={button_id}, Value={button_value}, Class={button_class}")
            except Exception as btn_list_e:
                print(f"ボタンの確認でエラー: {btn_list_e}")
        
        print("\n処理完了: 管理&診断ページに移動、スクリーンショット撮影完了")
        
    except Exception as e:
        print(f"管理&診断ページへの移動でエラーが発生: {e}")
        
        # 利用可能なメニューを確認
        print("利用可能なメニューを確認します...")
        try:
            menus = driver.find_elements(By.XPATH, "//div[@id='mn_li']//a")
            for menu in menus:
                menu_id = menu.get_attribute('id')
                menu_page = menu.get_attribute('menupage')
                print(f"利用可能なメニュー: {menu.text} (ID: {menu_id}, MenuPage: {menu_page})")
        except Exception as menu_e:
            print(f"メニューの確認でエラー: {menu_e}")
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    driver.save_screenshot("/app/data/output/error_screenshot.png")
    print("エラー時のスクリーンショットを保存しました: /app/data/output/error_screenshot.png")
    
finally:
    driver.quit()
    print("スクリプト実行完了")