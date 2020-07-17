#!/usr/bin/python3

import numpy as np
import matplotlib.pyplot as plt


def main(output_name: str, kmeshx: int, kpath: list, index_ls: list, d: int, echo: int):

	kplen = []

	for kpi in range(len(kpath) - 1):
		kps = np.array(kpath[kpi])
		kpe = np.array(kpath[kpi+1])
		if kpi > 0:
			bef = kplen[kpi - 1]
		else:
			bef = 0
		kplen.append(np.linalg.norm(kps-kpe) + bef)

	ind = kplen / kplen[len(kplen) - 1] * (kmeshx - 1)

	ind = [int(round(i)) for i in ind]

	ind.insert(0,0)

	out_ls = []
	tail = '-8.00 8.00'

	if echo == 1:
		print('OUTPUT ----> '+output_name)
		print('Index  Label  k-vector')

	for kpi in range(len(kplen)):
		kps = np.array(kpath[kpi])
		kpe = np.array(kpath[kpi+1])
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
					head = index_ls[kpi+1]
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
				head = index_ls[kpi+1]
			sc = (i - i_s) / (i_ee - i_s)
			kx = int(round((kps[0] * (1-sc) + kpe[0] * sc) * dnum))
			ky = int(round((kps[1] * (1-sc) + kpe[1] * sc) * dnum))
			kz = int(round((kps[2] * (1-sc) + kpe[2] * sc) * dnum))
			line = ['{:10}'.format(head), '{:5}'.format(kx), '{:5}'.format(ky), '{:5}'.format(kz), '{:5}'.format(dnum), '  2.0', tail]
			head = ''
			tail = ''
			out_ls.append(line)
	with open(output_name, 'w') as f:
		for lines in out_ls:
			print(''.join(lines), file = f)
		print('END', file=f)
		
	
def plot(kmeshx: int, kpath: list, d: int):

	kplen = []

	for kpi in range(len(kpath) - 1):
		kps = np.array(kpath[kpi])
		kpe = np.array(kpath[kpi+1])
		if kpi > 0:
			bef = kplen[kpi - 1]
		else:
			bef = 0
		kplen.append(np.linalg.norm(kps-kpe) + bef)

	ind = kplen / kplen[len(kplen) - 1] * (kmeshx - 1)

	ind = [int(round(i)) for i in ind]

	ind.insert(0,0)

	out_ls = []

	for kpi in range(len(kplen)):
		kps = np.array(kpath[kpi])
		kpe = np.array(kpath[kpi+1])
		kpd = abs(kps - kpe)
		kpd = [i for i in kpd.tolist() if i > 0]
		if len(kpd) > 0:
			minwid = min(kpd)
		i_s = ind[kpi]
		i_ee = ind[kpi + 1]
		
		if kpi == len(kplen) - 1:
			i_e = i_ee + 1
		else:
			i_e = i_ee

		if d > 0:
			dnum = int(round(d))
		else:
			dnum = int(round((i_ee - i_s) / minwid))

		for i in range(i_s, i_e):
			sc = (i - i_s) / (i_ee - i_s)
			kx = round((kps[0] * (1-sc) + kpe[0] * sc) * dnum) / dnum
			ky = round((kps[1] * (1-sc) + kpe[1] * sc) * dnum) / dnum
			kz = round((kps[2] * (1-sc) + kpe[2] * sc) * dnum) / dnum
			line = [kx,ky,kz]
			out_ls.append(line)

	data = np.array(out_ls)
	data = data.T
	kx = data[0]
	ky = data[1]
	kz = data[2]

	fig = plt.figure()
	ax = fig.add_subplot(1,1,1)

	ax.plot(kx, label = 'x')
	ax.plot(ky, label = 'y')
	ax.plot(kz, label = 'z')
	fig.legend()

	plt.show()


if __name__ == '__main__':

	name = "./GaAs_MLWF.klist_band"
	points = 11
	d = 0 # 0: Auto
	kpath1 = [[0.5,0,0],[0,0,0],[0.5,0.5,0],[5/8,5/8,1/4],[0,0,0]]
	index1 = ['L','G','X','U','G']

	kpath2 = [[0,0,0],[1,1,0]]
	index2 = ['G','X2']

	kpath3 = [[0,0,0],[1,0,0]]
	index3 = ['G','X']

	kpath4 = [[0.5,0,1],[0.5,0.5,0.5],[0,0,0],[0,0,1],[0.5,0,0.5],[0.75,0,0.75],[0,0,0]]
	index4 = ['W','L','G','X','W','K','G']

	main(name,points,kpath4,index4,d,1)

	#plot(points,kpath4,d)
