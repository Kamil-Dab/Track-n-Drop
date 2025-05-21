import http.client
import json

def fetch_olx_data(product_query):
    conn = http.client.HTTPSConnection("www.olx.pl")
    
    payload = json.dumps({
        "query": """query ListingSearchQuery(
  $searchParameters: [SearchParameter!] = {key: "", value: ""}
) {
  clientCompatibleListings(searchParameters: $searchParameters) {
    __typename
    ... on ListingSuccess {
      __typename
      data {
        id
        title
        url
        params {
          key
          name
          type
          value {
            __typename
            ... on PriceParam {
              value
              currency
              negotiable
              label
            }
            ... on GenericParam {
              key
              label
            }
          }
        }
      }
      metadata {
        total_elements
      }
    }
    ... on ListingError {
      __typename
      error {
        code
        detail
      }
    }
  }
}
""",
        "variables": {
            "searchParameters": [
                {"key": "offset", "value": "0"},
                {"key": "limit", "value": "10"},
                {"key": "query", "value": product_query},
                {"key": "filter_refiners", "value": "spell_checker"},
                {"key": "suggest_filters", "value": "true"}
            ]
        }
    })
    
    headers = {
        'accept': 'application/json',
        'accept-language': 'pl',
        'content-type': 'application/json',
        'origin': 'https://www.olx.pl',
        'referer': f'https://www.olx.pl/oferty/q-{product_query.replace(" ", "-")}/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    }
    
    try:
        conn.request("POST", "/apigateway/graphql", payload, headers)
        res = conn.getresponse()
        data = res.read()
        response_json = json.loads(data.decode("utf-8"))
        conn.close()
        return response_json
    except Exception as e:
        print(f"Error fetching OLX data for '{product_query}': {e}")
        if 'conn' in locals():
            conn.close()
        return None

def parse_olx_items(olx_response_json):
    items = []
    if not olx_response_json or "data" not in olx_response_json or \
       "clientCompatibleListings" not in olx_response_json["data"] or \
       olx_response_json["data"]["clientCompatibleListings"]["__typename"] != "ListingSuccess":
        print("OLX response format error or no success data.")
        return items

    listings_data = olx_response_json["data"]["clientCompatibleListings"]["data"]
    
    for item_data in listings_data:
        title = item_data.get("title")
        url = item_data.get("url")
        price = None
        currency = None
        
        for param in item_data.get("params", []):
            if param.get("key") == "price" and param.get("value", {}).get("__typename") == "PriceParam":
                price_value_data = param.get("value")
                price = price_value_data.get("value")
                currency = price_value_data.get("currency")
                break # Found price, no need to check other params
        
        if title and url and price is not None:
            items.append({
                "title": title,
                "price": float(price),
                "currency": currency,
                "url": url
            })
    return items

