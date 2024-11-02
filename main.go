package main

import (
	"fmt"
	"log"
	"net/http"
)

// API SCHEME:

// GET / - serves the index.html file
// GET /api/is_vpn?ip:str -> uses vpnapi.io to check if the IP is a VPN. returns {"is_vpn": True / False}
// GET /api/web_autocomplete?q:str -> gets the ddg autocomplete results and the wikipedia api results for the query. returns [{phrase: str, url:str}, ...]

// def is_vpn(ip:str, api_key:str) -> bool:
func is_vpn(ip string, api_key string) (bool, error) {
	// implement the is_vpn function here
	return false, nil
}

// def ddg_autocomplete(q:str) -> List[Dict[str, str]]:
func ddg_autocomplete(q string) []map[string]string {
	sample_results := []map[string]string{
		{"phrase": "Paris", "url": "https://duckduckgo.com/?q=Paris"},
		{"phrase": "Paris Hilton", "url": "https://duckduckgo.com/?q=Paris+Hilton"},
		{"phrase": "Paris Jackson", "url": "https://duckduckgo.com/?q=Paris+Jackson"},
	}
	return sample_results
}

// def wikipedia_autocomplete(q:str) -> List[Dict[str, str]]:
func wikipedia_autocomplete(q string) []map[string]string {
	sample_results := []map[string]string{
		{"phrase": "Paris", "url": "https://en.wikipedia.org/wiki/Paris"},
		{"phrase": "Paris Hilton", "url": "https://en.wikipedia.org/wiki/Paris_Hilton"},
		{"phrase": "Paris Jackson", "url": "https://en.wikipedia.org/wiki/Paris_Jackson"},
	}
	return sample_results
}

// def web_autocomplete(q:str) -> List[Dict[str, str]]:
func web_autocomplete(q string) []map[string]string {
	ddg_results := ddg_autocomplete(q)
	wikipedia_results := wikipedia_autocomplete(q)
	return append(ddg_results, wikipedia_results...)
}

// main function
func main() {

	VPNAPI_API_KEY := "API_KEY"

	// GET /api/is_vpn?ip:str
	http.HandleFunc("/api/is_vpn", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("/api/is_vpn endpoint hit")
		ip := r.URL.Query().Get("ip")
		if ip == "" {
			http.Error(w, "ip query parameter is required", http.StatusBadRequest)
			return
		}
		is_vpn, err := is_vpn(ip, VPNAPI_API_KEY)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		fmt.Fprintf(w, `{"is_vpn": %t}`, is_vpn)
	})

	// GET /api/web_autocomplete?q:str
	http.HandleFunc("/api/web_autocomplete", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("/api/web_autocomplete endpoint hit")
		q := r.URL.Query().Get("q")

		if q == "" {
			http.Error(w, "q query parameter is required", http.StatusBadRequest)
			return
		}

		results := web_autocomplete(q)
		fmt.Fprintf(w, "%v", results)
	})

	// GET / - serves the index.html file
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Println("/ endpoint hit")
		http.ServeFile(w, r, "index.html")
	})

	fmt.Println("Server running on http://127.0.0.1:8000")

	// Start the HTTP server on port 8000
	log.Fatal(http.ListenAndServe(":8000", nil))
}
