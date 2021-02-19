import numpy as np


def main(output_name: str, kmeshx: int, kpath: list, index_ls: list = [], d: int = 0, echo: int = 1):
	kplen = []

	for kpi in range(len(kpath) - 1):
		kps = np.array(kpath[kpi])
		kpe = np.array(kpath[kpi + 1])
		if kpi > 0:
			bef = kplen[kpi - 1]
		else:
			bef = 0
		kplen.append(np.linalg.norm(kps - kpe) + bef)

	ind = kplen / kplen[len(kplen) - 1] * (kmeshx - 1)

	ind = [int(round(i)) for i in ind]

	ind.insert(0, 0)

	out_ls = []
	tail = '-8.00 8.00'

	if echo == 1:
		print('OUTPUT ----> ' + output_name)
		print('Index  Label  k-vector')

	for kpi in range(len(kplen)):
		kps = np.array(kpath[kpi])
		kpe = np.array(kpath[kpi + 1])
		kpd = abs(kps - kpe)
		kpd = [i for i in kpd.tolist() if i > 0]
		if len(kpd) > 0:
			minwid = min(kpd)
		i_s = ind[kpi]
		i_ee = ind[kpi + 1]
		if echo == 1:
			if kpi < len(index_ls):
				head = index_ls[kpi]
			else:
				head = ''
			print('{:<7}'.format(i_s) + '{:7}'.format(head) + str(kps))
		if kpi == len(kplen) - 1:
			i_e = i_ee + 1
			if echo == 1:
				if kpi < len(index_ls) - 1:
					head = index_ls[kpi + 1]
				else:
					head = ''
				print('{:<7}'.format(i_ee) + '{:7}'.format(head) + str(kpe))
		else:
			i_e = i_ee

		if d > 0:
			dnum = int(round(d))
		else:
			dnum = int(round((i_ee - i_s) / minwid))

		if kpi < len(index_ls):
			head = index_ls[kpi]
		for i in range(i_s, i_e):
			if i == i_ee and kpi < len(index_ls) - 1:
				head = index_ls[kpi + 1]
			sc = (i - i_s) / (i_ee - i_s)
			kx = int(round((kps[0] * (1 - sc) + kpe[0] * sc) * dnum))
			ky = int(round((kps[1] * (1 - sc) + kpe[1] * sc) * dnum))
			kz = int(round((kps[2] * (1 - sc) + kpe[2] * sc) * dnum))
			line = ['{:10}'.format(head), '{:5}'.format(kx), '{:5}'.format(ky), '{:5}'.format(kz), '{:5}'.format(dnum),
					'  2.0', tail]
			head = ''
			tail = ''
			out_ls.append(line)
	with open(output_name, 'w') as f:
		for lines in out_ls:
			print(''.join(lines), file=f)
		print('END', file=f)


def sonomama(output_name: str, kpath: list, d: int, echo: int):
	out_ls = []
	tail = '-8.00 8.00'

	if echo == 1:
		print('OUTPUT ----> ' + output_name)

	for kpi in range(len(kpath)):
		kx = int(round(kpath[kpi][0] * d))
		ky = int(round(kpath[kpi][1] * d))
		kz = int(round(kpath[kpi][2] * d))
		line = ['{:10}'.format(''), '{:5}'.format(kx), '{:5}'.format(ky), '{:5}'.format(kz), '{:5}'.format(d), '  2.0',
				tail]
		head = ''
		tail = ''
		out_ls.append(line)
	with open(output_name, 'w') as f:
		for lines in out_ls:
			print(''.join(lines), file=f)
		print('END', file=f)


def fcc_temp(name, n):
	kpath = [[1, 0.5, 0], [0.5, 0.5, 0.5], [0, 0, 0], [1, 0, 0], [1, 0.5, 0], [0.75, 0.75, 0], [1, 1, 0],
			 [0.75, 0.75, 0], [0, 0, 0]]
	index = ['W', 'L', 'G', 'X', 'W', 'K', 'X2', 'K', 'G']
	main(name, n, kpath, index, 0, 1)
