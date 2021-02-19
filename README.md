# w2k_scripts
WIEN2k第一原理プログラムによるバンド計算を行うスクリプトです。
* run_w2k.py
* make_klist_band.py
* analyze_w2k.py

以上が基本となるスクリプトで、それぞれ独立に動きます。
これらを組み合わせて様々な計算が可能です。

例として、
* NL_calc.py

を添付しています。

## run_w2k.py
WIEN2k wrapper的なコードです。

### 準備
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

## 使用例
### kx-ky等エネルギー面を101 x 101点計算するコード
run_w2k.py、make_klist_band.pyと同じ階層にexample.pyを作成します。
#### 色々インポート
run_w2k.pyとmake_klist_band.pyをインポートします。

```python
import run_w2k
import make_klist_band as kb
```

必要なパッケージをインポートします。
インストールされていない場合、`$pip install subprocess`などでインストールできます。
詳しくは自分で調べることをおすすめします。

```python
import subprocess as sp
import datetime as dt # optional
```

#### クラスの呼び出し
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

#### .inspファイルの作成
.inspファイルにSCF計算で出力されるフェルミ準位を入れるコードです。
.inspファイルをSRC_templateからコピーし、`0.xxx`の部分を.scfファイルから読み取ったフェルミエネルギーで置換しています。

```python
w2k.set_ef_insp()
```

#### 出力ディレクトリの作成
バンド計算結果.bands.agrファイルを出力するディレクトリを作成します。
クラス変数`w2k.case_path`にセッションディレクトリのフルパスが入っているので、これを利用します。

```
outputdpath = w2k.case_path + 'kxkymap/'
sp.run(['mkdir', '-p', outputdpath])
```

#### コード全体

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
  kb.main(w2k.filepath('.klist_band'), kxn, [[0, ky / 100, 0], [1, ky / 100, 0]], [])
  name = 'ky_' + str(ky)
  w2k.run_band(outputdpath, name)
  tn = dt.datetime.now() # optional
  print('FINISH : ' + str(tst + (tn - tst) / (ky + 1) * kyn)) # optional
```
