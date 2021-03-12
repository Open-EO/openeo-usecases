library(openeo)
library(magrittr)

# basic login (disabled) ----
#euracHost = "https://openeo.eurac.edu"
#httr::set_config(httr::config(ssl_verifypeer = 0L))
#httr::set_config(httr::config(ssl_verifyhost= 0L))
#user = ""
#password = ""
#api_versions(url=euracHost)
#eurac = connect(host = euracHost, 
#                user = user, 
#                password = password, 
#                login_type = "basic")

# oidc login (active) ----
euracHost = "https://openeo.eurac.edu"
api_versions(url=euracHost)
conf = list(client_id = "CONTACT EURAC", secret = "CONTACT EURAC")
eurac = connect(host = euracHost)
prov = list_oidc_providers()
prov$Eurac_EDP_Keycloak

eurac$isConnected()
eurac$isLoggedIn()

eurac$login(login_type = "oidc", 
            provider = prov$Eurac_EDP_Keycloak, 
            config = conf)

eurac$isLoggedIn()

# collection descritption ----
eurac %>% describe_collection("openEO_S2_32632_10m_L2A_D22")
eurac %>% describe_collection("openEO_WUR_Usecase")
list_udf_runtimes(eurac)

# build graph ----
p = processes()
udfName = "BFAST_udf.R"
udfCode = readChar(udfName, file.info(udfName)$size)

# c("2017-01-01T00:00:00Z","2019-12-29T00:00:00Z")
# c("2019-04-21T00:00:00.000Z"," 2019-06-08T00:00:00.000Z")
# c("2017-05-01T00:00:00Z","2019-12-29T00:00:00Z")

s2 = p$load_collection(id = p$data$openEO_WUR_Usecase, 
                       spatial_extent = list(west = -54.8125, 
                                             south = -3.5125, 
                                             east =  -54.8100, 
                                             north = -3.5100), 
                       temporal_extent = c("2017-05-01T00:00:00Z","2019-12-29T00:00:00Z"),
                       bands = c('VH'))

udf = p$run_udf(data = s2, udf = udfCode, runtime = 'R') #"r"

result = p$save_result(udf, format="NETCDF")

# We can use debug() to see verbose information
# Also get the JSON text of the process graph:
graph = as(result,"Graph")

job_id = create_job(con = eurac, graph = result, title = "test_udf_rclient", description = "test_udf_rclient") # batch call, works on udf!
eurac %>% start_job(job_id)
# What is the status of the job?
eurac %>% describe_job(job_id)
# When it is finished:
done = download_results(job = job_id, folder = ".")
done


# look at result ----
library(raster)
fin = raster::stack(done)
names(fin)
fin
plot(fin[[3]])

library(stars)
fin = read_stars(done)
fin
stars::st_get_dimension_values(fin, "band")
plot(fin)


