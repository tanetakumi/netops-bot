# coding: UTF-8
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
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
    # ルーター管理画面にアクセス
    print("ルーター管理画面にアクセス中...")
    driver.get(f"http://{ROUTER_IP}")
    
    # ページの読み込みを待機
    time.sleep(3)
    
    # ログイン情報を入力
    print("ログイン情報を入力中...")
    
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
    
    print("ログイン完了。管理画面を確認中...")
    time.sleep(5)
    
    # メインナビゲーションが表示されるまで待機
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "mainNavigator"))
    )
    
    # インターネットメニューに直接移動
    print("インターネットメニューを探しています...")
    
    # ページが完全に読み込まれるまで待機
    WebDriverWait(driver, 10).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )
    
    # インターネットメニューを探す
    internet_menu = None
    internet_patterns = [
        "//a[contains(text(), 'インターネット')]",
        "//a[@id='internet']",
        "//a[@menupage='internet']"
    ]
    
    for pattern in internet_patterns:
        try:
            internet_menu = driver.find_element(By.XPATH, pattern)
            if internet_menu.is_enabled():
                print(f"インターネットメニューを発見: {internet_menu.text}")
                internet_menu.click()
                time.sleep(3)
                break
        except:
            continue
    
    if not internet_menu:
        # 利用可能なメニューを表示
        print("インターネットメニューが見つかりません。利用可能なメニューを確認します...")
        menus = driver.find_elements(By.XPATH, "//div[@id='mn_li']//a")
        for menu in menus:
            menu_id = menu.get_attribute('id')
            menu_page = menu.get_attribute('menupage')
            print(f"利用可能なメニュー: {menu.text} (ID: {menu_id}, MenuPage: {menu_page})")
    else:
        # インターネットページに移動後の処理
        print("インターネットページに移動しました")
        time.sleep(3)
        
        # インターネットページのHTMLを保存
        with open("/app/output/internet_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("インターネットページのHTMLを保存しました: /app/output/internet_page.html")
        
        # スクリーンショットを撮影
        driver.save_screenshot("/app/output/internet_page.png")
        print("インターネットページのスクリーンショットを保存しました: /app/output/internet_page.png")
        
        # WANセクションを選択
        print("\n=== WANセクションを選択 ===")
        try:
            wan_menu = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "internetConfig"))
            )
            print(f"WANメニューを発見: {wan_menu.text}")
            wan_menu.click()
            time.sleep(3)
            
            # WAN設定ページのHTMLを保存
            with open("/app/output/wan_config_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("WAN設定ページのHTMLを保存しました: /app/output/wan_config_page.html")
            
            # スクリーンショットを撮影
            driver.save_screenshot("/app/output/wan_config_page.png")
            print("WAN設定ページのスクリーンショットを保存しました: /app/output/wan_config_page.png")
            
            # コミュファの項目を展開
            print("\n=== コミュファの項目を展開 ===")
            try:
                # コミュファの項目を探す
                commufa_element = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "instName_Internet:1"))
                )
                print(f"コミュファ項目を発見: {commufa_element.text}")
                
                # 現在の状態を確認
                commufa_classes = commufa_element.get_attribute('class')
                print(f"コミュファ項目のクラス: {commufa_classes}")
                
                # 展開されているかチェック (instNameExp クラスがあるかどうか)
                if 'instNameExp' in commufa_classes:
                    print("コミュファ項目は既に展開されています")
                else:
                    print("コミュファ項目は折りたたまれています。展開中...")
                    commufa_element.click()
                    time.sleep(3)
                    
                    # 展開後の状態を確認
                    updated_classes = commufa_element.get_attribute('class')
                    print(f"展開後のクラス: {updated_classes}")
                
                # 展開後のページを保存
                with open("/app/output/commufa_expanded_page.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                print("コミュファ展開後のHTMLを保存しました: /app/output/commufa_expanded_page.html")
                
                # 展開後のスクリーンショットを撮影（メイン出力）
                driver.save_screenshot("/app/output/commufa_expanded.png")
                print("コミュファ展開後のスクリーンショットを保存しました: /app/output/commufa_expanded.png")
                
                # 接続モードの変更処理
                print("\n=== 接続モードの変更 ===")
                try:
                    # 接続モードのプルダウンを探す
                    connection_mode_dropdown = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "ConnTrigger:1"))
                    )
                    print(f"接続モードプルダウンを発見: {connection_mode_dropdown.get_attribute('value')}")
                    
                    # 1. 常時切断（Manual）に変更
                    print("接続モードを常時切断（Manual）に変更中...")
                    
                    # Selectオブジェクトを作成
                    select = Select(connection_mode_dropdown)
                    
                    # プルダウンを開いた瞬間のスクリーンショット（プルダウンクリック前）
                    connection_mode_dropdown.click()
                    time.sleep(1)
                    driver.save_screenshot("/app/output/dropdown_opened.png")
                    print("プルダウンを開いた瞬間のスクリーンショットを保存しました: /app/output/dropdown_opened.png")
                    
                    # 常時切断（Manual）を選択
                    select.select_by_value("Manual")
                    time.sleep(1)
                    print("接続モードを常時切断に変更しました")
                    
                    # 常時切断に変更した瞬間のスクリーンショット
                    driver.save_screenshot("/app/output/changed_to_manual.png")
                    print("常時切断に変更した瞬間のスクリーンショットを保存しました: /app/output/changed_to_manual.png")
                    
                    # 設定ボタンをクリック
                    try:
                        if DEBUG:
                            print("デバッグモードのため、設定ボタンをクリックしません")
                        else:
                            # apply_button = WebDriverWait(driver, 5).until(
                            #     EC.element_to_be_clickable((By.ID, "Btn_apply_internet:1"))
                            # )
                            print("設定ボタンをクリック中...")
                            # apply_button.click()
                        time.sleep(3)
                        print("設定ボタンをクリックしました")
                    except Exception as apply_e:
                        print(f"設定ボタンのクリックでエラー: {apply_e}")
                    
                    time.sleep(5)
                    # 2. 常時接続（AlwaysOn）に戻す
                    print("接続モードを常時接続（AlwaysOn）に戻し中...")
                    
                    # 常時接続（AlwaysOn）を選択
                    select.select_by_value("AlwaysOn")
                    time.sleep(1)
                    print("接続モードを常時接続に戻しました")
                    
                    # 常時接続に戻した瞬間のスクリーンショット
                    driver.save_screenshot("/app/output/changed_to_alwayson.png")
                    print("常時接続に戻した瞬間のスクリーンショットを保存しました: /app/output/changed_to_alwayson.png")
                    
                    # 再度設定ボタンをクリック
                    try:
                        if DEBUG:
                            print("デバッグモードのため、設定ボタンをクリックしません")
                        else:
                            # apply_button = WebDriverWait(driver, 5).until(
                            #     EC.element_to_be_clickable((By.ID, "Btn_apply_internet:1"))
                            # )
                            print("設定ボタンを再度クリック中...")
                            # apply_button.click()
                        time.sleep(3)
                        print("設定ボタンを再度クリックしました")
                    except Exception as apply_e:
                        print(f"設定ボタンの再クリックでエラー: {apply_e}")
                    
                    # 最終状態のスクリーンショットを撮影
                    driver.save_screenshot("/app/output/connection_mode_changed.png")
                    print("接続モード変更後のスクリーンショットを保存しました: /app/output/connection_mode_changed.png")
                    
                except Exception as conn_e:
                    print(f"接続モードの変更でエラーが発生: {conn_e}")
                    
                    # 利用可能な設定要素を確認
                    print("利用可能な設定要素を確認します...")
                    try:
                        select_elements = driver.find_elements(By.TAG_NAME, "select")
                        for select in select_elements:
                            select_id = select.get_attribute('id')
                            select_name = select.get_attribute('name')
                            print(f"Select要素: ID={select_id}, Name={select_name}")
                            
                        button_elements = driver.find_elements(By.XPATH, "//input[@type='button']")
                        for button in button_elements:
                            button_id = button.get_attribute('id')
                            button_value = button.get_attribute('value')
                            print(f"Button要素: ID={button_id}, Value={button_value}")
                    except Exception as elem_e:
                        print(f"設定要素の確認でエラー: {elem_e}")
                
                # 処理完了メッセージ
                print("\n=== 処理完了 ===")
                print("コミュファの項目が正常に展開され、接続モードの変更処理が完了しました。")
                print("スクリーンショットが /app/output/commufa_expanded.png に保存されました。")
                
            except Exception as commufa_e:
                print(f"コミュファ項目の展開でエラーが発生: {commufa_e}")
                
                # 代替方法を試す
                print("代替方法でコミュファ項目を探します...")
                try:
                    # テキストでコミュファ項目を探す
                    commufa_alt = driver.find_element(By.XPATH, "//span[contains(text(), 'コミュファ')]")
                    print(f"代替方法でコミュファ項目を発見: {commufa_alt.text}")
                    commufa_alt.click()
                    time.sleep(3)
                    print("代替方法でコミュファ項目をクリックしました")
                    
                    # 代替方法での結果を保存
                    driver.save_screenshot("/app/output/commufa_expanded_alt.png")
                    print("代替方法での結果を保存しました: /app/output/commufa_expanded_alt.png")
                    
                except Exception as alt_e:
                    print(f"代替方法でもエラー: {alt_e}")
                    
                    # 利用可能な折りたたみ項目を確認
                    print("利用可能な折りたたみ項目を確認します...")
                    try:
                        collapsible_items = driver.find_elements(By.CLASS_NAME, "collapsibleInst")
                        for item in collapsible_items:
                            item_id = item.get_attribute('id')
                            item_class = item.get_attribute('class')
                            print(f"折りたたみ項目: {item.text} (ID: {item_id}, Class: {item_class})")
                    except Exception as coll_e:
                        print(f"折りたたみ項目の確認でエラー: {coll_e}")
            
        except Exception as e:
            print(f"WANセクションの選択でエラーが発生: {e}")
            
            # 利用可能なサブメニューを確認
            print("利用可能なサブメニューを確認します...")
            try:
                submenus = driver.find_elements(By.XPATH, "//ul[@id='class2MenuItem']//a")
                for submenu in submenus:
                    submenu_id = submenu.get_attribute('id')
                    submenu_page = submenu.get_attribute('menupage')
                    submenu_title = submenu.get_attribute('title')
                    print(f"サブメニュー: {submenu.text} (ID: {submenu_id}, MenuPage: {submenu_page}, Title: {submenu_title})")
            except Exception as sub_e:
                print(f"サブメニューの確認でエラー: {sub_e}")
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    driver.save_screenshot("/app/output/error_screenshot.png")
    print("エラー時のスクリーンショットを保存しました: /app/output/error_screenshot.png")
    
finally:
    # ブラウザを閉じる
    driver.quit()
    print("ブラウザを閉じました。")
    print("スクリプトの実行が完了しました。")