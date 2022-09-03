import run_w2k
import make_klist_band as kb
import analyze_w2k as anal
import datetime as dt
import subprocess as sp
import numpy as np
import igorwriter as iw
import os

w2k = run_w2k.W2k("Co2MnGa")
w2k.parallel = 1
w2k.set_parallel(w2k.parallel)
w2k.spol = 1
w2k.spin_ls = ["up"]
w2k.print_parameters()


def mapall():  # calculate all BZ coarsely
    outfol = w2k.case_path + "mapall/"

    sp.call(["mkdir", "-p", outfol + "klist/"])
    sp.call(["mkdir", "-p", outfol + "data/"])
    t_st = dt.datetime.now()
    nx = 100
    ny = 100
    nz = 100
    c = 0
    for kz in range(nz + 1):
        for ky in range(ny + 1):
            name = "map_kz" + str(kz) + "_ky" + str(ky)
            kb.main(
                w2k.filepath(".klist_band"),
                kmeshx=nx + 1,
                kpath=[[0, ky / ny, kz / nz], [1, ky / ny, kz / nz]],
                index_ls=[],
            )
            sp.call(
                [
                    "cp",
                    w2k.filepath(".klist_band"),
                    outfol + "klist/" + name + ".klist_band",
                ]
            )
            w2k.run_band(outfol + "data/", name)
            t_n = dt.datetime.now()
            c += 1
            print("finish : " + str((t_n - t_st) / c * (ny + 1) * (nz + 1) + t_st))


def make_3Dband_npy():
    anal.make_3Dband_array(
        [101, 101],
        "up",
        w2k.case_path + "mapall/data/",
        w2k.case_path + "mapall/data.npy",
    )


def get_NLlist_coarse(ba_l):  # get coarse NL list between selected band
    for ba in ba_l:
        nl = anal.get_NL_list(w2k.case_path + "mapall/data.npy", ba, 0.015)
        nl = rmv_data_xyz_sym(nl)
        nl = nl / 100
        print(nl)
        print(nl.shape)
        np.save(w2k.case_path + "mapall/NL_" + str(ba) + ".npy", nl)


def rmv_data_xyz_sym(ar):  # reduce k points according to xyz symmetry
    ls = list(ar)
    nls = [l for l in ls if l[0] >= l[1] and l[1] >= l[2]]
    ar = np.array(nls)
    return ar


def make_klist_NL(ba_ls):  # make .klist_band files
    def vec2int(vec):
        val = round(vec[0]) + round(vec[1]) * 10000 + round(vec[2]) * 10000**2
        return val

    def int2vec(val):
        vec = [
            np.mod(val, 10000),
            np.floor(np.mod(val, 10000**2) / 10000),
            np.floor(val / 10000**2),
        ]
        vec = [int(round(i)) for i in vec]
        return vec

    for ba in ba_ls:
        nldir = w2k.case_path + "NLs/NL_" + str(ba) + "/"
        nl = np.load(w2k.case_path + "mapall/NL_" + str(ba) + ".npy")
        nl = list(nl)
        km = 900  # maximum number of k points in each .klist_band file
        d = 5000  # density of BZ for fine NL calculation
        fn = 1  # initial value of .klist_band file index
        klist_all = set([])  # initialize set of klist
        k_all = 0  # counter of all k points

        # fine kmesh
        dkx_ls = range(-30, 31)
        dky_ls = range(-25, 26, 5)
        dkz_ls = range(-25, 26, 5)

        prog = 0
        cp = 0
        nn = 0
        nt = dt.datetime.now().second
        pdens = 1

        for rkp in nl:
            for dkz in dkz_ls:
                for dky in dky_ls:
                    for dkx in dkx_ls:
                        kx = rkp[0] * d + dkx
                        ky = rkp[1] * d + dky
                        kz = rkp[2] * d + dkz
                        kl_app = vec2int([kx, ky, kz])
                        if not kl_app in klist_all:
                            if kx >= 0 and kx <= d:
                                if ky >= 0 and ky <= d:
                                    if kz >= 0 and kz <= d:
                                        if kx + ky + kz <= d * 3 / 2:
                                            klist_all.add(kl_app)
                        k_all += 1
                        prog += 1
                        nn = np.floor(
                            prog
                            / (len(nl) * len(dkx_ls) * len(dky_ls) * len(dkz_ls))
                            * 100
                            * pdens
                            * 100
                        ) / (pdens * 100)
                        nsec = dt.datetime.now().second
                        if np.floor(nn * pdens) / pdens > cp or (
                            (float(nsec) % 20) == 0 and nsec != nt
                        ):
                            nt = dt.datetime.now().second
                            cp = (
                                np.floor(
                                    prog
                                    / (
                                        len(nl)
                                        * len(dkx_ls)
                                        * len(dky_ls)
                                        * len(dkz_ls)
                                    )
                                    * 100
                                    * pdens
                                )
                                / pdens
                            )
                            print(str(dt.datetime.now()) + " : " + str(nn) + " %")

        print(len(klist_all), k_all)

        kbout = w2k.case_path + "NLs/NL_" + str(ba) + "/klist/"

        sp.call(["mkdir", "-p", kbout])

        if os.path.exists(nldir + "NL" + str(ba) + "_k_data.npy"):
            data_k = np.load(nldir + "NL" + str(ba) + "_k_data.npy")
            data_k = set([vec2int(v * d) for v in list(data_k)])
            klist_all = klist_all - data_k

            print(len(klist_all))

        klist_out = []
        for kp in klist_all:
            if len(klist_out) > km:
                np.save(kbout + "klist_" + str(fn), np.array(klist_out))
                kb.sonomama(
                    kbout + "klist_" + str(fn) + ".klist_band", klist_out, 5000, 0
                )
                klist_out = []
                fn += 1

            klist_out.append([i / d for i in int2vec(kp)])


def calc_NL_from_klists(ba_ls):  # calculate band dispersion
    stop = 0
    for ba in ba_ls:
        if stop:
            break
        nldir = w2k.case_path + "NLs/NL_" + str(ba) + "/"
        bdir = nldir + "band/"
        kdir = nldir + "klist/"
        sp.call(["mkdir", "-p", bdir])
        fl = os.listdir(kdir)
        fl = [f for f in fl if ".klist_band" in f]
        fl.sort()

        c = 0
        t_st = dt.datetime.now()

        fl = [f for f in fl if not os.path.exists(bdir + f[:-11] + "up.bands.agr")]

        for kbf in fl:
            if os.path.exists(w2k.case_path + "stop.txt"):
                print("stop.txt FILE DETECTED.")
                sp.call(["rm", w2k.case_path + "stop.txt"])
                stop = 1
                break
            sp.call(["cp", kdir + kbf, w2k.filepath(".klist_band")])
            w2k.run_band(bdir, kbf[:-11])
            t_n = dt.datetime.now()
            c += 1
            print("")
            print("FINISH: " + str((t_n - t_st) / c * len(fl) + t_st))
            print(
                "IF YOU WANT TO STOP THIS SCRIPT, MAKE stop.txt FILE IN "
                + w2k.case_path
            )
            print("")


def get_NLlist_fine(ba_ls):  # get fine NL list between selected band
    def sym_xyz(arr, ax):
        narr = arr.copy()
        narr[:, np.mod(ax, 3)] = arr[:, np.mod(ax + 1, 3)]
        narr[:, np.mod(ax + 1, 3)] = arr[:, np.mod(ax, 3)]
        return narr

    def sym_0(arr, ax):
        narr = arr.copy()
        narr[:, ax] = arr[:, ax] * -1
        return narr

    for ba in ba_ls:
        nldir = w2k.case_path + "NLs/NL_" + str(ba) + "/"
        bdir = nldir + "band/"
        kdir = nldir + "klist/"

        fl = os.listdir(kdir)
        fl = [f[:-4] for f in fl if ".npy" in f]
        fl.sort()

        if os.path.exists(nldir + "NL" + str(ba) + "_k_data.npy"):
            out_k = np.load(nldir + "NL" + str(ba) + "_k_data.npy")
            out_e = np.load(nldir + "NL" + str(ba) + "_e_data.npy")
            out_g = np.load(nldir + "NL" + str(ba) + "_g_data.npy")
        else:
            out_k = np.zeros((0, 3))
            out_e = np.zeros((0))
            out_g = np.zeros((0))

        for f in fl:
            print(f)
            kp = np.load(kdir + f + ".npy")
            eng, _ = anal.load_agr(bdir + f + "up.bands.agr")
            eng_1 = eng[ba - 1]
            eng_2 = eng[ba]
            eng_d = eng_2 - eng_1
            eng_a = (eng_2 + eng_1) / 2
            if eng_d.shape[0] == kp.shape[0]:
                out_k = np.concatenate([out_k, kp])
                out_e = np.concatenate([out_e, eng_a])
                out_g = np.concatenate([out_g, eng_d])
            else:
                print("ERROR: wrong data in " + f)

        np.save(nldir + "NL" + str(ba) + "_k_data.npy", out_k)
        np.save(nldir + "NL" + str(ba) + "_e_data.npy", out_e)
        np.save(nldir + "NL" + str(ba) + "_g_data.npy", out_g)

        cutoff = 0.001  # degenerate cutoff parameter

        out_e_1 = out_e
        out_k_1 = out_k
        out_g_1 = out_g

        out_e = []
        out_g = []
        out_k = []

        for i in range(out_k_1.shape[0]):  # extract degenerate points with cutoff
            if out_g_1[i] < cutoff:
                out_e.append(out_e_1[i])
                out_k.append(out_k_1[i])
                out_g.append(out_g_1[i])

        out_k = np.array(out_k)
        out_e = np.array(out_e)
        out_g = np.array(out_g)

        # symmetrize
        out_k1 = np.concatenate([out_k, sym_xyz(out_k, 0)])
        out_e1 = np.concatenate([out_e, out_e])
        out_g1 = np.concatenate([out_g, out_g])

        out_k = np.concatenate([out_k1, sym_xyz(out_k1, 1)])
        out_e = np.concatenate([out_e1, out_e1])
        out_g = np.concatenate([out_g1, out_g1])

        out_k1 = np.concatenate([out_k, sym_xyz(out_k, 2)])
        out_e1 = np.concatenate([out_e, out_e])
        out_g1 = np.concatenate([out_g, out_g])

        out_k = np.concatenate([out_k1, sym_0(out_k1, 0)])
        out_e = np.concatenate([out_e1, out_e1])
        out_g = np.concatenate([out_g1, out_g1])

        out_k1 = np.concatenate([out_k, sym_0(out_k, 1)])
        out_e1 = np.concatenate([out_e, out_e])
        out_g1 = np.concatenate([out_g, out_g])

        out_k = np.concatenate([out_k1, sym_0(out_k1, 2)])
        out_e = np.concatenate([out_e1, out_e1])
        out_g = np.concatenate([out_g1, out_g1])

        np.save(nldir + "NL" + str(ba) + "_k.npy", out_k)
        wave = iw.IgorWave(out_k, name="NL" + str(ba) + "_k")
        wave.save(nldir + "NL" + str(ba) + "_k.ibw")

        np.save(nldir + "NL" + str(ba) + "_e.npy", out_e)
        wave = iw.IgorWave(out_e, name="NL" + str(ba) + "_e")
        wave.save(nldir + "NL" + str(ba) + "_e.ibw")

        np.save(nldir + "NL" + str(ba) + "_g.npy", out_g)
        wave = iw.IgorWave(out_g, name="NL" + str(ba) + "_g")
        wave.save(nldir + "NL" + str(ba) + "_g.ibw")


if __name__ == "__main__":
    mapall()
    make_3Dband_npy()
    get_NLlist_coarse([30, 31])
    make_klist_NL([30, 31])
    calc_NL_from_klists([30, 31])
    get_NLlist_fine([30, 31])
