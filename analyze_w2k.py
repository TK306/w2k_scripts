import numpy as np
import subprocess as sp
from igorwriter import IgorWave
import os


def load_agr(path):  # output: ndarray energy(band,kx), weight(band,kx)
	if not path.endswith('.agr'):
		return 0
	with open(path, 'r') as f:
		lines = f.readlines()
	ba = 1
	ba_ls = [i for i in range(1, 600)]
	eng = []
	wei = []
	n = 0
	l = 0
	for line in lines:
		line = line.lstrip()
		if line.startswith('@'):
			pass
		elif line.startswith('#'):
			if (line.startswith('# bandindex:')):
				if ba in ba_ls:
					eng.append([])
					wei.append([])
		elif line.startswith('&'):
			if ba in ba_ls:
				n += 1
			ba += 1
		elif len(line) > 0:
			if ba in ba_ls:
				ls = line.split()
				try:
					lsf = [float(l) for l in ls]
				except ValueError:
					print('Wrong Data in ' + path + ' # bandindex: ' + str(ba))
				if len(lsf) == 3:
					eng[n].append(lsf[1])
					wei[n].append(lsf[2])
				else:
					print('Wrong Data in ' + path + ' # bandindex: ' + str(ba))
		l += 1
	energy = np.array(eng)
	weight = np.array(wei)
	return energy, weight


def load_dos(path):
	if not '.dos' in path:
		return 0

	if not os.path.isfile(path):
		return 0

	with open(path, 'r') as f:
		lines = f.readlines()

	ind = lines[2].split()
	del lines[0:3]
	del ind[0]

	dos = {}

	for i in ind:
		dos[i] = []

	for l in lines:
		ll = l.split()
		for i in range(len(ind)):
			dos[ind[i]].append(float(ll[i]))

	for i in ind:
		dos[i] = np.array(dos[i])

	return dos


def make_vox_vol(e_s, e_e, e_st, kx_n, ky_n, datafol, filename):
	e_n = int(round((e_e - e_s) / e_st) + 1)

	volup = np.zeros((e_n, kx_n, ky_n))
	voldn = np.zeros((e_n, kx_n, ky_n))

	for ky in range(ky_n):
		for s in ['up', 'dn']:
			datapath = datafol + filename + str(ky) + s + '.bands.agr'
			agr, wei = load_agr(datapath)
			for band in range(agr.shape[0]):
				for kx in range(agr.shape[1]):
					if (agr[band, kx] >= e_s and agr[band, kx] <= e_e):
						ve = int(round((agr[band, kx] - e_s) / e_st))
						if s == 'up':
							volup[ve, kx, ky] = 1
						elif s == 'dn':
							voldn[ve, kx, ky] = 1

	return volup, voldn, {'Offset': e_s, 'Delta': e_st, 'Size': e_n}


def make_3Dband_array(kml, spin, dfpath, savepath):  # kml: [knumber y, knumber z]
	dims = len(kml) + 1
	kmy = kml[0]

	if dims == 3:
		kmz = kml[1]
	else:
		kmz = 1

	for kz in range(kmz):
		print(str(kz) + ' / ' + str(kmz - 1))
		for ky in range(kmy):
			path = dfpath + 'map_kz' + str(kz) + '_ky' + str(ky) + spin + '.bands.agr'
			agr, wei = load_agr(path)
			if len(agr.shape) < 2:
				print(agr.shape)
			agrv = np.expand_dims(agr, 0)
			agrv = np.expand_dims(agrv, 0)

			if ky == 0:
				vol = agrv
			else:
				if (vol.shape[2] > agrv.shape[2]):
					nans = np.empty((agrv.shape[0], agrv.shape[1], vol.shape[2] - agrv.shape[2], agrv.shape[3]))
					nans[:] = np.nan
					agrv = np.append(agrv, nans, axis=2)
				elif (vol.shape[2] < agrv.shape[2]):
					nans = np.empty((vol.shape[0], vol.shape[1], agrv.shape[2] - vol.shape[2], vol.shape[3]))
					nans[:] = np.nan
					vol = np.append(vol, nans, axis=2)

				vol = np.concatenate([vol, agrv], 1)

		if kz == 0:
			ch = vol
		else:
			if (vol.shape[2] > ch.shape[2]):
				nans = np.empty((ch.shape[0], ch.shape[1], vol.shape[2] - ch.shape[2], ch.shape[3]))
				nans[:] = np.nan
				ch = np.append(ch, nans, axis=2)
			elif (vol.shape[2] < ch.shape[2]):
				nans = np.empty((vol.shape[0], vol.shape[1], ch.shape[2] - vol.shape[2], vol.shape[3]))
				nans[:] = np.nan
				vol = np.append(vol, nans, axis=2)

			ch = np.concatenate([ch, vol], 0)

	del vol
	ch = np.squeeze(ch)
	np.save(savepath, ch)


def get_NL_list(npypath, bandindex, cutoff):
	ch = np.load(npypath)
	print('npy data loaded')
	ba1 = bandindex - 1
	ba2 = bandindex
	if len(ch.shape) == 4:
		ch = np.transpose(ch, (2, 3, 1, 0))
		if ch.shape[0] >= ba2:
			dif = ch[ba2, :, :, :] - ch[ba1, :, :, :]
			NL_list = np.where((dif < cutoff))
			NL_list = np.array(NL_list).T
		else:
			print('Bandindex out of range')
			print(ch.shape)
			NL_list = 0
	else:
		print('3D band .npy data required')
		NL_list = 0

	return NL_list


def make_3Dband_ibw(npypath, savepath, name, e_s, e_e):
	ch = np.load(npypath)
	print('npy data loaded')
	dims = len(ch.shape) - 1
	ky_s = -1
	ky_e = 1
	kz_s = -1
	kz_e = 1

	sp.call(['mkdir', '-p', savepath])
	if dims == 2:
		ch = np.transpose(ch, (1, 2, 0))
		print(ch.shape)
		ch = np.concatenate([np.flip(ch, 1), np.delete(ch, 0, 1)], 1)
		ch = np.concatenate([np.flip(ch, 2), np.delete(ch, 0, 2)], 2)
	elif dims == 3:
		ch = np.transpose(ch, (2, 3, 1, 0))
		ch = np.concatenate([np.flip(ch, 1), np.delete(ch, 0, 1)], 1)
		ch = np.concatenate([np.flip(ch, 2), np.delete(ch, 0, 2)], 2)
		ch = np.concatenate([np.flip(ch, 3), np.delete(ch, 0, 3)], 3)
		kz_n = ch.shape[3]
		kz_st = (kz_e - kz_s) / (kz_n - 1)
	print('concatenate end')
	ky_n = ch.shape[1]
	ky_st = (ky_e - ky_s) / (ky_n - 1)

	for ba in range(ch.shape[0]):
		out = savepath + name + '_Band' + str(
			ba + 1) + '.ibw'
		if (np.amax(ch[ba]) >= e_s and np.amin(ch[ba]) <= e_e):
			wave = IgorWave(ch[ba], name=name + '_Band' + str(ba + 1))
			wave.set_dimscale('x', ky_s, ky_st, '2pi/a')
			wave.set_dimscale('y', ky_s, ky_st, '2pi/a')
			if dims == 3:
				wave.set_dimscale('z', kz_s, kz_st, '2pi/a')
			wave.save(out)
			print('save : ' + out)


def make_dos_waves(path_list):
	for rt in path_list:
		print(rt)

		fl = os.listdir(rt)
		fl = [f for f in fl if '.dos' in f]
		fl.sort()

		fm = []
		head = ''
		for f in fl:
			if not f.split('.')[0] == head:
				head = f.split('.')[0]
				fm.append([])
			fm[len(fm) - 1].append(f)

		print(fm)

		for fl in fm:
			ws = {}
			head = fl[0].split('.')[0]
			for f in fl:
				sp = f.split('eV')[1]
				if sp == 'up':
					r = 1
				elif sp == 'dn':
					r = -1
				en = 0
				wp = rt + head + '_dos.itx'
				path = rt + f
				dos = load_dos(path)
				for ky in dos.keys():
					ws[ky + sp] = dos[ky] * r

			print(ws.keys())
			el = ws['ENERGYup']

			e_s = el[0]
			e_n = el.shape[0]
			e_e = el[e_n - 1]
			e_st = (e_e - e_s) / (e_n - 1)

			with open(wp, 'w') as fp:
				for ky in ws.keys():
					if 'ENERGY' in ky:
						pass
					else:
						wn = head + '_' + ky.replace(':', '_')
						wn = wn.replace('-', '_')
						wave = IgorWave(ws[ky], name=wn)
						wave.set_dimscale('x', e_s, e_st, 'eV')
						wave.save_itx(fp)
		print(len(fm))
