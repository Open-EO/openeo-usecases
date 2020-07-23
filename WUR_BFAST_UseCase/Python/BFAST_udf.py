def bfast4openeo(udf_data):
    #
    from bfast import BFASTMonitor
    from bfast.utils import crop_data_dates
    from datetime import datetime
    import xarray as xr
    import pandas as pd
    import numpy as np
    #
    start_hist = datetime(2016, 12, 31)
    start_monitor = datetime(2019, 1, 1)
    end_monitor = datetime(2019, 12, 29)
    # get the dates from the data cube:
    dates = [pd.Timestamp(date).to_pydatetime() for date in udf_data.coords['time'].values]
    # pre-processing - crop the input data cube according to the history and monitor periods:
    data, dates = crop_data_dates(udf_data.values, dates, start_hist, end_monitor)
    # !!! Note !!! that data has the shape 91, and not 92 for our dataset. The reason is the definition in
    # the bfast utils.py script where the start_hist is set < than dates, and not <= than dates.
    # -------------------------------------
    # specify the BFASTmonitor parameters:
    model = BFASTMonitor(
        start_monitor,
        freq=31,
        k=3,
        verbose=1,
        hfrac=0.25,
        trend=True,
        level=0.05,
        backend='python'
    )
    # run the monitoring:
    # model.fit(data, dates, nan_value=udf_data.nodatavals[0])
    model.fit(data, dates)
    # get the detected breaks as an xarray Data Array:
    # !!! question !!! are those breaks identical to the breaks we get from R script?
    breaks_xr = xr.DataArray(model.breaks,
                             coords=[udf_data.coords['y'].values, udf_data.coords['x'].values],
                             dims=['y', 'x'])
    return breaks_xr



