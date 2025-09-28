from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import pandas as pd

port = 48630


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Get the query string (e.g., ?pi_id=pi_kitchen)
        query_components = {}
        if "?" in self.path:
            path, query = self.path.split("?", 1)
            for item in query.split("&"):
                key, value = item.split("=")
                query_components[key] = value
        else:
            path = self.path

        # Get the pi_id from the query, use a default if not provided
        pi_identifier = query_components.get("pi_id", "unknown")

        df = pd.read_csv("server_schedule.csv", index_col=0)
        df_pi = df.loc[:, pi_identifier]

        # Prepare and send the response
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = df_pi.to_dict()
        self.wfile.write(json.dumps(response).encode())


# Run the server on port
server_address = ("0.0.0.0", port)
httpd = HTTPServer(server_address, RequestHandler)
print(f"Server running on port {port}...")
httpd.serve_forever()
