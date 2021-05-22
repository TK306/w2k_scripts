import run_w2k
import analyze_w2k as an
import make_klist_band as kb
import subprocess as sp
from igorwriter import IgorWave as iw
import datetime as dt  # optional


def run():
	session = 'Co2MnGa'
	w2k = run_w2k.W2k(session)
	w2k.spol = 1
	w2k.spin_ls = ['up', 'dn']

	w2k.set_ef_insp()

	outputdpath = w2k.case_path + 'kxkymap/'
	sp.run(['mkdir', '-p', outputdpath])

	kxn = 101
	kyn = 101

	tst = dt.datetime.now()  # optional

	for ky in range(kyn):
		kb.main(w2k.filepath('.klist_band'), kxn, [[0, ky / (kyn - 1), 0], [1, ky / (kyn - 1), 0]], [])
		name = 'ky_' + str(ky)
		w2k.run_band(outputdpath, name)
		tn = dt.datetime.now()  # optional
		print('FINISH : ' + str(tst + (tn - tst) / (ky + 1) * kyn))  # optional

def anal():
	session = 'Co2MnGa'
	w2k = run_w2k.W2k(session)

	outputdpath = w2k.case_path + 'kxkymap/'

	volup, voldn, e_dic = an.make_vox_vol(-3, 1, 0.01, 101, 101, outputdpath, 'ky_')
	waveup = iw(volup, name='upspin')
	waveup.set_dimscale('x', e_dic['Offset'], e_dic['Delta'], 'eV')
	wavedn = iw(voldn, name='dnspin')
	wavedn.set_dimscale('x', e_dic['Offset'], e_dic['Delta'], 'eV')

	waveup.save(outputdpath + 'bands_upspin.ibw')
	wavedn.save(outputdpath + 'bands_dnspin.ibw')

if __name__ == '__main__':
	run()
	anal()
