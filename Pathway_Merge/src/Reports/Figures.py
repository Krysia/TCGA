'''
Created on Oct 15, 2012

@author: agross
'''
import matplotlib.pyplot as plt
from numpy import nanmax, sort, linspace, arange, rank
from scipy.stats import gaussian_kde

from Processing.Helpers import match_series, split_a_by_b

import rpy2.robjects as robjects 
from rpy2.robjects import r
import pandas.rpy.common as com 
survival = robjects.packages.importr('survival')
base = robjects.packages.importr('base')


def violin_plot(ax,data,pos=[], bp=False):
    '''
    create violin plots on an axis
    '''
    from scipy.stats import gaussian_kde
    from numpy import arange
    
    #dist = max(pos)-min(pos)
    dist = len(pos)
    w = min(0.25*max(dist,1.0),0.5)
    for p,d in enumerate(data):
        k = gaussian_kde(d) #calculates the kernel density
        m = k.dataset.min() #lower bound of violin
        M = k.dataset.max() #upper bound of violin
        x = arange(m,M,(M-m)/100.) # support for violin
        v = k.evaluate(x) #violin profile (density curve)
        v = v/v.max()*w #scaling the violin to the available space
        ax.fill_betweenx(x,p,v+p,facecolor='y',alpha=0.1)
        ax.fill_betweenx(x,p,-v+p,facecolor='y',alpha=0.1)
    if bp:
        boxPlot = ax.boxplot(data,notch=1,positions=range(len(pos)),vert=1, widths=.25)
        return boxPlot
    
def box_plot_pandas(hitVec, expVec, ax='None'):
    '''
    http://pyinsci.blogspot.com/2009/09/violin-plot-with-matplotlib.html
    Wrapper around matplotlib's boxplot function for KW eQTLs
    '''
    if ax=='None':
        fig, ax = plt.subplots(1,1)
    ax.boxplot([expVec[hitVec==num] for num in set(hitVec)], 
           positions=list(set(hitVec)));
    ax.set_ylabel('Sub-Cohort Gene Expression')
    ax.set_xlabel('Number of Mutations')
    if type(hitVec.name) == str:
        ax.set_title(hitVec.name +' x '+ expVec.name)
    
def violin_plot_pandas(bin_vec, real_vec, ax=None):
    '''
    Wrapper around matplotlib's boxplot function to add violin profile.
    '''   
    bin_vec, real_vec = match_series(bin_vec, real_vec)
    if ax is None:
        fig, ax = plt.subplots(1,1)
    else:
        fig = plt.gcf()
    try:
        categories = list(set(bin_vec.astype(int)))
        violin_plot(ax, [real_vec[bin_vec==num] for num in categories], 
                    pos=categories, bp=True)
        ax.set_xticklabels([str(c) +' (n=%i)'%sum(bin_vec==c) 
                            for c in categories])
    except:
        box_plot_pandas(bin_vec, real_vec, ax=ax)
    ax.set_ylabel('Sub-Cohort Expression')
    ax.set_xlabel('Number of Mutations')
    if type(bin_vec.name) == str:
        ax.set_title(bin_vec.name +' x '+ real_vec.name)
    return fig
    
def draw_survival_curves(clinical, hit_vec, filename='tmp.png', show=False, 
                         ax=None, title=True, labels=['No Mutation', 'Mutation']):
    hit_vec.name = 'pathway'
    df = clinical.join(hit_vec)
    df = com.convert_to_r_dataframe(df) #@UndefinedVariable
    fmla = robjects.Formula('Surv(days, censored) ~ ' + hit_vec.name)
    fit = survival.survfit(fmla, df)
    r('png')(filename=filename)
    ls = r('2:' + str(len(set(hit_vec))+1)) #R line styles
    r('plot')(fit, lty=ls, col=ls, xlab='Days to Death', ylab= 'Survival')
    if title:
        r('title')(hit_vec.name)
    r('legend')(nanmax(clinical.days) * .7,.9, labels, lty=ls, col=ls)
    r('dev.off()')
    if ax or show:
        img = plt.imread(filename)
        if ax is None:
            fig,ax = plt.subplots(1,1, figsize=(7,7), frameon=False)
        ax.imshow(img)
        ax.set_axis_off()
        ax.get_figure().tight_layout()
        
def draw_pathway_count_bar(p, cancer, gene_sets, file_name='tmp.svg'):
    fig, ax = plt.subplots(1,1, figsize=(3+len(gene_sets[p])/15.,2.5))
    m = cancer.hit_matrix.ix[list(gene_sets[p]), cancer.patients] > 0
    m = m[m.sum(1) > 0]
    m.sum(1).plot(kind='bar', ax=ax, alpha=.4);
    ax.set_xticklabels(m.index, ha='center', va='bottom', position=(0,.1), size=14)
    ax.set_ylabel('# Patients')
    
    fig.tight_layout()
    fig.savefig(file_name)
    
def draw_pathway_eig_bar(U, file_name='tmp.svg'):
    if rank(U)  == 2:
        U = U[0]
    fig, ax = plt.subplots(1,1, figsize=(3+len(U)/15.,2.5))
    sort(U).plot(kind='bar', ax=ax, alpha=.4)
    ax.set_ylabel('Loading')
    fig.tight_layout()
    fig.savefig(file_name)
    
def draw_pathway_age_scatter(p, cancer, file_name='tmp.svg'):
    fig, ax = plt.subplots(1,1, figsize=(6,4))
    ax.scatter(*match_series(cancer.pc.ix[p], cancer.clinical.age), alpha=.5, s=75)
    ax.set_xlabel('Principal Component Loading')
    ax.set_ylabel('Age')
    fig.savefig(file_name)
    
def histo_compare(hit_vec, response_vec, ax=None):
    '''
    Split response_vec by hit_vec and compared histograms.  
    Also plots the kde of the whole response_vec.
    '''
    if ax is None:
        fig, ax = plt.subplots(1,1)
    else:
        fig = fig.gcf()
    kde1 = gaussian_kde(response_vec)
    x_eval = linspace(min(response_vec), max(response_vec), num=200)
    ax.plot(x_eval, kde1(x_eval), 'k-')
    miss, hit = split_a_by_b(response_vec, hit_vec)
    ax.hist(miss, bins=20, normed=True, alpha=.2, label='WT');
    ax.hist(hit, bins=10, normed=True, alpha=.5, label='Mut');
    ax.legend()
    return fig

def mut_module_raster(cluster_num, mut, ax=None):
    assert hasattr(mut, 'clustered')
    if ax is None:
        fig, ax = plt.subplots(1,1, figsize=(10,8))
    else:
        fig = fig.gcf()
    p = mut.assignments[mut.assignments == cluster_num].index
    s = mut.meta_matrix.ix[p].sum()
    x_order = sort(-s[s > 0]).index
    y_order = sort(mut.meta_matrix.ix[p].sum(1)).index
    plt.imshow(mut.meta_matrix.ix[y_order, x_order], aspect=8, 
               interpolation='Nearest', cmap=plt.cm.bone_r) #@UndefinedVariable
    ax.set_yticks(range(len(p)))
    ax.set_yticklabels(p);
    ax.hlines(arange(len(p)) + .5, 0, len(x_order), colors='grey', alpha=.3, lw=4)
    ax.set_xlabel('Patients');
    ax.axvline(x=(mut.clustered.ix[cluster_num] == 1).sum(), ymin=0, 
               ymax=len(y_order), color='r', alpha=.7, lw=5)
    ax.set_xbound(0, len(x_order))
    fig.tight_layout()
    return fig
    