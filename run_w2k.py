import subprocess
import numpy as np
import os
from typing import List

# directory path string must finish with "/"


class W2k:
    def __init__(self, case_g: str) -> None:
        """sessionに対応するインスタンス生成.

        Args:
            case_g (str): sessionフォルダの名前.
        """
        self.case = case_g  # session name
        self.temp_path = "/usr/local/WIEN2k_17.1/SRC_templates/"  # template file path
        self.w2k_user = (
            "/Users/kounotakashi/WIEN2k_17.1_user/"  # wien2k user folder path
        )
        self.case_path = self.w2k_user + self.case + "/"  # session path

        self.so = 0  # spin orbit on: 1, off: 0
        self.orb = 0  # +U on: 1, off: 0
        self.spol = 1  # spin polarized calculation on: 1, off: 0
        self.spin_ls = ["up", "dn"]
        self.parallel = 1  # parallel on: >1, off: 1

        self.rkmax = 7
        self.__lmax = 10
        self.__gmax = 12
        self.kmesh = 10000

        self.scf_ec = 0.0001  # energy convergence (Ry)
        self.scf_cc = None  # charge convergence (e)
        self.ni = 1  # -NI option

    def set_parallel(self, p: int) -> None:
        """並列計算を設定.

        Args:
            p (int): 並列数.
        """
        self.parallel = p
        machinespath = self.case_path + ".machines"

        if p > 1:
            subprocess.call(["cp", self.temp_path + ".machines", machinespath])
            if p > 2:
                with open(machinespath, "r") as f:
                    ms = f.read()

                ms = ms.replace("1:localhost\n" * 2, "1:localhost\n" * p)

                with open(machinespath, "w") as f:
                    f.write(ms)

    def print_parameters(self) -> None:
        """インスタンスに設定されているパラメータをprint."""
        for key, value in self.__dict__.items():
            print(key, ":", value)

    def cp_from_temp(self, ext: str) -> None:
        """テンプレートファイルをsessionにコピー.

        Args:
            ext (str): コピーしたいテンプレートファイルの拡張子
        """
        if not ext.startswith("."):
            ext = f".{ext}"
        subprocess.call(
            ["cp", self.temp_path + "case" + ext, self.case_path + self.case + ext]
        )

    def get_ef(self) -> float:
        """.scfファイルからFermi Energyを抜き出す.

        Returns:
            float: Fermi Energy (eV)
        """
        with open(self.filepath(".scf"), "r") as f:
            l = f.readlines()
        l0 = [i for i in l if i.startswith(":FER")]
        l = l0[len(l0) - 1]
        l0 = l.split()
        ef = float(l0[len(l0) - 1])
        return ef

    def get_etot(self) -> float:
        """.scfファイルからTotal Energyを抜き出す.

        Returns:
            float: Total Energy (eV)
        """
        with open(self.filepath(".scf"), "r") as f:
            l = f.readlines()
        l0 = [i for i in l if i.startswith(":ENE")]
        l = l0[len(l0) - 1]
        l0 = l.split()
        etot = float(l0[len(l0) - 1])
        return etot

    @property
    def lmax(self) -> float:
        return self.__lmax

    @lmax.setter
    def lmax(self, val: float) -> None:
        """SCF計算のlmax値を指定し, .in1ファイルに書き込む.

        Args:
            val (float): 設定値

        ToDo:
            * 小数点以下桁数に上限を設けないと, wien2k実行時にエラーが起きるかも？
        """
        path = self.filepath(".in1")
        with open(path, "r") as f:
            s = f.readlines()

        for l in range(len(s)):
            if "R-MT*K-MAX" in s[l]:
                out = s[l].split()
                out[1] = str(val)
                s[l] = " ".join(out)
            if not s[l].endswith("\n"):
                s[l] += "\n"

        s = "".join(s)

        with open(path, "w") as f:
            f.write(s)

        self.__lmax = val

    @property
    def gmax(self) -> float:
        return self.__gmax

    @gmax.setter
    def gmax(self, val: float) -> None:
        """SCF計算のGmax値を指定し, .in2ファイルに書き込む.

        Args:
            val (float): 設定値

        ToDo:
            * 小数点以下桁数に上限を設けないと, wien2k実行時にエラーが起きるかも？
        """
        path = self.filepath(".in2")
        with open(path, "r") as f:
            s = f.readlines()

        for l in range(len(s)):
            if "GMAX" in s[l]:
                out = s[l].split()
                out[0] = str(val)
                s[l] = " ".join(out)
            if not s[l].endswith("\n"):
                s[l] += "\n"

        s = "".join(s)

        with open(path, "w") as f:
            f.write(s)

        self.__gmax = val

    def init_lapw(self) -> None:
        """initializeを実行する."""
        os.chdir(self.case_path)
        init_run = [
            "init_lapw",
            "-b",
            "-vxc",
            "13",
            "-ecut",
            "-6.0",
            "-rkmax",
            str(self.rkmax),
            "-numk",
            str(int(round(self.kmesh))),
        ]

        if self.spol:
            init_run.insert(2, "-sp")

        print("run " + " ".join(init_run))
        subprocess.run(init_run)

    def set_ef_insp(self):  # set ef parameter for x_lapw spaghetti
        self.cp_from_temp(".insp")
        with open(self.filepath(".insp"), "r") as f:
            s = f.read()

        s = s.replace("0.xxxx", str(self.get_ef()))

        with open(self.filepath(".insp"), "w") as f:
            f.write(s)

    def filepath(self, ext: str) -> str:
        """指定した拡張子を持つファイルのFull Pathを取得する.

        Args:
            ext (str): 拡張子

        Returns:
            str: Full Path
        """
        if not ext.startswith("."):
            ext = f".{ext}"
        return self.case_path + self.case + ext

    def BZinside(self, v: float) -> float:
        """入力値を0から1の値に規格化する.
        端は折りたたまれる.

        Args:
            v (float): 入力値

        Returns:
            float: 出力値
        """
        v = np.mod(v, 2)
        if v > 1:
            v = 2 - v
        return v

    def mod_insp_weight(self, atom: int, orb: int) -> None:
        """.inspファイルにatomとorbを書き込む.

        Args:
            atom (int): 元素を指定する整数
            orb (int): 軌道を指定する変数
        """
        path = self.filepath(".insp")

        with open(path, "r") as f:
            s = f.readlines()

        for l in range(len(s)):
            if "jatom, jcol, size" in s[l]:
                out = s[l].split()
                out[0] = str(atom)
                out[1] = str(orb)
                s[l] = " ".join(out)

        s = "".join(s)

        with open(path, "w") as f:
            f.write(s)

    def run_scf(self) -> None:
        """SCF計算を実行する."""
        so = self.so
        orb = self.orb
        p = self.parallel
        spol = self.spol

        ec = self.scf_ec
        cc = self.scf_cc
        ni = self.ni

        if spol:
            run_l = ["runsp_lapw", "-ec", str(ec)]
        else:
            run_l = ["run_lapw", "-ec", str(ec)]

        if not cc == None:
            run_l.append("-cc").append(str(cc))

        if p > 1:
            run_l.append("-p")

        if so:
            run_l.insert(1, "-so")

        if orb:
            run_l.insert(1, "-orb")

        if ni:
            run_l.append("-NI")

        os.chdir(self.case_path)

        subprocess.run(run_l)

    def restore_lapw(self, name: str) -> None:
        """SCF計算結果を呼び出す.

        Args:
            name (str): 保存名.
        """
        os.chdir(self.case_path)
        subprocess.run(["restore_lapw", name])

    def run_dos(self, outfol: str, name: str, int_list: List[str] = ["total"]) -> None:
        """DOS計算実行.

        Args:
            outfol (str): 出力フォルダパス
            name (str): 計算結果ファイル名
            int_list (List[str], optional): 計算したい軌道成分のリスト. デフォルト値=["total"].
        """
        so = self.so
        orb = self.orb
        p = self.parallel
        spol = self.spol

        os.chdir(self.case_path)

        if not outfol.startswith(self.case_path):
            outfol = self.case_path + outfol

        run_lapw1 = ["x_lapw", "lapw1"]
        run_lapw2 = ["x_lapw", "lapw2", "-qtl"]
        run_tetra = ["x_lapw", "tetra"]

        if so:
            run_lapw2.append("-so")

        if orb:
            run_lapw1.append("-orb")

        if p > 1:
            run_lapw1.append("-p")
            run_lapw2.append("-p")
            run_tetra.append("-p")

        if spol:
            for spin in self.spin_ls:
                run_lapw1s = run_lapw1 + ["-" + spin]
                print("run " + " ".join(run_lapw1s))
                subprocess.run(run_lapw1s)
            for spin in self.spin_ls:
                run_lapw2s = run_lapw2 + ["-" + spin]
                print("run " + " ".join(run_lapw2s))
                subprocess.run(run_lapw2s)
        else:
            print("run " + " ".join(run_lapw1))
            subprocess.run(run_lapw1)
            print("run " + " ".join(run_lapw2))
            subprocess.run(run_lapw2)

        print("run " + " ".join(["configure_int_lapw", "-b"] + int_list + ["END"]))
        subprocess.run(["configure_int_lapw", "-b"] + int_list + ["END"])

        if spol:
            for spin in self.spin_ls:
                run_tetras = run_tetra + ["-" + spin]
                print("run " + " ".join(run_tetras))
                subprocess.run(run_tetras)
        else:
            print("run " + " ".join(run_tetra))
            subprocess.run(run_tetra)

        subprocess.call(["mkdir", "-p", outfol])

        if spol:
            sp = len(self.spin_ls)
        else:
            sp = 1
        for s in range(sp):
            if spol:
                spin = self.spin_ls[s]
            else:
                spin = ""
            n = 1
            while 1:
                path = self.filepath(".dos" + str(n) + "eV" + spin)
                savepath = outfol + name + ".dos" + str(n) + "eV" + spin
                if os.path.exists(path):
                    subprocess.call(["cp", path, savepath])
                else:
                    break
                n += 1

    def run_band(
        self,
        outfol: str,
        name: str,
        qtl: int = 0,
        qtl_ls: List[List[int]] = [[1, 0]],
        atom_ls: List[str] = [""],
        orbital_ls: List[str] = [""],
    ) -> None:
        """バンド計算を実行.

        Args:
            outfol (str): 出力フォルダパス
            name (str): 計算結果ファイル名
            qtl (int, optional): 重み付け有無(たぶん). デフォルト値=0.
            qtl_ls (List[List[int]], optional): 重み付けしたい[元素, 軌道]のリスト(たぶん). デフォルト値=[[1, 0]].
            atom_ls (List[str], optional): 出力を見やすくするための元素名. 指定しない場合自動で命名される.
            orbital_ls (List[str], optional): 出力を見やすくするための軌道名. 指定しない場合自動で命名される.
        """
        os.chdir(self.case_path)

        if not outfol.startswith(self.case_path):
            outfol = self.case_path + outfol

        so = self.so
        orb = self.orb
        spol = self.spol
        p = self.parallel

        if not os.path.exists(self.filepath(".insp")):  # make .insp file if not exist
            self.set_ef_insp()
            print(".insp file made")

        run_lapw1 = ["x_lapw", "lapw1", "-band"]
        run_lapwso = ["x_lapw", "lapwso"]
        run_lapw2 = ["x_lapw", "lapw2", "-band", "-qtl"]
        run_spag = ["x_lapw", "spaghetti"]

        if p > 1:
            run_lapw1.insert(2, "-p")
            run_lapw2.insert(2, "-p")
            run_lapwso.insert(2, "-p")
            run_spag.insert(2, "-p")

        if orb:
            run_lapw1.append("-orb")
            run_lapwso.append("-orb")
            run_lapw2.append("-orb")
            run_spag.append("-orb")

        if so:
            run_lapw2.append("-so")
            run_spag.append("-so")

        if qtl:
            if not orb:
                run_lapwso.append("-orb")

        if spol:
            if so:
                run_lapwso.append("-up")
                run_spag.append("-up")

        if spol:
            for spin in self.spin_ls:
                run_lapw1s = run_lapw1 + ["-" + spin]
                print("run " + " ".join(run_lapw1s))
                subprocess.run(run_lapw1s)
        else:
            print("run " + " ".join(run_lapw1))
            subprocess.run(run_lapw1)

        if so:
            print("run " + " ".join(run_lapwso))
            subprocess.run(run_lapwso)

        if qtl:
            print("run " + " ".join(run_lapw2))
            subprocess.run(run_lapw2)

        subprocess.call(["mkdir", "-p", outfol])

        if qtl == 0:
            qtl_ls = [[0, 1]]

        for q in qtl_ls:
            self.mod_insp_weight(q[0], q[1])
            if spol:
                run_spags = run_spag
                for spin in self.spin_ls:
                    run_spags = run_spag + ["-" + spin]
                    print(
                        "run "
                        + " ".join(run_spags)
                        + " / .insp : "
                        + " ".join(str(v) for v in q)
                    )
                    subprocess.run(run_spags)
            else:
                print(
                    "run "
                    + " ".join(run_spag)
                    + " / .insp : "
                    + " ".join(str(v) for v in q)
                )
                subprocess.run(run_spag)

            if qtl:
                if len(atom_ls) >= q[0]:
                    atom_name = atom_ls[q[0]]
                else:
                    atom_name = "Atom" + str(q[0])

                if len(orbital_ls) >= q[1]:
                    orb_name = orbital_ls[q[1]]
                else:
                    orb_name = "Orb" + str(q[1])
                name = atom_name + orb_name + "_" + name
            else:
                name = name

            if spol:
                if so:
                    subprocess.call(
                        [
                            "cp",
                            self.filepath(".bandsup.agr"),
                            outfol + name + ".bands.agr",
                        ]
                    )
                else:
                    for spin in self.spin_ls:
                        subprocess.call(
                            [
                                "cp",
                                self.filepath(".bands" + spin + ".agr"),
                                outfol + name + spin + ".bands.agr",
                            ]
                        )
            else:
                subprocess.call(
                    ["cp", self.filepath(".bands.agr"), outfol + name + ".bands.agr"]
                )
