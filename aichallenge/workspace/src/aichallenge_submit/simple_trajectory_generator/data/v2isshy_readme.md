# raceline_awsim_v2isshy_* の経路編集のメモ

## trajectory-editor の使用方法

- 実行

```bash
cd aichallenge/tools/aichallenge-trajectory-editor
source .venv/bin/activate
./cmd_line/csv_editor
```

- 操作

  - [Load lane]
    - aichallenge/workspace/src/aichallenge_submit/aichallenge_submit_launch/map/lanelet2_map.osm.csv

  - [Load trj]
    - aichallenge/workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_v2isshy_34p99kph_07.csv

  - Show Labels ： 速度ラベルを表示
  - Add Point ： 点を追加
  - Move Point : 点を移動
  - Delete Point : 点を削除
  - Edit a Label : 速度ラベルの変更
  - Edit Lables : 選択した範囲の速度ラベルの一斉変更

  - [Save CSV] : 保存
  - [Post] : 未実装
  - [Quit] : 終了
  
  - Dark Mode : ダークモード
  - Move Selected Points : 選択範囲を一斉移動
  - Straight Lien : 選択範囲を直線化

  - [Smooth] : 全体をスムース化（あまり使えない）
    - Smoothing Window

  - [Generate Speed] : 速度ラベルの付け直し
    - Max Speed[km/h] : 34.99
    - Friction Coeff(μ): 0.8
    - Min Speed[km/h] : 34.99
    - Max Accel(m/s^2) : 2.0
    - Speed Smooth Window : 3
    - 上記設定では、すべて 34.99 kph に設定される

  - [Publish ROS] : 未実装

## 評価環境の実行方法

- グラフ画像保存の場合は、以下を実行し得ておく

    ```bash
    sudo plotly_get_chrome
    ```

- 最初の実行はこちら。もしくは、不安定なとき。

    ```bash
    ./build_autoware_isshy_v2.bash clean ; ./run_evaluation_isshy_v2.bash
    ```

- 以降はソースコードを修正後、以下を

    ```bash
    ./build_autoware_isshy_v2.bash ; ./run_evaluation_isshy_v2.bash
    ```

- 提出時は、以下を

    ```bash
    cp -p ./build_autoware_isshy_v2_release.bash ./build_autoware.bash
    cp -p ./run_evaluation_isshy_v2_release.bash ./run_evaluation.bash
    ./build_autoware.bash ; ./run_evaluation.bash
    ```

## 30kph 版

- raceline_awsim_v2isshy_30kph.csv
  - raceline_awsim_30km_from_garage.csv から 安定性向上のみ

## 35kph 版

- raceline_awsim_v2isshy_34p99kph.csv
  - raceline_awsim_v2isshy_30kph.csv から 車速を34.99kphに
- raceline_awsim_v2isshy_34p99kph_01.csv
  - 最終周に壁に衝突
  - "min_time": 45.060420989990234,
- raceline_awsim_v2isshy_34p99kph_02.csv
  - 全周走りきれた
    - "min_time": 44.97540283203125,
  - リミッタ無し x99
    - "min_time": 44.2402458190918,

| ファイル名 | speed_proportional_gain | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|-------------------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_km_from_garage.csv      | x1.0 | *49.31132888793945*  |                    |                    |                  |
| raceline_awsim_v2isshy_30kph.csv       | x1.0 | 49.00126266479492  | 28.295737092122867 | 0.5020778658864309 | 2025-08-22 11:16 |
| raceline_awsim_v2isshy_34p99kph_01.csv | x1.0 | 45.060420989990234 | 32.91405513443185  | 0.5861332516216289 | 2025-08-22 12:32 |
| raceline_awsim_v2isshy_34p99kph_02.csv | x1.0 | 44.97540283203125  | 34.638697869478484 | 0.5139918776161025 | 2025-08-22 14:58 |
| raceline_awsim_v2isshy_34p99kph_02.csv | x5.0 | 44.23524475097656  | 34.61154813440444  | 0.5523427376056574 | 2025-08-22 14:58 |
| raceline_awsim_v2isshy_34p99kph_02.csv | x10  | 44.660335540771484 | 34.809934795981995 | 0.5205933124028013 | 2025-08-22 14:58 |
| raceline_awsim_v2isshy_34p99kph_02.csv | x99  | 44.2402458190918   | **35.05378104175876**  | 0.5307193642722788 | 2025-08-22 14:58 |

### リミッタ有り x99　比較表

- MODE=01

```reference.launch.xml
    <param name="speed_proportional_gain" value="99.0"/> 

    <param name="speed_limit1" value="34.60"/>
    <param name="accel_limit1" value="-0.08"/>
    <param name="speed_limit2" value="34.95"/>
    <param name="accel_limit2" value="-0.2"/>
```

| ファイル名 | speed_proportional_gain | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|-------------------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_v2isshy_34p99kph_02.csv | x99  |   44.30025863647461    | **35.052569830912745**  |   0.5636117909054018   | 2025-08-22 14:58 |
| raceline_awsim_v2isshy_34p99kph_05.csv | x99  |   42.50487518310547    |   34.638697869478484    |   0.5139918776161025   | 2025-08-22 15:46 |
| raceline_awsim_v2isshy_34p99kph_06.csv | x99  |   41.94975662231445    |   34.71408833197464     |   0.6639585281115115   | 2025-08-22 17:33 |
| raceline_awsim_v2isshy_34p99kph_07.csv | x99  |   41.504661560058594   |   34.690522831496615    | **0.7643390998189656** | 2025-08-22 17:49 |
| raceline_awsim_v2isshy_34p99kph_08.csv | x99  | **41.184593200683594** |   34.726711780147085    |   0.5876384613662181   | 2025-08-22 18:15 |
| raceline_awsim_v2isshy_34p99kph_09.csv | x99  |   41.31962203979492    |   34.71224336146475     |   0.5992363862932949   | 2025-08-22 19:00 |

- MODE=02

```reference.launch.xml
    <param name="speed_proportional_gain" value="99.0"/> 

    <param name="speed_limit1" value="34.80"/>
    <param name="accel_limit1" value="-0.08"/>
    <param name="speed_limit2" value="34.95"/>
    <param name="accel_limit2" value="-0.2"/>
```

| ファイル名 | speed_proportional_gain | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|-------------------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_v2isshy_34p99kph_07.csv | x99  |   41.33962631225586    |   34.93320695148356     |   0.5603839021752508   | 2025-08-22 17:49 |
| raceline_awsim_v2isshy_34p99kph_08.csv | x99  |   41.484657287597656   |   34.912497804440314    |   0.6100709484289107   | 2025-08-22 18:15 |
| raceline_awsim_v2isshy_34p99kph_09.csv | x99  | **41.25960922241211**  | **34.94087030165678**   | **0.614640043067247**  | 2025-08-22 19:00 |

- MODE=03

```reference.launch.xml
    <param name="speed_proportional_gain" value="99.0"/> 

    <param name="speed_limit1" value="34.90"/>
    <param name="accel_limit1" value="-0.08"/>
    <param name="speed_limit2" value="34.95"/>
    <param name="accel_limit2" value="-0.2"/>
```

| ファイル名 | speed_proportional_gain | total_time | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|-------------------------|------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_v2isshy_34p99kph_07.csv | x99  |   251.75855255126953   |   41.44464874267578    |   34.97409394629537     | **0.7701191925785535** | 2025-08-22 17:49 |
| raceline_awsim_v2isshy_34p99kph_08.csv | x99  |   251.12341690063477   |   41.30461883544922    | **35.00513242446771**   |   0.6015257546603748   | 2025-08-22 18:15 |
| raceline_awsim_v2isshy_34p99kph_09.csv | x99  | **250.10319900512695** | **41.10957717895508**  |   34.97549475155447     |   0.6829745644905538   | 2025-08-22 19:00 |

- MODE=04

```reference.launch.xml
    <param name="speed_proportional_gain" value="99.0"/> 

    <param name="speed_limit1" value="34.95"/>
    <param name="accel_limit1" value="-0.08"/>
    <param name="speed_limit2" value="35.00"/>
    <param name="accel_limit2" value="-0.2"/>
```

| ファイル名 | speed_proportional_gain | total_time | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|-------------------------|------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_v2isshy_34p99kph_07.csv | x99  |   251.96859741210938   |   41.494659423828125   |   35.04259639716609     |   0.5333012113417815   | 2025-08-22 17:49 |
| raceline_awsim_v2isshy_34p99kph_08.csv | x99  |   251.12841796875      |   41.44464874267578    | **35.078311970711304**  |   0.6240145596755216   | 2025-08-22 18:15 |
| raceline_awsim_v2isshy_34p99kph_09.csv | x99  | **250.88336563110352** | **41.34962844848633**  |   35.041631361012655    | **0.7682457429384091** | 2025-08-22 19:00 |

- MODE=05

```reference.launch.xml
    <param name="speed_proportional_gain" value="99.0"/> 

    <param name="speed_limit1" value="35.00"/>
    <param name="accel_limit1" value="-0.08"/>
    <param name="speed_limit2" value="35.10"/>
    <param name="accel_limit2" value="-0.2"/>
```

| ファイル名 | speed_proportional_gain | total_time | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|-------------------------|------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_v2isshy_34p99kph_07.csv | x99  |   251.16842651367188   | **41.17959213256836**  | **35.0760235834354**    | **0.6964001340507688** | 2025-08-22 17:49 |
| raceline_awsim_v2isshy_34p99kph_08.csv | x99  | **250.808349609375**   |   41.26961135864258    |   35.04530090762962     |   0.6189930047469463   | 2025-08-22 18:15 |
| raceline_awsim_v2isshy_34p99kph_09.csv | x99  |   251.55350875854492   |   41.39963912963867    |   35.03546567925285     |   0.6234352045190988   | 2025-08-22 19:00 |

- Limmitter OFF

```reference.launch.xml
    <param name="speed_proportional_gain" value="99.0"/> 

    <param name="speed_limit1" value="40.00"/>
    <param name="accel_limit1" value="-0.2"/>
```

| ファイル名 | total_time | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_v2isshy_34p99kph_09.csv |  **251.11841583251953** |   41.3746337890625    | **35.02675590604106**   |   0.6113181683601228   | 2025-08-22 19:00 |
| raceline_awsim_v2isshy_40kp_01.csv     |    251.3184585571289    | **41.23460388183594** |   34.976416319408195    | **0.7712124968249672** | 2025-08-22 21:39 |

- Limmitter OFF

```reference.launch.xml
        <param name="accel_lowpass_gain" value="0.0"/>

    <param name="speed_proportional_gain" value="99.0"/> 

    <param name="speed_limit1" value="40.00"/>
    <param name="accel_limit1" value="-0.2"/>
```

| ファイル名 |  total_time | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_v2isshy_34p99kph_10.csv |   252.95880889892578   |   41.574676513671875  |   35.0639582780021      |   3.509670624656991    | 2025-08-23 17:31 |
| raceline_awsim_v2isshy_34p99kph_11.csv |   255.0292510986328    |   41.9997673034668    |   34.99690233465933     |   4.173248401044381    | 2025-08-23 17:44 |
| raceline_awsim_v2isshy_34p99kph_12.csv |   256.21450424194336   |   42.27982711791992   |   35.01701868822936     |   2.512420110724437    | 2025-08-23 18:09 |
| raceline_awsim_v2isshy_34p99kph_13.csv |   255.91944122314453   |   42.05978012084961   |   35.04343779891253     |   3.6668871503623635   | 2025-08-23 18:07 |
| raceline_awsim_v2isshy_34p99kph_14.csv |   256.1744956970215    |   42.37984848022461   |   35.04751213055151     |   2.1067230725848596   | 2025-08-23 18:30 |
| raceline_awsim_v2isshy_40kp_02.csv     |   255.16427993774414   |   42.1898078918457    |   35.02675121551064     |   3.2774864152118295   | 2025-08-23 19:00 |

### リミッタ有り x99　MODE=03 , 経路09 ベースで

- 速度リミッタ MODE=03 と定義

```reference.launch.xml
    <param name="speed_proportional_gain" value="99.0"/> 

    <param name="speed_limit1" value="34.90"/>
    <param name="accel_limit1" value="-0.08"/>
    <param name="speed_limit2" value="34.95"/>
    <param name="accel_limit2" value="-0.2"/>
```

- いずれかを選択

```reference.launch.xml
        <param name="accel_lowpass_gain" value="0.0"/>
        <param name="accel_lowpass_gain" value="0.5"/>
        <param name="accel_lowpass_gain" value="0.9"/>
```

| ファイル名 | accel_lowpass_gain | total_time | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|--------------------|------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_v2isshy_34p99kph_09.csv | 0.9  |   250.06319046020508   |   41.14458465576172    |   35.001887120310215    |   0.5693238584101983   | 2025-08-22 19:00 |
| raceline_awsim_v2isshy_34p99kph_15.csv | 0.9  |   249.72811889648438   |   41.244606018066406   |   34.99745783217101     |   0.5566961934746677   | 2025-08-23 15:53 |
| raceline_awsim_v2isshy_34p99kph_16.csv | 0.9  | **249.5130729675293**  |   41.244606018066406   | **35.03170775355064**   |   0.5749447374914741   | 2025-08-23 16:13 |
| raceline_awsim_v2isshy_34p99kph_09.csv | 0.0  |   250.5332908630371    |   41.209598541259766   |   34.984782880491935    | **2.879574614192748**  | 2025-08-22 19:00 |
| raceline_awsim_v2isshy_34p99kph_15.csv | 0.0  |   - 走行不可 -         |   -----------------    |   -----------------     |   -----------------    | 2025-08-23 15:53 |
| raceline_awsim_v2isshy_34p99kph_16.csv | 0.0  |   249.9631690979004    | **41.06456756591797**  |   35.02058450642681     |   1.699334086587449    | 2025-08-23 16:13 |
| raceline_awsim_v2isshy_34p99kph_16.csv | 0.5  |   250.02818298339844   |   41.324623107910156   |   35.01495175269111     |   1.0493793688986521   | 2025-08-23 16:13 |

### リミッタ無し x99　MODE=03

```reference.launch.xml
    <!-- リミッターOFF -->
    <param name="speed_limit1" value="40.00"/>
    <param name="accel_limit1" value="-0.2"/> 
```

| ファイル名 | accel_lowpass_gain | total_time | min_time | max_velocity_kmph | max_longitudinal_acceleration | date |
|------------|--------------------|------------|----------|-------------------|-------------------------------|------|
| raceline_awsim_v2isshy_34p99kph_16.csv | 0.9  |   249.78313064575195   |   41.334625244140625   |   35.027572249389166    |   0.5904474728804625   | 2025-08-23 16:13 |
