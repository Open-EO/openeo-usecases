import openeo

#connect with VITO backend
vito = openeo.connect("https://openeo-dev.vito.be")

vito.authenticate_basic("username","username123")
connection = vito

#NOTE: SentinelHub layers on VITO backend are experimental. Use with care, only small regions!
datacube = connection.load_collection("SENTINEL1_GAMMA0_SENTINELHUB",
                                      spatial_extent={"west": 16.06, "south": 48.1, "east": 16.65,
                                                      "north": 48.31, "crs": 4326},
                                   temporal_extent=["2019-03-01", "2019-03-05"],
                                   bands=["VV","VH"])
mean = datacube.mean_time()

#using indices as labels not yet supported on VITO
difference = mean.reduce_dimension(dimension="bands", reducer=lambda cube: cube.array_element(1) - cube.array_element(0))
difference = difference.add_dimension('bands',label='diff',type='bands')

#stack all bands into an 'RGB' image
mean.merge_cubes(difference).download('sar.tiff',options={"tiled":True})