library(openeo)

# enter valid credentials
driver_url = "https://openeo.eurac.edu"
eurac = connect(host = driver_url, login_type = "basic")

# Build a process graph:
p = processes()

s1 = p$load_collection(id = "openEO_WUR_Usecase",
                       # add time selection:
                       temporal_extent = c("2017-01-01T00:00:00Z","2019-12-29T00:00:00Z"),
                       # select the vh band:
                       bands = c('VH'))


# note: please take care of the working directory of your R session
udfName = "BFAST_udf.R"
udfCode = readChar(udfName, file.info(udfName)$size)

# ingest udf into the process graph
test1 = p$run_udf(data = s1, udf = udfCode, runtime = "R")
# save results
graph_test1 = p$save_result(test1, format="GTiff")

# create a bach job from the graph:
job_id = create_job(con = eurac, graph = graph_test1, title = "job_bfast_large_area", description = "job_bfast_large_area") # batch call, works on udf!

# start the job:
start_job(con = eurac, job = job_id)
done = download_results(job = job_id, folder = ".")


