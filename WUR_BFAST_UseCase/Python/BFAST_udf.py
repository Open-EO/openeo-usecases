def bfast4openeo(udf_data):
    udf_data_xr = udf_data.get_array()
    from bfast import BFASTMonitor
    from bfast.utils import crop_data_dates
    from datetime import datetime
    import xarray as xr
    start_hist = datetime(2017, 1, 1)
    start_monitor = datetime(2019, 1, 1)
    end_monitor = datetime(2020, 1, 1)
    # --- revisit parsing of time/labels -----
    dates = udf_data_xr.coords['time']
    # ---------------------------------------
    data, dates = crop_data_dates(udf_data_xr.values, dates, start_hist, end_monitor)
    # --------------------------
    model = BFASTMonitor(
        start_monitor,
        freq=365,
        k=3,
        hfrac=0.25,
        trend=False,
        level=0.05,
        backend='Python',
        device_id=0,
    )
    model.fit(data, dates, n_chunks=1, nan_value=-32768)
    breaks_xr = xr.DataArray(model.breaks, coords=[udf_data_xr.coords['x'],udf_data_xr.coords['y']], dim=['x', 'y'])
    udf_data.set_array(breaks_xr)

bfast4openeo(data)



