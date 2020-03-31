if (!require(devtools)) {
  install.packages("devtools",dependencies=TRUE)
  library(devtools)
}
install_github(repo="Open-EO/openeo-r-client@develop",dependencies=TRUE)
library(openeo)


# enter valid credentials
euracHost = "https://openeo.eurac.edu"
user = "guest"
password = "guest123"
api_versions(url=euracHost)

# eurac = connect(host = euracHost, version="0.4.2", user = user, password = password, login_type = "basic")
eurac = connect(host = euracHost)


# Build a process graph:
p = processes()

# the spatial and temporal exstends should be adopted:
s2 = p$load_collection(id = p$data$openEO_S2_32632_10m_L2A, 
                          spatial_extent = list(west = 11.2792, 
                                                south = 46.4643, 
                                                east = 11.4072, 
                                                north = 46.5182), 
                          temporal_extent = c("2018-06-04T00:00:00Z","2018-06-23T00:00:00Z"))


list_udf_runtimes(eurac)
describe_process(con = eurac,"run_udf")

udfName = "BFAST_udf.R"
udfCode = readChar(udfName, file.info(udfName)$size)

# send_udf(s2, udfCode, host = "", port = NULL, language = "R", debug = FALSE, download_info = FALSE)

p$run_udf(data = s2, udf = udfCode, runtime = "R")


describe_process(con = eurac,"save_result")
# test 2 (the simple one)
udfCode2 = quote({data2 = data*(2); data2})
graph_test2 = p$run_udf(data = s2, udf = udfCode2, runtime = "R")
list_file_types()
graph_test2 = p$save_result(graph_test2, format="GTiff")
# validate the graph at the client:
as(graph_test2, "Graph")$validate()
# validate at server
validate_process_graph(graph=graph_test2)
#
compute_result(graph=as(graph_test2, "Graph"), format="GTiff", output_file = 'results_test2.tiff')





