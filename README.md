# 概要
WIEN2k第一原理プログラムによるバンド計算を行うスクリプトです。
* run_w2k.py
* make_klist_band.py
* analyze_w2k.py

以上が基本となるスクリプトで、それぞれ独立に動きます。
これらを組み合わせて様々な計算が可能です。

例として、
* NL_calc.py

を添付しています。

# 目次
* run_w2k.py
  * 準備
* make_klist_band.py
  * 使用例
* analyze_w2k.py
* 計算コードの例
  * kx-ky等エネルギー面を計算するコード
  * SCF計算自動化コード

# run_w2k.py
WIEN2k wrapper的なコードです。

## 準備
環境に合わせて、以下の`self.temp_path`及び`self.w2k_user`の初期値を変更してください。

```:run_w2k.py
...
class W2k:
  def __init__(self, case_g):
    self.case = case_g  # session name
    self.temp_path = '/usr/local/WIEN2k_17.1/SRC_templates/'  # template file path
    self.w2k_user = '/Users/kounotakashi/WIEN2k_17.1_user/'  # wien2k user folder path
...
```

# make_klist_band.py
.klist_bandファイルを作成するコードです。  
XCrysdenみたいに波数点を何個か指定し、総点数を与えることでklistを作るモード`main`と、全く補完を行わないモード`sonomama`が存在します。
## 使用例
### `main`モードを用いたG--X--K(fcc)を通るklistの作成
```python
import make_klist_band
make_klist_band.main(output_name='example.klist_band', kmeshx=100, kpath=[[0, 0, 0], [1, 0, 0], [0.75, 0.75, 0]], index_ls=['Gamma', 'X', 'K'], d=0, echo=1)
```

| name          | description      | type                  | default | required |
|---------------|------------------|-----------------------|---------|----------|
| `output_name` | 出力ファイルのフルパス      | `str`                 |         | true     |
| `kmeshx`      | k点数              | `int`                 |         | true     |
| `kpath`       | kpath            | `float`の`list`の`list` |         | true     |
| `index_ls`    | kpathに対応するインデックス | `str`の`list`          | `[]`   |          |
| `d`           | 最大値（0で自動設定）      | `int`                 | `0`     |          |
| `echo`        | ログの出力フラグ         | `int`                 | `1`       |          |

### `sonomama`モードを用いたARPES測定の等エネルギー曲線を再現するklistの作成

```python
import make_klist_band
import numpy as np

def kikakuka(v):
  if v > 0:
    v = -v
  v = np.mod(v, 2)
  if v > 1:
    v = 2 - v
  return v

hn = 500
V0 = 12.5
W= 4.5
a = 5.755
th_s = -15
th_e = 15
th_n = 100
mm = 0.5123

ek = hn - W

kpath_list = []
d = 1000
for th in list(np.linespace(th_s, th_e, th_n)):
  kx = mm * np.sqrt(ek) * np.sin(th / 180 * np.pi)
  ky = 0
  kz = mm * np.sqrt(ek * np.cos(th / 180 * np.pi) ** 2 + V0)
  
  kx = kikakuka(kx / (2 * np.pi / a))
  ky = kikakuka(ky / (2 * np.pi / a))
  kz = kikakuka(kz / (2 * np.pi / a))
  kpath_list.append([kx, ky, kz])

make_klist_band.sonomama(output_name='example.klist_band', kpath=kpath_list, d=d, echo=0)
```

| name          | description | type                  | default | required |
|---------------|-------------|-----------------------|---------|----------|
| `output_name` | 出力ファイルのフルパス | `str`                 |         | true     |
| `kpath`       | kpath       | `float`の`list`の`list` |         | true     |
| `d`           | 最大値         | `int`                 |         | true     |
| `echo`        | ログの出力フラグ    | `int`                 | `0`       |          |

# analyze_w2k.py
.dosxevファイルや.agrファイルを読み込むコードです。

# 計算コードの例
## kx-ky等エネルギー面を計算するコード
run_w2k.py、make_klist_band.pyと同じ階層にexample.pyを作成します。
### 色々インポート
run_w2k.pyとmake_klist_band.pyをインポートします。

```python
import run_w2k
import make_klist_band as kb
```

必要なパッケージをインポートします。
インストールされていない場合、`$pip install subprocess`などでインストールできます。
インストール方法は環境に合わせて調査してください。

```python
import subprocess as sp
```

### クラスの呼び出し
run_w2k.pyでは様々な機能・変数を一つのクラスにまとめています。
`w2k = run_w2k.W2k(session)`としてクラスを呼び出した時点で、全ての変数が生成され、初期値が代入されています。

`session`には、セッションのディレクトリの名前を文字列として入れてください。
変数は`w2k.__init__`の中で初期値を設定しているので、適宜見に行ってください。

```python
session = 'Co2MnGa'
w2k = run_w2k.W2k(session)
w2k.spol = 1
w2k.spin_ls = ['up', 'dn']
```

### .inspファイルの作成
.inspファイルにSCF計算で出力されるフェルミ準位を入れます。
.inspファイルをSRC_templateからコピーし、`0.xxx`の部分を.scfファイルから読み取ったフェルミエネルギーで置換しています。

```python
w2k.set_ef_insp()
```

### 出力ディレクトリの作成
バンド計算結果.bands.agrファイルを出力するディレクトリを作成します。
クラス変数`w2k.case_path`にセッションディレクトリのフルパスが入っているので、これを利用します。

```python
outputdpath = w2k.case_path + 'kxkymap/'
sp.run(['mkdir', '-p', outputdpath])
```

### .klist_bandファイルの作成
今回ky, kxをそれぞれ101点計算することにしています。

インポートしたmake_klist_band.pyの中の`main`関数を使います。

```python
kxn = 101
kyn = 101

for ky in range(kyn):
  kb.main(w2k.filepath('.klist_band'), kxn, [[0, ky / (kyn - 1), 0], [1, ky / (kyn - 1), 0]])
```

### 計算の実行
出力ファイル名を`name`に格納（拡張子は不要）し、出力ディレクトリのフルパス`outputdpath`を指定し計算を実行します。

```python
  name = 'ky_' + str(ky)
  w2k.run_band(outputdpath, name)
```

### コード全体

```:example.py
import run_w2k
import make_klist_band as kb
import subprocess as sp
import datetime as dt # optional

session = 'Co2MnGa'
w2k = run_w2k.W2k(session)
w2k.spol = 1
w2k.spin_ls = ['up', 'dn']

w2k.set_ef_insp()

outputdpath = w2k.case_path + 'kxkymap/'
sp.run(['mkdir', '-p', outputdpath])

kxn = 101
kyn = 101

tst = dt.datetime.now() # optional

for ky in range(kyn):
  kb.main(w2k.filepath('.klist_band'), kxn, [[0, ky / (kyn - 1), 0], [1, ky / (kyn - 1), 0]], [])
  name = 'ky_' + str(ky)
  w2k.run_band(outputdpath, name)
  tn = dt.datetime.now() # optional
  print('FINISH : ' + str(tst + (tn - tst) / (ky + 1) * kyn)) # optional
```

## SCF計算自動化コード
イニシャライズからSCF計算、Total EnergyやDOS計算を自動化することで、k-meshやRKmax等のパラメータに対する収束性を確認することができます。  
例として、rkmaxを5から10まで0.5 stepで変化させながらEtotとDOSとSCF計算時間を取得するコードをつくります。
### 色々インポート
run_w2k.pyとanalyze_w2k.pyをインポートします。
これらのファイルは同じ階層に存在する必要があります。

```python
import run_w2k
import make_klist_band as kb
import analyze_w2k as an
```

必要なパッケージをインポートします。
`igorwriter`はndarrayを.ibwファイルや.itxファイルとして保存できるので、便利です。

```python
import igorwriter as iw
```

### クラスの呼び出し
`w2k.set_parallel(スレッド数)`によって、.machinesファイルを作成・編集し並列計算の準備を行います。  
単純なk点並列のみに対応しています。

```python
session = 'Co2MnGa'
w2k = run_w2k.W2k(session)
w2k.set_parallel(4)
```

### 出力の準備
Etot, SCF timeを格納する`list`を作成し、出力ディレクトリの作成も行います。

```python
etot_ls = []
scf_time_ls = []
convdir = w2k.case_path + 'conv/rkmax/'
dosout = convdir + 'dos/'
scfout = convdir + 'scf/'
os.makedirs(dosout, exist_ok=True)
os.makedirs(scfout, exist_ok=True)
```

### パラメータの設定
今回は`w2k.rkmax`をパラメータとして回します。他のパラメータで試す場合は、ここを変えます。
sessionディレクトリに空のstop.txtファイルを作成すれば計算が途中で止まるように細工しておきます。

```python
for v in range(10, 21):
  if not os.path.exists(w2k.case_path + 'stop.txt'):
    v = v / 2
    w2k.rkmax = v
    w2k.lmax = 10
    w2k.kmesh = 10000
    w2k.gmax = 12
```

### イニシャライズ・SCF計算の実行
まず、これまでのSCFデータを消すために.scfファイルと.broydファイルを消しておきます。
`w2k.init_lapw()`でイニシャライズし、`w2k.run_scf()`でSCF計算を行います。  
SCF計算が終わったら`etot = w2k.get_etot()`によって.scfファイルからEtotを読み出し、リストに格納します。
`datetime`パッケージを用いてSCF計算時間を取得しています。

```python
    sp.run('rm *.scf*', shell=True)
    sp.run('rm *.broyd*', shell=True)
    w2k.init_lapw()
    dt_s = dt.datetime.now()
    w2k.run_scf()
    scf_time = dt.datetime.now() - dt_s
    etot = w2k.get_etot()
    etot_ls.append(etot)
    scf_time_ls.append(scf_time)
```

### DOS計算
`w2k.run_dos(outputdpath, name)`によってDOS計算、計算結果の保存が行われます。
ファイル名に`.`が入ると不安なので、`.replace('.', 'p')`によって無害な文字に置換します。

```python
    dosname = 'dos' + str(v).replace('.', 'p')
    scfname = 'scf' + str(v).replace('.', 'p')
    w2k.run_dos(dosout, dosname)
```

### データの保存

`etot_ls`, `scf_time_ls`を.npy形式で保存します。
同時に、.dos1evupなどのファイルはigorで読み込むときに苦労するので、analyze_w2k.pyの機能`make_dos_waves`を使って.itxファイルに変換します。

```python
    np.save(scfout + 'etot.npy', np.array(etot_ls))
    np.save(scfout + 'scf_time.npy', np.array(scf_time_ls))
    an.make_dos_waves([dosout])
```

### コード全体

```python
import run_w2k
import os
import datetime as dt
import subprocess as sp
import analyze_w2k as an
import numpy as np

session = 'Co2MnGa'
w2k = run_w2k.W2k(session)
w2k.set_parallel(4)

etot_ls = []
scf_time_ls = []
convdir = w2k.case_path + 'conv/rkmax/'
dosout = convdir + 'dos/'
scfout = convdir + 'scf/'
os.makedirs(dosout, exist_ok=True)
os.makedirs(scfout, exist_ok=True)

for v in range(10,21):
  if not os.path.exists(w2k.case_path + 'stop.txt'):
    v = v / 2
    w2k.rkmax = v
    w2k.lmax = 10
    w2k.kmesh = 10000
    w2k.gmax = 12

    sp.run('rm *.scf*', shell=True)
    sp.run('rm *.broyd*', shell=True)
    w2k.init_lapw()
    dt_s = dt.datetime.now()
    w2k.run_scf()
    scf_time = dt.datetime.now() - dt_s
    etot = w2k.get_etot()
    etot_ls.append(etot)
    scf_time_ls.append(scf_time)

    dosname = 'dos' + str(v).replace('.', 'p')
    scfname = 'scf' + str(v).replace('.', 'p')
    w2k.run_dos(dosout, dosname)

    sp.run(['cp', w2k.filepath('.scf'), scfout + scfname + '.scf'])

    np.save(scfout + 'etot.npy', np.array(etot_ls))
    np.save(scfout + 'scf_time.npy', np.array(scf_time_ls))
    an.make_dos_waves([dosout])
```
