import numpy as np
from fuzzy_partition import weighted_dist


# v= (G,W,U)
def adequacy(v, m, diss_matrices):
	"""
	Função calcula resultado de função objetivo, a ser minimizada. Onde:
		v[0] = G, matriz de protótipos 
		v[1] = W, matriz de pesos  
		v[2] = U, matriz de grau de pertencimento
		m = 1.6,
		diss_matrices = matrizes de dissimilaridade  
	"""
	K = len(v[1])
	n = len(v[2])
	sum = 0;

	for k in range(K):
		for i in range(n):
			sum += v[2][i][k]**m * weighted_dist(v[1][k], i, v[0][k], diss_matrices)
	
	return sum

if __name__ == '__main__':
	np.random.seed(42)

	diss_matrices = np.random.rand(3,9,9) 


	G = [[7, 8, 3],[4, 5, 6]]

	W = [
		[1., 1., 1.,],
		[1., 1., 1.,]
	]
	U = [
		[0.76046769, 0.23953231],
		[0.86188325, 0.13811675],
		[0.23953231, 0.76046769]
	]
	v=[G,W,U]

	print(adequacy(v, 1.6, diss_matrices))
