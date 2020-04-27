def bfast4openeo(udf_data):
    #
    from bfast import BFASTMonitor
    from bfast.utils import crop_data_dates
    from datetime import datetime
    import xarray as xr
    import pandas as pd
    #
    start_hist = datetime(2017, 1, 1)
    start_monitor = datetime(2019, 1, 1)
    end_monitor = datetime(2019, 12, 29)
    # get the dates from the data cube:
    dates = [pd.Timestamp(date).to_pydatetime() for date in  udf_data.coords['time'].values]
    # pre-processing - crop the input data cube according to the history and monitor periods:
    data, dates = crop_data_dates(udf_data.values, dates, start_hist, end_monitor)
    # !!! Note !!! that data has the shape 91, and not 92 for our dataset. The reason is the definition in
    # the bfast utils.py script where the start_hist is set < than dates, and not <= than dates.
    # -------------------------------------
    # specify the BFASTmonitor parameters:
    model = BFASTMonitor(
        start_monitor,
        freq=365,
        k=3,
        verbose=1,
        hfrac=0.25,
        trend=False,
        level=0.05,
        backend='python',
        device_id=0,
    )
    # run the monitoring:
    # !!! question !!! can we get more informative progress bar for the below run?
    model.fit(data, dates, n_chunks=1, nan_value=-9999)
    # get the detected breaks as an xarray Data Array:
    # !!! question !!! are those breaks identical to the breaks we get from R script?
    breaks_xr = xr.DataArray(model.breaks,
                             coords=[udf_data.coords['y'].values,udf_data.coords['x'].values],
                             dims=['y', 'x'])
    return breaks_xr



