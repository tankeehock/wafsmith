export const MODSEC_RULE_ID_RANGE = {
  MIN: 1000000000000,
  MAX: 9999999999999
}
export const LOG_CLASSIFICATION = {
  'COMMAND_INJECTION': 'command-injection',
  'FILE_INCLUSION': 'file-inclusion',
   'SQL_INJECTION': 'sqli',
   'CROSS_SITE_SCRIPTING': 'xss',
   'DIRECTORY_TRAVERSAL': 'directory-traversal',
   'RECON': 'recon',
   'NON_MALICIOUS': 'non-malicious'
}
export const TARGET_PROTOCOL = "http"
export const TARGET_ENDPOINT = "http://127.0.0.1/"
export const DOCKER_SERVICES = {
  NGINX: "crs-nginx",
  WEB: "web-app"
}
export const COLORS = {
  DEFAULT: "default",
  RED: "red",
  YELLOW:"yellow",
  BLUE:"blue",
  GREEN:"green"
}
export const PAYLOAD_TYPES = {
  BUSINESS_TRAFFIC: "business-traffic",
  PAYLOAD: "payload",
};

export const PAYLOAD_POSITION = {
  HTTP_HEADERS: "http-headers",
  URL_PARAMETERS: "url-parameters",
  HTTP_BODY: "http-body",
};
export const HTTP_METHOD = {
  GET: "GET",
  POST: "POST",
  PUT: "PUT",
  DELETE: "DELETE",
};
export const DEFAULT_NUM_THREADS = 10;
