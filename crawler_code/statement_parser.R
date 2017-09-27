"Date: 25th Sept
Author: Mincev
Script for financial statement parsing. Uses XBRL library to convert 
files into XBRL format (format required for finstr) before parsing 
these files using the finstr library"
library(XBRL)
library(finstr)
library(rjson)

#'Opens a csv file returning a csv object
open_csv = function(filename = "apple_links.csv", 
                     file_path = "/home/mincev/Documents/git/fundamentals_crawler/crawler_code/obj/"){
  file = paste(file_path, filename, sep = '')
  csv_links = read.csv(file = file)
  return(csv_links)
}

#'Opens a txt file returning a list of lists. 
#'Note: To access eg first element in first row -> json_data[[1]][1]
open_json = function(filename = "apple_links.txt", 
                     file_path = "/home/mincev/Documents/git/fundamentals_crawler/crawler_code/obj/"){
  file = paste(file_path, filename, sep = '')
  json_data = fromJSON(file=file)
  return(json_data)
}

#'"Takes in a url (url_end, url_start) that links to an xml financial statement 
#'on sec.gov. The financial statement is then processd using the xbrl library 
#'and finstr library to produce 4 statements:
#'(balance sheet, income, other income, and cash flow statement)"
process_file = function(url_end = "/Archives/edgar/data/320193/000119312513416534/aapl-20130928.xml",
                        url_start = "https://www.sec.gov"){
  url = paste(url_start, url_end, sep = '')
  old_o = options(stringsAsFactors = FALSE)
  xbrl_data = xbrlDoAll(url)
  options(old_o)
  statements = xbrl_get_statements(xbrl_data)
  return(statements)
}

#'Merges income statement and balance sheet
#'The output statement is used when calculating ratios
merge_statements = function(statements){
  merged_statement = merge(
    statements[[1]], 
    statements[[2]] )
  for (i in 3:length(statements)){
    merged_statement = merge(
      merged_statement, 
      statements[[i]] )
  }
  return(merged_statement)
}

#----------------------------------------------------------------------------
#copied from finstr - due problems recognising fucntion
get_elements <- function(x, parent_id = NULL, all = TRUE) {
  # returns all terminating elements 
  # if parent_id provided, only descendands from this elements are returned
  
  if( is.null(x)  ) {
    stop("No statement")
  }
  if( !"statement" %in% class(x)  ) {
    stop("Not a statement class")
  }
  
  elements <- attr(x, "elements")
  
  if(!missing(parent_id)) {
    children <- elements[["elementId"]] == parent_id
    if(!any(children)) {
      stop("No children with parent ", parent_id, " found", call. = FALSE)
    }
    id_parent <- elements[["id"]][children]
    elements <- elements %>%
      dplyr::filter_(~substring(id, 1, nchar(id_parent)) == id_parent) %>%
      as.elements()
    
  }
  if(!all) {
    elements <- elements %>%
      dplyr::filter_(~terminal) %>%
      dplyr::mutate(level = 1) %>%
      as.elements()
  }
  
  return(elements)
  
}

#----------------------------------------------------------------------------
#'Fomulas for reusable Ratio calculation
ratios = calculation(
  
  Inventory_Turnover = 
    CostOfGoodsAndServicesSold / InventoryNet,
  
  .AccountReceivableLast = lag(AccountsReceivableNetCurrent),
  .AccountReceivableAvg = (.AccountReceivableLast + AccountsReceivableNetCurrent)/2,
  
  Receivables_Turnover = 
    NetRevenue / .AccountReceivableAvg,
  
  .AccountsPayableLast = lag(AccountsPayableCurrent),
  .AccountsPayableAvg = (.AccountsPayableLast + AccountsPayableCurrent)/2,
  
  Payables_Turnover = 
    NetRevenue / .AccountsPayableAvg,
  
  Asset_Turnover = 
    NetRevenue / Assets,
  
  CurrentRatio = 
    AssetsCurrent / LiabilitiesCurrent,
  
  Quick_Ratio =  
    ( CashAndCashEquivalentsAtCarryingValue + 
        AvailableForSaleSecuritiesCurrent +
        AccountsReceivableNetCurrent
    ) / LiabilitiesCurrent,
  
  Cash_Ratio = 
    ( CashAndCashEquivalentsAtCarryingValue + 
        AvailableForSaleSecuritiesCurrent
    ) / LiabilitiesCurrent,
  
  Gross_Margin = 
    (SalesRevenueNet -  CostOfGoodsAndServicesSold) / SalesRevenueNet,
  
  Operating_Margin =
    OperatingIncomeLoss / SalesRevenueNet,
  
  Net_Margin = 
    NetIncomeLoss / SalesRevenueNet,
  
  ROA = 
    NetIncomeLoss / Assets,
  
  ROE = 
    NetIncomeLoss / StockholdersEquity
  
)

#-------------------------------------------------------------------------
#main -> use apple_links (function defaults) as an example:
links = open_json()

#check where new cik begins and store index position in new_cik_index list
new_cik_index = list(1)
index = 1
for (i in 2:length(links)){
  # check ciks match
  if (substr(links[[i]][1], 22, 27) != substr(links[[index]][1], 22, 27)){ 
    new_cik_index = c(new_cik_index, i)
    index = i
  }
}
#add final element to new_cik_index
new_cik_index = c(new_cik_index, length(links) + 1)

#loop for every cik merging statements (for that cik) and calculating their 
#ratios - save ratios in a file named [CIK]. 
#UPDATE: do not merge or calculate ratios - simply save financial statements
file_path = "/home/mincev/Documents/git/fundamentals_crawler/crawler_code/obj/"
counter = 1
for (i in 1:(length(new_cik_index)-1)){
  list_of_financial_statements = list()
  #list_of_merged_statements = list()
  cik_ids = list()
  for (j in new_cik_index[[i]][1]:(new_cik_index[[i + 1]][1]-1)){
    tryCatch({
      print("Retrieving data for: ")
      print(links[[j]][1])
      statements = list(process_file(url_end = links[[j]][1]))
      list_of_financial_statements = c(list_of_financial_statements, statements)
      cik_ids = c(cik_ids, links[[j]][1])
      #statements_merged = list(merge_statements(statements))
      #list_of_merged_statements = c(list_of_merged_statements, statements_merged)
      #ratios = merged_statement %>% finstr::calculate(calculations = ratios, digits = 3)
      counter = 1
    },  error=function(e){
      print("Unable to get data for:")
      print(links[[j]][1])
      Sys.sleep((counter * 5))
      counter = counter + 1
    })
    #save ratios to file 
    if (j == (new_cik_index[[i+1]][1]-1)){
      cik = substr(links[[j]][1], 22, 27)
      f_statements = paste(file_path, paste("statements_", cik, sep = ''), sep = '')
      id_statements = paste(file_path, paste("id_", cik, sep = ''), sep = '')
      #m_statemenst = paste("merged_", cik, sep = '')
      saveRDS(list_of_financial_statements, paste(f_statements,".rds", sep = ''))
      saveRDS(list_of_financial_statements, paste(id_statements,".rds", sep = ''))
      #saveRDS(list_of_financial_statements, paste(m_statements,".rds", sep = ''))        
    }
  }
}



