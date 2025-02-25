from ..pp import *
import scanpy as sc
import numpy as np
import anndata


def batch_correction(adata:anndata.AnnData,batch_key:str,
                     methods:str,n_pcs:int=50,**kwargs)->anndata.AnnData:
    """
    Batch correction for single-cell data

    Arguments:
        adata: AnnData object
        batch_key: batch key
        methods: harmony,combat,scanorama
        n_pcs: number of PCs
        kwargs: other parameters for harmony`harmonypy.run_harmony()`,combat`sc.pp.combat()`,scanorama`scanorama.integrate_scanpy()`

    Returns:
        adata: AnnData object
    
    """

    print(f'...Begin using {methods} to correct batch effect')

    if methods=='harmony':
        try:
            import harmonypy
            #print('mofax have been install version:',mfx.__version__)
        except ImportError:
            raise ImportError(
                'Please install the harmonypy: `pip install harmonypy`.'
            )
        
        adata3=adata.copy()
        scale(adata3)
        pca(adata3,layer='scaled',n_pcs=n_pcs)
        sc.external.pp.harmony_integrate(adata3, batch_key,basis='scaled|original|X_pca',*kwargs)
        adata.obsm['X_harmony']=adata3.obsm['X_pca_harmony'].copy()
        return adata3
    elif methods=='combat':
        adata2=adata.copy()
        sc.pp.combat(adata2, key=batch_key,*kwargs)
        scale(adata2)
        pca(adata2,layer='scaled',n_pcs=n_pcs)
        adata2.obsm['X_combat']=adata2.obsm['scaled|original|X_pca'].copy()
        adata.obsm['X_combat']=adata2.obsm['X_combat'].copy()
        return adata2
    elif methods=='scanorama':
        try:
            import scanorama
            #print('mofax have been install version:',mfx.__version__)
        except ImportError:
            raise ImportError(
                'Please install the scanorama: `pip install scanorama`.'
            )
        import scanorama
        batches = adata.obs[batch_key].cat.categories.tolist()
        alldata = {}
        for batch in batches:
            alldata[batch] = adata[adata.obs[batch_key] == batch,]
        alldata2 = dict()
        for ds in alldata.keys():
            print(ds)
            alldata2[ds] = alldata[ds]
        
        #convert to list of AnnData objects
        adatas = list(alldata2.values())
        
        # run scanorama.integrate
        scanorama.integrate_scanpy(adatas, dimred = n_pcs,*kwargs)
        scanorama_int = [ad.obsm['X_scanorama'] for ad in adatas]

        # make into one matrix.
        all_s = np.concatenate(scanorama_int)
        print(all_s.shape)
        
        # add to the AnnData object, create a new object first
        adata.obsm["X_scanorama"] = all_s
        return adata
    else:
        print('Not supported')

    