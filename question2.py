import sys, os, warnings
import numpy as np
import seaborn as sns
import scipy.stats
import matplotlib.pyplot as plt
from sklearn.naive_bayes import GaussianNB
from utils.normalized_dissimilarity import load_normalized
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import GridSearchCV
from scipy.stats import wilcoxon
#Intervalo de confiança e estimativa pontual
def mean_confidence_interval(data, confidence=0.95):
	a = 1.0 * np.array(data)
	n = len(a)
	m, se = np.mean(a), scipy.stats.sem(a)
	h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
	return m, m-h, m+h

def main():
	path = 'output/question-2'
	os.path.exists(path) or os.makedirs(path)

	L = 3 #numero de views
	K = 10 #numero de classes

	D_matrices = load_normalized(
		list_files=('mfeat-fac', 'mfeat-fou', 'mfeat-kar')
		# list_files=('mfeat-fac-test', 'mfeat-fou-test', 'mfeat-kar-test')
	)

	true_labels = np.recfromtxt('output/question-1/crisp-vector')
	# true_labels = np.recfromtxt('output/question-1/true-labels')

	prob_priori = np.zeros(K)
	for i in range(0,K):
		prob_priori[i] = np.count_nonzero(true_labels==i) / true_labels.shape[0]

	np.savetxt('%s/prob-priori'%(path), prob_priori, fmt='%.7f')

	#GRID SEARCH CROSS VALIDATION - ENCONTRAR MELHOR NUMERO DE VIZINHOS
	kb_1 = KNeighborsClassifier()
	kb_2 = KNeighborsClassifier()
	kb_3 = KNeighborsClassifier()

	k_range = list(range(1,31))
	param_grid = dict(n_neighbors=k_range)

	grid_1 = GridSearchCV(kb_1, param_grid, cv=10, scoring='accuracy', n_jobs=6)
	grid_2 = GridSearchCV(kb_2, param_grid, cv=10, scoring='accuracy', n_jobs=6)
	grid_3 = GridSearchCV(kb_3, param_grid, cv=10, scoring='accuracy', n_jobs=6)

	grid_1.fit(D_matrices[0], true_labels)
	grid_2.fit(D_matrices[1], true_labels)
	grid_3.fit(D_matrices[2], true_labels)


	print(grid_1.best_params_['n_neighbors'])
	print(grid_2.best_params_['n_neighbors'])
	print(grid_3.best_params_['n_neighbors'])



	rskf = RepeatedStratifiedKFold(n_splits=10, n_repeats=30)
	score_gb = []
	score_kb = []

	for train_index, test_index in rskf.split(D_matrices[0], true_labels):

		matrix_train_1, matrix_test_1 = D_matrices[0][train_index], D_matrices[0][test_index]
		matrix_train_2, matrix_test_2 = D_matrices[1][train_index], D_matrices[1][test_index]
		matrix_train_3, matrix_test_3 = D_matrices[2][train_index], D_matrices[2][test_index]
		true_labels_train, true_labels_test = true_labels[train_index], true_labels[test_index]

		# print('view: ', view+1)
		# matrix = D_matrices[view]
		# print(rskf.get_n_splits(true_labels))

			# print('TRAIN: ', len(train_index))
			# print('TEST: ', len(test_index))

		#Classificador Bayesiano Gaussiano
		gb_1 = GaussianNB()
		gb_2 = GaussianNB()
		gb_3 = GaussianNB()

		gb_1.fit(matrix_train_1, true_labels_train)
		gb_2.fit(matrix_train_2, true_labels_train)
		gb_3.fit(matrix_train_3, true_labels_train)

		pred_1 = gb_1.predict_proba(matrix_test_1)
		pred_2 = gb_2.predict_proba(matrix_test_2)
		pred_3 = gb_3.predict_proba(matrix_test_3)

		#Ensemble pela regra da soma
		gb_ensemble = np.argmax(((1-L)*(prob_priori) + pred_1 + pred_2 + pred_3), axis=1)

		#Score do Ensemble
		score_gb.append(np.equal(gb_ensemble, true_labels_test).sum() / true_labels_test.shape[0])

		#Classificador KNN Bayesiano
		kb_1 = KNeighborsClassifier(n_neighbors=grid_1.best_params_['n_neighbors'])
		kb_2 = KNeighborsClassifier(n_neighbors=grid_2.best_params_['n_neighbors'])
		kb_3 = KNeighborsClassifier(n_neighbors=grid_3.best_params_['n_neighbors'])

		kb_1.fit(matrix_train_1, true_labels_train)
		kb_2.fit(matrix_train_2, true_labels_train)
		kb_3.fit(matrix_train_3, true_labels_train)

		pred_1 = kb_1.predict_proba(matrix_test_1)
		pred_2 = kb_2.predict_proba(matrix_test_2)
		pred_3 = kb_3.predict_proba(matrix_test_3)

		#Ensemble pela regra da soma
		kb_ensemble = np.argmax(((1-L)*(prob_priori) + pred_1 + pred_2 + pred_3), axis=1)
		#score dos ensembles
		score_kb.append(np.equal(kb_ensemble, true_labels_test).sum() / true_labels_test.shape[0])

	# Teste Wilcoxon nos 2 classificadores acima
	w, p = wilcoxon(score_gb, score_kb)
	print(w,p)

	#Esatistica
	stats_results = np.array([
		mean_confidence_interval(score_gb),
		mean_confidence_interval(score_kb),
		w,
		p])

	np.savetxt('%s/score-gb'%(path), score_gb, fmt='%.7f')
	np.savetxt('%s/score-kb'%(path), score_kb, fmt='%.7f')
	f = open('%s/stats-results'%(path), 'w+')
	for x in stats_results:
		f.write(str(x) + '\n')
	f.close()

	# #Histograma
	# Density Plot and Histogram of all arrival delays
	# f, axes = plt.subplots(1, 2, figsize=(7, 7), sharex=False, sharey=True)
	# sns.distplot(score_kb, hist=True, kde=True, color="skyblue", ax=axes[0])
	# sns.distplot(score_gb, hist=True, kde=True, color="olive", ax=axes[1])
	# f.tight_layout()
	# f.savefig('%s/hists.png'%(path))

	hist_skb  = sns.distplot(score_kb, hist=True, kde=True,
		bins=int(50), color = 'green',
		hist_kws={'edgecolor':'black'},
		kde_kws={'linewidth': 3})
	fig1 = hist_skb.get_figure()

	hist_sgb  = sns.distplot(score_gb, hist=True, kde=True,
		bins=int(50), hist_kws={'edgecolor':'red'},
		kde_kws={'linewidth': 3})
	hist_sgb.figure.savefig('%s/hist_sgb.png'%(path))

if __name__ == '__main__':
	np.random.seed(42)

	if not sys.warnoptions:
		warnings.simplefilter("ignore")

	main()