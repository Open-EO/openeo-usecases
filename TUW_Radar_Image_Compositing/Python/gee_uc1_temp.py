import openeo

GEE_DRIVER_URL = "https://earthengine.openeo.org/v1.0"

user = "group2"
password = "test123"

# Connect to backend via basic authentication
con = openeo.connect(GEE_DRIVER_URL)
con.authenticate_basic(user, password)

datacube = con.load_collection("COPERNICUS/S1_GRD",
                               spatial_extent={"west": 16.06, "south": 48.10, "east": 16.65, "north": 48.31, "crs": 4326},
                               temporal_extent=["2017-03-01", "2017-06-01"],
                               bands=["VV"])
march = datacube.filter_temporal("2017-03-01", "2017-04-01")
april = datacube.filter_temporal("2017-04-01", "2017-05-01")
may = datacube.filter_temporal("2017-05-01", "2017-06-01")

mean_march = march.mean_time()
mean_april = april.mean_time()
mean_may = may.mean_time()

R_band = mean_march.rename_labels(dimension="bands", target=["R"])
G_band = mean_april.rename_labels(dimension="bands", target=["G"])
B_band = mean_may.rename_labels(dimension="bands", target=["B"])

RG = R_band.merge(G_band)
RGB = RG.merge(B_band)

datacube = RGB.save_result(format="GTIFF-THUMB")

job = datacube.send_job()
job.start_and_wait().download_results()
