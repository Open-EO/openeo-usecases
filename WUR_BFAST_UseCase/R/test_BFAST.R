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

