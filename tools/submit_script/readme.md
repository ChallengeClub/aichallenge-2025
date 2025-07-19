# オンライン採点システムに自動アップロードするスクリプト
## 初回利用時ユーザ、パスワードを設定
```
cp setting.py my_setting.py
nano my_setting.py # ユーザ、パスワードを設定
```

## アップロード
```
python submit.py ../../submit/aichallenge_submit.tar.gz "your comment"
```