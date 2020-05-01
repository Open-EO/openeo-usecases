if (!require(devtools)) {
  install.packages("devtools",dependencies=TRUE)
  library(devtools)
}
install_github(repo="Open-EO/openeo-r-client@develop",dependencies=TRUE)
library(openeo)


# enter valid credentials
euracHost = "https://openeo.eurac.edu"
#user = "guest"
#password = "guest123"
user = ""
password = ""

api_versions(url=euracHost)

eurac = connect(host = euracHost, version="0.4.2", user = user, password = password, login_type = "basic")
#eurac = connect(host = euracHost)


# Build a process graph:
p = processes()

# the spatial and temporal exstends should be adopted:
s1 = p$load_collection(id = p$data$openEO_WUR_UseCase, 
                       spatial_extent = list(west = -54.8360, 
                                             south = -3.5467, 
                                             east =  -54.7956, 
                                             north = -3.5079), 
                       # add band selection here
                       temporal_extent = c("2017-01-01T00:00:00Z","2019-12-29T00:00:00Z"),
                       # select the vh band:
                       bands = c('VH'))


list_udf_runtimes(eurac)
describe_process(con = eurac,"load_collection")


# check the WUR test data at EURAC backend:
list_collections()
collection_viewer("openEO_WUR_UseCase")
describe_collection(id="openEO_WUR_UseCase")


udfName = "BFAST_udf.R"
udfCode = readChar(udfName, file.info(udfName)$size)

# send_udf(s1, udfCode, host = "", port = NULL, language = "R", debug = FALSE, download_info = FALSE)

test1 = p$run_udf(data = s1, udf = udfCode, runtime = "R")
graph_test1 = p$save_result(test1, format="GTiff")
compute_result(graph=graph_test1, format="GTiff", output_file = 'euracBackend_bfast_output.tif')


# --------------------------------------------------------------------------------------

describe_process(con = eurac,"save_result")
# test 2 (the simple one)
udfCode2 = quote({data2 = data*(2); data2})
graph_test2 = p$run_udf(data = s1, udf = udfCode2, runtime = "R")
list_file_types()
graph_test2 = p$save_result(graph_test2, format="netCDF")
# validate the graph at the client:
as(graph_test2, "Graph")$validate()
# validate at server
validate_process_graph(graph=graph_test2)
#
compute_result(graph=as(graph_test2, "Graph"), format="netCDF", output_file = 'results_test2.nc')





