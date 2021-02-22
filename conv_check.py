import run_w2k
import analyze_w2k as an
import numpy as np
import os
import datetime as dt
import subprocess as sp
import igorwriter as iw

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
v_start = 5
v_step = 0.5
v_end = 10
for v in np.arange(v_start, v_end + v_step / 2, v_step):
	if not os.path.exists(w2k.case_path + 'stop.txt'):
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
		scf_time_ls.append(scf_time.seconds)

		vstr = str(v).replace('.', 'p')
		dosname = 'dos' + vstr
		scfname = 'scf' + vstr
		w2k.run_dos(dosout, dosname)

		sp.run(['cp', w2k.filepath('.scf'), scfout + scfname + '.scf'])

		etotw = iw.IgorWave(np.array(etot_ls), name='etot')
		scftw = iw.IgorWave(np.array(scf_time_ls), name='scftime')
		etotw.set_dimscale('x', v_start, v_step, '')
		scftw.set_dimscale('x', v_start, v_step, '')
		etotw.set_datascale('eV')
		scftw.set_datascale('sec')
		with open(convdir + 'scflog.itx', 'w') as f:
			etotw.save_itx(f)
			scftw.save_itx(f)
		an.make_dos_waves([dosout])
