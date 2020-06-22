# -*- coding: utf-8 -*-
# Uncomment the import only for coding support
from openeo_udf.api.datacube import DataCube
from typing import Dict

def apply_hypercube(cube: DataCube, context: Dict) -> DataCube:

    import json
    import uuid

    # naming properties
    uid=uuid.uuid4().hex
    user=context['user']
    label=context['label']
    prefix=context['prefix']

    with open(prefix+user+'/'+label+'_'+uid+'.pre','w') as fw:
        fw.write("BLABLA")
        fw.flush()
     
    # write context
    with open(prefix+user+'/'+label+'_'+uid+'.ctxt','w') as fw:
        if (context is not None):
            fw.write(json.dumps(context,indent=4))
        fw.flush()

    # extract xarray
    inarr=cube.get_array()
  
    # write schema
    indict=inarr.to_dict(data=False)
    with open(prefix+user+'/'+label+'_'+uid+'.schema','w') as fw: 
        json.dump(indict, fw)
        fw.flush()
      
    # write data
    indict=cube.get_array().to_dict()
    with open(prefix+user+'/'+label+'_'+uid+'.json','w') as fw: 
        json.dump(indict, fw, default=str)
        fw.flush()
 
    with open(prefix+user+'/'+label+'_'+uid+'.post','w') as fw:
        fw.write("BLABLA")
        fw.flush()

    # behave transparently
    return cube
